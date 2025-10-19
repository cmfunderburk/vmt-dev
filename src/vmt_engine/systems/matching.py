"""
Matching and trading helpers.

Determinism and discrete search principles:
- Partner choice uses surplus with tie-breaker by lowest id; pair attempts
  are executed once per tick in a globally sorted (min_id, max_id) order.
- Round-half-up maps price to integer ΔB via floor(price*ΔA + 0.5).
- Quotes are stable within a tick; they refresh only in Housekeeping for
  agents whose inventories changed during the tick.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from math import floor
from ._trade_attempt_logger import log_trade_attempt

if TYPE_CHECKING:
    from ..core import Agent
    from telemetry import TelemetryManager


def compute_surplus(agent_i: 'Agent', agent_j: 'Agent') -> float:
    """
    Compute best overlap between two agents' quotes.
    
    Returns max(overlap_dir1, overlap_dir2) where:
    - overlap_dir1 = agent_i buys A from agent_j (i.bid - j.ask)
    - overlap_dir2 = agent_j buys A from agent_i (j.bid - i.ask)
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        
    Returns:
        Best overlap (positive indicates potential for trade)
    """
    overlap_dir1 = agent_i.quotes.bid_A_in_B - agent_j.quotes.ask_A_in_B  # i buys from j
    overlap_dir2 = agent_j.quotes.bid_A_in_B - agent_i.quotes.ask_A_in_B  # j buys from i
    return max(overlap_dir1, overlap_dir2)


def choose_partner(agent: 'Agent', neighbors: list[tuple[int, tuple[int, int]]], 
                   all_agents: dict[int, 'Agent'],
                   current_tick: int = 0) -> tuple[int | None, float | None, list[tuple[int, float]]]:
    """
    Choose best trading partner from visible neighbors.
    
    Picks partner with highest surplus. Tie-breaking: lowest id.
    Skips partners in cooldown period (recently failed trade attempts).
    
    Args:
        agent: The choosing agent
        neighbors: List of (agent_id, position) tuples
        all_agents: Dictionary mapping agent_id to Agent
        current_tick: Current simulation tick (for cooldown checking)
        
    Returns:
        Tuple of (partner_id, surplus_with_partner, all_candidates)
        - partner_id: Chosen partner or None
        - surplus_with_partner: Surplus with chosen partner or None
        - all_candidates: List of (neighbor_id, surplus) for all positive surplus neighbors
    """
    if not neighbors:
        return None, None, []
    
    candidates = []
    all_candidates_with_surplus = []
    
    for neighbor_id, _ in neighbors:
        if neighbor_id not in all_agents:
            continue
        
        # Skip if partner is in cooldown
        if neighbor_id in agent.trade_cooldowns:
            if current_tick < agent.trade_cooldowns[neighbor_id]:
                continue  # Still in cooldown, skip this partner
            else:
                # Cooldown expired, remove from dict
                del agent.trade_cooldowns[neighbor_id]
        
        neighbor = all_agents[neighbor_id]
        surplus = compute_surplus(agent, neighbor)
        
        # Record all candidates with their surplus (even if not positive)
        if surplus > 0:
            all_candidates_with_surplus.append((neighbor_id, surplus))
            # Store (negative surplus for sorting, id for tie-breaking)
            candidates.append((-surplus, neighbor_id))
    
    if not candidates:
        return None, None, all_candidates_with_surplus
    
    # Sort by (-surplus, id) - highest surplus first, then lowest id
    candidates.sort()
    chosen_id = candidates[0][1]
    chosen_surplus = -candidates[0][0]
    
    return chosen_id, chosen_surplus, all_candidates_with_surplus


def improves(agent: 'Agent', dA: int, dB: int, eps: float = 1e-12) -> bool:
    """
    Check if trade improves agent's utility strictly.
    
    Args:
        agent: Agent considering the trade
        dA: Change in A (can be positive or negative)
        dB: Change in B (can be positive or negative)
        eps: Epsilon for strict improvement check
        
    Returns:
        True if utility improves by more than eps
    """
    if not agent.utility:
        return False
    
    A0, B0 = agent.inventory.A, agent.inventory.B
    u0 = agent.utility.u(A0, B0)
    u1 = agent.utility.u(A0 + dA, B0 + dB)
    
    return u1 > u0 + eps


def generate_price_candidates(ask: float, bid: float, dA: int) -> list[float]:
    """
    Generate candidate prices to try within [ask, bid] range.
    
    Strategy: Prefer prices that yield integer ΔB at this ΔA, plus a small
    evenly-spaced cover across [ask, bid] to avoid missing feasible blocks
    when midpoint rounding fails.
    
    Args:
        ask: Seller's minimum acceptable price
        bid: Buyer's maximum acceptable price
        dA: Trade size in units of A
        
    Returns:
        List of candidate prices, sorted from low to high
    """
    if ask > bid:
        return []
    
    candidates = set()
    
    # Add prices that give specific integer ΔB values
    # This is key for finding mutually beneficial discrete trades
    max_dB = int(bid * dA + 1)
    for target_dB in range(1, min(max_dB + 1, 20)):  # Cap at 20 to avoid excessive candidates
        price = target_dB / dA
        if ask <= price <= bid:
            candidates.add(price)
    
    # Also add evenly-spaced samples for coverage
    num_samples = 5
    for i in range(num_samples):
        price = ask + i * (bid - ask) / (num_samples - 1) if num_samples > 1 else ask
        candidates.add(price)
    
    # Sort from low to high (prefer lower prices for fairness)
    return sorted(candidates)


def find_compensating_block(buyer: 'Agent', seller: 'Agent', price: float,
                           dA_max: int, epsilon: float, tick: int = 0,
                           direction: str = "", surplus: float = 0.0,
                           telemetry: 'TelemetryManager' | None = None) -> tuple[int, int, float] | None:
    """
    Find minimal ΔA ∈ [1..dA_max] and a price where both agents improve utility.
    
    Searches multiple candidate prices within [seller.ask, buyer.bid] range
    to find mutually beneficial terms of trade. This handles the case where
    the midpoint price doesn't work due to integer rounding effects.
    
    Args:
        buyer: Agent buying good A
        seller: Agent selling good A
        price: Midpoint price hint (kept for backward compatibility)
        dA_max: Maximum amount of A to trade
        epsilon: Epsilon for utility improvement check
        tick: Current simulation tick (for logging)
        direction: Trade direction string (for logging)
        surplus: Computed surplus (for logging)
        telemetry: TelemetryManager instance (optional)
        
    Returns:
        (dA, dB, actual_price) tuple or None if no feasible block found
    """
    # Get the valid price range
    ask = seller.quotes.ask_A_in_B
    bid = buyer.quotes.bid_A_in_B
    
    # Iterate over trade sizes
    for dA in range(1, dA_max + 1):
        # Generate candidate prices for this trade size
        price_candidates = generate_price_candidates(ask, bid, dA)
        
        # Try each price candidate
        for test_price in price_candidates:
            # Round-half-up: floor(x + 0.5)
            dB = int(floor(test_price * dA + 0.5))
            
            # Check if dB is valid
            if dB <= 0:
                if telemetry:
                    log_trade_attempt(
                        telemetry, tick, buyer, seller, direction, test_price, surplus,
                        dA, dB, False, False, True, True, "fail", "dB_nonpositive"
                    )
                continue
            
            # Check feasibility (inventory constraints)
            buyer_feasible = buyer.inventory.B >= dB
            seller_feasible = seller.inventory.A >= dA
            
            if not seller_feasible or not buyer_feasible:
                if telemetry:
                    reason = "inventory_infeasible"
                    if not seller_feasible:
                        reason = "seller_insufficient_A"
                    if not buyer_feasible:
                        reason = "buyer_insufficient_B"
                    
                    log_trade_attempt(
                        telemetry, tick, buyer, seller, direction, test_price, surplus,
                        dA, dB, False, False, buyer_feasible, seller_feasible, "fail", reason
                    )
                continue
            
            # Check utility improvement for both agents
            buyer_improves_flag = improves(buyer, +dA, -dB, epsilon)
            seller_improves_flag = improves(seller, -dA, +dB, epsilon)
            
            if buyer_improves_flag and seller_improves_flag:
                # Success! Found a mutually beneficial trade
                if telemetry:
                    log_trade_attempt(
                        telemetry, tick, buyer, seller, direction, test_price, surplus,
                        dA, dB, True, True, True, True, "success", "utility_improves_both"
                    )
                return (dA, dB, test_price)  # Return the price that worked
            else:
                if telemetry:
                    reason = "utility_no_improvement"
                    if not buyer_improves_flag and not seller_improves_flag:
                        reason = "both_utility_no_improvement"
                    elif not buyer_improves_flag:
                        reason = "buyer_utility_no_improvement"
                    elif not seller_improves_flag:
                        reason = "seller_utility_no_improvement"

                    log_trade_attempt(
                        telemetry, tick, buyer, seller, direction, test_price, surplus,
                        dA, dB, buyer_improves_flag, seller_improves_flag,
                        True, True, "fail", reason
                    )
                # Continue trying other prices for this dA
    
    return None


def execute_trade(buyer: 'Agent', seller: 'Agent', dA: int, dB: int):
    """
    Execute trade block, updating inventories.
    
    Args:
        buyer: Agent buying good A
        seller: Agent selling good A
        dA: Amount of good A to trade
        dB: Amount of good B to trade
    """
    # Validate inventories
    assert seller.inventory.A >= dA, f"Seller {seller.id} has insufficient A: {seller.inventory.A} < {dA}"
    assert buyer.inventory.B >= dB, f"Buyer {buyer.id} has insufficient B: {buyer.inventory.B} < {dB}"
    
    # Transfer goods
    buyer.inventory.A += dA
    buyer.inventory.B -= dB
    seller.inventory.A -= dA
    seller.inventory.B += dB
    
    # Mark inventories as changed
    buyer.inventory_changed = True
    seller.inventory_changed = True


def trade_pair(agent_i: 'Agent', agent_j: 'Agent', params: dict[str, Any],
               telemetry: 'TelemetryManager', tick: int) -> bool:
    """
    Attempt ONE trade between a pair of agents this tick.
    
    If a trade occurs, quotes will be recalculated at the end of the tick
    (in housekeeping phase), and agents can trade again on the next tick.
    This continues until no mutually beneficial trades remain, at which
    point agents will unpair and seek other opportunities.
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        params: Simulation parameters (ΔA_max, epsilon, spread)
        telemetry: TelemetryManager for logging
        tick: Current tick
        
    Returns:
        True if a trade occurred this tick
    """
    # Compute surplus in both directions
    overlap_dir1 = agent_i.quotes.bid_A_in_B - agent_j.quotes.ask_A_in_B  # i buys from j
    overlap_dir2 = agent_j.quotes.bid_A_in_B - agent_i.quotes.ask_A_in_B  # j buys from i
    
    if overlap_dir1 <= 0 and overlap_dir2 <= 0:
        return False  # No positive surplus
    
    # Pick direction with larger surplus
    if overlap_dir1 > overlap_dir2:
        buyer, seller = agent_i, agent_j
        direction = "i_buys_A"
        surplus = overlap_dir1
    else:
        buyer, seller = agent_j, agent_i
        direction = "j_buys_A"
        surplus = overlap_dir2
    
    # Midpoint price hint
    price = 0.5 * (seller.quotes.ask_A_in_B + buyer.quotes.bid_A_in_B)
    
    # Find compensating block (with price search)
    block = find_compensating_block(
        buyer, seller, price, 
        params['dA_max'], params['epsilon'],
        tick, direction, surplus, telemetry
    )
    
    if block is None:
        # Trade failed - set cooldown for both agents
        cooldown_until = tick + params['trade_cooldown_ticks']
        agent_i.trade_cooldowns[agent_j.id] = cooldown_until
        agent_j.trade_cooldowns[agent_i.id] = cooldown_until
        return False  # No feasible block
    
    dA, dB, actual_price = block  # Returns the price that worked
    
    # Execute trade
    execute_trade(buyer, seller, dA, dB)
    
    # Log trade with actual price used
    telemetry.log_trade(
        tick, buyer.pos[0], buyer.pos[1],
        buyer.id, seller.id,
        dA, dB, actual_price, direction
    )
    
    # Mark that inventories changed (quotes will be refreshed in housekeeping)
    agent_i.inventory_changed = True
    agent_j.inventory_changed = True
    
    return True

