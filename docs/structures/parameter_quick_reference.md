# VMT Scenario Parameter Quick Reference

**Purpose:** Quick lookup table for all VMT scenario parameters with their types, defaults, ranges, and typical values.

**Related Files:**
- Comprehensive template: [`comprehensive_scenario_template.yaml`](comprehensive_scenario_template.yaml)
- Full guide: [`../scenario_configuration_guide.md`](../scenario_configuration_guide.md)

---

## Top-Level Parameters (Required)

| Parameter | Type | Default | Range | Typical Values | Notes |
|-----------|------|---------|-------|----------------|-------|
| `schema_version` | int | - | 1 | 1 | Always 1 for current implementation |
| `name` | string | - | Any | Descriptive | Human-readable scenario name |
| `N` | int | - | > 0 | 10-40 | Grid size (N×N), larger = more computation |
| `agents` | int | - | > 0 | 5-50 | Agent count, density = agents/N² |

## Initial Inventories (Required)

| Parameter | Type | Default | Range | Typical Values | Notes |
|-----------|------|---------|-------|----------------|-------|
| `initial_inventories.A` | int \| list | - | ≥ 0 | 5-50 | Good A endowment |
| `initial_inventories.B` | int \| list | - | ≥ 0 | 5-50 | Good B endowment |
| `initial_inventories.M` | int \| list | - | ≥ 0 | 50-500 | Money (required for monetary regimes) |
| `initial_inventories.lambda_money` | list[float] | `params.lambda_money` | > 0 | 0.1-5.0 | Per-agent λ values (RECOMMENDED for monetary trading) |

## Spatial Parameters

| Parameter | Type | Default | Range | Typical Values | Notes |
|-----------|------|---------|-------|----------------|-------|
| `vision_radius` | int | 5 | ≥ 0 | N/4 to N/2 | Perception distance |
| `interaction_radius` | int | 1 | ≥ 0 | 1 | Trading distance |
| `move_budget_per_tick` | int | 1 | > 0 | 1-3 | Movement speed |
| `spread` | float | 0.0 | ≥ 0 | 0.0-0.15 | Bid-ask spread |

## Trading Parameters

| Parameter | Type | Default | Range | Typical Values | Notes |
|-----------|------|---------|-------|----------------|-------|
| `dA_max` | int | 5 | > 0 | 1-20 | Maximum trade size |
| `trade_cooldown_ticks` | int | 5 | ≥ 0 | 0-20 | Failed trade cooldown |

## Foraging Parameters

| Parameter | Type | Default | Range | Typical Values | Notes |
|-----------|------|---------|-------|----------------|-------|
| `forage_rate` | int | 1 | > 0 | 1-5 | Harvest rate per tick |
| `resource_growth_rate` | int | 0 | ≥ 0 | 0-3 | Resource regeneration |
| `resource_max_amount` | int | 5 | > 0 | 5-20 | Max resource per cell |
| `resource_regen_cooldown` | int | 5 | ≥ 0 | 0-20 | Regeneration delay |

## Resource Claiming

| Parameter | Type | Default | Range | Values | Notes |
|-----------|------|---------|-------|--------|-------|
| `enable_resource_claiming` | bool | true | true/false | true | Enable claiming system |
| `enforce_single_harvester` | bool | true | true/false | true | One harvester per cell |

## Economic Parameters

| Parameter | Type | Default | Range | Typical Values | Notes |
|-----------|------|---------|-------|----------------|-------|
| `epsilon` | float | 1e-12 | > 0 | 1e-9 to 1e-15 | Numerical stability |
| `beta` | float | 0.95 | (0, 1] | 0.8-0.95 | Distance discount |

## Money System Parameters

