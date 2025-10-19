### Money Implementation — Phase 2 (Atomic): Data → Matching → Integration

Author: VMT Assistant
Date: 2025-10-19

This checklist replaces prior Phase 2 guidance and is aligned with:
- `docs/BIG/implement/phase2_atomic_implementation_plan.md`
- `docs/BIG/implement/phase2_atomic_checklist.md`

It organizes Phase 2 into three atomic sub-phases: 2a (data structures), 2b (generic matching), 2c (integration). Use this as a high-level driver; defer to the implementation plan for details.

---

## Global

- [ ] Environment activated and PYTHONPATH set
- [ ] Baseline `pytest -q` all green (reset telemetry DB if needed)
- [ ] Determinism rules applied (agent/pair sorting, round-half-up, no mid-tick quote mutation)
- [ ] Deprecation policy acknowledged: money-aware APIs are canonical; legacy helpers warn
- [ ] Performance posture: optimization deferred; intervene only if TPS < 5 and blocks progress

---

## 2a — Generalize Core Data Structures (No Behavior Change)

Branch: `YYYY-MM-DD-HHMM-phase2a-data-structures`

Utility/Econ
- [ ] `u_goods`, `mu_A`, `mu_B` added; `u_total` routes via `u_goods`
- [ ] Legacy utility helpers emit `DeprecationWarning`
- [ ] `tests/test_utility_money.py` created and passing

Quotes
- [ ] `Agent.quotes` is `dict[str, float]` (default empty)
- [ ] `compute_quotes` returns barter + money keys; docstrings note deprecations
- [ ] `filter_quotes_by_regime` implemented
- [ ] `tests/test_quotes_money.py` created and passing

Consumers
- [ ] `HousekeepingSystem` computes+filters quotes and assigns dict
- [ ] `db_loggers` reads quotes via `dict.get(...)` safely
- [ ] Any `Quote`-dataclass adapters warn via `DeprecationWarning`

Gates
- [ ] Full suite `pytest -q` green
- [ ] Legacy scenarios unchanged (spot-check telemetry if needed)

---

## 2b — Generic Matching (Isolated, Unit-Tested)

Branch: `YYYY-MM-DD-HHMM-phase2b-generic-trade`

Primitives
- [ ] `find_compensating_block_generic` (pairs: A<->B, A<->M, B<->M)
- [ ] Strict ΔU_i>0 and ΔU_j>0; integer feasibility; stable tie-breaking
- [ ] `find_best_trade` chooses maximal total surplus across allowed pairs
- [ ] `execute_trade` updates inventories; conservation; flags set

Tests
- [ ] `tests/test_matching_money.py` uses mocks; covers `money_only` and `mixed`
- [ ] Determinism and no-trade cases covered

Gates
- [ ] `pytest -q tests/test_matching_money.py` green
- [ ] Legacy suite still green
- [ ] Temporary perf regressions acceptable unless TPS < 5

---

## 2c — Integration + E2E

Branch: `YYYY-MM-DD-HHMM-phase2c-integration`

Integration
- [ ] `TradeSystem` calls `find_best_trade` then `execute_trade`
- [ ] No mid-tick quote mutation; telemetry trade logging includes money as needed
- [ ] `DecisionSystem` decoupled: target selection only

Scenario & Test
- [ ] `scenarios/money_test_basic.yaml` (`exchange_regime: "money_only"`)
- [ ] `tests/test_money_phase2_integration.py` verifies: monetary trades occur; barter blocked; money conserved; determinism with fixed seed

Gates
- [ ] Full `pytest -q` suite green
- [ ] Optional headless run sanity check (`scripts/run_headless.py ... --seed 42`)

---

## Sign-off

- [ ] Determinism verified; legacy compatibility preserved
- [ ] Deprecations in place; documentation updated
- [ ] Performance acceptable for development (TPS ≥ 5)


