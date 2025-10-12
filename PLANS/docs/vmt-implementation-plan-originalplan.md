<!-- d58d48d7-9833-4631-a3e5-0b1d829673f5 5f79da30-7b08-402f-b363-b9e6a4fefaca -->
# VMT v1' Implementation Plan

## Project Setup

Create the complete directory structure following Planning-FINAL.md:

```
vmt-dev/
├── vmt_engine/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── grid.py
│   │   ├── agent.py
│   │   └── state.py
│   ├── econ/
│   │   ├── __init__.py
│   │   └── utility.py
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── perception.py
│   │   ├── movement.py
│   │   ├── matching.py
│   │   ├── foraging.py
│   │   └── quotes.py
│   └── simulation.py
├── vmt_pygame/
│   ├── __init__.py
│   └── renderer.py
├── scenarios/
│   ├── __init__.py
│   ├── schema.py
│   ├── loader.py
│   ├── single_agent_forage.yaml
│   └── three_agent_barter.yaml
├── telemetry/
│   ├── __init__.py
│   ├── logger.py
│   └── snapshots.py
├── tests/
│   ├── test_*.py (existing)
│   └── (new test files per module)
├── requirements.txt
└── README.md
```

---

## Milestone 0: Core Loop & Telemetry

**Goal**: Deterministic tick loop skeleton, RNG seeding, telemetry hooks, basic state management

### M0.1: Project Foundation

**Files to create**:

- `requirements.txt`: pygame, numpy, pyyaml, pytest
- `README.md`: Project description, setup instructions
- `vmt_engine/__init__.py`: Package initialization
- `vmt_engine/core/__init__.py`: Core module exports

### M0.2: Scenario Schema & Loader

**Purpose**: Enable YAML-driven configuration from the start

**Create `scenarios/schema.py`**:

- Define dataclasses/TypedDicts for scenario structure per typing_overview.md §4
- Validate parameter domains (spread ≥ 0, vision_radius ≥ 0, etc.)
- Support distribution parsing: `uniform_int(lo,hi)`, `uniform(lo,hi)`

**Create `scenarios/loader.py`**:

- `load_scenario(path: str) -> ScenarioConfig`
- Parse YAML, validate against schema
- Handle utility mix weights, initial inventory distributions
- Apply defaults for missing params (spread=0.05, epsilon=1e-12, etc.)

**Create `scenarios/single_agent_forage.yaml`**:

```yaml
schema_version: 1
name: single_agent_forage_test
N: 16
agents: 1
initial_inventories:
  A: 0
  B: 0
utilities:
  mix:
  - {type: ces, weight: 1.0, params: {rho: -0.5, wA: 1.0, wB: 1.0}}
params:
  spread: 0.05
  vision_radius: 5
  interaction_radius: 1
  move_budget_per_tick: 1
  ΔA_max: 5
  forage_rate: 1
  epsilon: 1e-12
  beta: 0.95
resource_seed:
  density: 0.1
  amount: 3
```

**Create `scenarios/three_agent_barter.yaml`**:

```yaml
schema_version: 1
name: three_agent_barter_test
N: 8
agents: 3
initial_inventories:
  A: [5, 0, 3]  # explicit list for testing
  B: [0, 5, 3]
utilities:
  mix:
  - {type: ces, weight: 0.67, params: {rho: -0.5, wA: 1.0, wB: 1.0}}
  - {type: linear, weight: 0.33, params: {vA: 1.0, vB: 1.2}}
params:
  spread: 0.05
  vision_radius: 3
  interaction_radius: 1
  move_budget_per_tick: 1
  ΔA_max: 5
  forage_rate: 1
  epsilon: 1e-12
  beta: 0.95
resource_seed:
  density: 0.05
  amount: 1
```

**Test**: `tests/test_scenario_loader.py`

- Valid scenarios load without error
- Invalid params (negative spread, ΔA_max=0) raise validation errors
- Distributions parse correctly

### M0.3: Core State Structures

**Create `vmt_engine/core/state.py`**:

- `Inventory`: dataclass with A:int, B:int fields
- `Quote`: dataclass with ask_A_in_B:float, bid_A_in_B:float
- `Position`: (x:int, y:int) type alias
- State validation helpers

**Create `vmt_engine/core/grid.py`**:

