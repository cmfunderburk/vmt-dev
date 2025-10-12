"""
Quote generation and management system.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Agent, Quote


def compute_quotes(agent: 'Agent', spread: float, epsilon: float) -> 'Quote':
    """
    Compute ask/bid quotes from reservation bounds.
    
    Args:
        agent: Agent to compute quotes for
        spread: Bid-ask spread parameter (0 ≤ spread)
        epsilon: Small value for zero-safe calculations
        
    Returns:
        Quote with ask_A_in_B and bid_A_in_B
    """
    from ..core.state import Quote
    
    if not agent.utility:
        # No utility function, return default quotes
        return Quote(ask_A_in_B=1.0, bid_A_in_B=1.0)
    
    A = agent.inventory.A
    B = agent.inventory.B
    
    # Get reservation bounds
    p_min, p_max = agent.utility.reservation_bounds_A_in_B(A, B, epsilon)
    
    # Apply spread
    ask_A_in_B = p_min * (1 + spread)
    bid_A_in_B = p_max * (1 - spread)
    
    # Ensure non-negative
    ask_A_in_B = max(0.0, ask_A_in_B)
    bid_A_in_B = max(0.0, bid_A_in_B)
    
    return Quote(ask_A_in_B=ask_A_in_B, bid_A_in_B=bid_A_in_B)


def refresh_quotes_if_needed(agent: 'Agent', spread: float, epsilon: float) -> bool:
    """
    Recompute quotes if inventory changed.
    
    Args:
        agent: Agent to check and refresh
        spread: Bid-ask spread parameter
        epsilon: Small value for zero-safe calculations
        
    Returns:
        True if quotes were refreshed, False otherwise
    """
    if agent.inventory_changed:
        agent.quotes = compute_quotes(agent, spread, epsilon)
        agent.inventory_changed = False
        return True
    return False

