"""
Search Protocols

Search protocols determine how agents select targets for movement and interaction.

Available Protocols:
- LegacySearchProtocol: Distance-discounted search (original VMT algorithm)
- RandomWalkSearch: Stochastic exploration baseline (Phase 2a)

Version: 2025.10.28 (Phase 2a - Baseline Protocols)
"""

from .legacy import LegacySearchProtocol
from .random_walk import RandomWalkSearch

__all__ = [
    "LegacySearchProtocol",
    "RandomWalkSearch",
]

