# VMT Copilot Instructions

## Project Overview
**VMT** is a Python 3.12 spatial agent-based simulation for microeconomic theory. Agents forage resources and trade (barter/monetary) using reservation prices. ~12K LOC, 256 tests, deterministic (same seed = identical results), SQLite telemetry, PyQt5 GUIs, Pygame visualization.

**CRITICAL**: 100% deterministic via fixed 7-phase tick cycle, sorted agent iteration by ID, explicit tie-breaking.

## Environment & Commands (All Validated)
```bash
# Setup (ALWAYS activate venv first)
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt  # pygame numpy pyyaml pytest PyQt5

# Test (256 tests, ~6s, ALWAYS from project root)
pytest                    # All tests
pytest -v                 # Verbose
pytest tests/test_*.py    # Specific file

# Run
python launcher.py                      # GUI launcher
python main.py scenarios/three_agent_barter.yaml --seed 42  # CLI+viz
python scripts/run_headless.py <scenario> --seed 42 --max-ticks 100  # Headless
python view_logs.py                     # Log viewer GUI

# Generate scenarios
python3 -m src.vmt_tools.generate_scenario my_test --agents 20 --grid 30 \
  --inventory-range 10,50 --utilities ces,linear --resources 0.3,5,1 --seed 42
```
**Note**: All entry points auto-add `src/` to sys.path. Python 3.11+ required.

## Structure
```
vmt-dev/
├── main.py, launcher.py, view_logs.py  # Entry points (auto-add src/ to path)
├── requirements.txt, pytest.ini        # Deps, pytest config (pythonpath = . src)
├── src/
│   ├── vmt_engine/                     # Core engine
│   │   ├── core/                       # agent.py, grid.py, state.py
│   │   ├── econ/utility.py             # 5 utility functions (UCES, ULinear, UQuadratic, UTranslog, UStoneGeary)
│   │   ├── systems/                    # matching.py (trade), quoting.py, movement.py
│   │   └── simulation.py               # Main loop (7-phase tick cycle)
│   ├── scenarios/                      # schema.py (YAML validation), loader.py
│   ├── telemetry/                      # database.py (SQLite schema), config.py
│   └── vmt_tools/generate_scenario.py  # CLI scenario generator
├── scenarios/                          # YAML files (three_agent_barter.yaml = default)
├── tests/                              # 256 tests (test_*.py)
├── scripts/run_headless.py             # Headless runner
├── logs/telemetry.db                   # Runtime SQLite (not in git)
└── docs/                               # Start with quick_reference.md, then 2_technical_manual.md
```

## 7-Phase Tick (NEVER REORDER)
Critical for determinism (`src/vmt_engine/simulation.py::Simulation.step()`):
1. **Perception**: Frozen snapshot (neighbors, resources)
2. **Decision**: Rank preferences, form trade pairs (3-pass: mutual consent → surplus-based fallback)
3. **Movement**: Move toward targets (tie-break: x-axis first, negative dir, lower ID wins)
4. **Trade**: Paired agents attempt trades (generic matching: A↔B, A↔M, B↔M)
5. **Foraging**: Harvest resources (single-harvester: lowest ID wins)
6. **Regen**: Harvested cells regenerate after cooldown
7. **Housekeeping**: Refresh quotes, log telemetry, check pairing integrity

**Key files**: `simulation.py::step()`, `systems/matching.py::find_best_trade()`, `systems/quoting.py`

## Architecture Patterns

**1. Determinism (SACRED)**
- ALWAYS iterate agents sorted by `agent.id`
- ALWAYS iterate pairs sorted by `(min_id, max_id)`
- NEVER rely on dict/set order without sorting
- Tie-break: x before y, negative dir, lower ID wins

**2. Utility API** (`src/vmt_engine/econ/utility.py`): 5 types (UCES, ULinear, UQuadratic, UTranslog, UStoneGeary)
```python
u_goods(A, B) -> float              # Canonical
mu_A(A, B), mu_B(A, B) -> float     # Marginals
reservation_bounds_A_in_B(A, B, eps) -> (p_min, p_max)
```

**3. Money System** (Phases 1-2 complete)
- Quasilinear: `U_total = U_goods(A,B) + λ·M` (λ=1.0 default)
- Regimes: `"barter_only"` (default), `"money_only"`, `"mixed"` (Phase 3 in progress)
- Quotes: `Agent.quotes: dict[str, float]` (e.g., "ask_A_in_B", "bid_B_in_M")
- Telemetry: `trades.dM`, `trades.exchange_pair_type`

**4. Scenarios** (`src/scenarios/schema.py`): YAML with `schema_version: 1`, heterogeneous agents via `utilities.mix`, auto-validated on load

**5. Telemetry**: SQLite `logs/telemetry.db` (schema in `telemetry/database.py`), tables: `simulation_runs`, `agent_snapshots`, `trades`, `decisions`, `pairings`, `tick_states`

## Common Pitfalls

**Import errors**: Entry points auto-add `src/` to path. For standalone scripts: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))`

**Test failures**: `pytest.ini` sets `pythonpath = . src`. ALWAYS run from project root with venv active.

**Breaking determinism**: Check unsorted iteration (agents/pairs), non-deterministic RNG (use `sim.rng`), ambiguous tie-breaks. Test: run same seed twice, compare telemetry.

**Backward compat**: Money fields default to legacy (`exchange_regime="barter_only"`, `M=0`). Verify with `tests/test_money_phase1_integration.py::test_legacy_scenario_unchanged`.

**Phase confusion**: Multiple numbering schemes exist. Always prefix: "Money Phase 3", "Scenario Gen Phase 2". See `docs/quick_reference.md`.

## Validation Checklist
1. `pytest` (256 tests, ~6s) - ALL must pass
2. Test determinism: same seed → identical telemetry
3. Performance: For core changes, run `scripts/benchmark_performance.py`
4. Update schema: If adding fields, edit `src/telemetry/database.py`
5. Document: Update `docs/2_technical_manual.md` for engine changes

**No CI/CD**: All validation is local. No linter configured (rely on tests).

## Status & Priorities
**✅ Done**: Money Phases 1-2, Scenario Gen Phase 1
**📋 Next**: Money Phase 3 (mixed regimes), then Scenario Gen Phase 2
**⏸️ Deferred**: Protocol modularization, Money Phases 5-6 (Track 2)
**See**: `docs/decisions/001-hybrid-money-modularization-sequencing.md`

## Final Notes
- **Trust this doc**: Only search if incomplete/incorrect
- **Docs**: Start `docs/quick_reference.md` → `2_technical_manual.md`
- **Versioning**: Pre-release. Use date+time IDs (e.g., `2025-10-19-1430`), NOT SemVer
- **Determinism is sacred**: Breaking it = rejected. Always verify with seed tests
- **SQLite > CSV**: ~99% size reduction. Don't revert without justification

