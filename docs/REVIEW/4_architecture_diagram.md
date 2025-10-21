# VMT Architecture: Visual Maps & Module Structure

**Date**: 2025-10-21  
**Purpose**: High-level architectural overview with visual diagrams  
**Audience**: Project lead, future contributors, architectural review

---

## Executive Summary

VMT's architecture has evolved from a simple barter simulation into a sophisticated multi-layered system. This document provides visual representations of:

1. **Module Structure** - How code is organized
2. **7-Phase Tick Cycle** - Core simulation loop
3. **Data Flow** - How information moves through the system
4. **System Interactions** - How subsystems communicate
5. **Money System Integration** - How money was layered on top

---

## Part 1: High-Level Module Structure

### Directory Organization

```
vmt-dev/
│
├── src/                           # All source code
│   ├── vmt_engine/                # Core simulation (THE HEART)
│   ├── vmt_launcher/              # GUI for launching sims
│   ├── vmt_log_viewer/            # GUI for analyzing results
│   ├── vmt_pygame/                # Real-time visualization
│   ├── vmt_tools/                 # CLI scenario generator
│   ├── scenarios/                 # Scenario loading/validation
│   └── telemetry/                 # SQLite logging
│
├── scenarios/                     # User-facing YAML files
│   ├── demos/                     # Pedagogical scenarios
│   └── test/                      # Integration test scenarios
│
├── tests/                         # 316+ test files
├── docs/                          # Comprehensive documentation
├── scripts/                       # Analysis & utility scripts
└── logs/                          # SQLite database (runtime)
```

### Architectural Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                     User-Facing Layer                           │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  GUI Launcher  │  │  Log Viewer    │  │  Scenario Files  │  │
│  │  (vmt_launcher)│  │  (log_viewer)  │  │  (YAML)          │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                      │                       │
         ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Interface Layer                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  Pygame        │  │  Telemetry     │  │  Scenario        │  │
│  │  Renderer      │  │  Manager       │  │  Loader          │  │
│  │  (vmt_pygame)  │  │  (telemetry)   │  │  (scenarios/)    │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                      │                       │
         └──────────────────────┼───────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Core Engine Layer                          │
│                     (vmt_engine/)                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              simulation.py (Orchestrator)                │  │
│  │  • 7-Phase Tick Cycle                                   │  │
│  │  • Mode Management (forage/trade/both)                  │  │
│  │  • System Execution Control                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                │                                │
│         ┌──────────────────────┼────────────────────┐          │
│         ▼                      ▼                    ▼          │
│  ┌────────────┐        ┌─────────────┐      ┌──────────────┐  │
│  │   core/    │        │   econ/     │      │   systems/   │  │
│  │            │        │             │      │              │  │
│  │ • Agent    │        │ • Utility   │      │ • Perception │  │
│  │ • Grid     │        │   (5 types) │      │ • Decision   │  │
│  │ • State    │        │ • Money API │      │ • Movement   │  │
│  │ • Inventory│        │             │      │ • Trading    │  │
│  │ • Spatial  │        └─────────────┘      │ • Foraging   │  │
│  │   Index    │                             │ • Regen      │  │
│  │            │                             │ • Housekeep  │  │
│  └────────────┘                             └──────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │                      │                       │
         ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  Grid State    │  │  Agent State   │  │  Telemetry DB    │  │
│  │  (memory)      │  │  (memory)      │  │  (SQLite)        │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Characteristics

| Layer | Responsibilities | Coupling |
|-------|-----------------|----------|
| **User-Facing** | UI, scenario files, result viewing | Loose (can swap GUIs) |
| **Interface** | Rendering, logging, config parsing | Medium (protocol-based) |
| **Core Engine** | Simulation logic, 7-phase cycle | Tight (orchestrated) |
| **Data** | State storage, persistence | Loose (clean interfaces) |

---

## Part 2: The 7-Phase Tick Cycle (Core Architecture)

### Conceptual Flow

