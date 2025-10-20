# GitHub Copilot Instructions for VMT

## Repository Overview

**VMT (Visualizing Microeconomic Theory)** is a Python-based spatial agent-based simulation for teaching and researching microeconomic behavior. Agents with heterogeneous CES or Linear utility functions forage for resources on a grid and engage in bilateral barter trade using reservation-price-based negotiation.

- **Languages**: Python 3.11
- **Key Frameworks**: Pygame (visualization), PyQt5 (GUI), SQLite (telemetry), NumPy, PyYAML, Pytest
- **Size**: ~12,000 lines across 55+ files
- **Tests**: 152 passing tests (3.7s runtime)
- **Type**: Pre-release research/educational software

## Environment Setup

**CRITICAL: Always use the `venv` directory (not `.venv`).**

```bash
# Setup (first time only)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Activate (every session)
source venv/bin/activate

# Verify environment
python --version  # Should show 3.11.x
```

**Python 3.11.2** is the validated version. Dependencies: `pygame>=2.5.0`, `numpy>=1.24.0`, `pyyaml>=6.0`, `pytest>=7.4.0`, `PyQt5>=5.15.0`.

## Build & Test Commands

### Testing (ALWAYS run before committing)

```bash
# Quick test (preferred - shows summary only)
pytest -q

# Verbose output
pytest -v

# Specific test file
pytest tests/test_barter_integration.py -v

# No traceback (fastest)
pytest -q --tb=no
```

**Expected result**: `152 passed, 2486 warnings in 3.73s` (warnings are deprecation notices, not errors).

**Configuration**: `pytest.ini` sets `pythonpath = . src` (required for imports).

### Running Simulations

```bash
# GUI launcher (recommended for visual verification)
python launcher.py

# CLI with visualization (requires display)
python main.py scenarios/three_agent_barter.yaml --seed 42

# Headless scripts (requires PYTHONPATH)
PYTHONPATH=.:src python scripts/benchmark_performance.py
```

**Entry Points**:
- `launcher.py` → GUI scenario browser/builder
- `main.py` → CLI with Pygame visualization
- `view_logs.py` → SQLite telemetry viewer

### Performance Benchmarking

```bash
PYTHONPATH=.:src python scripts/benchmark_performance.py
```

Runs standardized scenarios (forage-only, exchange-only, combined) and reports TPS (ticks per second). Use to detect performance regressions.

## Critical Database Gotcha ⚠️

**If you see SQLite errors about missing columns:**

```bash
rm logs/telemetry.db
# Then re-run your simulation
```

**Why**: The database schema is NOT auto-migrated. After schema changes in `src/telemetry/database.py`, the old database file must be deleted manually. This is a known limitation.

## Project Architecture

### Directory Structure

```
vmt-dev/
├── main.py              # CLI entry point (Pygame visualization)
├── launcher.py          # GUI entry point (scenario browser/builder)
├── view_logs.py         # Telemetry viewer entry point
├── requirements.txt     # Python dependencies
├── pytest.ini           # Test configuration (sets pythonpath)
├── scenarios/           # User-facing YAML scenario files
├── scripts/             # Performance benchmarking & utilities
├── docs/                # Comprehensive documentation hub
│   ├── 1_project_overview.md      # User guide
│   ├── 2_technical_manual.md      # Architecture deep-dive
│   ├── 3_strategic_roadmap.md     # Future development plan
│   └── 4_typing_overview.md       # Type system specification
├── src/
│   ├── vmt_engine/      # Core simulation engine (THE HEART)
│   │   ├── simulation.py          # Main simulation loop (7-phase tick)
│   │   ├── core/                  # State, grid, spatial indexing
│   │   ├── econ/                  # Utility functions, economics
│   │   └── systems/               # The 7 simulation phases
│   │       ├── perception.py      # Phase 1: Neighbor discovery
│   │       ├── decision.py        # Phase 2: Partner/target selection
│   │       ├── movement.py        # Phase 3: Grid movement
│   │       ├── matching.py        # Phase 4: Trade execution
│   │       ├── foraging.py        # Phase 5: Resource harvesting
│   │       ├── resource_regen.py  # Phase 6: Resource regeneration
│   │       └── housekeeping.py    # Phase 7: Quote refresh, logging
│   ├── vmt_launcher/    # PyQt5 GUI launcher & scenario builder
│   ├── vmt_log_viewer/  # PyQt5 SQLite telemetry viewer
│   ├── vmt_pygame/      # Pygame rendering layer
│   ├── scenarios/       # Scenario loader & schema validation
│   └── telemetry/       # SQLite database & logging system
└── tests/               # 152 passing tests
```

