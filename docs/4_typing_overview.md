# VMT Type System & Data Contracts

**Purpose & Scope:** This document defines the language-agnostic types, invariants, and serialization contracts for the VMT project. It serves as the authoritative reference for the data model, covering both the current implementation (foraging and bilateral barter exchange) and the specifications for upcoming features like money and markets.

**Document State:** This is a living specification. Sections are marked with one of the following statuses to reflect their relationship to the codebase:
*   `[IMPLEMENTED]` The contract is fully implemented and reflects the current state of the `main` branch.
*   `[PLANNED]` The contract is a forward-looking design for a feature that is not yet implemented.
*   `[DEPRECATED]` The contract is from a previous design and is no longer in use.

**Relation to Source Code:** While this document provides a comprehensive overview, the following files are considered the ultimate source of truth for their respective domains:
*   **Scenario Configuration:** `src/scenarios/schema.py`
*   **Telemetry Database Schema:** `src/telemetry/database.py` and `src/telemetry/db_loggers.py`

---

## Part 1: Core Simulation Contracts `[IMPLEMENTED]`

### 1. Core Primitives

These are the fundamental, language-agnostic data types that form the basis of the simulation.

```text
AgentID     := int (non-negative, unique)
Tick        := int (simulation time step, ≥ 0)
Coord       := tuple<int, int>  // (x, y) cartesian coordinates
Good        := str              // Identifier for a good, e.g., "A", "B", "M" (Money)
Quantity    := int              // Discrete amount of a good or resource (≥ 0)
Price       := float            // Exchange rate, typically in terms of a numéraire
UtilityVal  := float            // A scalar value representing an agent's utility
```

### 2. State Objects

These composite types represent the state of entities within the simulation.

#### 2.1 Position & Inventory
`Position` is an alias for `Coord`. The `Inventory` tracks goods A, B, and money M.

```text
Position := Coord
Inventory := {
  A: Quantity,  // Amount of good A
  B: Quantity,  // Amount of good B
  M: Quantity   // Money holdings in minor units [IMPLEMENTED Phase 1]
}
```
*   **Invariant:** All quantities in an inventory must be non-negative (integer ≥ 0).
*   **Source of Truth:** `src/vmt_engine/core/state.py:Inventory`

#### 2.2 Economic State: Quotes `[IMPLEMENTED]`
An agent's trading posture is represented as a dictionary mapping exchange pair keys to prices.

**Money-Aware Quotes Dictionary** (Phase 2+):
```text
Quotes := dict<str, Price> where keys are:
  "ask_A_in_B", "bid_A_in_B", "p_min", "p_max"  // Barter A↔B
  "ask_A_in_M", "bid_A_in_M"                     // Monetary A↔M
  "ask_B_in_M", "bid_B_in_M"                     // Monetary B↔M
```

**Legacy Quote Dataclass** (for bilateral barter only):
```text
Quote := {
  ask_A_in_B: Price,  // Price seller is asking for 1 unit of A (in terms of B)
  bid_A_in_B: Price,  // Price buyer is bidding for 1 unit of A (in terms of B)
  p_min:      Price,  // Seller's reservation price (derived from MRS)
  p_max:      Price   // Buyer's reservation price (derived from MRS)
}
```
*   **Source of Truth:** `src/vmt_engine/core/state.py:Quote` (dataclass), `src/vmt_engine/core/agent.py:Agent.quotes` (dict)
*   **Current Implementation:** Agents use `quotes: dict[str, float]` for money-aware exchange pairs
*   **Invariant:** For barter pairs, `ask_A_in_B ≥ p_min` and `bid_A_in_B ≤ p_max`. With non-zero `spread`, ask strictly exceeds bid.

#### 2.3 Agent State
The `Agent` object is separated into its configuration (defined at the start of a simulation) and its dynamic runtime state.

