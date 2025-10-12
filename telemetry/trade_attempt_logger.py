"""
Trade attempt logging for detailed trade diagnostics.
"""

import csv
from pathlib import Path
from typing import TextIO


class TradeAttemptLogger:
    """Logs all trade attempts with detailed diagnostics."""
    
    def __init__(self, log_dir: str = "./logs"):
        """
        Initialize trade attempt logger.
        
        Args:
            log_dir: Directory to write log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / "trade_attempts.csv"
        self.file: TextIO | None = None
        self.writer: csv.writer | None = None
        self._open()
    
    def _open(self):
        """Open log file and write header."""
        self.file = open(self.log_file, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow([
            'tick', 'buyer_id', 'seller_id', 'direction', 'price',
            'buyer_ask', 'buyer_bid', 'seller_ask', 'seller_bid', 'surplus',
            'dA_attempted', 'dB_calculated',
            'buyer_A_init', 'buyer_B_init', 'buyer_U_init',
            'buyer_A_final', 'buyer_B_final', 'buyer_U_final', 'buyer_improves',
            'seller_A_init', 'seller_B_init', 'seller_U_init',
            'seller_A_final', 'seller_B_final', 'seller_U_final', 'seller_improves',
            'buyer_feasible', 'seller_feasible', 'result', 'result_reason'
        ])
        self.file.flush()
    
    def log_attempt_start(self, tick: int, buyer_id: int, seller_id: int,
                          direction: str, price: float,
                          buyer_ask: float, buyer_bid: float,
                          seller_ask: float, seller_bid: float, surplus: float):
        """
        Log the start of a trade attempt (before trying block sizes).
        
        Args:
            tick: Current simulation tick
            buyer_id: ID of buying agent
            seller_id: ID of selling agent
            direction: Trade direction string
            price: Midpoint price being used
            buyer_ask: Buyer's ask price
            buyer_bid: Buyer's bid price
            seller_ask: Seller's ask price
            seller_bid: Seller's bid price
            surplus: Computed surplus (overlap)
        """
        # We'll store this info for the detailed iteration logs
        # For now, this is a placeholder - actual logging happens per iteration
        pass
    
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
        Log a single trade size iteration.
        
        Args:
            tick: Current simulation tick
            buyer_id: ID of buying agent
            seller_id: ID of selling agent
            direction: Trade direction string
            price: Midpoint price being used
            buyer_ask: Buyer's ask price
            buyer_bid: Buyer's bid price
            seller_ask: Seller's ask price
            seller_bid: Seller's bid price
            surplus: Computed surplus (overlap)
            dA: Amount of A being traded
            dB: Amount of B being traded
            buyer_A_init: Buyer's initial A inventory
            buyer_B_init: Buyer's initial B inventory
            buyer_U_init: Buyer's initial utility
            buyer_A_final: Buyer's final A inventory (hypothetical)
            buyer_B_final: Buyer's final B inventory (hypothetical)
            buyer_U_final: Buyer's final utility (hypothetical)
            buyer_improves: Whether buyer's utility improves
            seller_A_init: Seller's initial A inventory
            seller_B_init: Seller's initial B inventory
            seller_U_init: Seller's initial utility
            seller_A_final: Seller's final A inventory (hypothetical)
            seller_B_final: Seller's final B inventory (hypothetical)
            seller_U_final: Seller's final utility (hypothetical)
            seller_improves: Whether seller's utility improves
            buyer_feasible: Whether buyer has enough inventory
            seller_feasible: Whether seller has enough inventory
            result: Result of this iteration ('success', 'fail')
            result_reason: Reason for result
        """
        if self.writer is None or self.file is None:
            raise RuntimeError("Logger not initialized")
        
        self.writer.writerow([
            tick, buyer_id, seller_id, direction, f"{price:.6f}",
            f"{buyer_ask:.6f}", f"{buyer_bid:.6f}",
            f"{seller_ask:.6f}", f"{seller_bid:.6f}", f"{surplus:.6f}",
            dA, dB,
            buyer_A_init, buyer_B_init, f"{buyer_U_init:.6f}",
            buyer_A_final, buyer_B_final, f"{buyer_U_final:.6f}", buyer_improves,
            seller_A_init, seller_B_init, f"{seller_U_init:.6f}",
            seller_A_final, seller_B_final, f"{seller_U_final:.6f}", seller_improves,
            buyer_feasible, seller_feasible, result, result_reason
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

