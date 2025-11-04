# Comprehensive Code and Docstring Review

**Date:** 2025-11-04  
**Status:** Planning Phase - Analysis Only  
**Context:** VMT project is now a pure barter economy (A↔B only). Money system removed on 2025-10-31. Protocol system fully implemented and wired.

---

## Executive Summary

This review identifies **three categories** of issues:
1. **Functionally Broken Code** - References non-existent database columns, will cause runtime errors
2. **Misleading Documentation** - Docstrings and comments that incorrectly describe current architecture
3. **Documentation Inconsistencies** - Planning docs and technical manuals that don't match current implementation

**Total Issues Found:** 15 files requiring updates, with varying severity levels.

---

## Category 1: Functionally Broken Code (CRITICAL)

These files contain code that will fail at runtime because they reference database columns that no longer exist. The database schema was updated to remove money-related columns, but these files were not updated.

### 1.1 `src/vmt_log_viewer/queries.py` ⚠️ **CRITICAL**

**Status:** Multiple queries reference non-existent columns  
**Impact:** All money-related queries will fail with SQL errors

**Broken Queries:**
- **Line 170-171**: `get_trade_statistics()` queries `SUM(dM)` and `AVG(dM)` - column doesn't exist
- **Line 216**: `get_money_trades()` queries `WHERE dM != 0` - column doesn't exist  
- **Line 236-238**: `get_lambda_trajectory()` queries `lambda_money` - column doesn't exist
- **Line 256**: `get_mode_timeline()` queries `exchange_regime` - column doesn't exist
- **Line 281-285**: `get_money_statistics()` queries `dM`, `buyer_lambda`, `seller_lambda` - none exist

**Required Actions:**
1. Remove `get_money_trades()`, `get_lambda_trajectory()`, `get_money_statistics()` entirely
2. Update `get_trade_statistics()` to remove `SUM(dM)` and `AVG(dM)` columns
3. Update `get_mode_timeline()` to remove `exchange_regime` column
4. Update docstrings to remove all money references

**Files Dependent on Broken Queries:**
- `src/vmt_log_viewer/viewer.py` (calls these methods)
- `src/vmt_log_viewer/csv_export.py` (may call via QueryBuilder)

---

### 1.2 `src/vmt_log_viewer/csv_export.py` ⚠️ **CRITICAL**

**Status:** SQL queries reference non-existent columns  
**Impact:** CSV export will fail with SQL errors when querying agent snapshots or trades

**Broken Functions:**
- **Line 42-71**: `export_agent_snapshots()` 
  - Query selects `inventory_M as M` (line 45) - column doesn't exist
  - Query selects `lambda_money` (line 47) - column doesn't exist
  - CSV header includes `'M'` and `'lambda_money'` (line 58)
  - Code tries to access `row['M']` and `row['lambda_money']` (lines 65, 70)
  - Docstring says "with money columns" (line 42)

- **Line 124-152**: `export_trades()`
  - Query selects `dM`, `buyer_lambda`, `seller_lambda` (lines 127-128) - columns don't exist
  - CSV header includes these columns (lines 138-139)
  - Code tries to access these values (lines 147-150)
  - Docstring says "with money columns" (line 125)

**Required Actions:**
1. Remove `inventory_M`, `lambda_money` from `export_agent_snapshots()` query and CSV output
2. Remove `dM`, `buyer_lambda`, `seller_lambda` from `export_trades()` query and CSV output
3. Update docstrings to reflect barter-only export

---

### 1.3 `src/vmt_log_viewer/viewer.py` ⚠️ **CRITICAL**

**Status:** UI creates Money tab that calls broken queries  
**Impact:** Money tab will crash when loaded, preventing viewer from working

**Broken Code:**
- **Lines 81-83**: Creates "Money" tab via `_create_money_tab()`
- **Lines 166-204**: `_create_money_tab()` creates UI elements for money analysis
- **Lines 280-281, 346-416**: `load_money_tab()` calls broken queries:
  - `QueryBuilder.get_money_statistics()` (line 352)
  - `QueryBuilder.get_money_trades()` (line 397)
  - Accesses `result['money_trades']`, `result['avg_dM']`, etc. (lines 355-373)
  - Tries to display `dM`, `buyer_lambda`, `seller_lambda` columns (lines 400-414)

**Required Actions:**
1. Remove Money tab entirely (lines 81-83, 166-204, 280-281, 346-416)
2. Update `load_overview()` to remove money statistics (lines 311-318, 325-326)

---

