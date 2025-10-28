# VMT (Visualizing Microeconomic Theory) - Copilot Instructions

## Repository Overview

VMT is a **spatial agent-based simulation** for teaching and researching microeconomic behavior. Agents with heterogeneous preferences forage for resources on a grid and engage in bilateral trade using reservation-price negotiation. The simulation supports barter, monetary exchange, and mixed regimes with a deterministic 7-phase engine.

**Repository size**: ~1.1MB source code (54 Python files in src/, 37 test files)
**Languages**: Python 3.11+ (tested with 3.12)
**Frameworks**: PyQt6 (GUI), Pygame (visualization), NumPy (computation), PyYAML (configuration), Pytest (testing)
**Test suite**: 333 passing tests, 19 skipped, typically runs in ~15 seconds
**Target runtime**: Python 3.11+ with virtual environment

## Critical Build & Test Information

### Environment Setup (REQUIRED)

**ALWAYS create and use a virtual environment before installing dependencies**:

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

### Installation

**Install dependencies** (should complete in 30-60 seconds):

```bash
pip install -r requirements.txt
```

Dependencies: pygame>=2.5.0, numpy>=1.24.0, pyyaml>=6.0, pytest>=7.4.0, PyQt6>=6.4.0

**Note**: Installation may timeout on slow networks. If `pip install` hangs or times out, increase the timeout: `pip install --default-timeout=300 -r requirements.txt`

### Running Tests

**ALWAYS run tests before and after making changes**. The full test suite should complete in 15-20 seconds:

```bash
pytest                              # Run all tests (333 tests, ~15s)
pytest -v                          # Verbose output
pytest -q                          # Quiet mode, summary only
pytest --tb=no -q                  # Minimal output
pytest tests/test_<name>.py        # Run specific test file
pytest tests/test_<name>.py::test_function  # Run specific test
```

**Important**: Tests use `pytest.ini` which sets `pythonpath = . src`. This ensures imports work correctly.

**Test timing guidelines**:
- Individual test files: 0.2-0.5 seconds
- Performance tests (`test_performance.py`): ~0.7 seconds
- Full suite: 15-20 seconds

**Expected test status**: 333 passed, 19 skipped, 1 warning (about `mixed_liquidity_gated` regime - this is expected)

### Running the Application

**GUI Launcher** (recommended for interactive use):
```bash
python launcher.py
```
Note: Requires display/X11. Will fail in headless environments with ALSA/audio errors (this is normal for GUI apps in headless environments).

**Command-line simulation** (with visualization):
```bash
python main.py scenarios/foundational_barter_demo.yaml --seed 42
```

**Headless execution** (for testing/scripting):
```bash
python scripts/run_headless.py scenarios/foundational_barter_demo.yaml --seed 42 --max-ticks 100
```

**Test scenario loading without GUI**:
```bash
python -c "import sys; sys.path.insert(0, 'src'); from scenarios.loader import load_scenario; s = load_scenario('scenarios/foundational_barter_demo.yaml'); print('Success')"
```

## Project Architecture

### Directory Structure

```
vmt-dev/
├── src/                          # Main source code
│   ├── vmt_engine/              # Core simulation engine (~30 files)
│   │   ├── simulation.py        # Main simulation orchestrator
│   │   ├── core/                # Grid, Agent, State, SpatialIndex
│   │   ├── econ/                # Utility functions (CES, Linear, Quadratic, Translog, Stone-Geary)
│   │   ├── systems/             # 7-phase engine systems
│   │   │   ├── perception.py    # Phase 1: Agent perception
│   │   │   ├── decision.py      # Phase 2: Decision making
│   │   │   ├── movement.py      # Phase 3: Agent movement
│   │   │   ├── matching.py      # Phase 4: Agent pairing
│   │   │   ├── trading.py       # Phase 5: Trade execution
│   │   │   ├── foraging.py      # Phase 6: Resource collection & regeneration
│   │   │   └── housekeeping.py  # Phase 7: State cleanup
│   │   └── protocols/           # Pluggable protocol system (Phase 0 infrastructure)
│   ├── vmt_launcher/            # PyQt6 GUI launcher
│   ├── vmt_pygame/              # Pygame visualization renderer
│   ├── vmt_log_viewer/          # SQLite telemetry viewer GUI
│   ├── telemetry/               # SQLite logging system
│   ├── scenarios/               # Scenario loader and schema validation
│   └── vmt_tools/               # Utility tools
├── tests/                        # 37 test files (333 tests)
│   ├── test_barter_integration.py
│   ├── test_money_phase1_integration.py
│   ├── test_performance.py      # Performance benchmarks
│   └── ...                      # Comprehensive test coverage
├── scenarios/                    # YAML scenario definitions
│   ├── demos/                   # Tutorial scenarios (9 demos)
│   ├── test/                    # Test scenarios
│   └── *.yaml                   # Various scenario files
├── docs/                         # Comprehensive documentation
│   ├── 1_project_overview.md    # Feature walkthrough
│   ├── 2_technical_manual.md    # Implementation details
│   ├── 4_typing_overview.md     # Type system
│   ├── structures/              # Scenario templates and examples
│   └── ssot/                    # Single source of truth docs
├── scripts/                      # Utility scripts
│   ├── run_headless.py          # Headless simulation runner
│   ├── analyze_trade_distribution.py
│   ├── benchmark_performance.py
│   └── ...
├── main.py                       # CLI entry point (with Pygame visualization)
├── launcher.py                   # GUI entry point (PyQt6)
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration (sets pythonpath)
└── .gitignore                    # Git ignore rules
```

