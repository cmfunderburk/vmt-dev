# Changelog

All notable changes to the VMT (Visualizing Microeconomic Theory) simulation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

### Fixed
- Nothing yet

---

## [0.2.1] - 2025-10-17

### Fixed
- Corrected misleading documentation in the GUI Scenario Builder. The text now accurately describes that the "Utility Mix" feature creates a heterogeneous agent population by assigning a single utility function to each agent from a weighted random distribution, rather than creating agents with mixed utility functions. (`src/vmt_launcher/scenario_builder.py`)

### Changed
- Improved and clarified documentation in the user-facing `docs/1_project_overview.md` and the developer-focused `docs/2_technical_manual.md` to formally describe the probabilistic assignment of utility functions.

---

## [0.2.0] - 2025-10-12

### Added - GUI Launcher & Scenario Builder
- **GUI Launcher**: Added a PyQt5-based GUI (`launcher.py`) for browsing, selecting, and running scenarios with a specified seed.
- **Scenario Builder**: Implemented a comprehensive, tabbed GUI dialog for creating and saving custom `.yaml` scenarios from scratch, eliminating the need for manual YAML editing.
- **Input Validation**: Added a robust validator to the scenario builder to provide real-time feedback and prevent the creation of invalid scenarios.
- **In-Context Documentation**: Embedded a rich HTML documentation panel directly into the scenario builder's "Utility Functions" tab to explain economic concepts and parameters.

### Added - SQLite Telemetry System Overhaul
- **Database Backend**: Replaced the entire CSV-based logging system with a SQLite backend.
- **Interactive Log Viewer**: Created a new standalone PyQt5 application (`view_logs.py`) for interactively exploring simulation data. Features include a timeline scrubber, detailed agent state analysis, trade history, and CSV export functionality.
- **Structured Logging**: Implemented multiple log levels (SUMMARY, STANDARD, DEBUG) and a structured database schema to capture detailed information about agent states, trades, decisions, and resources.

### Changed
- **Project Structure**: Refactored the project into a `src/` layout for better organization and scalability.
- **Dependencies**: Added `PyQt5` to `requirements.txt`.
- **Documentation**: Overhauled the `docs/` folder, consolidating planning documents and creating the `1_project_overview.md`, `2_technical_manual.md`, and `3_strategic_roadmap.md` as the new single sources of truth.

---

## [0.1.0] - 2025-10-11

### Added - Core Simulation Engine
- **Agent-Based Model**: Initial implementation of a spatial agent-based simulation on a 2D grid.
- **Economic Utility**: Core economic modeling with CES (Constant Elasticity of Substitution) and Linear utility functions.
- **Barter Trading System**: Agents can engage in bilateral barter. Implemented a sophisticated price search algorithm to find mutually beneficial integer block trades (`ΔU > 0` for both parties).
- **Reservation Pricing**: Agent quotes (bids/asks) are derived from true reservation prices based on their Marginal Rate of Substitution (MRS), with a "zero-inventory guard" for robustness.
- **Behavioral Systems**: Implemented core agent behaviors including distance-discounted foraging, resource regeneration with cooldowns, and a trade cooldown system to prevent futile negotiations.
- **Determinism**: Ensured the simulation is fully deterministic; a given scenario and seed will always produce identical outcomes.
- **Initial Telemetry**: Created the first-generation telemetry system, logging simulation data to a set of CSV files (`trades.csv`, `agent_snapshots.csv`, etc.).
- **Visualization**: Implemented a real-time `Pygame` visualization window with interactive controls (pause, step, reset, quit).
- **Configuration**: Scenarios are defined via flexible `YAML` configuration files.
- **Testing**: Established a comprehensive test suite with over 45 tests covering all core systems.

---

