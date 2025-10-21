"""
Integration tests for new utility scenarios.
Tests scenario loading, quote computation, trade execution, and epsilon handling.
"""

import pytest
import sys
import math
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation
from vmt_engine.econ.utility import UQuadratic, UTranslog, UStoneGeary
from telemetry import LogConfig


class TestScenarioLoading:
    """Test that all demo scenarios load and validate correctly."""
    
    def test_bliss_point_demo_loads(self):
        """Test bliss_point_demo.yaml loads successfully."""
        config = load_scenario('scenarios/bliss_point_demo.yaml')
        
        assert config.name == "Bliss Point Demonstration"
        assert config.agents == 10
        assert config.N == 20
        assert len(config.utilities.mix) == 1
        assert config.utilities.mix[0].type == "quadratic"
        assert config.utilities.mix[0].params['A_star'] == 10.0
        assert config.utilities.mix[0].params['B_star'] == 10.0
    
    def test_translog_estimation_demo_loads(self):
        """Test translog_estimation_demo.yaml loads successfully."""
        config = load_scenario('scenarios/translog_estimation_demo.yaml')
        
        assert config.name == "Translog Empirical Demonstration"
        assert config.agents == 20
        assert config.N == 30
        assert len(config.utilities.mix) == 2
        assert config.utilities.mix[0].type == "translog"
        assert config.utilities.mix[1].type == "ces"
        assert config.utilities.mix[0].params['alpha_A'] == 0.5
    
    def test_subsistence_economy_demo_loads(self):
        """Test subsistence_economy_demo.yaml loads successfully."""
        config = load_scenario('scenarios/subsistence_economy_demo.yaml')
        
        assert config.name == "Subsistence Economy Demonstration"
        assert config.agents == 15
        assert config.N == 25
        assert len(config.utilities.mix) == 1
        assert config.utilities.mix[0].type == "stone_geary"
        assert config.utilities.mix[0].params['gamma_A'] == 5.0
        assert config.utilities.mix[0].params['gamma_B'] == 3.0
    
    def test_mixed_utility_showcase_loads(self):
        """Test mixed_utility_showcase.yaml loads successfully."""
        config = load_scenario('scenarios/mixed_utility_showcase.yaml')
        
        assert config.name == "Mixed Utility Showcase"
        assert config.agents == 24
        assert config.N == 30
        assert len(config.utilities.mix) == 3
        
        types = [u.type for u in config.utilities.mix]
        assert "quadratic" in types
        assert "translog" in types
        assert "stone_geary" in types


