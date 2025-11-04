# Changelog

All notable changes to the VMT (Visualizing Microeconomic Theory) simulation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed
- **Matching-Bargaining Decoupling Refactor** (2025-11-03): Separated matching from bargaining concerns
  - Decoupled matching protocols from bargaining implementations via abstraction interfaces
  - `BargainingProtocol.negotiate()` now receives agents directly (breaking change)
  - `ProtocolContext` now includes agents dict for matching protocols (breaking change)
  - Eliminated ALL params hacks (both bargaining and matching)
  - Renamed `legacy_compensating_block` protocol to `compensating_block` (reflects actual purpose)
  - Matching protocols now use lightweight heuristics; bargaining protocols use full discovery
  - Benefits: Independent protocol development, cleaner architecture, correct semantic separation

### Added
- `TradePotentialEvaluator` interface for lightweight matching phase evaluation
- `TradeDiscoverer` interface for full trade discovery in bargaining phase
- `QuoteBasedTradeEvaluator`: Default evaluator using quote overlaps (fast heuristic)
- `CompensatingBlockDiscoverer`: Default discoverer implementing VMT's core algorithm
- `TradePotential` and `TradeTuple` NamedTuples for zero-overhead data passing
- Debug immutability assertions in `TradeSystem` (activated via `debug_immutability` param)
- Comprehensive test suite for trade evaluation abstractions

### Removed
- `build_trade_world_view()` function (params hack eliminated)
- `legacy.py` bargaining protocol (replaced by `compensating_block.py`)
- `find_compensating_block_generic()` from `matching.py` (moved to `CompensatingBlockDiscoverer`)
- `find_all_feasible_trades()` from `matching.py` (no longer needed)
- `find_best_trade()` from `matching.py` (no longer needed)
- All `_build_agent_from_world()` adapter methods from bargaining protocols
- All `_build_agent_from_context()` adapter methods from matching protocols

- **Protocol Architecture Restructure** (2025-11-02): Moved protocols to domain-specific modules
  - Search protocols moved from `vmt_engine.protocols.search` to `vmt_engine.agent_based.search`
  - Matching protocols moved from `vmt_engine.protocols.matching` to `vmt_engine.game_theory.matching`
  - Bargaining protocols moved from `vmt_engine.protocols.bargaining` to `vmt_engine.game_theory.bargaining`
  - Effect types remain in `vmt_engine.protocols.base` (unchanged)
  - Registry system remains in `vmt_engine.protocols.registry` (unchanged)
  - YAML scenario files work identically (backward compatible via registry)
  - Import paths now reflect theoretical paradigms (Agent-Based vs Game Theory)
  - Benefits: clearer architecture, better extensibility for future domain-specific modules

- **GUI Framework Migration** (2025-10-22): Migrated from PyQt5 to PyQt6
  - Updated all imports from `PyQt5` to `PyQt6`
  - Updated Qt enum references to use proper namespaces (e.g., `Qt.UserRole` → `Qt.ItemDataRole.UserRole`)
  - Replaced deprecated `exec_()` with `exec()`
  - Updated documentation and requirements.txt

## [Pre-release: Money Track 1 WP3 (quasilinear) - 2025-10-21]

### Added
- Pygame money visualization enhancements (WP3 3A):
  - Money labels `$M` above agents with outline for readability
  - Money transfer sparkles animation on trades
  - Lambda heatmap overlay (toggle: L)
  - Mode/regime information overlay (toggle: I)
  - Keyboard toggle for money labels (M)
- Log Viewer money features (WP3 3B):
  - New “Money” tab with statistics, trade distribution by type, and money trades table
  - Query helpers: money trades, lambda trajectory, mode timeline, distribution by type
  - CSV export includes `inventory_M`, `lambda_money`, `dM`, `buyer_lambda`, `seller_lambda`, and `exchange_pair_type`
- Demo scenarios (WP3 3C):
  - `scenarios/demos/demo_01_simple_money.yaml`
  - `scenarios/demos/demo_02_barter_vs_money.yaml`
  - `scenarios/demos/demo_03_mixed_regime.yaml`
  - `scenarios/demos/demo_04_mode_schedule.yaml`
  - `scenarios/demos/demo_05_liquidity_zones.yaml`
