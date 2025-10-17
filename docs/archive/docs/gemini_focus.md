Here are the two documents you requested to help focus your development efforts.

Based on my analysis of your planning documents, the clearest path forward consists of four distinct milestones, which I've detailed below. The core "choice" that seems to be causing paralysis is the jump to v1.3 (Money), which requires a significant but manageable refactor of your trading system.

This plan tackles that head-on by first locking in v1.1, then implementing the easy v1.2 win, and then breaking the v1.3 refactor into discrete, logical steps.

-----

## Document 1: VMT Step-by-Step Implementation Plan (v1.1 - v1.4)

This document outlines the implementation, goals, and rationale for the next four development milestones, synthesizing the consensus from your "VMT (v2).md," "prompt\_for\_review\_and\_planning.md," and theoretical foundation files.

### **Milestone 1: v1.1 Polish (The Foundation)**

  * **Goal:** Solidify the current v1.1 barter engine. Ensure it is stable, well-documented, and provides a trusted foundation for all future features.
  * **Rationale:** Adding new features to an undocumented or unstable base is a recipe for bugs and lost time. This step is about locking in your gains.

**Implementation Steps:**

1.  **Core Engine Documentation:**
      * **File:** `vmt_engine/README.md` (New)
      * **Action:** Create a technical overview that explains the 7-phase tick cycle (Perception → Decision → ... → Housekeeping). Detail the responsibility of each phase and the deterministic guarantees (e.g., agent sorting by ID, pair sorting).
2.  **Code Clarity Pass:**
      * **Files:** `vmt_engine/systems/matching.py`, `vmt_engine/systems/quotes.py`, `vmt_engine/econ/utility.py`.
      * **Action:** Add explanatory comments for non-obvious logic. Specifically:
          * `matching.py`: Why tie-breaking by ID is used (determinism).
          * `matching.py`: The logic of the `find_compensating_block` price search.
          * `utility.py`: The purpose of the `epsilon` shift in `reservation_bounds_A_in_B` (the zero-inventory guard).
3.  **Foundational Scenario:**
      * **File:** `scenarios/foundational_barter_demo.yaml` (New)
      * **Action:** Create a heavily-commented scenario file (e.g., 3-4 agents with complementary endowments) that serves as a tutorial for the v1.1 feature set.
4.  **Integration Test:**
      * **File:** `tests/test_v1_1_integration.py` (New)
      * **Action:** Write a test that runs the `foundational_barter_demo.yaml` for a fixed number of ticks (e.g., 50) with a fixed seed. Assert deterministic outcomes (e.g., exact number of trades, final agent inventories, total goods conservation).

-----

### **Milestone 2: v1.2 Mode Toggles (The Easy Win)**

  * **Goal:** Create alternating "forage-only" and "trade-only" windows to create emergent budget constraints.
  * **Rationale:** This is a low-risk, high-reward feature. It adds significant pedagogical value and simulation flexibility without altering any core economic logic. It's a perfect warm-up.

**Implementation Steps:**

1.  **Modify Schema:**
      * **File:** `scenarios/schema.py`.
      * **Action:** Add a new dataclass or dictionary for `mode_schedule` within `ScenarioParams`. It should support options like `type: "global_cycle"`, `forage_ticks: int`, `trade_ticks: int`, and `start_mode: str`.
2.  **Modify Engine Loop:**
      * **File:** `vmt_engine/simulation.py`.
      * **Action:** In the `step()` method, add logic to determine the `current_mode` based on `self.tick` and `self.params['mode_schedule']`.
      * In `trade_phase()`: Add `if self.current_mode == 'forage': return` at the top.
      * In `forage_phase()`: Add `if self.current_mode == 'trade': return` at the top.
3.  **Modify Telemetry:**
      * **File:** `telemetry/db_loggers.py` (or legacy loggers).
      * **Action:** Add a new table or log entry for `mode_changes` (`tick`, `new_mode`). Add a `mode` column to the `decisions` log to make analysis easier.

