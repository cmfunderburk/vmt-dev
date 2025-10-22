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

2.  **Decision**: Based on the perception snapshot, agents decide on actions and establish trade pairings using a **three-pass algorithm**:
    *   **Pass 1: Target Selection & Preference Ranking** — Each agent (processed in ID order) evaluates all visible neighbors and builds a ranked preference list. Preferences are ranked by **distance-discounted surplus** = `surplus × β^distance`, where β is the discount factor and distance is Manhattan distance. 
        - **Money-Aware Surplus Calculation** (Phase 2+): In `money_only` and `mixed` regimes, agents use `estimate_money_aware_surplus()` which evaluates all allowed exchange pairs (A↔M, B↔M for money_only; A↔M, B↔M, A↔B for mixed) and returns the highest feasible surplus with money-first tie-breaking.
        - **Barter-Only Surplus** (Legacy): In `barter_only` regime, agents use `compute_surplus()` which evaluates only A↔B exchanges, preserving bit-identical backward compatibility.
        - **Inventory Feasibility**: Both surplus estimators check inventory constraints to prevent pairing when trades are impossible (e.g., if neither agent has goods or money to exchange).
        - **Money-First Priority**: When multiple exchange pairs offer equal surplus, monetary exchanges are preferred: A↔M (priority 0) > B↔M (priority 1) > A↔B (priority 2).
        - **⚠️ Important Limitation**: The surplus estimator uses **quote overlaps** (bid - ask price differences) as a heuristic proxy for actual utility gains. Quote overlaps may not perfectly predict true utility changes, especially with non-linear utility functions (CES, Quadratic) where the relationship between MRS and utility depends on function curvature. However, once paired, agents execute the ACTUAL best trade using full utility calculations, so they still achieve good outcomes. This design trades perfect accuracy for performance: O(1) per neighbor vs O(dA_max × prices) for exact calculation. See `estimate_money_aware_surplus()` documentation for details.
    *   Agents skip neighbors in cooldown. Already-paired agents validate their pairing and maintain target lock.
    *   **Pass 2: Mutual Consent Pairing** — Agents who mutually list each other as their top choice are paired via "mutual consent." Lower-ID agent executes the pairing to avoid duplication. Cooldowns are cleared for both agents.
    *   **Pass 3: Best-Available Fallback** — Unpaired agents with remaining preferences use **surplus-based greedy matching**: all potential pairings are sorted by descending discounted surplus, and pairs are greedily assigned in order. When an agent claims a partner, that partner's target is updated to point back at the claimer (reciprocal commitment).
    *   **Resource Claiming**: When agents select forage targets, they **claim** the resource to prevent clustering (if `enable_resource_claiming=True`). Stale claims are cleared at the start of each tick.
    *   **Pairing Commitment**: Once paired, both agents commit exclusively to each other. They move toward each other and attempt trades until opportunities are exhausted (trade fails) or mode changes. Paired agents do not re-evaluate preferences or seek new partners until unpaired.

3.  **Movement**: Agents move towards their chosen targets (paired partner, resource, or other position) according to their `move_budget_per_tick`. Movement is deterministic, following specific tie-breaking rules (x-axis before y-axis, negative direction on ties, diagonal deadlock resolution by higher ID).

4.  **Trade**: Only **paired agents** within `interaction_radius` attempt trades. The engine uses a sophisticated price search algorithm to find mutually beneficial terms:
    *   **Generic Matching**: Selects the best exchange pair (A↔B, A↔M, B↔M) based on `exchange_regime` parameter
    *   **Compensating Block Search**: Scans trade sizes ΔA from 1 to dA_max, testing candidate prices in [seller.ask, buyer.bid]
    *   **First-Acceptable-Trade Principle**: Accepts the first (ΔA, ΔB, price) tuple that yields strict utility gain (ΔU > 0) for both parties
    *   **Trade Outcome**: Successful trades maintain pairing (agents attempt another trade next tick); failed trades unpair agents and set mutual cooldown

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

## ⚙️ Key Systems & Design Principles

### Determinism and Reproducibility

Determinism is the cornerstone of the VMT engine. Given the same scenario file and the same seed, the simulation will produce the exact same outcome every single time. This is achieved through several strict rules:

-   **Fixed Tick Order**: The 7-phase cycle never changes.
-   **Sorted Iteration**: All loops over agents are sorted by `agent.id`. All loops over potential trade pairs are sorted by `(min_id, max_id)`. There is no reliance on non-deterministic data structures like Python dictionaries for iteration.
-   **Deterministic Tie-Breaking**: Any situation that could be ambiguous is resolved with a fixed rule. For example, when choosing a movement path, agents prefer reducing distance on the x-axis before the y-axis, and prefer negative directions on ties.

