"""
Scenario loading from YAML files.
"""

import yaml
from pathlib import Path
from .schema import (
    ScenarioConfig, ScenarioParams, UtilitiesMix, 
    UtilityConfig, ResourceSeed
)


def load_scenario(path: str) -> ScenarioConfig:
    """
    Load and validate a scenario from a YAML file.
    
    Args:
        path: Path to YAML scenario file
        
    Returns:
        Validated ScenarioConfig object
        
    Raises:
        ValueError: If scenario is invalid
        FileNotFoundError: If file doesn't exist
    """
    path_obj = Path(path)
    
    if not path_obj.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")
    
    with open(path_obj, 'r') as f:
        data = yaml.safe_load(f)
    
    # Parse scenario structure
    try:
        # Parse utilities
        utilities_data = data['utilities']
        utility_configs = []
        for util_spec in utilities_data['mix']:
            utility_configs.append(UtilityConfig(
                type=util_spec['type'],
                weight=util_spec['weight'],
                params=util_spec['params']
            ))
        utilities = UtilitiesMix(mix=utility_configs)
        
        # Parse params (with defaults)
        params_data = data.get('params', {})
        params = ScenarioParams(
            spread=params_data.get('spread', 0.05),
            vision_radius=params_data.get('vision_radius', 5),
            interaction_radius=params_data.get('interaction_radius', 1),
            move_budget_per_tick=params_data.get('move_budget_per_tick', 1),
            ΔA_max=params_data.get('ΔA_max', 5),
            forage_rate=params_data.get('forage_rate', 1),
            epsilon=params_data.get('epsilon', 1e-12),
            beta=params_data.get('beta', 0.95)
        )
        
        # Parse resource seed
        resource_data = data['resource_seed']
        resource_seed = ResourceSeed(
            density=resource_data['density'],
            amount=resource_data['amount']
        )
        
        # Create scenario config
        scenario = ScenarioConfig(
            schema_version=data['schema_version'],
            name=data['name'],
            N=data['N'],
            agents=data['agents'],
            initial_inventories=data['initial_inventories'],
            utilities=utilities,
            params=params,
            resource_seed=resource_seed
        )
        
        # Validate
        scenario.validate()
        
        return scenario
        
    except KeyError as e:
        raise ValueError(f"Missing required field in scenario: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing scenario: {e}")

