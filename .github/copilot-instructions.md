# GitHub Copilot Instructions — VMT (Visualizing Microeconomic Theory)

Use these project-specific rules to work productively in this deterministic barter/foraging simulation. Planning specs are in `Planning-FINAL.md` and `algorithmic_planning.md`. Behaviors are enforced by tests under `tests/`.

Core architecture and determinism
- Python 3.11; deps: `numpy` (engine RNG/arrays), `pyyaml` (scenarios), `pygame` (optional GUI). Use deterministic RNG: `np.random.Generator(np.random.PCG64(seed))` in `vmt_engine/simulation.py`.
- Fixed tick order per `Simulation.step()`: Perception → Decision → Movement → Trade → Forage → Housekeeping. Do not reorder.
- Iterate agents in ascending `agent.id`; process trade pairs in ascending `(min_id,max_id)` for determinism.

Utilities, reservation bounds, and quotes
- Utilities in `vmt_engine/econ/utility.py`: `UCES` (CES incl. Cobb–Douglas limit via ρ→0) and `ULinear`.
- Each utility exposes `reservation_bounds_A_in_B(A:int,B:int,eps)` → `(p_min,p_max)`; for CES/Linear these equal MRS but still use the bounds API.
- Zero-inventory guard: compute MRS/bounds using `(A+ε,B+ε)` only when A==0 or B==0; keep raw `(A,B)` for `u()` and ΔU checks. See `tests/test_reservation_zero_guard.py`.
- Quote rule (`vmt_engine/systems/quotes.py`): `ask = p_min*(1+spread)`, `bid = p_max*(1-spread)`. Refresh quotes after any inventory change (forage or trade) or at housekeeping.

Partner selection, matching, and trading
- Surplus overlap for i vs j: consider `i.bid - j.ask` and `j.bid - i.ask`; pick the positive maximum. Tie-break by larger surplus, then lower partner id (`systems/matching.py:choose_partner`).
- Interaction eligibility: pairs with Manhattan distance ≤ `interaction_radius` (0=same cell, 1=adjacent). Order candidate pairs by `(min_id,max_id)` before trading.
- Price: midpoint of crossed quotes in chosen direction.
- Quantity rounding: round-half-up for B per A lots: `ΔB = floor(p*ΔA + 0.5)`; avoid banker’s rounding. See `tests/test_trade_rounding_and_adjacency.py`.
- Compensating multi-lot: scan ΔA = 1..`ΔA_max`; choose first block with strict ΔU>0 for both and feasible inventories; execute, log, refresh quotes, then repeat while surplus remains.

Movement and perception
- Perception collects neighbor ids/quotes and visible resource cells within `vision_radius` (`systems/perception.py`).
- Movement toward target uses deterministic Manhattan steps with tie-breaks: reduce |dx| before |dy|; prefer negative direction on ties (`systems/movement.py`).

Parameters, scenarios, telemetry
- Default params (`scenarios/schema.py`): `spread=0.05`, `epsilon=1e-12`, `ΔA_max=5`, `vision_radius=5`, `interaction_radius=1`, `forage_rate=1`, `move_budget_per_tick=1`, `beta=0.95`.
- Scenarios live in `scenarios/*.yaml`, loaded/validated by `scenarios/loader.py`/`schema.py`. Keys: `schema_version`, `name`, `N`, `agents`, `initial_inventories`, `utilities.mix[{type,weight,params}]` (weights sum to 1), `params`, `resource_seed{density,amount}`.
- Telemetry writes CSVs under `./logs`: trades (`telemetry/logger.py`) and periodic agent/resource snapshots (`telemetry/snapshots.py`).

Developer workflow
- Install and test: `pip install -r requirements.txt`; run `pytest -v` (set `PYTHONPATH=.` if needed). Key tests: utility CES/Linear, zero-guard, core state, simulation init, M1 foraging.
- Run a scenario: `python main.py scenarios/three_agent_barter.yaml 42` (GUI via pygame). Headless runs can import `Simulation` directly.

Do this, not that
- DO derive quotes from reservation bounds; DON’T quote raw MRS directly in systems code.
- DO keep midpoint pricing + round-half-up; DON’T use banker’s rounding or float truncation.
- DO preserve all ordering/tie-break rules and the fixed tick order; DON’T use nondeterministic iteration or data structures.