# Renaming and Removal Plan for Legacy Code

**Date:** 2025-11-04  
**Status:** Planning Phase - Analysis Only  
**Goal:** Remove truly unused legacy code and rename active "legacy"-named protocols to accurate names.

---

## Executive Summary

This plan identifies:
1. **Active protocols with misleading "legacy" names** - These are currently used and should be renamed
2. **Active functions with misleading names** - These are used but have "legacy" or "money" in names
3. **Truly unused legacy code** - Functions that can be completely removed

---

## Part 1: Protocol Renaming (Active Protocols)

These protocols are actively used and should be renamed to remove the misleading "legacy" prefix.

### 1.1 `legacy_distance_discounted` → `distance_discounted_search`

**Current Name:** `legacy_distance_discounted`  
**New Name:** `distance_discounted_search`  
**Category:** Search Protocol  
**Status:** ✅ **ACTIVELY USED** - Default search protocol

**Files to Update:**
- `src/vmt_engine/agent_based/search/legacy.py`:
  - Rename file to `distance_discounted.py`
  - Rename class `LegacySearchProtocol` → `DistanceDiscountedSearch`
  - Update `@register_protocol(name="legacy_distance_discounted")` → `name="distance_discounted_search"`
  - Update module docstring to remove "Legacy" references
  - Update class docstring to remove "Legacy" references

- `src/vmt_engine/agent_based/search/__init__.py`:
  - Update import: `from .distance_discounted import DistanceDiscountedSearch`
  - Update exports: `"DistanceDiscountedSearch"` (remove `LegacySearchProtocol`)

- `src/scenarios/protocol_factory.py`:
  - Update default: `name = "distance_discounted_search"` (lines 25, 31)
  - Update examples in docstring (line 15)

- `src/scenarios/schema.py`:
  - Update default/defaults documentation if present

- All scenario YAML files:
  - `scenarios/demos/bargaining_comparison_6agent.yaml` (line 51)
  - `scenarios/demos/protocol_comparison_4agent.yaml` (if present)
  - `docs/structures/comprehensive_scenario_template.yaml` (line 210)
  - Update any other scenario files that reference this protocol

- Test files:
  - `tests/helpers/builders.py` (line 69)
  - `tests/test_myopic_search.py` (line 134, 157)
  - `tests/test_mode_integration.py` (line 29)
  - `tests/test_performance.py` (line 49)
  - `tests/test_protocol_registry.py` (line 23, 79)
  - `tests/test_resource_claiming.py` (line 91)
  - Update imports: `LegacySearchProtocol` → `DistanceDiscountedSearch`

**Verification:**
- This is the DEFAULT search protocol (used when None is specified)
- Used extensively in tests and scenarios
- Registered as active protocol in registry

---

### 1.2 `legacy_three_pass` → `three_pass_matching`

**Current Name:** `legacy_three_pass`  
**New Name:** `three_pass_matching`  
**Category:** Matching Protocol  
**Status:** ✅ **ACTIVELY USED** - Default matching protocol

**Files to Update:**
- `src/vmt_engine/game_theory/matching/legacy.py`:
  - Rename file to `three_pass.py`
  - Rename class `LegacyMatchingProtocol` → `ThreePassMatching`
  - Update `@register_protocol(name="legacy_three_pass")` → `name="three_pass_matching"`
  - Update module docstring to remove "Legacy" references
  - Update class docstring to remove "Legacy" references

- `src/vmt_engine/game_theory/matching/__init__.py`:
  - Update import: `from .three_pass import ThreePassMatching`
  - Update exports: `"ThreePassMatching"` (remove `LegacyMatchingProtocol`)

- `src/scenarios/protocol_factory.py`:
  - Update default: `name = "three_pass_matching"` (lines 57, 63)
  - Update examples in docstring (line 47)

- All scenario YAML files:
  - `scenarios/demos/bargaining_comparison_6agent.yaml` (line 55)
  - `scenarios/demos/protocol_comparison_4agent.yaml` (if present)
  - `docs/structures/comprehensive_scenario_template.yaml` (line 215)
  - Update any other scenario files that reference this protocol

