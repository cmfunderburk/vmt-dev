"""
Utility functions for agent preferences.

This module contains concrete implementations of the Utility base class.
See base.py for the abstract interface definition.

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
import math
import warnings

from .base import Utility


class UCES(Utility):
    """CES (Constant Elasticity of Substitution) utility function."""
    
    def __init__(self, rho: float, wA: float, wB: float, epsilon: float = 1e-9):
        """
        Initialize CES utility: U = [wA * A^ρ + wB * B^ρ]^(1/ρ)
        
        Args:
            rho: Elasticity parameter (ρ ≠ 1)
            wA: Weight for good A (> 0)
            wB: Weight for good B (> 0)
            epsilon: Small value for zero-safe calculations when rho < 0 (default: 1e-9)
        """
        if rho == 1.0:
            raise ValueError("CES utility cannot have rho=1.0")
        if wA <= 0 or wB <= 0:
            raise ValueError("CES weights must be positive")
        
        self.rho = rho
        self.wA = wA
        self.wB = wB
        self.epsilon = epsilon
    
    def u(self, A: int, B: int) -> float:
        """
        Compute CES utility with epsilon-shift for zero inventories when rho < 0.
        
        For negative rho, x^rho is undefined when x=0 (division by zero).
        We use epsilon-shift: treat A=0 as A=epsilon to get finite utility values.
        
        This ensures agents still value acquiring the first unit of a good.
        """
        if A == 0 and B == 0:
            return 0.0
        
        # Epsilon-shift for zero inventories when rho < 0 to avoid division by zero
        if self.rho < 0:
            A_safe = max(A, self.epsilon)
            B_safe = max(B, self.epsilon)
        else:
            A_safe = A
            B_safe = B
        
        term_A = self.wA * (A_safe ** self.rho) if A_safe > 0 else 0.0
        term_B = self.wB * (B_safe ** self.rho) if B_safe > 0 else 0.0
        
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


class UQuadratic(Utility):
    """Quadratic utility with bliss points and satiation."""
    
    def __init__(self, A_star: float, B_star: float, 
                 sigma_A: float, sigma_B: float, gamma: float = 0.0):
        """
        Initialize quadratic utility: U = -(A-A*)²/σ_A² - (B-B*)²/σ_B² - γ(A-A*)(B-B*)
        
        Args:
            A_star: Bliss point for good A (> 0)
            B_star: Bliss point for good B (> 0)
            sigma_A: Curvature parameter for A (> 0)
            sigma_B: Curvature parameter for B (> 0)
            gamma: Cross-curvature parameter (>= 0, typically < 1)
        
        Raises:
            ValueError: If parameters are invalid
        """
        if A_star <= 0 or B_star <= 0:
            raise ValueError("Bliss points must be positive")
        if sigma_A <= 0 or sigma_B <= 0:
            raise ValueError("Curvature parameters must be positive")
        if gamma < 0:
            raise ValueError("Cross-curvature gamma must be non-negative")
        
        self.A_star = A_star
        self.B_star = B_star
        self.sigma_A = sigma_A
        self.sigma_B = sigma_B
        self.gamma = gamma
    
    def u(self, A: int, B: int) -> float:
        """Compute quadratic utility with bliss points."""
        dA = A - self.A_star
        dB = B - self.B_star
        return -(dA**2 / self.sigma_A**2) - (dB**2 / self.sigma_B**2) - self.gamma * dA * dB
    
    def mu_A(self, A: int, B: int) -> float:
        """Marginal utility of A (can be negative beyond bliss point)."""
        return -2 * (A - self.A_star) / (self.sigma_A**2) - self.gamma * (B - self.B_star)
    
    def mu_B(self, A: int, B: int) -> float:
        """Marginal utility of B (can be negative beyond bliss point)."""
        return -2 * (B - self.B_star) / (self.sigma_B**2) - self.gamma * (A - self.A_star)
    
    def mrs_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> float | None:
        """
        Compute MRS for quadratic utility.
        Returns None if denominator is near zero (at bliss point for B).
        """
        mu_A = self.mu_A(A, B)
        mu_B = self.mu_B(A, B)
        
        if abs(mu_B) < eps:
            return None  # Undefined MRS near bliss point
        
        return mu_A / mu_B
    
    def reservation_bounds_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> tuple[float, float]:
        """
        Compute reservation bounds for quadratic utility.
        
        Special handling:
        - If MU_A <= 0: Agent wants to reduce A → willing to sell at any positive price (p_min = eps)
        - If MU_B <= 0: Agent wants to reduce B → willing to pay very high price (p_max = large)
        - If both MU <= 0: Agent won't trade in this direction
        """
        mu_A = self.mu_A(A, B)
        mu_B = self.mu_B(A, B)
        
        # If both marginal utilities are non-positive, no beneficial trade exists
        if mu_A <= 0 and mu_B <= 0:
            return (float('inf'), 0.0)  # No feasible trade: p_min > p_max
        
        # Standard case: both MU positive
        if mu_A > 0 and mu_B > 0:
            mrs = mu_A / mu_B
            return (mrs, mrs)
        
        # Agent wants to give away A (MU_A <= 0)
        if mu_A <= 0:
            return (eps, eps)  # Willing to sell A at any small positive price
        
        # Agent wants to give away B (MU_B <= 0)
        if mu_B <= 0:
            return (1e6, 1e6)  # Willing to pay huge amount of B for A
        
        # Fallback (should not reach here)
        mrs = self.mrs_A_in_B(A, B, eps)
        if mrs is None:
            return (1.0, 1.0)  # Neutral if undefined
        return (mrs, mrs)


class UTranslog(Utility):
    """Translog (transcendental logarithmic) utility function."""
    
    def __init__(self, alpha_0: float, alpha_A: float, alpha_B: float,
                 beta_AA: float, beta_BB: float, beta_AB: float):
        """
        Initialize translog utility:
        ln U = α₀ + α_A·ln(A) + α_B·ln(B) + (1/2)β_AA·[ln(A)]² + (1/2)β_BB·[ln(B)]² + β_AB·ln(A)·ln(B)
        
        Args:
            alpha_0: Constant term
            alpha_A: First-order coefficient for A (> 0 for monotonicity)
            alpha_B: First-order coefficient for B (> 0 for monotonicity)
            beta_AA: Second-order coefficient for A
            beta_BB: Second-order coefficient for B
            beta_AB: Cross-partial coefficient (interaction term)
        
        Raises:
            ValueError: If first-order coefficients are non-positive
        """
        if alpha_A <= 0 or alpha_B <= 0:
            raise ValueError("First-order coefficients must be positive for monotonicity")
        
        self.alpha_0 = alpha_0
        self.alpha_A = alpha_A
        self.alpha_B = alpha_B
        self.beta_AA = beta_AA
        self.beta_BB = beta_BB
        self.beta_AB = beta_AB
    
    def _ln_u(self, A: int, B: int, eps: float = 1e-12) -> float:
        """
        Compute ln(U) instead of U to avoid numerical overflow.
        This is the canonical representation for translog.
        """
        # Zero-safe logarithms
        ln_A = math.log(max(A, eps))
        ln_B = math.log(max(B, eps))
        
        return (self.alpha_0 
                + self.alpha_A * ln_A 
                + self.alpha_B * ln_B
                + 0.5 * self.beta_AA * ln_A**2
                + 0.5 * self.beta_BB * ln_B**2
                + self.beta_AB * ln_A * ln_B)
    
    def u(self, A: int, B: int) -> float:
        """
        Compute utility (exponential of ln U).
        
        Note: For very large ln_u, exp() can overflow. Consider capping or 
        warning if ln_u > 700 (approx limit for float64).
        """
        ln_u = self._ln_u(A, B)
        
        # Overflow protection
        if ln_u > 700:
            warnings.warn(f"Translog ln(U) = {ln_u:.2f} exceeds safe exp() range. Capping at 700.")
            ln_u = 700
        
        return math.exp(ln_u)
    
    def _d_ln_u_dA(self, A: int, B: int, eps: float = 1e-12) -> float:
        """Compute ∂[ln U]/∂A = (α_A + β_AA·ln(A) + β_AB·ln(B)) / A"""
        A_safe = max(A, eps)
        B_safe = max(B, eps)
        ln_A = math.log(A_safe)
        ln_B = math.log(B_safe)
        
        return (self.alpha_A + self.beta_AA * ln_A + self.beta_AB * ln_B) / A_safe
    
    def _d_ln_u_dB(self, A: int, B: int, eps: float = 1e-12) -> float:
        """Compute ∂[ln U]/∂B = (α_B + β_BB·ln(B) + β_AB·ln(A)) / B"""
        A_safe = max(A, eps)
        B_safe = max(B, eps)
        ln_A = math.log(A_safe)
        ln_B = math.log(B_safe)
        
        return (self.alpha_B + self.beta_BB * ln_B + self.beta_AB * ln_A) / B_safe
    
    def mu_A(self, A: int, B: int) -> float:
        """
        Marginal utility of A.
        MU_A = U · ∂[ln U]/∂A
        
        For quoting/trading, we can work with ∂[ln U]/∂A directly,
        but for consistency with the Utility interface, we return the full MU.
        """
        U = self.u(A, B)
        d_ln_u = self._d_ln_u_dA(A, B)
        return U * d_ln_u
    
    def mu_B(self, A: int, B: int) -> float:
        """Marginal utility of B."""
        U = self.u(A, B)
        d_ln_u = self._d_ln_u_dB(A, B)
        return U * d_ln_u
    
    def mrs_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> float:
        """
        Compute MRS = MU_A / MU_B.
        
        Since MU_i = U · ∂[ln U]/∂i, the U cancels:
        MRS = ∂[ln U]/∂A / ∂[ln U]/∂B
        
        This avoids computing exp() and is numerically stable.
        """
        d_ln_u_A = self._d_ln_u_dA(A, B, eps)
        d_ln_u_B = self._d_ln_u_dB(A, B, eps)
        
        if abs(d_ln_u_B) < eps:
            # Denominator near zero; use large default MRS
            return 1e6 if d_ln_u_A > 0 else eps
        
        return d_ln_u_A / d_ln_u_B
    
    def reservation_bounds_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> tuple[float, float]:
        """
        For translog with positive first-order coefficients, MRS is always well-defined and positive.
        Reservation bounds are (mrs, mrs).
        """
        mrs = self.mrs_A_in_B(A, B, eps)
        return (mrs, mrs)


class UStoneGeary(Utility):
    """Stone-Geary utility with subsistence constraints."""
    
    def __init__(self, alpha_A: float, alpha_B: float, 
                 gamma_A: float, gamma_B: float):
        """
        Initialize Stone-Geary utility: U = α_A·ln(A - γ_A) + α_B·ln(B - γ_B)
        
        Args:
            alpha_A: Preference weight for A (> 0)
            alpha_B: Preference weight for B (> 0)
            gamma_A: Subsistence level for A (>= 0)
            gamma_B: Subsistence level for B (>= 0)
        
        Raises:
            ValueError: If parameters are invalid
        """
        if alpha_A <= 0 or alpha_B <= 0:
            raise ValueError("Preference weights must be positive")
        if gamma_A < 0 or gamma_B < 0:
            raise ValueError("Subsistence levels must be non-negative")
        
        self.alpha_A = alpha_A
        self.alpha_B = alpha_B
        self.gamma_A = gamma_A
        self.gamma_B = gamma_B
        
        # Store epsilon for consistent zero-handling
        self.epsilon = 1e-12
    
    def u(self, A: int, B: int) -> float:
        """
        Compute Stone-Geary utility.
        
        Uses epsilon-shift to handle A ≤ γ_A or B ≤ γ_B cases gracefully.
        Returns very negative (but finite) utility when below subsistence.
        """
        A_above = max(A - self.gamma_A, self.epsilon)
        B_above = max(B - self.gamma_B, self.epsilon)
        
        return self.alpha_A * math.log(A_above) + self.alpha_B * math.log(B_above)
    
    def mu_A(self, A: int, B: int) -> float:
        """
        Marginal utility of A: MU_A = α_A / (A - γ_A)
        
        Uses epsilon-shift for safety when A ≤ γ_A.
        """
        A_above = max(A - self.gamma_A, self.epsilon)
        return self.alpha_A / A_above
    
    def mu_B(self, A: int, B: int) -> float:
        """
        Marginal utility of B: MU_B = α_B / (B - γ_B)
        
        Uses epsilon-shift for safety when B ≤ γ_B.
        """
        B_above = max(B - self.gamma_B, self.epsilon)
        return self.alpha_B / B_above
    
    def mrs_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> float:
        """
        Compute MRS for Stone-Geary utility.
        
        MRS = [α_A · (B - γ_B)] / [α_B · (A - γ_A)]
        
        Uses epsilon-shift to handle subsistence boundaries.
        """
        A_above = max(A - self.gamma_A, eps)
        B_above = max(B - self.gamma_B, eps)
        
        return (self.alpha_A * B_above) / (self.alpha_B * A_above)
    
    def reservation_bounds_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> tuple[float, float]:
        """
        Compute reservation bounds for Stone-Geary utility.
        
        Special handling for subsistence violations:
        - If A ≤ γ_A: Agent desperate for A, willing to pay very high price
        - If B ≤ γ_B: Agent cannot spare B, demands very high price for A
        - Otherwise: Standard MRS-based bounds
        """
        # Check if below subsistence (with small tolerance for numerical safety)
        below_A = (A - self.gamma_A) < eps
        below_B = (B - self.gamma_B) < eps
        
        if below_A and below_B:
            # Below subsistence in both: indeterminate, use neutral default
            return (1.0, 1.0)
        elif below_A:
            # Below subsistence in A only: desperate buyer
            return (1e6, 1e6)
        elif below_B:
            # Below subsistence in B only: cannot sell A (need to acquire B)
            # Could also refuse trade: return (float('inf'), 0.0)
            return (1e6, 1e6)
        
        # Normal case: both goods above subsistence
        mrs = self.mrs_A_in_B(A, B, eps)
        return (mrs, mrs)
    
    def is_above_subsistence(self, A: int, B: int, eps: float = 1e-12) -> bool:
        """
        Helper method to check if agent is above subsistence in both goods.
        
        Useful for decision logic or telemetry.
        """
        return (A - self.gamma_A) > eps and (B - self.gamma_B) > eps


def create_utility(config: dict) -> Utility:
    """
    Create utility instance from scenario configuration dictionary.
    
    This is the standard factory function used by the scenario loading system
    to dynamically instantiate utilities from YAML files. It maps string type
    names ("ces", "linear", "quadratic", "translog", "stone_geary") to their
    corresponding utility classes.
    
    For programmatic use when not loading from YAML, direct class instantiation
    may be more explicit:
        utility = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0)
    
    Args:
        config: Dictionary with 'type' and 'params' keys
            type: Utility type string (e.g., "quadratic", "translog")
            params: Dict of parameters for the chosen utility type
        
    Returns:
        Utility instance of the appropriate class
        
    Raises:
        ValueError: If utility type is unknown
    """
    utype = config['type']
    params = config['params']
    
    if utype == 'ces':
        return UCES(**params)
    elif utype == 'linear':
        return ULinear(**params)
    elif utype == 'quadratic':
        return UQuadratic(**params)
    elif utype == 'translog':
        return UTranslog(**params)
    elif utype == 'stone_geary':
        return UStoneGeary(**params)
    else:
        raise ValueError(f"Unknown utility type: {utype}")


def mu_money(M: int, lambda_money: float, money_utility_form: str = "linear", 
             M_0: float = 0.0, epsilon: float = 1e-12) -> float:
    """
    Compute marginal utility of money.
    
    Supports two functional forms:
    - linear: ∂U/∂M = λ (constant)
    - log: ∂U/∂M = λ/(M + M_0) (diminishing)
    
    Args:
        M: Money holdings (integer, in minor units)
        lambda_money: Base marginal utility parameter (λ)
        money_utility_form: "linear" or "log"
        M_0: Shift parameter for log form (subsistence money)
        epsilon: Guard against log(0) when M=0 and M_0=0
        
    Returns:
        Marginal utility of money (∂U/∂M)
        
    Raises:
        ValueError: If money_utility_form is not recognized
    """
    if money_utility_form == "linear":
        return lambda_money
    elif money_utility_form == "log":
        return lambda_money / max(M + M_0, epsilon)
    else:
        raise ValueError(f"Unknown money_utility_form: {money_utility_form}")


def u_total(inventory, params: dict) -> float:
    """
    Compute total utility including goods and money (money-aware API).
    
    This is the canonical top-level utility function for Phase 2+.
    
    Supports two money utility forms:
    - linear: U = U_goods(A,B) + λ·M
    - log: U = U_goods(A,B) + λ·log(M + M_0)
    
    Args:
        inventory: Inventory object with A, B, M fields
        params: Dict with keys:
            - 'utility': Utility instance for goods
            - 'lambda_money': λ parameter (default: 1.0)
            - 'money_utility_form': "linear" or "log" (default: "linear")
            - 'M_0': Shift parameter for log form (default: 0.0)
            - 'epsilon': Small value for zero-safe calculations (default: 1e-12)
            
    Returns:
        Total utility value
        
    Raises:
        KeyError: If params['utility'] is missing
        ValueError: If money_utility_form is not recognized
    """
    if 'utility' not in params:
        raise KeyError("params must contain 'utility' key with Utility instance")
    
    utility_func = params['utility']
    
    # Goods utility
    u_goods_val = utility_func.u_goods(inventory.A, inventory.B)
    
    # Money utility
    lambda_money = params.get('lambda_money', 1.0)
    money_form = params.get('money_utility_form', 'linear')
    M_0 = params.get('M_0', 0.0)
    epsilon = params.get('epsilon', 1e-12)
    
    if money_form == 'linear':
        u_money = lambda_money * inventory.M
    elif money_form == 'log':
        u_money = lambda_money * math.log(max(inventory.M + M_0, epsilon))
    else:
        raise ValueError(f"Unknown money_utility_form: {money_form}")
    
    return u_goods_val + u_money