```text
// Configuration (Static)
AgentConfig := {
  id:                   AgentID,
  utility:              Utility,
  vision_radius:        int ≥ 0,
  move_budget_per_tick: int ≥ 0
}

// Runtime State (Dynamic)
AgentState := {
  pos:               Position,
  inventory:         Inventory,
  quotes:            dict<str, Price>, // Money-aware: keys for all exchange pairs [IMPLEMENTED Phase 2]
  inventory_changed: bool,             // Flag to trigger quote recalculation
  target_pos:        optional<Position>,
  target_agent_id:   optional<AgentID>,
  trade_cooldowns:   map<AgentID, Tick>, // Cooldown until tick for a given partner
  paired_with_id:    optional<AgentID>,  // Trade partner ID (pairing system) [IMPLEMENTED]
  lambda_money:      float,              // Marginal utility of money [IMPLEMENTED Phase 1]
  lambda_changed:    bool                // Flag for lambda update detection [IMPLEMENTED Phase 1]
}
```
*   **Source of Truth:** `src/vmt_engine/core/agent.py:Agent`

#### 2.4 Environment State
The environment consists of a grid of `Cell` objects.

```text
Resource := {
  type:   Good,
  amount: Quantity
}

Cell := {
  position: Position,
  resource: Resource
}

Environment := {
  grid_size: int ≥ 1,
  cells:     map<Position, Cell>
}
```
*   **Source of Truth:** `src/vmt_engine/core/grid.py`

### 3. Economic Logic

This section defines the core economic computations.

#### 3.1 Utility Functions `[IMPLEMENTED]`
Utility is represented as a discriminated union, allowing for different functional forms.

```text
// CES Parameters
CESParams := { rho: float, wA: float > 0, wB: float > 0 }

// Linear Parameters
LinearParams := { vA: float > 0, vB: float > 0 }

// Quadratic Parameters
QuadraticParams := { 
  A_star: float > 0,    // Bliss point for A
  B_star: float > 0,    // Bliss point for B
  sigma_A: float > 0,   // Curvature parameter for A
  sigma_B: float > 0,   // Curvature parameter for B
  gamma: float >= 0     // Cross-curvature (optional, default 0.0)
}

// Translog Parameters
TranslogParams := { 
  alpha_0: float,       // Constant term
  alpha_A: float > 0,   // First-order coefficient for A
  alpha_B: float > 0,   // First-order coefficient for B
  beta_AA: float,       // Second-order coefficient for A
  beta_BB: float,       // Second-order coefficient for B
  beta_AB: float        // Cross-partial (interaction) coefficient
}

// Stone-Geary Parameters
StoneGearyParams := {
  alpha_A: float > 0,   // Preference weight for A
  alpha_B: float > 0,   // Preference weight for B
  gamma_A: float >= 0,  // Subsistence level for A
  gamma_B: float >= 0   // Subsistence level for B
}

// Discriminated Union
Utility :=
  | { type: "ces",         params: CESParams }
  | { type: "linear",      params: LinearParams }
  | { type: "quadratic",   params: QuadraticParams }
  | { type: "translog",    params: TranslogParams }
  | { type: "stone_geary", params: StoneGearyParams }
```

**Important Invariant for Stone-Geary**:
In any scenario using Stone-Geary utility, initial inventories must satisfy:
```
initial_A > gamma_A  AND  initial_B > gamma_B
```
This constraint is validated during scenario loading to prevent agents from starting below subsistence.

**Money-Aware Utility API** (Phase 2+):
*   `u_goods(A: int, B: int) -> float`: Compute utility from goods only (canonical method)
*   `mu_A(A: int, B: int) -> float`: Marginal utility of good A (∂U/∂A)
*   `mu_B(A: int, B: int) -> float`: Marginal utility of good B (∂U/∂B)
*   `u_total(inventory, params) -> float`: Total utility including money `[PLANNED Phase 3+]`

**Legacy API** (backward compatible):
*   `u(A: int, B: int) -> float`: Routes to `u_goods()` `[DEPRECATED]`
*   `mu(A: int, B: int) -> tuple[float, float]`: Routes to `(mu_A(), mu_B())` `[DEPRECATED]`

*   **Source of Truth:** `src/vmt_engine/econ/utility.py`
*   **Note:** Cobb-Douglas is implemented as a special case of CES where `rho` approaches 0.

#### 3.2 Trade & Surplus `[IMPLEMENTED]`
The logic for initiating and executing a trade is a multi-step process designed to find a mutually beneficial integer exchange.

**Surplus Computation:**
```text
// Surplus identifies trading potential (quote spread overlap)
surplus(i, j) := max(i.bid - j.ask, j.bid - i.ask)
```

