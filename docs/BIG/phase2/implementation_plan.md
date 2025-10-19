# VMT Money System: Phase 2 Re-Implementation Plan

This plan follows the atomic, three-part strategy outlined in `docs/BIG/phase2_postmortem.md` to safely re-implement the monetary exchange logic. Each part will be developed on a separate branch and rigorously tested in isolation before integration.

## Phase 2a: Generalize Core Data Structures

**Goal**: Refactor core data structures (`Utility`, `Agent.quotes`) to be money-aware without altering any trading behavior. The primary success criterion is that all 69 existing tests continue to pass, proving perfect backward compatibility of the refactoring.

- **Branch**: `feature/money-phase2a-data-structures`
- **Key Actions**:
    1.  **Refactor `utility.py`**: Separate `u_goods` from `u_total` and implement analytic marginal utility functions (`mu_A`, `mu_B`). This will be validated by new unit tests in `tests/test_utility_money.py`.
    2.  **Generalize `Agent.quotes`**: Change `agent.quotes` from a dataclass to a `dict` in `src/vmt_engine/core/agent.py`.
    3.  **Rewrite `quotes.py`**: The `compute_quotes` function will be updated to return a dictionary containing both barter (`A<->B`) and monetary (`A<->M`, `B<->M`) quotes. This will be validated by new unit tests in `tests/test_quotes_money.py`.
    4.  **Update Consumers**: Modify `HousekeepingSystem` and `db_loggers.py` to handle the new dictionary-based quote structure.

## Phase 2b: Implement Generic Trading Logic

**Goal**: Develop the generic, high-surplus trading algorithm in isolation. This logic will be tested using mock `Agent` objects, completely decoupled from the main simulation loop.

- **Branch**: `feature/money-phase2b-generic-trade` (from `2a`)
- **Key Actions**:
    1.  **Implement Generic Functions**: In `src/vmt_engine/systems/matching.py`, create the new core functions:
        -   `find_compensating_block_generic`: Calculates surplus for any good pair (A, B, M).
        -   `find_best_trade`: Iterates through permissible exchange pairs and identifies the one with the maximum total surplus.
        -   `execute_trade`: Applies a trade to agent inventories.
    2.  **Unit Test with Mocks**: Create `tests/test_matching_money.py` to test the above functions. Tests will use hand-crafted `Agent` objects with pre-defined quotes to verify that the correct trade is selected under different regimes (`money_only`, `mixed`).

## Phase 2c: Integration and Final Verification

**Goal**: Integrate the generic trading logic into the main simulation, refactor the `DecisionSystem`, and verify the complete end-to-end functionality with a new test scenario.

- **Branch**: `feature/money-phase2c-integration` (from `2b`)
- **Key Actions**:
    1.  **Integrate into `TradeSystem`**: Modify `src/vmt_engine/systems/trading.py` to call the new `find_best_trade` and `execute_trade` functions.
    2.  **Decouple `DecisionSystem`**: Refactor `src/vmt_engine/systems/decision.py` to simply target a potential partner, removing all trade evaluation logic.
    3.  **Create Test Scenario**: Create `scenarios/money_test_basic.yaml` configured for `exchange_regime: "money_only"`.
    4.  **End-to-End Test**: Create `tests/test_money_phase2_integration.py` to run the new scenario and verify that monetary trades occur as expected and that barter trades are correctly blocked.
    5.  **Final Verification**: Run the entire test suite. All legacy and new tests must pass.
