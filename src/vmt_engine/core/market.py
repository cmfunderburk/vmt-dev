"""
Market area data structures for endogenous market formation.

Markets emerge dynamically from agent clustering rather than being pre-placed.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..protocols.market.base import MarketMechanism

Position = tuple[int, int]


@dataclass
class MarketArea:
    """
    An emergent market formed by agent clustering.
    
    Unlike pre-defined MarketPosts, MarketAreas:
    - Form dynamically when agents cluster
    - May dissolve if density drops
    - Do not have fixed pre-determined locations
    """
    # Identity
    id: int
    center: Position  # Geometric center of cluster (may drift)
    radius: int  # Interaction radius
    
    # Current state
    participant_ids: list[int] = field(default_factory=list)
    
    # Market mechanism
    mechanism: Optional['MarketMechanism'] = None
    current_prices: dict[str, float] = field(default_factory=dict)
    
    # Lifecycle
    formation_tick: int = 0
    last_active_tick: int = 0
    ticks_below_threshold: int = 0
    
    # Statistics
    total_trades_executed: int = 0
    total_volume_traded: float = 0.0
    historical_prices: dict[int, dict[str, float]] = field(default_factory=dict)  # tick -> {commodity -> price}
    
    @property
    def is_active(self) -> bool:
        """Is this market currently operating?"""
        return len(self.participant_ids) > 0
    
    @property
    def age(self) -> int:
        """Ticks since formation"""
        return self.last_active_tick - self.formation_tick

