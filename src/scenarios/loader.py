"""
Scenario loading from YAML files.
"""

import yaml
from pathlib import Path
from .schema import (
    ScenarioConfig, ScenarioParams, UtilitiesMix, 
    UtilityConfig, ResourceSeed, ModeSchedule
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
            spread=params_data.get('spread', 0.0),
            vision_radius=params_data.get('vision_radius', 5),
            interaction_radius=params_data.get('interaction_radius', 1),
            move_budget_per_tick=params_data.get('move_budget_per_tick', 1),
            forage_rate=params_data.get('forage_rate', 1),
            epsilon=params_data.get('epsilon', 1e-12),
            beta=params_data.get('beta', 0.95),
            resource_growth_rate=params_data.get('resource_growth_rate', 0),
            resource_max_amount=params_data.get('resource_max_amount', 5),
            resource_regen_cooldown=params_data.get('resource_regen_cooldown', 5),
            trade_cooldown_ticks=params_data.get('trade_cooldown_ticks', 5),
            trade_execution_mode=params_data.get('trade_execution_mode', "minimum"),
            # Resource claiming params
            enable_resource_claiming=params_data.get('enable_resource_claiming', True),
            enforce_single_harvester=params_data.get('enforce_single_harvester', True),
            # Telemetry params
            log_preferences=params_data.get('log_preferences', False)
        )
        
        # Parse resource seed
        resource_data = data['resource_seed']
        resource_seed = ResourceSeed(
            density=resource_data['density'],
            amount=resource_data['amount']
        )
        
        # Parse mode schedule (optional)
        mode_schedule = None
        if 'mode_schedule' in data:
            mode_data = data['mode_schedule']
            mode_schedule = ModeSchedule(
                type=mode_data['type'],
                forage_ticks=mode_data['forage_ticks'],
                trade_ticks=mode_data['trade_ticks'],
                start_mode=mode_data.get('start_mode', 'forage')
            )
        
        # Parse protocol configuration (optional)
        # Support both string names and dict with name + params
        search_protocol = data.get('search_protocol', None)
        matching_protocol = data.get('matching_protocol', None)
        bargaining_protocol = data.get('bargaining_protocol', None)
        
        # Normalize to dict format if string (for consistency)
        if isinstance(search_protocol, str):
            search_protocol = {'name': search_protocol}
        elif isinstance(search_protocol, dict):
            # Ensure it has 'name' key
            if 'name' not in search_protocol:
                raise ValueError("search_protocol dict must have 'name' key")
        
        if isinstance(matching_protocol, str):
            matching_protocol = {'name': matching_protocol}
        elif isinstance(matching_protocol, dict):
            if 'name' not in matching_protocol:
                raise ValueError("matching_protocol dict must have 'name' key")
        
        if isinstance(bargaining_protocol, str):
            bargaining_protocol = {'name': bargaining_protocol}
        elif isinstance(bargaining_protocol, dict):
            if 'name' not in bargaining_protocol:
                raise ValueError("bargaining_protocol dict must have 'name' key")
        
        # Create scenario config
        scenario = ScenarioConfig(
            schema_version=data['schema_version'],
            name=data['name'],
            N=data['N'],
            agents=data['agents'],
            initial_inventories=data['initial_inventories'],
            utilities=utilities,
            params=params,
            resource_seed=resource_seed,
            mode_schedule=mode_schedule,
            search_protocol=search_protocol,
            matching_protocol=matching_protocol,
            bargaining_protocol=bargaining_protocol
        )
        
        # Validate
        scenario.validate()
        
        return scenario
        
    except KeyError as e:
        raise ValueError(f"Missing required field in scenario: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing scenario: {e}")

