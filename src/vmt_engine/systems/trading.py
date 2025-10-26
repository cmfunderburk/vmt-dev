"""
Trading System - Protocol Orchestrator

Coordinates bargaining protocols to execute trades between paired agents.

Phase 4 of the 7-phase simulation tick:
1. Process paired agents within interaction radius
2. Call bargaining protocol to negotiate
3. Apply trade or unpair effects
4. Log trades to telemetry

Version: 2025.10.26 (Phase 1 - Refactored for Protocol System)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
from ..protocols import (
    BargainingProtocol,
    Trade,
    Unpair,
    build_trade_world_view,
)
from .matching import execute_trade_generic

if TYPE_CHECKING:
    from ..simulation import Simulation
    from ..core import Agent


@dataclass
class TradeCandidate:
    """
    Represents a potential trade between two agents.
    
    DEPRECATED: This class is kept for backward compatibility with tests.
    The protocol system uses Effect types instead.
    """
    buyer_id: int
    seller_id: int
    good_sold: str
    good_paid: str
    dX: int
    dY: int
    buyer_surplus: float
    seller_surplus: float
    
    @property
    def total_surplus(self) -> float:
        """Total welfare gain from this trade."""
        return self.buyer_surplus + self.seller_surplus
    
    @property
    def pair_type(self) -> str:
        """Exchange pair type (e.g., 'A<->M', 'B<->A')."""
        return f"{self.good_sold}<->{self.good_paid}"


class TradeSystem:
    """
    Phase 4: Orchestrate protocol-based trade negotiation.
    
    Responsibilities:
    - Find paired agents within interaction radius
    - Build WorldView for trade negotiation
    - Call bargaining protocol
    - Apply trade/unpair effects
    - Log trades to telemetry
    
    The actual bargaining logic is delegated to protocols.
    """
    
    def __init__(self):
        self.bargaining_protocol: Optional[BargainingProtocol] = None
    
    def execute(self, sim: "Simulation") -> None:
        """Execute trade phase using bargaining protocol."""
        
        # Track processed pairs to avoid double-processing
        processed_pairs = set()
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            if agent.paired_with_id is None:
                continue  # Skip unpaired agents
            
            partner_id = agent.paired_with_id
            
            # Skip if pair already processed
            pair_key = tuple(sorted([agent.id, partner_id]))
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)
            
            partner = sim.agent_by_id[partner_id]
            
            # Check distance
            distance = abs(agent.pos[0] - partner.pos[0]) + abs(agent.pos[1] - partner.pos[1])
            
            if distance <= sim.params["interaction_radius"]:
                # Within range: attempt trade via bargaining protocol
                self._negotiate_trade(agent, partner, sim)
            # else: Too far apart, stay paired and keep moving
    
    def _negotiate_trade(self, agent_a: "Agent", agent_b: "Agent", sim: "Simulation") -> None:
        """
        Negotiate trade between two agents using bargaining protocol.
        
        Args:
            agent_a: First agent in pair
            agent_b: Second agent in pair
            sim: Current simulation state
        """
        # Build WorldView for trade negotiation
        world = build_trade_world_view(agent_a, agent_b, sim)
        
        # Call bargaining protocol
        effects = self.bargaining_protocol.negotiate((agent_a.id, agent_b.id), world)
        
        # Apply effects
        for effect in effects:
            if isinstance(effect, Trade):
                self._apply_trade_effect(effect, sim)
            elif isinstance(effect, Unpair):
                self._apply_unpair_effect(effect, sim)
    
    def _apply_trade_effect(self, effect: Trade, sim: "Simulation") -> None:
        """
        Apply trade effect: update inventories and log to telemetry.
        
        Note: Agents REMAIN PAIRED after successful trade (can trade again next tick).
        """
        buyer = sim.agent_by_id[effect.buyer_id]
        seller = sim.agent_by_id[effect.seller_id]
        
        # Determine trade tuple format for execute_trade_generic
        # Need to convert from Trade effect to (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
        
        # Determine which agent is buyer/seller relative to agent_i/agent_j
        if buyer.id < seller.id:
            agent_i, agent_j = buyer, seller
            is_i_buyer = True
        else:
            agent_i, agent_j = seller, buyer
            is_i_buyer = False
        
        # Build trade tuple based on pair type and direction
        if effect.pair_type == "A<->B":
            if is_i_buyer:
                # agent_i (buyer) receives A, pays B
                dA_i, dB_i, dM_i = effect.dA, -effect.dB, 0
                dA_j, dB_j, dM_j = -effect.dA, effect.dB, 0
            else:
                # agent_i (seller) pays A, receives B
                dA_i, dB_i, dM_i = -effect.dA, effect.dB, 0
                dA_j, dB_j, dM_j = effect.dA, -effect.dB, 0
        
        elif effect.pair_type == "A<->M":
            if is_i_buyer:
                # agent_i (buyer) receives A, pays M
                dA_i, dB_i, dM_i = effect.dA, 0, -effect.dM
                dA_j, dB_j, dM_j = -effect.dA, 0, effect.dM
            else:
                # agent_i (seller) pays A, receives M
                dA_i, dB_i, dM_i = -effect.dA, 0, effect.dM
                dA_j, dB_j, dM_j = effect.dA, 0, -effect.dM
        
        else:  # "B<->M"
            if is_i_buyer:
                # agent_i (buyer) receives B, pays M
                dA_i, dB_i, dM_i = 0, effect.dB, -effect.dM
                dA_j, dB_j, dM_j = 0, -effect.dB, effect.dM
            else:
                # agent_i (seller) pays B, receives M
                dA_i, dB_i, dM_i = 0, -effect.dB, effect.dM
                dA_j, dB_j, dM_j = 0, effect.dB, -effect.dM
        
        # Get surpluses from metadata
        surplus_buyer = effect.metadata.get("surplus_buyer", 0.0)
        surplus_seller = effect.metadata.get("surplus_seller", 0.0)
        
        if is_i_buyer:
            surplus_i, surplus_j = surplus_buyer, surplus_seller
        else:
            surplus_i, surplus_j = surplus_seller, surplus_buyer
        
        # Execute trade
        trade_tuple = (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
        execute_trade_generic(agent_i, agent_j, trade_tuple)
        
        # Log to telemetry
        self._log_trade(effect, sim)
    
    def _apply_unpair_effect(self, effect: Unpair, sim: "Simulation") -> None:
        """
        Apply unpair effect: dissolve pairing and set trade cooldown.
        """
        agent_a = sim.agent_by_id[effect.agent_a]
        agent_b = sim.agent_by_id[effect.agent_b]
        
        # Dissolve pairing
        agent_a.paired_with_id = None
        agent_b.paired_with_id = None
        
        # Set trade cooldown
        cooldown_until = sim.tick + sim.params.get('trade_cooldown_ticks', 10)
        agent_a.trade_cooldowns[effect.agent_b] = cooldown_until
        agent_b.trade_cooldowns[effect.agent_a] = cooldown_until
        
        # Log unpair event
        sim.telemetry.log_pairing_event(
            sim.tick, effect.agent_a, effect.agent_b, "unpair", effect.reason
        )
    
    def _log_trade(self, effect: Trade, sim: "Simulation") -> None:
        """Log trade to telemetry."""
        buyer = sim.agent_by_id[effect.buyer_id]
        seller = sim.agent_by_id[effect.seller_id]
        
        # Determine direction string
        if effect.pair_type == "A<->B":
            direction = "A_traded_for_B"
            dA, dB, dM = effect.dA, effect.dB, 0
        elif effect.pair_type == "A<->M":
            direction = "A_traded_for_M"
            dA, dB, dM = effect.dA, 0, effect.dM
        elif effect.pair_type == "B<->M":
            direction = "B_traded_for_M"
            dA, dB, dM = 0, effect.dB, effect.dM
        else:
            direction = "unknown"
            dA, dB, dM = effect.dA, effect.dB, effect.dM
        
        # Log trade event (using original API signature)
        sim.telemetry.log_trade(
            tick=sim.tick,
            x=buyer.pos[0],
            y=buyer.pos[1],
            buyer_id=effect.buyer_id,
            seller_id=effect.seller_id,
            dA=dA,
            dB=dB,
            price=effect.price,
            direction=direction,
            dM=dM,
            exchange_pair_type=effect.pair_type
        )
