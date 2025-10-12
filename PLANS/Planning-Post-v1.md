# VMT Planning Document — Post-v1 (As-Built Specification)

**Version:** Post-v1.1 (Production)  
**Date:** October 12, 2025  
**Status:** Production Ready — 54+ Tests Passing

---

## Document Purpose

This document serves as the **authoritative specification** for the VMT (Visualizing Microeconomic Theory) simulation engine **as actually implemented and deployed**. It supersedes all previous planning documents (`Planning-FINAL.md`, `algorithmic_planning.md`) and reflects the production system including all enhancements discovered during implementation.

**Key Principle:** This is a **descriptive** document (what exists) rather than **prescriptive** (what should be built). Use this as the source of truth for understanding, maintaining, and extending the system.

---

## Executive Summary

VMT is a modular, visualization-first simulation platform for demonstrating microeconomic behavior. Agents with heterogeneous preferences forage for resources on an NxN grid and engage in bilateral barter trade using reservation-price-based negotiation.

**Core Achievement:** Agents with complementary inventories successfully trade using a price search algorithm, forage sustainably with resource regeneration, and exhibit realistic behavior with cooldown-based loop prevention.

### Production Features
- ✅ **Economic Models:** CES (including Cobb-Douglas) and Linear utilities
- ✅ **Foraging:** Distance-discounted utility seeking with sustainable regeneration
- ✅ **Trading:** Price search algorithm with compensating multi-lot rounding
- ✅ **Behavioral Systems:** Trade cooldowns and resource regeneration cooldowns
- ✅ **SQLite Logging:** Database-backed telemetry with 99%+ space savings (v1.1+)
- ✅ **Interactive Log Viewer:** PyQt5 application for exploring simulation data (v1.1+)
- ✅ **GUI Launcher:** Form-based scenario creation with built-in documentation (v1.1+)
- ✅ **Visualization:** Pygame renderer with interactive controls
- ✅ **Testing:** 54+ comprehensive tests covering all systems

---

## 1. High-Level Architecture

### 1.1 Platform
- **Language:** Python 3.11
- **Visualization:** Pygame (desktop, Windows/Mac)
- **Numerical:** NumPy for RNG and basic operations
- **Configuration:** YAML-based scenarios

### 1.2 Module Structure

```
vmt-dev/
├── vmt_engine/              # Core simulation engine
│   ├── core/                # State structures
│   │   ├── state.py         # Inventory, Quote, Position dataclasses
│   │   ├── grid.py          # Grid and Resource management
│   │   └── agent.py         # Agent representation
│   ├── econ/                # Economic utilities
│   │   └── utility.py       # UCES, ULinear, base interface
│   ├── systems/             # Simulation subsystems
│   │   ├── perception.py    # Vision and neighbor detection
│   │   ├── movement.py      # Pathfinding and targeting
│   │   ├── foraging.py      # Harvesting and regeneration
│   │   ├── quotes.py        # Quote generation and refresh
│   │   └── matching.py      # Trade matching and price search
│   └── simulation.py        # Main tick loop orchestration
├── telemetry/               # Logging and diagnostics
│   ├── database.py          # SQLite database backend (v1.1+)
│   ├── config.py            # LogConfig and LogLevel classes (v1.1+)
│   ├── db_loggers.py        # TelemetryManager (v1.1+)
│   ├── logger.py            # Trade logging (legacy CSV)
│   ├── snapshots.py         # Agent/resource snapshots (legacy CSV)
│   ├── decision_logger.py   # Partner selection logging (legacy CSV)
│   └── trade_attempt_logger.py  # Failed trade diagnostics (legacy CSV)
├── vmt_log_viewer/          # Log viewer application (v1.1+)
│   ├── viewer.py            # Main PyQt5 window
│   ├── queries.py           # SQL query builders
│   ├── csv_export.py        # Database → CSV export
│   └── widgets/             # UI components
│       ├── timeline.py      # Timeline scrubber
│       ├── agent_view.py    # Agent analysis
│       ├── trade_view.py    # Trade visualization
│       └── filters.py       # Query filters
├── vmt_launcher/            # GUI launcher (v1.1+)
│   ├── launcher.py          # Main launcher window
│   ├── scenario_builder.py  # Custom scenario creator
│   └── validator.py         # Input validation
├── scenarios/               # Configuration system
│   ├── schema.py            # ScenarioConfig dataclasses
│   ├── loader.py            # YAML parsing
│   ├── single_agent_forage.yaml
│   └── three_agent_barter.yaml
├── vmt_pygame/              # Visualization
│   └── renderer.py          # Pygame rendering
├── tests/                   # Test suite (45 tests)
└── main.py                  # Entry point
```

---

## 2. Simulation Tick Structure