```
TICK N START
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 1: PERCEPTION                                         │
│  ─────────────────────                                       │
│  Each agent observes environment (FROZEN SNAPSHOT):          │
│  • Nearby agents (within vision_radius)                      │
│  • Their broadcasted quotes                                  │
│  • Resource locations                                        │
│  • Current mode (forage/trade/both)                          │
│                                                              │
│  Output: perception_cache populated                          │
└──────────────────────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 2: DECISION                                           │
│  ────────────────────                                        │
│  Pass 1: Build Preference Lists                             │
│    • Compute surplus with each neighbor                      │
│    • Apply distance discounting (surplus × β^distance)       │
│    • Rank by discounted surplus                              │
│    • Skip partners in cooldown                               │
│                                                              │
│  Pass 2: Mutual Consent Pairing                             │
│    • Agents who list each other as #1 pair immediately       │
│    • Lower ID agent executes pairing (deterministic)         │
│    • Cooldowns cleared                                       │
│                                                              │
│  Pass 3: Greedy Fallback Pairing                            │
│    • Unpaired agents ranked by global surplus               │
│    • Assign pairs greedily (highest surplus first)          │
│    • Reciprocal commitment (both target each other)         │
│                                                              │
│  Resource Claiming:                                          │
│    • Agents selecting forage targets claim resources         │
│    • Stale claims cleared first                              │
│    • Deterministic priority (lowest ID)                      │
│                                                              │
│  Output: agent.paired_with_id, agent.target_pos set          │
└──────────────────────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 3: MOVEMENT                                           │
│  ────────────────────                                        │
│  Each agent moves towards target:                            │
│  • Up to move_budget_per_tick Manhattan distance             │
│  • Deterministic tie-breaking (x before y, negative first)   │
│  • Diagonal deadlock resolution (higher ID yields)           │
│  • Spatial index updated                                     │
│                                                              │
│  Output: agent.pos updated                                   │
└──────────────────────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 4: TRADE (conditional: mode = "trade" or "both")      │
│  ─────────────────────────────────────────────────────────   │
│  For each PAIRED agent pair within interaction_radius:       │
│    1. Enumerate allowed exchange pairs (regime-dependent)    │
│    2. Find compensating block for each pair (price search)   │
│    3. Rank candidates by total surplus (descending)          │
│    4. Apply money-first tie-breaking (if mixed regime)       │
│    5. Execute top-ranked trade                               │
│                                                              │
│  On success:                                                 │
│    • Update inventories (A, B, M)                            │
│    • Log trade to telemetry                                  │
│    • Maintain pairing (try again next tick)                  │
│                                                              │
│  On failure:                                                 │
│    • Unpair agents                                           │
│    • Set mutual cooldown (trade_cooldown_ticks)              │
│                                                              │
│  Output: inventories updated, trade telemetry logged         │
└──────────────────────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 5: FORAGING (conditional: mode = "forage" or "both")  │
│  ──────────────────────────────────────────────────────────  │
│  For each agent AT a resource cell:                          │
│    • Skip if paired (exclusive commitment to trading)        │
│    • Check if already harvested this tick (single-harvester) │
│    • Harvest up to forage_rate units                         │
│    • Deplete resource                                        │
│    • Update inventory                                        │
│                                                              │
│  Output: agent.inventory updated, grid resources depleted    │
└──────────────────────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 6: RESOURCE REGENERATION                              │
│  ────────────────────────────                                │
│  For each depleted resource cell:                            │
│    • Wait resource_regen_cooldown ticks                      │
│    • Then regenerate resource_growth_rate units per tick     │
│    • Cap at resource_max_amount                              │
│                                                              │
│  Output: grid resources regenerated                          │
└──────────────────────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 7: HOUSEKEEPING                                       │
│  ────────────────────────                                    │
│  Quote Refresh:                                              │
│    • If inventory_changed or lambda_changed:                 │
│      - Recompute reservation bounds                          │
│      - Apply spread                                          │
│      - Filter by exchange_regime                             │
│      - Store in agent.quotes dict                            │
│    • Reset flags                                             │
│                                                              │
│  Pairing Integrity:                                          │
│    • Detect asymmetric pairings (defensive check)            │
│    • Repair or log warning                                   │
│                                                              │
│  Lambda Updates (KKT mode, Phase 6+):                        │
│    • Aggregate neighbor prices                               │
│    • Estimate λ̂ from perceived prices                        │
│    • Smooth: λ_{t+1} = (1-α)λ_t + αλ̂                        │
│    • Clamp to bounds, set lambda_changed if significant      │
│                                                              │
│  Telemetry Logging:                                          │
│    • Agent snapshots (position, inventory, utility, quotes)  │
│    • Resource snapshots (grid state)                         │
│    • Tick state (mode, regime, active pairs)                 │
│    • Preference lists (top 3 by default)                     │
│    • Pairing events                                          │
│                                                              │
│  Output: system state consistent, telemetry complete         │
└──────────────────────────────────────────────────────────────┘
      │
      ▼
   TICK N+1 START
```