- `Cell`: dataclass with position, resource (type: "A"|"B", amount:int)
- `Grid`: class managing NxN grid
                                - `__init__(self, N:int)`
                                - `get_cell(x, y) -> Cell`
                                - `set_resource(x, y, good_type, amount)`
                                - `manhattan_distance(pos1, pos2) -> int`
                                - `cells_within_radius(pos, radius) -> list[Cell]`
- Initialize from scenario resource_seed (density, amount distribution)

**Create `vmt_engine/core/agent.py`**:

- `Agent`: class with fields per typing_overview.md §3
                                - id, pos, inventory, utility (placeholder), quotes, vision_radius, move_budget_per_tick
                                - `__init__` from scenario config
                                - Utility object assigned later (after econ module)

**Test**: `tests/test_core_state.py`

- Grid correctly returns cells, computes manhattan distance
- Agent initialization validates id uniqueness
- cells_within_radius returns correct count

### M0.4: Simulation Loop Skeleton

**Create `vmt_engine/simulation.py`**:

- `Simulation` class:
                                - `__init__(scenario_config, seed:int)`
                                - `grid: Grid`
                                - `agents: list[Agent]` (sorted by id)
                                - `tick: int = 0`
                                - `rng: np.random.Generator` (seeded for reproducibility)
                                - Initialize grid and agents from scenario
- `run(max_ticks: int)` method with phases:
  ```python
  for tick in range(max_ticks):
      self.perception_phase()
      self.decision_phase()
      self.movement_phase()
      self.trade_phase()  # stub
      self.forage_phase()  # stub
      self.housekeeping_phase()
  ```

- Each phase is a stub method for now

**Test**: `tests/test_simulation_init.py`

- Simulation initializes with correct agent count
- Agents sorted by id
- Grid size matches scenario
- Fixed seed produces identical agent positions across runs

### M0.5: Telemetry Foundation

**Create `telemetry/logger.py`**:

- `TradeLogger`: CSV writer for trades (tick,x,y,buyer_id,seller_id,ΔA,ΔB,price,direction)
- `log_trade(tick, x, y, buyer_id, seller_id, dA, dB, price, direction)`

**Create `telemetry/snapshots.py`**:

- `AgentSnapshotLogger`: CSV writer (tick,id,x,y,A,B,U,partner_id,utility_type)
- `ResourceSnapshotLogger`: CSV writer (tick,cell_id,x,y,resource)
- `log_agent_snapshot(tick, agents)` every K ticks
- `log_resource_snapshot(tick, grid)` every K ticks

**Integrate into `Simulation`**:

- Add telemetry loggers to `__init__`
- Call loggers in `housekeeping_phase()`
- Output to `./logs/` directory

**Test**: `tests/test_telemetry.py`

- Loggers create valid CSV files
- Snapshot frequency K is respected
- File headers match spec

---

## Milestone 1: Foraging

**Goal**: Resource harvesting, movement, perception (no trading yet)

### M1.1: Utility Module Foundation

**Create `vmt_engine/econ/utility.py`**:

**Base interface**:

```python
from abc import ABC, abstractmethod

class Utility(ABC):
    @abstractmethod
    def u(self, A: int, B: int) -> float:
        """Utility function"""
        pass
    
    def mu(self, A: int, B: int) -> tuple[float, float] | None:
        """Marginal utilities (optional)"""
        return None
    
    def mrs_A_in_B(self, A: int, B: int) -> float | None:
        """MRS (optional)"""
        return None
    
    @abstractmethod
    def reservation_bounds_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> tuple[float, float]:
        """Returns (p_min, p_max)"""
        pass
```

**Implement `UCES`**:

```python
class UCES(Utility):
    def __init__(self, rho: float, wA: float, wB: float):
        assert rho != 1.0
        assert wA > 0 and wB > 0
        self.rho = rho
        self.wA = wA
        self.wB = wB
    
    def u(self, A: int, B: int) -> float:
        # CES formula: [wA*A^ρ + wB*B^ρ]^(1/ρ)
        # Handle edge cases (A=0, B=0)
        ...
    
    def mrs_A_in_B(self, A: int, B: int) -> float | None:
        # (wA/wB) * (A/B)^(ρ-1)
        # Use zero-safe shift for ratio calculation only
        ...
    
    def reservation_bounds_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> tuple[float, float]:
        # Apply zero-safe shift (A+eps, B+eps) for MRS calculation
        # Return (mrs, mrs) since analytic
        ...
```

**Implement `ULinear`**:

