# Scenario Generator Tool

**Version**: Phase 2 Complete  
**Last Updated**: 2025-10-21  
**Status**: ✅ Production Ready

---

## Overview

The VMT Scenario Generator is a command-line tool that creates valid YAML scenario files in <0.1 seconds. It's designed for rapid iteration, test suites, scripting, and batch generation.

**Key Features:**
- ✅ All 5 utility types with conservative parameter randomization
- ✅ Deterministic generation with `--seed` flag
- ✅ Automatic validation (schema-compliant YAML)
- ✅ Exchange regime support (`barter_only`, `money_only`, `mixed`)
- ✅ Scenario presets (`minimal`, `standard`, `large`, `money_demo`, `mixed_economy`)
- ✅ Automatic money inventory generation for monetary economies

---

## Current Status: Phase 2 Complete ✅

| Phase | Status | Completion Date | Features |
|-------|--------|-----------------|----------|
| Phase 1: CLI MVP | ✅ Complete | 2025-10-20 | All 5 utility types, deterministic generation |
| Phase 2: Exchange Regimes & Presets | ✅ Complete | 2025-10-21 | Money support, presets, automatic validation |
| Phase 3: Advanced Features | 🔮 Future | — | Weighted utility mixes, custom ranges |

---

## Quick Start

### Basic Usage

```bash
# Generate a test scenario
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

### Using Presets (Phase 2)

```bash
# Quick money demo
python3 -m src.vmt_tools.generate_scenario demo --preset money_demo --seed 42

# Override preset values
python3 -m src.vmt_tools.generate_scenario large_demo \
  --preset money_demo --agents 50 --seed 42
```

### Exchange Regimes (Phase 2)

```bash
# Money-only economy
python3 -m src.vmt_tools.generate_scenario money_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities linear --resources 0.2,5,1 \
  --exchange-regime money_only --seed 42

# Mixed economy (barter + money)
python3 -m src.vmt_tools.generate_scenario hybrid_test \
  --agents 30 --grid 40 --inventory-range 15,60 \
  --utilities ces,linear --resources 0.35,6,2 \
  --exchange-regime mixed --seed 42
```

---

## Phase 2 Features (Complete)

### 1. Exchange Regime Selection

Control which types of exchanges are allowed:

| Regime | Description | Use Case |
|--------|-------------|----------|
| `barter_only` | Only A↔B trades (default) | Traditional barter economy |
| `money_only` | Only A↔M and B↔M trades | Pure monetary economy |
| `mixed` | All exchange types (A↔B, A↔M, B↔M) | Hybrid economy |
| `mixed_liquidity_gated` | Mixed with liquidity requirements | Future extension |

**Automatic Money Inventory:**
When `--exchange-regime money_only` or `mixed` is specified, the generator automatically adds money inventory (M) to agents.

### 2. Scenario Presets

Pre-configured templates for common use cases:

| Preset | Agents | Grid | Utilities | Regime | Use Case |
|--------|--------|------|-----------|--------|----------|
| `minimal` | 10 | 20×20 | ces, linear | barter_only | Quick testing |
| `standard` | 30 | 40×40 | All 5 types | barter_only | Default demo |
| `large` | 80 | 80×80 | ces, linear | barter_only | Performance testing |
| `money_demo` | 20 | 30×30 | linear | money_only | Money showcase |
| `mixed_economy` | 40 | 50×50 | ces, linear, quad | mixed | Hybrid economy |

**Preset Override:**
```bash
# Use money_demo template but change agents
python3 -m src.vmt_tools.generate_scenario custom \
  --preset money_demo --agents 50 --grid 50 --seed 42
```

### 3. Validation & Error Handling

The generator validates:
- Schema compliance (all required fields present)
- Money inventory presence (for monetary regimes)
- Utility type compatibility
- Parameter ranges
- Grid size vs. agent count

**Error Example:**
```bash
$ python3 -m src.vmt_tools.generate_scenario test \
  --exchange-regime money_only --utilities ces

Error: exchange_regime='money_only' requires money inventory.
Money inventory will be automatically generated with default range [50, 150].
```

---

## Supported Utility Types

All 5 utility functions are supported with conservative parameter randomization:

### 1. CES (Constant Elasticity of Substitution)
```bash
--utilities ces
```
**Parameters:** `rho` ∈ [-2, 2], `wA`, `wB` ∈ [0.5, 2.0]

### 2. Linear (Perfect Substitutes)
```bash
--utilities linear
```
**Parameters:** `vA`, `vB` ∈ [0.5, 2.0]

### 3. Quadratic (Bliss Points)
```bash
--utilities quadratic
```
**Parameters:** `A_star`, `B_star` ∈ [30, 70], `sigma_A`, `sigma_B` ∈ [0.01, 0.05]

### 4. Translog (Transcendental Logarithmic)
```bash
--utilities translog
```
**Parameters:** `alpha_0`, `alpha_A`, `alpha_B`, `beta_AA`, `beta_BB`, `beta_AB` (conservative defaults)

### 5. Stone-Geary (Subsistence Constraints)
```bash
--utilities stone_geary
```
**Parameters:** `alpha_A`, `alpha_B` ∈ [0.5, 2.0], `gamma_A`, `gamma_B` = 0 (default, no subsistence)

---

## Usage Patterns

### Pattern 1: Test Suite Generation

```bash
# Generate deterministic test scenarios
for seed in 42 43 44 45 46; do
  python3 -m src.vmt_tools.generate_scenario test_$seed \
    --preset standard --seed $seed
