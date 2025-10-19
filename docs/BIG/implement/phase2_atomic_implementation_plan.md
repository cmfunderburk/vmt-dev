### VMT Money System — Phase 2 Atomic Implementation Plan (2a → 2b → 2c)

Author: Solo Developer Plan
Date: 2025-10-19

This plan operationalizes the revised Phase 2 approach described in `docs/BIG/phase2_postmortem.md` and `docs/BIG/phase2/implementation_plan.md`. It is designed for a single developer to implement with maximal safety, determinism, and backward compatibility.

It splits Phase 2 into three atomic sub-phases:
- 2a: Generalize core data structures (Utility, Quotes) without changing behavior
- 2b: Implement generic trading logic in isolation (pure unit tests with mocks)
- 2c: Integrate generic trading into the simulation and verify end-to-end

Follow the critical invariants and policies in `.cursor/rules/money-guide.mdc` and the always-applied workspace rules.

---

## Global Prerequisites and Conventions

- Activate environment and set Python path
  ```bash
  source venv/bin/activate
  export PYTHONPATH=.:src
  ```

- Run a clean test baseline
  ```bash
  pytest -q
  ```
  If you hit SQLite schema issues, reset telemetry DB:
  ```bash
  rm logs/telemetry.db && pytest -q
  ```

- Determinism and ordering (non-negotiable)
  - Always process agents sorted by `agent.id`
  - Always process trade pairs sorted by `(min_id, max_id)`
  - Use round-half-up for integerization: `floor(price * Δ + 0.5)`
  - Never mutate quotes mid-tick; refresh only in Housekeeping
  - Set `agent.inventory_changed = True` on any inventory change

- Type invariants
  - Integers: inventories (A, B), resources, positions, radii/budgets
  - Floats: utilities, prices, asks/bids

- Deprecation policy (canonicalization)
  - The money-aware APIs introduced in Phase 2 are the new canonical behavior.
  - Legacy aliases and code paths should be explicitly deprecated (warnings) once the equivalent money-aware path exists and is covered by tests.
  - Removal of deprecated symbols is deferred until after Phase 2 completes and a deprecation window is announced.

- Performance posture
  - Optimization is deferred until the money system is functionally complete.
  - Only intervene early if development throughput is blocked (e.g., sustained < 5 ticks/sec on standard test scenarios).

- Branch naming (policy)
  - Use date-time-based names per project policy, e.g.: `2025-10-19-1430-phase2a-data-structures`
  - Replace placeholders below with your current date-time

- Backward compatibility gates
  - Default `exchange_regime: "barter_only"`
  - Money fields default to 0 or NULL
  - All legacy scenarios must run identically in 2a (no behavior change)

---

## Phase 2a — Generalize Core Data Structures (No Behavior Change)

Goal: Make the codebase “money-aware” while preserving current behavior. All existing tests must remain green. New unit tests cover the economic primitives and quotes math.

Branch: `2025-10-19-1430-phase2a-data-structures`

### Step 2a.1 — Refactor `utility.py`

Files:
- `src/vmt_engine/econ/utility.py`

Actions:
- Introduce `u_goods(inventory_a: int, inventory_b: int, params) -> float`
- Introduce analytic marginal utilities `mu_A(...) -> float`, `mu_B(...) -> float`
- Introduce a top-level `u_total(inventory, params) -> float` that delegates to `u_goods` (future-proofing for money, but returns the legacy result now)
- Preserve existing public signatures used by legacy code; route through the new primitives to avoid breaking imports
- Add `DeprecationWarning` to any legacy-specific helpers that Phase 2 supersedes, pointing callers to the money-aware equivalents
- Ensure zero-safe handling (epsilons) remains correct and deterministic

Tests:
- Add `tests/test_utility_money.py` covering:
  - Consistency: `u_total` equals legacy utility for representative points
  - Monotonicity and diminishing MU where applicable
  - `mu_A`, `mu_B` signs and comparative statics

Gate:
- `pytest -q` (legacy suite) must remain green
- `pytest -q tests/test_utility_money.py` must pass

### Step 2a.2 — Generalize `Agent.quotes` to a dictionary

Files:
- `src/vmt_engine/core/agent.py`

