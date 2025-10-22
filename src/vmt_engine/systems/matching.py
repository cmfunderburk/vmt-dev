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
    Compute best overlap between two agents' quotes with inventory feasibility check.
    
    Returns max(overlap_dir1, overlap_dir2) where:
    - overlap_dir1 = agent_i buys A from agent_j (i.bid - j.ask)
    - overlap_dir2 = agent_j buys A from agent_i (j.bid - i.ask)
    
    INVENTORY FEASIBILITY: Returns 0 if neither agent has sufficient inventory
    to execute even a 1-unit trade in either direction. This prevents futile
    pairings when inventory constraints make theoretical surplus unrealizable.
    
    DEPRECATED: This function uses barter-only logic. For money-aware matching,
    use the generic matching primitives in Phase 2b.
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        
    Returns:
        Best overlap (positive indicates potential for trade), or 0 if no
        direction is inventory-feasible
    """
    # Use dict.get() with default 0.0 for safety (money-aware API)
    bid_i = agent_i.quotes.get('bid_A_in_B', 0.0)
    ask_i = agent_i.quotes.get('ask_A_in_B', 0.0)
    bid_j = agent_j.quotes.get('bid_A_in_B', 0.0)
    ask_j = agent_j.quotes.get('ask_A_in_B', 0.0)
    
    # Calculate theoretical overlaps
    overlap_dir1 = bid_i - ask_j  # i buys A from j
    overlap_dir2 = bid_j - ask_i  # j buys A from i
    
    # Check inventory feasibility for each direction
    # Direction 1: i buys A from j (j sells A for B, i pays with B)
    dir1_feasible = (agent_j.inventory.A >= 1 and agent_i.inventory.B >= 1)
    
    # Direction 2: j buys A from i (i sells A for B, j pays with B)
    dir2_feasible = (agent_i.inventory.A >= 1 and agent_j.inventory.B >= 1)
    
    # Only consider overlaps for feasible directions
    feasible_overlaps = []
    if dir1_feasible and overlap_dir1 > 0:
        feasible_overlaps.append(overlap_dir1)
    if dir2_feasible and overlap_dir2 > 0:
        feasible_overlaps.append(overlap_dir2)
    
    # Return max feasible overlap, or 0 if none are feasible
    return max(feasible_overlaps) if feasible_overlaps else 0.0


def estimate_money_aware_surplus(agent_i: 'Agent', agent_j: 'Agent', regime: str) -> tuple[float, str]:
    """
    Estimate best feasible surplus using quotes (lightweight, O(1)).
    
    Uses agent quotes to approximate surplus without full search.
    This is a fast heuristic for pairing decisions in money-aware regimes.
    
    Money-first priority on ties: A<->M > B<->M > A<->B
    
    INVENTORY FEASIBILITY: Returns 0 if neither direction is inventory-feasible.
    This prevents futile pairings when inventory constraints make theoretical 
    surplus unrealizable.
    
    IMPORTANT LIMITATION - Heuristic Approximation:
    ================================================
    This function uses QUOTE OVERLAPS (price differences) as a proxy for surplus.
    Quote overlap = bid_price - ask_price, which represents the "price space" 
    for mutually beneficial trade.
    
    However, quote overlaps may not perfectly predict ACTUAL UTILITY GAINS:
    - Quotes are based on MRS (marginal rate of substitution) at current inventory
    - Actual trades change inventory discretely, affecting utility non-linearly
    - With non-linear utilities (CES, Quadratic, etc.), the relationship between
      MRS and utility change depends on the curvature of the utility function
    - Integer rounding and discrete quantities can cause discrepancies
    
    Example: A quote overlap of 4.3 for barter might predict higher surplus than
    a quote overlap of 2.1 for money trades, but the ACTUAL utility calculation
    might show the money trade provides more utility gain (e.g., 2.3 vs 1.3).
    
    This is acceptable because:
    1. Once paired, agents execute the ACTUAL best trade (using full utility calc)
    2. The estimator is still directionally correct most of the time
    3. Performance matters: O(1) per neighbor vs O(dA_max × prices) for exact calc
    4. Agents still find good trades, just maybe not with the globally optimal partner
    
    For perfectly accurate pairing, use find_all_feasible_trades() instead, but
    expect O(N × dA_max × prices) cost in Decision phase.
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        regime: Exchange regime ("money_only", "mixed", "mixed_liquidity_gated")
        
    Returns:
        Tuple of (best_surplus, best_pair_type) where:
        - best_surplus: Estimated surplus (positive indicates potential for trade)
        - best_pair_type: Exchange pair type ("A<->B", "A<->M", "B<->M", or "")
        
        Returns (0.0, "") if no positive surplus found.
    """
    # Determine which pairs to evaluate based on regime
    if regime == "money_only":
        candidate_pairs = ["A<->M", "B<->M"]
    elif regime in ["mixed", "mixed_liquidity_gated"]:
        candidate_pairs = ["A<->M", "B<->M", "A<->B"]
    else:
        # Fallback to barter (shouldn't happen if called correctly)
        candidate_pairs = ["A<->B"]
    
    # Money-first priority (lower is better)
    PAIR_PRIORITY = {
        "A<->M": 0,
        "B<->M": 1,
        "A<->B": 2,
    }
    
    best_surplus = 0.0
    best_pair_type = ""
    best_priority = 999
    
    for pair in candidate_pairs:
        if pair == "A<->B":
            # Barter: A for B
            bid_i = agent_i.quotes.get('bid_A_in_B', 0.0)
            ask_i = agent_i.quotes.get('ask_A_in_B', 0.0)
            bid_j = agent_j.quotes.get('bid_A_in_B', 0.0)
            ask_j = agent_j.quotes.get('ask_A_in_B', 0.0)
            
            # Calculate overlaps
            overlap_dir1 = bid_i - ask_j  # i buys A from j
            overlap_dir2 = bid_j - ask_i  # j buys A from i
            
            # Check inventory feasibility
            dir1_feasible = (agent_j.inventory.A >= 1 and agent_i.inventory.B >= 1)
            dir2_feasible = (agent_i.inventory.A >= 1 and agent_j.inventory.B >= 1)
            
            # Get best feasible overlap
            feasible_overlaps = []
            if dir1_feasible and overlap_dir1 > 0:
                feasible_overlaps.append(overlap_dir1)
            if dir2_feasible and overlap_dir2 > 0:
                feasible_overlaps.append(overlap_dir2)
            
            if feasible_overlaps:
                surplus = max(feasible_overlaps)
            else:
                surplus = 0.0
        
        elif pair == "A<->M":
            # Monetary: A for M
            bid_i = agent_i.quotes.get('bid_A_in_M', 0.0)
            ask_i = agent_i.quotes.get('ask_A_in_M', 0.0)
            bid_j = agent_j.quotes.get('bid_A_in_M', 0.0)
            ask_j = agent_j.quotes.get('ask_A_in_M', 0.0)
            
            # Calculate overlaps
            overlap_dir1 = bid_i - ask_j  # i buys A from j with M
            overlap_dir2 = bid_j - ask_i  # j buys A from i with M
            
            # Check inventory feasibility
            dir1_feasible = (agent_j.inventory.A >= 1 and agent_i.inventory.M >= 1)
            dir2_feasible = (agent_i.inventory.A >= 1 and agent_j.inventory.M >= 1)
            
            # Get best feasible overlap
            feasible_overlaps = []
            if dir1_feasible and overlap_dir1 > 0:
                feasible_overlaps.append(overlap_dir1)
            if dir2_feasible and overlap_dir2 > 0:
                feasible_overlaps.append(overlap_dir2)
            
            if feasible_overlaps:
                surplus = max(feasible_overlaps)
            else:
                surplus = 0.0
        
        else:  # "B<->M"
            # Monetary: B for M
            bid_i = agent_i.quotes.get('bid_B_in_M', 0.0)
            ask_i = agent_i.quotes.get('ask_B_in_M', 0.0)
            bid_j = agent_j.quotes.get('bid_B_in_M', 0.0)
            ask_j = agent_j.quotes.get('ask_B_in_M', 0.0)
            
            # Calculate overlaps
            overlap_dir1 = bid_i - ask_j  # i buys B from j with M
            overlap_dir2 = bid_j - ask_i  # j buys B from i with M
            
            # Check inventory feasibility
            dir1_feasible = (agent_j.inventory.B >= 1 and agent_i.inventory.M >= 1)
            dir2_feasible = (agent_i.inventory.B >= 1 and agent_j.inventory.M >= 1)
            
            # Get best feasible overlap
            feasible_overlaps = []
            if dir1_feasible and overlap_dir1 > 0:
                feasible_overlaps.append(overlap_dir1)
            if dir2_feasible and overlap_dir2 > 0:
                feasible_overlaps.append(overlap_dir2)
            
            if feasible_overlaps:
                surplus = max(feasible_overlaps)
            else:
                surplus = 0.0
        
        # Update best if this surplus is better, or equal with higher priority
        priority = PAIR_PRIORITY.get(pair, 999)
        if surplus > best_surplus or (surplus == best_surplus and surplus > 0 and priority < best_priority):
            best_surplus = surplus
            best_pair_type = pair
            best_priority = priority
    
    return best_surplus, best_pair_type


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
    
    DEPRECATED: This function uses barter-only logic. For money-aware matching,
    use find_compensating_block_generic in Phase 2b.
    
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
    # Get the valid price range (money-aware API: use dict.get())
    ask = seller.quotes.get('ask_A_in_B', 1.0)
    bid = buyer.quotes.get('bid_A_in_B', 1.0)
    
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
    
    DEPRECATED: This function uses barter-only logic. For money-aware trading,
    use generic matching primitives in Phase 2b.
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        params: Simulation parameters (ΔA_max, epsilon, spread)
        telemetry: TelemetryManager for logging
        tick: Current tick
        
    Returns:
        True if a trade occurred this tick
    """
    # Compute surplus in both directions (money-aware API: use dict.get())
    bid_i = agent_i.quotes.get('bid_A_in_B', 0.0)
    ask_i = agent_i.quotes.get('ask_A_in_B', 0.0)
    bid_j = agent_j.quotes.get('bid_A_in_B', 0.0)
    ask_j = agent_j.quotes.get('ask_A_in_B', 0.0)
    
    overlap_dir1 = bid_i - ask_j  # i buys from j
    overlap_dir2 = bid_j - ask_i  # j buys from i
    
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
    
    # Midpoint price hint (money-aware API: use dict.get())
    ask = seller.quotes.get('ask_A_in_B', 1.0)
    bid = buyer.quotes.get('bid_A_in_B', 1.0)
    price = 0.5 * (ask + bid)
    
    # Find compensating block (with price search)
    block = find_compensating_block(
        buyer, seller, price, 
        params['dA_max'], params['epsilon'],
        tick, direction, surplus, telemetry
    )
    
    if block is None:
        # Trade failed - UNPAIR and set cooldown
        # This means trade opportunities are exhausted
        agent_i.paired_with_id = None
        agent_j.paired_with_id = None
        
        cooldown_until = tick + params['trade_cooldown_ticks']
        agent_i.trade_cooldowns[agent_j.id] = cooldown_until
        agent_j.trade_cooldowns[agent_i.id] = cooldown_until
        
        # Log unpair event
        telemetry.log_pairing_event(
            tick, agent_i.id, agent_j.id, "unpair", "trade_failed"
        )
        
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
    
    # REMAIN PAIRED - agents will attempt another trade next tick
    # This is critical for O(N) performance
    
    return True