Each tick follows a **deterministic 7-phase cycle**:

```python
def step(self):
    self.perception_phase()           # 1. Observe neighbors, quotes, resources
    self.decision_phase()              # 2. Choose partners or foraging targets
    self.movement_phase()              # 3. Move toward targets
    self.trade_phase()                 # 4. Execute ONE trade per pair
    self.forage_phase()                # 5. Harvest resources
    self.resource_regeneration_phase() # 6. Regenerate resources (with cooldown)
    self.housekeeping_phase()          # 7. Refresh quotes, log telemetry
    self.tick += 1
```

**Key Properties:**
- **Deterministic:** Agent iteration by ascending `id`, pair ordering by `(min_id, max_id)`
- **One trade per tick:** Agents trade once per tick, then recalculate quotes
- **Deferred updates:** Quote refresh happens in housekeeping, not during trading

---

## 3. Core State Structures

### 3.1 Agent State

```python
@dataclass
class Agent:
    id: int
    pos: Position  # (x, y) tuple
    inventory: Inventory  # A: int, B: int
    utility: Utility  # UCES or ULinear instance
    quotes: Quote  # ask_A_in_B, bid_A_in_B, p_min, p_max
    
    # Behavioral state
    trade_cooldowns: dict[int, int]  # partner_id -> cooldown_until_tick
    
    # Parameters (from scenario)
    vision_radius: int = 5
    move_budget_per_tick: int = 1
```

### 3.2 Grid State

```python
@dataclass
class Resource:
    type: Literal["A", "B"] | None
    amount: int
    original_amount: int  # For regeneration target
    last_harvested_tick: int | None  # For regeneration cooldown

@dataclass
class Grid:
    N: int  # Grid size (NxN)
    cells: dict[(int,int), Resource]
```

### 3.3 Scenario Parameters

```python
@dataclass
class ScenarioParams:
    # Trading
    spread: float = 0.0                  # Bid-ask spread (0.0 = true reservation prices)
    interaction_radius: int = 1          # Max distance for trade (0=same cell, 1=adjacent)
    ΔA_max: int = 5                      # Max trade size to search
    trade_cooldown_ticks: int = 5        # Cooldown after failed trade
    
    # Foraging
    forage_rate: int = 1                 # Units harvested per tick
    vision_radius: int = 5               # Perception range
    move_budget_per_tick: int = 1        # Movement speed
    beta: float = 0.95                   # Time discount factor for foraging
    
    # Resource Regeneration
    resource_growth_rate: int = 0        # Units/tick (0 = disabled)
    resource_max_amount: int = 5         # Never exceed original_amount
    resource_regen_cooldown: int = 5     # Ticks after harvest before regen
    
    # Numerical
    epsilon: float = 1e-12               # Zero-safe epsilon
```

**Critical Default:** `spread = 0.0` enables CES utilities to trade effectively with zero/low inventories.

---

## 4. Economic Models

### 4.1 Supported Utility Functions

#### CES Utility (Constant Elasticity of Substitution)
```python
class UCES(Utility):
    def __init__(self, rho: float, wA: float, wB: float):
        # U = [wA·A^ρ + wB·B^ρ]^(1/ρ)
        # ρ < 0: Complements, ρ > 0: Substitutes
        # MRS_A_in_B = (wA/wB) · (A/B)^(ρ-1)
```

**Special Case:** Cobb-Douglas is CES with `ρ → 0` limit, implemented as separate case in utility evaluation.

#### Linear Utility (Perfect Substitutes)
```python
class ULinear(Utility):
    def __init__(self, vA: float, vB: float):
        # U = vA·A + vB·B
        # MRS_A_in_B = vA/vB (constant)
```

### 4.2 Reservation Price Interface

All utilities implement:
```python
def reservation_bounds_A_in_B(self, A: int, B: int, eps: float) -> tuple[float, float]:
    """
    Returns (p_min, p_max) where:
    - p_min: minimum B-per-A to willingly sell 1 A (ΔU ≥ 0)
    - p_max: maximum B-per-A to willingly buy 1 A (ΔU ≥ 0)
    
    For CES/Linear: p_min = p_max = MRS (analytic)
    Handles A=0 or B=0 via epsilon shift for ratio calculations
    """
```

### 4.3 Zero-Inventory Handling

**Problem:** CES utilities with A=0 or B=0 produce undefined MRS.

**Solution:** Zero-safe shift for MRS calculation only:
```python
A_safe = max(A, epsilon)
B_safe = max(B, epsilon)
MRS = (wA/wB) * (A_safe/B_safe)**(rho - 1)
```

**Important:** This shift applies **only** to MRS/ratio calculations, not to utility values `u(A, B)` or inventory updates.

---

## 5. Quote System

### 5.1 Quote Generation

