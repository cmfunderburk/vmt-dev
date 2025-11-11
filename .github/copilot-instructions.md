# VMT Copilot Instructions

## Project Overview

VMT (Visualizing Microeconomic Theory) is a spatial agent-based simulation platform studying microeconomic exchange mechanisms. It's designed around three complementary tracks:
- **Agent-Based**: Emergent market phenomena from bilateral trading in spatial environments
- **Game Theory**: Strategic interactions with Edgeworth Box visualizations and bargaining solutions
- **Neoclassical**: Equilibrium benchmarks using traditional solution methods

The core principle: Markets are institutional constructions, not natural phenomena. Outcomes depend critically on search protocols, matching mechanisms, bargaining procedures, and spatial constraints.

## Architecture Essentials

### The 7-Phase Tick Cycle (Deterministic Order)

Every simulation tick executes phases in this strict order (see `src/vmt_engine/simulation.py:step()`):

1. **Perception** → 2. **Decision** (Search + Matching) → 3. **Movement** → 4. **Trade** → 5. **Forage** → 6. **Resource Regeneration** → 7. **Housekeeping**

This ordering is fundamental to reproducibility. Do not reorder.

### Protocol System Architecture (Post-Nov 2025 Refactor)

**Three decoupled protocol categories** each with distinct responsibilities:

