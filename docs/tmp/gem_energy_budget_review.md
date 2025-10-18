# Agent Energy Budgets and Rest Cycles: A Design Proposal

## 1. Overview

This document outlines a proposed "energy budget" system for agents within the VMT simulation. The core idea is to introduce a resource, "energy," that agents expend to perform actions and must replenish by resting. This creates a sleep/wake cycle dynamic, forcing agents to balance immediate economic goals (trading, foraging) with the long-term necessity of managing their energy.

The fundamental mechanics are as follows:
- Agents have a maximum energy capacity (e.g., 24 units).
- Each simulation tick, an active agent expends 1 unit of energy.
- When an agent's energy is depleted, they enter a "seeking rest" state. Their primary goal becomes returning to a designated "home" location.
- If an agent has no home, they must find a suitable unoccupied location and claim it.
- Once at their home, agents enter a "resting" state, during which they cannot perform other actions but regenerate energy at an accelerated rate (e.g., 3 units per tick).
- When energy is fully restored, the agent returns to an "active" state and resumes normal economic behavior.

## 2. Proposed Implementation Details

Integrating this system requires modifications to the agent's state, the core simulation loop, and several key systems.

### 2.1. Agent State Modifications

The `Agent` class in `vmt_engine/core/agent.py` will require the following new attributes:

- `energy: int`: The agent's current energy level.
- `max_energy: int`: The maximum energy capacity.
- `energy_regen_rate: int`: The amount of energy regained per tick while resting.
- `agent_status: Enum`: An enumerator to track the agent's current state. Values could be `ACTIVE`, `SEEKING_HOME`, `RESTING`.
- `home_x: Optional[int]`: The x-coordinate of the agent's home base. `None` if homeless.
- `home_y: Optional[int]`: The y-coordinate of the agent's home base. `None` if homeless.

### 2.2. System and Tick-Phase Modifications

The strict 7-phase tick order must be preserved. The energy mechanic would be integrated as follows:

1.  **Perception**: No changes required. An agent's perception is independent of its energy state.

2.  **Decision**: This phase will see the most significant changes. The agent's decision-making logic will be predicated on its `agent_status`:
    - **If `status == ACTIVE`**: Normal decision logic applies (e.g., evaluate foraging vs. trading opportunities).
    - **If `status == SEEKING_HOME`**: All other goals are suppressed. The agent's sole objective is to generate a movement plan towards its `(home_x, home_y)` coordinates. If the agent is homeless (`home_x is None`), its goal becomes claiming a home.
    - **If `status == RESTING`**: The agent makes no decisions and generates no new actions.

3.  **Movement**: The movement system will execute the plans generated in the decision phase. For an agent in the `SEEKING_HOME` state, this means executing a step towards its home location.

4.  **Trade / 5. Forage**: These systems must be modified to ignore agents that are not in the `ACTIVE` state. Resting or home-seeking agents cannot initiate or respond to trades, nor can they forage.

6.  **Resource Regeneration**: No changes required. This system is environmental, not agent-specific.

7.  **Housekeeping**: This phase is the natural place for all energy accounting:
    - For each agent, check its `agent_status`.
    - **If `status == RESTING`**:
        - Increase `agent.energy` by `agent.energy_regen_rate`, capped at `agent.max_energy`.
        - If `agent.energy == agent.max_energy`, change status to `ACTIVE`.
    - **If `status != RESTING`** (i.e., `ACTIVE` or `SEEKING_HOME`):
        - Decrease `agent.energy` by 1.
        - If `agent.energy == 0`, change status to `SEEKING_HOME`.

### 2.3. "Claiming a Home" Algorithm

For homeless agents, a deterministic algorithm is required to find and claim a home. When an agent's energy depletes and `home_x is None`:

1.  The agent scans for the nearest "unoccupied" grid cell. An unoccupied cell is one with no other agent present.
2.  The search must be deterministic. A suggested method is to search in an expanding square pattern around the agent's current location, checking cells in a fixed order (e.g., N, E, S, W, NE, SE, SW, NW) at each distance `d=1, 2, 3...`.
3.  The first valid, unoccupied cell found is chosen.
4.  The agent's `home_x`, `home_y` are set to the coordinates of this cell.
5.  The agent's movement goal becomes pathing to this newly claimed home. Once it arrives, its status changes to `RESTING`.

### 2.4. Configuration

The following parameters should be added to the scenario schema (`scenarios/schema.py`) to allow for configurability, with defaults that can disable the system if omitted.

- `defaults.agent.max_energy: int` (default: 24)
- `defaults.agent.energy_regen_rate: int` (default: 3)
- `simulation.tick_energy_cost: int` (default: 1)
- `simulation.energy_system_enabled: bool` (default: `False`)

## 3. Pros and Cons Analysis

### Pros

-   **Emergent Spatial Dynamics**: The need to return to a "home" base will naturally lead to more complex and potentially more realistic spatial patterns, such as central place foraging.
-   **New Strategic Layer**: Agents face a new optimization problem: balancing the immediate utility of economic activity against the future cost of having to travel and rest. This introduces a significant opportunity cost to all actions.
-   **Increased Realism**: The cycle of activity and rest is a fundamental constraint for most biological and human agents, making the simulation a richer analogy for real-world economic systems.
-   **Endogenous Constraints**: Unlike fixed parameters like `vision_radius`, the energy budget is a dynamic constraint that is affected by the agent's own choices, creating a tighter feedback loop between strategy and outcome.

### Cons

-   **Increased Complexity**: The agent state machine becomes more complex, increasing the potential for bugs and difficult-to-predict edge cases.
-   **Potential for Deadlocks**: What happens if an agent is physically trapped and cannot reach its home? Or if all nearby squares are occupied, preventing a homeless agent from claiming one? Fallback behaviors (e.g., resting in place at a reduced rate) would be necessary.
-   **Performance Overhead**: The additional logic in the decision and housekeeping phases for every agent on every tick could impact simulation performance, especially with a large number of agents.
-   **Scenario Compatibility**: Existing scenarios are not designed with this constraint in mind and may produce unintended or uninteresting results without re-tuning. The system should be disabled by default to maintain backward compatibility.

## 4. Pedagogical and Research Value

### Pedagogical Value

-   **Opportunity Cost**: This system provides a visceral, visual demonstration of opportunity cost. The time an agent spends traveling home and resting is time it *cannot* spend foraging or trading.
-   **Planning and Time Horizons**: It forces a consideration of long-term planning. Agents that stray too far from home risk being caught with low energy, illustrating the trade-off between exploration and exploitation.
-   **Behavioral Ecology Concepts**: It allows for the direct simulation of concepts from biology and ecology, such as central place foraging theory, territoriality, and the value of a secure home base.

### Research Value

-   **Emergence of Settlements**: This mechanic could be a primitive driver for the formation of "settlements" or "markets" as agents establish homes near each other or near valuable resources.
-   **Property Rights**: The "claiming" of a home square is a form of proto-property right. It could be extended to study how such claims are established, respected, or contested by other agents.
-   **Labor/Leisure Choice**: The decision to work (forage/trade) versus rest is a classic economic problem. This system provides an embodied, spatially-explicit model for studying that choice.
-   **State-Dependent Risk Preferences**: The energy level can be used as a state variable to influence other behaviors. For example, an agent with low energy might become more risk-averse in trading, or conversely, more desperate, accepting worse prices to acquire a needed good before being forced to rest. This opens up avenues for more complex, state-dependent agent strategies.