### The Sacred 7-Phase Tick Cycle

**Every simulation tick executes these phases IN THIS EXACT ORDER** (determinism requirement):

1. **Perception** (`perception.py`) - Agents observe neighbors via `SpatialIndex`
2. **Decision** (`decision.py`) - Agents choose trading partners or forage targets
3. **Movement** (`movement.py`) - Agents move toward targets (deterministic tie-breaking)
4. **Trade** (`matching.py`) - Bilateral trades execute (price search algorithm)
5. **Foraging** (`foraging.py`) - Agents harvest resources on their cell
6. **Resource Regeneration** (`resource_regen.py`) - Grid cells regenerate resources
7. **Housekeeping** (`housekeeping.py`) - Recompute quotes, log to database

**Reference**: `src/vmt_engine/simulation.py:tick()`, `docs/2_technical_manual.md`

## Core Invariants (DO NOT VIOLATE)

### Determinism Rules (SACRED)

1. **Always sort agent loops by `agent.id`**: `for agent in sorted(agents, key=lambda a: a.id)`
2. **Always sort trade pairs by `(min_id, max_id)`** for stable ordering
3. **Never mutate quotes mid-tick** (read-only during phases 1-6; refresh in phase 7)
4. **Use round-half-up for integer conversion**: `int(x + 0.5)` NOT Python's `round()`
5. **One trade attempt per pair per tick** (failed attempts set mutual cooldown)
6. **Use SpatialIndex for ALL neighbor queries** (never O(N²) loops)

### Type Constraints

**Integer fields** (do NOT store floats):
- Positions: `agent.x`, `agent.y`
- Inventories: `agent.inventory.A`, `agent.inventory.B`, `agent.inventory.M`
- Resources: `grid.resources[x,y]`
- Spatial params: `vision_radius`, `interaction_radius`, `move_budget_per_tick`

**Float fields**:
- Prices, utilities, spreads, valuations
- Utility parameters: `w_A`, `w_B`, `rho`, `lambda_money`

**Reference**: `docs/4_typing_overview.md`

### Backward Compatibility

- **New features MUST NOT break existing scenarios**: All YAML files in `scenarios/` must continue to work
- **Provide default values for new fields** in `src/scenarios/schema.py`
- **Telemetry schema changes are additive only** (never remove columns)
- **Run `pytest -q` to validate backward compatibility**

## Common Workflows

### Adding a New Feature

1. **Read the planning docs**: Check `docs/3_strategic_roadmap.md` and `.cursor/rules/feature-development-checklist.mdc`
2. **Update schema** (if needed): Modify `src/scenarios/schema.py` with defaults
3. **Update telemetry** (if needed): Add columns to `src/telemetry/database.py` (delete old DB!)
4. **Implement the feature**: Follow the 7-phase cycle, maintain determinism
5. **Add tests**: Create `tests/test_your_feature.py` with deterministic assertions
6. **Run full test suite**: `pytest -q` (all must pass)
7. **Update documentation**: Modify relevant files in `docs/`
8. **Check CHANGELOG.md**: Add entry under `[Unreleased]`

### Modifying Economic Logic

**Key files**:
- `src/vmt_engine/econ/utility.py` - Utility functions (UCES, ULinear)
- `src/vmt_engine/systems/quotes.py` - Reservation prices & quote calculation
- `src/vmt_engine/systems/matching.py` - Price search & trade execution

**Critical**: The **zero-inventory guard** in `reservation_bounds_A_in_B()` adds a tiny epsilon to handle CES utility edge cases when an agent has zero of a good. This prevents division by zero in MRS calculations. Do NOT remove this logic.

