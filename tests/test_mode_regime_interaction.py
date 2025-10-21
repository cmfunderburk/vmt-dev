"""
Tests for mode × regime interaction (Money Phase 3).

Verifies the two-layer control architecture:
- Temporal control (mode_schedule): WHEN activities occur
- Type control (exchange_regime): WHAT bilateral exchanges are permitted
"""

import pytest
import sqlite3
import tempfile
from src.vmt_engine.simulation import Simulation
from src.scenarios.loader import load_scenario
from src.telemetry.config import LogConfig


class TestModeRegimeInteraction:
    """Test two-layer control: mode_schedule × exchange_regime."""
    
    def test_forage_mode_blocks_all_trades(self):
        """Forage mode should block all trades regardless of exchange regime."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_forage.db"
            scenario = load_scenario("scenarios/money_test_mode_interaction.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Run through first forage cycle (10 ticks)
            sim.run(max_ticks=10)
            
            # Check that no trades occurred during forage mode
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM trades 
                WHERE run_id = ? AND tick <= 10
            """, (sim.telemetry.run_id,))
            
            trade_count = cursor.fetchone()[0]
            conn.close()
            sim.close()
            
            # Should have zero trades during forage mode
            assert trade_count == 0, \
                f"No trades should occur in forage mode, but found {trade_count}"
    
    def test_trade_mode_respects_regime(self):
        """Trade mode should allow trades according to exchange_regime."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_trade.db"
            scenario = load_scenario("scenarios/money_test_mode_interaction.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Run through forage cycle (10 ticks) + into trade cycle
            sim.run(max_ticks=25)
            
            # Check that trades occurred during trade mode (ticks 11-25)
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM trades 
                WHERE run_id = ? AND tick > 10 AND tick <= 25
            """, (sim.telemetry.run_id,))
            
            trade_count = cursor.fetchone()[0]
            conn.close()
            sim.close()
            
            # Should have some trades during trade mode
            assert trade_count > 0, \
                "Trades should occur during trade mode"
    
    def test_active_pairs_empty_in_forage_mode(self):
        """_get_active_exchange_pairs() should return [] in forage mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_pairs.db"
            scenario = load_scenario("scenarios/money_test_mode_interaction.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Check at tick 0 (forage mode)
            sim.step()  # Tick 0
            assert sim.current_mode == "forage", "Should start in forage mode"
            
            active_pairs = sim._get_active_exchange_pairs()
            assert active_pairs == [], \
                f"Forage mode should have no active pairs, got {active_pairs}"
            
            sim.close()
    
    def test_active_pairs_from_regime_in_trade_mode(self):
        """_get_active_exchange_pairs() should return regime pairs in trade mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_pairs.db"
            scenario = load_scenario("scenarios/money_test_mode_interaction.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Advance to trade mode (after 10 forage ticks)
            sim.run(max_ticks=11)
            assert sim.current_mode == "trade", f"Should be in trade mode, got {sim.current_mode}"
            
            active_pairs = sim._get_active_exchange_pairs()
            
            # Mixed regime should return all three pairs
            expected = ["A<->M", "B<->M", "A<->B"]
            assert set(active_pairs) == set(expected), \
                f"Mixed regime in trade mode should have {expected}, got {active_pairs}"
            
            sim.close()
    
    def test_mode_transitions_logged_to_telemetry(self):
        """Mode transitions should be logged in tick_states table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_transitions.db"
            scenario = load_scenario("scenarios/money_test_mode_interaction.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Run through one full cycle (10 forage + 15 trade = 25 ticks)
            sim.run(max_ticks=25)
            sim.close()
            
            # Query mode changes from telemetry
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT tick, current_mode FROM tick_states
                WHERE run_id = ?
                ORDER BY tick
            """, (sim.telemetry.run_id,))
            
            modes = list(cursor)
            conn.close()
            
            # Verify mode sequence
            assert modes[0][1] == "forage", "Should start in forage mode"
            
            # Find transition to trade mode (should be at tick 10)
            trade_mode_start = next((tick for tick, mode in modes if mode == "trade"), None)
            assert trade_mode_start is not None, "Should transition to trade mode"
            assert trade_mode_start == 10, f"Trade mode should start at tick 10, got {trade_mode_start}"
    
    def test_mode_regime_with_barter_only(self):
        """Mode schedule should work correctly with barter_only regime."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_barter_mode.db"
            
            # Load mixed scenario but override to barter_only
            scenario = load_scenario("scenarios/money_test_mode_interaction.yaml")
            scenario.params.exchange_regime = "barter_only"
            
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Run through trade mode
            sim.run(max_ticks=25)
            
            # Check active pairs in trade mode
            active_pairs = sim._get_active_exchange_pairs()
            assert active_pairs == ["A<->B"], \
                f"Barter-only should have only A<->B pair, got {active_pairs}"
            
            # Query trades
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT DISTINCT exchange_pair_type FROM trades
                WHERE run_id = ? AND tick > 10
            """, (sim.telemetry.run_id,))
            
            pair_types = {row[0] for row in cursor}
            conn.close()
            sim.close()
            
            # Should only have barter trades (if any)
            for pair_type in pair_types:
                assert "M" not in pair_type, \
                    f"Barter-only should not have money trades, got {pair_type}"
    
    def test_mode_regime_with_money_only(self):
        """Mode schedule should work correctly with money_only regime."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_money_mode.db"
            
            # Load mixed scenario but override to money_only
            scenario = load_scenario("scenarios/money_test_mode_interaction.yaml")
            scenario.params.exchange_regime = "money_only"
            
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Run through trade mode
            sim.run(max_ticks=25)
            
            # Check active pairs in trade mode
            active_pairs = sim._get_active_exchange_pairs()
            expected = ["A<->M", "B<->M"]
            assert set(active_pairs) == set(expected), \
                f"Money-only should have {expected}, got {active_pairs}"
            
            # Query trades
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT DISTINCT exchange_pair_type FROM trades
                WHERE run_id = ? AND tick > 10
            """, (sim.telemetry.run_id,))
            
            pair_types = {row[0] for row in cursor}
            conn.close()
            sim.close()
            
            # Should only have monetary trades (if any)
            for pair_type in pair_types:
                assert "M" in pair_type, \
                    f"Money-only should only have money trades, got {pair_type}"


