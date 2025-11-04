# Log Viewer Money System Removal Fix Plan

**Date:** 2025-11-04  
**Status:** Planning Phase  
**Goal:** Remove all references to removed money system columns from log viewer, preventing runtime SQL errors.

---

## Executive Summary

The log viewer contains **critical bugs** that will cause runtime failures:
- SQL queries reference non-existent columns (`dM`, `inventory_M`, `lambda_money`, `exchange_regime`)
- UI creates Money tab that calls broken queries
- CSV export functions query and include removed columns
- Trade view widget references `dM` column

**Impact:** Log viewer will crash when:
- Loading overview statistics
- Opening Money tab
- Exporting CSVs
- Viewing trades

**Fix Strategy:** Remove all money-related code and update queries/UI to match current barter-only schema.

---

## Database Schema Reference

### Current Schema (Barter-Only)

**`trades` table:**
- `id`, `run_id`, `tick`, `x`, `y`, `buyer_id`, `seller_id`, `dA`, `dB`, `price`, `direction`, `exchange_pair_type`, `buyer_surplus`, `seller_surplus`
- **Removed:** `dM`, `buyer_lambda`, `seller_lambda`

**`agent_snapshots` table:**
- `id`, `run_id`, `tick`, `agent_id`, `x`, `y`, `inventory_A`, `inventory_B`, `utility`, `ask_A_in_B`, `bid_A_in_B`, `p_min`, `p_max`, `target_agent_id`, `target_x`, `target_y`, `utility_type`
- **Removed:** `inventory_M`, `lambda_money`

**`tick_states` table:**
- `id`, `run_id`, `tick`, `current_mode`
- **Removed:** `exchange_regime`

---

## Phase 1: Fix SQL Queries (`src/vmt_log_viewer/queries.py`)

### 1.1 Update `get_trade_statistics()` - Remove dM

**Location:** Lines 165-178  
**Current:**
```python
query = """
    SELECT 
        COUNT(*) as total_trades,
        AVG(dA) as avg_dA,
        AVG(dB) as avg_dB,
        SUM(dM) as total_dM,      # REMOVE
        AVG(dM) as avg_dM,         # REMOVE
        AVG(price) as avg_price,
        MIN(tick) as first_trade_tick,
        MAX(tick) as last_trade_tick
    FROM trades
    WHERE run_id = ?
"""
```

**Fix:**
```python
query = """
    SELECT 
        COUNT(*) as total_trades,
        AVG(dA) as avg_dA,
        AVG(dB) as avg_dB,
        AVG(price) as avg_price,
        MIN(tick) as first_trade_tick,
        MAX(tick) as last_trade_tick
    FROM trades
    WHERE run_id = ?
"""
```

### 1.2 Remove `get_money_trades()` Function

**Location:** Lines 209-228  
**Action:** Delete entire function (not used by barter system)  
**Note:** This function is only called by Money tab, which will be removed.

### 1.3 Remove `get_lambda_trajectory()` Function

