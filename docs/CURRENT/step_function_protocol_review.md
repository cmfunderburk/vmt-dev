# VMT Step Function and Protocol Integration: Comprehensive Code Review (Grok)

**Date:** October 30, 2025  
**Reviewer:** AI Assistant  
**Scope:** Relationship between `simulation.py::step()` function and individual protocols across the 7-phase tick cycle

## Executive Summary

The VMT simulation implements a deterministic 7-phase tick cycle that orchestrates complex economic behavior through a Protocol → Effect → State pattern. The `step()` function in `simulation.py` serves as the central coordinator, executing systems in strict phase order while maintaining separation between decision logic (protocols) and state management (effects). This architecture ensures reproducibility, auditability, and extensibility.

## 1. Step Function Architecture Overview

### Core Design Pattern: Protocol → Effect → State

The simulation follows a strict separation of concerns:

1. **Protocols** generate declarative `Effect` objects representing intended actions
2. **Effects** are validated and applied by the core simulation engine
3. **State** changes occur only through validated Effects, never directly by protocols

### Step Function Signature and Flow

```python
def step(self):
    """Execute one simulation tick with mode-aware phase execution.

    7-phase tick order (see PLANS/Planning-Post-v1.md):
    1. Perception → 2. Decision → 3. Movement → 4. Trade →
    5. Forage → 6. Resource Regeneration → 7. Housekeeping
    """
    # Determine current mode
    if self.config.mode_schedule:
        new_mode = self.config.mode_schedule.get_mode_at_tick(self.tick)
        # ... mode transition logic ...

    # Execute systems conditionally based on mode
    for system in self.systems:
        if self._should_execute_system(system, self.current_mode):
            system.execute(self)

    # Log tick state for observability
    if self.telemetry:
        active_pairs = self._get_active_exchange_pairs()
        self.telemetry.log_tick_state(
            self.tick, self.current_mode, self.params.get('exchange_regime', 'barter_only'), active_pairs
        )

    self.tick += 1
```

### System Orchestration

The simulation maintains a fixed system execution order through `self.systems`:

```python
self.systems = [
    PerceptionSystem(),      # Phase 1
    decision_system,         # Phase 2 (contains protocols)
    MovementSystem(),        # Phase 3
    trade_system,            # Phase 4 (contains bargaining protocol)
    ForageSystem(),          # Phase 5
    ResourceRegenerationSystem(), # Phase 6
    HousekeepingSystem(),    # Phase 7
]
```

## 2. Phase-by-Phase Analysis

### Phase 1: Perception System

**Purpose:** Agents observe their environment  
**Protocol Involvement:** None (infrastructure-only phase)  
**Key Functions:** `perceive()`, `PerceptionSystem.execute()`

#### Data Flow
1. **Input:** Agent positions, vision_radius, grid state
2. **Processing:**
   - Use spatial index for O(N) neighbor queries (not O(N²))
   - Query cells within `vision_radius` for resources
   - Create `PerceptionView` containing neighbors, quotes, and resource cells
3. **Output:** `agent.perception_cache` dictionary with:
   ```python
   {
       "neighbors": list[tuple[int, Position]],
       "neighbor_quotes": dict[int, Quote],
       "resource_cells": list[Cell]
   }
   ```

#### Determinism Guarantees
- Spatial index queries are deterministic with same seed
- Cell visibility uses Manhattan distance calculations
- No random number generation in perception phase

### Phase 2: Decision System

**Purpose:** Agents select targets and form pairings using search/matching protocols  
**Protocol Involvement:** SearchProtocol + MatchingProtocol  
**Key Classes:** `DecisionSystem`, protocol execution methods

#### Subphases and Protocol Integration

**2.1: Clear Stale Claims**
- Removes resource claims from agents who reached target or changed target
- Ensures resource claiming system integrity
- No protocol involvement

**2.2: Search Phase** (`_execute_search_phase()`)
- **Protocol:** `self.search_protocol` (injected during simulation initialization)
- **Interface:** `SearchProtocol.build_preferences(world)` + `SearchProtocol.select_target(world)`
- **Data Flow:**
  1. Build `WorldView` for each agent via `build_world_view_for_agent()`
  2. Call `search_protocol.build_preferences(world)` → returns preference list
  3. Call `search_protocol.select_target(world)` → returns `Effect` list
  4. Apply effects via `_apply_search_effects()`
  5. Store preferences for matching phase

