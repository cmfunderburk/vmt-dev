# Trade Failure Diagnostic Report
**Scenario:** three_agent_barter.yaml, seed=21

## Executive Summary

**Root Cause Identified:** Agent 0 has **zero B inventory (B=0)**, which causes the CES utility function to generate extreme/infinite reservation prices. This creates an artificially massive surplus but makes actual trade execution impossible due to astronomical price calculations.

## Detailed Analysis

### 1. Agent Initial States (Tick 0)

From `agent_snapshots.csv`:

| Agent | A | B | Utility | ask_A_in_B | bid_A_in_B | p_min | p_max |
|-------|---|---|---------|------------|------------|-------|-------|
| **0** | **5** | **0** | **0.0** | **0.0** | **0.0** | **0.0** | **0.0** |
| **1** | **0** | **5** | **0.0** | **1.17e19** | **1.06e19** | **1.12e19** | **1.12e19** |
| 2 | 3 | 3 | 0.75 | 1.05 | 0.95 | 1.0 | 1.0 |

**Critical Issue:** 
- Agent 0 has **B=0**, causing all price quotes to be zero (likely from division or undefined MRS)
- Agent 1 has **A=0**, producing astronomical prices (**~10^19**)
- These agents have perfectly complementary inventories but can't trade!

### 2. Decision-Making Behavior

From `decisions.csv`:

**Agents 0 & 1:**
- Both agents **consistently choose each other** as trading partners
- Computed surplus: **1.06×10^19** (massive!)
- They remain locked in position trying to trade: Agent 0 at (3,3), Agent 1 at (3,2)
- **They never move apart** - stuck trying to trade forever

**Agent 2:**
- Has no visible neighbors (0 neighbors every tick)
- Forages successfully ticks 0-9 (A: 3→7, B: 3→4)
- Switches to **idle** at tick 10 when no more resources nearby
- Remains idle for ticks 10-31 (end of simulation)

### 3. Why Trades Fail (Every Tick)

From `trade_attempts.csv` - examining tick 0:

```
Direction: Agent 1 (buyer) trying to buy A from Agent 0 (seller)
Price: 5.31×10^18
Surplus: 1.06×10^19

Attempts (all 5 fail with same reason):
dA=1 → dB=5.31×10^18 → FAIL: buyer_insufficient_B
dA=2 → dB=1.06×10^19 → FAIL: buyer_insufficient_B
dA=3 → dB=1.59×10^19 → FAIL: buyer_insufficient_B
dA=4 → dB=2.12×10^19 → FAIL: buyer_insufficient_B
dA=5 → dB=2.66×10^19 → FAIL: buyer_insufficient_B
```

**The Problem:**
- Agent 1 only has **B=5** 
- But needs to pay **trillions of trillions** of B for even 1 unit of A
- This is physically impossible → all trades fail
- The calculated dB exceeds Agent 1's inventory by **10^18 orders of magnitude**!

### 4. The Zero-Inventory Cascade

**What's happening mathematically:**

1. **Agent 0** (A=5, B=0) with CES utility:
   - When B=0, the MRS calculation involves A/B ratios
   - Even with epsilon guard (A+ε, B+ε), the resulting price is broken
   - Quotes come out as 0.0 (likely clamped or undefined)

2. **Agent 1** (A=0, B=5) with CES utility:
   - When A=0, similar MRS issues occur
   - Produces astronomical prices (**1.12×10^19**)
   - This indicates A is infinitely valuable when you have zero of it

3. **Surplus Calculation:**
   ```
   surplus = max(
       agent_1.bid - agent_0.ask,    # 1.06e19 - 0.0 = 1.06e19
       agent_0.bid - agent_1.ask     # 0.0 - 1.17e19 = -1.17e19
   )
   = 1.06e19  (huge positive surplus!)
   ```

4. **Price Calculation:**
   ```
   price = 0.5 * (seller.ask + buyer.bid)
         = 0.5 * (0.0 + 1.06e19)
         = 5.31e18
   ```

5. **Trade Size Calculation:**
   ```
   For dA=1:
   dB = round_half_up(5.31e18 * 1) = 5.31e18
   
   But buyer only has B=5!
   ```

## Why Agent 2 Only Forages Then Idles

Agent 2's behavior is actually **correct**:

1. **Ticks 0-9: Foraging Phase**
   - Agent 2 starts at (2,6) with A=3, B=3
   - Has 0 visible neighbors (Agents 0&1 are at distance > vision_radius)
   - Correctly chooses to forage
   - Successfully gathers resources: A: 3→7, B: 3→4
   - Moves toward resource cells

