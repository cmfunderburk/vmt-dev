"""
Matching Protocols

Matching protocols determine how agents form bilateral pairs for trading.

Available Protocols:
- LegacyMatchingProtocol: Three-pass algorithm (mutual consent + greedy fallback)
- (Future: Greedy surplus, Stable matching)

Version: 2025.10.26 (Phase 1 - Legacy Implementation)
"""

from .legacy import LegacyMatchingProtocol

__all__ = [
    "LegacyMatchingProtocol",
]

