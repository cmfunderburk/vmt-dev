"""
Utility functions for agent preferences.

Contracts and zero-handling:
- Inventories A, B are integers; utility returns floats; prices/MRS are floats.
- CES MRS uses a zero-safe epsilon only for the A/B ratio when either A or B
  is zero; the utility function itself is not epsilon-shifted.
- Linear utility has constant MRS vA/vB and reservation bounds equal to MRS.

Money-aware API (Phase 2):
- u_goods(A, B): utility from goods only
- mu_A(A, B), mu_B(A, B): analytic marginal utilities
- u_total(inventory, params): top-level utility including money (future)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import math
import warnings


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


class UCES(Utility):
    """CES (Constant Elasticity of Substitution) utility function."""
    
    def __init__(self, rho: float, wA: float, wB: float):
        """
        Initialize CES utility: U = [wA * A^ρ + wB * B^ρ]^(1/ρ)
        
        Args:
            rho: Elasticity parameter (ρ ≠ 1)
            wA: Weight for good A (> 0)
            wB: Weight for good B (> 0)
        """
        if rho == 1.0:
            raise ValueError("CES utility cannot have rho=1.0")
        if wA <= 0 or wB <= 0:
            raise ValueError("CES weights must be positive")
        
        self.rho = rho
        self.wA = wA
        self.wB = wB
    
    def u(self, A: int, B: int) -> float:
        """Compute CES utility.
        For negative rho, zero in either good collapses utility toward 0.
        """
        if A == 0 and B == 0:
            return 0.0
        
        # Handle zero cases carefully
        if self.rho < 0:
            # For negative rho, zero inventory in either good makes utility approach 0
            if A == 0 or B == 0:
                return 0.0
        
        term_A = self.wA * (A ** self.rho) if A > 0 else 0.0
        term_B = self.wB * (B ** self.rho) if B > 0 else 0.0
        
        total = term_A + term_B
        if total <= 0:
            return 0.0
        
        return total ** (1.0 / self.rho)
    
    def mu(self, A: int, B: int, eps: float = 1e-12) -> tuple[float, float]:
        """
        Compute marginal utilities for CES.
        
        MU_A = U^(1-ρ) * wA * A^(ρ-1)
        MU_B = U^(1-ρ) * wB * B^(ρ-1)
        
        Args:
            A: Amount of good A
            B: Amount of good B
            eps: Small value for zero-safe calculations
            
        Returns:
            Tuple of (MU_A, MU_B)
        """
        # Handle zero cases
        if A == 0 and B == 0:
            # At origin, marginal utilities are indeterminate; use weights
            return (self.wA, self.wB)
        
        # For negative rho, zero in either good makes utility 0
        if self.rho < 0 and (A == 0 or B == 0):
            # At boundary with rho < 0, MU is infinite for the zero good
            # Use safe epsilon-shifted values
            A_safe = max(A, eps)
            B_safe = max(B, eps)
        else:
            A_safe = max(A, eps)
            B_safe = max(B, eps)
        
        # Compute utility at current point
        U = self.u(int(A_safe), int(B_safe))
        
        if U == 0:
            return (0.0, 0.0)
        
        # MU_A = U^(1-ρ) * wA * A^(ρ-1)
        # MU_B = U^(1-ρ) * wB * B^(ρ-1)
        U_power = U ** (1 - self.rho)
        mu_A = U_power * self.wA * (A_safe ** (self.rho - 1))
        mu_B = U_power * self.wB * (B_safe ** (self.rho - 1))
        
        return (mu_A, mu_B)
    
    def mrs_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> float:
        """
        Compute MRS for CES: (wA/wB) * (A/B)^(ρ-1)
        Apply zero-safe shift to the ratio only when A==0 or B==0.
        """
        # Only apply epsilon shift if either A or B is zero
        if A == 0 or B == 0:
            A_safe = A + eps
            B_safe = B + eps
        else:
            A_safe = float(A)
            B_safe = float(B)
        
        ratio = A_safe / B_safe
        mrs = (self.wA / self.wB) * (ratio ** (self.rho - 1))
        
        return mrs
    
    def reservation_bounds_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> tuple[float, float]:
        """For CES utility with analytic MRS, reservation bounds are (mrs, mrs)."""
        mrs = self.mrs_A_in_B(A, B, eps)
        return (mrs, mrs)


class ULinear(Utility):
    """Linear utility function: U = vA * A + vB * B"""
    
    def __init__(self, vA: float, vB: float):
        """
        Initialize linear utility.
        
        Args:
            vA: Value of good A (> 0)
            vB: Value of good B (> 0)
        """
        if vA <= 0 or vB <= 0:
            raise ValueError("Linear utility values must be positive")
        
        self.vA = vA
        self.vB = vB
    
    def u(self, A: int, B: int) -> float:
        """Compute linear utility."""
        return self.vA * A + self.vB * B
    
    def mu(self, A: int, B: int) -> tuple[float, float]:
        """
        Compute marginal utilities for linear utility.
        
        MU_A = vA (constant)
        MU_B = vB (constant)
        
        Args:
            A: Amount of good A (unused, kept for interface consistency)
            B: Amount of good B (unused, kept for interface consistency)
            
        Returns:
            Tuple of (MU_A, MU_B)
        """
        return (self.vA, self.vB)
    
    def mrs_A_in_B(self, A: int, B: int) -> float:
        """MRS for linear utility is constant: vA / vB"""
        return self.vA / self.vB
    
    def reservation_bounds_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> tuple[float, float]:
        """For linear utility, reservation bounds are constant (mrs, mrs)."""
        mrs = self.vA / self.vB
        return (mrs, mrs)


def create_utility(config: dict) -> Utility:
    """
    Factory function to create utility from configuration.
    
    DEPRECATED: Direct instantiation (UCES, ULinear) is preferred for clarity.
    
    Args:
        config: Dictionary with 'type' and 'params' keys
        
    Returns:
        Utility instance
        
    Raises:
        ValueError: If utility type is unknown
    """
    warnings.warn(
        "create_utility() is deprecated. Use direct instantiation (UCES, ULinear) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    utype = config['type']
    params = config['params']
    
    if utype == 'ces':
        return UCES(**params)
    elif utype == 'linear':
        return ULinear(**params)
    else:
        raise ValueError(f"Unknown utility type: {utype}")


def u_total(inventory, params: dict) -> float:
    """
    Compute total utility including goods and money (money-aware API).
    
    This is the canonical top-level utility function for Phase 2+.
    
    For Phase 2b: Implements quasilinear money utility.
    Money utility is added as: U_total = U_goods(A, B) + lambda_money * M
    
    Args:
        inventory: Inventory object with A, B, M fields
        params: Scenario parameters dict (must include 'utility' key)
        
    Returns:
        Total utility value
        
    Raises:
        KeyError: If params['utility'] is missing
    """
    if 'utility' not in params:
        raise KeyError("params must contain 'utility' key with Utility instance")
    
    utility_func = params['utility']
    
    # Goods utility
    u_goods_val = utility_func.u_goods(inventory.A, inventory.B)
    
    # Money utility (quasilinear by default)
    # Get lambda_money from params if provided, otherwise use 1.0
    lambda_money = params.get('lambda_money', 1.0)
    u_money = lambda_money * inventory.M
    
    return u_goods_val + u_money

