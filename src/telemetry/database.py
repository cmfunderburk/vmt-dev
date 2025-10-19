"""
SQLite database schema and connection management for simulation telemetry.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


class TelemetryDatabase:
    """Manages SQLite database for simulation telemetry."""
    
    def __init__(self, db_path: str | Path):
        """
        Initialize telemetry database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_schema()
    
    def _connect(self):
        """Open database connection."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        # Enable WAL mode for better concurrent access
        self.conn.execute("PRAGMA journal_mode=WAL")
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.row_factory = sqlite3.Row
    
    def _create_schema(self):
        """Create database schema if it doesn't exist."""
        if self.conn is None:
            raise RuntimeError("Database not connected")
        
        cursor = self.conn.cursor()
        
        # Simulation run metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_name TEXT,
                start_time TEXT,
                end_time TEXT,
                total_ticks INTEGER,
                num_agents INTEGER,
                grid_width INTEGER,
                grid_height INTEGER,
                config_json TEXT,
                exchange_regime TEXT DEFAULT 'barter_only',
                money_mode TEXT DEFAULT NULL,
                money_scale INTEGER DEFAULT 1
            )
        """)
        
        # Agent snapshots - state at each tick
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                inventory_A INTEGER NOT NULL,
                inventory_B INTEGER NOT NULL,
                inventory_M INTEGER DEFAULT 0,
                utility REAL NOT NULL,
                ask_A_in_B REAL,
                bid_A_in_B REAL,
                p_min REAL,
                p_max REAL,
                ask_A_in_M REAL DEFAULT NULL,
                bid_A_in_M REAL DEFAULT NULL,
                ask_B_in_M REAL DEFAULT NULL,
                bid_B_in_M REAL DEFAULT NULL,
                perceived_price_A REAL DEFAULT NULL,
                perceived_price_B REAL DEFAULT NULL,
                lambda_money REAL DEFAULT NULL,
                lambda_changed INTEGER DEFAULT 0,
                target_agent_id INTEGER,
                target_x INTEGER,
                target_y INTEGER,
                utility_type TEXT,
                FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
            )
        """)
        
        # Create indices for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_snapshots_run_tick 
            ON agent_snapshots(run_id, tick)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_snapshots_agent 
            ON agent_snapshots(run_id, agent_id, tick)
        """)
        
        # Resource snapshots - grid resources at each tick
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                resource_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resource_snapshots_run_tick 
            ON resource_snapshots(run_id, tick)
        """)
        
        # Agent decisions - partner selection and movement
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                chosen_partner_id INTEGER,
                surplus_with_partner REAL,
                target_type TEXT NOT NULL,
                target_x INTEGER,
                target_y INTEGER,
                num_neighbors INTEGER NOT NULL,
                alternatives TEXT,
                mode TEXT,
                FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_run_tick 
            ON decisions(run_id, tick)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_agent 
            ON decisions(run_id, agent_id, tick)
        """)
        
        # Successful trades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                dA INTEGER NOT NULL,
                dB INTEGER NOT NULL,
                dM INTEGER DEFAULT 0,
                price REAL NOT NULL,
                direction TEXT NOT NULL,
                exchange_pair_type TEXT DEFAULT 'A<->B',
                buyer_lambda REAL DEFAULT NULL,
                seller_lambda REAL DEFAULT NULL,
                buyer_surplus REAL DEFAULT NULL,
                seller_surplus REAL DEFAULT NULL,
                FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_run_tick 
            ON trades(run_id, tick)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_agents 
            ON trades(run_id, buyer_id, seller_id)
        """)
        
        # Trade attempts - detailed diagnostics (optional, for debug mode)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                direction TEXT NOT NULL,
                price REAL NOT NULL,
                buyer_ask REAL NOT NULL,
                buyer_bid REAL NOT NULL,
                seller_ask REAL NOT NULL,
                seller_bid REAL NOT NULL,
                surplus REAL NOT NULL,
                dA_attempted INTEGER NOT NULL,
                dB_calculated INTEGER NOT NULL,
                buyer_A_init INTEGER NOT NULL,
                buyer_B_init INTEGER NOT NULL,
                buyer_U_init REAL NOT NULL,
                buyer_A_final INTEGER NOT NULL,
                buyer_B_final INTEGER NOT NULL,
                buyer_U_final REAL NOT NULL,
                buyer_improves INTEGER NOT NULL,
                seller_A_init INTEGER NOT NULL,
                seller_B_init INTEGER NOT NULL,
                seller_U_init REAL NOT NULL,
                seller_A_final INTEGER NOT NULL,
                seller_B_final INTEGER NOT NULL,
                seller_U_final REAL NOT NULL,
                seller_improves INTEGER NOT NULL,
                buyer_feasible INTEGER NOT NULL,
                seller_feasible INTEGER NOT NULL,
                result TEXT NOT NULL,
                result_reason TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trade_attempts_run_tick 
            ON trade_attempts(run_id, tick)
        """)
        
        # Mode transition tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mode_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                old_mode TEXT NOT NULL,
                new_mode TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mode_changes_run_tick 
            ON mode_changes(run_id, tick)
        """)
        
        # New tables for money system (Phase 1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tick_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                current_mode TEXT NOT NULL,
                exchange_regime TEXT NOT NULL,
                active_pairs TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id),
                UNIQUE(run_id, tick)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tick_states_run_tick 
            ON tick_states(run_id, tick)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lambda_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                tick INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                lambda_old REAL NOT NULL,
                lambda_new REAL NOT NULL,
                lambda_hat_A REAL NOT NULL,
                lambda_hat_B REAL NOT NULL,
                lambda_hat REAL NOT NULL,
                clamped INTEGER NOT NULL,
                clamp_type TEXT,
                FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lambda_updates_run_agent 
            ON lambda_updates(run_id, agent_id, tick)
        """)

        self.conn.commit()
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        if self.conn is None:
            raise RuntimeError("Database not connected")
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
    
    def execute(self, query: str, params: tuple = ()):
        """Execute a query and return cursor."""
        if self.conn is None:
            raise RuntimeError("Database not connected")
        return self.conn.execute(query, params)
    
    def executemany(self, query: str, params_list: list):
        """Execute a query with multiple parameter sets."""
        if self.conn is None:
            raise RuntimeError("Database not connected")
        return self.conn.executemany(query, params_list)
    
    def commit(self):
        """Commit pending transactions."""
        if self.conn is None:
            raise RuntimeError("Database not connected")
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __del__(self):
        """Ensure connection is closed."""
        self.close()
    
    # Convenience methods for creating a run
    def create_run(self, scenario_name: str, start_time: str,
                   num_agents: int, grid_width: int, grid_height: int,
                   config_json: str = "",
                   exchange_regime: str = "barter_only",
                   money_mode: Optional[str] = None,
                   money_scale: int = 1) -> int:
        """
        Create a new simulation run entry.
        
        Returns:
            run_id for the new run
        """
        cursor = self.execute("""
            INSERT INTO simulation_runs 
            (scenario_name, start_time, num_agents, grid_width, grid_height, config_json,
             exchange_regime, money_mode, money_scale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (scenario_name, start_time, num_agents, grid_width, grid_height, config_json,
              exchange_regime, money_mode, money_scale))
        self.commit()
        return cursor.lastrowid
    
    def finalize_run(self, run_id: int, end_time: str, total_ticks: int):
        """Update run with completion information."""
        self.execute("""
            UPDATE simulation_runs 
            SET end_time = ?, total_ticks = ?
            WHERE run_id = ?
        """, (end_time, total_ticks, run_id))
        self.commit()
    
    def get_runs(self):
        """Get all simulation runs."""
        cursor = self.execute("""
            SELECT * FROM simulation_runs ORDER BY run_id DESC
        """)
        return cursor.fetchall()
    
    def get_run_info(self, run_id: int):
        """Get information about a specific run."""
        cursor = self.execute("""
            SELECT * FROM simulation_runs WHERE run_id = ?
        """, (run_id,))
        return cursor.fetchone()