### Phase Order Rationale

| Phase | Why This Order? |
|-------|----------------|
| 1. Perception | Must observe BEFORE deciding (frozen snapshot prevents race conditions) |
| 2. Decision | Must decide targets BEFORE moving |
| 3. Movement | Must move BEFORE trading (need to be within interaction_radius) |
| 4. Trade | Must trade BEFORE foraging (paired agents skip foraging) |
| 5. Foraging | Must forage BEFORE regeneration (clear what was harvested this tick) |
| 6. Regeneration | Must regenerate BEFORE housekeeping (so quotes reflect new resource availability) |
| 7. Housekeeping | Must update quotes/state AFTER all actions complete |

**Critical:** This order is **NEVER changed**. It's the architectural invariant.

---

## Part 3: Data Flow Diagram

### Information Flow Through a Tick

```
┌─────────────┐
│  Scenario   │  (Initial conditions)
│    YAML     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Simulation.init()                        │
│  • Create Grid (NxN)                                        │
│  • Create Agents (heterogeneous utilities)                  │
│  • Initialize inventories (A, B, M)                         │
│  • Seed resources                                           │
│  • Initialize spatial index                                 │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Tick Loop (while running)                │
└─────────────────────────────────────────────────────────────┘
       │
       ├─────► Perception ─────► perception_cache
       │                             │
       │                             ▼
       ├─────► Decision ──────► target_pos, paired_with_id
       │                             │
       │                             ▼
       ├─────► Movement ──────► agent.pos (updated)
       │                             │
       │                             ▼
       ├─────► Trading ───────► inventories (A,B,M), trades table
       │                             │
       │                             ▼
       ├─────► Foraging ──────► inventories (+A/+B), grid resources (depleted)
       │                             │
       │                             ▼
       ├─────► Regeneration ──► grid resources (regenerated)
       │                             │
       │                             ▼
       └─────► Housekeeping ──► quotes (updated), telemetry (logged)
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  Telemetry DB   │
                            │  (SQLite)       │
                            │  • 8 tables     │
                            │  • Indexed      │
                            │  • Queryable    │
                            └─────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  Log Viewer     │
                            │  • Timeline     │
                            │  • Agent view   │
                            │  • Trade view   │
                            │  • CSV export   │
                            └─────────────────┘
```

### Data Structures (In-Memory)

```
Grid:
  • cells: dict[(x,y) → Cell]
  • Cell.resource: {type: Good, amount: int}
  • O(1) lookup by position

Agents: list[Agent] (sorted by ID)
  • Agent.id: int
  • Agent.pos: (x, y)
  • Agent.inventory: {A: int, B: int, M: int}
  • Agent.utility: Utility (polymorphic)
  • Agent.quotes: dict[str → float]
  • Agent.paired_with_id: int | None
  • Agent.target_pos: (x, y) | None

SpatialIndex:
  • buckets: dict[bucket_id → set[agent_id]]
  • Bucket size = max(vision_radius, interaction_radius)
  • O(k) query for agents_within_radius (k = local density)

Resource Claims:
  • dict[(x,y) → agent_id]
  • Cleared each tick, repopulated in Decision phase
```

---

## Part 4: System Interaction Map

### How Systems Communicate

