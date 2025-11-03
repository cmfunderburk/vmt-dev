# VMT Project - AI Agent Instructions

This document provides essential guidance for contributing to the VMT (Visualizing Microeconomic Theory) codebase. Adhering to these conventions is critical for maintaining the project's integrity, especially its deterministic nature.

## 1. Core Architecture: `Protocol → Effect → State`

The entire simulation is built on a declarative, functional pattern. Understand this before writing any code.

- **Protocols**: These are swappable "institutional rules" that define agent behavior (e.g., how to search for partners, how to bargain). They are pure functions that read the world state and decide on actions. You'll find them organized by domain:
  - `src/vmt_engine/agent_based/search/`
  - `src/vmt_engine/game_theory/matching/`
  - `src/vmt_engine/game_theory/bargaining/`
- **Effects**: Protocols do **not** change the world state directly. Instead, they return a list of `Effect` objects (e.g., `MoveEffect`, `TradeEffect`, `PairEffect`). These are simple data structures that declare an intended change.
- **State**: Systems in `src/vmt_engine/systems/` are responsible for iterating through agents, executing the appropriate protocol to get `Effects`, and then applying those effects to the simulation state.

**Example Flow**:
1. `DecisionSystem` executes the `MyopicSearch` protocol for an agent.
2. `MyopicSearch` analyzes the `WorldView` and returns `[MoveEffect(agent_id=1, new_pos=(10, 12))]`.
3. `MovementSystem` later receives this effect and updates the agent's position in the main state.

**Your Task**: When implementing logic, think in terms of "what decision (Effect) should be produced?" not "how do I change the agent's state?".

## 2. The 7-Phase Tick Cycle

Every simulation step (`tick`) follows a strict, immutable 7-phase cycle. Logic must operate only within its designated phase to ensure correctness.

1.  **Perception**: Build read-only `WorldView` snapshots for agents.
2.  **Decision**: Agents use protocols to choose targets and form pairs.
3.  **Movement**: Apply `MoveEffect`s.
4.  **Trade**: Paired agents execute bargaining protocols to attempt trades.
5.  **Foraging**: Unpaired agents gather resources.
6.  **Regeneration**: Resources on the grid respawn.
7.  **Housekeeping**: Update agent quotes, log data, and perform cleanup.

Refer to `src/vmt_engine/systems/` to see how each phase is implemented. Do not introduce logic that violates this phase separation.

## 3. Developer Workflow

### Setup & Running
- **Virtual Environment**: ALWAYS work within the Python virtual environment.
  ```bash
  # Set up once
  python3 -m venv venv
  pip install -r requirements.txt

  # Activate for each session
  source venv/bin/activate
  ```
- **Run GUI**: `python launcher.py`
- **Run Headless**: `python main.py scenarios/demos/minimal_2agent.yaml`

### Testing
- **Framework**: We use `pytest`. Run the suite with the `pytest` command.
- **Determinism is CRITICAL**: Every new feature or protocol **must** have a determinism test. This involves running the simulation twice with the same seed and asserting that the final states are identical. See `tests/test_simulation_init.py` for examples.
- **Test Scenarios**: Use `tests.helpers.scenarios.create_minimal_scenario()` to build scenarios for unit tests. For integration tests, use dedicated files in `scenarios/test/`.

### Debugging
- **Telemetry Database**: The primary debugging tool is the SQLite database at `logs/telemetry.db`. It contains detailed, tick-by-tick logs of agent state, trades, pairings, and more.
- **Log Viewer**: Use `python view_logs.py` to get a GUI for exploring the telemetry database. This is the fastest way to understand why a simulation behaved unexpectedly.

## 4. Key Conventions

### Protocol Development
- **Template**: Follow the template in `docs/planning_thinking_etc/BIGGEST_PICTURE/opus_plan/implementation/COMPREHENSIVE_IMPLEMENTATION_PLAN.md`. Protocols must inherit from a base class, implement the `execute` method, and be stateless.
- **Registration**: New protocols must be decorated with `@register_protocol` and imported into their module's `__init__.py` to be available in YAML scenarios.
- **Randomness**: Never use Python's global `random` module. For deterministic results, use the seeded random number generator provided in the `ProtocolContext`, e.g., `context.world_view.random.choice()`.

### Scenario Configuration
- Simulations are configured entirely through YAML files in `scenarios/`.
- Before creating a new scenario, review the existing examples in `scenarios/demos/` and the comprehensive template in `docs/structures/comprehensive_scenario_template.yaml`.
- You can mix and match protocols to compare how different "institutions" affect market outcomes.

### Economic Logic
- The project simulates a **pure barter economy**. Agents have utility functions (CES, Linear, etc.) defined in `src/vmt_engine/econ/`.
- Before implementing any economic logic, consult `docs/planning_thinking_etc/BIGGEST_PICTURE/opus_plan/implementation/COMPREHENSIVE_IMPLEMENTATION_PLAN.md` to understand concepts like Marginal Rate of Substitution (MRS), reservation prices, and surplus as they are implemented in this codebase.
- **Core Principle**: Agents act based on maximizing their utility. An agent will never accept a trade that lowers its utility.
