"""
Bargaining Protocols

Bargaining protocols determine how paired agents negotiate trade terms.

Available Protocols:
- LegacyBargainingProtocol: Compensating block with money-aware matching
- (Future: Take-it-or-leave-it, Rubinstein, Nash)

Version: 2025.10.26 (Phase 1 - Legacy Implementation)
"""

from .legacy import LegacyBargainingProtocol

__all__ = [
    "LegacyBargainingProtocol",
]

