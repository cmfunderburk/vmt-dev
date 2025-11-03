# The 7-Phase Tick Cycle

Every tick executes exactly 7 phases in this fixed order. **Never violate phase ordering.**

## Phase Order (Immutable)

```
1. Perception    → Build WorldView snapshots
2. Decision      → Three-pass pairing + target selection
3. Movement      → Manhattan movement with tie-breaking
4. Trade         → Paired agents attempt trades
5. Foraging      → Unpaired agents harvest resources
6. Regeneration  → Resources respawn with cooldowns
7. Housekeeping  → Quote refresh, pairing checks, telemetry
```

## Phase 1: Perception

**Purpose**: Build frozen snapshots for decision-making

**Implementation**: `src/vmt_engine/systems/perception.py`

**Key operations**:
- Query neighbors within `vision_radius` using `SpatialIndex`
- Snapshot neighbor quotes (stable for entire tick)
- Identify visible resources
- Build immutable `WorldView` per agent

**Invariant**: Quotes used in decisions are from tick start, even if inventories change later.

## Phase 2: Decision

**Purpose**: Agent target selection and pairing

**Implementation**: `src/vmt_engine/systems/decision.py`

**Three-pass algorithm**:
1. **Pass 1**: Build preference lists (distance-discounted surplus = `surplus × β^distance`)
2. **Pass 2**: Mutual consent pairing (both rank each other as top)
3. **Pass 3**: Greedy surplus matching for unpaired agents

**Key operations**:
- Clear stale resource claims
- Process agents in ID order (determinism)
- Resource claiming: claim forage targets to reduce clustering
- Set `agent.target_pos` and `agent.paired_with_id`

**Outputs**: Target positions, pairing state, preference lists (for telemetry)

## Phase 3: Movement

**Purpose**: Move agents toward targets

**Implementation**: `src/vmt_engine/systems/movement.py`

**Rules**:
- Manhattan movement up to `move_budget_per_tick`
- Tie-breaking: reduce `|dx|` before `|dy|`
- Prefer negative direction on equal distances
- Diagonal deadlock: only higher ID moves
- Update `SpatialIndex` after all movement

**Invariant**: All movement tie-breaking must be deterministic.

## Phase 4: Trade

**Purpose**: Execute bilateral trades for paired agents

**Implementation**: `src/vmt_engine/systems/trading.py`

**Eligibility**:
- Agents must be paired (`paired_with_id` not None)
- Must be within `interaction_radius`
- No active trade cooldown

**Process**:
- Only A↔B barter trades (pure barter economy)
- Compensating block search: scan ΔA, test candidate prices
- First-acceptable-trade principle (not highest surplus)
- Successful trade: maintain pairing, set `inventory_changed=True`
- Failed trade: unpair both agents, set mutual cooldown

**Invariant**: Trade quantities use round-half-up rounding.

## Phase 5: Foraging

**Purpose**: Harvest resources from grid

**Implementation**: `src/vmt_engine/systems/foraging.py`

**Rules**:
- Paired agents skip foraging (exclusive commitment)
- Unpaired agents on resource cells harvest up to `forage_rate`
- If `enforce_single_harvester=True`: only first agent (by ID) harvests
- Set `inventory_changed=True` after harvest

**Invariant**: Paired agents never forage.

## Phase 6: Regeneration

**Purpose**: Respawn harvested resources

**Implementation**: `src/vmt_engine/systems/regeneration.py` (part of Grid)

**Rules**:
- Cells wait `resource_regen_cooldown` ticks after harvest
- Regenerate at `resource_growth_rate` per tick
- Cap at `resource_max_amount`

## Phase 7: Housekeeping

**Purpose**: End-of-tick cleanup and logging

**Implementation**: `src/vmt_engine/systems/housekeeping.py`

**Operations**:
1. **Quote Refresh**: Only for agents with `inventory_changed=True`
2. **Pairing Integrity**: Detect and repair asymmetric pairings
3. **Telemetry Logging**: Batch write agent snapshots, trades, pairings, preferences
4. **State Cleanup**: Clear `_preference_list`, reset flags

**Invariant**: Quotes only refresh here, never mid-tick.

## Phase Dependencies

```
Perception → Decision     (Decision uses WorldView from Perception)
Decision → Movement       (Movement uses targets from Decision)
Movement → Trade          (Trade checks interaction_radius after movement)
Trade → Foraging          (Foraging checks pairing state from Trade)
All → Housekeeping        (Housekeeping logs cumulative tick state)
```

## Code That Spans Phases

**Avoid this**:
```python
# BAD - mixing phases
def mixed_phase():
    decide_target()  # Phase 2
    move_agent()     # Phase 3
    try_trade()      # Phase 4
```

**Do this**:
```python
# GOOD - respect phase boundaries
def run_tick():
    perception_phase()
    decision_phase()
    movement_phase()
    trade_phase()
    foraging_phase()
    regeneration_phase()
    housekeeping_phase()
```

## Debugging Phase Issues

If simulation behavior is wrong, check:
1. Are phases being called in correct order?
2. Is state being mutated outside appropriate phase?
3. Are quotes being refreshed mid-tick?
4. Is pairing state consistent across phases?

**Check phase execution**:
```python
# Add logging to verify phase order
logger.info(f"Tick {tick}: Starting {phase_name}")
```

**Examine telemetry**:
```sql
-- Check tick-by-tick state evolution
SELECT tick, agent_id, pos_x, pos_y, paired_with_id
FROM agent_snapshots 
WHERE run_id = ? AND agent_id = ?
ORDER BY tick;
```

