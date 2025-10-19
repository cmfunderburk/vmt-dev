# Copilot Instructions for VMT (Visualizing Microeconomic Theory)

## Repository Overview

**VMT** is a deterministic spatial agent-based simulation for teaching and researching microeconomic behavior. It implements a 7-phase discrete-time tick cycle on an NxN grid where agents engage in bilateral barter trading and resource foraging.

- **Type**: Python simulation engine with PyQt5 GUI applications
- **Size**: ~56 Python files, 58MB (excluding venv/logs)
- **Languages**: Python 3.12+
- **Key Dependencies**: pygame, numpy, PyQt5, pyyaml, pytest
- **Test Suite**: 63+ tests (all must pass)

## Critical Build Requirements

### Virtual Environment Setup

**IMPORTANT**: The venv directory is named `venv`, NOT `.venv` (contrary to README examples).

```bash
# If venv doesn't exist, create it:
python3 -m venv venv

# Always activate before any operations:
source venv/bin/activate  # Linux/Mac
```

### Dependency Installation

```bash
# Must be run with venv activated
pip install -r requirements.txt
```

**Required versions** (from requirements.txt):
- pygame>=2.5.0
- numpy>=1.24.0
- pyyaml>=6.0
- pytest>=7.4.0
- PyQt5>=5.15.0

### Testing

**ALWAYS run tests before committing changes.**

```bash
# Standard test run (quiet mode)
pytest -q

# Run with full output
pytest -v

# Run specific test file
pytest tests/test_barter_integration.py
```

**Expected Result**: `63 passed, 1 skipped` (as of Oct 2025)

### Critical Testing Gotcha

**If tests fail with database schema errors** (e.g., `table decisions has no column named mode`):

```bash
# Delete stale database before running tests
rm logs/telemetry.db
pytest -q
```

This issue occurs when the telemetry schema evolves but an old database exists. **Always delete logs/telemetry.db when schema changes are made.**

### Running Simulations

```bash
# GUI launcher (recommended for testing)
python launcher.py

# Command-line with visualization
python main.py scenarios/three_agent_barter.yaml --seed 42

# View telemetry logs
python view_logs.py
```

**Note**: pygame window requires X11/display. For headless environments, use programmatic access:

```bash
# Set PYTHONPATH for programmatic access
export PYTHONPATH=.:src
python your_script.py
```

```python
# your_script.py
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario
from telemetry.config import LogConfig

scenario = load_scenario("scenarios/three_agent_barter.yaml")
sim = Simulation(scenario, seed=42, log_config=LogConfig.debug())
sim.run(max_ticks=100)
```

## Project Architecture

### Directory Structure

```
/home/chris/PROJECTS/vmt-dev/
├── src/
│   ├── vmt_engine/          # Core simulation (7-phase tick cycle)
│   │   ├── core/            # Agent, Grid, SpatialIndex, state.py
│   │   ├── econ/            # utility.py (UCES, ULinear)
│   │   └── systems/         # 7 phase systems (perception, decision, etc.)
│   ├── scenarios/           # schema.py, loader.py
│   ├── telemetry/           # SQLite logging (config, database, db_loggers)
│   ├── vmt_launcher/        # GUI launcher (PyQt5)
│   ├── vmt_log_viewer/      # GUI log viewer (PyQt5)
│   └── vmt_pygame/          # renderer.py (Pygame visualization)
├── tests/                   # 14 test files, 63+ tests
├── scenarios/               # YAML scenario files
├── docs/                    # Comprehensive documentation
├── main.py                  # CLI entry point
├── launcher.py              # GUI launcher entry point
├── view_logs.py             # Log viewer entry point
├── requirements.txt         # Python dependencies
└── pytest.ini               # Sets pythonpath = . src
```

### Critical Code Conventions

**Determinism is paramount.** The simulation must produce identical results given the same scenario and seed.

1. **Always sort agent loops**: `for agent in sorted(sim.agents, key=lambda a: a.id)`
2. **Always sort pair loops**: `for (id1, id2) in sorted(pairs, key=lambda p: (min(p), max(p)))`
3. **Use round-half-up**: `floor(price * delta_A + 0.5)` for quantity calculations
4. **Integer types**: Inventories, resources, and spatial params (vision_radius, interaction_radius, move_budget_per_tick) are integers
5. **Quote stability**: Never mutate quotes mid-tick; only refresh in Housekeeping phase
6. **Set inventory_changed flag**: When inventories change, set `agent.inventory_changed = True` to trigger quote recomputation