-----

### **Milestone 3: v1.3 Introduce Money (The Core Refactor)**

  * **Goal:** Introduce money (M) as a tradable asset using the quasilinear utility model: `U_total = U_goods(A, B) + λ * M`. This requires refactoring the trade system from `A-B` only to support generic `Good-Good` trades (specifically `A-B`, `A-M`, `B-M`).
  * **Rationale:** This is the most complex step, but it's the necessary foundation for all future market mechanics. Breaking it down makes it manageable.

**Implementation Steps:**

1.  **Update Core State:**
      * **File:** `vmt_engine/core/state.py`.
      * **Action:**
          * `Inventory`: Add `M: int = 0`.
          * `Quote`: Refactor this dataclass. Instead of `ask_A_in_B`, it needs to hold quotes for all pairs. A simple (if verbose) way is to add fields for all pairs: `ask_A_in_B`, `bid_A_in_B`, ... `ask_A_in_M`, `bid_A_in_M`, ... `ask_B_in_M`, `bid_B_in_M`, etc.
2.  **Update Schema:**
      * **File:** `scenarios/schema.py`.
      * **Action:** Add `lambda_money: float = 0.0` to `ScenarioParams`. Allow `M` in `initial_inventories`.
3.  **Refactor Utility Engine (The Hardest Part):**
      * **File:** `vmt_engine/econ/utility.py`.
      * **Action:**
          * Rename the existing `Utility.u` method to `u_goods(self, A: int, B: int) -> float`.
          * Add `lambda_money: float = 0.0` as an attribute to the `Utility` base class. The `create_utility` factory should set this from `ScenarioParams`.
          * Add a new method: `u_total(self, A: int, B: int, M: int) -> float`:
            ```python
            def u_total(self, A: int, B: int, M: int) -> float:
                return self.u_goods(A, B) + self.lambda_money * M
            ```
          * Add a new method `mu_goods(self, A, B, eps)` to `UCES` and `ULinear` that returns `(mu_A, mu_B)`.
              * `ULinear`: `return (self.vA, self.vB)`
              * `UCES`: `A_safe = A + eps if A == 0...`, `mu_A = self.wA * (A_safe ** (self.rho - 1))`, etc.
          * Add new `reservation_bounds` methods for money:
              * `reservation_bounds_A_in_M(...)`: `mu_A, _ = self.mu_goods(...)`, `mrs = mu_A / self.lambda_money`. Return `(mrs, mrs)`.
              * `reservation_bounds_B_in_M(...)`: `_, mu_B = self.mu_goods(...)`, `mrs = mu_B / self.lambda_money`. Return `(mrs, mrs)`.
          * The existing `improves` function in `vmt_engine/systems/matching.py` must be updated to use `u_total` and take `dA, dB, dM`.
4.  **Refactor Quote System:**
      * **File:** `vmt_engine/systems/quotes.py`.
      * **Action:** `compute_quotes` must now call `reservation_bounds_A_in_B`, `reservation_bounds_A_in_M`, and `reservation_bounds_B_in_M` and populate all fields in the new `Quote` object.
5.  **Refactor Matching System:**
      * **File:** `vmt_engine/systems/matching.py`.
      * **Action:** This is the second half of the hard part.
          * `compute_surplus`: Must be refactored. It needs to check for surplus in all three pairs (`A-B`, `A-M`, `B-M`) and return the *best* surplus and *which pair* is being traded (e.g., `return (best_surplus, ("A", "M"))`).
          * `choose_partner`: Will now receive `(partner_id, best_surplus, best_pair)` and must store `best_pair` on the agent's state (e.g., `agent.target_trade_pair = best_pair`).
          * `trade_pair`: Must be refactored to *read* the `target_trade_pair` from the agents.
          * `find_compensating_block` & `execute_trade`: Must be parameterized to handle generic trades.
              * E.g., `find_compensating_block(buyer, seller, price, good_to_buy: str, good_to_pay: str, ...)`
              * Inside `find_compensating_block`, the `improves` check must be generalized:
                  * If `(good_to_buy, good_to_pay) == ("A", "M")`: check `improves(buyer, dA, 0, -dM)` and `improves(seller, -dA, 0, +dM)`.
              * `execute_trade` must be similarly generalized to update `A`, `B`, or `M` inventories.

