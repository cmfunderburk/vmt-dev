# VMT Codebase AI Agent Instructions

## Core Architecture

VMT is an agent-based economic simulation platform with a **7-phase deterministic tick cycle**:
1. **Perception** - Agents observe local environment within `vision_radius`
2. **Decision** - Protocol-driven target selection (search) and pairing (matching)
3. **Movement** - Agents move toward targets with `move_budget_per_tick`
4. **Trade** - Paired agents negotiate via bargaining protocols
5. **Forage** - Unpaired agents harvest resources
6. **Resource Regeneration** - Harvested resources regenerate
7. **Housekeeping** - Quote refresh, pairing checks, telemetry logging

## Critical Conventions

### Determinism is Sacred
- **ALWAYS** test with determinism checks: run simulation twice with same seed, assert identical outcomes
- See `tests/test_simulation_init.py` for pattern - use `tests.helpers.assertions.assert_deterministic()`
- All RNG must use `sim.rng` (seeded numpy Generator), never `random` module

### Decimal Goods Representation
- Goods use `Decimal` type with 4 decimal places precision (not floats!)
- Always use `decimal_from_numeric()` for conversion, `quantize_quantity()` for rounding
- Storage in DB uses integers: multiply by 10^4 via `to_storage_int()`
```python
from vmt_engine.core.decimal_config import decimal_from_numeric, quantize_quantity
inventory.A = decimal_from_numeric(10)  # Decimal('10.0000')
```

### Protocol System (Effect-based)
Protocols return declarative **Effects** that the system applies:
```python
# Protocols don't modify state directly!
effects = [
    SetTarget(agent_id=1, target=(5, 5)),
    Pair(agent_a=1, agent_b=2, reason="high_surplus")
]
```

### Agent Coordination
- **Resource claiming** prevents multiple agents targeting same resource (`sim.resource_claims`)
- **Trade pairing** creates exclusive bilateral commitments that persist across ticks
- **Trade cooldowns** prevent immediate re-pairing after failed trades (`agent.trade_cooldowns`)

## Development Workflow

### Environment Setup (MANDATORY)
```bash
# ALWAYS activate venv before ANY Python command
source venv/bin/activate  # Linux/macOS
bash -c "source venv/bin/activate && python ..."  # If issues

# Run tests with determinism checks
pytest tests/test_barter_integration.py

# Launch GUI for interactive testing
python launcher.py

# Debug via telemetry database
python view_logs.py  # Interactive SQL viewer at logs/telemetry.db
```

### Testing Patterns
```python
# Use scenario builders for tests
from tests.helpers import builders
scenario = builders.build_scenario(N=20, agents=10)
sim = builders.make_sim(scenario, seed=42, matching="greedy_surplus")

# ALWAYS test determinism for new features
def test_my_feature_determinism():
    # Run twice with same seed
    for _ in range(2):
        sim = make_sim(scenario, seed=42)
        sim.run(10)
    # Assert identical states
```

## Key Integration Points

### Protocol Configuration
Protocols are configured in YAML or overridden via CLI:
```yaml
# In scenario YAML
search_protocol: "myopic"  # or {"name": "myopic", "params": {...}}
matching_protocol: "greedy_surplus"
bargaining_protocol: "compensating_block"
```

### Protocol Registry Pattern
New protocols auto-register via decorator:
```python
from vmt_engine.protocols.registry import register_protocol

@register_protocol("my_search", "search")
class MySearchProtocol(SearchProtocol):
    def select_targets(self, view: WorldView) -> list[Effect]:
        # Return SetTarget effects
```

### Scenario Schema
Scenarios follow strict schema (`src/scenarios/schema.py`):
- `initial_inventories`: Dict or list format for agent endowments
- `utilities`: Support for CES, Linear, Quadratic, Stone-Geary, Translog
- `params`: Spatial, trading, foraging, economic parameters
- `resource_seed`: Resource distribution configuration

### Telemetry System
All events logged to SQLite (`logs/telemetry.db`):
```python
# In protocols/systems
sim.telemetry.log_trade(tick, x, y, buyer_id, seller_id, dA, dB, price, direction)
sim.telemetry.log_decision(tick, agent_id, target_type, target_pos)
```

## File Organization

- `src/vmt_engine/` - Core simulation engine
  - `agent_based/` - Search protocols (agent perspective)
  - `game_theory/` - Matching & bargaining protocols (global perspective)
  - `systems/` - Phase execution logic
  - `core/` - Agent, Grid, Inventory data structures
- `scenarios/` - YAML simulation configurations
- `tests/` - Pytest suite with determinism focus
- `src/telemetry/` - Database logging infrastructure

## Common Pitfalls to Avoid

1. **Never use float for goods** - Always Decimal with proper quantization
2. **Never use random module** - Always sim.rng for determinism
3. **Never modify agent state in protocols** - Return Effects only
4. **Always test determinism** - Non-deterministic code breaks research validity
5. **Always activate venv** - Python commands fail without environment
