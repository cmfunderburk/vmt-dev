# VMT Scenario Generator - Phase 2 Implementation Plan

**Date:** 2025-10-21  
**Status:** Planning  
**Phase:** Phase 2 - Exchange Regimes & Presets  
**Prerequisites:** Phase 1 Complete ✅  
**Estimated Time:** 1-2 days  
**Target:** Add exchange regime support and scenario presets while keeping CLI simple

---

## Overview

Phase 2 adds two essential features to the scenario generator:

1. **Exchange Regime Selection**: Support all 4 exchange regimes with automatic money inventory generation
2. **Scenario Presets**: Pre-configured templates for common use cases

**Design Philosophy**: Keep the CLI simple and focused. Defer advanced features (weighted utility mixes, parameter overrides, validation) to Phase 3+.

---

## Prerequisites & Dependencies

### VMT Money System Status

✅ **Phase 1 Complete**: Money infrastructure (schema, state, telemetry)  
✅ **Phase 2 Complete**: Monetary exchange implementation (money_only, mixed regimes)  
⏳ **Phase 3+**: Advanced money features (in progress)

**Available Exchange Regimes:**
- `barter_only` - Default (A↔B only)
- `money_only` - Phase 2 (A↔M, B↔M only)
- `mixed` - Phase 2 (A↔B, A↔M, B↔M all allowed)
- `mixed_liquidity_gated` - Phase 2 (monetary trades always, barter when thin market)

**Money Parameters Available:**
- `money_mode`: "quasilinear" (default) or "kkt_lambda"
- `money_scale`: Minor units scale (default: 1)
- `lambda_money`: Marginal utility of money (default: 1.0)
- Additional: `lambda_update_rate`, `lambda_bounds`, `liquidity_gate` (advanced)

---

## Success Criteria

Phase 2 is complete when:

1. ✅ CLI supports `--exchange-regime` flag with all 4 regimes
2. ✅ Money inventories (M) auto-generated when needed
3. ✅ Default money parameters set appropriately
4. ✅ At least 3 useful presets defined
5. ✅ Generated money scenarios load and run without errors
6. ✅ Documentation updated with Phase 2 examples
7. ✅ Backward compatibility: Phase 1 commands still work

---

## Feature 1: Exchange Regime Selection

### CLI Interface

**New optional flag:**
```bash
--exchange-regime {barter_only|money_only|mixed|mixed_liquidity_gated}
```

**Default**: `barter_only` (Phase 1 behavior, no breaking changes)

### Examples

```bash
# Phase 1 behavior (no change)
python3 -m src.vmt_tools.generate_scenario test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear --resources 0.3,5,1

# Money-only economy
python3 -m src.vmt_tools.generate_scenario money_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear --resources 0.3,5,1 \
  --exchange-regime money_only

# Mixed economy (barter + money)
python3 -m src.vmt_tools.generate_scenario mixed_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear --resources 0.3,5,1 \
  --exchange-regime mixed
```

### Money Inventory Generation

**Rule**: If exchange regime is `money_only`, `mixed`, or `mixed_liquidity_gated`, generate M inventories.

**Default Strategy: Same as Goods**
```python
if exchange_regime in ["money_only", "mixed", "mixed_liquidity_gated"]:
    # Use same range as goods by default
    M_inventories = generate_inventories(n_agents, inv_min, inv_max)
    initial_inventories['M'] = M_inventories
```

**Rationale:**
- Simple and predictable
- Ensures all agents can participate in monetary trade
- Users can manually edit YAML if they want specific money distributions

### Money Parameters

**Phase 2 defaults (conservative):**
```python
if exchange_regime in ["money_only", "mixed", "mixed_liquidity_gated"]:
    params['exchange_regime'] = exchange_regime
    params['money_mode'] = 'quasilinear'        # Simple, well-tested
    params['money_scale'] = 1                    # No scaling
    params['lambda_money'] = 1.0                 # Neutral marginal utility
    # lambda_update_rate, lambda_bounds, liquidity_gate use schema defaults
```

