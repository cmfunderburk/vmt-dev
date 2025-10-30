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
    
    # Price signal learning system
    observed_market_prices: dict[str, list[float]] = field(default_factory=dict)  # commodity -> [prices]
    price_learning_rate: float = 0.1  # How quickly to update lambda_money based on prices
    max_price_history: int = 10  # Maximum number of price observations to keep

    def __post_init__(self):
        if self.id < 0:
            raise ValueError(f"Agent id must be non-negative, got {self.id}")
        if self.vision_radius < 0:
            raise ValueError(f"vision_radius must be non-negative, got {self.vision_radius}")
        if self.move_budget_per_tick <= 0:
            raise ValueError(f"move_budget_per_tick must be positive, got {self.move_budget_per_tick}")
    
    def update_price_observations(self, recent_prices: dict[str, list[float]]) -> None:
        """
        Update agent's observed market prices from recent trade data.
        
        Args:
            recent_prices: Dictionary mapping commodity names to lists of recent prices
        """
        for commodity, prices in recent_prices.items():
            if commodity not in self.observed_market_prices:
                self.observed_market_prices[commodity] = []
            
            # Add new prices
            self.observed_market_prices[commodity].extend(prices)
            
            # Trim to max history length
            if len(self.observed_market_prices[commodity]) > self.max_price_history:
                self.observed_market_prices[commodity] = self.observed_market_prices[commodity][-self.max_price_history:]
    
    def learn_from_prices(self) -> None:
        """
        Update lambda_money based on observed market prices.
        
        This implements a simple learning rule where agents adjust their money utility
        parameter based on observed price signals in the market.
        """
        if not self.observed_market_prices:
            return
        
        # Simple learning rule: adjust lambda_money based on price trends
        for commodity, prices in self.observed_market_prices.items():
            if len(prices) < 2:
                continue
            
            # Calculate price trend (simple moving average)
            recent_avg = sum(prices[-3:]) / len(prices[-3:]) if len(prices) >= 3 else sum(prices) / len(prices)
            older_avg = sum(prices[:-3]) / len(prices[:-3]) if len(prices) > 3 else recent_avg
            
            if older_avg > 0:
                price_change = (recent_avg - older_avg) / older_avg
                
                # Adjust lambda_money based on price change
                # If prices are rising, increase lambda_money (money becomes more valuable)
                # If prices are falling, decrease lambda_money (money becomes less valuable)
                adjustment = self.price_learning_rate * price_change
                new_lambda = self.lambda_money * (1 + adjustment)
                
                # Keep lambda_money within reasonable bounds
                new_lambda = max(0.1, min(10.0, new_lambda))
                
                if abs(new_lambda - self.lambda_money) > 0.01:  # Only update if significant change
                    self.lambda_money = new_lambda
                    self.lambda_changed = True

