### Phase 2 Atomic Checklist (2a → 2b → 2c)

Use this checklist alongside `docs/BIG/implement/phase2_atomic_implementation_plan.md`.
Mark each box only when the gate conditions are fully met.

---

## Global

- [ ] `source venv/bin/activate` and `export PYTHONPATH=.:src`
- [ ] Baseline `pytest -q` all green
- [ ] If telemetry schema error: `rm logs/telemetry.db` then re-run tests
- [ ] Determinism rules acknowledged and applied (agent sorting, pair sorting, round-half-up, no mid-tick quote mutation)
- [ ] Deprecation policy acknowledged: money-aware APIs are canonical; legacy paths warned
- [ ] Performance posture: optimization deferred unless TPS < 5 blocks progress

---

## Phase 2a — Data Structures (No Behavior Change)

Branch: `YYYY-MM-DD-HHMM-phase2a-data-structures`

Utility
- [ ] `u_goods` added and returns legacy-consistent values
- [ ] `mu_A`, `mu_B` implemented and tested
- [ ] `u_total` routes through `u_goods`; legacy signatures preserved
- [ ] Legacy helper paths emit `DeprecationWarning` directing to money-aware APIs
- [ ] `tests/test_utility_money.py` created and passing

Agent & Quotes
- [ ] `Agent.quotes` converted to `dict[str, float]` (default empty)
- [ ] `compute_quotes` returns barter + monetary keys
- [ ] `filter_quotes_by_regime` implemented and used
- [ ] Docstrings note deprecation of legacy quote access patterns; prefer dict-based
- [ ] `tests/test_quotes_money.py` created and passing

Consumers
- [ ] `HousekeepingSystem` computes and filters quotes; assigns to `agent.quotes`
- [ ] `db_loggers` reads quotes via `dict.get(...)` safely
- [ ] Any legacy `Quote` dataclass adapters emit `DeprecationWarning`

Gates
- [ ] Full suite `pytest -q` green
- [ ] Legacy scenario(s) produce identical behavior (spot-check telemetry)

---

## Phase 2b — Generic Trading (Isolated Unit Tests)

Branch: `YYYY-MM-DD-HHMM-phase2b-generic-trade`

Primitives
- [ ] `find_compensating_block_generic` implemented (pairs: A<->B, A<->M, B<->M)
- [ ] Integer feasibility, ΔU_i>0 and ΔU_j>0 enforced
- [ ] Stable tie-breaking implemented
- [ ] `find_best_trade` enumerates regime-allowed pairs and selects max total surplus
- [ ] `execute_trade` updates inventories, conserves goods/money, sets flags

Tests
- [ ] `tests/test_matching_money.py` created with mocks
- [ ] Covers `money_only` and `mixed` regimes
- [ ] Tests determinism, no-trade cases, and tie-breaking

Gates
- [ ] `pytest -q tests/test_matching_money.py` green
- [ ] Legacy suite still green
- [ ] Accept temporary perf regressions unless TPS < 5 on standard tests

---

## Phase 2c — Integration + E2E

Branch: `YYYY-MM-DD-HHMM-phase2c-integration`

Integration
- [ ] `TradeSystem` uses `find_best_trade` and `execute_trade`
- [ ] No mid-tick quote mutation; telemetry `log_trade` updated for money
- [ ] `DecisionSystem` simplified to target selection only

Scenario & Test
- [ ] `scenarios/money_test_basic.yaml` created (`exchange_regime: "money_only"`)
- [ ] `tests/test_money_phase2_integration.py` created
- [ ] Verifies monetary trades occur; barter blocked; money conserved; determinism

Gates
- [ ] Full `pytest -q` suite green
- [ ] Optional headless run passes sanity checks

---

## Sign-off

- [ ] Performance: no O(N²) regressions; spatial queries remain efficient
- [ ] Determinism verified with fixed seeds
- [ ] Backward compatibility preserved for legacy scenarios
- [ ] Documentation updated where applicable


