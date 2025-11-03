"""
Compensating Block Bargaining Protocol

Implements the foundational VMT compensating block algorithm for bilateral
barter trade negotiation. This protocol searches for the first mutually
beneficial trade using discrete quantity steps and price candidate generation.

This is the default bargaining protocol in VMT.

Version: 2025.11.03 (Restructured)
"""

from typing import Optional
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from .discovery import CompensatingBlockDiscoverer
from ...systems.trade_evaluation import TradeDiscoverer, TradeTuple
from ...protocols.base import Effect, Trade, Unpair
from ...protocols.context import WorldView


@register_protocol(
    category="bargaining",
    name="compensating_block",
    description="First feasible trade using compensating block algorithm (default)",
    properties=["deterministic", "first_feasible"],
    complexity="O(K·P)",  # K = quantities tried, P = prices per quantity
    references=["VMT foundational algorithm"],
    phase="4",
)
class CompensatingBlockBargaining(BargainingProtocol):
    """
    Compensating block bargaining - the foundational VMT algorithm.
    
    Searches over discrete quantities (1, 2, 3, ...) and price candidates
    to find the first mutually beneficial barter trade. Returns Trade effect
    if successful, Unpair effect if no feasible trade exists.
    
    This is the default bargaining protocol and implements the core VMT
    trade discovery logic.
    """
    
    def __init__(self, discoverer: TradeDiscoverer | None = None):
        """
        Initialize compensating block bargaining.
        
        Args:
            discoverer: Trade discovery algorithm (default: CompensatingBlockDiscoverer)
        """
        self.discoverer = discoverer or CompensatingBlockDiscoverer()
    
    @property
    def name(self) -> str:
        return "compensating_block"
    
    @property
    def version(self) -> str:
        return "2025.11.03"
    
    VERSION = "2025.11.03"
    
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
        epsilon = world.params.get("epsilon", 1e-9)
        
        # Build agent objects from WorldView
        agent_i = self._build_agent_from_world(world, agent_a_id)
        agent_j = self._build_agent_from_world(world, agent_b_id)
        
        # Discover trade using injected discovery algorithm
        trade_tuple = self.discoverer.discover_trade(agent_i, agent_j, world.params, epsilon)
        
        if trade_tuple is None:
            # No mutually beneficial trade - unpair
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=agent_a_id,
                agent_b=agent_b_id,
                reason="trade_failed"
            )]
        
        # Convert TradeTuple to Trade effect
        return [self._create_trade_effect(agent_a_id, agent_b_id, trade_tuple, world)]
    
    def _build_agent_from_world(self, world: WorldView, agent_id: int):
        """
        Build a pseudo-Agent object from WorldView for discovery algorithms.
        
        This is a temporary adapter. Future refactoring may pass protocol
        contexts directly to discovery algorithms.
        """
        from ...core.agent import Agent
        from ...core.state import Inventory
        
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
                # Partner not visible - create minimal agent defensively
                inventory = Inventory(A=0, B=0)
                quotes = {}
                utility = None
            else:
                # Extract from AgentView
                inventory = Inventory(
                    A=world.params.get(f"partner_{agent_id}_inv_A", 0),
                    B=world.params.get(f"partner_{agent_id}_inv_B", 0)
                )
                quotes = partner_view.quotes
                utility = world.params.get(f"partner_{agent_id}_utility", None)
        
        # Create minimal agent
        agent = Agent(
            id=agent_id,
            pos=(0, 0),  # Not used in discovery
            inventory=inventory,
            utility=utility,
            quotes=quotes,
        )
        
        return agent
    
    def _create_trade_effect(
        self,
        agent_a_id: int,
        agent_b_id: int,
        trade_tuple: TradeTuple,
        world: WorldView
    ) -> Trade:
        """
        Convert TradeTuple to Trade effect.
        
        Args:
            agent_a_id: First agent ID
            agent_b_id: Second agent ID
            trade_tuple: Trade specification from discovery
            world: Context for tick
            
        Returns:
            Trade effect
        """
        # Determine buyer/seller from trade direction
        if trade_tuple.dA_i > 0:  # agent_a receives A (buyer)
            buyer_id, seller_id = agent_a_id, agent_b_id
            dA = trade_tuple.dA_i
            dB = -trade_tuple.dB_i
            surplus_buyer = trade_tuple.surplus_i
            surplus_seller = trade_tuple.surplus_j
        else:  # agent_b receives A (buyer)
            buyer_id, seller_id = agent_b_id, agent_a_id
            dA = -trade_tuple.dA_i
            dB = -trade_tuple.dB_i
            surplus_buyer = trade_tuple.surplus_j
            surplus_seller = trade_tuple.surplus_i
        
        return Trade(
            protocol_name=self.name,
            tick=world.tick,
            buyer_id=buyer_id,
            seller_id=seller_id,
            pair_type="A<->B",
            dA=abs(dA),
            dB=abs(dB),
            price=float(trade_tuple.price),
            metadata={
                "surplus_buyer": surplus_buyer,
                "surplus_seller": surplus_seller,
                "total_surplus": trade_tuple.surplus_i + trade_tuple.surplus_j,
            }
        )

