---
description: Scenario generation
alwaysApply: false
---
# VMT Scenario Generator - AI Agent Guide

## When to Use

Use the CLI scenario generator when you need to:
- Create test scenarios quickly
- Generate scenarios with random but valid parameters
- Create scenarios programmatically or in batch
- Avoid manual YAML editing for standard cases

**DO NOT use for:**
- Mode schedules (requires manual YAML editing)
- Advanced money parameters (Phase 3+)
- Scenarios with specific exact parameter values

## Current Status (Phase 1 - Complete)

### Basic Usage

```bash
python3 -m src.vmt_tools.generate_scenario NAME \
  --agents N --grid SIZE --inventory-range MIN,MAX \
  --utilities TYPE1,TYPE2,... --resources DENSITY,MAX,REGEN \
  [--seed SEED] [--output PATH]
```

### Supported Utility Types
- `ces` - Constant Elasticity of Substitution
- `linear` - Perfect Substitutes  
- `quadratic` - Bliss Points
- `translog` - Transcendental Logarithmic
- `stone_geary` - Subsistence Constraints (gamma=0 by default)

### Key Constraints
- `MIN` inventory must be >= 1 (required for log-based utilities)
- `MAX` inventory must be > `MIN`
- Utility weights automatically sum to 1.0
- All float parameters rounded to 2 decimals in YAML

### Examples

**Quick test scenario:**
```bash
python3 -m src.vmt_tools.generate_scenario quick_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear --resources 0.3,5,1 --seed 42
```

**All utility types:**
```bash
python3 -m src.vmt_tools.generate_scenario all_utils \
  --agents 30 --grid 40 --inventory-range 15,60 \
  --utilities ces,linear,quadratic,translog,stone_geary \
  --resources 0.35,6,2 --seed 42
```

**Reproducible generation:**
```bash
# Same seed produces identical output
python3 -m src.vmt_tools.generate_scenario test \
  --agents 10 --grid 20 --inventory-range 10,50 \
  --utilities ces --resources 0.3,5,1 --seed 42
```

## Phase 2 Features (Ready for Implementation)

**NOT YET IMPLEMENTED** - Coming soon:

### Exchange Regimes
```bash
# Will support (when Phase 2 is complete):
--exchange-regime {barter_only|money_only|mixed|mixed_liquidity_gated}
```

### Presets
```bash
# Will support (when Phase 2 is complete):
--preset {minimal|standard|large|money_demo|mixed_economy}
```

## Programmatic API

```python
from src.vmt_tools import generate_scenario
import random

random.seed(42)

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

## Parameter Ranges (Conservative Defaults)

All utility parameters use validated conservative ranges:

- **CES**: rho ∈ [-1.0, 1.0] excluding [0.8, 1.2]; wA ∈ [0.3, 0.7]
- **Linear**: vA, vB ∈ [0.5, 3.0]
- **Quadratic**: A_star ∈ [inv_min×1.2, inv_max×0.8]; sigma ∈ [star×0.4, star×0.8]; gamma ∈ [0, 0.2]
- **Translog**: alpha ∈ [0.4, 0.6]; beta_AA, beta_BB ∈ [-0.10, -0.02]; beta_AB ∈ [-0.03, 0.03]
- **Stone-Geary**: alpha ∈ [0.4, 0.6]; gamma_A, gamma_B = 0.0 (acts like Cobb-Douglas)

## Default Simulation Parameters

Generated scenarios use these defaults (can be manually edited in YAML):
- `spread: 0.0` - Zero bid-ask spread (reservation prices)
- `vision_radius: 8` - Moderate perception range
- `interaction_radius: 1` - Adjacent trading only
- `move_budget_per_tick: 1` - One step per tick
- `dA_max: 5` - Standard search range
- `forage_rate: 1` - One resource per tick
- `trade_cooldown_ticks: 3` - Standard cooldown
- `beta: 0.95` - Standard discount factor
- `exchange_regime: barter_only` - Default (Phase 1)

## Documentation

- **User Guide**: `src/vmt_tools/README.md`
- **Implementation Plan**: `docs/tmp/plans/scenario_generator_tool_plan.md`
- **Phase 1 Changelog**: `docs/tmp/plans/scenario_generator_phase1_changelog.md`
- **Phase 2 Plan**: `docs/tmp/plans/scenario_generator_phase2_implementation.md`

## Common Pitfalls

❌ **Don't use inventory_min < 1**
```bash
# WRONG - will fail
--inventory-range 0,50
```

✅ **Use inventory_min >= 1**
```bash
# CORRECT
--inventory-range 10,50
```

❌ **Don't forget resources are required**
```bash
# WRONG - missing --resources
python3 -m src.vmt_tools.generate_scenario test --agents 10 --grid 20
```

✅ **Always specify resources**
```bash
# CORRECT
python3 -m src.vmt_tools.generate_scenario test \
  --agents 10 --grid 20 --inventory-range 10,50 \
  --utilities ces --resources 0.3,5,1
