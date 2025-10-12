# GUI Launcher User Guide

## Overview

The VMT GUI Launcher provides an intuitive interface for running simulations and creating custom scenarios without editing YAML files directly.

## Installation

Make sure PyQt5 is installed:

```bash
pip install -r requirements.txt
```

## Launching the GUI

```bash
python launcher.py
```

## Main Launcher Window

### Components

1. **Create Custom Scenario Button** - Opens the scenario builder dialog
2. **Scenario List** - Shows all `.yaml` files in `scenarios/` folder
3. **Seed Input** - Enter an integer seed (default: 42)
4. **Run Simulation Button** - Launches the selected scenario
5. **Status Label** - Shows current selection and status

### Running a Simulation

1. Select a scenario from the list (click on it)
2. Enter a seed number (any integer)
3. Click "Run Simulation"
4. The Pygame visualization window will open
5. The launcher remains open for running additional simulations

### Auto-Refresh

The scenario list automatically refreshes when:
- New scenarios are created through the builder
- Files are saved to the `scenarios/` folder

## Scenario Builder

### Opening the Builder

Click "Create Custom Scenario" in the main launcher window.

### Tabs

#### Tab 1: Basic Settings

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| Scenario Name | Text | Name for your scenario | Required |
| Grid Size (N) | Integer | Creates NxN grid | 20 |
| Number of Agents | Integer | How many agents | 3 |
| Initial Inventory A | Int or List | Starting A (e.g., "10" or "8,4,6") | 10 |
| Initial Inventory B | Int or List | Starting B (e.g., "10" or "4,8,6") | 10 |

**Inventory Tips:**
- Single value: All agents get same amount
- List: Each agent gets specific amount (must match agent count)
- Use commas to separate values: `8,4,6`

#### Tab 2: Simulation Parameters

| Parameter | Range | Description | Default |
|-----------|-------|-------------|---------|
| Spread | 0.0 - 1.0 | Bid-ask spread | 0.1 |
| Vision Radius | 0 - 50 | How far agents see | 5 |
| Interaction Radius | 0 - 50 | Range for trading | 2 |
| Move Budget Per Tick | 1 - 20 | Steps per tick | 1 |
| ΔA_max | 1 - 100 | Max trade size | 5 |
| Forage Rate | 1 - 20 | Harvest per tick | 1 |
| Epsilon | Float | Precision (scientific notation OK) | 1e-12 |
| Beta | 0.01 - 1.0 | Distance discount factor | 0.95 |
| Trade Cooldown Ticks | 0 - 100 | Failed trade cooldown | 5 |

**Parameter Tips:**
- Vision Radius should be ≥ Interaction Radius
- Higher beta = less distance penalty for foraging
- Trade cooldown prevents infinite failed retries

#### Tab 3: Resources

| Field | Range | Description | Default |
|-------|-------|-------------|---------|
| Resource Density | 0.0 - 1.0 | Fraction of cells with resources | 0.1 |
| Resource Amount | 1 - 100 | Initial amount per cell | 10 |
| Resource Growth Rate | 0 - 20 | Units regenerated per tick (0=off) | 1 |
| Resource Max Amount | 1 - 100 | Maximum per cell | 10 |
| Resource Regen Cooldown | 0 - 100 | Ticks before regeneration | 5 |

**Resource Tips:**
- Density slider provides visual feedback
- Growth rate 0 disables regeneration
- Cooldown starts after last harvest

#### Tab 4: Utility Functions

Agents' preferences are defined by utility functions. You can mix multiple types.

**Table Columns:**
1. **Type**: `ces` or `linear`
2. **Weight**: Fraction of agents with this utility (must sum to 1.0)
3. **Param 1**: For CES=rho, for Linear=vA
4. **Param 2**: For CES=wA, for Linear=vB
5. **Param 3**: For CES=wB, for Linear=unused

**Buttons:**
- **Add Utility**: Add a new row
- **Remove Selected**: Remove selected row
- **Auto-normalize weights**: Automatically adjust weights to sum to 1.0

### CES Utility Parameters

```
U = [wA * A^ρ + wB * B^ρ]^(1/ρ)
```

| Parameter | Description | Constraints |
|-----------|-------------|-------------|
| rho (ρ) | Elasticity of substitution | ρ ≠ 1.0 |
| wA | Weight for good A | > 0 |
| wB | Weight for good B | > 0 |

**Rho Values:**
- **ρ → 0**: Cobb-Douglas (balanced preferences)
- **ρ < 0**: Complements (prefer balanced bundles)
- **ρ > 0**: Substitutes (flexible trade-offs)
- **ρ = 0.5**: Common choice for demos

### Linear Utility Parameters

```
U = vA * A + vB * B
```

| Parameter | Description | Constraints |
|-----------|-------------|-------------|
| vA | Value of good A | > 0 |
| vB | Value of good B | > 0 |

**MRS:** Constant at vA/vB (perfect substitutes)

### Utility Mix Examples

**Example 1: Complementary Preferences**
```
Agent Type 1 (50%): CES with ρ=0.5, wA=2.0, wB=1.0  (prefers A)
Agent Type 2 (50%): CES with ρ=0.5, wA=1.0, wB=2.0  (prefers B)
```
Creates incentive for trade!

**Example 2: Mixed Types**
```
Agent Type 1 (40%): CES with ρ=0.0, wA=1.0, wB=1.0  (Cobb-Douglas)
Agent Type 2 (30%): Linear with vA=2.0, vB=1.0      (prefers A)
Agent Type 3 (30%): Linear with vA=1.0, vB=2.0      (prefers B)
```

