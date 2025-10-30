# VMT Simulation Cycle: A Deep Dive into `Simulation.step()` (Gemini)

This document provides an exhaustive, step-by-step analysis of the VMT simulation's core tick cycle, managed by the `Simulation.step()` method in `src/vmt_engine/simulation.py`. It details the 7-phase execution flow, focusing on the interaction between the main simulation loop, the various systems, and the agent-level protocols.

## Core Architecture: Systems and Protocols

The simulation is not monolithic. Instead of a single, massive `step()` function, the logic is broken down into a series of **Systems**, each responsible for one phase of the tick. In `Simulation.__init__`, these systems are instantiated and ordered correctly:

```python:src/vmt_engine/simulation.py
self.systems = [
    PerceptionSystem(),
    decision_system,
    MovementSystem(),
    trade_system,
    ForageSystem(),
    ResourceRegenerationSystem(),
    HousekeepingSystem(),
]
```

The `step()` method itself is remarkably simple. It iterates through this list and executes each system in order, delegating the logic of each phase to the corresponding system object.

```python:src/vmt_engine/simulation.py
def step(self):
    # ... mode handling ...
    for system in self.systems:
        if self._should_execute_system(system, self.current_mode):
            system.execute(self)
    # ... telemetry logging ...
```

The key architectural pattern is that the `simulation` object (`self`) is passed to each system's `execute` method. This gives the system access to the complete world state (`sim.agents`, `sim.grid`, `sim.rng`, etc.) to perform its function.

**Protocols** are specialized algorithms that define agent *decision-making*. They are not executed directly by the simulation loop. Instead, they are injected as dependencies into the relevant systems (`DecisionSystem` and `TradeSystem`). This keeps the main loop clean and adheres to the "Protocol → Effect → State" pattern.

---

## The 7-Phase Tick Cycle: Step-by-Step

### Phase 1: Perception

*   **System**: `PerceptionSystem`
*   **Purpose**: To provide each agent with a snapshot of its local environment. This is a critical step that ensures all agents make decisions based on the state of the world *at the beginning of the tick*, preventing intra-tick race conditions and ensuring determinism.
*   **Execution Flow**:
    1.  `PerceptionSystem.execute(sim)` is called.
    2.  The system iterates through every agent in `sim.agents`.
    3.  For each agent, it constructs a `WorldView` object. This object is a read-only snapshot containing information the agent is allowed to "see."
    4.  The `WorldView` is populated with:
        *   The agent's own state (inventory, position, utility function).
        *   A list of neighboring agents within its `vision_radius`.
        *   Information about resource patches on the grid within its vision.
        *   Publicly available information like quotes from nearby agents.
    5.  This `WorldView` is then attached to the agent object (e.g., `agent.world_view`). It will be used by the agent in subsequent decision-making phases.

### Phase 2: Decision (Search & Matching Protocols)

*   **System**: `DecisionSystem`
*   **Protocols**: `SearchProtocol`, `MatchingProtocol`
*   **Purpose**: To determine agent intentions for the tick, such as identifying potential trading partners or deciding to forage for resources. This phase generates the initial set of `Effects` that represent desired actions.
*   **Execution Flow**:
    1.  `DecisionSystem.execute(sim)` is called.
    2.  The system's configured `SearchProtocol` is executed.
        *   **Input**: The `SearchProtocol` receives the list of agents, each with their `WorldView` from Phase 1.
        *   **Logic**: The protocol implements the specific logic for how agents identify potential partners. For example, `MyopicSearch` would have agents look for the best immediate trade in their vicinity.
        *   **Output**: The search protocol returns a data structure of "potentials" or "candidates" for each agent.
    3.  The system's configured `MatchingProtocol` is then executed.
        *   **Input**: The `MatchingProtocol` takes the output from the search protocol (the lists of potential matches).
        *   **Logic**: This protocol implements the market-matching algorithm. For instance, `GreedySurplusMatching` would iterate through agents and form pairs that generate the highest mutual surplus, ensuring no agent is paired twice.
        *   **Output**: The protocol generates `PairingEffect`s for agents that have successfully matched for a trade, and potentially `ForageEffect`s for agents that have decided to forage instead.
    4.  These effects are collected by the `DecisionSystem` and applied to the simulation state. For example, a `PairingEffect` sets the `agent.paired_with_id` attribute on the two matched agents.

