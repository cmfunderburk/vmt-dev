"""
Compensating Block Bargaining Protocol

Implements the foundational VMT compensating block algorithm for bilateral
barter trade negotiation. This protocol searches for the first mutually
beneficial trade using discrete quantity steps and price candidate generation.

This is the default bargaining protocol in VMT.

Version: 2025.11.04 (Architecture Correction - Inlined Search)
"""

from typing import TYPE_CHECKING
from decimal import Decimal
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from ...systems.trade_evaluation import TradeTuple, trade_tuple_to_effect
from ...systems.matching import generate_price_candidates
from ...core.decimal_config import quantize_quantity
from ...protocols.base import Effect, Unpair
from ...protocols.context import WorldView

if TYPE_CHECKING:
    from ...core import Agent


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
    trade discovery logic. Search algorithm is self-contained within this protocol.
    """
    
    @property
    def name(self) -> str:
        return "compensating_block"
    
    @property
    def version(self) -> str:
        return "2025.11.04"
    
    VERSION = "2025.11.04"
    
    def negotiate(
        self,
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: WorldView
    ) -> list[Effect]:
        """
        Negotiate trade between paired agents using compensating block search.
        
        Finds first mutually beneficial trade using discrete quantity search
        over candidate prices.
        
        Args:
            pair: (agent_a_id, agent_b_id) tuple
            agents: (agent_a, agent_b) direct access
            world: Context for tick, params, rng
        
        Returns:
            [Trade(...)] if successful
            [Unpair(...)] if no mutually beneficial trade found
        """
        agent_a, agent_b = agents
        epsilon = world.params.get("epsilon", 1e-9)
        
        # Search for first feasible trade
        trade_tuple = self._search_first_feasible(agent_a, agent_b, epsilon)
        
        if trade_tuple is None:
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=pair[0],
                agent_b=pair[1],
                reason="no_feasible_trade"
            )]
        
        # Convert to Trade effect using shared utility
        trade_effect = trade_tuple_to_effect(pair, trade_tuple, world, self.name)
        return [trade_effect]
    
    def _search_first_feasible(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        epsilon: float
    ) -> TradeTuple | None:
        """
        Search for first mutually beneficial trade.
        
        Searches discrete quantities in both directions,
        returns immediately when feasible trade is found.
        
        Returns:
            TradeTuple if feasible trade exists, None otherwise
        """
        if not agent_i.utility or not agent_j.utility:
            return None
        
        # Current utilities
        u_i_0 = agent_i.utility.u(agent_i.inventory.A, agent_i.inventory.B)
        u_j_0 = agent_j.utility.u(agent_j.inventory.A, agent_j.inventory.B)
        
        # Try Direction 1: agent_i gives A, receives B
        result = self._search_direction(
            agent_i, agent_j,
            giver=agent_i, receiver=agent_j,
            u_i_0=u_i_0, u_j_0=u_j_0,
            epsilon=epsilon
        )
        if result:
            return result
        
        # Try Direction 2: agent_j gives A, agent_i receives A
        result = self._search_direction(
            agent_i, agent_j,
            giver=agent_j, receiver=agent_i,
            u_i_0=u_i_0, u_j_0=u_j_0,
            epsilon=epsilon
        )
        return result
    
    def _search_direction(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        giver: "Agent",
        receiver: "Agent",
        u_i_0: float,
        u_j_0: float,
        epsilon: float
    ) -> TradeTuple | None:
        """
        Search one direction for feasible trade.
        
        The giver sells good A, the receiver buys good A (pays with B).
        Searches over discrete quantities and price candidates.
        
        Args:
            agent_i: First agent (for determining dA_i, dB_i in result)
            agent_j: Second agent (for determining dA_j, dB_j in result)
            giver: Agent giving A (selling)
            receiver: Agent receiving A (buying, paying B)
            u_i_0, u_j_0: Initial utilities
            epsilon: Utility improvement threshold
            
        Returns:
            TradeTuple if feasible trade found, None otherwise
        """
        # Get quotes for this direction
        ask_giver = giver.quotes.get('ask_A_in_B', float('inf'))
        bid_receiver = receiver.quotes.get('bid_A_in_B', 0.0)
        
        # Check if there's quote overlap
        if ask_giver > bid_receiver:
            return None  # No quote overlap, no trade possible
        
        # Maximum quantity giver can sell
        max_dA = int(giver.inventory.A)
        if max_dA <= 0:
            return None
        
        # Discrete quantity search: 1, 2, 3, ... up to max_dA
        for dA_int in range(1, max_dA + 1):
            dA = quantize_quantity(Decimal(str(dA_int)))
            
            # Generate price candidates between ask and bid
            price_candidates = generate_price_candidates(ask_giver, bid_receiver, dA_int)
            
            for price in price_candidates:
                # Calculate dB = price * dA (amount of B to exchange)
                dB_raw = Decimal(str(price)) * dA
                dB = quantize_quantity(dB_raw)
                
                if dB <= 0:
                    continue
                
                # Check inventory constraints
                if giver.inventory.A < dA or receiver.inventory.B < dB:
                    continue
                
                # Calculate utilities with proposed trade
                if giver.id == agent_i.id:
                    # agent_i gives A, receives B
                    u_i_new = agent_i.utility.u(agent_i.inventory.A - dA, agent_i.inventory.B + dB)
                    u_j_new = agent_j.utility.u(agent_j.inventory.A + dA, agent_j.inventory.B - dB)
                    dA_i, dB_i = -dA, dB
                    dA_j, dB_j = dA, -dB
                else:
                    # agent_j gives A, agent_i receives A
                    u_i_new = agent_i.utility.u(agent_i.inventory.A + dA, agent_i.inventory.B - dB)
                    u_j_new = agent_j.utility.u(agent_j.inventory.A - dA, agent_j.inventory.B + dB)
                    dA_i, dB_i = dA, -dB
                    dA_j, dB_j = -dA, dB
                
                surplus_i = u_i_new - u_i_0
                surplus_j = u_j_new - u_j_0
                
                # Check mutual benefit (strict improvement for both)
                if surplus_i > epsilon and surplus_j > epsilon:
                    # Found feasible trade - return immediately
                    return TradeTuple(
                        dA_i=dA_i,
                        dB_i=dB_i,
                        dA_j=dA_j,
                        dB_j=dB_j,
                        surplus_i=surplus_i,
                        surplus_j=surplus_j,
                        price=price,
                        pair_name="A<->B"
                    )
        
        # No feasible trade found in this direction
        return None

