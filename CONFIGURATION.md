# VMT Configuration Guide

## Centralized Parameters

The VMT simulation uses centralized default parameters defined in `scenarios/schema.py` (`ScenarioParams` class). Scenario YAML files inherit these defaults and only need to specify parameters that differ from the defaults.

### Default Parameters

```python
# From scenarios/schema.py:
class ScenarioParams:
    spread: float = 0.0                    # Bid-ask spread (0.0 = true reservation prices)
    vision_radius: int = 5                 # Manhattan distance for perception
    interaction_radius: int = 1            # Manhattan distance for trading
    move_budget_per_tick: int = 1          # Maximum Manhattan distance per tick
    ΔA_max: int = 5                        # Maximum trade size per transaction
    forage_rate: int = 1                   # Resource harvest rate per tick
    epsilon: float = 1e-12                 # Zero-safe epsilon for calculations
    beta: float = 0.95                     # Exploration parameter for foraging
    resource_growth_rate: int = 0          # Resource regeneration rate (0 = disabled)
    resource_max_amount: int = 5           # Maximum resource amount per cell
    resource_regen_cooldown: int = 5       # Ticks to wait after depletion before regen
```

## Important: Spread Parameter

**The `spread` parameter defaults to `0.0`** (zero spread), which means agents reveal their true reservation prices. This is the recommended default because:

1. **Zero-inventory compatibility:** Non-zero spreads can prevent trades when agents have complementary inventories but produce quotes that don't overlap enough
2. **Economic clarity:** Zero spread makes the surplus calculations directly reflect true gains from trade
3. **Diagnostic simplicity:** Easier to understand why trades succeed or fail

### When to Override Spread

Only explicitly set `spread` in your scenario YAML if you need to test:
- Strategic behavior with hidden preferences
- Bid-ask spread dynamics
- Realistic market friction

Example of overriding spread:
```yaml
params:
  spread: 0.05  # 5% bid-ask spread
  # Other params inherit defaults
```

### When NOT to Override Spread

For most simulation scenarios, **omit the `spread` parameter** to use the centralized default of `0.0`:

```yaml
params:
  # spread defaults to 0.0 from schema.py
  vision_radius: 3
  interaction_radius: 1
  # Only specify params that differ from defaults
```

## Parameter Guidelines

### Vision Radius
- Determines which agents and resources an agent can perceive
- Should be ≥ interaction_radius for agents to see potential trade partners

### Interaction Radius
- Manhattan distance within which agents can trade
- Typically 1 (adjacent or co-located)
- Set to 0 to require exact co-location

### ΔA_max
- Limits trade size per transaction
- Prevents extreme wealth transfers in single trades
- Agents can make multiple sequential trades to reach equilibrium

### Epsilon
- Small value used in zero-safe MRS calculations
- Default `1e-12` works for most CES utility functions
- Increase if encountering numerical instability

### Beta
- Controls forage target selection bias toward higher-value resources
- Higher beta (→1) = more exploitation, lower beta (→0) = more exploration
- Default `0.95` balances exploration and exploitation

### Resource Regeneration

**resource_growth_rate** (default: 0)
- Units that regenerate per tick after cooldown period
- `0` = No regeneration (finite resources, backward compatible)
- `1` = Slow regeneration (strategic resource management)
- `2+` = Fast regeneration (sustainable foraging)

**resource_max_amount** (default: 5)
- Maximum resource units per cell
- Caps regeneration to prevent unbounded growth
- Should be ≥ initial resource amount for natural behavior

**resource_regen_cooldown** (default: 5)
- Ticks a depleted cell must wait before regeneration begins
- Only applies to cells that were fully harvested to 0
- Creates strategic timing element (when to return to harvested areas)

**Regeneration Behavior:**
1. Cell starts with resources (e.g., amount=3)
2. Agent harvests: 3 → 2 → 1 → 0
3. When amount hits 0, `depleted_at_tick` is recorded
4. Cell waits for cooldown period (default 5 ticks)
5. After cooldown, regeneration starts at `resource_growth_rate`
6. Continues growing until `resource_max_amount` reached
7. Can be harvested again, repeating the cycle

## Scenario File Best Practices

1. **Use defaults when possible** - Only override parameters that need to differ
2. **Document overrides** - Add comments explaining why a parameter differs from default
3. **Keep spread at 0.0** - Unless specifically testing spread dynamics
4. **Bootstrap inventories** - Ensure agents start with non-zero amounts of both goods when using CES utility

Example minimal scenario:
```yaml
schema_version: 1
name: my_scenario
N: 10
agents: 5
initial_inventories:
  A: [10, 10, 10, 10, 10]
  B: [10, 10, 10, 10, 10]
utilities:
  mix:
  - {type: ces, weight: 1.0, params: {rho: -0.5, wA: 1.0, wB: 1.0}}
params:
  # All params use centralized defaults from schema.py
  vision_radius: 3  # Only override what's needed
resource_seed:
  density: 0.05
  amount: 1
```

## Modifying Centralized Defaults

To change the global default for any parameter:

1. Edit `scenarios/schema.py`, class `ScenarioParams`
2. Update this documentation
3. Run all tests to verify nothing breaks: `pytest tests/`
4. Update all scenario files that explicitly set the old default (remove those lines)

## See Also

- `scenarios/schema.py` - Parameter definitions and validation
- `scenarios/loader.py` - Scenario loading logic
- `DIAGNOSTIC_REPORT.md` - Trade failure analysis with spread=0 recommendation