### Phase 3: Movement

*   **System**: `MovementSystem`
*   **Purpose**: To move agents closer to their intended targets, whether that's a trading partner or a resource patch.
*   **Execution Flow**:
    1.  `MovementSystem.execute(sim)` is called.
    2.  The system iterates through all agents.
    3.  It checks each agent's state to see if they have a movement target.
        *   If an agent is paired (`agent.paired_with_id is not None`), their target is the position of their partner.
        *   If an agent is committed to foraging (`agent.is_foraging_committed`), their target is the resource location.
    4.  For agents with a target, the system calculates the path and generates `MoveEffect`s, respecting the agent's `move_budget_per_tick`.
    5.  The `MovementSystem` validates these effects (e.g., ensuring moves are within grid bounds) and then applies them by updating each agent's `pos` attribute and updating the `SpatialIndex` for the new positions.

### Phase 4: Trade (Bargaining Protocol)

*   **System**: `TradeSystem`
*   **Protocol**: `BargainingProtocol`
*   **Purpose**: For paired agents that are within interaction range to negotiate and execute trades.
*   **Execution Flow**:
    1.  `TradeSystem.execute(sim)` is called.
    2.  The system identifies all pairs of agents where `a.paired_with_id == b.id` and `b.paired_with_id == a.id`.
    3.  For each pair, it checks if they are within `interaction_radius` of each other.
    4.  If they are in range, the system invokes the configured `BargainingProtocol`.
        *   **Input**: The protocol receives the two paired agents (and their `WorldView`s).
        *   **Logic**: The protocol contains the economic logic for negotiation. For example, a Nash bargaining protocol would find the trade that maximizes the product of their utility gains. An Edgeworth Box protocol would find a trade on the contract curve.
        *   **Output**: If a trade is agreed upon, the protocol returns a `TradeEffect`.
    5.  The `TradeSystem` receives the `TradeEffect` and validates it (e.g., ensuring agents have sufficient inventory).
    6.  If valid, the system applies the effect by modifying the inventories of the two agents involved. It also logs the trade event to telemetry.
    7.  After the trade (or failed attempt), the agents are unpaired.

### Phase 5: Foraging

*   **System**: `ForageSystem`
*   **Purpose**: To allow agents to harvest resources from the grid.
*   **Execution Flow**:
    1.  `ForageSystem.execute(sim)` is called.
    2.  The system iterates through all agents that are committed to foraging (`agent.is_foraging_committed`).
    3.  It checks if the agent is at their target resource location.
    4.  If the agent is at the correct location, the system generates a `ForageEffect`.
    5.  The system validates and applies the effect, which involves:
        *   Decreasing the resource amount at that grid cell.
        *   Increasing the agent's inventory of that resource.
        *   Logging the foraging event to telemetry.

### Phase 6: Resource Regeneration

*   **System**: `ResourceRegenerationSystem`
*   **Purpose**: To handle the natural growth of resources on the grid over time.
*   **Execution Flow**:
    1.  `ResourceRegenerationSystem.execute(sim)` is called.
    2.  The system iterates through all resource cells in `sim.grid`.
    3.  It applies the scenario's configured growth logic (e.g., increasing the resource amount by `resource_growth_rate` up to `resource_max_amount`). This process is independent of agent actions.

### Phase 7: Housekeeping

*   **System**: `HousekeepingSystem`
*   **Purpose**: To perform end-of-tick cleanup and state updates.
*   **Execution Flow**:
    1.  `HousekeepingSystem.execute(sim)` is called.
    2.  The system performs several cleanup tasks:
        *   **Quote Updates**: It recalculates the buy/sell quotes for any agent whose inventory changed during the tick. This is vital for the accuracy of the next tick's Perception phase.
        *   **Cooldowns**: It decrements any active cooldowns on agents (e.g., trade cooldowns).
        *   **State Resets**: It resets transient per-tick flags on agents (e.g., `inventory_changed`).
    3.  **Telemetry Logging**: While the main `step()` loop calls the primary `telemetry.log_tick_state`, this phase could be extended to log more detailed end-of-tick agent states if needed.