### 1.4 `src/vmt_log_viewer/widgets/trade_view.py` ⚠️ **CRITICAL**

**Status:** UI references non-existent `dM` column  
**Impact:** Trade view will crash when displaying trades

**Broken Code:**
- **Line 68**: Column list includes `'dM'` - column doesn't exist in trades table
- **Line 89**: Tries to sum `row['dM']` - will fail
- **Line 93**: Displays `total_dM` in summary - will fail
- **Line 109**: Tries to read `dM` from table item - will fail
- **Line 119**: Displays `Amount M Traded: {dM}` - will fail

**Required Actions:**
1. Remove `'dM'` from columns list (line 68)
2. Remove `total_dM` calculation and display (lines 89, 93)
3. Remove `dM` from trade details display (lines 109, 119)

---

## Category 2: Misleading Documentation (MEDIUM PRIORITY)

These files contain docstrings that incorrectly describe the current architecture. The code works, but the documentation is misleading about *what* the code is and *where* the primary logic lives.

### 2.1 `src/vmt_engine/systems/matching.py` ⚠️ **MEDIUM**

**Status:** Docstrings misrepresent the role of this file  
**Impact:** Developers will misunderstand where core logic lives

**Issues:**

1. **Module Docstring (Line 2):**
   - Current: `"Matching and trading helpers."`
   - Problem: Vague, doesn't clarify this is legacy/helper code
   - **Recommendation:** Update to: `"Legacy matching and trading helpers. Primary protocol logic is in src/vmt_engine/game_theory/ and src/vmt_engine/agent_based/. This file contains legacy implementations used by 'legacy_three_pass' matching protocol."`

2. **`estimate_money_aware_surplus()` (Lines 74-121):**
   - Current: Function name and docstring contain "historical apology" (lines 85-87)
   - Problem: Name is misleading, docstring apologizes rather than explaining
   - **Recommendation:** 
     - Rename to `estimate_barter_surplus()`
     - Remove historical apology, update docstring to state it's a barter-only heuristic

3. **`find_compensating_block()` (Lines 275-299):**
   - Current: Docstring describes this as the core trading logic
   - Problem: This is misleading - the PRIMARY implementation is now in `CompensatingBlockBargaining` protocol
   - **Recommendation:** Add to docstring: `"This is a legacy helper function used by the 'legacy_three_pass' matching protocol. The primary implementation of this logic is in the CompensatingBlockBargaining protocol (src/vmt_engine/game_theory/bargaining/compensating_block.py)."`

4. **`trade_pair()` (Lines 419-509):**
   - Current: Docstring doesn't mention it's legacy
   - Problem: This function is only used by legacy protocols, not the primary protocol system
   - **Recommendation:** Add to docstring: `"This is a legacy helper function used by the 'legacy_three_pass' matching protocol. The primary trade execution logic is now in protocol-specific bargaining implementations."`

**Verification:**
- `CompensatingBlockBargaining` exists at `src/vmt_engine/game_theory/bargaining/compensating_block.py`
- It implements the same compensating block logic but as a proper protocol
- Legacy `trade_pair()` is only called by `legacy_three_pass` matching protocol

---

### 2.2 `src/vmt_engine/simulation.py` ⚠️ **MEDIUM**

**Status:** Docstring claims protocol system is not wired  
**Impact:** Misleads developers about current implementation status

**Issue:**
- **Line 22-23**: Comment says `"Protocol system (Phase 0 - Infrastructure only, not yet wired)"`
- **Reality:** Lines 54-78 show protocols are fully wired and configurable via `scenario_config`
- Protocols are injected into systems (lines 111-117)
- Protocols are used throughout the simulation

**Required Action:**
- Update comment to: `"Protocol system - fully implemented and configurable via scenario_config"`
- Remove the "Phase 0 - Infrastructure only" misleading comment

---

## Category 3: Documentation Inconsistencies (LOW PRIORITY)

These files are documentation or planning files that don't match the current codebase state.

### 3.1 `docs/2_typing_overview.md` ⚠️ **LOW**

**Status:** Internally inconsistent - schema section contradicts history section  
**Impact:** Confuses developers reading the documentation

**Issue:**
- **Lines 539-542**: "Specification History" section correctly notes "Money System Removal (2025-10-31)"
- **Lines 328-380**: "Telemetry Schema (SQLite)" section still lists:
  - `inventory_M` (mentioned in agent_snapshots description)
  - `lambda_money` (mentioned in agent_snapshots description)
  - `dM` (mentioned in trades description)
  - `exchange_regime` (mentioned in tick_states description)

