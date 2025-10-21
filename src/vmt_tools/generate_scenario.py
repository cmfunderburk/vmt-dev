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
        "--exchange-regime",
        choices=['barter_only', 'money_only', 'mixed', 'mixed_liquidity_gated'],
        default='barter_only',
        help="Exchange regime (default: barter_only)"
    )
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
            resource_config=(density, max_amt, regen),
            exchange_regime=args.exchange_regime
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
        print(f"  - Exchange regime: {args.exchange_regime}")
        if args.exchange_regime in ['money_only', 'mixed', 'mixed_liquidity_gated']:
            print(f"  - Money inventories: generated (same range as goods)")
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

