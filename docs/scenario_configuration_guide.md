# VMT Scenario Configuration Guide

**Purpose:** This document provides a comprehensive reference for creating and configuring VMT simulation scenarios using YAML files. It serves as a single source of truth for all scenario parameters, their types, defaults, constraints, and interactions.

**Audience:** Developers and researchers creating new scenarios or modifying existing ones.

**Related Documents:**
- Schema implementation: [`src/scenarios/schema.py`](../src/scenarios/schema.py)
- Type specifications: [`docs/4_typing_overview.md`](4_typing_overview.md)
- Demo scenarios: [`scenarios/demos/`](../scenarios/demos/)

---

## Table of Contents

1. [Overview & Structure](#1-overview--structure)
2. [Top-Level Metadata](#2-top-level-metadata)
3. [Initial Inventories](#3-initial-inventories)
4. [Utility Functions](#4-utility-functions)
5. [Simulation Parameters](#5-simulation-parameters)
6. [Resource Seeding](#6-resource-seeding)
7. [Mode Scheduling](#7-mode-scheduling)
8. [Complete Examples](#8-complete-examples)
9. [Validation Rules](#9-validation-rules)
10. [Common Patterns & Best Practices](#10-common-patterns--best-practices)

---

## 1. Overview & Structure

### 1.1 What is a Scenario?

A **scenario** is a complete specification of a simulation's initial conditions and behavioral parameters. It defines:

- The environment (grid size)
- The agents (count, inventories, preferences)
- The resources (distribution and amounts)
- The rules (movement, trading, foraging)
- The temporal structure (mode scheduling)
- The economic regime (barter, money, or mixed)

### 1.2 Basic Structure

Every scenario YAML file follows this top-level structure:

```yaml
schema_version: int       # Always 1 for current implementation
name: string              # Human-readable scenario name
N: int                    # Grid size (N×N)
agents: int               # Number of agents

initial_inventories:      # Agent starting endowments
  A: ...                  # Good A
  B: ...                  # Good B
  M: ...                  # Money (optional, required for monetary regimes)

utilities:                # Agent preference specifications
  mix: [...]              # List of utility functions with weights

params:                   # Simulation parameters (all optional)
  ...                     # Movement, trading, foraging rules

resource_seed:            # Environment resource distribution
  density: float
  amount: int | dist

mode_schedule:            # Optional: temporal mode cycling
  ...
```

### 1.3 File Location

Scenarios are typically stored in:
- `scenarios/` - General scenarios
- `scenarios/demos/` - Pedagogical demonstrations
- `scenarios/test/` - Testing scenarios

Load a scenario with: `python launcher.py <path_to_scenario.yaml>`

---

## 2. Top-Level Metadata

### 2.1 `schema_version`

**Type:** `int`  
**Required:** Yes  
**Current Value:** `1`

Specifies the scenario schema version. Currently, only version 1 is supported. This allows for backward compatibility if the schema evolves.

```yaml
schema_version: 1
```

### 2.2 `name`

**Type:** `string`  
**Required:** Yes

A human-readable name for the scenario. Displayed in the UI and recorded in telemetry logs.

```yaml
name: "Demo 1: Simple Money"
```

**Best Practice:** Use descriptive names that indicate the scenario's purpose or pedagogical goal.

### 2.3 `N`

**Type:** `int > 0`  
**Required:** Yes

The size of the square grid. An `N` value of 20 creates a 20×20 grid with 400 cells.

```yaml
N: 20
```

**Constraints:**
- Must be positive
- Larger grids increase computation time
- Recommended: 10-40 for visual clarity; 40+ for spatial heterogeneity studies

**Performance Note:** Grid processing is O(N²) per tick for certain operations (resource regeneration, rendering).

### 2.4 `agents`

**Type:** `int > 0`  
**Required:** Yes

The number of agents to create in the simulation.

```yaml
agents: 15
```

**Constraints:**
- Must be positive
- Should be ≤ N² (number of cells) for reasonable density
- Recommended density: 1-10% of cells occupied

**Agent Density Formula:**
```
density = agents / N² 
```

For `N=20, agents=15`: density = 15/400 = 3.75%

---

## 3. Initial Inventories

### 3.1 Overview

The `initial_inventories` section specifies how much of each good agents start with. Inventories are **integer quantities** (not floats).

### 3.2 Basic Syntax

#### 3.2.1 Fixed Integer (All Agents Equal)

```yaml
initial_inventories:
  A: 10
  B: 10
  M: 100
```

All agents receive the same endowment: 10 A, 10 B, 100 M.

#### 3.2.2 Explicit List (Heterogeneous Agents)

```yaml
initial_inventories:
  A: [10, 5, 0, 8, 2]
  B: [0, 5, 10, 2, 8]
  M: [100, 100, 100, 100, 100]
```

Each agent receives the inventory at their index position:
- Agent 0: A=10, B=0, M=100
- Agent 1: A=5, B=5, M=100
- Agent 2: A=0, B=10, M=100
- etc.

**Constraint:** List length must equal the `agents` count.

#### 3.2.3 Distribution (Planned Feature)

**Note:** Distribution syntax is defined in the schema but not currently used in practice. For now, use explicit lists for heterogeneous inventories.

```yaml
initial_inventories:
  A: { uniform_int: [5, 15] }  # Each agent gets random int in [5,15]
  B: { uniform_int: [5, 15] }
```

### 3.3 Good Types

#### 3.3.1 Good A

**Type:** `int | list[int] | distribution`  
**Required:** Yes  
**Constraints:** Must be ≥ 0

The first tradeable good. In barter scenarios, A and B are symmetric. In pedagogical scenarios, often represents one side of a specialization (e.g., "fish" vs "fruit").

#### 3.3.2 Good B

**Type:** `int | list[int] | distribution`  
**Required:** Yes  
**Constraints:** Must be ≥ 0

The second tradeable good.

#### 3.3.3 Money (M)

**Type:** `int | list[int] | distribution`  
**Required:** Only if `exchange_regime` ∈ {`money_only`, `mixed`, `mixed_liquidity_gated`}  
**Constraints:** Must be ≥ 0

Money holdings in **minor units** (e.g., cents if `money_scale=100`).

**Exchange Regime Rules:**
- `barter_only`: M not needed (agents may have money, but it won't be used)
- `money_only`: M **required**; agents need money to trade
- `mixed`: M **required**; both barter and monetary trades possible
- `mixed_liquidity_gated`: M **required**; barter fallback if money market thin

```yaml
params:
  exchange_regime: money_only
  money_scale: 10  # Minor units (e.g., dimes)

initial_inventories:
  A: 50
  B: 50
  M: 1000  # = 100 major units (1000 / 10)
```

#### 3.3.4 Per-Agent Lambda (Optional)

**Type:** `list[float]`  
**Optional:** Yes (defaults to `params.lambda_money` for all agents)

Allows heterogeneous marginal utility of money across agents.

```yaml
initial_inventories:
  A: [50, 200, 100]
  B: [200, 50, 100]
  M: [1000, 1000, 500]
  lambda_money: [2.0, 0.5, 1.0]  # Agent-specific λ values
```

**Use Case:** Create trading opportunities based on different money valuations. High-λ agents (value money more) have lower ask prices in M; low-λ agents (value money less) have higher bid prices in M, creating profitable monetary trades.

**See:** `scenarios/demos/demo_06_money_aware_pairing.yaml` for a worked example.

### 3.4 Stone-Geary Constraint

If using `stone_geary` utility with subsistence levels γ_A and γ_B, initial inventories **must** satisfy:

```
initial_A > γ_A  AND  initial_B > γ_B
```

for all agents. The loader will reject scenarios that violate this constraint.

**Example:**
```yaml
utilities:
  mix:
    - type: stone_geary
      weight: 1.0
      params:
        gamma_A: 5.0  # Subsistence level
        gamma_B: 3.0

initial_inventories:
  A: 8   # OK: 8 > 5
  B: 6   # OK: 6 > 3
```

**Invalid:**
```yaml
initial_inventories:
  A: 5   # ERROR: 5 ≤ γ_A
  B: 6   # OK
```

---

## 4. Utility Functions

### 4.1 Overview

The `utilities` section defines agent preferences using **utility functions**. Agents can have heterogeneous preferences by specifying a **mix** of utility types with weights.

### 4.2 Structure

```yaml
utilities:
  mix:
    - type: "ces"
      weight: 0.5
      params:
        rho: 0.4
        wA: 0.6
        wB: 0.4
    
    - type: "linear"
      weight: 0.5
      params:
        vA: 2.0
        vB: 1.5
```

**Interpretation:**
- 50% of agents receive a CES utility function
- 50% of agents receive a linear utility function
- Agents are assigned utility types **deterministically** by index and weight proportions

**Weight Constraint:** Weights must sum **exactly** to 1.0 (within 1e-6 tolerance).

### 4.3 Utility Function Types

VMT supports five utility function types, each with specific parameters.

---

#### 4.3.1 CES (Constant Elasticity of Substitution)

**Type:** `"ces"`

**Formula:**
```
U(A, B) = (wA · A^ρ + wB · B^ρ)^(1/ρ)
```

where:
- **ρ** (rho): Elasticity parameter (ρ ≠ 1)
  - ρ → 0: Approaches Cobb-Douglas
  - ρ < 0: Complements (prefer balanced bundles)
  - ρ > 0 (but < 1): Substitutes
  - ρ → -∞: Perfect complements (Leontief)
  - ρ → +∞: Perfect substitutes
- **wA, wB**: Preference weights (must be > 0)

**Parameters:**
```yaml
params:
  rho: float     # ρ ≠ 1.0
  wA: float > 0  # Weight for A
  wB: float > 0  # Weight for B
```

**Example:**
```yaml
- type: "ces"
  weight: 1.0
  params:
    rho: 0.4      # Mild substitutes
    wA: 0.6       # Prefer A slightly more
    wB: 0.4
```

**Common Values:**
- `rho = -1.0`: Unit elasticity of substitution
- `rho = 0.5`: Strong substitutes
- `rho = -0.5`: Weak complements
- `rho → 0`: Cobb-Douglas (use rho = 0.001 for approximation)

**Validation:**
- `rho` cannot equal 1.0 (mathematical singularity)
- `wA, wB` must be positive
- No constraint on sum of weights (unlike utility mix weights)

---

#### 4.3.2 Linear

**Type:** `"linear"`

**Formula:**
```
U(A, B) = vA · A + vB · B
```

Perfect substitutes with constant marginal utilities.

**Parameters:**
```yaml
params:
  vA: float > 0  # Value of A
  vB: float > 0  # Value of B
```

**Example:**
```yaml
- type: "linear"
  weight: 0.3
  params:
    vA: 2.0   # 1 unit of A worth 2 utils
    vB: 1.5   # 1 unit of B worth 1.5 utils
```

**Behavior:**
- Marginal rate of substitution (MRS) is constant: `MRS = vA / vB`
- Agents always willing to trade A for B at rate `vA/vB`
- Useful for baseline comparisons

**Validation:**
- `vA, vB` must be positive

---

#### 4.3.3 Quadratic (Bliss Point)

**Type:** `"quadratic"`

**Formula:**
```
U(A, B) = -σ_A · (A - A*)² - σ_B · (B - B*)² - γ · (A - A*) · (B - B*)
```

where:
- **A\*, B\***: Bliss points (ideal quantities)
- **σ_A, σ_B**: Curvature parameters (higher = more sensitive to deviations)
- **γ** (gamma): Cross-curvature (0 = independent goods; γ > 0 = complements)

**Parameters:**
```yaml
params:
  A_star: float > 0   # Bliss point for A
  B_star: float > 0   # Bliss point for B
  sigma_A: float > 0  # Curvature for A
  sigma_B: float > 0  # Curvature for B
  gamma: float ≥ 0    # Cross-curvature (optional, default 0.0)
```

**Example:**
```yaml
- type: "quadratic"
  weight: 0.2
  params:
    A_star: 20.0
    B_star: 15.0
    sigma_A: 0.5
    sigma_B: 0.5
    gamma: 0.1  # Mild complementarity
```

**Behavior:**
- Utility maximized at (A\*, B\*)
- Agents seek to **reach** bliss point, not accumulate infinitely
- Useful for modeling satiation or target-seeking behavior
- `gamma > 0`: Prefers balanced deviations from bliss point

**Validation:**
- All parameters must be positive (γ ≥ 0)
- Bliss points should be achievable but non-trivial given initial inventories

**Pedagogical Use:**
- Demonstrates diminishing marginal utility explicitly
- Shows non-monotonic preferences (post-satiation)

---

#### 4.3.4 Translog (Transcendental Logarithmic)

**Type:** `"translog"`

**Formula:**
```
ln U(A, B) = α₀ + α_A · ln A + α_B · ln B 
             + ½ β_AA · (ln A)² + ½ β_BB · (ln B)² + β_AB · ln A · ln B
```

Flexible functional form with variable elasticity of substitution.

**Parameters:**
```yaml
params:
  alpha_0: float       # Constant term
  alpha_A: float > 0   # First-order coefficient for A
  alpha_B: float > 0   # First-order coefficient for B
  beta_AA: float       # Second-order coefficient for A
  beta_BB: float       # Second-order coefficient for B
  beta_AB: float       # Cross-partial (interaction term)
```

**Example:**
```yaml
- type: "translog"
  weight: 0.5
  params:
    alpha_0: 0.0
    alpha_A: 0.5
    alpha_B: 0.5
    beta_AA: -0.1   # Negative: diminishing marginal utility
    beta_BB: -0.1
    beta_AB: 0.05   # Positive: weak complementarity
```

**Behavior:**
- Variable elasticity of substitution (EOS depends on inventory levels)
- More flexible than CES; can fit a wider range of empirical data
- `beta_AB > 0`: Complementarity
- `beta_AB < 0`: Substitutability
- `beta_AA, beta_BB < 0`: Typical for diminishing marginal utility

**Validation:**
- `alpha_A, alpha_B` must be positive (for monotonicity)
- No general restrictions on second-order terms, but negative β_AA, β_BB are typical

**Use Case:**
- Empirical estimation exercises
- Comparing with CES baseline (see `scenarios/translog_estimation_demo.yaml`)

---

#### 4.3.5 Stone-Geary (Subsistence)

**Type:** `"stone_geary"`

**Formula:**
```
U(A, B) = (A - γ_A)^α_A · (B - γ_B)^α_B
```

where:
- **γ_A, γ_B**: Subsistence levels (minimum needs)
- **α_A, α_B**: Preference weights (must be > 0)

Above subsistence, behaves like Cobb-Douglas. Near subsistence, MRS → ∞ (desperate to maintain minimum consumption).

**Parameters:**
```yaml
params:
  alpha_A: float > 0   # Preference weight for A
  alpha_B: float > 0   # Preference weight for B
  gamma_A: float ≥ 0   # Subsistence level for A
  gamma_B: float ≥ 0   # Subsistence level for B
```

**Example:**
```yaml
- type: "stone_geary"
  weight: 1.0
  params:
    alpha_A: 0.6
    alpha_B: 0.4
    gamma_A: 5.0   # Need at least 5 A to survive
    gamma_B: 3.0   # Need at least 3 B to survive
```

**Critical Constraint:**
Initial inventories **must** satisfy:
```
initial_A > gamma_A  AND  initial_B > gamma_B
```

The scenario loader will **reject** scenarios that violate this.

**Behavior:**
- Agents desperately avoid falling below subsistence
- MRS approaches infinity as inventory → γ
- Models "hierarchy of needs" and survival trading
- Agents with inventories near subsistence accept unfavorable trades

**Validation:**
- `alpha_A, alpha_B` must be positive
- `gamma_A, gamma_B` must be non-negative
- Initial inventories checked at load time

**Pedagogical Use:**
- Development economics (basic needs vs. optimization)
- Demonstrates non-homothetic preferences
- Shows priority-based trading behavior

**See:** `scenarios/subsistence_economy_demo.yaml` for a worked example.

---

### 4.4 Utility Mix Mechanics

#### 4.4.1 Weight Assignment

Agents are assigned utility functions **deterministically** based on:
1. Agent index (0, 1, 2, ...)
2. Cumulative weight proportions

**Example:**
```yaml
utilities:
  mix:
    - type: "ces"
      weight: 0.6
      params: {...}
    
    - type: "linear"
      weight: 0.4
      params: {...}

agents: 10
```

**Assignment:**
- Agents 0-5 (60% of 10): CES utility
- Agents 6-9 (40% of 10): Linear utility

**Important:** Assignment is deterministic and consistent across runs with the same scenario file.

#### 4.4.2 Single Utility Type

To give all agents the same utility:

```yaml
utilities:
  mix:
    - type: "ces"
      weight: 1.0
      params: {...}
```

#### 4.4.3 Multiple Types

For complex heterogeneous populations:

```yaml
utilities:
  mix:
    - type: "ces"
      weight: 0.4
      params: {rho: 0.5, wA: 0.6, wB: 0.4}
    
    - type: "ces"
      weight: 0.3
      params: {rho: -0.5, wA: 0.4, wB: 0.6}  # Different parameters
    
    - type: "stone_geary"
      weight: 0.3
      params: {alpha_A: 0.6, alpha_B: 0.4, gamma_A: 5.0, gamma_B: 3.0}
```

**Result:** Three distinct preference types with different parameters and trade motivations.

---

## 5. Simulation Parameters

### 5.1 Overview

The `params` section controls simulation dynamics. **All parameters are optional** and have sensible defaults. Override only what you need.

```yaml
params:
  # Spatial
  vision_radius: 10
  interaction_radius: 1
  move_budget_per_tick: 2
  spread: 0.05
  
  # Trading
  dA_max: 5
  trade_cooldown_ticks: 5
  
  # Foraging
  forage_rate: 2
  resource_growth_rate: 1
  resource_max_amount: 8
  resource_regen_cooldown: 5
  
  # Resource Claiming
  enable_resource_claiming: true
  enforce_single_harvester: true
  
  # Economics
  epsilon: 1e-12
  beta: 0.95
  
  # Money System
  exchange_regime: "mixed"
  money_mode: "quasilinear"
  money_scale: 1
  lambda_money: 1.0
  lambda_update_rate: 0.2
  lambda_bounds: {lambda_min: 1e-6, lambda_max: 1e6}
  liquidity_gate: {min_quotes: 3}
  earn_money_enabled: false
```

---

### 5.2 Spatial Parameters

#### 5.2.1 `vision_radius`

**Type:** `int ≥ 0`  
**Default:** `5`

Manhattan distance an agent can perceive. Affects:
- Which agents are visible as potential trade partners
- Which resources are visible for foraging

**Value Selection:**
- `vision_radius = N`: Agents see entire grid (global information)
- `vision_radius < N`: Limited local information (more realistic)
- `vision_radius = 0`: Agents see only their own cell

**Example:**
```yaml
N: 20
params:
  vision_radius: 10  # See half the grid radius
```

**Performance:** Higher vision radius increases perception phase computation (O(agents × vision_radius²)).

#### 5.2.2 `interaction_radius`

**Type:** `int ≥ 0`  
**Default:** `1`

Manhattan distance within which agents can trade. Typically set to 1 (adjacent cells only).

**Value Selection:**
- `interaction_radius = 1`: Adjacent trading (most realistic)
- `interaction_radius = 0`: Same-cell trading only (rare use)
- `interaction_radius > 1`: Remote trading (less realistic but useful for testing)

**Constraint:** Usually `interaction_radius ≤ vision_radius` (can't trade with unseen agents).

#### 5.2.3 `move_budget_per_tick`

**Type:** `int ≥ 1`  
**Default:** `1`

Maximum Manhattan distance an agent can move in one tick.

**Value Selection:**
- `move_budget_per_tick = 1`: Slow, realistic movement
- `move_budget_per_tick = 2-3`: Moderate speed
- `move_budget_per_tick ≥ N`: Agents can reach any cell in one tick (unrealistic)

**Example:**
```yaml
N: 40
params:
  move_budget_per_tick: 2  # Faster movement on large grid
```

**Trade-off:** Higher values reduce time to reach trade partners but make spatial structure less important.

---

### 5.3 Trading Parameters

#### 5.3.1 `dA_max`

**Type:** `int ≥ 1`  
**Default:** `5`

Maximum trade size to search for good A. The trading algorithm iterates ΔA from 1 to `dA_max` to find mutually beneficial trades.

**Value Selection:**
- `dA_max = 1-3`: Small trades only (conservative)
- `dA_max = 5-10`: Moderate trades (typical)
- `dA_max > 10`: Large trades (can lead to inventory concentration)

**Performance:** Trade search is O(dA_max × prices), so higher values increase trading phase computation time.

**Backward Compatibility:** Previously named `ΔA_max` in older scenarios. Both names are supported.

#### 5.3.2 `trade_cooldown_ticks`

**Type:** `int ≥ 0`  
**Default:** `5`

Number of ticks agents must wait after a **failed** trade attempt before they can attempt to trade with the same partner again.

**Purpose:** Prevents agents from repeatedly attempting impossible trades.

**Value Selection:**
- `trade_cooldown_ticks = 0`: No cooldown (agents retry immediately)
- `trade_cooldown_ticks = 5-10`: Typical (prevents thrashing)
- `trade_cooldown_ticks > 20`: Long cooldown (agents explore other partners)

**Behavior:**
- **Successful trades:** No cooldown applied
- **Failed trades:** Agents unpaired and cooldown set
- Cooldown tracked per partner pair

#### 5.3.3 `spread`

**Type:** `float ≥ 0`  
**Default:** `0.0`

Bid-ask spread factor. Increases the gap between an agent's bid and ask prices.

**Formula:**
```python
ask_A_in_B = p_min * (1 + spread)
bid_A_in_B = p_max * (1 - spread)
```

**Value Selection:**
- `spread = 0.0`: No spread (quotes equal reservation prices)
- `spread = 0.05-0.10`: Realistic market spread (5-10%)
- `spread > 0.5`: Very wide spread (few trades)

**Effect:**
- `spread = 0`: Maximum trades (agents trade at MRS)
- `spread > 0`: Fewer trades (requires larger surplus to overcome spread)

**Use Case:**
- Model transaction costs
- Create more realistic price discovery
- Reduce trade frequency for analysis

---

### 5.4 Foraging Parameters

#### 5.4.1 `forage_rate`

**Type:** `int ≥ 1`  
**Default:** `1`

Maximum units of resource an agent can harvest per tick from their current cell.

**Value Selection:**
- `forage_rate = 1`: Slow accumulation
- `forage_rate = 2-3`: Moderate accumulation
- `forage_rate > 5`: Fast accumulation (resources less scarce)

**Interaction with Resource Parameters:**
- If `forage_rate > resource_max_amount`: Agents can deplete cells in one tick
- Typically set `forage_rate ≤ resource_max_amount` for multi-tick harvesting

#### 5.4.2 `resource_growth_rate`

**Type:** `int ≥ 0`  
**Default:** `0`

Units of resource that regenerate per tick in non-depleted cells.

**Value Selection:**
- `resource_growth_rate = 0`: No regeneration (finite resources)
- `resource_growth_rate = 1-2`: Slow regeneration
- `resource_growth_rate ≥ forage_rate`: Resources renew as fast as harvested

**Zero (No Regeneration):**
```yaml
params:
  resource_growth_rate: 0  # Resources never regenerate
```

**Equilibrium Regeneration:**
```yaml
params:
  forage_rate: 2
  resource_growth_rate: 2  # Sustainable harvesting
```

#### 5.4.3 `resource_max_amount`

**Type:** `int ≥ 1`  
**Default:** `5`

Maximum amount of resource a cell can hold. Regeneration stops when this limit is reached.

**Value Selection:**
- `resource_max_amount = 5-10`: Typical
- `resource_max_amount < forage_rate`: Cells depleted in one harvest
- `resource_max_amount >> forage_rate`: Multiple harvests per cell

**Cap Behavior:**
```python
if cell.amount < resource_max_amount:
    cell.amount += resource_growth_rate
    cell.amount = min(cell.amount, resource_max_amount)
```

#### 5.4.4 `resource_regen_cooldown`

**Type:** `int ≥ 0`  
**Default:** `5`

Number of ticks a depleted cell must wait before regeneration begins.

**Purpose:** Prevents immediate re-harvesting of the same cell; encourages spatial distribution of foraging.

**Value Selection:**
- `resource_regen_cooldown = 0`: Immediate regeneration
- `resource_regen_cooldown = 5-10`: Typical delay
- `resource_regen_cooldown >> move_budget`: Forces agents to move to new cells

**Behavior:**
```
Cell depleted (amount = 0) at tick T
→ Wait resource_regen_cooldown ticks
→ Regeneration starts at tick T + resource_regen_cooldown
```

---

### 5.5 Resource Claiming System

#### 5.5.1 `enable_resource_claiming`

**Type:** `bool`  
**Default:** `true`

Enables the resource claiming system, which allows agents to "claim" a resource cell during the Decision phase, preventing other agents from targeting it.

**Purpose:** Reduces clustering and failed foraging attempts when multiple agents target the same resource.

**Effect:**
- `true`: Agents claim forage targets; other agents see claimed cells as unavailable
- `false`: No claiming; multiple agents may target same resource (first arrival harvests)

**Recommendation:** Keep `true` for realistic simulations.

#### 5.5.2 `enforce_single_harvester`

**Type:** `bool`  
**Default:** `true`

Ensures only one agent can harvest from a resource cell per tick, even if multiple agents are present.

**Purpose:** Prevents multiple agents from harvesting the same resource simultaneously (which would be physically unrealistic).

**Effect:**
- `true`: First agent at cell harvests; others get nothing
- `false`: All agents at cell can harvest (unrealistic but useful for testing)

**Recommendation:** Keep `true` for realistic simulations.

---

### 5.6 Economic Parameters

#### 5.6.1 `epsilon`

**Type:** `float > 0`  
**Default:** `1e-12`

Small constant for numerical stability in division operations (e.g., calculating MRS).

**Value Selection:**
- `epsilon = 1e-9` to `1e-15`: Typical range
- Smaller: More precision, risk of underflow
- Larger: More stability, less precision

**Use Case:** Prevents division by zero when marginal utilities are near zero.

**Example:**
```python
mrs = mu_A / (mu_B + epsilon)
```

**Recommendation:** Use default unless numerical issues arise.

#### 5.6.2 `beta`

**Type:** `0 < float ≤ 1`  
**Default:** `0.95`

Distance discount factor for scoring forage targets and trade partners.

**Formula:**
```
score = undiscounted_value × beta^distance
```

**Value Selection:**
- `beta = 1.0`: No distance penalty (scores based purely on value)
- `beta = 0.95`: Mild preference for nearby targets
- `beta = 0.8`: Strong preference for nearby targets
- `beta → 0`: Extreme preference for adjacent targets only

**Effect:**
- Higher β: Agents willing to travel farther for better opportunities
- Lower β: Agents prefer nearby targets even if lower value

**Example:**
```yaml
params:
  beta: 0.9  # 10% utility loss per cell of distance
```

**Use Case:**
- Model transportation costs implicitly
- Create spatial market segmentation

---

### 5.7 Money System Parameters

The money system introduces several new parameters for monetary exchange. These are **only relevant** if `exchange_regime` allows monetary trades.

#### 5.7.1 `exchange_regime`

**Type:** `"barter_only" | "money_only" | "mixed" | "mixed_liquidity_gated"`  
**Default:** `"barter_only"`

Controls which types of exchanges are permitted.

**Options:**

| Regime | Barter (A↔B) | Monetary (A↔M, B↔M) | Condition |
|--------|-------------|---------------------|-----------|
| `barter_only` | ✓ | ✗ | Default (backward compatible) |
| `money_only` | ✗ | ✓ | Only monetary trades |
| `mixed` | ✓ | ✓ | All trade types allowed |
| `mixed_liquidity_gated` | Conditional | ✓ | Barter only if money market thin |

**Barter Only (Default):**
```yaml
params:
  exchange_regime: barter_only
```
- Agents trade goods directly (A↔B)
- Money not used (even if agents have it)
- Backward compatible with pre-money scenarios

**Money Only:**
```yaml
params:
  exchange_regime: money_only

initial_inventories:
  M: 100  # REQUIRED for money_only
```
- Agents trade goods for money (A↔M, B↔M)
- Direct barter (A↔B) not allowed
- Demonstrates money as medium of exchange

**Mixed:**
```yaml
params:
  exchange_regime: mixed

initial_inventories:
  M: 100  # REQUIRED for mixed
```
- All trade types allowed (A↔B, A↔M, B↔M)
- Agents choose best trade based on surplus
- Money-first tie-breaking: if surplus equal, prefer A↔M > B↔M > A↔B

**Mixed Liquidity Gated:**
```yaml
params:
  exchange_regime: mixed_liquidity_gated
  liquidity_gate: {min_quotes: 3}

initial_inventories:
  M: 100  # REQUIRED
```
- Monetary trades always allowed
- Barter only allowed if agent observes fewer than `min_quotes` monetary quotes (thin market)
- Models transition from barter to monetary economy as markets thicken

**Requirement:** `money_only`, `mixed`, and `mixed_liquidity_gated` **require** `M` in `initial_inventories`.

#### 5.7.2 `money_mode`

**Type:** `"quasilinear" | "kkt_lambda"`  
**Default:** `"quasilinear"`

Determines how agents compute the marginal utility of money (λ).

**Quasilinear Mode:**
```yaml
params:
  money_mode: quasilinear
  lambda_money: 1.0  # Fixed λ for all agents
```

**Formula:**
```
U_total = U_goods(A, B) + λ · M
```

**Properties:**
- λ is constant (does not change with inventories)
- Simple to understand and configure
- Suitable for pedagogical scenarios

**KKT Lambda Mode:**
```yaml
params:
  money_mode: kkt_lambda
  lambda_update_rate: 0.2
  lambda_bounds: {lambda_min: 1e-6, lambda_max: 1e6}
```

**Behavior:**
- λ is **endogenously estimated** from observed market prices
- Agents update λ based on neighbor quotes
- More realistic but complex

**Update Rule:**
```
λ_new = (1 - α) · λ_old + α · λ_hat
```

where α = `lambda_update_rate` and λ_hat is estimated from perceived prices.

**Recommendation:**
- Use `quasilinear` for demos and teaching
- Use `kkt_lambda` for advanced research scenarios

#### 5.7.3 `money_scale`

**Type:** `int ≥ 1`  
**Default:** `1`

Scale factor for money, representing minor units.

**Examples:**

| `money_scale` | Interpretation | M=100 means |
|---------------|----------------|-------------|
| 1 | No scaling (whole units) | 100 units |
| 10 | Dimes | 10 dollars |
| 100 | Cents | 1 dollar |
| 1000 | Mills | 0.10 dollars |

**Purpose:**
- Allow fractional prices while keeping integer money holdings
- Model real-world currency denominations

**Example:**
```yaml
params:
  money_scale: 100  # Cents

initial_inventories:
  M: 1000  # = $10.00
```

**Trade Example:**
```
Trade: 2 units of A for 150 M
→ Agent pays 150 cents = $1.50
→ Price: 75 cents per A = $0.75/A
```

**Recommendation:** Use `money_scale = 1` for simplicity unless modeling specific currency systems.

#### 5.7.4 `lambda_money`

**Type:** `float > 0`  
**Default:** `1.0`

Fixed marginal utility of money (λ) in `quasilinear` mode.

**Ignored if `money_mode = "kkt_lambda"`.**

**Economic Interpretation:**
- λ = marginal utility of an additional unit of money
- Higher λ: Agent values money more (lower ask prices in M)
- Lower λ: Agent values money less (higher bid prices in M)

**Example:**
```yaml
params:
  money_mode: quasilinear
  lambda_money: 2.0  # All agents value money highly
```

**Per-Agent Override:**
```yaml
initial_inventories:
  M: [100, 100, 100]
  lambda_money: [2.0, 1.0, 0.5]  # Heterogeneous λ
```

**Effect on Prices:**
```
ask_A_in_M = MU_A / λ

High λ (e.g., 2.0): Low ask prices (willing to sell for less money)
Low λ (e.g., 0.5): High ask prices (demand more money to sell)
```

**Use Case:**
- Model heterogeneous money preferences
- Create trading opportunities based on different money valuations

#### 5.7.5 `money_utility_form`

**Type:** `string`  
**Default:** `"linear"`  
**Options:** `"linear"`, `"log"`

Controls the functional form of money utility component.

**Linear Form** (default):
```
U_total = U_goods(A, B) + λ·M
∂U/∂M = λ (constant)
```

**Logarithmic Form**:
```
U_total = U_goods(A, B) + λ·log(M + M_0)
∂U/∂M = λ/(M + M_0) (diminishing)
```

**Key Differences:**
- **Linear**: Constant marginal utility of money, no wealth effects
- **Log**: Diminishing marginal utility, captures income effects

**Example:**
```yaml
params:
  money_utility_form: "log"
  M_0: 10.0  # Shift parameter for log form
```

**Economic Implications:**

With **linear** money:
- All agents with same goods holdings offer identical money prices
- Wealth doesn't affect willingness to pay
- Simpler, good for basic pedagogy

With **log** money:
- Wealthy agents (high M) have lower MU_money → willing to pay MORE for goods
- Poor agents (low M) have higher MU_money → demand MORE money when selling
- Creates realistic income/wealth effects in trade
- Rich agents dominate monetary markets

**Use Case:**
- Use `linear` for introductory scenarios and basic demonstrations
- Use `log` for realistic simulations showing wealth inequality effects
- See `scenarios/demos/demo_log_money.yaml` for complete example

#### 5.7.6 `M_0`

**Type:** `float ≥ 0`  
**Default:** `0.0`

Shift parameter for logarithmic money utility.

**Ignored if `money_utility_form = "linear"`.**

**Purpose:**
- Prevents log(0) singularity when M=0
- Calibrates curvature of diminishing marginal utility
- Analogous to subsistence parameter in Stone-Geary utility

**Effect:**
```
MU_money = λ/(M + M_0)

M_0 = 0:   MU varies from infinity (M=0) to very small (large M)
M_0 = 10:  MU varies from λ/10 (M=0) to smaller values (large M)
M_0 = 50:  Flatter curve, less dramatic wealth effects
```

**Guidelines:**
- **M_0 = 0**: Maximum wealth sensitivity (use epsilon guard at M=0)
- **M_0 = 5-20**: Moderate wealth effects (RECOMMENDED for realistic scenarios)
- **M_0 > 50**: Mild wealth effects, approaching linear behavior

**Example:**
```yaml
params:
  money_utility_form: "log"
  M_0: 10.0  # Subsistence money level

initial_inventories:
  M: [20, 500, 100]  # Poor, rich, middle agents
```

**Result:** 
- Poor agent (M=20): MU_money = λ/30 = 0.033 (high)
- Rich agent (M=500): MU_money = λ/510 = 0.002 (low)
- Rich agent willing to pay ~16× more money for same goods!

**Agent-Specific M_0** (optional):
```yaml
initial_inventories:
  M_0: [5.0, 10.0, 15.0]  # Per-agent shift parameters
```

#### 5.7.7 `lambda_update_rate`

**Type:** `0 ≤ float ≤ 1`  
**Default:** `0.2`

Smoothing factor (α) for updating λ in `kkt_lambda` mode.

**Ignored if `money_mode = "quasilinear"`.**

**Update Formula:**
```
λ_new = (1 - α) · λ_old + α · λ_hat
```

**Value Selection:**
- `alpha = 0.0`: No updating (λ stays constant)
- `alpha = 0.1-0.3`: Slow adaptation (typical)
- `alpha = 1.0`: Immediate jump to new estimate (unstable)

**Example:**
```yaml
params:
  money_mode: kkt_lambda
  lambda_update_rate: 0.2  # 20% weight on new estimate
```

**Trade-off:**
- Higher α: Faster adaptation to price changes, more volatility
- Lower α: Slower adaptation, more stability

#### 5.7.8 `lambda_bounds`

**Type:** `dict[str, float]`  
**Default:** `{lambda_min: 1e-6, lambda_max: 1e6}`

Minimum and maximum allowed values for λ in `kkt_lambda` mode.

**Ignored if `money_mode = "quasilinear"`.**

**Purpose:** Prevent extreme λ values that could cause numerical instability.

**Example:**
```yaml
params:
  money_mode: kkt_lambda
  lambda_bounds:
    lambda_min: 0.01
    lambda_max: 100.0
```

**Constraints:**
- `lambda_min < lambda_max`
- `lambda_min > 0` (λ must be positive)

**Effect:**
```python
if λ_new < lambda_min:
    λ_new = lambda_min
elif λ_new > lambda_max:
    λ_new = lambda_max
```

#### 5.7.9 `liquidity_gate`

**Type:** `dict[str, int]`  
**Default:** `{min_quotes: 3}`

Configuration for `mixed_liquidity_gated` exchange regime.

**Only relevant if `exchange_regime = "mixed_liquidity_gated"`.**

**Parameter:**
- `min_quotes`: Minimum number of unique monetary quotes an agent must observe for the market to be considered "thick"

**Behavior:**
```python
if agent.num_monetary_quotes >= min_quotes:
    # Market is thick → disable barter
    allowed_pairs = ["A<->M", "B<->M"]
else:
    # Market is thin → allow barter fallback
    allowed_pairs = ["A<->M", "B<->M", "A<->B"]
```

**Example:**
```yaml
params:
  exchange_regime: mixed_liquidity_gated
  liquidity_gate:
    min_quotes: 5  # Need 5+ monetary quotes to disable barter
```

**Value Selection:**
- `min_quotes = 0`: Barter never allowed (equivalent to `money_only`)
- `min_quotes = 3-5`: Typical threshold
- `min_quotes >> num_agents`: Barter always allowed (equivalent to `mixed`)

**Use Case:**
- Model emergence of money (barter → money transition)
- Study how market thickness affects trade type distribution

#### 5.7.8 `earn_money_enabled`

**Type:** `bool`  
**Default:** `false`

**Status:** Placeholder for future features. Currently unused.

**Future Purpose:** Allow agents to earn money through activities other than trade (e.g., labor, production).

**Current Effect:** None. Leave as `false`.

---

## 6. Resource Seeding

### 6.1 Overview

The `resource_seed` section defines how resources are distributed on the grid at initialization.

### 6.2 Structure

```yaml
resource_seed:
  density: float       # Probability [0,1] of a cell having a resource
  amount: int | dist   # Amount of resource in seeded cells
```

### 6.3 `density`

**Type:** `0 ≤ float ≤ 1`  
**Required:** Yes

Probability that any given cell will have a resource.

**Value Selection:**
- `density = 0.0`: No resources (trade-only scenario)
- `density = 0.1-0.3`: Sparse resources (competition for foraging)
- `density = 0.5`: Half the cells have resources
- `density = 1.0`: Every cell has a resource (resource-rich)

**Example:**
```yaml
N: 20  # 400 cells

resource_seed:
  density: 0.2  # Expected: 80 cells with resources (20% of 400)
```

**Stochastic:** Actual count varies due to random seeding (use `--seed` for reproducibility).

### 6.4 `amount`

**Type:** `int | distribution`  
**Required:** Yes (if `density > 0`)

Amount of resource in each seeded cell.

#### 6.4.1 Fixed Integer

```yaml
resource_seed:
  density: 0.3
  amount: 5  # Every seeded cell has exactly 5 units
```

#### 6.4.2 Distribution (Planned)

**Note:** Defined in schema but not widely used. For now, use fixed integer.

```yaml
resource_seed:
  density: 0.3
  amount: {uniform_int: [3, 7]}  # Random amount in [3,7] per cell
```

### 6.5 Resource Types

Resources are **currently homogeneous**. In the future, the system may support multiple resource types (e.g., A-only cells, B-only cells).

**Current Behavior:** All resources are of the same type (typically "A" or "B" based on cell position or random assignment).

---

## 7. Mode Scheduling

### 7.1 Overview

The `mode_schedule` section enables **temporal control** over agent behavior. Agents alternate between "forage" mode (only foraging allowed) and "trade" mode (only trading allowed).

**Optional:** If omitted, agents are in "both" mode (can forage and trade simultaneously).

### 7.2 Structure

```yaml
mode_schedule:
  type: "global_cycle"              # Scheduling pattern
  forage_ticks: int                 # Duration of forage mode
  trade_ticks: int                  # Duration of trade mode
  start_mode: "forage" | "trade"    # Optional: initial mode (default: "forage")
```

### 7.3 `type`

**Type:** `"global_cycle" | "agent_specific" | "spatial_zones"`  
**Required:** Yes (if `mode_schedule` present)

**Implemented:** `"global_cycle"` only. Other types planned for future.

**Global Cycle:** All agents follow the same mode schedule synchronized globally.

```yaml
mode_schedule:
  type: global_cycle
```

### 7.4 `forage_ticks`

**Type:** `int > 0`  
**Required:** Yes

Number of consecutive ticks in forage mode.

**Example:**
```yaml
mode_schedule:
  forage_ticks: 20  # Agents forage for 20 ticks
```

### 7.5 `trade_ticks`

**Type:** `int > 0`  
**Required:** Yes

Number of consecutive ticks in trade mode.

**Example:**
```yaml
mode_schedule:
  trade_ticks: 30  # Then trade for 30 ticks
```

### 7.6 `start_mode`

**Type:** `"forage" | "trade"`  
**Default:** `"forage"`

Initial mode at tick 0.

**Example:**
```yaml
mode_schedule:
  start_mode: trade  # Start with trading instead of foraging
```

### 7.7 Mode Cycle Example

```yaml
mode_schedule:
  type: global_cycle
  forage_ticks: 15
  trade_ticks: 20
  start_mode: forage
```

**Timeline:**
```
Tick 0-14:   forage mode (15 ticks)
Tick 15-34:  trade mode (20 ticks)
Tick 35-49:  forage mode (15 ticks)
Tick 50-69:  trade mode (20 ticks)
...
```

**Cycle Length:** `forage_ticks + trade_ticks = 35 ticks`

### 7.8 Mode vs. Exchange Regime

**Two-Layer Control:**

| Layer | Control | Parameters | Values |
|-------|---------|-----------|---------|
| **Mode** | **When** agents trade | `mode_schedule` | `forage`, `trade`, `both` |
| **Regime** | **What** trade types allowed | `exchange_regime` | `barter_only`, `money_only`, `mixed` |

**Independence:** Mode and regime are orthogonal and can be combined.

**Example:**
```yaml
mode_schedule:
  type: global_cycle
  forage_ticks: 10
  trade_ticks: 10

params:
  exchange_regime: mixed  # When trading, allow all trade types
```

**Behavior:**
- Ticks 0-9: Forage only (no trading)
- Ticks 10-19: Trade only (A↔B, A↔M, B↔M all allowed)
- Ticks 20-29: Forage only
- etc.

**See:** `scenarios/demos/demo_04_mode_schedule.yaml`

### 7.9 Mode Effects

**Forage Mode:**
- Agents target resources
- Trading phase skipped (pairs dissolved if mode switches)
- Movement toward resources
- Foraging phase executes normally

**Trade Mode:**
- Agents target trade partners
- Foraging phase skipped
- Movement toward partners
- Trading phase executes normally

**Both Mode (No Schedule):**
- Agents decide between trading and foraging each tick
- Both phases execute
- Default behavior if `mode_schedule` omitted

### 7.10 Pairing Integrity

When mode switches from trade → forage, all agent pairs are **unpaired** (to prevent trade attempts during forage mode).

**Telemetry:** Unpair events logged with reason `"mode_switch"` in `pairings` table.

---

## 8. Complete Examples

### 8.1 Minimal Barter Scenario

```yaml
schema_version: 1
name: "Minimal Barter"
N: 10
agents: 5

initial_inventories:
  A: 10
  B: 10

utilities:
  mix:
    - type: ces
      weight: 1.0
      params:
        rho: 0.5
        wA: 0.6
        wB: 0.4

resource_seed:
  density: 0.2
  amount: 5

# All params use defaults
```

### 8.2 Money-Only Economy

```yaml
schema_version: 1
name: "Money Economy"
N: 15
agents: 10

initial_inventories:
  A: [10, 5, 0, 8, 2, 0, 9, 4, 1, 7]
  B: [0, 5, 10, 2, 8, 9, 0, 4, 7, 1]
  M: 100  # All agents get 100 money

utilities:
  mix:
    - type: ces
      weight: 1.0
      params:
        rho: 0.4
        wA: 0.6
        wB: 0.4

params:
  vision_radius: 15
  interaction_radius: 1
  move_budget_per_tick: 2
  dA_max: 3
  
  exchange_regime: money_only
  money_mode: quasilinear
  money_scale: 1
  lambda_money: 1.0

resource_seed:
  density: 0.15
  amount: 3
```

### 8.3 Mixed Regime with Mode Schedule

```yaml
schema_version: 1
name: "Mixed Economy with Cycles"
N: 20
agents: 15

mode_schedule:
  type: global_cycle
  forage_ticks: 15
  trade_ticks: 20
  start_mode: forage

initial_inventories:
  A: [10, 5, 0, 8, 2, 0, 9, 4, 1, 7, 0, 6, 3, 0, 10]
  B: [0, 5, 10, 2, 8, 9, 0, 4, 7, 1, 10, 3, 6, 8, 0]
  M: 120

utilities:
  mix:
    - type: ces
      weight: 0.6
      params:
        rho: 0.4
        wA: 0.6
        wB: 0.4
    
    - type: linear
      weight: 0.4
      params:
        vA: 2.0
        vB: 1.5

params:
  spread: 0.08
  vision_radius: 20
  interaction_radius: 1
  move_budget_per_tick: 2
  dA_max: 4
  forage_rate: 2
  
  exchange_regime: mixed
  money_mode: quasilinear
  money_scale: 1
  lambda_money: 1.0

resource_seed:
  density: 0.3
  amount: 5
```

### 8.4 Subsistence Economy

```yaml
schema_version: 1
name: "Subsistence Traders"
N: 25
agents: 15

initial_inventories:
  A: [8, 9, 10, 12, 15, 20, 25, 30, 35, 40, 22, 28, 18, 32, 26]
  B: [6, 7, 8, 10, 12, 15, 20, 25, 30, 35, 18, 22, 14, 28, 20]

utilities:
  mix:
    - type: stone_geary
      weight: 1.0
      params:
        alpha_A: 0.6
        alpha_B: 0.4
        gamma_A: 5.0   # Subsistence: need at least 5 A
        gamma_B: 3.0   # Subsistence: need at least 3 B

params:
  vision_radius: 8
  interaction_radius: 1
  move_budget_per_tick: 1
  dA_max: 5
  forage_rate: 2
  resource_growth_rate: 1
  resource_max_amount: 8

resource_seed:
  density: 0.35
  amount: 4
```

### 8.5 Heterogeneous Money Valuations

```yaml
schema_version: 1
name: "Heterogeneous Lambda"
N: 10
agents: 3

initial_inventories:
  A: [50, 200, 100]
  B: [200, 50, 100]
  M: [1000, 1000, 500]
  lambda_money: [2.0, 0.5, 1.0]  # Agent-specific

utilities:
  mix:
    - type: ces
      weight: 0.33
      params: {rho: 0.9, wA: 0.8, wB: 0.2}
    
    - type: ces
      weight: 0.33
      params: {rho: 0.5, wA: 0.2, wB: 0.8}
    
    - type: ces
      weight: 0.34
      params: {rho: -0.5, wA: 0.7, wB: 0.3}

params:
  exchange_regime: mixed
  money_mode: quasilinear
  money_scale: 10
  vision_radius: 10
  dA_max: 50

resource_seed:
  density: 0.1
  amount: 5
```

---

## 9. Validation Rules

### 9.1 Validation Process

When a scenario is loaded (`load_scenario(path)`), the following validations occur:

1. **YAML Parsing:** File must be valid YAML
2. **Schema Parsing:** Required fields must be present
3. **Type Checking:** Fields must match expected types
4. **Scenario Validation:** `scenario.validate()` checks constraints
5. **Cross-Field Validation:** Parameter interactions validated

**Failure:** Any validation error raises `ValueError` with a descriptive message.

### 9.2 Top-Level Constraints

- `N > 0`: Grid size must be positive
- `agents > 0`: Agent count must be positive
- `schema_version == 1`: Only version 1 supported

### 9.3 Initial Inventory Constraints

- All quantities must be `≥ 0` (non-negative integers)
- If using explicit lists: list length must equal `agents`
- If `exchange_regime` ∈ {`money_only`, `mixed`, `mixed_liquidity_gated`}: `M` **required**
- If using `stone_geary` utility:
  - `initial_A > gamma_A` for all agents
  - `initial_B > gamma_B` for all agents

### 9.4 Utility Mix Constraints

- `utilities.mix` must contain at least one utility function
- Sum of `weight` must equal 1.0 (within 1e-6 tolerance)
- Each `weight ≥ 0`

**Per Utility Type:**

**CES:**
- `rho ≠ 1.0`
- `wA, wB > 0`

**Linear:**
- `vA, vB > 0`

**Quadratic:**
- `A_star, B_star > 0`
- `sigma_A, sigma_B > 0`
- `gamma ≥ 0`

**Translog:**
- `alpha_A, alpha_B > 0` (for monotonicity)

**Stone-Geary:**
- `alpha_A, alpha_B > 0`
- `gamma_A, gamma_B ≥ 0`
- Initial inventories validated (see above)

### 9.5 Parameter Constraints

**Spatial:**
- `spread ≥ 0`
- `vision_radius ≥ 0`
- `interaction_radius ≥ 0`
- `move_budget_per_tick > 0`

**Trading:**
- `dA_max > 0`
- `trade_cooldown_ticks ≥ 0`

**Foraging:**
- `forage_rate > 0`
- `resource_growth_rate ≥ 0`
- `resource_max_amount > 0`
- `resource_regen_cooldown ≥ 0`

**Economic:**
- `epsilon > 0`
- `0 < beta ≤ 1`

**Money:**
- `money_scale ≥ 1`
- `lambda_money > 0`
- `0 ≤ lambda_update_rate ≤ 1`
- `lambda_bounds.lambda_min < lambda_bounds.lambda_max`
- `lambda_bounds.lambda_min > 0`
- `liquidity_gate.min_quotes ≥ 0`

### 9.6 Resource Seed Constraints

- `0 ≤ density ≤ 1`
- If `density > 0` and `amount` is int: `amount > 0`

### 9.7 Mode Schedule Constraints

- `forage_ticks > 0`
- `trade_ticks > 0`
- `type == "global_cycle"` (only implemented type)

---

## 10. Common Patterns & Best Practices

### 10.1 Scenario Design Patterns

#### 10.1.1 Pedagogical Scenarios

**Goal:** Demonstrate a specific economic concept clearly.

**Pattern:**
- Small agent count (5-15)
- Simple utility (single type, e.g., CES with rho=0.5)
- Clear heterogeneity (explicit inventory lists)
- Descriptive name and comments

**Example:** `scenarios/demos/demo_01_simple_money.yaml`

#### 10.1.2 Performance Benchmarks

**Goal:** Measure computational performance under varying load.

**Pattern:**
- Vary grid size and agent count
- Minimal complexity (fast per-tick operations)
- No mode schedule (both mode)
- Fixed random seed for reproducibility

**Example:** `scenarios/perf_exchange_only.yaml`

#### 10.1.3 Empirical Estimation

**Goal:** Generate data for econometric analysis.

**Pattern:**
- Heterogeneous agents (multiple utility types)
- Long run time (100+ ticks)
- Regenerating resources (equilibrium behavior)
- Translog utility for flexible functional form

**Example:** `scenarios/translog_estimation_demo.yaml`

#### 10.1.4 Spatial Studies

**Goal:** Analyze spatial market structure.

**Pattern:**
- Large grid (N=40+)
- Lower agent density (<5%)
- Limited vision radius (local information)
- Clustered initial positions (future feature)

**Example:** `scenarios/demos/demo_05_liquidity_zones.yaml`

### 10.2 Parameter Selection Guidelines

#### 10.2.1 Vision Radius

- **Global information:** `vision_radius = N`
- **Local markets:** `vision_radius = N/4 to N/2`
- **Extreme locality:** `vision_radius = 1-5`

**Trade-off:** Larger vision → more trades but less spatial variation.

#### 10.2.2 Move Budget

- **Slow economy:** `move_budget_per_tick = 1`
- **Moderate:** `move_budget_per_tick = 2-3`
- **Fast (large grids):** `move_budget_per_tick = N/10`

**Rule of Thumb:** `move_budget ≈ vision_radius / 5` (takes ~5 ticks to reach visible targets).

#### 10.2.3 Trade Size (dA_max)

- **Small trades:** `dA_max = 1-3`
- **Typical:** `dA_max = 5-10`
- **Large trades:** `dA_max = 20+`

**Constraint:** Should be ≤ typical inventory levels / 2 (to avoid inventory exhaustion).

#### 10.2.4 Resource Density

- **Resource-poor:** `density = 0.1-0.2`
- **Moderate:** `density = 0.3-0.4`
- **Resource-rich:** `density = 0.5+`

**Balance:** Higher density → more foraging, less trading (agents self-sufficient).

#### 10.2.5 Spread

- **No transaction costs:** `spread = 0.0`
- **Realistic:** `spread = 0.05-0.15`
- **High friction:** `spread = 0.3+`

**Effect:** Higher spread → fewer trades (requires larger surplus to overcome).

### 10.3 Common Pitfalls

#### 10.3.1 Missing Money in Monetary Regimes

**Error:**
```yaml
params:
  exchange_regime: money_only

initial_inventories:
  A: 10
  B: 10
  # M missing!
```

**Solution:** Add `M` to initial inventories:
```yaml
initial_inventories:
  A: 10
  B: 10
  M: 100
```

#### 10.3.2 Utility Weights Don't Sum to 1.0

**Error:**
```yaml
utilities:
  mix:
    - type: ces
      weight: 0.5  # ...
    - type: linear
      weight: 0.4  # Sum = 0.9 ≠ 1.0
```

**Solution:**
```yaml
utilities:
  mix:
    - type: ces
      weight: 0.5
    - type: linear
      weight: 0.5  # Sum = 1.0 ✓
```

#### 10.3.3 Stone-Geary Inventories Below Subsistence

**Error:**
```yaml
utilities:
  mix:
    - type: stone_geary
      weight: 1.0
      params:
        gamma_A: 5.0
        gamma_B: 3.0

initial_inventories:
  A: 5  # 5 ≤ gamma_A (ERROR)
  B: 6
```

**Solution:**
```yaml
initial_inventories:
  A: 6  # 6 > 5 ✓
  B: 4  # 4 > 3 ✓
```

#### 10.3.4 List Length Mismatch

**Error:**
```yaml
agents: 5

initial_inventories:
  A: [10, 5, 0]  # Only 3 values, but 5 agents!
```

**Solution:**
```yaml
initial_inventories:
  A: [10, 5, 0, 8, 2]  # 5 values ✓
```

Or use fixed integer:
```yaml
initial_inventories:
  A: 10  # All agents get 10
```

#### 10.3.5 CES with rho = 1.0

**Error:**
```yaml
- type: ces
  weight: 1.0
  params:
    rho: 1.0  # Mathematical singularity!
```

**Solution:** Use a value slightly different from 1.0:
```yaml
params:
  rho: 0.999  # Or 1.001
```

### 10.4 Reproducibility

**Use Seeds for Reproducibility:**

```bash
python launcher.py scenarios/my_scenario.yaml --seed 42
```

**Deterministic Elements:**
- Agent movement
- Trade order (sorted by agent ID)
- Pairing algorithm

**Stochastic Elements (seed-controlled):**
- Initial agent positions (if not specified)
- Resource placement (based on `density`)
- Utility assignment (based on `weight` proportions)

**Best Practice:** Always specify `--seed` for reproducible experiments.

### 10.5 Debugging Scenarios

**Use Telemetry:**

```bash
# Run scenario
python launcher.py scenarios/my_scenario.yaml --max-ticks 20 --seed 42

# View logs
python view_logs.py
```

**Key Telemetry Tables:**
- `agent_snapshots`: Agent states over time
- `trades`: All successful trades
- `decisions`: Agent decision rationale
- `pairings`: Pairing events

**Common Issues:**

**No trades occurring:**
- Check `spread` (too high?)
- Check `interaction_radius` (agents not getting close?)
- Check inventories (agents need complementary endowments)
- Check `exchange_regime` and `mode_schedule` (trading allowed?)

**Agents not moving:**
- Check `move_budget_per_tick > 0`
- Check `vision_radius` (can agents see targets?)

**Few monetary trades in mixed regime:**
- Check `lambda_money` values (similar λ → less monetary trade opportunity)
- Use heterogeneous λ (explicit list in `initial_inventories.lambda_money`)

---

## Appendix A: Quick Reference Tables

### A.1 All Parameters

| Parameter | Type | Default | Range/Values |
|-----------|------|---------|--------------|
| **Top-Level** |
| `schema_version` | int | - | 1 |
| `name` | string | - | Any |
| `N` | int | - | > 0 |
| `agents` | int | - | > 0 |
| **Inventories** |
| `initial_inventories.A` | int \| list | - | ≥ 0 |
| `initial_inventories.B` | int \| list | - | ≥ 0 |
| `initial_inventories.M` | int \| list | - | ≥ 0 |
| `initial_inventories.lambda_money` | list[float] | `params.lambda_money` | > 0 |
| **Resource Seed** |
| `resource_seed.density` | float | - | [0, 1] |
| `resource_seed.amount` | int \| dist | - | > 0 |
| **Params: Spatial** |
| `vision_radius` | int | 5 | ≥ 0 |
| `interaction_radius` | int | 1 | ≥ 0 |
| `move_budget_per_tick` | int | 1 | > 0 |
| `spread` | float | 0.0 | ≥ 0 |
| **Params: Trading** |
| `dA_max` | int | 5 | > 0 |
| `trade_cooldown_ticks` | int | 5 | ≥ 0 |
| **Params: Foraging** |
| `forage_rate` | int | 1 | > 0 |
| `resource_growth_rate` | int | 0 | ≥ 0 |
| `resource_max_amount` | int | 5 | > 0 |
| `resource_regen_cooldown` | int | 5 | ≥ 0 |
| **Params: Resource Claiming** |
| `enable_resource_claiming` | bool | true | true, false |
| `enforce_single_harvester` | bool | true | true, false |
| **Params: Economic** |
| `epsilon` | float | 1e-12 | > 0 |
| `beta` | float | 0.95 | (0, 1] |
| **Params: Money** |
| `exchange_regime` | string | barter_only | See §5.7.1 |
| `money_mode` | string | quasilinear | quasilinear, kkt_lambda |
| `money_utility_form` | string | linear | linear, log |
| `M_0` | float | 0.0 | ≥ 0 |
| `money_scale` | int | 1 | ≥ 1 |
| `lambda_money` | float | 1.0 | > 0 |
| `lambda_update_rate` | float | 0.2 | [0, 1] |
| `lambda_bounds` | dict | See §5.7.8 | min < max, min > 0 |
| `liquidity_gate` | dict | {min_quotes: 3} | min_quotes ≥ 0 |
| `earn_money_enabled` | bool | false | true, false (unused) |
| **Mode Schedule** |
| `mode_schedule.type` | string | - | global_cycle |
| `mode_schedule.forage_ticks` | int | - | > 0 |
| `mode_schedule.trade_ticks` | int | - | > 0 |
| `mode_schedule.start_mode` | string | forage | forage, trade |

### A.2 Utility Function Parameters

| Utility Type | Parameters | Constraints |
|--------------|-----------|-------------|
| **ces** | `rho`, `wA`, `wB` | rho ≠ 1, wA > 0, wB > 0 |
| **linear** | `vA`, `vB` | vA > 0, vB > 0 |
| **quadratic** | `A_star`, `B_star`, `sigma_A`, `sigma_B`, `gamma` | All > 0, gamma ≥ 0 |
| **translog** | `alpha_0`, `alpha_A`, `alpha_B`, `beta_AA`, `beta_BB`, `beta_AB` | alpha_A > 0, alpha_B > 0 |
| **stone_geary** | `alpha_A`, `alpha_B`, `gamma_A`, `gamma_B` | alpha > 0, gamma ≥ 0, init_inv > gamma |

---

## Appendix B: Related Documentation

- **Type Specifications:** [`docs/4_typing_overview.md`](4_typing_overview.md) - Authoritative type definitions
- **Schema Implementation:** [`src/scenarios/schema.py`](../src/scenarios/schema.py) - Python dataclasses
- **Loader Implementation:** [`src/scenarios/loader.py`](../src/scenarios/loader.py) - YAML parsing logic
- **Demo Scenarios:** [`scenarios/demos/`](../scenarios/demos/) - Annotated examples
- **Technical Manual:** [`docs/2_technical_manual.md`](2_technical_manual.md) - Simulation mechanics
- **Project Overview:** [`docs/1_project_overview.md`](1_project_overview.md) - High-level architecture

---

## Changelog

**2025-10-22:** Initial version - Comprehensive scenario configuration reference created

---

**End of Scenario Configuration Guide**