```python
class ULinear(Utility):
    def __init__(self, vA: float, vB: float):
        assert vA > 0 and vB > 0
        self.vA = vA
        self.vB = vB
    
    def u(self, A: int, B: int) -> float:
        return self.vA * A + self.vB * B
    
    def reservation_bounds_A_in_B(self, A: int, B: int, eps: float = 1e-12) -> tuple[float, float]:
        mrs = self.vA / self.vB
        return (mrs, mrs)
```

**Add utility factory**:

```python
def create_utility(config: dict) -> Utility:
    utype = config['type']
    params = config['params']
    if utype == 'ces':
        return UCES(**params)
    elif utype == 'linear':
        return ULinear(**params)
    # Optional: 'cobb_douglas' -> UCES(rho=0, ...)
    else:
        raise ValueError(f"Unknown utility type: {utype}")
```

**Test**: `tests/test_utility_ces.py`, `tests/test_utility_linear.py`

- CES utility values match known formulas
- Zero-inventory (A=B=0) produces finite reservation bounds
- epsilon variation doesn't affect bounds for positive inventories
- Linear utility has constant MRS

### M1.2: Assign Utilities to Agents

**Update `Agent.__init__` in `core/agent.py`**:

- Accept utility config, instantiate via `create_utility()`
- Store `self.utility: Utility`

**Update `Simulation.__init__`**:

- Sample utility types according to scenario mix weights
- Assign to agents during initialization

**Test**: `tests/test_agent_utility_assignment.py`

- Agents have correct utility types
- Mixed populations respect weight ratios (statistical test)

### M1.3: Perception System

**Create `vmt_engine/systems/perception.py`**:

```python
@dataclass
class PerceptionView:
    neighbors: list[tuple[int, Position]]  # (agent_id, pos)
    neighbor_quotes: dict[int, Quote]      # agent_id -> quotes
    resource_cells: list[Cell]              # visible resource cells

def perceive(agent: Agent, grid: Grid, all_agents: list[Agent]) -> PerceptionView:
    """
    Returns what agent can see within vision_radius.
    """
    # Find agents within manhattan distance <= vision_radius
    # Snapshot their quotes (read-only)
    # Get resource cells within radius
    ...
```

**Implement `Simulation.perception_phase()`**:

- Store perception views in `agent.perception_cache` (temporary dict)

**Test**: `tests/test_perception.py`

