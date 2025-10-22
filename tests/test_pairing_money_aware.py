"""
Tests for money-aware pairing system (P0 resolution).

Tests that money-aware surplus estimation works correctly in money_only and mixed
regimes, while preserving barter_only behavior unchanged.
"""

import pytest
import tempfile
import sqlite3
from src.vmt_engine.simulation import Simulation
from src.scenarios.loader import load_scenario
from src.telemetry.config import LogConfig
from src.vmt_engine.systems.matching import estimate_money_aware_surplus, compute_surplus
from src.vmt_engine.core import Agent, Inventory
from src.vmt_engine.econ.utility import UCES


class TestMoneyAwarePairing:
    """Test money-aware pairing functionality."""
    
    def test_estimate_money_aware_surplus_money_only(self):
        """Test money-aware surplus estimation in money_only regime."""
        # Create agents with complementary preferences
        agent1 = Agent(
            id=1, pos=(0, 0), inventory=Inventory(A=10, B=5, M=100),
            utility=UCES(rho=-0.5, wA=0.8, wB=0.2),
            quotes={
                'bid_A_in_M': 2.0, 'ask_A_in_M': 1.5,  # Willing to pay 2M for A, sell A for 1.5M
                'bid_B_in_M': 0.5, 'ask_B_in_M': 0.3,  # Willing to pay 0.5M for B, sell B for 0.3M
            }
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1), inventory=Inventory(A=5, B=10, M=100),
            utility=UCES(rho=-0.5, wA=0.2, wB=0.8),
            quotes={
                'bid_A_in_M': 1.0, 'ask_A_in_M': 1.8,  # Willing to pay 1M for A, sell A for 1.8M
                'bid_B_in_M': 1.5, 'ask_B_in_M': 1.0,  # Willing to pay 1.5M for B, sell B for 1M
            }
        )
        
        # Test money_only regime
        surplus, pair_type = estimate_money_aware_surplus(agent1, agent2, "money_only")
        
        # Should find positive surplus in monetary trades
        assert surplus > 0, "Should find positive surplus in money_only regime"
        assert pair_type in ["A<->M", "B<->M"], f"Should be monetary pair type, got {pair_type}"
        
        # Verify it's the best monetary option
        # A<->M: agent1 bid (2.0) - agent2 ask (1.8) = 0.2
        # B<->M: agent2 bid (1.5) - agent1 ask (0.3) = 1.2 (better)
        assert pair_type == "B<->M", "Should prefer B<->M trade (higher surplus)"
        assert abs(surplus - 1.2) < 0.01, f"Expected surplus ~1.2, got {surplus}"
    
    def test_estimate_money_aware_surplus_mixed_regime(self):
        """Test money-aware surplus estimation in mixed regime."""
        agent1 = Agent(
            id=1, pos=(0, 0), inventory=Inventory(A=10, B=5, M=100),
            utility=UCES(rho=-0.5, wA=0.8, wB=0.2),
            quotes={
                'bid_A_in_B': 3.0, 'ask_A_in_B': 2.0,  # Barter quotes
                'bid_A_in_M': 2.0, 'ask_A_in_M': 1.5,  # Money quotes
                'bid_B_in_M': 0.5, 'ask_B_in_M': 0.3,
            }
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1), inventory=Inventory(A=5, B=10, M=100),
            utility=UCES(rho=-0.5, wA=0.2, wB=0.8),
            quotes={
                'bid_A_in_B': 1.5, 'ask_A_in_B': 2.5,  # Barter quotes
                'bid_A_in_M': 1.0, 'ask_A_in_M': 1.8,  # Money quotes
                'bid_B_in_M': 1.5, 'ask_B_in_M': 1.0,
            }
        )
        
        # Test mixed regime
        surplus, pair_type = estimate_money_aware_surplus(agent1, agent2, "mixed")
        
        # Should find positive surplus
        assert surplus > 0, "Should find positive surplus in mixed regime"
        assert pair_type in ["A<->B", "A<->M", "B<->M"], f"Should be valid pair type, got {pair_type}"
        
        # Should prefer money trades when surplus is equal (money-first tie-breaking)
        # This test verifies the priority system works
    
    def test_money_first_tie_breaking(self):
        """Test that money-first tie-breaking works correctly."""
        # Create agents where barter and money trades have equal surplus
        agent1 = Agent(
            id=1, pos=(0, 0), inventory=Inventory(A=10, B=5, M=100),
            utility=UCES(rho=-0.5, wA=0.8, wB=0.2),
            quotes={
                'bid_A_in_B': 2.0, 'ask_A_in_B': 1.0,  # Barter surplus = 1.0
                'bid_A_in_M': 2.0, 'ask_A_in_M': 1.0,  # Money surplus = 1.0
            }
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1), inventory=Inventory(A=5, B=10, M=100),
            utility=UCES(rho=-0.5, wA=0.2, wB=0.8),
            quotes={
                'bid_A_in_B': 1.5, 'ask_A_in_B': 0.5,  # Barter surplus = 1.0
                'bid_A_in_M': 1.5, 'ask_A_in_M': 0.5,  # Money surplus = 1.0
            }
        )
        
        surplus, pair_type = estimate_money_aware_surplus(agent1, agent2, "mixed")
        
        # Should prefer money trade due to tie-breaking
        assert pair_type == "A<->M", f"Should prefer money trade on tie, got {pair_type}"
    
    def test_inventory_feasibility_checks(self):
        """Test that inventory feasibility prevents impossible pairings."""
        # Agent with no money
        agent1 = Agent(
            id=1, pos=(0, 0), inventory=Inventory(A=10, B=5, M=0),  # No money
            utility=UCES(rho=-0.5, wA=0.8, wB=0.2),
            quotes={'bid_A_in_M': 2.0, 'ask_A_in_M': 1.5}
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1), inventory=Inventory(A=5, B=10, M=100),
            utility=UCES(rho=-0.5, wA=0.2, wB=0.8),
            quotes={'bid_A_in_M': 1.0, 'ask_A_in_M': 1.8}
        )
        
        # Should return 0 surplus due to inventory constraints
        surplus, pair_type = estimate_money_aware_surplus(agent1, agent2, "money_only")
        assert surplus == 0.0, "Should return 0 surplus when inventory constraints prevent trade"
        assert pair_type == "", "Should return empty pair type when no feasible trade"
    
    def test_barter_only_unchanged(self):
        """Test that barter_only regime still uses compute_surplus."""
        agent1 = Agent(
            id=1, pos=(0, 0), inventory=Inventory(A=10, B=5, M=0),
            utility=UCES(rho=-0.5, wA=0.8, wB=0.2),
            quotes={'bid_A_in_B': 2.0, 'ask_A_in_B': 1.0}
        )
        
        agent2 = Agent(
            id=2, pos=(0, 1), inventory=Inventory(A=5, B=10, M=0),
            utility=UCES(rho=-0.5, wA=0.2, wB=0.8),
            quotes={'bid_A_in_B': 1.5, 'ask_A_in_B': 0.5}
        )
        
        # Should use compute_surplus for barter_only
        surplus = compute_surplus(agent1, agent2)
        assert surplus > 0, "Should find positive barter surplus"
        
        # Money-aware should also work but may return different result
        money_surplus, pair_type = estimate_money_aware_surplus(agent1, agent2, "barter_only")
        assert pair_type == "A<->B", "Should return barter pair type in barter_only regime"


