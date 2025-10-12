"""
Matching and trading system.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from math import floor

if TYPE_CHECKING:
    from ..core import Agent
    from telemetry.logger import TradeLogger


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
                   all_agents: dict[int, 'Agent']) -> int | None:
    """
    Choose best trading partner from visible neighbors.
    
    Picks partner with highest surplus. Tie-breaking: lowest id.
    
    Args:
        agent: The choosing agent
        neighbors: List of (agent_id, position) tuples
        all_agents: Dictionary mapping agent_id to Agent
        
    Returns:
        Partner agent_id or None if no positive surplus
    """
    if not neighbors:
        return None
    
    candidates = []
    
    for neighbor_id, _ in neighbors:
        if neighbor_id not in all_agents:
            continue
        
        neighbor = all_agents[neighbor_id]
        surplus = compute_surplus(agent, neighbor)
        
        # Only consider positive surplus
        if surplus > 0:
            # Store (negative surplus for sorting, id for tie-breaking)
            candidates.append((-surplus, neighbor_id))
    
    if not candidates:
        return None
    
    # Sort by (-surplus, id) - highest surplus first, then lowest id
    candidates.sort()
    return candidates[0][1]


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


def find_compensating_block(buyer: 'Agent', seller: 'Agent', price: float,
                           dA_max: int, epsilon: float) -> tuple[int, int] | None:
    """
    Find minimal ΔA ∈ [1..dA_max] such that ΔB = round_half_up(price * ΔA)
    and both agents improve their utility.
    
    Args:
        buyer: Agent buying good A
        seller: Agent selling good A
        price: Trade price (A in terms of B)
        dA_max: Maximum amount of A to trade
        epsilon: Epsilon for utility improvement check
        
    Returns:
        (dA, dB) tuple or None if no feasible block found
    """
    for dA in range(1, dA_max + 1):
        # Round-half-up: floor(x + 0.5)
        dB = int(floor(price * dA + 0.5))
        
        if dB <= 0:
            continue
        
        # Check feasibility (inventory constraints)
        if seller.inventory.A < dA or buyer.inventory.B < dB:
            continue
        
        # Check utility improvement for both agents
        if improves(buyer, +dA, -dB, epsilon) and improves(seller, -dA, +dB, epsilon):
            return (dA, dB)
    
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
               logger: 'TradeLogger', tick: int) -> bool:
    """
    Attempt trade between a pair of agents.
    
    Supports multi-block continuation until surplus exhausted.
    
    Args:
        agent_i: First agent
        agent_j: Second agent
        params: Simulation parameters (ΔA_max, epsilon, spread)
        logger: Trade logger
        tick: Current tick
        
    Returns:
        True if any trade occurred
    """
    from .quotes import compute_quotes
    
    traded = False
    
    while True:
        # Compute surplus in both directions
        overlap_dir1 = agent_i.quotes.bid_A_in_B - agent_j.quotes.ask_A_in_B  # i buys from j
        overlap_dir2 = agent_j.quotes.bid_A_in_B - agent_i.quotes.ask_A_in_B  # j buys from i
        
        if overlap_dir1 <= 0 and overlap_dir2 <= 0:
            break  # No positive surplus
        
        # Pick direction with larger surplus
        if overlap_dir1 > overlap_dir2:
            buyer, seller = agent_i, agent_j
            direction = "i_buys_A"
        else:
            buyer, seller = agent_j, agent_i
            direction = "j_buys_A"
        
        # Midpoint price
        price = 0.5 * (seller.quotes.ask_A_in_B + buyer.quotes.bid_A_in_B)
        
        # Find compensating block
        block = find_compensating_block(
            buyer, seller, price, 
            params['ΔA_max'], params['epsilon']
        )
        
        if block is None:
            break  # No feasible block
        
        dA, dB = block
        
        # Execute trade
        execute_trade(buyer, seller, dA, dB)
        traded = True
        
        # Log trade
        logger.log_trade(
            tick, buyer.pos[0], buyer.pos[1],
            buyer.id, seller.id,
            dA, dB, price, direction
        )
        
        # Refresh quotes for both agents
        agent_i.quotes = compute_quotes(agent_i, params['spread'], params['epsilon'])
        agent_j.quotes = compute_quotes(agent_j, params['spread'], params['epsilon'])
        agent_i.inventory_changed = False
        agent_j.inventory_changed = False
    
    return traded

