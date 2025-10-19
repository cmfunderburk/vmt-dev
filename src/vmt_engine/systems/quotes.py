"""
Quote generation and management.

Contract:
- Quotes are derived from reservation bounds (p_min, p_max) with optional
  spread: ask = p_min*(1+spread), bid = p_max*(1-spread).
- Quote invariants: ask_A_in_B ≥ p_min and bid_A_in_B ≤ p_max, both ≥ 0.
- Quotes are stable within a tick; only Housekeeping refreshes quotes for
  agents whose inventories changed (agent.inventory_changed=True), then
  resets the flag. Matching/Trading must not mutate quotes mid-tick.
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
        Quote with ask_A_in_B, bid_A_in_B, p_min, and p_max
    """
    from ..core.state import Quote
    
    if not agent.utility:
        # No utility function, return default quotes
        return Quote(ask_A_in_B=1.0, bid_A_in_B=1.0, p_min=1.0, p_max=1.0)
    
    A = agent.inventory.A
    B = agent.inventory.B
    
    # Get reservation bounds (seller's minimum and buyer's maximum)
    p_min, p_max = agent.utility.reservation_bounds_A_in_B(A, B, epsilon)
    
    # Apply spread (no mid-tick mutation; recompute only in Housekeeping)
    ask_A_in_B = p_min * (1 + spread)
    bid_A_in_B = p_max * (1 - spread)
    
    # Ensure non-negative
    ask_A_in_B = max(0.0, ask_A_in_B)
    bid_A_in_B = max(0.0, bid_A_in_B)
    
    return Quote(ask_A_in_B=ask_A_in_B, bid_A_in_B=bid_A_in_B, p_min=p_min, p_max=p_max)


def refresh_quotes_if_needed(agent: 'Agent', spread: float, epsilon: float) -> bool:
    """
    Recompute quotes if inventory changed. This is called in Housekeeping only
    to preserve per-tick quote stability.
    
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