```
PerceptionSystem
      │ reads
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Simulation State (shared)                                  │
│  • agents: list[Agent]                                      │
│  • grid: Grid                                               │
│  • spatial_index: SpatialIndex                              │
│  • resource_claims: dict                                    │
│  • params: dict (config)                                    │
│  • current_mode: str                                        │
└─────────────────────────────────────────────────────────────┘
      │ reads
      ▼
DecisionSystem
      │ writes: target_pos, paired_with_id, resource_claims
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent State (modified by systems)                          │
│  • perception_cache (Perception writes)                     │
│  • target_pos, paired_with_id (Decision writes)             │
│  • pos (Movement writes)                                    │
│  • inventory, trade_cooldowns (Trading writes)              │
│  • inventory (Foraging writes)                              │
│  • quotes (Housekeeping writes)                             │
└─────────────────────────────────────────────────────────────┘
      │ read/write
      ▼
MovementSystem
      │ writes: pos
      ▼
TradeSystem
      │ writes: inventory, trade_cooldowns, paired_with_id
      │ reads: paired_with_id, quotes
      ▼
ForageSystem
      │ writes: inventory
      │ reads: paired_with_id (to skip paired agents)
      ▼
ResourceRegenerationSystem
      │ writes: grid.cells[...].resource.amount
      ▼
HousekeepingSystem
      │ writes: quotes, inventory_changed, lambda_changed
      │ reads: inventory, lambda_money
      ▼
┌─────────────────────────────────────────────────────────────┐
│  TelemetryManager (observer)                                │
│  • log_agent_snapshot()                                     │
│  • log_trade()                                              │
│  • log_pairing_event()                                      │
│  • log_tick_state()                                         │
└─────────────────────────────────────────────────────────────┘
```

### Communication Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **Shared State** | Systems read/write common simulation state | All systems access `sim.agents` |
| **Sequential Pipeline** | Output of Phase N is input to Phase N+1 | Decision sets `target_pos`, Movement reads it |
| **Observer** | Systems emit events, telemetry observes | Trading logs to telemetry after execution |
| **Configuration** | Systems read global params | All systems check `sim.params['exchange_regime']` |

### Dependencies (Who depends on whom)

```
Simulation (orchestrator)
  ├──┬──── depends on all Systems (calls execute())
  │  └──── depends on TelemetryManager (logs state)
  │
Systems (7 phase systems)
  ├──┬──── depend on Simulation (read shared state)
  │  └──── depend on Agent/Grid/State (data structures)
  │
Agent/Grid/State (data)
  ├──── depend on Utility (economic logic)
  └──── depend on nothing else (pure data)

TelemetryManager
  ├──── depends on SQLite (database)
  └──── depends on nothing else (observer pattern)
```

**Key Design:** Data structures (Agent, Grid) have **no dependencies** on systems. Systems operate **on** data structures but don't own them. This enables clean testing and modularity.

---

## Part 5: Money System Integration Layer

### How Money Was Added (Phases 1-2)

```
┌─────────────────────────────────────────────────────────────┐
│  BEFORE MONEY (Pure Barter)                                 │
│                                                             │
│  Agent:                           Trade:                    │
│    inventory: {A, B}                match_pair(i, j)        │
│                                     find_compensating_block │
│  Utility:                            (A ↔ B only)          │
│    u(A, B) → float                                          │
│    mu_A(A, B), mu_B(A, B)                                   │
│                                                             │
│  Quotes:                                                    │
│    ask_A_in_B, bid_A_in_B                                   │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ ADD MONEY (Phases 1-2)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  AFTER MONEY (Monetary + Barter)                           │
│                                                             │
│  Agent:                           Trade:                    │
│    inventory: {A, B, M}             match_pair(i, j)        │
│    lambda_money: float              find_best_trade()       │
│                                       ├─ A ↔ B (barter)    │
│  Utility (money-aware):               ├─ A ↔ M (monetary)  │
│    u_goods(A, B) → float              └─ B ↔ M (monetary)  │
│    u_total = u_goods + λ·M                                  │
│    mu_A(A, B), mu_B(A, B)                                   │
│                                     rank_candidates()       │
│  Quotes (expanded):                   ├─ by surplus        │
│    Barter:                            ├─ money-first tie   │
│      ask_A_in_B, bid_A_in_B           └─ by agent ID      │
│    Money:                                                   │
│      ask_A_in_M, bid_A_in_M         find_compensating_block│
│      ask_B_in_M, bid_B_in_M           (generic: X ↔ Y)    │
│                                                             │
│  Config (new):                                              │
│    exchange_regime: "barter_only" | "money_only" | "mixed" │
│    money_mode: "quasilinear" | "kkt_lambda"                │
│    lambda_money: 1.0 (quasilinear)                          │
│                                                             │
│  Telemetry (extended):                                      │
│    trades.dM, trades.exchange_pair_type                     │
│    agent_snapshots.inventory_M, .lambda_money               │
│    tick_states.active_pairs                                 │
└─────────────────────────────────────────────────────────────┘
```