### Key Configuration Files

- **pytest.ini**: Sets `pythonpath = . src` for correct import resolution
- **requirements.txt**: All dependencies with version constraints
- **.gitignore**: Excludes venv/, logs/, __pycache__/, .pytest_cache/, etc.

### No Linting Configuration

**Important**: There are **no linting tools** configured in this repository (no .pylintrc, .flake8, mypy.ini, black, etc.). Do not run linters unless explicitly asked. Focus on running tests to validate changes.

## Making Code Changes

### Module Import Pattern

**Critical**: Both `main.py` and `launcher.py` add `src/` to the Python path:

```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
```

When writing code that imports from src/, use this pattern or ensure `src/` is in PYTHONPATH.

### Testing Pattern

**Always run tests after changes**:
1. Make minimal code change
2. Run `pytest tests/test_<relevant>.py` for quick feedback
3. Run `pytest` for full suite validation
4. Check that test count remains 333 passed, 19 skipped

### Common Test Files for Different Changes

- **Core engine changes**: `test_core_state.py`, `test_simulation_init.py`
- **Trade/barter logic**: `test_barter_integration.py`, `test_matching_money.py`
- **Money system**: `test_money_phase1_integration.py`, `test_quotes_money.py`, `test_log_money_utility.py`
- **Utility functions**: `test_utility_ces.py`, `test_utility_linear.py`, etc.
- **Mode/regime system**: `test_mode_integration.py`, `test_mode_regime_interaction.py`
- **Performance**: `test_performance.py` (runs in ~0.7s)
- **Resource system**: `test_resource_regeneration.py`, `test_resource_claiming.py`

### Scenario Files

Scenarios are defined in YAML under `scenarios/`. The loader validates against the schema in `src/scenarios/schema.py`.

**Demo scenarios** (use these as examples):
- `scenarios/demos/demo_01_simple_money.yaml` - Basic money system
- `scenarios/demos/demo_02_barter_vs_money.yaml` - Comparison
- `scenarios/demos/demo_03_mixed_regime.yaml` - Mixed trading
- `scenarios/foundational_barter_demo.yaml` - Classic barter example

**Scenario structure**: See `docs/structures/` for templates and `docs/scenario_configuration_guide.md` for details.

## Common Issues and Workarounds

### Issue: GUI fails with ALSA/audio errors
**Symptom**: `ALSA lib confmisc.c:855:(parse_card) cannot find card '0'`
**Cause**: No audio device in headless/containerized environment
**Workaround**: This is normal for GUI apps in headless environments. Use `scripts/run_headless.py` instead, or ignore the error if running in a desktop environment with audio.

### Issue: Import errors when running scripts
**Symptom**: `ModuleNotFoundError: No module named 'vmt_engine'` or `No module named 'scenarios'`
**Cause**: `src/` not in Python path
**Solution**: Either:
1. Run from repository root with: `python -c "import sys; sys.path.insert(0, 'src'); ..."`
2. Set PYTHONPATH: `export PYTHONPATH="$PWD/src:$PYTHONPATH"`
3. Use pytest which reads pytest.ini

### Issue: Scenario file not found
**Symptom**: `FileNotFoundError: Scenario file not found: scenarios/demos/demo_01_foundational_barter.yaml`
**Cause**: Incorrect scenario path (the file is `foundational_barter_demo.yaml`, not in demos/)
**Solution**: Check exact filename with `ls scenarios/` or `ls scenarios/demos/`. Common scenarios:
- `scenarios/foundational_barter_demo.yaml`
- `scenarios/demos/demo_01_simple_money.yaml`
- `scenarios/three_agent_barter.yaml`

