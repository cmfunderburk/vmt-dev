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
from typing import TYPE_CHECKING, Any, Optional
from math import floor
from decimal import Decimal
from ._trade_attempt_logger import log_trade_attempt

if TYPE_CHECKING:
    from ..core import Agent
    from telemetry import TelemetryManager
else:
    # Avoid circular import
    from ..core.decimal_config import quantize_quantity


def compute_surplus(agent_i: 'Agent', agent_j: 'Agent') -> float:
    """
    Compute best overlap between two agents' quotes with inventory feasibility check.
    
    Returns max(overlap_dir1, overlap_dir2) where:
    - overlap_dir1 = agent_i buys A from agent_j (i.bid - j.ask)
    - overlap_dir2 = agent_j buys A from agent_i (j.bid - i.ask)
    
    INVENTORY FEASIBILITY: Returns 0 if neither agent has sufficient inventory
    to execute even a 1-unit trade in either direction. This prevents futile
    pairings when inventory constraints make theoretical surplus unrealizable.
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        
    Returns:
        Best overlap (positive indicates potential for trade), or 0 if no
        direction is inventory-feasible
    """
    # Use dict.get() with default 0.0 for safety
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


def estimate_money_aware_surplus(agent_i: 'Agent', agent_j: 'Agent') -> tuple[float, str]:
    """
    Estimate best feasible surplus using quotes for barter (lightweight, O(1)).
    
    Uses agent quotes to approximate surplus without full search.
    This is a fast heuristic for pairing decisions in barter-only economy.
    
    INVENTORY FEASIBILITY: Returns 0 if neither direction is inventory-feasible.
    This prevents futile pairings when inventory constraints make theoretical 
    surplus unrealizable.
    
    Note: This function is named "estimate_money_aware_surplus" for historical
    reasons but now only handles barter trades. The name is retained for backward
    compatibility with existing code that imports this function.
    
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
    
    This is acceptable because:
    1. Once paired, agents execute the ACTUAL best trade (using full utility calc)
    2. The estimator is still directionally correct most of the time
    3. Performance matters: O(1) per neighbor vs O(inventory_A × prices) for exact calc
    4. Agents still find good trades, just maybe not with the globally optimal partner
    
    For perfectly accurate pairing, matching protocols can use TradePotentialEvaluator
    with full utility calculations, but expect higher computational cost.
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        
    Returns:
        Tuple of (best_surplus, best_pair_type) where:
        - best_surplus: Estimated surplus (positive indicates potential for trade)
        - best_pair_type: Always "A<->B" for barter-only economy
        
        Returns (0.0, "") if no positive surplus found.
    """
    # Only barter: A<->B
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
        best_surplus = max(feasible_overlaps)
        return best_surplus, "A<->B"
    else:
        return 0.0, ""


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


