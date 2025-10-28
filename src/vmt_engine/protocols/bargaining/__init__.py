"""
Bargaining Protocols

Bargaining protocols determine how paired agents negotiate trade terms.

Available Protocols:
- LegacyBargainingProtocol: Compensating block with money-aware matching
- SplitDifference: Equal surplus division baseline (Phase 2a)

Version: 2025.10.28 (Phase 2a - Baseline Protocols)
"""

from .legacy import LegacyBargainingProtocol
from .split_difference import SplitDifference

from ..registry import ProtocolRegistry  # Crash-fast check
_reg = ProtocolRegistry.list_protocols()
assert "legacy_compensating_block" in _reg.get("bargaining", []), "Bargaining registry missing 'legacy_compensating_block'"
assert "split_difference" in _reg.get("bargaining", []), "Bargaining registry missing 'split_difference'"

__all__ = [
    "LegacyBargainingProtocol",
    "SplitDifference",
]