| Parameter | Type | Default | Range | Typical Values | Notes |
|-----------|------|---------|-------|----------------|-------|
| `exchange_regime` | string | "barter_only" | See below | "mixed" | Trade type control (mixed_liquidity_gated planned) |
| `money_mode` | string | "quasilinear" | See below | "quasilinear" | Money utility mode (kkt_lambda planned) |
| `money_utility_form` | string | "linear" | "linear", "log" | "log" | Money utility functional form |
| `M_0` | float | 0.0 | ≥ 0 | 5-20 | Log money shift parameter (subsistence money) |
| `money_scale` | int | 1 | ≥ 1 | 1, 10, 100 | Money scale factor |
| `lambda_money` | float | 1.0 | > 0 | 0.1-5.0 | Fixed λ value |
| `lambda_update_rate` | float | 0.2 | [0, 1] | 0.1-0.3 | λ update smoothing (kkt_lambda mode only) |
| `lambda_bounds.lambda_min` | float | 1e-6 | > 0 | 0.01-1.0 | Minimum λ (kkt_lambda mode only) |
| `lambda_bounds.lambda_max` | float | 1e6 | > lambda_min | 10-1000 | Maximum λ (kkt_lambda mode only) |
| `liquidity_gate.min_quotes` | int | 3 | ≥ 0 | 3-5 | Min quotes for thick market (PLANNED) |
| `earn_money_enabled` | bool | false | true/false | false | Placeholder (unused) |

### Exchange Regime Values

| Value | Barter (A↔B) | Monetary (A↔M, B↔M) | Condition | Requires M |
|-------|-------------|---------------------|-----------|-------------|
| `barter_only` | ✓ | ✗ | Default | No |
| `money_only` | ✗ | ✓ | Pure monetary | Yes |
| `mixed` | ✓ | ✓ | All trade types | Yes |
| `mixed_liquidity_gated` | Conditional | ✓ | Barter if thin market (PLANNED) | Yes |

### Money Mode Values

| Value | Description | λ Behavior | Use Case | Status |
|-------|-------------|------------|----------|--------|
| `quasilinear` | Fixed λ | Constant | Pedagogical, simple | Implemented |
| `kkt_lambda` | Endogenous λ | Updates from prices | Research, realistic | Planned |

## Resource Seeding (Required)

| Parameter | Type | Default | Range | Typical Values | Notes |
|-----------|------|---------|-------|----------------|-------|
| `resource_seed.density` | float | - | [0, 1] | 0.1-0.5 | Resource probability |
| `resource_seed.amount` | int | - | > 0 | 3-10 | Resource per cell |

## Mode Schedule (Optional)

| Parameter | Type | Default | Range | Typical Values | Notes |
|-----------|------|---------|-------|----------------|-------|
| `mode_schedule.type` | string | - | "global_cycle" | "global_cycle" | Only implemented type |
| `mode_schedule.forage_ticks` | int | - | > 0 | 10-30 | Forage mode duration |
| `mode_schedule.trade_ticks` | int | - | > 0 | 15-40 | Trade mode duration |
| `mode_schedule.start_mode` | string | "forage" | "forage", "trade" | "forage" | Initial mode |

## Utility Function Parameters

### CES (Constant Elasticity of Substitution)

| Parameter | Type | Range | Typical Values | Notes |
|-----------|------|-------|----------------|-------|
| `rho` | float | ≠ 1.0 | -1.0 to 0.9 | Elasticity parameter |
| `wA` | float | > 0 | 0.1-0.9 | Weight for A |
| `wB` | float | > 0 | 0.1-0.9 | Weight for B |

### Linear (Perfect Substitutes)

| Parameter | Type | Range | Typical Values | Notes |
|-----------|------|-------|----------------|-------|
| `vA` | float | > 0 | 0.5-5.0 | Value of A |
| `vB` | float | > 0 | 0.5-5.0 | Value of B |

### Quadratic (Bliss Point)

| Parameter | Type | Range | Typical Values | Notes |
|-----------|------|-------|----------------|-------|
| `A_star` | float | > 0 | 10-50 | Bliss point for A |
| `B_star` | float | > 0 | 10-50 | Bliss point for B |
| `sigma_A` | float | > 0 | 0.1-2.0 | Curvature for A |
| `sigma_B` | float | > 0 | 0.1-2.0 | Curvature for B |
| `gamma` | float | ≥ 0 | 0.0-0.5 | Cross-curvature |

### Translog (Transcendental Logarithmic)