- Launcher improvements:
  - Recursive discovery of scenarios (nested folders under `scenarios/`)

### Documentation
- User Guide: Money System (`docs/user_guide_money.md`)
- Regime Comparison Guide (`docs/regime_comparison.md`)
- Technical Reference: Money Implementation (`docs/technical/money_implementation.md`)
- Core Docs updated (WP3 3E/3F): `docs/2_technical_manual.md`, `docs/4_typing_overview.md`, Quick Reference updates

### Testing Status
- 316 tests passing; 1 warning in quotes filtering when `exchange_regime = "mixed_liquidity_gated"` (falls back to `barter_only` pending Track 2 work)
- E2E runs executed separately on demo scenarios; telemetry verified (DB created, trades recorded where applicable)

### Notes
- This prerelease finalizes Money Track 1 WP3 (renderer, log viewer, demos, documentation). Performance validation is deferred; quality checks are minimized for functional focus.

### Added
- **Trade Pairing System** (2025-10-20): Implemented three-pass pairing algorithm for committed bilateral partnerships
  - Pass 1: Agents build ranked preference lists using distance-discounted surplus (surplus × β^distance)
  - Pass 2: Mutual consent pairing establishes partnerships where both agents list each other as top choice
  - Pass 3: Surplus-based greedy matching assigns highest-surplus unmatched pairs
  - Commitment model: paired agents move toward each other and attempt multiple trades until opportunities exhausted
  - Performance: Reduces trade phase from O(N²) to O(P) where P = paired count
  - New agent state fields: `paired_with_id`, `_preference_list`, `_decision_target_type`
  - New telemetry tables: `pairings` (pair/unpair events), `preferences` (top 3 agent preferences), `decisions.is_paired` flag
  - Comprehensive test suite covering mutual consent, fallback pairing, cooldown interactions, integrity checks
  - See: `docs/tmp/pairing/FINAL_PAIRING.md` for complete design specification

- **Money System Phase 1: Infrastructure** (2025-10-19): Added complete money system infrastructure with zero behavioral impact
  - New schema fields: `exchange_regime`, `money_mode`, `money_scale`, `lambda_money` and related parameters
  - Core state extensions: `Inventory.M` (money in minor units), `Agent.lambda_money`, `Agent.lambda_changed`
  - Telemetry extensions: money columns in all tables, new `tick_states` table (mode+regime per tick), `lambda_updates` table (Phase 3+)
  - Simulation integration: money params added to sim.params dict, tick-level telemetry logging
  - Backward compatibility: all money fields default to preserve legacy behavior (exchange_regime="barter_only", M=0)
  - Performance baseline: 4.7-22.9 TPS with 400 agents (established regression thresholds)
  - Test suite: 15 new tests (78 total passing, 0 skipped)
  - See: `docs/BIG/PHASE1_COMPLETION_SUMMARY.md` for detailed completion report

- **Money System Phase 2: Bilateral Exchange** (2025-10-20): Implemented monetary exchange with quasilinear utility
  - Quasilinear utility: U_total = U_goods(A, B) + λ·M where λ = marginal utility of money
  - Money-aware utility API: `u_goods()`, `mu_A()`, `mu_B()` (canonical); legacy `u()`, `mu()` route through for compatibility
  - Generic matching algorithm: evaluates all allowed exchange pairs (A↔B, A↔M, B↔M) based on exchange_regime
  - Exchange regimes: "barter_only" (default), "money_only", "mixed" (all pairs), "mixed_liquidity_gated" (Phase 3+)
  - Quotes dictionary: `Agent.quotes: dict[str, float]` with keys for all active exchange pairs
  - Generic compensating block search: supports barter and monetary trades with same first-acceptable-trade principle
  - Money transfers: recorded in `trades.dM` telemetry field with exchange pair type
  - Agent quotes now stored as dict (money-aware) instead of Quote dataclass (barter-only)
  - Comprehensive test suite: generic matching, money trades, quote computation, integration scenarios
  - See: `docs/BIG/PHASE2_PR_DESCRIPTION.md` for detailed implementation report

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

