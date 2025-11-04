"""
Myopic Search Protocol

Constrained search strategy with limited vision radius.
Demonstrates information constraints and search costs.

Economic Properties:
- Limited information (vision radius = 1)
- Slower convergence to efficient outcomes
- Demonstrates value of information
- Shows network effects in markets

Teaching Points:
- Search costs reduce market efficiency
- Information is valuable in markets
- Market "thickness" depends on search range
- Network effects in economic interactions

References:
- Stigler (1961) "The Economics of Information"
- Search models in labor economics
- Network effects in markets

Version: 2025.10.28
"""

from typing import Any
from ...protocols.registry import register_protocol
from .base import SearchProtocol
from ...protocols.base import Effect, SetTarget, ClaimResource
from ...protocols.context import WorldView
from ...systems.matching import compute_surplus, estimate_barter_surplus


@register_protocol(
    category="search",
    name="myopic",
    description="Limited vision search (radius=1)",
    properties=["information_constrained", "pedagogical"],
    complexity="O(1)",
    references=[
        "Stigler (1961) Economics of Information",
        "Search models in labor economics"
    ],
)
class MyopicSearch(SearchProtocol):
    """
    Constrained search with limited vision radius.
    
    Teaching Points:
        - Information constraints reduce efficiency
        - Search costs matter in markets
        - Network effects and market thickness
        - Value of information in economic decisions
    """
    
    @property
    def name(self) -> str:
        return "myopic"
    
    @property
    def version(self) -> str:
        return "2025.10.28"
    
    # Class-level for registry
    VERSION = "2025.10.28"
    
    def build_preferences(self, world: WorldView) -> list[tuple[Any, float, dict]]:
        """
        Build preferences using limited vision (radius=1).
        
        Args:
            world: Agent's immutable perception snapshot
            
        Returns:
            List of (target, score, metadata) tuples
            Only includes targets within Manhattan distance 1
        """
        mode = world.mode
        vision_radius = 1  # Myopic: only distance 1
        
        # Build trade preferences if mode allows
        trade_prefs = []
        if mode in ("trade", "both"):
            trade_prefs = self._build_trade_preferences(world, vision_radius)
        
        # Build forage preferences if mode allows
        forage_prefs = []
        if mode in ("forage", "both"):
            forage_prefs = self._build_forage_preferences(world, vision_radius)
        
        # Combine for "both" mode, return single list for other modes
        if mode == "both":
            combined = []
            for agent_id, score, meta in trade_prefs:
                combined.append((agent_id, score, {**meta, "target_type": "trade"}))
            for pos, score, meta in forage_prefs:
                combined.append((pos, score, {**meta, "target_type": "forage"}))
            return combined
        elif mode == "trade":
            return trade_prefs
        else:  # "forage"
            return forage_prefs
    
    def select_target(self, world: WorldView) -> list[Effect]:
        """
        Select target from myopic preferences.
        
        Args:
            world: Agent's immutable perception snapshot
            
        Returns:
            List of SetTarget effects
        """
        # Skip if already paired (honor commitments)
        if world.paired_with_id is not None:
            return []
        
        mode = world.mode
        
        if mode == "trade":
            return self._select_trade_target(world)
        elif mode == "forage":
            return self._select_forage_target(world)
        else:  # "both"
            return self._select_mixed_target(world)
    
    def _build_trade_preferences(
        self, 
        world: WorldView, 
        vision_radius: int
    ) -> list[tuple[int, float, dict]]:
        """
        Build ranked list of trade partners within vision radius.
        
        Args:
            world: Agent's perception snapshot
            vision_radius: Maximum distance to consider (1 for myopic)
            
        Returns:
            List of (agent_id, discounted_surplus, metadata) sorted descending
        """
        beta = world.params.get("beta", 0.95)
        
        candidates = []
        
        for neighbor in world.visible_agents:
            # Check distance - myopic only considers distance 1
            distance = abs(world.pos[0] - neighbor.pos[0]) + abs(world.pos[1] - neighbor.pos[1])
            
            if distance > vision_radius:
                continue  # Skip agents beyond vision radius
            
            # Check trade cooldown
            if neighbor.agent_id in world.trade_cooldowns:
                if world.tick < world.trade_cooldowns[neighbor.agent_id]:
                    continue
            
            # Calculate surplus (barter-only)
            surplus = self._compute_barter_surplus_from_views(world, neighbor)
            pair_type = "A<->B"
            
            if surplus > 0:
                # Beta-discounted surplus
                discounted_surplus = surplus * (beta ** distance)
                
                candidates.append((neighbor.agent_id, surplus, discounted_surplus, distance, pair_type))
        
        # Sort by (-discounted_surplus, agent_id) for deterministic ranking
        candidates.sort(key=lambda x: (-x[2], x[0]))
        
        # Convert to preference format
        preferences = []
        for agent_id, surplus, discounted, distance, pair_type in candidates:
            meta = {
                "surplus": surplus,
                "discounted_surplus": discounted,
                "distance": distance,
                "pair_type": pair_type,
            }
            preferences.append((agent_id, discounted, meta))
        
        return preferences
    
    def _build_forage_preferences(
        self,
        world: WorldView,
        vision_radius: int
    ) -> list[tuple[tuple[int, int], float, dict]]:
        """
        Build ranked list of forage targets within vision radius.
        
        Args:
            world: Agent's perception snapshot
            vision_radius: Maximum distance to consider (1 for myopic)
            
        Returns:
            List of (position, discounted_utility_gain, metadata) sorted descending
        """
        beta = world.params.get("beta", 0.95)
        forage_rate = world.params.get("forage_rate", 1)
        
        # Filter to resources within vision radius
        available_resources = []
        for resource in world.visible_resources:
            distance = abs(resource.pos[0] - world.pos[0]) + abs(resource.pos[1] - world.pos[1])
            if distance <= vision_radius:
                # Check if claimed by other agents
                if resource.claimed_by_id is None or resource.claimed_by_id == world.agent_id:
                    available_resources.append(resource)
        
        if not available_resources:
            return []
        
        candidates = []
        current_u = world.utility.u(world.inventory["A"], world.inventory["B"])
        
        for resource in available_resources:
            pos = resource.pos
            distance = abs(pos[0] - world.pos[0]) + abs(pos[1] - world.pos[1])
            
            # Calculate utility gain from harvesting
            harvest_amount = min(resource.A + resource.B, forage_rate)
            
            # Determine which resource type and calculate new utility
            if resource.A > 0:
                new_u = world.utility.u(
                    world.inventory["A"] + harvest_amount,
                    world.inventory["B"]
                )
            elif resource.B > 0:
                new_u = world.utility.u(
                    world.inventory["A"],
                    world.inventory["B"] + harvest_amount
                )
            else:
                continue  # Empty resource
            
            delta_u = new_u - current_u
            
            if delta_u > 0:
                discounted_u = delta_u * (beta ** distance)
                candidates.append((pos, delta_u, discounted_u, distance))
        
        # Sort by (-discounted_u, pos[0], pos[1]) for deterministic ranking
        candidates.sort(key=lambda x: (-x[2], x[0][0], x[0][1]))
        
        # Convert to preference format
        preferences = []
        for pos, delta_u, discounted, distance in candidates:
            meta = {
                "utility_gain": delta_u,
                "discounted_utility_gain": discounted,
                "distance": distance,
            }
            preferences.append((pos, discounted, meta))
        
        return preferences
    
    def _select_trade_target(self, world: WorldView) -> list[Effect]:
        """Select best trade target within vision radius."""
        trade_prefs = self._build_trade_preferences(world, vision_radius=1)
        
        if not trade_prefs:
            # No targets within radius 1 - stay in place
            return []
        
        # Select top preference
        best_target_id, score, meta = trade_prefs[0]
        
        return [SetTarget(
            protocol_name=self.name,
            tick=world.tick,
            agent_id=world.agent_id,
            target=best_target_id  # Target is agent ID for trade
        )]
    
    def _select_forage_target(self, world: WorldView) -> list[Effect]:
        """Select best forage target within vision radius."""
        forage_prefs = self._build_forage_preferences(world, vision_radius=1)
        
        if not forage_prefs:
            # No targets within radius 1 - stay in place
            return []
        
        # Select top preference
        best_pos, score, meta = forage_prefs[0]
        
        effects = [
            SetTarget(
                protocol_name=self.name,
                tick=world.tick,
                agent_id=world.agent_id,
                target=best_pos
            ),
            ClaimResource(
                protocol_name=self.name,
                tick=world.tick,
                agent_id=world.agent_id,
                pos=best_pos
            )
        ]
        
        return effects
    
    def _select_mixed_target(self, world: WorldView) -> list[Effect]:
        """Compare best trade vs best forage within vision radius."""
        trade_prefs = self._build_trade_preferences(world, vision_radius=1)
        forage_prefs = self._build_forage_preferences(world, vision_radius=1)
        
        # Get best scores
        best_trade_score = trade_prefs[0][1] if trade_prefs else 0.0
        best_forage_score = forage_prefs[0][1] if forage_prefs else 0.0
        
        # Choose activity with higher score
        if trade_prefs and best_trade_score > best_forage_score:
            return self._select_trade_target(world)
        elif forage_prefs:
            return self._select_forage_target(world)
        else:
            # No targets within radius 1 - stay in place
            return []
    
    def _compute_barter_surplus_from_views(
        self, world: WorldView, neighbor
    ) -> float:
        """Compute barter surplus using quotes."""
        my_bid = world.quotes.get("bid_A_in_B", 0.0)
        my_ask = world.quotes.get("ask_A_in_B", 0.0)
        their_bid = neighbor.quotes.get("bid_A_in_B", 0.0)
        their_ask = neighbor.quotes.get("ask_A_in_B", 0.0)
        
        # Calculate overlaps
        overlap_dir1 = my_bid - their_ask  # I buy A from them
        overlap_dir2 = their_bid - my_ask  # They buy A from me
        
        # Check inventory feasibility
        dir1_feasible = (world.inventory.get("B", 0) >= 1)
        dir2_feasible = (world.inventory.get("A", 0) >= 1)
        
        # Return max feasible overlap
        feasible_overlaps = []
        if dir1_feasible and overlap_dir1 > 0:
            feasible_overlaps.append(overlap_dir1)
        if dir2_feasible and overlap_dir2 > 0:
            feasible_overlaps.append(overlap_dir2)
        
        return max(feasible_overlaps) if feasible_overlaps else 0.0
    

