"""
Split-the-Difference Bargaining Protocol

Equal surplus division for fairness baseline. Finds the trade that splits gains from
trade as equally as possible between both agents.

Economic Properties:
- Nash bargaining solution approximation (equal surplus split)
- Fairness baseline for comparison with other bargaining protocols
- Pareto efficient (both agents gain)

References:
- Nash (1950) "The Bargaining Problem"
- Equal surplus as fairness criterion in experimental economics

Version: 2025.10.28 (Phase 2a - Baseline Protocol)
"""

from typing import Optional
from ..registry import register_protocol
from ..base import BargainingProtocol, Effect, Trade, Unpair
from ..context import WorldView
from ...systems.matching import find_all_feasible_trades


@register_protocol(
    category="bargaining",
    name="split_difference",
    description="Equal surplus division (fairness baseline)",
    properties=["deterministic", "baseline"],
    complexity="O(K)",  # K = number of feasible trades examined
    references=[
        "Nash (1950) The Bargaining Problem",
        "Equal-surplus fairness criteria"
    ],
    phase="2a",
)
class SplitDifference(BargainingProtocol):
    """
    Equal surplus division for fairness baseline.
    
    Behavior:
        - Enumerate all feasible trades (all quantities, all pairs)
        - Calculate surplus for each agent for each trade
        - Select trade closest to 50/50 surplus split
        - If no mutually beneficial trade, unpair
    
    Economic Properties:
        - Approximates Nash bargaining solution
        - Fairness criterion: equal gains from trade
        - Pareto efficient: both agents strictly better off
    
    Note: This is computationally more expensive than legacy protocol since it
    evaluates ALL feasible trades, not just the first one found.
    """
    
    @property
    def name(self) -> str:
        return "split_difference"
    
    @property
    def version(self) -> str:
        return "2025.10.28"
    
    # Class-level for registry
    VERSION = "2025.10.28"
    
    def negotiate(self, pair: tuple[int, int], world: WorldView) -> list[Effect]:
        """
        Find trade that splits surplus equally.
        
        Args:
            pair: (agent_a_id, agent_b_id) tuple
            world: Context with both agents' states
        
        Returns:
            [Trade(...)] if mutually beneficial trade with equal split found
            [Unpair(...)] if no feasible trade exists
        """
        agent_a_id, agent_b_id = pair
        
        # Build pseudo-agent objects from WorldView
        agent_i = self._build_agent_from_world(world, agent_a_id)
        agent_j = self._build_agent_from_world(world, agent_b_id)
        
        # Get all feasible trades
        exchange_regime = world.exchange_regime
        epsilon = world.params.get("epsilon", 1e-9)
        
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
                reason="no_feasible_trade"
            )]
        
        # Find trade with most equal surplus split
        best_trade = None
        best_pair_name = None
        best_evenness = float('inf')
        
        for pair_name, trade_tuple in feasible_trades:
            # trade_tuple = (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
            surplus_i = trade_tuple[6]
            surplus_j = trade_tuple[7]
            
            # Both must have positive surplus (should always be true from find_all_feasible_trades)
            if surplus_i <= 0 or surplus_j <= 0:
                continue
            
            # Calculate how far from equal split
            total_surplus = surplus_i + surplus_j
            evenness = abs(surplus_i - total_surplus / 2)
            
            # Select trade closest to 50/50 split
            if evenness < best_evenness:
                best_evenness = evenness
                best_trade = trade_tuple
                best_pair_name = pair_name
        
        if best_trade is None:
            # No positive-surplus trade found (shouldn't happen but defensive)
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=agent_a_id,
                agent_b=agent_b_id,
                reason="no_positive_surplus"
            )]
        
        # Convert to Trade effect
        return [self._create_trade_effect(
            agent_a_id, agent_b_id, best_pair_name, best_trade, best_evenness, world
        )]
    
    def _build_agent_from_world(self, world: WorldView, agent_id: int):
        """Build pseudo-agent object from WorldView for matching functions."""
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
            M_0 = world.inventory.get("M", 0)
        else:
            # Partner - extract from params (populated by context builder)
            inventory = Inventory(
                A=world.params.get(f"partner_{agent_id}_inv_A", 0),
                B=world.params.get(f"partner_{agent_id}_inv_B", 0),
                M=world.params.get(f"partner_{agent_id}_inv_M", 0)
            )
            quotes = {}
            # Find partner in visible agents for quotes
            for neighbor in world.visible_agents:
                if neighbor.agent_id == agent_id:
                    quotes = neighbor.quotes
                    break
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
    
    def _create_trade_effect(
        self,
        agent_a_id: int,
        agent_b_id: int,
        pair_name: str,
        trade_tuple: tuple,
        evenness: float,
        world: WorldView
    ) -> Trade:
        """Convert trade tuple to Trade effect."""
        dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade_tuple
        
        # Determine buyer/seller based on who receives the good
        # For A<->B: buyer is who receives A (dA > 0)
        # For A<->M or B<->M: buyer is who receives the good (not money)
        
        if pair_name == "A<->B":
            # In barter, agent i gives dA_i and receives dB_i
            if dA_i < 0:  # i gives A, j gives B
                buyer_id = agent_b_id  # j receives A
                seller_id = agent_a_id  # i gives A
                dA = abs(dA_i)
                dB = abs(dB_i)
                price = dB / dA if dA > 0 else 0
            else:  # i gives B, j gives A
                buyer_id = agent_a_id  # i receives A
                seller_id = agent_b_id  # j gives A
                dA = abs(dA_j)
                dB = abs(dB_j)
                price = dB / dA if dA > 0 else 0
            
            return Trade(
                protocol_name=self.name,
                tick=world.tick,
                buyer_id=buyer_id,
                seller_id=seller_id,
                pair_type=pair_name,
                dA=dA,
                dB=dB,
                dM=0,
                price=round(price, 2),
                metadata={
                    "surplus_buyer": surplus_i if buyer_id == agent_a_id else surplus_j,
                    "surplus_seller": surplus_j if buyer_id == agent_a_id else surplus_i,
                    "total_surplus": surplus_i + surplus_j,
                    "split_evenness": evenness,
                }
            )
        
        elif pair_name == "A<->M":
            # Money trade for good A
            if dA_i < 0:  # i sells A for M
                buyer_id = agent_b_id
                seller_id = agent_a_id
                dA = abs(dA_i)
                dM = abs(dM_i)
            else:  # i buys A with M
                buyer_id = agent_a_id
                seller_id = agent_b_id
                dA = abs(dA_j)
                dM = abs(dM_j)
            
            price = dM / dA if dA > 0 else 0
            
            return Trade(
                protocol_name=self.name,
                tick=world.tick,
                buyer_id=buyer_id,
                seller_id=seller_id,
                pair_type=pair_name,
                dA=dA,
                dB=0,
                dM=dM,
                price=round(price, 2),
                metadata={
                    "surplus_buyer": surplus_i if buyer_id == agent_a_id else surplus_j,
                    "surplus_seller": surplus_j if buyer_id == agent_a_id else surplus_i,
                    "total_surplus": surplus_i + surplus_j,
                    "split_evenness": evenness,
                }
            )
        
        else:  # B<->M
            # Money trade for good B
            if dB_i < 0:  # i sells B for M
                buyer_id = agent_b_id
                seller_id = agent_a_id
                dB = abs(dB_i)
                dM = abs(dM_i)
            else:  # i buys B with M
                buyer_id = agent_a_id
                seller_id = agent_b_id
                dB = abs(dB_j)
                dM = abs(dM_j)
            
            price = dM / dB if dB > 0 else 0
            
            return Trade(
                protocol_name=self.name,
                tick=world.tick,
                buyer_id=buyer_id,
                seller_id=seller_id,
                pair_type=pair_name,
                dA=0,
                dB=dB,
                dM=dM,
                price=round(price, 2),
                metadata={
                    "surplus_buyer": surplus_i if buyer_id == agent_a_id else surplus_j,
                    "surplus_seller": surplus_j if buyer_id == agent_a_id else surplus_i,
                    "total_surplus": surplus_i + surplus_j,
                    "split_evenness": evenness,
                }
            )

