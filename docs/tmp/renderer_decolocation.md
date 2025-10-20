# Renderer-Only Visual Decolocation Design

**Author**: GitHub Copilot  
**Date**: 2025-10-19  
**Status**: Design Proposal (PREFERRED APPROACH)  
**Context**: Pygame rendering enhancement for co-located agents

---

## Executive Summary

This document proposes a **pure visualization solution** that handles co-located agents entirely within the Pygame renderer without modifying any simulation state. When multiple agents occupy the same grid cell, the renderer will:

1. **Scale agent sprites** proportionally to the number of co-located agents
2. **Position agents** in non-overlapping layouts within the cell
3. **Adjust labels** to prevent overlap and maintain readability

**Key Advantage**: Zero impact on simulation logic, determinism, or performance. Pure presentation layer.

---

## Design Philosophy

### Separation of Concerns

```
┌─────────────────────────────────────┐
│   Simulation Layer (vmt_engine)    │
│   - Economic logic                  │
│   - Agent positions (ground truth)  │
│   - Trade execution                 │
│   - NO CHANGES NEEDED               │
└─────────────────────────────────────┘
                 ↓
          (read-only)
                 ↓
┌─────────────────────────────────────┐
│   Visualization Layer (vmt_pygame)  │
│   - Detect co-location              │
│   - Calculate visual offsets        │
│   - Scale sprites intelligently     │
│   - ALL CHANGES HERE                │
└─────────────────────────────────────┘
```

**Principle**: The simulation maintains a single source of truth (agent.pos). The renderer interprets this data for optimal visual presentation.

---

## Proposed Layouts

### Layout Geometry

Each grid cell has dimensions `cell_size × cell_size` pixels. Agents are drawn as circles with configurable radius. When multiple agents share a cell, we use geometric patterns that maximize spacing:

#### 1 Agent (Current Behavior)
```
┌─────────────┐
│             │
│      ●      │  radius = cell_size // 3
│             │  position = center
│             │
└─────────────┘
```

#### 2 Agents
```
┌─────────────┐
│   ●         │  radius = cell_size // 4  (75% of normal)
│             │  
│         ●   │  positions = opposite corners
│             │  offset = ±cell_size // 4
└─────────────┘
```

#### 3 Agents
```
┌─────────────┐
│      ●      │  radius = cell_size // 5  (60% of normal)
│             │  
│   ●     ●   │  positions = triangle pattern
│             │  angles = 0°, 120°, 240°
└─────────────┘
```

#### 4 Agents
```
┌─────────────┐
│  ●      ●   │  radius = cell_size // 6  (50% of normal)
│             │
│  ●      ●   │  positions = four corners
│             │  offset = ±cell_size // 4 for x and y
└─────────────┘
```

#### 5+ Agents (Circle Pack)
```
┌─────────────┐
│   ●  ●  ●   │  radius = cell_size // (2 + count)
│             │  
│  ● center ● │  positions = circle around center
│             │  angles = evenly distributed
│   ●  ●  ●   │
└─────────────┘
```

### Scaling Formula

```python
def calculate_agent_radius(cell_size: int, agent_count: int) -> int:
    """
    Calculate optimal agent radius based on co-location count.
    
    Strategy:
    - 1 agent: cell_size // 3 (current behavior)
    - 2 agents: cell_size // 4 (75% scale)
    - 3 agents: cell_size // 5 (60% scale)
    - 4+ agents: cell_size // (count + 2) with floor of 3px
    
    Returns:
        Radius in pixels (minimum 3px for visibility)
    """
    if agent_count == 1:
        return max(3, cell_size // 3)
    elif agent_count == 2:
        return max(3, cell_size // 4)
    elif agent_count == 3:
        return max(3, cell_size // 5)
    else:
        return max(3, cell_size // (agent_count + 2))
```

---

## Implementation Design

### Phase 1: Co-location Detection

Add helper method to group agents by position:

