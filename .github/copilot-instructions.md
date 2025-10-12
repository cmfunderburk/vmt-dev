# GitHub Copilot Instructions — VMT (Visualizing Microeconomic Theory)

Use these project-specific rules to work productively in this deterministic barter/foraging simulation. Planning specs are in `PLANS/Planning-FINAL.md` and `PLANS/algorithmic_planning.md`. Behaviors are enforced by tests under `tests/`.

## Core architecture and determinism
- **Python 3.11**; deps: `numpy` (engine RNG/arrays), `pyyaml` (scenarios), `pygame` (optional GUI). Use deterministic RNG: `np.random.Generator(np.random.PCG64(seed))` in `vmt_engine/simulation.py`.
- **Fixed tick order** per `Simulation.step()`: Perception → Decision → Movement → Trade → Forage → Housekeeping. Do not reorder.
- **Deterministic iteration**: agents in ascending `agent.id`; trade pairs in ascending `(min_id,max_id)`; use sorted structures, never `dict.values()` or `set` iteration.
- **Module structure**: `vmt_engine/` (simulation core), `scenarios/` (YAML configs), `telemetry/` (CSV logging), `tests/` (pytest suite), `vmt_pygame/` (visualization).

## Utilities, reservation bounds, and quotes
- **Utility families** in `vmt_engine/econ/utility.py`: `UCES` (CES incl. Cobb–Douglas limit via ρ→0) and `ULinear` (perfect substitutes).
- **Family-agnostic API**: Each utility exposes `reservation_bounds_A_in_B(A:int,B:int,eps)` → `(p_min,p_max)`; for CES/Linear these equal MRS but always use the bounds API, never hardcode MRS formulas.
- **Zero-inventory guard**: compute MRS/bounds using `(A+ε,B+ε)` only when A==0 or B==0; keep raw `(A,B)` for `u()` and ΔU checks. Critical: epsilon only shifts ratio calculations, never distorts utility comparisons. See `tests/test_reservation_zero_guard.py`.
- **Quote rule** (`vmt_engine/systems/quotes.py`): `ask = p_min*(1+spread)`, `bid = p_max*(1-spread)`. Refresh quotes after any inventory change (forage or trade) or at housekeeping.

## Partner selection, matching, and trading
- **Surplus overlap** for i vs j: consider `i.bid - j.ask` (i buys from j) and `j.bid - i.ask` (j buys from i); pick the positive maximum. Tie-break by larger surplus, then lower partner id (`systems/matching.py:choose_partner`).
- **Trade cooldown**: skip partners with recent failed trade attempts (tracked per-agent in `agent.trade_cooldowns` dict mapping partner_id → expiry_tick). Default cooldown: 5 ticks (`trade_cooldown_ticks` param).
- **Interaction eligibility**: pairs with Manhattan distance ≤ `interaction_radius` (0=same cell, 1=adjacent). Order candidate pairs by `(min_id,max_id)` before trading.
- **Price search**: searches candidate prices within `[ask_seller, bid_buyer]` range; includes prices yielding integer ΔB values and evenly-spaced samples. Finds mutually beneficial terms despite integer rounding constraints.
- **Quantity rounding**: round-half-up for B per A lots: `ΔB = floor(p*ΔA + 0.5)`; avoid banker's rounding. Portable across platforms. See `tests/test_trade_rounding_and_adjacency.py`.
- **Compensating multi-lot**: scan ΔA = 1..`ΔA_max`; choose first block with strict ΔU>0 for both (via `improves()` checking `u(A+dA,B+dB) > u(A,B)`) and feasible inventories; execute, log. **One trade per tick**: quotes refresh in housekeeping phase; agents can trade again next tick if surplus remains.

## Movement and perception
- **Perception** collects neighbor ids/quotes and visible resource cells within `vision_radius` (`systems/perception.py`). Returns structured data: neighbors list, quotes snapshot, resource view.
- **Movement toward target** uses deterministic Manhattan steps with tie-breaks: reduce |dx| before |dy|; prefer negative direction on ties; if still tied, choose lowest (x,y) (`systems/movement.py`).
- **Foraging movement**: two modes (scenario-configurable): (1) distance-discounted utility-seeking: score = `ΔU_arrival * β^dist`, path to argmax; (2) random-nearest-resource fallback. Uses `beta` parameter for time discounting. **Critical**: ΔU_arrival computed using `min(cell.amount, forage_rate)`, not full cell amount.

## Parameters, scenarios, telemetry
- **Default params** (`scenarios/schema.py`): `spread=0.0`, `epsilon=1e-12`, `ΔA_max=5`, `vision_radius=5`, `interaction_radius=1`, `forage_rate=1`, `move_budget_per_tick=1`, `beta=0.95`, `resource_growth_rate=0`, `resource_max_amount=5`, `resource_regen_cooldown=5`, `trade_cooldown_ticks=5`.
- **Scenarios** live in `scenarios/*.yaml`, loaded/validated by `scenarios/loader.py`/`schema.py`. Keys: `schema_version`, `name`, `N`, `agents`, `initial_inventories` (dict with 'A'/'B' keys; values can be int or list), `utilities.mix[{type,weight,params}]` (weights sum to 1), `params`, `resource_seed{density,amount}`.
- **Utility config examples**: CES: `{type: ces, weight: 0.67, params: {rho: -0.5, wA: 1.0, wB: 1.0}}`; Linear: `{type: linear, weight: 0.33, params: {vA: 1.0, vB: 1.2}}`.
- **Telemetry** writes CSVs under `./logs`: trades (`telemetry/logger.py`), trade attempts (`telemetry/trade_attempt_logger.py`), decisions (`telemetry/decision_logger.py`), and periodic agent/resource snapshots (`telemetry/snapshots.py`). Logs auto-flush for real-time analysis.

## Developer workflow
- **Install and test**: `pip install -r requirements.txt`; run `pytest -v` (set `PYTHONPATH=.` if needed). Key tests: utility CES/Linear, zero-guard, core state, simulation init, M1 foraging, trade rounding, resource regeneration, trade cooldown.
- **Run a scenario**: `python main.py scenarios/three_agent_barter.yaml 42` (GUI via pygame). Controls: SPACE=pause, R=reset, S=step, UP/DOWN=speed, Q=quit.
- **Headless runs**: Import `Simulation` from `vmt_engine.simulation` and call `sim.step()` or `sim.run(max_ticks)` directly.
- **Creating utilities**: Use factory `create_utility(type, params)` from `vmt_engine.econ.utility`; never instantiate `UCES`/`ULinear` directly in systems code.
- **Agent initialization**: Utilities sampled from scenario `utilities.mix` according to weights; inventories distributed from `initial_inventories` dict.

## Do this, not that
- DO derive quotes from reservation bounds; DON'T quote raw MRS directly in systems code.
- DO use round-half-up for integer rounding: `floor(x + 0.5)`; DON'T use banker's rounding or float truncation.
- DO preserve all ordering/tie-break rules and the fixed tick order; DON'T use nondeterministic iteration or data structures.