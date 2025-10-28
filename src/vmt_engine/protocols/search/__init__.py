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

from ..registry import ProtocolRegistry  # Crash-fast check
_reg = ProtocolRegistry.list_protocols()
assert "legacy" in _reg.get("search", []), "Search registry missing 'legacy'"
assert "random_walk" in _reg.get("search", []), "Search registry missing 'random_walk'"

__all__ = [
    "LegacySearchProtocol",
    "RandomWalkSearch",
]

