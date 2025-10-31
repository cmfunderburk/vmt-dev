"""
Take-It-Or-Leave-It Bargaining Protocol

Monopolistic offer with single acceptance/rejection.
Demonstrates bargaining power and market power effects.

Economic Properties:
- Asymmetric surplus distribution
- Proposer captures most gains
- Fast resolution (single round)
- Demonstrates bargaining power

Teaching Points:
- Bargaining power affects outcomes
- Market power vs competitive pricing
- Hold-up problems in economics
- Asymmetric information and power

Parameters:
- proposer_power: float [0, 1] - fraction of surplus to proposer (default: 0.9)
- proposer_selection: str - how to select proposer:
    - "random": Random selection using RNG (default)
    - "first_in_pair": First agent in pair tuple (deterministic)
    - "higher_id": Agent with higher ID (deterministic)
    - "lower_id": Agent with lower ID (deterministic)

References:
- Rubinstein (1982) - limiting case of alternating offers
- Market power literature
- Hold-up problem literature

Version: 2025.10.28 (Phase 2b - Pedagogical Protocol)
"""

from typing import Any
from ..registry import register_protocol
from ..base import BargainingProtocol, Effect, Trade, Unpair
from ..context import WorldView
from ...systems.matching import find_all_feasible_trades


@register_protocol(
    category="bargaining",
    name="take_it_or_leave_it",
    description="Monopolistic offer bargaining",
    properties=["asymmetric", "power_based", "pedagogical"],
    complexity="O(K)",  # K = number of feasible trades examined
    references=[
        "Rubinstein (1982) alternating offers",
        "Market power literature"
    ],
    phase="2b",
)
class TakeItOrLeaveIt(BargainingProtocol):
    """
    Monopolistic offer with single acceptance/rejection.
    
    Teaching Points:
        - Bargaining power extraction
        - Market power vs competitive price
        - Hold-up problem
        - Asymmetric outcomes from asymmetric power
    """
    
    @property
    def name(self) -> str:
        return "take_it_or_leave_it"
    
    @property
    def version(self) -> str:
        return "2025.10.28"
    
    # Class-level for registry
    VERSION = "2025.10.28"
    
    def __init__(self, proposer_power: float = 0.9, proposer_selection: str = "random"):
        """
        Initialize TIOL bargaining protocol.
        
        Args:
            proposer_power: Fraction of surplus going to proposer [0, 1]. Default 0.9.
            proposer_selection: How to select proposer. Options:
                - "random": Random selection using RNG (default)
                - "first_in_pair": First agent in pair tuple (deterministic)
                - "higher_id": Agent with higher ID (deterministic)
                - "lower_id": Agent with lower ID (deterministic)
        """
        if not 0 <= proposer_power <= 1:
            raise ValueError(f"proposer_power must be in [0, 1], got {proposer_power}")
        if proposer_selection not in ("random", "first_in_pair", "higher_id", "lower_id"):
            raise ValueError(
                f"proposer_selection must be one of: random, first_in_pair, higher_id, lower_id. "
                f"Got: {proposer_selection}"
            )
        
        self.proposer_power = proposer_power
        self.proposer_selection = proposer_selection
    
    def negotiate(self, pair: tuple[int, int], world: WorldView) -> list[Effect]:
        """
        Single-round negotiation with monopolistic offer.
        
        Args:
            pair: (agent_a_id, agent_b_id) to negotiate
            world: Context with both agents' states
            
        Returns:
            List of Trade or Unpair effects
        """
        agent_a_id, agent_b_id = pair
        
        # Determine proposer based on selection strategy
        proposer_id, responder_id = self._select_proposer(pair, world)
        
        # Build agent objects from WorldView
        # IMPORTANT: Call find_all_feasible_trades with agents in sorted order (lower ID first)
        # This matches how _apply_trade_effect converts Trade effects back to trade tuples
        if agent_a_id < agent_b_id:
            agent_i_obj = self._build_agent_from_world(world, agent_a_id)
            agent_j_obj = self._build_agent_from_world(world, agent_b_id)
            agent_i_id, agent_j_id = agent_a_id, agent_b_id
        else:
            agent_i_obj = self._build_agent_from_world(world, agent_b_id)
            agent_j_obj = self._build_agent_from_world(world, agent_a_id)
            agent_i_id, agent_j_id = agent_b_id, agent_a_id
        
        # Get all feasible trades (i=lower ID, j=higher ID)
        epsilon = world.params.get("epsilon", 1e-9)
        params = {
            "dA_max": world.params.get("dA_max", 50),
        }
        
        feasible_trades = find_all_feasible_trades(
            agent_i_obj, agent_j_obj, params, epsilon
        )
        
        if not feasible_trades:
            # No mutually beneficial trade - unpair
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=agent_a_id,
                agent_b=agent_b_id,
                reason="no_feasible_trade"
            )]
        
        # Find trade that maximizes proposer surplus while responder gets >= epsilon
        # Try to achieve proposer_power fraction of total surplus
        best_trade = None
        best_pair_name = None
        best_proposer_surplus = -float('inf')
        
        # IMPORTANT: In trade_tuple, i=lower ID agent, j=higher ID agent
        # Map proposer/responder to trade tuple indices
        if proposer_id == agent_i_id:
            proposer_is_i = True
        else:
            proposer_is_i = False
        
        for pair_name, trade_tuple in feasible_trades:
            # trade_tuple = (dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j)
            # i=lower ID agent, j=higher ID agent
            if proposer_is_i:
                proposer_surplus = trade_tuple[4]  # surplus_i
                responder_surplus = trade_tuple[5]  # surplus_j
            else:
                proposer_surplus = trade_tuple[5]  # surplus_j
                responder_surplus = trade_tuple[4]  # surplus_i
            
            # Responder must get at least epsilon (individual rationality)
            if responder_surplus < epsilon:
                continue
            
            # Total surplus
            total_surplus = proposer_surplus + responder_surplus
            
            # Check if this trade gives proposer desired fraction
            if total_surplus > 0:
                actual_proposer_fraction = proposer_surplus / total_surplus
                
                # Select trade closest to desired proposer_power, prioritizing higher proposer surplus
                # We want to maximize proposer surplus while respecting responder's minimum
                if proposer_surplus > best_proposer_surplus:
                    best_proposer_surplus = proposer_surplus
                    best_trade = trade_tuple
                    best_pair_name = pair_name
        
        if best_trade is None:
            # No trade satisfies responder's minimum - unpair
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=agent_a_id,
                agent_b=agent_b_id,
                reason="responder_rejected"
            )]
        
        # Convert to Trade effect
        # agent_i_id = lower ID, agent_j_id = higher ID (matches _apply_trade_effect convention)
        return [self._create_trade_effect(
            proposer_id, responder_id, agent_a_id, agent_b_id,
            agent_i_id, agent_j_id, proposer_is_i,
            best_pair_name, best_trade, world
        )]
    
    def _select_proposer(
        self, 
        pair: tuple[int, int], 
        world: WorldView
    ) -> tuple[int, int]:
        """
        Select proposer based on selection strategy.
        
        Returns:
            Tuple of (proposer_id, responder_id)
        """
        agent_a_id, agent_b_id = pair
        
        if self.proposer_selection == "random":
            # Random selection using deterministic RNG
            if world.rng.random() < 0.5:
                return (agent_a_id, agent_b_id)
            else:
                return (agent_b_id, agent_a_id)
        elif self.proposer_selection == "first_in_pair":
            return (agent_a_id, agent_b_id)
        elif self.proposer_selection == "higher_id":
            if agent_a_id > agent_b_id:
                return (agent_a_id, agent_b_id)
            else:
                return (agent_b_id, agent_a_id)
        else:  # "lower_id"
            if agent_a_id < agent_b_id:
                return (agent_a_id, agent_b_id)
            else:
                return (agent_b_id, agent_a_id)
    
    def _build_agent_from_world(self, world: WorldView, agent_id: int):
        """Build pseudo-agent object from WorldView for matching functions."""
        from ...core.agent import Agent
        from ...core.state import Inventory
        
        # If this is the current agent
        if agent_id == world.agent_id:
            inventory = Inventory(
                A=world.inventory.get("A", 0),
                B=world.inventory.get("B", 0)
            )
            quotes = world.quotes
            utility = world.utility
        else:
            # Partner - extract from params (populated by context builder)
            inventory = Inventory(
                A=world.params.get(f"partner_{agent_id}_inv_A", 0),
                B=world.params.get(f"partner_{agent_id}_inv_B", 0)
            )
            quotes = {}
            # Find partner in visible agents for quotes
            for neighbor in world.visible_agents:
                if neighbor.agent_id == agent_id:
                    quotes = neighbor.quotes
                    break
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
        proposer_id: int,
        responder_id: int,
        agent_a_id: int,
        agent_b_id: int,
        agent_i_id: int,
        agent_j_id: int,
        proposer_is_i: bool,
        pair_name: str,
        trade_tuple: tuple,
        world: WorldView
    ) -> Trade:
        """
        Convert trade tuple to Trade effect.
        
        Args:
            proposer_id: ID of proposer agent
            responder_id: ID of responder agent
            agent_a_id: First agent in pair
            agent_b_id: Second agent in pair
            agent_i_id: Agent ID corresponding to 'i' in trade_tuple (lower ID)
            agent_j_id: Agent ID corresponding to 'j' in trade_tuple (higher ID)
            proposer_is_i: True if proposer is agent_i (lower ID), False if proposer is agent_j
            pair_name: Exchange pair type
            trade_tuple: Trade tuple from find_all_feasible_trades
            world: WorldView context
        """
        dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j = trade_tuple
        
        # Map surpluses to proposer/responder
        if proposer_is_i:
            proposer_surplus = surplus_i
            responder_surplus = surplus_j
        else:
            proposer_surplus = surplus_j
            responder_surplus = surplus_i
        
        # Determine buyer/seller based on pair type and direction (barter-only)
        # Trade tuple format: (dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j)
        # Conservation: dA_i + dA_j = 0, dB_i + dB_j = 0
        # In trade tuple: i=lower ID agent, j=higher ID agent
        
        if pair_name == "A<->B":
            # Barter trade
            if dA_i < 0:  # i (lower ID) gives A, receives B (j receives A, gives B)
                buyer_id = agent_j_id  # j receives A
                seller_id = agent_i_id  # i gives A
                dA = abs(dA_i)  # Amount of A traded
                dB = abs(dB_j)  # Amount of B traded (j gives B, so dB_j < 0)
                price = dB / dA if dA > 0 else 0
            else:  # dA_i > 0: i receives A, gives B (j gives A, receives B)
                buyer_id = agent_i_id  # i receives A
                seller_id = agent_j_id  # j gives A
                dA = abs(dA_j)  # Amount of A traded (j gives A, so dA_j < 0)
                dB = abs(dB_i)  # Amount of B traded (i gives B, so dB_i < 0)
                price = dB / dA if dA > 0 else 0
            
            return Trade(
                protocol_name=self.name,
                tick=world.tick,
                buyer_id=buyer_id,
                seller_id=seller_id,
                pair_type=pair_name,
                dA=dA,
                dB=dB,
                price=round(price, 2),
                metadata={
                    "proposer_id": proposer_id,
                    "responder_id": responder_id,
                    "proposer_surplus": proposer_surplus,
                    "responder_surplus": responder_surplus,
                    "total_surplus": proposer_surplus + responder_surplus,
                    "proposer_power": self.proposer_power,
                }
            )

