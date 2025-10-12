"""
Agent representation and initialization.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from .state import Inventory, Quote, Position

if TYPE_CHECKING:
    from ..econ.utility import Utility


@dataclass
class Agent:
    """An agent in the simulation."""
    id: int
    pos: Position
    inventory: Inventory
    utility: Optional['Utility'] = None
    quotes: Quote = field(default_factory=lambda: Quote(ask_A_in_B=0.0, bid_A_in_B=0.0))
    vision_radius: int = 5
    move_budget_per_tick: int = 1
    
    # Runtime state (not persisted)
    target_pos: Optional[Position] = field(default=None, repr=False)
    target_agent_id: Optional[int] = field(default=None, repr=False)
    perception_cache: dict = field(default_factory=dict, repr=False)
    inventory_changed: bool = field(default=True, repr=False)
    
    def __post_init__(self):
        if self.id < 0:
            raise ValueError(f"Agent id must be non-negative, got {self.id}")
        if self.vision_radius < 0:
            raise ValueError(f"vision_radius must be non-negative, got {self.vision_radius}")
        if self.move_budget_per_tick <= 0:
            raise ValueError(f"move_budget_per_tick must be positive, got {self.move_budget_per_tick}")