```

## When to Edit YAML Manually

The generator is optimized for common cases. Edit YAML manually for:
- **Mode schedules** - Temporal cycling between forage/trade phases
- **Custom parameter values** - Specific utility parameter combinations
- **Distribution-based inventories** - `uniform_int` or custom distributions
- **Advanced money parameters** - `lambda_update_rate`, `lambda_bounds`, `liquidity_gate`
- **Overriding defaults** - Custom vision_radius, interaction_radius, etc.

## Future Features (Phase 3+)

Not yet implemented, may require Phase 3:
- Weighted utility mixes: `--utilities ces:0.6,linear:0.4`
- Custom money ranges: `--money-range 100,500`
- Parameter validation: `--validate` flag
- Batch generation: `--count 50`
- Parameter overrides: `--vision 10`, `--movement 2`

# VMT Scenario Generator - AI Agent Guide

## When to Use

Use the CLI scenario generator when you need to:
- Create test scenarios quickly
- Generate scenarios with random but valid parameters
- Create scenarios programmatically or in batch
- Avoid manual YAML editing for standard cases

**DO NOT use for:**
- Mode schedules (requires manual YAML editing)
- Advanced money parameters (Phase 3+)
- Scenarios with specific exact parameter values

## Current Status (Phase 1 - Complete)

### Basic Usage

```bash
python3 -m src.vmt_tools.generate_scenario NAME \
  --agents N --grid SIZE --inventory-range MIN,MAX \
  --utilities TYPE1,TYPE2,... --resources DENSITY,MAX,REGEN \
  [--seed SEED] [--output PATH]
```

### Supported Utility Types
- `ces` - Constant Elasticity of Substitution
- `linear` - Perfect Substitutes  
- `quadratic` - Bliss Points
- `translog` - Transcendental Logarithmic
- `stone_geary` - Subsistence Constraints (gamma=0 by default)

### Key Constraints
- `MIN` inventory must be >= 1 (required for log-based utilities)
- `MAX` inventory must be > `MIN`
- Utility weights automatically sum to 1.0
- All float parameters rounded to 2 decimals in YAML

### Examples

**Quick test scenario:**
```bash
python3 -m src.vmt_tools.generate_scenario quick_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear --resources 0.3,5,1 --seed 42
```

**All utility types:**
```bash
python3 -m src.vmt_tools.generate_scenario all_utils \
  --agents 30 --grid 40 --inventory-range 15,60 \
  --utilities ces,linear,quadratic,translog,stone_geary \
  --resources 0.35,6,2 --seed 42
```

**Reproducible generation:**
```bash
# Same seed produces identical output
python3 -m src.vmt_tools.generate_scenario test \
  --agents 10 --grid 20 --inventory-range 10,50 \
  --utilities ces --resources 0.3,5,1 --seed 42
```

## Phase 2 Features (Ready for Implementation)

**NOT YET IMPLEMENTED** - Coming soon:

### Exchange Regimes
```bash
# Will support (when Phase 2 is complete):
--exchange-regime {barter_only|money_only|mixed|mixed_liquidity_gated}
```

### Presets
```bash
# Will support (when Phase 2 is complete):
--preset {minimal|standard|large|money_demo|mixed_economy}
```

## Programmatic API

```python
from src.vmt_tools import generate_scenario
import random

random.seed(42)

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

## Parameter Ranges (Conservative Defaults)

All utility parameters use validated conservative ranges:

- **CES**: rho ∈ [-1.0, 1.0] excluding [0.8, 1.2]; wA ∈ [0.3, 0.7]
- **Linear**: vA, vB ∈ [0.5, 3.0]
- **Quadratic**: A_star ∈ [inv_min×1.2, inv_max×0.8]; sigma ∈ [star×0.4, star×0.8]; gamma ∈ [0, 0.2]
- **Translog**: alpha ∈ [0.4, 0.6]; beta_AA, beta_BB ∈ [-0.10, -0.02]; beta_AB ∈ [-0.03, 0.03]
- **Stone-Geary**: alpha ∈ [0.4, 0.6]; gamma_A, gamma_B = 0.0 (acts like Cobb-Douglas)

## Default Simulation Parameters

Generated scenarios use these defaults (can be manually edited in YAML):
- `spread: 0.0` - Zero bid-ask spread (reservation prices)
- `vision_radius: 8` - Moderate perception range
- `interaction_radius: 1` - Adjacent trading only
- `move_budget_per_tick: 1` - One step per tick
- `dA_max: 5` - Standard search range
- `forage_rate: 1` - One resource per tick
- `trade_cooldown_ticks: 3` - Standard cooldown
- `beta: 0.95` - Standard discount factor
- `exchange_regime: barter_only` - Default (Phase 1)

## Documentation

- **User Guide**: `src/vmt_tools/README.md`
- **Implementation Plan**: `docs/tmp/plans/scenario_generator_tool_plan.md`
- **Phase 1 Changelog**: `docs/tmp/plans/scenario_generator_phase1_changelog.md`
- **Phase 2 Plan**: `docs/tmp/plans/scenario_generator_phase2_implementation.md`

## Common Pitfalls

❌ **Don't use inventory_min < 1**
```bash
# WRONG - will fail
--inventory-range 0,50
```

✅ **Use inventory_min >= 1**
```bash
# CORRECT
--inventory-range 10,50
```

❌ **Don't forget resources are required**
```bash
# WRONG - missing --resources
python3 -m src.vmt_tools.generate_scenario test --agents 10 --grid 20
```

✅ **Always specify resources**
```bash
# CORRECT
python3 -m src.vmt_tools.generate_scenario test \
  --agents 10 --grid 20 --inventory-range 10,50 \
  --utilities ces --resources 0.3,5,1
```

## When to Edit YAML Manually

The generator is optimized for common cases. Edit YAML manually for:
- **Mode schedules** - Temporal cycling between forage/trade phases
- **Custom parameter values** - Specific utility parameter combinations
- **Distribution-based inventories** - `uniform_int` or custom distributions
- **Advanced money parameters** - `lambda_update_rate`, `lambda_bounds`, `liquidity_gate`
- **Overriding defaults** - Custom vision_radius, interaction_radius, etc.

## Future Features (Phase 3+)

Not yet implemented, may require Phase 3:
- Weighted utility mixes: `--utilities ces:0.6,linear:0.4`
- Custom money ranges: `--money-range 100,500`
- Parameter validation: `--validate` flag
- Batch generation: `--count 50`
- Parameter overrides: `--vision 10`, `--movement 2`

