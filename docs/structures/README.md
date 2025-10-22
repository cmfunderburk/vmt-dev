# VMT Scenario Structure Reference

This directory contains comprehensive reference materials for creating VMT simulation scenarios using YAML configuration files.

## Files Overview

### 📋 [comprehensive_scenario_template.yaml](comprehensive_scenario_template.yaml)
**Complete parameter reference with ranges and examples**

- Shows ALL available parameters with their valid ranges
- Includes detailed comments explaining each parameter
- Demonstrates all utility function types with typical values
- Contains parameter selection guidelines and best practices
- Includes validation rules and common pitfalls to avoid
- **Use this as your primary reference when creating new scenarios**

### 📊 [parameter_quick_reference.md](parameter_quick_reference.md)
**Quick lookup table for all parameters**

- Tabular format for fast parameter lookup
- Shows types, defaults, ranges, and typical values
- Organized by parameter category (spatial, trading, money, etc.)
- Includes utility function parameter tables
- Contains common parameter combinations for different scenario types
- **Use this for quick parameter lookups while editing scenarios**

### 🚀 [minimal_working_example.yaml](minimal_working_example.yaml)
**Absolute minimum required parameters**

- Shows the smallest possible working scenario
- Demonstrates only the required parameters
- All other parameters use their default values
- **Use this as a starting point for new scenarios**

### 💰 [money_example.yaml](money_example.yaml)
**Monetary scenario with mixed exchange regime**

- Demonstrates all money-related parameters
- Shows heterogeneous agent inventories and λ values
- **Emphasizes heterogeneous lambda_money for realistic monetary trading**
- Includes mode scheduling for temporal control
- **Use this as a template for monetary scenarios**

## How to Use These Files

### For New Scenario Creation
1. Start with `minimal_working_example.yaml` as your base
2. Use `parameter_quick_reference.md` to look up specific parameters
3. Refer to `comprehensive_scenario_template.yaml` for detailed explanations
4. Use `money_example.yaml` if you need monetary features

### For Parameter Reference
1. Use `parameter_quick_reference.md` for quick lookups
2. Use `comprehensive_scenario_template.yaml` for detailed explanations
3. Check the validation checklist in the quick reference

### For Understanding Parameter Interactions
1. Read the guidelines in `comprehensive_scenario_template.yaml`
2. Study the common parameter combinations
3. Review the performance considerations

## Related Documentation

- **Full Configuration Guide:** [`../scenario_configuration_guide.md`](../scenario_configuration_guide.md)
- **Schema Implementation:** [`../../src/scenarios/schema.py`](../../src/scenarios/schema.py)
- **Demo Scenarios:** [`../../scenarios/demos/`](../../scenarios/demos/)

## Quick Start

1. **Copy the minimal example:**
   ```bash
   cp docs/structures/minimal_working_example.yaml scenarios/my_scenario.yaml
   ```

2. **Edit the parameters you need:**
   - Change `name`, `N`, `agents` for basic setup
   - Modify `initial_inventories` for agent endowments
   - Adjust `utilities` for agent preferences
   - Set `params` for simulation behavior

3. **Test your scenario:**
   ```bash
   python launcher.py scenarios/my_scenario.yaml --seed 42
   ```

4. **For monetary scenarios:**
   - Add `M` to `initial_inventories`
   - Set `exchange_regime: "mixed"` or `"money_only"`
   - **RECOMMENDED: Add heterogeneous `lambda_money` for realistic monetary trading**

## Parameter Categories

### Required Parameters
- `schema_version`, `name`, `N`, `agents`
- `initial_inventories.A`, `initial_inventories.B`
- `utilities.mix` (at least one utility function)
- `resource_seed.density`, `resource_seed.amount`

### Optional Parameters (All have defaults)
- **Spatial:** `vision_radius`, `interaction_radius`, `move_budget_per_tick`, `spread`
- **Trading:** `dA_max`, `trade_cooldown_ticks`
- **Foraging:** `forage_rate`, `resource_growth_rate`, `resource_max_amount`, `resource_regen_cooldown`
- **Economic:** `epsilon`, `beta`
- **Money:** `exchange_regime`, `money_mode`, `money_scale`, `lambda_money`, etc.
- **Mode Schedule:** `mode_schedule` (entire section optional)

### Implementation Status
- **Fully Implemented:** All basic parameters, money system (barter_only, money_only, mixed), quasilinear mode, mode scheduling
- **Planned:** `kkt_lambda` mode, `mixed_liquidity_gated` regime, `liquidity_gate` parameters, distribution syntax
- **Recommended:** Use heterogeneous `lambda_money` values for monetary trading scenarios

## Common Scenarios

### Pedagogical Scenarios
- Small agent count (5-15)
- Simple utilities (single type)
- Clear heterogeneity (explicit inventory lists)
- Descriptive names

### Performance Benchmarks
- Vary grid size and agent count
- Minimal complexity
- No mode schedule
- Fixed seeds

### Research Scenarios
- Heterogeneous agents (multiple utility types)
- Long runs (100+ ticks)
- Regenerating resources
- Complex parameter combinations

## Validation

All scenarios are validated when loaded. Common errors:
- Missing required parameters
- Invalid parameter ranges
- List length mismatches
- Utility weights not summing to 1.0
- Stone-Geary inventories below subsistence
- Missing money for monetary regimes

## Performance Tips

- **Agent density:** Keep agents/N² between 1-10%
- **Vision radius:** Use N/4 to N/2 for local markets
- **Move budget:** Set to vision_radius/5 for realistic movement
- **Trade size:** Keep dA_max ≤ typical inventory levels/2
- **Resource density:** 0.1-0.3 for sparse, 0.3-0.5 for moderate

---

**Last Updated:** 2025-01-27  
**VMT Version:** Current  
**Schema Version:** 1