done
```

### Pattern 2: Performance Benchmarking

```bash
# Large-scale stress test
python3 -m src.vmt_tools.generate_scenario perf_test \
  --agents 400 --grid 64 --inventory-range 10,100 \
  --utilities ces,linear --resources 0.2,10,2 --seed 42
```

### Pattern 3: Comparative Analysis

```bash
# Same initial conditions, different regimes
python3 -m src.vmt_tools.generate_scenario barter_test \
  --agents 30 --grid 40 --utilities ces --seed 42 \
  --exchange-regime barter_only

python3 -m src.vmt_tools.generate_scenario money_test \
  --agents 30 --grid 40 --utilities ces --seed 42 \
  --exchange-regime money_only

# Compare results in log viewer
```

### Pattern 4: Heterogeneous Populations

```bash
# All 5 utility types (equal weights)
python3 -m src.vmt_tools.generate_scenario mixed_population \
  --agents 50 --grid 50 --inventory-range 20,80 \
  --utilities ces,linear,quadratic,translog,stone_geary \
  --resources 0.4,8,3 --seed 42
```

---

## Command Reference

### Required Arguments

- `scenario_name` — Output filename (creates `scenarios/{name}.yaml`)

### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--agents` | int | 20 | Number of agents |
| `--grid` | int | 32 | Grid size (NxN) |
| `--inventory-range` | int,int | 5,20 | Min,max initial inventory |
| `--utilities` | list | ces,linear | Comma-separated utility types |
| `--resources` | float,int,int | 0.2,5,1 | Density,amount,growth_rate |
| `--seed` | int | Random | Deterministic generation seed |
| `--exchange-regime` | str | barter_only | Exchange type control |
| `--preset` | str | — | Use predefined template |

### Exchange Regime Options

| Value | Description |
|-------|-------------|
| `barter_only` | Only A↔B trades (default, backward compatible) |
| `money_only` | Only A↔M and B↔M trades (auto-generates M inventory) |
| `mixed` | All exchange types (A↔B, A↔M, B↔M) |

### Preset Options

| Value | Configuration |
|-------|---------------|
| `minimal` | 10 agents, 20×20 grid, ces+linear, barter |
| `standard` | 30 agents, 40×40 grid, all 5 utilities, barter |
| `large` | 80 agents, 80×80 grid, ces+linear, barter |
| `money_demo` | 20 agents, 30×30 grid, linear, money_only |
| `mixed_economy` | 40 agents, 50×50 grid, ces+linear+quadratic, mixed |

---

## Advanced Usage

### Custom Resource Configuration

```bash
# Low-density, high-value resources
python3 -m src.vmt_tools.generate_scenario sparse \
  --agents 20 --grid 40 --resources 0.1,10,2 --seed 42

# High-density, low-value resources
python3 -m src.vmt_tools.generate_scenario abundant \
  --agents 20 --grid 40 --resources 0.5,3,1 --seed 42
```

### Specific Utility Type Only

```bash
# Pure CES economy
python3 -m src.vmt_tools.generate_scenario ces_only \
  --agents 30 --grid 40 --utilities ces --seed 42

# Pure Linear economy (perfect substitutes)
python3 -m src.vmt_tools.generate_scenario linear_only \
  --agents 30 --grid 40 --utilities linear --seed 42
```

### Money with Custom Inventory Ranges

```bash
# Money economy with high initial wealth
python3 -m src.vmt_tools.generate_scenario wealthy \
  --agents 20 --grid 30 --inventory-range 50,150 \
  --utilities linear --exchange-regime money_only --seed 42
# Note: Money inventory (M) is auto-generated with similar range
```

---

## Output Format

Generated YAML files follow the standard VMT scenario schema:

```yaml
schema_version: 1
name: my_test
N: 30
agents: 20

initial_inventories:
  A: { uniform_int: [10, 50] }
  B: { uniform_int: [10, 50] }
  M: { uniform_int: [50, 150] }  # Auto-generated for money_only/mixed

utilities:
  mix:
    - type: ces
      weight: 0.5
      params:
        rho: -0.5
        wA: 1.0
        wB: 1.0
    - type: linear
      weight: 0.5
      params:
        vA: 1.0
        vB: 1.0

params:
  exchange_regime: money_only  # If specified
  # ... other params with defaults

resource_seed:
  density: 0.3
  amount: 5
```

---

## Implementation History

### Phase 1: CLI MVP (Complete — 2025-10-20)

