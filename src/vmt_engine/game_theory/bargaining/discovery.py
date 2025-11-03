"""
Trade Discovery Algorithms

Implements various algorithms for discovering mutually beneficial trades.
Each algorithm implements the TradeDiscoverer interface and can be injected
into bargaining protocols.

Version: 2025.11.03 (Decoupling Refactor)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from decimal import Decimal
from ...systems.trade_evaluation import TradeDiscoverer, TradeTuple
from ...systems.matching import generate_price_candidates
from ...core.decimal_config import quantize_quantity

if TYPE_CHECKING:
    from ...core import Agent


class CompensatingBlockDiscoverer(TradeDiscoverer):
    """
    Trade discovery using compensating block algorithm.
    
    This is the foundational VMT trade discovery algorithm. It searches
    over discrete quantities (1, 2, 3, ...) and price candidates to find
    the first mutually beneficial trade.
    
    Algorithm:
    1. Check both directions (i gives A, j gives A)
    2. For each direction with quote overlap:
       a. Try quantity dA = 1, 2, 3, ... up to max inventory
       b. Generate price candidates between ask and bid
       c. For each (dA, price) pair:
          - Calculate dB = price * dA
          - Check inventory feasibility
          - Evaluate utility improvement for both agents
          - Return first feasible trade found
    3. Return None if no feasible trade exists
    
    This implements the foundational VMT compensating block algorithm.
    
    Economic Properties:
    - First feasible trade (not optimizing)
    - Discrete quantity search (1, 2, 3, ...)
    - Price search between ask and bid quotes
    - Barter-only (A<->B exchange)
    """
    
    def discover_trade(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        params: dict[str, Any] | None = None,
        epsilon: float = 1e-9
    ) -> TradeTuple | None:
        """
        Discover first feasible trade using compensating block algorithm.
        
        Searches both directions (i gives A, j gives A) and returns the
        first mutually beneficial trade found.
        
        Args:
            agent_i: First agent
            agent_j: Second agent
            params: Optional simulation parameters (currently unused)
            epsilon: Threshold for utility improvement
            
        Returns:
            TradeTuple if feasible trade exists, None otherwise
        """
        # Verify agents have utility functions
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
        Search for feasible trade in one direction.
        
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