**2.3: Matching Phase** (`_execute_matching_phase()`)
- **Protocol:** `self.matching_protocol` (injected during simulation initialization)
- **Interface:** `MatchingProtocol.find_matches(preferences, context)`
- **Data Flow:**
  1. Build global `ProtocolContext` via `build_protocol_context()`
  2. Call `matching_protocol.find_matches(preferences, context)` → returns `Pair`/`Unpair` effects
  3. Apply effects via `_apply_pairing_effects()`

#### Effect Handling in Decision Phase

**Search Effects Applied:**
- `SetTarget`: Updates `agent.target_pos`, `target_agent_id`, `_decision_target_type`
- `ClaimResource`: Adds to `sim.resource_claims` dict
- `ReleaseClaim`: Removes from `sim.resource_claims` dict

**Matching Effects Applied:**
- `Pair`: Establishes bidirectional pairing, clears trade cooldowns, logs events
- `Unpair`: Dissolves pairings, sets trade cooldowns, logs events

#### Special Agent States Handled

1. **Already Paired Agents:** Lock target to partner, skip search
2. **Foraging-Committed Agents:** Validate commitment, maintain target if valid
3. **Trade Cooldowns:** Prevent repeated pairings via `trade_cooldowns` dict

### Phase 3: Movement System

**Purpose:** Agents move toward targets  
**Protocol Involvement:** None (direct execution)  
**Key Functions:** `MovementSystem.execute()`, `next_step_toward()`

#### Movement Logic
1. **Target Determination:**
   - Paired agents: Move toward `partner.pos`
   - Unpaired agents: Move toward `agent.target_pos`

2. **Interaction Range Check:**
   - If targeting agent and within `interaction_radius`, don't move
   - Prevents redundant movement when already in trading range

3. **Deadlock Resolution:**
   - Diagonal deadlock detection: Both agents targeting each other diagonally
   - Resolution: Higher ID agent waits (deterministic tie-breaking)

4. **Pathfinding:**
   - Manhattan distance movement with budget constraints
   - Prefer reducing |dx| before |dy|
   - Prefer negative direction when |dx| = |dy|

#### State Updates
- Position updates via `agent.pos = new_pos`
- Spatial index updates via `sim.spatial_index.update_position(agent.id, new_pos)`

### Phase 4: Trade System

**Purpose:** Negotiate trades between paired agents using bargaining protocols  
**Protocol Involvement:** BargainingProtocol  
**Key Classes:** `TradeSystem`, bargaining protocol execution

#### Trade Execution Logic

1. **Pair Processing:**
   - Iterate agents in ID order for determinism
   - Process each pair only once (track `processed_pairs`)
   - Skip unpaired agents

2. **Distance Validation:**
   - Check Manhattan distance ≤ `interaction_radius`
   - If too far, remain paired but don't trade

3. **Protocol Negotiation:**
   - **Protocol:** `self.bargaining_protocol` (injected during initialization)
   - **Interface:** `BargainingProtocol.negotiate(pair, world)`
   - **Data Flow:**
     1. Build `WorldView` via `build_trade_world_view(agent_a, agent_b, sim)`
     2. Call `bargaining_protocol.negotiate((agent_a.id, agent_b.id), world)`
     3. Apply returned effects

#### Effect Handling

**Trade Effects Applied:**
- `Trade`: Execute via `execute_trade_generic()`, update inventories, log to telemetry
- `Unpair`: Dissolve pairing, set trade cooldowns, log events

#### Trade Validation and Execution

**Inventory Updates:** Handled by `execute_trade_generic()` which:
- Validates non-negative final inventories
- Updates agent inventories
- Logs trade events with surplus calculations
- Tracks trade counts in `sim._trades_made`

**Surplus Calculation:** Computed using exchange regime-aware functions:
- Barter: `compute_surplus()`
- Money regimes: `estimate_money_aware_surplus()`

### Phase 5: Forage System

**Purpose:** Agents harvest resources  
**Protocol Involvement:** None (direct execution)  
**Key Functions:** `ForageSystem.execute()`, `forage()`

#### Foraging Logic

1. **Eligibility Checks:**
   - Skip paired agents (exclusive commitment to trading)
   - Skip if `enforce_single_harvester` and cell harvested this tick

