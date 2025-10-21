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
    resource_config: Tuple[float, int, int],
    exchange_regime: str = 'barter_only'
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
        exchange_regime: Exchange regime type (default: 'barter_only')
        
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
    
    # Validate exchange regime
    valid_regimes = {'barter_only', 'money_only', 'mixed', 'mixed_liquidity_gated'}
    if exchange_regime not in valid_regimes:
        raise ValueError(
            f"Unknown exchange_regime: {exchange_regime}. "
            f"Valid types: {', '.join(sorted(valid_regimes))}"
        )
    
    # Generate inventories (integers)
    inventories_A = generate_inventories(n_agents, inv_min, inv_max)
    inventories_B = generate_inventories(n_agents, inv_min, inv_max)
    
    # Generate money inventories if regime requires it (Phase 2+)
    initial_inventories = {
        'A': inventories_A,
        'B': inventories_B
    }
    
    if exchange_regime in ['money_only', 'mixed', 'mixed_liquidity_gated']:
        # Use same range as goods for money (users can edit YAML for custom amounts)
        inventories_M = generate_inventories(n_agents, inv_min, inv_max)
        initial_inventories['M'] = inventories_M
    
    # Generate utility mix
    utility_mix = []
    weight = 1.0 / len(utilities)
    for i, util_type in enumerate(utilities):
        params = generate_utility_params(util_type, inventory_range)
        # Round all float params to 2 decimals for YAML output
        params = {
            k: round(v, 2) if isinstance(v, float) else v
            for k, v in params.items()
        }
        
        # Calculate weight ensuring they sum to 1.0
        # Last utility gets remainder to avoid rounding errors
        if i == len(utilities) - 1:
            assigned_weight = sum(entry['weight'] for entry in utility_mix)
            utility_weight = round(1.0 - assigned_weight, 2)
        else:
            utility_weight = round(weight, 2)
        
        utility_mix.append({
            'type': util_type,
            'weight': utility_weight,
            'params': params
        })
    
    # Construct scenario dict (schema-compliant)
    scenario = {
        'schema_version': 1,
        'name': name,
        'N': grid_size,
        'agents': n_agents,
        'initial_inventories': initial_inventories,
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
            'exchange_regime': exchange_regime,
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
    
    # Add money parameters if regime requires them (Phase 2+)
    if exchange_regime in ['money_only', 'mixed', 'mixed_liquidity_gated']:
        scenario['params'].update({
            'money_mode': 'quasilinear',
            'money_scale': 1,
            'lambda_money': 1.0
        })
    
    return scenario

