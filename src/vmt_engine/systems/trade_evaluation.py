"""
Trade Evaluation Abstractions

Provides protocol-agnostic interfaces for trade evaluation.
Decouples matching protocols from bargaining protocol implementations.

This module defines:
1. TradePotentialEvaluator: Lightweight heuristic evaluation for matching phase
2. TradeTuple: Utility type for trade specification (bargaining protocols)
3. trade_tuple_to_effect(): Shared utility for converting TradeTuple to Trade effect

Version: 2025.11.04 (Architecture Correction)
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, NamedTuple
from decimal import Decimal

if TYPE_CHECKING:
    from ..core import Agent
    from ..protocols.context import WorldView
    from ..protocols.base import Trade


class TradePotential(NamedTuple):
    """
    Lightweight evaluation of trade potential between two agents.
    
    Used by matching protocols for pairing decisions.
    NamedTuple for zero-overhead performance.
    """
    is_feasible: bool                  # Can these agents trade?
    estimated_surplus: float           # Estimated total surplus (heuristic)
    preferred_direction: str | None    # "i_gives_A" or "i_gives_B" or None
    confidence: float                  # 0.0 to 1.0, heuristic confidence


class TradePotentialEvaluator(ABC):
    """
    Abstract interface for evaluating trade potential between agents.
    
    Used by matching protocols to make pairing decisions without
    depending on specific bargaining implementations. Implementations
    should be fast heuristics suitable for the matching phase.
    """
    
    @abstractmethod
    def evaluate_pair_potential(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        params: dict[str, Any] | None = None
    ) -> TradePotential:
        """
        Evaluate trade potential between two agents.
        
        This is a lightweight heuristic evaluation for pairing decisions.
        Does not perform full utility calculations.
        
        Args:
            agent_i: First agent
            agent_j: Second agent
            params: Optional simulation parameters
            
        Returns:
            TradePotential indicating feasibility and estimated surplus
        """
        pass


class QuoteBasedTradeEvaluator(TradePotentialEvaluator):
    """
    Default trade potential evaluator using quote overlaps.
    
    Fast heuristic based on bid/ask quotes. Does not perform
    full utility calculations. Suitable for matching phase.
    
    Uses the existing compute_surplus() logic from matching.py
    which checks quote overlaps and inventory feasibility.
    """
    
    def evaluate_pair_potential(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        params: dict[str, Any] | None = None
    ) -> TradePotential:
        """
        Evaluate using quote overlaps (existing compute_surplus logic).
        
        This provides a fast heuristic for matching protocols without
        requiring full utility calculations.
        """
        from .matching import compute_surplus
        
        # Use existing compute_surplus for quote-based evaluation
        best_overlap = compute_surplus(agent_i, agent_j)
        
        if best_overlap <= 0:
            return TradePotential(
                is_feasible=False,
                estimated_surplus=0.0,
                preferred_direction=None,
                confidence=1.0  # High confidence in "no trade" result
            )
        
        # Determine preferred direction from quotes
        bid_i = agent_i.quotes.get('bid_A_in_B', 0.0)
        ask_i = agent_i.quotes.get('ask_A_in_B', 0.0)
        bid_j = agent_j.quotes.get('bid_A_in_B', 0.0)
        ask_j = agent_j.quotes.get('ask_A_in_B', 0.0)
        
        overlap_dir1 = bid_i - ask_j  # i buys A from j
        overlap_dir2 = bid_j - ask_i  # j buys A from i
        
        if overlap_dir1 > overlap_dir2:
            preferred_direction = "i_gives_B"  # i buys A (gives B)
        else:
            preferred_direction = "i_gives_A"  # j buys A (i gives A)
        
        # Confidence based on overlap magnitude (heuristic)
        # Larger overlap relative to quotes suggests higher confidence
        max_quote = max(bid_i, ask_i, bid_j, ask_j, 1.0)
        confidence = min(1.0, best_overlap / max_quote)
        
        return TradePotential(
            is_feasible=True,
            estimated_surplus=best_overlap,
            preferred_direction=preferred_direction,
            confidence=confidence
        )


class TradeTuple(NamedTuple):
    """
    Complete trade specification.
    
    Utility type for bargaining protocols. Convenient format for representing
    trades in agent-centric terms (i/j) before converting to role-centric
    (buyer/seller) Trade effects.
    
    NamedTuple for performance (zero-overhead tuple).
    """
    dA_i: Decimal      # Change in A for agent_i
    dB_i: Decimal      # Change in B for agent_i
    dA_j: Decimal      # Change in A for agent_j
    dB_j: Decimal      # Change in B for agent_j
    surplus_i: float   # Utility gain for agent_i
    surplus_j: float   # Utility gain for agent_j
    price: float       # Price of A in terms of B
    pair_name: str     # Exchange pair name (e.g., "A<->B")


def trade_tuple_to_effect(
    pair: tuple[int, int],
    trade_tuple: TradeTuple,
    world: "WorldView",
    protocol_name: str
) -> "Trade":
    """
    Convert TradeTuple to Trade effect.
    
    Shared utility for bargaining protocols. Handles agent-centric 
    (i/j) to role-centric (buyer/seller) transformation.
    
    Args:
        pair: (agent_a_id, agent_b_id) - must match i/j ordering in trade_tuple
        trade_tuple: Trade specification from search
        world: WorldView context for tick
        protocol_name: Name of bargaining protocol
        
    Returns:
        Trade effect ready for system application
    """
    agent_a_id, agent_b_id = pair
    
    # Determine buyer/seller from trade direction
    if trade_tuple.dA_i > 0:  # agent_a receives A (buyer)
        buyer_id, seller_id = agent_a_id, agent_b_id
        dA = trade_tuple.dA_i
        dB = -trade_tuple.dB_i
        surplus_buyer = trade_tuple.surplus_i
        surplus_seller = trade_tuple.surplus_j
    else:  # agent_b receives A (buyer)
        buyer_id, seller_id = agent_b_id, agent_a_id
        dA = -trade_tuple.dA_i
        dB = trade_tuple.dB_i
        surplus_buyer = trade_tuple.surplus_j
        surplus_seller = trade_tuple.surplus_i
    
    from ..protocols.base import Trade
    
    return Trade(
        protocol_name=protocol_name,
        tick=world.tick,
        buyer_id=buyer_id,
        seller_id=seller_id,
        pair_type="A<->B",
        dA=abs(dA),
        dB=abs(dB),
        price=trade_tuple.price,
        metadata={
            "surplus_buyer": surplus_buyer,
            "surplus_seller": surplus_seller,
            "total_surplus": trade_tuple.surplus_i + trade_tuple.surplus_j,
        }
    )