| Parameter | Type | Range | Typical Values | Notes |
|-----------|------|-------|----------------|-------|
| `alpha_0` | float | Any | 0.0-2.0 | Constant term |
| `alpha_A` | float | > 0 | 0.1-1.0 | First-order coefficient A |
| `alpha_B` | float | > 0 | 0.1-1.0 | First-order coefficient B |
| `beta_AA` | float | Any | -0.5 to 0.0 | Second-order coefficient A |
| `beta_BB` | float | Any | -0.5 to 0.0 | Second-order coefficient B |
| `beta_AB` | float | Any | -0.2 to 0.2 | Cross-partial term |

### Stone-Geary (Subsistence)

| Parameter | Type | Range | Typical Values | Notes |
|-----------|------|-------|----------------|-------|
| `alpha_A` | float | > 0 | 0.1-0.9 | Preference weight A |
| `alpha_B` | float | > 0 | 0.1-0.9 | Preference weight B |
| `gamma_A` | float | ≥ 0 | 0-20 | Subsistence level A |
| `gamma_B` | float | ≥ 0 | 0-20 | Subsistence level B |

**Critical Constraint:** For Stone-Geary, initial inventories must satisfy `A > gamma_A` AND `B > gamma_B` for all agents.

## Heterogeneous Lambda Values (RECOMMENDED for Monetary Trading)

**Why Use Heterogeneous λ Values:**
- High λ agents: value money more → lower ask prices in M → willing to sell goods for less money
- Low λ agents: value money less → higher bid prices in M → demand more money for goods
- Creates profitable monetary trading opportunities between agents with different λ values

**How to Set Up:**
```yaml
initial_inventories:
  M: 100
  lambda_money: [1.0, 2.0, 0.5, 1.5, 0.8]  # Agent-specific λ values
```

**Typical Values:**
- Range: 0.1-5.0
- Variation: 2-3x between highest and lowest λ
- Example: [0.5, 1.0, 1.5, 2.0, 0.8] for 5 agents

**Effect on Trading:**
- Homogeneous λ → few monetary trades (agents have similar money valuations)
- Heterogeneous λ → more trading opportunities and realistic dynamics

## Common Parameter Combinations

### Pedagogical Scenarios
- Small agents (5-15)
- Simple utilities (single type)
- Clear heterogeneity (explicit lists)
- Descriptive names

### Performance Benchmarks
- Vary grid size and agent count
- Minimal complexity
- No mode schedule
- Fixed seeds

### Empirical Estimation
- Heterogeneous agents (multiple utility types)
- Long runs (100+ ticks)
- Regenerating resources
- Translog utility

### Spatial Studies
- Large grids (N=40+)
- Lower agent density (<5%)
- Limited vision radius
- Clustered positions (future)

## Validation Checklist

- [ ] `schema_version = 1`
- [ ] `N > 0` and `agents > 0`
- [ ] Initial inventories ≥ 0
- [ ] List lengths equal `agents` count
- [ ] Money required for monetary regimes
- [ ] Utility weights sum to 1.0
- [ ] Stone-Geary inventories above subsistence
- [ ] CES rho ≠ 1.0
- [ ] Valid exchange regime (barter_only, money_only, mixed - mixed_liquidity_gated planned)
- [ ] Valid money mode (quasilinear implemented, kkt_lambda planned)
- [ ] Resource density [0, 1]
- [ ] Mode schedule ticks > 0
- [ ] **For monetary trading: Use heterogeneous lambda_money values**

## Performance Guidelines

### Agent Density
- Recommended: 1-10% of cells (agents/N²)
- High density: More interactions, more computation
- Low density: Sparse interactions, less computation

### Vision Radius
- Global: `vision_radius = N`
- Local: `vision_radius = N/4 to N/2`
- Extreme locality: `vision_radius = 1-5`

### Move Budget
- Rule of thumb: `move_budget ≈ vision_radius / 5`
- Slow: `move_budget_per_tick = 1`
- Moderate: `move_budget_per_tick = 2-3`
- Fast: `move_budget_per_tick = N/10`

### Trade Size
- Small: `dA_max = 1-3`
- Typical: `dA_max = 5-10`
- Large: `dA_max = 20+`
- Constraint: ≤ typical inventory levels / 2

---

**Last Updated:** 2025-01-27
**Version:** 1.0
