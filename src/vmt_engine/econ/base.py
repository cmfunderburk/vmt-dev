"""
Base interface for utility functions.

This module defines the abstract base class that all utility function
implementations must inherit from. It provides the contract for computing
utility values, marginal utilities, and reservation prices.

Contracts and zero-handling:
- Inventories A, B are Decimal; utility returns floats; prices/MRS are floats.
- CES MRS uses a zero-safe epsilon only for the A/B ratio when either A or B
  is zero; the utility function itself is not epsilon-shifted.
- Linear utility has constant MRS vA/vB and reservation bounds equal to MRS.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from decimal import Decimal


class Utility(ABC):
    """Base interface for utility functions."""
    
    @abstractmethod
    def u(self, A: Decimal, B: Decimal) -> float:
        """
        Compute utility for inventory (A, B).
        
        Args:
            A: Amount of good A (Decimal)
            B: Amount of good B (Decimal)
            
        Returns:
            Utility value
        """
        pass
    
    def u_goods(self, A: Decimal, B: Decimal) -> float:
        """
        Compute utility from goods only.
        
        Args:
            A: Amount of good A (Decimal)
            B: Amount of good B (Decimal)
            
        Returns:
            Utility value from goods
        """
        return self.u(A, B)
    
    def mu_A(self, A: Decimal, B: Decimal) -> float:
        """
        Compute marginal utility of good A (∂U/∂A).
        
        Args:
            A: Amount of good A (Decimal)
            B: Amount of good B (Decimal)
            
        Returns:
            Marginal utility of A
        """
        mu_tuple = self.mu(A, B)
        if mu_tuple is None:
            raise NotImplementedError(f"{self.__class__.__name__} must implement mu() or mu_A()")
        return mu_tuple[0]
    
    def mu_B(self, A: Decimal, B: Decimal) -> float:
        """
        Compute marginal utility of good B (∂U/∂B).
        
        Args:
            A: Amount of good A (Decimal)
            B: Amount of good B (Decimal)
            
        Returns:
            Marginal utility of B
        """
        mu_tuple = self.mu(A, B)
        if mu_tuple is None:
            raise NotImplementedError(f"{self.__class__.__name__} must implement mu() or mu_B()")
        return mu_tuple[1]
    
    def mu(self, A: Decimal, B: Decimal) -> tuple[float, float] | None:
        """
        Compute marginal utilities (∂U/∂A, ∂U/∂B).
        
        Args:
            A: Amount of good A (Decimal)
            B: Amount of good B (Decimal)
            
        Returns:
            Tuple of (MU_A, MU_B) or None if not implemented
        """
        return None
    
    def mrs_A_in_B(self, A: Decimal, B: Decimal) -> float | None:
        """
        Compute marginal rate of substitution (MRS) of A in terms of B.
        MRS = MU_A / MU_B
        
        Args:
            A: Amount of good A (Decimal)
            B: Amount of good B (Decimal)
            
        Returns:
            MRS value or None if not implemented
        """
        return None
    
    @abstractmethod
    def reservation_bounds_A_in_B(self, A: Decimal, B: Decimal, eps: float = 1e-12) -> tuple[float, float]:
        """
        Compute reservation price bounds (p_min, p_max) for trading A in terms of B.
        
        Args:
            A: Amount of good A (Decimal)
            B: Amount of good B (Decimal)
            eps: Small value for zero-safe calculations
            
        Returns:
            Tuple of (p_min, p_max) where p_min is seller's minimum and p_max is buyer's maximum
        """
        pass

