"""
SQL query builders for log viewer.
"""

from typing import Optional


class QueryBuilder:
    """Builds SQL queries for telemetry analysis."""
    
    @staticmethod
    def get_tick_range(run_id: int) -> tuple[str, tuple]:
        """Get the min and max ticks for a run."""
        query = """
            SELECT MIN(tick) as min_tick, MAX(tick) as max_tick
            FROM agent_snapshots
            WHERE run_id = ?
        """
        return query, (run_id,)
    
    @staticmethod
    def get_agent_ids(run_id: int) -> tuple[str, tuple]:
        """Get all unique agent IDs in a run."""
        query = """
            SELECT DISTINCT agent_id
            FROM agent_snapshots
            WHERE run_id = ?
            ORDER BY agent_id
        """
        return query, (run_id,)
    
    @staticmethod
    def get_agent_snapshot(run_id: int, agent_id: int, tick: int) -> tuple[str, tuple]:
        """Get agent state at a specific tick."""
        query = """
            SELECT *
            FROM agent_snapshots
            WHERE run_id = ? AND agent_id = ? AND tick = ?
        """
        return query, (run_id, agent_id, tick)
    
    @staticmethod
    def get_all_agents_at_tick(run_id: int, tick: int) -> tuple[str, tuple]:
        """Get all agent states at a specific tick."""
        query = """
            SELECT *
            FROM agent_snapshots
            WHERE run_id = ? AND tick = ?
            ORDER BY agent_id
        """
        return query, (run_id, tick)
    
    @staticmethod
    def get_agent_trajectory(run_id: int, agent_id: int, 
                            start_tick: Optional[int] = None,
                            end_tick: Optional[int] = None) -> tuple[str, tuple]:
        """Get agent's position over time."""
        query = """
            SELECT tick, x, y, inventory_A, inventory_B, utility
            FROM agent_snapshots
            WHERE run_id = ? AND agent_id = ?
        """
        params = [run_id, agent_id]
        
        if start_tick is not None:
            query += " AND tick >= ?"
            params.append(start_tick)
        if end_tick is not None:
            query += " AND tick <= ?"
            params.append(end_tick)
        
        query += " ORDER BY tick"
        return query, tuple(params)
    
    @staticmethod
    def get_trades_at_tick(run_id: int, tick: int) -> tuple[str, tuple]:
        """Get all trades at a specific tick."""
        query = """
            SELECT *
            FROM trades
            WHERE run_id = ? AND tick = ?
        """
        return query, (run_id, tick)
    
    @staticmethod
    def get_trades_by_agent(run_id: int, agent_id: int,
                           start_tick: Optional[int] = None,
                           end_tick: Optional[int] = None) -> tuple[str, tuple]:
        """Get all trades involving a specific agent."""
        query = """
            SELECT *
            FROM trades
            WHERE run_id = ? AND (buyer_id = ? OR seller_id = ?)
        """
        params = [run_id, agent_id, agent_id]
        
        if start_tick is not None:
            query += " AND tick >= ?"
            params.append(start_tick)
        if end_tick is not None:
            query += " AND tick <= ?"
            params.append(end_tick)
        
        query += " ORDER BY tick"
        return query, tuple(params)
    
    @staticmethod
    def get_trades_in_range(run_id: int, start_tick: int, end_tick: int) -> tuple[str, tuple]:
        """Get all trades in a tick range."""
        query = """
            SELECT *
            FROM trades
            WHERE run_id = ? AND tick >= ? AND tick <= ?
            ORDER BY tick
        """
        return query, (run_id, start_tick, end_tick)
    
    @staticmethod
    def get_decisions_at_tick(run_id: int, tick: int) -> tuple[str, tuple]:
        """Get all decisions at a specific tick."""
        query = """
            SELECT *
            FROM decisions
            WHERE run_id = ? AND tick = ?
        """
        return query, (run_id, tick)
    
    @staticmethod
    def get_agent_decisions(run_id: int, agent_id: int,
                           start_tick: Optional[int] = None,
                           end_tick: Optional[int] = None) -> tuple[str, tuple]:
        """Get decisions for a specific agent."""
        query = """
            SELECT *
            FROM decisions
            WHERE run_id = ? AND agent_id = ?
        """
        params = [run_id, agent_id]
        
        if start_tick is not None:
            query += " AND tick >= ?"
            params.append(start_tick)
        if end_tick is not None:
            query += " AND tick <= ?"
            params.append(end_tick)
        
        query += " ORDER BY tick"
        return query, tuple(params)
    
    @staticmethod
    def get_trade_attempts_for_trade(run_id: int, buyer_id: int, seller_id: int, 
                                    tick: int) -> tuple[str, tuple]:
        """Get all trade attempts for a specific trade negotiation."""
        query = """
            SELECT *
            FROM trade_attempts
            WHERE run_id = ? AND buyer_id = ? AND seller_id = ? AND tick = ?
            ORDER BY id
        """
        return query, (run_id, buyer_id, seller_id, tick)
    
    @staticmethod
    def get_trade_statistics(run_id: int) -> tuple[str, tuple]:
        """Get overall trade statistics for a run."""
        query = """
            SELECT 
                COUNT(*) as total_trades,
                AVG(dA) as avg_dA,
                AVG(dB) as avg_dB,
                AVG(price) as avg_price,
                MIN(tick) as first_trade_tick,
                MAX(tick) as last_trade_tick
            FROM trades
            WHERE run_id = ?
        """
        return query, (run_id,)
    
    @staticmethod
    def get_agent_trade_count(run_id: int) -> tuple[str, tuple]:
        """Get trade counts per agent."""
        query = """
            SELECT agent_id, COUNT(*) as trade_count
            FROM (
                SELECT buyer_id as agent_id FROM trades WHERE run_id = ?
                UNION ALL
                SELECT seller_id as agent_id FROM trades WHERE run_id = ?
            )
            GROUP BY agent_id
            ORDER BY trade_count DESC
        """
        return query, (run_id, run_id)
    
    @staticmethod
    def get_resource_state_at_tick(run_id: int, tick: int) -> tuple[str, tuple]:
        """Get resource distribution at a specific tick."""
        query = """
            SELECT *
            FROM resource_snapshots
            WHERE run_id = ? AND tick <= ?
            ORDER BY tick DESC
            LIMIT 1000
        """
        return query, (run_id, tick)
    
    @staticmethod
    def get_mode_timeline(run_id: int) -> tuple[str, tuple]:
        """Get mode transitions over time."""
        query = """
            SELECT tick, current_mode
            FROM tick_states
            WHERE run_id = ?
            ORDER BY tick
        """
        return query, (run_id,)
    
    @staticmethod
    def get_trade_distribution_by_type(run_id: int) -> tuple[str, tuple]:
        """Get trade count distribution by exchange pair type."""
        query = """
            SELECT exchange_pair_type, COUNT(*) as count
            FROM trades
            WHERE run_id = ?
            GROUP BY exchange_pair_type
            ORDER BY count DESC
        """
        return query, (run_id,)
    