# ============================================================================
# Phase 2b: Generic Matching Primitives (Money-Aware)
# ============================================================================

def find_compensating_block_generic(
    agent_i: 'Agent', 
    agent_j: 'Agent',
    pair: str,
    params: dict[str, Any],
    epsilon: float = 1e-9
) -> tuple[int, int, int, int, int, int, float, float] | None:
    """
    Find mutually beneficial trade block for any exchange pair.
    
    Supports three pairs:
    - "A<->B": Barter exchange (agent i gives ΔA_i, receives ΔB_i)
    - "A<->M": Good A for money (agent i gives ΔA_i, receives ΔM_i)
    - "B<->M": Good B for money (agent i gives ΔB_i, receives ΔM_i)
    
    Search strategy (matches legacy find_compensating_block):
    - Try quantities in ascending order: dA ∈ [1, 2, ..., dA_max]
    - For each quantity, try candidate prices from generate_price_candidates()
    - Prices are sorted low-to-high and include integer-yielding values
    - Return FIRST (dA, price) combination where both ΔU_i > 0 AND ΔU_j > 0
    
    Economic correctness:
    - Agents act rationally: accept any trade that strictly improves their utility
    - Utilities are ordinal - agents don't try to "maximize" across trades
    - Deterministic search order ensures reproducibility
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        pair: Exchange pair ("A<->B", "A<->M", or "B<->M")
        params: Simulation parameters (must include 'utility' key for each agent)
        epsilon: Threshold for strict utility improvement
        
    Returns:
        Tuple of (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
        representing the best trade block, or None if no mutually beneficial trade exists.
        
        For barter A<->B:
            - agent i: gives dA_i > 0, receives dB_i > 0; dM_i = 0
            - agent j: receives dA_j > 0, gives dB_j > 0; dM_j = 0
            - dA_i = dA_j, dB_i = dB_j (conservation)
        
        For A<->M:
            - agent i gives ΔA, receives ΔM (or vice versa)
            - dB_i = dB_j = 0 (no B exchange)
        
        For B<->M:
            - agent i gives ΔB, receives ΔM (or vice versa)
            - dA_i = dA_j = 0 (no A exchange)
    """
    from ..econ.utility import u_total
    
    # Get agent utilities
    if not agent_i.utility or not agent_j.utility:
        return None
    
    params_i = {'utility': agent_i.utility, 'lambda_money': agent_i.lambda_money}
    params_j = {'utility': agent_j.utility, 'lambda_money': agent_j.lambda_money}
    
    # Current utility
    u_i_0 = u_total(agent_i.inventory, params_i)
    u_j_0 = u_total(agent_j.inventory, params_j)
    
    dA_max = params.get('dA_max', 5)
    
    if pair == "A<->B":
        # Barter: agent i and j exchange A for B
        # Try both directions: i gives A (seller) or i gives B (buyer)
        
        # Direction 1: agent i sells A, buys B
        ask_i = agent_i.quotes.get('ask_A_in_B', float('inf'))
        bid_j = agent_j.quotes.get('bid_A_in_B', 0.0)
        
        if ask_i <= bid_j:
            # Generate price candidates in overlap region
            price_candidates = generate_price_candidates(ask_i, bid_j, 1)
            
            for dA in range(1, min(dA_max + 1, agent_i.inventory.A + 1)):
                for price in generate_price_candidates(ask_i, bid_j, dA):
                    dB = int(floor(price * dA + 0.5))
                    
                    if dB <= 0 or dB > agent_j.inventory.B:
                        continue
                    
                    # Check utility improvements
                    from ..core.state import Inventory
                    inv_i_new = Inventory(A=agent_i.inventory.A - dA, B=agent_i.inventory.B + dB, M=agent_i.inventory.M)
                    inv_j_new = Inventory(A=agent_j.inventory.A + dA, B=agent_j.inventory.B - dB, M=agent_j.inventory.M)
                    
                    u_i_new = u_total(inv_i_new, params_i)
                    u_j_new = u_total(inv_j_new, params_j)
                    
                    surplus_i = u_i_new - u_i_0
                    surplus_j = u_j_new - u_j_0
                    
                    if surplus_i > epsilon and surplus_j > epsilon:
                        # Return FIRST mutually beneficial trade found
                        return (-dA, dB, 0, dA, -dB, 0, surplus_i, surplus_j)
        
        # Direction 2: agent i buys A, sells B
        bid_i = agent_i.quotes.get('bid_A_in_B', 0.0)
        ask_j = agent_j.quotes.get('ask_A_in_B', float('inf'))
        
        if ask_j <= bid_i:
            for dA in range(1, min(dA_max + 1, agent_j.inventory.A + 1)):
                for price in generate_price_candidates(ask_j, bid_i, dA):
                    dB = int(floor(price * dA + 0.5))
                    
                    if dB <= 0 or dB > agent_i.inventory.B:
                        continue
                    
                    from ..core.state import Inventory
                    inv_i_new = Inventory(A=agent_i.inventory.A + dA, B=agent_i.inventory.B - dB, M=agent_i.inventory.M)
                    inv_j_new = Inventory(A=agent_j.inventory.A - dA, B=agent_j.inventory.B + dB, M=agent_j.inventory.M)
                    
                    u_i_new = u_total(inv_i_new, params_i)
                    u_j_new = u_total(inv_j_new, params_j)
                    
                    surplus_i = u_i_new - u_i_0
                    surplus_j = u_j_new - u_j_0
                    
                    if surplus_i > epsilon and surplus_j > epsilon:
                        # Return FIRST mutually beneficial trade found
                        return (dA, -dB, 0, -dA, dB, 0, surplus_i, surplus_j)
    
    elif pair == "A<->M":
        # Good A for money
        # Direction 1: agent i sells A for M
        ask_i = agent_i.quotes.get('ask_A_in_M', float('inf'))
        bid_j = agent_j.quotes.get('bid_A_in_M', 0.0)
        
        if ask_i <= bid_j:
            for dA in range(1, min(dA_max + 1, agent_i.inventory.A + 1)):
                for price in generate_price_candidates(ask_i, bid_j, dA):
                    dM = int(floor(price * dA + 0.5))
                    
                    if dM <= 0 or dM > agent_j.inventory.M:
                        continue
                    
                    from ..core.state import Inventory
                    inv_i_new = Inventory(A=agent_i.inventory.A - dA, B=agent_i.inventory.B, M=agent_i.inventory.M + dM)
                    inv_j_new = Inventory(A=agent_j.inventory.A + dA, B=agent_j.inventory.B, M=agent_j.inventory.M - dM)
                    
                    u_i_new = u_total(inv_i_new, params_i)
                    u_j_new = u_total(inv_j_new, params_j)
                    
                    surplus_i = u_i_new - u_i_0
                    surplus_j = u_j_new - u_j_0
                    
                    if surplus_i > epsilon and surplus_j > epsilon:
                        # Return FIRST mutually beneficial trade found
                        return (-dA, 0, dM, dA, 0, -dM, surplus_i, surplus_j)
        
        # Direction 2: agent i buys A for M
        bid_i = agent_i.quotes.get('bid_A_in_M', 0.0)
        ask_j = agent_j.quotes.get('ask_A_in_M', float('inf'))
        
        if ask_j <= bid_i:
            for dA in range(1, min(dA_max + 1, agent_j.inventory.A + 1)):
                for price in generate_price_candidates(ask_j, bid_i, dA):
                    dM = int(floor(price * dA + 0.5))
                    
                    if dM <= 0 or dM > agent_i.inventory.M:
                        continue
                    
                    from ..core.state import Inventory
                    inv_i_new = Inventory(A=agent_i.inventory.A + dA, B=agent_i.inventory.B, M=agent_i.inventory.M - dM)
                    inv_j_new = Inventory(A=agent_j.inventory.A - dA, B=agent_j.inventory.B, M=agent_j.inventory.M + dM)
                    
                    u_i_new = u_total(inv_i_new, params_i)
                    u_j_new = u_total(inv_j_new, params_j)
                    
                    surplus_i = u_i_new - u_i_0
                    surplus_j = u_j_new - u_j_0
                    
                    if surplus_i > epsilon and surplus_j > epsilon:
                        # Return FIRST mutually beneficial trade found
                        return (dA, 0, -dM, -dA, 0, dM, surplus_i, surplus_j)
    
    elif pair == "B<->M":
        # Good B for money
        # Direction 1: agent i sells B for M
        ask_i = agent_i.quotes.get('ask_B_in_M', float('inf'))
        bid_j = agent_j.quotes.get('bid_B_in_M', 0.0)
        
        if ask_i <= bid_j:
            for dB in range(1, min(dA_max + 1, agent_i.inventory.B + 1)):
                for price in generate_price_candidates(ask_i, bid_j, dB):
                    dM = int(floor(price * dB + 0.5))
                    
                    if dM <= 0 or dM > agent_j.inventory.M:
                        continue
                    
                    from ..core.state import Inventory
                    inv_i_new = Inventory(A=agent_i.inventory.A, B=agent_i.inventory.B - dB, M=agent_i.inventory.M + dM)
                    inv_j_new = Inventory(A=agent_j.inventory.A, B=agent_j.inventory.B + dB, M=agent_j.inventory.M - dM)
                    
                    u_i_new = u_total(inv_i_new, params_i)
                    u_j_new = u_total(inv_j_new, params_j)
                    
                    surplus_i = u_i_new - u_i_0
                    surplus_j = u_j_new - u_j_0
                    
                    if surplus_i > epsilon and surplus_j > epsilon:
                        # Return FIRST mutually beneficial trade found
                        return (0, -dB, dM, 0, dB, -dM, surplus_i, surplus_j)
        
        # Direction 2: agent i buys B for M
        bid_i = agent_i.quotes.get('bid_B_in_M', 0.0)
        ask_j = agent_j.quotes.get('ask_B_in_M', float('inf'))
        
        if ask_j <= bid_i:
            for dB in range(1, min(dA_max + 1, agent_j.inventory.B + 1)):
                for price in generate_price_candidates(ask_j, bid_i, dB):
                    dM = int(floor(price * dB + 0.5))
                    
                    if dM <= 0 or dM > agent_i.inventory.M:
                        continue
                    
                    from ..core.state import Inventory
                    inv_i_new = Inventory(A=agent_i.inventory.A, B=agent_i.inventory.B + dB, M=agent_i.inventory.M - dM)
                    inv_j_new = Inventory(A=agent_j.inventory.A, B=agent_j.inventory.B - dB, M=agent_j.inventory.M + dM)
                    
                    u_i_new = u_total(inv_i_new, params_i)
                    u_j_new = u_total(inv_j_new, params_j)
                    
                    surplus_i = u_i_new - u_i_0
                    surplus_j = u_j_new - u_j_0
                    
                    if surplus_i > epsilon and surplus_j > epsilon:
                        # Return FIRST mutually beneficial trade found
                        return (0, dB, -dM, 0, -dB, dM, surplus_i, surplus_j)
    
    # No mutually beneficial trade found
    return None


