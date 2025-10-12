# VMT Trade Execution Failure Analysis

## Problem Statement

Agents with complementary inventories and utility functions are not trading, even when:
1. They are within interaction radius (adjacent or co-located)
2. They have `spread=0` (revealing true reservation prices)
3. Their initial endowments suggest gains from trade should exist

## Critical Knowledge Gap

**We cannot diagnose this issue because the telemetry system is incomplete.** The logger only records successful trades, not the decision-making process that leads to trades (or failures to trade). This is a fundamental design flaw that must be addressed before any other fixes.

## Required Diagnostic Information

To understand why trades aren't happening, we need to know:

### 1. Quote Generation (Every Tick)
- What `bid` and `ask` prices is each agent generating?
- What are the underlying reservation bounds `(p_min, p_max)`?
- Is the zero-inventory guard being applied correctly?

### 2. Partner Selection (Every Decision Phase)
- Which agent did each agent choose as a partner (if any)?
- What was the computed surplus for each potential partner?
- Why were certain partners rejected?

### 3. Trade Attempt Details (Every Matching Phase)
- When `find_compensating_block` is called:
  - What price was used?
  - What trade sizes (ΔA) were attempted?
  - For each size, what was the calculated ΔB?
  - Did the utility improvement check pass for both agents?
  - Did the inventory feasibility check pass?
  - What was the final result?

### 4. Movement Decisions
- What target did each agent choose?
- Was it a trade target, forage target, or idle?
- Did movement deadlock prevention activate?

## Hypothesis Space

Without proper telemetry, we can only guess at the root cause:

### H1: No Surplus Exists
- Even with `spread=0`, the agents' reservation prices may not cross
- Agent 0's `bid` (max price to buy B) ≤ Agent 1's `ask` (min price to sell B)

### H2: Surplus Exists but Compensating Block Fails
- Quotes cross, creating surplus
- But `find_compensating_block` cannot find a trade size where both agents strictly improve
- This could happen if the utility gain is too small relative to `epsilon`

### H3: Zero-Inventory Guard Issue
- The epsilon-shift for zero inventories might be creating unexpected behavior
- MRS calculations at `(A+ε, B+ε)` might not align with actual utility changes

### H4: Rounding/Discretization Problem
- The integer constraint and round-half-up rule might prevent feasible trades
- Small trade sizes might not generate enough utility improvement

## Implementation Checklist

### Phase 1: Enhance Telemetry (MUST DO FIRST)
- [ ] Extend `AgentSnapshotLogger` to log every tick, not just periodic snapshots
- [ ] Add quote data (bid, ask, p_min, p_max) to agent snapshots
- [ ] Add partner selection data (chosen partner ID, surplus) to snapshots
- [ ] Create `TradeAttemptLogger` to record all calls to `find_compensating_block`
- [ ] Log each attempted trade size and why it passed/failed
- [ ] Ensure all loggers write on every relevant event, not just successes

### Phase 2: Diagnostic Analysis
- [ ] Run `three_agent_barter.yaml` with seed 21
- [ ] Examine the enhanced logs to identify:
  - Are quotes being generated correctly?
  - Is there actually a positive surplus?
  - Which step in the matching process is failing?
- [ ] Create a minimal test case that reproduces the issue

### Phase 3: Targeted Fix
- [ ] Based on telemetry data, identify the specific failure point
- [ ] Implement the minimal fix needed
- [ ] Add tests to prevent regression
- [ ] Document the root cause and solution

## Design Principles Moving Forward

1. **Complete Observability**: Every decision, calculation, and attempt should be logged
2. **Fail Loud**: When expected behavior doesn't occur, it should be obvious in the logs
3. **Test Coverage**: Every economic edge case needs a test
4. **No Silent Failures**: If agents can't trade when they "should," we need to know why

## Immediate Next Steps

1. **Do NOT modify the trading logic yet** - we don't know what's broken
2. **Implement comprehensive telemetry first** - this is the foundation
3. **Run the scenario and analyze the complete logs**
4. **Only then implement a targeted fix based on evidence**

## Questions to Answer with Enhanced Telemetry

1. What are Agent 0's and Agent 1's exact quotes at tick 0?
2. Do their quotes create a positive surplus?
3. If yes, what happens in `find_compensating_block`?
4. What trade sizes are attempted?
5. What are the exact utility calculations for each attempted trade?
6. Where specifically does the logic fail?

Without answers to these questions, any "fix" is just guessing. The telemetry enhancement must come first.