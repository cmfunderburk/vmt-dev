"""
Protocol factory for instantiating protocols from configuration names and parameters.
"""

from typing import Optional, Any, Union


def get_search_protocol(protocol_config: Optional[Union[str, dict[str, Any]]]):
    """
    Instantiate a search protocol via the registry.
    
    Args:
        protocol_config: Either a string (protocol name) or dict with 'name' and optional 'params'
            Examples:
                "legacy_distance_discounted"
                {"name": "myopic"}
                {"name": "myopic", "params": {}}
    
    Returns:
        Instantiated protocol instance
    """
    from vmt_engine.protocols.registry import ProtocolRegistry
    
    if protocol_config is None:
        name = "legacy_distance_discounted"
        params = {}
    elif isinstance(protocol_config, str):
        name = protocol_config
        params = {}
    elif isinstance(protocol_config, dict):
        name = protocol_config.get('name', "legacy_distance_discounted")
        params = protocol_config.get('params', {})
    else:
        raise ValueError(f"protocol_config must be str or dict, got {type(protocol_config)}")
    
    cls = ProtocolRegistry.get_protocol_class(name, "search")
    return cls(**params)


def get_matching_protocol(protocol_config: Optional[Union[str, dict[str, Any]]]):
    """
    Instantiate a matching protocol via the registry.
    
    Args:
        protocol_config: Either a string (protocol name) or dict with 'name' and optional 'params'
            Examples:
                "legacy_three_pass"
                {"name": "greedy_surplus"}
                {"name": "greedy_surplus", "params": {}}
    
    Returns:
        Instantiated protocol instance
    """
    from vmt_engine.protocols.registry import ProtocolRegistry
    
    if protocol_config is None:
        name = "legacy_three_pass"
        params = {}
    elif isinstance(protocol_config, str):
        name = protocol_config
        params = {}
    elif isinstance(protocol_config, dict):
        name = protocol_config.get('name', "legacy_three_pass")
        params = protocol_config.get('params', {})
    else:
        raise ValueError(f"protocol_config must be str or dict, got {type(protocol_config)}")
    
    cls = ProtocolRegistry.get_protocol_class(name, "matching")
    return cls(**params)


def get_bargaining_protocol(protocol_config: Optional[Union[str, dict[str, Any]]]):
    """
    Instantiate a bargaining protocol via the registry.
    
    Args:
        protocol_config: Either a string (protocol name) or dict with 'name' and optional 'params'
            Examples:
                "legacy_compensating_block"
                {"name": "split_difference"}
                {"name": "take_it_or_leave_it", "params": {"proposer_power": 0.9, "proposer_selection": "random"}}
    
    Returns:
        Instantiated protocol instance
    """
    from vmt_engine.protocols.registry import ProtocolRegistry
    
    if protocol_config is None:
        name = "legacy_compensating_block"
        params = {}
    elif isinstance(protocol_config, str):
        name = protocol_config
        params = {}
    elif isinstance(protocol_config, dict):
        name = protocol_config.get('name', "legacy_compensating_block")
        params = protocol_config.get('params', {})
    else:
        raise ValueError(f"protocol_config must be str or dict, got {type(protocol_config)}")
    
    cls = ProtocolRegistry.get_protocol_class(name, "bargaining")
    return cls(**params)

