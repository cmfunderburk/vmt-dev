# Energy Budget Implementation Plan
**Date:** October 19, 2025  
**Author:** Opus  
**Based on:** Energy budget review documents (son45, gpt5h, gem)

---

## Executive Summary

This document provides a rigorous, step-by-step implementation plan for adding an energy budget system to VMT. The feature introduces mandatory rest cycles through energy depletion and home-based regeneration, creating temporal dynamics and spatial anchoring that enrich the economic simulation.

**Implementation Complexity:** MODERATE (5-7 days)  
**Risk Level:** LOW (feature can be disabled by default)  
**Value:** HIGH (pedagogical, research, and behavioral realism)

---

## Critical Design Decisions

Based on synthesis of the three review documents and codebase analysis, these decisions are recommended:

### Core Decisions ✅

1. **Energy as explicit state variable** (not emergent from optimization)
2. **Mandatory rest when depleted** (not voluntary leisure choice)
3. **Permanent homes once claimed** (no relocation in v1)
4. **Exclusive home occupancy** (one agent per home square)
5. **Feature disabled by default** (backward compatibility)
6. **Energy costs uniform per tick** (not action-dependent in v1)

### Parameter Defaults

```python
energy_max: int = 24                    # Maximum energy capacity
energy_current: int = 24                # Starting energy (full)
energy_cost_per_tick: int = 1           # Cost for being active
energy_regen_rate: int = 3              # Energy restored per tick while resting
home_location: Optional[Position] = None # Agent's home coordinates
enable_energy_system: bool = False       # Feature flag
```

With these defaults: 24 ticks active → 8 ticks rest → 75% duty cycle

---

## Implementation Steps

### Phase 1: Core Data Model (Day 1)

#### Step 1.1: Update Agent State
**File:** `src/vmt_engine/core/agent.py`

Add to `Agent` dataclass:
```python
@dataclass
class Agent:
    # ... existing fields ...
    
    # Energy system fields
    energy_current: int = field(default=24, repr=False)
    energy_max: int = field(default=24, repr=False)
    energy_regen_rate: int = field(default=3, repr=False)
    home_location: Optional[Position] = field(default=None, repr=False)
    agent_state: Literal["ACTIVE", "RETURNING_HOME", "RESTING", "SEEKING_HOME"] = field(default="ACTIVE", repr=False)
    
    def __post_init__(self):
        # ... existing validation ...
        if self.energy_max <= 0:
            raise ValueError(f"energy_max must be positive, got {self.energy_max}")
        if self.energy_current < 0 or self.energy_current > self.energy_max:
            raise ValueError(f"energy_current must be in [0, energy_max], got {self.energy_current}")
```

#### Step 1.2: Update Scenario Schema
**File:** `src/scenarios/schema.py`

Add to `ScenarioParams`:
```python
@dataclass
class ScenarioParams:
    # ... existing fields ...
    
    # Energy system parameters
    enable_energy_system: bool = False
    energy_max: int = 24
    energy_cost_per_tick: int = 1
    energy_regen_rate: int = 3
    
    # Optional: per-agent overrides
    agent_homes: Optional[list[Optional[tuple[int, int]]]] = None
```

Update validation in `ScenarioConfig.validate()`:
```python
# Energy system validation
if self.params.energy_max <= 0:
    raise ValueError(f"energy_max must be positive, got {self.params.energy_max}")
if self.params.energy_cost_per_tick < 0:
    raise ValueError(f"energy_cost_per_tick must be non-negative")
if self.params.energy_regen_rate <= 0:
    raise ValueError(f"energy_regen_rate must be positive")
```

#### Step 1.3: Update Simulation Initialization
**File:** `src/vmt_engine/simulation.py`

In `_initialize_agents()`:
```python
# After creating agent
if self.params['enable_energy_system']:
    agent.energy_max = self.params['energy_max']
    agent.energy_current = self.params['energy_max']  # Start fully rested
    agent.energy_regen_rate = self.params['energy_regen_rate']
    
    # Optional: Pre-assigned homes from scenario
    if 'agent_homes' in self.params and self.params['agent_homes']:
        if i < len(self.params['agent_homes']) and self.params['agent_homes'][i]:
            agent.home_location = tuple(self.params['agent_homes'][i])
```