- Test files:
  - `tests/helpers/builders.py` (line 70)
  - `tests/test_greedy_surplus_matching.py` (line 140, 197)
  - `tests/test_mode_integration.py` (line 30)
  - `tests/test_performance.py` (line 50)
  - `tests/test_protocol_registry.py` (line 26, 80)
  - `tests/test_random_matching.py` (line 155)
  - `tests/test_resource_claiming.py` (line 92)
  - Update imports: `LegacyMatchingProtocol` → `ThreePassMatching`

- Documentation:
  - `docs/1_technical_manual.md` (line 47, 97)
  - `docs/planning/2_Implementation_Stage4_Launcher.md` (if present)

**Verification:**
- This is the DEFAULT matching protocol (used when None is specified)
- Used extensively in tests and scenarios
- Registered as active protocol in registry

---

## Part 2: Function Renaming (Active Functions)

These functions are actively used but have misleading names that reference "legacy" or "money".

### 2.1 `estimate_money_aware_surplus()` → `estimate_barter_surplus()`

**Current Name:** `estimate_money_aware_surplus()`  
**New Name:** `estimate_barter_surplus()`  
**Location:** `src/vmt_engine/systems/matching.py`  
**Status:** ✅ **ACTIVELY USED** - Used by active protocols

**Used By:**
- `src/vmt_engine/game_theory/matching/legacy.py` (line 19) → Will be `three_pass.py`
- `src/vmt_engine/agent_based/search/legacy.py` (line 18) → Will be `distance_discounted.py`
- `src/vmt_engine/agent_based/search/myopic.py` (line 32)

**Files to Update:**
- `src/vmt_engine/systems/matching.py`:
  - Rename function: `estimate_money_aware_surplus()` → `estimate_barter_surplus()`
  - Update docstring to remove "historical apology" (lines 85-87)
  - Update docstring to clearly state it's a barter-only heuristic
  - Remove "money_aware" from internal comments

- Update all callers:
  - `src/vmt_engine/game_theory/matching/three_pass.py` (after rename)
  - `src/vmt_engine/agent_based/search/distance_discounted.py` (after rename)
  - `src/vmt_engine/agent_based/search/myopic.py`

**Verification:**
- Function is called by active protocols
- No references to money in implementation (already barter-only)
- Name change is purely cosmetic but improves clarity

---

## Part 3: Unused Code Removal

These functions are not called anywhere and can be completely removed.

### 3.1 Remove `trade_pair()` Function

**Location:** `src/vmt_engine/systems/matching.py` (lines 419-509)  
**Status:** ❌ **UNUSED** - Not called by any active code

**Verification:**
- Grep search shows function is only defined, never called
- Not imported or referenced by any protocol
- Was used by old pre-protocol system, now replaced by protocol-based trading

**Action:**
- Delete entire function (lines 419-509)
- Remove from any documentation references

---

### 3.2 Remove `find_compensating_block()` Function

**Location:** `src/vmt_engine/systems/matching.py` (lines 275-391)  
**Status:** ❌ **UNUSED** - Only called by `trade_pair()` which is unused

**Verification:**
- Only called by `trade_pair()` (line 467)
- `trade_pair()` is unused, so this is transitively unused
- Primary implementation is in `CompensatingBlockBargaining` protocol

**Action:**
- Delete entire function (lines 275-391)
- Remove from any documentation references
- Note: `generate_price_candidates()` is KEPT (used by `CompensatingBlockBargaining`)

---

### 3.3 Remove `execute_trade()` Function

**Location:** `src/vmt_engine/systems/matching.py` (lines 394-417)  
**Status:** ❌ **UNUSED** - Only called by `trade_pair()` which is unused

**Verification:**
- Only called by `trade_pair()` on line 493
- `trade_pair()` is unused, so this is transitively unused
- `execute_trade_generic()` is the active function used by `TradeSystem`

**Action:**
- Delete entire function (lines 394-417)
- Remove from any documentation references

**Note:** `execute_trade_generic()` is actively used by `TradeSystem` and should be kept.

