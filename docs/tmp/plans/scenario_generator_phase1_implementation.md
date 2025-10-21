# VMT Scenario Generator - Phase 1 Implementation Plan

**Date:** 2025-10-21  
**Status:** Ready for Implementation  
**Phase:** Phase 1 - CLI MVP  
**Estimated Time:** 1-2 days  
**Target:** Minimal viable CLI that generates valid, schema-compliant scenario YAML files

---

## Overview

This plan details the step-by-step implementation of Phase 1 of the VMT Scenario Generator tool. The goal is to create a working CLI that can generate valid scenario YAML files for all 5 utility types with conservative parameter defaults.

---

## Pre-Implementation Checklist

- [ ] Review the full scenario generator plan (`docs/tmp/scenario_generator_tool_plan.md`)
- [ ] Understand the schema requirements (`src/scenarios/schema.py`)
- [ ] Have example scenarios available for reference (`scenarios/*.yaml`)
- [ ] Workspace is on a clean git branch
- [ ] Python environment is activated

---

## Implementation Steps

### Step 1: Create Package Structure

**Goal:** Set up the basic package structure for `vmt_tools`

**Tasks:**
1. Create directory structure:
   ```bash
   mkdir -p src/vmt_tools
   ```

2. Create `src/vmt_tools/__init__.py`:
   ```python
   """
   VMT Tools - Developer utilities for the VMT simulation.
   
   This package contains tools for generating, manipulating, and analyzing
   VMT scenario files and simulation data.
   """
   
   __version__ = "0.1.0"
   
   # Future: Export main API components
   # from .param_strategies import generate_utility_params, generate_inventories
   ```

**Validation:**
- [ ] Directory exists: `src/vmt_tools/`
- [ ] File exists: `src/vmt_tools/__init__.py`
- [ ] Can import: `python -c "import src.vmt_tools"`

**Estimated time:** 5 minutes

---

### Step 2: Implement Parameter Generation Module

**Goal:** Create the core parameter randomization logic

**Tasks:**

1. Create `src/vmt_tools/param_strategies.py` with the following structure:

```python
"""
Parameter generation strategies for VMT scenario files.

This module provides functions to generate random but valid parameters for
all supported utility functions. Parameters are generated within conservative
ranges that ensure well-behaved utility functions.
"""

import random
from typing import Tuple, List, Dict


def generate_utility_params(utility_type: str, inventory_range: Tuple[int, int]) -> Dict[str, float]:
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
        
    Raises:
        ValueError: If utility_type is unknown
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


def generate_inventories(n_agents: int, min_val: int, max_val: int) -> List[int]:
    """
    Generate random integer inventories for agents.
    
    Args:
        n_agents: Number of agents
        min_val: Minimum inventory (must be >= 1)
        max_val: Maximum inventory (must be > min_val)
        
    Returns:
        List of n_agents random integers in [min_val, max_val]
        
    Raises:
        ValueError: If min_val < 1 or max_val <= min_val
    """
    if min_val < 1:
        raise ValueError(f"min_val must be >= 1 (got {min_val})")
    if max_val <= min_val:
        raise ValueError(f"max_val must be > min_val (got max={max_val}, min={min_val})")
    
    return [random.randint(min_val, max_val) for _ in range(n_agents)]


def _uniform_excluding(min_val: float, max_val: float, excl_min: float, excl_max: float, max_tries: int = 100) -> float:
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
    would explicitly sample from the valid regions.
    """
    for _ in range(max_tries):
        val = random.uniform(min_val, max_val)
        if val < excl_min or val > excl_max:
            return val
    # Fallback: return edge value
    return min_val if random.random() < 0.5 else max_val
```

**Validation:**
- [ ] File created: `src/vmt_tools/param_strategies.py`
- [ ] Test each utility type manually:
  ```python
  from src.vmt_tools.param_strategies import generate_utility_params
  params = generate_utility_params("ces", (10, 50))
  print(params)  # Should have rho, wA, wB
  ```
