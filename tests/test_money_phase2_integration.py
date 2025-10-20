"""
Integration tests for Phase 2 monetary exchange (money_only regime).

Verifies:
- Monetary trades occur in money_only mode
- Barter trades are blocked in money_only mode
- Money is conserved across all trades
- Determinism with fixed seed
"""

import pytest
import sqlite3
import tempfile
from src.vmt_engine.simulation import Simulation
from src.scenarios.loader import load_scenario
from src.telemetry.config import LogConfig


class TestMoneyOnlyRegime:
    """Test money_only exchange regime."""
    
    def test_monetary_trades_occur(self):
        """Should execute monetary trades in money_only mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_money_phase2.db"
            scenario = load_scenario("scenarios/money_test_basic.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Run for a few ticks
            sim.run(max_ticks=10)
            sim.close()
            
            # Check that some monetary trades occurred
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM trades 
                WHERE run_id = ? AND dM != 0
            """, (sim.telemetry.run_id,))
            
            monetary_trade_count = cursor.fetchone()[0]
            conn.close()
            
            # Should have at least one monetary trade
            assert monetary_trade_count > 0, "No monetary trades occurred in money_only mode"
    
    def test_barter_blocked_in_money_only(self):
        """Should not execute any barter trades in money_only mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_money_phase2.db"
            scenario = load_scenario("scenarios/money_test_basic.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            sim.run(max_ticks=10)
            sim.close()
            
            # Check that no barter trades occurred (dM should be non-zero in money_only)
            # Barter would have dB != 0 and dM == 0
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM trades 
                WHERE run_id = ? AND dB != 0 AND dM == 0
            """, (sim.telemetry.run_id,))
            
            barter_trade_count = cursor.fetchone()[0]
            conn.close()
            
            # Should have zero barter trades
            assert barter_trade_count == 0, f"Found {barter_trade_count} barter trades in money_only mode"
    
    def test_money_conservation(self):
        """Money should be conserved across all trades."""
        scenario = load_scenario("scenarios/money_test_basic.yaml")
        sim = Simulation(scenario, seed=42, log_config=LogConfig(use_database=False))
        
        # Initial total money
        initial_M = sum(agent.inventory.M for agent in sim.agents)
        
        # Run simulation
        sim.run(max_ticks=20)
        
        # Final total money
        final_M = sum(agent.inventory.M for agent in sim.agents)
        
        # Should be conserved
        assert initial_M == final_M, \
            f"Money not conserved: {initial_M} → {final_M}"
    
    def test_determinism_with_fixed_seed(self):
        """Same seed should produce identical results."""
        # Run 1
        scenario1 = load_scenario("scenarios/money_test_basic.yaml")
        sim1 = Simulation(scenario1, seed=42, log_config=LogConfig(use_database=False))
        sim1.run(max_ticks=15)
        
        final_inventories_1 = [
            (a.inventory.A, a.inventory.B, a.inventory.M) 
            for a in sorted(sim1.agents, key=lambda x: x.id)
        ]
        
        # Run 2
        scenario2 = load_scenario("scenarios/money_test_basic.yaml")
        sim2 = Simulation(scenario2, seed=42, log_config=LogConfig(use_database=False))
        sim2.run(max_ticks=15)
        
        final_inventories_2 = [
            (a.inventory.A, a.inventory.B, a.inventory.M) 
            for a in sorted(sim2.agents, key=lambda x: x.id)
        ]
        
        # Should be identical
        assert final_inventories_1 == final_inventories_2, \
            "Determinism violated: same seed produced different results"
    
    def test_scenario_loads_and_runs(self):
        """Scenario should load and run without errors."""
        scenario = load_scenario("scenarios/money_test_basic.yaml")
        sim = Simulation(scenario, seed=42, log_config=LogConfig(use_database=False))
        
        # Run should not raise
        sim.run(max_ticks=10)
        
        # Should have 3 agents
        assert len(sim.agents) == 3
        
        # exchange_regime should be money_only
        assert sim.params.get('exchange_regime') == 'money_only'


class TestMoneyTelemetry:
    """Test that monetary trades are properly logged."""
    
    def test_trade_direction_logged(self):
        """Trade direction should indicate monetary exchange."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_money_phase2.db"
            scenario = load_scenario("scenarios/money_test_basic.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            sim.run(max_ticks=10)
            sim.close()
            
            # Query trades
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT direction FROM trades WHERE run_id = ?
            """, (sim.telemetry.run_id,))
            
            directions = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if len(directions) > 0:
                # Should have monetary trade directions
                monetary_directions = [d for d in directions if '_for_M' in d]
                assert len(monetary_directions) > 0, "No monetary trade directions logged"
    
    def test_trade_prices_reasonable(self):
        """Logged trade prices should be positive and reasonable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_money_phase2.db"
            scenario = load_scenario("scenarios/money_test_basic.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            sim.run(max_ticks=10)
            sim.close()
            
            # Query trade prices
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT price FROM trades WHERE run_id = ?
            """, (sim.telemetry.run_id,))
            
            prices = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if len(prices) > 0:
                # All prices should be positive
                assert all(p > 0 for p in prices), "Found non-positive trade price"
                
                # Prices should be reasonable (not astronomical)
                assert all(p < 1000 for p in prices), "Found unreasonably high price"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

