# VMT Code Review Guide

**Purpose:** This guide provides a comprehensive directory-by-directory overview of the VMT codebase, with emphasis on how each component relates to the main simulation engine (`vmt_engine/simulation.py`).

**Target Audience:** Developers conducting thorough code review, onboarding to the project, or understanding architectural relationships.

**Last Updated:** 2025-10-23

---

## Table of Contents

1. [Core Architecture Overview](#core-architecture-overview)
2. [src/vmt_engine/](#srcvmt_engine) - **Main Simulation Engine**
3. [src/scenarios/](#srcscenarios) - Scenario Loading & Schema
4. [src/telemetry/](#srctelemetry) - Database Logging System
5. [src/vmt_pygame/](#srcvmt_pygame) - Pygame Visualization
6. [src/vmt_launcher/](#srcvmt_launcher) - PyQt6 GUI Application
7. [src/vmt_log_viewer/](#srcvmt_log_viewer) - Telemetry Analysis GUI
8. [src/vmt_tools/](#srcvmt_tools) - Scenario Generation Tools

---

## Core Architecture Overview

The VMT simulation engine follows a **7-phase tick cycle** orchestrated by `simulation.py`:

```
TICK N:
  1. Perception     → agents observe environment
  2. Decision       → agents choose targets (3-pass pairing algorithm)
  3. Movement       → agents move toward targets
  4. Trade          → paired agents execute trades
  5. Forage         → unpaired agents harvest resources
  6. Regeneration   → depleted resources regenerate
  7. Housekeeping   → quotes refresh, telemetry logged
```

**Key Principles:**
- **Determinism:** All operations sorted by agent ID, fixed tie-breaking
- **Phase Ordering:** Never change the 7-phase sequence (critical for reproducibility)
- **Separation of Concerns:** Each phase is a separate System class
- **Money-Aware Architecture:** Supports barter, monetary, and mixed exchange regimes

---

## src/vmt_engine/

**Purpose:** Core simulation engine implementing the 7-phase tick cycle.

### simulation.py

**Role:** Main orchestrator. This is the central file that coordinates all other systems.

**Key Responsibilities:**
1. Initializes simulation from `ScenarioConfig` (loaded by `scenarios/loader.py`)
2. Creates and manages the **7 Systems** (Perception, Decision, Movement, Trade, Forage, Regeneration, Housekeeping)
3. Executes `step()` each tick, calling each system's `execute()` method in order
4. Manages global simulation state: `tick`, `current_mode`, `agents`, `grid`, `resource_claims`
5. Integrates `TelemetryManager` for SQLite logging

**Important Methods:**
- `__init__()` - Loads scenario, seeds grid, creates agents, initializes systems
- `run(max_ticks)` - Main simulation loop
- `step()` - Execute one tick (7 phases)
- `_should_execute_system()` - Mode-aware system filtering (trade vs forage vs both)
- `_handle_mode_transition()` - Clear pairings and foraging commitments on mode change

**Dependencies:**
- Imports: `Grid`, `Agent`, `Inventory`, `SpatialIndex` from `core/`
- Imports: `ScenarioConfig` from `scenarios/`
- Imports: All 7 System classes from `systems/`
- Imports: `TelemetryManager` from `telemetry/`

---

### core/ - Fundamental Data Structures

These files define the basic building blocks used throughout the simulation.

#### core/agent.py

**Purpose:** Agent representation with inventory, utility, quotes, and runtime state.

**Relationship to simulation.py:**
- `simulation.py` creates list of `Agent` objects in `_initialize_agents()`
- Each agent has: position, inventory (A, B, M), utility function, quotes dict, trade cooldowns
- Agents have **pairing state** (`paired_with_id`) and **foraging commitment** state
- Money-aware: `lambda_money` per agent, `quotes` is `dict[str, float]` with monetary keys

**Key Attributes:**
- `inventory: Inventory` - Current holdings (A, B, M)
- `quotes: dict[str, float]` - Ask/bid prices for all exchange pairs (money-aware API)
- `paired_with_id: int | None` - Trade partner (persists across ticks)
- `is_foraging_committed: bool` - Resource commitment state
- `trade_cooldowns: dict[int, int]` - Prevents re-pairing after failed trade

#### core/grid.py

**Purpose:** N×N grid with resource cells.

**Relationship to simulation.py:**
- `simulation.py` creates `Grid(N)` and seeds resources via `seed_resources()`
- `Grid.cells: dict[Position, Cell]` - All grid cells
- `Grid.harvested_cells: set[Position]` - Active set for O(1) regeneration tracking
- Provides `manhattan_distance()` and `cells_within_radius()` for spatial queries

**Key Classes:**
- `Resource` - Type (A/B), amount, original_amount, last_harvested_tick
- `Cell` - Position + Resource
- `Grid` - N×N grid manager with helper methods

#### core/spatial_index.py

**Purpose:** Grid-based spatial hash for efficient O(N) proximity queries.

**Relationship to simulation.py:**
- `simulation.py` creates `SpatialIndex` with `bucket_size = max(vision_radius, interaction_radius)`
- Used by **PerceptionSystem** to find nearby agents without O(N²) all-pairs checks
- Agents update index on movement via `spatial_index.update_position()`

**Performance:** Reduces agent-agent queries from O(N²) to O(N) average case.

#### core/state.py

**Purpose:** Core data structures: `Inventory`, `Quote`, `Position`.

**Relationship to simulation.py:**
- `Inventory(A, B, M)` - Agent holdings (integers ≥ 0)
- `Quote` - Legacy dataclass (DEPRECATED, use dict-based quotes)
- `Position` - Type alias for `tuple[int, int]`

---

### econ/ - Economic Utility Functions

#### econ/utility.py

**Purpose:** 5 utility function implementations with money-aware API.

**Relationship to simulation.py:**
- `simulation.py` creates utility for each agent via `create_utility(config)`
- Utilities used in:
  - **Decision phase:** Compute surplus for pairing
  - **Trading phase:** Check if trade improves utility
  - **Foraging phase:** Calculate utility gain from resource harvest

**Utility Classes:**
1. **UCES** - Constant Elasticity of Substitution (includes Cobb-Douglas as special case)
2. **ULinear** - Perfect substitutes with constant MRS
3. **UQuadratic** - Bliss points with satiation behavior
4. **UTranslog** - Flexible translog form
5. **UStoneGeary** - Subsistence constraints (γ_A, γ_B)

**Money-Aware API:**
- `u_goods(A, B)` - Utility from goods only
- `mu_A(A, B)`, `mu_B(A, B)` - Marginal utilities
- `u_total(inventory, params)` - Total utility including quasilinear money: U_goods(A,B) + λ·M

**Key Function:**
- `create_utility(config)` - Factory function for dynamic instantiation from YAML scenarios

---

### systems/ - 7-Phase System Implementations

Each system implements the `System` protocol with an `execute(sim)` method called by `simulation.py` during its phase.

#### systems/base.py

**Purpose:** Protocol definition for systems.

**Relationship to simulation.py:**
- Defines `System` protocol with `execute(sim: Simulation) -> None`
- All 7 systems implement this protocol

#### systems/perception.py

**Purpose:** **Phase 1** - Agents perceive environment (neighbors, quotes, resources).

**Relationship to simulation.py:**
- Called first in `simulation.step()`
- Uses `sim.spatial_index.query_radius()` for efficient neighbor discovery
- Stores perception in `agent.perception_cache` for use by Decision phase
- **Money-aware:** Captures neighbor quotes dict with all exchange pairs

**Output:** Each agent's `perception_cache` contains:
- `neighbors: list[(agent_id, pos)]`
- `neighbor_quotes: dict[agent_id -> quotes_dict]`
- `resource_cells: list[Cell]`

#### systems/decision.py

**Purpose:** **Phase 2** - Three-pass pairing algorithm with money-aware surplus calculation.

**Relationship to simulation.py:**
- Called after Perception phase
- Implements **critical pairing logic** that determines who trades with whom

**Algorithm (3 passes):**

**Pass 1: Target Selection**
- Each agent builds ranked preference list of neighbors
- Uses `estimate_money_aware_surplus()` for money/mixed regimes
- Uses `compute_surplus()` for barter-only regime
- Sorts by β-discounted surplus: `surplus × β^distance`
- Stores preferences in `agent._preference_list`
- Sets `agent.target_agent_id` to top choice

**Pass 2: Mutual Consent**
- If agent i targets j AND j targets i → **PAIR** (strongest signal)
- Both agents set `paired_with_id`
- Logs "mutual_consent" pairing event

**Pass 3: Best Available Fallback**
- Collect all (agent, partner) preferences from unpaired agents
- Sort globally by discounted surplus (welfare-maximizing greedy)
- Greedily assign pairs (highest surplus first)
- Logs "fallback_rank_N" pairing events

**Pass 3b: Unpaired Trade Targets**
- Agents with unfulfilled trade targets fall back to foraging (if in "both" mode)

**Pass 4: Logging**
- Log all decisions to telemetry
- Optionally log full preference rankings if `params['log_preferences'] = True`

**Money-Aware Details:**
- Uses `estimate_money_aware_surplus()` which checks A<->M, B<->M, A<->B feasibility
- Returns (surplus, pair_type) tuple
- Preference list now stores 5-tuple: `(partner_id, surplus, discounted_surplus, distance, pair_type)`
- Inventory feasibility checked per exchange pair

#### systems/movement.py

**Purpose:** **Phase 3** - Agents move toward targets using Manhattan distance.

**Relationship to simulation.py:**
- Called after Decision phase
- Moves agents toward `agent.target_pos` (partner or resource)
- Updates `sim.spatial_index` after movement
- Handles **diagonal deadlock** (paired agents diagonally adjacent)

**Key Functions:**
- `next_step_toward(current, target, budget)` - Greedy pathfinding with deterministic tie-breaking
- Respects `move_budget_per_tick` parameter

#### systems/quotes.py

**Purpose:** Quote generation and management (reservation prices with bid-ask spread).

**Relationship to simulation.py:**
- NOT a system with `execute()` method
- Called from **Housekeeping phase** via `refresh_quotes_if_needed()`
- Initial quotes computed in `simulation._initialize_agents()`

**Money-Aware API:**
- `compute_quotes(agent, spread, epsilon, money_scale)` → `dict[str, float]`
- Returns keys for all exchange pairs:
  - Barter: `ask_A_in_B`, `bid_A_in_B`, `p_min_A_in_B`, `p_max_A_in_B`
  - Monetary: `ask_A_in_M`, `bid_A_in_M`, `ask_B_in_M`, `bid_B_in_M`
- `filter_quotes_by_regime()` - Restricts visibility based on exchange_regime

**Quote Calculation:**
- Barter: Uses `utility.reservation_bounds_A_in_B()` based on MRS
- Monetary: Price_A_in_M = (MU_A / λ) × money_scale

**Stability Contract:** Quotes only refresh in Housekeeping when `inventory_changed = True`

#### systems/matching.py

**Purpose:** Surplus calculation and trade block finding (supports all exchange pairs).

**Relationship to simulation.py:**
- NOT a system with `execute()` method
- Called by **Decision phase** for surplus estimation
- Called by **Trading phase** for trade execution

**Key Functions:**

**For Pairing (Decision Phase):**
- `estimate_money_aware_surplus(i, j, regime)` - **O(1) heuristic** using quote overlaps
  - Returns: `(best_surplus, best_pair_type)`
  - Checks all allowed pairs: A<->B, A<->M, B<->M
  - Money-first priority on ties: A<->M > B<->M > A<->B
  - **IMPORTANT:** This is an approximation! Quote overlaps may not perfectly predict actual utility gains.
  
- `compute_surplus(i, j)` - Legacy barter-only (DEPRECATED for money regimes)

**For Trading (Trade Phase):**
- `find_compensating_block_generic(i, j, pair, params)` - **Full utility calculation**
  - Searches dA ∈ [1, dA_max], tries multiple prices
  - Returns: `(dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)` or None
  - Supports 'minimum' mode (first feasible) or 'maximum' mode (max quantity at price)
  
- `find_best_trade(i, j, regime, params)` - Tries pairs in order, returns first success
- `find_all_feasible_trades(i, j, regime, params)` - Returns ALL feasible trades (for mixed regime tie-breaking)
- `execute_trade_generic(i, j, trade)` - Updates inventories, sets `inventory_changed = True`

**Price Search:**
- `generate_price_candidates(ask, bid, dA)` - Smart price sampling
  - Generates prices yielding integer dB values
  - Adds evenly-spaced samples for coverage
  - Critical for finding mutually beneficial discrete trades

#### systems/trading.py

**Purpose:** **Phase 4** - Execute trades between paired agents.

**Relationship to simulation.py:**
- Called after Movement phase
- Processes only **paired agents** (pairing replaces spatial matching)
- Checks `interaction_radius` before attempting trade

**Algorithm:**
1. Iterate over paired agents (sorted by ID, process each pair once)
2. Check if within `interaction_radius`
3. If money/mixed regime: call `_trade_generic()`
4. If barter-only regime: call legacy `trade_pair()`
5. If trade succeeds: agents REMAIN PAIRED (will try again next tick)
6. If trade fails: UNPAIR both agents, set `trade_cooldown_ticks`

**Money-Aware Trading:**
- For **mixed regimes:** Finds ALL feasible trades, ranks with money-first tie-breaking
- For **barter/money_only:** Uses first feasible trade
- Logs trade with `exchange_pair_type` field

**Trade Execution Modes:**
- `minimum` (default): Return first mutually beneficial trade (pedagogical)
- `maximum`: Return largest batch at chosen price (efficient)

#### systems/foraging.py

**Purpose:** **Phase 5** - Resource harvesting and **Phase 6** - Resource regeneration.

**Relationship to simulation.py:**
- Two systems: `ForageSystem` and `ResourceRegenerationSystem`
- Called after Trading phase

**ForageSystem:**
- Skips paired agents (exclusive trading commitment)
- Harvests `min(cell.resource.amount, forage_rate)` units
- Updates agent inventory, sets `inventory_changed = True`
- Breaks foraging commitment after harvest
- Clears trade cooldowns (productive foraging clears frustration)
- Enforces `enforce_single_harvester` (one agent per resource per tick)

**ResourceRegenerationSystem:**
- Uses **active set tracking** via `grid.harvested_cells`
- Only regenerates cells that were harvested
- Waits `resource_regen_cooldown` ticks after last harvest
- Regenerates `growth_rate` units per tick, capped at `original_amount`
- O(harvested_cells) instead of O(N²)

#### systems/housekeeping.py

**Purpose:** **Phase 7** - Quote refresh, pairing integrity, telemetry logging.

**Relationship to simulation.py:**
- Called last in each tick
- Ensures quotes stay synchronized with inventory changes

**Tasks:**
1. **Refresh Quotes:** Call `refresh_quotes_if_needed()` for agents with `inventory_changed = True`
2. **Verify Pairing Integrity:** Defensive check that all pairings are bidirectional
3. **Log Telemetry:** Call `telemetry.log_agent_snapshots()` and `log_resource_snapshots()`

**Quote Stability:** This is the ONLY phase where quotes can change (preserves per-tick stability).

---

## src/scenarios/

**Purpose:** Scenario loading, schema validation, and configuration management.

**Relationship to simulation.py:**
- `simulation.py.__init__()` receives a `ScenarioConfig` object
- Scenario files (YAML) → `loader.py` → `ScenarioConfig` → `simulation.py`

### scenarios/schema.py

**Purpose:** Dataclass definitions for scenario structure.

**Key Classes:**
- `ScenarioConfig` - Top-level scenario structure
  - `N: int` - Grid size
  - `agents: int` - Agent count
  - `initial_inventories: dict` - Starting A, B, M, lambda_money
  - `utilities: UtilitiesMix` - Utility function mix
  - `params: ScenarioParams` - All simulation parameters
  - `resource_seed: ResourceSeed` - Initial resource seeding
  - `mode_schedule: ModeSchedule` - Optional mode alternation

- `ScenarioParams` - 40+ simulation parameters including:
  - Trade parameters: `dA_max`, `spread`, `epsilon`, `beta`, `trade_cooldown_ticks`
  - Movement: `vision_radius`, `interaction_radius`, `move_budget_per_tick`
  - Resources: `forage_rate`, `resource_growth_rate`, `resource_regen_cooldown`
  - Money system: `exchange_regime`, `money_mode`, `money_scale`, `lambda_money`
  - Telemetry: `log_preferences`

- `ModeSchedule` - Alternating forage/trade modes
  - `get_mode_at_tick(tick)` - Returns "forage", "trade", or "both"

**Validation:** All classes have `.validate()` methods called during loading.

### scenarios/loader.py

**Purpose:** Load YAML scenario files and convert to `ScenarioConfig`.

**Key Function:**
- `load_scenario(path)` - Parses YAML, validates, returns `ScenarioConfig`

**Used by:**
- `main.py` (CLI entry point)
- `launcher.py` (GUI)
- All test files

---

## src/telemetry/

**Purpose:** SQLite-based comprehensive logging system (99% compression over CSV).

**Relationship to simulation.py:**
- `simulation.py.__init__()` creates `TelemetryManager` instance
- All systems call `sim.telemetry.log_*()` methods to record events
- Database closed in `simulation.close()`

### telemetry/config.py

**Purpose:** Logging configuration and verbosity levels.

**Key Classes:**
- `LogLevel` - STANDARD (default) vs DEBUG (includes failed trade attempts)
- `LogConfig` - Configures what/when to log
  - `agent_snapshot_frequency` - Log agents every N ticks
  - `resource_snapshot_frequency` - Log resources every N ticks
  - `log_preferences` - Enable preference table logging
  - `log_trade_attempts` - Enable detailed trade diagnostics (DEBUG only)

**Factory Methods:**
- `LogConfig.standard()` - Default logging
- `LogConfig.debug()` - Verbose logging for diagnostics
- `LogConfig.minimal()` - Testing only

### telemetry/database.py

**Purpose:** SQLite schema creation and connection management.

**Tables Created:**
- `simulation_runs` - Run metadata (scenario, seed, timestamps)
- `agent_snapshots` - Agent state per tick (position, inventory, quotes, utility)
- `resource_snapshots` - Grid resources per tick
- `decisions` - Agent decisions (partner choice, target, mode)
- `trades` - Successful trades (dA, dB, dM, price, exchange_pair_type)
- `trade_attempts` - Failed trades (DEBUG mode only)
- `pairings` - Pair/unpair events with reasons
- `preferences` - Top-N preference rankings (opt-in)
- `tick_states` - Mode and exchange regime per tick
- `mode_changes` - Mode transition events

**Features:**
- WAL mode for concurrent access
- Indexed queries for fast retrieval
- Foreign keys enabled

### telemetry/db_loggers.py

**Purpose:** `TelemetryManager` class that wraps database and provides logging API.

**Key Methods Used by Systems:**

**Housekeeping Phase:**
- `log_agent_snapshots(tick, agents)` - Batch insert agent states
- `log_resource_snapshots(tick, grid)` - Batch insert resource states

**Decision Phase:**
- `log_decision(tick, agent_id, partner_id, surplus, target_type, ...)` - Decision context
- `log_preference(tick, agent_id, partner_id, rank, surplus, ...)` - Preference rankings (opt-in)
- `log_pairing_event(tick, i, j, event, reason, surplus_i, surplus_j)` - Pair/unpair with reasons

**Trading Phase:**
- `log_trade(tick, x, y, buyer_id, seller_id, dA, dB, price, direction, dM, exchange_pair_type)`
- `log_trade_attempt(tick, ...)` - Detailed trade diagnostics (DEBUG mode)

**Mode Transitions:**
- `log_mode_change(tick, old_mode, new_mode)` - Mode switches
- `log_tick_state(tick, mode, regime, active_pairs)` - Per-tick state snapshot

**Performance:** Batch buffering with configurable `batch_size` (default 100) for efficiency.

---

## src/vmt_pygame/

**Purpose:** Real-time PyGame visualization of simulation.

**Relationship to simulation.py:**
- Created by `main.py` or `launcher.py` after simulation initialization
- `renderer.step()` called after each `simulation.step()`
- Visualization is **passive observer** (does not affect simulation logic)

### vmt_pygame/renderer.py

**Purpose:** PyGame-based 2D grid visualization with HUD.

**Key Features:**
- **Adaptive Scaling:** Auto-detects cell size based on monitor resolution
- **Scrolling:** Large grids support camera panning
- **Agent Rendering:** Color-coded by utility type, shows inventory, quotes, target lines
- **Resource Rendering:** Gradient intensity based on amount
- **HUD Display:** Tick counter, mode indicator, regime indicator, trade counter
- **Left Panel:** Detailed statistics (agent count, trade counts by pair type, avg utility)
- **Trade Visualization:** Recent trades shown with buyer/seller highlighting

**Rendering Layers:**
1. Grid lines
2. Resources (gradient color by amount)
3. Agents (circles with inventory text)
4. Target lines (from agent to target)
5. HUD overlays

**User Interactions:**
- Arrow keys: Pan camera (if scrolling enabled)
- Mouse hover: Show agent details tooltip

**Performance:** Uses double buffering, dirty rect optimization for large grids.

---

## src/vmt_launcher/

**Purpose:** PyQt6 GUI application for scenario browsing, building, and launching.

**Relationship to simulation.py:**
- **Indirectly:** Launcher creates scenario files, then spawns `main.py` subprocess
- Does NOT import or run `simulation.py` directly

### vmt_launcher/launcher.py

**Purpose:** Main GUI window with tabbed interface.

**Features:**
- **Scenario Browser Tab:** Browse/load/edit YAML scenarios from `scenarios/` directory
- **Scenario Builder Tab:** Visual GUI for creating new scenarios (uses `scenario_builder.py`)
- **Log Viewer Tab:** View simulation results from telemetry database (uses `vmt_log_viewer/`)
- **Launch Button:** Spawns `main.py` subprocess with selected scenario

### vmt_launcher/scenario_builder.py

**Purpose:** PyQt6 form for building scenarios visually.

**Features:**
- Grid size, agent count, max steps sliders
- Utility mix editor (add/remove/reweight utilities)
- Parameter panels for all `ScenarioParams` fields
- Resource seeding configuration
- Mode schedule builder
- Validation and YAML export

### vmt_launcher/validator.py

**Purpose:** Scenario validation and error reporting.

**Features:**
- Calls `ScenarioConfig.validate()` from `schema.py`
- Displays user-friendly error messages
- Highlights invalid fields in builder UI

---

## src/vmt_log_viewer/

**Purpose:** PyQt6 GUI for analyzing simulation telemetry data.

**Relationship to simulation.py:**
- **Post-hoc analysis:** Reads SQLite database written by `TelemetryManager`
- Does NOT interact with live simulations

### vmt_log_viewer/viewer.py

**Purpose:** Main log viewer window with multi-tabbed analysis interface.

**Features:**
- **Run Selection:** Browse all runs in database
- **Agent Trajectory Tab:** Plot agent positions, inventory over time
- **Trade Analysis Tab:** Trade timeline, pair distribution, surplus distribution
- **Money Analytics Tab:** Money balance histograms, λ trajectories (for money regimes)
- **Preference Analysis Tab:** View preference rankings logged during Decision phase

### vmt_log_viewer/queries.py

**Purpose:** SQL query builders for telemetry database.

**Key Queries:**
- `get_all_runs()` - List simulation runs
- `get_agent_trajectory(run_id, agent_id)` - Agent position/inventory time series
- `get_trades_by_tick(run_id)` - Trade timeline
- `get_preference_rankings(run_id, tick)` - Decision phase preferences
- `get_money_balances(run_id, tick)` - Money distribution snapshot

### vmt_log_viewer/csv_export.py

**Purpose:** Export query results to CSV for external analysis.

**Features:**
- Export agent snapshots
- Export trades table
- Export custom SQL query results
- Progress bar for large exports

### vmt_log_viewer/widgets/ (multiple files)

**Purpose:** Custom PyQt6 widgets for visualization.

**Files:**
- `agent_view.py` - Agent trajectory plots
- `trade_view.py` - Trade timeline and histograms
- `timeline.py` - Tick slider with mode annotations
- `filters.py` - Filter controls for queries

---

## src/vmt_tools/

**Purpose:** Command-line tools for scenario generation and manipulation.

**Relationship to simulation.py:**
- **Pre-simulation:** Creates scenario files consumed by `simulation.py`

### vmt_tools/generate_scenario.py

**Purpose:** Programmatic scenario generation from Python code.

**Features:**
- Build `ScenarioConfig` objects programmatically
- Random utility parameter generation
- Batch scenario creation for experiments
- YAML export

**Example Usage:**
```python
from vmt_tools.generate_scenario import generate_scenario

scenario = generate_scenario(
    N=40, agents=20, max_steps=200,
    utility_types=['ces', 'linear'],
    exchange_regime='mixed'
)
scenario.to_yaml('my_scenario.yaml')
```

### vmt_tools/scenario_builder.py

**Purpose:** CLI scenario builder (alternative to GUI version).

**Features:**
- Interactive prompts for all scenario parameters
- Template-based generation
- Validation before save

### vmt_tools/param_strategies.py

**Purpose:** Parameter sampling strategies for scenario generation.

**Features:**
- Uniform distributions
- Log-uniform for scale-invariant parameters (e.g., λ, money_scale)
- Gaussian distributions
- Grid search parameter sweeps

**Used by:** `generate_scenario.py` for creating experimental scenarios

---

## Architecture Relationships Summary

### Data Flow: Scenario → Simulation → Telemetry → Visualization

```
┌─────────────────┐
│  YAML Scenario  │
│   (scenarios/)  │
└────────┬────────┘
         │ load_scenario()
         ▼
┌─────────────────┐
│ ScenarioConfig  │
│  (schema.py)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         simulation.py                       │
│  ┌──────────────────────────────────────┐  │
│  │  7-Phase Tick Loop:                  │  │
│  │  1. Perception                       │  │
│  │  2. Decision (3-pass pairing)        │  │
│  │  3. Movement                         │  │
│  │  4. Trade (paired agents)            │  │
│  │  5. Forage (unpaired agents)         │  │
│  │  6. Regeneration                     │  │
│  │  7. Housekeeping (quote refresh)     │  │
│  └──────────────────────────────────────┘  │
│         ▲                       │           │
│         │ uses                  │ logs      │
│         │                       ▼           │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │  core/       │      │ TelemetryManager│ │
│  │  econ/       │      │   (db_loggers)  │ │
│  │  systems/    │      └────────┬────────┘ │
│  └──────────────┘               │          │
└─────────────────────────────────┼──────────┘
                                  │ writes
                                  ▼
                         ┌─────────────────┐
                         │ telemetry.db    │
                         │   (SQLite)      │
                         └────────┬────────┘
                                  │ reads
                 ┌────────────────┴────────────────┐
                 │                                  │
        ┌────────▼─────────┐              ┌────────▼────────┐
        │  vmt_log_viewer  │              │  vmt_pygame     │
        │    (analysis)    │              │ (real-time viz) │
        └──────────────────┘              └─────────────────┘
```

### Key Architectural Patterns

**1. System Protocol Pattern**
- All 7 phases implement `System` protocol
- `simulation.py` iterates over `self.systems` list
- Uniform `execute(sim)` interface

**2. Money-Aware Architecture**
- Quotes stored as `dict[str, float]` (not dataclass)
- Matching functions accept `exchange_regime` parameter
- Telemetry logs `exchange_pair_type` field
- Backward compatible with barter-only legacy code

**3. Pairing-Based Trading**
- Replaces spatial proximity matching
- Persistent pairs across ticks (until trade fails)
- DecisionSystem handles pairing logic
- TradeSystem only processes paired agents

**4. Inventory Feasibility**
- Checked at pairing (Decision phase) via `estimate_money_aware_surplus()`
- Checked at trading (Trade phase) via `find_compensating_block_generic()`
- Prevents futile pairings when theoretical surplus is unrealizable

**5. Quote Stability**
- Quotes only refresh in Housekeeping phase
- Set `inventory_changed = True` to trigger refresh
- Preserves per-tick stability for determinism

---

## Critical Invariants to Maintain

When modifying code, these invariants MUST be preserved:

1. **7-Phase Order:** Never change phase execution sequence
2. **Sorted Agent Iteration:** Always process agents sorted by ID
3. **Quote Stability:** Only refresh quotes in Housekeeping phase
4. **Pairing Integrity:** Pairings must be bidirectional (A.paired_with_id = B.id ↔ B.paired_with_id = A.id)
5. **Conservation Laws:** dA_i + dA_j = 0, dB_i + dB_j = 0, dM_i + dM_j = 0
6. **Non-Negativity:** All inventories ≥ 0 at all times
7. **Money Scale Consistency:** M stored in minor units, prices include money_scale factor
8. **Determinism:** Fixed seeds produce identical results

---

## Testing Strategy

**Unit Tests:** Each system and utility function has dedicated test file in `tests/`

**Integration Tests:**
- `test_barter_integration.py` - Full barter-only scenarios
- `test_money_phase1_integration.py` - Money system integration
- `test_mixed_regime_integration.py` - Mixed barter+money scenarios
- `test_mode_integration.py` - Mode alternation (forage↔trade)

**Determinism Tests:**
- Run same scenario with same seed multiple times
- Assert bit-identical results (inventories, positions, trades)

**Performance Benchmarks:**
- `scripts/benchmark_performance.py` - TPS measurement
- Target: >1000 TPS for 100 agents on commodity hardware

---

## Development Workflow

**Before Making Changes:**
1. Run full test suite: `pytest`
2. Identify which phase(s) your change affects
3. Read related system file(s) from this guide

**After Making Changes:**
1. Run affected tests: `pytest tests/test_<relevant>*.py`
2. Run full integration tests: `pytest tests/test_*_integration.py`
3. Verify determinism: Run scenario 3× with same seed, diff results
4. Update this guide if architectural changes made

**Code Quality:**
```bash
black --check .        # Format check
ruff check .           # Linting
mypy src/              # Type checking (goal: 100% coverage)
```

---

## Future Architecture Changes

**Planned Refactoring (from roadmap):**

1. **Protocol Modularization** - Refactor DecisionSystem into pluggable protocol interfaces
   - Current: Monolithic 3-pass algorithm
   - Future: Support multiple search/matching protocols

2. **KKT Lambda Mode** - Endogenous λ estimation from market prices
   - Current: Fixed λ (quasilinear mode)
   - Future: Agents estimate λ from observed A<->M, B<->M prices

3. **Mixed Liquidity Gated** - Barter fallback when money market thin
   - Current: All exchange types always available in mixed regime
   - Future: Liquidity threshold determines when barter is allowed

4. **Phase C Market Mechanisms** - Posted-price markets, auctions
   - Current: Bilateral negotiation only
   - Future: Centralized market mechanisms

**Impact on Code Review:**
- These changes will primarily affect `systems/decision.py` and `systems/trading.py`
- Core architecture (7-phase cycle) will remain unchanged
- Backward compatibility required for existing scenarios

---

## Glossary of Key Terms

- **Agent:** Economic actor with position, inventory, utility, quotes
- **Pairing:** Two agents committed to trading (persists until trade fails)
- **Surplus:** Utility gain from potential trade (used for partner selection)
- **Exchange Pair:** Type of trade (A<->B barter, A<->M, B<->M monetary)
- **Exchange Regime:** Which pairs are allowed (barter_only, money_only, mixed)
- **Quote:** Bid/ask prices derived from reservation prices (MRS + spread)
- **Reservation Price:** p_min (seller), p_max (buyer) from utility function
- **Money-Aware:** API that supports monetary exchanges (dict-based quotes)
- **dA_max:** Maximum trade quantity to search (performance parameter)
- **Beta (β):** Distance discount factor for surplus (0 < β ≤ 1)
- **Mode Schedule:** Alternating forage/trade/both periods
- **Foraging Commitment:** Exclusive focus on resource target (blocks trading)
- **Trade Cooldown:** Ticks to wait after failed trade before re-pairing
- **Tick:** One complete 7-phase cycle
- **TPS:** Ticks per second (performance metric)

---

## Contact & Maintenance

**Primary Developer:** User (PhD Economics)

**Documentation Updates:**
- Update this guide when adding new systems/files
- Increment "Last Updated" date at top
- Add new sections following existing format

**Questions During Code Review:**
- Refer to section describing the file/system in question
- Check "Relationship to simulation.py" subsection
- Verify invariants section for constraints

---

**End of Code Review Guide**

