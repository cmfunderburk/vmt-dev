"""
Bargaining Protocols - Game Theory Paradigm

Bargaining protocols determine how paired agents negotiate trade terms.
These protocols implement strategic negotiation mechanisms from bargaining theory.

Available Protocols:
- compensating_block: Foundational VMT algorithm (first feasible trade) [DEFAULT]
- split_difference: Equal surplus division (Nash bargaining)
- take_it_or_leave_it: Asymmetric bargaining power (ultimatum game)

Theoretical Context:
- Axiomatic bargaining solutions
- Strategic bargaining games
- Nash program

Version: Post-Decoupling (v2)
"""

from .base import BargainingProtocol
from .compensating_block import CompensatingBlockBargaining
from .split_difference import SplitDifference
from .take_it_or_leave_it import TakeItOrLeaveIt

__all__ = [
    "BargainingProtocol",
    "CompensatingBlockBargaining",
    "SplitDifference",
    "TakeItOrLeaveIt",
]

