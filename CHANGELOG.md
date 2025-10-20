# Changelog

All notable changes to the VMT (Visualizing Microeconomic Theory) simulation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Target Arrow Visualization** (2025-10-20): Implemented visual indicators for agent movement intentions in Pygame renderer
  - Color-coded arrows show agent targets: green for trade targets (agent pursuing another agent), orange for forage targets (agent pursuing resources)
  - Red borders highlight idle agents (no target)
  - Keyboard toggle controls: T (trade arrows), F (forage arrows), A (all on), O (all off)
  - HUD status display shows current arrow mode: "Arrows: OFF", "Arrows: Trade", "Arrows: Forage", or "Arrows: Trade+Forage"
  - Performance: O(N) rendering with viewport culling for large grids
  - Default state: arrows disabled for clean initial view
  - Arrow rendering methods: `draw_arrow()`, `draw_target_arrows()`, `draw_idle_agent_borders()`
  - Helps visualize agent decision-making and coordination dynamics
  - Implementation: `src/vmt_pygame/renderer.py` (arrow rendering), `main.py` (keyboard controls)
  - See: `docs/tmp/target_arrows_brainstorm.md` for design exploration, `docs/tmp/target_arrows_implementation.md` for implementation summary

- **Resource Claiming System** (2025-10-20): Implemented resource claiming mechanism to reduce inefficient agent clustering at resource cells
  - Agents claim resources during Decision phase (Phase 2), preventing other agents from targeting the same resource
  - Claims expire when agent reaches resource or changes target
  - Single-harvester enforcement: only one agent per resource cell can harvest per tick (deterministic by agent ID)
  - Both features enabled by default: `enable_resource_claiming: true` and `enforce_single_harvester: true`
  - Telemetry integration: `claimed_resource_pos` column added to `decisions` table
  - Performance: O(N*R) complexity - same as existing system, no asymptotic change
  - Comprehensive test suite: `tests/test_resource_claiming.py` with 9 tests covering claiming, expiration, single-harvester, and clustering reduction
  - Demo scenario: `scenarios/resource_claiming_demo.yaml` with 6 agents showcasing reduced clustering
  - Configuration flags in `ScenarioParams`: agents can disable features for comparison studies
  - Determinism preserved: claims processed in agent ID order, single-harvester by lowest ID

- **Smart Co-location Rendering** (2025-10-19): Enhanced Pygame renderer to intelligently handle multiple agents on the same grid cell
  - When agents co-locate, sprites automatically scale down proportionally (2 agents = 75% size, 3 = 60%, 4 = 50%, etc.)
  - Uses non-overlapping geometric layouts: diagonal (2 agents), triangle (3 agents), corners (4 agents), circle pack (5+ agents)
  - Inventory labels organize automatically: single label for 1 agent, stacked labels for 2-3 agents, summary label for 4+ agents
  - Pure visualization enhancement - simulation positions remain accurate in telemetry database
  - Deterministic rendering: agents sorted by ID within each co-located group
  - New test suite: `tests/test_renderer_colocation.py` with 8 tests covering geometric layouts and scaling
  - Demo scenario: `scenarios/visual_clarity_demo.yaml` demonstrating the feature
  - See: `docs/tmp/renderer_decolocation.md` for full design documentation

### Removed - BREAKING CHANGE
- **Summary Logging Level Removed** (2025-10-19): Removed `LogLevel.SUMMARY` and `LogConfig.summary()` from telemetry system based on performance benchmark evidence showing minimal benefit (<3% in exchange scenarios) while removing valuable decision data.
  - **Breaking**: Code using `LogConfig.summary()` will raise `AttributeError`
  - **Breaking**: Code using `LogLevel.SUMMARY` will raise `AttributeError`
  - **Breaking**: CLI argument `--log-level summary` will raise `argparse` error
  - **Migration**: Replace all `LogConfig.summary()` with `LogConfig.standard()`
  - **Rationale**: Performance benchmarks showed summary logging (4.0 TPS) was actually slower than standard logging (4.1 TPS) in exchange scenarios. Trade logging dominates overhead regardless of level. Comprehensive logging is vital for pedagogical and research use.
  - **Remaining levels**: STANDARD (default, comprehensive production logging) and DEBUG (adds failed trade attempt logging)
  - **See**: `docs/PLAN_remove_summary_logging.md` for full implementation details

### Removed
- **Unused CSV Config Fields** (2025-10-19): Removed `export_csv` and `csv_dir` fields from `LogConfig` dataclass in `src/telemetry/config.py`
  - **Non-breaking**: These fields were never used in the codebase; they were placeholders for automatic CSV export during simulation
  - **Note**: CSV export functionality remains available via the log viewer GUI (`src/vmt_log_viewer/csv_export.py`)
  - **Rationale**: Simplifies configuration by removing dead code; automatic CSV export during simulation is not currently a planned feature

### Changed
- **Telemetry Configuration Simplified** (2025-10-19): `LogLevel` enum renumbered (STANDARD=1, DEBUG=2) and `__post_init__` logic simplified to only handle DEBUG level configuration

### Fixed
- Nothing yet

---

### Summary of Recent Enhancements (2025-10-19 to 2025-10-20)

This release period introduced three major visualization and coordination features:
1. **Target Arrow Visualization**: Shows agent movement intentions with color-coded arrows
2. **Resource Claiming System**: Reduces agent clustering through coordination mechanism
3. **Smart Co-location Rendering**: Intelligently displays multiple agents on same cell

**Test Status**: 169/169 passing (up from 152, +17 new tests)  
**Performance**: No regressions detected, all features maintain O(N) complexity  
**Backward Compatibility**: All features either opt-in or automatic enhancements

See `docs/IMPLEMENTATION_REVIEW_2025-10-20.md` for comprehensive review.

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