```python
def group_agents_by_position(self) -> dict[tuple[int, int], list['Agent']]:
    """
    Group agents by their grid position.
    
    Returns:
        Dictionary mapping (x, y) position to list of agents at that position
    """
    position_groups = {}
    
    for agent in self.sim.agents:
        pos = agent.pos
        if pos not in position_groups:
            position_groups[pos] = []
        position_groups[pos].append(agent)
    
    # Sort agents within each group by ID for deterministic rendering
    for pos in position_groups:
        position_groups[pos].sort(key=lambda a: a.id)
    
    return position_groups
```

**Performance**: O(N) - single pass through all agents  
**Determinism**: Sorting by ID ensures consistent visual order across runs

### Phase 2: Position Calculation Functions

```python
def calculate_agent_display_position(
    self,
    agent_index: int,
    total_agents: int,
    cell_center_x: int,
    cell_center_y: int
) -> tuple[int, int]:
    """
    Calculate display position for agent within a co-located group.
    
    Args:
        agent_index: Index of agent in sorted group (0 to total_agents-1)
        total_agents: Total number of agents at this position
        cell_center_x: Center x coordinate of cell in screen pixels
        cell_center_y: Center y coordinate of cell in screen pixels
        
    Returns:
        (px, py) display coordinates for this agent
    """
    if total_agents == 1:
        # Single agent - use center (current behavior)
        return (cell_center_x, cell_center_y)
    
    elif total_agents == 2:
        # Two agents - opposite corners (diagonal)
        # Agent 0: upper-left, Agent 1: lower-right
        offset = self.cell_size // 4
        if agent_index == 0:
            return (cell_center_x - offset, cell_center_y - offset)
        else:
            return (cell_center_x + offset, cell_center_y + offset)
    
    elif total_agents == 3:
        # Three agents - triangle pattern
        import math
        offset = self.cell_size // 4
        # Angles: 90° (top), 210° (bottom-left), 330° (bottom-right)
        angles = [90, 210, 330]
        angle_rad = math.radians(angles[agent_index])
        px = cell_center_x + int(offset * math.cos(angle_rad))
        py = cell_center_y - int(offset * math.sin(angle_rad))  # Negative because y increases downward
        return (px, py)
    
    elif total_agents == 4:
        # Four agents - one per corner
        offset = self.cell_size // 4
        corners = [
            (-offset, -offset),  # Upper-left
            (offset, -offset),   # Upper-right
            (-offset, offset),   # Lower-left
            (offset, offset),    # Lower-right
        ]
        dx, dy = corners[agent_index]
        return (cell_center_x + dx, cell_center_y + dy)
    
    else:
        # 5+ agents - circle pack around center
        import math
        offset = self.cell_size // 3
        angle_step = 360 / total_agents
        angle_rad = math.radians(agent_index * angle_step)
        px = cell_center_x + int(offset * math.cos(angle_rad))
        py = cell_center_y - int(offset * math.sin(angle_rad))
        return (px, py)
```

**Note**: This function is deterministic - same inputs always produce same outputs.

### Phase 3: Refactor draw_agents()

Replace the current single-pass loop with a group-based approach:

