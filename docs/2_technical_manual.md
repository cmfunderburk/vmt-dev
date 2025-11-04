# VMT Technical Manual

This document provides a detailed technical overview of the Visualizing Microeconomic Theory (VMT) engine. It is intended for developers, researchers, and users who wish to understand the internal mechanics of the simulation.

---

## 🏗️ Core Architecture

The VMT engine is designed around a set of core principles that ensure determinism, theoretical soundness, and extensibility.

### Project Structure

```
vmt-dev/
├── docs/                    # Consolidated documentation
├── scenarios/               # User-facing YAML scenario files
├── src/
│   ├── vmt_engine/          # Core simulation engine
│   ├── vmt_launcher/        # GUI Launcher application
│   ├── vmt_log_viewer/      # GUI Log Viewer application
│   ├── telemetry/           # SQLite logging system
│   └── scenarios/           # Scenario-related Python code (schema, loader)
├── tests/                   # Test suite (55+ tests)
├── launcher.py              # GUI entry point
└── main.py                  # CLI entry point
```

### The 7-Phase Tick Cycle

The simulation proceeds in discrete time steps called "ticks." Each tick, the engine executes 7 distinct phases in a fixed, deterministic order. This strict ordering is crucial for reproducibility and ensures that all agent actions are based on a consistent state of the world.

1.  **Perception**: Each agent observes its local environment within its `vision_radius`. This includes the positions of other agents, their broadcasted trade quotes, and the location of resources. To prevent race conditions, this perception is a **frozen snapshot** of the world at the beginning of the tick.