Actions:
- Change `Agent.quotes` type to `dict[str, float]`
- Keep default empty dict and ensure construction is deterministic
- Do not remove legacy attributes that other modules may rely on in this phase; only provide the dict and adjust the quote producers/consumers listed below

### Step 2a.3 — Rewrite `compute_quotes` and add `filter_quotes_by_regime`

Files:
- `src/vmt_engine/systems/quotes.py`

Actions:
- Update `compute_quotes(agent, params) -> dict[str, float]` to return a dictionary with keys for both barter and monetary pairs:
  - `ask_A_in_B`, `bid_A_in_B`, `ask_B_in_A`, `bid_B_in_A`
  - `ask_A_in_M`, `bid_A_in_M`, `ask_B_in_M`, `bid_B_in_M`
- Add `filter_quotes_by_regime(quotes: dict[str, float], regime: str) -> dict[str, float]` that hides monetary keys unless `regime in {"mixed", "money_only"}`; defaults maintain exact legacy visibility for `"barter_only"`
- Ensure no in-tick mutation; compute only when `agent.inventory_changed` or on scheduled refresh in Housekeeping
- Add deprecation notes in docstrings where legacy quote access patterns are superseded; consumers should use the dict keys and regime filter

Tests:
- Add `tests/test_quotes_money.py` covering:
  - Arithmetic correctness for all returned keys under simple synthetic parameters
  - Visibility filtering by `exchange_regime`
  - Deterministic stability given fixed seeds and inputs

### Step 2a.4 — Update consumers: Housekeeping and Telemetry

Files:
- `src/vmt_engine/systems/housekeeping.py`
- `src/telemetry/db_loggers.py`

Actions:
- Housekeeping: call `compute_quotes` and immediately pass through `filter_quotes_by_regime` depending on scenario params; assign back to `agent.quotes`
- Telemetry agent snapshot logging: when reading quotes, use `dict.get(key)` to avoid KeyError for regime-hidden keys; do not change DB schema yet
- If any consumer relies on legacy `Quote` dataclass attributes, retain a thin adapter with `DeprecationWarning` and migrate usages to dict-based access in subsequent edits

Gate:
- Full suite green: `pytest -q`
- No change in legacy scenario outputs (run a representative legacy scenario before/after and compare telemetry snapshots if needed)

Definition of Done (2a):
- All legacy tests pass identically
- New unit tests for utility and quotes pass
- No regression in performance or determinism

---

## Phase 2b — Generic Trading Logic (Isolated, Unit-Tested with Mocks)

Goal: Build and prove the regime-generic trading primitives without touching the simulation loop.

Branch: `2025-10-19-1430-phase2b-generic-trade` (branch from 2a)

### Step 2b.1 — Implement generic matching primitives

Files:
- `src/vmt_engine/systems/matching.py`

Actions:
- Add `find_compensating_block_generic(agent_i, agent_j, pair: str, quotes_i: dict, quotes_j: dict, params) -> tuple | None`
  - `pair` ∈ {`"A<->B"`, `"A<->M"`, `"B<->M"`}
  - Scan admissible integer trade blocks (ΔA ∈ [1..dA_max], derive ΔB or ΔM by price using round-half-up)
  - Compute each agent’s ΔU via `u_total` and select integer-feasible blocks with ΔU_i > 0 and ΔU_j > 0
  - Return the block with maximal total surplus (ΔU_i + ΔU_j) for that pair, with stable tie-breaking
- Add `find_best_trade(agent_i, agent_j, regime: str, params) -> tuple | None`
  - Enumerate candidate pairs allowed by `regime`
  - Call `find_compensating_block_generic` per pair
  - Choose globally maximal surplus with stable tie-breaking (price, seller_id)
- Add `execute_trade(state, agent_i, agent_j, trade) -> None`
  - Apply integer inventory updates
  - Preserve invariants: non-negativity, conservation (for goods and money), set `inventory_changed`

Constraints:
- Determinism: fixed orderings; no nondeterministic dict iteration for side-effects
- Performance: aim for O(N) average scans; tolerate slower performance during development unless TPS drops below ~5 on standard tests

### Step 2b.2 — Unit tests with mocks

Files:
- `tests/test_matching_money.py`