```python
def draw_agents(self):
    """Draw agents with intelligent co-location handling."""
    # Group agents by position
    position_groups = self.group_agents_by_position()
    
    for pos, agents in position_groups.items():
        x, y = pos
        screen_x, screen_y = self.to_screen_coords(x, y)
        
        # Skip if not visible
        if not self.is_visible(screen_x, screen_y):
            continue
        
        # Calculate cell center
        cell_center_x = screen_x + self.cell_size // 2
        cell_center_y = screen_y + self.cell_size // 2
        
        # Calculate optimal radius for this group size
        agent_count = len(agents)
        radius = self.calculate_agent_radius(self.cell_size, agent_count)
        
        # Draw each agent in the group
        for idx, agent in enumerate(agents):
            # Get display position for this agent
            px, py = self.calculate_agent_display_position(
                idx, agent_count, cell_center_x, cell_center_y
            )
            
            # Color based on utility type (unchanged)
            color = self._get_agent_color(agent)
            
            # Draw agent circle
            pygame.draw.circle(self.screen, color, (px, py), radius)
            pygame.draw.circle(
                self.screen, self.COLOR_BLACK, (px, py), radius, 
                max(1, radius // 5)
            )
            
            # Draw agent ID (if space permits)
            if radius >= 5 and self.cell_size >= 15:
                id_label = self.small_font.render(str(agent.id), True, self.COLOR_BLACK)
                id_rect = id_label.get_rect(center=(px, py))
                self.screen.blit(id_label, id_rect)
        
        # Draw inventory labels BELOW the entire group (avoid overlap)
        if self.cell_size >= 20:
            self._draw_group_inventory_labels(
                agents, screen_x, screen_y, agent_count
            )

def _get_agent_color(self, agent: 'Agent') -> tuple[int, int, int]:
    """Extract agent color based on utility type."""
    if agent.utility:
        utility_type = agent.utility.__class__.__name__
        if utility_type == "UCES":
            return self.COLOR_GREEN
        elif utility_type == "ULinear":
            return self.COLOR_PURPLE
        else:
            return self.COLOR_YELLOW
    return self.COLOR_BLACK

def _draw_group_inventory_labels(
    self, 
    agents: list['Agent'],
    screen_x: int,
    screen_y: int,
    agent_count: int
):
    """
    Draw inventory labels for a group of co-located agents.
    
    Strategy:
    - 1 agent: Label below agent (current behavior)
    - 2-3 agents: Stack labels vertically below cell
    - 4+ agents: Show "N agents" summary instead of individual inventories
    """
    has_money = (
        any(a.inventory.M > 0 for a in agents) or 
        self.sim.params.get('exchange_regime') in ('money_only', 'mixed')
    )
    
    cell_center_x = screen_x + self.cell_size // 2
    cell_bottom_y = screen_y + self.cell_size
    
    if agent_count == 1:
        # Single agent - draw inventory below (current behavior)
        agent = agents[0]
        if has_money:
            inv_text = f"A:{agent.inventory.A} B:{agent.inventory.B} M:{agent.inventory.M}"
        else:
            inv_text = f"A:{agent.inventory.A} B:{agent.inventory.B}"
        
        inv_label = self.small_font.render(inv_text, True, self.COLOR_BLACK)
        inv_width = inv_label.get_width()
        self.screen.blit(inv_label, (cell_center_x - inv_width // 2, cell_bottom_y + 2))
    
    elif agent_count <= 3:
        # 2-3 agents - stack labels vertically
        for idx, agent in enumerate(agents):
            if has_money:
                inv_text = f"[{agent.id}] A:{agent.inventory.A} B:{agent.inventory.B} M:{agent.inventory.M}"
            else:
                inv_text = f"[{agent.id}] A:{agent.inventory.A} B:{agent.inventory.B}"
            
            inv_label = self.small_font.render(inv_text, True, self.COLOR_BLACK)
            inv_width = inv_label.get_width()
            y_offset = cell_bottom_y + 2 + (idx * 12)  # 12px spacing between labels
            self.screen.blit(inv_label, (cell_center_x - inv_width // 2, y_offset))
    
    else:
        # 4+ agents - show summary only
        summary_text = f"{agent_count} agents at ({agents[0].pos[0]}, {agents[0].pos[1]})"
        summary_label = self.small_font.render(summary_text, True, self.COLOR_BLACK)
        summary_width = summary_label.get_width()
        self.screen.blit(summary_label, (cell_center_x - summary_width // 2, cell_bottom_y + 2))
```

---

## Visual Examples

### Example: 3 Agents Trading on Same Cell

