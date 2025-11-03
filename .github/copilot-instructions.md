# VMT (Visualizing Microeconomic Theory) - AI Agent Guide

## Project Overview

VMT is a spatial agent-based simulation platform for studying microeconomic exchange mechanisms. Agents with heterogeneous preferences forage for resources and trade through configurable institutional rules (protocols for search, matching, and bargaining). The platform demonstrates how different market institutions produce different outcomes—prices and markets are emergent phenomena, not assumptions.

**Core Philosophy**: Markets don't "just happen"—they require explicit institutional mechanisms. VMT makes these mechanisms swappable and comparable.

## Architecture: The Big Picture

### Protocol-Driven Design

The entire simulation is built around **swappable protocols** that define institutional rules:

- **Search Protocols** (`src/vmt_engine/agent_based/search/`): How agents find trading partners (e.g., `myopic`, `random_walk`, `legacy`)
- **Matching Protocols** (`src/vmt_engine/game_theory/matching/`): How pairs form (e.g., `greedy`, `random`, `legacy`)
- **Bargaining Protocols** (`src/vmt_engine/game_theory/bargaining/`): How prices are negotiated (e.g., `split_difference`, `take_it_or_leave_it`, `legacy`)

**Why domain-organized**: Search is agent-based behavior; matching and bargaining are game-theoretic mechanisms. This organization reflects the conceptual distinction.

### Effect-Based Execution

Protocols return **declarative Effects** (not mutating state directly):
```python
# Protocols produce effects
effects = [
    Pair(agent_i=1, agent_j=2),
    Trade(agent_i=1, agent_j=2, delta_A=5, delta_B=3),
    Move(agent_id=1, new_pos=(10, 15))
]
# Effects are applied by systems to maintain determinism
```

This separation ensures determinism and enables protocol testing without full simulation context.

### The 7-Phase Tick Cycle

**CRITICAL**: Every tick executes exactly 7 phases in this order:

1. **Perception**: Build immutable WorldView snapshots for each agent
2. **Decision**: Three-pass pairing algorithm + target selection
3. **Movement**: Manhattan movement toward targets with deterministic tie-breaking
4. **Trade**: Paired agents within interaction radius attempt trades
5. **Foraging**: Unpaired agents harvest resources
6. **Regeneration**: Resources respawn with cooldowns
7. **Housekeeping**: Quote refresh, pairing integrity checks, telemetry logging

**Why this matters**: Code must never violate phase ordering. Agents use frozen snapshots during decision-making to prevent race conditions.

## Critical Development Patterns

### Integer Math and Rounding

All goods, positions, and inventories are **integers**. Prices are floats, but trade quantities must be integers.

**Critical rounding rule**: Use **round-half-up** for price-to-quantity conversion:
```python
delta_B = int(np.floor(price * delta_A + 0.5))  # Round-half-up
```

Why: Ensures consistency in compensating block search across different price paths.

### The Three-Pass Pairing Algorithm

Agent pairing uses a sophisticated three-pass system (implemented in `src/vmt_engine/systems/decision.py`):

1. **Pass 1**: Each agent ranks visible neighbors by **distance-discounted surplus** = `surplus × β^distance`
2. **Pass 2**: Mutual consent pairing (both agents rank each other as top choice)
3. **Pass 3**: Greedy surplus matching for unpaired agents

**Why this matters**: Once paired, agents maintain **exclusive commitment** across ticks—they ignore other opportunities until trade fails or mode changes. This is not greedy reselection each tick.

**Telemetry captures**: Preference lists (top 3 by default), pairing/unpairing events, and commitment state.

### WorldView Pattern

Protocols receive **immutable snapshots** via `WorldView` objects—never direct access to simulation state:

```python
@dataclass
class WorldView:
    tick: int
    agents: dict[int, AgentView]  # Read-only agent data
    resources: dict[Position, ResourceView]
    spatial_index: SpatialIndex
    # No methods that mutate state
```

**Why**: Prevents protocols from creating side effects, ensures determinism, enables protocol unit testing.

## Developer Workflows

### Environment Setup

**ALWAYS activate the virtual environment before any Python command**:
```bash
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

**Dependencies**: pygame, numpy, pyyaml, pytest, PyQt6 (see `requirements.txt`)

### Running Simulations

```bash
# GUI launcher (recommended for exploration)
python launcher.py

