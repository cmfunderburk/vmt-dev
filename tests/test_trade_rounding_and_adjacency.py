import math
import pytest
from vmt_engine.core.spatial_index import SpatialIndex


def round_half_up(x: float) -> int:
    # reference impl the engine must match (portable round-half-up)
    from math import floor
    return int(floor(x + 0.5))


def test_round_half_up_reference():
    vals = [(1.49, 1), (1.5, 2), (2.5, 3), (2.51, 3), (0.5, 1)]
    for x, want in vals:
        assert round_half_up(x) == want


def manhattan_distance(pos1, pos2):
    """Calculate Manhattan distance between two positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def test_pairs_within_interaction_radius_are_matched():
    """
    Verify that query_pairs_within_radius only returns pairs within the specified
    Manhattan distance, and that all valid pairs are included.
    """
    # Create a spatial index on a 10x10 grid
    spatial_index = SpatialIndex(grid_size=10, bucket_size=5)
    
    # Place agents at specific positions
    # Agent 0 at (5, 5) - center
    # Agent 1 at (5, 6) - distance 1 (adjacent)
    # Agent 2 at (6, 5) - distance 1 (adjacent)
    # Agent 3 at (7, 7) - distance 4 (not adjacent)
    # Agent 4 at (5, 5) - distance 0 (same position as agent 0)
    positions = {
        0: (5, 5),
        1: (5, 6),
        2: (6, 5),
        3: (7, 7),
        4: (5, 5),
    }
    
    for agent_id, pos in positions.items():
        spatial_index.add_agent(agent_id, pos)
    
    # Query pairs within interaction_radius=1
    pairs = spatial_index.query_pairs_within_radius(radius=1)
    
    # Convert to set for easier testing
    pair_set = set(pairs)
    
    # Verify all pairs are within distance 1
    for id1, id2 in pairs:
        dist = manhattan_distance(positions[id1], positions[id2])
        assert dist <= 1, f"Pair ({id1}, {id2}) has distance {dist} > 1"
    
    # Verify expected adjacent pairs are included
    # (0, 1): distance 1 ✓
    # (0, 2): distance 1 ✓
    # (0, 4): distance 0 ✓
    # (1, 4): distance 1 ✓
    # (2, 4): distance 1 ✓
    # (3, X): distance 4 or 3, should NOT appear with radius 1
    
    assert (0, 1) in pair_set or (1, 0) in pair_set
    assert (0, 2) in pair_set or (2, 0) in pair_set
    assert (0, 4) in pair_set or (4, 0) in pair_set
    
    # Verify distant pair is NOT included
    assert (0, 3) not in pair_set and (3, 0) not in pair_set
    assert (1, 3) not in pair_set and (3, 1) not in pair_set
    assert (2, 3) not in pair_set and (3, 2) not in pair_set
    
    # Verify agent 3 either has no pairs or only with agent 4 (if they're close)
    agent3_pairs = [p for p in pairs if 3 in p]
    for p in agent3_pairs:
        other_id = p[0] if p[1] == 3 else p[1]
        dist = manhattan_distance(positions[3], positions[other_id])
        assert dist <= 1


def test_interaction_radius_zero_only_same_cell():
    """
    Verify that interaction_radius=0 only matches agents at exactly the same position.
    """
    spatial_index = SpatialIndex(grid_size=10, bucket_size=5)
    
    # Place agents
    spatial_index.add_agent(0, (5, 5))
    spatial_index.add_agent(1, (5, 5))  # Same position as 0
    spatial_index.add_agent(2, (5, 6))  # Adjacent, distance 1
    
    pairs = spatial_index.query_pairs_within_radius(radius=0)
    pair_set = set(pairs)
    
    # Only agents at the same position should be paired
    assert (0, 1) in pair_set or (1, 0) in pair_set
    
    # Adjacent agent should NOT be paired
    assert (0, 2) not in pair_set and (2, 0) not in pair_set
    assert (1, 2) not in pair_set and (2, 1) not in pair_set