def improves(agent: 'Agent', dA: int | Decimal, dB: int | Decimal, eps: float = 1e-12) -> bool:
    """
    Check if trade improves agent's utility strictly.
    
    Args:
        agent: Agent considering the trade
        dA: Change in A (can be positive or negative, int or Decimal)
        dB: Change in B (can be positive or negative, int or Decimal)
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


def generate_price_candidates(ask: float, bid: float, dA: Decimal) -> list[float]:
    """
    Generate candidate prices to try within [ask, bid] range.
    
    Strategy: Prefer prices that yield quantized ΔB at this ΔA, plus a small
    evenly-spaced cover across [ask, bid] to avoid missing feasible blocks
    when midpoint rounding fails.
    
    Args:
        ask: Seller's minimum acceptable price
        bid: Buyer's maximum acceptable price
        dA: Trade size in units of A (Decimal)
        
    Returns:
        List of candidate prices, sorted from low to high
    """
    if ask > bid:
        return []
    
    candidates = set()
    
    # Add prices that give specific quantized ΔB values
    # Convert dA to float for calculation, then quantize results
    dA_float = float(dA)
    max_dB_float = bid * dA_float + 1
    # Generate candidate prices that yield quantized dB values
    # Step by reasonable increments (use 10 candidates up to max)
    for i in range(1, min(21, int(max_dB_float) + 1)):  # Cap at 20 to avoid excessive candidates
        target_dB = Decimal(str(i))
        price = float(target_dB / dA)
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
                           epsilon: float, tick: int = 0,
                           direction: str = "", surplus: float = 0.0,
                           telemetry: Optional['TelemetryManager'] = None) -> Optional[tuple[Decimal, Decimal, float]]:
    """
    Find minimal ΔA ∈ [1..seller.inventory.A] and a price where both agents improve utility.
    
    Searches multiple candidate prices within [seller.ask, buyer.bid] range
    to find mutually beneficial terms of trade. This handles the case where
    the midpoint price doesn't work due to decimal rounding effects.
    
    Args:
        buyer: Agent buying good A
        seller: Agent selling good A
        price: Midpoint price hint (kept for backward compatibility)
        epsilon: Epsilon for utility improvement check
        tick: Current simulation tick (for logging)
        direction: Trade direction string (for logging)
        surplus: Computed surplus (for logging)
        telemetry: TelemetryManager instance (optional)
        
    Returns:
        (dA, dB, actual_price) tuple or None if no feasible block found
        dA and dB are Decimal values quantized to the configured precision
    """
    from ..core.decimal_config import quantize_quantity
    
    # Get the valid price range
    ask = seller.quotes.get('ask_A_in_B', 1.0)
    bid = buyer.quotes.get('bid_A_in_B', 1.0)
    
    # Determine maximum trade size from seller's inventory
    max_dA = seller.inventory.A
    if max_dA <= 0:
        return None  # Seller has nothing to sell
    
    # Get quantization step size for fractional trade search
    from ..core.decimal_config import QUANTITY_QUANTIZER
    step_size = QUANTITY_QUANTIZER
    
    # Iterate over trade sizes from minimum to maximum
    # Start from one step (smallest non-zero trade)
    current_dA = step_size
    while current_dA <= max_dA:
        # Quantize current_dA to ensure precision
        dA = quantize_quantity(current_dA)
        
        # Generate candidate prices for this trade size
        price_candidates = generate_price_candidates(ask, bid, dA)
        
        # Try each price candidate
        for test_price in price_candidates:
            # Calculate dB and quantize to configured precision
            dB_raw = Decimal(str(test_price)) * Decimal(str(dA))
            dB = quantize_quantity(dB_raw)
            
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
                # dA is already Decimal and quantized
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
        
        # Move to next trade size
        current_dA += step_size
    
    return None


def execute_trade(buyer: 'Agent', seller: 'Agent', dA: int | Decimal, dB: int | Decimal):
    """
    Execute trade block, updating inventories.
    
    Args:
        buyer: Agent buying good A
        seller: Agent selling good A
        dA: Amount of good A to trade (int or Decimal)
        dB: Amount of good B to trade (int or Decimal)
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
        params: Simulation parameters (epsilon, spread)
        telemetry: TelemetryManager for logging
        tick: Current tick
        
    Returns:
        True if a trade occurred this tick
    """
    # Compute surplus in both directions
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
    
    # Midpoint price hint
    ask = seller.quotes.get('ask_A_in_B', 1.0)
    bid = buyer.quotes.get('bid_A_in_B', 1.0)
    price = 0.5 * (ask + bid)
    
    # Find compensating block (with price search)
    block = find_compensating_block(
        buyer, seller, price, 
        params['epsilon'],
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
# Phase 2b: Trade Execution
# ============================================================================

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
        trade: Trade tuple (dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j)
               from find_compensating_block_generic
        
    Invariants maintained:
    - Non-negativity: All inventories remain ≥ 0
    - Conservation: dA_i + dA_j = 0, dB_i + dB_j = 0
    - Decimal quantities (quantized to configured precision)
    - inventory_changed flags set for both agents
    """
    dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j = trade
    
    # Verify conservation
    assert dA_i + dA_j == 0, f"Good A not conserved: {dA_i} + {dA_j} != 0"
    assert dB_i + dB_j == 0, f"Good B not conserved: {dB_i} + {dB_j} != 0"
    
    # Apply changes to agent i
    agent_i.inventory.A += dA_i
    agent_i.inventory.B += dB_i
    
    # Apply changes to agent j
    agent_j.inventory.A += dA_j
    agent_j.inventory.B += dB_j
    
    # Verify non-negativity
    assert agent_i.inventory.A >= 0, f"Agent {agent_i.id} A inventory negative: {agent_i.inventory.A}"
    assert agent_i.inventory.B >= 0, f"Agent {agent_i.id} B inventory negative: {agent_i.inventory.B}"
    assert agent_j.inventory.A >= 0, f"Agent {agent_j.id} A inventory negative: {agent_j.inventory.A}"
    assert agent_j.inventory.B >= 0, f"Agent {agent_j.id} B inventory negative: {agent_j.inventory.B}"
    
    # Set inventory_changed flags
    agent_i.inventory_changed = True
    agent_j.inventory_changed = True


def get_allowed_exchange_pairs() -> list[str]:
    """
    Get allowed exchange pair types (always barter-only).
    
    Returns:
        List of allowed pair type strings: ["A<->B"]
    """
    return ["A<->B"]

