# Trade Cooldown System - Implementation Complete

## Problem Solved

Agents were detecting small MRS-based surplus, choosing each other as partners, but all trades failed due to discrete utility constraints. They remained locked targeting each other instead of foraging.

**Before (seed=45):**
```
Tick 3-9: Agents 0 & 1 target each other
          54 trade attempts, all fail
          0 foraging
          Stuck in futile loop
```

**After (seed=45):**
```
Tick 0-1: Successful trades
Tick 2: Forage (no surplus)
Tick 3: Trade attempt fails → Cooldown activated
Tick 4-8: Agents forage (cooldown active)
Tick 9: Still foraging

Result: 15 foraging decisions vs 10 trade decisions
```

## How It Works

### Cooldown Lifecycle

1. **Trade Attempt:** Agents within interaction_radius attempt to trade
2. **Trade Fails:** `find_compensating_block()` returns None
3. **Cooldown Set:** Both agents record `trade_cooldowns[partner_id] = current_tick + 5`
4. **Cooldown Period:** Agents skip that partner in `choose_partner()` for 5 ticks
5. **Cooldown Expires:** After 5 ticks, agents can attempt trade again
6. **Forage Instead:** During cooldown, agents forage or seek other partners

### Example with Agents 0 & 1

```
Tick 3: Small surplus detected (0.26)
        Trade attempted between Agent 0 and 1
        All attempts fail (54 tries)
        → Cooldown set: agent 0 can't target 1 until tick 8
        → Cooldown set: agent 1 can't target 0 until tick 8

Tick 4: Agent 0 sees Agent 1, but skips (cooldown active)
        Agent 0 forages instead

Tick 5-7: Both agents continue foraging

Tick 8: Cooldown expires
        Agents can attempt trade again if surplus still exists
```

## Implementation Details

### Files Modified

#### 1. `vmt_engine/core/agent.py`
Added cooldown tracking:
```python
trade_cooldowns: dict[int, int] = {}  # partner_id -> cooldown_until_tick
```

#### 2. `scenarios/schema.py`
Added parameter:
```python
trade_cooldown_ticks: int = 5  # Default: 5-tick cooldown
```

#### 3. `scenarios/loader.py`
Loads cooldown parameter from YAML files.

#### 4. `vmt_engine/simulation.py`
Passes cooldown parameter and current tick to matching system.

#### 5. `vmt_engine/systems/matching.py`

**`choose_partner()` - Filters cooldown partners:**
```python
for neighbor_id in neighbors:
    # Skip if in cooldown
    if neighbor_id in agent.trade_cooldowns:
        if current_tick < agent.trade_cooldowns[neighbor_id]:
            continue  # Skip this partner
        else:
            del agent.trade_cooldowns[neighbor_id]  # Expired
```

**`trade_pair()` - Sets cooldown on failure:**
```python
if block is None:
    # Trade failed
    cooldown_until = tick + params['trade_cooldown_ticks']
    agent_i.trade_cooldowns[agent_j.id] = cooldown_until
    agent_j.trade_cooldowns[agent_i.id] = cooldown_until
    return False
```

## Testing

### Unit Tests (4 tests, all passing)

1. **test_trade_cooldown_prevents_retargeting** - Verifies cooldown blocks re-selection
2. **test_cooldown_allows_other_partners** - Agent A in cooldown with B can still trade with C
3. **test_cooldown_with_no_surplus** - Cooldown doesn't interfere with no-surplus case
4. **test_cooldown_zero_disables** - cooldown_ticks=0 allows immediate retry

### Integration Test Results

**Scenario: three_agent_barter.yaml, seed=45**

Before cooldown:
- 27 trade decisions, 3 forage decisions
- Agents stuck targeting each other

After cooldown:
- 10 trade decisions, 15 forage decisions
- ✅ Agents forage when trades fail
- ✅ Agents explore other opportunities
- ✅ No futile looping

## Configuration

### Default (Enabled)
```yaml
# Centralized in schema.py
trade_cooldown_ticks: 5  # 5-tick cooldown after failed trade
```

### Disable Cooldown
```yaml
params:
  trade_cooldown_ticks: 0  # No cooldown, immediate retry
```

### Longer Cooldown
```yaml
params:
  trade_cooldown_ticks: 10  # Longer exploration period
```

## Benefits

1. **Prevents futile loops** - Agents don't waste ticks on impossible trades
2. **Encourages diverse behavior** - Forage, explore, try other partners
3. **Adaptive** - Agents can retry later if inventories change
4. **Configurable** - Tune for different gameplay styles
5. **Mutual** - Both agents enter cooldown (symmetric)

## Edge Cases Handled

✅ **Multiple partners** - Cooldown with A doesn't prevent trading with B  
✅ **Cooldown expiry** - Automatically removed when expired  
✅ **No surplus** - Doesn't set cooldown if never attempts trade  
✅ **Successful trade** - Doesn't set cooldown, can trade next tick  
✅ **Zero ticks** - cooldown_ticks=0 effectively disables system  

## Performance

- **Memory:** O(partners attempted) per agent, typically < 5 entries
- **CPU:** Dict lookup per neighbor, negligible
- **Cleanup:** Automatic on expiry (lazy deletion)

## Interaction with Other Systems

### With Resource Regeneration
- Agents forage during cooldown
- Resources may regenerate while agent explores
- Creates dynamic return-visit strategies

### With Trading
- Successful trades never trigger cooldown
- Agents continue trading until equilibrium
- Cooldown only on confirmed failures

### With Multi-Agent Scenarios
- Agent A and B in cooldown → both explore
- Agent A can still trade with C, D, E...
- Cooldown is pairwise, not global

## Future Enhancements

Possible extensions:
1. **Graduated cooldown** - Longer cooldown after repeated failures
2. **Partner memory** - Remember which partners never work
3. **Surplus-based cooldown** - Shorter cooldown for larger surplus
4. **Asymmetric cooldown** - Different durations for buyer vs seller

## Status

✅ **Implementation Complete**  
✅ **All Tests Pass (44/44)**  
✅ **Verified with seed=45**  
✅ **Backward Compatible**  
✅ **Ready for Use**

