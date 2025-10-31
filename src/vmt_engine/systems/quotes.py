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


def compute_quotes(agent: 'Agent', spread: float, epsilon: float) -> dict[str, float]:
    """
    Compute ask/bid quotes for barter exchange pairs (A<->B).
    
    Args:
        agent: Agent to compute quotes for
        spread: Bid-ask spread parameter (0 ≤ spread)
        epsilon: Small value for zero-safe calculations
        
    Returns:
        Dict with keys: ask_A_in_B, bid_A_in_B, ask_B_in_A, bid_B_in_A,
                       p_min_A_in_B, p_max_A_in_B, p_min_B_in_A, p_max_B_in_A
    """
    quotes = {}
    
    if not agent.utility:
        # No utility function, return neutral quotes (equal prices)
        quotes['ask_A_in_B'] = 1.0
        quotes['bid_A_in_B'] = 1.0
        quotes['ask_B_in_A'] = 1.0
        quotes['bid_B_in_A'] = 1.0
        quotes['p_min_A_in_B'] = 1.0
        quotes['p_max_A_in_B'] = 1.0
        quotes['p_min_B_in_A'] = 1.0
        quotes['p_max_B_in_A'] = 1.0
        return quotes
    
    A = agent.inventory.A
    B = agent.inventory.B
    
    # Barter pair: A<->B
    p_min_A_in_B, p_max_A_in_B = agent.utility.reservation_bounds_A_in_B(A, B, epsilon)
    ask_A_in_B = p_min_A_in_B * (1 + spread)
    bid_A_in_B = p_max_A_in_B * (1 - spread)
    
    quotes['ask_A_in_B'] = max(0.0, ask_A_in_B)
    quotes['bid_A_in_B'] = max(0.0, bid_A_in_B)
    quotes['p_min_A_in_B'] = max(0.0, p_min_A_in_B)
    quotes['p_max_A_in_B'] = max(0.0, p_max_A_in_B)
    
    # Barter pair: B<->A (reciprocal)
    if p_max_A_in_B > epsilon:
        p_min_B_in_A = 1.0 / p_max_A_in_B
        ask_B_in_A = p_min_B_in_A * (1 + spread)
    else:
        p_min_B_in_A = 1e6  # Large value if A is essentially free
        ask_B_in_A = p_min_B_in_A
    
    if p_min_A_in_B > epsilon:
        p_max_B_in_A = 1.0 / p_min_A_in_B
        bid_B_in_A = p_max_B_in_A * (1 - spread)
    else:
        p_max_B_in_A = 1e6
        bid_B_in_A = p_max_B_in_A
    
    quotes['ask_B_in_A'] = max(0.0, ask_B_in_A)
    quotes['bid_B_in_A'] = max(0.0, bid_B_in_A)
    quotes['p_min_B_in_A'] = max(0.0, p_min_B_in_A)
    quotes['p_max_B_in_A'] = max(0.0, p_max_B_in_A)
    
    return quotes


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