def find_all_feasible_trades(
    agent_i: 'Agent',
    agent_j: 'Agent',
    exchange_regime: str,
    params: dict[str, Any],
    epsilon: float = 1e-9
) -> list[tuple[str, tuple]]:
    """
    Find ALL mutually beneficial trades across allowed exchange pairs.
    
    Used in mixed regimes (Phase 3+) where multiple trade types may be
    feasible simultaneously and tie-breaking is needed.
    
    Search strategy:
    - Try all pairs allowed by regime: A<->B, A<->M, B<->M
    - Return ALL feasible trades (not just first)
    - Caller ranks and selects best trade
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        exchange_regime: "barter_only", "money_only", "mixed", or "mixed_liquidity_gated"
        params: Simulation parameters
        epsilon: Threshold for strict improvement
        
    Returns:
        List of (pair_name, trade_tuple) for all feasible trades.
        Empty list if no trades possible.
        
        Each trade_tuple is (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
        pair_name is one of: "A<->B", "A<->M", "B<->M"
    """
    # Determine which pairs to try based on regime
    if exchange_regime == "barter_only":
        candidate_pairs = ["A<->B"]
    elif exchange_regime == "money_only":
        candidate_pairs = ["A<->M", "B<->M"]
    elif exchange_regime in ["mixed", "mixed_liquidity_gated"]:
        candidate_pairs = ["A<->B", "A<->M", "B<->M"]
    else:
        # Unknown regime, default to barter
        candidate_pairs = ["A<->B"]
    
    # Collect all feasible trades
    feasible_trades = []
    
    for pair in candidate_pairs:
        trade = find_compensating_block_generic(agent_i, agent_j, pair, params, epsilon)
        
        if trade is not None:
            # Found a mutually beneficial trade - add to list
            feasible_trades.append((pair, trade))
    
    return feasible_trades


