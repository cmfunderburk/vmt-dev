# Resource Claiming System - Design Document

**Date**: 2025-10-19  
**Status**: Design Proposal  
**Problem**: Multiple agents targeting/harvesting same resource causes inefficient clustering

---

## Problem Statement

### Current Behavior

When multiple agents finish trading and co-locate on the same cell, they often make independent forage decisions that lead to inefficient clustering:

1. **Phase 2 (Decision)**: Multiple co-located agents independently scan visible resources
2. Each agent evaluates resources using `ΔU * β^distance` scoring
3. **Problem**: All agents typically choose the **same** highest-scoring resource
4. **Phase 3 (Movement)**: All agents move toward same target in lockstep
5. **Phase 5 (Foraging)**: When they arrive, only ONE agent can harvest per tick
   - With `forage_rate=1`, resource amount decreases by 1
   - Other agents wait/compete on subsequent ticks
6. **Result**: Inefficient bunching and wasted movement

### Economic Inefficiency

This creates a **coordination failure**:
- Agents ignore opportunity cost of competing for same resource
- No implicit "claiming" mechanism
- Resources elsewhere go unharvested while agents cluster
- Movement budgets wasted chasing already-claimed resources

### Example Scenario

```
Tick 10: Agents 1, 2, 3 co-located at (5, 5) after trading
         Resource A at (8, 5) has amount=5
         Resource B at (5, 8) has amount=5
         
Phase 2: All agents independently evaluate:
         - Resource A: score = ΔU * β^3 = high score
         - Resource B: score = ΔU * β^3 = high score
         All choose Resource A (e.g., due to tie-breaking)

Phase 3-4: All move toward (8, 5) together

Tick 13: All arrive at (8, 5)
         Agent 1 harvests 1 unit (amount -> 4)
         Agents 2, 3 harvest nothing this tick

Tick 14: Agent 2 harvests 1 unit (amount -> 3)
         Agents 1, 3 still there, competing
         
Meanwhile: Resource B at (5, 8) sits untouched!
```

---

## Proposed Solution: Resource Claiming System

### Core Idea

Add **two complementary mechanisms**:

1. **Explicit claiming** during Phase 2 (Decision)
2. **Claim-aware target selection** that avoids claimed resources

### Design Principles

1. **First-come, first-served**: Agent with lowest ID claims resource first (deterministic)
2. **Transient claims**: Claims expire if agent reaches resource or changes target
3. **Claim visibility**: All agents see which resources are claimed before deciding
4. **Backward compatible**: Optional feature with configuration flag
5. **O(N) performance**: No nested loops or expensive data structures

---

## Detailed Implementation

### Phase 1: Add Claim Tracking to Simulation

Add claim tracking state to `Simulation` class:

```python
# In src/vmt_engine/simulation.py __init__

class Simulation:
    def __init__(self, config, seed):
        # ... existing init ...
        
        # Resource claiming (optional feature)
        self.resource_claims: dict[Position, int] = {}  # position -> claiming_agent_id
```

**Performance**: Dict lookup is O(1), total space is O(R) where R = claimed resources (typically << N)

### Phase 2: Claim Logic in Decision System

Modify `DecisionSystem` to handle claiming:

```python
# In src/vmt_engine/systems/decision.py

class DecisionSystem:
    def execute(self, sim: "Simulation") -> None:
        # Clear old claims at start of tick
        if sim.params.get("enable_resource_claiming", False):
            self._clear_stale_claims(sim)
        
        # Process agents in ID order (deterministic)
        for agent in sorted(sim.agents, key=lambda a: a.id):
            view = agent.perception_cache
            
            if sim.current_mode in ("forage", "both"):
                # Filter out claimed resources before target selection
                available_resources = self._filter_claimed_resources(
                    view.get("resource_cells", []), 
                    sim,
                    agent.id
                )
                
                # Choose from available resources only
                target_pos, target_type = self._choose_forage_target_with_claiming(
                    agent, available_resources, sim
                )
                
                if target_pos is not None:
                    agent.target_pos = target_pos
                    agent.target_agent_id = None
                    
                    # Claim the resource
                    if sim.params.get("enable_resource_claiming", False):
                        self._claim_resource(sim, agent.id, target_pos)
                
                # ... rest of decision logic ...
    
    def _clear_stale_claims(self, sim):
        """
        Remove claims from agents that:
        1. Reached their target resource
        2. Changed their target
        3. No longer have a forage target
        """
        claims_to_remove = []
        
        for pos, agent_id in sim.resource_claims.items():
            agent = sim.agent_by_id.get(agent_id)
            if agent is None:
                # Agent doesn't exist (shouldn't happen but be defensive)
                claims_to_remove.append(pos)
                continue
            
            # Check if agent reached the resource
            if agent.pos == pos:
                claims_to_remove.append(pos)
                continue
            
            # Check if agent changed target (no longer targeting this resource)
            if agent.target_pos != pos:
                claims_to_remove.append(pos)
                continue
        
        # Remove stale claims
        for pos in claims_to_remove:
            del sim.resource_claims[pos]
    
    def _filter_claimed_resources(self, resource_cells, sim, current_agent_id):
        """
        Filter out resources already claimed by OTHER agents.
        
        Agent can still target resources it has already claimed.
        """
        if not sim.params.get("enable_resource_claiming", False):
            return resource_cells  # Feature disabled, return all
        
        available = []
        for cell in resource_cells:
            claiming_agent = sim.resource_claims.get(cell.position)
            
            # Include if: unclaimed OR claimed by current agent
            if claiming_agent is None or claiming_agent == current_agent_id:
                available.append(cell)
        
        return available
    
    def _claim_resource(self, sim, agent_id, resource_pos):
        """Record that agent is claiming this resource."""
        sim.resource_claims[resource_pos] = agent_id
```

