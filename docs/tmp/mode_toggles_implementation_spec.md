# Phase A→B Mode Toggles: Detailed Implementation Specification

## Executive Summary

This document provides a rigorous specification for implementing alternating "forage-only" and "trade-only" windows in the VMT simulation engine. This creates emergent budget constraints where agents must balance time between resource acquisition and trading activities.

## 1. Schema Layer Modifications

### 1.1 New Data Structures

Add to `src/scenarios/schema.py`:

```python
from enum import Enum

class ModeType(str, Enum):
    """Types of mode scheduling patterns."""
    GLOBAL_CYCLE = "global_cycle"  # All agents follow same schedule
    AGENT_SPECIFIC = "agent_specific"  # Each agent has own schedule (future)
    SPATIAL_ZONES = "spatial_zones"  # Different grid regions have different modes (future)

@dataclass
class ModeSchedule:
    """Configuration for alternating phase modes."""
    type: Literal["global_cycle", "agent_specific", "spatial_zones"]
    forage_ticks: int  # Number of ticks in forage-only mode
    trade_ticks: int   # Number of ticks in trade-only mode
    start_mode: Literal["forage", "trade"] = "forage"  # Which mode starts first
    
    def validate(self) -> None:
        """Validate mode schedule parameters."""
        if self.forage_ticks <= 0:
            raise ValueError(f"forage_ticks must be positive, got {self.forage_ticks}")
        if self.trade_ticks <= 0:
            raise ValueError(f"trade_ticks must be positive, got {self.trade_ticks}")
        if self.type != "global_cycle":
            raise NotImplementedError(f"Mode type {self.type} not yet implemented")
    
    def get_mode_at_tick(self, tick: int) -> Literal["forage", "trade", "both"]:
        """
        Determine the mode for a given tick.
        
        Returns:
            "forage" - only foraging allowed
            "trade" - only trading allowed
            "both" - both allowed (when no schedule active)
        """
        if self.type == "global_cycle":
            cycle_length = self.forage_ticks + self.trade_ticks
            position_in_cycle = tick % cycle_length
            
            if self.start_mode == "forage":
                return "forage" if position_in_cycle < self.forage_ticks else "trade"
            else:
                return "trade" if position_in_cycle < self.trade_ticks else "forage"
        
        # Future: implement agent_specific and spatial_zones
        return "both"
```

### 1.2 ScenarioConfig Extension

Modify `ScenarioConfig` class:

```python
@dataclass
class ScenarioConfig:
    """Complete scenario configuration."""
    # ... existing fields ...
    mode_schedule: Optional[ModeSchedule] = None  # New field
    
    def validate(self) -> None:
        """Validate scenario parameters."""
        # ... existing validation ...
        
        # Validate mode schedule if present
        if self.mode_schedule:
            self.mode_schedule.validate()
```

### 1.3 Scenario Loader Updates

Modify `src/scenarios/loader.py` to parse mode schedules:

```python
# In load_scenario function, after parsing resource_seed:
# Parse mode schedule (optional)
mode_schedule = None
if 'mode_schedule' in data:
    mode_data = data['mode_schedule']
    mode_schedule = ModeSchedule(
        type=mode_data['type'],
        forage_ticks=mode_data['forage_ticks'],
        trade_ticks=mode_data['trade_ticks'],
        start_mode=mode_data.get('start_mode', 'forage')
    )

# Add to ScenarioConfig constructor:
scenario = ScenarioConfig(
    # ... existing fields ...
    mode_schedule=mode_schedule
)
```

## 2. Simulation Engine Modifications

### 2.1 Simulation Class State

Add to `Simulation.__init__`:

```python
# Mode tracking
self.current_mode: Literal["forage", "trade", "both"] = "both"
self._previous_mode: Optional[str] = None
self._mode_change_tick: Optional[int] = None
```

### 2.2 Step Method Redesign

Replace the current `step()` method:

```python
def step(self):
    """Execute one simulation tick with mode-aware phase execution."""
    # Determine current mode
    if self.config.mode_schedule:
        new_mode = self.config.mode_schedule.get_mode_at_tick(self.tick)
        
        # Detect and log mode changes
        if new_mode != self.current_mode:
            self._handle_mode_transition(self.current_mode, new_mode)
            self.current_mode = new_mode
            self._mode_change_tick = self.tick
    else:
        self.current_mode = "both"
    
    # Execute systems conditionally based on mode
    for system in self.systems:
        if self._should_execute_system(system, self.current_mode):
            system.execute(self)
    
    self.tick += 1

def _should_execute_system(self, system: Any, mode: str) -> bool:
    """Determine if a system should execute in the current mode."""
    # Always execute these core systems
    always_execute = (PerceptionSystem, DecisionSystem, MovementSystem, 
                     ResourceRegenerationSystem, HousekeepingSystem)
    
    if isinstance(system, always_execute):
        return True
    
    # Mode-specific systems
    if isinstance(system, TradeSystem):
        return mode in ["trade", "both"]
    
    if isinstance(system, ForageSystem):
        return mode in ["forage", "both"]
    
    return True  # Default to executing unknown systems

def _handle_mode_transition(self, old_mode: str, new_mode: str):
    """Handle bookkeeping when modes change."""
    # Log the transition
    if self.telemetry:
        self.telemetry.log_mode_change(self.tick, old_mode, new_mode)
    
    # Clear any mode-specific state
    # (Currently none, but placeholder for future extensions)
    pass
```

## 3. System-Level Adjustments

### 3.1 DecisionSystem Modifications

The DecisionSystem needs to be mode-aware when computing targets:

```python
class DecisionSystem:
    """Phase 2: Agents decide on partners and movement targets."""
    
    def execute(self, sim: "Simulation") -> None:
        for agent in sim.agents:
            view = agent.perception_view
            
            # Mode-aware decision making
            if sim.current_mode == "forage":
                # Only consider resource targets
                target = self._choose_forage_target(agent, view)
            elif sim.current_mode == "trade":
                # Only consider trade partners
                target = self._choose_trade_target(agent, view, sim)
            else:  # mode == "both"
                # Current behavior - consider both
                target = self._choose_best_target(agent, view, sim)
            
            agent.decision = target
            
            # Log decision with mode context
            if sim.telemetry:
                sim.telemetry.log_decision(
                    sim.tick, agent, target, 
                    mode=sim.current_mode  # New parameter
                )
```

### 3.2 PerceptionSystem Considerations

Keep perception unchanged - agents should see everything regardless of mode. This allows for strategic planning.

## 4. Telemetry Extensions

### 4.1 Database Schema Additions

Add to `src/telemetry/database.py`:

```sql
-- New table for mode transitions
CREATE TABLE IF NOT EXISTS mode_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    tick INTEGER NOT NULL,
    old_mode TEXT NOT NULL,
    new_mode TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_mode_changes_run_tick 
ON mode_changes(run_id, tick);

-- Extend decisions table
ALTER TABLE decisions ADD COLUMN mode TEXT;
```

### 4.2 TelemetryManager Methods

Add to `src/telemetry/db_loggers.py`:

```python
def log_mode_change(self, tick: int, old_mode: str, new_mode: str):
    """Log a mode transition."""
    if not self.config.use_database or self.db is None:
        return
    
    self.db.execute("""
        INSERT INTO mode_changes (run_id, tick, old_mode, new_mode)
        VALUES (?, ?, ?, ?)
    """, (self.run_id, tick, old_mode, new_mode))
    self.db.commit()
```

## 5. Critical Design Decisions & Recommendations

### 5.1 Mode Transition Handling

**Question**: What happens to agents mid-movement when mode switches?

**Recommendation**: Allow movements to complete.
- **Rationale**: Movement represents physical position changes that shouldn't be interrupted. An agent walking toward a resource when trade mode begins should still complete their step.
- **Implementation**: MovementSystem always executes regardless of mode.

### 5.2 Quote Persistence

**Question**: Should quotes be recomputed at mode boundaries?

**Recommendation**: Keep quotes stable across mode changes.
- **Rationale**: Quotes reflect underlying preferences which don't change just because activities are restricted. This maintains consistency and reduces computational overhead.
- **Implementation**: No special handling needed; existing quote refresh logic in HousekeepingSystem remains unchanged.