**Git Commits:**
- `072cc2f` — Add CLI scenario generator documentation
- `deeba96` — Minimal CLI scenario generator added
- `5092fc8` — Phase 1 finished but needs review
- `a84ae98` — Precommit for phase 1 scenario generator

**Features Delivered:**
- Basic CLI with argparse
- All 5 utility types with parameter randomization
- Deterministic generation with `--seed`
- Automatic schema validation
- Generation time < 0.1 seconds
- Comprehensive README in `src/vmt_tools/`

**Tests:** Basic validation, deterministic reproduction

---

### Phase 2: Exchange Regimes & Presets (Complete — 2025-10-21)

**Git Commits:**
- `e0152f0` — Feature/scenario gen phase2 (#5) [MERGED]
- `d3ce44c` — Add PR description for Scenario Generator Phase 2
- `227a388` — Mark Scenario Generator Phase 2 as complete
- `0e5d26c` — Add Scenario Generator Phase 2 completion summary
- `30312df` — Add comprehensive validation tests
- `5488b0e` — Update scenario generator documentation for Phase 2
- `4ce25be` — Add preset system to scenario generator
- `e75b5e0` — Add exchange regime support to scenario generator

**Features Delivered:**
- Exchange regime selection (`--exchange-regime`)
- Scenario presets (`--preset`)
- Automatic money inventory generation
- Enhanced validation (money inventory checks)
- 5 predefined presets (minimal, standard, large, money_demo, mixed_economy)

**Tests:** `test_comprehensive_validation_tests_for_scenario_generator_phase2.py`

**Key Achievement:** Tool now supports full money system integration with automatic configuration.

---

### Phase 3: Advanced Features (Future — Based on Feedback)

**Status:** Not yet planned, awaiting user feedback

**Possible Features:**
- Weighted utility mixes (`--utilities ces:0.6,linear:0.4`)
- Custom money inventory ranges (`--money-range 100,500`)
- Parameter validation mode (`--validate-only`)
- Unit test integration
- Batch generation with CSV input
- Custom parameter overrides (vision_radius, trade_cooldown, etc.)

**Decision Gate:** After v1.0 release and user feedback collection

---

## Testing

### Validation Tests (Phase 2)

The generator includes comprehensive validation tests:

```python
def test_exchange_regime_support():
    """Verify all exchange regimes work."""
    for regime in ["barter_only", "money_only", "mixed"]:
        scenario = generate_scenario(..., exchange_regime=regime)
        assert scenario.params.exchange_regime == regime
        if regime in ["money_only", "mixed"]:
            assert scenario.initial_inventories["M"] > 0

def test_preset_system():
    """Verify all presets generate valid scenarios."""
    for preset in ["minimal", "standard", "large", "money_demo", "mixed_economy"]:
        scenario = generate_scenario(..., preset=preset)
        validate_scenario(scenario)  # Schema validation
```

### Determinism Testing

```bash
# Generate same scenario twice, verify identical output
python3 -m src.vmt_tools.generate_scenario test1 --seed 42 --utilities ces
python3 -m src.vmt_tools.generate_scenario test2 --seed 42 --utilities ces
diff scenarios/test1.yaml scenarios/test2.yaml
# Expected: No differences
```

---

## Related Documentation

- **Tool README**: [`src/vmt_tools/README.md`](../../src/vmt_tools/README.md) — Complete CLI reference
- **Project Overview**: [`docs/1_project_overview.md`](../1_project_overview.md#method-1-cli-scenario-generator-developer-workflow-) — User-facing guide
- **Money System Guide**: [`docs/guides/money_system.md`](money_system.md) — Money system integration
- **Schema Reference**: [`src/scenarios/schema.py`](../../src/scenarios/schema.py) — Complete schema definition

---

## Troubleshooting

### Error: "exchange_regime='money_only' requires positive M inventory"

**Solution:** Money inventory is auto-generated. If you see this error, it's likely a bug. Report it.

### Error: "Utility type 'X' not recognized"

**Solution:** Check supported types: `ces`, `linear`, `quadratic`, `translog`, `stone_geary` (case-sensitive)

### Error: "Grid size too small for agent count"

**Solution:** Increase `--grid` or decrease `--agents`. Recommended: grid_size² ≥ agents × 2

### Generated scenarios don't load

**Solution:** The generator validates output. If scenarios don't load, check:
1. Schema version compatibility
2. Parameter ranges (use `--seed` for reproducibility)
3. File permissions (scenarios/ directory must be writable)

---

## Summary

The Scenario Generator (Phase 2 Complete) provides:

✅ **Rapid Generation** — Valid scenarios in <0.1 seconds  
✅ **Deterministic** — Same seed → identical output  
✅ **Money Support** — Full integration with money system  
✅ **Presets** — 5 common templates ready to use  
✅ **Validation** — Automatic schema and parameter checks  
✅ **Flexible** — All 5 utility types, all exchange regimes

**Status:** Production-ready tool for developers and researchers.

**Next Steps:** Await user feedback to determine Phase 3 priorities.

