"""
Search Protocols - Agent-Based Modeling Paradigm

Search protocols determine how agents select targets for interaction in spatial
environments. These protocols implement bounded rationality and local information
processing, leading to emergent market patterns.

Available Protocols:
- distance_discounted_search: Original VMT distance-weighted search
- random_walk: Stochastic exploration (pedagogical baseline)

Theoretical Context:
- Decentralized decision making
- Spatial search with friction
- Bounded rationality

Version: Post-Restructure (Part 0)
"""

from .base import SearchProtocol
from .distance_discounted import DistanceDiscountedSearch
from .random_walk import RandomWalkSearch

__all__ = [
    "SearchProtocol",
    "DistanceDiscountedSearch",
    "RandomWalkSearch",
]