- [ ] Test inventory generation:
  ```python
  from src.vmt_tools.param_strategies import generate_inventories
  inv = generate_inventories(10, 10, 50)
  print(inv)  # Should be 10 integers in [10, 50]
  ```
- [ ] Test error handling:
  ```python
  generate_utility_params("invalid", (10, 50))  # Should raise ValueError
  generate_inventories(10, 0, 50)  # Should raise ValueError
  ```

**Estimated time:** 30 minutes

---

### Step 3: Implement Core Scenario Generation Logic

**Goal:** Create the function that assembles scenario dictionaries

**Tasks:**

1. Create `src/vmt_tools/scenario_builder.py`:

```python
"""
Core scenario generation logic.

This module contains functions to build complete scenario dictionaries
from input parameters and random generation strategies.
"""

from typing import Tuple, List, Dict, Any
from .param_strategies import generate_utility_params, generate_inventories


def generate_scenario(
    name: str,
    n_agents: int,
    grid_size: int,
    inventory_range: Tuple[int, int],
    utilities: List[str],
    resource_config: Tuple[float, int, int]
) -> Dict[str, Any]:
    """
    Generate a complete scenario dictionary.
    
    Args:
        name: Scenario name
        n_agents: Number of agents
        grid_size: Grid size (NxN)
        inventory_range: (min, max) for initial inventories
        utilities: List of utility type names
        resource_config: (density, max_amount, regen_rate)
        
    Returns:
        Complete scenario dictionary ready for YAML serialization
        
    Raises:
        ValueError: If parameters are invalid
    """
    inv_min, inv_max = inventory_range
    density, max_amt, regen = resource_config
    
    # Validate inventory range
    if inv_min < 1:
        raise ValueError(
            f"inventory_min must be >= 1 (got {inv_min}). "
            f"Required for log-based utilities (Translog, Stone-Geary)."
        )
    if inv_max <= inv_min:
        raise ValueError(
            f"inventory_max must be > inventory_min "
            f"(got max={inv_max}, min={inv_min})"
        )
    
    # Validate utilities
    if not utilities:
        raise ValueError("At least one utility type must be specified")
    
    valid_utilities = {'ces', 'linear', 'quadratic', 'translog', 'stone_geary'}
    for util in utilities:
        if util not in valid_utilities:
            raise ValueError(
                f"Unknown utility type: {util}. "
                f"Valid types: {', '.join(sorted(valid_utilities))}"
            )
    
    # Generate inventories (integers)
    inventories_A = generate_inventories(n_agents, inv_min, inv_max)
    inventories_B = generate_inventories(n_agents, inv_min, inv_max)
    
    # Generate utility mix
    utility_mix = []
    weight = 1.0 / len(utilities)
    for util_type in utilities:
        params = generate_utility_params(util_type, inventory_range)
        # Round all float params to 2 decimals for YAML output
        params = {
            k: round(v, 2) if isinstance(v, float) else v
            for k, v in params.items()
        }
        utility_mix.append({
            'type': util_type,
            'weight': round(weight, 2),
            'params': params
        })
    
    # Construct scenario dict (schema-compliant)
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
            'resource_regen_cooldown': 5
        },
        'resource_seed': {
            'density': density,
            'amount': max_amt
        }
    }
    
    return scenario
```

**Validation:**
- [ ] File created: `src/vmt_tools/scenario_builder.py`
- [ ] Test scenario generation:
  ```python
  from src.vmt_tools.scenario_builder import generate_scenario
  import random
  random.seed(42)
  scenario = generate_scenario(
      name="test",
      n_agents=10,
      grid_size=20,
      inventory_range=(10, 50),
      utilities=["ces", "linear"],
      resource_config=(0.3, 5, 1)
  )
  print(scenario.keys())  # Should have all required fields
  ```
- [ ] Verify schema compliance (manual check against schema.py)

**Estimated time:** 30 minutes

---

### Step 4: Implement CLI Interface

**Goal:** Create the main CLI entry point

**Tasks:**

1. Create `src/vmt_tools/generate_scenario.py`:

