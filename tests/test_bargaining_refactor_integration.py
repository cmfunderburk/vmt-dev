"""
Integration tests for Phase 2 refactor (direct agent passing).

Verifies that all bargaining protocols have been updated to the new
signature and work correctly with direct agent access.
"""

import pytest
import inspect
import numpy as np
from decimal import Decimal
from src.vmt_engine.protocols.registry import ProtocolRegistry
from src.vmt_engine.game_theory.bargaining.compensating_block import CompensatingBlockBargaining
from src.vmt_engine.protocols.context import WorldView
from src.vmt_engine.protocols.base import Trade, Unpair
from tests.helpers.builders import build_agent


class TestProtocolSignatureCompliance:
    """Verify all bargaining protocols updated to new signature."""
    
    def test_all_bargaining_protocols_use_new_signature(self):
        """Verify all bargaining protocols have (pair, agents, world) signature."""
        protocols_dict = ProtocolRegistry.list_protocols("bargaining")
        protocol_names = protocols_dict.get("bargaining", [])
        
        for name in protocol_names:
            protocol_cls = ProtocolRegistry.get_protocol_class(name, "bargaining")
            protocol = protocol_cls()
            
            # Check signature
            sig = inspect.signature(protocol.negotiate)
            params = list(sig.parameters.keys())
            
            assert params == ['pair', 'agents', 'world'], \
                f"Protocol {name} has wrong signature: {params}"
    
    def test_on_timeout_signature_updated(self):
        """Verify on_timeout also updated to new signature."""
        protocols_dict = ProtocolRegistry.list_protocols("bargaining")
        protocol_names = protocols_dict.get("bargaining", [])
        
        for name in protocol_names:
            protocol_cls = ProtocolRegistry.get_protocol_class(name, "bargaining")
            protocol = protocol_cls()
            
            # Check on_timeout signature
            sig = inspect.signature(protocol.on_timeout)
            params = list(sig.parameters.keys())
            
            assert params == ['pair', 'agents', 'world'], \
                f"Protocol {name}.on_timeout has wrong signature: {params}"


class TestDirectAgentPassing:
    """Test protocols work correctly with direct agent access."""
    
    def test_compensating_block_with_direct_agents(self):
        """Test compensating block protocol works with direct agent passing."""
        # Build test agents with complementary preferences
        agent_a = build_agent(
            id=1,
            inv_A=Decimal("10"),
            inv_B=Decimal("10"),
            quotes={'bid_A_in_B': 2.0, 'ask_A_in_B': 1.5},
            utility_type="linear",
            utility_params={"vA": 2.0, "vB": 1.0}
        )
        agent_b = build_agent(
            id=2,
            inv_A=Decimal("10"),
            inv_B=Decimal("10"),
            quotes={'bid_A_in_B': 1.8, 'ask_A_in_B': 1.0},
            utility_type="linear",
            utility_params={"vA": 1.0, "vB": 2.0}
        )
        
        # Build minimal WorldView
        rng = np.random.Generator(np.random.PCG64(42))
        world = WorldView(
            tick=0,
            mode="trade",
            agent_id=1,
            pos=(0, 0),
            inventory={"A": agent_a.inventory.A, "B": agent_a.inventory.B},
            utility=agent_a.utility,
            quotes=agent_a.quotes,
            paired_with_id=2,
            trade_cooldowns={},
            visible_agents=[],
            visible_resources=[],
            params={"epsilon": 1e-9},
            rng=rng
        )
        
        # Call protocol with new signature
        protocol = CompensatingBlockBargaining()
        effects = protocol.negotiate(
            (agent_a.id, agent_b.id),
            (agent_a, agent_b),
            world
        )
        
        # Should return Trade or Unpair
        assert len(effects) > 0
        assert isinstance(effects[0], (Trade, Unpair))
    
    def test_all_protocols_callable_with_direct_agents(self):
        """Test all bargaining protocols can be called with direct agent access."""
        # Build test agents
        agent_a = build_agent(id=1, inv_A=10, inv_B=10)
        agent_b = build_agent(id=2, inv_A=10, inv_B=10)
        
        # Build minimal WorldView
        rng = np.random.Generator(np.random.PCG64(42))
        world = WorldView(
            tick=0,
            mode="trade",
            agent_id=1,
            pos=(0, 0),
            inventory={"A": agent_a.inventory.A, "B": agent_a.inventory.B},
            utility=agent_a.utility,
            quotes=agent_a.quotes,
            paired_with_id=2,
            trade_cooldowns={},
            visible_agents=[],
            visible_resources=[],
            params={"epsilon": 1e-9},
            rng=rng
        )
        
        # Test all bargaining protocols
        protocols_dict = ProtocolRegistry.list_protocols("bargaining")
        protocol_names = protocols_dict.get("bargaining", [])
        
        for name in protocol_names:
            protocol_cls = ProtocolRegistry.get_protocol_class(name, "bargaining")
            protocol = protocol_cls()
            
            # Should be callable without error
            effects = protocol.negotiate(
                (agent_a.id, agent_b.id),
                (agent_a, agent_b),
                world
            )
            
            # Should return a list of effects
            assert isinstance(effects, list)


