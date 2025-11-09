# VMT Code Review Guide for New Developers

**Purpose:** This guide helps new developers quickly understand the VMT codebase structure and prioritize what to review. Whether you're conducting a code review, onboarding, or contributing, this document provides a roadmap through the ~13,000 lines of Python code.

**Last Updated:** 2025-11-09  
**Target Audience:** Developers with economics background, Python proficiency, and interest in agent-based modeling

---

## Table of Contents

1. [Quick Start: First Hour](#quick-start-first-hour)
2. [Core Concepts You Must Understand](#core-concepts-you-must-understand)
3. [Suggested Reading Order](#suggested-reading-order)
4. [File-by-File Reference Guide](#file-by-file-reference-guide)
5. [Testing Strategy & Key Tests](#testing-strategy--key-tests)
6. [Common Patterns & Idioms](#common-patterns--idioms)
7. [What to Look For in Code Review](#what-to-look-for-in-code-review)
8. [Red Flags & Known Issues](#red-flags--known-issues)

---

## Quick Start: First Hour

### Must-Read Documents (30 minutes)

Read these in order before diving into code:

1. **[README.md](../README.md)** (10 min)
   - Overview of the three-track vision
   - The 7-phase tick cycle
   - Protocol architecture overview
   - Current limitations (bargaining stubs, no money)

2. **[docs/planning/PROJECT_STATUS_REVIEW.md](../planning/PROJECT_STATUS_REVIEW.md)** (10 min)
   - Recent refactoring (protocol decoupling)
   - Current state vs. planned features
   - Known issues and technical debt

3. **[docs/2_typing_overview.md](../2_typing_overview.md)** (10 min)
   - Core data types (Inventory, Quote, Position)
   - `Decimal` quantities (4 decimal places)
   - Type contracts and invariants

### Must-Run Commands (30 minutes)

```bash
# 1. Set up environment
cd /Users/cmfunderburk/CODE_PROJECTS/vmt-dev
source venv/bin/activate

# 2. Run minimal scenario (observe 7-phase cycle)
python main.py scenarios/demos/minimal_2agent.yaml

# 3. View telemetry database (primary debugging tool)
python view_logs.py

# 4. Run determinism test (critical property)
pytest tests/test_simulation_init.py::test_deterministic_execution -v

# 5. Run full test suite to understand coverage
pytest --tb=short
```

**What to observe:**
- How agents perceive, decide, move, trade, and forage
- Telemetry logging (every state change recorded in SQLite)
- Deterministic execution (same seed = identical results)

---

## Core Concepts You Must Understand

### 1. The 7-Phase Tick Cycle (THE MOST IMPORTANT CONCEPT)

Every simulation tick executes these phases **in strict order**:

```
1. Perception      → Agents observe local environment (frozen snapshot)
2. Decision        → Search + Matching protocols select targets & form pairs
3. Movement        → Agents move toward targets
4. Trade           → Paired agents negotiate via bargaining protocol
5. Forage          → Unpaired agents harvest resources
6. Resource Regen  → Resources regrow
7. Housekeeping    → Cleanup, telemetry logging, quote updates
```

**Why this matters:**
- **Determinism** depends on strict phase ordering
- **Race conditions** prevented by frozen snapshots
- **Effect-based architecture**: protocols return declarative effects, core applies them

**Where to see it:** `src/vmt_engine/simulation.py:Simulation.tick()`

### 2. Protocol Architecture (Recently Refactored - Nov 2025)

Three independent protocol types control institutional rules:

| Protocol Type | Domain Module | Phase | Perspective | Input | Output |
|--------------|---------------|-------|-------------|-------|--------|
| **Search** | `agent_based.search` | 2 (sub-phase 1) | Agent-local | `WorldView` | `SetTarget` effects |
| **Matching** | `game_theory.matching` | 2 (sub-phase 2-3) | Global matchmaker | `ProtocolContext` | `Pair`/`Unpair` effects |
| **Bargaining** | `game_theory.bargaining` | 4 | Self-contained | Agents directly | `TradeEffect` |

**Key architectural principle:**
- Search uses **heuristics** (quote overlaps) for speed
- Matching uses **lightweight evaluation** (TradePotentialEvaluator)
- Bargaining uses **full utility calculations** for precise negotiation

**Critical insight:**
- Only `compensating_block` bargaining is fully implemented
- `split_difference` and `take_it_or_leave_it` are honest stubs (raise NotImplementedError)

### 3. Type System: Decimal Quantities

**Recent change (Nov 2025):** Quantities moved from `int` to `Decimal` (4 decimal places)

```python
from decimal import Decimal

# ✅ Correct
inv = Inventory(A=Decimal('10.5'), B=Decimal('5.25'))

# ⚠️ Automatic conversion (float → Decimal, may have precision artifacts)
inv = Inventory(A=10.5, B=5.25)  # Converted via decimal_from_numeric()

# ❌ Wrong (don't use float directly in logic)
amount = 10.5  # Use Decimal('10.5') instead
```

**Storage:** Database uses integer minor units (multiply by 10^4)  
**Conversion utilities:** `to_storage_int()`, `from_storage_int()`  
**Source:** `src/vmt_engine/core/decimal_config.py`

### 4. Effect-Based Architecture

Protocols don't mutate state directly. They return **declarative effects**:

```python
# Example: Search protocol returns SetTarget effect
class MySearchProtocol(SearchProtocol):
    def execute(self, context: WorldView) -> list[Effect]:
        return [
            SetTarget(
                protocol_name="my_search",
                tick=context.current_tick,
                agent_id=agent.id,
                target=target_pos
            )
        ]
```

**Core applies effects** in `systems/` modules (movement, trading, etc.)

**Why this pattern:**
- Separation of concerns (logic vs. execution)
- Easier testing (inspect effects without state changes)
- Telemetry logging (all effects recorded)

### 5. Telemetry Database as Primary Debugging Tool

**Location:** `logs/telemetry.db` (SQLite)

**Tables:**
- `agent_snapshots` — Tick-by-tick agent state (position, inventory, utility)
- `trades` — All executed trades with quantities and prices
- `pairing_events` — When agents pair/unpair
- `agent_preferences` — Search protocol preference lists
- `tick_states` — Global state per tick

**Access:**
```bash
python view_logs.py  # Interactive PyQt6 viewer
sqlite3 logs/telemetry.db  # Direct SQL queries
```

**Critical for debugging:**
- Non-determinism issues (compare runs with same seed)
- Protocol behavior (why did agents pair/unpair?)
- Trade failures (reservation prices, utility changes)

---

## Suggested Reading Order

### Phase 1: Core Fundamentals (2-3 hours)

Start with the foundational data structures and simulation loop:

1. **`src/vmt_engine/core/state.py`** (30 min)
   - `Inventory`, `Quote`, `Position` data structures
   - Type contracts and validation
   - **Why first:** These types appear everywhere

2. **`src/vmt_engine/core/decimal_config.py`** (15 min)
   - Decimal conversion utilities
   - Storage format (integer minor units)
   - Precision configuration

3. **`src/vmt_engine/core/agent.py`** (30 min)
   - Agent data structure
   - Runtime state fields (paired_with_id, cooldowns, etc.)
   - Validation logic

4. **`src/vmt_engine/simulation.py`** (60 min)
   - Main simulation loop
   - Protocol initialization
   - The 7-phase tick() method
   - **Focus on:** `tick()` method starting line ~150

5. **`src/vmt_engine/protocols/base.py`** (30 min)
   - Effect types (SetTarget, Pair, TradeEffect, etc.)
   - Protocol base class
   - Effect validation

### Phase 2: Systems - The 7 Phases (3-4 hours)

Read `systems/` modules in tick-cycle order:

1. **`src/vmt_engine/systems/perception.py`** (30 min)
   - WorldView construction (frozen snapshot)
   - Vision radius filtering
   - Perception cache management

2. **`src/vmt_engine/systems/decision.py`** (60 min)
   - Search protocol execution (target selection)
   - Matching protocol execution (pairing formation)
   - Resource claiming logic
   - **This is complex** — coordinates search + matching

3. **`src/vmt_engine/systems/movement.py`** (30 min)
   - Deterministic tie-breaking rules
   - Diagonal deadlock resolution
   - Movement budget enforcement

4. **`src/vmt_engine/systems/trading.py`** (45 min)
   - Bargaining protocol invocation
   - Trade validation (reservation prices)
   - Cooldown management
   - Pairing maintenance/dissolution

5. **`src/vmt_engine/systems/foraging.py`** (30 min)
   - Resource harvesting
   - Single-harvester enforcement
   - Pairing exclusion (paired agents don't forage)

6. **`src/vmt_engine/systems/housekeeping.py`** (30 min)
   - Quote refresh logic
   - Pairing integrity checks
   - Telemetry logging calls

7. **`src/vmt_engine/systems/quotes.py`** (20 min)
   - MRS calculation (Marginal Rate of Substitution)
   - Reservation price computation
   - Quote broadcasting

### Phase 3: Protocol Implementations (2-3 hours)

Now understand the configurable mechanisms:

#### Search Protocols (Agent Perspective)

1. **`src/vmt_engine/agent_based/search/base.py`** (20 min)
   - SearchProtocol ABC
   - WorldView structure

2. **`src/vmt_engine/agent_based/search/distance_discounted.py`** (45 min)
   - Default search protocol
   - Distance-discounted surplus scoring
   - Preference list construction
   - **Most complex search protocol** — read carefully

3. **`src/vmt_engine/agent_based/search/myopic.py`** (15 min)
   - Nearest-neighbor greedy search
   - Simpler alternative to distance_discounted

4. **`src/vmt_engine/agent_based/search/random_walk.py`** (10 min)
   - Random exploration (baseline comparison)

#### Matching Protocols (Global Perspective)

1. **`src/vmt_engine/game_theory/matching/base.py`** (20 min)
   - MatchingProtocol ABC
   - ProtocolContext structure (omniscient access)

2. **`src/vmt_engine/game_theory/matching/three_pass.py`** (45 min)
   - Default matching protocol
   - Three-pass algorithm: mutual consent → greedy fallback → unpaired pairing
   - **Complex logic** — read with tests

3. **`src/vmt_engine/game_theory/matching/greedy.py`** (30 min)
   - Greedy surplus maximization
   - Sorting by trade potential

4. **`src/vmt_engine/game_theory/matching/random.py`** (10 min)
   - Random pairing (baseline)

#### Bargaining Protocols (Self-Contained)

1. **`src/vmt_engine/game_theory/bargaining/base.py`** (15 min)
   - BargainingProtocol ABC
   - negotiate() signature (receives agents directly)

2. **`src/vmt_engine/game_theory/bargaining/compensating_block.py`** (60 min)
   - **THE ONLY FULLY IMPLEMENTED BARGAINING PROTOCOL**
   - Discrete quantity search (1, 2, 3, ...)
   - Price candidate generation
   - Full utility calculations
   - **Critical to understand** — this is VMT's foundational trade mechanism

3. **`src/vmt_engine/game_theory/bargaining/split_difference.py`** (5 min)
   - Stub only (raises NotImplementedError)
   - Placeholder for equal surplus division

4. **`src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py`** (5 min)
   - Stub only (raises NotImplementedError)
   - Placeholder for asymmetric power bargaining

### Phase 4: Economic Foundations (1-2 hours)

1. **`src/vmt_engine/econ/base.py`** (15 min)
   - Utility ABC
   - compute() and mrs() signatures

2. **`src/vmt_engine/econ/utility.py`** (60 min)
   - CES utility (default)
   - Linear, Quadratic, StoneGeary, Translog
   - create_utility() factory
   - **Focus on:** CES and Linear first, others are specialized

3. **`src/vmt_engine/core/grid.py`** (20 min)
   - Grid spatial structure
   - Resource distribution
   - Resource regeneration state

4. **`src/vmt_engine/core/spatial_index.py`** (15 min)
   - Efficient neighbor queries
   - Vision radius filtering

### Phase 5: Infrastructure (1 hour)

1. **`src/scenarios/schema.py`** (30 min)
   - YAML scenario structure
   - Validation logic
   - Default values

2. **`src/scenarios/loader.py`** (20 min)
   - Scenario loading
   - Protocol resolution (YAML → Python instances)

3. **`src/telemetry/database.py`** (30 min)
   - SQLite schema
   - Table definitions
   - Storage format

4. **`src/telemetry/db_loggers.py`** (30 min)
   - Logging functions
   - Decimal → integer conversion
   - Batch insertion

### Phase 6: UI & Tooling (Optional, 1-2 hours)

1. **`src/vmt_launcher/launcher.py`** (30 min)
   - PyQt6 GUI
   - Scenario selection
   - Parameter overrides

2. **`src/vmt_log_viewer/viewer.py`** (30 min)
   - Telemetry database viewer
   - Interactive queries

3. **`src/vmt_pygame/renderer.py`** (30 min)
   - Real-time visualization
   - Agent and resource rendering

---

## File-by-File Reference Guide

### Core Engine (`src/vmt_engine/`)

#### Top-Level

| File | Lines | Complexity | Purpose | Priority |
|------|-------|------------|---------|----------|
| `simulation.py` | ~460 | High | Main simulation loop, 7-phase orchestration | **Critical** |

#### Core Primitives (`core/`)

| File | Lines | Complexity | Purpose | Priority |
|------|-------|------------|---------|----------|
| `state.py` | ~60 | Low | Inventory, Quote, Position data structures | **Critical** |
| `agent.py` | ~50 | Low | Agent data structure, validation | **Critical** |
| `decimal_config.py` | ~80 | Medium | Decimal conversion, storage utilities | **Critical** |
| `grid.py` | ~200 | Medium | Spatial grid, resource management | High |
| `spatial_index.py` | ~100 | Medium | Efficient neighbor queries | Medium |

#### Systems (`systems/`)

All systems are **high priority** — they implement the 7 phases.

| File | Lines | Complexity | Purpose | Phase |
|------|-------|------------|---------|-------|
| `perception.py` | ~120 | Medium | WorldView construction | 1 |
| `decision.py` | ~250 | **High** | Search + matching coordination | 2 |
| `movement.py` | ~180 | Medium | Deterministic movement | 3 |
| `trading.py` | ~200 | High | Bargaining, validation, cooldowns | 4 |
| `foraging.py` | ~140 | Low | Resource harvesting, regeneration | 5-6 |
| `housekeeping.py` | ~150 | Medium | Cleanup, telemetry, quotes | 7 |
| `quotes.py` | ~100 | Medium | MRS calculation, quote computation | Used by 7 |
| `trade_evaluation.py` | ~120 | Medium | TradePotentialEvaluator (heuristic) | Used by 2 |

#### Protocols (`protocols/`)

| File | Lines | Complexity | Purpose | Priority |
|------|-------|------------|---------|----------|
| `base.py` | ~300 | High | Effect types, protocol ABC | **Critical** |
| `context.py` | ~120 | Medium | ProtocolContext (global view) | High |
| `context_builders.py` | ~100 | Low | Context construction utilities | Medium |
| `registry.py` | ~80 | Low | Protocol registration, factory | Medium |
| `telemetry_schema.py` | ~60 | Low | Telemetry data structures | Low |

#### Agent-Based Track (`agent_based/search/`)

| File | Lines | Complexity | Purpose | Priority |
|------|-------|------------|---------|----------|
| `base.py` | ~80 | Low | SearchProtocol ABC, WorldView | High |
| `distance_discounted.py` | ~200 | **High** | Default search (distance-discounted surplus) | **Critical** |
| `myopic.py` | ~100 | Low | Nearest-neighbor search | Medium |
| `random_walk.py` | ~80 | Low | Random exploration | Low |

#### Game Theory Track (`game_theory/`)

**Matching** (`game_theory/matching/`)

| File | Lines | Complexity | Purpose | Priority |
|------|-------|------------|---------|----------|
| `base.py` | ~60 | Low | MatchingProtocol ABC | High |
| `three_pass.py` | ~250 | **High** | Default matching (3-pass algorithm) | **Critical** |
| `greedy.py` | ~150 | Medium | Greedy surplus maximization | Medium |
| `random.py` | ~80 | Low | Random pairing | Low |

**Bargaining** (`game_theory/bargaining/`)

| File | Lines | Complexity | Purpose | Priority |
|------|-------|------------|---------|----------|
| `base.py` | ~50 | Low | BargainingProtocol ABC | High |
| `compensating_block.py` | ~350 | **Very High** | Discrete quantity search, full implementation | **CRITICAL** |
| `split_difference.py` | ~40 | N/A | Stub only (NotImplementedError) | Low |
| `take_it_or_leave_it.py` | ~40 | N/A | Stub only (NotImplementedError) | Low |

#### Economic Models (`econ/`)

| File | Lines | Complexity | Purpose | Priority |
|------|-------|------------|---------|----------|
| `base.py` | ~40 | Low | Utility ABC | High |
| `utility.py` | ~400 | High | CES, Linear, Quadratic, StoneGeary, Translog | High |

### Infrastructure

#### Scenarios (`src/scenarios/`)

| File | Lines | Complexity | Purpose | Priority |
|------|-------|------------|---------|----------|
| `schema.py` | ~300 | Medium | YAML schema, validation | High |
| `loader.py` | ~200 | Medium | Scenario loading, protocol resolution | High |
| `protocol_factory.py` | ~120 | Low | Protocol instantiation | Medium |

#### Telemetry (`src/telemetry/`)

| File | Lines | Complexity | Purpose | Priority |
|------|-------|------------|---------|----------|
| `database.py` | ~200 | Medium | SQLite schema, initialization | High |
| `db_loggers.py` | ~300 | Medium | Logging functions, batch insertion | High |
| `config.py` | ~80 | Low | Telemetry configuration | Low |

#### Launcher & Viewer (`src/vmt_launcher/`, `src/vmt_log_viewer/`)

| File | Lines | Complexity | Purpose | Priority |
|------|-------|------------|---------|----------|
| `launcher.py` | ~400 | Medium | PyQt6 GUI launcher | Low |
| `viewer.py` | ~350 | Medium | Telemetry database viewer | Medium |
| `renderer.py` | ~300 | Medium | Pygame real-time visualization | Low |

---

## Testing Strategy & Key Tests

### Testing Philosophy

**Determinism is the most critical property:**
- Same scenario + seed = identical outcomes (down to exact floats)
- Use `sim.rng`, never Python's `random` module
- Every protocol must have a determinism test

### Test Categories

#### 1. Core Determinism Tests (MUST REVIEW)

| Test File | Purpose | What to Check |
|-----------|---------|---------------|
| `test_simulation_init.py` | Multi-tick determinism | Exact state reproduction across runs |
| `test_foundational_baseline_trades.py` | Trade determinism | Same trades at same ticks |

**How to verify:**
```bash
# Run same test 10 times, should always pass
for i in {1..10}; do pytest tests/test_simulation_init.py::test_deterministic_execution -v; done
```

#### 2. Protocol Integration Tests

| Test File | Protocol | What to Check |
|-----------|----------|---------------|
| `test_distance_discounted.py` | Search (N/A yet) | Would test preference list construction |
| `test_myopic_search.py` | Search | Nearest-neighbor selection |
| `test_random_walk_search.py` | Search | Random exploration |
| `test_three_pass_matching.py` | Matching (N/A yet) | Would test 3-pass algorithm |
| `test_greedy_surplus_matching.py` | Matching | Greedy pairing |
| `test_random_matching.py` | Matching | Random pairing |
| `test_bargaining_refactor_integration.py` | Bargaining | compensating_block correctness |
| `test_split_difference.py` | Bargaining | Stub raises NotImplementedError |
| `test_take_it_or_leave_it_bargaining.py` | Bargaining | Stub raises NotImplementedError |

#### 3. Utility Function Tests

Each utility function has dedicated tests:
- `test_utility_ces.py` — CES utility (default)
- `test_utility_linear.py` — Linear utility
- `test_utility_quadratic.py` — Quadratic utility
- `test_utility_stone_geary.py` — Stone-Geary utility
- `test_utility_translog.py` — Translog utility
- `test_utility_mix_integration.py` — Heterogeneous agents

**What to check:**
- MRS calculation correctness
- Boundary conditions (zero quantities)
- Parameter validation

#### 4. Mechanism Tests

| Test File | Mechanism | What to Check |
|-----------|-----------|---------------|
| `test_trade_cooldown.py` | Cooldowns | Agents respect mutual cooldown periods |
| `test_resource_claiming.py` | Resource claiming | Prevents clustering |
| `test_resource_regeneration.py` | Resource regen | Correct growth rates |
| `test_trade_rounding_and_adjacency.py` | Trade adjacency | Agents must be within interaction_radius |
| `test_reservation_zero_guard.py` | Zero quantities | No divide-by-zero in MRS |

#### 5. System Tests

| Test File | System | What to Check |
|-----------|--------|---------------|
| `test_mode_integration.py` | Mode system | Phase transitions (future feature) |
| `test_mode_schedule.py` | Mode scheduling | Tick-based mode changes |

### Running Tests

```bash
# Full suite
pytest

# Specific category
pytest tests/test_utility*.py -v

# Single test
pytest tests/test_simulation_init.py::test_deterministic_execution -v

# With coverage
pytest --cov=src/vmt_engine --cov-report=html
```

### Test Helpers

**Location:** `tests/helpers/`

| File | Purpose |
|------|---------|
| `scenarios.py` | `create_minimal_scenario()` — Build test scenarios |
| `assertions.py` | Custom assertions for inventory, quotes, etc. |
| `builders.py` | Agent and grid builders |
| `run.py` | Simulation runner utilities |

---

## Common Patterns & Idioms

### 1. Effect-Based Protocol Returns

**Pattern:**
```python
def execute(self, context: WorldView) -> list[Effect]:
    effects = []
    for agent in context.visible_agents:
        if some_condition:
            effects.append(SetTarget(
                protocol_name="my_protocol",
                tick=context.current_tick,
                agent_id=agent.id,
                target=target_pos
            ))
    return effects
```

**Why:** Declarative, testable, separates logic from execution.

### 2. Decimal Quantity Initialization

**Pattern:**
```python
from decimal import Decimal
from vmt_engine.core.decimal_config import decimal_from_numeric, quantize_quantity

# ✅ Best practice
inv = Inventory(A=Decimal('10.5'), B=Decimal('5.25'))

# ✅ Acceptable (auto-conversion)
inv = Inventory(A=10.5, B=5.25)  # Converted via __post_init__

# ⚠️ Use for user input
amount = decimal_from_numeric(user_input)  # Handles int/float/str

# ⚠️ Use for calculations
result = quantize_quantity(a + b)  # Ensures 4 decimal places
```

### 3. MRS Calculation with Zero Guard

**Pattern:**
```python
def compute_mrs(self, inv: Inventory) -> float:
    if inv.A <= 0 or inv.B <= 0:
        return 0.0  # Guard against division by zero
    # ... calculate MRS
```

**Why:** Agents may have zero quantities, especially early in simulation.

### 4. Deterministic Tie-Breaking

**Pattern:**
```python
# Sort by value, break ties by agent ID
sorted_agents = sorted(candidates, key=lambda a: (-potential[a.id], a.id))
```

**Why:** Ensures same results across runs. Always use consistent tie-breakers.

### 5. Telemetry Logging

**Pattern:**
```python
# In systems/
if self.telemetry:
    self.telemetry.log_agent_snapshots(agents, tick)
    self.telemetry.log_trades(trades, tick)
```

**Why:** All state changes must be logged for debugging.

### 6. Protocol Registration

**Pattern:**
```python
from vmt_engine.protocols.registry import register_protocol

@register_protocol("my_protocol_name", protocol_type="search")
class MySearchProtocol(SearchProtocol):
    # ...
```

**Why:** Enables YAML configuration, automatic discovery.

### 7. WorldView Construction (Immutable Snapshot)

**Pattern:**
```python
# In perception.py
world_view = WorldView(
    agent=agent,
    visible_agents=visible,  # Frozen at tick start
    visible_resources=resources,
    current_tick=tick,
    # ...
)
```

**Why:** Prevents race conditions, ensures consistent perception.

---

## What to Look For in Code Review

### Critical Review Areas

#### 1. Determinism Violations

**🚨 Red Flags:**
- Using Python's `random` module instead of `sim.rng`
- Non-deterministic tie-breaking (set iteration, dict iteration)
- Time-based logic (datetime, time.time())
- External state (file I/O without seed, network calls)

**✅ What to check:**
```python
# ❌ BAD
import random
partner = random.choice(candidates)

# ✅ GOOD
partner = self.rng.choice(candidates)

# ❌ BAD
for agent_id in agent_dict:  # Dict iteration order is non-deterministic in Python < 3.7

# ✅ GOOD
for agent_id in sorted(agent_dict.keys()):
```

#### 2. Decimal Precision Issues

**🚨 Red Flags:**
- Mixing `float` and `Decimal` in arithmetic
- Forgetting to quantize after calculations
- Using `==` for Decimal comparisons without quantization

**✅ What to check:**
```python
# ❌ BAD
amount = Decimal('10.5') + 0.3  # Returns Decimal but loses precision

# ✅ GOOD
amount = quantize_quantity(Decimal('10.5') + Decimal('0.3'))

# ❌ BAD
if inv.A == Decimal('10.333333'):  # May fail due to precision

# ✅ GOOD
if abs(inv.A - Decimal('10.333333')) < Decimal('0.0001'):
```

#### 3. Protocol Contract Violations

**🚨 Red Flags:**
- Bargaining protocol mutating agent state directly
- Search protocol accessing agents outside vision_radius
- Matching protocol using agent's local view instead of global context

**✅ What to check:**
```python
# ❌ BAD (in bargaining protocol)
agent_i.inventory.A -= amount  # Direct mutation

# ✅ GOOD
return TradeEffect(
    protocol_name="my_bargaining",
    tick=context.current_tick,
    agent_i_id=agent_i.id,
    agent_j_id=agent_j.id,
    amount=amount,
    # ...
)
```

#### 4. Missing Telemetry Logging

**🚨 Red Flags:**
- State changes without telemetry calls
- New effects without corresponding log entries

**✅ What to check:**
- Every state mutation should have `if self.telemetry: ...` logging

#### 5. Incorrect Phase Ordering

**🚨 Red Flags:**
- Trading logic in movement phase
- Movement logic in perception phase
- Foraging before trading

**✅ What to check:**
- Verify new code respects the 7-phase cycle order

#### 6. Test Coverage Gaps

**🚨 Red Flags:**
- New protocols without determinism tests
- New utility functions without boundary condition tests
- Protocol changes without integration tests

**✅ What to check:**
```bash
# Verify protocol has determinism test
pytest tests/ -k "deterministic" -v

# Verify utility has complete test coverage
pytest tests/test_utility_*.py --cov=src/vmt_engine/econ
```

### Secondary Review Areas

#### 7. Type Safety

**What to check:**
- Type hints on all function signatures
- Proper use of `Optional[]` for nullable fields
- `TYPE_CHECKING` imports to avoid circular dependencies

#### 8. Documentation Quality

**What to check:**
- Module docstrings explain purpose
- Complex algorithms have inline comments
- Protocol contracts documented in class docstrings

#### 9. Performance Concerns

**What to check:**
- O(n²) loops in tight inner loops (e.g., matching protocols)
- Inefficient database queries (missing indices)
- Redundant utility calculations (should cache in worldview)

#### 10. Error Handling

**What to check:**
- Validation in `__post_init__` methods
- Graceful handling of edge cases (zero quantities, empty preference lists)
- Informative error messages

---

## Red Flags & Known Issues

### Known Technical Debt

1. **Bargaining Protocol Stubs**
   - `split_difference` and `take_it_or_leave_it` are NOT implemented
   - They raise `NotImplementedError` when called
   - **Impact:** Only `compensating_block` is usable
   - **Mitigation:** Clearly documented in README

2. **No Money System**
   - Current economy is pure barter (A ↔ B only)
   - Money, prices, and markets are planned for Stage 5
   - **Impact:** Can't study monetary phenomena
   - **Mitigation:** Documented as current limitation

3. **Quote-Based Heuristics**
   - Search and matching use quote overlaps, not full utility
   - **Impact:** May not perfectly predict utility gains for non-linear utilities
   - **Mitigation:** Bargaining phase uses full utility, so good trades still happen

4. **No Learning/Adaptation**
   - Agents use static heuristics (no reinforcement learning, no belief updating)
   - **Impact:** Can't study adaptive behavior
   - **Mitigation:** Planned for future stages

5. **Single-Protocol Limitation**
   - All agents use the same bargaining protocol
   - Can't compare heterogeneous institutional rules within a simulation
   - **Impact:** No within-simulation mechanism comparisons
   - **Mitigation:** Use separate scenarios for protocol comparison

### Potential Bugs to Watch For

1. **Pairing Integrity**
   - Asymmetric pairings (A paired with B, but B not paired with A)
   - **Where:** `systems/housekeeping.py` has defensive checks
   - **Test:** `test_mode_integration.py` verifies pairing consistency

2. **Cooldown Violations**
   - Agents trading with partners in cooldown period
   - **Where:** `systems/decision.py` filters cooldown neighbors
   - **Test:** `test_trade_cooldown.py`

3. **Resource Claim Conflicts**
   - Multiple agents claiming same resource
   - **Where:** `systems/decision.py` resource claiming logic
   - **Test:** `test_resource_claiming.py`

4. **Division by Zero in MRS**
   - When inventory quantities are zero
   - **Where:** `econ/utility.py` in `mrs()` methods
   - **Test:** `test_reservation_zero_guard.py`

5. **Movement Tie-Breaking Non-Determinism**
   - Diagonal deadlock resolution
   - **Where:** `systems/movement.py` tie-breaking logic
   - **Test:** `test_simulation_init.py` (determinism test catches this)

### Anti-Patterns to Avoid

1. **Global Mutable State**
   - ❌ Module-level variables that change during simulation
   - ✅ Pass state via function arguments or `Simulation` instance

2. **Premature Optimization**
   - ❌ Complex caching before profiling
   - ✅ Measure first, optimize second

3. **Tight Coupling**
   - ❌ Systems directly calling other systems
   - ✅ Use effects and let `Simulation.tick()` orchestrate

4. **Ignoring Test Failures**
   - ❌ "It's just a flaky test"
   - ✅ Flaky tests indicate non-determinism bugs

5. **Over-Engineering Protocols**
   - ❌ Abstract base classes with 10 methods
   - ✅ Simple interfaces (`execute()` or `negotiate()`)

---

## Quick Reference: Where to Find Things

### Common Tasks

| Task | File(s) |
|------|---------|
| Add new utility function | `src/vmt_engine/econ/utility.py`, test in `tests/test_utility_*.py` |
| Add new search protocol | `src/vmt_engine/agent_based/search/`, register in `__init__.py` |
| Add new matching protocol | `src/vmt_engine/game_theory/matching/`, register in `__init__.py` |
| Add new bargaining protocol | `src/vmt_engine/game_theory/bargaining/`, register in `__init__.py` |
| Modify tick cycle | `src/vmt_engine/simulation.py:tick()` |
| Change telemetry schema | `src/telemetry/database.py`, migrations in same file |
| Add scenario parameter | `src/scenarios/schema.py:ScenarioConfig` |
| Debug trade failure | `logs/telemetry.db` → `trades` table, check reservation prices |
| Debug pairing issues | `logs/telemetry.db` → `pairing_events` table |
| Debug preference lists | `logs/telemetry.db` → `agent_preferences` table |

### Key Configuration Constants

| Constant | File | Default | Purpose |
|----------|------|---------|---------|
| `QUANTITY_DECIMAL_PLACES` | `core/decimal_config.py` | 4 | Precision for quantities |
| `INTERACTION_RADIUS` | `scenarios/schema.py` | 1 | Max distance for trading |
| `SPREAD` | `systems/quotes.py` | 0.15 | Quote spread (ask/bid gap) |
| `EPSILON` | `game_theory/bargaining/compensating_block.py` | 1e-6 | Utility improvement threshold |

---

## Summary: Code Review Checklist

When reviewing VMT code, verify:

- [ ] **Determinism:** No `random` module, deterministic tie-breaking
- [ ] **Decimal precision:** Proper `Decimal` usage, quantization after calculations
- [ ] **Protocol contracts:** Effects returned, no direct state mutation (except in systems)
- [ ] **Phase ordering:** Logic in correct phase (perception → decision → movement → trade → forage → housekeeping)
- [ ] **Telemetry logging:** All state changes logged
- [ ] **Test coverage:** Determinism tests for protocols, boundary tests for utilities
- [ ] **Type hints:** Complete type annotations
- [ ] **Documentation:** Docstrings explain purpose and edge cases
- [ ] **Error handling:** Validation in `__post_init__`, graceful edge case handling
- [ ] **Performance:** No obvious O(n²) issues in tight loops

---

## Getting Help

- **Architecture questions:** [docs/1_technical_manual.md](../1_technical_manual.md)
- **Type system details:** [docs/2_typing_overview.md](../2_typing_overview.md)
- **Current status:** [docs/planning/PROJECT_STATUS_REVIEW.md](../planning/PROJECT_STATUS_REVIEW.md)
- **Debugging:** `python view_logs.py` → inspect `logs/telemetry.db`
- **Testing issues:** Check `tests/helpers/` for utilities, see `tests/test_simulation_init.py` for determinism patterns

**Remember:** The telemetry database is your friend. When in doubt, query the database to see what actually happened.

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-09  
**Maintainer:** VMT Core Team