```python
def compute_quotes(agent, spread, epsilon):
    p_min, p_max = agent.utility.reservation_bounds_A_in_B(
        agent.inventory.A, 
        agent.inventory.B, 
        epsilon
    )
    agent.quotes.ask_A_in_B = p_min * (1 + spread)
    agent.quotes.bid_A_in_B = p_max * (1 - spread)
    agent.quotes.p_min = p_min  # Store for telemetry
    agent.quotes.p_max = p_max
```

### 5.2 Quote Refresh Triggers

Quotes recalculate whenever utility changes:
- After trade (inventory changed)
- After foraging (inventory changed)
- In housekeeping phase (deferred from trading phase)

### 5.3 Quote Broadcasting

- Quotes visible to all agents within `vision_radius`
- Read-only snapshot taken during perception phase
- Quotes used for partner selection and movement decisions

---

## 6. Partner Selection & Movement

### 6.1 Surplus Calculation

For agent *i* considering neighbor *j*:

```python
overlap_dir1 = bid_A_in_B_i - ask_A_in_B_j  # i buys A from j
overlap_dir2 = bid_A_in_B_j - ask_A_in_B_i  # j buys A from i
best_overlap = max(overlap_dir1, overlap_dir2)
```

Positive overlap indicates feasible price interval exists.

### 6.2 Trade Cooldown Filtering

```python
def choose_partner(agent, neighbors, current_tick):
    candidates = []
    for neighbor in neighbors:
        # Filter cooldown partners
        if neighbor.id in agent.trade_cooldowns:
            if current_tick < agent.trade_cooldowns[neighbor.id]:
                continue  # Skip, still in cooldown
            else:
                del agent.trade_cooldowns[neighbor.id]  # Expired
        
        # Calculate surplus
        surplus = calculate_surplus(agent, neighbor)
        if surplus > 0:
            candidates.append((neighbor, surplus))
    
    # Choose highest surplus, tie-break by lowest ID
    return max(candidates, key=lambda x: (x[1], -x[0].id))[0] if candidates else None
```

### 6.3 Movement Policy

**With partner:**
- Path toward partner (Manhattan distance)
- Movement budget: `move_budget_per_tick` (default: 1)

**Without partner (foraging):**
- Distance-discounted utility seeking (primary mode)
- Calculate for each visible resource cell: `score = ΔU_arrival * β^distance`
- `ΔU_arrival` uses `min(cell.amount, forage_rate)` (actual harvestable amount)
- Move toward highest-scoring cell

---

## 7. Trading System

### 7.1 Trade Pair Algorithm (One Trade Per Tick)

```python
def trade_pair(agent_i, agent_j, params, tick):
    """Execute exactly ONE trade between agents if possible."""
    
    # 1. Determine direction with positive surplus
    if bid_i - ask_j > bid_j - ask_i:
        buyer, seller = agent_i, agent_j
    else:
        buyer, seller = agent_j, agent_i
    
    surplus = buyer.quotes.bid_A_in_B - seller.quotes.ask_A_in_B
    if surplus <= 0:
        return False  # No trade possible
    
    # 2. Find compensating block with price search
    ask, bid = seller.quotes.ask_A_in_B, buyer.quotes.bid_A_in_B
    block = find_compensating_block(buyer, seller, ask, bid, params)
    
    if block is None:
        # Trade failed - set mutual cooldown
        cooldown_until = tick + params['trade_cooldown_ticks']
        agent_i.trade_cooldowns[agent_j.id] = cooldown_until
        agent_j.trade_cooldowns[agent_i.id] = cooldown_until
        return False
    
    # 3. Execute trade (unpack 3-tuple)
    dA, dB, actual_price = block
    buyer.inventory.A += dA
    buyer.inventory.B -= dB
    seller.inventory.A -= dA
    seller.inventory.B += dB
    
    # 4. Mark inventories as changed (quotes refresh in housekeeping)
    # Log trade
    
    return True
```

**Key Change from Original Plan:** One trade per tick instead of multi-block continuation loop.

### 7.2 Price Search Algorithm

The critical innovation that makes CES utilities work:

