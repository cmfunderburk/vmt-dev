"""
Game Theory Module

Implements strategic interaction mechanisms: bargaining, matching, and future
game-theoretic protocols (auctions, voting, etc.).

Sub-modules:
- bargaining: Trade negotiation protocols
- matching: Bilateral pairing protocols
"""

from . import bargaining
from . import matching

__all__ = ["bargaining", "matching"]