-----

### **Milestone 4: v1.4 Prototype Posted-Price Market (The Payoff)**

  * **Goal:** Implement the "Local Posted-Price Auction" mechanism.
  * **Rationale:** This feature builds directly on the v1.3 refactor. It demonstrates the "invisible hand" at a micro-level and is the first true market mechanism.

**Implementation Steps:**

1.  **Modify Simulation Loop:**
      * **File:** `vmt_engine/simulation.py`.
      * **Action:** In `trade_phase`, before iterating over pairs, add logic to detect "connected components" (groups of agents within `interaction_radius`). Your `SpatialIndex` can help here, but a simple graph traversal (BFS/DFS) on the agent proximity graph might be needed.
2.  **Create Market Logic:**
      * **File:** `vmt_engine/systems/matching.py` (New functions).
      * **Action:**
          * `run_market(agent_ids: set[int], sim_params, logger, tick)`:
              * **Filter:** If `len(agent_ids) < market_min_size` (e.g., 3), exit and let the bilateral logic handle it.
              * **Focus:** For v1.4, pick *one* market (e.g., `A-in-M`).
              * **Aggregate:** Collect all `ask_A_in_M` and `bid_A_in_M` quotes from agents in the set.
              * **Price Discovery:** Find `p_star` (clearing price). A simple, deterministic rule: `p_star = (max(bids) + min(asks)) / 2`. If `max(bids) < min(asks)`, there is no market, so `return`.
              * **Match:** Create `willing_buyers = [a for a in agents if a.bid >= p_star]` and `willing_sellers = [a for a in agents if a.ask <= p_star]`.
              * **Execute:** Sort buyers and sellers by `agent.id` (for determinism). Iterate and match the first buyer with the first seller, then second with second, etc.
              * For each matched pair, call `find_compensating_block(..., price=p_star, good_to_buy="A", good_to_pay="M")`. This re-uses your v1.3 logic but with a *fixed price*.
              * Crucially, enforce the `ΔU > 0` check inside `find_compensating_block` to ensure individual rationality even at the market price.
              * Enforce the "one trade per agent per tick" rule.
3.  **Update Telemetry:**
      * **File:** `telemetry/db_loggers.py`.
      * **Action:** Add a new `log_market_event(tick, market_id, clearing_price, volume)` function to record market-level outcomes.

-----

## Document 2: Companion Checklist (v1.1 - v1.4)

Here is a step-by-step checklist to track your progress through the implementation plan.

### **Milestone 1: v1.1 Polish**

  - [ ] **Docs:** Create `vmt_engine/README.md` explaining the 7-phase tick cycle.
  - [ ] **Code:** Add comments to `matching.py`, `quotes.py`, and `utility.py` explaining determinism rules and `epsilon` guard.
  - [ ] **Scenario:** Create `scenarios/foundational_barter_demo.yaml` with extensive comments.
  - [ ] **Test:** Create `tests/test_v1_1_integration.py` that runs the foundational demo and asserts deterministic outcomes.

### **Milestone 2: v1.2 Mode Toggles**

  - [ ] **Schema:** Modify `scenarios/schema.py` to add `mode_schedule` to `ScenarioParams`.
  - [ ] **Engine:** Modify `vmt_engine/simulation.py` to read `mode_schedule` and determine `current_mode` based on `self.tick`.
  - [ ] **Engine:** Add logic to `trade_phase()` to `return` if `current_mode == 'forage'`.
  - [ ] **Engine:** Add logic to `forage_phase()` to `return` if `current_mode == 'trade'`.
  - [ ] **Telemetry:** Add `mode_changes` logging to `telemetry/db_loggers.py`.
  - [ ] **Telemetry:** Add `mode` column to `decisions` log.
  - [ ] **Test:** Create `tests/test_mode_schedule.py` to verify trades and foraging are correctly skipped.
  - [ ] **Scenario:** Create `scenarios/mode_cycle_demo.yaml` to demonstrate the feature.

