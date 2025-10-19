"""
Compares two telemetry databases to verify behavioral equivalence.

This script is a critical part of the backward-compatibility test suite.
It checks that a simulation run on a legacy scenario produces identical
results before and after a code change.

It ignores columns that are expected to change (e.g., run_id, start_time)
and verifies that core behavioral data (agent positions, inventories A/B,
trades A/B) are identical.
"""
import sqlite3
import pandas as pd
import argparse

# Columns to compare for key tables
AGENT_SNAPSHOT_COLS = [
    "tick", "agent_id", "x", "y", "inventory_A", "inventory_B", "utility"
]
TRADE_COLS = ["tick", "buyer_id", "seller_id", "dA", "dB", "price", "direction"]


def compare_databases(db_path1: str, db_path2: str):
    """
    Compares two telemetry databases for behavioral equivalence.

    Args:
        db_path1: Path to the baseline (before) database.
        db_path2: Path to the current (after) database.
    """
    print(f"Comparing baseline DB '{db_path1}' with current DB '{db_path2}'...")

    try:
        with sqlite3.connect(db_path1) as conn1, sqlite3.connect(db_path2) as conn2:
            # --- Compare Agent Snapshots ---
            print("\nComparing agent_snapshots...")
            df1_agents = pd.read_sql_query("SELECT * FROM agent_snapshots ORDER BY tick, agent_id", conn1)
            df2_agents = pd.read_sql_query("SELECT * FROM agent_snapshots ORDER BY tick, agent_id", conn2)

            if len(df1_agents) != len(df2_agents):
                print(f"  ❌ FAILED: Row count mismatch. Baseline has {len(df1_agents)} rows, current has {len(df2_agents)} rows.")
                return False

            compare_df1 = df1_agents[AGENT_SNAPSHOT_COLS]
            compare_df2 = df2_agents[AGENT_SNAPSHOT_COLS]

            if not compare_df1.equals(compare_df2):
                print("  ❌ FAILED: Core agent snapshot data is not identical.")
                diff = pd.concat([compare_df1, compare_df2]).drop_duplicates(keep=False)
                print("Differences:\n", diff.to_string())
                return False
            
            print("  ✅ PASSED: Core agent snapshot data is identical.")

            # --- Compare Trades ---
            print("\nComparing trades...")
            df1_trades = pd.read_sql_query("SELECT * FROM trades ORDER BY tick, buyer_id, seller_id", conn1)
            df2_trades = pd.read_sql_query("SELECT * FROM trades ORDER BY tick, buyer_id, seller_id", conn2)

            if len(df1_trades) != len(df2_trades):
                print(f"  ❌ FAILED: Trade count mismatch. Baseline has {len(df1_trades)} trades, current has {len(df2_trades)} trades.")
                return False

            compare_df1_trades = df1_trades[TRADE_COLS]
            compare_df2_trades = df2_trades[TRADE_COLS]

            if not compare_df1_trades.equals(compare_df2_trades):
                print("  ❌ FAILED: Core trade data is not identical.")
                diff = pd.concat([compare_df1_trades, compare_df2_trades]).drop_duplicates(keep=False)
                print("Differences:\n", diff.to_string())
                return False

            print("  ✅ PASSED: Core trade data is identical.")

            # --- Check for new columns (Phase 1 specific) ---
            print("\nVerifying new columns in current DB...")
            cursor2 = conn2.cursor()
            
            # Check agent_snapshots for inventory_M
            cursor2.execute("PRAGMA table_info(agent_snapshots)")
            cols = [info[1] for info in cursor2.fetchall()]
            if "inventory_M" not in cols:
                print("  ❌ FAILED: 'inventory_M' column missing from agent_snapshots in current DB.")
                return False

            # Verify inventory_M is always 0 for this legacy run
            sum_m = pd.read_sql_query("SELECT SUM(inventory_M) as total_m FROM agent_snapshots", conn2).iloc[0]['total_m']
            if sum_m != 0:
                print(f"  ❌ FAILED: 'inventory_M' column has non-zero values (total: {sum_m}). Legacy scenario should have M=0.")
                return False
            print("  ✅ PASSED: 'inventory_M' column exists and is correctly zeroed.")

            # Check tick_states table
            try:
                # Check if table exists first
                cursor2.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tick_states'")
                if cursor2.fetchone() is None:
                    print("  ⚠️ SKIPPED: 'tick_states' table does not exist in current DB (expected in later versions).")
                else:
                    df2_tick_states = pd.read_sql_query("SELECT * FROM tick_states", conn2)
                    if not df2_tick_states.empty:
                        unique_regimes = df2_tick_states['exchange_regime'].unique()
                        if list(unique_regimes) != ['barter_only']:
                             print(f"  ❌ FAILED: tick_states.exchange_regime should only be 'barter_only', but found {unique_regimes}")
                             return False
                        print("  ✅ PASSED: 'tick_states' table exists and correctly logs 'barter_only'.")
                    else:
                        print("  ✅ PASSED: 'tick_states' table exists and is empty (as expected for runs with no mode changes).")

            except pd.io.sql.DatabaseError as e:
                print(f"  ❌ FAILED: Error querying 'tick_states' table: {e}")
                return False

    except sqlite3.Error as e:
        print(f"\nAn error occurred: {e}")
        return False

    print("\n" + "="*30)
    print("  Overall Status: SUCCESS")
    print("  Behavior is identical, and new infrastructure is correctly passive.")
    print("="*30)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two VMT telemetry databases for behavioral equivalence.")
    parser.add_argument("baseline_db", help="Path to the baseline (before) database file.")
    parser.add_argument("current_db", help="Path to the current (after) database file.")
    args = parser.parse_args()

    if not compare_databases(args.baseline_db, args.current_db):
        exit(1)
