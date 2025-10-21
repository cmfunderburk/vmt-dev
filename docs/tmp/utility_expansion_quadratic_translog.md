# VMT Utility Function Expansion: Quadratic, Translog, and Stone-Geary

**Document Type:** Planning & Design Brainstorm  
**Date:** 2025-10-21  
**Status:** Draft / Brainstorming  
**Revision:** 2025-10-21 - Expanded to include Stone-Geary utility

---

## Executive Summary

This document proposes the addition of three new utility functions to the VMT simulation framework: **quadratic**, **translog**, and **Stone-Geary**. These additions would significantly expand the project's analytical power and pedagogical value by enabling demonstrations of diverse economic phenomena.

**Key Benefits:**
- **Quadratic**: Enables demonstrations of non-monotonic preferences, satiation, and bliss points — crucial for advanced microeconomic pedagogy
- **Translog**: Provides a flexible second-order Taylor approximation widely used in empirical economics and production function estimation
- **Stone-Geary**: Demonstrates subsistence constraints and hierarchical needs, foundation of the Linear Expenditure System (LES) used in applied demand analysis
- **Combined**: Dramatically increases the scope of economic phenomena that can be modeled within VMT, from basic needs to satiation to flexible empirical specifications

---

## Part 1: Mathematical Foundations

### 1.1 Quadratic Utility Function

#### Functional Form
The general quadratic utility function over two goods takes the form:

```
U(A, B) = α₀ + α_A·A + α_B·B + β_AA·A² + β_BB·B² + β_AB·A·B
```

For practical implementation in VMT, we propose a **canonical bliss-point form**:

```
U(A, B) = -(A - A*)²/σ_A² - (B - B*)²/σ_B² - γ·(A - A*)·(B - B*)
```

Where:
- `A*`, `B*` are the **bliss points** (optimal consumption bundles)
- `σ_A`, `σ_B` are **curvature parameters** controlling satiation rates
- `γ` is the **cross-curvature parameter** controlling interaction effects (typically ∈ [0, 1])

**Alternative parametrization** (for zero-centered preferences):
```
U(A, B) = α_A·A + α_B·B - β_A·A² - β_B·B² - β_AB·A·B
```
where `α_A, α_B > 0` and `β_A, β_B, β_AB ≥ 0`.

#### Economic Properties
1. **Non-monotonicity**: Utility can decrease with additional consumption beyond bliss points
2. **Satiation**: Marginal utility declines linearly and becomes negative
3. **Interiority**: Optimal bundles are typically interior (not corner solutions)
4. **Pedagogical value**: Excellent for demonstrating:
   - Consumer surplus with satiation
   - Non-convex preferences (if cross-terms dominate)
   - Giffen good behavior under certain conditions

#### Marginal Utilities
For the bliss-point form:
```
MU_A = ∂U/∂A = -2(A - A*)/σ_A² - γ(B - B*)
MU_B = ∂U/∂B = -2(B - B*)/σ_B² - γ(A - A*)
```

**Critical consideration**: Marginal utilities can be **negative** beyond bliss points. This requires careful handling:
- Quote computation must check for negative MU and either:
  - Refuse to trade (no quotes generated), or
  - Generate quotes only for reducing inventory
- MRS becomes negative in certain regions, requiring special logic

#### MRS and Trading Behavior
```
MRS_A_in_B = MU_A / MU_B = [2(A - A*)/σ_A² + γ(B - B*)] / [2(B - B*)/σ_B² + γ(A - A*)]
```

**Special cases requiring handling:**
1. When agent is at bliss point: `MU_A = MU_B = 0` → no incentive to trade
2. When agent is beyond bliss point in one good: may want to give away excess
3. Denominators can approach zero near bliss points

---

### 1.2 Translog Utility Function

#### Functional Form
The **transcendental logarithmic** (translog) utility function is:

```
ln U(A, B) = α₀ + α_A·ln(A) + α_B·ln(B) 
             + (1/2)·β_AA·[ln(A)]² + (1/2)·β_BB·[ln(B)]² 
             + β_AB·ln(A)·ln(B)
```

Or equivalently:
```
U(A, B) = exp(α₀ + α_A·ln(A) + α_B·ln(B) 
              + (1/2)·β_AA·[ln(A)]² + (1/2)·β_BB·[ln(B)]² 
              + β_AB·ln(A)·ln(B))
```

For numerical stability and practical use, we can work with `ln U` directly:
```
V(A, B) = ln U(A, B) = α₀ + α_A·ln(A) + α_B·ln(B) 
                       + (1/2)·β_AA·[ln(A)]² + (1/2)·β_BB·[ln(B)]²
                       + β_AB·ln(A)·ln(B)
```

#### Economic Properties
1. **Flexible functional form**: Second-order Taylor approximation to any arbitrary utility function in log space
2. **Widely used empirically**: Standard in production function estimation (duality with cost functions)
3. **Nested structures**: Can approximate Cobb-Douglas (when β terms = 0) and CES under restrictions
4. **Monotonicity**: Always increasing in both goods (unlike quadratic) when properly parameterized
5. **Variable elasticity of substitution**: Unlike CES, the elasticity can vary with consumption levels
6. **Regularity conditions**: Must satisfy symmetry (β_AB already symmetric) and curvature restrictions for well-behaved preferences

#### Computational Complexity Analysis

**Operations count** (compared to existing utility functions):
- **Linear**: 2 multiplications, 1 addition (trivial)
- **CES**: Multiple exponentiations (`A^ρ`, `B^ρ`, total`^(1/ρ)`), computationally heavier
- **Translog**: 2 `ln()` calls, 5 multiplications, 5 additions

**Performance verdict**: Logarithms are fast on modern processors. Translog is slightly more expensive than CES per evaluation, but unlikely to be a bottleneck. The main simulation costs are agent interactions (O(N) in decision phase with spatial indexing) and compensating block search, not raw utility calculation.

**Comparison to existing bottlenecks**:
- Spatial queries: O(N) per agent with bucket-based spatial index
- Compensating block search: O(dA_max × price_candidates) per trade attempt
- Translog utility: O(1) with ~10 operations

**Conclusion**: Computational cost is **acceptable and comparable to CES**.

#### Marginal Utilities
Using the chain rule on `V(A, B) = ln U(A, B)`:

```
MU_A = (∂U/∂A) = U · (∂V/∂A) = U · [α_A/A + β_AA·ln(A)/A + β_AB·ln(B)/A]
MU_B = (∂U/∂B) = U · (∂V/∂B) = U · [α_B/B + β_BB·ln(B)/B + β_AB·ln(A)/B]
```

Simplifying (since only the ratio matters for MRS):
```
∂V/∂A = (α_A + β_AA·ln(A) + β_AB·ln(B)) / A
∂V/∂B = (α_B + β_BB·ln(B) + β_AB·ln(A)) / B
```

**Key insight for implementation**: Work with `∂V/∂A` and `∂V/∂B` rather than full marginal utilities. This:
- Avoids computing `exp(V)` which can overflow
- Gives correct MRS (the `U` factors cancel)
- Maintains monotonicity checks (sign of `∂V/∂A` equals sign of `MU_A`)