### **Milestone 3: v1.3 Introduce Money (The Core Refactor)**

  - [ ] **State:** Add `M: int = 0` to `Inventory` in `vmt_engine/core/state.py`.
  - [ ] **State:** Refactor `Quote` dataclass in `vmt_engine/core/state.py` to include fields for `A-M` and `B-M` pairs (e.g., `ask_A_in_M`, `bid_A_in_M`, ...).
  - [ ] **Schema:** Add `lambda_money: float` to `ScenarioParams` in `scenarios/schema.py`.
  - [ ] **Schema:** Allow `M` in `initial_inventories` in `scenarios/schema.py`.
  - [ ] **Utility:** Refactor `Utility` class in `vmt_engine/econ/utility.py`:
      - [ ] Rename `u` to `u_goods`.
      - [ ] Add `lambda_money` attribute.
      - [ ] Add `u_total(A, B, M)` method.
      - [ ] Add `mu_goods(A, B, eps)` method to `UCES` and `ULinear`.
      - [ ] Add `reservation_bounds_A_in_M` and `reservation_bounds_B_in_M` methods.
  - [ ] **Quotes:** Refactor `compute_quotes` in `vmt_engine/systems/quotes.py` to compute and store all three trade pairs in the new `Quote` object.
  - [ ] **Matching:** Refactor `improves` in `vmt_engine/systems/matching.py` to use `u_total` and accept `dM`.
  - [ ] **Matching:** Refactor `compute_surplus` to check all 3 pairs (`A-B`, `A-M`, `B-M`) and return `(best_surplus, best_pair)`.
  - [ ] **Matching:** Refactor `choose_partner` to store `agent.target_trade_pair`.
  - [ ] **Matching:** Refactor `find_compensating_block` to be generic, taking `good_to_buy` and `good_to_pay` arguments.
  - [ ] **Matching:** Refactor `execute_trade` to be generic, updating `A`, `B`, or `M` based on arguments.
  - [ ] **Test:** Create `tests/test_money_quasilinear.py` to verify `u_total`, `reservation_bounds_A_in_M`, and that `A-M` trades are successful.
  - [ ] **Test:** Update all existing trade tests to use the new refactored matching functions (e.g., explicitly testing the `A-B` pair).
  - [ ] **Scenario:** Create `scenarios/money_quasilinear_demo.yaml`.

### **Milestone 4: v1.4 Prototype Posted-Price Market**

  - [ ] **Engine:** Add component detection logic to `trade_phase` in `vmt_engine/simulation.py`.
  - [ ] **Schema:** Add `market_min_size: int = 3` to `ScenarioParams` in `scenarios/schema.py`.
  - [ ] **Matching:** Create new function `run_market` in `vmt_engine/systems/matching.py`.
  - [ ] **Matching:** Implement quote aggregation logic inside `run_market`.
  - [ ] **Matching:** Implement deterministic price discovery logic (`p_star`).
  - [ ] **Matching:** Implement deterministic matching logic (sort by ID) for willing buyers/sellers.
  - [ ] **Matching:** Call the generic `find_compensating_block` (from v1.3) with the fixed `p_star` for each match.
  - [ ] **Engine:** Ensure `trade_phase` correctly dispatches to `run_market` for large components and falls back to bilateral `trade_pair` for small ones.
  - [ ] **Telemetry:** Add `log_market_event` to `telemetry/db_loggers.py`.
  - [ ] **Test:** Create `tests/test_market_posted_price.py` to verify deterministic price and trade execution.
  - [ ] **Scenario:** Create `scenarios/posted_price_market_demo.yaml`.