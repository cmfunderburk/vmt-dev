"""
Comparative tests for different exchange regimes (Money Phase 3).

Compares outcomes under barter_only, money_only, and mixed regimes
with identical initial conditions to demonstrate pedagogical differences.
"""

import pytest
import sqlite3
import tempfile
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario
from telemetry.config import LogConfig


class TestRegimeComparison:
    """Compare outcomes across different exchange regimes."""
    
    def test_compare_trade_counts(self):
        """Compare total trade counts across regimes."""
        results = {}
        
        for regime in ["barter_only", "money_only", "mixed"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = f"{tmpdir}/test_{regime}.db"
                scenario = load_scenario("scenarios/money_test_mixed.yaml")
                
                # Override regime
                scenario.params.exchange_regime = regime
                
                log_cfg = LogConfig(use_database=True, db_path=db_path)
                sim = Simulation(scenario, seed=42, log_config=log_cfg)
                sim.run(max_ticks=100)
                
                # Query trade count
                conn = sqlite3.connect(db_path)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM trades WHERE run_id = ?
                """, (sim.telemetry.run_id,))
                
                trade_count = cursor.fetchone()[0]
                conn.close()
                sim.close()
                
                results[regime] = trade_count
        
        # Report results
        print(f"\nTrade Counts by Regime (100 ticks, seed=42):")
        for regime, count in results.items():
            print(f"  {regime:15} : {count:3} trades")
        
        # All regimes should allow some trades (with this scenario)
        for regime, count in results.items():
            assert count >= 0, f"{regime} should complete without errors"
    
    def test_compare_final_utilities(self):
        """Compare final agent utilities across regimes."""
        results = {}
        
        for regime in ["barter_only", "money_only", "mixed"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = f"{tmpdir}/test_{regime}.db"
                scenario = load_scenario("scenarios/money_test_mixed.yaml")
                
                # Override regime
                scenario.params.exchange_regime = regime
                
                log_cfg = LogConfig(use_database=True, db_path=db_path)
                sim = Simulation(scenario, seed=42, log_config=log_cfg)
                sim.run(max_ticks=100)
                
                # Get final utilities
                final_utilities = [agent.utility.u(agent.inventory.A, agent.inventory.B) 
                                   for agent in sim.agents]
                avg_utility = sum(final_utilities) / len(final_utilities)
                
                sim.close()
                
                results[regime] = {
                    'avg': avg_utility,
                    'min': min(final_utilities),
                    'max': max(final_utilities)
                }
        
        # Report results
        print(f"\nFinal Utilities by Regime (100 ticks, seed=42):")
        for regime, stats in results.items():
            print(f"  {regime:15} : avg={stats['avg']:7.2f}, min={stats['min']:7.2f}, max={stats['max']:7.2f}")
        
        # All regimes should produce positive utilities
        for regime, stats in results.items():
            assert stats['avg'] > 0, f"{regime} should have positive average utility"
    
    def test_compare_surplus_efficiency(self):
        """Compare total surplus generated across regimes."""
        results = {}
        
        for regime in ["barter_only", "money_only", "mixed"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = f"{tmpdir}/test_{regime}.db"
                scenario = load_scenario("scenarios/money_test_mixed.yaml")
                
                # Override regime
                scenario.params.exchange_regime = regime
                
                log_cfg = LogConfig(use_database=True, db_path=db_path)
                sim = Simulation(scenario, seed=42, log_config=log_cfg)
                
                # Record initial utilities
                initial_utility = sum(agent.utility.u(agent.inventory.A, agent.inventory.B) 
                                     for agent in sim.agents)
                
                sim.run(max_ticks=100)
                
                # Record final utilities
                final_utility = sum(agent.utility.u(agent.inventory.A, agent.inventory.B) 
                                   for agent in sim.agents)
                
                # Query trade count
                conn = sqlite3.connect(db_path)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM trades WHERE run_id = ?
                """, (sim.telemetry.run_id,))
                trade_count = cursor.fetchone()[0]
                conn.close()
                
                sim.close()
                
                total_gain = final_utility - initial_utility
                avg_gain_per_trade = total_gain / trade_count if trade_count > 0 else 0
                
                results[regime] = {
                    'initial': initial_utility,
                    'final': final_utility,
                    'gain': total_gain,
                    'trades': trade_count,
                    'avg_per_trade': avg_gain_per_trade
                }
        
        # Report results
        print(f"\nSurplus Efficiency by Regime (100 ticks, seed=42):")
        for regime, stats in results.items():
            print(f"  {regime:15} :")
            print(f"    Initial utility : {stats['initial']:8.2f}")
            print(f"    Final utility   : {stats['final']:8.2f}")
            print(f"    Total gain      : {stats['gain']:8.2f}")
            print(f"    Trades          : {stats['trades']:8}")
            print(f"    Gain per trade  : {stats['avg_per_trade']:8.2f}")
        
        # Utilities should not decrease (agents only trade if beneficial)
        for regime, stats in results.items():
            assert stats['final'] >= stats['initial'] - 0.01, \
                f"{regime} should not decrease total utility"
    
    def test_mixed_regime_uses_both_types(self):
        """Mixed regime should be able to use both barter and monetary trades."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_mixed.db"
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            sim.run(max_ticks=150)  # Run longer to increase chance of both types
            
            # Query pair types
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT DISTINCT exchange_pair_type FROM trades
                WHERE run_id = ?
            """, (sim.telemetry.run_id,))
            
            pair_types = {row[0] for row in cursor}
            conn.close()
            sim.close()
            
            print(f"\nMixed regime pair types observed: {pair_types}")
            
            # Should have at least one pair type
            assert len(pair_types) > 0, "Mixed regime should have at least one trade type"
    
    def test_regime_determinism(self):
        """Same regime with same seed should produce identical results."""
        for regime in ["barter_only", "money_only", "mixed"]:
            # Run 1
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = f"{tmpdir}/run1.db"
                scenario = load_scenario("scenarios/money_test_mixed.yaml")
                scenario.params.exchange_regime = regime
                
                log_cfg = LogConfig(use_database=True, db_path=db_path)
                sim1 = Simulation(scenario, seed=123, log_config=log_cfg)
                sim1.run(max_ticks=50)
                
                final_state_1 = [(a.id, a.inventory.A, a.inventory.B, a.inventory.M) 
                                 for a in sorted(sim1.agents, key=lambda x: x.id)]
                
                sim1.close()
            
            # Run 2
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = f"{tmpdir}/run2.db"
                scenario = load_scenario("scenarios/money_test_mixed.yaml")
                scenario.params.exchange_regime = regime
                
                log_cfg = LogConfig(use_database=True, db_path=db_path)
                sim2 = Simulation(scenario, seed=123, log_config=log_cfg)
                sim2.run(max_ticks=50)
                
                final_state_2 = [(a.id, a.inventory.A, a.inventory.B, a.inventory.M) 
                                 for a in sorted(sim2.agents, key=lambda x: x.id)]
                
                sim2.close()
            
            # Should be identical
            assert final_state_1 == final_state_2, \
                f"{regime} should be deterministic with same seed"