2. **Harvest Execution:**
   - Amount = min(`cell.resource.amount`, `forage_rate`)
   - Update agent inventory: `agent.inventory.A/B += harvest`
   - Update cell: `cell.resource.amount -= harvest`

3. **State Changes:**
   - Reset last_harvested_tick for regeneration cooldown
   - Mark inventory_changed for quote refresh
   - Break foraging commitment: `agent.is_foraging_committed = False`

#### Single Harvester Enforcement

When `enforce_single_harvester = True`:
- Track harvested positions in `harvested_this_tick` set
- Only one agent can harvest from each cell per tick
- Processed in agent ID order for determinism

### Phase 6: Resource Regeneration System

**Purpose:** Resources grow after cooldown period  
**Protocol Involvement:** None (direct execution)  
**Key Functions:** `ResourceRegenerationSystem.execute()`, `regenerate_resources()`

#### Regeneration Logic

1. **Active Set Management:**
   - Track harvested cells in `grid.harvested_cells` set (O(harvested) vs O(N²))
   - Bootstrap from cells with `last_harvested_tick` set

2. **Cooldown Validation:**
   - Check `current_tick - last_harvested_tick >= cooldown_ticks`
   - Only regenerate after full cooldown period

3. **Growth Application:**
   - Amount = min(`growth_rate`, `original_amount - current_amount`)
   - Never exceed original seeded amount

4. **Set Management:**
   - Remove fully regenerated cells from active tracking
   - Maintain efficient regeneration queries

### Phase 7: Housekeeping System

**Purpose:** Update quotes, verify integrity, log telemetry  
**Protocol Involvement:** None (infrastructure)  
**Key Functions:** `HousekeepingSystem.execute()`

#### Housekeeping Tasks

1. **Quote Refresh:**
   - Refresh quotes for agents with `inventory_changed = True`
   - Money-scale aware: `refresh_quotes_if_needed(agent, spread, epsilon, money_scale, exchange_regime)`

2. **Integrity Verification:**
   - Check all pairings are bidirectional
   - Repair corrupted pairings (log and clear)

3. **Telemetry Logging:**
   - Agent snapshots: positions, inventories, utilities
   - Resource snapshots: all grid cells
   - Full state audit trail

## 3. Protocol Integration Architecture

### Protocol Injection Pattern

Protocols are injected during simulation initialization:

```python
# Decision system gets search + matching protocols
decision_system = DecisionSystem()
decision_system.search_protocol = self.search_protocol
decision_system.matching_protocol = self.matching_protocol

# Trade system gets bargaining protocol
trade_system = TradeSystem()
trade_system.bargaining_protocol = self.bargaining_protocol
```

### Protocol Resolution Order

1. **CLI Arguments:** Override everything if provided
2. **YAML Configuration:** Scenario-specific protocol selection
3. **Legacy Defaults:** Fallback for backward compatibility

### WorldView Construction

**For Search Phase:**
- `build_world_view_for_agent(agent, sim)` - Per-agent view
- Includes perception cache, inventory, quotes, simulation parameters

**For Matching Phase:**
- `build_protocol_context(sim)` - Global context
- Includes all agent states, pairings, parameters

**For Bargaining Phase:**
- `build_trade_world_view(agent_a, agent_b, sim)` - Bilateral view
- Includes both agents' states, quotes, utility functions

### Effect Validation and Application

All effects go through validation before application:

1. **Search Effects:** Applied immediately in decision phase
2. **Matching Effects:** Applied after global matching resolution
3. **Trade Effects:** Inventory validation + surplus checks
4. **State Effects:** Integrity checks + deterministic ordering

## 4. Data Flow and State Management

### State Snapshot Pattern

Each phase receives a frozen snapshot of simulation state:

- **Perception:** Grid cells, agent positions (spatial index)
- **Decision:** Perception cache, agent inventories, quotes
- **Movement:** Target positions, pairing status
- **Trade:** Paired agent states within interaction radius
- **Forage:** Current position, grid resources
- **Regeneration:** Harvested cell tracking
- **Housekeeping:** All state for logging

### Deterministic Processing Guarantees