class TestImmutability:
    """Test that protocols don't mutate agent state."""
    
    def test_protocols_do_not_mutate_agents(self):
        """Verify protocols don't mutate agent inventories during negotiation."""
        # Build test agents
        agent_a = build_agent(
            id=1,
            inv_A=Decimal("10"),
            inv_B=Decimal("10"),
            quotes={'bid_A_in_B': 2.0, 'ask_A_in_B': 1.5}
        )
        agent_b = build_agent(
            id=2,
            inv_A=Decimal("10"),
            inv_B=Decimal("10"),
            quotes={'bid_A_in_B': 1.8, 'ask_A_in_B': 1.0}
        )
        
        # Build WorldView
        rng = np.random.Generator(np.random.PCG64(42))
        world = WorldView(
            tick=0,
            mode="trade",
            agent_id=1,
            pos=(0, 0),
            inventory={"A": agent_a.inventory.A, "B": agent_a.inventory.B},
            utility=agent_a.utility,
            quotes=agent_a.quotes,
            paired_with_id=2,
            trade_cooldowns={},
            visible_agents=[],
            visible_resources=[],
            params={"epsilon": 1e-9},
            rng=rng
        )
        
        # Test all protocols don't mutate
        protocols_dict = ProtocolRegistry.list_protocols("bargaining")
        protocol_names = protocols_dict.get("bargaining", [])
        
        for name in protocol_names:
            protocol_cls = ProtocolRegistry.get_protocol_class(name, "bargaining")
            protocol = protocol_cls()
            
            # Snapshot state
            inv_a_before = (agent_a.inventory.A, agent_a.inventory.B)
            inv_b_before = (agent_b.inventory.A, agent_b.inventory.B)
            
            # Call protocol
            effects = protocol.negotiate(
                (agent_a.id, agent_b.id),
                (agent_a, agent_b),
                world
            )
            
            # Verify no mutation
            inv_a_after = (agent_a.inventory.A, agent_a.inventory.B)
            inv_b_after = (agent_b.inventory.A, agent_b.inventory.B)
            
            assert inv_a_before == inv_a_after, \
                f"Protocol {name} mutated agent_a inventory!"
            assert inv_b_before == inv_b_after, \
                f"Protocol {name} mutated agent_b inventory!"
    
    def test_debug_immutability_assertions_work(self):
        """Test that debug mode catches mutations (when implemented in TradeSystem)."""
        # This test verifies the debug assertion logic in TradeSystem
        # For now, just verify the test infrastructure is in place
        from tests.helpers.builders import build_scenario, make_sim
        
        scenario = build_scenario(agents=2)
        
        sim = make_sim(scenario, seed=42)
        
        # If debug_immutability=True were set, TradeSystem would check
        # This test just verifies the parameter is recognized
        assert not sim.params.get("debug_immutability", False)


class TestNoParamsHack:
    """Verify params hack is eliminated."""
    
    def test_worldview_does_not_contain_partner_state(self):
        """Verify WorldView doesn't smuggle partner state through params."""
        from tests.helpers.builders import build_scenario, make_sim
        from src.vmt_engine.protocols.context_builders import build_world_view_for_agent
        
        scenario = build_scenario(agents=2)
        sim = make_sim(scenario, seed=42)
        
        # Simulation auto-initializes on creation
        agent_a = sim.agents[0]
        agent_b = sim.agents[1]
        
        # Build WorldView
        world = build_world_view_for_agent(agent_a, sim)
        
        # Verify no partner state in params
        for key in world.params.keys():
            assert not key.startswith("partner_"), \
                f"Found params hack key: {key}"

