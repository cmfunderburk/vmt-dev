"""
Tests for Protocol Registry System.

Covers:
- Registration completeness for baseline protocols
- Class lookup via ProtocolRegistry
- Metadata availability and shape
- Helpful errors for invalid names
- Factory functions delegate to registry and honor defaults
- Helper utilities list/describe
"""

import pytest


def test_all_protocols_registered():
    # Import top-level to trigger registration and crash-fast asserts
    import vmt_engine.protocols as protos  # noqa: F401
    from vmt_engine.protocols import ProtocolRegistry

    protocols = ProtocolRegistry.list_protocols()

    assert "legacy_distance_discounted" in protocols["search"]
    assert "random_walk" in protocols["search"]

    assert "legacy_three_pass" in protocols["matching"]
    assert "random_matching" in protocols["matching"]

    assert "legacy_compensating_block" in protocols["bargaining"]
    assert "split_difference" in protocols["bargaining"]


def test_get_protocol_class_and_instantiate():
    import vmt_engine.protocols as protos  # noqa: F401
    from vmt_engine.protocols import ProtocolRegistry

    SearchCls = ProtocolRegistry.get_protocol_class("random_walk", "search")
    MatchingCls = ProtocolRegistry.get_protocol_class("random_matching", "matching")
    BargainingCls = ProtocolRegistry.get_protocol_class("split_difference", "bargaining")

    assert SearchCls().__class__.__name__ == "RandomWalkSearch"
    assert MatchingCls().__class__.__name__ == "RandomMatching"
    assert BargainingCls().__class__.__name__ == "SplitDifference"


def test_metadata_complete_for_random_walk():
    import vmt_engine.protocols as protos  # noqa: F401
    from vmt_engine.protocols import ProtocolRegistry

    meta = ProtocolRegistry.get_metadata("random_walk", "search")
    assert meta.name == "random_walk"
    assert meta.category == "search"
    assert isinstance(meta.version, str) and len(meta.version) > 0
    assert isinstance(meta.description, str)
    assert isinstance(meta.properties, list)
    assert isinstance(meta.complexity, str)
    assert isinstance(meta.references, list)
    assert isinstance(meta.phase, str)


def test_invalid_protocol_raises_helpful_error():
    import vmt_engine.protocols as protos  # noqa: F401
    from vmt_engine.protocols import ProtocolRegistry

    with pytest.raises(ValueError) as exc:
        ProtocolRegistry.get_protocol_class("does_not_exist", "search")
    assert "Available:" in str(exc.value)


def test_factory_uses_registry_for_defaults_and_explicit():
    import vmt_engine.protocols as protos  # noqa: F401
    from scenarios.protocol_factory import (
        get_search_protocol,
        get_matching_protocol,
        get_bargaining_protocol,
    )

    # Defaults
    assert get_search_protocol(None).__class__.__name__ == "LegacySearchProtocol"
    assert get_matching_protocol(None).__class__.__name__ == "LegacyMatchingProtocol"
    assert get_bargaining_protocol(None).__class__.__name__ == "LegacyBargainingProtocol"

    # Explicit
    assert get_search_protocol("random_walk").__class__.__name__ == "RandomWalkSearch"
    assert get_matching_protocol("random_matching").__class__.__name__ == "RandomMatching"
    assert get_bargaining_protocol("split_difference").__class__.__name__ == "SplitDifference"


def test_list_and_describe_helpers():
    import vmt_engine.protocols as protos  # noqa: F401
    from vmt_engine.protocols import list_all_protocols, describe_all_protocols

    allp = list_all_protocols()
    assert set(allp.keys()) == {"search", "matching", "bargaining"}
    assert "random_walk" in allp["search"]

    desc = describe_all_protocols()
    assert "random_walk" in desc["search"]
    rw = desc["search"]["random_walk"]
    # Check minimal shape
    for key in ["version", "description", "properties", "complexity", "references", "phase"]:
        assert key in rw


