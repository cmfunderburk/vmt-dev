"""
Tests for Split-the-Difference Bargaining Protocol

Currently a stub protocol (not_implemented). This test verifies
the stub behavior until the protocol is fully implemented.

Version: 2025.11.04 (Stub Verification)
"""

import pytest
from tests.helpers.builders import build_agent
from vmt_engine.game_theory.bargaining import SplitDifference
from vmt_engine.protocols.context_builders import build_world_view_for_agent
from vmt_engine.protocols.base import Unpair
from tests.helpers.builders import build_scenario, make_sim


class TestSplitDifferenceStub:
    """Verify stub protocol returns not_implemented."""
    
    def test_split_difference_returns_not_implemented(self):
        """Verify stub returns not_implemented."""
        protocol = SplitDifference()
        agent_a = build_agent(id=1)
        agent_b = build_agent(id=2)
        
        # Create minimal scenario for world view
        scenario = build_scenario(agents=2)
        sim = make_sim(scenario, seed=42)
        world = build_world_view_for_agent(agent_a, sim)
        
        effects = protocol.negotiate((1, 2), (agent_a, agent_b), world)
        
        assert len(effects) == 1
        assert isinstance(effects[0], Unpair)
        assert effects[0].reason == "not_implemented"
    
    def test_has_required_properties(self):
        """Protocol exposes required properties."""
        protocol = SplitDifference()
        
        assert hasattr(protocol, "name")
        assert hasattr(protocol, "version")
        assert hasattr(protocol, "negotiate")
        assert protocol.name == "split_difference"
        assert protocol.version == "2025.11.04.stub"