**Testing**: Always run `tests/test_utility_ces.py` and `tests/test_utility_linear.py` after changes.

### Modifying Telemetry

**Key files**:
- `src/telemetry/database.py` - Schema definition & table creation
- `src/telemetry/db_loggers.py` - Logging functions called from simulation
- `src/telemetry/config.py` - LogLevel enum & LogConfig dataclass

**Process**:
1. Modify schema in `database.py`
2. **Delete `logs/telemetry.db`** (schema not auto-migrated!)
3. Update logging calls in `src/vmt_engine/systems/housekeeping.py`
4. Run a test simulation to validate schema
5. Update `view_logs.py` GUI if new tables need visualization

## Common Pitfalls & Workarounds

### Import Errors

**Problem**: `ModuleNotFoundError` when running scripts.

**Solution**: Always set `PYTHONPATH=.:src` for ad-hoc scripts:
```bash
PYTHONPATH=.:src python your_script.py
```

Or run via main entry points (`launcher.py`, `main.py`, `view_logs.py`) which handle paths automatically.

### GUI Not Opening (macOS)

**Problem**: `python main.py` or `python launcher.py` exits immediately without error.

**Cause**: Pygame/PyQt5 requires a display. This is expected behavior for GUI apps.

**Solution**: Cannot run headless. For testing, use `pytest` or write programmatic tests.

### Test Failures After Schema Changes

**Problem**: Tests fail with SQLite errors about missing columns.

**Solution**: `rm logs/telemetry.db` then re-run tests. See "Critical Database Gotcha" above.

### Deprecation Warnings

**Problem**: 2486 warnings when running tests.

**Status**: Known issue. Warnings are from `create_utility()` deprecation (old API still supported for backward compatibility). Tests pass correctly.

**Action**: Ignore warnings unless adding new code. New code should use direct instantiation: `UCES(...)` or `ULinear(...)` instead of `create_utility(...)`.

## Versioning Policy

**This project is pre-release.** Do NOT introduce semantic versioning (e.g., `v1.0.0`) unless authorized.

- **Use date-time identifiers**: `2025-10-19-1430` for snapshots, branches, tags
- **Update CHANGELOG.md**: Add entries under `[Unreleased]` section
- **Do NOT bump version numbers** in badge URLs or code

## Validation Checklist (Before Committing)

```bash
# 1. Ensure venv is activated
source venv/bin/activate

# 2. If you modified telemetry schema, delete old database
rm logs/telemetry.db

# 3. Run full test suite (MUST pass)
pytest -q

# 4. Verify determinism (if touching core engine)
pytest tests/test_barter_integration.py -v

# 5. Check performance (if touching hot paths)
PYTHONPATH=.:src python scripts/benchmark_performance.py

# 6. Test GUI still launches (if touching launcher/viewer)
python launcher.py  # Should open window
python view_logs.py  # Should open window

# 7. Update CHANGELOG.md if user-facing change
# 8. Update docs/ if API or behavior changed
```

## Key Files Reference

**Must read before editing**:
- `docs/2_technical_manual.md` - Complete architecture explanation
- `.cursor/rules/core-invariants.mdc` - Inviolable requirements
- `.cursor/rules/testing-workflow.mdc` - Test procedures
- `.cursor/RULES_SUMMARY.md` - Overview of all cursor rules

**Configuration files**:
- `pytest.ini` - Test configuration (sets pythonpath)
- `requirements.txt` - Python dependencies
- No linting config (no flake8, pylint, etc.)
- No CI/CD workflows (no `.github/workflows/`)

**No build step required** - Python project, direct execution.

## Trust These Instructions

These instructions were validated by:
1. Running the complete test suite (`pytest -q` → 152 passed)
2. Examining all documentation files in `docs/`
3. Reviewing 14 cursor rule files (1,619 lines of context)
4. Analyzing project structure and entry points
5. Testing simulation execution workflows

**If information here is incomplete or incorrect, THEN search the codebase. Otherwise, trust these instructions and proceed with confidence.**

---

**Last Updated**: 2025-10-19  
**Validated Against**: vmt-dev @ commit main  
**Test Status**: 152/152 passing (3.73s)
