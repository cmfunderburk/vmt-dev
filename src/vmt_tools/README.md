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
- Exchange regime: Phase 1 only supports `barter_only`

### Programmatic API

```python
from src.vmt_tools import generate_scenario
import random

# Set seed for reproducibility
random.seed(42)

# Generate scenario
scenario = generate_scenario(
    name="my_scenario",
    n_agents=20,
    grid_size=30,
    inventory_range=(10, 50),
    utilities=["ces", "linear"],
    resource_config=(0.3, 5, 1)
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

## Future Enhancements (Phase 2+)

- Weighted utility mixes (e.g., `--utilities ces:0.5,linear:0.5`)
- Money support and exchange regimes
- Parameter validation (`--validate` flag)
- Presets for common scenarios
- Simulation parameter overrides

See `docs/tmp/plans/scenario_generator_phase1_implementation.md` for full roadmap.

