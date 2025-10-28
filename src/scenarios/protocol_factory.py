"""
Protocol factory for instantiating protocols from configuration names.
"""

from typing import Optional


def get_search_protocol(protocol_name: Optional[str]):
    """
    Instantiate a search protocol from its name.
    
    Args:
        protocol_name: Name of protocol ("legacy", "random_walk", etc.) or None for default
    
    Returns:
        Instantiated protocol object
    
    Raises:
        ValueError: If protocol name is invalid
    """
    if protocol_name is None or protocol_name == "legacy":
        from vmt_engine.protocols.search import LegacySearchProtocol
        return LegacySearchProtocol()
    elif protocol_name == "random_walk":
        from vmt_engine.protocols.search import RandomWalkSearch
        return RandomWalkSearch()
    else:
        raise ValueError(f"Unknown search protocol: {protocol_name}")


def get_matching_protocol(protocol_name: Optional[str]):
    """
    Instantiate a matching protocol from its name.
    
    Args:
        protocol_name: Name of protocol ("legacy_three_pass", "random", etc.) or None for default
    
    Returns:
        Instantiated protocol object
    
    Raises:
        ValueError: If protocol name is invalid
    """
    if protocol_name is None or protocol_name == "legacy_three_pass":
        from vmt_engine.protocols.matching import LegacyMatchingProtocol
        return LegacyMatchingProtocol()
    elif protocol_name == "random":
        from vmt_engine.protocols.matching import RandomMatching
        return RandomMatching()
    else:
        raise ValueError(f"Unknown matching protocol: {protocol_name}")


def get_bargaining_protocol(protocol_name: Optional[str]):
    """
    Instantiate a bargaining protocol from its name.
    
    Args:
        protocol_name: Name of protocol ("legacy_compensating_block", "split_difference", etc.) or None for default
    
    Returns:
        Instantiated protocol object
    
    Raises:
        ValueError: If protocol name is invalid
    """
    if protocol_name is None or protocol_name == "legacy_compensating_block":
        from vmt_engine.protocols.bargaining import LegacyBargainingProtocol
        return LegacyBargainingProtocol()
    elif protocol_name == "split_difference":
        from vmt_engine.protocols.bargaining import SplitDifference
        return SplitDifference()
    else:
        raise ValueError(f"Unknown bargaining protocol: {protocol_name}")

