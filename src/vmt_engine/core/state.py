"""
Core state structures for VMT simulation.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TypeAlias

from .decimal_config import decimal_from_numeric, quantize_quantity


@dataclass
class Inventory:
    """
    Agent inventory state.
    
    Attributes:
        A: Quantity of good A (Decimal ≥ 0)
        B: Quantity of good B (Decimal ≥ 0)
    """
    A: Decimal = field(default_factory=lambda: Decimal('0'))
    B: Decimal = field(default_factory=lambda: Decimal('0'))

    def __post_init__(self):
        # Convert to Decimal if needed and quantize
        if isinstance(self.A, (int, float)):
            self.A = decimal_from_numeric(self.A)
        else:
            self.A = quantize_quantity(self.A)
        
        if isinstance(self.B, (int, float)):
            self.B = decimal_from_numeric(self.B)
        else:
            self.B = quantize_quantity(self.B)
        
        # Validate non-negativity
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