### The 7-Phase Tick Cycle

Order is sacred and must never change:

1. **Perception** - Agents observe environment (frozen snapshot)
2. **Decision** - Choose trading partner or foraging target
3. **Movement** - Move toward targets (Manhattan distance)
4. **Trade** - Execute bilateral trades (one per pair per tick)
5. **Forage** - Harvest resources on current cell
6. **Resource Regeneration** - Resources regrow with cooldowns
7. **Housekeeping** - Refresh quotes, flush telemetry

See `src/vmt_engine/simulation.py` for system orchestration.

## Configuration Files

- **pytest.ini**: Sets `pythonpath = . src` (required for imports to work)
- **requirements.txt**: Dependency versions
- **scenarios/*.yaml**: Simulation scenarios (schema in `src/scenarios/schema.py`)

**No linter config files** (flake8, pylint, black) exist yet. Code style is informal.

## Known Issues & Workarounds

### Database Schema Drift
**Problem**: Old telemetry.db with incompatible schema causes test failures.
**Solution**: `rm logs/telemetry.db` before running tests after schema changes.

### Import Path Setup
**Problem**: Top-level scripts (main.py, launcher.py) need src/ in path.
**Solution**: Already handled via `sys.path.insert(0, 'src')` in entry points. Tests use pytest.ini pythonpath setting.

### Virtual Environment Name
**Problem**: README examples use `.venv` but actual directory is `venv`.
**Solution**: Always use `source venv/bin/activate`.

## Development Workflow

### Making Changes

1. Activate venv: `source venv/bin/activate`
2. Make code changes
3. Delete stale DB if schema changed: `rm logs/telemetry.db`
4. Run tests: `pytest -q`
5. Verify all tests pass (63 passed, 1 skipped expected)
6. Test with GUI if UI changed: `python launcher.py`
7. Test simulation runs: `python main.py scenarios/three_agent_barter.yaml --seed 42`

### Common Tasks

**Adding a new test**:
- Create in `tests/` directory
- Import required: `import pytest` and simulation components
- Follow naming: `test_*.py`
- Run: `pytest tests/test_your_new_test.py -v`

**Adding a new scenario**:
- Create YAML in `scenarios/` directory
- Follow schema in `src/scenarios/schema.py`
- Validate by loading: `load_scenario("scenarios/your_scenario.yaml")`

**Modifying telemetry schema**:
- Edit `src/telemetry/database.py` (table definitions)
- Edit `src/telemetry/db_loggers.py` (logging logic)
- **MUST delete logs/telemetry.db** before testing
- Update any tests that query database

**Changing agent behavior**:
- Modify systems in `src/vmt_engine/systems/`
- Maintain determinism (sort loops by agent.id)
- Preserve 7-phase order
- Test with: `pytest tests/test_barter_integration.py -v`

## Versioning Policy

**No SemVer or numeric versions** unless explicitly authorized. Use date-time identifiers (e.g., `2025-10-19-1430`) for any versioning needs in docs, branches, tags.

## Validation Checklist

Before submitting changes, verify:

- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip list | grep -E "pygame|numpy|pyyaml|pytest|PyQt5"`)
- [ ] Old database deleted if schema changed (`rm logs/telemetry.db`)
- [ ] All tests pass (`pytest -q` shows "63 passed, 1 skipped")
- [ ] GUI launches without errors (if GUI changed: `python launcher.py`)
- [ ] Simulation runs without errors: `python main.py scenarios/three_agent_barter.yaml --seed 42`
- [ ] Determinism preserved (same seed = same output)
- [ ] Agent loops sorted by id (if modified agent processing)
- [ ] Inventory types remain integers (no floats for goods/quantities)

## Trust These Instructions

These instructions have been validated by running all commands in a clean environment. If you encounter issues not documented here, investigate the specific error rather than searching the codebase extensively. The information above covers 95%+ of common development tasks.

