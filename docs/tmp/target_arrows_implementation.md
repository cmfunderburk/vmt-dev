# Target Arrows Phase 1: Implementation Summary

**Date:** 2025-10-20  
**Status:** ✅ Complete

## Overview

Implemented target arrow visualization to show agent movement intentions in the Pygame renderer. Arrows are color-coded by target type (trade/forage) and can be toggled on/off with keyboard controls. Idle agents (no target) are highlighted with red borders when arrows are enabled.

## Features Implemented

### 1. Arrow Visualization
- **Green arrows:** Trade targets (agent pursuing another agent)
- **Orange arrows:** Forage targets (agent pursuing resources)
- **Red borders:** Idle agents (no target)

### 2. Toggle Controls
- **T key:** Toggle trade arrows on/off
- **F key:** Toggle forage arrows on/off
- **A key:** Turn all arrows on
- **O key:** Turn all arrows off

### 3. HUD Display
- Real-time status showing which arrow types are enabled
- Displays: "Arrows: OFF", "Arrows: Trade", "Arrows: Forage", or "Arrows: Trade+Forage"

## Files Modified

### `src/vmt_pygame/renderer.py`
- Added toggle state variables: `show_trade_arrows`, `show_forage_arrows`
- Added color constants: `COLOR_ARROW_TRADE`, `COLOR_ARROW_FORAGE`, `COLOR_IDLE_BORDER`
- Implemented `draw_arrow()`: Draws arrow with arrowhead from start to end position
- Implemented `draw_target_arrows()`: Main arrow rendering logic with viewport culling
- Implemented `draw_idle_agent_borders()`: Draws red borders around idle agents
- Updated `render()`: Added call to `draw_target_arrows()`
- Updated `draw_hud()`: Added arrow status display

### `main.py`
- Added keyboard event handlers for T, F, A, O keys
- Updated help text to include arrow controls
- Added console output for arrow toggle state changes

## Technical Details

### Arrow Rendering Algorithm
1. Check if any arrow types are enabled (early exit if disabled)
2. Iterate through all agents
3. For agents with targets:
   - Determine if target is trade (has `target_agent_id`) or forage
   - Skip if that arrow type is disabled
   - Convert grid coordinates to screen coordinates
   - Apply viewport culling (only draw visible arrows)
   - Draw arrow from agent center to target center
4. Track idle agents (no `target_pos`)
5. Draw red borders around idle agents

### Idle Agent Border Rendering
- Groups idle agents by position (handles co-location)
- Uses same positioning logic as `draw_agents()` for consistency
- Border width scales with agent size: `max(2, radius // 3)`
- Border drawn as thick circle outline around agent

### Performance Optimizations
- **Viewport culling:** Only render arrows for visible agents
- **Early exit:** Skip all rendering if arrows disabled
- **Efficient grouping:** Idle agents grouped by position to minimize iterations

## Testing

### Validation Results
- ✅ All 169 tests passed
- ✅ Trade arrows work correctly (three_agent_barter scenario)
- ✅ Forage arrows work correctly (single_agent_forage scenario)
- ✅ Idle agent detection works correctly
- ✅ Toggle controls work as expected
- ✅ HUD updates correctly
- ✅ No linter errors

### Test Scenarios
1. **three_agent_barter.yaml:** All agents show green trade arrows
2. **single_agent_forage.yaml:** Agent shows orange forage arrows
3. **Mixed scenarios:** Correctly distinguishes trade vs forage targets

## Usage

### Running the Visualization
```bash
python main.py scenarios/three_agent_barter.yaml --seed 42
```

### Controls
- Press **T** to toggle trade arrows
- Press **F** to toggle forage arrows
- Press **A** to show all arrows
- Press **O** to hide all arrows

### HUD Status
Bottom-left corner shows current arrow state:
- "Arrows: OFF" - All arrows disabled
- "Arrows: Trade" - Only trade arrows enabled
- "Arrows: Forage" - Only forage arrows enabled
- "Arrows: Trade+Forage" - All arrows enabled

## Design Decisions

1. **Default state: OFF**
   - Cleaner initial view
   - User can enable arrows on-demand
   - Reduces visual clutter for presentations

2. **Independent toggles**
   - T and F toggle independently
   - A and O provide quick all-on/all-off
   - Flexible for analyzing specific behaviors

3. **Color choices**
   - Green: Trade (economic activity, growth)
   - Orange: Forage (resources, harvest)
   - Red: Idle (alert, inactive)

4. **Idle agent borders**
   - More visible than attempting to draw "no target" indicator
   - Works well with co-located agents
   - Scales appropriately with agent size

5. **Viewport culling**
   - Performance optimization for large grids
   - Only render visible arrows
   - Maintains smooth framerate

## Future Enhancements (Phase 2+)

Potential additions from the brainstorming doc:
- **Mutual targeting highlights:** Thicker/brighter arrows for mutual trade targets
- **Distance-based fading:** Fade distant arrows to reduce clutter
- **Curved arrows:** Reduce overlap when multiple agents target same position
- **Animation:** Dashed/moving patterns to show directionality
- **Target position markers:** Show competition/crowding for resources

## References

- Planning document: `docs/tmp/target_arrows_brainstorm.md`
- Renderer code: `src/vmt_pygame/renderer.py`
- Main loop: `main.py`
- Agent state: `src/vmt_engine/core/agent.py` (target_pos, target_agent_id)

