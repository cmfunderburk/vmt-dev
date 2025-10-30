# Complete Money Elimination Plan

**Goal**: Completely remove all money functionality from VMT simulation to enable clean rethinking of money mechanisms.

**Principle**: Money should not exist in ANY form. No fields, no parameters, no calculations, no references. Pure goods-only (A↔B barter) economy.

---

## Phase 1: Core Data Structures

### 1.1 Remove Money from `Inventory` (`src/vmt_engine/core/state.py`)
- [ ] Remove `M: int = 0` field from `Inventory` dataclass
- [ ] Remove `M` from `__post_init__` validation
- [ ] Update docstring to remove money mention

### 1.2 Remove Money Fields from `Agent` (`src/vmt_engine/core/agent.py`)
- [ ] Remove `lambda_money: float = 1.0`
- [ ] Remove `lambda_changed: bool = False`
- [ ] Remove `money_utility_form: str = "linear"`
- [ ] Remove `M_0: float = 0.0`
- [ ] Update docstring to remove money-aware API references

---

## Phase 2: Utility System

### 2.1 Simplify Utility Interface (`src/vmt_engine/econ/base.py`)
- [ ] Remove all "Money-aware API" docstrings
- [ ] Remove references to `u_total()`, `mu_money()` in comments
- [ ] Keep only `u()` and `u_goods()` (make `u_goods()` just call `u()`)

### 2.2 Remove Money Utility Functions (`src/vmt_engine/econ/utility.py`)
- [ ] **DELETE** `mu_money()` function entirely (lines ~565-592)
- [ ] **DELETE** `u_total()` function entirely (lines ~595-642)
- [ ] Remove all money utility form logic (linear/log)
- [ ] Update docstrings to remove money references
- [ ] Ensure all utility classes only implement goods utility

### 2.3 Update All Utility Calls
- [ ] Replace all `u_total(inventory, params)` calls with `utility.u(inventory.A, inventory.B)`
- [ ] Remove `params` dicts that include `lambda_money`, `money_utility_form`, `M_0`
- [ ] Files to update:
  - `src/vmt_engine/systems/matching.py` (multiple locations)
  - `src/vmt_engine/simulation.py` (initialization, summary)
  - `src/vmt_engine/protocols/` (all protocol files using utility)

---

## Phase 3: Quote System

### 3.1 Simplify Quote Computation (`src/vmt_engine/systems/quotes.py`)
- [ ] **REMOVE** all money quote computation (A↔M, B↔M)
- [ ] Keep ONLY barter quotes: `ask_A_in_B`, `bid_A_in_B`, `ask_B_in_A`, `bid_B_in_A`, and reservation bounds
- [ ] Remove `money_scale` parameter from `compute_quotes()`
- [ ] Remove `mu_mש()` import and calls
- [ ] Remove money quote keys from return dict (lines ~101-124)
- [ ] Simplify `compute_quotes()` to ONLY compute A↔B and B↔A quotes

### 3.2 Remove Exchange Regime Filtering
- [ ] **DELETE** `filter_quotes_by_regime()` function entirely
- [ ] Remove `exchange_regime` parameter from `refresh_quotes_if_needed()`
- [ ] Update `refresh_quotes_if_needed()` to call `compute_quotes()` directly (no filtering)
- [ ] Remove all regime-based quote filtering logic

---

## Phase 4: Exchange Regimes and Pair Types

### 4.1 Remove Money from Exchange Regimes (`src/scenarios/schema.py`)
- [ ] Change `exchange_regime` type from `Literal["barter_only", "money_only", "mixed", "mixed_liquidity_gated"]` to just `"barter_only"` (or remove entirely)
- [ ] **DELETE** all money-related parameters:
  - `money_mode`
  - `money_utility_form`
  - `M_0`
  - `money_scale`
  - `lambda_money`
  - `lambda_update_rate`
  - `lambda_bounds`
  - `liquidity_gate`
  - `earn_money_enabled`
- [ ] Update `ScenarioParams` docstrings

### 4.2 Update Scenario Loading (`src/scenarios/loader.py`)
- [ ] Remove parsing of `M` from `initial_inventories`
- [ ] Remove parsing of `lambda_money`, `M_0` lists
- [ ] Remove all money parameter parsing