### Documentation
- **Comprehensive Documentation Refresh** (2025-10-20): Updated all major documentation files to reflect implemented features
  - Updated `docs/4_typing_overview.md`: Money fields marked [IMPLEMENTED], money-aware Quotes, utility API split, telemetry extensions
  - Updated `src/vmt_engine/README.md`: 7-phase tick details (pairing, claiming, money-aware matching, single-harvester)
  - Updated `docs/2_technical_manual.md`: Expanded tick cycle, trade pairing (3-pass algorithm), money system (Phases 1-2), resource claiming
  - Updated `docs/1_project_overview.md`: Target arrows, smart co-location, resource claiming, money intro, telemetry schema
  - Updated `docs/README.md`: Refreshed hub descriptions with current feature set
  - Updated `docs/BIG/money_SSOT_implementation_plan.md`: Marked Phases 1-2 complete, Phase 3+ planned
  - All docs now accurately reflect 75+ tests, pairing system, money Phases 1-2, and visualization features
  - Created `docs/PLAN_OF_RECORD.md` tracking all documentation updates

### Fixed
- Nothing yet

---

### Summary of Recent Enhancements (2025-10-19 to 2025-10-20)

This release period introduced major economic, coordination, and visualization features:

**Economic Systems:**
1. **Money System Phases 1-2**: Complete infrastructure and bilateral monetary exchange with quasilinear utility
2. **Trade Pairing**: Three-pass algorithm with mutual consent and surplus-based greedy matching

**Coordination & Visualization:**
3. **Resource Claiming System**: Reduces agent clustering through claim-based coordination
4. **Target Arrow Visualization**: Shows agent movement intentions and pairings with color-coded arrows
5. **Smart Co-location Rendering**: Intelligently displays multiple agents on same cell

**Documentation:**
6. **Comprehensive Documentation Refresh**: All docs updated to reflect implemented features (money, pairing, claiming, viz)

**Test Status**: 75+ tests passing (up from 63 baseline, +15 new tests for money/pairing)  
**Performance**: Baseline established at 4.7-22.9 TPS with 400 agents; no regressions detected  
**Backward Compatibility**: All features maintain full backward compatibility (exchange_regime="barter_only" default)

See `docs/BIG/PHASE1_COMPLETION_SUMMARY.md`, `docs/BIG/PHASE2_PR_DESCRIPTION.md`, and `docs/PLAN_OF_RECORD.md` for comprehensive implementation details.

---

## [0.2.1] - 2025-10-17

### Fixed
- Corrected misleading documentation in the GUI Scenario Builder. The text now accurately describes that the "Utility Mix" feature creates a heterogeneous agent population by assigning a single utility function to each agent from a weighted random distribution, rather than creating agents with mixed utility functions. (`src/vmt_launcher/scenario_builder.py`)

### Changed
- Improved and clarified documentation in the user-facing `docs/1_project_overview.md` and the developer-focused `docs/2_technical_manual.md` to formally describe the probabilistic assignment of utility functions.

---

## [0.2.0] - 2025-10-12

### Added - GUI Launcher & Scenario Builder
- **GUI Launcher**: Added a PyQt6-based GUI (`launcher.py`) for browsing, selecting, and running scenarios with a specified seed.
- **Scenario Builder**: Implemented a comprehensive, tabbed GUI dialog for creating and saving custom `.yaml` scenarios from scratch, eliminating the need for manual YAML editing.
- **Input Validation**: Added a robust validator to the scenario builder to provide real-time feedback and prevent the creation of invalid scenarios.
- **In-Context Documentation**: Embedded a rich HTML documentation panel directly into the scenario builder's "Utility Functions" tab to explain economic concepts and parameters.

### Added - SQLite Telemetry System Overhaul
- **Database Backend**: Replaced the entire CSV-based logging system with a SQLite backend.
- **Interactive Log Viewer**: Created a new standalone PyQt6 application (`view_logs.py`) for interactively exploring simulation data. Features include a timeline scrubber, detailed agent state analysis, trade history, and CSV export functionality.
- **Structured Logging**: Implemented multiple log levels (SUMMARY, STANDARD, DEBUG) and a structured database schema to capture detailed information about agent states, trades, decisions, and resources.

### Changed
- **Project Structure**: Refactored the project into a `src/` layout for better organization and scalability.
- **Dependencies**: Added `PyQt6` to `requirements.txt`.
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

