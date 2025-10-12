# Enhanced Telemetry System Implementation

## Summary

The VMT simulation now has comprehensive logging to diagnose trade execution failures and understand agent decision-making. All changes have been implemented according to the plan in `Log_system_problems.md`.

## What Was Changed

### 1. Extended Quote Data Structure
**File**: `vmt_engine/core/state.py`
- Added `p_min` and `p_max` fields to the `Quote` dataclass to store reservation price bounds
- These are the true reservation prices before applying the spread

### 2. Enhanced Quote Computation
**File**: `vmt_engine/systems/quotes.py`
- Modified `compute_quotes()` to return reservation bounds alongside computed quotes
- Now stores the raw `p_min` and `p_max` values for logging and analysis

### 3. New Logger: DecisionLogger
**File**: `telemetry/decision_logger.py`
- Logs every agent's decision each tick
- Captures:
  - Chosen trading partner (if any)
  - Surplus with that partner
  - Target type (trade/forage/idle)
  - Target position
  - All alternative partners considered with their surplus values

### 4. New Logger: TradeAttemptLogger
**File**: `telemetry/trade_attempt_logger.py`
- Logs every call to `find_compensating_block()`
- For each trade size attempt (ΔA from 1 to ΔA_max):
  - Calculated ΔB value
  - Initial and final inventories for both agents
  - Initial and final utilities for both agents
  - Whether each agent's utility improves
  - Inventory feasibility checks
  - Success/failure with detailed reason

### 5. Enhanced AgentSnapshotLogger
**File**: `telemetry/snapshots.py`
- Changed default `snapshot_frequency` to 1 (logs every tick)
- Added columns: `ask_A_in_B`, `bid_A_in_B`, `p_min`, `p_max`
- Added columns: `target_agent_id`, `target_x`, `target_y`
- Now captures complete agent state including quotes and movement targets

### 6. Instrumented Matching System
**File**: `vmt_engine/systems/matching.py`

**`choose_partner()`**:
- Now returns tuple: `(partner_id, surplus, all_candidates)`
- Provides diagnostic data for decision logging

**`find_compensating_block()`**:
- Accepts optional `TradeAttemptLogger` parameter
- Logs every iteration through trade sizes
- Records exact reason for success or failure:
  - `dB_nonpositive`: Calculated ΔB ≤ 0
  - `buyer_insufficient_B`: Buyer can't afford trade
  - `seller_insufficient_A`: Seller doesn't have enough A
  - `buyer_utility_no_improvement`: Buyer's utility doesn't improve
  - `seller_utility_no_improvement`: Seller's utility doesn't improve
  - `both_utility_no_improvement`: Neither agent improves
  - `utility_improves_both`: Success!

### 7. Updated Simulation Orchestration
**File**: `vmt_engine/simulation.py`
- Initialized `DecisionLogger` and `TradeAttemptLogger`
- Changed `AgentSnapshotLogger` to log every tick
- Modified `decision_phase()` to log all decisions with partner selection details
- Modified `trade_phase()` to pass `TradeAttemptLogger` to `trade_pair()`
- Added `close()` method to ensure all loggers are properly closed

## Log Files Generated

After running a simulation, you will find these CSV files in the `logs/` directory:

1. **`agent_snapshots.csv`** - Every tick, all agent states
   - Inventory, position, utility
   - Complete quote data (ask, bid, p_min, p_max)
   - Current target (agent or location)

2. **`decisions.csv`** - Every tick, all agent decisions
   - Which partner was chosen (if any)
   - Surplus with that partner
   - Target type and position
   - Alternative partners considered

3. **`trade_attempts.csv`** - Every trade attempt with full diagnostics
   - For each ΔA attempted in `find_compensating_block()`
   - Complete utility calculations
   - Exact failure reasons
   - This is the most detailed log and will be largest

4. **`trades.csv`** - Successful trades only (existing)
   - Trade size, price, location
   - Buyer and seller IDs

5. **`resource_snapshots.csv`** - Resource state (existing)
   - Grid cell resources at intervals

## How to Use for Diagnosis

### Example: Investigating Why Agents Don't Trade

```python
from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation
import pandas as pd

# Run simulation
config = load_scenario('scenarios/three_agent_barter.yaml')
sim = Simulation(config, seed=21)
sim.run(max_ticks=10)
sim.close()

# Analyze agent snapshots at tick 0
agents_df = pd.read_csv('logs/agent_snapshots.csv')
tick0 = agents_df[agents_df['tick'] == 0]
print("Agent states at tick 0:")
print(tick0[['id', 'A', 'B', 'ask_A_in_B', 'bid_A_in_B', 'p_min', 'p_max']])

# Check decisions
decisions_df = pd.read_csv('logs/decisions.csv')
tick0_decisions = decisions_df[decisions_df['tick'] == 0]
print("\nAgent decisions at tick 0:")
print(tick0_decisions)

# Analyze trade attempts
attempts_df = pd.read_csv('logs/trade_attempts.csv')
tick0_attempts = attempts_df[attempts_df['tick'] == 0]
print("\nTrade attempts at tick 0:")
print(tick0_attempts[['buyer_id', 'seller_id', 'dA_attempted', 'dB_calculated', 
                      'buyer_improves', 'seller_improves', 'result', 'result_reason']])
```

### Key Questions Now Answerable

1. **What are the exact quotes at tick 0?**
   - Check `agent_snapshots.csv`
   - Look at `ask_A_in_B`, `bid_A_in_B`, `p_min`, `p_max`

2. **Do quotes create positive surplus?**
   - Check `decisions.csv` for `surplus_with_partner` values
   - Positive values indicate potential for trade

3. **What happens in `find_compensating_block()`?**
   - Check `trade_attempts.csv`
   - See every ΔA attempted and why it failed/succeeded

4. **Are utility calculations correct?**
   - Check `trade_attempts.csv`
   - Compare `buyer_U_init` vs `buyer_U_final`
   - Check `buyer_improves` and `seller_improves` flags

5. **Where does the logic fail?**
   - Check `result_reason` in `trade_attempts.csv`
   - Exact failure point is logged

## Testing

All existing tests pass:
- 33 tests passed, 1 skipped
- No regressions introduced

The enhanced logging system was tested with `three_agent_barter.yaml` and successfully generated all expected log files with detailed diagnostic data.

## Next Steps

With this telemetry in place, you can now:

1. Run `three_agent_barter.yaml` with seed 21
2. Examine the logs to identify the exact failure point
3. Determine if the issue is:
   - Zero-inventory guard behavior
   - Utility calculation issues
   - Rounding/discretization problems
   - Quote generation problems
4. Implement a targeted fix based on evidence
5. Use the logs to verify the fix works

## Notes

- The logging system is production-ready and adds comprehensive observability
- Log files are flushed on every write for reliability
- All loggers have proper `close()` methods
- The system has minimal performance impact for diagnostic use
- For production runs with thousands of ticks, consider increasing `snapshot_frequency` or selectively disabling verbose loggers