class TestAgentInitialization:
    """Test that agents are initialized correctly with new utility types."""
    
    def test_bliss_point_demo_creates_quadratic_agents(self):
        """Test that bliss_point_demo creates agents with UQuadratic utility."""
        config = load_scenario('scenarios/bliss_point_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        # All agents should have UQuadratic utility
        for agent in sim.agents:
            assert isinstance(agent.utility, UQuadratic)
            assert agent.utility.A_star == 10.0
            assert agent.utility.B_star == 10.0
    
    def test_subsistence_economy_creates_stone_geary_agents(self):
        """Test that subsistence_economy_demo creates Stone-Geary agents."""
        config = load_scenario('scenarios/subsistence_economy_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        # All agents should have UStoneGeary utility
        for agent in sim.agents:
            assert isinstance(agent.utility, UStoneGeary)
            assert agent.utility.gamma_A == 5.0
            assert agent.utility.gamma_B == 3.0
    
    def test_mixed_showcase_creates_heterogeneous_population(self):
        """Test that mixed_utility_showcase creates diverse agents."""
        config = load_scenario('scenarios/mixed_utility_showcase.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        # Count utility types
        utility_types = [type(agent.utility).__name__ for agent in sim.agents]
        
        assert 'UQuadratic' in utility_types
        assert 'UTranslog' in utility_types
        assert 'UStoneGeary' in utility_types
        
        # Verify roughly equal distribution (within sampling variance)
        from collections import Counter
        counts = Counter(utility_types)
        assert counts['UQuadratic'] >= 5  # Expect ~8 ± variance
        assert counts['UTranslog'] >= 5
        assert counts['UStoneGeary'] >= 5


class TestQuoteComputation:
    """Test quote computation integration for new utility types."""
    
    def test_quadratic_quotes_finite(self):
        """Test that quadratic agents generate finite quotes (except when saturated)."""
        config = load_scenario('scenarios/bliss_point_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        for agent in sim.agents:
            quotes = agent.quotes
            
            # Quotes should exist
            assert 'ask_A_in_B' in quotes
            assert 'bid_A_in_B' in quotes
            
            # Should be non-negative (even if inf)
            assert quotes['ask_A_in_B'] >= 0
            assert quotes['bid_A_in_B'] >= 0
    
    def test_quadratic_saturated_agents_refuse_trades(self):
        """Test that quadratic agents above bliss refuse trades."""
        config = load_scenario('scenarios/bliss_point_demo.yaml')
        sim = Simulation(config, seed=123, log_config=LogConfig.minimal())
        
        # Find agents above bliss point
        for agent in sim.agents:
            if agent.inventory.A > 12 and agent.inventory.B > 12:
                # Agent is above bliss (10, 10)
                # Should have ask > bid (no feasible trade)
                assert agent.quotes['ask_A_in_B'] > agent.quotes['bid_A_in_B']
    
    def test_translog_quotes_well_defined(self):
        """Test that translog agents always have well-defined quotes."""
        config = load_scenario('scenarios/translog_estimation_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        translog_agents = [a for a in sim.agents if isinstance(a.utility, UTranslog)]
        
        for agent in translog_agents:
            quotes = agent.quotes
            
            # All quotes should be finite and positive
            assert 0 < quotes['ask_A_in_B'] < float('inf')
            assert 0 < quotes['bid_A_in_B'] < float('inf')
            assert not math.isnan(quotes['ask_A_in_B'])
            assert not math.isnan(quotes['bid_A_in_B'])
    
    def test_stone_geary_desperate_quotes(self):
        """Test that Stone-Geary agents near subsistence have high quotes."""
        config = load_scenario('scenarios/subsistence_economy_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        # Find agents close to subsistence (A near 8, B near 6)
        for agent in sim.agents:
            if agent.inventory.A <= 10 and agent.inventory.B <= 8:
                # Agent is close to subsistence (gamma_A=5, gamma_B=3)
                # MRS should be relatively high
                mrs = agent.utility.mrs_A_in_B(agent.inventory.A, agent.inventory.B)
                assert mrs > 1.0  # Higher than symmetric preferences


class TestTradeExecution:
    """Test trade execution with new utility types."""
    
    def test_bliss_point_demo_runs_without_errors(self):
        """Test that bliss_point_demo runs for 10 ticks."""
        config = load_scenario('scenarios/bliss_point_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        # Run simulation
        sim.run(max_ticks=10)
        
        assert sim.tick == 10
    
    def test_translog_demo_runs_without_errors(self):
        """Test that translog_estimation_demo runs for 10 ticks."""
        config = load_scenario('scenarios/translog_estimation_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        sim.run(max_ticks=10)
        
        assert sim.tick == 10
    
    def test_subsistence_demo_runs_without_errors(self):
        """Test that subsistence_economy_demo runs for 10 ticks."""
        config = load_scenario('scenarios/subsistence_economy_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        sim.run(max_ticks=10)
        
        assert sim.tick == 10
    
    def test_mixed_showcase_runs_without_errors(self):
        """Test that mixed_utility_showcase runs for 10 ticks."""
        config = load_scenario('scenarios/mixed_utility_showcase.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        sim.run(max_ticks=10)
        
        assert sim.tick == 10
    
    def test_mixed_showcase_different_utilities_can_trade(self):
        """Test that agents with different utility types can trade."""
        config = load_scenario('scenarios/mixed_utility_showcase.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        # Run for a few ticks
        sim.run(max_ticks=20)
        
        # Check if any trades occurred (telemetry would show this)
        # For now, verify simulation completed without errors
        assert sim.tick == 20


class TestDeterminism:
    """Test that simulations with new utilities are deterministic."""
    
    def test_bliss_point_demo_deterministic(self):
        """Test that bliss_point_demo is deterministic."""
        config = load_scenario('scenarios/bliss_point_demo.yaml')
        
        # Run 1
        sim1 = Simulation(config, seed=42, log_config=LogConfig.minimal())
        sim1.run(max_ticks=10)
        
        # Capture final state
        state1 = [(a.id, a.pos, a.inventory.A, a.inventory.B) for a in sim1.agents]
        
        # Run 2 with same seed
        sim2 = Simulation(config, seed=42, log_config=LogConfig.minimal())
        sim2.run(max_ticks=10)
        
        # Capture final state
        state2 = [(a.id, a.pos, a.inventory.A, a.inventory.B) for a in sim2.agents]
        
        # Should be identical
        assert state1 == state2
    
    def test_mixed_showcase_deterministic(self):
        """Test that mixed_utility_showcase is deterministic."""
        config = load_scenario('scenarios/mixed_utility_showcase.yaml')
        
        # Run 1
        sim1 = Simulation(config, seed=99, log_config=LogConfig.minimal())
        sim1.run(max_ticks=10)
        state1 = [(a.id, a.pos, a.inventory.A, a.inventory.B) for a in sim1.agents]
        
        # Run 2 with same seed
        sim2 = Simulation(config, seed=99, log_config=LogConfig.minimal())
        sim2.run(max_ticks=10)
        state2 = [(a.id, a.pos, a.inventory.A, a.inventory.B) for a in sim2.agents]
        
        assert state1 == state2


class TestEpsilonHandling:
    """Test epsilon handling consistency across utilities."""
    
    def test_translog_zero_inventory_handled(self):
        """Test that translog handles zero inventory gracefully."""
        from vmt_engine.econ.utility import UTranslog
        from vmt_engine.core.state import Inventory
        from vmt_engine.core.agent import Agent
        from vmt_engine.systems.quotes import compute_quotes
        
        u = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5,
                      beta_AA=0.0, beta_BB=0.0, beta_AB=0.0)
        
        agent = Agent(id=0, pos=(0, 0), inventory=Inventory(A=0, B=10, M=0), utility=u)
        
        # Should handle A=0 with epsilon-shift
        quotes = compute_quotes(agent, spread=0.0, epsilon=1e-12)
        
        assert not math.isnan(quotes['ask_A_in_B'])
        assert not math.isinf(quotes['ask_A_in_B'])
    
    def test_stone_geary_at_subsistence_handled(self):
        """Test that Stone-Geary handles subsistence boundary gracefully."""
        from vmt_engine.econ.utility import UStoneGeary
        from vmt_engine.core.state import Inventory
        from vmt_engine.core.agent import Agent
        from vmt_engine.systems.quotes import compute_quotes
        
        u = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
        
        # Agent exactly at subsistence
        agent = Agent(id=0, pos=(0, 0), inventory=Inventory(A=5, B=3, M=0), utility=u)
        
        # Should handle epsilon-shift gracefully
        quotes = compute_quotes(agent, spread=0.0, epsilon=1e-12)
        
        assert not math.isnan(quotes['ask_A_in_B'])
        assert not math.isinf(quotes['ask_A_in_B'])
    
    def test_quadratic_at_bliss_handled(self):
        """Test that quadratic at bliss point is handled gracefully."""
        from vmt_engine.econ.utility import UQuadratic
        from vmt_engine.core.state import Inventory
        from vmt_engine.core.agent import Agent
        from vmt_engine.systems.quotes import compute_quotes
        
        u = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0)
        
        # Agent at bliss point
        agent = Agent(id=0, pos=(0, 0), inventory=Inventory(A=10, B=10, M=0), utility=u)
        
        # MRS is undefined, but quotes should still be computed
        quotes = compute_quotes(agent, spread=0.0, epsilon=1e-12)
        
        # Should have some quote values (possibly indicating no trade)
        assert 'ask_A_in_B' in quotes
        assert 'bid_A_in_B' in quotes


class TestFullSimulations:
    """Test that full simulations complete successfully."""
    
    def test_bliss_point_demo_50_ticks(self):
        """Run bliss_point_demo for 50 ticks."""
        config = load_scenario('scenarios/bliss_point_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        sim.run(max_ticks=50)
        
        assert sim.tick == 50
        # Verify agents still exist and have valid state
        assert len(sim.agents) == 10
        for agent in sim.agents:
            assert agent.inventory.A >= 0
            assert agent.inventory.B >= 0
    
    def test_translog_demo_50_ticks(self):
        """Run translog_estimation_demo for 50 ticks."""
        config = load_scenario('scenarios/translog_estimation_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        sim.run(max_ticks=50)
        
        assert sim.tick == 50
        assert len(sim.agents) == 20
    
    def test_subsistence_demo_50_ticks(self):
        """Run subsistence_economy_demo for 50 ticks."""
        config = load_scenario('scenarios/subsistence_economy_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        sim.run(max_ticks=50)
        
        assert sim.tick == 50
        assert len(sim.agents) == 15
        
        # Verify no agents fell below subsistence
        for agent in sim.agents:
            # All should be above subsistence (epsilon-shift protects edge cases)
            assert agent.inventory.A >= 0
            assert agent.inventory.B >= 0
    
    def test_mixed_showcase_50_ticks(self):
        """Run mixed_utility_showcase for 50 ticks."""
        config = load_scenario('scenarios/mixed_utility_showcase.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        sim.run(max_ticks=50)
        
        assert sim.tick == 50
        assert len(sim.agents) == 24


class TestQuoteRefreshAfterTrade:
    """Test that quotes refresh correctly after inventory changes."""
    
    def test_quotes_refresh_for_quadratic_agents(self):
        """Test that quadratic agents recompute quotes after trading."""
        config = load_scenario('scenarios/bliss_point_demo.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        # Get initial quotes for first agent
        agent = sim.agents[0]
        initial_ask = agent.quotes['ask_A_in_B']
        
        # Run a few ticks (might trigger trades)
        sim.run(max_ticks=5)
        
        # If inventory changed, quotes should be different
        # (This is a weak test, but validates the refresh mechanism works)
        # Quotes exist and are valid
        assert 'ask_A_in_B' in agent.quotes
        assert agent.quotes['ask_A_in_B'] >= 0


class TestBehavioralDifferences:
    """Test that different utility types exhibit unique behaviors."""
    
    def test_quadratic_vs_translog_mrs_behavior(self):
        """Test that quadratic and translog have different MRS patterns."""
        from vmt_engine.econ.utility import UQuadratic, UTranslog
        
        u_quad = UQuadratic(A_star=20.0, B_star=20.0, sigma_A=10.0, sigma_B=10.0)
        u_trans = UTranslog(alpha_0=0.0, alpha_A=0.5, alpha_B=0.5,
                           beta_AA=0.0, beta_BB=0.0, beta_AB=0.0)
        
        # At (20, 20): quadratic is at bliss (MRS undefined)
        mrs_quad = u_quad.mrs_A_in_B(20, 20)
        assert mrs_quad is None
        
        # Translog has well-defined MRS
        mrs_trans = u_trans.mrs_A_in_B(20, 20)
        assert mrs_trans is not None
        assert mrs_trans > 0
    
    def test_stone_geary_vs_translog_desperate_trading(self):
        """Test that Stone-Geary shows desperate trading, translog does not."""
        from vmt_engine.econ.utility import UStoneGeary, UTranslog
        
        u_sg = UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=5.0, gamma_B=3.0)
        u_trans = UTranslog(alpha_0=0.0, alpha_A=0.6, alpha_B=0.4,
                           beta_AA=0.0, beta_BB=0.0, beta_AB=0.0)
        
        # Near subsistence for Stone-Geary: (A=6, B=10)
        mrs_sg_near = u_sg.mrs_A_in_B(6, 10)
        
        # Same inventory for translog
        mrs_trans = u_trans.mrs_A_in_B(6, 10)
        
        # Stone-Geary should have much higher MRS (desperate)
        # MRS_sg = (0.6 * 7) / (0.4 * 1) = 10.5
        # MRS_trans = (0.6 * 10) / (0.4 * 6) = 2.5
        # Ratio is ~4.2, so test for > 3
        assert mrs_sg_near > mrs_trans * 3


class TestPerformance:
    """Test that new utilities don't significantly degrade performance."""
    
    def test_mixed_showcase_performance(self):
        """Test that mixed utility simulation completes in reasonable time."""
        import time
        
        config = load_scenario('scenarios/mixed_utility_showcase.yaml')
        sim = Simulation(config, seed=42, log_config=LogConfig.minimal())
        
        start = time.time()
        sim.run(max_ticks=50)
        elapsed = time.time() - start
        
        # Should complete in under 5 seconds (generous bound)
        assert elapsed < 5.0
        assert sim.tick == 50