**Compensating Block Search** (First-Acceptable-Trade Principle):
```text
// 1. Iterate through trade sizes ΔA from 1 to dA_max
// 2. For each ΔA, test multiple candidate prices within [seller.ask, buyer.bid]
// 3. For each candidate price, compute rounded ΔB:
ΔB = floor(price * ΔA + 0.5)

// 4. Accept the FIRST (ΔA, ΔB, price) tuple that yields strict utility gain for both:
if ΔU_buyer > 0 AND ΔU_seller > 0:
    execute trade and return
```

**Generic Matching** (Phase 2):
*   `find_compensating_block_generic()`: Supports barter (A↔B) and monetary (A↔M, B↔M) exchange
*   `find_best_trade()`: Selects highest-surplus exchange pair for a given agent pair

*   **Source of Truth:** `src/vmt_engine/systems/matching.py:find_compensating_block`, `find_compensating_block_generic`, `find_best_trade`
*   **Invariants:** 
    *   A trade only executes if `ΔU > 0` for *both* parties
    *   Uses first-acceptable-trade (not highest-surplus search)
    *   Final price is the discovered candidate, not quote midpoint
    *   Rounding ensures integer transfers for all goods

### 4. Simulation Loop (Tick Cycle) `[IMPLEMENTED]`

The simulation proceeds in a fixed, deterministic sequence of 7 phases. **This order is never changed.**

1.  **Perception:** Agents gather information about their local environment (neighbors, resources).
2.  **Decision:** Agents decide on a target and establish trade pairings.
    *   3-pass pairing algorithm: (1) build preference lists, (2) mutual consent pairing, (3) best-available fallback
    *   Resource claiming: agents claim forage targets to reduce clustering
    *   Stale claims cleared at start of tick
3.  **Movement:** Agents move towards their target (paired partner, resource, or other).
4.  **Trade:** Paired agents attempt to execute trades if within interaction radius.
    *   Generic money-aware matching (Phase 2): supports A↔B, A↔M, B↔M
    *   Only paired agents trade (enforces commitment)
    *   Failed trades unpair agents and set cooldown
5.  **Forage:** Agents harvest resources from their current cell.
    *   Single-harvester enforcement: first agent at cell claims harvest
    *   Paired agents skip foraging (exclusive commitment to trading)
6.  **Resource Regeneration:** Resources in cells are replenished according to scenario parameters.
7.  **Housekeeping:** Internal state is updated.
    *   Quotes recomputed if inventories changed
    *   Pairing integrity checks
    *   Lambda updates (KKT mode, Phase 3+)

*   **Determinism Rule:** Within each phase, agents are always processed in ascending order of their `agent.id`. Trade pairs are processed in ascending order of `(min_id, max_id)`.

---

## Part 2: Configuration & Telemetry `[IMPLEMENTED]`

This part details the data contracts for configuring a simulation run and for interpreting its output logs.

### 5. Scenario Schema (YAML)

A scenario is defined by a YAML file that adheres to the following structure. The authoritative source for this schema is the set of `dataclass` definitions in `src/scenarios/schema.py`.