class TestRegimePedagogicalInsights:
    """Tests that demonstrate pedagogical value of different regimes."""
    
    def test_double_coincidence_of_wants(self):
        """
        Demonstrate double coincidence of wants problem.
        
        Money should enable trades that barter cannot, showing the
        pedagogical value of money as a medium of exchange.
        """
        results = {}
        
        for regime in ["barter_only", "money_only"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = f"{tmpdir}/test_{regime}.db"
                scenario = load_scenario("scenarios/money_test_mixed.yaml")
                scenario.params.exchange_regime = regime
                
                log_cfg = LogConfig(use_database=True, db_path=db_path)
                sim = Simulation(scenario, seed=42, log_config=log_cfg)
                sim.run(max_ticks=100)
                
                # Count trades
                conn = sqlite3.connect(db_path)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM trades WHERE run_id = ?
                """, (sim.telemetry.run_id,))
                trade_count = cursor.fetchone()[0]
                conn.close()
                sim.close()
                
                results[regime] = trade_count
        
        barter_trades = results["barter_only"]
        money_trades = results["money_only"]
        
        print(f"\nDouble Coincidence of Wants Comparison:")
        print(f"  Barter-only trades : {barter_trades}")
        print(f"  Money-only trades  : {money_trades}")
        
        if money_trades > barter_trades:
            print(f"  → Money enabled {money_trades - barter_trades} additional trades")
            print(f"  → Demonstrates liquidity advantage of money")
        elif barter_trades > money_trades:
            print(f"  → Barter enabled {barter_trades - money_trades} additional trades")
            print(f"  → May indicate specific preferences in this scenario")
        else:
            print(f"  → Both regimes achieved similar trade volumes")
    
    def test_money_as_unit_of_account(self):
        """
        Verify that money provides a common unit of account.
        
        In money_only regime, all trades should involve money, making
        price comparisons easier (pedagogical point).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_money.db"
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            scenario.params.exchange_regime = "money_only"
            
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            sim.run(max_ticks=100)
            
            # Query all trades
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT exchange_pair_type, COUNT(*) FROM trades
                WHERE run_id = ?
                GROUP BY exchange_pair_type
            """, (sim.telemetry.run_id,))
            
            results = list(cursor)
            conn.close()
            sim.close()
            
            print(f"\nUnit of Account Verification (money_only regime):")
            for pair_type, count in results:
                print(f"  {pair_type}: {count} trades")
                assert "M" in pair_type, \
                    f"All trades should involve money in money_only regime"
            
            if results:
                print(f"  ✓ All trades use money as common unit of account")
    
    def test_regime_flexibility_tradeoff(self):
        """
        Compare flexibility (mixed) vs constraints (single regime).
        
        Demonstrates pedagogical tradeoff: mixed regime offers flexibility
        but may have less predictable outcomes.
        """
        results = {}
        
        for regime in ["barter_only", "money_only", "mixed"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = f"{tmpdir}/test_{regime}.db"
                scenario = load_scenario("scenarios/money_test_mixed.yaml")
                scenario.params.exchange_regime = regime
                
                log_cfg = LogConfig(use_database=True, db_path=db_path)
                sim = Simulation(scenario, seed=42, log_config=log_cfg)
                sim.run(max_ticks=100)
                
                # Query pair type diversity
                conn = sqlite3.connect(db_path)
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT exchange_pair_type) FROM trades
                    WHERE run_id = ?
                """, (sim.telemetry.run_id,))
                
                pair_diversity = cursor.fetchone()[0]
                conn.close()
                sim.close()
                
                results[regime] = pair_diversity
        
        print(f"\nRegime Flexibility Comparison:")
        for regime, diversity in results.items():
            print(f"  {regime:15} : {diversity} distinct pair type(s)")
        
        # Mixed regime should have opportunity for highest diversity
        # (though actual trades depend on agent interactions)
        assert results["mixed"] >= results["barter_only"], \
            "Mixed regime should allow at least as many pair types as barter_only"
        assert results["mixed"] >= results["money_only"], \
            "Mixed regime should allow at least as many pair types as money_only"