**Performance**: 
- `_clear_stale_claims`: O(C) where C = number of claims (typically < N)
- `_filter_claimed_resources`: O(R) where R = visible resources per agent (~5-10)
- `_claim_resource`: O(1)
- **Total per tick**: O(N * R) = same as current (resource evaluation already O(N*R))

### Phase 3: Enforce Single-Harvester Rule

**Current behavior**: Multiple agents on same cell can all harvest (limited by `forage_rate` each).

**Proposed behavior**: Only ONE agent harvests per resource cell per tick.

```python
# In src/vmt_engine/systems/foraging.py

class ForageSystem:
    def execute(self, sim: "Simulation") -> None:
        # Track which resources have been harvested this tick
        harvested_this_tick = set()
        
        # Process agents in ID order (deterministic)
        for agent in sorted(sim.agents, key=lambda a: a.id):
            pos = agent.pos
            
            # Skip if this resource was already harvested this tick
            if sim.params.get("enforce_single_harvester", False):
                if pos in harvested_this_tick:
                    continue  # Another agent already harvested here
            
            # Attempt to forage
            did_harvest = forage(agent, sim.grid, sim.params["forage_rate"], sim.tick)
            
            if did_harvest and sim.params.get("enforce_single_harvester", False):
                harvested_this_tick.add(pos)
```

**Performance**: O(N) - same as current

**Determinism**: ✅ Processing by agent ID ensures consistent behavior

---

## Configuration Schema

Add two new optional parameters to `scenarios/schema.py`:

```python
@dataclass
class ScenarioParams:
    # ... existing fields ...
    
    # Resource claiming system (default: enabled)
    enable_resource_claiming: bool = True
    enforce_single_harvester: bool = True
```

**Backward Compatibility**: Both default to `True`, if needed for backward compatibility set to False.

---

## Example Scenario Usage

```yaml
# scenarios/resource_competition_demo.yaml

name: "Resource Competition Demo"
N: 15
agents: 6

params:
  # ... other params ...
  
  # Enable resource claiming to reduce clustering
  enable_resource_claiming: true
  enforce_single_harvester: true
  
  forage_rate: 1
```

---

## Expected Behavior Changes

### Before (Current)

```
Tick 10: Agents 1, 2, 3 at (5, 5)
         Resource A at (8, 5), amount=5
         Resource B at (5, 8), amount=5

Phase 2: All agents choose Resource A
Phase 3: All move toward (8, 5)
Tick 13: All arrive
         Agent 1 harvests 1 (amount -> 4)
         Agents 2, 3 idle
Tick 14: Agent 2 harvests 1 (amount -> 3)
         Agent 1, 3 idle

Result: Resource B untouched, 3 agents bunched
```

### After (With Claiming)

```
Tick 10: Agents 1, 2, 3 at (5, 5)
         Resource A at (8, 5), amount=5
         Resource B at (5, 8), amount=5

Phase 2 (ID-sorted processing):
  Agent 1: Claims Resource A (best score)
  Agent 2: Sees A is claimed, chooses Resource B (next best)
  Agent 3: Sees A, B claimed, chooses Resource C or idles

Phase 3: 
  Agent 1 moves toward (8, 5)
  Agent 2 moves toward (5, 8)
  Agent 3 moves toward different resource

Tick 13: Agents spread across multiple resources
         Each harvesting independently

Result: Efficient resource utilization, no bunching
```

---

## Edge Cases & Handling

### Edge Case 1: Claim Expires Mid-Path