```yaml
# Top-level metadata
name: string               # A human-readable name for the scenario.
N: int                     # The size of the NxN grid. Must be > 0.
agents: int                # The number of agents to create. Must be > 0.

# Defines the initial endowment of goods for the agents.
# Can be a fixed integer or a distribution function.
initial_inventories:
  A: int | { "uniform_int": [min, max] }
  B: int | { "uniform_int": [min, max] }

# Defines the mix of utility functions assigned to agents.
# The weights must sum to 1.0.
utilities:
  mix:
    - type: "ces" | "linear" | "quadratic" | "translog" | "stone_geary"
      weight: float         # Proportion of agents to receive this utility function.
      params:
        # For type: "ces"
        rho: float          # Elasticity of substitution parameter (cannot be 1.0).
        wA: float           # Weight for good A (> 0).
        wB: float           # Weight for good B (> 0).
        
        # For type: "linear"
        vA: float           # Value for good A (> 0).
        vB: float           # Value for good B (> 0).
        
        # For type: "quadratic"
        A_star: float       # Bliss point for A (> 0).
        B_star: float       # Bliss point for B (> 0).
        sigma_A: float      # Curvature parameter for A (> 0).
        sigma_B: float      # Curvature parameter for B (> 0).
        gamma: float        # Cross-curvature parameter (>= 0, optional, default 0.0).
        
        # For type: "translog"
        alpha_0: float      # Constant term.
        alpha_A: float      # First-order coefficient for A (> 0).
        alpha_B: float      # First-order coefficient for B (> 0).
        beta_AA: float      # Second-order coefficient for A.
        beta_BB: float      # Second-order coefficient for B.
        beta_AB: float      # Cross-partial coefficient (interaction term).
        
        # For type: "stone_geary"
        alpha_A: float      # Preference weight for A (> 0).
        alpha_B: float      # Preference weight for B (> 0).
        gamma_A: float      # Subsistence level for A (>= 0, must be < initial inventory).
        gamma_B: float      # Subsistence level for B (>= 0, must be < initial inventory).

# Defines the parameters governing simulation dynamics.
# All values have defaults, but can be overridden here.
params:
  spread: float                   # Bid-ask spread factor. Default: 0.0
  vision_radius: int              # How many cells an agent can see. Default: 5
  interaction_radius: int         # How close agents must be to trade. Default: 1
  move_budget_per_tick: int       # Max Manhattan distance to move per tick. Default: 1
  dA_max: int                     # Max trade size to search for good A. Default: 5
  forage_rate: int                # Max resources to forage per tick. Default: 1
  epsilon: float                  # Small number for safe division. Default: 1e-12
  beta: float                     # Discount factor for foraging scores. Default: 0.95
  resource_growth_rate: int       # Units of resource to regenerate per tick. Default: 0
  resource_max_amount: int        # Max amount of resource per cell. Default: 5
  resource_regen_cooldown: int    # Ticks to wait before regen starts. Default: 5
  trade_cooldown_ticks: int       # Ticks to wait after a failed trade attempt. Default: 5

# Defines how resources are seeded onto the grid.
resource_seed:
  density: float                # Probability [0,1] that a cell will have a resource.
  amount: int | { "uniform_int": [min, max] } # Amount of resource in a seeded cell.
```

### 6. Telemetry Schema (SQLite)

The simulation generates detailed logs stored in a SQLite database (`./logs/telemetry.db`). The schema for this database is the primary contract for analyzing simulation output.

*   **Source of Truth:** The `CREATE TABLE` statements in `src/telemetry/database.py`.

#### Table: `simulation_runs`
Stores metadata for each simulation run.
*   `run_id` (INTEGER, PK): Unique ID for the run.
*   `scenario_name` (TEXT): Name of the scenario.
*   `start_time` (TEXT): ISO 8601 timestamp of when the run started.
*   `end_time` (TEXT): ISO 8601 timestamp of when the run finished.
*   `total_ticks` (INTEGER): The total number of ticks the simulation ran for.
*   `num_agents` (INTEGER): Number of agents in the run.
*   `grid_width`, `grid_height` (INTEGER): Dimensions of the grid.
*   `config_json` (TEXT): A JSON dump of the full scenario configuration.
*   `exchange_regime` (TEXT): Exchange type control ("barter_only", "money_only", "mixed") `[IMPLEMENTED Phase 1]`
*   `money_mode` (TEXT): Money utility mode ("quasilinear", "kkt_lambda") `[IMPLEMENTED Phase 1]`
*   `money_scale` (INTEGER): Minor units scale for money `[IMPLEMENTED Phase 1]`