**Verification:**
- Actual schema in `src/telemetry/database.py` correctly has NO money columns
- `agent_snapshots` table (lines 59-80) has only `inventory_A`, `inventory_B`
- `trades` table (lines 143-161) has only `dA`, `dB` (no `dM`)
- `tick_states` table (lines 234-244) has only `current_mode` (no `exchange_regime`)

**Required Action:**
- Update telemetry schema documentation section to match actual schema
- Remove all references to `inventory_M`, `lambda_money`, `dM`, `exchange_regime` from schema descriptions

---

### 3.2 `src/vmt_engine/protocols/telemetry_schema.py` ⚠️ **LOW**

**Status:** Planning file with outdated example  
**Impact:** Confuses developers reading planning documentation

**Issue:**
- **Line 142**: Example `Trade` effect includes `"dM": 0` in `effect_data`
- **Reality:** VMT is pure barter, no `dM` field should exist

**Required Action:**
- Update example to remove `"dM": 0`
- Example should be: `'{"pair_type": "A_for_B", "dA": -5, "dB": 3, "price": 1.67, ...}'`

---

## Additional Findings

### Scripts with Legacy References

Several analysis scripts also reference old money columns, but these may be intentional for backward compatibility with old database files:

- `scripts/compare_telemetry_snapshots.py` (lines 79-91, 102-104)
- `scripts/plot_mode_timeline.py` (line 45)
- `scripts/analyze_trade_distribution.py` (line 80)

**Recommendation:** Review these scripts to determine if they should:
1. Be updated to remove money column references (if only analyzing new databases)
2. Be kept with backward compatibility checks (if analyzing legacy databases)

---

## Examples of Good Documentation

These files serve as excellent templates for how to handle legacy code:

### `src/vmt_pygame/renderer.py`

**Approach:** Clear deprecation notice in module docstring
- Lines 4-6: Explicit "DEPRECATION NOTICE" explaining money features are deprecated
- Functions like `draw_agents_with_lambda_heatmap` have docstrings stating they fall back to barter-only behavior

**This is the model to follow** for updating legacy-facing code.

### `src/vmt_engine/game_theory/bargaining/split_difference.py`

**Approach:** Clear "NOT YET IMPLEMENTED" status
- Module docstring clearly states "NOT YET IMPLEMENTED - Stub"
- Version marked as "2025.11.04.stub"

**This is the model to follow** for documenting unimplemented features.

---

## Priority Ranking

### Immediate (Blocks Functionality):
1. `src/vmt_log_viewer/queries.py` - Remove/fix broken queries
2. `src/vmt_log_viewer/csv_export.py` - Fix SQL queries and CSV output
3. `src/vmt_log_viewer/viewer.py` - Remove Money tab
4. `src/vmt_log_viewer/widgets/trade_view.py` - Remove dM references

### High Priority (Causes Confusion):
5. `src/vmt_engine/systems/matching.py` - Update docstrings to clarify legacy status
6. `src/vmt_engine/simulation.py` - Fix misleading protocol comment

### Medium Priority (Documentation Quality):
7. `docs/2_typing_overview.md` - Update schema documentation
8. `src/vmt_engine/protocols/telemetry_schema.py` - Update example

---

## Implementation Notes

### Testing Strategy

After fixing these issues, verify:
1. Log viewer can open and view databases without errors
2. CSV export works for agent snapshots and trades
3. All UI tabs load without crashing
4. Trade view displays correctly
5. No SQL errors in logs when using viewer

### Backward Compatibility

Consider:
- Old databases may have money columns (if they were created before removal)
- Viewer should gracefully handle missing columns (catch SQL exceptions)
- CSV export should handle missing columns gracefully

### Code Review Checklist

When implementing fixes:
- [ ] Remove all SQL queries referencing `dM`, `inventory_M`, `lambda_money`, `exchange_regime`
- [ ] Update all docstrings to remove money references
- [ ] Add deprecation notices where legacy code is retained
- [ ] Update UI to remove money-related tabs/panels
- [ ] Test with current database schema
- [ ] Verify no runtime errors in viewer
- [ ] Update documentation to match actual schema

---

## Conclusion

This review identifies 8 files requiring immediate attention, with 4 files being critically broken (will cause runtime errors). The issues stem from the money system removal (2025-10-31) and protocol system implementation, where documentation and some helper code were not fully updated.

The fixes are straightforward but require careful attention to:
1. Remove all database column references that no longer exist
2. Update docstrings to accurately reflect current architecture
3. Clarify which code is legacy vs. primary implementation