def find_best_trade(
    agent_i: 'Agent',
    agent_j: 'Agent',
    exchange_regime: str,
    params: dict[str, Any],
    epsilon: float = 1e-9
) -> tuple[str, tuple] | None:
    """
    Find a mutually beneficial trade across allowed exchange pairs.
    
    Search strategy:
    - Try pairs in fixed order: A<->B, then A<->M, then B<->M (as allowed by regime)
    - Return FIRST pair that yields a mutually beneficial trade
    - Within each pair, uses same search as legacy algorithm (see find_compensating_block_generic)
    
    Economic correctness:
    - Agents act rationally: accept first trade found where ΔU > 0
    - No attempt to "maximize" or "optimize" across multiple opportunities
    - Deterministic ordering ensures reproducibility
    
    NOTE: This function is used for barter_only and money_only regimes.
    For mixed regimes (Phase 3+), use find_all_feasible_trades() instead
    to enable proper tie-breaking when multiple trade types are available.
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        exchange_regime: "barter_only", "money_only", or "mixed"
        params: Simulation parameters
        epsilon: Threshold for strict improvement
        
    Returns:
        Tuple of (pair_name, trade_tuple) where trade_tuple is the result
        from find_compensating_block_generic, or None if no trade possible.
        
        pair_name is one of: "A<->B", "A<->M", "B<->M"
    """
    # Determine which pairs to try based on regime
    if exchange_regime == "barter_only":
        candidate_pairs = ["A<->B"]
    elif exchange_regime == "money_only":
        candidate_pairs = ["A<->M", "B<->M"]
    elif exchange_regime == "mixed":
        candidate_pairs = ["A<->B", "A<->M", "B<->M"]
    else:
        # Unknown regime, default to barter
        candidate_pairs = ["A<->B"]
    
    # Try each allowed pair in deterministic order
    # Return FIRST successful trade found
    for pair in candidate_pairs:
        trade = find_compensating_block_generic(agent_i, agent_j, pair, params, epsilon)
        
        if trade is not None:
            # Found a mutually beneficial trade - return immediately
            return (pair, trade)
    
    # No mutually beneficial trade found in any pair
    return None