```python
"""
CLI tool for generating VMT scenario YAML files.

Usage:
    python -m vmt_tools.generate_scenario NAME --agents N --grid N 
           --inventory-range MIN,MAX --utilities LIST --resources DENSITY,MAX,REGEN
           [--seed SEED] [--output PATH]
"""

import argparse
import random
import sys
from pathlib import Path
from typing import Optional

import yaml

from .scenario_builder import generate_scenario


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for scenario generation CLI.
    
    Args:
        argv: Command-line arguments (for testing)
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Generate VMT scenario YAML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a simple test scenario
  %(prog)s quick_test --agents 20 --grid 30 --inventory-range 10,50 \\
    --utilities ces,linear --resources 0.3,5,1 --seed 42
  
  # Generate with all utility types
  %(prog)s full_demo --agents 50 --grid 50 --inventory-range 20,80 \\
    --utilities ces,linear,quadratic,translog,stone_geary \\
    --resources 0.35,6,2 --seed 123
"""
    )
    
    # Positional arguments
    parser.add_argument(
        "name",
        help="Scenario name (used in YAML and default filename)"
    )
    
    # Required arguments
    parser.add_argument(
        "--agents",
        type=int,
        required=True,
        help="Number of agents"
    )
    parser.add_argument(
        "--grid",
        type=int,
        required=True,
        help="Grid size (NxN)"
    )
    parser.add_argument(
        "--inventory-range",
        required=True,
        help="Initial inventory range as MIN,MAX (e.g., 10,50)"
    )
    parser.add_argument(
        "--utilities",
        required=True,
        help="Comma-separated utility types (ces, linear, quadratic, translog, stone_geary)"
    )
    parser.add_argument(
        "--resources",
        required=True,
        help="Resource configuration as DENSITY,MAX_AMOUNT,REGEN_RATE (e.g., 0.3,5,1)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: random)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: scenarios/{name}.yaml)"
    )
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    try:
        # Parse inventory range
        try:
            inv_parts = args.inventory_range.split(',')
            if len(inv_parts) != 2:
                raise ValueError("Expected format: MIN,MAX")
            inv_min, inv_max = int(inv_parts[0]), int(inv_parts[1])
        except ValueError as e:
            print(f"Error parsing --inventory-range: {e}", file=sys.stderr)
            print(f"Got: {args.inventory_range}", file=sys.stderr)
            print(f"Expected format: MIN,MAX (e.g., 10,50)", file=sys.stderr)
            return 1
        
        # Parse utilities
        utilities = [u.strip() for u in args.utilities.split(',')]
        
        # Parse resources
        try:
            res_parts = args.resources.split(',')
            if len(res_parts) != 3:
                raise ValueError("Expected format: DENSITY,MAX,REGEN")
            density = float(res_parts[0])
            max_amt = int(res_parts[1])
            regen = int(res_parts[2])
        except ValueError as e:
            print(f"Error parsing --resources: {e}", file=sys.stderr)
            print(f"Got: {args.resources}", file=sys.stderr)
            print(f"Expected format: DENSITY,MAX,REGEN (e.g., 0.3,5,1)", file=sys.stderr)
            return 1
        
        # Set random seed if provided
        if args.seed is not None:
            random.seed(args.seed)
        
        # Generate scenario
        scenario = generate_scenario(
            name=args.name,
            n_agents=args.agents,
            grid_size=args.grid,
            inventory_range=(inv_min, inv_max),
            utilities=utilities,
            resource_config=(density, max_amt, regen)
        )
        
        # Determine output path
        output_path = args.output or f"scenarios/{args.name}.yaml"
        output_file = Path(output_path)
        
        # Create parent directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write YAML file
        with open(output_file, 'w') as f:
            yaml.dump(
                scenario,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )
        
        # Success message
        print(f"✓ Generated {output_path}")
        print(f"  - {args.agents} agents on {args.grid}×{args.grid} grid")
        print(f"  - Utilities: {', '.join(utilities)}")
        print(f"  - Inventory range: [{inv_min}, {inv_max}]")
        print(f"  - Resources: density={density}, max={max_amt}, regen={regen}")
        print(f"  - Seed: {args.seed or 'random'}")
        
        return 0
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

2. Update `src/vmt_tools/__init__.py` to add CLI entry point:

```python
"""
VMT Tools - Developer utilities for the VMT simulation.

This package contains tools for generating, manipulating, and analyzing
VMT scenario files and simulation data.
"""