---

### Phase 2: Energy Check System (Day 1-2)

#### Step 2.1: Create Energy System
**File:** `src/vmt_engine/systems/energy.py` (NEW)

```python
"""
Energy management system - Phase 0 (before Perception).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..simulation import Simulation
    from ..core import Agent

class EnergySystem:
    """Phase 0: Check and update agent energy states."""
    
    def execute(self, sim: "Simulation") -> None:
        if not sim.params.get('enable_energy_system', False):
            return
        
        energy_cost = sim.params.get('energy_cost_per_tick', 1)
        
        # Process agents in deterministic order
        for agent in sim.agents:
            self._update_energy_state(agent, energy_cost, sim.tick)
    
    def _update_energy_state(self, agent: "Agent", energy_cost: int, tick: int) -> None:
        """Update agent's energy state based on current energy level."""
        
        # If resting and fully recovered, return to active
        if agent.agent_state == "RESTING" and agent.energy_current >= agent.energy_max:
            agent.agent_state = "ACTIVE"
            return
        
        # If already returning/seeking home, keep that state
        if agent.agent_state in ["RETURNING_HOME", "SEEKING_HOME"]:
            return
        
        # Check if energy depleted (for ACTIVE agents)
        if agent.agent_state == "ACTIVE" and agent.energy_current <= 0:
            if agent.home_location is not None:
                agent.agent_state = "RETURNING_HOME"
            else:
                agent.agent_state = "SEEKING_HOME"
```

#### Step 2.2: Integrate Energy System
**File:** `src/vmt_engine/simulation.py`

```python
from .systems.energy import EnergySystem

# In __init__, update systems list (Energy MUST be first):
self.systems = [
    EnergySystem(),         # NEW: Phase 0
    PerceptionSystem(),     # Phase 1
    DecisionSystem(),       # Phase 2
    MovementSystem(),       # Phase 3
    TradeSystem(),         # Phase 4
    ForageSystem(),        # Phase 5
    ResourceRegenerationSystem(),  # Phase 6
    HousekeepingSystem(),  # Phase 7
]
```

---

### Phase 3: Modified Decision System (Day 2)

#### Step 3.1: Update Decision Logic
**File:** `src/vmt_engine/systems/decision.py`

```python
def execute(self, sim: "Simulation") -> None:
    for agent in sim.agents:
        # Energy system overrides
        if sim.params.get('enable_energy_system', False):
            if agent.agent_state == "RESTING":
                # Resting agents make no decisions
                agent.target_pos = None
                agent.target_agent_id = None
                continue
            
            elif agent.agent_state == "RETURNING_HOME":
                # Set home as target
                agent.target_pos = agent.home_location
                agent.target_agent_id = None
                continue
            
            elif agent.agent_state == "SEEKING_HOME":
                # Find nearest unoccupied square
                home = self._find_home_location(agent, sim)
                if home == agent.pos:
                    # Claim current position as home
                    agent.home_location = home
                    agent.agent_state = "RESTING"
                    agent.target_pos = None
                else:
                    # Move toward potential home
                    agent.target_pos = home
                agent.target_agent_id = None
                continue
        
        # ... existing decision logic for ACTIVE agents ...

def _find_home_location(self, agent: "Agent", sim: "Simulation") -> Position:
    """Find nearest unoccupied square for home, deterministically."""
    
    # Check if current position is unoccupied (by other homes)
    if self._is_unoccupied_for_home(agent.pos, sim):
        return agent.pos
    
    # BFS outward in Manhattan distance rings
    visited = set()
    visited.add(agent.pos)
    
    for distance in range(1, sim.grid.N * 2):
        # Get all positions at this distance
        candidates = []
        for x in range(sim.grid.N):
            for y in range(sim.grid.N):
                pos = (x, y)
                if pos in visited:
                    continue
                if sim.grid.manhattan_distance(agent.pos, pos) == distance:
                    candidates.append(pos)
        
        # Sort for determinism: lowest (x, y)
        candidates.sort()
        
        # Check each candidate
        for pos in candidates:
            visited.add(pos)
            if self._is_unoccupied_for_home(pos, sim):
                return pos
    
    # Fallback: claim current position even if occupied
    return agent.pos

def _is_unoccupied_for_home(self, pos: Position, sim: "Simulation") -> bool:
    """Check if position is available for claiming as home."""
    for other_agent in sim.agents:
        if other_agent.home_location == pos:
            return False
    return True
```

