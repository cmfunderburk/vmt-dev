"""
Database-backed loggers for simulation telemetry.
"""

from typing import TYPE_CHECKING, Optional
from datetime import datetime
import json

from .database import TelemetryDatabase
from .config import LogConfig

if TYPE_CHECKING:
    from vmt_engine.core import Agent, Grid


class TelemetryManager:
    """Manages all telemetry logging with database backend."""
    
    def __init__(self, config: LogConfig, scenario_name: str = "simulation"):
        """
        Initialize telemetry manager.
        
        Args:
            config: Logging configuration
            scenario_name: Name of the scenario being run
        """
        self.config = config
        self.scenario_name = scenario_name
        
        # Set up database
        if config.use_database:
            db_path = config.db_path or "./logs/telemetry.db"
            self.db = TelemetryDatabase(db_path)
        else:
            self.db = None
        
        # Create run entry
        self.run_id: Optional[int] = None
        self.start_time = datetime.now()
        self.current_tick = 0
        
        # Batch buffers for performance
        self._agent_snapshot_buffer: list = []
        self._resource_snapshot_buffer: list = []
        self._decision_buffer: list = []
        self._trade_buffer: list = []
        self._trade_attempt_buffer: list = []
        
        # For renderer compatibility
        self.recent_trades_for_renderer: list = []
    
    def start_run(self, num_agents: int, grid_width: int, grid_height: int,
                  config_dict: Optional[dict] = None):
        """
        Start a new simulation run.
        
        Args:
            num_agents: Number of agents in simulation
            grid_width: Width of grid
            grid_height: Height of grid
            config_dict: Optional configuration dictionary to store
        """
        if self.db is None:
            return
        
        config_json = json.dumps(config_dict or {})
        self.run_id = self.db.create_run(
            scenario_name=self.scenario_name,
            start_time=self.start_time.isoformat(),
            num_agents=num_agents,
            grid_width=grid_width,
            grid_height=grid_height,
            config_json=config_json
        )
    
    def finalize_run(self, total_ticks: int):
        """Finalize the run and flush all buffers."""
        self._flush_all_buffers()
        if self.db and self.run_id:
            self.db.finalize_run(
                run_id=self.run_id,
                end_time=datetime.now().isoformat(),
                total_ticks=total_ticks
            )
    
    def log_agent_snapshots(self, tick: int, agents: list['Agent']):
        """
        Log agent state snapshots.
        
        Args:
            tick: Current simulation tick
            agents: List of all agents
        """
        if not self.config.log_agent_snapshots or self.db is None or self.run_id is None:
            return
        
        # Check frequency (0 = disabled, >0 = log every N ticks)
        if self.config.agent_snapshot_frequency == 0:
            return  # Disabled
        if tick % self.config.agent_snapshot_frequency != 0:
            return  # Not the right tick
        
        self.current_tick = tick
        
        for agent in agents:
            # Calculate utility
            utility_val = 0.0
            if agent.utility:
                utility_val = agent.utility.u(agent.inventory.A, agent.inventory.B)
            
            # Get utility type
            utility_type = "none"
            if agent.utility:
                utility_type = agent.utility.__class__.__name__
            
            # Get target data
            target_agent_id = agent.target_agent_id
            target_x = agent.target_pos[0] if agent.target_pos else None
            target_y = agent.target_pos[1] if agent.target_pos else None
            
            self._agent_snapshot_buffer.append((
                self.run_id, tick, agent.id,
                int(agent.pos[0]), int(agent.pos[1]),  # Convert numpy int to Python int
                int(agent.inventory.A), int(agent.inventory.B), float(utility_val),
                float(agent.quotes.ask_A_in_B), float(agent.quotes.bid_A_in_B),
                float(agent.quotes.p_min), float(agent.quotes.p_max),
                target_agent_id, target_x if target_x is None else int(target_x), 
                target_y if target_y is None else int(target_y), utility_type
            ))
        
        # Flush buffer if needed
        if len(self._agent_snapshot_buffer) >= self.config.batch_size:
            self._flush_agent_snapshots()
    
    def log_resource_snapshots(self, tick: int, grid: 'Grid'):
        """
        Log resource state snapshots.
        
        Args:
            tick: Current simulation tick
            grid: The simulation grid
        """
        if not self.config.log_resource_snapshots or self.db is None or self.run_id is None:
            return
        
        # Check frequency (0 = disabled, >0 = log every N ticks)
        if self.config.resource_snapshot_frequency == 0:
            return  # Disabled
        if tick % self.config.resource_snapshot_frequency != 0:
            return  # Not the right tick
        
        for cell in grid.cells.values():
            if cell.resource.amount > 0 and cell.resource.type:
                self._resource_snapshot_buffer.append((
                    self.run_id, tick,
                    int(cell.position[0]), int(cell.position[1]),  # Convert numpy int to Python int
                    cell.resource.type, int(cell.resource.amount)
                ))
        
        # Flush buffer if needed
        if len(self._resource_snapshot_buffer) >= self.config.batch_size:
            self._flush_resource_snapshots()
    
    def log_decision(self, tick: int, agent_id: int, chosen_partner_id: Optional[int],
                     surplus_with_partner: Optional[float], target_type: str,
                     target_x: Optional[int], target_y: Optional[int],
                     num_neighbors: int, alternatives: str = ""):
        """
        Log an agent's decision.
        
        Args:
            tick: Current simulation tick
            agent_id: ID of the deciding agent
            chosen_partner_id: ID of chosen partner (None if no partner)
            surplus_with_partner: Surplus with chosen partner
            target_type: Type of target ('trade', 'forage', 'idle')
            target_x: X coordinate of target
            target_y: Y coordinate of target
            num_neighbors: Number of visible neighbors
            alternatives: String representation of alternatives
        """
        if not self.config.log_decisions or self.db is None or self.run_id is None:
            return
        
        self._decision_buffer.append((
            self.run_id, tick, agent_id,
            chosen_partner_id, surplus_with_partner,
            target_type, 
            target_x if target_x is None else int(target_x),  # Convert numpy int to Python int
            target_y if target_y is None else int(target_y),  # Convert numpy int to Python int
            num_neighbors, alternatives
        ))
        
        # Flush buffer if needed
        if len(self._decision_buffer) >= self.config.batch_size:
            self._flush_decisions()
    
    def log_trade(self, tick: int, x: int, y: int, buyer_id: int, seller_id: int,
                  dA: int, dB: int, price: float, direction: str):
        """
        Log a successful trade.
        
        Args:
            tick: Current simulation tick
            x, y: Location of trade
            buyer_id: ID of buying agent
            seller_id: ID of selling agent
            dA: Amount of good A traded
            dB: Amount of good B traded
            price: Trade price
            direction: Trade direction string
        """
        if not self.config.log_trades or self.db is None or self.run_id is None:
            return
        
        self._trade_buffer.append((
            self.run_id, tick, int(x), int(y),
            int(buyer_id), int(seller_id),
            int(dA), int(dB), float(price), direction
        ))
        
        # Also store for renderer
        self.recent_trades_for_renderer.append({
            "tick": tick, "x": x, "y": y,
            "buyer_id": buyer_id, "seller_id": seller_id,
            "dA": dA, "dB": dB, "price": price, "direction": direction
        })
        if len(self.recent_trades_for_renderer) > 20:
            self.recent_trades_for_renderer.pop(0)
        
        # Flush buffer if needed
        if len(self._trade_buffer) >= self.config.batch_size:
            self._flush_trades()
    
    def log_trade_attempt(self, tick: int, buyer_id: int, seller_id: int,
                          direction: str, price: float,
                          buyer_ask: float, buyer_bid: float,
                          seller_ask: float, seller_bid: float, surplus: float,
                          dA: int, dB: int,
                          buyer_A_init: int, buyer_B_init: int, buyer_U_init: float,
                          buyer_A_final: int, buyer_B_final: int, buyer_U_final: float,
                          buyer_improves: bool,
                          seller_A_init: int, seller_B_init: int, seller_U_init: float,
                          seller_A_final: int, seller_B_final: int, seller_U_final: float,
                          seller_improves: bool,
                          buyer_feasible: bool, seller_feasible: bool,
                          result: str, result_reason: str):
        """
        Log a trade attempt (successful or failed).
        
        Only logs if DEBUG level is enabled.
        """
        if not self.config.log_trade_attempts or self.db is None or self.run_id is None:
            return
        
        self._trade_attempt_buffer.append((
            self.run_id, tick, int(buyer_id), int(seller_id),
            direction, float(price),
            float(buyer_ask), float(buyer_bid), float(seller_ask), float(seller_bid), float(surplus),
            int(dA), int(dB),
            int(buyer_A_init), int(buyer_B_init), float(buyer_U_init),
            int(buyer_A_final), int(buyer_B_final), float(buyer_U_final),
            1 if buyer_improves else 0,
            int(seller_A_init), int(seller_B_init), float(seller_U_init),
            int(seller_A_final), int(seller_B_final), float(seller_U_final),
            1 if seller_improves else 0,
            1 if buyer_feasible else 0, 1 if seller_feasible else 0,
            result, result_reason
        ))
        
        # Flush buffer if needed
        if len(self._trade_attempt_buffer) >= self.config.batch_size:
            self._flush_trade_attempts()
    
    def log_iteration(self, tick: int, buyer_id: int, seller_id: int,
                      direction: str, price: float,
                      buyer_ask: float, buyer_bid: float,
                      seller_ask: float, seller_bid: float, surplus: float,
                      dA: int, dB: int,
                      buyer_A_init: int, buyer_B_init: int, buyer_U_init: float,
                      buyer_A_final: int, buyer_B_final: int, buyer_U_final: float,
                      buyer_improves: bool,
                      seller_A_init: int, seller_B_init: int, seller_U_init: float,
                      seller_A_final: int, seller_B_final: int, seller_U_final: float,
                      seller_improves: bool,
                      buyer_feasible: bool, seller_feasible: bool,
                      result: str, result_reason: str):
        """
        Alias for log_trade_attempt for backward compatibility with matching.py.
        
        This method name is used by the trading system's find_compensating_block function.
        """
        self.log_trade_attempt(
            tick, buyer_id, seller_id, direction, price,
            buyer_ask, buyer_bid, seller_ask, seller_bid, surplus,
            dA, dB,
            buyer_A_init, buyer_B_init, buyer_U_init,
            buyer_A_final, buyer_B_final, buyer_U_final, buyer_improves,
            seller_A_init, seller_B_init, seller_U_init,
            seller_A_final, seller_B_final, seller_U_final, seller_improves,
            buyer_feasible, seller_feasible, result, result_reason
        )
    
    def _flush_agent_snapshots(self):
        """Flush agent snapshot buffer to database."""
        if not self._agent_snapshot_buffer or self.db is None:
            return
        
        self.db.executemany("""
            INSERT INTO agent_snapshots
            (run_id, tick, agent_id, x, y, inventory_A, inventory_B, utility,
             ask_A_in_B, bid_A_in_B, p_min, p_max,
             target_agent_id, target_x, target_y, utility_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, self._agent_snapshot_buffer)
        self.db.commit()
        self._agent_snapshot_buffer.clear()
    
    def _flush_resource_snapshots(self):
        """Flush resource snapshot buffer to database."""
        if not self._resource_snapshot_buffer or self.db is None:
            return
        
        self.db.executemany("""
            INSERT INTO resource_snapshots
            (run_id, tick, x, y, resource_type, amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, self._resource_snapshot_buffer)
        self.db.commit()
        self._resource_snapshot_buffer.clear()
    
    def _flush_decisions(self):
        """Flush decision buffer to database."""
        if not self._decision_buffer or self.db is None:
            return
        
        self.db.executemany("""
            INSERT INTO decisions
            (run_id, tick, agent_id, chosen_partner_id, surplus_with_partner,
             target_type, target_x, target_y, num_neighbors, alternatives)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, self._decision_buffer)
        self.db.commit()
        self._decision_buffer.clear()
    
    def _flush_trades(self):
        """Flush trade buffer to database."""
        if not self._trade_buffer or self.db is None:
            return
        
        self.db.executemany("""
            INSERT INTO trades
            (run_id, tick, x, y, buyer_id, seller_id, dA, dB, price, direction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, self._trade_buffer)
        self.db.commit()
        self._trade_buffer.clear()
    
    def _flush_trade_attempts(self):
        """Flush trade attempt buffer to database."""
        if not self._trade_attempt_buffer or self.db is None:
            return
        
        self.db.executemany("""
            INSERT INTO trade_attempts
            (run_id, tick, buyer_id, seller_id, direction, price,
             buyer_ask, buyer_bid, seller_ask, seller_bid, surplus,
             dA_attempted, dB_calculated,
             buyer_A_init, buyer_B_init, buyer_U_init,
             buyer_A_final, buyer_B_final, buyer_U_final, buyer_improves,
             seller_A_init, seller_B_init, seller_U_init,
             seller_A_final, seller_B_final, seller_U_final, seller_improves,
             buyer_feasible, seller_feasible, result, result_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, self._trade_attempt_buffer)
        self.db.commit()
        self._trade_attempt_buffer.clear()
    
    def _flush_all_buffers(self):
        """Flush all buffers to database."""
        self._flush_agent_snapshots()
        self._flush_resource_snapshots()
        self._flush_decisions()
        self._flush_trades()
        self._flush_trade_attempts()
    
    def close(self):
        """Close the telemetry manager and database."""
        self._flush_all_buffers()
        if self.db:
            self.db.close()
    
    def __del__(self):
        """Ensure cleanup on deletion."""
        try:
            self.close()
        except:
            pass