**Simulation State** (unchanged):
```python
agent_1.pos = (5, 5)
agent_2.pos = (5, 5)  # Co-located after trade
agent_3.pos = (5, 5)  # Also at same position
```

**Current Rendering** (before fix):
```
┌─────────────┐
│             │
│      ●      │  All 3 agents drawn at exact same (px, py)
│             │  Only top agent visible
│             │  Labels completely overlap
└─────────────┘
```

**Proposed Rendering** (after fix):
```
┌─────────────┐
│      ●₁     │  Agent 1 (ID visible inside)
│             │  
│   ●₂    ●₃  │  Agents 2 & 3 (triangle pattern)
│             │  
└─────────────┘
[1] A:5 B:3 M:10
[2] A:2 B:8 M:5
[3] A:4 B:4 M:12
```

All agents clearly visible with distinct positions and readable labels.

---

## Advantages Over Simulation-Layer Solution

| Aspect | Renderer-Only | Simulation Modification |
|--------|---------------|-------------------------|
| **Simulation Logic** | Zero changes | New system in Phase 7 |
| **Determinism Risk** | None | Must ensure sorting, tie-breaking |
| **Backward Compatibility** | Automatic | Requires opt-in flag |
| **Testing Burden** | Minimal (visual only) | Full unit + integration tests |
| **Performance** | O(N) once per frame | O(N) every tick |
| **Code Complexity** | ~150 LOC in renderer | ~200 LOC + schema + telemetry |
| **Conceptual Purity** | Clean separation of concerns | Mixes visualization with economics |
| **Semantic Accuracy** | Positions remain truthful | Positions become "adjusted truth" |
| **Educational Value** | Clear that co-location occurred | May confuse students about interaction rules |

---

## Edge Cases & Handling

### Edge Case 1: Very Small Cell Size (cell_size < 10px)

**Problem**: Agents become too small to render distinctly.

**Solution**:
```python
def calculate_agent_radius(cell_size: int, agent_count: int) -> int:
    # Enforce absolute minimum radius of 2px
    if agent_count == 1:
        return max(2, cell_size // 3)
    else:
        return max(2, cell_size // (agent_count + 2))
```

With 2px minimum, even tiny cells show something visible.

### Edge Case 2: Large Agent Counts (10+ agents on one cell)

**Problem**: Too many agents to fit legibly in one cell.

**Solution**: Use circle-pack layout and summary label:
```
┌─────────────┐
│  ●●●●●●●    │  10 tiny agents in circular pattern
│  ●  ?  ●    │  "?" indicates "check label for details"
│  ●●●●●●●    │
└─────────────┘
"10 agents at (5, 5)"
```

Users can inspect telemetry or logs for detailed agent info.

### Edge Case 3: Label Overflow (labels extend beyond screen)

**Problem**: Stacked labels for 3 agents may extend off bottom of screen.

**Solution**: Clip labels to viewport or show abbreviated versions:
```python
if y_offset + label_height > self.height:
    # Truncate label list or use summary
    break
```

### Edge Case 4: Agent IDs Too Large to Fit in Small Circles

**Problem**: 3-digit agent IDs don't fit in radius=3px circles.

**Solution**: Only render ID if `radius >= 5`:
```python
if radius >= 5 and self.cell_size >= 15:
    id_label = self.small_font.render(str(agent.id), True, self.COLOR_BLACK)
    # ...
```

For tiny agents, users rely on color-coding and hover tooltips (future enhancement).

---

## Performance Analysis

### Current Implementation (Before)
```python
for agent in self.sim.agents:  # O(N)
    # Draw one agent
```
**Complexity**: O(N)

### Proposed Implementation (After)
```python
# Group agents by position
position_groups = {}
for agent in self.sim.agents:  # O(N)
    position_groups[agent.pos].append(agent)

# Draw groups
for pos, agents in position_groups.items():  # O(P) where P = unique positions
    for agent in agents:  # O(A) where A = agents at this position
        # Draw one agent
```
**Complexity**: Still O(N) total (N agents drawn exactly once)

