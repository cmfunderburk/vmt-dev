"""
Matching Protocols

Matching protocols determine how agents form bilateral pairs for trading.

Available Protocols:
- LegacyMatchingProtocol: Three-pass algorithm (mutual consent + greedy fallback)
- RandomMatching: Random pairing baseline (Phase 2a)
- GreedySurplusMatching: Welfare maximization without consent (Phase 2b)

Version: 2025.10.28 (Phase 2b - Pedagogical Protocols)
"""

from .legacy import LegacyMatchingProtocol
from .random import RandomMatching
from .greedy import GreedySurplusMatching

from ..registry import ProtocolRegistry  # Crash-fast check
_reg = ProtocolRegistry.list_protocols()
assert "legacy_three_pass" in _reg.get("matching", []), "Matching registry missing 'legacy_three_pass'"
assert "random_matching" in _reg.get("matching", []), "Matching registry missing 'random_matching'"
assert "greedy_surplus" in _reg.get("matching", []), "Matching registry missing 'greedy_surplus'"

__all__ = [
    "LegacyMatchingProtocol",
    "RandomMatching",
    "GreedySurplusMatching",
]