**Scenario**: Agent 1 claims resource at (10, 10), starts moving. On Tick 5, Agent 1 encounters a better trade partner and switches target.

**Handling**: Claim is cleared in `_clear_stale_claims()` because `agent.target_pos != claimed_pos`. Resource becomes available for other agents.

### Edge Case 2: All Resources Claimed

**Scenario**: 10 agents, only 3 visible resources, all claimed by first 3 agents.

**Handling**: Remaining agents get empty `available_resources` list. `choose_forage_target()` returns `None`, agents idle. This is correct behavior - no resources available.

### Edge Case 3: Agent Reaches Resource But Can't Harvest

**Scenario**: Agent reaches resource cell, but `enforce_single_harvester=True` and another agent (lower ID) already harvested it this tick.

**Handling**: 
- Agent doesn't harvest this tick
- Claim expires because `agent.pos == claimed_pos`
- Next tick, agent re-evaluates and may choose different target

### Edge Case 4: Resource Depleted Before Agent Arrives

**Scenario**: Agent 1 claims resource with amount=1. Agent 2 is already on cell and harvests it completely before Agent 1 arrives.

**Handling**:
- When Agent 1 arrives, `cell.resource.amount == 0`
- `forage()` returns `False` (no harvest)
- Claim expires
- Next tick, Agent 1 chooses new target

### Edge Case 5: Claim Conflicts (shouldn't happen but defensive)

**Scenario**: Due to bug, two agents try to claim same resource.

**Handling**: Processing in ID order ensures lower ID always claims first. Higher ID sees resource as claimed during `_filter_claimed_resources()`.

---

## Testing Strategy

### Unit Tests

Create `tests/test_resource_claiming.py`:

```python
def test_claiming_disabled_by_default():
    """Verify claiming is opt-in (backward compatibility)."""
    # Load scenario without claiming flags
    # Verify multiple agents can target same resource

def test_single_agent_claims_resource():
    """Single agent successfully claims visible resource."""
    # 1 agent, 1 resource
    # Verify claim recorded in sim.resource_claims

def test_second_agent_avoids_claimed_resource():
    """Second agent chooses different resource when first is claimed."""
    # 2 agents at same location, 2 resources
    # Agent 1 claims Resource A
    # Verify Agent 2 chooses Resource B

def test_claim_expires_when_reached():
    """Claim is removed when agent reaches resource."""
    # Agent claims resource, moves toward it
    # When agent reaches, claim should be cleared

def test_claim_expires_when_target_changes():
    """Claim is removed when agent changes target."""
    # Agent claims resource
    # Next tick, agent targets trade partner instead
    # Verify claim is cleared

def test_single_harvester_enforcement():
    """Only first agent harvests when enforce_single_harvester=True."""
    # 3 agents on same resource cell
    # Only lowest ID should harvest

def test_deterministic_claiming():
    """Same seed produces identical claim patterns."""
    # Run scenario twice with same seed
    # Verify identical resource_claims state each tick
```

### Integration Tests

Add to `tests/test_integration_resource_competition.py`:

```python
def test_reduced_clustering_with_claiming():
    """Claiming reduces agent clustering at resources."""
    # Run scenario with 6 agents, 3 resources
    # Compare with/without claiming
    # Measure: average agents per resource cell
    # Expect: lower clustering with claiming enabled
```

---

## Performance Analysis

### Current System (No Claiming)

```
Phase 2 (Decision): O(N * R) where R = resources per agent view
Phase 5 (Foraging): O(N)
```

### Proposed System (With Claiming)

```
Phase 2 (Decision): 
  - Clear stale claims: O(C) where C = active claims
  - Filter resources per agent: O(R)
  - Claim resource: O(1)
  - Total: O(C + N*R) = O(N*R) (since C ≤ N)

Phase 5 (Foraging):
  - Track harvested cells: O(N) space
  - Check if harvested: O(1) per agent
  - Total: O(N)
```

**Conclusion**: No asymptotic change. Same O(N*R) complexity.

**Overhead**: Dict operations (O(1) average) for claim management. Negligible in practice.

---

## Telemetry Enhancements

### Optional: Add Claims Table

```python
# In src/telemetry/database.py

def create_tables(self):
    # ... existing tables ...
    
    self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS resource_claims (
            tick INTEGER,
            agent_id INTEGER,
            resource_x INTEGER,
            resource_y INTEGER,
            claim_status TEXT,  -- 'new', 'renewed', 'expired'
            PRIMARY KEY (tick, agent_id, resource_x, resource_y)
        )
    """)
```