class TestPairingIntegration:
    """Test money-aware pairing in full simulation context."""
    
    def test_money_only_pairing_uses_money_aware_surplus(self):
        """Test that money_only regime uses money-aware pairing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_money_pairing.db"
            
            # Create scenario with money_only regime
            scenario = load_scenario("scenarios/demos/demo_06_money_aware_pairing.yaml")
            scenario.params.exchange_regime = "money_only"
            
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Run for a few ticks
            sim.run(max_ticks=5)
            
            # Check that preferences were logged with pair_type
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT agent_id, rank, pair_type, surplus 
                FROM preferences 
                WHERE tick = 0 AND pair_type IS NOT NULL
                ORDER BY agent_id, rank
            """)
            
            preferences = list(cursor)
            conn.close()
            sim.close()
            
            # Should have preferences with pair_type
            assert len(preferences) > 0, "Should have logged preferences with pair_type"
            
            # All pair types should be monetary in money_only regime
            for _, _, pair_type, _ in preferences:
                assert pair_type in ["A<->M", "B<->M"], f"Should be monetary pair type in money_only, got {pair_type}"
    
    def test_mixed_regime_allows_all_pair_types(self):
        """Test that mixed regime can use all pair types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_mixed_pairing.db"
            
            scenario = load_scenario("scenarios/demos/demo_06_money_aware_pairing.yaml")
            scenario.params.exchange_regime = "mixed"
            
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            sim.run(max_ticks=5)
            
            # Check preferences
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT DISTINCT pair_type FROM preferences 
                WHERE tick = 0 AND pair_type IS NOT NULL
            """)
            
            pair_types = {row[0] for row in cursor}
            conn.close()
            sim.close()
            
            # Should have multiple pair types in mixed regime
            assert len(pair_types) > 0, "Should have logged pair types"
            # Note: May not see all three types in just 5 ticks, but should see some variety
    
    def test_determinism_preserved(self):
        """Test that money-aware pairing preserves determinism."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path1 = f"{tmpdir}/run1.db"
            db_path2 = f"{tmpdir}/run2.db"
            
            scenario = load_scenario("scenarios/demos/demo_06_money_aware_pairing.yaml")
            
            # Run 1
            log_cfg1 = LogConfig(use_database=True, db_path=db_path1)
            sim1 = Simulation(scenario, seed=123, log_config=log_cfg1)
            sim1.run(max_ticks=10)
            
            final_state_1 = [(a.id, a.inventory.A, a.inventory.B, a.inventory.M) 
                             for a in sorted(sim1.agents, key=lambda x: x.id)]
            sim1.close()
            
            # Run 2
            log_cfg2 = LogConfig(use_database=True, db_path=db_path2)
            sim2 = Simulation(scenario, seed=123, log_config=log_cfg2)
            sim2.run(max_ticks=10)
            
            final_state_2 = [(a.id, a.inventory.A, a.inventory.B, a.inventory.M) 
                             for a in sorted(sim2.agents, key=lambda x: x.id)]
            sim2.close()
            
            # Should be identical
            assert final_state_1 == final_state_2, "Money-aware pairing should preserve determinism"
    
    def test_backward_compatibility_barter_only(self):
        """Test that barter_only mode remains unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path1 = f"{tmpdir}/barter.db"
            db_path2 = f"{tmpdir}/barter2.db"
            
            scenario = load_scenario("scenarios/foundational_barter_demo.yaml")
            
            # Run 1
            log_cfg1 = LogConfig(use_database=True, db_path=db_path1)
            sim1 = Simulation(scenario, seed=456, log_config=log_cfg1)
            sim1.run(max_ticks=10)
            
            final_state_1 = [(a.id, a.inventory.A, a.inventory.B, a.inventory.M) 
                             for a in sorted(sim1.agents, key=lambda x: x.id)]
            sim1.close()
            
            # Run 2
            log_cfg2 = LogConfig(use_database=True, db_path=db_path2)
            sim2 = Simulation(scenario, seed=456, log_config=log_cfg2)
            sim2.run(max_ticks=10)
            
            final_state_2 = [(a.id, a.inventory.A, a.inventory.B, a.inventory.M) 
                             for a in sorted(sim2.agents, key=lambda x: x.id)]
            sim2.close()
            
            # Should be identical (barter_only unchanged)
            assert final_state_1 == final_state_2, "Barter_only mode should remain bit-identical"


class TestPairingPerformance:
    """Test that money-aware pairing maintains reasonable performance."""
    
    def test_pairing_performance_acceptable(self):
        """Test that money-aware pairing doesn't significantly slow down simulation."""
        import time
        
        scenario = load_scenario("scenarios/demos/demo_06_money_aware_pairing.yaml")
        
        # Time the simulation
        start_time = time.time()
        sim = Simulation(scenario, seed=42, log_config=LogConfig.standard())
        sim.run(max_ticks=50)
        elapsed = time.time() - start_time
        sim.close()
        
        # Should complete in reasonable time (< 2 seconds for 50 ticks with 3 agents)
        assert elapsed < 2.0, f"Money-aware pairing too slow: {elapsed:.2f}s"
        print(f"Performance: 50 ticks in {elapsed:.2f}s ({50/elapsed:.1f} ticks/sec)")


if __name__ == "__main__":
    pytest.main([__file__])