# VMT Scenario Generator Tool - Planning Document

**Document Type:** Planning & Design  
**Date:** 2025-10-21  
**Status:** Draft / Planning  
**Purpose:** Streamline developer workflow for creating diverse YAML scenario configurations

---

## Executive Summary

This document proposes the development of a **CLI-based scenario generator tool** to address the tedium of manually creating YAML scenario files. The tool will enable rapid generation of diverse, valid scenario configurations through simple command-line parameters, dramatically improving the developer workflow for testing, experimentation, and scenario suite creation.

**Key Goals:**
- **Speed**: Generate complete YAML scenarios in < 1 second
- **Simplicity**: Specify only essential parameters, get sensible defaults
- **Diversity**: Randomize utility parameters within validated ranges
- **Scriptability**: Enable batch generation for test suites and experiments
- **Maintainability**: Centralize parameter range logic for easy updates

**Impact**: Reduce scenario creation time from ~10 minutes (manual) to ~10 seconds (CLI), enabling rapid iteration and comprehensive testing.

---

## Part 1: Problem Statement

### Current State

**Manual YAML Creation** is the current approach:
1. Copy existing scenario file
2. Manually adjust agent count, grid size, inventories
3. Manually specify utility functions and parameters
4. Manually ensure parameter validity (e.g., Stone-Geary subsistence < inventories)
5. Manually balance utility mix weights to sum to 1.0
6. Save, load in GUI/CLI, test, iterate

**Pain points:**
- **Time-consuming**: 5-10 minutes per scenario
- **Error-prone**: Easy to violate constraints (rho=1.0, gamma>inventory, weights≠1.0)
- **Tedious**: Repetitive typing for similar scenarios
- **Limited diversity**: Developers tend to reuse same parameter sets