### 4.3 Remove Money Pair Types (`src/vmt_engine/systems/matching.py`)
- [ ] **DELETE** `find_compensating_block_generic()` support for `"A<->M"` and `"B<->M"` pairs
- [ ] Keep ONLY `"A<->B"` barter logic
- [ ] **DELETE** `get_allowed_exchange_pairs()` function OR simplify to always return `["A<->B"]`
- [ ] **DELETE** `find_all_feasible_trades()` money pair enumeration (keep only A↔B)
- [ ] Update all docstrings to remove money pair references
- [ ] Simplify `find_first_feasible_trade()` to only try `"A<->B"`

### 4.4 Update Trade Tuple Format
- [ ] Simplify trade tuple from `(dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)` to `(dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j)`
- 항목 `execute_trade_generic()` to remove `dM_i`, `dM_j` and M inventory updates
- 항목 Remove money conservation assertions

---

## Phase 5: Protocol System

### 5.1 Update Protocol Context (`src/vmt_engine/protocols/context.py`)
- [ ] Remove `exchange_regime` from `WorldView` and `ProtocolContext`
- [ ] Remove money fields from `AgentView` (if any)
- [ ] Remove `lambda_money`, `M_0`, `money_utility_form` from params dicts in context builders

### 5.2 Update Context Builders (`src/vmt_engine/protocols/context_builders.py`)
- [ ] Remove money-related params from `build_world_view_for_agent()`
- [ ] Remove money-related params from `build_protocol_context()`
- [ ] Remove money-related params from `build_trade_world_view()`

### 5.3 Update All Protocols
- [ ] **Search Protocols** (`src/vmt_engine/protocols/search/`):
  - Remove `estimate_money_aware_surplus()` calls
  - Remove money pair preference building
  - Remove exchange regime checks
  - Keep ONLY barter surplus calculations
- [ ] **Matching Protocols** (`src/vmt_engine/protocols/matching/`):
  - Remove money pair enumeration
  - Remove `exchange_regime` checks
  - Keep ONLY A↔B pairing logic
- [ ] **Bargaining Protocols** (`src/vmt_engine/protocols/bargaining/`):
  - Ensure `find_all_feasible_trades()` only returns A↔B trades
  - Remove money utility calculations
  - Update to use `utility.u()` instead of `u_total()`

---

## Phase 6: Simulation Core

### 6.1 Update Simulation Initialization (`src/vmt_engine/simulation.py`)
- [ ] Remove `inv_M` parsing and initialization
- [ ] Remove `inv_lambda`, `inv_M_0` parsing
- [ ] Remove `lambda_money`, `money_utility_form`, `M_0` from Agent construction
- [ ] Remove `money_scale` from `compute_quotes()` call
- [ ] Remove `exchange_regime` from params dict
- [ ] Remove all money-related params from `self.params`
- [ ] Update `_initialize_agents()` to not include M in Inventory
- [ ] Update `_start_inventory` tracking to remove M

### 6.2 Update Simulation Summary (`src/vmt_engine/simulation.py`)
- [ ] Remove M from inventory delta calculations
- [ ] Remove M from inventory segment printing
- [ ] Update utility calculation to use `utility.u()` instead of `u_total()`
- [ ] Remove money params from utility calculation dicts

### 6.3 Update Active Exchange Pairs (`src/vmt_engine/simulation.py`)
- [ ] Simplify `_get_active_exchange_pairs()` to always return `["A<->B"]`
- [ ] Remove all exchange regime logic

---

## Phase 7: Systems

### 7.1 Update Decision System (`src/vmt_engine/systems/decision.py`)
- [ ] Remove `exchange_regime` checks
- [ ] Remove money-aware surplus estimation
- [ ] Keep ONLY barter preference building

### 7.2 Update Housekeeping System (`src/vmt_engine/systems/housekeeping.py`)
- [ ] Remove `exchange_regime` from `refresh_quotes_if_needed()` call
- [ ] Remove `money_scale` parameter
- [ ] Simplify quote refresh to only barter quotes

### 7.3 Update Trade System (`src/vmt_engine/systems/trading.py`)
- [ ] Verify no money-specific logic remains
- [ ] Update trade logging to remove money references

---

## Phase 8: Telemetry

### 8.1 Update Telemetry Logging (`src/telemetry/db_loggers.py`)
- [ ] Remove M from agent snapshot logging
- [ ] Remove money trade logging (if separate from barter)
- [ ] Update trade mentions to remove money pair types
- [ ] Remove `exchange_regime` from tick state logging

