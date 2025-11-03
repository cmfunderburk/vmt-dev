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

from typing import Any, TYPE_CHECKING
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from ...protocols.base import Effect, Trade, Unpair
from ...protocols.context import WorldView
from .discovery import CompensatingBlockDiscoverer
from ...systems.trade_evaluation import TradeDiscoverer

if TYPE_CHECKING:
    from ...core import Agent


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
    
    def __init__(
        self,
        discoverer: TradeDiscoverer | None = None,
        proposer_power: float = 0.9,
        proposer_selection: str = "random"
    ):
        """
        Initialize TIOL bargaining protocol.
        
        Args:
            discoverer: Trade discovery algorithm (default: CompensatingBlockDiscoverer)
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
        
        self.discoverer = discoverer or CompensatingBlockDiscoverer()
        self.proposer_power = proposer_power
        self.proposer_selection = proposer_selection
    
    def negotiate(
        self,
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: WorldView
    ) -> list[Effect]:
        """
        Single-round negotiation with monopolistic offer.
        
        Args:
            pair: (agent_a_id, agent_b_id) to negotiate
            agents: (agent_a, agent_b) - direct access to agent states
            world: Context (tick, params, rng)
            
        Returns:
            List of Trade or Unpair effects
        """
        agent_a, agent_b = agents
        agent_a_id, agent_b_id = pair
        
        # Determine proposer based on selection strategy
        proposer_id, responder_id = self._select_proposer(pair, world)
        
        # Sort agents by ID for consistent trade tuple format
        # IMPORTANT: Call discoverer with agents in sorted order (lower ID first)
        if agent_a_id < agent_b_id:
            agent_i_obj, agent_j_obj = agent_a, agent_b
            agent_i_id, agent_j_id = agent_a_id, agent_b_id
        else:
            agent_i_obj, agent_j_obj = agent_b, agent_a
            agent_i_id, agent_j_id = agent_b_id, agent_a_id
        
        # Discover trade using injected discovery algorithm
        epsilon = world.params.get("epsilon", 1e-9)
        
        trade_tuple_obj = self.discoverer.discover_trade(
            agent_i_obj, agent_j_obj, {}, epsilon
        )
        
        if trade_tuple_obj is None:
            # No mutually beneficial trade - unpair
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=pair[0],
                agent_b=pair[1],
                reason="no_feasible_trade"
            )]
        
        # Convert TradeTuple to the format expected by the rest of the method
        # trade_tuple = (dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j)
        trade_tuple = (
            trade_tuple_obj.dA_i,
            trade_tuple_obj.dB_i,
            trade_tuple_obj.dA_j,
            trade_tuple_obj.dB_j,
            trade_tuple_obj.surplus_i,
            trade_tuple_obj.surplus_j
        )
        pair_name = "A<->B"
        
        # Map proposer/responder to trade tuple indices
        if proposer_id == agent_i_id:
            proposer_is_i = True
        else:
            proposer_is_i = False
        
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
            # No trade satisfies responder's minimum - unpair
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=pair[0],
                agent_b=pair[1],
                reason="responder_rejected"
            )]
        
        # Convert to Trade effect
        # agent_i_id = lower ID, agent_j_id = higher ID (matches _apply_trade_effect convention)
        return [self._create_trade_effect(
            proposer_id, responder_id, agent_a_id, agent_b_id,
            agent_i_id, agent_j_id, proposer_is_i,
            pair_name, trade_tuple, world
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
                price=float(round(price, 2)),
                metadata={
                    "proposer_id": proposer_id,
                    "responder_id": responder_id,
                    "proposer_surplus": proposer_surplus,
                    "responder_surplus": responder_surplus,
                    "total_surplus": proposer_surplus + responder_surplus,
                    "proposer_power": self.proposer_power,
                }
            )

