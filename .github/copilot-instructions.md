# VMT-Dev Copilot Instructions

This document provides guidance for AI agents working on the Visualizing Microeconomic Theory (VMT) codebase.

## Overall Architecture

The project is a deterministic agent-based simulation of economic principles. The core logic is in `src/vmt_engine/`.

-   **Simulation Core**: `src/vmt_engine/simulation.py` orchestrates the simulation tick by tick. `src/vmt_engine/core/state.py` holds the simulation state, including agents and the grid.
-   **Agent Behavior**: Agent actions are divided into systems within `src/vmt_engine/systems/`. These systems are executed in a fixed order during each simulation tick.
-   **Economic Model**: Economic logic, including utility functions (`UCES`, `ULinear`), is defined in `src/vmt_engine/econ/`.
-   **Scenarios**: Simulation setups are defined in YAML files in `scenarios/`. See `src/scenarios/schema.py` for the structure.
-   **Data Logging**: The primary logging mechanism uses SQLite (`src/telemetry/database.py`, `src/telemetry/db_loggers.py`). Logs are stored in `logs/telemetry.db`. A PyQt5-based viewer is available in `view_logs.py`.

## Determinism and Tick Order

Determinism is critical. All randomness is controlled by a central RNG in `src/vmt_engine/simulation.py`.

The simulation proceeds in a fixed 7-phase tick order. When modifying or adding behavior, respect this order:
1.  Perception (`src/vmt_engine/systems/perception.py`)
2.  Decision
3.  Movement (`src/vmt_engine/systems/movement.py`)
4.  Trade (`src/vmt_engine/systems/matching.py`)
5.  Forage (`src/vmt_engine/systems/foraging.py`)
6.  Resource Regeneration
7.  Housekeeping

Always iterate over agents by their ID (`agent.id`) and trade pairs by `(min_id, max_id)` to ensure deterministic outcomes.

## Economic Logic and Trading

-   **Utility Functions**: Use the factory `create_utility(type, params)` instead of instantiating `UCES` or `ULinear` directly.
-   **Reservation Prices**: Do not calculate Marginal Rate of Substitution (MRS) directly. Use `reservation_bounds_A_in_B(A, B, eps)` from `src/vmt_engine/econ/utility.py` to get reservation prices. This handles edge cases like zero inventory correctly.
-   **Quotes**: Quotes are derived from reservation prices with a spread. See `src/vmt_engine/systems/quotes.py`. Quotes must be refreshed after any inventory change.
-   **Trading**: A single trade can occur per agent pair per tick. The process involves finding surplus overlaps, price searching, and executing one feasible trade. See `src/vmt_engine/systems/matching.py`. Note the round-half-up rule for quantity calculations: `floor(p*ΔA + 0.5)`.

## Developer Workflow

-   **Setup**: `pip install -r requirements.txt`
-   **Testing**: Run tests with `pytest -v`. Key tests for core mechanics are in `tests/`. It's important to add tests for any new economic logic.
-   **Running Simulations**:
    -   CLI: `python main.py scenarios/three_agent_barter.yaml 42`
    -   GUI: `python launcher.py`

## Key Files & Directories

-   `src/vmt_engine/simulation.py`: Main simulation loop and tick orchestrator.
-   `src/vmt_engine/core/state.py`: Central simulation state.
-   `src/vmt_engine/systems/`: Directory containing agent behavior logic for each tick phase.
-   `src/vmt_engine/econ/utility.py`: Utility functions and reservation price logic.
-   `scenarios/schema.py`: Defines the structure of scenario files.
-   `docs/archive/Planning-Post-v1.md`: The authoritative spec for simulation behavior.