#### Table: `agent_snapshots`
Records the state of each agent at periodic intervals.
*   `snapshot_id` (INTEGER, PK)
*   `run_id` (INTEGER, FK)
*   `tick` (INTEGER)
*   `agent_id` (INTEGER)
*   `x`, `y` (INTEGER): Agent's position.
*   `inventory_A`, `inventory_B` (INTEGER): Agent's goods inventory.
*   `inventory_M` (INTEGER): Agent's money holdings in minor units `[IMPLEMENTED Phase 1]`
*   `utility` (REAL): Agent's calculated utility value.
*   `ask_A_in_B`, `bid_A_in_B` (REAL): Barter quotes for A in terms of B.
*   `p_min`, `p_max` (REAL): Reservation prices for barter.
*   `ask_A_in_M`, `bid_A_in_M` (REAL): Monetary quotes for A `[IMPLEMENTED Phase 2]`
*   `ask_B_in_M`, `bid_B_in_M` (REAL): Monetary quotes for B `[IMPLEMENTED Phase 2]`
*   `perceived_price_A`, `perceived_price_B` (REAL): Aggregated neighbor prices (KKT mode) `[IMPLEMENTED Phase 2]`
*   `lambda_money` (REAL): Marginal utility of money `[IMPLEMENTED Phase 1]`
*   `lambda_changed` (INTEGER): Boolean flag for lambda update detection `[IMPLEMENTED Phase 1]`
*   `target_agent_id` (INTEGER, nullable): The ID of the agent's current trade target.
*   `target_x`, `target_y` (INTEGER, nullable): The coordinates of the agent's current target.
*   `utility_type` (TEXT): The class name of the agent's utility function.

#### Table: `resource_snapshots`
Records the state of resources on the grid at periodic intervals.
*   `snapshot_id` (INTEGER, PK)
*   `run_id` (INTEGER, FK)
*   `tick` (INTEGER)
*   `x`, `y` (INTEGER): Cell position.
*   `resource_type` (TEXT): The `Good` in the cell.
*   `amount` (INTEGER): The quantity of the resource.

#### Table: `trades`
Records every successful trade that occurs.
*   `trade_id` (INTEGER, PK)
*   `run_id` (INTEGER, FK)
*   `tick` (INTEGER)
*   `x`, `y` (INTEGER): Location of the trade.
*   `buyer_id`, `seller_id` (INTEGER)
*   `dA`, `dB` (INTEGER): The amounts of goods A and B exchanged.
*   `dM` (INTEGER): Money transfer amount (0 for barter) `[IMPLEMENTED Phase 2]`
*   `price` (REAL): The price of the trade.
*   `direction` (TEXT): String indicating who initiated the trade.
*   `exchange_pair_type` (TEXT): Exchange pair ("A<->B", "A<->M", "B<->M") `[IMPLEMENTED Phase 3]` — Properly logged with money-first tie-breaking in mixed regimes
*   `buyer_lambda`, `seller_lambda` (REAL): Lambda values at trade time `[IMPLEMENTED Phase 2]`
*   `buyer_surplus`, `seller_surplus` (REAL): Utility gains for each party `[IMPLEMENTED Phase 2]`

#### Table: `decisions`
Records the outcome of the decision-making phase for each agent at each tick.
*   `decision_id` (INTEGER, PK)
*   `run_id` (INTEGER, FK)
*   `tick` (INTEGER)
*   `agent_id` (INTEGER)
*   `chosen_partner_id` (INTEGER, nullable): Partner chosen for trade.
*   `surplus_with_partner` (REAL, nullable): Potential surplus with the chosen partner.
*   `target_type` (TEXT): The type of action chosen ('trade', 'forage', 'idle', 'trade_paired').
*   `target_x`, `target_y` (INTEGER, nullable): The target coordinates.
*   `num_neighbors` (INTEGER): Number of other agents in the agent's vision radius.
*   `alternatives` (TEXT): A string representation of the other options considered (deprecated, see `preferences` table).
*   `mode` (TEXT): Current mode from mode_schedule ('forage', 'trade', 'both') `[IMPLEMENTED]`
*   `claimed_resource_pos` (TEXT): Resource position claimed by agent `[IMPLEMENTED]`
*   `is_paired` (INTEGER): Boolean flag indicating if agent is paired `[IMPLEMENTED]`

#### Table: `trade_attempts`
(Debug-level log) Records the detailed mechanics of every trade attempt, successful or not.
*   `attempt_id` (INTEGER, PK)
*   `run_id`, `tick`, `buyer_id`, `seller_id` (INTEGER)
*   ... (many columns detailing the initial/final states, feasibility, and outcome of the compensating block search)

