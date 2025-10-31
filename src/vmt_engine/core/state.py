"""
Core state structures for VMT simulation.
"""

from dataclasses import dataclass
from typing import TypeAlias


@dataclass
class Inventory:
    """
    Agent inventory state.
    
    Attributes:
        A: Quantity of good A (integer ≥ 0)
        B: Quantity of good B (integer ≥ 0)
    """
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
    p_min: float = 0.0  # Seller's reservation price (minimum)
    p_max: float = 0.0  # Buyer's reservation price (maximum)
    
    def __post_init__(self):
        if self.ask_A_in_B < 0 or self.bid_A_in_B < 0:
            raise ValueError(f"Quote prices cannot be negative: ask={self.ask_A_in_B}, bid={self.bid_A_in_B}")
        if self.p_min < 0 or self.p_max < 0:
            raise ValueError(f"Reservation prices cannot be negative: p_min={self.p_min}, p_max={self.p_max}")


# Position is a tuple of (x, y) coordinates
Position: TypeAlias = tuple[int, int]