- Agent perceives neighbors within radius
- Agent does not perceive beyond radius
- Quotes are snapshots (don't change if quote updates)

### M1.4: Movement System (Foraging Only)

**Create `vmt_engine/systems/movement.py`**:

**Pathfinding helper**:

```python
def next_step_toward(current: Position, target: Position, budget: int) -> Position:
    """
    Return next position moving toward target by up to budget steps.
    Tie-break: prefer reducing |dx| before |dy|; prefer negative direction.
    """
    ...
```

**Foraging movement**:

```python
def choose_forage_target(agent: Agent, perception: PerceptionView, beta: float) -> Position | None:
    """
    Primary: distance-discounted utility seeking
    Fallback: nearest-resource (A before B, then lowest x, y)
    """
    resource_cells = perception.resource_cells
    if not resource_cells:
        return None  # random walk or stay
    
    # Score each cell: ΔU_arrival * β^distance
    # Use agent.utility.u() to compute ΔU
    ...
```

**Implement `Simulation.decision_phase()`**:

- For each agent: choose forage target, store in `agent.target_pos`

**Implement `Simulation.movement_phase()`**:

- For each agent: move toward target by move_budget_per_tick

**Test**: `tests/test_movement_foraging.py`

- Agent moves toward nearest resource
- Distance discounting prefers closer resources
- Tie-breaking is deterministic

### M1.5: Foraging Execution

**Create `vmt_engine/systems/foraging.py`**:

```python
def forage(agent: Agent, grid: Grid, forage_rate: int) -> bool:
    """
    Harvest resources from agent's current cell.
    Returns True if harvested anything.
    """
    cell = grid.get_cell(*agent.pos)
    if cell.resource.amount == 0:
        return False
    
    harvest = min(cell.resource.amount, forage_rate)
    good_type = cell.resource.type
    
    # Update agent inventory
    if good_type == "A":
        agent.inventory.A += harvest
    else:
        agent.inventory.B += harvest
    
    # Update cell resource
    cell.resource.amount -= harvest
    
    return True
```

**Implement `Simulation.forage_phase()`**:

- For each agent: call `forage()`
- Mark agents whose utility changed (for quote refresh in M2)

**Test**: `tests/test_foraging.py`

- Harvest respects forage_rate
- Inventory and cell resource conserved
- Agent at (x,y) harvests from cell (x,y) only

### M1.6: End-to-End M1 Integration Test

**Create `tests/test_m1_integration.py`**:

- Load `single_agent_forage.yaml`
- Run simulation for 50 ticks
- Verify agent moves toward resources and harvests
- Check inventory increases over time
- Verify determinism (same seed → same trajectory)

---

## Milestone 2: Quotes & Partner Targeting

**Goal**: Quote generation, broadcasting, surplus-based partner selection, movement toward partners

### M2.1: Quote Generation System

**Create `vmt_engine/systems/quotes.py`**:

```python
def compute_quotes(agent: Agent, spread: float, epsilon: float) -> Quote:
    """
    Compute ask/bid from reservation bounds.
    """
    A = agent.inventory.A
    B = agent.inventory.B
    p_min, p_max = agent.utility.reservation_bounds_A_in_B(A, B, epsilon)
    
    ask_A_in_B = p_min * (1 + spread)
    bid_A_in_B = p_max * (1 - spread)
    
    return Quote(ask_A_in_B=ask_A_in_B, bid_A_in_B=bid_A_in_B)

def refresh_quotes_if_needed(agent: Agent, spread: float, epsilon: float):
    """
    Recompute quotes if inventory changed.
    """
    # Check if inventory changed since last quote
    # Recompute and update agent.quotes
    ...
```

**Update `Simulation.housekeeping_phase()`**:

- Refresh quotes for agents whose utility changed (post-trade or forage)

**Test**: `tests/test_quotes.py`

- Quotes respect spread (ask > bid for one agent)
- Zero-inventory quotes are finite for CES
- Quote refresh triggers on inventory change

### M2.2: Partner Selection (Surplus-Based)

**Create `vmt_engine/systems/matching.py`**:

```python
def compute_surplus(agent_i: Agent, agent_j: Agent) -> float:
    """
    Returns best_overlap = max(overlap_dir1, overlap_dir2)
    """
    overlap_dir1 = agent_i.quotes.bid_A_in_B - agent_j.quotes.ask_A_in_B  # i buys from j
    overlap_dir2 = agent_j.quotes.bid_A_in_B - agent_i.quotes.ask_A_in_B  # j buys from i
    return max(overlap_dir1, overlap_dir2)

def choose_partner(agent: Agent, perception: PerceptionView) -> int | None:
    """
    Pick partner with highest surplus, tie -> lowest id.
    """
    candidates = []
    for neighbor_id, _ in perception.neighbors:
        # Get neighbor from all_agents by id
        # Compute surplus
        # Track (surplus, neighbor_id)
        ...
    
    if not candidates:
        return None
    
    # Sort by (-surplus, id)
    candidates.sort()
    return candidates[0][1]  # neighbor_id
```

**Update `Simulation.decision_phase()`**:

- For each agent:
                                - Compute partner using `choose_partner()`
                                - If partner exists, set target to partner position
                                - Else, use forage target from M1

**Test**: `tests/test_partner_selection.py`

- Agent with complementary preferences selects correct partner
- Tie-breaking by id works
- No positive surplus -> no partner

### M2.3: Movement Toward Partners

**Update `movement.py`**:

- Prioritize partner target over forage target in decision phase
- Agent moves toward partner position

**Test**: `tests/test_movement_partner.py`

- Agents with positive surplus move toward each other
- Movement respects move_budget_per_tick

### M2.4: End-to-End M2 Integration Test

**Create `tests/test_m2_integration.py`**:

- Load `three_agent_barter.yaml`
- Run simulation for 20 ticks (no trading yet)
- Verify agents broadcast quotes
- Verify agents with surplus move toward each other
- Verify agents without partners forage

---

## Milestone 3: Matching & Trade

**Goal**: Midpoint pricing, compensating multi-lot rounding, ΔU guards, trade execution

### M3.1: Trade Block Search

**Update `vmt_engine/systems/matching.py`**:

```python
def improves(agent: Agent, dA: int, dB: int, eps: float = 1e-12) -> bool:
    """
    Check if trade improves utility strictly.
    """
    A0, B0 = agent.inventory.A, agent.inventory.B
    u0 = agent.utility.u(A0, B0)
    u1 = agent.utility.u(A0 + dA, B0 + dB)
    return u1 > u0 + eps

def find_compensating_block(buyer: Agent, seller: Agent, price: float, 
                           dA_max: int, epsilon: float) -> tuple[int, int] | None:
    """
    Find minimal ΔA ∈ [1..dA_max] s.t. ΔB = round_half_up(price * ΔA)
    and both agents improve.
    """
    for dA in range(1, dA_max + 1):
        dB = int(floor(price * dA + 0.5))  # round-half-up
        
        if dB <= 0:
            continue
        
        # Check feasibility
        if seller.inventory.A < dA or buyer.inventory.B < dB:
            continue
        
        # Check ΔU improvement
        if improves(buyer, +dA, -dB, epsilon) and improves(seller, -dA, +dB, epsilon):
            return (dA, dB)
    
    return None
```

**Test**: `tests/test_compensating_block.py`

- Block search finds feasible trade when surplus exists
- Returns None when no mutually beneficial trade
- Respects inventory constraints

### M3.2: Trade Execution

**Add to `matching.py`**:

```python
def execute_trade(buyer: Agent, seller: Agent, dA: int, dB: int):
    """
    Execute trade block, update inventories.
    """
    # Validate inventories
    assert seller.inventory.A >= dA
    assert buyer.inventory.B >= dB
    
    # Transfer
    buyer.inventory.A += dA
    buyer.inventory.B -= dB
    seller.inventory.A -= dA
    seller.inventory.B += dB

def trade_pair(agent_i: Agent, agent_j: Agent, params: dict, logger: TradeLogger, tick: int) -> bool:
    """
    Attempt trade between pair. Returns True if any trade occurred.
    Multi-block continuation supported.
    """
    traded = False
    
    while True:
        # Compute surplus, pick direction
        overlap_dir1 = agent_i.quotes.bid_A_in_B - agent_j.quotes.ask_A_in_B
        overlap_dir2 = agent_j.quotes.bid_A_in_B - agent_i.quotes.ask_A_in_B
        
        if overlap_dir1 <= 0 and overlap_dir2 <= 0:
            break  # No surplus
        
        # Pick direction with larger surplus
        if overlap_dir1 > overlap_dir2:
            buyer, seller = agent_i, agent_j
            direction = "i_buys_A"
        else:
            buyer, seller = agent_j, agent_i
            direction = "j_buys_A"
        
        # Midpoint price
        price = 0.5 * (seller.quotes.ask_A_in_B + buyer.quotes.bid_A_in_B)
        
        # Find block
        block = find_compensating_block(buyer, seller, price, params['ΔA_max'], params['epsilon'])
        
        if block is None:
            break
        
        dA, dB = block
        
        # Execute
        execute_trade(buyer, seller, dA, dB)
        traded = True
        
        # Log
        logger.log_trade(tick, buyer.pos[0], buyer.pos[1], buyer.id, seller.id, 
                        dA, dB, price, direction)
        
        # Refresh quotes
        refresh_quotes_if_needed(buyer, params['spread'], params['epsilon'])
        refresh_quotes_if_needed(seller, params['spread'], params['epsilon'])
    
    return traded
```

**Test**: `tests/test_trade_execution.py`

- Single block trade updates inventories correctly
- Multi-block continuation works until ΔU exhausted
- Integer conservation maintained
- Quotes refresh after each block

### M3.3: Matching Phase Implementation

**Implement `Simulation.trade_phase()`**:

```python
def trade_phase(self):
    """
    Process all pairs within interaction_radius, ordered by (min_id, max_id).
    """
    # Build list of unordered pairs within interaction_radius
    pairs = []
    for i, agent_i in enumerate(self.agents):
        for agent_j in self.agents[i+1:]:  # avoid double-counting
            dist = self.grid.manhattan_distance(agent_i.pos, agent_j.pos)
            if dist <= self.params['interaction_radius']:
                pairs.append((min(agent_i.id, agent_j.id), max(agent_i.id, agent_j.id)))
    
    # Sort by (min_id, max_id)
    pairs.sort()
    
    # Execute trades
    for id_i, id_j in pairs:
        agent_i = self.agent_by_id[id_i]
        agent_j = self.agent_by_id[id_j]
        trade_pair(agent_i, agent_j, self.params, self.trade_logger, self.tick)
```

**Test**: `tests/test_matching_phase.py`

- Pairs within interaction_radius are matched
- Pair ordering is deterministic (min_id, max_id)
- Co-located agents (distance=0) always match
- Adjacent agents (distance=1) match when interaction_radius=1

### M3.4: End-to-End M3 Integration Test

**Create `tests/test_m3_integration.py`**:

- Load `three_agent_barter.yaml`
- Run simulation for 100 ticks
- Verify trades occur when agents co-locate
- Check trade log format matches spec
- Verify integer conservation (sum A + sum B constant)
- Check determinism (same seed → identical trade sequence)

### M3.5: Mixed Utility Population Tests

**Create `tests/test_mixed_utility_trades.py`**:

- CES agent trading with Linear agent
- Verify both agents improve (ΔU > 0)
- Verify trades occur only with positive surplus
- Test edge case: identical utility parameters (no surplus, no trade)

---

## Milestone 4: Telemetry Refinement & Comprehensive Tests

**Goal**: Complete telemetry, deterministic tests, validation, edge case handling

### M4.1: Complete Telemetry Implementation

**Update `telemetry/snapshots.py`**:

- Implement agent snapshot logging every K ticks
- Include utility_type field
- Optional partner_id tracking

**Update `Simulation.housekeeping_phase()`**:

- Log agent snapshots
- Optional resource snapshots
- Add run metadata (seed, scenario name, params) to header

**Test**: `tests/test_telemetry_complete.py`

- Snapshots written at correct frequency
- All required fields present
- CSVs are valid and parseable

### M4.2: Determinism & Reproducibility Tests

**Create `tests/test_determinism.py`**:

- Run same scenario with same seed twice
- Verify bit-identical logs (trades, snapshots)
- Run with different seeds, verify different outcomes
- Test RNG state management

### M4.3: Conservation & Invariant Tests

**Create `tests/test_invariants.py`**:

- **Integer conservation**: sum(A) + sum(B) across agents + grid is constant (modulo foraging)
- **Non-negative inventories**: all agents have A,B ≥ 0 at all times
- **Quote sanity**: ask_A_in_B ≥ bid_A_in_B for single agent (with spread)
- **Trade feasibility**: all logged trades had sufficient inventories

### M4.4: Edge Case Tests

**Create `tests/test_edge_cases.py`**:

- Agent at (A=0, B=0) can forage and trade
- All agents with identical preferences and inventories (no trade)
- Single resource cell, multiple agents competing
- Grid with no resources (agents only trade)
- Agent with very high vision_radius (sees entire grid)

### M4.5: Performance & Scalability Test

**Create `tests/test_performance.py`**:

- Run 40 agents on 32×32 grid for 500 ticks
- Measure tick rate (should be >10 ticks/sec on modern hardware)
- Profile hotspots (likely in distance calculations, utility evaluations)

---

## Milestone 5: Pygame Visualization (Full v1 MVP)

**Goal**: Basic GUI to observe simulation in real-time

### M5.1: Pygame Setup

**Create `vmt_pygame/renderer.py`**:

```python
class VMTRenderer:
    def __init__(self, simulation: Simulation, cell_size: int = 20):
        pygame.init()
        self.sim = simulation
        self.cell_size = cell_size
        self.width = simulation.grid.N * cell_size
        self.height = simulation.grid.N * cell_size + 100  # HUD space
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("VMT v1")
    
    def render(self):
        self.screen.fill((255, 255, 255))  # white background
        self.draw_grid()
        self.draw_resources()
        self.draw_agents()
        self.draw_hud()
        pygame.display.flip()
    
    def draw_grid(self):
        # Draw grid lines
        ...
    
    def draw_resources(self):
        # Draw resource cells (A=red, B=blue, alpha by amount)
        ...
    
    def draw_agents(self):
        # Draw agents as circles, color by utility type
        # CES=green, Linear=purple
        ...
    
    def draw_hud(self):
        # Display tick, total trades, agent count
        ...
```

**Create main entry point `main.py`**:

```python
import sys
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario
from vmt_pygame.renderer import VMTRenderer

def main():
    scenario_path = sys.argv[1] if len(sys.argv) > 1 else "scenarios/three_agent_barter.yaml"
    scenario = load_scenario(scenario_path)
    
    sim = Simulation(scenario, seed=42)
    renderer = VMTRenderer(sim)
    
    clock = pygame.time.Clock()
    running = True
    paused = False
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
        
        if not paused:
            sim.tick()
        
        renderer.render()
        clock.tick(10)  # 10 FPS
    
    pygame.quit()

if __name__ == "__main__":
    main()
```

**Test**: Manual testing

- Run `python main.py scenarios/single_agent_forage.yaml`
- Verify agent moves and forages visually
- Run `python main.py scenarios/three_agent_barter.yaml`
- Verify agents move toward partners and trade

### M5.2: Enhanced Visualization

**Add to renderer**:

- Vision radius circles (faint)
- Trade indicators (line between agents when trade occurs)
- Agent inventory display (hover or always-on labels)
- Resource amount labels on cells

### M5.3: Interactive Controls

**Add keyboard controls**:

- SPACE: pause/unpause
- R: reset simulation
- S: step one tick (when paused)
- Arrow keys: increase/decrease simulation speed
- T: toggle telemetry overlay

---

## Final Deliverables

1. **Working engine**: All M0-M4 milestones complete
2. **Test suite**: >90% coverage, all tests passing
3. **Pygame GUI**: Functional visualization (M5)
4. **Documentation**: Updated README with usage examples
5. **Scenarios**: Two validated test scenarios
6. **Logs**: Clean telemetry outputs for analysis

---

## Success Criteria

- Load `single_agent_forage.yaml`, agent harvests resources over 100 ticks
- Load `three_agent_barter.yaml`, agents trade when co-located
- All tests pass (`pytest tests/`)
- Deterministic: same seed → identical logs
- Integer conservation maintained
- Pygame visualization shows correct agent/resource states

### To-dos

- [ ] M0: Project Setup - Create directory structure, requirements.txt, README.md, package __init__ files
- [ ] M0: Scenario System - Implement schema.py, loader.py, and create two YAML test scenarios
- [ ] M0: Core State - Implement state.py, grid.py, agent.py with basic structures and validation
- [ ] M0: Simulation Loop Skeleton - Create simulation.py with tick phases as stubs, RNG seeding
- [ ] M0: Telemetry Foundation - Implement logger.py and snapshots.py with CSV writers
- [ ] M1: Utility Module - Implement UCES and ULinear classes with reservation bounds, handle zero-inventory edge case
- [ ] M1: Perception System - Implement perception.py to gather neighbors, quotes, and resources within vision_radius
- [ ] M1: Movement System - Implement movement.py with pathfinding, foraging target selection (distance-discounted)
- [ ] M1: Foraging Execution - Implement foraging.py to harvest resources and update inventories/grid
- [ ] M1: Integration Test - End-to-end test with single_agent_forage.yaml, verify movement and harvesting
- [ ] M2: Quote Generation - Implement quotes.py to compute ask/bid from reservation bounds with spread
- [ ] M2: Partner Selection - Implement surplus computation and partner selection in matching.py
- [ ] M2: Partner Movement - Update decision/movement phases to prioritize partner targets over foraging
- [ ] M2: Integration Test - Test three_agent_barter.yaml with quotes and partner targeting (no trades yet)
- [ ] M3: Trade Block Search - Implement compensating multi-lot algorithm with ΔU guards
- [ ] M3: Trade Execution - Implement trade execution, multi-block continuation, quote refresh
- [ ] M3: Matching Phase - Implement trade_phase() with pair ordering and interaction_radius filtering
- [ ] M3: Integration Test - Full trading test with three_agent_barter.yaml, verify trades and conservation
- [ ] M3: Mixed Utility Tests - Verify CES and Linear agents can trade with each other correctly
- [ ] M4: Complete Telemetry - Implement agent/resource snapshots, run metadata, frequency control
- [ ] M4: Determinism Tests - Verify identical logs for same seed, different logs for different seeds
- [ ] M4: Conservation & Invariant Tests - Test integer conservation, non-negative inventories, quote sanity
- [ ] M4: Edge Case Tests - Test zero inventories, identical agents, no resources, single resource scenarios
- [ ] M4: Performance Test - Run large scenario (40 agents, 500 ticks), measure tick rate
- [ ] M5: Pygame Setup - Create renderer.py with basic grid, resource, and agent rendering
- [ ] M5: Enhanced Visualization - Add vision circles, trade indicators, inventory labels
- [ ] M5: Interactive Controls - Add pause/unpause, reset, step, speed controls, telemetry overlay