class TestModeScheduleIntegration:
    """Test mode schedule integration with exchange regimes."""
    
    def test_both_mode_allows_trading(self):
        """'both' mode should allow trading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_both.db"
            
            # Load scenario without mode_schedule (defaults to 'both')
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Should be in 'both' mode
            assert sim.current_mode == "both", "No mode_schedule should default to 'both'"
            
            # Active pairs should be present
            active_pairs = sim._get_active_exchange_pairs()
            assert len(active_pairs) > 0, "'both' mode should have active pairs"
            
            sim.run(max_ticks=10)
            sim.close()
    
    def test_full_cycle_transitions(self):
        """Test full cycle of mode transitions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_cycle.db"
            scenario = load_scenario("scenarios/money_test_mode_interaction.yaml")
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Run two full cycles (10 forage + 15 trade) × 2 = 50 ticks
            sim.run(max_ticks=50)
            sim.close()
            
            # Query mode sequence
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("""
                SELECT tick, current_mode FROM tick_states
                WHERE run_id = ?
                ORDER BY tick
            """, (sim.telemetry.run_id,))
            
            modes = list(cursor)
            conn.close()
            
            # Verify cycle repeats
            # Ticks 0-9: forage
            # Ticks 10-24: trade
            # Ticks 25-34: forage (second cycle)
            # Ticks 35-49: trade (second cycle)
            
            assert modes[0][1] == "forage"  # Tick 0
            assert modes[10][1] == "trade"  # Tick 10
            assert modes[25][1] == "forage"  # Tick 25 (second forage)
            assert modes[35][1] == "trade"  # Tick 35 (second trade)


class TestEdgeCases:
    """Test edge cases in mode × regime interaction."""
    
    def test_unknown_regime_returns_empty_pairs(self):
        """Unknown exchange regime should return empty active pairs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_unknown.db"
            scenario = load_scenario("scenarios/money_test_mixed.yaml")
            
            # Override to unknown regime
            scenario.params.exchange_regime = "unknown_regime"
            
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            # Should return empty list
            active_pairs = sim._get_active_exchange_pairs()
            assert active_pairs == [], \
                f"Unknown regime should return empty pairs, got {active_pairs}"
            
            sim.close()
    
    def test_mode_none_defaults_to_both(self):
        """Scenario without mode_schedule should default to 'both' mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_default.db"
            scenario = load_scenario("scenarios/money_test_basic.yaml")  # No mode_schedule
            
            log_cfg = LogConfig(use_database=True, db_path=db_path)
            sim = Simulation(scenario, seed=42, log_config=log_cfg)
            
            assert sim.current_mode == "both", \
                f"Should default to 'both' mode, got {sim.current_mode}"
            
            # Active pairs should be present
            active_pairs = sim._get_active_exchange_pairs()
            assert len(active_pairs) > 0, "'both' mode should have active pairs"
            
            sim.close()

