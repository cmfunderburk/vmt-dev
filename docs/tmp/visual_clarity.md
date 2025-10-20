# Visual Clarity Enhancement: Agent De-colocation for Trading Pairs

**Author**: GitHub Copilot  
**Date**: 2025-10-19  
**Status**: Design Proposal  
**Context**: Pygame rendering issue where trading agents stack on same cell

---

## Executive Summary

When two agents successfully complete a trade, they are often co-located on the same grid cell. This creates visual confusion in the Pygame renderer where both agents are drawn as overlapping circles at the exact same position, making it difficult to see that two agents are present. This document analyzes the problem and proposes a **minimal, non-invasive solution** that improves visual clarity without interfering with foundational economic logic or introducing performance overhead.

**Recommended Solution**: Add an optional **post-trade micro-nudge** in Phase 7 (Housekeeping) that moves one agent to a free adjacent cell if available, purely for visualization purposes.

---

## Problem Statement

### Current Behavior

1. **Phase 2 (Decision)**: Agent A targets Agent B for trade based on surplus calculation
2. **Phase 3 (Movement)**: Agent A moves toward Agent B 
3. **Phase 4 (Trade)**: When within `interaction_radius`, agents execute trade if they're on the same cell or adjacent
4. **Result**: Agents remain co-located on same cell after trade completes

### Visual Impact

From `src/vmt_pygame/renderer.py:draw_agents()` (lines 203-255):
```python
# Calculate center position
px = screen_x + self.cell_size // 2
py = screen_y + self.cell_size // 2

# Draw agent circle
radius = max(3, self.cell_size // 3)
pygame.draw.circle(self.screen, color, (px, py), radius)
```

When two agents occupy the same cell:
- Both circles are drawn at the **exact same (px, py) coordinates**
- Only the top-drawn agent is visible (the second agent is completely hidden)
- Agent IDs and inventory labels overlap and become unreadable
- Users cannot tell that two agents are present at all

### Why This Matters

- **Educational Use**: Students observing the simulation cannot see which agents are trading
- **Research Use**: Harder to track agent clustering and interaction patterns visually
- **Debugging**: Difficult to verify correct agent counts and positions during development

---

## Core Constraints (Non-Negotiable)

### 1. Preserve Determinism (SACRED)

From `.github/copilot-instructions.md`:
> **Determinism Rules (SACRED)**
> 1. Always sort agent loops by `agent.id`
> 2. Always sort trade pairs by `(min_id, max_id)`
> 3. Never mutate quotes mid-tick
> 4. One trade attempt per pair per tick

**Implication**: Any de-colocation logic MUST be deterministic and MUST NOT affect:
- Partner selection (Phase 2)
- Movement decisions (Phase 3)
- Trade execution (Phase 4)
- Resource foraging (Phase 5)

### 2. No Performance Regression (O(N) Maximum)

From `.github/copilot-instructions.md`:
> You are not to introduce any performance overhead greater than O(n)

Current performance baseline: ~152 tests passing in 3.73s

**Implication**: Cannot use O(N²) checks. Must leverage existing spatial index infrastructure.

### 3. Non-Functional Feature (Visual Only)

This is explicitly a **visualization enhancement**, not an economic mechanism. The simulation's core economic logic must be unchanged:
- Trades happen based on surplus, not spatial arrangement
- Movement is driven by utility-seeking, not visual considerations
- Resource foraging is unaffected

---

## Existing Collision-Handling Mechanisms

The codebase already contains precedent for handling agent positioning issues:

### Diagonal Deadlock Prevention

From `src/vmt_engine/systems/movement.py` (lines 30-43):
```python
# Check for diagonal deadlock with another agent
if agent.target_agent_id is not None:
    target_agent = sim.agent_by_id.get(agent.target_agent_id)
    if target_agent and target_agent.target_agent_id == agent.id:
        # Both agents are targeting each other.
        # Check if they are diagonally adjacent
        if (
            sim.grid.manhattan_distance(agent.pos, target_agent.pos) == 2
            and abs(agent.pos[0] - target_agent.pos[0]) == 1
            and abs(agent.pos[1] - target_agent.pos[1]) == 1
        ):
            # Diagonal deadlock detected. Only higher ID agent moves.
            if agent.id < target_agent.id:
                continue  # Lower ID agent waits
```

**Key Insight**: The system already modifies movement for non-economic reasons (avoiding deadlock). Precedent exists for spatial adjustments that don't affect core economic logic.