```python
def find_compensating_block(buyer, seller, ask, bid, params):
    """
    Search for (dA, dB, price) that improves both agents.
    Returns 3-tuple or None.
    """
    dA_max = params['ΔA_max']
    epsilon = params['epsilon']
    
    for dA in range(1, dA_max + 1):
        # Generate price candidates in [ask, bid] range
        price_candidates = generate_price_candidates(ask, bid, dA)
        
        for price in price_candidates:
            dB = int(floor(price * dA + 0.5))  # Round-half-up
            
            if dB <= 0:
                continue
            
            # Check feasibility
            if seller.inventory.A < dA or buyer.inventory.B < dB:
                continue
            
            # Check mutual improvement (ΔU > 0 for both)
            if (improves(buyer, +dA, -dB, epsilon) and 
                improves(seller, -dA, +dB, epsilon)):
                return (dA, dB, price)  # Success!
    
    return None  # No mutually beneficial trade found

def generate_price_candidates(ask, bid, dA):
    """
    Generate smart price samples that target specific integer dB values.
    Also sample evenly across [ask, bid] range.
    Sorted low to high (fairness preference).
    Returns up to 20 candidates.
    """
    candidates = set([ask, bid, (ask + bid) / 2])  # Key prices
    
    # Target prices for specific dB values
    for dB_target in range(1, 6):
        price = dB_target / dA
        if ask <= price <= bid:
            candidates.add(price)
    
    # Even sampling
    for i in range(1, 10):
        candidates.add(ask + (bid - ask) * i / 10)
    
    return sorted(candidates)[:20]  # Cap at 20, early exit typical
```

**Why This Works:**
- Midpoint pricing often fails due to integer rounding effects
- Example: price=1.59 → dB=2 (buyer loses utility), but price=1.0 → dB=1 (both gain)
- Price search tries multiple candidates until finding mutual improvement
- Early exit makes it efficient (typically 2-3 attempts)

### 7.3 Mutual Improvement Check

```python
def improves(agent, dA, dB, epsilon):
    """Check if trade improves agent's utility."""
    A0, B0 = agent.inventory.A, agent.inventory.B
    u0 = agent.utility.u(A0, B0)
    u1 = agent.utility.u(A0 + dA, B0 + dB)
    return u1 > u0 + epsilon
```

Uses actual utility function, not hardcoded formulas.

---

## 8. Foraging & Resource System

### 8.1 Resource Harvesting

```python
def forage(agent, grid, current_tick, forage_rate):
    """Harvest resources on agent's current cell."""
    cell = grid.get_cell(agent.pos)
    
    if cell.resource.amount > 0:
        harvest = min(cell.resource.amount, forage_rate)
        
        # Update inventories
        if cell.resource.type == "A":
            agent.inventory.A += harvest
        else:
            agent.inventory.B += harvest
        
        # Update cell
        cell.resource.amount -= harvest
        cell.resource.last_harvested_tick = current_tick  # For cooldown
        
        # Mark for quote refresh (happens in housekeeping)
```

### 8.2 Resource Regeneration System

**Lifecycle:**
1. Agent harvests any amount → `last_harvested_tick = current_tick`
2. Wait `resource_regen_cooldown` ticks (default: 5)
3. Once cooldown expires, regenerate at `resource_growth_rate` per tick
4. Stop when reaching `original_amount` (per-cell cap)
5. Any harvest during regeneration resets cooldown

**Implementation:**
```python
def regenerate_resources(grid, params, current_tick):
    """Regenerate resources with harvest-based cooldown."""
    growth_rate = params['resource_growth_rate']
    cooldown = params['resource_regen_cooldown']
    
    if growth_rate == 0:
        return  # Regeneration disabled
    
    for cell in grid.all_cells():
        resource = cell.resource
        
        # Skip empty cells or never-harvested cells
        if resource.type is None or resource.last_harvested_tick is None:
            continue
        
        # Check cooldown
        ticks_since_harvest = current_tick - resource.last_harvested_tick
        if ticks_since_harvest < cooldown:
            continue  # Still in cooldown
        
        # Regenerate (capped at original amount)
        if resource.amount < resource.original_amount:
            resource.amount = min(
                resource.amount + growth_rate,
                resource.original_amount
            )
```

**Key Feature:** Cooldown applies to **any harvest**, not just full depletion. This creates sustainable foraging patterns where agents must rotate between resource patches.

---

## 9. Telemetry & Diagnostics

VMT provides two comprehensive telemetry systems: a modern SQLite database system (default) and a legacy CSV system (for backward compatibility).

### 9.1 SQLite Database Logging System (v1.1+)

**Status:** Production ready, default since v1.1

#### Architecture

The modern telemetry system uses SQLite with configurable log levels:

**Components:**
- `telemetry/database.py` - SQLite schema and connection management
- `telemetry/config.py` - LogConfig and LogLevel classes
- `telemetry/db_loggers.py` - TelemetryManager (batch writing)
- `vmt_log_viewer/` - Interactive PyQt5 log viewer application

**Database Schema:**
- `simulation_runs` - Metadata for each run
- `agent_snapshots` - Agent state at each tick
- `resource_snapshots` - Resource distribution over time
- `decisions` - Partner selection and movement decisions
- `trades` - Successful trades only
- `trade_attempts` - All attempts including failures (DEBUG mode)

#### Log Levels