### Issue: Tests fail with "logs already exist" or state issues
**Symptom**: Intermittent test failures related to logging or state
**Cause**: Stale logs/ directory or leftover state
**Solution**: Tests create logs in `logs/` which are gitignored. Clean with: `rm -rf logs/`

### Known Warning in Tests

**Expected warning**: `UserWarning: Unknown exchange_regime 'mixed_liquidity_gated', defaulting to barter_only`
- This appears in `test_mixed_regime_integration.py::test_mixed_liquidity_gated_scenario_loads`
- It is **expected** and indicates Track 2 work is not yet complete
- **Do not fix** this warning unless working on Track 2 liquidity gating feature

## Simulation Engine Details

### 7-Phase Execution

The simulation runs in a deterministic loop with 7 phases per tick:

1. **Perception** (`systems/perception.py`): Agents observe nearby resources and other agents within `vision_radius`
2. **Decision** (`systems/decision.py`): Agents compute utility and make decisions
3. **Movement** (`systems/movement.py`): Agents move toward resources or trade partners
4. **Matching** (`systems/matching.py`): Agents are paired for potential trades based on proximity and quotes
5. **Trading** (`systems/trading.py`): Paired agents negotiate and execute trades using reservation prices
6. **Foraging** (`systems/foraging.py`): Agents collect resources from grid cells; resources regenerate
7. **Housekeeping** (`systems/housekeeping.py`): Update cooldowns, clean up state, log telemetry

### Trade Regimes

- **barter_only**: Agents trade resources A and B directly
- **money_only**: Agents trade resources A or B for money M (quasilinear utility)
- **mixed**: Agents can choose barter or monetary trades (optimal surplus chosen)

### Mode System

- **forage** mode: Only foraging and regeneration phases active (no trading)
- **trade** mode: Only trading phases active (no foraging)
- **both** mode: All phases active (default)

Controlled by `mode_schedule` in scenario config.

### Utility Functions

Implemented in `src/vmt_engine/econ/utility.py`:
- **CES**: Constant Elasticity of Substitution
- **Linear**: Simple linear utility
- **Quadratic**: Quadratic utility (bliss points)
- **Translog**: Transcendental logarithmic
- **Stone-Geary**: Subsistence economy model

All implement `UtilityBase` ABC with `utility()` and `marginal_utility()` methods.

### Telemetry System

- **Database**: SQLite database created in `logs/` directory
- **Schema**: Defined in `src/telemetry/database.py` and `src/vmt_engine/protocols/telemetry_schema.py`
- **Tables**: trades, agent_state, mode_transitions, resource_state
- **Viewer**: `python -m src.vmt_log_viewer.main` (PyQt6 GUI)

## File List Reference

**Root files**:
- main.py, launcher.py, view_logs.py (entry points)
- requirements.txt, pytest.ini, .gitignore (configuration)
- README.md, CHANGELOG.md, LICENSE (documentation)

**Key source files** (most frequently modified):
- `src/vmt_engine/simulation.py` - Main simulation loop
- `src/vmt_engine/core/agent.py` - Agent class
- `src/vmt_engine/core/state.py` - Simulation state
- `src/vmt_engine/systems/trading.py` - Trade execution
- `src/vmt_engine/systems/quotes.py` - Quote computation
- `src/vmt_engine/econ/utility.py` - Utility function implementations
- `src/scenarios/loader.py` - Scenario loading
- `src/scenarios/schema.py` - Scenario validation

**Most commonly edited test files**:
- `tests/test_barter_integration.py`
- `tests/test_money_phase1_integration.py`
- `tests/test_mixed_regime_integration.py`

## Additional Resources

**Documentation to consult**:
- `docs/1_project_overview.md` - Complete feature walkthrough
- `docs/2_technical_manual.md` - Algorithm details and implementation
- `docs/4_typing_overview.md` - Type system and invariants
- `docs/scenario_configuration_guide.md` - How to create scenarios
- `docs/structures/parameter_quick_reference.md` - All parameters

**For implementation examples**: Look at test files in `tests/` - they demonstrate proper API usage.

## Trust These Instructions

These instructions are based on a comprehensive exploration of the repository including:
- Running the full test suite (333 tests)
- Testing installation and setup procedures
- Examining all configuration files
- Reviewing documentation and code structure
- Testing scenario loading and basic functionality

**Only perform additional searches if**:
1. These instructions are incomplete for your specific task
2. You find information that contradicts these instructions
3. You need details about a specific algorithm or implementation

For most code changes, these instructions provide sufficient context to work efficiently without extensive exploration.