### 5.3 Trade Cooldown Handling

**Question**: Do trade cooldowns persist across mode changes?

**Recommendation**: Cooldowns continue counting down even in forage mode.
- **Rationale**: 
  1. Simplifies implementation (no need to pause/resume cooldown timers)
  2. Creates interesting strategic considerations (failed trades have lasting consequences)
  3. Matches real-world intuition (relationship "cooldowns" don't pause when you're doing other activities)
- **Implementation**: `agent.trade_cooldowns` dict continues decrementing in HousekeepingSystem regardless of mode.

### 5.4 Perception During Restricted Modes

**Question**: What information should agents perceive in each mode?

**Recommendation**: Full perception in all modes.
- **Rationale**:
  1. Allows strategic planning (agents can plan future trades while foraging)
  2. Simpler implementation (no mode-specific perception filters)
  3. More realistic (you can observe even if you can't act)
- **Implementation**: PerceptionSystem unchanged; agents see all nearby agents and resources regardless of current mode.

### 5.5 Decision System Target Selection

**Question**: How should DecisionSystem handle restricted modes?

**Recommendation**: Compute only valid targets for current mode.
- **Rationale**: 
  1. Prevents impossible decisions
  2. Speeds up computation (no need to evaluate invalid options)
  3. Cleaner telemetry (decisions always reflect achievable actions)
- **Implementation**: 
  - In forage mode: only evaluate resource cells
  - In trade mode: only evaluate trade partners
  - In both mode: current behavior

### 5.6 Resource Regeneration Timing

**Question**: Does ResourceRegenerationSystem run during trade-only mode?

**Recommendation**: Always run resource regeneration.
- **Rationale**:
  1. Resources are environmental processes independent of agent activities
  2. Creates interesting dynamics (resources can accumulate during trade periods)
  3. Simpler implementation
- **Implementation**: ResourceRegenerationSystem executes in all modes.

### 5.7 Edge Case: Agent at Resource During Mode Switch

**Question**: What if an agent is standing on a resource cell when trade mode starts?

**Recommendation**: No foraging occurs; agent must wait for forage mode.
- **Rationale**: Maintains strict mode boundaries and creates tactical positioning decisions.
- **Implementation**: ForageSystem checks mode and skips execution if not in forage/both mode.

### 5.8 Edge Case: Adjacent Agents During Mode Switch

**Question**: What if two agents are adjacent when forage mode starts?

**Recommendation**: No trade occurs; they must wait for trade mode.
- **Rationale**: Symmetric to the foraging case; maintains clear mode boundaries.
- **Implementation**: TradeSystem checks mode and skips execution if not in trade/both mode.

## 6. Testing Strategy

### 6.1 Unit Tests Required

```python
# test_mode_schedule.py
def test_mode_schedule_validation():
    """Test that invalid schedules raise appropriate errors."""
    with pytest.raises(ValueError):
        ModeSchedule(type="global_cycle", forage_ticks=-1, trade_ticks=5)

def test_mode_calculation():
    """Test correct mode determination at various ticks."""
    schedule = ModeSchedule(type="global_cycle", forage_ticks=10, trade_ticks=5)
    assert schedule.get_mode_at_tick(0) == "forage"
    assert schedule.get_mode_at_tick(9) == "forage"
    assert schedule.get_mode_at_tick(10) == "trade"
    assert schedule.get_mode_at_tick(14) == "trade"
    assert schedule.get_mode_at_tick(15) == "forage"  # New cycle

def test_mode_transitions_logged():
    """Test that mode changes are properly logged to telemetry."""
    # Create simulation with mode schedule
    # Run for enough ticks to see transitions
    # Query telemetry database for mode_changes table
    pass

def test_systems_skip_based_on_mode():
    """Test that TradeSystem skips in forage mode and vice versa."""
    # Mock simulation in forage mode
    # Verify TradeSystem.execute not called
    # Verify ForageSystem.execute is called
    pass
```

### 6.2 Integration Tests Required

1. **Full cycle test**: Run simulation through multiple complete forage→trade cycles
2. **Decision adaptation test**: Verify agents make appropriate decisions in each mode
3. **Cooldown persistence test**: Verify trade cooldowns continue during forage mode
4. **Resource accumulation test**: Verify resources regenerate during trade mode
5. **Edge timing test**: Verify correct behavior at exact mode transition ticks

## 7. Example YAML Configuration

```yaml
schema_version: 1
name: "Mode Toggle Demo"
N: 20
agents: 10

# New mode schedule configuration
mode_schedule:
  type: global_cycle
  forage_ticks: 15  # 15 ticks of foraging
  trade_ticks: 10   # 10 ticks of trading
  start_mode: forage  # Begin with foraging

initial_inventories:
  A: 5
  B: 5

utilities:
  mix:
    - type: ces
      weight: 1.0
      params:
        rho: 0.5
        wA: 0.5
        wB: 0.5

params:
  vision_radius: 5
  interaction_radius: 1
  move_budget_per_tick: 1
  dA_max: 5
  forage_rate: 1

resource_seed:
  density: 0.2
  amount: 3
```

## 8. Implementation Checklist

- [ ] **Schema Layer**
  - [ ] Add ModeSchedule dataclass to schema.py
  - [ ] Add mode_schedule field to ScenarioConfig
  - [ ] Update validation logic
  - [ ] Update loader.py to parse mode_schedule from YAML

- [ ] **Simulation Engine**
  - [ ] Add mode tracking state to Simulation class
  - [ ] Implement _should_execute_system method
  - [ ] Implement _handle_mode_transition method
  - [ ] Update step() method with mode logic

- [ ] **System Updates**
  - [ ] Make DecisionSystem mode-aware
  - [ ] Verify TradeSystem respects mode
  - [ ] Verify ForageSystem respects mode
  - [ ] Ensure other systems execute correctly

- [ ] **Telemetry**
  - [ ] Add mode_changes table to database schema
  - [ ] Add mode column to decisions table
  - [ ] Implement log_mode_change method
  - [ ] Update decision logging to include mode

- [ ] **Testing**
  - [ ] Write unit tests for ModeSchedule
  - [ ] Write integration tests for mode transitions
  - [ ] Test edge cases
  - [ ] Verify telemetry captures mode information

- [ ] **Documentation**
  - [ ] Update technical manual with mode system
  - [ ] Add mode schedule to typing overview
  - [ ] Create example scenarios with mode toggles
  - [ ] Update README with mode feature

## 9. Future Extensions

### 9.1 Agent-Specific Schedules
Different agents could have different schedules, creating heterogeneous time constraints.

### 9.2 Spatial Zone Modes
Different regions of the grid could be in different modes, creating spatial market segmentation.

### 9.3 Probabilistic Mode Switches
Instead of deterministic cycles, modes could switch based on random events or environmental triggers.

### 9.4 Partial Restrictions
Instead of binary on/off, modes could modify rates (e.g., "slow trade mode" with reduced dA_max).

## 10. Open Questions for Future Consideration

1. Should agents be able to "see" what mode is coming next? (Strategic anticipation)
2. Should mode schedules be mutable during simulation? (Dynamic market regulations)
3. Should there be a "transition period" with special rules when modes switch?
4. How do modes interact with future money/credit systems?

## Appendix: Rationale for Design Choices

### Why Start Simple with Global Cycles?

The global cycle approach is the minimum viable implementation that:
1. Tests the core hypothesis about emergent budget constraints
2. Requires minimal changes to existing systems
3. Provides clear, interpretable dynamics
4. Serves as foundation for more complex scheduling patterns

### Why Keep Perception Unchanged?

Restricting perception would:
1. Require complex filtering logic
2. Make debugging harder (agents behaving mysteriously)
3. Remove strategic planning opportunities
4. Not match real-world intuition (you can observe markets even when they're closed)

### Why Allow Movement in All Modes?

Movement represents physical reality that shouldn't be mode-dependent:
1. Agents still need to position themselves
2. Creates interesting strategic movement during "off" periods
3. Prevents agents from being "stuck" in bad positions
4. Simplifies implementation (no movement queue/buffer needed)
