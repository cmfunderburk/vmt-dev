# VMT Tools

Developer utilities for the VMT simulation project.

## Scenario Generator

Generate random but valid scenario YAML files for testing and experimentation.

### Quick Start

```bash
python3 -m src.vmt_tools.generate_scenario my_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear --resources 0.3,5,1 --seed 42
```

This creates `scenarios/my_test.yaml` with:
- 20 agents on a 30×30 grid
- Random inventories in [10, 50]
- 50% CES agents, 50% Linear agents
- Resources: 30% density, max amount 5, regen rate 1
- Deterministic generation (seed=42)

### Presets (Phase 2)

Presets provide pre-configured templates for common use cases:

| Preset | Agents | Grid | Utilities | Regime | Use Case |
|--------|--------|------|-----------|--------|----------|
| `minimal` | 10 | 20×20 | ces, linear | barter_only | Quick testing |
| `standard` | 30 | 40×40 | All 5 types | barter_only | Default demo |
| `large` | 80 | 80×80 | ces, linear | barter_only | Performance testing |
| `money_demo` | 20 | 30×30 | linear | money_only | Money showcase |
| `mixed_economy` | 40 | 50×50 | ces, linear, quad | mixed | Hybrid economy |

**Use presets:**
```bash
python3 -m src.vmt_tools.generate_scenario demo --preset money_demo --seed 42
```

**Override preset values:**
```bash
# Use money_demo but with 50 agents instead of 20
python3 -m src.vmt_tools.generate_scenario large_demo \
  --preset money_demo --agents 50 --seed 42
```

### Exchange Regimes (Phase 2)

Control which types of exchanges are allowed:

- `barter_only` - Only A↔B trades (default, backward compatible)
- `money_only` - Only A↔M and B↔M trades (goods for money)
- `mixed` - All exchange types allowed (A↔B, A↔M, B↔M)
- `mixed_liquidity_gated` - Mixed with liquidity requirements (future)

**Money-only economy:**
```bash
python3 -m src.vmt_tools.generate_scenario money_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities linear --resources 0.2,5,1 \
  --exchange-regime money_only --seed 42
```

**Mixed economy:**
```bash
python3 -m src.vmt_tools.generate_scenario hybrid_test \
  --agents 30 --grid 40 --inventory-range 15,60 \
  --utilities ces,linear --resources 0.35,6,2 \
  --exchange-regime mixed --seed 42
```

### Supported Utility Types

- `ces` - Constant Elasticity of Substitution
- `linear` - Perfect Substitutes
- `quadratic` - Bliss Points
- `translog` - Transcendental Logarithmic
- `stone_geary` - Subsistence Constraints (gamma=0 by default)

### Usage Examples

**Single utility type:**
```bash
python3 -m src.vmt_tools.generate_scenario ces_only \
  --agents 30 --grid 40 --inventory-range 15,60 \
  --utilities ces --resources 0.35,6,2
```

**Multiple utility types (equal weights):**
```bash
python3 -m src.vmt_tools.generate_scenario mixed \
  --agents 50 --grid 50 --inventory-range 20,80 \
  --utilities ces,linear,quadratic,translog,stone_geary \
  --resources 0.4,8,3
```

**With reproducible seed:**
```bash
python3 -m src.vmt_tools.generate_scenario reproducible \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear --resources 0.3,5,1 --seed 42
```

**Custom output path:**
```bash
python3 -m src.vmt_tools.generate_scenario my_test \
  --agents 10 --grid 20 --inventory-range 10,50 \
  --utilities ces --resources 0.3,5,1 \
  --output tests/fixtures/my_test.yaml
```

### Parameter Ranges

All utility parameters are generated within conservative ranges that ensure valid, well-behaved utility functions. See the main planning document for details on parameter ranges.

### Constraints

- Inventory range: MIN must be >= 1 (required for log-based utilities)
- Inventory range: MAX must be > MIN
- Grid size: Must be positive integer
- Agents: Must be positive integer
- Resource density: Must be in [0.0, 1.0]
- Exchange regime: Must be one of: barter_only, money_only, mixed, mixed_liquidity_gated

### Programmatic API

```python
from src.vmt_tools import generate_scenario
from src.vmt_tools.param_strategies import get_preset
import random

# Set seed for reproducibility
random.seed(42)

# Generate scenario (Phase 2: with exchange regime)
scenario = generate_scenario(
    name="my_scenario",
    n_agents=20,
    grid_size=30,
    inventory_range=(10, 50),
    utilities=["ces", "linear"],
    resource_config=(0.3, 5, 1),
    exchange_regime="mixed"  # Phase 2: specify regime
)

# Or use a preset
preset = get_preset("money_demo")
scenario = generate_scenario(
    name="demo",
    n_agents=preset['agents'],
    grid_size=preset['grid'],
    inventory_range=preset['inventory_range'],
    utilities=preset['utilities'],
    resource_config=preset['resource_config'],
    exchange_regime=preset['exchange_regime']
)

# scenario is a dict ready for YAML serialization
import yaml
with open("scenarios/my_scenario.yaml", "w") as f:
    yaml.dump(scenario, f, default_flow_style=False, sort_keys=False)
```

## Development

### Project Structure

```
src/vmt_tools/
├── __init__.py              # Package exports
├── generate_scenario.py     # CLI entry point
├── scenario_builder.py      # Core scenario generation
├── param_strategies.py      # Parameter randomization
└── README.md               # This file
```

### Testing

Generate test scenarios:
```bash
# Generate one scenario for each utility type
for util in ces linear quadratic translog stone_geary; do
  python3 -m src.vmt_tools.generate_scenario "test_${util}" \
    --agents 10 --grid 20 --inventory-range 10,50 \
    --utilities $util --resources 0.3,5,1 --seed 42
done
```

Validate generated scenarios:
```python
from src.scenarios.loader import load_scenario

scenario = load_scenario("scenarios/test_ces.yaml")
# Raises exception if invalid
```

## Phase 2 Features (Completed)

✅ **Exchange Regime Support** - Generate scenarios with barter, money, or mixed economies  
✅ **Preset System** - 5 presets for common use cases  
✅ **Automatic Money Generation** - M inventories auto-generated for money regimes  
✅ **Preset Overrides** - Explicit flags override preset values  

## Future Enhancements (Phase 3+)

- Weighted utility mixes (e.g., `--utilities ces:0.5,linear:0.5`)
- Custom money inventory ranges (`--money-range 100,500`)
- Money parameter overrides (`--lambda-money 2.0`)
- Parameter validation (`--validate` flag)
- Simulation parameter overrides (`--vision 10`, `--movement 2`)

See [scenario_generator_phase2_plan.md](../../../docs/implementation/scenario_generator_phase2_plan.md) for details.

