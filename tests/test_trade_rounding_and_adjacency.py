import math
import pytest


def round_half_up(x: float) -> int:
    # reference impl the engine must match (portable round-half-up)
    from math import floor
    return int(floor(x + 0.5))


def test_round_half_up_reference():
    vals = [(1.49, 1), (1.5, 2), (2.5, 3), (2.51, 3), (0.5, 1)]
    for x, want in vals:
        assert round_half_up(x) == want


def test_pairs_within_interaction_radius_are_matched():
    # Pseudocode/contract placeholder: ensure the matcher yields pairs at distance 0 or 1 when param==1.
    # Implement once the matcher exists; for now, encode the contract with a skip.
    pytest.skip("Implement once matching module exists: expect adjacency pairs when interaction_radius=1")
