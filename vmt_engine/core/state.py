"""
Core state structures for VMT simulation.
"""

from dataclasses import dataclass
from typing import TypeAlias


@dataclass
class Inventory:
    """Agent inventory of goods A and B."""
    A: int = 0
    B: int = 0
    
    def __post_init__(self):
        if self.A < 0 or self.B < 0:
            raise ValueError(f"Inventory cannot be negative: A={self.A}, B={self.B}")


@dataclass
class Quote:
    """Trading quotes for good A priced in good B."""
    ask_A_in_B: float  # Seller's asking price (higher)
    bid_A_in_B: float  # Buyer's bid price (lower)
    
    def __post_init__(self):
        if self.ask_A_in_B < 0 or self.bid_A_in_B < 0:
            raise ValueError(f"Quote prices cannot be negative: ask={self.ask_A_in_B}, bid={self.bid_A_in_B}")


# Position is a tuple of (x, y) coordinates
Position: TypeAlias = tuple[int, int]

