"""
Trade logging for telemetry.
"""

import csv
from pathlib import Path
from typing import TextIO


class TradeLogger:
    """Logs trade events to CSV."""
    
    def __init__(self, log_dir: str = "./logs"):
        """
        Initialize trade logger.
        
        Args:
            log_dir: Directory to write log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / "trades.csv"
        self.file: TextIO | None = None
        self.writer: csv.writer | None = None
        self.recent_trades_for_renderer: list = []
        self._open()
    
    def _open(self):
        """Open log file and write header."""
        self.file = open(self.log_file, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow([
            'tick', 'x', 'y', 'buyer_id', 'seller_id', 
            'dA', 'dB', 'price', 'direction'
        ])
        self.file.flush()
    
    def log_trade(self, tick: int, x: int, y: int, buyer_id: int, seller_id: int,
                  dA: int, dB: int, price: float, direction: str):
        """
        Log a trade event.
        
        Args:
            tick: Current simulation tick
            x, y: Location of trade
            buyer_id: ID of buying agent
            seller_id: ID of selling agent
            dA: Amount of good A traded
            dB: Amount of good B traded
            price: Trade price (A in terms of B)
            direction: Trade direction string
        """
        if self.writer is None or self.file is None:
            raise RuntimeError("Logger not initialized")
        
        self.writer.writerow([
            tick, x, y, buyer_id, seller_id,
            dA, dB, f"{price:.6f}", direction
        ])
        self.file.flush()

        # Also store in memory for renderer
        self.recent_trades_for_renderer.append({
            "tick": tick, "x": x, "y": y, "buyer_id": buyer_id, "seller_id": seller_id,
            "dA": dA, "dB": dB, "price": price, "direction": direction
        })
        # Keep only recent trades
        if len(self.recent_trades_for_renderer) > 20:
            self.recent_trades_for_renderer.pop(0)
    
    def close(self):
        """Close log file."""
        if self.file:
            self.file.close()
            self.file = None
            self.writer = None
    
    def __del__(self):
        """Ensure file is closed on deletion."""
        self.close()

