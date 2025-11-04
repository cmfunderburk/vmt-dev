"""
Trading System - Protocol Orchestrator

Coordinates bargaining protocols to execute trades between paired agents.

Phase 4 of the 7-phase simulation tick:
1. Process paired agents within interaction radius
2. Call bargaining protocol to negotiate
3. Apply trade or unpair effects
4. Log trades to telemetry

Version: 2025.10.26
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
from ..game_theory.bargaining import BargainingProtocol
from ..protocols import (
    Trade,
    Unpair,
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
        """Exchange pair type (always 'A<->B' for barter)."""
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
        # Build standard WorldView (no partner state hacking needed)
        from ..protocols.context_builders import build_world_view_for_agent
        world = build_world_view_for_agent(agent_a, sim)
        
        # Add debug assertions if enabled
        if sim.params.get("debug_immutability", False):
            # Snapshot agent state before protocol call
            snapshot_a = (agent_a.inventory.A, agent_a.inventory.B)
            snapshot_b = (agent_b.inventory.A, agent_b.inventory.B)
        
        # Call bargaining protocol with direct agent access
        effects = self.bargaining_protocol.negotiate(
            (agent_a.id, agent_b.id),
            (agent_a, agent_b),  # NEW: Pass agents directly
            world
        )
        
        # Verify immutability in debug mode
        if sim.params.get("debug_immutability", False):
            assert snapshot_a == (agent_a.inventory.A, agent_a.inventory.B), \
                f"Protocol {self.bargaining_protocol.name} mutated agent {agent_a.id} inventory!"
            assert snapshot_b == (agent_b.inventory.A, agent_b.inventory.B), \
                f"Protocol {self.bargaining_protocol.name} mutated agent {agent_b.id} inventory!"
        
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
        # Need to convert from Trade effect to (dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j)
        
        # Determine which agent is buyer/seller relative to agent_i/agent_j
        if buyer.id < seller.id:
            agent_i, agent_j = buyer, seller
            is_i_buyer = True
        else:
            agent_i, agent_j = seller, buyer
            is_i_buyer = False
        
        # Build trade tuple (barter-only: A<->B)
        if is_i_buyer:
            # agent_i (buyer) receives A, pays B
            dA_i, dB_i = effect.dA, -effect.dB
            dA_j, dB_j = -effect.dA, effect.dB
        else:
            # agent_i (seller) pays A, receives B
            dA_i, dB_i = -effect.dA, effect.dB
            dA_j, dB_j = effect.dA, -effect.dB
        
        # Get surpluses from metadata
        surplus_buyer = effect.metadata.get("surplus_buyer", 0.0)
        surplus_seller = effect.metadata.get("surplus_seller", 0.0)
        
        if is_i_buyer:
            surplus_i, surplus_j = surplus_buyer, surplus_seller
        else:
            surplus_i, surplus_j = surplus_seller, surplus_buyer
        
        # Execute trade
        trade_tuple = (dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j)
        execute_trade_generic(agent_i, agent_j, trade_tuple)
        
        if hasattr(sim, "_trades_made"):
            sim._trades_made[effect.buyer_id] = sim._trades_made.get(effect.buyer_id, 0) + 1
            sim._trades_made[effect.seller_id] = sim._trades_made.get(effect.seller_id, 0) + 1
        
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
        
        # Determine direction string (barter-only)
        direction = "A_traded_for_B"
        dA, dB = effect.dA, effect.dB
        
        # Log trade event (barter-only)
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
            exchange_pair_type="A<->B"
        )