### Money Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Data Structures (Phase 1)                        │
│  ────────────────────────────────────────────────────────   │
│  Inventory: {A: int, B: int, M: int}                        │
│  Agent.lambda_money: float                                  │
│  Agent.lambda_changed: bool                                 │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Economic Logic (Phase 1-2)                       │
│  ────────────────────────────────────────────────────────   │
│  Utility API:                                               │
│    u_goods(A, B) → float  [canonical]                       │
│    mu_A(A, B) → float                                       │
│    mu_B(A, B) → float                                       │
│    u_total(inv, params) → u_goods(A,B) + λ·M                │
│                                                             │
│  Reservation Prices:                                        │
│    p*_A_in_B = MU_A / MU_B  (barter)                        │
│    p*_A_in_M = MU_A / λ     (money)                         │
│    p*_B_in_M = MU_B / λ     (money)                         │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Matching Logic (Phase 2)                         │
│  ────────────────────────────────────────────────────────   │
│  find_best_trade(agent_i, agent_j, exchange_regime):        │
│    if regime == "barter_only":                              │
│      try A ↔ B only                                         │
│    elif regime == "money_only":                             │
│      try A ↔ M, B ↔ M                                       │
│    elif regime == "mixed":                                  │
│      try all three, return highest surplus                  │
│                                                             │
│  find_compensating_block_generic(buyer, seller, X, Y):      │
│    [Generic price search for any X ↔ Y exchange]            │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Regime Control (Phase 3)                         │
│  ────────────────────────────────────────────────────────   │
│  Two-layer control:                                         │
│    1. Temporal: mode_schedule (WHEN trade/forage)           │
│    2. Type: exchange_regime (WHAT exchange pairs)           │
│                                                             │
│  If mode == "forage":                                       │
│    active_pairs = []  (no trading)                          │
│  Else if mode in ["trade", "both"]:                         │
│    if regime == "barter_only": ["A<->B"]                    │
│    if regime == "money_only": ["A<->M", "B<->M"]            │
│    if regime == "mixed": ["A<->M", "B<->M", "A<->B"]        │
│                                                             │
│  Money-first tie-breaking (Phase 3):                        │
│    Sort candidates by:                                      │
│      1. Total surplus (descending)                          │
│      2. Pair type priority: A↔M, B↔M, A↔B (money first)     │
│      3. Agent pair ID (deterministic)                       │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: Telemetry (Phase 1-3)                            │
│  ────────────────────────────────────────────────────────   │
│  Extended schema:                                           │
│    agent_snapshots.inventory_M                              │
│    agent_snapshots.lambda_money                             │
│    trades.dM, trades.exchange_pair_type                     │
│    tick_states.current_mode, .active_pairs                  │
│                                                             │
│  Log viewer additions:                                      │
│    Money tab (trade distribution by pair type)              │
│    Money labels overlay (M: 100)                            │
│    Lambda heatmap visualization                             │
└─────────────────────────────────────────────────────────────┘
```

### Backward Compatibility Strategy

**Key Decision:** All money features default to preserve legacy behavior.

```python
# schema.py defaults (Phase 1)
exchange_regime: Literal[...] = "barter_only"  # Legacy pure barter
money_mode: Literal[...] = "quasilinear"       # Simple fixed λ
lambda_money: float = 1.0                      # Standard MU of money
M: int = 0                                     # No money by default

