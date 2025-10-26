"""
Base interface for utility functions.

This module defines the abstract base class that all utility function
implementations must inherit from. It provides the contract for computing
utility values, marginal utilities, and reservation prices.

Contracts and zero-handling:
- Inventories A, B are integers; utility returns floats; prices/MRS are floats.
- CES MRS uses a zero-safe epsilon only for the A/B ratio when either A or B
  is zero; the utility function itself is not epsilon-shifted.
- Linear utility has constant MRS vA/vB and reservation bounds equal to MRS.

Money-aware API (Phase 2):
- u_goods(A, B): utility from goods only
- mu_A(A, B), mu_B(A, B): analytic marginal utilities
- u_total(inventory, params): top-level utility including money
- mu_money(M, lambda_money, money_utility_form, M_0): marginal utility of money
- Money utility forms: linear (λ·M) or log (λ·log(M + M_0))
"""

from __future__ import annotations
from abc import ABC, abstractmethod


class Utility(ABC):
    """Base interface for utility functions."""
    
    @abstractmethod
    def u(self, A: int, B: int) -> float:
        """
        Compute utility for inventory (A, B).
        
        DEPRECATED: Use u_goods() for the money-aware API.
        
        Args:
            A: Amount of good A
            B: Amount of good B
            
        Returns:
            Utility value
        """
        pass
    
    def u_goods(self, A: int, B: int) -> float:
        """
        Compute utility from goods only (money-aware API).
        
        This is the canonical method for Phase 2+. The legacy u() method
        routes through this for backward compatibility.
        
        Args:
            A: Amount of good A
            B: Amount of good B
            
        Returns:
            Utility value from goods
        """
        # Default implementation routes to u() for backward compatibility
        return self.u(A, B)
    
    def mu_A(self, A: int, B: int) -> float:
        """
        Compute marginal utility of good A (∂U/∂A).
        
        Args:
            A: Amount of good A
            B: Amount of good B
            
        Returns:
            Marginal utility of A
        """
        mu_tuple = self.mu(A, B)
        if mu_tuple is None:
            raise NotImplementedError(f"{self.__class__.__name__} must implement mu() or mu_A()")
        return mu_tuple[0]
    
    def mu_B(self, A: int, B: int) -> float:
        """
        Compute marginal utility of good B (∂U/∂B).
        
        Args:
            A: Amount of good A
            B: Amount of good B
            
        Returns:
            Marginal utility of B
        """
        mu_tuple = self.mu(A, B)
        if mu_tuple is None:
            raise NotImplementedError(f"{self.__class__.__name__} must implement mu() or mu_B()")
        return mu_tuple[1]
    
    def mu(self, A: int, B: int) -> tuple[float, float] | None:
        """
        Compute marginal utilities (∂U/∂A, ∂U/∂B).
        
        DEPRECATED: Use mu_A() and mu_B() for the money-aware API.
        
        Args:
            A: Amount of good A
            B: Amount of good B
            
        Returns:
            Tuple of (MU_A, MU_B) or None if not implemented
        """
        return None
    
    def mrs_A_in_B(self, A: int, B: int) -> float | None:
        """
        Compute marginal rate of substitution (MRS) of A in terms of B.
        MRS = MU_A / MU_B
        
        Args:
            A: Amount of good A
            B: Amount of good B
            
        Returns:
            MRS value or None if not implemented
        """
        return None
    
    @abstractmethod
    def reservation_bounds_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> tuple[float, float]:
        """
        Compute reservation price bounds (p_min, p_max) for trading A in terms of B.
        
        Args:
            A: Amount of good A
            B: Amount of good B
            eps: Small value for zero-safe calculations
            
        Returns:
            Tuple of (p_min, p_max) where p_min is seller's minimum and p_max is buyer's maximum
        """
        pass

