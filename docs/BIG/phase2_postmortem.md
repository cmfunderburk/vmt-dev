### Post-Mortem and Revised Plan for Money Implementation Phase 2

Author: VMT Assistant
Date: 2025-10-19

## 1. Overview

The initial attempt to implement Phase 2 (Monetary Exchange Basics) resulted in a cascade of test failures that were difficult to debug. The root cause was an overly ambitious refactoring that simultaneously modified multiple interconnected systems (Utility, Quotes, Matching, Trading, Logging) without sufficient atomic testing at each stage.

This document serves as a post-mortem of the failed attempt and presents a revised, more granular implementation plan for Phase 2.

## 2. Summary of Difficulties

The test suite failed with three primary categories of errors:

1.  **`ImportError` and `AttributeError` Cascade**: Modifying the `Agent.quotes` attribute from a `Quote` object to a `dict` immediately broke all modules that accessed it. Attempts to fix this created circular dependencies (e.g., `decision.py` importing `matching.py`, which had grown in complexity).
2.  **Incorrect Surplus Calculation**: The core economic logic for calculating surplus in monetary trades was flawed, leading to nonsensical results where agents would accept trades that were not in their interest. This invalidated the core purpose of the phase.
3.  **Flawed Testing Procedures**: Initial test runs were non-deterministic due to manual termination of visualized simulations. Subsequent failures were caused by stale test databases and test helper functions that did not account for the new data schemas, creating confusing `KeyError` and `AttributeError` failures unrelated to the core logic being tested.

## 3. Root Cause Analysis

The core mistake was **violating the principle of atomicity**. The initial plan, while logically sound on paper, encouraged a single, large-scale change across the codebase. When a bug was introduced in one part (the surplus calculation), its effects were magnified by simultaneous breaking changes in data structures (`Agent.quotes`) and dependencies (`decision.py`), making the root cause difficult to isolate.

Key tactical errors included:
-   **Lack of Unit Testing for Quotes**: The new `compute_quotes` function, which is the foundation of monetary exchange, was never tested in isolation.
-   **Premature Refactoring of `DecisionSystem`**: The decision to refactor `decision.py` was made *in response* to an `ImportError`, not as a planned step. This led to a hasty redesign that was not fully thought through.
-   **Insufficiently Robust Test Helpers**: Test helpers like `create_test_scenario` were not updated to handle the new `ScenarioParams`, coupling them too tightly to a specific version of the schema.

## 4. Lessons Learned

1.  **Isolate Data Structure Changes**: Changing a core data structure like `Agent.quotes` is a significant "surgery." It should be done as a distinct, isolated step with its own branch and verification.
2.  **Unit Test Economic Primitives**: Core economic calculations (marginal utility, reservation price, surplus) must have dedicated, rigorous unit tests *before* being integrated into the larger system.
3.  **Decouple Systems**: The trading logic should not be so tightly coupled with the decision logic. The `TradeSystem` should be capable of evaluating potential trades between any pair of agents, regardless of what the `DecisionSystem` "targets."

## 5. Revised Atomic Implementation Plan for Phase 2

Phase 2 will be re-attempted in three smaller, sequential sub-phases, each on its own branch.

### Phase 2a: Generalize Core Data Structures

**Goal**: Update `Utility`, `Agent.quotes`, and `compute_quotes` to support monetary pairs, without changing any trading logic. All existing tests must pass.

1.  **Create Branch**: `feature/money-phase2a-data-structures`
2.  **Refactor `utility.py`**:
    -   Add `u_goods`, `mu_A`, and `mu_B` methods.
    -   Add the top-level `u_total` function.
    -   Create `tests/test_utility_money.py` to rigorously test these new functions in isolation.
3.  **Refactor `agent.py` and `quotes.py`**:
    -   Change `Agent.quotes` to `dict[str, float]`.
    -   Rewrite `compute_quotes` to return a dictionary of all potential barter and monetary quotes.
    -   Add `filter_quotes_by_regime` helper function.
    -   Create `tests/test_quotes_money.py` to verify that `compute_quotes` returns arithmetically correct values for `ask_A_in_M`, etc.
4.  **Update `HousekeepingSystem`**: Modify it to call `compute_quotes` and `filter_quotes_by_regime`.
5.  **Update `db_loggers.py`**: Modify `log_agent_snapshots` to use `.get()` on the new quotes dictionary.
6.  **Verification**: Run the *entire existing test suite*. All 69 tests must pass. This proves the data structure refactoring has not broken any existing functionality.

### Phase 2b: Implement Generic Trading Logic

**Goal**: Create the generic trading and surplus functions and test them in isolation with mock data.

1.  **Create Branch**: `feature/money-phase2b-generic-trade` (from `2a`)
2.  **Implement `matching.py` Functions**:
    -   Create `find_compensating_block_generic`.
    -   Create `find_best_trade`.
    -   Create `execute_trade`.
3.  **Create Unit Tests**:
    -   Create `tests/test_matching_money.py`.
    -   Write tests that create mock `Agent` objects with pre-filled `.quotes` dictionaries.
    -   Call `find_best_trade` with these mock agents and assert that it correctly identifies the highest-surplus trade (whether barter or monetary).
    -   Test the `money_only` and `mixed` regimes.

### Phase 2c: Integration and Final Verification

**Goal**: Integrate the new trading logic into the simulation loop and verify end-to-end behavior with a dedicated scenario.

1.  **Create Branch**: `feature/money-phase2c-integration` (from `2b`)
2.  **Refactor `trading.py`**:
    -   Update `TradeSystem.execute` to call `find_best_trade` and `execute_trade`.
    -   Update the call to `telemetry.log_trade` with all the new monetary details.
3.  **Refactor `decision.py`**:
    -   Remove the dependency on `choose_partner` as planned. Simplify the logic to merely target a neighbor.
4.  **Create Test Scenario**: Create `scenarios/money_test_basic.yaml`.
5.  **Create Integration Test**: Create `tests/test_money_phase2_integration.py` to run the new scenario.
6.  **Verification**: Run the full test suite. All tests, including the new integration test, must pass. The integration test must verify that monetary trades occurred, barter was blocked, and money was conserved.

This atomic plan ensures that each component is tested and verified before integration, dramatically reducing the risk of a systemic failure.
