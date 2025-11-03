# Scenario Configuration

Scenarios are YAML files that configure simulations. Understanding the structure helps create meaningful experiments.

## Minimal Scenario Template

```yaml
schema_version: 1
name: "my_scenario"

# Grid and agent basics
grid_size: 32                    # NxN grid
num_agents: 10                   # Number of agents

# Protocol selection (institutional rules)
search_protocol: "myopic"        # How agents find partners
matching_protocol: "greedy_surplus"  # How pairs form
bargaining_protocol: "split_difference"  # How prices negotiate

# Initial inventories
initial_inventories:
  A: {uniform_int: [5, 15]}      # Random uniform distribution
  B: {uniform_int: [5, 15]}

# Utility functions
utilities:
  mix:
    - type: ces
      weight: 1.0
      params:
        rho: -0.5
        wA: 1.0
        wB: 1.0

# Resources
resource_seed:
  density: 0.15                  # Fraction of cells with resources
  amount: 3                      # Initial amount per resource cell
```

## Protocol Selection

### Search Protocols

**`myopic`** (default, recommended):
- Evaluates visible neighbors, selects highest utility gain
- Distance-discounted scoring: `score = surplus × β^distance`
- Economically rational

**`random_walk`**:
- Random movement
- No information usage
- Baseline for comparison

**`legacy`**:
- Original distance-discounted implementation
- Kept for backward compatibility

### Matching Protocols

**`greedy_surplus`** (recommended):
- Ranks all potential pairs by total surplus
- Greedily assigns highest-surplus pairs first
- Welfare-maximizing

**`random`**:
- Random pairing
- No preference consideration
- Baseline for comparison

**`legacy`**:
- Three-pass algorithm (mutual consent + fallback)
- Original implementation

### Bargaining Protocols

**`split_difference`** (recommended):
- Divides surplus equally
- Fair division
- Price = midpoint of reservation bounds

**`take_it_or_leave_it`**:
- One agent makes ultimatum offer
- Strategic power asymmetry
- Tests bargaining power effects

**`legacy`**:
- Compensating block search
- Original implementation

## Inventory Specifications

### Fixed values
```yaml
initial_inventories:
  A: 10           # All agents start with 10 A
  B: 5            # All agents start with 5 B
```

### Per-agent lists
```yaml
initial_inventories:
  A: [10, 8, 6, 12, 9]  # Explicit per-agent values
  B: [5, 7, 9, 3, 6]
```

### Random distributions
```yaml
initial_inventories:
  A: {uniform_int: [5, 15]}      # Random uniform integers
  B: {uniform_real: [5.0, 15.0]}  # Random uniform floats (rounded)
```

## Utility Configuration

### Homogeneous population
```yaml
utilities:
  mix:
    - type: ces
      weight: 1.0
      params: {rho: -0.5, wA: 1.0, wB: 1.0}
```

### Heterogeneous population
```yaml
utilities:
  mix:
    - type: ces
      weight: 0.6          # 60% CES agents
      params: {rho: -0.5, wA: 1.0, wB: 1.0}
    
    - type: linear
      weight: 0.3          # 30% Linear agents
      params: {vA: 1.0, vB: 1.5}
    
    - type: quadratic
      weight: 0.1          # 10% Quadratic agents
      params: {A_star: 10.0, B_star: 10.0, sigma_A: 0.5, sigma_B: 0.5, gamma: 0.0}
```

**Note**: Weights must sum to 1.0

### Utility Parameters

**CES**:
```yaml
params:
  rho: -0.5      # Elasticity (-∞ to ∞)
  wA: 1.0        # Weight on good A
  wB: 1.0        # Weight on good B
```

**Linear**:
```yaml
params:
  vA: 1.0        # Per-unit value of A
  vB: 1.5        # Per-unit value of B
```

**Quadratic**:
```yaml
params:
  A_star: 10.0   # Bliss point for A
  B_star: 10.0   # Bliss point for B
  sigma_A: 0.5   # Curvature for A
  sigma_B: 0.5   # Curvature for B
  gamma: 0.0     # Cross-curvature
```

**Translog**:
```yaml
params:
  alpha_0: 0.0
  alpha_A: 0.5
  alpha_B: 0.5
  beta_AA: -0.1
  beta_BB: -0.1
  beta_AB: 0.05
```

**Stone-Geary**:
```yaml
params:
  alpha_A: 0.6      # Preference weight for A
  alpha_B: 0.4      # Preference weight for B
  gamma_A: 2.0      # Subsistence level for A
  gamma_B: 2.0      # Subsistence level for B
```

