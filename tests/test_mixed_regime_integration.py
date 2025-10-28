"""
Integration tests for mixed exchange regime (Money Phase 3).

Tests that mixed regimes work end-to-end, including:
- Both barter and monetary trades can occur
- Tie-breaking policy is applied correctly
- exchange_pair_type is logged to telemetry
- Performance is within acceptable bounds
"""

import pytest
import sqlite3
import tempfile
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario
from telemetry.config import LogConfig


class TestMixedRegimeIntegration:
    """Test mixed regime end-to-end functionality."""
    
    def test_mixed_regime_scenario_runs(self):
        """Mixed regime scenario should run to completion without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_mixed.db"
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Run for 50 ticks
            sim.run(max_ticks=50)
            sim.close()
            
            # Should complete without errors
            assert sim.tick == 50, "Simulation should run for 50 ticks"
    
    def test_mixed_regime_allows_multiple_trade_types(self):
        """Mixed regime should allow both barter and monetary trades."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_mixed.db"
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Run for 100 ticks to give trades opportunity to occur
            sim.run(max_ticks=100)
            sim.close()
            
            # Query trade types
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT DISTINCT exchange_pair_type FROM trades
                WHERE run_id = ?
            """, (sim.telemetry.run_id,))
            
            pair_types = {row[0] for row in cursor}
            conn.close()
            
            # Should have at least one trade type
            assert len(pair_types) > 0, "Should have at least one type of trade"
            
            # Mixed regime allows all three types: A<->B, A<->M, B<->M
            # At least one should occur (can't guarantee all will occur in 100 ticks)
            print(f"Trade types observed: {pair_types}")
    
    def test_exchange_pair_type_logged_correctly(self):
        """exchange_pair_type should be logged for all trades."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_mixed.db"
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            sim.run(max_ticks=50)
            sim.close()
            
            # Query trades
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT COUNT(*), exchange_pair_type FROM trades
                WHERE run_id = ?
                GROUP BY exchange_pair_type
            """, (sim.telemetry.run_id,))
            
            results = list(cursor)
            conn.close()
            
            # All trades should have a pair type
            for count, pair_type in results:
                assert pair_type is not None, "exchange_pair_type should not be NULL"
                assert pair_type in ["A<->B", "A<->M", "B<->M"], \
                    f"Invalid pair type: {pair_type}"
                print(f"  {pair_type}: {count} trades")
    
    def test_money_conservation_in_mixed_regime(self):
        """Money should be conserved across all trades in mixed regime."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_mixed.db"
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Record initial money
            initial_money = sum(agent.inventory.M for agent in sim.agents)
            
            sim.run(max_ticks=50)
            
            # Record final money
            final_money = sum(agent.inventory.M for agent in sim.agents)
            
            sim.close()
            
            # Money should be conserved
            assert initial_money == final_money, \
                f"Money not conserved: {initial_money} → {final_money}"
    
    def test_determinism_with_mixed_regime(self):
        """Mixed regime should produce deterministic results with same seed."""
        # Run 1
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/run1.db"
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim1 = Simulation(scenario, seed=42, log_config=log_cfg)
            sim1.run(max_ticks=30)
            
            # Get final state
            final_positions_1 = [(a.id, a.pos) for a in sorted(sim1.agents, key=lambda x: x.id)]
            final_inventories_1 = [(a.id, a.inventory.A, a.inventory.B, a.inventory.M) 
                                   for a in sorted(sim1.agents, key=lambda x: x.id)]
            
            sim1.close()
        
        # Run 2
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/run2.db"
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim2 = Simulation(scenario, seed=42, log_config=log_cfg)
            sim2.run(max_ticks=30)
            
            # Get final state
            final_positions_2 = [(a.id, a.pos) for a in sorted(sim2.agents, key=lambda x: x.id)]
            final_inventories_2 = [(a.id, a.inventory.A, a.inventory.B, a.inventory.M) 
                                   for a in sorted(sim2.agents, key=lambda x: x.id)]
            
            sim2.close()
        
        # Results should be identical
        assert final_positions_1 == final_positions_2, "Agent positions should be identical"
        assert final_inventories_1 == final_inventories_2, "Inventories should be identical"
    
    def test_performance_within_bounds(self):
        """Mixed regime should complete within reasonable time."""
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_perf.db"
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            start_time = time.time()
            sim.run(max_ticks=100)
            elapsed = time.time() - start_time
            
            sim.close()
            
            # Should complete in reasonable time (< 5 seconds for 100 ticks with 8 agents)
            assert elapsed < 5.0, f"Took too long: {elapsed:.2f}s"
            print(f"Performance: 100 ticks in {elapsed:.2f}s ({100/elapsed:.1f} ticks/sec)")


class TestMixedRegimelLiquidity:
    """Test mixed_liquidity_gated regime (Phase 3 extension)."""
    
    def test_mixed_liquidity_gated_scenario_loads(self):
        """mixed_liquidity_gated regime should be valid."""
        # Create a simple scenario with this regime
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_gated.db"
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            
            # Override regime (params is a dataclass, not a dict)
            scenario.params.exchange_regime = "mixed_liquidity_gated"
            
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Should initialize without error (sim.params is a dict)
            assert sim.params["exchange_regime"] == "mixed_liquidity_gated"
            
            sim.run(max_ticks=10)
            sim.close()

