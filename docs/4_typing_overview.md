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
`Position` is an alias for `Coord`. The `Inventory` is a mapping from a `Good` to its `Quantity`.

```text
Position := Coord
Inventory := map<Good, Quantity>
```
*   **Invariant:** All quantities in an inventory must be non-negative.

#### 2.2 Economic State: Quote
A `Quote` encapsulates an agent's trading posture for a given good pair (e.g., A in terms of B).

```text
Quote := {
  ask_A_in_B: Price,  // Price seller is asking for 1 unit of A (in terms of B)
  bid_A_in_B: Price,  // Price buyer is bidding for 1 unit of A (in terms of B)
  p_min:      Price,  // Seller's reservation price (derived from MRS)
  p_max:      Price   // Buyer's reservation price (derived from MRS)
}
```
*   **Source of Truth:** `src/vmt_engine/core/state.py:Quote`
*   **Invariant:** `ask_A_in_B ≥ p_min` and `bid_A_in_B ≤ p_max`. For a non-zero `spread` parameter, `ask_A_in_B` will be strictly greater than `bid_A_in_B`.

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
  quotes:            Quote,
  inventory_changed: bool, // Flag to trigger quote recalculation
  target_pos:        optional<Position>,
  target_agent_id:   optional<AgentID>,
  trade_cooldowns:   map<AgentID, Tick> // Cooldown until tick for a given partner
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

#### 3.1 Utility Functions
Utility is represented as a discriminated union, allowing for different functional forms.

```text
// CES Parameters
CESParams := { rho: float, wA: float > 0, wB: float > 0 }

// Linear Parameters
LinearParams := { vA: float > 0, vB: float > 0 }

// Discriminated Union
Utility :=
  | { type: "ces",    params: CESParams }
  | { type: "linear", params: LinearParams }
```
*   **Source of Truth:** `src/vmt_engine/econ/utility.py`
*   **Note:** Cobb-Douglas is implemented as a special case of CES where `rho` approaches 0.

#### 3.2 Trade & Surplus
The core logic for initiating and executing a trade.

```text
// Surplus is the potential gain from trade between two agents
surplus(i, j) := max(i.bid - j.ask, j.bid - i.ask)

// The transaction price is the midpoint of the overlapping quotes
price(seller, buyer) := 0.5 * (seller.ask + buyer.bid)

// Trade execution involves a search for a mutually beneficial integer trade
// using round-half-up for quantities.
ΔB = floor(price * ΔA + 0.5)
```
*   **Invariants:** A trade only executes if it results in a strict utility increase (`ΔU > 0`) for *both* parties. The search for a valid trade block (`ΔA`, `ΔB`) starts at `ΔA=1` and proceeds up to `dA_max`.

### 4. Simulation Loop (Tick Cycle)

The simulation proceeds in a fixed, deterministic sequence of 7 phases. **This order is never changed.**

1.  **Perception:** Agents gather information about their local environment.
2.  **Decision:** Agents decide on a target (e.g., another agent to trade with, a resource to forage).
3.  **Movement:** Agents move towards their target.
4.  **Trade:** Agents attempt to execute trades with adjacent partners.
5.  **Forage:** Agents harvest resources from their current cell.
6.  **Resource Regeneration:** Resources in cells are replenished according to scenario parameters.
7.  **Housekeeping:** Internal state is updated (e.g., quotes are recomputed if inventories changed).

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
    - type: "ces" | "linear"
      weight: float         # Proportion of agents to receive this utility function.
      params:
        # For type: "ces"
        rho: float          # Elasticity of substitution parameter (cannot be 1.0).
        wA: float           # Weight for good A (> 0).
        wB: float           # Weight for good B (> 0).
        # For type: "linear"
        vA: float           # Value for good A (> 0).
        vB: float           # Value for good B (> 0).

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

#### Table: `runs`
Stores metadata for each simulation run.
*   `run_id` (INTEGER, PK): Unique ID for the run.
*   `scenario_name` (TEXT): Name of the scenario.
*   `start_time` (TEXT): ISO 8601 timestamp of when the run started.
*   `end_time` (TEXT): ISO 8601 timestamp of when the run finished.
*   `total_ticks` (INTEGER): The total number of ticks the simulation ran for.
*   `num_agents` (INTEGER): Number of agents in the run.
*   `grid_width`, `grid_height` (INTEGER): Dimensions of the grid.
*   `config_json` (TEXT): A JSON dump of the full scenario configuration.

#### Table: `agent_snapshots`
Records the state of each agent at periodic intervals.
*   `snapshot_id` (INTEGER, PK)
*   `run_id` (INTEGER, FK)
*   `tick` (INTEGER)
*   `agent_id` (INTEGER)
*   `x`, `y` (INTEGER): Agent's position.
*   `inventory_A`, `inventory_B` (INTEGER): Agent's inventory.
*   `utility` (REAL): Agent's calculated utility value.
*   `ask_A_in_B`, `bid_A_in_B` (REAL): Agent's current quotes.
*   `p_min`, `p_max` (REAL): Agent's reservation prices.
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
*   `price` (REAL): The price of the trade (in B per A).
*   `direction` (TEXT): String indicating who initiated the trade.

#### Table: `decisions`
Records the outcome of the decision-making phase for each agent at each tick.
*   `decision_id` (INTEGER, PK)
*   `run_id` (INTEGER, FK)
*   `tick` (INTEGER)
*   `agent_id` (INTEGER)
*   `chosen_partner_id` (INTEGER, nullable): Partner chosen for trade.
*   `surplus_with_partner` (REAL, nullable): Potential surplus with the chosen partner.
*   `target_type` (TEXT): The type of action chosen ('trade', 'forage', 'idle').
*   `target_x`, `target_y` (INTEGER, nullable): The target coordinates.
*   `num_neighbors` (INTEGER): Number of other agents in the agent's vision radius.
*   `alternatives` (TEXT): A string representation of the other options considered.

#### Table: `trade_attempts`
(Debug-level log) Records the detailed mechanics of every trade attempt, successful or not.
*   `attempt_id` (INTEGER, PK)
*   `run_id`, `tick`, `buyer_id`, `seller_id` (INTEGER)
*   ... (many columns detailing the initial/final states, feasibility, and outcome of the compensating block search)

---

## Part 3: Future & Cross-Platform

This part outlines planned extensions to the type system and provides reference material for ports to other languages.

### 7. Money & Market Contracts `[PLANNED]`

This section specifies the data contracts for a future implementation of centralized markets and currency.

#### 7.1 Core Monetary Concepts
*   **Numéraire (Money):** A special `Good` with the identifier `"M"` will be introduced. It is perfectly divisible (`Quantity` becomes `float` for "M"), fungible, and serves as the universal medium of exchange.
*   **Price:** All prices will be quoted in terms of the numéraire, `Price_in_M`.
*   **Wallets:** Agent inventories will be partitioned into `goods: map<Good, int>` and `money: float`.

#### 7.2 Market Maker & Order Book
A new type of entity, the `MarketMakerAgent`, will be introduced to facilitate exchange.

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

#### 7.3 New Simulation Phases
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
---