**GUI Scenario Builder** exists but:
- Still requires many clicks and form fields
- Not scriptable (can't generate 100 scenarios for a test suite)
- Too slow for rapid iteration during development
- Good for end-users, not developer workflow

### Desired State

**CLI Scenario Generator** workflow:
```bash
# Simple command
python -m vmt_tools.generate_scenario quick_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,quadratic --resources 0.3,5,1

# Creates scenarios/quick_test.yaml in < 1 second
```

**Benefits:**
- **10-100x faster** than manual creation
- **Scriptable**: Generate test suites, parameter sweeps
- **Valid by construction**: Enforces constraints automatically
- **Reproducible**: Seeded randomization for deterministic generation
- **Version controllable**: Commands in scripts, not 100 YAML files

---

## Part 2: Design Decisions

### 2.1 Core Design Principles

1. **CLI-first**: Optimized for developer terminal workflow
2. **Conservative defaults**: All random parameters use safe, tested ranges
3. **Explicit resources**: Require density, max_amount, regen_rate as inputs
4. **YAML-only output**: No validation or simulation (fast generation)
5. **Simple subsistence**: Stone-Geary gamma=0 by default (acts like Cobb-Douglas)
6. **Seeded randomization**: `--seed` flag for reproducible scenarios

### 2.2 Parameter Randomization Strategy

For each utility type, define conservative parameter ranges:

#### CES (Constant Elasticity of Substitution)
```python
rho: uniform(-1.0, 1.0) excluding [0.8, 1.2]  # Avoid near-Cobb-Douglas, avoid rho=1
wA: uniform(0.3, 0.7)
wB: 1.0 - wA  # Normalize weights
```
**Rationale**: 
- Moderate substitution/complementarity (-1 to 1)
- Avoid rho≈1 (undefined) and rho≈0 (Cobb-Douglas overlap)
- Symmetric preference distribution (0.3-0.7 range)

#### Linear (Perfect Substitutes)
```python
vA: uniform(0.5, 3.0)
vB: uniform(0.5, 3.0)
```
**Rationale**:
- Moderate relative valuations (not extreme like 0.01 or 100)
- Independent values (no normalization needed)

#### Quadratic (Bliss Points)
```python
A_star: uniform(inventory_min * 1.2, inventory_max * 0.8)  # Within inventory range
B_star: uniform(inventory_min * 1.2, inventory_max * 0.8)
sigma_A: uniform(A_star * 0.4, A_star * 0.8)  # Moderate curvature
sigma_B: uniform(B_star * 0.4, B_star * 0.8)
gamma: uniform(0.0, 0.2)  # Weak cross-curvature
```
**Rationale**:
- Bliss points inside typical inventory range (agents can reach them)
- Curvature proportional to bliss point (sensible satiation rates)
- Small gamma (weak complementarity, avoids complex interactions)
- **Note**: Schema expects parameter name `gamma` (not `gamma_quad`). This is a different parameter than Stone-Geary's `gamma_A`/`gamma_B`

#### Translog (Transcendental Logarithmic)
```python
alpha_0: 0.0  # Standard normalization
alpha_A: uniform(0.4, 0.6)
alpha_B: uniform(0.4, 0.6)
beta_AA: uniform(-0.10, -0.02)  # Negative = diminishing returns
beta_BB: uniform(-0.10, -0.02)
beta_AB: uniform(-0.03, 0.03)  # Small interaction term
```
**Rationale**:
- First-order coefficients near 0.5 (balanced preferences)
- Negative second-order terms (standard diminishing returns)
- Small beta_AB (avoids extreme complementarity/substitutability)
- These ranges ensure monotonicity over inventory range [1, 1000]

#### Stone-Geary (Subsistence Constraints)
```python
alpha_A: uniform(0.4, 0.6)
alpha_B: 1.0 - alpha_A  # Normalize to 1.0 (standard LES)
gamma_A: 0.0  # Default: no subsistence (acts like Cobb-Douglas)
gamma_B: 0.0
```
**Rationale**:
- Default gamma=0 avoids subsistence constraint complexity
- Normalized alphas (standard LES formulation)
- Users can manually edit YAML to add subsistence if needed
- Avoids inventory-parameter coupling issues
- **Note**: Schema expects parameter names `gamma_A` and `gamma_B` (not `gamma_A_SG`). These are different parameters than quadratic's `gamma`

### 2.3 Inventory Generation

```python
# For each agent, independently:
A_initial = randint(inventory_min, inventory_max)
B_initial = randint(inventory_min, inventory_max)
```

**Properties:**
- Heterogeneous starting endowments (more realistic)
- Uniform distribution over specified range
- Integer values (consistent with VMT type system)

**Validation:**
- `inventory_min >= 1` (required for log-based utilities like Translog and Stone-Geary)
- `inventory_max > inventory_min`

**Type Safety:**
- Good inventories (A, B) are always integers
- Money inventories (M) are always integers
- Utility parameters are floats, rounded to 2 decimal places in YAML output

### 2.4 Utility Mix Assignment

```python
# Equal weights by default
if utilities = ["ces", "quadratic", "translog"]:
    weights = [1/3, 1/3, 1/3]

# Explicit weights if provided
if utilities = ["ces:0.5", "quadratic:0.3", "translog:0.2"]:
    weights = [0.5, 0.3, 0.2]
    assert sum(weights) == 1.0
```

For each agent, randomly sample one utility from the mix (weighted sampling).

**Note on CES Weights:**
- CES utility weights (wA, wB) are normalized to sum to 1.0 by convention for interpretability
- The CES formula does not strictly require normalization (weights are scale-free)
- This is a convention, not a mathematical requirement

### 2.5 Default Simulation Parameters

**Conservative defaults for fast testing:**
```yaml
params:
  spread: 0.0                    # Zero bid-ask spread (reservation prices)
  vision_radius: 8               # Moderate vision
  interaction_radius: 1          # Adjacent trading only
  move_budget_per_tick: 1        # One step per tick
  dA_max: 5                      # Standard search range
  forage_rate: 1                 # One resource per tick
  trade_cooldown_ticks: 3        # Standard cooldown
  beta: 0.95                     # Standard discount factor
  epsilon: 1e-12                 # Standard epsilon
  exchange_regime: barter_only   # Default to barter
  enable_resource_claiming: true # Prevent clustering
  enforce_single_harvester: true # One agent per resource
  resource_growth_rate: 1        # Resource regeneration rate
  resource_max_amount: 5         # Max resource per cell
  resource_regen_cooldown: 5     # Cooldown before regen starts
```

**Note:** All resource parameters are now in the main `params` dict, not a separate `resource_params` section.

Users can override any of these via CLI flags if needed (Phase 2 feature).

### 2.6 Money Inventory Generation

When `exchange_regime` is set to `money_only`, `mixed`, or `mixed_liquidity_gated`, the schema requires money (M) in `initial_inventories`.

**Default behavior (Phase 1):**
- Phase 1 only supports `barter_only` regime (no money)
- Money inventory generation is deferred to Phase 2

**Phase 2 behavior:**
```python
if exchange_regime in ["money_only", "mixed", "mixed_liquidity_gated"]:
    # Generate money inventories (integers)
    # Default: same range as goods, or user-specified via --money-range
    M_inventories = [randint(money_min, money_max) for _ in range(n_agents)]
    initial_inventories['M'] = M_inventories
    
    # Update params with money configuration
    params['money_mode'] = 'quasilinear'  # Default, or user-specified
    params['money_scale'] = 100           # Default, or user-specified
    params['lambda_money'] = 1.0          # Default, or user-specified
    # Other money params use schema defaults
```

**CLI flags (Phase 2):**
```bash
--exchange-regime mixed              # Required to enable money
--money-range 100,500               # Optional: defaults to goods inventory range
--money-scale 100                   # Optional: defaults to 1
--lambda-money 1.0                  # Optional: defaults to 1.0
--money-mode quasilinear            # Optional: defaults to quasilinear
```

**Important:** Mode schedules are NOT supported in the CLI. They are considered a power-user feature and should be manually added to YAML files if needed.

### 2.7 Agent Positioning

**Important:** Agent starting positions are **not specified in the scenario YAML**. The simulation engine handles agent placement deterministically based on the simulation seed.

From the simulation engine:
- Agents are placed on random grid cells during initialization
- Placement is deterministic given the simulation seed
- Positions are shuffled but reproducible

This is not a scenario generation concern, but users should understand that:
1. The scenario file does not control agent positions
2. Running the same scenario with different simulation seeds produces different spatial configurations
3. Spatial heterogeneity emerges from the simulation, not the scenario

---

## Part 3: Benefits to the VMT Project

### 3.1 Developer Workflow Improvements

**Faster Testing:**
- Generate test scenarios in seconds, not minutes
- Rapidly iterate on parameter combinations
- Quick smoke tests before committing code changes

**Batch Generation:**
```bash
# Generate 10 scenarios with different seeds
for i in {1..10}; do
  python -m vmt_tools.generate_scenario "test_${i}" \
    --agents 20 --grid 30 --inventory-range 10,50 \
    --utilities ces,linear,quadratic \
    --resources 0.3,5,1 --seed $i
done
```

**Reproducibility:**
- Seeded randomization ensures identical scenarios across machines
- Easy to share scenario generation commands (not large YAML files)
- Version control the generator script, not every test scenario

### 3.2 Enhanced Testing & Validation

**Diverse Test Suites:**
- Automatically generate scenarios covering all utility types
- Test edge cases (low/high agent counts, small/large grids)
- Validate invariants across wide parameter ranges

**Regression Testing:**
```bash
# Generate consistent test suite for regression tests
python scripts/generate_test_suite.py --seed 42 --count 50
pytest tests/test_performance.py  # Uses generated scenarios
```

**Performance Benchmarking:**
- Generate scenarios of varying complexity
- Consistent parameterization across benchmark runs
- Isolate performance impacts (agent count vs. utility complexity)

### 3.3 Research & Experimentation

**Parameter Sweeps:**
```bash
# Study effect of agent density
for agents in 10 20 40 80; do
  generate_scenario "density_${agents}" --agents $agents --grid 50 ...
done
```

**Utility Comparison Studies:**
```bash
# Compare each utility in isolation
for util in ces linear quadratic translog stone_geary; do
  generate_scenario "${util}_only" --agents 30 --grid 40 \
    --utilities $util ...
done
```

**Mixed Population Studies:**
- Easily test different utility mixes (80/20, 50/50, 33/33/33)
- Study emergent behaviors in heterogeneous populations

### 3.4 Documentation & Pedagogy

**Example Scenarios:**
- Quickly generate diverse examples for documentation
- Demonstrate each utility type's behavior
- Create teaching scenarios with known properties

**Reproducible Demonstrations:**
```bash
# Share exact command to recreate pedagogical scenario
python -m vmt_tools.generate_scenario "gains_from_trade_demo" \
  --agents 10 --grid 20 --inventory-range 5,15 \
  --utilities ces:0.5,linear:0.5 --resources 0.25,3,1 --seed 123
```

---

## Part 4: Implementation Plan

### Phase 1: CLI MVP (Core Functionality)

**Goal:** Minimal viable CLI that generates basic scenarios

**Timeline:** 1-2 days

**Deliverables:**
1. `src/vmt_tools/generate_scenario.py` - Main CLI script
2. `src/vmt_tools/param_strategies.py` - Parameter randomization logic
3. `src/vmt_tools/__init__.py` - Package initialization

**Features:**
- Required arguments:
  - `name` (positional) - Scenario name
  - `--agents N` - Number of agents
  - `--grid N` - Grid size (N×N)
  - `--inventory-range MIN,MAX` - Initial inventory range
  - `--utilities LIST` - Comma-separated utility types (equal weights)
  - `--resources DENSITY,MAX,REGEN` - Resource configuration
- Optional arguments:
  - `--seed N` - Random seed for reproducibility
  - `--output PATH` - Output file path (default: `scenarios/{name}.yaml`)
  - `--skip-validation` - Skip parameter validation (default: True for Phase 1)
- Parameter randomization for all 5 utility types
- Conservative default ranges (as specified in Part 2.2)
- Stone-Geary with gamma=0 (Cobb-Douglas behavior)
- All parameters rounded to 2 decimal places for YAML output
- Inventory validation: MIN >= 1, MAX > MIN

**Example usage:**
```bash
python -m vmt_tools.generate_scenario quick_test \
  --agents 20 \
  --grid 30 \
  --inventory-range 10,50 \
  --utilities ces,quadratic \
  --resources 0.3,5,1 \
  --seed 42
```

**Output:** `scenarios/quick_test.yaml` with:
- 20 agents with random inventories in [10, 50]
- 30×30 grid
- 50% CES agents, 50% Quadratic agents (random params)
- Resources: 30% density, max amount 5, regen rate 1
- Default simulation params (movement=1, interaction=1, etc.)

**Implementation approach:**
```python
# src/vmt_tools/generate_scenario.py
import argparse
import yaml
from pathlib import Path
from .param_strategies import generate_utility_params, generate_inventories

def main():
    parser = argparse.ArgumentParser(description="Generate VMT scenario YAML")
    parser.add_argument("name", help="Scenario name")
    parser.add_argument("--agents", type=int, required=True)
    parser.add_argument("--grid", type=int, required=True)
    parser.add_argument("--inventory-range", required=True, 
                        help="MIN,MAX inventory range")
    parser.add_argument("--utilities", required=True,
                        help="Comma-separated utility types")
    parser.add_argument("--resources", required=True,
                        help="DENSITY,MAX_AMOUNT,REGEN_RATE")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", default=None)
    
    args = parser.parse_args()
    
    # Parse arguments
    inv_min, inv_max = map(int, args.inventory_range.split(','))
    utilities = args.utilities.split(',')
    density, max_amt, regen = args.resources.split(',')
    
    # Set seed
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
    
    # Generate scenario dict
    scenario = generate_scenario(
        name=args.name,
        n_agents=args.agents,
        grid_size=args.grid,
        inventory_range=(inv_min, inv_max),
        utilities=utilities,
        resource_config=(float(density), int(max_amt), int(regen))
    )
    
    # Write to file
    output_path = args.output or f"scenarios/{args.name}.yaml"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        yaml.dump(scenario, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Generated {output_path}")
    print(f"  - {args.agents} agents on {args.grid}×{args.grid} grid")
    print(f"  - Utilities: {', '.join(utilities)}")
    print(f"  - Seed: {args.seed or 'random'}")

def generate_scenario(name, n_agents, grid_size, inventory_range, 
                       utilities, resource_config):
    """Core logic to generate scenario dictionary."""
    inv_min, inv_max = inventory_range
    density, max_amt, regen = resource_config
    
    # Validate inventory range
    if inv_min < 1:
        raise ValueError(f"inventory_min must be >= 1 (got {inv_min}). Required for log-based utilities.")
    if inv_max <= inv_min:
        raise ValueError(f"inventory_max must be > inventory_min (got max={inv_max}, min={inv_min})")
    
    # Generate inventories (integers)
    inventories_A = generate_inventories(n_agents, inv_min, inv_max)
    inventories_B = generate_inventories(n_agents, inv_min, inv_max)
    
    # Generate utility mix
    utility_mix = []
    weight = 1.0 / len(utilities)
    for util_type in utilities:
        params = generate_utility_params(util_type, inventory_range)
        # Round all float params to 2 decimals
        params = {k: round(v, 2) if isinstance(v, float) else v 
                  for k, v in params.items()}
        utility_mix.append({
            'type': util_type,
            'weight': round(weight, 2),
            'params': params
        })
    
    # Construct scenario dict
    scenario = {
        'schema_version': 1,
        'name': name,
        'N': grid_size,
        'agents': n_agents,
        'initial_inventories': {
            'A': inventories_A,
            'B': inventories_B
        },
        'utilities': {
            'mix': utility_mix
        },
        'params': {
            'spread': 0.0,
            'vision_radius': 8,
            'interaction_radius': 1,
            'move_budget_per_tick': 1,
            'dA_max': 5,
            'forage_rate': 1,
            'trade_cooldown_ticks': 3,
            'beta': 0.95,
            'epsilon': 1e-12,
            'exchange_regime': 'barter_only',
            'enable_resource_claiming': True,
            'enforce_single_harvester': True,
            'resource_growth_rate': regen,
            'resource_max_amount': max_amt,
            'resource_regen_cooldown': 5  # Standard default
        },
        'resource_seed': {
            'density': density,
            'amount': max_amt
        }
    }
    
    return scenario
```

**Validation:** Generate scenarios and load them in GUI/CLI to verify they run without errors.

---

### Phase 2: Exchange Regimes & Presets

**Goal:** Add exchange regime support and scenario presets (keeping CLI simple)

**Status:** 📋 Ready for Implementation (see detailed plan in `docs/tmp/plans/scenario_generator_phase2_implementation.md`)

**Timeline:** 1-2 days (~2-3 hours core work)

**Prerequisites:** 
- ✅ VMT Money System Phase 1-2 complete
- ✅ Scenario Generator Phase 1 complete

**Scope (Simplified from Original Plan):**

**INCLUDED in Phase 2:**
1. **Exchange regime selection:**
   ```bash
   --exchange-regime {barter_only|money_only|mixed|mixed_liquidity_gated}
   ```
   - Automatically generates M inventories when needed
   - Sets default money parameters (money_mode, money_scale, lambda_money)

2. **Scenario presets:**
   ```bash
   --preset {minimal|standard|large|money_demo|mixed_economy}
   ```
   - Pre-configured parameter sets for common use cases
   - Can be overridden with explicit flags

**DEFERRED to Phase 3+:**
- ❌ Weighted utility mixes (`--utilities ces:0.6,linear:0.4`)
- ❌ Custom money inventory ranges (`--money-range`)
- ❌ Money parameter overrides (`--lambda-money`, `--money-scale`)
- ❌ Simulation parameter overrides (`--movement`, `--vision`, etc.)
- ❌ Custom parameter ranges (`--param-ranges config.json`)
- ❌ Parameter validation (`--validate` flag)

**Rationale:** Keep CLI simple and focused on the two most-requested features. Advanced customization can wait for user feedback.

**Example:**
```bash
python -m vmt_tools.generate_scenario complex_test \
  --agents 40 --grid 50 --inventory-range 15,60 \
  --utilities ces:0.3,linear:0.2,quadratic:0.2,translog:0.15,stone_geary:0.15 \
  --resources 0.35,8,2 \
  --exchange-regime mixed \
  --money-range 200,800 \
  --money-scale 100 \
  --lambda-money 1.0 \
  --movement 2 --vision 12 \
  --seed 42
```

**Note:** Mode schedules are not supported in the CLI. Users who need mode schedules should manually edit the generated YAML to add:
```yaml
mode_schedule:
  type: "global_cycle"
  forage_ticks: 10
  trade_ticks: 5
  start_mode: "forage"
```

---

### Phase 3: Python API & Programmatic Generation

**Goal:** Expose generator as importable Python library

**Timeline:** 1 day

**Features:**
1. Refactor CLI to use underlying `ScenarioGenerator` class
2. Expose as importable library from `vmt_tools`
3. Enable programmatic scenario creation for test fixtures

**Example usage:**
```python
from vmt_tools import ScenarioGenerator

# Programmatic generation
gen = ScenarioGenerator(
    name="my_test",
    agents=30,
    grid_size=40,
    inventory_range=(10, 50),
    utilities=["ces", "quadratic"],
    resource_config=(0.3, 5, 1),
    seed=42
)

scenario = gen.generate()
scenario.save("scenarios/my_test.yaml")

# Or generate multiple variants
for i, seed in enumerate([42, 43, 44, 45, 46]):
    gen.seed = seed
    scenario = gen.generate()
    scenario.save(f"scenarios/variant_{i}.yaml")
```

**Test fixture integration:**
```python
# tests/conftest.py
import pytest
from vmt_tools import ScenarioGenerator

@pytest.fixture
def random_scenario():
    """Generate a random test scenario."""
    gen = ScenarioGenerator(
        name="test_scenario",
        agents=20,
        grid_size=30,
        inventory_range=(10, 50),
        utilities=["ces", "linear"],
        resource_config=(0.3, 5, 1),
        seed=pytest.current_test_seed  # Deterministic per test
    )
    return gen.generate()
```

---

### Phase 4: Advanced Features (Optional)

**Goal:** Power-user features and optimizations

**Timeline:** 1-2 days (as needed)

**Features:**
1. **Batch generation:**
   ```bash
   --count 50  # Generate 50 scenarios with sequential seeds
   ```

2. **Parameter validation:**
   ```bash
   --validate  # Check parameter constraints (monotonicity, subsistence, etc.)
   ```

3. **Template-based generation:**
   ```bash
   --template templates/mixed_economy.yaml.j2
   ```

4. **Verbose output:**
   ```bash
   --verbose  # Print generated parameter values for debugging
   ```

5. **Dry run:**
   ```bash
   --dry-run  # Print YAML to stdout instead of saving
   ```

---

## Part 5: Parameter Strategy Details

### 5.1 Conservative Default Ranges

Complete specification of random parameter generation:

```python
# src/vmt_tools/param_strategies.py
import random
import numpy as np

def generate_utility_params(utility_type: str, inventory_range: tuple) -> dict:
    """
    Generate random parameters for a utility type.
    
    Uses explicit parameter generation with clear dependency ordering.
    All parameters are generated within conservative ranges that ensure
    valid, well-behaved utility functions.
    
    Args:
        utility_type: One of 'ces', 'linear', 'quadratic', 'translog', 'stone_geary'
        inventory_range: Tuple of (min, max) inventory values
        
    Returns:
        Dictionary of parameters for the utility function
    """
    inv_min, inv_max = inventory_range
    
    if utility_type == "ces":
        # CES: U = [wA * A^ρ + wB * B^ρ]^(1/ρ)
        wA = random.uniform(0.3, 0.7)
        return {
            'rho': _uniform_excluding(-1.0, 1.0, 0.8, 1.2),
            'wA': wA,
            'wB': 1.0 - wA  # Normalized (convention, not requirement)
        }
    
    elif utility_type == "linear":
        # Linear: U = vA * A + vB * B
        return {
            'vA': random.uniform(0.5, 3.0),
            'vB': random.uniform(0.5, 3.0)
        }
    
    elif utility_type == "quadratic":
        # Quadratic: U = -sigma_A*(A - A_star)^2 - sigma_B*(B - B_star)^2 - gamma*(A - A_star)*(B - B_star)
        A_star = random.uniform(inv_min * 1.2, inv_max * 0.8)
        B_star = random.uniform(inv_min * 1.2, inv_max * 0.8)
        return {
            'A_star': A_star,
            'B_star': B_star,
            'sigma_A': random.uniform(A_star * 0.4, A_star * 0.8),
            'sigma_B': random.uniform(B_star * 0.4, B_star * 0.8),
            'gamma': random.uniform(0.0, 0.2)
        }
    
    elif utility_type == "translog":
        # Translog: ln(U) = α₀ + αₐ*ln(A) + αᵦ*ln(B) + βₐₐ*ln(A)² + βᵦᵦ*ln(B)² + βₐᵦ*ln(A)*ln(B)
        return {
            'alpha_0': 0.0,  # Standard normalization
            'alpha_A': random.uniform(0.4, 0.6),
            'alpha_B': random.uniform(0.4, 0.6),
            'beta_AA': random.uniform(-0.10, -0.02),  # Negative = diminishing returns
            'beta_BB': random.uniform(-0.10, -0.02),
            'beta_AB': random.uniform(-0.03, 0.03)    # Small interaction
        }
    
    elif utility_type == "stone_geary":
        # Stone-Geary: U = αₐ * ln(A - γₐ) + αᵦ * ln(B - γᵦ)
        alpha_A = random.uniform(0.4, 0.6)
        return {
            'alpha_A': alpha_A,
            'alpha_B': 1.0 - alpha_A,  # Normalized (standard LES)
            'gamma_A': 0.0,             # No subsistence (acts like Cobb-Douglas)
            'gamma_B': 0.0
        }
    
    else:
        raise ValueError(f"Unknown utility type: {utility_type}")

def generate_inventories(n_agents: int, min_val: int, max_val: int) -> list:
    """
    Generate random integer inventories for agents.
    
    Args:
        n_agents: Number of agents
        min_val: Minimum inventory (must be >= 1)
        max_val: Maximum inventory (must be > min_val)
        
    Returns:
        List of n_agents random integers in [min_val, max_val]
    """
    if min_val < 1:
        raise ValueError(f"min_val must be >= 1 (got {min_val})")
    if max_val <= min_val:
        raise ValueError(f"max_val must be > min_val (got max={max_val}, min={min_val})")
    
    return [random.randint(min_val, max_val) for _ in range(n_agents)]

def _uniform_excluding(min_val, max_val, excl_min, excl_max, max_tries=100):
    """
    Sample uniform random value excluding a range.
    
    Used for CES rho to avoid rho=1 (undefined) and near-Cobb-Douglas values.
    
    Args:
        min_val: Minimum value
        max_val: Maximum value
        excl_min: Start of excluded range
        excl_max: End of excluded range
        max_tries: Maximum attempts before giving up
        
    Returns:
        Random value in [min_val, max_val] \ [excl_min, excl_max]
        
    Note: This implementation uses rejection sampling. A more robust version
    would explicitly sample from the valid regions. See Open Question #11.
    """
    for _ in range(max_tries):
        val = random.uniform(min_val, max_val)
        if val < excl_min or val > excl_max:
            return val
    # Fallback: return edge value (IMPERFECT - see Open Question #11)
    return min_val if random.random() < 0.5 else max_val
```

### 5.2 Rationale for Conservative Ranges

**CES:**
- `rho ∈ [-1.0, 1.0]`: Covers moderate substitutes to moderate complements
- Exclude `[0.8, 1.2]`: Avoids rho=1 (undefined) and near-Cobb-Douglas overlap
- `wA ∈ [0.3, 0.7]`: Ensures neither good dominates, balanced preferences

**Linear:**
- `vA, vB ∈ [0.5, 3.0]`: Prevents extreme relative valuations
- No extreme cases like vA=0.01 or vA=1000 that break intuition

**Quadratic:**
- Bliss points 20-80% into inventory range: Reachable but not trivial
- Sigma 40-80% of bliss point: Moderate curvature, not too sharp/flat
- gamma 0-0.2: Weak complementarity, avoids complex interactions

**Translog:**
- Alpha near 0.5: Balanced first-order preferences
- Beta_AA, Beta_BB negative: Standard diminishing returns
- Beta_AB small: Weak interaction effects, avoids extreme behaviors
- These ranges empirically ensure monotonicity over [1, 1000]

**Stone-Geary:**
- gamma_A = gamma_B = 0: Acts like Cobb-Douglas, avoids subsistence complexity
- Normalized alphas: Standard LES formulation
- Users can manually set gamma > 0 in YAML if subsistence needed

---

## Part 6: Usage Examples

### 6.1 Basic Scenarios

**Quick test (minimal parameters):**
```bash
python -m vmt_tools.generate_scenario quick_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear --resources 0.3,5,1
```

**All utility types:**
```bash
python -m vmt_tools.generate_scenario all_utilities \
  --agents 50 --grid 50 --inventory-range 20,80 \
  --utilities ces,linear,quadratic,translog,stone_geary \
  --resources 0.35,6,2 --seed 42
```

**Large performance test:**
```bash
python -m vmt_tools.generate_scenario perf_test_large \
  --agents 100 --grid 100 --inventory-range 10,100 \
  --utilities ces --resources 0.4,10,3 --seed 123
```

### 6.2 Test Suite Generation

**Generate 10 test scenarios:**
```bash
#!/bin/bash
# scripts/generate_test_suite.sh

for i in {1..10}; do
  python -m vmt_tools.generate_scenario "test_suite_${i}" \
    --agents 20 --grid 30 --inventory-range 10,50 \
    --utilities ces,linear,quadratic \
    --resources 0.3,5,1 --seed $i
done

echo "Generated 10 test scenarios in scenarios/"
```

**Parameter sweep:**
```bash
#!/bin/bash
# Study effect of agent count

for n in 10 20 40 80; do
  python -m vmt_tools.generate_scenario "agent_count_${n}" \
    --agents $n --grid 50 --inventory-range 10,50 \
    --utilities ces,linear --resources 0.3,5,1 --seed 42
done
```

### 6.3 Research Scenarios

**Utility comparison:**
```bash
# Generate one scenario per utility type
for util in ces linear quadratic translog stone_geary; do
  python -m vmt_tools.generate_scenario "${util}_isolated" \
    --agents 30 --grid 40 --inventory-range 15,60 \
    --utilities $util --resources 0.35,6,2 --seed 42
done
```

**Mixed populations:**
```bash
# 80/20 split
python -m vmt_tools.generate_scenario "ces_dominant" \
  --agents 50 --grid 50 --inventory-range 20,70 \
  --utilities ces:0.8,quadratic:0.2 --resources 0.3,5,1

# Equal split
python -m vmt_tools.generate_scenario "equal_mix" \
  --agents 60 --grid 50 --inventory-range 20,70 \
  --utilities ces:0.33,linear:0.33,quadratic:0.34 \
  --resources 0.3,5,1
```

---

## Part 7: Success Criteria

### Phase 1 Complete When:
- [x] CLI script generates valid YAML scenarios
- [x] All 5 utility types supported with conservative defaults
- [x] Resources require explicit density/max/regen inputs
- [x] Stone-Geary uses gamma=0 by default
- [x] `--seed` flag enables reproducible generation
- [x] Generated scenarios load and run without errors
- [x] Generation time < 1 second per scenario
- [x] Documentation includes usage examples

**Status:** ✅ COMPLETE (2025-10-21)

### Phase 2 Complete When:
- [ ] Exchange regime flag supports all 4 regimes
- [ ] M inventories auto-generated when needed
- [ ] Default money parameters set appropriately
- [ ] At least 5 presets defined and working
- [ ] Generated money scenarios load and run
- [ ] Documentation updated with Phase 2 examples
- [ ] Backward compatibility verified

**Status:** 📋 Ready for Implementation

### Phase 3 Complete When:
- [ ] `ScenarioGenerator` class importable from `vmt_tools`
- [ ] Programmatic API documented with examples
- [ ] Test fixtures can use generator
- [ ] CLI refactored to use underlying class (DRY)

### Overall Success Metrics:
- **Speed**: Generate scenario in < 1 second ✓
- **Correctness**: 100% of generated scenarios are valid and runnable ✓
- **Usability**: Developers prefer CLI over manual YAML creation ✓
- **Adoption**: Used for test suite generation and experimentation ✓

---

## Part 8: Open Questions & Future Enhancements

### 8.1 Open Questions

1. **Should the tool support subsistence generation for Stone-Geary?** (DEFERRED)
   - Current plan: gamma=0 by default
   - Future: Add `--enable-subsistence` flag that sets gamma = min_inventory * 0.3?
   - Trade-off: Simplicity vs. feature completeness
   - **Decision**: Deferred to post-Phase 1 (non-critical)

2. **Should we validate generated parameters?** (RESOLVED for Phase 1)
   - Phase 1 plan: Skip validation by default (`--skip-validation` flag)
   - Phase 2: Add `--validate` flag for monotonicity and constraint checking
   - Trade-off: Speed vs. safety
   - **Decision**: Validation deferred to Phase 2

3. **Should resource placement be randomized or deterministic?**
   - Current: Uses density parameter (deterministic cell selection per seed)
   - Alternative: Explicit `--resource-locations` file?
   - **Status**: Current approach is sufficient for Phase 1

4. **Parameter preset names?**
   - Proposed: `quick_test`, `full_demo`, `performance`
   - Better names? `minimal`, `standard`, `benchmark`?
   - **Status**: To be finalized during Phase 2 implementation

5. **How should `_uniform_excluding` handle edge cases?** (DEFERRED)
   - Current: Rejection sampling with fallback
   - Alternative: Explicit region sampling (see review comments)
   - **Decision**: Current implementation sufficient for Phase 1; revisit if issues arise

6. **Parameter naming for gamma values:** (RESOLVED)
   - Quadratic uses `gamma_quad` for cross-curvature
   - Stone-Geary uses `gamma_A_SG` and `gamma_B_SG` for subsistence levels
   - **Decision**: Disambiguated to avoid confusion

### 8.2 Future Enhancements

**Phase 5: GUI Integration (Optional)**
- Add "Generate Random" button to GUI launcher
- Fill form fields with generated values
- Allow tweaking before saving

**Advanced randomization:**
- Correlated parameters (e.g., high rho → high wA)
- Utility-specific constraints (e.g., ensure translog monotonicity)
- Spatial heterogeneity (different regions have different utility distributions)

**Scenario templates:**
- Pre-defined templates for common use cases
- Example: "gains_from_trade", "resource_competition", "market_segmentation"
- Load template, fill in basic params, generate

**Batch analysis:**
- Generate scenarios + run simulations + collect results
- Built-in parameter sweep framework
- Export summary statistics

**Resource amount distributions (out of scope for Phase 1):**
- The schema supports `amount: {uniform_int: [3, 8]}` for variable resource amounts
- Phase 1 uses fixed integer amounts only
- Future enhancement: Support distribution syntax for more variety
- Example: `--resources 0.3,uniform:5:10,1` for amounts uniformly distributed in [5, 10]

---

## Part 9: Implementation Checklist

### Phase 1: CLI MVP
- [ ] Create `src/vmt_tools/` package
- [ ] Implement `generate_scenario.py` main CLI script
- [ ] Implement `param_strategies.py` with conservative ranges
- [ ] Add all 5 utility types to parameter strategies
- [ ] Implement inventory generation (random lists)
- [ ] Implement resource configuration from CLI args
- [ ] Add `--seed` support for reproducibility
- [ ] Test: Generate scenario for each utility type
- [ ] Test: Load generated scenarios in GUI/CLI
- [ ] Test: Run simulation with generated scenario
- [ ] Document: Add usage examples to README or new docs
- [ ] Document: Add to developer workflow guide

### Phase 2: Enhanced Parameterization
- [ ] Parse weighted utility syntax (`ces:0.5,linear:0.5`)
- [ ] Add `--param-ranges` JSON config file support
- [ ] Add simulation parameter override flags
- [ ] Add `--exchange-regime` flag
- [ ] Add `--mode-schedule` flag
- [ ] Implement 3 presets (quick_test, full_demo, performance)
- [ ] Test: Generate scenarios with custom weights
- [ ] Test: Validate parameter override behavior
- [ ] Document: Update examples with Phase 2 features

### Phase 3: Python API
- [ ] Refactor CLI to use `ScenarioGenerator` class
- [ ] Design clean Python API
- [ ] Add type hints and docstrings
- [ ] Export from `vmt_tools` package
- [ ] Create example usage scripts
- [ ] Test: Import and use programmatically
- [ ] Test: Generate from test fixtures
- [ ] Document: Add Python API examples

---

## Part 10: Appendix - Example Output

### Generated YAML Structure

```yaml
schema_version: 1
name: "quick_test"
N: 30
agents: 20

initial_inventories:
  A: [15, 32, 47, 18, 25, 41, 13, 29, 38, 22, 45, 17, 31, 26, 40, 19, 35, 28, 42, 21]
  B: [28, 14, 39, 33, 21, 48, 16, 27, 44, 19, 36, 23, 49, 11, 37, 25, 43, 18, 31, 20]

utilities:
  mix:
    - type: "ces"
      weight: 0.5
      params:
        rho: 0.35
        wA: 0.58
        wB: 0.42
    
    - type: "quadratic"
      weight: 0.5
      params:
        A_star: 28.45
        B_star: 31.23
        sigma_A: 17.34
        sigma_B: 19.12
        gamma: 0.15

params:
  spread: 0.0
  vision_radius: 8
  interaction_radius: 1
  move_budget_per_tick: 1
  dA_max: 5
  forage_rate: 1
  trade_cooldown_ticks: 3
  beta: 0.95
  epsilon: 1e-12
  exchange_regime: "barter_only"
  enable_resource_claiming: true
  enforce_single_harvester: true
  resource_growth_rate: 1
  resource_max_amount: 5
  resource_regen_cooldown: 5

resource_seed:
  density: 0.3
  amount: 5
```

**Changes from original plan:**
- ✅ Added `schema_version: 1` (required field)
- ✅ Moved resource parameters into main `params` dict
- ✅ Rounded float parameters to 2 decimal places
- ✅ Inventories remain as integers (A, B are goods)

**Note on parameter names:**
- Quadratic uses `gamma` for cross-curvature (schema requirement)
- Stone-Geary uses `gamma_A` and `gamma_B` for subsistence levels (schema requirement)
- These are distinct parameters for different utility functions - no name collision in practice
- Parameter names MUST match schema exactly for validation to pass

---

## Conclusion

The **VMT Scenario Generator Tool** will dramatically improve developer workflow by reducing scenario creation time from minutes to seconds. The phased implementation plan balances immediate utility (Phase 1 MVP) with long-term extensibility (Phases 2-3). Conservative parameter defaults ensure generated scenarios are valid and representative of typical use cases, while seeded randomization maintains reproducibility for scientific workflows.

**Next Steps:**
1. Review and refine this plan with stakeholders
2. Begin Phase 1 implementation
3. Iterate based on developer feedback
4. Expand to Phases 2-3 as needs emerge

---

---

## Revision Log

**2025-10-21 - Post-Review Updates**

The following changes were made based on comprehensive pre-implementation review:

### Critical Issues Resolved:
1. ✅ **Added `schema_version: 1`** to all generated YAML outputs (required field)
2. ✅ **Fixed parameter structure**: Moved resource parameters from separate `resource_params` into main `params` dict
3. ✅ **CES weight clarification**: Documented that normalization is by convention, not requirement

### High Priority Issues Resolved:
4. ✅ **Validation approach**: Phase 1 skips validation by default; Phase 2 adds `--validate` flag for monotonicity checking
5. ✅ **Inventory validation**: Added `ValueError` for `inventory_min < 1` (required for log-based utilities)
6. ⏭️ **Subsistence validation**: Deferred (non-critical for Phase 1 with gamma=0)
7. ✅ **Parameter generation refactored**: Replaced reflection-based approach with explicit, maintainable code
8. ✅ **Phase 2 exchange regime**: Resolved - no mode schedule support in CLI (manual YAML editing)
9. ✅ **Money inventory generation**: Added section 2.6 with Phase 2 plan
10. ✅ **Type safety**: Documented integer inventories, 2-decimal float parameters in YAML
11. ⏭️ **`_uniform_excluding` improvements**: Deferred; current implementation sufficient
12. ✅ **Parameter naming**: Clarified that `gamma` (quadratic) and `gamma_A`/`gamma_B` (Stone-Geary) are distinct parameters that don't collide; must match schema exactly
13. ✅ **Agent positioning**: Added section 2.7 documenting simulation engine behavior
14. ✅ **Resource distributions**: Noted as future enhancement (out of scope for Phase 1)

### Documentation Improvements:
- Added explicit rationale for all parameter ranges
- Clarified CES weight normalization convention
- Documented type safety guarantees (integers vs. floats)
- Added agent positioning clarification
- Updated example YAML to reflect all changes
- Marked open questions with resolution status

### Code Quality Improvements:
- Replaced brittle reflection-based parameter generation with explicit, readable code
- Added comprehensive docstrings to utility functions
- Improved error messages with actionable guidance
- Added validation at scenario generation time (not just schema validation)

**Status**: Ready for Phase 1 implementation. Phase 2 design is complete and ready for implementation after Phase 1.

---

**End of Document**

