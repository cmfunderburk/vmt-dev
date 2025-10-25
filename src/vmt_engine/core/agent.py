"""
Agent representation and initialization.

Money-aware API (Phase 2):
- Agent.quotes is now dict[str, float] with keys for all exchange pairs
- Legacy Quote dataclass access is deprecated
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
    quotes: dict[str, float] = field(default_factory=dict)  # Money-aware: dict of all exchange pairs
    vision_radius: int = 5
    move_budget_per_tick: int = 1
    home_pos: Optional[Position] = None  # Initial position for idle fallback
    
    # Runtime state (not persisted)
    target_pos: Optional[Position] = field(default=None, repr=False)
    target_agent_id: Optional[int] = field(default=None, repr=False)
    perception_cache: dict = field(default_factory=dict, repr=False)
    inventory_changed: bool = field(default=True, repr=False)
    trade_cooldowns: dict[int, int] = field(default_factory=dict, repr=False)  # partner_id -> cooldown_until_tick
    
    # Foraging commitment state
    is_foraging_committed: bool = field(default=False, repr=False)  # True when committed to harvesting a specific resource
    forage_target_pos: Optional[Position] = field(default=None, repr=False)  # Resource position agent is committed to
    
    # Pairing state (persists across ticks until unpaired)
    paired_with_id: Optional[int] = field(default=None, repr=False)
    
    # Decision context (cleared each tick)
    _preference_list: list[tuple[int, float, float, int]] = field(default_factory=list, repr=False)  # (partner_id, surplus, discounted_surplus, distance)
    _decision_target_type: Optional[str] = field(default=None, repr=False)  # "trade", "forage", "idle", "trade_paired"

    # Money system state (Phase 1)
    lambda_money: float = 1.0  # Marginal utility of money parameter (λ)
    lambda_changed: bool = False  # Flag for Housekeeping
    money_utility_form: str = "linear"  # "linear" or "log"
    M_0: float = 0.0  # Shift parameter for log money utility

    def __post_init__(self):
        if self.id < 0:
            raise ValueError(f"Agent id must be non-negative, got {self.id}")
        if self.vision_radius < 0:
            raise ValueError(f"vision_radius must be non-negative, got {self.vision_radius}")
        if self.move_budget_per_tick <= 0:
            raise ValueError(f"move_budget_per_tick must be positive, got {self.move_budget_per_tick}")