**SUMMARY** (Production):
- Trades only, no periodic snapshots
- **Size:** 0.01% of CSV (~0.09 MB for 500 ticks, 50 agents)
- **Use case:** Final analysis, production runs

**STANDARD** (Default):
- Trades, decisions, agent/resource snapshots
- **Size:** 0.9% of CSV (~5.88 MB for 500 ticks, 50 agents)
- **Use case:** Development, normal analysis

**DEBUG** (Diagnostic):
- Everything including failed trade attempts with utility calculations
- **Size:** 92% of CSV (~593 MB for 500 ticks, 50 agents)
- **Use case:** Debugging trade issues, detailed analysis

#### Usage

```python
from vmt_engine.simulation import Simulation
from telemetry import LogConfig
from scenarios.loader import load_scenario

scenario = load_scenario("scenarios/three_agent_barter.yaml")

# Use preset configurations
log_config = LogConfig.standard()  # or .summary() or .debug()

sim = Simulation(scenario, seed=42, log_config=log_config)
sim.run(max_ticks=1000)
sim.close()

# Database saved to: ./logs/telemetry.db
```

#### Interactive Log Viewer

Launch the PyQt5 log viewer:
```bash
python view_logs.py
```

**Features:**
- Timeline scrubber (navigate through ticks)
- Agent analysis (state, trajectories, trades)
- Trade visualization (details, attempts, statistics)
- Decision exploration (partner selection, movement)
- Resource viewer (distribution over time)
- CSV export (backward compatibility)

#### Performance Benefits

| Metric | CSV (Legacy) | SQLite (Standard) | Improvement |
|--------|--------------|-------------------|-------------|
| **File Size** | 644 MB | 5.88 MB | 99.1% reduction |
| **Load Time** | 30-60s | <1s | 30-60x faster |
| **Query Speed** | N/A | <0.5s | Instant queries |
| **Multi-run Support** | No | Yes | Single database |

### 9.2 Legacy CSV Logging System (v1.0)

**Status:** Maintained for backward compatibility

The original CSV-based system is still available:

```python
# Enable legacy logging
sim = Simulation(scenario, seed=42, use_legacy_logging=True)
```

#### CSV Files (`logs/` directory)

**Trade Logs (`logs/trades.csv`)**
```csv
tick,x,y,buyer_id,seller_id,dA,dB,price,direction
```
Logs every successful trade.

**Trade Attempt Logs (`logs/trade_attempts.csv`)**
```csv
tick,agent_i,agent_j,i_ask,i_bid,j_ask,j_bid,direction,surplus,success,dA,dB,price,reason
```
Logs **all trade attempts**, including failures with diagnostic reasons.

**Agent Snapshots (`logs/agent_snapshots.csv`)**
```csv
tick,agent_id,x,y,A,B,U,partner_id,ask,bid,p_min,p_max
```
Logged **every tick** with complete quote information.

**Decision Logs (`logs/decisions.csv`)**
```csv
tick,agent_id,decision_type,target_id,target_x,target_y,reason
```
Logs partner selection and movement decisions every tick.

**Resource Snapshots (`logs/resource_snapshots.csv`)**
```csv
tick,x,y,type,amount,last_harvested_tick
```
Periodic snapshots of resource states.

### 9.3 Diagnostic Capabilities

Both telemetry systems enable:
- **Trade failure diagnosis:** See exactly why trades fail (no block found, inventory constraints, etc.)
- **Partner lock-in detection:** Identify when agents target each other repeatedly
- **Quote evolution tracking:** Observe how quotes change as inventories shift
- **Convergence analysis:** Measure time to equilibrium
- **Resource dynamics:** Track harvest/regeneration cycles

**Key Insight:** Logging failures was as important as logging successes for building a working system.

### 9.4 Migration and Export

**Backward Compatibility:**
- Export database runs to CSV: Use log viewer or `vmt_log_viewer.csv_export`
- Existing analysis scripts work with exported CSV
- No breaking changes to simulation API

**See Also:** `PLANS/docs/NEW_LOGGING_SYSTEM.md` for complete documentation

---

## 10. Behavioral Systems

### 10.1 Trade Cooldown

**Purpose:** Prevent agents from repeatedly attempting impossible trades.

**Mechanism:**
- After failed trade attempt: both agents enter 5-tick cooldown
- During cooldown: agents cannot select that partner
- Agents forage or seek other partners instead
- Cooldown expires automatically after duration
- Cooldown is mutual and pairwise (not global)

**Configuration:**
```yaml
trade_cooldown_ticks: 5  # Default
trade_cooldown_ticks: 0  # Disable
```

**Impact:** Prevents "partner lock-in loops" where small MRS surplus doesn't translate to feasible discrete trades.

### 10.2 Resource Regeneration Cooldown