---

### Phase 4: Conditional System Behavior (Day 2-3)

#### Step 4.1: Update Movement System
**File:** `src/vmt_engine/systems/movement.py`

No changes needed! The existing movement system already:
- Moves agents toward `target_pos`
- Handles diagonal deadlock
- Updates spatial index

The energy states set appropriate targets in Decision phase.

#### Step 4.2: Update Trade System
**File:** `src/vmt_engine/systems/trading.py`

```python
def execute(self, sim: "Simulation") -> None:
    # Get eligible pairs (both must be ACTIVE if energy enabled)
    if sim.params.get('enable_energy_system', False):
        eligible_agents = {
            agent.id for agent in sim.agents 
            if agent.agent_state == "ACTIVE"
        }
    else:
        eligible_agents = {agent.id for agent in sim.agents}
    
    # Original spatial pair finding
    pairs = sim.spatial_index.query_pairs_within_radius(
        sim.params["interaction_radius"]
    )
    
    # Filter pairs to only eligible agents
    eligible_pairs = [
        (id_i, id_j) for id_i, id_j in pairs
        if id_i in eligible_agents and id_j in eligible_agents
    ]
    
    # Sort and execute trades
    eligible_pairs.sort()
    for id_i, id_j in eligible_pairs:
        # ... existing trade logic ...
```

#### Step 4.3: Update Foraging System
**File:** `src/vmt_engine/systems/foraging.py`

```python
def execute(self, sim: "Simulation") -> None:
    for agent in sim.agents:
        # Skip non-active agents if energy enabled
        if sim.params.get('enable_energy_system', False):
            if agent.agent_state != "ACTIVE":
                continue
        
        forage(agent, sim.grid, sim.params["forage_rate"], sim.tick)
```

---

### Phase 5: Energy Bookkeeping in Housekeeping (Day 3)

#### Step 5.1: Update Housekeeping System
**File:** `src/vmt_engine/systems/housekeeping.py`

```python
def execute(self, sim: "Simulation") -> None:
    # Refresh quotes for agents whose inventory changed
    for agent in sim.agents:
        refresh_quotes_if_needed(
            agent, sim.params["spread"], sim.params["epsilon"]
        )
    
    # NEW: Energy bookkeeping (before telemetry for proper logging)
    if sim.params.get('enable_energy_system', False):
        self._update_energy_levels(sim)
    
    # Log telemetry
    sim.telemetry.log_agent_snapshots(sim.tick, sim.agents)
    sim.telemetry.log_resource_snapshots(sim.tick, sim.grid)

def _update_energy_levels(self, sim: "Simulation") -> None:
    """Update energy levels based on agent states."""
    energy_cost = sim.params.get('energy_cost_per_tick', 1)
    
    for agent in sim.agents:
        if agent.agent_state == "RESTING":
            # Check if at home (should be, but verify)
            if agent.pos == agent.home_location:
                # Regenerate energy
                agent.energy_current = min(
                    agent.energy_max,
                    agent.energy_current + agent.energy_regen_rate
                )
                
                # Check if fully rested
                if agent.energy_current >= agent.energy_max:
                    agent.agent_state = "ACTIVE"
            else:
                # Not at home yet, transition to returning
                agent.agent_state = "RETURNING_HOME"
        
        elif agent.agent_state == "ACTIVE":
            # Deduct energy cost
            agent.energy_current = max(0, agent.energy_current - energy_cost)
            
            # State change handled by EnergySystem next tick
        
        elif agent.agent_state == "RETURNING_HOME":
            # Check if arrived home
            if agent.pos == agent.home_location:
                agent.agent_state = "RESTING"
            else:
                # Still traveling, deduct energy
                agent.energy_current = max(0, agent.energy_current - energy_cost)
        
        elif agent.agent_state == "SEEKING_HOME":
            # Still searching, deduct energy
            agent.energy_current = max(0, agent.energy_current - energy_cost)
            
            # Check if found home (set in Decision phase)
            if agent.home_location is not None and agent.pos == agent.home_location:
                agent.agent_state = "RESTING"
```

