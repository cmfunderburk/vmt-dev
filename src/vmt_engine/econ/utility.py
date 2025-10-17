"""
Utility functions for agent preferences.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import math


class Utility(ABC):
    """Base interface for utility functions."""
    
    @abstractmethod
    def u(self, A: int, B: int) -> float:
        """
        Compute utility for inventory (A, B).
        
        Args:
            A: Amount of good A
            B: Amount of good B
            
        Returns:
            Utility value
        """
        pass
    
    def mu(self, A: int, B: int) -> tuple[float, float] | None:
        """
        Compute marginal utilities (∂U/∂A, ∂U/∂B).
        
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
        """Compute CES utility."""
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
    
    def mrs_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> float:
        """
        Compute MRS for CES: (wA/wB) * (A/B)^(ρ-1)
        
        Uses zero-safe shift for ratio calculation only when needed.
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
        """
        For CES utility with analytic MRS, reservation bounds are (mrs, mrs).
        """
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
    
    Args:
        config: Dictionary with 'type' and 'params' keys
        
    Returns:
        Utility instance
        
    Raises:
        ValueError: If utility type is unknown
    """
    utype = config['type']
    params = config['params']
    
    if utype == 'ces':
        return UCES(**params)
    elif utype == 'linear':
        return ULinear(**params)
    else:
        raise ValueError(f"Unknown utility type: {utype}")

