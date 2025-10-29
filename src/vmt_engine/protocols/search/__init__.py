"""
Search Protocols

Search protocols determine how agents select targets for movement and interaction.

Available Protocols:
- LegacySearchProtocol: Distance-discounted search (original VMT algorithm)
- RandomWalkSearch: Stochastic exploration baseline (Phase 2a)
- MyopicSearch: Limited vision search (radius=1) (Phase 2b)

Version: 2025.10.28 (Phase 2b - Pedagogical Protocols)
"""

from .legacy import LegacySearchProtocol
from .random_walk import RandomWalkSearch
from .myopic import MyopicSearch

from ..registry import ProtocolRegistry  # Crash-fast check
_reg = ProtocolRegistry.list_protocols()
assert "legacy_distance_discounted" in _reg.get("search", []), "Search registry missing 'legacy_distance_discounted'"
assert "random_walk" in _reg.get("search", []), "Search registry missing 'random_walk'"
assert "myopic" in _reg.get("search", []), "Search registry missing 'myopic'"

__all__ = [
    "LegacySearchProtocol",
    "RandomWalkSearch",
    "MyopicSearch",
]

