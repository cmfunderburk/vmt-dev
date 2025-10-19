# Copilot instructions for vmt-dev (VMT)

These are concise, project-specific rules to make AI agents productive in this repo. Prefer concrete references below over generic advice.

## Project shape and architecture
- Core engine: `src/vmt_engine/` (tick loop in `simulation.py`; core types under `core/`; systems per phase under `systems/`).
- Scenarios: `src/scenarios/` (`schema.py` for validation, `loader.py` reads YAML under `scenarios/` at repo root).
- Telemetry: `src/telemetry/` (SQLite schema in `database.py`, writers in `db_loggers.py`, config in `config.py`). DB file: `./logs/telemetry.db`.
- Launchers/UI: `main.py` (CLI viz), `launcher.py` (GUI), `view_logs.py` (log viewer), `src/vmt_pygame`, `src/vmt_launcher`, `src/vmt_log_viewer`.

## The 7-phase tick (sacred order)
Perception → Decision → Movement → Trade → Forage → Resource Regeneration → Housekeeping.
- Determinism rules (must hold):
  - Process agents sorted by `agent.id`; trade pairs sorted by `(min_id, max_id)`.
  - Quotes are read-only within a tick; recompute only in Housekeeping.
  - Exactly one trade attempt per pair per tick; failed attempts set mutual cooldown.
  - Use SpatialIndex (`core/spatial_index.py`) for neighbor queries and pair construction (avoid O(N^2)).
  - Integer mapping for quantities uses round-half-up: `floor(x + 0.5)`.

## Data and invariants
- Integers: inventories/resources/positions and spatial params (`vision_radius`, `interaction_radius`, `move_budget_per_tick`).
- Floats: prices, utilities, spreads, lambda (money mode).
- Set `agent.inventory_changed = True` whenever inventories mutate; quotes refresh in Housekeeping only.

## Patterns you must follow (with file anchors)
- Movement tie-breakers: reduce |dx| before |dy|; prefer negative on ties; diagonal deadlock rule (see `systems/movement.py`).
- Trading: price/quantity search with compensating blocks; map price→integer ΔB with round-half-up; one attempt per pair (see `systems/trading.py`).
- Partner choice: choose best surplus; break ties by lowest partner id; honor cooldowns (see `systems/decision.py`).
- Spatial queries: always via `core/spatial_index.py` (`query_radius`, `query_pairs_within_radius`).

## Money and modes (present, backward compatible)
- `Inventory` includes integer `M` (money). `exchange_regime` controls allowed pairs: `barter_only` (default), `money_only`, `mixed`, etc.
- Mode schedule controls WHEN activities occur; regime controls WHAT can be exchanged (see docs and `systems/quotes.py`, `systems/trading.py`).

## Running, testing, debugging
- Use this venv name: `venv` (not `.venv`). Activate before anything: `source venv/bin/activate`.
- Install deps: `pip install -r requirements.txt`.
- Run: `python launcher.py` (GUI) or `python main.py scenarios/three_agent_barter.yaml --seed 42`.
- Programmatic use requires PYTHONPATH: `PYTHONPATH=.:src` when running ad hoc scripts.
- Tests: `pytest -q` (configured via `pytest.ini` with `pythonpath = . src`). For a single test: `pytest tests/test_barter_integration.py -v`.
- Critical DB gotcha: if you see SQLite schema errors (e.g., missing columns), delete the local DB: `rm logs/telemetry.db` and re-run.

## Conventions and non-goals
- Determinism over cleverness: avoid nondeterministic dict iteration for side effects; keep all loops explicitly ordered.
- Versioning: do NOT add SemVer. Use date+time identifiers (e.g., `2025-10-19-1430`) in docs/tags/branches when needed.

## Minimal examples
- Programmatic run:
  ```python
  from vmt_engine.simulation import Simulation
  from scenarios.loader import load_scenario
  from telemetry.config import LogConfig
  sim = Simulation(load_scenario("scenarios/three_agent_barter.yaml"), seed=42, log_config=LogConfig.debug())
  sim.run(max_ticks=100)
  ```
- Deterministic quantity mapping:
  ```python
  from math import floor
  def round_half_up(x: float) -> int: return floor(x + 0.5)
  ```

If any section above is unclear or missing context (e.g., specific system files differ), tell me which part to refine and I’ll update this guide accordingly.