# CLI with visualization
python main.py scenarios/demos/minimal_2agent.yaml 42

# Headless (programmatic)
python scripts/run_headless.py
```

### Testing

```bash
# Full suite (316+ tests)
pytest

# Specific test file
pytest tests/test_barter_integration.py

# Specific test function
pytest tests/test_protocol_registry.py::test_protocol_registration

# Verbose with output
pytest -v -s
```

**Test organization**: Tests are named `test_<feature>.py`. Helper fixtures in `tests/helpers/`.

**Testing patterns**:
- Integration tests: Load YAML scenario, run simulation, check trade counts and final inventories
- Unit tests: Directly test protocol logic with mock WorldView objects

### Telemetry and Debugging

Simulations log comprehensive telemetry to `./logs/telemetry.db` (SQLite):

**Key tables**:
- `simulation_runs`: Run metadata and configuration
- `agent_snapshots`: Per-tick agent state (position, inventory, utility, quotes)
- `trades`: Successful trades with quantities and surplus decomposition
- `pairings`: Pairing/unpairing events with reason codes
- `preferences`: Agent preference rankings (top 3 by default)
- `decisions`: Decision outcomes with pairing status
- `tick_states`: Per-tick mode and regime state

**Viewing logs**:
```bash
python view_logs.py  # PyQt6 GUI for exploring telemetry
```

**Programmatic access**:
```python
import sqlite3
conn = sqlite3.connect('./logs/telemetry.db')
cursor = conn.execute("SELECT * FROM trades WHERE run_id = ? ORDER BY tick", (run_id,))
```

## Scenario Configuration

Scenarios are defined in YAML files in `scenarios/` directory:

**Key structure**:
```yaml
grid_size: 32
num_agents: 10
max_ticks: 100

# Protocol selection (institutional rules)
search_protocol: "myopic"              # or "random_walk", "legacy"
matching_protocol: "greedy_surplus"     # or "random", "legacy"
bargaining_protocol: "split_difference" # or "take_it_or_leave_it", "legacy"

# Agent configuration
initial_inventories:
  A: {uniform_int: [5, 15]}
  B: {uniform_int: [5, 15]}

utilities:
  mix:
    - type: ces
      weight: 0.7
      params: {rho: -0.5, wA: 1.0, wB: 1.0}
    - type: linear
      weight: 0.3
      params: {vA: 1.0, vB: 1.5}

params:
  spread: 0.0                  # Bid-ask spread (0 = true reservation prices)
  trade_cooldown_ticks: 5      # Cooldown after failed trade
  beta: 0.95                   # Time discount factor
  # ... see docs/structures/ for complete reference
```

**Templates**: `docs/structures/minimal_working_example.yaml` and `comprehensive_scenario_template.yaml`

## Code Organization Quick Reference

```
src/vmt_engine/
├── core/                    # Primitives: Agent, Grid, State, Position
├── econ/                    # Utility functions (CES, Linear, Quadratic, Translog, Stone-Geary)
├── protocols/               # Protocol system infrastructure
│   ├── base.py             # Effect types, ProtocolBase
│   ├── context.py          # WorldView, ProtocolContext
│   └── registry.py         # Protocol registration and lookup
├── agent_based/search/      # Search protocols (target selection)
├── game_theory/
│   ├── matching/           # Matching protocols (pairing)
│   └── bargaining/         # Bargaining protocols (price negotiation)
├── systems/                # Phase implementations (perception, decision, movement, etc.)
└── simulation.py           # Main simulation orchestration

src/scenarios/
├── schema.py               # YAML schema validation
└── loader.py               # Scenario loading logic

src/telemetry/
├── database.py             # SQLite schema
├── db_loggers.py           # Logging manager
└── config.py               # Logging configuration

scenarios/
├── demos/                  # Example scenarios
├── baseline/               # Benchmark scenarios
└── test/                   # Test scenarios

tests/                      # 316+ tests covering all systems
scripts/                    # Analysis tools (analyze_baseline.py, etc.)
docs/                       # Documentation
└── planning_thinking_etc/BIGGEST_PICTURE/opus_plan/  # Updated planning docs
```

## Common Tasks

### Adding a New Protocol

1. Create protocol file in appropriate domain directory:
   - Search → `src/vmt_engine/agent_based/search/my_search.py`
   - Matching → `src/vmt_engine/game_theory/matching/my_matching.py`
   - Bargaining → `src/vmt_engine/game_theory/bargaining/my_bargaining.py`

2. Inherit from base class and use `@register_protocol` decorator:
```python
from vmt_engine.protocols import ProtocolBase, register_protocol, Effect