Actions:
- Create tiny mock `Agent` objects with pre-filled inventories and quotes dicts
- Test `money_only` and `mixed` regimes across cases:
  - Monetary trade dominates barter under certain prices
  - No-trade when no positive-sum block exists
  - Tie-breaking is stable and deterministic
- Verify `execute_trade` preserves integer feasibility, non-negativity, and conservation

Gate:
- `pytest -q tests/test_matching_money.py`
- No changes to legacy test outcomes

Definition of Done (2b):
- Matching primitives fully covered by unit tests
- Deterministic, integer-feasible, and performance-conscious

---

## Phase 2c — Integration into Simulation + E2E Verification

Goal: Replace bespoke trade evaluation with generic logic; keep `DecisionSystem` simple and decoupled.

Branch: `2025-10-19-1430-phase2c-integration` (branch from 2b)

### Step 2c.1 — Integrate into `TradeSystem`

Files:
- `src/vmt_engine/systems/trading.py`

Actions:
- In the trading loop, call `find_best_trade` for candidate pairs selected by spatial/matching policy
- If a trade is returned, call `execute_trade`, then invoke telemetry `log_trade` with monetary details if present
- Ensure per-tick quote refresh policy remains unchanged (no mid-tick mutations)

### Step 2c.2 — Decouple `DecisionSystem`

Files:
- `src/vmt_engine/systems/decision.py`

Actions:
- Remove/avoid embedded trade evaluation logic
- Keep responsibility to target a potential partner (spatial/heuristic), leaving all trade evaluation to `matching.py`

### Step 2c.3 — Minimal money scenario and E2E test

Files:
- `scenarios/money_test_basic.yaml`
- `tests/test_money_phase2_integration.py`

Actions:
- Scenario: set `exchange_regime: "money_only"`, small grid, few agents with initial `inventory.M > 0` and simple preferences
- Integration test assertions:
  - Monetary trades occur; barter is blocked
  - Money conservation across the system
  - Determinism with fixed seed (e.g., 42)

Gate:
- `pytest -q` (full suite)
- Run the scenario headless if desired:
  ```bash
  python scripts/run_headless.py scenarios/money_test_basic.yaml --seed 42
  ```

Definition of Done (2c):
- End-to-end monetary trading works in `money_only`; legacy behavior preserved elsewhere
- All tests green (legacy + new unit + integration)

---

## Risk Management and Rollback

- Keep each sub-phase on its own branch and merge only after gates are green
- If 2a breaks legacy tests, revert to pre-2a baseline and minimize the surface of change (focus first on `utility.py` tests, then `quotes.py`)
- If 2b primitives are hard to validate, expand unit tests before integration; do not proceed to 2c with uncertainty
- If 2c introduces regressions, bisect by temporarily swapping back to legacy trading to isolate integration faults

---

## Deliverables Checklist (Artifacts per Sub-Phase)

- 2a
  - `tests/test_utility_money.py`
  - `tests/test_quotes_money.py`
  - Updated `utility.py`, `agent.py`, `quotes.py`, `housekeeping.py`, `db_loggers.py`

- 2b
  - `matching.py` functions: `find_compensating_block_generic`, `find_best_trade`, `execute_trade`
  - `tests/test_matching_money.py`

- 2c
  - Updated `trading.py`, simplified `decision.py`
  - `scenarios/money_test_basic.yaml`
  - `tests/test_money_phase2_integration.py`

---

## Appendix A — Quotes Dictionary Keys (canonical)

- Barter pairs
  - `ask_A_in_B`, `bid_A_in_B`
  - `ask_B_in_A`, `bid_B_in_A`

- Monetary pairs
  - `ask_A_in_M`, `bid_A_in_M`
  - `ask_B_in_M`, `bid_B_in_M`

Notes:
- Keys may be filtered out by `filter_quotes_by_regime` for backward compatibility
- Prices are floats; conversions to integer quantities use round-half-up

---

## Appendix B — Commands Reference

```bash
# Environment
source venv/bin/activate
export PYTHONPATH=.:src

# Test suites
pytest -q
pytest -q tests/test_utility_money.py
pytest -q tests/test_quotes_money.py
pytest -q tests/test_matching_money.py

# Headless demo (post-integration)
python scripts/run_headless.py scenarios/money_test_basic.yaml --seed 42
```