**Location:** Lines 230-250  
**Action:** Delete entire function (lambda_money column doesn't exist)

### 1.4 Update `get_mode_timeline()` - Remove exchange_regime

**Location:** Lines 252-261  
**Current:**
```python
query = """
    SELECT tick, current_mode, exchange_regime  # REMOVE exchange_regime
    FROM tick_states
    WHERE run_id = ?
    ORDER BY tick
"""
```

**Fix:**
```python
query = """
    SELECT tick, current_mode
    FROM tick_states
    WHERE run_id = ?
    ORDER BY tick
"""
```

### 1.5 Remove `get_money_statistics()` Function

**Location:** Lines 275-289  
**Action:** Delete entire function (queries non-existent columns)

---

## Phase 2: Fix CSV Export (`src/vmt_log_viewer/csv_export.py`)

### 2.1 Update `export_agent_snapshots()` - Remove Money Columns

**Location:** Lines 41-71  
**Current Issues:**
- Line 45: Queries `inventory_M as M` (doesn't exist)
- Line 47: Queries `lambda_money` (doesn't exist)
- Line 58: CSV header includes `'M'` and `'lambda_money'`
- Line 65: Accesses `row['M']`
- Line 70: Accesses `row['lambda_money']`
- Docstring says "with money columns"

**Fix:**
1. Remove `inventory_M as M,` from SELECT (line 45)
2. Remove `lambda_money` from SELECT (line 47)
3. Remove `'M'` from CSV header (line 56)
4. Remove `'lambda_money'` from CSV header (line 58)
5. Remove `row['M']` from writerow (line 65)
6. Remove `row['lambda_money']` from writerow (line 70)
7. Update docstring: "Export agent snapshots to CSV."

### 2.2 Update `export_trades()` - Remove Money Columns

**Location:** Lines 124-152  
**Current Issues:**
- Line 127: Queries `dM` (doesn't exist)
- Line 128: Queries `buyer_lambda`, `seller_lambda` (don't exist)
- Line 138: CSV header includes `'dM'`
- Line 139: CSV header includes `'buyer_lambda'`, `'seller_lambda'`
- Line 147: Accesses `row['dM']`
- Lines 149-150: Accesses `row['buyer_lambda']`, `row['seller_lambda']`
- Docstring says "with money columns"

**Fix:**
1. Remove `dM,` from SELECT (line 127)
2. Remove `buyer_lambda, seller_lambda,` from SELECT (line 128)
3. Remove `'dM',` from CSV header (line 138)
4. Remove `'buyer_lambda', 'seller_lambda',` from CSV header (line 139)
5. Remove `row['dM'],` from writerow (line 147)
6. Remove `buyer_lambda` and `seller_lambda` from writerow (lines 149-150)
7. Update docstring: "Export trades to CSV."

---

## Phase 3: Remove Money Tab from UI (`src/vmt_log_viewer/viewer.py`)

### 3.1 Remove Money Tab Creation

**Location:** Lines 81-83  
**Action:** Delete these lines:
```python
# Money tab (WP3 Part 3B)
self.money_tab = self._create_money_tab()
self.tabs.addTab(self.money_tab, "Money")
```

### 3.2 Remove `_create_money_tab()` Method

**Location:** Lines 166-204  
**Action:** Delete entire method (no longer needed)

### 3.3 Remove `load_money_tab()` Call

**Location:** Line 281  
**Action:** Delete line:
```python
# Load money tab data
self.load_money_tab()
```

### 3.4 Remove `load_money_tab()` Method

**Location:** Lines 346-416  
**Action:** Delete entire method (calls broken queries)

### 3.5 Update `load_overview()` - Remove Money Statistics

**Location:** Lines 286-344  
**Current Issues:**
- Lines 311-312: Accesses `result['total_dM']`, `result['avg_dM']` (won't exist after query fix)
- Lines 317-318: Formats `total_dM_text`, `avg_dM_text`
- Lines 325-326: Displays money statistics in HTML

**Fix:**
1. Remove `total_dM = result['total_dM']` (line 311)
2. Remove `avg_dM = result['avg_dM']` (line 312)
3. Remove `total_dM_text = f"{total_dM}" if total_dM is not None else "N/A"` (line 317)
4. Remove `avg_dM_text = f"{avg_dM:.2f}" if avg_dM is not None else "N/A"` (line 318)
5. Remove from HTML:
   ```html
   <b>Total dM:</b> {total_dM_text}<br>
   <b>Average dM:</b> {avg_dM_text}<br>
   ```

---

## Phase 4: Fix Trade View Widget (`src/vmt_log_viewer/widgets/trade_view.py`)

### 4.1 Remove dM from Column List

**Location:** Line 68  
**Current:**
```python
columns = ['buyer_id', 'seller_id', 'x', 'y', 'dA', 'dB', 'dM', 'price', 'direction', 'exchange_pair_type']
```

**Fix:**
```python
columns = ['buyer_id', 'seller_id', 'x', 'y', 'dA', 'dB', 'price', 'direction', 'exchange_pair_type']
```

### 4.2 Remove dM from Summary Calculation

**Location:** Lines 87-94  
**Current:**
```python
total_dA = sum(row['dA'] for row in results)
total_dB = sum(row['dB'] for row in results)
total_dM = sum(row['dM'] for row in results)  # REMOVE
avg_price = sum(row['price'] for row in results) / len(results)
summary = (
    f"{len(results)} trades | Total dA: {total_dA} | "
    f"Total dB: {total_dB} | Total dM: {total_dM} | Avg Price: {avg_price:.4f}"  # REMOVE dM
)
```

**Fix:**
```python
total_dA = sum(row['dA'] for row in results)
total_dB = sum(row['dB'] for row in results)
avg_price = sum(row['price'] for row in results) / len(results)
summary = (
    f"{len(results)} trades | Total dA: {total_dA} | "
    f"Total dB: {total_dB} | Avg Price: {avg_price:.4f}"
)
```

### 4.3 Remove dM from Trade Details

**Location:** Lines 100-124  
**Current Issues:**
- Line 109: Tries to read `dM` from column index 6 (will be wrong index after removing dM)
- Line 119: Displays `Amount M Traded: {dM}` in HTML

**Fix:**
1. Remove `dM = int(self.current_trades_table.item(row, 6).text())` (line 109)
   - Note: After removing dM from columns, column indices shift, so:
     - `price` moves from index 7 → 6
     - `direction` moves from index 8 → 7
     - `exchange_pair_type` moves from index 9 → 8
2. Update column index references:
   - `price`: Change from index 7 to 6
   - `direction`: Change from index 8 to 7
   - `exchange_pair_type`: Change from index 9 to 8
3. Remove from HTML:
   ```html
   <b>Amount M Traded:</b> {dM}<br>
   ```

---

## Implementation Order

### Step 1: Fix SQL Queries (Foundation)
1. Update `get_trade_statistics()` - remove dM columns
2. Remove `get_money_trades()` function
3. Remove `get_lambda_trajectory()` function
4. Update `get_mode_timeline()` - remove exchange_regime
5. Remove `get_money_statistics()` function

### Step 2: Fix CSV Export
6. Update `export_agent_snapshots()` - remove money columns
7. Update `export_trades()` - remove money columns

### Step 3: Fix UI - Remove Money Tab
8. Remove Money tab creation (lines 81-83)
9. Remove `_create_money_tab()` method
10. Remove `load_money_tab()` call
11. Remove `load_money_tab()` method

### Step 4: Fix Overview Statistics
12. Update `load_overview()` - remove money statistics

### Step 5: Fix Trade View Widget
13. Remove dM from column list
14. Remove dM from summary calculation
15. Remove dM from trade details and fix column indices

---

## Testing Strategy

After implementation, verify:

1. **Log viewer opens** without errors
2. **Overview tab loads** and displays correct statistics (no dM references)
3. **Trades tab loads** and displays trades correctly (no dM column)
4. **CSV export works:**
   - `export_agent_snapshots()` creates CSV without money columns
   - `export_trades()` creates CSV without money columns
5. **Trade view widget** displays correctly (no dM in summary or details)
6. **No SQL errors** in logs when using viewer
7. **No Money tab** appears in UI

---

## Verification Checklist

- [ ] All SQL queries only reference existing columns
- [ ] No references to `dM`, `inventory_M`, `lambda_money`, `exchange_regime` in queries
- [ ] CSV exports don't include money columns
- [ ] CSV export docstrings updated
- [ ] Money tab removed from UI
- [ ] `_create_money_tab()` method removed
- [ ] `load_money_tab()` method removed
- [ ] Overview statistics don't show money data
- [ ] Trade view widget doesn't reference dM
- [ ] Column indices updated in trade view widget
- [ ] All broken query methods removed

---

## Files Summary

### Files to Modify (4 files):
1. `src/vmt_log_viewer/queries.py` - Fix/remove queries
2. `src/vmt_log_viewer/csv_export.py` - Fix export functions
3. `src/vmt_log_viewer/viewer.py` - Remove Money tab, fix overview
4. `src/vmt_log_viewer/widgets/trade_view.py` - Remove dM references

### Functions to Remove (3):
- `get_money_trades()` - Queries non-existent dM column
- `get_lambda_trajectory()` - Queries non-existent lambda_money column
- `get_money_statistics()` - Queries multiple non-existent columns

### Functions to Update (5):
- `get_trade_statistics()` - Remove dM columns
- `get_mode_timeline()` - Remove exchange_regime
- `export_agent_snapshots()` - Remove money columns
- `export_trades()` - Remove money columns
- `load_overview()` - Remove money statistics display

### Methods to Remove (2):
- `_create_money_tab()` - Creates Money tab UI
- `load_money_tab()` - Loads money data (calls broken queries)

---

## Breaking Changes

**None** - This fix removes broken functionality that currently causes crashes. The Money tab feature is being removed entirely, which is appropriate since the money system no longer exists.

---

## Notes

- All money-related code is being removed, not deprecated
- No backward compatibility needed - old databases won't have money columns either
- The fix is straightforward but requires careful attention to column indices in trade_view.py
- After fixes, log viewer will work correctly with current barter-only schema

