"""
Legacy Search Protocol

Implements the original VMT search and target selection algorithm using
distance-discounted surplus for trade partners and distance-discounted
utility gain for foraging targets.

This protocol is bit-compatible with the pre-protocol DecisionSystem implementation.

Version: 2025.10.26 (Phase 1 - Legacy Adapter)
"""

from typing import Optional
from ..base import SearchProtocol, Effect, SetTarget, ClaimResource
from ..context import WorldView, AgentView, ResourceView
from ...systems.matching import compute_surplus, estimate_money_aware_surplus
from ...systems.movement import choose_forage_target
from ...core.state import Position

# Type alias for preference tuples
# (target_id, surplus, discounted_surplus, distance, pair_type)
Preference = tuple[int, float, float, int, str]


class LegacySearchProtocol(SearchProtocol):
    """
    Legacy distance-discounted search protocol.
    
    For trade:
    - Evaluates all visible neighbors
    - Calculates surplus (regime-aware)
    - Discounts by β^distance
    - Ranks by discounted surplus
    
    For forage:
    - Evaluates all visible resources
    - Calculates utility gain from harvesting
    - Discounts by β^distance
    - Filters claimed resources
    
    For mixed mode:
    - Evaluates both trade and forage
    - Chooses activity with higher discounted score
    """
    
    @property
    def name(self) -> str:
        return "legacy_distance_discounted"
    
    @property
    def version(self) -> str:
        return "2025.10.26"
    
    def build_preferences(self, world: WorldView) -> list[tuple[int | Position, float, dict]]:
        """
        Build ranked preference list for visible opportunities.
        
        For trade mode: Returns list of (agent_id, score, metadata)
        For forage mode: Returns list of (position, score, metadata)
        For both mode: Returns both, caller will compare and select
        
        Args:
            world: Agent's perception snapshot
        
        Returns:
            List of (target, discounted_score, metadata) tuples sorted by score descending
        """
        mode = world.mode
        
        # Always build trade preferences if mode allows
        trade_prefs = []
        if mode in ("trade", "both"):
            trade_prefs = self._build_trade_preferences(world)
        
        # Always build forage preferences if mode allows
        forage_prefs = []
        if mode in ("forage", "both"):
            forage_prefs = self._build_forage_preferences(world)
        
        # For "both" mode, caller needs both lists to compare
        # For single mode, return the applicable list
        if mode == "both":
            # Return combined list with type tag in metadata
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
        Select best target and emit effects.
        
        Returns:
            List of effects:
            - [SetTarget(...)] if target selected
            - [ClaimResource(...)] if foraging target selected
            - [] if no suitable target (idle)
        """
        mode = world.mode
        
        if mode == "trade":
            return self._select_trade_target(world)
        elif mode == "forage":
            return self._select_forage_target(world)
        else:  # "both"
            return self._select_mixed_target(world)
    
    def _build_trade_preferences(self, world: WorldView) -> list[tuple[int, float, dict]]:
        """
        Build ranked list of trade partners.
        
        Returns:
            List of (agent_id, discounted_surplus, metadata) sorted descending by score
        """
        beta = world.params.get("beta", 0.95)
        exchange_regime = world.exchange_regime
        
        candidates: list[tuple[int, float, float, int, str]] = []
        
        for neighbor in world.visible_agents:
            # Skip foraging-committed neighbors (not available for trade)
            # Note: We infer this from metadata, or could add to AgentView
            # For now, we'll check if they're targeting a resource
            # Actually, we don't have this info in AgentView - will need to add
            
            # Check trade cooldown
            if neighbor.agent_id in world.trade_cooldowns:
                if world.tick < world.trade_cooldowns[neighbor.agent_id]:
                    continue  # Still in cooldown
            
            # Calculate surplus (regime-aware)
            if exchange_regime in ("money_only", "mixed", "mixed_liquidity_gated"):
                # Need to create temporary Agent-like objects for surplus calculation
                # This is a temporary adapter - in Phase 2 we'll refactor surplus functions
                surplus, pair_type = self._estimate_surplus_from_views(
                    world, neighbor, exchange_regime
                )
            else:
                surplus, pair_type = self._compute_barter_surplus_from_views(
                    world, neighbor
                ), "A<->B"
            
            if surplus > 0:
                # Compute distance
                distance = abs(world.pos[0] - neighbor.pos[0]) + abs(world.pos[1] - neighbor.pos[1])
                
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
    
    def _build_forage_preferences(self, world: WorldView) -> list[tuple[Position, float, dict]]:
        """
        Build ranked list of forage targets.
        
        Returns:
            List of (position, discounted_utility_gain, metadata) sorted descending
        """
        beta = world.params.get("beta", 0.95)
        forage_rate = world.params.get("forage_rate", 1)
        
        # Filter claimed resources (exclude those claimed by others)
        available_resources = self._filter_claimed_resources(world)
        
        if not available_resources:
            return []
        
        # Use existing choose_forage_target helper
        # But we need to adapt it or reimplement for WorldView
        # For now, let's reimplement the logic here
        
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
        """Select best trade target."""
        trade_prefs = self._build_trade_preferences(world)
        
        if not trade_prefs:
            # No trade targets, agent goes idle
            # No effect needed - orchestrator will handle idle state
            return []
        
        # Select top preference
        best_target_id, score, meta = trade_prefs[0]
        
        # Return SetTarget effect pointing to the partner's position
        # We need the partner's position - find it in visible_agents
        partner_pos = None
        for neighbor in world.visible_agents:
            if neighbor.agent_id == best_target_id:
                partner_pos = neighbor.pos
                break
        
        if partner_pos is None:
            # Shouldn't happen, but defensive
            return []
        
        return [SetTarget(
            protocol_name=self.name,
            tick=world.tick,
            agent_id=world.agent_id,
            target=best_target_id  # Target is agent ID for trade
        )]
    
    def _select_forage_target(self, world: WorldView) -> list[Effect]:
        """Select best forage target."""
        forage_prefs = self._build_forage_preferences(world)
        
        if not forage_prefs:
            # No forage targets available
            # Idle fallback - return to home
            if world.params.get("home_pos") is not None:
                return [SetTarget(
                    protocol_name=self.name,
                    tick=world.tick,
                    agent_id=world.agent_id,
                    target=world.params["home_pos"]
                )]
            return []
        
        # Select top preference
        best_pos, score, meta = forage_prefs[0]
        
        # Return both SetTarget and ClaimResource effects
        return [
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
    
    def _select_mixed_target(self, world: WorldView) -> list[Effect]:
        """
        Compare best trade vs best forage and select higher-scoring option.
        """
        trade_prefs = self._build_trade_preferences(world)
        forage_prefs = self._build_forage_preferences(world)
        
        # Get best scores
        best_trade_score = trade_prefs[0][1] if trade_prefs else 0.0
        best_forage_score = forage_prefs[0][1] if forage_prefs else 0.0
        
        # Choose activity with higher score
        if trade_prefs and best_trade_score > best_forage_score:
            return self._select_trade_target(world)
        elif forage_prefs:
            return self._select_forage_target(world)
        else:
            # Both options exhausted - idle
            if world.params.get("home_pos") is not None:
                return [SetTarget(
                    protocol_name=self.name,
                    tick=world.tick,
                    agent_id=world.agent_id,
                    target=world.params["home_pos"]
                )]
            return []
    
    def _filter_claimed_resources(self, world: WorldView) -> list[ResourceView]:
        """Filter out resources claimed by OTHER agents."""
        if not world.params.get("enable_resource_claiming", False):
            return world.visible_resources  # Feature disabled, return all
        
        # Get resource claims from world context
        resource_claims = world.params.get("resource_claims", {})
        
        available = []
        for resource in world.visible_resources:
            claiming_agent = resource_claims.get(resource.pos)
            
            # Include if: unclaimed OR claimed by current agent
            if claiming_agent is None or claiming_agent == world.agent_id:
                available.append(resource)
        
        return available
    
    def _compute_barter_surplus_from_views(
        self, world: WorldView, neighbor: AgentView
    ) -> float:
        """
        Compute barter surplus between agent and neighbor using quotes.
        
        This is a lightweight approximation used during search.
        Full compensating block search happens during bargaining.
        """
        # Get quotes
        my_bid = world.quotes.get("bid_A_in_B", 0.0)
        my_ask = world.quotes.get("ask_A_in_B", 0.0)
        their_bid = neighbor.quotes.get("bid_A_in_B", 0.0)
        their_ask = neighbor.quotes.get("ask_A_in_B", 0.0)
        
        # Calculate overlaps
        overlap_dir1 = my_bid - their_ask  # I buy A from them
        overlap_dir2 = their_bid - my_ask  # They buy A from me
        
        # Check inventory feasibility (simplified - just check we have ANY inventory)
        dir1_feasible = (world.inventory.get("B", 0) >= 1)  # I need B to buy
        dir2_feasible = (world.inventory.get("A", 0) >= 1)  # I need A to sell
        
        # Return max feasible overlap
        feasible_overlaps = []
        if dir1_feasible and overlap_dir1 > 0:
            feasible_overlaps.append(overlap_dir1)
        if dir2_feasible and overlap_dir2 > 0:
            feasible_overlaps.append(overlap_dir2)
        
        return max(feasible_overlaps) if feasible_overlaps else 0.0
    
    def _estimate_surplus_from_views(
        self, world: WorldView, neighbor: AgentView, regime: str
    ) -> tuple[float, str]:
        """
        Estimate money-aware surplus using quotes.
        
        This is a lightweight heuristic for pairing decisions.
        """
        # Money-aware surplus estimation
        # We'll need to implement a simplified version or import the helper
        
        # Get all quotes
        my_quotes = world.quotes
        their_quotes = neighbor.quotes
        
        # Try each pair type and find best
        best_surplus = 0.0
        best_pair = "A<->B"
        
        # A<->M: I buy A for money
        if regime in ("money_only", "mixed", "mixed_liquidity_gated"):
            # I ask for A (sell A for M), they bid for A (buy A for M)
            my_ask_A_M = my_quotes.get("ask_A_in_M", float("inf"))
            their_bid_A_M = their_quotes.get("bid_A_in_M", 0.0)
            overlap_A_M = their_bid_A_M - my_ask_A_M
            
            if overlap_A_M > best_surplus:
                best_surplus = overlap_A_M
                best_pair = "A<->M"
            
            # B<->M: Similar logic
            my_ask_B_M = my_quotes.get("ask_B_in_M", float("inf"))
            their_bid_B_M = their_quotes.get("bid_B_in_M", 0.0)
            overlap_B_M = their_bid_B_M - my_ask_B_M
            
            if overlap_B_M > best_surplus:
                best_surplus = overlap_B_M
                best_pair = "B<->M"
        
        # A<->B: Barter (allowed in mixed, not in money_only)
        if regime in ("barter_only", "mixed", "mixed_liquidity_gated"):
            barter_surplus = self._compute_barter_surplus_from_views(world, neighbor)
            if barter_surplus > best_surplus:
                best_surplus = barter_surplus
                best_pair = "A<->B"
        
        return best_surplus, best_pair

