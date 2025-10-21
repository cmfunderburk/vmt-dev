"""
CSV export functionality for backward compatibility.
"""

import csv
from pathlib import Path
from typing import Optional

from telemetry.database import TelemetryDatabase
from .queries import QueryBuilder


def export_run_to_csv(db: TelemetryDatabase, run_id: int, output_dir: str):
    """
    Export a simulation run to CSV files (legacy format).
    
    Args:
        db: Database connection
        run_id: Run ID to export
        output_dir: Directory to write CSV files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Export agent snapshots
    export_agent_snapshots(db, run_id, output_path / "agent_snapshots.csv")
    
    # Export resource snapshots
    export_resource_snapshots(db, run_id, output_path / "resource_snapshots.csv")
    
    # Export decisions
    export_decisions(db, run_id, output_path / "decisions.csv")
    
    # Export trades
    export_trades(db, run_id, output_path / "trades.csv")
    
    # Export trade attempts if available
    export_trade_attempts(db, run_id, output_path / "trade_attempts.csv")


def export_agent_snapshots(db: TelemetryDatabase, run_id: int, output_file: Path):
    """Export agent snapshots to CSV (with money columns)."""
    query = """
        SELECT tick, agent_id as id, x, y, inventory_A as A, inventory_B as B, 
               inventory_M as M, utility as U,
               ask_A_in_B, bid_A_in_B, p_min, p_max,
               target_agent_id, target_x, target_y, utility_type, lambda_money
        FROM agent_snapshots
        WHERE run_id = ?
        ORDER BY tick, agent_id
    """
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'tick', 'id', 'x', 'y', 'A', 'B', 'M', 'U',
            'ask_A_in_B', 'bid_A_in_B', 'p_min', 'p_max',
            'target_agent_id', 'target_x', 'target_y', 'utility_type', 'lambda_money'
        ])
        
        cursor = db.execute(query, (run_id,))
        for row in cursor:
            writer.writerow([
                row['tick'], row['id'], row['x'], row['y'],
                row['A'], row['B'], row['M'], f"{row['U']:.6f}",
                f"{row['ask_A_in_B']:.6f}", f"{row['bid_A_in_B']:.6f}",
                f"{row['p_min']:.6f}", f"{row['p_max']:.6f}",
                row['target_agent_id'] or '', row['target_x'] or '', 
                row['target_y'] or '', row['utility_type'],
                f"{row['lambda_money']:.6f}" if row['lambda_money'] is not None else ''
            ])


def export_resource_snapshots(db: TelemetryDatabase, run_id: int, output_file: Path):
    """Export resource snapshots to CSV."""
    query = """
        SELECT tick, x || '_' || y as cell_id, x, y, resource_type, amount
        FROM resource_snapshots
        WHERE run_id = ?
        ORDER BY tick, x, y
    """
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['tick', 'cell_id', 'x', 'y', 'resource_type', 'amount'])
        
        cursor = db.execute(query, (run_id,))
        for row in cursor:
            writer.writerow([
                row['tick'], row['cell_id'], row['x'], row['y'],
                row['resource_type'], row['amount']
            ])


def export_decisions(db: TelemetryDatabase, run_id: int, output_file: Path):
    """Export decisions to CSV."""
    query = """
        SELECT tick, agent_id, chosen_partner_id, surplus_with_partner,
               target_type, target_x, target_y, num_neighbors, alternatives
        FROM decisions
        WHERE run_id = ?
        ORDER BY tick, agent_id
    """
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'tick', 'agent_id', 'chosen_partner_id', 'surplus_with_partner',
            'target_type', 'target_x', 'target_y', 'num_neighbors', 'alternatives'
        ])
        
        cursor = db.execute(query, (run_id,))
        for row in cursor:
            writer.writerow([
                row['tick'], row['agent_id'],
                row['chosen_partner_id'] or '',
                f"{row['surplus_with_partner']:.6f}" if row['surplus_with_partner'] else '',
                row['target_type'],
                row['target_x'] or '', row['target_y'] or '',
                row['num_neighbors'], row['alternatives'] or ''
            ])


def export_trades(db: TelemetryDatabase, run_id: int, output_file: Path):
    """Export trades to CSV (with money columns)."""
    query = """
        SELECT tick, x, y, buyer_id, seller_id, dA, dB, dM, price, direction,
               buyer_lambda, seller_lambda, exchange_pair_type
        FROM trades
        WHERE run_id = ?
        ORDER BY tick
    """
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'tick', 'x', 'y', 'buyer_id', 'seller_id',
            'dA', 'dB', 'dM', 'price', 'direction',
            'buyer_lambda', 'seller_lambda', 'exchange_pair_type'
        ])
        
        cursor = db.execute(query, (run_id,))
        for row in cursor:
            writer.writerow([
                row['tick'], row['x'], row['y'],
                row['buyer_id'], row['seller_id'],
                row['dA'], row['dB'], row['dM'], f"{row['price']:.6f}",
                row['direction'],
                f"{row['buyer_lambda']:.6f}" if row['buyer_lambda'] is not None else '',
                f"{row['seller_lambda']:.6f}" if row['seller_lambda'] is not None else '',
                row['exchange_pair_type']
            ])


def export_trade_attempts(db: TelemetryDatabase, run_id: int, output_file: Path):
    """Export trade attempts to CSV (if available)."""
    query = """
        SELECT tick, buyer_id, seller_id, direction, price,
               buyer_ask, buyer_bid, seller_ask, seller_bid, surplus,
               dA_attempted, dB_calculated,
               buyer_A_init, buyer_B_init, buyer_U_init,
               buyer_A_final, buyer_B_final, buyer_U_final, buyer_improves,
               seller_A_init, seller_B_init, seller_U_init,
               seller_A_final, seller_B_final, seller_U_final, seller_improves,
               buyer_feasible, seller_feasible, result, result_reason
        FROM trade_attempts
        WHERE run_id = ?
        ORDER BY tick, id
    """
    
    # Check if there are any trade attempts
    count_query = "SELECT COUNT(*) as count FROM trade_attempts WHERE run_id = ?"
    result = db.execute(count_query, (run_id,)).fetchone()
    
    if result['count'] == 0:
        # Don't create empty file
        return
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'tick', 'buyer_id', 'seller_id', 'direction', 'price',
            'buyer_ask', 'buyer_bid', 'seller_ask', 'seller_bid', 'surplus',
            'dA_attempted', 'dB_calculated',
            'buyer_A_init', 'buyer_B_init', 'buyer_U_init',
            'buyer_A_final', 'buyer_B_final', 'buyer_U_final', 'buyer_improves',
            'seller_A_init', 'seller_B_init', 'seller_U_init',
            'seller_A_final', 'seller_B_final', 'seller_U_final', 'seller_improves',
            'buyer_feasible', 'seller_feasible', 'result', 'result_reason'
        ])
        
        cursor = db.execute(query, (run_id,))
        for row in cursor:
            writer.writerow([
                row['tick'], row['buyer_id'], row['seller_id'],
                row['direction'], f"{row['price']:.6f}",
                f"{row['buyer_ask']:.6f}", f"{row['buyer_bid']:.6f}",
                f"{row['seller_ask']:.6f}", f"{row['seller_bid']:.6f}",
                f"{row['surplus']:.6f}",
                row['dA_attempted'], row['dB_calculated'],
                row['buyer_A_init'], row['buyer_B_init'], f"{row['buyer_U_init']:.6f}",
                row['buyer_A_final'], row['buyer_B_final'], f"{row['buyer_U_final']:.6f}",
                bool(row['buyer_improves']),
                row['seller_A_init'], row['seller_B_init'], f"{row['seller_U_init']:.6f}",
                row['seller_A_final'], row['seller_B_final'], f"{row['seller_U_final']:.6f}",
                bool(row['seller_improves']),
                bool(row['buyer_feasible']), bool(row['seller_feasible']),
                row['result'], row['result_reason']
            ])

