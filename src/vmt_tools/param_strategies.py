"""
Parameter generation strategies for VMT scenario files.

This module provides functions to generate random but valid parameters for
all supported utility functions. Parameters are generated within conservative
ranges that ensure well-behaved utility functions.

Also includes preset configurations (Phase 2) for common use cases.
"""

import random
from typing import Tuple, List, Dict, Optional


# Preset configurations for common scenarios (Scenario Generator Phase 2)
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


def get_preset(preset_name: str) -> Dict:
    """
    Get preset configuration by name.
    
    Args:
        preset_name: Name of the preset
        
    Returns:
        Dictionary of preset parameters (copy, safe to modify)
        
    Raises:
        ValueError: If preset_name is not recognized
        
    Available presets:
        - minimal: Quick testing (10 agents, 20×20)
        - standard: Default demonstration (30 agents, 40×40, all utility types)
        - large: Performance testing (80 agents, 80×80)
        - money_demo: Money-only economy (20 agents, money_only regime)
        - mixed_economy: Hybrid barter + money (40 agents, mixed regime)
    """
    if preset_name not in PRESETS:
        raise ValueError(
            f"Unknown preset: {preset_name}. "
            f"Available presets: {', '.join(sorted(PRESETS.keys()))}"
        )
    return PRESETS[preset_name].copy()


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
        Random value in [min_val, max_val] excluding [excl_min, excl_max]
        
    Note: This implementation uses rejection sampling. A more robust version
    would explicitly sample from the valid regions.
    """
    for _ in range(max_tries):
        val = random.uniform(min_val, max_val)
        if val < excl_min or val > excl_max:
            return val
    # Fallback: return edge value
    return min_val if random.random() < 0.5 else max_val

