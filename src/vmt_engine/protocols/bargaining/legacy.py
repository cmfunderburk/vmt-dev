"""
Legacy Bargaining Protocol

Implements the original VMT compensating block bargaining using generic
matching primitives for money-aware trade negotiation.

This protocol is bit-compatible with the pre-protocol TradeSystem implementation.

Version: 2025.10.26 (Phase 1 - Legacy Adapter)
"""

from typing import Optional
from ..base import BargainingProtocol, Effect, Trade, Unpair
from ..context import WorldView
from ...systems.matching import (
    find_all_feasible_trades,
    find_best_trade,
)


class LegacyBargainingProtocol(BargainingProtocol):
    """
    Legacy compensating block bargaining.
    
    Uses generic matching primitives to find mutually beneficial trades:
    - For mixed regimes: Evaluates all feasible pair types, ranks with money-first tie-breaking
    - For barter/money-only: Finds first feasible trade
    
    Returns Trade effect if successful, Unpair effect if negotiation fails.
    """
    
    @property
    def name(self) -> str:
        return "legacy_compensating_block"
    
    @property
    def version(self) -> str:
        return "2025.10.26"
    
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
        
        exchange_regime = world.exchange_regime
        epsilon = world.params.get("epsilon", 1e-9)
        
        # Build pseudo-agent objects from WorldView for matching functions
        # This is a temporary adapter - proper refactoring in Phase 2
        agent_i = self._build_agent_from_world(world, agent_a_id)
        agent_j = self._build_agent_from_world(world, agent_b_id)
        
        # Mixed regime: find all feasible trades and rank
        if exchange_regime in ["mixed", "mixed_liquidity_gated"]:
            feasible_trades = find_all_feasible_trades(
                agent_i, agent_j, exchange_regime, world.params, epsilon
            )
            
            if not feasible_trades:
                # No mutually beneficial trade - unpair
                return [Unpair(
                    protocol_name=self.name,
                    tick=world.tick,
                    agent_a=agent_a_id,
                    agent_b=agent_b_id,
                    reason="trade_failed"
                )]
            
            # Rank trades with money-first tie-breaking
            best_pair_name, best_trade = self._rank_and_select_best(feasible_trades)
            
            # Convert to Trade effect
            return [self._create_trade_effect(
                agent_a_id, agent_b_id, best_pair_name, best_trade, world
            )]
        
        else:
            # Barter-only or money-only: find first feasible trade
            result = find_best_trade(
                agent_i, agent_j, exchange_regime, world.params, epsilon
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
                M=world.inventory.get("M", 0)
            )
            quotes = world.quotes
            utility = world.utility
            lambda_money = world.lambda_money
            money_utility_form = world.params.get("money_utility_form", "linear")
            M_0 = world.inventory.get("M", 0)  # Use current M as M_0
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
                inventory = Inventory(A=0, B=0, M=0)
                quotes = {}
                utility = None
                lambda_money = 1.0
                money_utility_form = "linear"
                M_0 = 0
            else:
                # Extract from AgentView
                # Note: AgentView doesn't have inventory, only quotes
                # We'll need to get this from params or extend AgentView
                inventory = Inventory(
                    A=world.params.get(f"partner_{agent_id}_inv_A", 0),
                    B=world.params.get(f"partner_{agent_id}_inv_B", 0),
                    M=world.params.get(f"partner_{agent_id}_inv_M", 0)
                )
                quotes = partner_view.quotes
                utility = world.params.get(f"partner_{agent_id}_utility", None)
                lambda_money = world.params.get(f"partner_{agent_id}_lambda", 1.0)
                money_utility_form = world.params.get(f"partner_{agent_id}_money_utility_form", "linear")
                M_0 = world.params.get(f"partner_{agent_id}_M_0", 0)
        
        # Create minimal agent
        agent = Agent(
            id=agent_id,
            pos=(0, 0),  # Not used in matching
            inventory=inventory,
            utility=utility,
            quotes=quotes,
        )
        agent.lambda_money = lambda_money
        agent.money_utility_form = money_utility_form
        agent.M_0 = M_0
        
        return agent
    
    def _rank_and_select_best(
        self, feasible_trades: list[tuple[str, tuple]]
    ) -> tuple[str, tuple]:
        """
        Rank feasible trades using money-first tie-breaking.
        
        Ranking criteria:
        1. Total surplus (higher is better)
        2. Money-first priority: A↔M > B↔M > A↔B on ties
        3. Lexical by pair name (deterministic)
        
        Returns:
            Best (pair_name, trade) tuple
        """
        if not feasible_trades:
            raise ValueError("Cannot rank empty list of trades")
        
        # Define money-first priority
        priority_map = {
            "A<->M": 0,
            "B<->M": 1,
            "A<->B": 2,
        }
        
        def sort_key(item):
            pair_name, trade = item
            # Extract total surplus
            dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade
            total_surplus = surplus_i + surplus_j
            
            priority = priority_map.get(pair_name, 999)
            
            # Sort by: (-total_surplus, priority, pair_name)
            return (-total_surplus, priority, pair_name)
        
        sorted_trades = sorted(feasible_trades, key=sort_key)
        return sorted_trades[0]
    
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
            pair_name: Pair type ("A<->B", "A<->M", "B<->M")
            trade: Tuple (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
            world: Context for tick
        
        Returns:
            Trade effect
        """
        dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade
        
        # Determine buyer/seller and trade amounts
        # Convention: buyer receives the good, seller receives payment
        
        if pair_name == "A<->B":
            # Barter: whoever receives A is buyer
            if dA_i > 0:  # agent_a receives A (buyer)
                buyer_id, seller_id = agent_a_id, agent_b_id
                dA, dB, dM = dA_i, dB_i, 0
                price = -dB_i / dA_i if dA_i != 0 else 0.0  # B per unit A
            else:  # agent_b receives A (buyer)
                buyer_id, seller_id = agent_b_id, agent_a_id
                dA, dB, dM = -dA_i, -dB_i, 0
                price = dB_i / (-dA_i) if dA_i != 0 else 0.0
        
        elif pair_name == "A<->M":
            # Monetary: whoever receives A is buyer
            if dA_i > 0:  # agent_a receives A (buyer)
                buyer_id, seller_id = agent_a_id, agent_b_id
                dA, dB, dM = dA_i, 0, dM_i
                price = -dM_i / dA_i if dA_i != 0 else 0.0  # M per unit A
            else:  # agent_b receives A (buyer)
                buyer_id, seller_id = agent_b_id, agent_a_id
                dA, dB, dM = -dA_i, 0, -dM_i
                price = dM_i / (-dA_i) if dA_i != 0 else 0.0
        
        else:  # "B<->M"
            # Monetary: whoever receives B is buyer
            if dB_i > 0:  # agent_a receives B (buyer)
                buyer_id, seller_id = agent_a_id, agent_b_id
                dA, dB, dM = 0, dB_i, dM_i
                price = -dM_i / dB_i if dB_i != 0 else 0.0  # M per unit B
            else:  # agent_b receives B (buyer)
                buyer_id, seller_id = agent_b_id, agent_a_id
                dA, dB, dM = 0, -dB_i, -dM_i
                price = dM_i / (-dB_i) if dB_i != 0 else 0.0
        
        # Create Trade effect
        return Trade(
            protocol_name=self.name,
            tick=world.tick,
            buyer_id=buyer_id,
            seller_id=seller_id,
            pair_type=pair_name,
            dA=abs(dA),
            dB=abs(dB),
            dM=abs(dM),
            price=abs(price),
            metadata={
                "surplus_buyer": surplus_i if buyer_id == agent_a_id else surplus_j,
                "surplus_seller": surplus_j if seller_id == agent_b_id else surplus_i,
                "total_surplus": surplus_i + surplus_j,
            }
        )