**Advanced money parameters**: Deferred to Phase 3+ (users can manually edit YAML)

---

## Feature 2: Scenario Presets

### Motivation

Common use cases require specific parameter combinations. Presets eliminate repetitive typing and encode best practices.

### CLI Interface

**New optional flag:**
```bash
--preset {minimal|standard|large|money_demo|mixed_economy}
```

**Behavior**: Preset overrides default values but can be overridden by explicit flags.

**Example:**
```bash
# Use preset
python3 -m src.vmt_tools.generate_scenario demo --preset money_demo

# Override preset's utilities
python3 -m src.vmt_tools.generate_scenario demo \
  --preset money_demo --utilities ces
```

### Preset Definitions

#### 1. `minimal` - Quick Testing
**Purpose**: Fast smoke tests, debugging

```python
{
    'agents': 10,
    'grid': 20,
    'inventory_range': (10, 50),
    'utilities': ['ces', 'linear'],
    'resource_config': (0.3, 5, 1),
    'exchange_regime': 'barter_only'
}
```

**Output**: Generates in < 0.5s, runs in < 10s

---

#### 2. `standard` - Default Demonstration
**Purpose**: Typical demo, shows all utility types

```python
{
    'agents': 30,
    'grid': 40,
    'inventory_range': (15, 60),
    'utilities': ['ces', 'linear', 'quadratic', 'translog', 'stone_geary'],
    'resource_config': (0.35, 6, 2),
    'exchange_regime': 'barter_only'
}
```

**Output**: Balanced complexity, good for documentation

---

#### 3. `large` - Performance Testing
**Purpose**: Stress testing, benchmarking

```python
{
    'agents': 80,
    'grid': 80,
    'inventory_range': (10, 100),
    'utilities': ['ces', 'linear'],  # Simple utilities for performance
    'resource_config': (0.4, 8, 3),
    'exchange_regime': 'barter_only'
}
```

**Output**: Large agent count, good for profiling

---

#### 4. `money_demo` - Monetary Exchange Demo
**Purpose**: Showcase money system (Phase 2+)

```python
{
    'agents': 20,
    'grid': 30,
    'inventory_range': (10, 50),
    'utilities': ['linear'],  # Simple for clarity
    'resource_config': (0.2, 5, 1),  # Less foraging, more trading
    'exchange_regime': 'money_only'
}
```

**Output**: Demonstrates A↔M and B↔M trades

**Special behavior**: Automatically generates M inventories

---

#### 5. `mixed_economy` - Hybrid Barter + Money
**Purpose**: Test mixed exchange dynamics

```python
{
    'agents': 40,
    'grid': 50,
    'inventory_range': (20, 80),
    'utilities': ['ces', 'linear', 'quadratic'],
    'resource_config': (0.3, 6, 2),
    'exchange_regime': 'mixed'
}
```

**Output**: Agents can use both barter and monetary trade

**Special behavior**: Automatically generates M inventories

---

### Preset Implementation Strategy

**Approach**: Dictionary-based presets in `param_strategies.py`

