"""
Random Walk Search Protocol

Pure stochastic exploration for baseline comparison. Agents select random
movement targets within vision radius with no utility calculation.

Economic Properties:
- Zero information efficiency
- Equivalent to Brownian motion in economic search models
- Demonstrates value of information vs rational search

References:
- Stigler (1961) "The Economics of Information"
- Random search models in labor economics

Version: 2025.10.28
"""

from typing import Any
from ...protocols.registry import register_protocol

from .base import SearchProtocol
from ...protocols.base import SetTarget
from ...protocols.context import WorldView


@register_protocol(
    category="search",
    name="random_walk",
    description="Pure stochastic exploration for baseline comparison",
    properties=["stochastic", "baseline", "pedagogical"],
    complexity="O(V)",
    references=[
        "Stigler (1961) The Economics of Information",
        "Random search models in labor economics",
    ],
)
class RandomWalkSearch(SearchProtocol):
    """
    Stochastic exploration for baseline comparison.
    
    Behavior:
        - Agents select random positions within vision radius
        - No utility calculation or optimization
        - Pure exploration, zero exploitation
        - Honors pairing commitments (paired agents don't search)
    
    Economic Interpretation:
        - Zero-information baseline for measuring search efficiency
        - Shows opportunity cost of not using available information
        - Demonstrates how random search performs in spatial markets
    
    Pedagogical Value:
        - Clear demonstration of information value
        - Simple null hypothesis for search theory
        - Easy to understand and implement
    """
    
    @property
    def name(self) -> str:
        return "random_walk"
    
    @property
    def version(self) -> str:
        return "2025.10.28"
    
    # Class-level for registry
    VERSION = "2025.10.28"
    
    def build_preferences(self, world: WorldView) -> list[tuple[Any, float, dict]]:
        """
        Build randomly ordered list of movement targets.
        
        Args:
            world: Agent's immutable perception snapshot
        
        Returns:
            List of (position, score, metadata) tuples with equal scores.
            All positions get score 0.0 since there's no preference.
        """
        # Get all visible positions within Manhattan distance
        vision_radius = world.params.get("vision_radius", 5)
        grid_size = world.params.get("grid_size", 32)
        
        visible_positions = self._get_visible_positions(
            world.pos,
            vision_radius,
            grid_size
        )
        
        # Filter out current position (don't "move" to where we are)
        targets = [pos for pos in visible_positions if pos != world.pos]
        
        if not targets:
            return []
        
        # Shuffle using deterministic RNG for reproducibility
        shuffled = targets.copy()
        world.rng.shuffle(shuffled)
        
        # Return as preferences with equal scores (no real preference)
        # All targets equally likely, ordering is random
        preferences = []
        for pos in shuffled:
            preferences.append((
                pos,
                0.0,  # No score - all positions equal
                {"type": "random_walk", "distance": self._manhattan_distance(world.pos, pos)}
            ))
        
        return preferences
    
    def select_target(self, world: WorldView) -> list:
        """
        Select random target from preferences.
        
        Args:
            world: Agent's immutable perception snapshot
        
        Returns:
            List containing single SetTarget effect, or empty list if no targets
        """
        # Skip if already paired (honor commitments)
        if world.paired_with_id is not None:
            return []
        
        # Build random preferences
        prefs = self.build_preferences(world)
        
        if not prefs:
            # No visible targets, stay put
            return []
        
        # Select first target (random due to shuffle)
        target_pos, score, metadata = prefs[0]
        
        # Emit SetTarget effect
        return [SetTarget(
            protocol_name=self.name,
            tick=world.tick,
            agent_id=world.agent_id,
            target=target_pos
        )]
    
    def _get_visible_positions(
        self,
        center: tuple[int, int],
        radius: int,
        grid_size: int
    ) -> list[tuple[int, int]]:
        """
        Get all positions within Manhattan distance radius.
        
        Args:
            center: Agent's current position
            radius: Vision radius (Manhattan distance)
            grid_size: Grid dimension (for wrapping)
        
        Returns:
            List of all visible positions including center
        
        Note:
            Grid positions are [0, grid_size-1]. We do NOT wrap - VMT grids
            are bounded, not toroidal. Only include positions within grid bounds.
        """
        positions = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                # Check Manhattan distance
                if abs(dx) + abs(dy) <= radius:
                    x = center[0] + dx
                    y = center[1] + dy
                    
                    # Only include if within grid bounds (no wrapping)
                    if 0 <= x < grid_size and 0 <= y < grid_size:
                        positions.append((x, y))
        return positions
    
    def _manhattan_distance(
        self,
        pos1: tuple[int, int],
        pos2: tuple[int, int]
    ) -> int:
        """Calculate Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

