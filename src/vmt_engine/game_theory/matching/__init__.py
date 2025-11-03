"""
Matching Protocols - Game Theory Paradigm

Matching protocols determine how agents form bilateral pairs for negotiation.
These protocols implement strategic pairing mechanisms from matching theory.

Available Protocols:
- legacy_three_pass: Original VMT three-pass matching
- random_matching: Random bilateral pairing (baseline)
- greedy_surplus: Greedy matching by expected surplus

Theoretical Context:
- Two-sided matching markets
- Stable matchings
- Mechanism design

Version: Post-Restructure (Part 0)
"""

from .base import MatchingProtocol
from .legacy import LegacyMatchingProtocol
from .random import RandomMatching
from .greedy import GreedySurplusMatching

__all__ = [
    "MatchingProtocol",
    "LegacyMatchingProtocol",
    "RandomMatching",
    "GreedySurplusMatching",
]

