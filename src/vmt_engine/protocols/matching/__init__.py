"""
Matching Protocols

Matching protocols determine how agents form bilateral pairs for trading.

Available Protocols:
- LegacyMatchingProtocol: Three-pass algorithm (mutual consent + greedy fallback)
- RandomMatching: Random pairing baseline (Phase 2a)

Version: 2025.10.28 (Phase 2a - Baseline Protocols)
"""

from .legacy import LegacyMatchingProtocol
from .random import RandomMatching

__all__ = [
    "LegacyMatchingProtocol",
    "RandomMatching",
]