# This means:
# - Old scenarios run UNCHANGED
# - No code needs M != 0 guards (M=0 is valid)
# - Barter-only regime skips monetary matching
```

---

## Part 6: Module Dependency Graph

### Import Structure

```
main.py, launcher.py
      │
      ├───► scenarios.loader
      │         └───► scenarios.schema
      │
      ├───► vmt_engine.simulation
      │         ├───► vmt_engine.core.*
      │         ├───► vmt_engine.econ.*
      │         ├───► vmt_engine.systems.*
      │         └───► telemetry.*
      │
      └───► vmt_pygame.renderer
                └───► vmt_engine.core.* (read-only)

vmt_log_viewer.*
      └───► telemetry.database (queries only)

vmt_tools.*
      └───► scenarios.schema (generates valid YAML)
```

### Circular Dependency Prevention

**Problem**: Systems need Agent, Agent could need Systems (circular).

**Solution**: Clear layering with TYPE_CHECKING:

```python
# agent.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..econ.utility import Utility  # Type hint only, not runtime

# This allows:
#   - agent.py imports nothing from systems/
#   - systems/ imports Agent freely
#   - No circular imports at runtime
```

### Third-Party Dependencies

```
Core Engine:
  numpy (RNG, numerical operations)
  
GUI Applications:
  PyQt5 (launcher, log viewer)
  pygame (renderer)

Telemetry:
  sqlite3 (stdlib, no external dep)

Scenarios:
  pyyaml (YAML parsing)

Development:
  pytest (testing)
  black (formatting - not in runtime)
  mypy (type checking - not in runtime)
```

**No heavy dependencies**: No TensorFlow, no pandas, no scipy. Keeps it lightweight and educational.

---

## Part 7: Testing Architecture

### Test Organization

```
tests/
  │
  ├── Unit Tests (test individual components)
  │   ├── test_core_state.py          # Agent, Grid, Inventory
  │   ├── test_utility_*.py (x5)      # Each utility type
  │   ├── test_quotes_money.py        # Quote computation
  │   ├── test_matching_money.py      # Generic matching
  │   └── test_reservation_zero_guard.py  # Edge cases
  │
  ├── System Tests (test individual systems)
  │   ├── test_resource_claiming.py   # Claiming logic
  │   ├── test_resource_regeneration.py  # Regen logic
  │   ├── test_mode_schedule.py       # Mode transitions
  │   └── test_trade_cooldown.py      # Cooldown behavior
  │
  ├── Integration Tests (test full scenarios)
  │   ├── test_barter_integration.py  # Barter economy end-to-end
  │   ├── test_money_phase1_integration.py  # Money infrastructure
  │   ├── test_money_phase2_integration.py  # Monetary exchange
  │   ├── test_mixed_regime_integration.py  # Mixed economies
  │   ├── test_mode_integration.py    # Mode × regime interaction
  │   └── test_new_utility_scenarios.py  # 5 utility types
  │
  ├── Validation Tests (test economic correctness)
  │   ├── test_regime_comparison.py   # Compare barter/money/mixed
  │   ├── test_mixed_regime_tie_breaking.py  # Money-first policy
  │   └── test_utility_mix_integration.py  # Heterogeneous populations
  │
  └── Performance Tests
      ├── test_performance.py         # TPS benchmarks
      └── test_performance_scenarios.py  # Large-scale stress tests
```

### Test Strategy per Layer

| Layer | Test Approach | Example |
|-------|--------------|---------|
| **Data (core/)** | Unit test invariants, edge cases | `test_core_state.py`: Inventory non-negative |
| **Economic (econ/)** | Validate against theory | `test_utility_ces.py`: MRS formula correct |
| **Systems** | Mock simulation state, test logic | `test_resource_claiming.py`: Claims respected |
| **Integration** | Full scenario, verify telemetry | `test_barter_integration.py`: Trades occur |
| **Performance** | Stress tests, TPS benchmarks | `test_performance.py`: 400 agents @ 10+ TPS |

### Determinism Testing

**Critical property**: Same seed → identical results.

**Test approach:**
```python
def test_deterministic_reproduction():
    """Run same scenario twice, verify bit-identical telemetry."""
    sim1 = Simulation(scenario, seed=42)
    sim1.run(max_ticks=100)
    db1 = query_telemetry(sim1.telemetry.run_id)
    
    sim2 = Simulation(scenario, seed=42)
    sim2.run(max_ticks=100)
    db2 = query_telemetry(sim2.telemetry.run_id)
    
    assert db1 == db2  # Exact match required