**Purpose:** Prevent immediate re-harvesting; create spatial foraging patterns.

**Mechanism:**
- ANY harvest sets `last_harvested_tick`
- Must wait `resource_regen_cooldown` ticks before regeneration starts
- Harvesting during regeneration resets timer
- Creates "resource rest periods"

**Configuration:**
```yaml
resource_growth_rate: 1          # 1 unit/tick (0 = disabled)
resource_regen_cooldown: 5       # 5-tick wait
```

**Impact:** Agents develop spatial foraging strategies, rotating between resource patches.

---

## 11. Determinism & Reproducibility

### 11.1 Deterministic Guarantees

- **Agent iteration:** Ascending `id` order
- **Pair ordering:** `(min_id, max_id)` tuples, ascending
- **Partner tie-breaking:** Highest surplus, then lowest `id`
- **Movement tie-breaking:** Reduce |dx| before |dy|, prefer negative direction
- **RNG seeding:** NumPy Generator with explicit seed
- **Quote snapshots:** Frozen during perception, updated in housekeeping

**Result:** Same seed → identical simulation trajectory

### 11.2 Testing Strategy

**45 tests covering:**
- Core state management (5 tests)
- Utility functions (12 tests) - CES, Linear, edge cases
- Scenario loading (3 tests)
- Simulation initialization (4 tests)
- Foraging (integration tests)
- Resource regeneration (8 tests)
- Trade cooldown (4 tests)
- Trade rounding (2 tests)
- Reservation bounds (5 tests)
- M1 integration (3 tests)

**All 45 passing + 1 skipped**

---

## 12. Pygame Visualization

### 12.1 Rendering

- **Grid:** 32×32 NxN cells
- **Resources:** Color-coded (A=red, B=blue) with amount labels
- **Agents:** Circles with ID labels
- **Inventory:** Displayed per agent
- **Utility:** Real-time utility values

### 12.2 Interactive Controls

- **Space:** Pause/resume
- **R:** Reset simulation
- **S:** Single step (when paused)
- **+/-:** Adjust simulation speed
- **Q/ESC:** Quit

### 12.3 Usage

```bash
python main.py scenarios/three_agent_barter.yaml 42
```

---

## 13. Scenario Configuration

### 13.1 Example Scenario

```yaml
schema_version: 1
name: three_agent_barter
N: 32
agents: 3

initial_inventories:
  A:
    - 8  # Agent 0
    - 4  # Agent 1
    - 6  # Agent 2
  B:
    - 4  # Agent 0
    - 8  # Agent 1
    - 6  # Agent 2

utilities:
  mix:
    - type: ces
      weight: 1.0
      params:
        rho: -0.5  # Complementarity
        wA: 1.0
        wB: 1.0

params:
  # Trading (uses defaults from schema.py)
  # spread: 0.0                  # Centralized default
  # trade_cooldown_ticks: 5      # Centralized default
  
  # Resources
  resource_growth_rate: 1        # Enable regeneration
  resource_regen_cooldown: 5
  
resource_seed:
  density: 0.15
  amount: 3
```

### 13.2 Parameter Defaults (Centralized in schema.py)

All parameters have sensible defaults. Scenarios only override what differs.

**Trading:**
- `spread: 0.0` ← Critical for CES utilities
- `interaction_radius: 1`
- `ΔA_max: 5`
- `trade_cooldown_ticks: 5`

**Foraging:**
- `vision_radius: 5`
- `move_budget_per_tick: 1`
- `forage_rate: 1`
- `beta: 0.95`

**Regeneration:**
- `resource_growth_rate: 0` (disabled by default)
- `resource_max_amount: 5`
- `resource_regen_cooldown: 5`

**Numerical:**
- `epsilon: 1e-12`

### 13.3 GUI Launcher & Scenario Builder (v1.1+)

**Status:** Production ready, available since v1.1

VMT provides a comprehensive PyQt5-based GUI for running simulations and creating custom scenarios without manual YAML editing.

#### Components

**Main Launcher Window (`vmt_launcher/launcher.py`)**
- Browse scenarios from `scenarios/` folder
- Seed input with validation
- One-click simulation launching
- Auto-refresh when new scenarios created
- Subprocess-based (GUI stays responsive)

**Scenario Builder (`vmt_launcher/scenario_builder.py`)**
- 4-tab interface for organized input:
  - **Tab 1: Basic Settings** - Name, grid, agents, inventories
  - **Tab 2: Simulation Parameters** - Spread, vision, movement, cooldowns
  - **Tab 3: Resources** - Density, growth, regeneration cooldown
  - **Tab 4: Utility Functions** - CES and Linear with built-in documentation
