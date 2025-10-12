"""
Decision logging for agent partner selection and movement.
"""

import csv
from pathlib import Path
from typing import TextIO


class DecisionLogger:
    """Logs agent decision-making events to CSV."""
    
    def __init__(self, log_dir: str = "./logs"):
        """
        Initialize decision logger.
        
        Args:
            log_dir: Directory to write log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / "decisions.csv"
        self.file: TextIO | None = None
        self.writer: csv.writer | None = None
        self._open()
    
    def _open(self):
        """Open log file and write header."""
        self.file = open(self.log_file, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow([
            'tick', 'agent_id', 'chosen_partner_id', 'surplus_with_partner',
            'target_type', 'target_x', 'target_y', 'num_neighbors',
            'alternatives'
        ])
        self.file.flush()
    
    def log_decision(self, tick: int, agent_id: int, chosen_partner_id: int | None,
                     surplus_with_partner: float | None, target_type: str,
                     target_x: int | None, target_y: int | None,
                     num_neighbors: int, alternatives: str = ""):
        """
        Log an agent's decision.
        
        Args:
            tick: Current simulation tick
            agent_id: ID of the deciding agent
            chosen_partner_id: ID of chosen partner (None if no partner)
            surplus_with_partner: Surplus with chosen partner (None if no partner)
            target_type: Type of target ('trade', 'forage', 'idle')
            target_x: X coordinate of target (None if idle)
            target_y: Y coordinate of target (None if idle)
            num_neighbors: Number of visible neighbors
            alternatives: String representation of alternative partners with surplus
        """
        if self.writer is None or self.file is None:
            raise RuntimeError("Logger not initialized")
        
        partner_id_str = "" if chosen_partner_id is None else str(chosen_partner_id)
        surplus_str = "" if surplus_with_partner is None else f"{surplus_with_partner:.6f}"
        target_x_str = "" if target_x is None else str(target_x)
        target_y_str = "" if target_y is None else str(target_y)
        
        self.writer.writerow([
            tick, agent_id, partner_id_str, surplus_str,
            target_type, target_x_str, target_y_str, num_neighbors,
            alternatives
        ])
        self.file.flush()
    
    def close(self):
        """Close log file."""
        if self.file:
            self.file.close()
            self.file = None
            self.writer = None
    
    def __del__(self):
        """Ensure file is closed on deletion."""
        self.close()

