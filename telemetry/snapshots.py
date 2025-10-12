"""
Snapshot logging for periodic state recording.
"""

import csv
from pathlib import Path
from typing import TextIO, TYPE_CHECKING

if TYPE_CHECKING:
    from vmt_engine.core import Agent, Grid


class AgentSnapshotLogger:
    """Logs agent state snapshots at intervals."""
    
    def __init__(self, log_dir: str = "./logs", snapshot_frequency: int = 10):
        """
        Initialize agent snapshot logger.
        
        Args:
            log_dir: Directory to write log files
            snapshot_frequency: Log every K ticks
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_frequency = snapshot_frequency
        
        self.log_file = self.log_dir / "agent_snapshots.csv"
        self.file: TextIO | None = None
        self.writer: csv.writer | None = None
        self._open()
    
    def _open(self):
        """Open log file and write header."""
        self.file = open(self.log_file, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow([
            'tick', 'id', 'x', 'y', 'A', 'B', 'U', 'partner_id', 'utility_type'
        ])
        self.file.flush()
    
    def log_snapshot(self, tick: int, agents: list['Agent']):
        """
        Log snapshot of all agents.
        
        Args:
            tick: Current simulation tick
            agents: List of all agents
        """
        if self.writer is None:
            raise RuntimeError("Logger not initialized")
        
        if tick % self.snapshot_frequency != 0:
            return  # Only log at specified frequency
        
        for agent in agents:
            # Calculate utility if available
            utility_val = 0.0
            if agent.utility:
                utility_val = agent.utility.u(agent.inventory.A, agent.inventory.B)
            
            # Get utility type
            utility_type = "none"
            if agent.utility:
                utility_type = agent.utility.__class__.__name__
            
            # Get partner (if targeting another agent)
            partner_id = ""
            # This will be populated later when partner tracking is implemented
            
            self.writer.writerow([
                tick, agent.id, agent.pos[0], agent.pos[1],
                agent.inventory.A, agent.inventory.B,
                f"{utility_val:.6f}", partner_id, utility_type
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


class ResourceSnapshotLogger:
    """Logs resource state snapshots at intervals."""
    
    def __init__(self, log_dir: str = "./logs", snapshot_frequency: int = 10):
        """
        Initialize resource snapshot logger.
        
        Args:
            log_dir: Directory to write log files
            snapshot_frequency: Log every K ticks
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_frequency = snapshot_frequency
        
        self.log_file = self.log_dir / "resource_snapshots.csv"
        self.file: TextIO | None = None
        self.writer: csv.writer | None = None
        self._open()
    
    def _open(self):
        """Open log file and write header."""
        self.file = open(self.log_file, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['tick', 'cell_id', 'x', 'y', 'resource_type', 'amount'])
        self.file.flush()
    
    def log_snapshot(self, tick: int, grid: 'Grid'):
        """
        Log snapshot of grid resources.
        
        Args:
            tick: Current simulation tick
            grid: The simulation grid
        """
        if self.writer is None:
            raise RuntimeError("Logger not initialized")
        
        if tick % self.snapshot_frequency != 0:
            return  # Only log at specified frequency
        
        for cell in grid.cells.values():
            if cell.resource.amount > 0 and cell.resource.type:
                cell_id = f"{cell.position[0]}_{cell.position[1]}"
                self.writer.writerow([
                    tick, cell_id, cell.position[0], cell.position[1],
                    cell.resource.type, cell.resource.amount
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