### Economic Logic

#### Utility Functions and Money-Aware API
-   **Utility Functions**: The engine supports five utility function classes, all defined in `src/vmt_engine/econ/utility.py`:
    *   `UCES` — Constant Elasticity of Substitution (including Cobb-Douglas as a special case)
    *   `ULinear` — Perfect substitutes (constant marginal utility)
    *   `UQuadratic` — Bliss points and satiation (non-monotonic preferences)
    *   `UTranslog` — Transcendental logarithmic (flexible second-order approximation)
    *   `UStoneGeary` — Subsistence constraints (foundation of Linear Expenditure System)
-   **Money-Aware API** (Phase 2+): The utility interface provides separate methods for goods and total utility:
    *   `u_goods(A, B)` — Utility from goods only (canonical method)
    *   `mu_A(A, B)`, `mu_B(A, B)` — Marginal utilities of goods A and B (∂U/∂A, ∂U/∂B)
    *   `u_total(inventory, params)` — Total utility including money (Phase 3+, planned)
    *   Legacy methods `u(A, B)` and `mu(A, B)` route to the money-aware API for backward compatibility
-   **Quasilinear Utility** (Phases 1-2): U_total = U_goods(A, B) + λ·M, where λ is the marginal utility of money and M is money holdings in minor units
-   **Reservation Bounds**: Agents' willingness to trade is determined by their reservation price, which is derived from their marginal rate of substitution (MRS). To avoid hard-coding MRS formulas, the engine uses a generic `reservation_bounds_A_in_B(A, B, eps)` function. This returns the minimum price an agent would accept (`p_min`) and the maximum price they would pay (`p_max`).
-   **Zero-Inventory Guard**: A critical innovation is the handling of zero-inventory cases for CES utilities. When an agent has zero of a good, its MRS can be undefined or infinite. The engine handles this by adding a tiny `epsilon` value to the inventory levels *only for the ratio calculation* used to determine reservation bounds. The core utility calculation `u_goods(A, B)` always uses the true integer inventories.

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
-   **Quotes**: Agents maintain a dictionary of quotes (`Agent.quotes: dict[str, float]`) with keys for all active exchange pairs:
    *   Barter: `"ask_A_in_B"`, `"bid_A_in_B"`, `"p_min"`, `"p_max"`
    *   Money (Phase 2+): `"ask_A_in_M"`, `"bid_A_in_M"`, `"ask_B_in_M"`, `"bid_B_in_M"`
    *   Quotes are calculated from reservation bounds: `ask = p_min * (1 + spread)` and `bid = p_max * (1 - spread)`
-   **Generic Matching Algorithm** (Phase 2+): The engine selects the best exchange pair for each agent pair based on `exchange_regime`:
    *   `"barter_only"` — Only A↔B trades (default, backward compatible)
    *   `"money_only"` — Only A↔M and B↔M trades
    *   `"mixed"` — All exchange pairs allowed; selects pair with highest surplus
    *   Function: `find_best_trade(agent_i, agent_j, exchange_regime)` in `src/vmt_engine/systems/matching.py`
-   **Price Search Algorithm**: Because goods are discrete integers, a price that looks good on paper (based on MRS) might not result in a mutually beneficial trade after rounding. The `find_compensating_block_generic` function solves this:
    *   Probes multiple prices within the valid `[ask_seller, bid_buyer]` range
    *   For each price, scans trade quantities from `ΔA=1` (or `ΔM=1` for money trades) up to `ΔA_max`
    *   Applies **round-half-up** rounding: `ΔB = floor(price * ΔA + 0.5)`
    *   Accepts the **first** trade block `(ΔA, ΔB)` that provides **strict utility improvement (ΔU > 0)** for both agents
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

#### Money System (v1.0 — Phases 1-4 Complete)
-   **Money as Good**: Money holdings (`M`) are stored as integers in minor units (e.g., cents). The `money_scale` parameter converts between whole units and minor units (default: 1 = no conversion).
-   **Exchange Regimes**: The `exchange_regime` parameter controls allowed exchange types:
    *   `"barter_only"` — Only A↔B trades (default, backward compatible with legacy scenarios)
    *   `"money_only"` — Only A↔M and B↔M trades (goods for money)
    *   `"mixed"` — All exchange pairs allowed (Phase 3); uses money-first tie-breaking when multiple pairs have equal surplus
    *   `"mixed_liquidity_gated"` — Mixed with minimum quote depth requirement (future extension)