---

### Phase 6: Telemetry Updates (Day 3-4)

#### Step 6.1: Update Database Schema
**File:** `src/telemetry/database.py`

Add columns to `agent_snapshots` table:
```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_snapshots (
        -- ... existing columns ...
        
        -- Energy system columns
        energy_current INTEGER,
        energy_max INTEGER,
        agent_state TEXT,
        home_x INTEGER,
        home_y INTEGER,
        
        FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
    )
""")
```

#### Step 6.2: Update Telemetry Logger
**File:** `src/telemetry/db_loggers.py`

In `log_agent_snapshots()`:
```python
# Add energy fields to snapshot data
if hasattr(agent, 'energy_current'):
    # Energy system enabled
    snapshot_data.extend([
        agent.energy_current,
        agent.energy_max,
        agent.agent_state,
        agent.home_location[0] if agent.home_location else None,
        agent.home_location[1] if agent.home_location else None,
    ])
else:
    # Energy system disabled
    snapshot_data.extend([None, None, None, None, None])
```

---

### Phase 7: Visualization Updates (Day 4)

#### Step 7.1: Update Pygame Renderer
**File:** `src/vmt_pygame/renderer.py`

```python
def _draw_agents(self):
    """Draw agents with energy state indicators."""
    for agent in self.sim.agents:
        x, y = self._world_to_screen(agent.pos)
        
        # Determine agent color based on state
        if hasattr(agent, 'agent_state'):
            if agent.agent_state == "RESTING":
                color = (100, 100, 200)  # Blue (sleeping)
            elif agent.agent_state == "RETURNING_HOME":
                color = (200, 200, 100)  # Yellow (tired)
            elif agent.agent_state == "SEEKING_HOME":
                color = (200, 100, 100)  # Red (desperate)
            else:  # ACTIVE
                color = (100, 200, 100)  # Green (active)
        else:
            color = (100, 200, 100)  # Default green
        
        # Draw agent circle
        pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 3)
        
        # Draw home marker if exists
        if hasattr(agent, 'home_location') and agent.home_location:
            hx, hy = self._world_to_screen(agent.home_location)
            pygame.draw.rect(
                self.screen, color,
                (hx - 2, hy - 2, 5, 5),
                1  # Border only
            )
        
        # Optional: Energy bar
        if hasattr(agent, 'energy_current'):
            self._draw_energy_bar(agent, x, y)

def _draw_energy_bar(self, agent, x, y):
    """Draw small energy bar above agent."""
    bar_width = self.cell_size - 4
    bar_height = 3
    bar_x = x - bar_width // 2
    bar_y = y - self.cell_size // 2 - 5
    
    # Background
    pygame.draw.rect(
        self.screen, (50, 50, 50),
        (bar_x, bar_y, bar_width, bar_height)
    )
    
    # Energy fill
    if agent.energy_max > 0:
        fill_width = int(bar_width * agent.energy_current / agent.energy_max)
        pygame.draw.rect(
            self.screen, (255, 255, 0),  # Yellow
            (bar_x, bar_y, fill_width, bar_height)
        )
```

---

### Phase 8: Testing (Day 5)

#### Step 8.1: Unit Tests
**File:** `tests/test_energy_system.py` (NEW)

