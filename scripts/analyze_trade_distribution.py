#!/usr/bin/env python3
"""
Analyze trade pair type distribution from VMT telemetry database.

Usage:
    python scripts/analyze_trade_distribution.py <db_path> <run_id>

Example:
    python scripts/analyze_trade_distribution.py runs.db 1
"""

import sys
import sqlite3
from pathlib import Path


def analyze_pair_distribution(db_path: str, run_id: int) -> dict:
    """
    Analyze distribution of exchange pair types in a simulation run.
    
    Args:
        db_path: Path to SQLite telemetry database
        run_id: Run ID to analyze
        
    Returns:
        Dictionary mapping pair type to count
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    
    # Get total trade count
    cursor = conn.execute("""
        SELECT COUNT(*) FROM trades WHERE run_id = ?
    """, (run_id,))
    total_trades = cursor.fetchone()[0]
    
    if total_trades == 0:
        print(f"No trades found for run_id {run_id}")
        conn.close()
        return {}
    
    # Get pair type distribution
    cursor = conn.execute("""
        SELECT exchange_pair_type, COUNT(*) as count
        FROM trades
        WHERE run_id = ?
        GROUP BY exchange_pair_type
        ORDER BY count DESC
    """, (run_id,))
    
    results = {}
    for pair_type, count in cursor:
        results[pair_type] = count
    
    conn.close()
    return results


def print_distribution(distribution: dict, total: int):
    """Print formatted distribution table."""
    print(f"\n{'Exchange Pair':<15} {'Count':>10} {'Percentage':>12}")
    print("-" * 40)
    
    for pair_type, count in sorted(distribution.items(), key=lambda x: -x[1]):
        percentage = (count / total) * 100
        print(f"{pair_type:<15} {count:>10} {percentage:>11.1f}%")
    
    print("-" * 40)
    print(f"{'Total':<15} {total:>10} {100.0:>11.1f}%")


def get_regime_info(db_path: str, run_id: int) -> str:
    """Get exchange regime from run metadata."""
    conn = sqlite3.connect(db_path)
    
    try:
        cursor = conn.execute("""
            SELECT exchange_regime FROM tick_states 
            WHERE run_id = ? 
            LIMIT 1
        """, (run_id,))
        
        result = cursor.fetchone()
        regime = result[0] if result else "unknown"
    except sqlite3.OperationalError:
        regime = "unknown"
    finally:
        conn.close()
    
    return regime


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    try:
        run_id = int(sys.argv[2])
    except ValueError:
        print(f"Error: run_id must be an integer, got '{sys.argv[2]}'")
        sys.exit(1)
    
    try:
        # Get regime info
        regime = get_regime_info(db_path, run_id)
        
        print(f"\n{'=' * 40}")
        print(f"Trade Distribution Analysis")
        print(f"{'=' * 40}")
        print(f"Database: {db_path}")
        print(f"Run ID: {run_id}")
        print(f"Exchange Regime: {regime}")
        
        # Analyze distribution
        distribution = analyze_pair_distribution(db_path, run_id)
        
        if not distribution:
            sys.exit(0)
        
        total = sum(distribution.values())
        
        # Print results
        print_distribution(distribution, total)
        
        # Additional insights
        print(f"\n{'Insights:'}")
        
        if regime == "mixed":
            monetary_count = sum(
                count for pair_type, count in distribution.items() 
                if "M" in pair_type
            )
            barter_count = sum(
                count for pair_type, count in distribution.items() 
                if "M" not in pair_type
            )
            
            if monetary_count > 0 and barter_count > 0:
                ratio = monetary_count / barter_count
                print(f"  - Monetary/Barter ratio: {ratio:.2f}")
                print(f"  - Monetary trades: {monetary_count} ({monetary_count/total*100:.1f}%)")
                print(f"  - Barter trades: {barter_count} ({barter_count/total*100:.1f}%)")
            elif monetary_count > 0:
                print(f"  - Only monetary trades occurred (100%)")
            elif barter_count > 0:
                print(f"  - Only barter trades occurred (100%)")
        
        elif regime == "money_only":
            if all("M" in pt for pt in distribution.keys()):
                print(f"  - ✓ Correctly restricted to monetary trades only")
            else:
                print(f"  - ⚠ Warning: Non-monetary trades found in money_only regime")
        
        elif regime == "barter_only":
            if all("M" not in pt for pt in distribution.keys()):
                print(f"  - ✓ Correctly restricted to barter trades only")
            else:
                print(f"  - ⚠ Warning: Monetary trades found in barter_only regime")
        
        print()
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