1. **Agent Ordering:** Always `sorted(sim.agents, key=lambda a: a.id)`
2. **Pair Processing:** Deduplication via `tuple(sorted([id_a, id_b]))`
3. **Effect Ordering:** Applied in protocol return order
4. **RNG Usage:** Only through `sim.rng` (seeded generator)

### Mode-Aware Execution

The `_should_execute_system()` method implements temporal control:

```python
def _should_execute_system(self, system, mode: str) -> bool:
    # Always execute core systems
    always_execute = (PerceptionSystem, DecisionSystem, MovementSystem,
                     ResourceRegenerationSystem, HousekeepingSystem)
    
    # Mode-specific systems
    if isinstance(system, TradeSystem):
        return mode in ["trade", "both"]
    if isinstance(system, ForageSystem):
        return mode in ["forage", "both"]
```

## 5. Critical Design Patterns

### Protocol → Effect → State Pattern

**Rationale:** Ensures auditability, testability, and extensibility

- **Protocols:** Pure functions, no side effects, fully testable
- **Effects:** Declarative intents, serializable for telemetry
- **State:** Only modified through validated effects

### Spatial Index Optimization

**Problem:** Naive neighbor queries would be O(N²)  
**Solution:** Bucket-based spatial index with O(N) queries  
**Implementation:** `SpatialIndex(grid.N, bucket_size=max_radius)`

### Active Set Tracking for Regeneration

**Problem:** Scanning entire grid each tick inefficient  
**Solution:** Track only harvested cells in set  
**Implementation:** `grid.harvested_cells` set with automatic cleanup

### Perception Caching

**Problem:** Recomputing perceptions each phase wasteful  
**Solution:** Cache in `agent.perception_cache`  
**Implementation:** Computed once in Phase 1, consumed in Phase 2

## 6. Telemetry and Observability

### Multi-Level Logging

1. **Tick State:** Mode, exchange regime, active pairs
2. **Agent Snapshots:** Positions, inventories, utilities
3. **Resource Snapshots:** All cell states
4. **Events:** Pairings, trades, unpairings
5. **Preferences:** Search protocol rankings (optional)

### Audit Trail

Every effect logged with:
- Protocol name and version
- Tick number
- Full context (WorldView snapshots)
- Resulting state changes

## 7. Performance Characteristics

### Time Complexity

- **Perception:** O(N) via spatial index
- **Decision:** O(N × P) where P = perception size
- **Movement:** O(N) 
- **Trade:** O(P) where P = paired agents
- **Forage:** O(N)
- **Regeneration:** O(H) where H = harvested cells
- **Housekeeping:** O(N)

### Space Complexity

- **Spatial Index:** O(N) buckets
- **Perception Cache:** O(N × V) where V = vision radius
- **Resource Claims:** O(C) where C = active claims
- **Harvested Cells:** O(H) where H = cells in cooldown

## 8. Testing and Validation

### Determinism Verification

Core requirement: Same seed → identical outcomes across:
- Agent processing order
- Effect application sequence
- Random number generation
- Spatial query results

### Protocol Isolation

Each protocol tested independently with:
- Mock WorldView inputs
- Expected Effect outputs
- No simulation state dependencies

## 9. Extension Points

### Adding New Protocols

1. Implement protocol interface (Search/Matching/Bargaining)
2. Add to protocol registry
3. Configure via YAML or CLI
4. No core simulation changes required

### Adding New Phases

1. Create new System class
2. Add to `self.systems` list
3. Implement mode-aware execution logic
4. Update phase documentation

### Adding New Effects

1. Define Effect dataclass in `protocols/base.py`
2. Add handling logic in appropriate system
3. Update telemetry schema
4. Maintain backward compatibility

## Conclusion

The VMT step function implements a sophisticated orchestration layer that maintains clean separation between economic decision logic (protocols) and simulation mechanics (systems). The Protocol → Effect → State pattern ensures that complex market behaviors remain deterministic, auditable, and extensible while providing the performance characteristics needed for large-scale agent-based simulations.

The 7-phase architecture successfully balances:
- **Modularity:** Each phase has clear responsibilities
- **Performance:** Optimized data structures and algorithms  
- **Determinism:** Strict ordering and seeded randomness
- **Observability:** Comprehensive telemetry and audit trails
- **Extensibility:** Protocol system allows new market mechanisms

This architecture provides a solid foundation for implementing and testing advanced microeconomic theories in agent-based simulation environments.
