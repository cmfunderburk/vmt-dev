"""
Search Protocols - Agent-Based Modeling Paradigm

Search protocols determine how agents select targets for interaction in spatial
environments. These protocols implement bounded rationality and local information
processing, leading to emergent market patterns.

Available Protocols:
- legacy_distance_discounted: Original VMT distance-weighted search
- random_walk: Stochastic exploration (pedagogical baseline)
- myopic: Limited-vision search (radius=1, pedagogical)

Theoretical Context:
- Decentralized decision making
- Spatial search with friction
- Bounded rationality

Version: Post-Restructure (Part 0)
"""

from .base import SearchProtocol
from .legacy import LegacySearchProtocol
from .random_walk import RandomWalkSearch
from .myopic import MyopicSearch

__all__ = [
    "SearchProtocol",
    "LegacySearchProtocol",
    "RandomWalkSearch",
    "MyopicSearch",
]

