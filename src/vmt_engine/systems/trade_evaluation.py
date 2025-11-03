"""
Trade Evaluation Abstractions

Provides protocol-agnostic interfaces for trade evaluation and discovery.
Decouples matching protocols from bargaining protocol implementations.

This module defines two key abstraction layers:
1. TradePotentialEvaluator: Lightweight heuristic evaluation for matching phase
2. TradeDiscoverer: Full trade discovery for bargaining phase

Version: 2025.11.03 (Decoupling Refactor)
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, NamedTuple
from decimal import Decimal

if TYPE_CHECKING:
    from ..core import Agent


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
    
    Used by bargaining protocols for negotiation.
    NamedTuple for performance (tuple overhead, named access).
    """
    dA_i: Decimal      # Change in A for agent_i
    dB_i: Decimal      # Change in B for agent_i
    dA_j: Decimal      # Change in A for agent_j
    dB_j: Decimal      # Change in B for agent_j
    surplus_i: float   # Utility gain for agent_i
    surplus_j: float   # Utility gain for agent_j
    price: float       # Price of A in terms of B
    pair_name: str     # Exchange pair name (e.g., "A<->B")


class TradeDiscoverer(ABC):
    """
    Abstract interface for discovering trade terms between agents.
    
    Each bargaining protocol can implement its own discovery algorithm.
    This allows different bargaining protocols to use different
    trade discovery strategies (e.g., compensating block, Nash bargaining,
    optimization-based search, etc.)
    
    Unlike TradePotentialEvaluator, implementations perform full utility
    calculations and detailed trade search.
    """
    
    @abstractmethod
    def discover_trade(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        params: dict[str, Any] | None = None,
        epsilon: float = 1e-9
    ) -> TradeTuple | None:
        """
        Discover a mutually beneficial trade between two agents.
        
        Returns the first feasible trade found (not exhaustive search).
        This performs full utility calculations and detailed trade search.
        
        Args:
            agent_i: First agent
            agent_j: Second agent
            params: Optional simulation parameters
            epsilon: Threshold for utility improvement (strict positivity)
            
        Returns:
            TradeTuple if feasible trade exists, None otherwise
        """
        pass