### Validation

The builder validates inputs when you click "Generate Scenario":

- All required fields filled
- Values in valid ranges
- Utility weights sum to 1.0
- CES rho ≠ 1.0
- All utility parameters positive

If validation fails:
- Error dialog shows what's wrong
- Builder stays open for corrections
- Fix the issue and try again

### Saving

1. Click "Generate Scenario"
2. File dialog opens
3. Choose location (default: `scenarios/` folder)
4. Enter filename (auto-adds `.yaml` extension)
5. Click Save
6. Success message confirms

**Auto-Selection:**
If saved to `scenarios/` folder, the new scenario automatically:
- Appears in launcher list
- Gets selected for you
- Ready to run!

## Tips and Best Practices

### Good Scenario Design

1. **Start Simple**: 3-5 agents, small grid (20x20)
2. **Complementary Preferences**: Use different wA/wB ratios
3. **Adequate Resources**: Density 0.1-0.3 provides scarcity
4. **Reasonable Vision**: 5-10 for most scenarios
5. **Trade Cooldown**: 5-10 ticks prevents spam

### Testing Scenarios

1. **Quick Test**: Run with seed 42 for 50 ticks
2. **Check Logs**: Look in `logs/` folder
3. **Trade Activity**: Should see trades in `trades.csv`
4. **Adjust Parameters**: Iterate based on results

### Common Issues

**No Trades Happening:**
- Check utility preferences (need complementary types)
- Increase vision/interaction radius
- Reduce grid size to bring agents closer
- Check ΔA_max is reasonable

**Agents Not Moving:**
- Check move_budget_per_tick > 0
- Verify resources exist (density > 0)
- Check forage_rate > 0

**Performance Issues:**
- Reduce agent count
- Reduce grid size
- Lower tick rate in Pygame window

## Workflow Examples

### Example 1: Quick Educational Demo

1. Launch `python launcher.py`
2. Click "Create Custom Scenario"
3. Basic Settings:
   - Name: "classroom_demo"
   - Grid: 20, Agents: 3
   - Inventory: "10" for both
4. Use defaults for other tabs
5. Utilities: Keep default CES
6. Generate and save to `scenarios/`
7. Run with seed 42

### Example 2: Research Experiment

1. Create base scenario with GUI
2. Save as `experiment_base.yaml`
3. Create variations by:
   - Loading in GUI (future feature)
   - Or manually edit saved YAML
4. Run multiple seeds: 1, 2, 3, etc.
5. Analyze logs with pandas

### Example 3: Testing Utility Types

1. Create scenario with 50/50 CES/Linear mix
2. Run and observe trade patterns
3. Check `trade_attempts.csv` for surplus data
4. Adjust utility weights
5. Re-run and compare

## Keyboard Shortcuts

### Launcher Window
- **Enter**: Run selected simulation
- **Escape**: Close window

### Scenario Builder
- **Tab**: Navigate between fields
- **Enter**: Accept/Generate (when valid)
- **Escape**: Cancel

## File Locations

### Scenarios
- Default location: `scenarios/`
- Can save anywhere with file dialog
- Only `scenarios/*.yaml` appear in launcher

### Logs
- Output: `logs/` folder
- `trades.csv`: All successful trades
- `trade_attempts.csv`: All attempts (including failures)
- `decisions.csv`: Agent decision-making
- `agent_snapshots.csv`: State over time
- `resource_snapshots.csv`: Resource levels

## Troubleshooting

### GUI Won't Launch

```bash
# Check PyQt5 installed
pip list | grep PyQt5

# Reinstall if needed
pip install --force-reinstall PyQt5
```

### Import Errors

```bash
# Ensure in correct directory
cd /path/to/vmt-dev

# Activate venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Simulation Won't Start

- Check scenario file is valid YAML
- Try loading directly: `python main.py scenarios/your_scenario.yaml 42`
- Check terminal for error messages

### Scenario Builder Issues

- **Weights Don't Sum to 1.0**: Enable "Auto-normalize weights"
- **Invalid rho**: Can't use exactly 1.0 for CES
- **Empty Fields**: All required fields must be filled

## Advanced Usage

### Command Line Alternative

You can still use CLI directly:

```bash
python main.py scenarios/custom_scenario.yaml 123
```

### Programmatic Access

```python
from vmt_launcher.scenario_builder import ScenarioBuilderDialog
from vmt_launcher.validator import ScenarioValidator

# Use validator in your own scripts
validator = ScenarioValidator()
data = validator.validate_positive_int("5", "test_field")
```

### Batch Processing

Create multiple scenarios programmatically:

```python
import yaml

template = {
    'schema_version': 1,
    'name': 'batch_scenario',
    # ... rest of scenario
}

for i in range(10):
    template['name'] = f'scenario_{i}'
    with open(f'scenarios/scenario_{i}.yaml', 'w') as f:
        yaml.dump(template, f, default_flow_style=False)
```

## Future Enhancements

Planned features:
- Load existing scenario for editing
- Scenario templates library
- Preview scenario before saving
- Recent scenarios list
- Parameter tooltips with examples
- Validation preview as you type

## Getting Help

- Check README.md for overview
- See PLANS/ folder for detailed docs
- Run tests: `pytest tests/ -v`
- Check logs for diagnostics

## Summary

The GUI launcher makes VMT accessible to users who:
- Don't want to edit YAML manually
- Want to quickly test different parameters
- Need a visual interface for teaching
- Prefer form-based input

Both GUI and CLI remain fully supported!