- Dynamic utility rows (add/remove)
- Auto-normalize weights (ensures sum to 1.0)
- Comprehensive validation (ranges, constraints, economic rules)
- YAML generation matching schema
- File save dialog with defaults

**Validator (`vmt_launcher/validator.py`)**
- Type-specific validation
- Range checking
- Inventory list parsing (single value or comma-separated)
- Utility weight summation checks
- CES parameter validation (ρ ≠ 1.0)
- User-friendly error messages

**Built-in Documentation Panel**
- Split-panel layout in Utility Functions tab (60/40)
- Rich HTML documentation with embedded CSS
- Resizable panels
- Comprehensive CES and Linear explanations
- Parameter-by-parameter behavior descriptions
- Common configuration examples
- Color-coded information boxes

#### Usage

**Launch GUI:**
```bash
python launcher.py
```

**Create Custom Scenario:**
1. Click "Create Custom Scenario"
2. Fill in the 4 tabs
3. Use built-in docs for utility function guidance
4. Click "Generate Scenario"
5. Save YAML (default: `scenarios/` folder)
6. New scenario automatically appears in launcher list

**Run Simulation:**
1. Select scenario from list
2. Enter seed (default: 42)
3. Click "Run Simulation"
4. Pygame window opens (launcher stays open)

#### Benefits

**Accessibility:**
- No YAML syntax knowledge required
- Form validation prevents common errors
- In-context parameter explanations
- Educational value (explains economic concepts)

**Workflow:**
- CLI and GUI methods coexist
- Generated YAMLs identical to hand-written ones
- No changes to simulation engine required
- All existing tests pass

**User Experience:**
```bash
# Before: Manual YAML editing
vim scenarios/my_scenario.yaml
python main.py scenarios/my_scenario.yaml 42

# After: GUI-based creation
python launcher.py
# Click, fill forms, run - all explained in-app
```

**See Also:** `PLANS/docs/GUI_LAUNCHER_GUIDE.md` for complete user guide

---

## 14. Key Implementation Insights

### 14.1 The MRS vs. Discrete Trade Gap

**Discovery:** Continuous MRS theory doesn't guarantee discrete integer trades work.

**Example:**
```
MRS overlap: bid=1.0, ask=0.65 → surplus=0.35 (positive!)
Midpoint price: 0.825
Round(0.825 × 1) = 1
Trade 1A for 1B: Seller U=1.37→1.37 (no gain due to rounding)
→ Trade fails despite positive theoretical surplus
```

**Solution:** Price search tries multiple candidates until finding one that works with integer rounding.

### 14.2 Bootstrap Requirement for CES

**Discovery:** CES utilities with very unbalanced inventories produce extreme prices.

**Example:**
```
Agent A: [5, 0] → MRS ≈ infinity (wants B desperately)
Agent B: [0, 5] → MRS ≈ 0 (wants A desperately)
```

**Solution:** Bootstrap inventories to non-zero, somewhat balanced values:
```yaml
initial_inventories:
  A: [8, 4, 6]  # Not [10, 0, 0]
  B: [4, 8, 6]  # Not [0, 10, 0]
```

### 14.3 Cooldowns as Design Pattern

Both resource and trade cooldowns follow the same pattern:
```
action → last_action_tick → wait cooldown_duration → allow again
```

This prevents pathological loops in agent systems:
- Trade cooldown → prevents futile re-targeting
- Resource cooldown → prevents instant re-harvest

**Lesson:** Agent systems need temporal rate-limiting to avoid degeneracies.

### 14.4 Telemetry-Driven Development

**Process:**
1. Observe unexpected behavior in visualization
2. Add detailed logging for that subsystem
3. Analyze logs to understand root cause
4. Implement fix
5. Verify in logs

**Example:** Trade failures were invisible until `trade_attempt_logger` was added, revealing the midpoint pricing problem.

---

## 15. Deferred Features

### 15.1 Utility Functions

**Deferred to future:**
- Leontief (kinked indifference curves)
- Stone-Geary / LES (subsistence levels)

**Reason:** Require discrete ΔU probe logic instead of analytic MRS. CES and Linear sufficient for v1 pedagogical goals.

### 15.2 Resource Spawning

**Option 3 (not implemented):**
- Spawn resources in empty cells randomly
- Parameters: `resource_spawn_rate`, `resource_spawn_amount`
- Would create more dynamic environments

**Current:** Resources only regenerate in initially-seeded cells.

### 15.3 Advanced Pricing

**Not implemented:**
- Nash bargaining solution
- Learning successful price ranges
- Adaptive price search

**Current:** Fixed price candidate generation works well.

---

## 16. Backward Compatibility Notes

### 16.1 Preserved
- All original tests pass
- Existing scenarios work unchanged
- Default parameters maintain old behavior where applicable
- No breaking API changes