#### MRS and Trading Behavior
```
MRS_A_in_B = MU_A / MU_B = [α_A + β_AA·ln(A) + β_AB·ln(B)] · B / 
                            [α_B + β_BB·ln(B) + β_AB·ln(A)] · A
```

**Practical simplification**: For quoting and trading, work entirely with `V(A, B)` and its derivatives:
```
MRS_A_in_B = (∂V/∂A) / (∂V/∂B)
```

This avoids computing the exponential entirely.

#### Special Considerations

**1. Zero Handling (The `ln(0)` Problem)**:
- Standard VMT approach: Use `max(A, epsilon)` only where division by zero or log of zero would occur
- For translog: Replace `ln(A)` with `ln(max(A, epsilon))` throughout
- Use existing `epsilon` parameter from `ScenarioParams` (default: 1e-12)
- Apply consistently in both `V(A, B)` calculation and derivative calculations

**2. Monotonicity Over Goods Range (1-1000)**:
Logarithm behavior:
- `ln(1) = 0.0`
- `ln(10) ≈ 2.3`
- `ln(100) ≈ 4.6`
- `ln(1000) ≈ 6.9`

For monotonicity, need `∂V/∂A > 0` over the range:
```
∂V/∂A = (α_A + β_AA·ln(A) + β_AB·ln(B)) / A > 0
```

This requires:
```
α_A + β_AA·ln(A) + β_AB·ln(B) > 0  for all A, B in [1, 1000]
```

**Implications**:
- If `β_AA < 0` (typical for diminishing returns), need `α_A` large enough to keep derivative positive
- For `A = 1000, B = 1000`: Need `α_A + 6.9·β_AA + 6.9·β_AB > 0`
- **Solution**: Provide parameter presets and validation in GUI; document "safe" parameter ranges

**3. Quasi-concavity (Convex Indifference Curves)**:
Requires Hessian of `V(A, B)` to be negative semi-definite. This imposes restrictions on β parameters:
- `β_AA, β_BB < 0` generally helps
- `β_AB^2 < β_AA · β_BB` (determinant condition)

**Implementation strategy**: 
- Phase 1: Document expected parameter ranges, provide tested examples
- Phase 5: Add optional validation checks for monotonicity and quasi-concavity