__version__ = "0.1.0"

# Export main API components
from .param_strategies import generate_utility_params, generate_inventories
from .scenario_builder import generate_scenario

__all__ = [
    'generate_utility_params',
    'generate_inventories',
    'generate_scenario',
]
```

3. Make the module runnable:
   ```bash
   # Test that it works
   python -m src.vmt_tools.generate_scenario --help
   ```

**Validation:**
- [ ] File created: `src/vmt_tools/generate_scenario.py`
- [ ] `__init__.py` updated with exports
- [ ] Can run `python -m src.vmt_tools.generate_scenario --help`
- [ ] Help message displays correctly
- [ ] All required arguments listed

**Estimated time:** 45 minutes

---

### Step 5: Test Scenario Generation

**Goal:** Verify that generated scenarios are valid and loadable

**Tasks:**

1. Generate test scenarios for each utility type:

```bash
# CES
python -m src.vmt_tools.generate_scenario test_ces \
  --agents 10 --grid 20 --inventory-range 10,50 \
  --utilities ces --resources 0.3,5,1 --seed 42

# Linear
python -m src.vmt_tools.generate_scenario test_linear \
  --agents 10 --grid 20 --inventory-range 10,50 \
  --utilities linear --resources 0.3,5,1 --seed 42

# Quadratic
python -m src.vmt_tools.generate_scenario test_quadratic \
  --agents 10 --grid 20 --inventory-range 10,50 \
  --utilities quadratic --resources 0.3,5,1 --seed 42

# Translog
python -m src.vmt_tools.generate_scenario test_translog \
  --agents 10 --grid 20 --inventory-range 10,50 \
  --utilities translog --resources 0.3,5,1 --seed 42

# Stone-Geary
python -m src.vmt_tools.generate_scenario test_stone_geary \
  --agents 10 --grid 20 --inventory-range 10,50 \
  --utilities stone_geary --resources 0.3,5,1 --seed 42

# Mixed
python -m src.vmt_tools.generate_scenario test_mixed \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear,quadratic --resources 0.3,5,1 --seed 42
```

2. Verify schema compliance:

```python
# Test that scenarios load correctly
from src.scenarios.loader import load_scenario

# Test each generated scenario
for name in ['test_ces', 'test_linear', 'test_quadratic', 'test_translog', 'test_stone_geary', 'test_mixed']:
    try:
        scenario = load_scenario(f"scenarios/{name}.yaml")
        print(f"✓ {name}: Valid")
    except Exception as e:
        print(f"✗ {name}: {e}")
```

3. Verify YAML structure manually:
   - Open one generated YAML file
   - Check that `schema_version: 1` is present
   - Check that resource params are in `params` dict (not separate)
   - Check that parameter names match schema (e.g., `gamma` not `gamma_quad`)
   - Check that float values are rounded to 2 decimals

4. Test edge cases:

```bash
# Invalid inventory range (min < 1)
python -m src.vmt_tools.generate_scenario test_invalid1 \
  --agents 10 --grid 20 --inventory-range 0,50 \
  --utilities ces --resources 0.3,5,1
# Should fail with clear error message

# Invalid inventory range (max <= min)
python -m src.vmt_tools.generate_scenario test_invalid2 \
  --agents 10 --grid 20 --inventory-range 50,10 \
  --utilities ces --resources 0.3,5,1
# Should fail with clear error message

# Unknown utility type
python -m src.vmt_tools.generate_scenario test_invalid3 \
  --agents 10 --grid 20 --inventory-range 10,50 \
  --utilities invalid_type --resources 0.3,5,1