---

## Phase 9: Rendering/UI

### 9.1 Update Renderer (`src/vmt_pygame/renderer.py`)
- [ ] Remove M inventory display
- [ ] Remove money-related UI elements
- [ ] Remove exchange regime display

---

## Phase 10: Documentation and Comments

### 10.1 Update Code Comments
- [ ] Remove all "Money-aware API" comments
- [ ] Remove all references to Phase 2+ money features
- [ ] Update docstrings to remove money mentions
- [ ] Clean up TODO comments about money

### 10.2 Update README Files
- [ ] `src/vmt_engine/README.md`: Remove money system documentation
- [ ] Update protocol documentation to remove money examples

---

## Phase 11: Test Files

### 11.1 Update Test Files
- [ ] Remove money inventory from test scenario builders
- [ ] Remove money parameters from test configs
- [ ] Update utility assertions to use `utility.u()` instead of `u_total()`
- [ ] Remove money-related test cases
- [ ] Update or remove tests in:
  - `tests/test_money_*.py` (may need to delete some)
  - `tests/test_mixed_regime_*.py` (may need to delete)
  - `tests/test_utility_money.py` (may need to delete)
  - All tests using money inventories or regimes

---

## Phase 12: Scenario Files

### 12.1 Update Scenario YAML Files
- [ ] Remove `M` from `initial_inventories` in all scenarios
- [ ] Remove `exchange_regime` or set to `"barter_only"` in all scenarios
- [ ] Remove all money-related parameters
- [ ] Files to update (may need to delete money-specific scenarios):
  - `scenarios/money_test_*.yaml` (consider deleting)
  - `scenarios/mixed_*.yaml` (update or delete)
  - All demo scenarios with money

---

## Phase 13: Validation and Cleanup

### 13.1 Code Search for Remaining References
- [ ] Grep for `\bM\b|money|lambda_money|M_0|money_scale|exchange_regime|A<->M|B<->M`
- [ ] Verify no money references remain (except in historical comments if desired)
- [ ] Check for imports of deleted functions (`mu_money`, `u_total`)

### 13.2 Run Test Suite
- [ ] Run all tests: `bash -c "source venv/bin/activate && python -m pytest tests/ -v"`
- [ ] Fix any failures from money removal
- [ ] Verify determinism still holds
- [ ] Verify barter-only trading works correctly

---

## Implementation Order Recommendation

**Critical Path** (must do in order):
1. Phase 2 (Utility) → Phase 4 (Exchange Regimes) → Phase 3 (Quotes)
2. Phase 1 (Data Structures) → Phase 6 (Simulation) → Phase 5 (Protocols)
3. Phase 7 (Systems) → Phase 8 (Telemetry) → Phase 9 (Rendering)
4. Phase 11 (Tests) → Phase 12 (Scenarios) → Phase 13 (Validation)

**Rationale**: 
- Remove utility money calculations first (breaks dependencies)
- Then remove data structures (clean slate)
- Then update all consumers
- Finally validate with tests

---

## Risk Mitigation

1. **Breaking Changes**: This is INTENTIONAL - money is being completely removed
2. **Test Failures**: Expected; update tests as part of Phase 11
3. **Scenario Files**: Some may break; update or delete money-specific scenarios
4. **Git History**: Consider creating a branch for this work for easy review

---

## Success Criteria

- [ ] No references to money in code (except historical comments if desired)
- [ ] All tests pass (after updating)
- [ ] Simulation runs with barter-only trading
- [ ] No money fields in Inventory or Agent
- [ ] No money utility functions
- [ ] No money quotes
- [ ] No money pair types
- [ ] Pure A↔B barter economy only

---

## Notes

- **Inventory.M**: Will need to be removed from ALL existing scenarios or handled gracefully during loading (set to 0 and ignore)
- **Exchange Regime**: Consider removing the parameter entirely vs. hardcoding to "barter_only"
- **Utility API**: `u_goods()` vs `u()` distinction may no longer be needed - can simplify to just `u()`
- **Backward Compatibility**: NOT a goal - breaking change is intentional

---

**Estimated Effort**: ~4-6 hours of focused work + test updates

**Review Status**: ⏸️ PENDING USER REVIEW