-   **Quasilinear Utility** (Phases 1-3): U_total = U_goods(A, B) + λ·M, where:
    *   λ (`lambda_money`) is the marginal utility of money (default: 1.0)
    *   M is money holdings in minor units
    *   Phases 1-3 use fixed λ (quasilinear mode); future phases will implement adaptive λ (KKT mode)
-   **Money-First Tie-Breaking** (Phase 3): When multiple trade types offer equal surplus in mixed regimes, the engine uses deterministic three-level sorting:
    1.  **Total surplus** (descending) — Maximizes welfare
    2.  **Pair type priority** (ascending) — Money-first policy:
        *   Priority 0: A↔M (highest — monetary exchange for good A)
        *   Priority 1: B↔M (middle — monetary exchange for good B)
        *   Priority 2: A↔B (lowest — barter)
    3.  **Agent pair ID** `(min_id, max_id)` (ascending) — Deterministic tie-breaker
    *   Rationale: Money trades preferred when surplus equal due to liquidity advantages
    *   Implementation: `TradeSystem._rank_trade_candidates()` in `src/vmt_engine/systems/trading.py`
-   **Mode × Regime Interaction** (Phase 3): Two-layer control architecture:
    *   **Temporal control** (`mode_schedule`): WHEN activities occur (forage/trade/both modes)
    *   **Type control** (`exchange_regime`): WHAT bilateral exchanges are permitted
    *   In forage mode, no trading occurs regardless of regime
    *   In trade/both modes, allowed pairs determined by regime
    *   Method: `Simulation._get_active_exchange_pairs()` combines both controls
-   **Generic Matching**: 
    *   `find_best_trade()` (Phases 1-2): Evaluates allowed pairs, returns first feasible trade
    *   `find_all_feasible_trades()` (Phase 3): Returns ALL feasible trades for ranking in mixed regimes
    *   Each pair uses the same compensating block search as barter
-   **Money Transfers**: Successful money trades update inventories: `buyer.M -= dM`, `seller.M += dM`. Money transfers are recorded in the `trades.dM` telemetry field.
-   **Telemetry Extensions** (Phase 3): The `exchange_pair_type` field logs which pair type was executed ("A<->B", "A<->M", or "B<->M"), enabling analysis of trade type distributions in mixed regimes.
-   **Backward Compatibility**: All money fields default to preserve legacy behavior:
    *   `exchange_regime` defaults to `"barter_only"`
    *   `Inventory.M` defaults to 0
    *   `lambda_money` defaults to 1.0
    *   Legacy scenarios run identically with zero behavioral changes
-   **Phase 4 Deliverables**: Money system v1.0 includes:
    *   Renderer enhancements: money labels, lambda heatmap, mode/regime overlay
    *   Log viewer: Money tab with trade distribution analysis
    *   5 demo scenarios in `scenarios/demos/`
    *   Comprehensive user documentation: [User Guide](../user_guide_money.md), [Regime Comparison](../regime_comparison.md)
    *   Technical reference: [Money Implementation](../technical/money_implementation.md)

---

## 🔬 Testing and Validation

The VMT engine is rigorously tested to ensure both technical correctness and theoretical soundness. The test suite (`tests/`) contains 316+ tests covering:
-   **Core State**: Grid logic, agent creation, state management, pairing state
-   **Utilities**: Correctness of UCES and ULinear calculations, especially at edge cases; money-aware API methods
-   **Reservation Bounds**: Correctness of the zero-inventory guard
-   **Trade Logic**: Correctness of rounding, compensating multi-lot search, cooldowns, and pairing
-   **Generic Matching**: Money-aware matching algorithm, exchange regime parameter, quote computation
-   **Trade Pairing**: Mutual consent pairing, fallback pairing, pairing integrity, cooldown interactions
-   **Resource Claiming**: Claim recording, stale clearing, single-harvester enforcement
-   **Resource Regeneration**: Correctness of cooldowns, growth rates, and caps
-   **Money Integration**: Phase 1 infrastructure, Phase 2 monetary exchange, telemetry extensions
-   **Mode Management**: Mode schedule transitions, exchange regime interactions
-   **Determinism**: End-to-end tests that verify bit-identical log outputs for the same seed
-   **Performance**: Benchmark scenarios validating TPS thresholds with 400 agents