# Should fail with clear error message
```

**Validation:**
- [ ] All 5 utility types generate successfully
- [ ] Mixed utility scenario generates successfully
- [ ] All generated scenarios pass schema validation
- [ ] YAML files have correct structure
- [ ] Float values are rounded to 2 decimals
- [ ] Integer inventories remain integers
- [ ] Error cases produce clear error messages
- [ ] Same seed produces identical outputs (determinism)

**Estimated time:** 30 minutes

---

### Step 6: Run Integration Test

**Goal:** Verify generated scenarios work in full simulation

**Tasks:**

1. Create a simple integration test script `test_generated_scenarios.py`:

```python
"""
Integration test for generated scenarios.

Tests that generated scenarios can be loaded and run without errors.
"""

import sys
import subprocess
from pathlib import Path

# Test scenarios
test_cases = [
    'test_ces',
    'test_linear',
    'test_quadratic',
    'test_translog',
    'test_stone_geary',
    'test_mixed'
]

print("Testing scenario loading and validation...")
for name in test_cases:
    path = f"scenarios/{name}.yaml"
    if not Path(path).exists():
        print(f"✗ {name}: File not found")
        continue
    
    try:
        # Load with schema validation
        from src.scenarios.loader import load_scenario
        scenario = load_scenario(path)
        print(f"✓ {name}: Loads and validates")
    except Exception as e:
        print(f"✗ {name}: {e}")
        sys.exit(1)

print("\nAll scenarios loaded successfully!")
print("\nNote: Full simulation test requires GUI/CLI - run manually if needed:")
for name in test_cases:
    print(f"  python -m src.vmt_launcher scenarios/{name}.yaml")
```

2. Run the test:
   ```bash
   python test_generated_scenarios.py
   ```

3. (Optional) Run a brief simulation with one of the generated scenarios:
   ```bash
   # Use the launcher to run a short simulation
   python -m src.vmt_launcher scenarios/test_mixed.yaml
   ```

**Validation:**
- [ ] All test scenarios load without errors
- [ ] (Optional) At least one scenario runs in simulation without errors
- [ ] No schema validation errors
- [ ] No runtime errors

**Estimated time:** 15 minutes

---

### Step 7: Add Basic Documentation

**Goal:** Document usage and API

**Tasks:**

1. Create `src/vmt_tools/README.md`:

```markdown
# VMT Tools

Developer utilities for the VMT simulation project.

## Scenario Generator

Generate random but valid scenario YAML files for testing and experimentation.

### Quick Start

```bash
python -m src.vmt_tools.generate_scenario my_test \
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
python -m src.vmt_tools.generate_scenario ces_only \
  --agents 30 --grid 40 --inventory-range 15,60 \
  --utilities ces --resources 0.35,6,2
```

**Multiple utility types (equal weights):**
```bash
python -m src.vmt_tools.generate_scenario mixed \
  --agents 50 --grid 50 --inventory-range 20,80 \
  --utilities ces,linear,quadratic,translog,stone_geary \
  --resources 0.4,8,3
```

**With reproducible seed:**
```bash
python -m src.vmt_tools.generate_scenario reproducible \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear --resources 0.3,5,1 --seed 42
```

**Custom output path:**
```bash
python -m src.vmt_tools.generate_scenario my_test \
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
  python -m src.vmt_tools.generate_scenario "test_${util}" \
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

See `docs/tmp/scenario_generator_tool_plan.md` for full roadmap.
```

2. Update main project documentation (if applicable)

**Validation:**
- [ ] README created with usage examples
- [ ] Examples are copy-pasteable and work
- [ ] API usage documented

**Estimated time:** 20 minutes

---

### Step 8: Clean Up and Final Testing

**Goal:** Ensure code quality and remove test artifacts

**Tasks:**

1. Clean up any test files:
   ```bash
   # Remove test scenarios (optional - keep for manual testing)
   rm scenarios/test_*.yaml
   ```

2. Run linter (if available):
   ```bash
   # If using pylint/flake8
   pylint src/vmt_tools/*.py
   ```