```python
# src/vmt_tools/param_strategies.py

PRESETS = {
    'minimal': {
        'agents': 10,
        'grid': 20,
        'inventory_range': (10, 50),
        'utilities': ['ces', 'linear'],
        'resource_config': (0.3, 5, 1),
        'exchange_regime': 'barter_only'
    },
    'standard': {
        'agents': 30,
        'grid': 40,
        'inventory_range': (15, 60),
        'utilities': ['ces', 'linear', 'quadratic', 'translog', 'stone_geary'],
        'resource_config': (0.35, 6, 2),
        'exchange_regime': 'barter_only'
    },
    'large': {
        'agents': 80,
        'grid': 80,
        'inventory_range': (10, 100),
        'utilities': ['ces', 'linear'],
        'resource_config': (0.4, 8, 3),
        'exchange_regime': 'barter_only'
    },
    'money_demo': {
        'agents': 20,
        'grid': 30,
        'inventory_range': (10, 50),
        'utilities': ['linear'],
        'resource_config': (0.2, 5, 1),
        'exchange_regime': 'money_only'
    },
    'mixed_economy': {
        'agents': 40,
        'grid': 50,
        'inventory_range': (20, 80),
        'utilities': ['ces', 'linear', 'quadratic'],
        'resource_config': (0.3, 6, 2),
        'exchange_regime': 'mixed'
    }
}

def get_preset(preset_name: str) -> dict:
    """Get preset configuration by name."""
    if preset_name not in PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. "
                        f"Available: {', '.join(PRESETS.keys())}")
    return PRESETS[preset_name].copy()
```

**CLI argument parsing:**
```python
# In generate_scenario.py

if args.preset:
    preset = get_preset(args.preset)
    # Apply preset defaults
    agents = args.agents or preset['agents']
    grid = args.grid or preset['grid']
    # ... etc
else:
    # Existing behavior (all required)
    agents = args.agents
    grid = args.grid
    # ... etc
```

---

## Implementation Steps

### Step 1: Add Exchange Regime Support (30 min)

**Files to modify:**
- `src/vmt_tools/scenario_builder.py`
- `src/vmt_tools/generate_scenario.py`

**Changes:**
1. Add `exchange_regime` parameter to `generate_scenario()`
2. Generate M inventories when needed
3. Set money parameters when regime requires it
4. Add CLI argument for `--exchange-regime`

**Validation:**
- Generate scenario with `money_only` → M field present
- Generate scenario with `barter_only` → M field absent
- Load both scenarios with schema loader

---

### Step 2: Add Preset System (45 min)

**Files to modify:**
- `src/vmt_tools/param_strategies.py` (add PRESETS dict)
- `src/vmt_tools/generate_scenario.py` (add --preset flag and logic)

**Changes:**
1. Define 5 presets in `PRESETS` dict
2. Add `get_preset()` function
3. Add `--preset` CLI argument
4. Update argument parsing to use preset defaults
5. Make other arguments optional when preset is used

**Validation:**
- Generate scenario with each preset
- Override preset values with explicit flags
- Verify preset + explicit flag combinations work

---

### Step 3: Update Documentation (30 min)

**Files to modify:**
- `src/vmt_tools/README.md`

**Changes:**
1. Add exchange regime section with examples
2. Document all 5 presets with use cases
3. Add "Phase 2 Features" section
4. Update usage examples

---

### Step 4: Test & Validate (30 min)

**Test scenarios to generate:**
1. `test_money_only.yaml` - money_only regime
2. `test_mixed.yaml` - mixed regime
3. `test_preset_minimal.yaml` - minimal preset
4. `test_preset_money_demo.yaml` - money_demo preset
5. `test_preset_mixed_economy.yaml` - mixed_economy preset

**Validation checklist:**
- [ ] All test scenarios pass schema validation
- [ ] Money scenarios have M field
- [ ] Money parameters set correctly
- [ ] Presets produce expected configurations
- [ ] Preset overrides work
- [ ] Backward compatibility (Phase 1 commands unchanged)

---

## Usage Examples

### Exchange Regime Examples

**Money-only economy:**
```bash
python3 -m src.vmt_tools.generate_scenario monetary_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities linear --resources 0.3,5,1 \
  --exchange-regime money_only --seed 42
```

**Mixed economy:**
```bash
python3 -m src.vmt_tools.generate_scenario hybrid_test \
  --agents 30 --grid 40 --inventory-range 15,60 \
  --utilities ces,linear --resources 0.35,6,2 \
  --exchange-regime mixed --seed 42
```

### Preset Examples

**Quick test:**
```bash
python3 -m src.vmt_tools.generate_scenario quick_test --preset minimal --seed 42
```