---

## Proposed Solution: Post-Trade Micro-Nudge

### High-Level Design

Add a new **optional micro-adjustment** in **Phase 7 (Housekeeping)** that:
1. Identifies agents who just completed a trade on the same cell
2. Attempts to move **only the higher-ID agent** to a free adjacent cell
3. Updates spatial index if movement occurs
4. Does NOT affect any economic calculations (quotes already refreshed before this step)

### Why Phase 7 (Housekeeping)?

From `docs/2_technical_manual.md`:
> **7. Housekeeping**: The tick concludes with cleanup and maintenance tasks. Agents refresh their trade quotes based on their new inventory levels, and the telemetry system logs all data for the tick to the database.

Phase 7 is the perfect location because:
- All economic decisions for this tick are **already complete**
- Quotes are **already refreshed** based on new inventories
- Telemetry has **already been logged** (trade positions recorded)
- This phase is explicitly for "cleanup and maintenance"
- Moving an agent here won't affect next tick's perception (which creates a fresh snapshot)

### Detailed Implementation

#### Step 1: Detect Co-located Agents

In Phase 7, after quote refresh but before tick ends:

```python
def detect_colocated_agents(self, sim: 'Simulation') -> list[tuple[int, int]]:
    """
    Find pairs of agents on the same cell.
    
    Returns:
        List of (lower_id, higher_id) tuples for co-located pairs
    """
    # Use spatial index for O(N) detection
    # Query all agents within radius=0 (same cell only)
    colocated_pairs = []
    seen_positions = {}
    
    for agent in sorted(sim.agents, key=lambda a: a.id):
        pos = agent.pos
        if pos in seen_positions:
            # Found colocation
            other_id = seen_positions[pos]
            pair = (min(agent.id, other_id), max(agent.id, other_id))
            colocated_pairs.append(pair)
        else:
            seen_positions[pos] = agent.id
    
    return colocated_pairs
```

**Performance**: O(N) - single pass through all agents

#### Step 2: Check if Pair Just Traded

Track recent trades in telemetry. Check if this pair executed a trade this tick:

```python
def pair_just_traded(agent_i_id: int, agent_j_id: int, recent_trades: list) -> bool:
    """Check if two agents just traded this tick."""
    for trade in recent_trades:
        if {trade['buyer_id'], trade['seller_id']} == {agent_i_id, agent_j_id}:
            return True
    return False
```

**Performance**: O(T) where T = trades this tick (typically T << N)

#### Step 3: Find Free Adjacent Cell

```python
def find_free_adjacent_cell(pos: Position, grid: Grid, spatial_index: SpatialIndex) -> Position | None:
    """
    Find a free adjacent cell (Manhattan distance = 1) with no agent.
    
    Tie-breaking: Prefer cells in order: (x-1,y), (x+1,y), (x,y-1), (x,y+1)
    
    Returns:
        Free adjacent position or None if all occupied
    """
    x, y = pos
    candidates = [
        (x - 1, y),  # Left
        (x + 1, y),  # Right  
        (x, y - 1),  # Down
        (x, y + 1),  # Up
    ]
    
    for candidate in candidates:
        cx, cy = candidate
        # Check grid bounds
        if not (0 <= cx < grid.N and 0 <= cy < grid.N):
            continue
        
        # Check if any agent is at this position (O(1) average case with spatial index)
        agents_at_pos = spatial_index.query_radius(candidate, radius=0)
        if len(agents_at_pos) == 0:
            return candidate
    
    return None
```

**Performance**: O(1) - checks exactly 4 cells with O(1) spatial index lookups

#### Step 4: Execute Micro-Nudge

```python
def execute_micro_nudge(self, sim: 'Simulation') -> None:
    """
    Phase 7 micro-adjustment: separate co-located trading partners.
    
    Only affects visualization, does not change economic behavior.
    """
    # Skip if feature disabled
    if not sim.params.get('enable_visual_decolocation', False):
        return
    
    colocated_pairs = self.detect_colocated_agents(sim)
    
    for id_i, id_j in colocated_pairs:
        # Check if this pair just traded
        if not self.pair_just_traded(id_i, id_j, sim.telemetry.recent_trades_for_renderer):
            continue
        
        agent_i = sim.agent_by_id[id_i]
        agent_j = sim.agent_by_id[id_j]
        
        # Deterministic: higher ID agent moves
        mover = agent_j if agent_j.id > agent_i.id else agent_i
        
        # Find free adjacent cell
        new_pos = self.find_free_adjacent_cell(mover.pos, sim.grid, sim.spatial_index)
        
        if new_pos is not None:
            # Update agent position
            old_pos = mover.pos
            mover.pos = new_pos
            
            # Update spatial index
            sim.spatial_index.update_position(mover.id, new_pos)
            
            # Optional: Log the nudge for debugging
            if sim.telemetry:
                sim.telemetry.log_visual_nudge(sim.tick, mover.id, old_pos, new_pos)
```