2. **Tick 10+: Idle Phase**
   - Agent 2 reaches (7,4) with A=7, B=4
   - No more resources within vision
   - Still 0 neighbors visible
   - **Correctly switches to idle** (no trade partners, no resources)
   - Target becomes empty (no target_x, target_y)

**Agent 2's isolation:**
- Agents 0 and 1 are stuck at (3,3) and (3,2) forever
- Agent 2 moves away from them while foraging
- The three agents never get close enough to interact

## Hypothesis Confirmation

From the original problem document, testing the hypotheses:

### ❌ H1: No Surplus Exists
**FALSE** - There's a *massive* surplus (1.06×10^19), but it's artificial/meaningless

### ✅ H2: Surplus Exists but Compensating Block Fails  
**TRUE** - Surplus exists, but every trade size fails due to impossible payment requirements

### ✅ H3: Zero-Inventory Guard Issue
**TRUE** - The epsilon-shift for zero inventories creates astronomical prices that break trading

### ✅ H4: Rounding/Discretization Problem
**PARTIALLY TRUE** - Round-half-up produces integer dB values, but they're so large that rounding is irrelevant

## Root Cause Classification

**Primary Issue:** **Zero-Inventory Valuation Problem (H3)**

The CES utility function's MRS calculation produces extreme/undefined values when either inventory is zero, even with epsilon guards. The current epsilon-based approach:

```python
# Current approach (in UCES.mrs_A_in_B)
if A == 0 or B == 0:
    A_safe = A + eps
    B_safe = B + eps
    
ratio = A_safe / B_safe  # Still produces extreme values
mrs = (wA / wB) * (ratio ** (rho - 1))
```

With A=5, B=0, eps=1e-12:
- ratio = (5 + 1e-12) / (0 + 1e-12) ≈ 5×10^12
- If rho=-0.5, then (rho-1)=-1.5
- mrs ≈ (wA/wB) * (5×10^12)^(-1.5) = extremely large number

## Recommended Solutions

### Option 1: Prevent Zero-Inventory Trading (Conservative)
Don't allow agents to generate quotes or attempt trades when either inventory is zero:

```python
def compute_quotes(agent, spread, epsilon):
    # Don't trade if either inventory is zero
    if agent.inventory.A == 0 or agent.inventory.B == 0:
        return Quote(ask_A_in_B=0.0, bid_A_in_B=0.0, p_min=0.0, p_max=0.0)
    # ... existing logic
```

### Option 2: Clamp Reservation Prices (Practical)
Set reasonable bounds on reservation prices:

```python
def reservation_bounds_A_in_B(self, A, B, eps):
    mrs = self.mrs_A_in_B(A, B, eps)
    
    # Clamp to reasonable range
    MAX_PRICE = 1e6  # Configurable limit
    mrs = min(mrs, MAX_PRICE)
    
    return (mrs, mrs)
```

### Option 3: Use Different MRS Formula for Edge Cases (Sophisticated)
Implement special handling for near-zero inventories:

```python
def mrs_A_in_B(self, A, B, eps):
    if A == 0 or B == 0:
        # Use larger epsilon or return a default "high value" price
        # that's still tradeable
        return 1000.0  # Configurable default for zero-inventory case
    
    # Normal calculation for positive inventories
    ratio = float(A) / float(B)
    return (self.wA / self.wB) * (ratio ** (self.rho - 1))
```

### Option 4: Bootstrap with Non-Zero Inventories (Scenario Fix)
Modify the scenario to ensure agents start with positive amounts of both goods:

```yaml
initial_inventories:
  A: [5, 1, 3]  # Agent 1 gets 1 A instead of 0
  B: [1, 5, 3]  # Agent 0 gets 1 B instead of 0
```

## Immediate Next Steps

1. **Choose a solution approach** (recommend Option 2 for practicality)
2. **Implement the fix** in the appropriate file(s)
3. **Re-run with seed 21** and examine logs to verify trading occurs
4. **Add test cases** for zero-inventory edge cases
5. **Document** the solution in code comments

## Conclusion

The telemetry system successfully identified the root cause: **zero-inventory agents produce extreme/infinite prices that prevent trade execution, despite appearing to have huge surplus**. This is a fundamental economic modeling issue that requires either:
- Preventing zero-inventory trading, or
- Clamping/handling extreme price values gracefully

The good news: Agents 0 and 1 *want* to trade (they recognize each other as valuable partners) - we just need to fix the price calculation to make it feasible!

