"""
Tests for scenario loading and validation.
"""

import pytest
from scenarios.loader import load_scenario


def test_load_single_agent_forage():
    """Test loading single agent forage scenario."""
    scenario = load_scenario("scenarios/single_agent_forage.yaml")
    
    assert scenario.schema_version == 1
    assert scenario.name == "single_agent_forage_test"
    assert scenario.N == 16
    assert scenario.agents == 1
    assert scenario.params.spread == 0.0  # Uses centralized default
    assert scenario.params.vision_radius == 5
    
    # Check utilities
    assert len(scenario.utilities.mix) == 1
    assert scenario.utilities.mix[0].type == "ces"
    assert scenario.utilities.mix[0].weight == 1.0


def test_load_three_agent_barter():
    """Test loading three agent barter scenario."""
    scenario = load_scenario("scenarios/three_agent_barter.yaml")
    
    assert scenario.schema_version == 1
    assert scenario.name == "three_agent_barter_test"
    assert scenario.N == 8
    assert scenario.agents == 3
    
    # Check initial inventories (updated to bootstrap with non-zero amounts)
    assert scenario.initial_inventories['A'] == [8, 4, 6]
    assert scenario.initial_inventories['B'] == [4, 8, 6]
    
    # Check utilities mix
    assert len(scenario.utilities.mix) == 2
    assert scenario.utilities.mix[0].type == "ces"
    assert scenario.utilities.mix[1].type == "linear"


def test_invalid_scenario():
    """Test that invalid scenarios raise errors."""
    with pytest.raises(FileNotFoundError):
        load_scenario("scenarios/nonexistent.yaml")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