def execute_trade_generic(
    agent_i: 'Agent',
    agent_j: 'Agent',
    trade: tuple
) -> None:
    """
    Execute a trade, updating both agents' inventories.
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        trade: Trade tuple (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
               from find_compensating_block_generic
        
    Invariants maintained:
    - Non-negativity: All inventories remain ≥ 0
    - Conservation: dA_i + dA_j = 0, dB_i + dB_j = 0, dM_i + dM_j = 0
    - Integer quantities
    - inventory_changed flags set for both agents
    """
    dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade
    
    # Verify conservation
    assert dA_i + dA_j == 0, f"Good A not conserved: {dA_i} + {dA_j} != 0"
    assert dB_i + dB_j == 0, f"Good B not conserved: {dB_i} + {dB_j} != 0"
    assert dM_i + dM_j == 0, f"Money not conserved: {dM_i} + {dM_j} != 0"
    
    # Apply changes to agent i
    agent_i.inventory.A += dA_i
    agent_i.inventory.B += dB_i
    agent_i.inventory.M += dM_i
    
    # Apply changes to agent j
    agent_j.inventory.A += dA_j
    agent_j.inventory.B += dB_j
    agent_j.inventory.M += dM_j
    
    # Verify non-negativity
    assert agent_i.inventory.A >= 0, f"Agent {agent_i.id} A inventory negative: {agent_i.inventory.A}"
    assert agent_i.inventory.B >= 0, f"Agent {agent_i.id} B inventory negative: {agent_i.inventory.B}"
    assert agent_i.inventory.M >= 0, f"Agent {agent_i.id} M inventory negative: {agent_i.inventory.M}"
    assert agent_j.inventory.A >= 0, f"Agent {agent_j.id} A inventory negative: {agent_j.inventory.A}"
    assert agent_j.inventory.B >= 0, f"Agent {agent_j.id} B inventory negative: {agent_j.inventory.B}"
    assert agent_j.inventory.M >= 0, f"Agent {agent_j.id} M inventory negative: {agent_j.inventory.M}"
    
    # Set inventory_changed flags
    agent_i.inventory_changed = True
    agent_j.inventory_changed = True