```python
"""Tests for energy budget system."""

import pytest
from vmt_engine.core import Agent, Inventory
from vmt_engine.core.grid import Grid
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario


def test_energy_depletion():
    """Test that active agents deplete energy."""
    agent = Agent(
        id=1, pos=(0, 0), inventory=Inventory(A=5, B=5),
        energy_max=10, energy_current=10, agent_state="ACTIVE"
    )
    
    # Simulate energy depletion
    for tick in range(10):
        agent.energy_current = max(0, agent.energy_current - 1)
    
    assert agent.energy_current == 0
    
def test_energy_regeneration():
    """Test that resting agents regenerate energy."""
    agent = Agent(
        id=1, pos=(5, 5), inventory=Inventory(A=5, B=5),
        energy_max=10, energy_current=0,
        energy_regen_rate=3,
        home_location=(5, 5),
        agent_state="RESTING"
    )
    
    # Simulate resting
    for tick in range(4):
        agent.energy_current = min(
            agent.energy_max,
            agent.energy_current + agent.energy_regen_rate
        )
    
    assert agent.energy_current == 10  # 3*3 = 9, then capped at 10
    
def test_home_seeking_deterministic():
    """Test that home seeking is deterministic."""
    # Create simple scenario
    # ... test that same seed produces same home locations
    
def test_state_transitions():
    """Test correct state transitions."""
    # ACTIVE -> RETURNING_HOME (when energy = 0 and has home)
    # ACTIVE -> SEEKING_HOME (when energy = 0 and no home)
    # RETURNING_HOME -> RESTING (when arrives at home)
    # SEEKING_HOME -> RESTING (when claims home)
    # RESTING -> ACTIVE (when fully rested)
    
def test_energy_disabled_by_default():
    """Test that energy system doesn't affect existing scenarios."""
    scenario = load_scenario("scenarios/three_agent_barter.yaml")
    sim = Simulation(scenario, seed=42)
    
    # Agents should not have energy fields
    agent = sim.agents[0]
    assert agent.agent_state == "ACTIVE"  # Default
    
    # Run simulation - should work normally
    sim.run(max_ticks=10)
    
def test_duty_cycle():
    """Test expected duty cycle with default parameters."""
    # With energy_max=24, energy_regen_rate=3
    # Expect 24 active ticks, 8 rest ticks
    # Duty cycle = 24/32 = 75%
```

#### Step 8.2: Integration Tests
**File:** `tests/test_energy_integration.py` (NEW)

```python
def test_energy_full_cycle():
    """Test complete energy cycle from active to rest to active."""
    
def test_energy_trade_interaction():
    """Test that resting agents cannot trade."""
    
def test_energy_forage_interaction():
    """Test that resting agents cannot forage."""
    
def test_multiple_agents_home_conflicts():
    """Test that multiple agents handle home conflicts deterministically."""
```

---

### Phase 9: Scenario Creation (Day 5-6)

#### Step 9.1: Create Test Scenario
**File:** `scenarios/energy_test.yaml` (NEW)

```yaml
schema_version: 1
name: energy_budget_test
N: 16
agents: 4

initial_inventories:
  A: [5, 5, 5, 5]
  B: [5, 5, 5, 5]

utilities:
  mix:
    - type: ces
      weight: 1.0
      params:
        rho: -0.5
        wA: 1.0
        wB: 1.0

params:
  # Energy system
  enable_energy_system: true
  energy_max: 20
  energy_cost_per_tick: 1
  energy_regen_rate: 4
  
  # Optional: pre-assign homes
  # agent_homes: [[0, 0], [15, 0], [0, 15], [15, 15]]
  
  # Standard params
  spread: 0.0
  vision_radius: 5
  interaction_radius: 1
  move_budget_per_tick: 1
  dA_max: 5
  forage_rate: 1

resource_seed:
  density: 0.1
  amount: 3
```

---

### Phase 10: Documentation (Day 6)

#### Step 10.1: Update README
Add to features section:
```markdown
### Energy Budget System (v1.2)
- **⚡ Energy Management** - Agents have limited energy requiring periodic rest
- **🏠 Home Bases** - Agents claim and return to home locations for rest
- **😴 Rest Cycles** - Creates natural activity rhythms and temporal dynamics
- **🎯 Spatial Anchoring** - Home locations create neighborhoods and territories
```