@register_protocol("my_search", "search")
class MySearchProtocol(ProtocolBase):
    def execute(self, context: ProtocolContext) -> list[Effect]:
        # Return effects, don't mutate state
        return [SetTarget(agent_id=context.agent_id, target_pos=(x, y))]
```

3. Add import to module's `__init__.py` to trigger registration
4. Write tests in `tests/test_my_search.py`
5. Add protocol to scenario YAML: `search_protocol: "my_search"`

### Reading Code: Start Here

1. **Understand the tick cycle**: `src/vmt_engine/README.md` (definitive reference)
2. **See protocols in action**: `src/vmt_engine/agent_based/search/myopic.py` (well-documented example)
3. **Understand effects**: `src/vmt_engine/protocols/base.py` (effect types)
4. **Study decision-making**: `src/vmt_engine/systems/decision.py` (three-pass algorithm)
5. **Examine trade logic**: `src/vmt_engine/systems/matching.py` (compensating block search)

### Debugging Common Issues

**Simulation not deterministic**:
- Check agent iteration order (must be sorted by ID)
- Verify no global random state usage
- Confirm quotes aren't being refreshed mid-tick

**Trades not executing**:
- Check agents are within `interaction_radius`
- Verify agents are paired (check `agent.paired_with_id`)
- Confirm no active trade cooldowns (check `agent.trade_cooldowns`)
- Examine quote overlaps (bid must exceed ask)

**Protocol not being used**:
- Verify protocol is imported in module's `__init__.py` to trigger `@register_protocol`
- Check protocol name in YAML matches registered name
- Run `list_all_protocols()` to confirm registration

## Project-Specific Conventions

### Pure Barter Economy

VMT currently only supports **A↔B direct barter**. No money, no centralized markets (yet—these are planned for Stage 3).

**Implications**:
- All trades are bilateral agent-to-agent exchanges
- Trade matching logic is in `src/vmt_engine/systems/matching.py:find_best_trade()`
- Quote keys: `"ask_A_in_B"`, `"bid_A_in_B"`, `"p_min_A_in_B"`, etc.

### Resource Claiming System

Enabled by default to reduce clustering:
- Agents "claim" forage targets during Decision phase
- Other agents see claimed resources as unavailable
- Claims expire when agent reaches resource or changes target
- Only first agent (by ID) harvests per tick if `enforce_single_harvester=True`

**Why**: Without claiming, agents cluster inefficiently on high-value resources.

### Quote Stability Within Tick

Agent quotes are **frozen during the tick** and only refreshed in Housekeeping phase:
- Agents see consistent neighbor quotes during decision-making
- Quote updates happen only when `agent.inventory_changed=True` flag is set
- This prevents mid-tick inconsistencies

### Commitment Model

Paired agents maintain **exclusive commitment** until unpaired:
- Paired agents ignore forage opportunities
- Paired agents don't re-evaluate partner selection
- Successful trades maintain pairing (agents attempt another trade next tick)
- Failed trades unpair and set mutual cooldown

**Why**: Demonstrates opportunity cost of commitment and iterative bilateral exchange.

## Important Documentation

- **Type specifications**: `docs/4_typing_overview.md`
- **Technical manual**: `docs/2_technical_manual.md` (OUTDATED warning—check opus_plan docs)
- **Updated planning**: `docs/planning_thinking_etc/BIGGEST_PICTURE/opus_plan/`
- **Scenario templates**: `docs/structures/`

## Planning Context

Current development follows staged roadmap in `docs/planning_thinking_etc/BIGGEST_PICTURE/opus_plan/`:
- **Stage 0** (Complete): Protocol architecture restructure
- **Stage 1-2** (In Progress): Behavioral baseline analysis and protocol comparison infrastructure
- **Stage 3** (Planned): Centralized market mechanisms (Walrasian auctioneer, double auctions)

**Key principle**: Don't implement complex features until explicitly told to start—focus on planning, design clarity, and understanding current behavior first.