**Purpose**: Track claim dynamics for analysis:
- How often do claims expire before reaching resource?
- What's the average distance traveled to claimed resources?
- Does claiming reduce total movement?

**Overhead**: Minimal (C log entries per tick where C = active claims)

---

## Backward Compatibility Guarantees

1. **Default disabled**: Both `enable_resource_claiming` and `enforce_single_harvester` default to `False`
2. **Existing scenarios unchanged**: All scenarios in `scenarios/` continue working identically
3. **All tests pass**: 160/160 tests must pass with feature disabled
4. **Determinism preserved**: Feature doesn't affect RNG or tick order

---

## Implementation Checklist

### Phase A: Core Claiming Logic
- [ ] Add `resource_claims` dict to `Simulation.__init__`
- [ ] Add config fields to `ScenarioParams` (default False)
- [ ] Implement `_clear_stale_claims()` in `DecisionSystem`
- [ ] Implement `_filter_claimed_resources()` in `DecisionSystem`
- [ ] Implement `_claim_resource()` in `DecisionSystem`
- [ ] Update `execute()` in `DecisionSystem` to use claiming logic

### Phase B: Single Harvester Enforcement
- [ ] Modify `ForageSystem.execute()` to track harvested cells
- [ ] Add conditional check before allowing harvest

### Phase C: Testing
- [ ] Create `tests/test_resource_claiming.py` (7+ tests)
- [ ] Add integration test for clustering reduction
- [ ] Run full test suite (all must pass)
- [ ] Benchmark performance (verify <5% overhead)

### Phase D: Documentation
- [ ] Update `docs/2_technical_manual.md` with claiming system
- [ ] Create demo scenario `scenarios/resource_competition_demo.yaml`
- [ ] Update `CHANGELOG.md`
- [ ] Add telemetry table if implemented

---

## Open Questions for Discussion

### Question 1: Should claims be visible in perception?

**Current proposal**: Agents see filtered resource lists (claimed resources removed)

**Alternative**: Show all resources but mark claimed ones
```python
cell.claimed_by = agent_id  # Add to PerceptionView
```

**Trade-off**: More information vs simpler API

**Recommendation**: Start with filtered lists (simpler), add visibility later if needed for research.

### Question 2: Should agents "reserve" capacity?

**Current proposal**: Binary claiming (claimed or not)

**Alternative**: Agent claims N units of resource based on utility need
```python
resource_claims[pos] = {
    'agent_id': 1,
    'reserved_amount': 3
}
```

**Trade-off**: More realistic vs more complex

**Recommendation**: Start with binary claiming. Add capacity reservation in future version if research requires it.

### Question 3: Priority system for claims?

**Current proposal**: First-come (lowest ID) always wins

**Alternative**: Higher-utility agents get priority
```python
# If Agent 2 has 10x utility gain vs Agent 1's 2x gain,
# Agent 2 could "outbid" the claim
```

**Trade-off**: Economic efficiency vs determinism complexity

**Recommendation**: Start with ID-based priority (simplest, most deterministic). Research extension could add utility-based priority.

### Question 4: Telemetry logging priority?

**Options**:
- **A**: No telemetry (simplest, least overhead)
- **B**: Log to existing `decisions` table (add `claimed_resource_pos` column)
- **C**: New `resource_claims` table (most detailed)

**Recommendation**: Option B (log in decisions table). Easy to add, no schema migration burden.

---

## Expected Impact

### Benefits

1. **Reduced clustering**: Agents spread across multiple resources instead of bunching
2. **Higher throughput**: More resources harvested per tick (agents don't idle waiting)
3. **Better visualization**: Co-location rendering now handles fewer edge cases
4. **Emergent coordination**: Decentralized claiming creates efficient allocation
5. **Research value**: Study coordination failures with/without claiming

### Risks

1. **Behavioral change**: Existing scenario dynamics may shift (hence opt-in)
2. **Testing burden**: Need comprehensive tests for claim expiration logic
3. **Complexity**: More moving parts = more potential bugs

### Mitigation

- Opt-in design ensures backward compatibility
- Comprehensive test suite catches regressions
- Clear documentation explains when to enable feature

---

## Recommendation

**Proceed with implementation** of resource claiming system as designed.

This is a **high-value, low-risk enhancement** that:
- ✅ Solves real coordination problem
- ✅ Maintains backward compatibility
- ✅ Preserves determinism and performance
- ✅ Adds research value (can study with/without claiming)
- ✅ Clean, testable design

The feature aligns perfectly with VMT's mission: demonstrating economic phenomena through simulation. Resource claiming is a microeconomic coordination mechanism worthy of study.

---

**Next Steps**: Review design, discuss open questions, then implement Phase A (core claiming logic).
