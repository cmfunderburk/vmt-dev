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
2.  **Decision**: Based on the perception snapshot, each agent decides on its action for the tick. This involves either selecting a trading partner based on the highest potential surplus or choosing a foraging target based on a distance-discounted utility calculation. When an agent selects a foraging target, it **claims** that resource to prevent other agents from targeting it (if `enable_resource_claiming=True`).
3.  **Movement**: Agents move towards their chosen targets (either another agent or a resource cell) according to their `move_budget_per_tick`. Movement is deterministic, following specific tie-breaking rules.
4.  **Trade**: Agents who are within `interaction_radius` and have mutually agreed to trade execute their exchange. The engine uses a sophisticated price search algorithm to find mutually beneficial terms. At most **one trade per pair** is executed per tick.
5.  **Foraging**: Agents located on a resource cell harvest that resource, increasing their inventory. The amount harvested is limited by the `forage_rate`. If `enforce_single_harvester=True`, only one agent per resource cell can harvest per tick (determined by lowest `agent.id`).
6.  **Resource Regeneration**: Resource cells that have been harvested regenerate over time. A cell must wait `resource_regen_cooldown` ticks before it can begin regenerating at a rate of `resource_growth_rate` per tick.
7.  **Housekeeping**: The tick concludes with cleanup and maintenance tasks. Agents refresh their trade quotes based on their new inventory levels, and the telemetry system logs all data for the tick to the database.

---

## ⚙️ Key Systems & Design Principles

### Determinism and Reproducibility

Determinism is the cornerstone of the VMT engine. Given the same scenario file and the same seed, the simulation will produce the exact same outcome every single time. This is achieved through several strict rules:

-   **Fixed Tick Order**: The 7-phase cycle never changes.
-   **Sorted Iteration**: All loops over agents are sorted by `agent.id`. All loops over potential trade pairs are sorted by `(min_id, max_id)`. There is no reliance on non-deterministic data structures like Python dictionaries for iteration.
-   **Deterministic Tie-Breaking**: Any situation that could be ambiguous is resolved with a fixed rule. For example, when choosing a movement path, agents prefer reducing distance on the x-axis before the y-axis, and prefer negative directions on ties.

### Economic Logic

#### Utility and Reservation Prices
-   **Utility Functions**: The engine supports `UCES` (Constant Elasticity of Substitution, including the Cobb-Douglas case) and `ULinear` (perfect substitutes) utility functions, defined in `src/vmt_engine/econ/utility.py`.
-   **Reservation Bounds**: Agents' willingness to trade is determined by their reservation price, which is derived from their marginal rate of substitution (MRS). To avoid hard-coding MRS formulas, the engine uses a generic `reservation_bounds_A_in_B(A, B, eps)` function. This returns the minimum price an agent would accept (`p_min`) and the maximum price they would pay (`p_max`).
-   **Zero-Inventory Guard**: A critical innovation is the handling of zero-inventory cases for CES utilities. When an agent has zero of a good, its MRS can be undefined or infinite. The engine handles this by adding a tiny `epsilon` value to the inventory levels *only for the ratio calculation* used to determine reservation bounds. The core utility calculation `u(A, B)` always uses the true integer inventories.

#### Agent Initialization and Heterogeneity
Agents are not required to be homogeneous. The `scenarios/*.yaml` format allows for specifying a distribution of preferences across the agent population.

-   **Utility Mix**: The `utilities.mix` section of a scenario file defines a list of one or more utility function configurations, each with a `type`, `params`, and a `weight`. The weights must sum to 1.0.
-   **Probabilistic Assignment**: During simulation setup, each agent's utility function is independently chosen from this list via weighted random sampling (`numpy.random.Generator.choice`). This means that a scenario can define, for example, a population composed of 80% CES agents and 20% Linear agents, each with their own specific parameters. An agent is assigned exactly one utility function.
-   **Initial Inventories**: Initial inventories can also be heterogeneous, specified either as a single value (all agents start the same) or as an explicit list of values, one for each agent.
    
#### Quotes and Trading
-   **Quotes**: An agent's broadcasted `ask` and `bid` prices are calculated from their reservation bounds: `ask = p_min * (1 + spread)` and `bid = p_max * (1 - spread)`.
-   **Partner Selection**: An agent `i` chooses a partner `j` by evaluating the potential surplus from a trade. The surplus is the overlap between `i`'s bid and `j`'s ask (or vice-versa). The agent targets the partner with the highest positive surplus.
-   **Price Search Algorithm**: Because goods are discrete integers, a price that looks good on paper (based on MRS) might not result in a mutually beneficial trade after rounding. The `find_compensating_block` function in `src/vmt_engine/systems/matching.py` solves this. It probes multiple prices within the valid `[ask_seller, bid_buyer]` range and, for each price, scans trade quantities from `ΔA=1` up to `ΔA_max`. It accepts the first trade block `(ΔA, ΔB)` that provides a **strict utility improvement (ΔU > 0)** for both agents.
-   **Rounding**: All quantity calculations use **round-half-up** (`floor(p * ΔA + 0.5)`) for consistency.

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

---

## 🔬 Testing and Validation

The VMT engine is rigorously tested to ensure both technical correctness and theoretical soundness. The test suite (`tests/`) contains over 55 tests covering:
-   **Core State**: Grid logic, agent creation, state management.
-   **Utilities**: Correctness of UCES and ULinear calculations, especially at edge cases.
-   **Reservation Bounds**: Correctness of the zero-inventory guard.
-   **Trade Logic**: Correctness of rounding, compensating multi-lot search, and cooldowns.
-   **Resource Regeneration**: Correctness of cooldowns, growth rates, and caps.
-   **Determinism**: End-to-end tests that verify bit-identical log outputs for the same seed.

