"""
Legacy Bargaining Protocol

Implements the original VMT compensating block bargaining using generic
matching primitives for barter trade negotiation.

This protocol is bit-compatible with the pre-protocol TradeSystem implementation.

Version: 2025.10.26 (Phase 1 - Legacy Adapter)
"""

from typing import Optional
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from ...protocols.base import Effect, Trade, Unpair
from ...protocols.context import WorldView
from ...systems.matching import (
    find_all_feasible_trades,
    find_best_trade,
)


@register_protocol(
    category="bargaining",
    name="legacy_compensating_block",
    description="Legacy compensating block bargaining",
    properties=["deterministic", "legacy"],
    complexity="O(K)",  # K = number of feasible trades examined
    references=[],
    phase="1",
)
class LegacyBargainingProtocol(BargainingProtocol):
    """
    Legacy compensating block bargaining.
    
    Uses matching primitives to find mutually beneficial barter trades.
    
    Returns Trade effect if successful, Unpair effect if negotiation fails.
    """
    
    @property
    def name(self) -> str:
        return "legacy_compensating_block"
    
    @property
    def version(self) -> str:
        return "2025.10.26"
    
    # Class-level for registry
    VERSION = "2025.10.26"
    
    def negotiate(self, pair: tuple[int, int], world: WorldView) -> list[Effect]:
        """
        Negotiate trade between paired agents.
        
        Args:
            pair: (agent_a_id, agent_b_id) tuple
            world: Context with both agents' states
        
        Returns:
            [Trade(...)] if successful
            [Unpair(...)] if no mutually beneficial trade found
        """
        agent_a_id, agent_b_id = pair
        
        # Note: WorldView is from one agent's perspective
        # For bargaining, we need both agents' full states
        # This will be passed via WorldView.params or we need ProtocolContext
        # For now, assume we have access to both agents' quotes and inventories
        
        # Check if agents are within interaction range
        # (Distance check should happen before calling negotiate, but let's be defensive)
        
        epsilon = world.params.get("epsilon", 1e-9)
        
        # Build pseudo-agent objects from WorldView for matching functions
        agent_i = self._build_agent_from_world(world, agent_a_id)
        agent_j = self._build_agent_from_world(world, agent_b_id)
        
        # Barter-only: find first feasible trade
        result = find_best_trade(
            agent_i, agent_j, world.params, epsilon
        )
        
        if result is None:
            # No mutually beneficial trade - unpair
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=agent_a_id,
                agent_b=agent_b_id,
                reason="trade_failed"
            )]
        
        pair_name, trade = result
        
        # Convert to Trade effect
        return [self._create_trade_effect(
            agent_a_id, agent_b_id, pair_name, trade, world
        )]
    
    def _build_agent_from_world(self, world: WorldView, agent_id: int):
        """
        Build a pseudo-Agent object from WorldView for legacy matching functions.
        
        This is a temporary adapter. In Phase 2, we'll refactor matching functions
        to work directly with protocol contexts.
        """
        from ...core.agent import Agent
        from ...core.state import Inventory
        
        # If this is the current agent
        if agent_id == world.agent_id:
            inventory = Inventory(
                A=world.inventory.get("A", 0),
                B=world.inventory.get("B", 0),
            )
            quotes = world.quotes
            utility = world.utility
        else:
            # Find partner in visible agents
            partner_view = None
            for neighbor in world.visible_agents:
                if neighbor.agent_id == agent_id:
                    partner_view = neighbor
                    break
            
            if partner_view is None:
                # Partner not visible - shouldn't happen for paired agents
                # Create minimal agent for defensive purposes
                inventory = Inventory(A=0, B=0)
                quotes = {}
                utility = None
            else:
                # Extract from AgentView
                # Note: AgentView doesn't have inventory, only quotes
                # We'll need to get this from params or extend AgentView
                inventory = Inventory(
                    A=world.params.get(f"partner_{agent_id}_inv_A", 0),
                    B=world.params.get(f"partner_{agent_id}_inv_B", 0)
                )
                quotes = partner_view.quotes
                utility = world.params.get(f"partner_{agent_id}_utility", None)
        
        # Create minimal agent
        agent = Agent(
            id=agent_id,
            pos=(0, 0),  # Not used in matching
            inventory=inventory,
            utility=utility,
            quotes=quotes,
        )
        
        return agent
    
    def _create_trade_effect(
        self,
        agent_a_id: int,
        agent_b_id: int,
        pair_name: str,
        trade: tuple,
        world: WorldView
    ) -> Trade:
        """
        Convert trade tuple to Trade effect.
        
        Args:
            agent_a_id: First agent ID
            agent_b_id: Second agent ID  
            pair_name: Pair type (always "A<->B")
            trade: Tuple (dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j)
            world: Context for tick
        
        Returns:
            Trade effect
        """
        dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j = trade
        
        # Determine buyer/seller and trade amounts (barter-only)
        # Convention: buyer receives A, pays B
        if dA_i > 0:  # agent_a receives A (buyer)
            buyer_id, seller_id = agent_a_id, agent_b_id
            dA, dB = dA_i, -dB_i
            price = -dB_i / dA_i if dA_i != 0 else 0.0  # B per unit A
        else:  # agent_b receives A (buyer)
            buyer_id, seller_id = agent_b_id, agent_a_id
            dA, dB = -dA_i, -dB_i
            price = dB_i / (-dA_i) if dA_i != 0 else 0.0
        
        # Create Trade effect
        return Trade(
            protocol_name=self.name,
            tick=world.tick,
            buyer_id=buyer_id,
            seller_id=seller_id,
            pair_type="A<->B",
            dA=abs(dA),
            dB=abs(dB),
            price=abs(price),
            metadata={
                "surplus_buyer": surplus_i if buyer_id == agent_a_id else surplus_j,
                "surplus_seller": surplus_j if seller_id == agent_b_id else surplus_i,
                "total_surplus": surplus_i + surplus_j,
            }
        )