#### Step 10.2: Create Energy System Guide
**File:** `docs/energy_budget_guide.md` (NEW)

Document:
- Conceptual overview
- Parameter tuning guide
- Pedagogical applications
- Research possibilities

---

## Critical Gaps Requiring Clarification

### 1. Home Assignment Strategy ❓

**Question:** Should agents start with pre-assigned homes or discover them?

**Options:**
1. **Random assignment**: Scatter homes at initialization
2. **Emergent**: Let agents claim homes when first tired
3. **Hybrid**: Some pre-assigned, some emergent

**Recommendation:** Start with emergent (Option 2) as default, allow YAML override for pre-assignment.

### 2. Energy Cost Variability ❓

**Question:** Should different actions cost different energy?

**Current proposal:** Uniform cost (1 per tick)

**Alternative:** 
- Movement: 1 energy
- Trading: 0.5 energy
- Foraging: 1.5 energy
- Standing still: 0.5 energy

**Recommendation:** Keep uniform for v1, add variability in v2 if needed.

### 3. Home Quality Differentiation ❓

**Question:** Should some home locations be "better" than others?

**Options:**
1. All homes equal
2. Homes near resources regenerate faster
3. Homes in center have bonus

**Recommendation:** Keep equal for v1 simplicity.

### 4. Visualization Priority ❓

**Question:** How much visual emphasis on energy states?

**Options:**
1. **Minimal**: Just color coding
2. **Moderate**: Color + energy bars
3. **Full**: Color + bars + home markers + paths

**Recommendation:** Moderate (Option 2) by default with toggle for full.

### 5. Performance Impact Tolerance ❓

**Question:** Acceptable performance degradation?

The energy system will add:
- State checks per agent per tick
- Home pathfinding for depleted agents
- Additional telemetry data

**Estimated impact:** 5-10% slowdown

**Recommendation:** Optimize hot paths, profile before/after.

---

## Risk Mitigation

### Technical Risks

1. **Determinism bugs**: Mitigate with extensive seed-based testing
2. **Performance degradation**: Profile and optimize spatial queries
3. **Edge cases** (no viable homes): Fallback to current position

### Design Risks

1. **Parameter sensitivity**: Provide well-tested defaults
2. **Uninteresting dynamics**: Tune for 75% duty cycle
3. **Complexity overwhelm**: Keep disabled by default

---

## Success Criteria

The implementation will be considered successful when:

1. ✅ All existing tests pass with energy disabled
2. ✅ Energy system tests pass (15+ new tests)
3. ✅ Determinism preserved (same seed → same results)
4. ✅ Performance impact < 10%
5. ✅ Visual indicators clear and informative
6. ✅ Documentation complete
7. ✅ Example scenario demonstrates interesting dynamics

---

## Timeline Summary

**Total: 5-6 Days**

- **Day 1**: Core data model + Energy system
- **Day 2**: Decision logic + Home finding
- **Day 3**: System integration + Housekeeping
- **Day 4**: Visualization + Telemetry
- **Day 5**: Testing suite
- **Day 6**: Documentation + Polish

---

## Conclusion

The energy budget system is a well-conceived feature that naturally extends VMT's capabilities. The implementation plan provided here:

1. Preserves all existing functionality (backward compatible)
2. Maintains determinism and economic soundness
3. Integrates cleanly with the 7-phase architecture
4. Provides rich pedagogical and research value

The feature should be implemented with:
- Energy disabled by default
- Conservative parameter defaults (24/3 for 75% duty cycle)
- Emergent home discovery (not pre-assigned)
- Uniform energy costs (not action-dependent)
- Moderate visualization (colors + energy bars)

With careful implementation following this plan, the energy budget system will enhance VMT without compromising its core strengths.

**Recommended Action:** Proceed with implementation following this plan, starting with Phase 1 (Core Data Model).