3. Check imports and dependencies:
   ```python
   # Verify all imports work
   from src.vmt_tools import generate_scenario, generate_utility_params, generate_inventories
   ```

4. Run final integration test:
   ```bash
   # Generate a comprehensive test scenario
   python -m src.vmt_tools.generate_scenario phase1_complete \
     --agents 30 --grid 40 --inventory-range 15,60 \
     --utilities ces,linear,quadratic,translog,stone_geary \
     --resources 0.35,6,2 --seed 42
   
   # Verify it loads
   python -c "from src.scenarios.loader import load_scenario; load_scenario('scenarios/phase1_complete.yaml'); print('✓ Success')"
   ```

**Validation:**
- [ ] No linter errors (or documented exceptions)
- [ ] All imports work
- [ ] Final test scenario generates and loads successfully
- [ ] Code is clean and commented

**Estimated time:** 15 minutes

---

## Post-Implementation Checklist

- [ ] All 3 modules created (`__init__.py`, `param_strategies.py`, `scenario_builder.py`, `generate_scenario.py`)
- [ ] CLI works and displays help correctly
- [ ] All 5 utility types generate valid scenarios
- [ ] Mixed utility scenarios work
- [ ] Generated scenarios pass schema validation
- [ ] Generated scenarios can be loaded by `src.scenarios.loader`
- [ ] Error handling works (invalid inputs produce clear messages)
- [ ] Seeded randomization is deterministic
- [ ] Documentation is complete
- [ ] Integration test passes

---

## Success Criteria

Phase 1 is complete when:

1. ✅ CLI generates valid YAML scenarios
2. ✅ All 5 utility types supported with conservative defaults
3. ✅ Resources require explicit density/max/regen inputs
4. ✅ Stone-Geary uses gamma=0 by default
5. ✅ `--seed` flag enables reproducible generation
6. ✅ Generated scenarios load and run without errors
7. ✅ Generation time < 1 second per scenario
8. ✅ Documentation includes usage examples

---

## Troubleshooting

### Common Issues

**Issue: "Module not found" when running CLI**
```bash
# Make sure you're in project root
cd /home/chris/PROJECTS/vmt-dev

# Try running with full module path
python -m src.vmt_tools.generate_scenario --help
```

**Issue: Schema validation fails**
- Check that `schema_version: 1` is present
- Verify parameter names match schema exactly
- Ensure resource params are in main `params` dict

**Issue: Generated parameters are extreme/invalid**
- Check that inventory range is reasonable (e.g., 10-50, not 1-1000)
- Verify utility parameter ranges in `param_strategies.py`

**Issue: Scenarios fail in simulation**
- Load scenario with schema loader first to catch validation errors
- Check that all required fields are present
- Verify that default params match schema defaults

---

## Next Steps After Phase 1

Once Phase 1 is complete and tested:

1. **Create unit tests** (optional but recommended):
   - Test parameter generation for each utility type
   - Test inventory generation
   - Test scenario building
   - Test CLI argument parsing

2. **Begin Phase 2** (Enhanced Parameterization):
   - Weighted utility mixes
   - Money support
   - Parameter validation
   - Presets

3. **Gather feedback**:
   - Use the tool to generate diverse scenarios
   - Identify pain points or missing features
   - Refine parameter ranges based on usage

---

## Estimated Total Time

- Step 1: 5 minutes
- Step 2: 30 minutes
- Step 3: 30 minutes
- Step 4: 45 minutes
- Step 5: 30 minutes
- Step 6: 15 minutes
- Step 7: 20 minutes
- Step 8: 15 minutes

**Total: ~3 hours** (with breaks and debugging time: 4-6 hours, spread over 1-2 days)

---

## Notes

- This is an MVP - focus on getting it working, not perfect
- Parameter ranges are conservative by design
- Phase 1 only supports barter_only exchange regime
- Mode schedules are not supported (power-user feature)
- Validation is deferred to Phase 2

---

**Ready to begin? Start with Step 1!** 🚀

