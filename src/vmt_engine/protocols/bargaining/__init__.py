"""
Bargaining Protocols

Bargaining protocols determine how paired agents negotiate trade terms.

Available Protocols:
- LegacyBargainingProtocol: Compensating block with money-aware matching
- SplitDifference: Equal surplus division baseline (Phase 2a)
- TakeItOrLeaveIt: Monopolistic offer bargaining (Phase 2b)

Version: 2025.10.28 (Phase 2b - Pedagogical Protocols)
"""

from .legacy import LegacyBargainingProtocol
from .split_difference import SplitDifference
from .take_it_or_leave_it import TakeItOrLeaveIt

from ..registry import ProtocolRegistry  # Crash-fast check
_reg = ProtocolRegistry.list_protocols()
assert "legacy_compensating_block" in _reg.get("bargaining", []), "Bargaining registry missing 'legacy_compensating_block'"
assert "split_difference" in _reg.get("bargaining", []), "Bargaining registry missing 'split_difference'"
assert "take_it_or_leave_it" in _reg.get("bargaining", []), "Bargaining registry missing 'take_it_or_leave_it'"

__all__ = [
    "LegacyBargainingProtocol",
    "SplitDifference",
    "TakeItOrLeaveIt",
]