**Performance**: O(N + T) where T = trades. Since T ≤ N/2 (max one trade per agent), total is O(N).

### Schema Changes

Add optional parameter to `scenarios/schema.py`:

```python
@dataclass
class ScenarioParams:
    # ... existing fields ...
    
    # Visual enhancement (default: disabled for backward compatibility)
    enable_visual_decolocation: bool = False
```

Users can opt-in per scenario:
```yaml
params:
  enable_visual_decolocation: true
```

---

## Alternative Approaches Considered

### Option A: Modify Phase 3 (Movement) to Avoid Co-location

**Idea**: Make agents stop 1 cell away from trading partner instead of moving onto same cell.

**Rejected Because**:
- Breaks interaction semantics (agents expect to be within `interaction_radius`)
- `interaction_radius` can be 0, 1, or more - makes logic complex
- Affects foundational movement logic (violation of non-functional constraint)
- Creates edge cases with diagonal adjacency

### Option B: Modify Phase 4 (Trade) to Push Agents Apart

**Idea**: After successful trade, push one agent to adjacent cell.

**Rejected Because**:
- Phase 4 should be pure economic logic
- Trade execution and spatial adjustment are conceptually distinct operations
- Harder to make optional (trades should work with or without this feature)

### Option C: Renderer-Only Solution (Display Offset)

**Idea**: When rendering, draw co-located agents with small pixel offsets without changing actual positions.

**Rejected Because**:
- Doesn't solve the fundamental problem (users still think agents are in wrong place)
- Creates visual inconsistency (agent appears between cells)
- Doesn't help with inventory label overlap
- Misleading for educational purposes (position IS semantically important)

---

## Testing Strategy

### Unit Tests

Create `tests/test_visual_decolocation.py`:

```python
def test_micro_nudge_disabled_by_default():
    """Verify feature is opt-in and doesn't break existing scenarios."""
    # Run test without enable_visual_decolocation flag
    # Verify agents can still co-locate (backward compatibility)

def test_micro_nudge_deterministic():
    """Verify micro-nudge is deterministic across runs."""
    # Run same scenario twice with same seed
    # Verify identical final positions

def test_micro_nudge_only_after_trade():
    """Verify nudge only occurs for trading pairs."""
    # Create scenario where agents forage to same cell (no trade)
    # Verify they remain co-located (nudge didn't trigger)

def test_micro_nudge_higher_id_moves():
    """Verify deterministic choice of which agent moves."""
    # Set up co-located pair
    # Verify agent with higher ID is the one that moves

def test_micro_nudge_when_no_free_cell():
    """Verify graceful handling when all adjacent cells occupied."""
    # Surround co-located pair with agents on all 4 adjacent cells
    # Verify they remain co-located (no crash or invalid move)

def test_spatial_index_updated():
    """Verify spatial index remains consistent after nudge."""
    # After nudge, query spatial index
    # Verify moved agent is in correct bucket
```

### Integration Tests

Add assertions to existing `tests/test_barter_integration.py`:
- Run with `enable_visual_decolocation: false` → verify no change in behavior
- Run with `enable_visual_decolocation: true` → verify agent separation occurs
- Compare telemetry logs (should be identical except for positions after trade)

### Performance Testing

Update `scripts/benchmark_performance.py`:
- Benchmark scenarios with feature enabled vs disabled
- Verify TPS (ticks per second) delta is negligible (<5%)

---

## Backward Compatibility

**Critical**: This feature MUST be backward compatible.

### Guarantees

1. **Default Off**: Feature disabled by default via `enable_visual_decolocation: false`
2. **No Schema Breaking**: All existing scenarios work without modification
3. **Opt-In Only**: Users must explicitly enable feature in scenario YAML
4. **Determinism Preserved**: When enabled, behavior is fully deterministic
5. **Tests Still Pass**: All 152 existing tests continue passing without modification

### Migration Path