---

## Part 4: Documentation Updates

After renaming and removal, update documentation to reflect changes:

### 4.1 Update Module Docstrings

**File:** `src/vmt_engine/systems/matching.py`

**Current:** `"Matching and trading helpers."`  
**New:** `"Matching helpers for protocols. Contains utility functions used by search and matching protocols. Some functions are used by the protocol system, others are deprecated."`

Then add clear markers:
- Functions marked as "Used by protocols" should list which protocols
- Functions marked as "DEPRECATED" should note they're being removed

---

### 4.2 Update Technical Manual

**File:** `docs/1_technical_manual.md`

Update references to:
- `legacy_distance_discounted` → `distance_discounted_search`
- `legacy_three_pass` → `three_pass_matching`

---

### 4.3 Update Scenario Templates

**File:** `docs/structures/comprehensive_scenario_template.yaml`

Update protocol examples and defaults to use new names.

---

## Implementation Order

### Phase 1: Rename Active Protocols (DO FIRST)
1. Rename `legacy_distance_discounted` → `distance_discounted_search`
   - Update protocol registration
   - Update all references in codebase
   - Update all scenario files
   - Update all tests
2. Rename `legacy_three_pass` → `three_pass_matching`
   - Update protocol registration
   - Update all references in codebase
   - Update all scenario files
   - Update all tests

### Phase 2: Rename Active Functions
3. Rename `estimate_money_aware_surplus()` → `estimate_barter_surplus()`
   - Update function definition
   - Update all callers

### Phase 3: Remove Unused Code
4. Remove `execute_trade()`
   - Delete function (lines 394-417)
5. Remove `find_compensating_block()`
   - Delete function
   - Remove documentation references
6. Remove `trade_pair()`
   - Delete function
   - Remove documentation references

### Phase 4: Documentation Cleanup
7. Update module docstrings
8. Update technical manual
9. Update scenario templates

---

## Testing Strategy

After each phase:
1. Run full test suite: `pytest`
2. Verify protocol registry works correctly
3. Verify scenario loading works with new names
4. Verify no import errors
5. Verify protocol system still functions correctly

---

## Breaking Changes

### Protocol Name Changes
- **Breaking:** Scenario YAML files using `legacy_distance_discounted` or `legacy_three_pass` will need to be updated
- **Mitigation:** Could add backward compatibility aliases in protocol factory, but cleaner to update all scenarios

### Function Removal
- **Breaking:** Any external code calling `trade_pair()` or `find_compensating_block()` will break
- **Mitigation:** These functions are not part of the public API and appear unused

---

## Files Summary

### Files to Rename:
- `src/vmt_engine/agent_based/search/legacy.py` → `distance_discounted.py`
- `src/vmt_engine/game_theory/matching/legacy.py` → `three_pass.py`

### Files to Modify (~30 files):
- Protocol registration files (2)
- Protocol factory (1)
- Protocol __init__ files (2)
- Scenario YAML files (~5)
- Test files (~10)
- Documentation files (~3)
- Matching.py (1)
- Search protocol files (2-3)

### Functions to Remove:
- `trade_pair()` - Confirmed unused (only defined, never called)
- `find_compensating_block()` - Confirmed unused (only called by unused `trade_pair()`)
- `execute_trade()` - Confirmed unused (only called by unused `trade_pair()`)

### Functions to Rename:
- `estimate_money_aware_surplus()` → `estimate_barter_surplus()`

---

## Verification Checklist

Before starting implementation:
- [x] Confirm `trade_pair()` is truly unused (grep confirmed - only defined, never called)
- [x] Confirm `find_compensating_block()` is truly unused (grep confirmed - only called by unused `trade_pair()`)
- [x] Confirm `execute_trade()` usage status (grep confirmed - only called by unused `trade_pair()`)
- [ ] List all scenario YAML files that need updating
- [ ] List all test files that need updating

After implementation:
- [ ] All tests pass
- [ ] Protocol registry shows correct names
- [ ] Scenario loading works with new names
- [ ] No broken imports
- [ ] Documentation updated