- **SearchProtocol** (`src/vmt_engine/agent_based/search/base.py`): Select targets using `WorldView` (agent's local perspective). Returns `SetTarget` effects.
- **MatchingProtocol** (`src/vmt_engine/game_theory/matching/base.py`): Form trading pairs using `ProtocolContext` (global perspective). Returns `Pair`/`Unpair` effects.
- **BargainingProtocol** (`src/vmt_engine/game_theory/bargaining/base.py`): Negotiate trade terms between paired agents. Returns `Trade`/`Unpair` effects.

**Key principle**: Protocols are immutable read-only algorithms that return declarative `Effect` lists. The simulation core validates and applies effects. No params hacks—protocols receive full agent state directly via `agents: tuple[Agent, Agent]` in bargaining or `context.agents[id]` in matching.

### Core Data Structures

**Agents** (`src/vmt_engine/core/agent.py`):
- Economic: `id`, `pos`, `inventory` (Inventory(A, B)), `utility` (Utility function instance)
- Perception: `vision_radius`, `quotes` (dict of barter exchange rates)
- Movement: `target_pos`, `target_agent_id`, `move_budget_per_tick`
- Trade state: `paired_with_id` (persistent across ticks until unpaired)
- Forage state: `is_foraging_committed`, `forage_target_pos`

**Utility Functions** (`src/vmt_engine/econ/utility.py`):
- Five implementations: CES, Linear, Quadratic, Stone-Geary, Translog
- Interface: `u(A, B)` → float (canonical utility calculation)
- Marginal utilities: `mu_A(A, B)`, `mu_B(A, B)` → float
- All inputs accept `Decimal` precision quantities; calculations use `float` internally
- Zero-inventory guard: Adds tiny epsilon only for MRS ratio calculation, never for core utility

**Effect System** (`src/vmt_engine/protocols/base.py`):
- Effects are immutable dataclasses: `SetTarget`, `Pair`, `Unpair`, `Move`, `Trade`, `ClaimResource`
- All effects include `protocol_name: str` and `tick: int` for logging
- Trade effects include full specification: `dA`, `dB` (Decimal), `price` (float), `metadata` dict
- Core validates then applies effects in deterministic sorted order

### Context Objects

- **WorldView**: Immutable snapshot of one agent's perspective (own state, visible neighbors). Used by search/bargaining protocols.
- **ProtocolContext**: Immutable snapshot of global state. Includes `agents: dict[int, Agent]` for omniscient matching logic and `all_agent_views` for public information.

## Critical Patterns

### Determinism Requirements

**Absolute rules** (violations cause non-reproducibility):
- Use `sim.rng` (numpy Generator), never Python's `random` module
- All agent loops sorted by `agent.id`; all pair loops sorted by `(min_id, max_id)`
- Fixed-precision arithmetic: `Decimal` for quantities (4 decimal places via `QUANTITY_DECIMAL_PLACES`)
- Database storage: Convert Decimal ↔ integer minor units via `to_storage_int()` / `from_storage_int()`
- Deterministic tie-breaking: Movement prefers x before y; negative direction on ties

**Every new test must verify determinism**: same scenario + seed = identical telemetry logs. See `test_simulation_init.py` for examples.

### Trade Logic: Compensating Block Algorithm

The foundational VMT trade discovery mechanism (only fully implemented protocol):

1. Check if pair is within `interaction_radius`
2. For each direction (i sells A, j sells A):
   - Probe multiple prices within `[ask_seller, bid_buyer]` range
   - For each price, scan discrete quantities: ΔA = 1, 2, 3, ..., seller_inventory
   - Calculate ΔB = quantize_quantity(Decimal(price) × Decimal(ΔA))
   - Accept **first feasible trade** where both ΔU > ε (strict improvement)
3. Return immediately on first found (not optimal search)

This is the **first-acceptable-trade principle**, not surplus maximization.

### Protocol Registration & YAML Integration

All protocols auto-register via `@register_protocol` decorator (see `src/vmt_engine/protocols/registry.py`):

```python
@register_protocol(
    category="bargaining",
    name="compensating_block",
    version="2025.11.02",
    description="First-feasible trade via discrete quantity search",
    properties=["deterministic", "complete"],
    references=["VMT foundational algorithm"]
)
class CompensatingBlockBargaining(BargainingProtocol):
    def negotiate(self, pair, agents, world):
        # ... implementation ...
```

Protocol names are immediately available in YAML scenario files and CLI overrides. Registry validates name/category consistency.

### Pairing Persistence

Trade pairing persists across ticks until:
- Trade fails (no feasible trade found)
- Mode changes (simulation transitions between trade/forage modes)

Once paired, agents:
- Move toward partner (skip other opportunities)
- Attempt trades each tick (may execute multiple trades over several ticks)
- Ignore all other trading/foraging until unpaired

This demonstrates economic commitment cost and iterative bilateral exchange.

### Resource Claiming System

Prevents clustering: when agent claims a forage target, other agents see it as unavailable until:
- Agent reaches the resource (`agent.pos == claimed_pos`)
- Agent changes target (`agent.target_pos != claimed_pos`)

Controlled by `ScenarioParams`:
- `enable_resource_claiming` (default: True)
- `enforce_single_harvester` (default: True) — only lowest-ID agent per cell harvests per tick

## Development Workflow

### Running Simulations

**GUI** (recommended for exploration):
```bash
python launcher.py
```

**Command-line**:
```bash
python main.py scenarios/demos/minimal_2agent.yaml
```

**View telemetry**:
```bash
python view_logs.py
```
Opens interactive viewer of `logs/telemetry.db` (SQLite database with tick-by-tick state).

### Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_simulation_init.py -v

# Determinism test template
def test_my_feature_determinism():
    scenario = load_scenario("scenarios/test/my_scenario.yaml")
    sim1 = Simulation(scenario, seed=42)
    sim2 = Simulation(scenario, seed=42)
    sim1.run(100)
    sim2.run(100)
    assert get_telemetry_log(sim1) == get_telemetry_log(sim2)
```

### Scenario Configuration

Scenarios are YAML files (see `docs/structures/comprehensive_scenario_template.yaml`):

```yaml
grid_size: 20
num_agents: 10
max_ticks: 1000

# Protocols (auto-discovered via registry)
search_protocol: "distance_discounted"
matching_protocol: "greedy_surplus"
bargaining_protocol: "compensating_block"

# Utilities (heterogeneous agents supported)
utilities:
  mix:
    - type: "ces"
      params: {alpha_A: 0.5, alpha_B: 0.5, rho: 0.5}
      weight: 0.7
    - type: "linear"
      params: {vA: 1, vB: 2}
      weight: 0.3

agents:
  - utility_function: "ces"  # or index into mix
    initial_A: 10
    initial_B: 15
```

## Key File Reference

| Purpose | File |
|---------|------|
| Simulation main loop, 7-phase orchestration | `src/vmt_engine/simulation.py` |
| All Effect types | `src/vmt_engine/protocols/base.py` |
| Search protocol interface & defaults | `src/vmt_engine/agent_based/search/base.py` |
| Matching protocol interface & defaults | `src/vmt_engine/game_theory/matching/base.py` |
| Bargaining protocol interface & `compensating_block` | `src/vmt_engine/game_theory/bargaining/` |
| Utility functions (all 5 types) | `src/vmt_engine/econ/utility.py` |
| Protocol registry & auto-discovery | `src/vmt_engine/protocols/registry.py` |
| Type system (Decimal config, Inventory, Quote) | `src/vmt_engine/core/` |
| Telemetry database schema & logging | `src/telemetry/database.py` |
| YAML scenario loading & validation | `src/scenarios/loader.py` |

## Common Extension Points

**Adding a new bargaining protocol**:
1. Create class in `src/vmt_engine/game_theory/bargaining/your_protocol.py`
2. Inherit from `BargainingProtocol`, implement `negotiate(pair, agents, world) → list[Effect]`
3. Use `@register_protocol` decorator (copies from `compensating_block.py` template)
4. Add determinism test in `tests/`
5. Reference in YAML scenarios by name

**Adding a new utility function**:
1. Implement in `src/vmt_engine/econ/utility.py` (inherit from `Utility` ABC)
2. Implement: `u(A, B)`, `mu_A(A, B)`, `mu_B(A, B)` (all return float)
3. Handle zero-inventory edge cases (add epsilon only for MRS ratio)
4. Add test case in `tests/test_utility_*.py`
5. Register name in `create_utility()` factory function

**Adding a new protocol category** (rare): Add new ABC interface in respective module (`agent_based/`, `game_theory/`), register category in `ProtocolRegistry`, add telemetry schema in `protocols/telemetry_schema.py`.

## Known Architectural Decisions

1. **Barter-only economy**: All trades are A↔B direct exchanges. Money system reserved for future work.
2. **Heuristic vs. full evaluation**: Matching phase uses lightweight quote-based heuristics (`TradePotentialEvaluator`); bargaining uses full utility calculations.
3. **First-acceptable vs. optimal**: Compensating block returns first feasible trade, not highest-surplus. This enables pedagogical exploration of mechanism design.
4. **Immutable protocols**: Protocols are pure functions that read agent state but cannot mutate. Core applies effects only.
5. **Pessimistic claims**: Resource claims are cleared at tick start, forcing agents to re-evaluate every tick. This prevents stale claims.

## Typical Agent Error: Avoiding Non-Determinism

**Bad**: `import random; random.choice(agent_list)`
**Good**: `self.rng.choice(agent_list)` (where self is Simulation or protocol context with rng)

**Bad**: Iterating unordered dict: `for agent_id in agents_dict: ...`
**Good**: `for agent_id in sorted(agents_dict.keys()): ...`

**Bad**: Using float for quantities: `quantity = price * amount`
**Good**: `quantity = quantize_quantity(Decimal(price) * Decimal(amount))`

