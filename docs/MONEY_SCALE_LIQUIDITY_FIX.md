# Money Scale Liquidity Fix

**Date:** 2025-10-22  
**Issue:** `money_scale` parameter was not scaling initial money inventories, breaking liquidity

## Problem

The `money_scale` parameter was **only** scaling prices in quotes, not the actual initial money inventories. This meant:

- Scenario specifies: `M: 200, money_scale: 1000`
- **Expected behavior:** Agents get `M = 200,000` units, prices scale 1000x
- **Actual (buggy) behavior:** Agents get `M = 200` units, prices scale 1000x
- **Result:** Agents had 1/1000th the purchasing power they should have!

### Why This Matters

`money_scale` is designed to **increase liquidity** by scaling both money holdings AND prices proportionally. When only prices scaled, it had the **opposite effect** - reducing liquidity.

**Example with `lambda_money = 1.0`, `mu_A = 2.0`:**
- `money_scale = 1`: Price = 2.0, M = 200 → Can buy 100 units
- `money_scale = 1000` (buggy): Price = 2000.0, M = 200 → Can buy 0.1 units ❌
- `money_scale = 1000` (fixed): Price = 2000.0, M = 200,000 → Can buy 100 units ✅

Purchasing power should remain constant!

## Root Causes (Two Bugs Fixed)

### Bug 1: Initial inventory not scaled
**Location:** `src/vmt_engine/simulation.py:143-144`

```python
# BEFORE (buggy):
if isinstance(inv_M, int):
    inv_M = [inv_M] * n_agents
# M values not scaled!
```

```python
# AFTER (fixed):
if isinstance(inv_M, int):
    inv_M = [inv_M] * n_agents

# Scale money inventory by money_scale (liquidity adjustment)
money_scale = self.params['money_scale']
inv_M = [m * money_scale for m in inv_M]
```

### Bug 2: Initial quotes not scaled
**Location:** `src/vmt_engine/simulation.py:210`

```python
# BEFORE (buggy):
agent.quotes = compute_quotes(agent, self.params['spread'], self.params['epsilon'])
# money_scale parameter not passed!
```

```python
# AFTER (fixed):
agent.quotes = compute_quotes(
    agent, 
    self.params['spread'], 
    self.params['epsilon'],
    money_scale=self.params['money_scale']  # Now scaled properly
)
```

## Solution

### Code Changes

1. **`src/vmt_engine/simulation.py` (lines 148-151)**
   - Added money inventory scaling after converting to lists
   - Multiplies all M values by `money_scale`

2. **`src/vmt_engine/simulation.py` (lines 209-216)**
   - Pass `money_scale` parameter to initial `compute_quotes()` call
   - Ensures initial prices are scaled correctly

3. **`docs/structures/comprehensive_scenario_template.yaml`**
   - Updated documentation to clarify that `money_scale` multiplies BOTH inventory and prices
   - Added comprehensive money scale guidelines (lines 290-302)
   - Added example showing the multiplication behavior

### New Tests

Created `tests/test_money_scale_liquidity.py` with 3 tests:

1. **`test_money_scale_multiplies_initial_inventory`**
   - Verifies M inventory is multiplied by money_scale
   - Verifies A and B inventories are NOT affected

2. **`test_money_scale_1_no_multiplier`**
   - Verifies money_scale=1 leaves M unchanged (baseline)

3. **`test_money_scale_proportional_liquidity`**
   - Verifies both M and prices scale proportionally
   - Verifies purchasing power (M / price) remains constant
   - **This test would have caught the bug!**

## Verification

### All Tests Pass ✅

```bash
pytest tests/test_money_scale_liquidity.py -v
# 3 passed

pytest tests/test_money_phase1_integration.py -v
# 2 passed

pytest tests/test_scenario_loader.py -v
# 3 passed
```

### Behavior Verification

With `M: 200` and `money_scale: 1000`:

**Before (buggy):**
- Agent inventory: `M = 200`
- Price quote: `ask_A_in_M = 2000.0`
- Purchasing power: `200 / 2000 = 0.1` units ❌

**After (fixed):**
- Agent inventory: `M = 200,000`
- Price quote: `ask_A_in_M = 2000.0`
- Purchasing power: `200,000 / 2000 = 100` units ✅

## Impact on Existing Scenarios

### Backward Compatibility

**Scenarios with `money_scale = 1` (default):** ✅ NO CHANGE
- Multiplication by 1 has no effect
- All existing scenarios work identically

**Scenarios with `money_scale > 1`:** ⚠️ BEHAVIOR CHANGE (FIX)
- These scenarios were **broken before** (insufficient liquidity)
- Now work as intended
- If any scenarios were manually compensating (e.g., using very large M values), they may need adjustment

### Your Scenario (`large_100_agents.yaml`)

With `money_scale: 1000` and `M: 200`:

**Before (broken):**
- Agents had M = 200 units
- Prices ~1000x higher than they should afford
- Very few monetary trades possible

**After (fixed):**
- Agents have M = 200,000 units
- Prices appropriately scaled
- Normal liquidity and trading activity

## Documentation Updates

### Updated Files

1. **`docs/structures/comprehensive_scenario_template.yaml`**
   - Clarified `money_scale` multiplies BOTH inventory AND prices
   - Added explicit example showing multiplication
   - Added comprehensive guidelines for when to use different money_scale values
   - Recommended `money_scale ≥ 100` for scenarios with heterogeneous λ

2. **Inline Comments**
   - Added explanatory comments in `simulation.py` explaining the liquidity adjustment

## Key Takeaways

1. **`money_scale` is a liquidity parameter**, not just a display unit converter
2. **Proportional scaling** maintains purchasing power: (M * scale) / (price * scale) = M / price
3. **Higher money_scale values** provide:
   - Reduced integer rounding errors (primary benefit)
   - Finer price granularity
   - Better precision for heterogeneous λ scenarios
4. **Recommended values:**
   - Simple scenarios: `money_scale: 1`
   - Standard simulations: `money_scale: 100`
   - Large/precise simulations: `money_scale: 1000`

## Future Considerations

### Potential Enhancements

1. **Validation Warning:** Consider warning if `money_scale > 1` but all agents have identical λ values (limited benefit)

2. **Auto-scaling:** Could add automatic money_scale selection based on expected price ranges

3. **Documentation:** Add example showing trade outcomes with different money_scale values in tutorials

### Related Parameters

- **`lambda_money`**: Marginal utility of money (affects price levels)
- **`exchange_regime`**: Must be `money_only` or `mixed` for money_scale to matter
- **`dM` (trade transfers)**: Automatically scales with prices due to integer rounding

---

**Status:** ✅ RESOLVED  
**Tests:** ✅ ALL PASSING  
**Backward Compatibility:** ✅ MAINTAINED (for default money_scale=1)

