"""
Quote generation and management.

Contract:
- Quotes are derived from reservation bounds (p_min, p_max) with optional
  spread: ask = p_min*(1+spread), bid = p_max*(1-spread).
- Quote invariants: ask_A_in_B ≥ p_min and bid_A_in_B ≤ p_max, both ≥ 0.
- Quotes are stable within a tick; only Housekeeping refreshes quotes for
  agents whose inventories changed (agent.inventory_changed=True), then
  resets the flag. Matching/Trading must not mutate quotes mid-tick.

Money-aware API (Phase 2):
- compute_quotes() returns dict[str, float] with keys for all exchange pairs
- filter_quotes_by_regime() restricts visibility based on exchange_regime
- Legacy Quote dataclass return type is deprecated
"""

from typing import TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    from ..core import Agent, Quote


def compute_quotes(agent: 'Agent', spread: float, epsilon: float, money_scale: int = 1) -> dict[str, float]:
    """
    Compute ask/bid quotes for all exchange pairs (money-aware API).
    
    Returns quotes for:
    - Barter pairs: A<->B
    - Monetary pairs: A<->M, B<->M
    
    Visibility is controlled by filter_quotes_by_regime().
    
    Args:
        agent: Agent to compute quotes for
        spread: Bid-ask spread parameter (0 ≤ spread)
        epsilon: Small value for zero-safe calculations
        money_scale: Minor units per major unit (default: 1)
        
    Returns:
        Dict with keys: ask_A_in_B, bid_A_in_B, ask_B_in_A, bid_B_in_A,
                       ask_A_in_M, bid_A_in_M, ask_B_in_M, bid_B_in_M,
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
        
        # Monetary quotes (using lambda_money as price)
        lambda_m = agent.lambda_money
        quotes['ask_A_in_M'] = lambda_m * money_scale
        quotes['bid_A_in_M'] = lambda_m * money_scale
        quotes['ask_B_in_M'] = lambda_m * money_scale
        quotes['bid_B_in_M'] = lambda_m * money_scale
        
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
    
    # Monetary pairs: A<->M and B<->M
    # Price in money = (MU_good / MU_money) * money_scale
    # MU_money depends on utility form (linear: constant λ, log: λ/(M+M_0))
    from ..econ.utility import mu_money
    
    mu_m = mu_money(
        agent.inventory.M,
        agent.lambda_money,
        money_utility_form=agent.money_utility_form,
        M_0=agent.M_0,
        epsilon=epsilon
    )
    
    # Ask/bid for A in terms of M (minor units)
    mu_A = agent.utility.mu_A(A, B)
    price_A_in_M = (mu_A / mu_m) * money_scale if mu_m > epsilon else 1e6 * money_scale
    quotes['ask_A_in_M'] = max(0.0, price_A_in_M * (1 + spread))
    quotes['bid_A_in_M'] = max(0.0, price_A_in_M * (1 - spread))
    
    # Ask/bid for B in terms of M
    mu_B = agent.utility.mu_B(A, B)
    price_B_in_M = (mu_B / mu_m) * money_scale if mu_m > epsilon else 1e6 * money_scale
    quotes['ask_B_in_M'] = max(0.0, price_B_in_M * (1 + spread))
    quotes['bid_B_in_M'] = max(0.0, price_B_in_M * (1 - spread))
    
    return quotes


def filter_quotes_by_regime(quotes: dict[str, float], exchange_regime: str) -> dict[str, float]:
    """
    Filter quotes based on exchange_regime parameter.
    
    - "barter_only": Only barter keys (A<->B, B<->A)
    - "money_only": Only monetary keys (A<->M, B<->M)
    - "mixed": All keys
    
    Args:
        quotes: Full quotes dictionary
        exchange_regime: Exchange regime ("barter_only", "money_only", or "mixed")
        
    Returns:
        Filtered quotes dictionary
    """
    if exchange_regime == "barter_only":
        # Only barter pairs
        return {
            k: v for k, v in quotes.items()
            if 'A_in_B' in k or 'B_in_A' in k
        }
    elif exchange_regime == "money_only":
        # Only monetary pairs
        return {
            k: v for k, v in quotes.items()
            if 'A_in_M' in k or 'B_in_M' in k
        }
    elif exchange_regime == "mixed":
        # All pairs
        return quotes.copy()
    else:
        # Unknown regime, default to barter_only for safety
        warnings.warn(
            f"Unknown exchange_regime '{exchange_regime}', defaulting to barter_only",
            UserWarning,
            stacklevel=2
        )
        return {
            k: v for k, v in quotes.items()
            if 'A_in_B' in k or 'B_in_A' in k
        }


def refresh_quotes_if_needed(agent: 'Agent', spread: float, epsilon: float, 
                            money_scale: int = 1, exchange_regime: str = "barter_only") -> bool:
    """
    Recompute quotes if inventory changed. This is called in Housekeeping only
    to preserve per-tick quote stability.
    
    Args:
        agent: Agent to check and refresh
        spread: Bid-ask spread parameter
        epsilon: Small value for zero-safe calculations
        money_scale: Minor units per major unit (default: 1)
        exchange_regime: Exchange regime for filtering (default: "barter_only")
        
    Returns:
        True if quotes were refreshed, False otherwise
    """
    if agent.inventory_changed:
        # Compute all quotes, then filter by regime
        all_quotes = compute_quotes(agent, spread, epsilon, money_scale)
        agent.quotes = filter_quotes_by_regime(all_quotes, exchange_regime)
        agent.inventory_changed = False
        return True
    return False