**Additional Overhead**:
- Dictionary creation: O(N)
- Sorting within groups: O(N log N) worst case if all agents co-located (unlikely)
- Trigonometric calculations: O(N) but only for groups with 3+ agents

**Real-World Impact**: Negligible. The bottleneck is Pygame rendering, not position calculations.

### Benchmark Comparison

Expected performance (compared to current renderer):
- **1 agent per cell**: Identical performance (no grouping needed)
- **2-4 agents per cell**: <5% overhead (simple offset calculations)
- **5+ agents per cell**: <10% overhead (trig functions for circle pack)

Since co-location is typically rare (most agents are spread across grid), average case is ~1-2% overhead.

---

## Testing Strategy

### Visual Regression Tests

Create test scenarios to validate rendering:

1. **`scenarios/test_colocation_2agents.yaml`**:
   - 2 agents at (5, 5)
   - Verify diagonal positioning in screenshot
   
2. **`scenarios/test_colocation_4agents.yaml`**:
   - 4 agents at (10, 10)
   - Verify corner positioning
   
3. **`scenarios/test_colocation_many.yaml`**:
   - 8 agents at (3, 3)
   - Verify circle pack layout

### Manual Testing Checklist

- [ ] Load `three_agent_barter.yaml`, pause simulation, verify agents visible
- [ ] Run simulation until trade occurs, verify trading agents separate visually
- [ ] Test with small cell_size (10px) - agents still visible?
- [ ] Test with large cell_size (50px) - layouts look good?
- [ ] Verify inventory labels don't overlap
- [ ] Check that agent IDs render correctly inside circles
- [ ] Test with 10+ agents on one cell - summary label appears?
- [ ] Verify deterministic rendering (same seed = same visual layout)

### Unit Tests (Optional)

While primarily visual, we can test the math:

```python
# tests/test_renderer_positions.py

def test_single_agent_position():
    """Single agent renders at cell center."""
    renderer = MockRenderer(cell_size=30)
    px, py = renderer.calculate_agent_display_position(0, 1, 15, 15)
    assert px == 15 and py == 15

def test_two_agents_diagonal():
    """Two agents render in opposite corners."""
    renderer = MockRenderer(cell_size=20)
    px1, py1 = renderer.calculate_agent_display_position(0, 2, 10, 10)
    px2, py2 = renderer.calculate_agent_display_position(1, 2, 10, 10)
    assert px1 < 10 and py1 < 10  # Upper-left
    assert px2 > 10 and py2 > 10  # Lower-right

def test_radius_scaling():
    """Radius scales down with agent count."""
    renderer = MockRenderer(cell_size=30)
    r1 = renderer.calculate_agent_radius(30, 1)
    r2 = renderer.calculate_agent_radius(30, 2)
    r4 = renderer.calculate_agent_radius(30, 4)
    assert r1 > r2 > r4  # Decreasing radius
    assert r4 >= 3  # Minimum radius enforced
```

---

## Implementation Checklist

- [ ] Add `import math` to renderer.py
- [ ] Implement `group_agents_by_position()` method
- [ ] Implement `calculate_agent_radius()` method
- [ ] Implement `calculate_agent_display_position()` method
- [ ] Refactor `draw_agents()` to use group-based rendering
- [ ] Extract `_get_agent_color()` helper method
- [ ] Implement `_draw_group_inventory_labels()` method
- [ ] Test with existing scenarios (verify no visual regressions)
- [ ] Create test scenario with intentional co-location
- [ ] Manual visual verification in launcher
- [ ] Update documentation (add note about co-location rendering)
- [ ] Optional: Add configuration flag `renderer.smart_colocation_display` (default True)

**Estimated LOC**: ~150 lines (mostly in renderer.py, no other files touched)

---

## Future Enhancements (Post-MVP)

