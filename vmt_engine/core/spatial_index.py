"""
Spatial indexing for efficient proximity queries.
"""

from typing import TYPE_CHECKING
from collections import defaultdict
from .state import Position

if TYPE_CHECKING:
    from .agent import Agent


class SpatialIndex:
    """
    Grid-based spatial hash for efficient agent proximity queries.
    
    Reduces agent-agent proximity queries from O(N²) to O(N) average case
    by bucketing agents into grid cells and only checking nearby buckets.
    """
    
    def __init__(self, grid_size: int, bucket_size: int):
        """
        Initialize spatial index.
        
        Args:
            grid_size: Size of the simulation grid (N for NxN grid)
            bucket_size: Size of each bucket (should be >= max query radius for best performance)
        """
        self.grid_size = grid_size
        self.bucket_size = max(1, bucket_size)
        
        # Map from bucket coordinate to set of agent IDs
        self.buckets: dict[tuple[int, int], set[int]] = defaultdict(set)
        
        # Map from agent ID to current bucket coordinate
        self.agent_buckets: dict[int, tuple[int, int]] = {}
        
        # Map from agent ID to position (for distance calculations)
        self.agent_positions: dict[int, Position] = {}
    
    def _get_bucket(self, pos: Position) -> tuple[int, int]:
        """Get bucket coordinate for a position."""
        bx = pos[0] // self.bucket_size
        by = pos[1] // self.bucket_size
        return (bx, by)
    
    def add_agent(self, agent_id: int, pos: Position):
        """
        Add or update an agent's position in the index.
        
        Args:
            agent_id: Agent ID
            pos: Agent position
        """
        # Remove from old bucket if exists
        if agent_id in self.agent_buckets:
            old_bucket = self.agent_buckets[agent_id]
            self.buckets[old_bucket].discard(agent_id)
        
        # Add to new bucket
        new_bucket = self._get_bucket(pos)
        self.buckets[new_bucket].add(agent_id)
        self.agent_buckets[agent_id] = new_bucket
        self.agent_positions[agent_id] = pos
    
    def remove_agent(self, agent_id: int):
        """
        Remove an agent from the index.
        
        Args:
            agent_id: Agent ID to remove
        """
        if agent_id in self.agent_buckets:
            bucket = self.agent_buckets[agent_id]
            self.buckets[bucket].discard(agent_id)
            del self.agent_buckets[agent_id]
            del self.agent_positions[agent_id]
    
    def update_position(self, agent_id: int, new_pos: Position):
        """
        Update an agent's position (equivalent to add_agent).
        
        Args:
            agent_id: Agent ID
            new_pos: New position
        """
        self.add_agent(agent_id, new_pos)
    
    def query_radius(self, pos: Position, radius: int, exclude_id: int | None = None) -> list[int]:
        """
        Find all agents within Manhattan distance radius of pos.
        
        Args:
            pos: Query position
            radius: Maximum Manhattan distance
            exclude_id: Optional agent ID to exclude from results (e.g., querying agent itself)
            
        Returns:
            List of agent IDs within radius
        """
        # Determine which buckets to check
        # We need to check all buckets that could contain agents within radius
        bucket_radius = (radius + self.bucket_size - 1) // self.bucket_size  # Ceiling division
        
        center_bucket = self._get_bucket(pos)
        candidates = []
        
        for bx in range(center_bucket[0] - bucket_radius, center_bucket[0] + bucket_radius + 1):
            for by in range(center_bucket[1] - bucket_radius, center_bucket[1] + bucket_radius + 1):
                bucket_agents = self.buckets.get((bx, by), set())
                for agent_id in bucket_agents:
                    if exclude_id is not None and agent_id == exclude_id:
                        continue
                    
                    agent_pos = self.agent_positions[agent_id]
                    distance = abs(pos[0] - agent_pos[0]) + abs(pos[1] - agent_pos[1])
                    
                    if distance <= radius:
                        candidates.append(agent_id)
        
        return candidates
    
    def query_pairs_within_radius(self, radius: int) -> list[tuple[int, int]]:
        """
        Find all pairs of agents within Manhattan distance radius of each other.
        
        More efficient than checking all O(N²) pairs by only checking agents
        in nearby buckets.
        
        Args:
            radius: Maximum Manhattan distance between pairs
            
        Returns:
            List of (agent_id1, agent_id2) tuples where id1 < id2 and distance <= radius
        """
        pairs = []
        seen_pairs = set()
        
        # For each agent, query nearby agents
        for agent_id, pos in self.agent_positions.items():
            nearby = self.query_radius(pos, radius, exclude_id=agent_id)
            
            for other_id in nearby:
                # Ensure we don't double-count pairs
                pair = (min(agent_id, other_id), max(agent_id, other_id))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    pairs.append(pair)
        
        return pairs
    
    def clear(self):
        """Clear all agents from the index."""
        self.buckets.clear()
        self.agent_buckets.clear()
        self.agent_positions.clear()