## Scenario Parameters

### Trading parameters
```yaml
params:
  spread: 0.0                    # Bid-ask spread (0 = true reservation prices)
  trade_cooldown_ticks: 5        # Cooldown after failed trade
  interaction_radius: 1          # Must be within this distance to trade
```

### Spatial parameters
```yaml
params:
  vision_radius: 5               # How far agents can see
  move_budget_per_tick: 1        # Movement speed
  beta: 0.95                     # Time discount factor (distance discounting)
```

### Resource parameters
```yaml
params:
  forage_rate: 1                 # Units harvested per tick
  resource_growth_rate: 1        # Regeneration rate
  resource_max_amount: 5         # Maximum resource per cell
  resource_regen_cooldown: 5     # Ticks before regeneration starts
  enable_resource_claiming: true # Claiming system
  enforce_single_harvester: true # One harvester per cell per tick
```

### Mode scheduling
```yaml
mode_schedule:
  intervals:
    - mode: "forage"
      duration: 20               # First 20 ticks: forage only
    - mode: "trade"
      duration: 80               # Next 80 ticks: trade only
    - mode: "both"
      duration: null             # Rest of simulation: both activities
```

Modes:
- `forage`: Only foraging, no trading
- `trade`: Only trading, no foraging
- `both`: Agents choose based on expected utility

## Example Scenarios

### Two-agent Edgeworth box
```yaml
name: "edgeworth_box"
grid_size: 10
num_agents: 2

search_protocol: "myopic"
matching_protocol: "greedy_surplus"
bargaining_protocol: "split_difference"

initial_inventories:
  A: [10, 0]    # Agent 0: all A
  B: [0, 10]    # Agent 1: all B

utilities:
  mix:
    - type: ces
      weight: 1.0
      params: {rho: 0.0, wA: 0.5, wB: 0.5}  # Cobb-Douglas

resource_seed:
  density: 0.0  # No resources (pure exchange)
  amount: 0
```

### Large market comparison
```yaml
name: "protocol_comparison_100agents"
grid_size: 50
num_agents: 100

# Run 3 times with different protocols to compare
search_protocol: "myopic"      # Try: "random_walk"
matching_protocol: "greedy_surplus"  # Try: "random"
bargaining_protocol: "split_difference"  # Try: "take_it_or_leave_it"

initial_inventories:
  A: {uniform_int: [5, 15]}
  B: {uniform_int: [5, 15]}

utilities:
  mix:
    - type: ces
      weight: 0.5
      params: {rho: -0.5, wA: 1.0, wB: 1.0}
    - type: linear
      weight: 0.5
      params: {vA: 1.0, vB: 1.0}

resource_seed:
  density: 0.10
  amount: 5
```

### Subsistence economy
```yaml
name: "subsistence_test"
grid_size: 20
num_agents: 10

search_protocol: "myopic"
matching_protocol: "greedy_surplus"
bargaining_protocol: "split_difference"

initial_inventories:
  A: {uniform_int: [3, 12]}  # Some near subsistence
  B: {uniform_int: [3, 12]}

utilities:
  mix:
    - type: stone_geary
      weight: 1.0
      params:
        alpha_A: 0.6
        alpha_B: 0.4
        gamma_A: 2.0   # Subsistence: must have > 2 A
        gamma_B: 2.0   # Subsistence: must have > 2 B

resource_seed:
  density: 0.15
  amount: 3
```

## Validation

Scenarios are validated on load:
- Weights must sum to 1.0
- Grid size must be positive
- Initial inventories match agent count
- Stone-Geary: initial inventories > subsistence levels

**Validation errors** are raised as `ValueError` with specific message.

## Testing Scenarios

Create minimal scenarios in test code:
```python
from tests.helpers.scenarios import create_minimal_scenario

scenario = create_minimal_scenario(
    num_agents=5,
    grid_size=20,
    utility_type='ces',
    utility_params={'rho': -0.5, 'wA': 1.0, 'wB': 1.0},
    search_protocol='myopic',
    matching_protocol='greedy_surplus',
    bargaining_protocol='split_difference'
)
```

## Scenario Organization

```
scenarios/
├── demos/           # Pedagogical examples
├── baseline/        # Benchmark scenarios
├── test/            # Test-specific scenarios
└── curated/         # Validated research scenarios
```

## Documentation

**Full templates**: `docs/structures/`
- `minimal_working_example.yaml` - Simplest valid scenario
- `comprehensive_scenario_template.yaml` - All parameters documented

**Parameter reference**: `docs/structures/parameter_quick_reference.md`

