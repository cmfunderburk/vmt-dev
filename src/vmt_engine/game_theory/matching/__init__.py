"""
Matching Protocols - Game Theory Paradigm

Matching protocols determine how agents form bilateral pairs for negotiation.
These protocols implement strategic pairing mechanisms from matching theory.

Available Protocols:
- three_pass_matching: Original VMT three-pass matching
- random_matching: Random bilateral pairing (baseline)
- greedy_surplus: Greedy matching by expected surplus

Theoretical Context:
- Two-sided matching markets
- Stable matchings
- Mechanism design

Version: Post-Restructure (Part 0)
"""

from .base import MatchingProtocol
from .three_pass import ThreePassMatching
from .random import RandomMatching
from .greedy import GreedySurplusMatching

__all__ = [
    "MatchingProtocol",
    "ThreePassMatching",
    "RandomMatching",
    "GreedySurplusMatching",
]

