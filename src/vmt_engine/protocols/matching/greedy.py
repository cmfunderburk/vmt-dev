"""
Greedy Surplus Matching Protocol

Pure welfare maximization without mutual consent requirement.
Demonstrates central planner perspective vs decentralized markets.

Economic Properties:
- Maximizes total surplus across all pairs
- May violate individual rationality (negative surplus for some)
- Not strategy-proof (agents may want to misreport preferences)
- Useful for efficiency benchmarks

Algorithm:
1. Enumerate all possible agent pairs
2. Calculate total surplus for each potential pair
3. Apply distance discounting (β^distance)
4. Sort pairs by total discounted surplus (descending)
5. Greedily assign pairs (no double-booking)
6. Stop when no more pairs possible

References:
- First-best welfare economics
- Market vs planner comparisons
- Mechanism design literature

Version: 2025.10.28 (Phase 2b - Pedagogical Protocol)
"""

from typing import Any
from ..registry import register_protocol
from ..base import MatchingProtocol, Effect, Pair
from ..context import ProtocolContext
from ...systems.matching import find_all_feasible_trades
from ...core.agent import Agent


@register_protocol(
    category="matching",
    name="greedy_surplus",
    description="Welfare maximization without consent requirement",
    properties=["welfare_maximizing", "central_planner", "pedagogical"],
    complexity="O(n²)",
    references=[
        "First-best welfare economics",
        "Market vs planner comparisons"
    ],
    phase="2b",
)
class GreedySurplusMatching(MatchingProtocol):
    """
    Pure welfare maximization without mutual consent requirement.
    
    Teaching Points:
        - Demonstrates central planner perspective
        - Shows efficiency-fairness trade-off
        - Illustrates market failure (may violate IR)
    
    Economic Properties:
        - Maximizes total surplus
        - May violate individual rationality
        - Not strategy-proof
        - Useful for efficiency benchmarks
    """
    
    @property
    def name(self) -> str:
        return "greedy_surplus"
    
    @property
    def version(self) -> str:
        return "2025.10.28"
    
    # Class-level for registry
    VERSION = "2025.10.28"
    
    def find_matches(
        self,
        preferences: dict[int, list[tuple[int | tuple[int, int], float, dict]]],
        world: ProtocolContext
    ) -> list[Effect]:
        """
        Greedily match agents to maximize total discounted surplus.
        
        Args:
            preferences: Agent preferences from search protocols
            world: Protocol execution context
            
        Returns:
            List of Pair effects for optimal welfare assignment
        """
        effects = []
        
        # Track which agents are already paired
        paired_this_pass = set()
        
        # Get agents wanting to trade (have trade preferences)
        trade_agents = set()
        for agent_id, agent_prefs in preferences.items():
            # Filter to trade preferences (agent IDs, not positions)
            trade_prefs = [p for p in agent_prefs if isinstance(p[0], int)]
            if trade_prefs:
                trade_agents.add(agent_id)
        
        # Skip already-paired agents
        available_agents = [
            aid for aid in trade_agents 
            if aid not in world.current_pairings and aid not in paired_this_pass
        ]
        
        if len(available_agents) < 2:
            return []  # Need at least 2 agents to pair
        
        # Enumerate all potential pairs and calculate surplus
        potential_pairings = []
        beta = world.params.get("beta", 0.95)
        exchange_regime = world.params.get("exchange_regime", "barter_only")
        epsilon = world.params.get("epsilon", 1e-9)
        
        # Sort agents for deterministic iteration
        sorted_agents = sorted(available_agents)
        
        for i, agent_a_id in enumerate(sorted_agents):
            for agent_b_id in sorted_agents[i+1:]:
                # Skip if either already paired
                if agent_a_id in paired_this_pass or agent_b_id in paired_this_pass:
                    continue
                
                # Calculate surplus for this pair
                total_surplus, discounted_surplus, distance = self._calculate_pair_surplus(
                    agent_a_id, agent_b_id, world, exchange_regime, epsilon, beta
                )
                
                if total_surplus > 0:
                    # Store with negative discounted surplus for descending sort
                    potential_pairings.append((
                        -discounted_surplus,  # Negative for descending sort
                        total_surplus,
                        agent_a_id,
                        agent_b_id,
                        distance
                    ))
        
        # Sort by discounted surplus (descending)
        potential_pairings.sort(key=lambda x: (x[0], x[2], x[3]))  # Sort by discounted surplus, then IDs
        
        # Greedily assign pairs
        for neg_discounted, total_surplus, agent_a_id, agent_b_id, distance in potential_pairings:
            # Check if both are still available
            if agent_a_id in paired_this_pass or agent_b_id in paired_this_pass:
                continue
            
            # Create pair
            effects.append(Pair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=agent_a_id,
                agent_b=agent_b_id,
                reason="greedy_welfare_maximization"
            ))
            
            # Mark as paired
            paired_this_pass.add(agent_a_id)
            paired_this_pass.add(agent_b_id)
        
        return effects
    
    def _calculate_pair_surplus(
        self,
        agent_a_id: int,
        agent_b_id: int,
        world: ProtocolContext,
        exchange_regime: str,
        epsilon: float,
        beta: float
    ) -> tuple[float, float, int]:
        """
        Calculate total surplus for a potential pair.
        
        Returns:
            Tuple of (total_surplus, discounted_surplus, distance)
        """
        # Build agent objects from ProtocolContext
        agent_a = self._build_agent_from_context(world, agent_a_id)
        agent_b = self._build_agent_from_context(world, agent_b_id)
        
        # Find all feasible trades
        params = {
            "dA_max": world.params.get("dA_max", 50),
            "money_scale": world.params.get("money_scale", 1),
        }
        
        feasible_trades = find_all_feasible_trades(
            agent_a, agent_b, exchange_regime, params, epsilon
        )
        
        if not feasible_trades:
            return (0.0, 0.0, 0)
        
        # Find trade with maximum total surplus
        best_total_surplus = 0.0
        for pair_name, trade_tuple in feasible_trades:
            # trade_tuple = (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
            surplus_a = trade_tuple[6]
            surplus_b = trade_tuple[7]
            total_surplus = surplus_a + surplus_b
            
            if total_surplus > best_total_surplus:
                best_total_surplus = total_surplus
        
        # Calculate distance
        view_a = world.all_agent_views[agent_a_id]
        view_b = world.all_agent_views[agent_b_id]
        distance = abs(view_a.pos[0] - view_b.pos[0]) + abs(view_a.pos[1] - view_b.pos[1])
        
        # Apply distance discounting
        discounted_surplus = best_total_surplus * (beta ** distance)
        
        return (best_total_surplus, discounted_surplus, distance)
    
    def _build_agent_from_context(self, world: ProtocolContext, agent_id: int) -> Agent:
        """Build pseudo-agent object from ProtocolContext for matching functions."""
        from ...core.state import Inventory
        
        view = world.all_agent_views[agent_id]
        
        # Extract full agent state from params (added by build_protocol_context)
        inventory = Inventory(
            A=world.params.get(f"agent_{agent_id}_inv_A", 0),
            B=world.params.get(f"agent_{agent_id}_inv_B", 0),
            M=world.params.get(f"agent_{agent_id}_inv_M", 0)
        )
        utility = world.params.get(f"agent_{agent_id}_utility")
        lambda_money = world.params.get(f"agent_{agent_id}_lambda", 1.0)
        money_utility_form = world.params.get(f"agent_{agent_id}_money_utility_form", "linear")
        M_0 = world.params.get(f"agent_{agent_id}_M_0", 0)
        
        # Create minimal agent with required state
        agent = Agent(
            id=agent_id,
            pos=view.pos,
            inventory=inventory,
            utility=utility,
            quotes=view.quotes.copy(),
        )
        agent.lambda_money = lambda_money
        agent.money_utility_form = money_utility_form
        agent.M_0 = M_0
        
        return agent

