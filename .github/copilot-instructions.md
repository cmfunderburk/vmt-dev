## Copilot instructions for VMT (Visualizing Microeconomic Theory)

### Big picture
- **Engine**: Deterministic, discrete-time ABM on an `N×N` grid with a fixed 7-phase tick: Perception → Decision → Movement → Trade → Forage → Resource Regeneration → Housekeeping. See `src/vmt_engine/simulation.py` and `src/vmt_engine/systems/*`.
- **Determinism rules**: Always process agents sorted by `agent.id`, trade pairs sorted by `(min_id,max_id)`, round quantities with round-half-up, never mutate quotes mid-tick (quotes refresh in Housekeeping). Spatial queries use a bucketed `SpatialIndex` for O(N) average proximity checks.
- **Data flow**: YAML scenario → `src/scenarios/loader.py` → `Simulation(...)` creates `Grid`, `Agent`s, `SpatialIndex`, and starts telemetry. Systems advance the world; telemetry batches to SQLite (`./logs/telemetry.db`).

### Where to start
- **CLI with visualization**: `python main.py scenarios/three_agent_barter.yaml --seed 42` (Pygame renderer in `src/vmt_pygame/renderer.py`).
- **GUI launcher**: `python launcher.py` (PyQt UI in `src/vmt_launcher/`), includes a scenario builder.
- **Log viewer**: `python view_logs.py` (PyQt viewer in `src/vmt_log_viewer/`).
- **Docs hub**: `docs/README.md` → overview, technical manual, and type contracts in `docs/4_typing_overview.md`.

### Core conventions (project-specific)
- **Types/invariants**: Inventories and resources are integers; spatial params (`vision_radius`, `interaction_radius`, `move_budget_per_tick`) are integers. Utility returns floats; prices are floats. Quote fields `ask_A_in_B ≥ p_min`, `bid_A_in_B ≤ p_max`. See `src/vmt_engine/core/state.py` and `docs/4_typing_overview.md`.
- **Quotes**: Compute from reservation bounds with optional spread; recompute only when `agent.inventory_changed` is set. See `src/vmt_engine/systems/quotes.py` and `HousekeepingSystem`.
- **Trading**: One trade attempt per pair per tick. Price search tests integer feasibility via `find_compensating_block` scanning `ΔA ∈ [1..dA_max]` and candidate prices; `ΔB = floor(price*ΔA + 0.5)` (round-half-up). Failed attempts set mutual cooldown (`trade_cooldown_ticks`). See `src/vmt_engine/systems/matching.py` and `trading.py`.
- **Movement**: Manhattan steps with tie-breakers (reduce |dx| before |dy|; prefer negative direction on ties). Diagonal deadlock resolution: the higher `agent.id` moves. See `src/vmt_engine/systems/movement.py`.
- **Perception**: Use `SpatialIndex.query_radius`; treat quotes as stable within the tick. See `src/vmt_engine/systems/perception.py` and `core/spatial_index.py`.

### Architecture map (by responsibility)
- **Core**: `src/vmt_engine/core/` (`Agent`, `Inventory`, `Quote`, `Grid`, `SpatialIndex`).
- **Economics**: `src/vmt_engine/econ/utility.py` with `UCES` and `ULinear`; `create_utility` factory. CES MRS uses zero-safe epsilon only for the ratio (not for utility itself).
- **Systems**: `src/vmt_engine/systems/` for the 7 phases; trading uses surplus-based partner choice and integer-compensating search.
- **Scenarios**: `src/scenarios/schema.py` (dataclass schema, validation), `loader.py` (supports `dA_max` and legacy `ΔA_max`).
- **Telemetry**: `src/telemetry/` (`LogConfig`, `TelemetryManager`, `TelemetryDatabase`) batching to SQLite; renderer reads `recent_trades_for_renderer`.

### Developer workflows
- **Setup**:
  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ```
- **Run tests**: `pytest -q` (see `pytest.ini` sets `pythonpath = . src`).
- **Programmatic run**:
  ```python
  from vmt_engine.simulation import Simulation
  from scenarios.loader import load_scenario
  from telemetry.config import LogConfig
  sim = Simulation(load_scenario("scenarios/three_agent_barter.yaml"), seed=42, log_config=LogConfig.debug())
  sim.run(max_ticks=100)
  ```
- **View telemetry**: open `./logs/telemetry.db` in the viewer (`python view_logs.py`), or export via the viewer’s CSV tool.

### Implementation tips for this codebase
- **Maintain determinism**: sort all new agent loops and pair loops; avoid nondeterministic dict iteration for side effects.
- **Respect integer math**: keep goods/quantities/positions as ints; preserve round-half-up when mapping prices to quantities.
- **Only refresh quotes in Housekeeping**: set `inventory_changed=True` when inventories mutate; don’t recompute quotes mid-tick.
- **Use `SpatialIndex`** for proximity; don’t hand-roll O(N²) scans.
- **Follow system order** when adding/altering phases; update `Simulation.systems` explicitly.

### Versioning policy
- **No SemVer or numeric versions** until explicitly authorized by the maintainer. Treat the project as pre-release.
- **Use date+time-based naming** for versions/artifacts (e.g., `2025-10-19-1430`) in docs, branches, tags, and snapshot files.
- Do not add or update version badges or release labels; consider any existing ones as legacy and do not modify them.
- In PRs and changelogs, reference changes by date-time identifiers rather than version numbers.