```

**Enforced by:**
- Sorted iteration (by agent ID, pair ID)
- Explicit tie-breaking rules
- Deterministic RNG (numpy PCG64 with seed)
- No reliance on dict iteration order (Python 3.7+)

---

## Part 8: Extensibility Points

### Where New Features Can Plug In

#### 1. New Utility Types

**Location**: `src/vmt_engine/econ/utility.py`

**Interface**:
```python
class Utility(ABC):
    @abstractmethod
    def u_goods(self, A: int, B: int) -> float:
        """Compute utility from goods only."""
    
    @abstractmethod
    def mu_A(self, A: int, B: int) -> float:
        """Marginal utility of A."""
    
    @abstractmethod
    def mu_B(self, A: int, B: int) -> float:
        """Marginal utility of B."""
```

**Steps to add**:
1. Create `class UMyUtility(Utility)` implementing interface
2. Add to `create_utility()` factory
3. Add to schema as new utility type
4. Write tests in `test_utility_myutility.py`

**Example**: Adding CES was this easy, Stone-Geary was this easy, etc.

#### 2. New Matching Protocols

**Location**: `src/vmt_engine/systems/matching.py`

**Future interface** (from Protocol Modularization proposal):
```python
class MatchingProtocol(ABC):
    @abstractmethod
    def match_agents(self, sim: Simulation) -> list[tuple[int, int]]:
        """Return list of matched agent pairs."""
```

**Planned implementations**:
- `ThreePassMatching` (current, wrap existing logic)
- `PostedPriceMarket` (centralized clearing)
- `ContinuousDoubleAuction` (order book)
- `RandomMatching` (baseline comparison)

**Steps to add**:
1. Implement `MatchingProtocol` interface
2. Register in `matching_registry`
3. Add to schema as `matching_protocol: "posted_price"`
4. Write tests

#### 3. New Systems (Phases)

**Location**: `src/vmt_engine/systems/`

**Interface**:
```python
class System(ABC):
    @abstractmethod
    def execute(self, sim: Simulation) -> None:
        """Execute this phase of the tick cycle."""
```

**Current systems**: Perception, Decision, Movement, Trade, Forage, Regeneration, Housekeeping

**Future systems** (Strategic Roadmap):
- `MarketSystem` (centralized exchange)
- `ProductionSystem` (firms producing goods)
- `LaborSystem` (agents earning money)
- `AuctionSystem` (mechanism design experiments)

**Steps to add**:
1. Create `class MySystem(System)` implementing interface
2. Add to `simulation.systems` list
3. Decide where in 7-phase cycle it belongs (or extend to 8-phase)
4. Write system tests

#### 4. New Economic Models

**Example**: Adding game theory.

**Changes needed**:
1. **Agent state**: Add `strategy`, `beliefs`, `payoffs`
2. **Utility**: Create `StrategicUtility` (includes beliefs)
3. **Decision**: Modify to include strategic reasoning
4. **Telemetry**: Log strategies, beliefs, payoffs
5. **Scenarios**: Add game-theoretic configurations

**Estimated effort**: 40-60 hours (significant but feasible).

---

## Part 9: Performance Characteristics

### Computational Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| **Perception (per agent)** | O(k) | k = neighbors within vision_radius |
| **Decision (pairing)** | O(N·k) | N agents, k neighbors each |
| **Movement** | O(N) | Each agent moves once |
| **Trading** | O(P) | P = number of paired agents (typically P ≤ N/2) |
| **Foraging** | O(N) | Each agent checks once |
| **Regeneration** | O(R) | R = number of resource cells |
| **Housekeeping** | O(N) | Each agent recomputes quotes |
| **Per Tick Total** | O(N·k + R) | Dominated by perception + decision |

### Spatial Index Optimization

**Without spatial index:**
- Perception: O(N²) (each agent checks all agents)
- Total per tick: O(N²)

**With spatial index:**
- Perception: O(N·k) where k = local density
- Bucket size = max(vision_radius, interaction_radius)
- Typical k << N (spatially distributed agents)

**Impact:**
- 100 agents, uniform grid: O(N²) = 10,000 vs. O(N·k) ≈ 800 (k≈8)
- 400 agents: O(N²) = 160,000 vs. O(N·k) ≈ 3,200 (k≈8)

### Benchmark Results (from tests)

| Scenario | Agents | Grid | TPS | Notes |
|----------|--------|------|-----|-------|
| Small | 10 | 16×16 | 100+ | Interactive, smooth |
| Medium | 50 | 32×32 | 50-80 | Standard demos |
| Large | 400 | 64×64 | 10-15 | Performance test |

**Target**: 10+ TPS for educational use (acceptable responsiveness).

**Achieved**: All targets met per `test_performance.py`.

---

## Part 10: Future Architecture Evolution

### Planned Major Changes (from ADR-001 and proposals)

#### 1. Protocol Modularization (Post-v1.0)

**Goal**: Enable swappable matching algorithms, search protocols.

**Current**:
```python
# decision.py: Fixed three-pass pairing
def execute(self, sim):
    pass1_mutual_consent(...)
    pass2_greedy_fallback(...)