Existing scenarios:
```yaml
# No change needed - feature disabled by default
params:
  N: 20
  vision_radius: 5
```

New scenarios (opt-in):
```yaml
params:
  N: 20
  vision_radius: 5
  enable_visual_decolocation: true  # Enable visual clarity enhancement
```

---

## Documentation Requirements

### User-Facing Documentation

Update `docs/1_project_overview.md`:
- Add section explaining visual decolocation feature
- Clarify it's a visualization aid, not economic logic
- Provide example YAML snippet

### Technical Documentation

Update `docs/2_technical_manual.md`:
- Document the micro-nudge in Phase 7 section
- Explain when/why it runs
- Link to this design document

### Scenario Template

Create `scenarios/visual_clarity_demo.yaml`:
- Demonstrate feature with 3-4 agents
- Show agents trading and auto-separating
- Include comments explaining the feature

---

## Open Questions & Future Enhancements

### Question 1: Should We De-collocate Non-Trading Pairs?

**Current Proposal**: Only separate agents who just completed a trade.

**Alternative**: Separate ANY co-located agents, regardless of trade status.

**Recommendation**: Start with trade-only approach. If users report issues with foraging agents stacking, expand scope in future version.

### Question 2: Should Movement Direction Be Smarter?

**Current Proposal**: Fixed tie-breaking order: left, right, down, up.

**Alternative**: Move away from opponent's next target to minimize future re-colocation.

**Recommendation**: Keep simple tie-breaking for now. Smart positioning is complex and risks violating non-functional constraint.

### Question 3: Telemetry Logging?

**Current Proposal**: Optional logging via `log_visual_nudge()`.

**Question**: Should this be in main telemetry DB or separate log?

**Recommendation**: Main DB with new table `visual_nudges(tick, agent_id, old_x, old_y, new_x, new_y)`. Useful for debugging and understanding agent clustering.

---

## Implementation Checklist

- [ ] Add `enable_visual_decolocation: bool` to schema with default False
- [ ] Implement `detect_colocated_agents()` in new `systems/visual_clarity.py`
- [ ] Implement `find_free_adjacent_cell()` with deterministic tie-breaking
- [ ] Implement `execute_micro_nudge()` in Phase 7 of simulation loop
- [ ] Add `visual_nudges` table to telemetry schema (remember to delete old DB!)
- [ ] Create `tests/test_visual_decolocation.py` with 6+ test cases
- [ ] Update `tests/test_barter_integration.py` to verify backward compatibility
- [ ] Run `pytest -q` and verify all tests pass
- [ ] Run `scripts/benchmark_performance.py` and verify <5% performance delta
- [ ] Create `scenarios/visual_clarity_demo.yaml` example scenario
- [ ] Update `docs/2_technical_manual.md` Phase 7 section
- [ ] Update `docs/1_project_overview.md` with feature explanation
- [ ] Update `CHANGELOG.md` under `[Unreleased]`
- [ ] Test with GUI: `python launcher.py` → load demo → observe agent separation

---

## Risk Assessment

### Low Risk ✅

- **Performance**: O(N) algorithm, leverages existing spatial index, negligible overhead
- **Determinism**: Fully deterministic with sorted iteration and fixed tie-breaking
- **Backward Compatibility**: Opt-in feature, default disabled, no breaking changes
- **Code Complexity**: ~100 lines of new code in isolated module

### Medium Risk ⚠️

- **User Confusion**: Users might think micro-nudge affects economic behavior
  - **Mitigation**: Clear documentation emphasizing "visual only"
- **Edge Cases**: Agents surrounded by others with no free cell
  - **Mitigation**: Graceful fallback (stay co-located)

### No High Risks Identified

---

## Recommendation

**Proceed with implementation** using the Post-Trade Micro-Nudge approach.

This solution:
1. ✅ Solves the visual clarity problem
2. ✅ Maintains all core invariants (determinism, performance, backward compatibility)
3. ✅ Provides clear precedent (diagonal deadlock handling)
4. ✅ Minimal code complexity (~100 LOC)
5. ✅ Opt-in design (no forced changes for existing users)
6. ✅ Well-scoped for incremental enhancement

The feature should be implemented in a new file `src/vmt_engine/systems/visual_clarity.py` and integrated into Phase 7 (Housekeeping) with an explicit flag check. All 152 existing tests must continue passing without modification.

---

**Next Steps**: Discuss this proposal, address any concerns, then proceed with implementation checklist if approved.
