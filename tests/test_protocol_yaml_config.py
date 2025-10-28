"""
Tests for protocol configuration in YAML scenarios.

Validates:
- Protocols can be specified in YAML
- Protocol validation works
- Protocols are instantiated correctly from YAML
- CLI overrides work
- Invalid protocol names are rejected

Version: 2025-10-28 (Phase 2a - Protocol YAML Configuration)
"""

import pytest
from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation
from vmt_engine.protocols.search import RandomWalkSearch, LegacySearchProtocol
from vmt_engine.protocols.matching import RandomMatching, LegacyMatchingProtocol
from vmt_engine.protocols.bargaining import SplitDifference, LegacyBargainingProtocol


class TestProtocolYAMLConfiguration:
    """Test protocol configuration in YAML files."""
    
    def test_all_new_protocols_from_yaml(self):
        """Load scenario with all three Phase 2a protocols specified."""
        scenario = load_scenario("scenarios/pro_tests/protocol_comparison_baseline.yaml")
        
        # Check protocols are set in config
        assert scenario.search_protocol == "random_walk"
        assert scenario.matching_protocol == "random_matching"
        assert scenario.bargaining_protocol == "split_difference"
        
        # Create simulation - should use protocols from YAML
        sim = Simulation(scenario, seed=42)
        
        # Verify correct protocols instantiated
        assert sim.search_protocol.name == "random_walk"
        assert sim.matching_protocol.name == "random_matching"
        assert sim.bargaining_protocol.name == "split_difference"
        
        # Run should work
        sim.run(5)
        assert sim.tick == 5
    
    def test_partial_protocol_specification(self):
        """Protocols can be partially specified with defaults for unspecified."""
        scenario = load_scenario("scenarios/pro_tests/legacy_with_random_walk.yaml")
        
        # Only search protocol specified
        assert scenario.search_protocol == "random_walk"
        assert scenario.matching_protocol is None  # Will default to legacy
        assert scenario.bargaining_protocol is None  # Will default to legacy
        
        sim = Simulation(scenario, seed=42)
        
        # Verify protocols
        assert sim.search_protocol.name == "random_walk"
        assert sim.matching_protocol.name == "legacy_three_pass"
        assert sim.bargaining_protocol.name == "legacy_compensating_block"
    
    def test_cli_override_yaml_protocol(self):
        """CLI arguments override YAML protocol configuration."""
        scenario = load_scenario("scenarios/pro_tests/protocol_comparison_baseline.yaml")
        
        # YAML specifies random_walk, but CLI overrides with legacy
        override_search = LegacySearchProtocol()
        sim = Simulation(scenario, seed=42, search_protocol=override_search)
        
        # CLI override wins
        assert sim.search_protocol.name == "legacy_distance_discounted"
        # Other protocols from YAML
        assert sim.matching_protocol.name == "random_matching"
        assert sim.bargaining_protocol.name == "split_difference"
    
    def test_legacy_scenario_without_protocols(self):
        """Old scenarios without protocol fields still work (default to legacy)."""
        scenario = load_scenario("scenarios/foundational_barter_demo.yaml")
        
        # No protocol fields in YAML
        assert scenario.search_protocol is None
        assert scenario.matching_protocol is None
        assert scenario.bargaining_protocol is None
        
        # Should default to legacy
        sim = Simulation(scenario, seed=42)
        assert sim.search_protocol.name == "legacy_distance_discounted"
        assert sim.matching_protocol.name == "legacy_three_pass"
        assert sim.bargaining_protocol.name == "legacy_compensating_block"


class TestProtocolValidation:
    """Test protocol name validation in schema."""
    
    def test_invalid_search_protocol_rejected(self):
        """Invalid search protocol names are rejected."""
        import yaml
        import tempfile
        
        bad_yaml = """
schema_version: 1
name: bad_protocol
N: 10
agents: 5
initial_inventories:
  A: 5
  B: 5
utilities:
  mix:
    - {type: ces, weight: 1.0, params: {rho: 0.5, wA: 0.5, wB: 0.5}}
resource_seed:
  density: 0.1
  amount: 1
params: {}
search_protocol: "invalid_protocol_name"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(bad_yaml)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid search_protocol"):
                load_scenario(temp_path)
        finally:
            import os
            os.unlink(temp_path)


class TestProtocolScenarios:
    """Test that protocol test scenarios run successfully."""
    
    def test_protocol_comparison_baseline_runs(self):
        """All new protocols scenario runs successfully."""
        scenario = load_scenario("scenarios/pro_tests/protocol_comparison_baseline.yaml")
        sim = Simulation(scenario, seed=42)
        sim.run(10)
        
        assert sim.tick == 10
        # Verify protocols used
        assert isinstance(sim.search_protocol, RandomWalkSearch)
        assert isinstance(sim.matching_protocol, RandomMatching)
        assert isinstance(sim.bargaining_protocol, SplitDifference)
    
    def test_all_four_protocol_scenarios_load(self):
        """All four protocol test scenarios load without errors."""
        scenarios = [
            "scenarios/pro_tests/protocol_comparison_baseline.yaml",
            "scenarios/pro_tests/legacy_with_random_walk.yaml",
            "scenarios/pro_tests/legacy_with_random_matching.yaml",
            "scenarios/pro_tests/legacy_with_split_difference.yaml",
        ]
        
        for scenario_path in scenarios:
            # Should not raise
            s = load_scenario(scenario_path)
            assert s is not None
            assert s.schema_version == 1