```

**Future**:
```python
# decision.py: Pluggable protocols
def execute(self, sim):
    matching_protocol = sim.config.matching_protocol
    pairs = matching_protocol.match_agents(sim)
```

**Benefits**:
- Easy to add new matching algorithms (posted-price, auctions)
- Compare protocols in same simulation framework
- Research-friendly (test novel mechanisms)

**Estimated effort**: 6-9 weeks (160-200 hours).

#### 2. Markets (Strategic Roadmap Phase C)

**Goal**: Centralized exchange, order books, market clearing.

**Architecture additions**:
```python
# New system
class MarketSystem(System):
    def execute(self, sim):
        # Collect orders from agents
        # Match buyers and sellers
        # Clear at equilibrium price
        # Execute trades
```

**Requires**: Protocol Modularization (to cleanly separate market matching from bilateral matching).

#### 3. Production (Strategic Roadmap Phase D)

**Goal**: Firms producing goods using inputs.

**Architecture additions**:
```python
# New entity type
class Firm:
    id: int
    production_function: ProductionFunction
    inventory: Inventory
    # ...

# New system
class ProductionSystem(System):
    def execute(self, sim):
        for firm in sim.firms:
            outputs = firm.produce(inputs)
```

**Requires**: Refactoring to support multiple entity types (agents, firms, resources).

#### 4. Game Theory (Strategic Roadmap Phase F)

**Goal**: Strategic interaction, beliefs, repeated games.

**Architecture additions**:
```python
# Extended agent state
class Agent:
    # ... existing fields ...
    strategy: Strategy
    beliefs: dict[int, Belief]  # beliefs about other agents
    memory: list[Outcome]  # game history

# New system
class StrategicInteractionSystem(System):
    def execute(self, sim):
        # Agents update beliefs
        # Agents choose strategies
        # Game outcomes computed
        # Payoffs distributed
```

**Requires**: Significant refactoring of decision logic (strategic vs. parametric).

---

## Conclusion

VMT's architecture is **well-structured** with clear layers:

1. **Data Layer**: Clean data structures (Agent, Grid, State)
2. **Logic Layer**: 7 systems implementing tick cycle phases
3. **Economic Layer**: Utility functions and matching algorithms
4. **Interface Layer**: GUIs, telemetry, scenario loading
5. **User Layer**: YAML scenarios, analysis tools

**Key strengths:**
- 7-phase cycle provides clear organizing principle
- Determinism enforced through sorted iteration and explicit tie-breaking
- Money system cleanly integrated via layered approach
- Extensibility points clearly defined

**Architectural tensions** (see Critical Problems doc):
- DecisionSystem complexity (mixing pairing, resources, claims)
- Trade/Matching boundary unclear
- Parameter sprawl in flat config structure

**Planned evolution:**
- Protocol Modularization (post-v1.0)
- Markets (Strategic Phase C)
- Production (Strategic Phase D)
- Game Theory (Strategic Phase F)

**Overall verdict:** Solid foundation for educational and research platform, with clear path forward for major extensions.

