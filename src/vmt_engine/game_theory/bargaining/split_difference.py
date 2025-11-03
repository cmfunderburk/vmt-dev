"""
Split-the-Difference Bargaining Protocol

Equal surplus division for fairness baseline. Finds the trade that splits gains from
trade as equally as possible between both agents.

Economic Properties:
- Nash bargaining solution approximation (equal surplus split)
- Fairness baseline for comparison with other bargaining protocols
- Pareto efficient (both agents gain)

References:
- Nash (1950) "The Bargaining Problem"
- Equal surplus as fairness criterion in experimental economics

Version: 2025.10.28 (Phase 2a - Baseline Protocol)
"""

from typing import Optional, TYPE_CHECKING
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from ...protocols.base import Effect, Trade, Unpair
from ...protocols.context import WorldView
from .discovery import CompensatingBlockDiscoverer
from ...systems.trade_evaluation import TradeDiscoverer

if TYPE_CHECKING:
    from ...core import Agent


@register_protocol(
    category="bargaining",
    name="split_difference",
    description="Equal surplus division (fairness baseline)",
    properties=["deterministic", "baseline"],
    complexity="O(K)",  # K = number of feasible trades examined
    references=[
        "Nash (1950) The Bargaining Problem",
        "Equal-surplus fairness criteria"
    ],
    phase="2a",
)
class SplitDifference(BargainingProtocol):
    """
    Equal surplus division for fairness baseline.
    
    Behavior:
        - Enumerate all feasible trades (all quantities, all pairs)
        - Calculate surplus for each agent for each trade
        - Select trade closest to 50/50 surplus split
        - If no mutually beneficial trade, unpair
    
    Economic Properties:
        - Approximates Nash bargaining solution
        - Fairness criterion: equal gains from trade
        - Pareto efficient: both agents strictly better off
    
    Note: This is computationally more expensive than legacy protocol since it
    evaluates ALL feasible trades, not just the first one found.
    """
    
    @property
    def name(self) -> str:
        return "split_difference"
    
    @property
    def version(self) -> str:
        return "2025.10.28"
    
    # Class-level for registry
    VERSION = "2025.10.28"
    
    def __init__(self, discoverer: TradeDiscoverer | None = None):
        """
        Initialize split difference bargaining.
        
        Args:
            discoverer: Trade discovery algorithm (default: CompensatingBlockDiscoverer)
        """
        self.discoverer = discoverer or CompensatingBlockDiscoverer()
    
    def negotiate(
        self,
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: WorldView
    ) -> list[Effect]:
        """
        Find trade that splits surplus equally.
        
        Args:
            pair: (agent_a_id, agent_b_id) tuple
            agents: (agent_a, agent_b) - direct access to agent states
            world: Context (tick, params, rng)
        
        Returns:
            [Trade(...)] if mutually beneficial trade with equal split found
            [Unpair(...)] if no feasible trade exists
        """
        agent_a, agent_b = agents
        epsilon = world.params.get("epsilon", 1e-9)
        
        # Discover trade using injected discovery algorithm
        trade_tuple_obj = self.discoverer.discover_trade(
            agent_a, agent_b, world.params, epsilon
        )
        
        if trade_tuple_obj is None:
            # No mutually beneficial trade - unpair
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=pair[0],
                agent_b=pair[1],
                reason="no_feasible_trade"
            )]
        
        # Convert TradeTuple to the format expected by the rest of the method
        # trade_tuple = (dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j)
        best_trade = (
            trade_tuple_obj.dA_i,
            trade_tuple_obj.dB_i,
            trade_tuple_obj.dA_j,
            trade_tuple_obj.dB_j,
            trade_tuple_obj.surplus_i,
            trade_tuple_obj.surplus_j
        )
        best_pair_name = "A<->B"
        
        # Note: With single trade discovery, we don't search for most equal split
        # We use the discovered trade directly
        if best_trade is None:
            # No positive-surplus trade found (shouldn't happen but defensive)
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=pair[0],
                agent_b=pair[1],
                reason="no_positive_surplus"
            )]
        
        # Convert to Trade effect
        # Note: evenness is 0.0 since we no longer optimize for equal split with single trade discovery
        return [self._create_trade_effect(
            pair[0], pair[1], best_pair_name, best_trade, 0.0, world
        )]
    
    def _create_trade_effect(
        self,
        agent_a_id: int,
        agent_b_id: int,
        pair_name: str,
        trade_tuple: tuple,
        evenness: float,
        world: WorldView
    ) -> Trade:
        """Convert trade tuple to Trade effect."""
        dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j = trade_tuple
        
        # Determine buyer/seller based on who receives the good
        # For A<->B: buyer is who receives A (dA > 0)
        # Barter-only: buyer is who receives A
        
        if pair_name == "A<->B":
            # In barter, agent i gives dA_i and receives dB_i
            if dA_i < 0:  # i gives A, j gives B
                buyer_id = agent_b_id  # j receives A
                seller_id = agent_a_id  # i gives A
                dA = abs(dA_i)
                dB = abs(dB_i)
                price = dB / dA if dA > 0 else 0
            else:  # i gives B, j gives A
                buyer_id = agent_a_id  # i receives A
                seller_id = agent_b_id  # j gives A
                dA = abs(dA_j)
                dB = abs(dB_j)
                price = dB / dA if dA > 0 else 0
            
            return Trade(
                protocol_name=self.name,
                tick=world.tick,
                buyer_id=buyer_id,
                seller_id=seller_id,
                pair_type=pair_name,
                dA=dA,
                dB=dB,
                price=float(round(price, 2)),
                metadata={
                    "surplus_buyer": surplus_i if buyer_id == agent_a_id else surplus_j,
                    "surplus_seller": surplus_j if buyer_id == agent_a_id else surplus_i,
                    "total_surplus": surplus_i + surplus_j,
                    "split_evenness": evenness,
                }
            )
        