### 16.2 Intentional Changes
- **spread: 0.05 → 0.0** (necessary for CES to work)
- **Trade cooldown: disabled → 5 ticks** (prevents loops)
- **Regeneration: N/A → configurable** (new feature, disabled by default)
- **One trade per tick** (was multi-block loop)

---

## 17. Running the System

### 17.1 Command Line

```bash
# Activate environment
source venv/bin/activate

# Run with visualization
python main.py scenarios/three_agent_barter.yaml 42

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_resource_regeneration.py -v
```

### 17.2 Programmatic API

```python
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario

# Load scenario
scenario = load_scenario("scenarios/three_agent_barter.yaml")

# Create simulation
sim = Simulation(scenario, seed=42)

# Run
sim.run(max_ticks=100)

# Access results
for agent in sim.agents:
    print(f"Agent {agent.id}: A={agent.inventory.A}, B={agent.inventory.B}, U={agent.utility.u(...):.2f}")
    
# Read logs
import pandas as pd
trades = pd.read_csv("logs/trades.csv")
print(f"Total trades: {len(trades)}")
```

---

## 18. Future Development Roadmap

### 18.1 Short-term Enhancements
1. Visualize cooldown states (highlight agents in cooldown)
2. Monitor behavior across more random seeds
3. Tune cooldown durations based on user testing
4. Add Option 3: random resource spawning
5. Performance profiling for larger scenarios

### 18.2 Long-term Research
1. Implement Leontief/Stone-Geary utilities
2. Investigate Nash bargaining pricing
3. Add learning/adaptation mechanisms
4. Study convergence rates and equilibrium properties
5. Multi-good extension (A, B, C, ...)
6. Cash/credit extensions

### 18.3 Pedagogical Extensions
1. Edgeworth box visualization overlay
2. Contract curve display
3. Pareto frontier calculations
4. Gini coefficient tracking
5. Interactive scenario builder GUI

---

## 19. Reference Documents

This document consolidates information from:
- `Planning-FINAL.md` (original design)
- `algorithmic_planning.md` (original algorithms)
- `V1_CHECKPOINT_REVIEW.md` (implementation retrospective)
- `Big_Review.md` (comprehensive evaluation)
- Implementation docs in `PLANS/docs/`:
  - `TELEMETRY_IMPLEMENTATION.md`
  - `PRICE_SEARCH_IMPLEMENTATION.md`
  - `ONE_TRADE_PER_TICK.md`
  - `RESOURCE_REGENERATION_IMPLEMENTATION.md`
  - `REGENERATION_COOLDOWN_FIX.md`
  - `TRADE_COOLDOWN_IMPLEMENTATION.md`
  - `CONFIGURATION.md`

---

## 20. Version History

| Version | Date | Notes |
|---------|------|-------|
| v1 | 2025-09 | Initial planning |
| v2 | 2025-09 | Architectural revisions |
| v3 | 2025-10 | Operational specs |
| vFinal | 2025-10-11 | Multi-utility architecture planning |
| **Post-v1.0** | **2025-10-11** | **As-built specification with core enhancements** |
| **Post-v1.1** | **2025-10-12** | **Added SQLite logging system, GUI launcher, log viewer** |

---

## Appendix A: Quick Reference - Key Differences from Original Plan

| Aspect | Original Plan | Actual Implementation | Reason |
|--------|---------------|----------------------|--------|
| **Pricing** | Midpoint only | Price search algorithm | Midpoint failed with CES + rounding |
| **Trade Flow** | Multi-block per tick | One trade per tick | Pedagogical clarity |
| **Regeneration** | Not specified | Full system with cooldown | Sustainable scenarios needed |
| **Trade Cooldown** | Not specified | 5-tick mutual cooldown | Prevent partner lock-in |
| **Telemetry** | Success logs only | All attempts + decisions | Debugging required |
| **Spread Default** | 0.05 | 0.0 | CES compatibility |
| **Foraging Calc** | Full cell amount | min(amount, forage_rate) | Correct incentives |

---

## Appendix B: Critical Production Rules

**For Maintainers and Extenders:**

1. **Never change `spread` default from 0.0** - CES trading depends on this
2. **Always log failures, not just successes** - Debugging depends on this
3. **Test with CES utilities (rho=-0.5)** - Most sensitive to changes
4. **Bootstrap inventories away from zero** - Especially for CES agents
5. **Preserve determinism** - Sort by ID, use explicit seeds
6. **One trade per tick** - Don't reintroduce multi-block loops
7. **Price search before any pricing changes** - Understand why it's needed
8. **Run full test suite** - 45 tests must pass

---

**END OF DOCUMENT**

**Status:** Production Ready  
**Test Status:** 45/45 Passing  
**Last Updated:** October 12, 2025