2.  **Decision**: Based on the perception snapshot, agents select targets and form trading pairs via configurable **search** and **matching protocols**:
    *   **Sub-phase 1: Search (Target Selection)** — Each agent uses a search protocol to evaluate visible options and select a target:
        - Search protocols build ranked preference lists from `WorldView` (agent's local perspective)
        - Default: `legacy_distance_discounted` uses distance-discounted surplus scoring
        - Alternative: `random_walk` (exploration), `myopic` (nearest-neighbor only)
        - **Preference Ranking**: Scored by `surplus × β^distance` where surplus is estimated via quote overlaps
        - **⚠️ Heuristic Nature**: Quote overlaps are fast O(1) heuristics that may not perfectly predict utility changes for non-linear utilities. However, once paired, Phase 4 uses full utility calculations, so agents still find good trades.
        - Agents skip neighbors in cooldown; paired agents maintain their pairing
        - **Resource Claiming**: Forage targets are claimed to prevent clustering (if `enable_resource_claiming=True`)
    *   **Sub-phase 2-3: Matching (Pairing Formation)** — A matching protocol processes all agent preferences using `ProtocolContext` (global perspective):
        - Matching protocols have omniscient access via `context.agents[id]` for evaluation
        - Default: `legacy_three_pass` implements mutual consent + greedy fallback
        - Alternative: `greedy_surplus` (welfare maximization), `random_matching` (baseline)
        - **Lightweight Evaluation**: Matching uses `TradePotentialEvaluator` (heuristic, fast)
        - **Pairing Commitment**: Once paired, both agents commit exclusively to each other until trade fails or mode changes

3.  **Movement**: Agents move towards their chosen targets (paired partner, resource, or other position) according to their `move_budget_per_tick`. Movement is deterministic, following specific tie-breaking rules (x-axis before y-axis, negative direction on ties, diagonal deadlock resolution by higher ID).

4.  **Trade**: Only **paired agents** within `interaction_radius` attempt trades via configurable **bargaining protocols**:
    *   **Protocol Selection**: Bargaining protocols determine negotiation mechanism (configurable in YAML)
    *   **Direct Agent Access**: Protocols receive full agent state directly (no params hacking)
    *   **Available Protocols**:
        - `compensating_block` (default): First feasible trade using VMT's foundational algorithm
        - `split_difference`: Equal surplus division (Nash bargaining approximation)
        - `take_it_or_leave_it`: Asymmetric power (ultimatum game)
    *   **Trade Discovery**: Protocols use injected `TradeDiscoverer` for finding terms
        - `CompensatingBlockDiscoverer`: Discrete quantity search (1, 2, 3, ...) with price candidates
        - Searches both directions (i gives A, j gives A)
        - Returns first mutually beneficial trade where both ΔU > ε
        - Full utility calculations (not heuristics)
    *   **Trade Outcome**: Successful trades maintain pairing (agents try again next tick); failed trades unpair agents and set mutual cooldown

5.  **Foraging**: Agents located on a resource cell harvest that resource, increasing their inventory. The amount harvested is limited by the `forage_rate`.
    *   **Paired Agent Skip**: Paired agents skip foraging (exclusive commitment to trading).
    *   **Single-Harvester Enforcement**: If `enforce_single_harvester=True`, only one agent per resource cell can harvest per tick (determined by lowest `agent.id`).

6.  **Resource Regeneration**: Resource cells that have been harvested regenerate over time. A cell must wait `resource_regen_cooldown` ticks before it can begin regenerating at a rate of `resource_growth_rate` per tick.

7.  **Housekeeping**: The tick concludes with cleanup and maintenance tasks:
    *   **Quote Refresh**: Agents refresh their trade quotes if `inventory_changed` or `lambda_changed` flags are set
    *   **Pairing Integrity Checks**: Detect and repair asymmetric pairings (defensive validation)
    *   **Lambda Updates** (Phase 3+, KKT mode): Adaptive marginal utility estimation from neighbor prices
    *   **Telemetry Logging**: Agent snapshots, resource snapshots, tick states, pairing events, preferences logged to database

---

## 🔌 Protocol Architecture (Post-Decoupling)

VMT uses a modular protocol system that allows swapping economic mechanisms via YAML configuration. As of November 2025, the architecture has been fully decoupled to separate concerns between matching (pairing decisions) and bargaining (negotiation logic).

### Protocol Categories

**Search Protocols** (`agent_based.search`) - Phase 2, Sub-phase 1
- Determine how agents select targets and build preference lists
- Examples: `random_walk`, `legacy_distance_discounted`, `myopic`
- Input: `WorldView` (agent's local perspective)
- Output: `SetTarget` effects

**Matching Protocols** (`game_theory.matching`) - Phase 2, Sub-phase 2-3
- Determine how agents are paired for trading
- Examples: `greedy_surplus`, `random_matching`, `legacy_three_pass`
- Input: `ProtocolContext` (global matchmaker perspective)
- Output: `Pair`/`Unpair` effects

**Bargaining Protocols** (`game_theory.bargaining`) - Phase 4
- Determine trade terms between paired agents
- Examples: `compensating_block`, `split_difference`, `take_it_or_leave_it`
- Input: `(pair, agents, world)` - direct agent access
- Output: `Trade`/`Unpair` effects

### Decoupling Architecture (2025-11-03 Refactor)

Prior to the decoupling refactor, matching and bargaining protocols were tightly coupled through shared functions. This created three problems:
1. Matching protocols ran full bargaining algorithms just to decide pairings (behavioral issue)
2. Bargaining protocols couldn't use alternative discovery methods (flexibility issue)
3. Params hacks smuggled state through dictionaries (code quality issue)

**The solution**: Two abstraction interfaces that separate concerns:

#### TradePotentialEvaluator (Matching Phase)

Lightweight heuristic for "Can these agents trade?"

```python
class TradePotential(NamedTuple):
    is_feasible: bool                  # Can they trade?
    estimated_surplus: float           # Estimated gains (heuristic)
    preferred_direction: str | None    # "i_gives_A" or "i_gives_B"
    confidence: float                  # 0.0 to 1.0

class TradePotentialEvaluator(ABC):
    @abstractmethod
    def evaluate_pair_potential(
        self, agent_i: Agent, agent_j: Agent
    ) -> TradePotential:
        """Fast heuristic evaluation for pairing decisions."""
        pass
```

**Default Implementation**: `QuoteBasedTradeEvaluator`
- Uses `compute_surplus()` (quote overlaps)
- O(1) per pair evaluation
- No full utility calculations
- Used by: `greedy_surplus` matching protocol

#### TradeDiscoverer (Bargaining Phase)

Full trade discovery for "What exact terms?"

```python
class TradeTuple(NamedTuple):
    dA_i: Decimal      # Change in A for agent_i
    dB_i: Decimal      # Change in B for agent_i
    dA_j: Decimal      # Change in A for agent_j
    dB_j: Decimal      # Change in B for agent_j
    surplus_i: float   # Utility gain for agent_i
    surplus_j: float   # Utility gain for agent_j
    price: float       # Price of A in terms of B
    pair_name: str     # "A<->B"

class TradeDiscoverer(ABC):
    @abstractmethod
    def discover_trade(
        self, agent_i: Agent, agent_j: Agent, epsilon: float
    ) -> TradeTuple | None:
        """Full utility calculation and discrete search."""
        pass
```

**Default Implementation**: `CompensatingBlockDiscoverer`
- Implements VMT's foundational algorithm
- Searches quantities (1, 2, 3, ...) and prices
- Returns first feasible trade
- O(K×P) where K=quantities, P=prices per quantity
- Used by: All bargaining protocols

### Context Objects

**WorldView** (Individual agent perspective)
- Immutable snapshot of what one agent perceives
- Own state: inventory, utility, quotes, position
- Visible neighbors: positions, quotes (public info only)
- Used by: Search protocols, Bargaining protocols (for tick/params/rng)
- Mutation control: Agents read-only, return Effects

**ProtocolContext** (Central matchmaker perspective)
- Immutable snapshot of global simulation state
- All agents: Direct access via `agents` dict (omniscient planner)
- All agent views: Public information (`all_agent_views`)
- Used by: Matching protocols
- Philosophy: Information hiding applies to agent-to-agent interactions, not protocol coordination

### Direct Agent Access (Params Hack Elimination)

**Bargaining protocols** receive agents directly:
```python
def negotiate(
    self,
    pair: tuple[int, int],
    agents: tuple[Agent, Agent],  # Direct access
    world: WorldView
) -> list[Effect]:
```

**Matching protocols** access via context:
```python
def find_matches(
    self, preferences: dict, world: ProtocolContext
) -> list[Effect]:
    agent = world.agents[agent_id]  # Direct access
```

**Why this works**: Protocols can read full agent state for decisions but cannot mutate (must return Effects). Debug assertions enforce immutability in development.

---

## ⚙️ Key Systems & Design Principles

### Determinism and Reproducibility

Determinism is the cornerstone of the VMT engine. Given the same scenario file and the same seed, the simulation will produce the exact same outcome every single time. This is achieved through several strict rules:

-   **Fixed Tick Order**: The 7-phase cycle never changes.
-   **Sorted Iteration**: All loops over agents are sorted by `agent.id`. All loops over potential trade pairs are sorted by `(min_id, max_id)`. There is no reliance on non-deterministic data structures like Python dictionaries for iteration.
-   **Deterministic Tie-Breaking**: Any situation that could be ambiguous is resolved with a fixed rule. For example, when choosing a movement path, agents prefer reducing distance on the x-axis before the y-axis, and prefer negative directions on ties.
-   **Fixed-Precision Arithmetic**: All quantity calculations use Python's `Decimal` type with a fixed precision of 4 decimal places (configurable via `QUANTITY_DECIMAL_PLACES`). This ensures exact, reproducible arithmetic operations and avoids floating-point rounding errors that could affect determinism. Quantities are stored in the database as integer minor units (value × 10^4) using `to_storage_int()` conversion.

### Economic Logic

#### Utility Functions
-   **Utility Functions**: The engine supports five utility function classes, all defined in `src/vmt_engine/econ/utility.py`:
    *   `UCES` — Constant Elasticity of Substitution (including Cobb-Douglas as a special case)
    *   `ULinear` — Perfect substitutes (constant marginal utility)
    *   `UQuadratic` — Bliss points and satiation (non-monotonic preferences)
    *   `UTranslog` — Transcendental logarithmic (flexible second-order approximation)
    *   `UStoneGeary` — Subsistence constraints (foundation of Linear Expenditure System)
-   **Utility API**: The utility interface provides core methods:
    *   `u(A, B)` — Utility from goods (canonical method), accepts `Decimal` inputs, returns `float`
    *   `u_goods(A, B)` — Alias for `u(A, B)` (backward compatibility)
    *   `mu_A(A, B)`, `mu_B(A, B)` — Marginal utilities of goods A and B (∂U/∂A, ∂U/∂B), accept `Decimal`, return `float`
    *   `mu(A, B)` — Returns tuple (MU_A, MU_B)
    *   All quantity inputs use `Decimal` for precision; calculations convert to `float` internally for mathematical operations
-   **Pure Barter Economy**: VMT is a pure barter economy - all trades are direct A↔B exchanges
-   **Reservation Bounds**: Agents' willingness to trade is determined by their reservation price, which is derived from their marginal rate of substitution (MRS). The engine uses a generic `reservation_bounds_A_in_B(A, B, eps)` function. This returns the minimum price an agent would accept (`p_min`) and the maximum price they would pay (`p_max`).
-   **Zero-Inventory Guard**: A critical feature is the handling of zero-inventory cases for CES utilities. When an agent has zero of a good, its MRS can be undefined or infinite. The engine handles this by adding a tiny `epsilon` value to the inventory levels *only for the ratio calculation* used to determine reservation bounds. The core utility calculation `u(A, B)` always uses the true integer inventories.

#### Agent Initialization and Heterogeneity
Agents are not required to be homogeneous. The `scenarios/*.yaml` format allows for specifying a distribution of preferences across the agent population.

-   **Utility Mix**: The `utilities.mix` section of a scenario file defines a list of one or more utility function configurations, each with a `type`, `params`, and a `weight`. The weights must sum to 1.0.
-   **Probabilistic Assignment**: During simulation setup, each agent's utility function is independently chosen from this list via weighted random sampling (`numpy.random.Generator.choice`). This means that a scenario can define, for example, a population composed of 80% CES agents and 20% Linear agents, each with their own specific parameters. An agent is assigned exactly one utility function.
-   **Initial Inventories**: Initial inventories can also be heterogeneous, specified either as a single value (all agents start the same) or as an explicit list of values, one for each agent.

##### Utility Function Details

**CES (Constant Elasticity of Substitution)**:
- Parameters: `rho` (elasticity), `wA`, `wB` (weights)
- Special case: When `rho → 0`, approaches Cobb-Douglas
- Properties: Monotonic, convex preferences, constant elasticity of substitution
- Use cases: Standard microeconomic analysis, variety-seeking behavior

**Linear (Perfect Substitutes)**:
- Parameters: `vA`, `vB` (per-unit values)
- Properties: Constant marginal rate of substitution (MRS = vA/vB)
- Use cases: Homogeneous goods, arbitrage scenarios, simple exchange

**Quadratic (Bliss Points)**:
- Parameters: `A_star`, `B_star` (bliss points), `sigma_A`, `sigma_B` (curvature), `gamma` (cross-curvature)
- Properties: Non-monotonic (satiation beyond bliss points), can have negative marginal utility
- Use cases: Demonstrations of satiation, gift economies, non-convex preferences
- Special handling: Agents may refuse trades when saturated (MU ≤ 0)

**Translog (Transcendental Logarithmic)**:
- Parameters: `alpha_0` (constant), `alpha_A`, `alpha_B` (first-order), `beta_AA`, `beta_BB`, `beta_AB` (second-order)
- Properties: Flexible functional form, variable elasticity of substitution, second-order Taylor approximation
- Use cases: Empirical estimation, production function analysis, testing functional form assumptions
- Special handling: Works in log-space for numerical stability, epsilon-shift for zero inventories

**Stone-Geary (Subsistence Constraints)**:
- Parameters: `alpha_A`, `alpha_B` (preference weights), `gamma_A`, `gamma_B` (subsistence levels)
- Properties: Subsistence thresholds, hyperbolic marginal utility near subsistence, nests Cobb-Douglas
- Use cases: Development economics, basic needs modeling, poverty analysis, LES demand systems
- Special handling: Requires initial inventories > subsistence; agents trade desperately when close to subsistence
- Important invariant: Scenarios must validate `initial_A > gamma_A` and `initial_B > gamma_B`
    
#### Quotes and Trading
-   **Quotes**: Agents maintain a dictionary of quotes (`Agent.quotes: dict[str, float]`) with keys for barter exchange:
    *   Barter: `"ask_A_in_B"`, `"bid_A_in_B"`, `"p_min_A_in_B"`, `"p_max_A_in_B"`, `"ask_B_in_A"`, `"bid_B_in_A"`, `"p_min_B_in_A"`, `"p_max_B_in_A"`
    *   Quotes are calculated from reservation bounds: `ask = p_min * (1 + spread)` and `bid = p_max * (1 - spread)`
-   **Trade Discovery Architecture** (Post-Decoupling): Finding mutually beneficial trades is now handled by `TradeDiscoverer` implementations:
    *   **Interface**: `TradeDiscoverer.discover_trade(agent_i, agent_j, epsilon) -> TradeTuple | None`
    *   **Default**: `CompensatingBlockDiscoverer` implements VMT's foundational algorithm
    *   **Barter Only**: All trades are A↔B goods exchanges
-   **Compensating Block Algorithm**: The foundational VMT trade discovery method:
    *   Probes multiple prices within valid `[ask_seller, bid_buyer]` range
    *   For each price, scans discrete quantities from `ΔA=1` up to seller's inventory
    *   Applies **decimal quantization**: `ΔB = quantize_quantity(Decimal(price) * Decimal(ΔA))`
    *   Returns **first feasible trade** where both agents gain utility (ΔU > ε)
    *   Searches both directions (i sells A, j sells A) and returns immediately when found
    *   Accepts the **first** trade block `(ΔA, ΔB)` that provides **strict utility improvement (ΔU > 0)** for both agents
    *   All quantity deltas are `Decimal` values quantized to configured precision (4 decimal places)
    *   This is the **first-acceptable-trade principle**, not highest-surplus search

### Behavioral Logic

#### Trade Cooldown
-   To prevent agents from getting stuck in futile loops (e.g., two agents repeatedly targeting each other but failing to find a valid trade block), the engine implements a trade cooldown.
-   After a failed trade attempt, a mutual cooldown is set for both agents for `trade_cooldown_ticks`. During this period, they will not consider each other as potential trading partners.

#### Foraging and Movement
-   **Foraging Target Score**: Agents decide which resource to pursue by calculating a score for each visible resource cell: `Score = ΔU_arrival * β^dist`.
    -   `ΔU_arrival` is the expected utility gain from harvesting the resource.
    -   `β` (beta) is the agent's time discount factor (0 < β < 1).
    -   `dist` is the Manhattan distance to the cell.
-   This scoring mechanism means agents intelligently balance the richness of a resource patch against the time it will take to reach it.

#### Resource Claiming System
-   **Motivation**: Without coordination, multiple agents often target the same high-value resource, leading to inefficient clustering. Only one agent can harvest per tick, so others wait idle.
-   **Claiming Mechanism**: During Phase 2 (Decision), when an agent selects a forage target, it **claims** that resource by recording `resource_claims[position] = agent_id` in the simulation state. Other agents scanning for targets in the same tick see this resource as unavailable and choose alternatives.
-   **Claim Expiration**: Claims are transient and expire under two conditions:
    1. The agent reaches the resource cell (`agent.pos == claimed_pos`)
    2. The agent changes its target (`agent.target_pos != claimed_pos`)
-   **Stale Claim Clearing**: At the start of each tick's Decision phase, the engine clears all stale claims before agents make new decisions.
-   **Determinism**: Agents are processed in `agent.id` order during the Decision phase. Lower-ID agents claim resources first, ensuring consistent behavior across runs with the same seed.
-   **Configuration**: The system is controlled by two flags in `ScenarioParams`:
    -   `enable_resource_claiming` (default: `True`): Enables claim-based filtering
    -   `enforce_single_harvester` (default: `True`): During Phase 5 (Foraging), only the first agent (by ID) on a resource cell can harvest per tick
-   **Performance**: Claiming adds O(C) overhead where C = active claims (typically C ≤ N). Total decision complexity remains O(N*R). Single-harvester enforcement adds O(N) set operations during foraging.

#### Trade Pairing System
-   **Motivation**: Previous all-pairs matching was O(N²) per tick. The pairing system reduces this to O(N) by establishing committed bilateral partnerships that persist across ticks.
-   **Three-Pass Algorithm**: See [Decision Phase](#the-7-phase-tick-cycle) above for full details. Summary:
    *   **Pass 1**: Build ranked preference lists using distance-discounted surplus = `surplus × β^distance`
    *   **Pass 2**: Mutual consent pairing (both agents list each other as top choice)
    *   **Pass 3**: Surplus-based greedy matching (highest-surplus unmatched pairs assigned first)
-   **Commitment Model**: Once paired, agents commit exclusively to each other:
    *   Move toward partner until within interaction radius
    *   Attempt trades each tick (may execute multiple trades across ticks)
    *   Ignore all other trading and foraging opportunities during pairing
    *   Unpair only when trade fails (opportunities exhausted) or mode changes
-   **Telemetry**: Three new tables track pairing dynamics:
    *   `pairings` — Pairing/unpairing events with reason codes
    *   `preferences` — Top-ranked agent preferences (default: top 3, configurable to full list)
    *   `decisions.is_paired` — Boolean flag indicating pairing status
-   **Performance**: Reduces trade phase from O(N²) distance checks to O(P) where P = paired count (typically P ≤ N/2). Decision phase remains O(N·k) where k = average neighbors.
-   **Pedagogical Note**: Agents can commit to distant partners and spend many ticks moving toward them while ignoring other opportunities. Once paired, they execute multiple sequential trades. This demonstrates opportunity cost of commitment and iterative bilateral exchange.

#### Economic Decision-Making: Trade vs Forage Comparison
-   **Motivation**: When both trading and foraging are available (mode = "both"), agents must decide which activity offers higher utility gain. This is a fundamental economic choice: should I gather resources or exchange with others?
-   **Comparable Scoring**: Both activities are measured in utility units with identical distance discounting:
    *   **Trade score**: `surplus × β^distance` where surplus = bilateral utility gain from best feasible trade
    *   **Forage score**: `delta_u × β^distance` where delta_u = utility gain from harvesting best resource
    *   Both use the same β (discount factor parameter), making direct comparison economically valid
-   **Decision Rule** (`_evaluate_trade_vs_forage` in `src/vmt_engine/systems/decision.py`):
    1.  Evaluate all visible trade partners, rank by discounted surplus (done in `_evaluate_trade_preferences`)
    2.  Evaluate all available resources, calculate best forage score using `choose_forage_target`
    3.  **Choose whichever activity has the higher score**
    4.  If trade chosen: Set target to best partner and participate in pairing algorithm
    5.  If forage chosen: Claim resource and set foraging commitment (persists until harvest)
-   **Example**: Agent with neighbors offering trade scores (5.2, 3.1) and forage opportunity with score 4.0:
    *   Agent chooses trading with best partner (5.2 > 4.0 > 3.1)
    *   If forage score were 6.0, agent would forage instead (6.0 > 5.2)
    *   This implements rational utility-maximizing behavior
-   **Mode Behavior**:
    *   **mode = "trade"**: Only trade opportunities evaluated (forage unavailable)
    *   **mode = "forage"**: Only forage opportunities evaluated (trade unavailable)
    *   **mode = "both"**: Full comparison as described above (economically optimal)
-   **Historical Note**: Prior to this implementation, agents used lexicographic preferences ("trade if any opportunity exists, otherwise forage"), which was not economically correct. The current system properly balances opportunity costs.

#### Trade System
-   **Pure Barter Economy**: All trades are direct A↔B good-for-good exchanges
-   **Mode Scheduling**: Temporal control of agent activities:
    *   **`mode_schedule`**: WHEN activities occur (forage/trade/both modes)
    *   In forage mode, no trading occurs
    *   In trade/both modes, agents can engage in A↔B barter
-   **Bargaining Protocols**: Configurable negotiation mechanisms:
    *   `compensating_block` (default): First feasible trade, VMT's core algorithm
    *   `split_difference`: Equal surplus division for fairness
    *   `take_it_or_leave_it`: Asymmetric power dynamics
    *   Protocols inject custom `TradeDiscoverer` implementations
-   **Trade Discovery**: 
    *   `CompensatingBlockDiscoverer`: Default discoverer using discrete search
    *   Returns `TradeTuple` with full trade specification (quantities, surpluses, price)
    *   Performs full utility calculations (not heuristics like matching phase)
-   **Telemetry**: Trade telemetry logs A and B quantities exchanged, along with the price and surplus for each agent

---

## 🔬 Testing and Validation

The VMT engine is rigorously tested to ensure both technical correctness and theoretical soundness. The test suite (`tests/`) contains 320+ tests covering:
-   **Core State**: Grid logic, agent creation, state management, pairing state
-   **Utilities**: Correctness of all utility function calculations, especially at edge cases
-   **Reservation Bounds**: Correctness of the zero-inventory guard
-   **Trade Logic**: Correctness of rounding, compensating multi-lot search, cooldowns, and pairing
-   **Trade Evaluation Abstractions** (New): 
    *   `TradePotentialEvaluator` interface and implementations
    *   `TradeDiscoverer` interface and implementations
    *   NamedTuple return types (immutability, zero overhead)
    *   Immutability enforcement (protocols don't mutate agent state)
-   **Trade Pairing**: Mutual consent pairing, fallback pairing, pairing integrity, cooldown interactions
-   **Resource Claiming**: Claim recording, stale clearing, single-harvester enforcement
-   **Resource Regeneration**: Correctness of cooldowns, growth rates, and caps
-   **Protocol System**: Search, matching, and bargaining protocol implementations
    *   Protocol signature compliance (all protocols use correct interfaces)
    *   Direct agent access (no params hacks)
    *   Protocol integration (end-to-end with Effect system)
-   **Mode Management**: Mode schedule transitions and phase execution
-   **Determinism**: End-to-end tests that verify bit-identical log outputs for the same seed
-   **Performance**: Benchmark scenarios validating TPS thresholds with 400 agents

