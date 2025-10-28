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

from ..registry import ProtocolRegistry  # Crash-fast check
_reg = ProtocolRegistry.list_protocols()
assert "legacy_three_pass" in _reg.get("matching", []), "Matching registry missing 'legacy_three_pass'"
assert "random_matching" in _reg.get("matching", []), "Matching registry missing 'random_matching'"

__all__ = [
    "LegacyMatchingProtocol",
    "RandomMatching",
]

