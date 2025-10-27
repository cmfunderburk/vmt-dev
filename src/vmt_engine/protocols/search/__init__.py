"""
Search Protocols

Search protocols determine how agents select targets for movement and interaction.

Available Protocols:
- LegacySearchProtocol: Distance-discounted search (original VMT algorithm)
- (Future: Random walk, Memory-based)

Version: 2025.10.26 (Phase 1 - Legacy Implementation)
"""

from .legacy import LegacySearchProtocol

__all__ = [
    "LegacySearchProtocol",
]

