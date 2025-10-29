"""
Market clearing mechanisms.

Market mechanisms determine how trades are executed within a market area.
Examples:
- Walrasian: Tatonnement-based price adjustment to clear markets
- Posted Price: Fixed prices set by market maker
- CDA: Continuous double auction (deferred)
"""

from .walrasian import WalrasianAuctioneer

__all__ = ['WalrasianAuctioneer']