#### Table: `tick_states` `[IMPLEMENTED Phase 1]`
Tracks combined mode+regime state per tick (Option A-plus observability).
*   `tick_id` (INTEGER, PK)
*   `run_id` (INTEGER, FK)
*   `tick` (INTEGER)
*   `current_mode` (TEXT): Temporal control ("forage", "trade", "both")
*   `exchange_regime` (TEXT): Type control ("barter_only", "money_only", "mixed")
*   `active_pairs` (TEXT): JSON array of active exchange pair types, e.g., `["A<->M", "B<->M"]`

#### Table: `pairings` `[IMPLEMENTED]`
Records pairing and unpairing events between agents.
*   `pairing_id` (INTEGER, PK)
*   `run_id` (INTEGER, FK)
*   `tick` (INTEGER)
*   `agent_i`, `agent_j` (INTEGER): The two agents involved
*   `event` (TEXT): "pair" or "unpair"
*   `reason` (TEXT): Event reason ("mutual_consent", "fallback_rank_0_surplus_0.6", "trade_failed", "mode_switch", etc.)
*   `surplus_i`, `surplus_j` (REAL, nullable): Undiscounted surplus for each agent (NULL for unpair events)

#### Table: `preferences` `[IMPLEMENTED]`
Records agent preference rankings (top 3 by default, configurable to full list).
*   `preference_id` (INTEGER, PK)
*   `run_id` (INTEGER, FK)
*   `tick` (INTEGER)
*   `agent_id` (INTEGER)
*   `partner_id` (INTEGER)
*   `rank` (INTEGER): Preference ranking (0 = top choice, 1 = second, etc.)
*   `surplus` (REAL): Undiscounted surplus
*   `discounted_surplus` (REAL): Distance-discounted surplus (= surplus × β^distance)
*   `distance` (INTEGER): Manhattan distance to partner

#### Table: `lambda_updates` `[PLANNED Phase 3+]`
Tracks KKT lambda estimation diagnostics (KKT mode only).
*   `update_id` (INTEGER, PK)
*   `run_id` (INTEGER, FK)
*   `tick` (INTEGER)
*   `agent_id` (INTEGER)
*   `lambda_old`, `lambda_new` (REAL): Lambda before/after update
*   `lambda_hat_A`, `lambda_hat_B`, `lambda_hat` (REAL): Intermediate estimates
*   `clamped` (INTEGER): Boolean flag if bounds were hit
*   `clamp_type` (TEXT, nullable): "lower", "upper", or NULL

---

## Part 3: Future & Cross-Platform

This part outlines planned extensions to the type system and provides reference material for ports to other languages.

### 7. Money & Market Contracts

This section documents the money system implementation and plans for centralized markets.

#### 7.1 Core Monetary Concepts `[IMPLEMENTED]`
*   **Numéraire (Money):** Good with identifier `"M"`, stored as `Inventory.M: int` in minor units (e.g., cents)
*   **Exchange Regimes:** `exchange_regime` parameter controls allowed exchange types:
    *   `"barter_only"`: Only A↔B trades (default, backward compatible) `[IMPLEMENTED]`
    *   `"money_only"`: Only A↔M and B↔M trades `[IMPLEMENTED]`
    *   `"mixed"`: All exchange pairs allowed `[IMPLEMENTED]`
    *   `"mixed_liquidity_gated"`: Mixed with minimum quote depth requirement `[PLANNED]`
*   **Quasilinear Utility:** Current implementation uses U_total = U_goods(A, B) + λ·M where λ = marginal utility of money `[IMPLEMENTED]`
*   **Lambda Management:** 
    *   Fixed λ (quasilinear mode) with per-agent heterogeneity `[IMPLEMENTED]`
    *   Adaptive λ (KKT mode) estimated from neighbor prices `[PLANNED]`
*   **Money Scale:** `money_scale` converts between whole units and minor units (default: 1 = no conversion) `[IMPLEMENTED]`

#### 7.2 Bilateral Money Exchange `[IMPLEMENTED]`
Current implementation provides decentralized bilateral money exchange:
*   Agents trade goods (A or B) for money (M) with adjacent partners
*   Generic matching algorithm selects best exchange pair (A↔M, B↔M, or A↔B)
*   Quotes computed for all active exchange pairs based on marginal utilities
*   Same pairing and compensating block logic as barter
*   Money transfers recorded in `trades.dM` telemetry field

#### 7.3 Market Maker & Order Book `[PLANNED]`
A new type of entity, the `MarketMakerAgent`, will be introduced to facilitate centralized exchange.

