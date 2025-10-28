"""
Protocol factory for instantiating protocols from configuration names.
"""

from typing import Optional


def get_search_protocol(protocol_name: Optional[str]):
    """
    Instantiate a search protocol via the registry.
    Defaults to legacy_distance_discounted when protocol_name is None.
    """
    from vmt_engine.protocols.registry import ProtocolRegistry
    name = protocol_name or "legacy_distance_discounted"
    cls = ProtocolRegistry.get_protocol_class(name, "search")
    return cls()


def get_matching_protocol(protocol_name: Optional[str]):
    """
    Instantiate a matching protocol via the registry.
    Defaults to legacy_three_pass when protocol_name is None.
    """
    from vmt_engine.protocols.registry import ProtocolRegistry
    name = protocol_name or "legacy_three_pass"
    cls = ProtocolRegistry.get_protocol_class(name, "matching")
    return cls()


def get_bargaining_protocol(protocol_name: Optional[str]):
    """
    Instantiate a bargaining protocol via the registry.
    Defaults to legacy_compensating_block when protocol_name is None.
    """
    from vmt_engine.protocols.registry import ProtocolRegistry
    name = protocol_name or "legacy_compensating_block"
    cls = ProtocolRegistry.get_protocol_class(name, "bargaining")
    return cls()