### Enhancement 1: Hover Tooltips
When mouse hovers over co-located group, show popup with all agent details:
```
┌─────────────────────────┐
│ 3 Agents at (5, 5)      │
├─────────────────────────┤
│ Agent 1: A:5 B:3 M:10   │
│ Agent 2: A:2 B:8 M:5    │
│ Agent 3: A:4 B:4 M:12   │
└─────────────────────────┘
```

### Enhancement 2: Visual Trade Indicators
Draw connecting lines between recently traded agents:
```
   ●₁ ←──trade──→ ●₂
```

### Enhancement 3: Configurable Layouts
Allow users to choose layout strategy in UI:
- Classic (current behavior - overlap)
- Smart (proposed - auto-arrange)
- Minimal (just scale, no offset)

### Enhancement 4: Animation
Smoothly interpolate agent positions when they co-locate:
```
Tick N:   ●₁        ●₂     (separate)
          ↓          ↓
Tick N+1: ●₁  ●₂           (sliding into position)
```

---

## Open Questions for Discussion

### Question 1: Should This Be Opt-In or Default Behavior?

**Option A (Recommended)**: Default enabled, can disable with config flag
```python
self.smart_colocation = sim.config.get('renderer_smart_colocation', True)
```

**Option B**: Always enabled (no flag)

**Option C**: Opt-in only (default disabled)

**Recommendation**: Default enabled. This is strictly better UX with no downsides.

### Question 2: What About Very Large Grids with Tiny Cells?

When `cell_size < 10px`, even smart layouts are hard to see. Should we:
- **Option A**: Keep trying (2px minimum radius)
- **Option B**: Fall back to classic overlap (accept that tiny grids are hard to read)
- **Option C**: Show warning in HUD: "Zoom in for better visibility"

**Recommendation**: Option A with optional HUD hint.

### Question 3: Inventory Labels for 4+ Agents?

Current proposal shows summary label only. Alternatives:
- **Option A**: Show all labels stacked (may overflow screen)
- **Option B**: Show first 3 + "...N more" indicator
- **Option C**: Truncate to summary (current proposal)

**Recommendation**: Option B with tooltip enhancement later.

### Question 4: Should Agent Rendering Order Be Deterministic?

Currently, agents are sorted by ID before rendering within a group. This ensures:
- Agent 1 always gets first position in layout
- Screenshots are reproducible

Alternative: Random order for visual variety?

**Recommendation**: Keep deterministic (ID-sorted) for reproducibility and debugging.

---

## Comparison with Original Proposal

| Aspect | Simulation Micro-Nudge | Renderer-Only (This) |
|--------|----------------------|----------------------|
| Complexity | High | Medium |
| Risk | Medium | Low |
| Testability | Full test suite needed | Visual verification |
| User Confusion | Moderate (positions change) | None (positions truthful) |
| Backward Compat | Requires opt-in flag | Automatic |
| Performance | O(N) per tick | O(N) per frame |
| Educational Clarity | Positions adjusted | Positions accurate |
| **Overall Score** | 6/10 | 9/10 |

---

## Recommendation

**Implement the renderer-only solution.**

This approach:
- ✅ Solves the visual clarity problem completely
- ✅ Zero risk to simulation logic or determinism
- ✅ No backward compatibility concerns
- ✅ Minimal code changes (~150 LOC in one file)
- ✅ Clean separation of concerns (visualization ≠ simulation)
- ✅ Educationally honest (positions remain truthful)
- ✅ Extensible for future enhancements (tooltips, animations)

The only trade-off is that this is a **presentation-layer solution**, meaning:
- Agent positions in telemetry database remain co-located (truthful)
- Programmatic analysis sees true positions (not adjusted)
- Visual representation diverges from raw data (intentionally, for clarity)

This is the **right** trade-off for an educational/research visualization tool.

---

**Next Steps**: Review this proposal, confirm approach, then implement the refactored `draw_agents()` method with smart co-location handling.