```text
// An order submitted to the market maker
LimitOrder := {
  order_id:   UUID,
  agent_id:   AgentID,
  side:       enum { "buy", "sell" },
  good:       Good,
  quantity:   int,
  price_limit: Price_in_M
}

// The market maker's central ledger
OrderBook := {
  good: Good,
  bids: ordered_list<LimitOrder>, // Sorted high-to-low price
  asks: ordered_list<LimitOrder>  // Sorted low-to-high price
}
```

#### 7.4 New Simulation Phases `[PLANNED]`
The introduction of a market will require new phases in the tick cycle, such as:
*   `OrderPlacement`
*   `MarketClearing`

The exact sequence and interaction with existing phases is to be determined.

### 8. Cross-Language Mappings (Reference Design) `[IMPLEMENTED]`

This section provides reference implementations for the core data structures in other languages. These are intended as a guide for potential future ports of the VMT engine.

> **Note**: The current implementation is Python-only. These mappings serve as a design contract and a validation that the core model is language-agnostic.

#### 8.1 Rust (serde + strong enums)
```rust
struct Quote {
    ask_a_in_b: f64,
    bid_a_in_b: f64,
    p_min: f64,
    p_max: f64,
}

// Using a HashMap for inventory to support multiple goods
type Inventory = std::collections::HashMap<String, i32>;

enum Utility {
    Ces { rho: f64, w_a: f64, w_b: f64 },
    Linear { v_a: f64, v_b: f64 },
}
```

#### 8.2 TypeScript (zod)
```ts
import { z } from 'zod';

const Quote = z.object({
  ask_a_in_b: z.number(),
  bid_a_in_b: z.number(),
  p_min: z.number(),
  p_max: z.number(),
});

const Inventory = z.map(z.string(), z.number().int().nonnegative());

const Utility = z.union([
  z.object({ type: z.literal("ces"),    params: z.object({ rho: z.number(), wA: z.number().positive(), wB: z.number().positive() }) }),
  z.object({ type: z.literal("linear"), params: z.object({ vA: z.number().positive(), vB: z.number().positive() }) }),
]);
```

### 9. Specification History

This section tracks major revisions to this type and data contract specification.

*   **Initial Draft (October 2025):**
    *   Document created.
    *   Rewritten to align with the existing codebase for foraging and bilateral barter.
    *   Added detailed, code-derived schemas for Scenario Configuration (YAML) and Telemetry (SQLite).
    *   Added `[PLANNED]` section for Money & Market contracts.

*   **Money System Documentation (2025-10-20):**
    *   Updated Inventory to include M field `[IMPLEMENTED Phase 1]`
    *   Updated AgentState with lambda_money and lambda_changed `[IMPLEMENTED Phase 1]`
    *   Documented money-aware Quotes dictionary `[IMPLEMENTED Phase 2]`
    *   Updated Utility API with u_goods, mu_A, mu_B methods `[IMPLEMENTED Phase 2]`
    *   Documented generic matching and first-acceptable-trade principle `[IMPLEMENTED Phase 2]`
    *   Expanded 7-Phase Tick Cycle with pairing, claiming, and single-harvester details `[IMPLEMENTED]`
    *   Extended telemetry schema with money fields and new tables `[IMPLEMENTED Phases 1-2]`
    *   Added tick_states, pairings, and preferences tables `[IMPLEMENTED]`
    *   Updated Money & Market Contracts section with Phase 1-2 implementation status
*   **Money System Implementation (2025-10-21):**
    *   Core money system complete: quasilinear utility, three exchange regimes
    *   Marked `exchange_pair_type` as `[IMPLEMENTED]` in trades table
    *   Documented money-first tie-breaking algorithm
    *   Documented mode × regime interaction (two-layer control)
    *   Money-aware pairing and matching algorithms
    *   Comprehensive telemetry and demo scenarios
*   **Implementation Status Clarification (2025-01-27):**
    *   Clarified that kkt_lambda mode is `[PLANNED]`, not implemented
    *   Clarified that mixed_liquidity_gated regime is `[PLANNED]`, not implemented
    *   Updated all documents to reflect actual implementation status
    *   Documented protocol modularization requirement before Phase C
---