**Money demonstration:**
```bash
python3 -m src.vmt_tools.generate_scenario demo --preset money_demo --seed 42
```

**Override preset:**
```bash
# Use money_demo preset but with 50 agents instead of 20
python3 -m src.vmt_tools.generate_scenario large_demo \
  --preset money_demo --agents 50 --seed 42
```

---

## Deferred to Phase 3+

The following features are explicitly deferred to keep Phase 2 simple:

### NOT in Phase 2:
- ❌ Weighted utility mixes (`--utilities ces:0.6,linear:0.4`)
- ❌ Custom money inventory range (`--money-range 100,500`)
- ❌ Money parameter overrides (`--lambda-money 2.0`, `--money-scale 100`)
- ❌ Simulation parameter overrides (`--vision 10`, `--movement 2`)
- ❌ Parameter validation (`--validate` flag)
- ❌ Custom parameter ranges (`--param-ranges config.json`)
- ❌ Mode schedules (already documented as manual YAML editing)
- ❌ Advanced money parameters (lambda_update_rate, lambda_bounds, liquidity_gate)

**Rationale**: These features add complexity without immediate benefit. Phase 2 focuses on the two most-requested features (exchange regimes and presets) while maintaining CLI simplicity.

---

## Testing Strategy

### Unit Tests (Optional - Phase 3)

If unit tests are added in Phase 3, they should cover:
- Preset loading and validation
- Money inventory generation
- Exchange regime parameter setting
- Preset override logic

### Integration Tests (Required)

**Generate and validate:**
1. One scenario per exchange regime
2. One scenario per preset
3. Combinations: preset + explicit overrides

**Validation steps:**
1. Run `src.scenarios.loader.load_scenario()` → no errors
2. Check M field presence/absence
3. Check money parameters when applicable
4. Spot-check a few generated values

---

## Backward Compatibility

**Critical requirement**: All Phase 1 commands must work identically.

**Test:**
```bash
# This Phase 1 command should produce identical results
python3 -m src.vmt_tools.generate_scenario test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear --resources 0.3,5,1 --seed 42
```

**Expected:**
- No M field in initial_inventories
- exchange_regime = "barter_only"
- No money parameters in params dict (uses schema defaults)

---

## Post-Implementation Checklist

- [ ] `--exchange-regime` flag works for all 4 regimes
- [ ] M inventories generated when needed
- [ ] Money parameters set appropriately
- [ ] 5 presets defined and tested
- [ ] Preset overrides work correctly
- [ ] README updated with Phase 2 examples
- [ ] 5 test scenarios generated and validated
- [ ] Backward compatibility verified
- [ ] No linter errors
- [ ] Phase 2 changelog created

---

## Estimated Time Breakdown

- **Step 1** (Exchange Regime): 30 minutes
- **Step 2** (Presets): 45 minutes
- **Step 3** (Documentation): 30 minutes
- **Step 4** (Testing): 30 minutes

**Total: ~2-3 hours** (with buffer: 4 hours)

---

## Success Metrics

Phase 2 succeeds if:

1. ✅ Developers can generate money scenarios with one command
2. ✅ Presets eliminate repetitive typing for common cases
3. ✅ All 4 exchange regimes supported
4. ✅ Generated money scenarios load and run without errors
5. ✅ CLI remains simple (no cognitive overload)
6. ✅ Phase 1 behavior unchanged (backward compatibility)

---

## Next Steps After Phase 2

**Immediate:**
- User feedback on presets (are these useful? need more?)
- Identify most-requested customization (weighted utils? param overrides?)

**Phase 3 Candidates (prioritize based on feedback):**
1. Weighted utility mixes
2. Custom money inventory ranges
3. Parameter validation
4. Unit test suite
5. Money parameter overrides

**Long-term (Phase 4+):**
- Advanced presets (research scenarios)
- Batch generation (`--count 50`)
- Template system
- GUI integration

---

**Ready to implement Phase 2!** 🚀