**4. Parameter Interpretation**:
- `α₀`: Scaling constant (doesn't affect MRS, can normalize to 0)
- `α_A, α_B`: First-order preferences (like Cobb-Douglas exponents)
- `β_AA, β_BB`: Own-curvature (negative = diminishing MU faster than log alone)
- `β_AB`: Cross-curvature (positive = complementarity, negative = substitutability)

**Practical parameterization**:
- Start with Cobb-Douglas (`β = 0`) and add small β terms for flexibility
- Test parameter sets over inventory range [0, 1000] to ensure reasonable MRS values
- GUI should provide presets: "Cobb-Douglas nested", "Weak complements", "Flexible substitutes"

#### Educational Value

**Pedagogical positioning**:
- **Not intuitive**: Parameters lack simple economic interpretation compared to CES
- **Best use cases**:
  - Demonstrate limitations of simpler functional forms (CES has constant elasticity, translog doesn't)
  - Show how elasticity of substitution varies with consumption levels
  - Advanced/research scenarios where empirical realism matters
  - Parameter estimation exercises (generate data, estimate translog coefficients)

**Teaching strategy**:
- Introduce *after* students understand CES and linear
- Focus on its role as a "flexible approximation" that can fit diverse behaviors
- Use comparative scenarios: same agents, CES vs. translog, show different trading patterns
- Emphasize empirical applications (production functions, demand systems)

---

### 1.3 Stone-Geary Utility Function

#### Functional Form

The **Stone-Geary utility function** incorporates subsistence levels — minimum quantities required before additional consumption provides utility. We implement the **logarithmic form** for consistency with VMT's CES/Cobb-Douglas patterns:

```
U(A, B) = α_A · ln(A - γ_A) + α_B · ln(B - γ_B)
```

where:
- `γ_A, γ_B ≥ 0` are **subsistence levels** (minimum required quantities)
- `α_A, α_B > 0` are **preference weights** for goods beyond subsistence
- Requires `A > γ_A` and `B > γ_B` for well-defined utility

**Alternative power form** (Cobb-Douglas-like):
```
U(A, B) = (A - γ_A)^α · (B - γ_B)^(1-α)
```

**Recommendation**: Use logarithmic form to avoid potential overflow with large inventories and maintain consistency with existing VMT patterns.

#### Economic Properties

1. **Subsistence constraints**: Utility is undefined (or -∞) below minimum thresholds
2. **Hierarchy of needs**: Agents prioritize reaching subsistence before optimizing
3. **Nests Cobb-Douglas**: When `γ_A = γ_B = 0`, reduces exactly to Cobb-Douglas (which in turn is a limit case of CES)
4. **Linear Expenditure System (LES)**: Stone-Geary is the direct utility function underlying LES demand
5. **Income effects**: Behavior differs dramatically above vs. below subsistence
6. **Real-world applicability**: Models basic needs (food, shelter) vs. discretionary consumption

#### Marginal Utilities

For the logarithmic form:

```
MU_A = ∂U/∂A = α_A / (A - γ_A)
MU_B = ∂U/∂B = α_B / (B - γ_B)
```

**Key properties**:
- `MU → ∞` as inventory approaches subsistence from above (desperate to avoid starvation)
- `MU → 0` as inventory → ∞ (standard diminishing marginal utility)
- Always positive and well-defined for `A > γ_A, B > γ_B`
- Hyperbolic decay (faster than logarithmic Cobb-Douglas near subsistence)

#### MRS and Trading Behavior

```
MRS_A_in_B = MU_A / MU_B = [α_A / (A - γ_A)] / [α_B / (B - γ_B)]
           = [α_A · (B - γ_B)] / [α_B · (A - γ_A)]
```

**Trading implications**:
- **Below subsistence in A**: Agent has very high MRS (willing to pay enormous amounts of B for A)
- **At subsistence in A**: MRS → ∞ (would trade anything for one more unit of A)
- **Far above subsistence**: MRS stabilizes, behaves like Cobb-Douglas
- **Asymmetric subsistence**: Agent with `A = γ_A + 1, B = 100` trades very differently than agent with `A = 100, B = γ_B + 1`

**Example**:
```
Agent with γ_A = 5, γ_B = 3, α_A = 0.6, α_B = 0.4
- At (A=6, B=10): MRS = [0.6·7]/[0.4·1] = 10.5 (desperate for A)
- At (A=10, B=10): MRS = [0.6·7]/[0.4·5] = 2.1 (stable)
- At (A=50, B=50): MRS = [0.6·47]/[0.4·45] ≈ 1.57 (approaching Cobb-Douglas)
```

#### Reservation Bounds

With analytic MRS, reservation bounds are straightforward in the normal region:

```python
def reservation_bounds_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> tuple[float, float]:
    """
    Reservation bounds for Stone-Geary utility.
    
    Special handling when below subsistence:
    - If A <= γ_A: Agent desperately needs A, willing to pay huge price
    - If B <= γ_B: Agent cannot spare B, will demand very high price for A
    """
    # Check subsistence constraints
    if A <= self.gamma_A or B <= self.gamma_B:
        if A <= self.gamma_A and B > self.gamma_B:
            # Below subsistence in A only: desperate buyer
            return (1e6, 1e6)
        elif A > self.gamma_A and B <= self.gamma_B:
            # Below subsistence in B only: won't sell A
            return (1e6, 1e6)  # Or could refuse trade: (float('inf'), 0.0)
        else:
            # Below subsistence in both: undefined/desperate
            # Agent would trade whichever good brings them toward subsistence
            return (1.0, 1.0)  # Neutral default
    
    # Normal case: both goods above subsistence
    mrs = self.mrs_A_in_B(A, B, eps)
    return (mrs, mrs)
```

#### Special Considerations

**1. Subsistence Violation Handling**:

When `A ≤ γ_A` or `B ≤ γ_B`, utility is undefined. Several implementation options:

- **Option A**: Return large negative utility (e.g., `-1e9`) to signal "desperate" state
- **Option B**: Return `-inf` (mathematically correct for log form)
- **Option C**: Epsilon-shift: compute `ln(max(A - γ_A, epsilon))`

**Recommendation**: Use Option C (epsilon-shift) for consistency with CES/translog zero-handling:
```python
def u(self, A: int, B: int) -> float:
    A_above = max(A - self.gamma_A, self.epsilon)
    B_above = max(B - self.gamma_B, self.epsilon)
    return self.alpha_A * math.log(A_above) + self.alpha_B * math.log(B_above)
```

This gives finite (though very negative) utility when below subsistence, allowing agents to still compute MRS and potentially trade toward subsistence.

**2. Initial Inventory Constraints**:

Scenarios using Stone-Geary **must** ensure initial inventories satisfy:
```
A_initial > γ_A
B_initial > γ_B
```

**Implementation**:
- Add validation in scenario loader: if Stone-Geary utility, check inventory constraints
- Provide clear error message if violated
- Document requirement in YAML schema comments

**3. Zero Handling (Combined with Subsistence)**:

When exactly at subsistence (e.g., `A = γ_A`), both issues arise:
- `A - γ_A = 0` (subsistence problem)
- `ln(0)` undefined (zero problem)

Epsilon-shift solves both:
```python
A_safe = max(A - self.gamma_A, eps)
```

**4. Parameter Validation**:

Must enforce during initialization:
- `γ_A, γ_B ≥ 0`
- `α_A, α_B > 0`
- Ideally: `γ_A, γ_B` should be less than typical inventory levels (e.g., `< 50` for inventories up to 1000)

**5. Relationship to Money/Quasi-linearity**:

Stone-Geary naturally extends to quasi-linear preferences when one good has `γ = 0` and `α = 1`:
```
U(A, B) = α_A · ln(A - γ_A) + B
```

This could be a future extension (Phase 5) as "quasi-linear Stone-Geary."

#### Pedagogical Value

**Stone-Geary offers exceptional teaching opportunities**:

1. **Hierarchy of needs**: Demonstrate Maslow-like prioritization
   - Agents below subsistence trade desperately, accept unfavorable prices
   - Agents above subsistence trade normally
   
2. **Development economics**: Model basic needs vs. luxury goods
   - Low-endowment agents focused on survival
   - High-endowment agents optimize leisure/variety
   
3. **Inequality and welfare**: 
   - Show how same price change affects agents differently based on distance from subsistence
   - Demonstrate welfare implications of redistribution
   
4. **Market segmentation**:
   - Agents cluster into "subsistence traders" (high MRS) and "normal traders" (stable MRS)
   - Price discrimination opportunities emerge naturally
   
5. **Applied demand analysis**:
   - LES is widely used in CGE (Computable General Equilibrium) models
   - Students can connect VMT to real-world policy analysis
   
6. **Nesting relationships**:
   - Start with Cobb-Douglas (`γ = 0`)
   - Add subsistence constraints to show richer behavior
   - Demonstrates value of model generalization

#### Empirical Applications

**Linear Expenditure System (LES)**:

Stone-Geary utility generates LES demand:
```
p_A · q_A = p_A · γ_A + α_A · (M - p_A·γ_A - p_B·γ_B)
p_B · q_B = p_B · γ_B + α_B · (M - p_A·γ_A - p_B·γ_B)
```

where `M` is total expenditure. This shows:
- First term: committed expenditure on subsistence
- Second term: discretionary income allocated by preference weights

**Estimation potential**:
- Generate VMT trade data with Stone-Geary agents
- Students can estimate `γ` and `α` parameters from observed trade patterns
- Compare estimated vs. true parameters to validate simulation

---

## Part 2: Benefits for the VMT Project

### 2.1 Pedagogical Value

#### Quadratic Utility
- **Demonstrate bliss points**: Show students that "more is not always better"
- **Non-monotonic preferences**: Visualize agents who want to *reduce* holdings of certain goods
- **Gift-giving behavior**: Agents may offer goods at negative prices (pay to give away excess)
- **Market dynamics with satiation**: Explore price formation when some agents have negative marginal utility
- **Consumer theory edge cases**: Demonstrate Giffen-like behavior, corner solutions transitioning to interior, etc.

#### Translog Utility
- **Empirical realism**: Bridge pedagogical models and real-world estimation
- **Flexible substitution**: Second-order flexibility allows richer substitution patterns than CES
- **Variable elasticity**: Show how elasticity of substitution changes with consumption levels (unlike CES)
- **Nested testing**: Students can test whether Cobb-Douglas (β=0) or other special cases fit simulated data
- **Production function duality**: Since translog is standard in production theory, VMT can demonstrate duality principles
- **Limitations of simple forms**: Use as teaching tool to show what CES/Linear cannot capture

#### Stone-Geary Utility
- **Hierarchy of needs**: Demonstrate Maslow-like behavior with subsistence priorities
- **Survival vs. optimization**: Show stark difference between agents below and above subsistence
- **Development economics**: Model basic needs (food, shelter) vs. discretionary consumption
- **Inequality visualization**: Same price affects rich and poor agents dramatically differently
- **Market segmentation**: Agents naturally cluster into "subsistence traders" and "normal traders"
- **Applied CGE modeling**: LES is widely used in Computable General Equilibrium models — students connect VMT to policy analysis
- **Income effects**: Demonstrate strong income effects near subsistence, weak effects far above

### 2.2 Research & Analytical Power

#### Quadratic Utility
- **Heterogeneous preferences**: Mix quadratic and CES/linear agents to study how satiation affects market dynamics
- **Trading volume**: Agents with satiation may trade less frequently → study liquidity effects
- **Spatial clustering**: Agents might cluster around high-resource cells to maintain bliss-point inventories
- **Stability analysis**: Test if markets clear efficiently when some agents refuse trades
- **Demand reversal**: Study situations where agents become suppliers of goods they previously demanded

#### Translog Utility
- **Estimation exercises**: Generate synthetic data, then estimate translog parameters to validate simulation methods
- **Welfare analysis**: More realistic welfare calculations for policy experiments
- **Comparative statics**: Study how second-order terms affect trade patterns vs. first-order (linear/Cobb-Douglas)
- **Production-consumption duality**: Model both sides of the market with same functional form
- **Functional form testing**: Generate data with translog, test if CES provides adequate fit (specification tests)
- **Elasticity heterogeneity**: Study how agents with different elasticities at different consumption levels interact

#### Stone-Geary Utility
- **Subsistence economies**: Model and study markets where basic needs dominate
- **Redistribution experiments**: Test welfare effects of transfers from rich to poor agents
- **Price shock analysis**: Study differential impacts when staple goods vs. luxury goods change prices
- **Poverty traps**: Investigate whether agents below subsistence can trade their way out
- **Market power**: Agents with subsistence constraints have less bargaining power — quantify exploitation
- **Empirical calibration**: Use real-world LES estimates to calibrate agent preferences for realistic simulations
- **Policy evaluation**: Test policies like basic income, price subsidies on staples, progressive taxation

### 2.3 Codebase Maturity & Extensibility

Adding these three functions demonstrates that VMT's architecture is:
- **Modular**: New utility functions slot in cleanly without core engine changes
- **Rigorous**: Each function properly implements `u_goods()`, `mu_A()`, `mu_B()`, `mrs_A_in_B()`, `reservation_bounds_A_in_B()`
- **Production-ready**: Comprehensive testing, edge case handling, and documentation
- **Diverse**: Handles functions with very different properties (non-monotonic, flexible, subsistence-constrained)

This expansion validates the **Utility ABC design pattern** and sets precedent for future additions (e.g., Leontief for perfect complements, quasi-linear for partial equilibrium, CRRA for risk analysis).

**Specific architectural validations**:
- **Quadratic**: Tests handling of undefined/negative MRS, agents refusing trades
- **Translog**: Tests numerical stability (overflow protection), working in log-space
- **Stone-Geary**: Tests parameter-dependent constraints (subsistence validation), epsilon-shifting for safety

---

## Part 3: Implementation Plan

### 3.1 Core Utility Classes

#### File: `src/vmt_engine/econ/utility.py`

**New class: `UQuadratic`**

```python
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
```

**New class: `UTranslog`**

```python
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
```

**New class: `UStoneGeary`**

```python
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
```

---

### 3.2 Schema Extensions

#### File: `src/scenarios/schema.py`

Update `UtilityConfig` to support new types:

```python
@dataclass
class UtilityConfig:
    """Configuration for a utility function."""
    type: Literal["ces", "linear", "quadratic", "translog", "stone_geary"]  # Add new types
    weight: float
    params: dict[str, float]
```

#### YAML Schema Documentation

Update `docs/4_typing_overview.md` to document new parameters:

**Quadratic parameters:**
```yaml
type: "quadratic"
params:
  A_star: float    # Bliss point for A (> 0)
  B_star: float    # Bliss point for B (> 0)
  sigma_A: float   # Curvature for A (> 0)
  sigma_B: float   # Curvature for B (> 0)
  gamma: float     # Cross-curvature (>= 0, default 0.0)
```

**Translog parameters:**
```yaml
type: "translog"
params:
  alpha_0: float   # Constant term
  alpha_A: float   # First-order A (> 0)
  alpha_B: float   # First-order B (> 0)
  beta_AA: float   # Second-order A
  beta_BB: float   # Second-order B
  beta_AB: float   # Interaction term
```

**Stone-Geary parameters:**
```yaml
type: "stone_geary"
params:
  alpha_A: float   # Preference weight for A (> 0)
  alpha_B: float   # Preference weight for B (> 0)
  gamma_A: float   # Subsistence level for A (>= 0, must be < initial inventory)
  gamma_B: float   # Subsistence level for B (>= 0, must be < initial inventory)
```

---

### 3.3 Factory Function Update

Update `create_utility()` in `src/vmt_engine/econ/utility.py`:

```python
def create_utility(config: dict) -> Utility:
    """Factory function to create utility from configuration."""
    warnings.warn(
        "create_utility() is deprecated. Use direct instantiation instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
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
```

---

### 3.4 Testing Strategy

#### File: `tests/test_utility_quadratic.py`

**Test suite structure:**
1. **Initialization tests**: Valid/invalid parameters
2. **Utility computation**: 
   - At bliss point (U = 0)
   - Below bliss point (U < 0 but MU > 0)
   - Above bliss point (U < 0 and MU < 0)
3. **Marginal utility tests**:
   - Verify MU_A, MU_B signs in each region
   - Check that MU = 0 at bliss points
4. **MRS tests**:
   - Undefined at bliss points (return None)
   - Correct ratio away from bliss points
5. **Reservation bounds tests**:
   - Standard case (both MU > 0)
   - Satiation case (one or both MU < 0)
   - Verify p_min > p_max when no trade is beneficial
6. **Money-aware API**: Verify `u_goods()` routes correctly

#### File: `tests/test_utility_translog.py`

**Test suite structure:**
1. **Initialization tests**: Valid/invalid parameters (alpha_A, alpha_B > 0)
2. **Utility computation**:
   - Verify monotonicity (U increases with A, B)
   - Test numerical stability (large/small inventories)
   - Overflow protection (very large parameters)
3. **Marginal utility tests**:
   - Always positive for positive inventories
   - Correct derivatives (can use numerical differentiation to verify)
4. **MRS tests**:
   - Always positive and well-defined
   - Verify formula correctness vs. numerical differentiation
5. **Zero handling**:
   - Verify epsilon-shift works correctly
   - No NaN or inf in outputs
6. **Special cases**:
   - Cobb-Douglas nesting (beta terms = 0)
   - Comparison with CES (if appropriate restrictions)
7. **Money-aware API**: Verify `u_goods()`, `mu_A()`, `mu_B()` routes

#### File: `tests/test_utility_stone_geary.py`

**Test suite structure:**
1. **Initialization tests**: Valid/invalid parameters (alpha > 0, gamma >= 0)
2. **Utility computation**:
   - Above subsistence: verify positive and well-behaved utility
   - At subsistence: verify epsilon-shift gives finite (very negative) utility
   - Below subsistence: verify graceful handling via epsilon-shift
   - Verify Cobb-Douglas nesting (gamma = 0)
3. **Marginal utility tests**:
   - Always positive for A, B > gamma (after epsilon-shift)
   - Verify MU → ∞ as inventory approaches subsistence
   - Verify MU → 0 as inventory → ∞
4. **MRS tests**:
   - Correct formula implementation
   - High MRS when close to subsistence in A
   - Low MRS when far above subsistence
   - Numerical verification vs. finite differences
5. **Reservation bounds tests**:
   - Standard case: both goods above subsistence
   - Desperate buyer: A ≤ gamma_A, B > gamma_B
   - Cannot sell: A > gamma_A, B ≤ gamma_B
   - Both below subsistence: neutral default or refuse trade
6. **Subsistence validation**:
   - Verify `is_above_subsistence()` helper method
   - Test boundary conditions (exactly at subsistence)
7. **Money-aware API**: Verify all routes work correctly

#### Integration Tests

**File: `tests/test_utility_mix_integration.py`**

Test scenarios with mixed utility types:
1. **Heterogeneous agents**: Some quadratic, some translog, some Stone-Geary, some CES
2. **Trade dynamics**: Verify agents with different utility types can trade
3. **Quote computation**: All utility types generate valid quotes
4. **Edge case handling**: 
   - Agents with satiation (quadratic) correctly refuse trades
   - Agents below subsistence (Stone-Geary) trade desperately
   - Translog agents handle numerical edge cases
5. **Subsistence constraint validation**: 
   - Scenario loader rejects Stone-Geary with initial inventories ≤ subsistence
   - Clear error messages for configuration violations

---

### 3.5 GUI/Launcher Updates

#### File: `src/vmt_launcher/scenario_builder.py`

**Update `add_utility_row()` method:**

```python
def add_utility_row(self, row: int, utype: str, weight: float, 
                    p1: float, p2: float, p3: float, p4: float = 0.0, 
                    p5: float = 0.0, p6: float = 0.0):
    """
    Add a utility function row to the table.
    
    Parameter mapping:
    - CES: p1=rho, p2=wA, p3=wB
    - Linear: p1=vA, p2=vB
    - Quadratic: p1=A_star, p2=B_star, p3=sigma_A, p4=sigma_B, p5=gamma
    - Translog: p1=alpha_0, p2=alpha_A, p3=alpha_B, p4=beta_AA, p5=beta_BB, p6=beta_AB
    - Stone-Geary: p1=alpha_A, p2=alpha_B, p3=gamma_A, p4=gamma_B
    """
    # ... implementation with extended columns for additional parameters
```

**Add documentation panel for new utilities:**
- **Quadratic**: Explain bliss points, show example parameter values, warning about satiation
- **Translog**: Explain second-order flexibility, show Cobb-Douglas nesting, provide parameter presets
- **Stone-Geary**: Explain subsistence constraints, show LES connection, warning about initial inventory requirements

---

### 3.6 Documentation Updates

#### File: `docs/1_project_overview.md`

Add section on utility function options, including quadratic, translog, and Stone-Geary.

#### File: `docs/2_technical_manual.md`

Add detailed mathematical descriptions and implementation notes for all three functions.

#### File: `docs/4_typing_overview.md`

Update Part 1, Section 3.1 to include quadratic, translog, and Stone-Geary in the discriminated union:

```text
Utility :=
  | { type: "ces",         params: CESParams }
  | { type: "linear",      params: LinearParams }
  | { type: "quadratic",   params: QuadraticParams }
  | { type: "translog",    params: TranslogParams }
  | { type: "stone_geary", params: StoneGearyParams }
```

And define the new parameter types:

```text
QuadraticParams := { 
  A_star: float > 0, 
  B_star: float > 0, 
  sigma_A: float > 0, 
  sigma_B: float > 0, 
  gamma: float >= 0 
}

TranslogParams := { 
  alpha_0: float,
  alpha_A: float > 0, 
  alpha_B: float > 0,
  beta_AA: float, 
  beta_BB: float, 
  beta_AB: float 
}

StoneGearyParams := {
  alpha_A: float > 0,
  alpha_B: float > 0,
  gamma_A: float >= 0,
  gamma_B: float >= 0
}
```

**Important invariant for Stone-Geary**: 
In any scenario using Stone-Geary utility, initial inventories must satisfy:
```
initial_A > gamma_A  AND  initial_B > gamma_B
```
This constraint must be validated during scenario loading.

---

### 3.7 Example Scenarios

#### File: `scenarios/bliss_point_demo.yaml`

Demonstrate quadratic utility with agents clustering around bliss points:

```yaml
name: "Bliss Point Demonstration"
N: 20
agents: 10

initial_inventories:
  A: { uniform_int: [5, 15] }
  B: { uniform_int: [5, 15] }

utilities:
  mix:
    - type: "quadratic"
      weight: 1.0
      params:
        A_star: 10.0
        B_star: 10.0
        sigma_A: 5.0
        sigma_B: 5.0
        gamma: 0.2

params:
  vision_radius: 8
  interaction_radius: 2
  move_budget_per_tick: 2
  dA_max: 3
  forage_rate: 1
  resource_growth_rate: 1
  resource_max_amount: 5

resource_seed:
  density: 0.3
  amount: { uniform_int: [2, 5] }
```

#### File: `scenarios/translog_estimation_demo.yaml`

Demonstrate translog utility for empirical estimation exercises:

```yaml
name: "Translog Empirical Demonstration"
N: 30
agents: 20

initial_inventories:
  A: { uniform_int: [10, 50] }
  B: { uniform_int: [10, 50] }

utilities:
  mix:
    - type: "translog"
      weight: 0.5
      params:
        alpha_0: 0.0
        alpha_A: 0.5
        alpha_B: 0.5
        beta_AA: -0.1
        beta_BB: -0.1
        beta_AB: 0.05
    - type: "ces"
      weight: 0.5
      params:
        rho: -0.5
        wA: 1.0
        wB: 1.0

params:
  vision_radius: 10
  interaction_radius: 2
  move_budget_per_tick: 2
  dA_max: 5
  spread: 0.05

resource_seed:
  density: 0.4
  amount: { uniform_int: [3, 8] }
```

#### File: `scenarios/subsistence_economy_demo.yaml`

Demonstrate Stone-Geary utility with subsistence constraints and inequality:

```yaml
name: "Subsistence Economy Demonstration"
N: 25
agents: 15

# Heterogeneous initial endowments: some agents close to subsistence, others far above
initial_inventories:
  A: { uniform_int: [8, 40] }
  B: { uniform_int: [6, 35] }

utilities:
  mix:
    # All agents have same subsistence levels but may start at different distances from them
    - type: "stone_geary"
      weight: 1.0
      params:
        alpha_A: 0.6
        alpha_B: 0.4
        gamma_A: 5.0   # Subsistence: need at least 5 units of A
        gamma_B: 3.0   # Subsistence: need at least 3 units of B

params:
  vision_radius: 8
  interaction_radius: 2
  move_budget_per_tick: 2
  dA_max: 5
  forage_rate: 2
  resource_growth_rate: 1
  resource_max_amount: 8
  spread: 0.1

resource_seed:
  density: 0.35
  amount: { uniform_int: [2, 6] }
```

**Expected behaviors:**
- Agents with inventories close to (gamma_A, gamma_B) trade desperately, accept unfavorable prices
- Agents far above subsistence trade more selectively, like standard Cobb-Douglas agents
- Market naturally segments into "subsistence traders" and "normal traders"
- Visualizations should show agents clustering above subsistence thresholds over time

#### File: `scenarios/mixed_utility_showcase.yaml`

Showcase all three new utilities in one heterogeneous population:

```yaml
name: "Mixed Utility Showcase"
N: 30
agents: 24

initial_inventories:
  A: { uniform_int: [10, 50] }
  B: { uniform_int: [10, 50] }

utilities:
  mix:
    - type: "quadratic"
      weight: 0.33
      params:
        A_star: 30.0
        B_star: 30.0
        sigma_A: 10.0
        sigma_B: 10.0
        gamma: 0.1
    
    - type: "translog"
      weight: 0.33
      params:
        alpha_0: 0.0
        alpha_A: 0.5
        alpha_B: 0.5
        beta_AA: -0.08
        beta_BB: -0.08
        beta_AB: 0.03
    
    - type: "stone_geary"
      weight: 0.34
      params:
        alpha_A: 0.6
        alpha_B: 0.4
        gamma_A: 8.0
        gamma_B: 6.0

params:
  vision_radius: 10
  interaction_radius: 2
  move_budget_per_tick: 2
  dA_max: 5
  spread: 0.05
  resource_growth_rate: 1
  resource_max_amount: 10

resource_seed:
  density: 0.4
  amount: { uniform_int: [3, 8] }
```

**Expected behaviors:**
- Quadratic agents seek bliss points, may refuse trades when saturated
- Translog agents show variable elasticity based on inventory levels
- Stone-Geary agents prioritize staying above subsistence
- Rich diversity of trading patterns demonstrates architectural flexibility

---

## Part 4: Implementation Sequence

### Phase 1: Core Implementation (Priority: High)
1. Implement `UQuadratic` class with full API
2. Implement `UTranslog` class with full API
3. Implement `UStoneGeary` class with full API
4. Update schema to accept new types (`"quadratic"`, `"translog"`, `"stone_geary"`)
5. Update factory function to handle all three new types

**Validation**: Unit tests pass for all three classes in isolation.

**Estimated effort**: 2-3 days
- Quadratic: 4-6 hours (simpler math, complex edge cases)
- Translog: 6-8 hours (complex math, numerical considerations)
- Stone-Geary: 4-6 hours (moderate math, subsistence validation)
- Testing: 6-8 hours (comprehensive coverage for all three)

---

### Phase 2: Integration (Priority: High)
1. Update scenario loader to instantiate new utility types
2. Add subsistence validation for Stone-Geary (check initial inventories > gamma)
3. Test quote computation with new utilities
4. Test trade execution with new utilities
5. Add integration tests with mixed utility populations
6. Verify epsilon-handling works consistently across all utilities

**Validation**: 
- Existing scenarios still run without changes
- New utility scenarios execute without errors
- Mixed-utility scenario runs and shows diverse trading patterns
- Stone-Geary scenarios reject invalid initial inventories with clear error messages

**Estimated effort**: 2-3 days

---

### Phase 3: Edge Case Handling (Priority: Medium)
1. **Quadratic**: Handle negative MU, undefined MRS, no-trade regions
   - Agents with all MU ≤ 0 skip quote generation
   - Return None from mrs_A_in_B() when at bliss point
   - Reservation bounds handle satiation regions gracefully
2. **Translog**: Handle zero inventories, numerical overflow protection
   - Epsilon-shift consistently applied for A=0, B=0
   - Cap ln(U) before exp() to prevent overflow (max 700)
   - Test with very large and very small parameter values
3. **Stone-Geary**: Handle subsistence boundary conditions
   - Graceful handling when exactly at subsistence (epsilon-shift)
   - Clear error messages for initial inventory violations
   - Test desperate trading behavior when close to subsistence
4. Add defensive checks in quoting system for invalid/None MRS
5. Add telemetry warnings when agents refuse trades due to special conditions

**Validation**: 
- Edge case unit tests pass for all three utilities
- Scenarios with extreme parameters run stably
- Telemetry captures subsistence violations, satiation events, overflow warnings

**Estimated effort**: 2-3 days

---

### Phase 4: Documentation & Examples (Priority: Medium)
1. Update all documentation files (project_overview, technical_manual, typing_overview)
2. Create bliss point demo scenario (`bliss_point_demo.yaml`)
3. Create translog demo scenario (`translog_estimation_demo.yaml`)
4. Create subsistence economy demo scenario (`subsistence_economy_demo.yaml`)
5. Create mixed utility showcase scenario (`mixed_utility_showcase.yaml`)
6. Write tutorial Jupyter notebook demonstrating all three new utilities
7. Update GUI with new utility options and documentation panels
   - Quadratic: Explain bliss points, parameter guidance
   - Translog: Parameter presets (Cobb-Douglas, weak complements, flexible substitutes)
   - Stone-Geary: Subsistence constraints, LES connection, inventory warnings

**Validation**: 
- All demo scenarios run successfully
- Documentation is comprehensive and accurate
- Jupyter tutorial executes without errors and provides clear explanations
- GUI correctly handles 6-parameter utilities (translog needs 6 inputs)

**Estimated effort**: 2-3 days

---

### Phase 5: Advanced Features (Priority: Low / Future)
1. **Translog enhancements**:
   - Add validation for regularity conditions (monotonicity, quasi-concavity checks)
   - Implement helper functions for Cobb-Douglas → translog conversion
   - Parameter estimation tutorial using generated translog data
2. **Quadratic enhancements**:
   - Add visualization for indifference curves showing bliss points
   - Implement "gift economy" extension (negative prices / one-sided transfers)
   - Explore non-convex preference scenarios
3. **Stone-Geary enhancements**:
   - Implement quasi-linear Stone-Geary variant (one good has gamma=0, alpha=1)
   - Add telemetry tracking for time spent below subsistence
   - Poverty trap analysis tools (can agents escape subsistence?)
   - LES demand estimation from trade data
4. **Cross-cutting enhancements**:
   - Performance benchmarking with new utility types
   - Indifference curve visualization for all utility types
   - Advanced heterogeneity scenarios (e.g., rich Quadratic, poor Stone-Geary)
   - Integration with money system (Phase 2+ money modes)

**Validation**: 
- Advanced features documented and tested
- Performance is acceptable (no significant slowdown vs. CES/Linear)
- Estimation tutorials produce accurate parameter recovery

**Estimated effort**: 3-5 days (spread over time as needs arise)

---

## Part 5: Technical Challenges & Mitigations

### 5.1 Quadratic Utility Challenges

| Challenge | Impact | Mitigation |
|-----------|--------|------------|
| **Negative marginal utility** | Agents may refuse all trades when saturated | Add `has_trade_incentive()` check in decision phase; skip agents with all MU <= 0 |
| **Undefined MRS at bliss** | Division by zero when MU_B = 0 | Return `None` from `mrs_A_in_B()`; quoting system handles None gracefully |
| **Non-convex preferences** | May lead to unstable trading patterns | Document as feature, not bug; interesting for research |
| **Inventory below zero** | Mathematical model allows negative, but simulation doesn't | Ensure bliss points are set high enough above typical inventories |

### 5.2 Translog Utility Challenges

| Challenge | Impact | Mitigation |
|-----------|--------|------------|
| **Exponential overflow** | `exp(ln_u)` can overflow for large ln_u | Cap `ln_u` at 700 before exp(); work in log-space where possible |
| **Zero inventory** | `ln(0)` undefined | Use epsilon-shift (same as CES); document in function docstring |
| **Complex parameters** | 6 parameters is cognitively demanding | Provide helper functions/presets for common cases (e.g., Cobb-Douglas nesting) |
| **Regularity conditions** | Unconstrained parameters may violate curvature/monotonicity | Phase 5: Add validation; Phase 1: Document expected ranges, provide tested examples |
| **Pedagogical opacity** | Parameters lack intuitive economic meaning | Position as advanced/empirical tool; use comparatively with CES |

### 5.3 Stone-Geary Utility Challenges

| Challenge | Impact | Mitigation |
|-----------|--------|------------|
| **Subsistence violations** | `ln(A - gamma_A)` undefined when A ≤ gamma_A | Use epsilon-shift: `max(A - gamma_A, eps)`; validate at scenario load |
| **Initial inventory constraints** | Scenario must ensure starting inventories > subsistence | Add validation in scenario loader; reject configs that violate constraints |
| **Desperate trading** | Agents near subsistence have extremely high MRS | This is a feature; document and provide telemetry for subsistence distance |
| **Parameter interpretation** | Users may not understand gamma vs. alpha roles | GUI documentation panel; provide example scenarios with clear explanations |
| **Cobb-Douglas confusion** | When gamma=0, identical to Cobb-Douglas (redundant?) | Document nesting relationship; Stone-Geary is the general form |

### 5.4 General Integration Challenges

| Challenge | Impact | Mitigation |
|-----------|--------|------------|
| **Quote computation compatibility** | Existing quoting system assumes MRS always defined | Update `compute_quotes()` to handle `None` MRS (skip that exchange pair) |
| **Telemetry schema** | `utility_type` field may need updating | Already stores class name as string; no schema changes needed |
| **GUI parameter inputs** | More parameters = more complex UI | Use expandable parameter rows; provide tooltips with descriptions |
| **Backward compatibility** | Don't break existing scenarios | New utilities are additive; no changes to CES/linear |

---

## Part 6: Open Questions & Design Decisions

### 6.1 Quadratic: How to Handle "Gift Economy"?

**Question**: If agent has negative MU for good A, should they be able to *pay* another agent to take it (i.e., A + M for nothing)?

**Options**:
1. **Allow negative prices**: Extend matching logic to handle negative prices (complex)
2. **Refuse trades**: Agents with negative MU simply don't trade (simple, conservative)
3. **One-sided gifts**: Allow free transfers (ΔA > 0, ΔB = 0) if buyer has positive MU and seller has negative MU

**Recommendation**: Start with Option 2 (refuse trades) for simplicity. Option 3 could be a Phase 5 extension.

---

### 6.2 Translog: Work in Log-Space or Exponentiate?

**Question**: Should we store/return `ln(U)` or `U` in the `u()` method?

**Options**:
1. **Exponentiate**: Return `U = exp(ln_u)` (matches interface contract)
2. **Log-space**: Return `ln_u` and document that translog uses log-utility

**Recommendation**: Option 1 (exponentiate) to maintain interface consistency. For MRS, work in log-space internally (the `U` cancels anyway).

---

### 6.3 Translog: Simplify to Fewer Parameters?

**Question**: 6 parameters is a lot. Should we offer a simplified 3-parameter version?

**Options**:
1. **Full flexibility**: All 6 parameters (current proposal)
2. **Restricted form**: Fix `beta_AA = beta_BB = 0`, only allow `beta_AB` (Cobb-Douglas with interaction)
3. **Dual classes**: `UTranslog` (full) and `UTranslogSimple` (restricted)

**Recommendation**: Start with full flexibility (Option 1). Users can set beta terms to 0 for simpler cases. Option 3 could be added later if demand exists.

---

### 6.4 Stone-Geary: How to Handle Agents Below Subsistence?

**Question**: If an agent falls below subsistence during simulation (e.g., bad trade, foraging fails), how should they behave?

**Options**:
1. **Epsilon-shift always**: Use `max(A - gamma_A, eps)` so utility is finite but very negative
2. **Refuse all trades**: Agent cannot generate quotes, becomes inactive
3. **Desperate mode**: Agent accepts any trade that moves them toward subsistence, ignoring normal surplus rules

**Recommendation**: Start with Option 1 (epsilon-shift) combined with very high MRS. This gives agents maximum incentive to trade toward subsistence. Option 3 could be a Phase 5 enhancement.

---

### 6.5 Should We Add Scenario-Level Validation for Stone-Geary?

**Question**: Should the scenario loader automatically reject Stone-Geary configurations where any initial inventory could be ≤ subsistence?

**Options**:
1. **Strict validation**: Reject if there's any possibility (e.g., `uniform_int: [5, 15]` with `gamma_A: 10` could generate A=5)
2. **Soft validation**: Only check if maximum possible inventory > subsistence (allow risk)
3. **No validation**: Let it fail at runtime with clear error message

**Recommendation**: Option 1 (strict validation). Better to fail fast at scenario load than mid-simulation.

---

### 6.6 Testing: How Comprehensive?

**Question**: What level of testing is sufficient before merge?

**Requirements** (minimum):
1. Unit tests for all three utility classes (initialization, u(), mu(), mrs(), reservation_bounds())
2. Integration test with mixed population (quadratic + translog + Stone-Geary + CES)
3. Edge case tests (zero inventory, satiation, overflow, subsistence violations)
4. At least one demo scenario for each new utility
5. Stone-Geary: Validation test that rejects invalid initial inventories

**Nice-to-have** (Phase 5):
1. Numerical differentiation verification (test that analytic MU matches finite differences)
2. Property-based tests (e.g., U monotonic in A, B for translog with positive alphas)
3. Performance benchmarks (are new utilities slower than CES?)
4. Stone-Geary: LES demand estimation exercise using generated trade data

---

## Part 7: Success Criteria

### Implementation Complete When:
1. ✅ All three classes (`UQuadratic`, `UTranslog`, `UStoneGeary`) implemented with full Utility API
2. ✅ All unit tests pass (>90% coverage for new classes)
3. ✅ Integration tests pass with mixed populations (including all three + CES)
4. ✅ Schema updated, loader handles new types (`"quadratic"`, `"translog"`, `"stone_geary"`)
5. ✅ Stone-Geary validation: Scenario loader rejects invalid subsistence configurations
6. ✅ At least one demo scenario for each utility runs successfully
7. ✅ Mixed utility showcase scenario runs and demonstrates all three
8. ✅ Documentation updated (project_overview.md, technical_manual.md, typing_overview.md)
9. ✅ GUI updated with parameter inputs for all three utilities (including 6-parameter translog)
10. ✅ No regressions in existing tests

### Pedagogical Success:
- **Quadratic**: Students can load bliss point demo and observe satiation behavior
- **Translog**: Students can load translog demo and see variable elasticity, compare to Cobb-Douglas
- **Stone-Geary**: Students can load subsistence demo and observe desperate trading, market segmentation
- **Mixed showcase**: Students can run heterogeneous population and see diverse trading patterns
- Documentation clearly explains when to use each utility type and provides parameter guidance

### Research Success:
- Researchers can configure realistic preference heterogeneity across all dimensions (satiation, flexibility, subsistence)
- Generated data can be used for parameter estimation exercises (especially translog and Stone-Geary/LES)
- New utilities enable new research questions:
  - Quadratic: satiation effects, gift economies, non-convex preferences
  - Translog: functional form testing, variable elasticity, empirical calibration
  - Stone-Geary: inequality, poverty traps, basic needs, redistribution policies

---

## Part 8: Next Steps

1. **Review & Approval**: Share this document with stakeholders, gather feedback
2. **Parameter Design**: Finalize default parameter values for demo scenarios
   - Quadratic: What bliss points are pedagogically useful? (10, 10) with sigma around 5?
   - Translog: Safe parameter ranges for goods 1-1000? Presets for common cases?
   - Stone-Geary: Subsistence levels that allow meaningful trading? (gamma = 5, alpha = 0.6)?
3. **Implementation Kickoff**: Create feature branch `feature/utility-expansion`, implement Phase 1
4. **Iterative Testing**: Implement, test, refine each phase sequentially
   - Phase 1: Core classes (2-3 days)
   - Phase 2: Integration (2-3 days)
   - Phase 3: Edge cases (2-3 days)
   - Phase 4: Documentation & examples (2-3 days)
5. **Documentation Sprint**: Ensure all docs are updated before merge to main
6. **Tutorial Development**: Create Jupyter notebook demonstrating all three new utilities
   - Section 1: Quadratic (bliss points, satiation)
   - Section 2: Translog (flexible approximation, Cobb-Douglas nesting)
   - Section 3: Stone-Geary (subsistence, LES, inequality)
   - Section 4: Heterogeneous population showcase

---

## Appendix A: Mathematical Derivations

### A.1 Quadratic MRS Derivation

Given:
```
U(A, B) = -(A - A*)²/σ_A² - (B - B*)²/σ_B² - γ(A - A*)(B - B*)
```

Marginal utilities:
```
MU_A = ∂U/∂A = -2(A - A*)/σ_A² - γ(B - B*)
MU_B = ∂U/∂B = -2(B - B*)/σ_B² - γ(A - A*)
```

MRS:
```
MRS = MU_A / MU_B = [-2(A - A*)/σ_A² - γ(B - B*)] / [-2(B - B*)/σ_B² - γ(A - A*)]
```

At the bliss point `(A*, B*)`:
```
MU_A = 0, MU_B = 0 → MRS undefined
```

### A.2 Translog MRS Derivation

Given:
```
V(A, B) = ln U = α₀ + α_A·ln(A) + α_B·ln(B) + (1/2)β_AA·[ln(A)]² + (1/2)β_BB·[ln(B)]² + β_AB·ln(A)·ln(B)
```

Derivatives:
```
∂V/∂A = α_A/A + β_AA·ln(A)/A + β_AB·ln(B)/A = [α_A + β_AA·ln(A) + β_AB·ln(B)] / A
∂V/∂B = α_B/B + β_BB·ln(B)/B + β_AB·ln(A)/B = [α_B + β_BB·ln(B) + β_AB·ln(A)] / B
```

Marginal utilities (using chain rule: `MU = U · ∂V/∂x`):
```
MU_A = U · [α_A + β_AA·ln(A) + β_AB·ln(B)] / A
MU_B = U · [α_B + β_BB·ln(B) + β_AB·ln(A)] / B
```

MRS (U cancels):
```
MRS = MU_A / MU_B = [α_A + β_AA·ln(A) + β_AB·ln(B)] · B / [α_B + β_BB·ln(B) + β_AB·ln(A)] · A
```

### A.3 Stone-Geary MRS Derivation

Given:
```
U(A, B) = α_A·ln(A - γ_A) + α_B·ln(B - γ_B)
```

Marginal utilities (using chain rule):
```
MU_A = ∂U/∂A = α_A / (A - γ_A)
MU_B = ∂U/∂B = α_B / (B - γ_B)
```

MRS:
```
MRS = MU_A / MU_B = [α_A / (A - γ_A)] / [α_B / (B - γ_B)]
                   = [α_A · (B - γ_B)] / [α_B · (A - γ_A)]
```

**Special cases**:
- When `A → γ_A` (approaching subsistence in A): `MRS → ∞` (infinitely willing to trade B for A)
- When `B → γ_B` (approaching subsistence in B): `MRS → 0` (unwilling to trade B for A)
- When `γ_A = γ_B = 0`: Reduces to Cobb-Douglas MRS: `(α_A · B) / (α_B · A)`

**Nesting relationship**:
Stone-Geary with `γ_A = γ_B = 0` is exactly Cobb-Douglas utility (logarithmic form).

---

## Appendix B: Example Parameter Values

### Quadratic (Bliss Point Scenario)
```yaml
# Moderate bliss points with symmetric curvature
A_star: 10.0
B_star: 10.0
sigma_A: 5.0
sigma_B: 5.0
gamma: 0.0  # No cross-curvature (independent goods)

# Asymmetric bliss points (agent prefers more A)
A_star: 15.0
B_star: 8.0
sigma_A: 6.0
sigma_B: 4.0
gamma: 0.3  # Weak complementarity
```

### Translog (Empirical Scenario)
```yaml
# Cobb-Douglas nested case (beta terms = 0)
alpha_0: 0.0
alpha_A: 0.6
alpha_B: 0.4
beta_AA: 0.0
beta_BB: 0.0
beta_AB: 0.0

# Flexible second-order (weak complements)
alpha_0: 1.0
alpha_A: 0.5
alpha_B: 0.5
beta_AA: -0.05  # Negative = diminishing returns
beta_BB: -0.05
beta_AB: 0.02   # Positive = complementarity

# Strong substitutes
alpha_0: 0.0
alpha_A: 0.7
alpha_B: 0.3
beta_AA: -0.1
beta_BB: -0.1
beta_AB: -0.05  # Negative = substitutability
```

### Stone-Geary (Subsistence Scenario)
```yaml
# Moderate subsistence with balanced preferences
alpha_A: 0.6
alpha_B: 0.4
gamma_A: 5.0   # Need at least 5 units of A
gamma_B: 3.0   # Need at least 3 units of B
# Typical initial inventories: A ∈ [8, 40], B ∈ [6, 35]
# Ensures all agents start above subsistence

# High subsistence (closer to poverty)
alpha_A: 0.5
alpha_B: 0.5
gamma_A: 10.0  # Higher subsistence requirement
gamma_B: 8.0
# Typical initial inventories: A ∈ [12, 50], B ∈ [10, 45]
# Some agents will be close to subsistence, desperate traders

# Asymmetric subsistence (A is critical, B is luxury)
alpha_A: 0.8
alpha_B: 0.2
gamma_A: 8.0   # High subsistence for critical good A
gamma_B: 2.0   # Low subsistence for luxury good B
# Typical initial inventories: A ∈ [10, 30], B ∈ [5, 50]
# Agents prioritize A over B

# Cobb-Douglas nested case (zero subsistence)
alpha_A: 0.6
alpha_B: 0.4
gamma_A: 0.0   # No subsistence constraint
gamma_B: 0.0   # Reduces to pure Cobb-Douglas
# This demonstrates nesting: Stone-Geary generalizes Cobb-Douglas
```

**Important**: For any Stone-Geary parameters, ensure:
```
min(initial_inventories_A) > gamma_A
min(initial_inventories_B) > gamma_B
```
The scenario loader should validate this constraint and reject configurations that violate it.

---

## Document History

- **2025-10-21 (Morning)**: Initial draft created covering quadratic and translog utilities
- **2025-10-21 (Afternoon)**: Expanded to include Stone-Geary utility
  - Added comprehensive Stone-Geary mathematical foundation (Part 1.3)
  - Included Stone-Geary in all implementation plans, testing strategies, and example scenarios
  - Added subsistence economy demo and mixed utility showcase scenarios
  - Incorporated detailed translog computational analysis and parameter guidance
  - Updated all phases, success criteria, and appendices for three-utility implementation
- **Status**: Comprehensive planning document ready for review and approval before implementation begins

---

**End of Document**

