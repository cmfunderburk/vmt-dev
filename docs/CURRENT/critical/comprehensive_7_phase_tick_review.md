# Comprehensive 7-Phase Tick Cycle Review
**Date:** 2024-10-30  
**Purpose:** Exhaustive documentation of the step function and protocol relationships

---

## Executive Summary

The VMT simulation engine operates on a strict 7-phase tick cycle, orchestrated by the `Simulation.step()` function. Each phase is executed by a **System** that may delegate decision logic to **Protocols**. This architecture implements the **Protocol → Effect → State** pattern, where:

1. **Protocols** receive frozen, read-only `WorldView` snapshots
2. **Protocols** return declarative `Effect` objects
3. **Systems** validate and apply effects to mutate simulation state

This design ensures determinism, testability, and clean separation of concerns between infrastructure (systems) and domain logic (protocols).

---

## Architecture Overview

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────┐
│ SIMULATION (simulation.py)                              │
│ - Orchestrates 7-phase tick cycle                       │
│ - Manages global state (agents, grid, telemetry)        │
│ - Provides deterministic RNG                             │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ SYSTEMS (systems/*.py)                                   │
│ - PerceptionSystem: Build frozen WorldViews             │
│ - DecisionSystem: Coordinate search & matching          │
│ - MovementSystem: Update agent positions                │
│ - TradeSystem: Coordinate bargaining                    │
│ - ForageSystem: Harvest resources                       │
│ - ResourceRegenerationSystem: Regenerate depleted cells │
│ - HousekeepingSystem: Refresh quotes & log telemetry    │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ PROTOCOLS (protocols/*/.)                                │
│ - SearchProtocol: Build preferences & select targets    │
│ - MatchingProtocol: Form bilateral pairings             │
│ - BargainingProtocol: Negotiate trade terms             │
└─────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Determinism**: All randomness uses seeded RNG (`sim.rng`). All iterations are sorted.
2. **Immutability**: Protocols receive frozen `WorldView` objects, cannot mutate state.
3. **Effect-Based State Transitions**: State changes only through validated Effect application.
4. **Mode-Aware Execution**: Systems conditionally execute based on `mode` (trade/forage/both).

---

## The 7-Phase Tick Cycle

### High-Level Overview

Each tick executes these phases in fixed order:

1. **Perception** → Agents observe environment (frozen snapshot)
2. **Decision** → Agents select targets and form pairings (Search + Matching)
3. **Movement** → Agents move toward targets
4. **Trade** → Paired agents negotiate trades (Bargaining)
5. **Forage** → Agents harvest resources
6. **Resource Regeneration** → Resources grow over time
7. **Housekeeping** → Quote refresh, telemetry logging, cleanup

**Critical:** All agent observations (phase 1) are based on state at tick start. This prevents race conditions and ensures determinism.

---

## Phase-by-Phase Detailed Analysis

### PHASE 0: Step Function Entry Point

**Location:** `simulation.py:321-355` (`Simulation.step()`)

#### Execution Flow

1. **Mode Determination** (lines 329-338)
   - Check if `mode_schedule` exists
   - Call `mode_schedule.get_mode_at_tick(self.tick)`
   - Compare with `self.current_mode`
   - If changed: call `_handle_mode_transition()`
     - Log mode change to telemetry
     - Clear all pairings via `_clear_pairings_on_mode_switch()`
     - Clear all foraging commitments
   - Update `self.current_mode` and `self._mode_change_tick`

2. **System Execution Loop** (lines 341-343)
   ```python
   for system in self.systems:
       if self._should_execute_system(system, self.current_mode):
           system.execute(self)
   ```

3. **Mode-Aware System Filtering** (`_should_execute_system`, lines 357-380)
   - **Always execute:**
     - PerceptionSystem (agents need to observe)
     - DecisionSystem (target selection)
     - MovementSystem (move toward targets)
     - ResourceRegenerationSystem (background process)
     - HousekeepingSystem (maintenance)
   
   - **Conditionally execute:**
     - TradeSystem: only if `mode in ["trade", "both"]`
     - ForageSystem: only if `mode in ["forage", "both"]`

4. **Telemetry Logging** (lines 346-353)
   - Compute active exchange pairs via `_get_active_exchange_pairs()`
   - Log tick state (tick, mode, regime, active pairs)

5. **Tick Increment** (line 355)
   - `self.tick += 1`

#### Key Data Structures at Step Entry

```python
self.agents: list[Agent]               # All agents (sorted by id)
self.agent_by_id: dict[int, Agent]     # Fast lookup by agent ID
self.grid: Grid                        # N×N grid with resources
self.spatial_index: SpatialIndex       # O(N) proximity queries
self.resource_claims: dict[pos, id]    # position → claiming agent
self.current_mode: str                 # "trade" | "forage" | "both"
self.params: dict                      # Scenario parameters
self.rng: np.random.Generator          # Deterministic RNG
self.telemetry: TelemetryManager       # Database logger
self.systems: list[System]             # 7 phase systems
```

---

### PHASE 1: Perception

**Location:** `systems/perception.py` (`PerceptionSystem.execute()`)

**Purpose:** Build frozen WorldView snapshots for all agents. This snapshot is the **single source of truth** for all decisions made during this tick.

#### System Implementation

```python
class PerceptionSystem:
    def execute(self, sim: Simulation) -> None:
        for agent in sim.agents:
            # Find nearby agents using spatial index (O(N) not O(N²))
            nearby_agent_ids = sim.spatial_index.query_radius(
                agent.pos,
                agent.vision_radius,
                exclude_id=agent.id,
            )
            
            # Build PerceptionView
            perception = perceive(agent, sim.grid, nearby_agent_ids, sim.agent_by_id)
            
            # Cache in agent for Decision phase
            agent.perception_cache = {
                "neighbors": perception.neighbors,
                "neighbor_quotes": perception.neighbor_quotes,
                "resource_cells": perception.resource_cells,
            }
```

#### The `perceive()` Function (lines 40-79)

**Inputs:**
- `agent`: The perceiving agent
- `grid`: Simulation grid (for resource visibility)
- `nearby_agent_ids`: Pre-filtered list from spatial index
- `agent_by_id`: Agent lookup dictionary

**Outputs:**
- `PerceptionView` with three components:
  1. `neighbors`: list[(agent_id, position)]
  2. `neighbor_quotes`: dict[agent_id → Quote]
  3. `resource_cells`: list[Cell] with visible resources

**Algorithm:**

1. **Build Neighbor List**
   - Iterate over `nearby_agent_ids` (already filtered by spatial index)
   - For each neighbor:
     - Append `(neighbor.id, neighbor.pos)` to neighbors list
     - Snapshot quotes: `neighbor_quotes[neighbor.id] = neighbor.quotes` (copy)
   
2. **Get Visible Resources**
   - Call `grid.cells_within_radius(agent.pos, vision_radius)`
   - Filter for cells where `cell.resource.amount > 0` and `cell.resource.type != None`
   - Append to `resource_cells`

3. **Return Frozen Snapshot**
   - Create `PerceptionView` dataclass
   - This snapshot is **frozen** - quote changes during this tick won't affect decisions

#### Performance Optimization: Spatial Index

**Why:** Naive neighbor finding is O(N²) - each of N agents checks all N agents.

**Solution:** `SpatialIndex` with bucket-based spatial hashing
- Grid divided into buckets of size `max(vision_radius, interaction_radius)`
- Agent positions hashed to buckets
- `query_radius()` only checks agents in nearby buckets
- **Complexity:** O(N) average case (assumes uniform distribution)

**Update Protocol:**
- Agents added: `spatial_index.add_agent(id, pos)` during initialization
- Positions updated: `spatial_index.update_position(id, new_pos)` during Movement phase

#### Critical Design Decision: Snapshot Timing

**All agents observe CURRENT state before any decisions are made.**

This means:
- If agent A trades in tick T, agent B still sees A's OLD position/inventory during tick T decisions
- Agent B will observe A's NEW state in tick T+1 perception
- This prevents information propagation within a tick (realistic delay)

---

### PHASE 2: Decision

**Location:** `systems/decision.py` (`DecisionSystem.execute()`)

**Purpose:** Agents select targets (trade partners or forage sites) and form bilateral pairings through two-sub-phase protocol coordination.

**Protocol Involvement:**
- **SearchProtocol**: Individual target selection
- **MatchingProtocol**: Bilateral pairing formation

#### System Implementation Overview

```python
class DecisionSystem:
    def __init__(self):
        self.search_protocol: Optional[SearchProtocol] = None
        self.matching_protocol: Optional[MatchingProtocol] = None
    
    def execute(self, sim: Simulation) -> None:
        # Step 1: Clear stale resource claims
        self._clear_stale_claims(sim)
        
        # Step 2: Search phase - build preferences and select targets
        preferences = self._execute_search_phase(sim)
        
        # Step 3: Matching phase - establish pairings
        self._execute_matching_phase(sim, preferences)
        
        # Step 4: Log decisions to telemetry
        self._log_decisions(sim, preferences)
```

#### Step 1: Clear Stale Resource Claims (lines 299-318)

**Purpose:** Remove resource claims from agents that no longer need them.

**Algorithm:**

```python
def _clear_stale_claims(self, sim: Simulation) -> None:
    claims_to_remove = []
    
    for pos, agent_id in sim.resource_claims.items():
        agent = sim.agent_by_id.get(agent_id)
        
        # Keep claim if agent is foraging-committed to this resource
        if agent and agent.is_foraging_committed and agent.forage_target_pos == pos:
            continue  # Persist until commitment breaks
        
        # Remove claim if:
        # 1. Agent doesn't exist (defensive)
        # 2. Agent reached the resource (pos == target)
        # 3. Agent changed target (target_pos != claimed pos)
        if agent is None or agent.pos == pos or agent.target_pos != pos:
            claims_to_remove.append(pos)
    
    for pos in claims_to_remove:
        del sim.resource_claims[pos]
```

**Foraging Commitment Model:**
- When agent selects forage target, sets `agent.is_foraging_committed = True`
- Claim persists across ticks until:
  - Agent reaches resource and harvests (commitment broken in ForageSystem)
  - Resource disappears (validated in `_validate_foraging_commitment`)
  - Mode changes (commitment cleared in `_handle_mode_transition`)

---

#### Step 2A: Search Phase (lines 66-109)

**Purpose:** Each agent builds preference rankings and selects a target using SearchProtocol.

**Algorithm:**

```python
def _execute_search_phase(self, sim: Simulation) -> dict:
    preferences = {}
    
    for agent in sorted(sim.agents, key=lambda a: a.id):  # DETERMINISTIC ORDER
        # Skip if already paired from previous tick
        if agent.paired_with_id is not None:
            self._handle_paired_agent(agent, sim)
            preferences[agent.id] = []
            continue
        
        # Skip if foraging-committed and commitment still valid
        if agent.is_foraging_committed and agent.forage_target_pos:
            if self._validate_foraging_commitment(agent, sim):
                agent.target_pos = agent.forage_target_pos
                agent.target_agent_id = None
                agent._decision_target_type = "forage"
                preferences[agent.id] = []
                continue
            else:
                # Commitment broken - clear and proceed with search
                agent.is_foraging_committed = False
                agent.forage_target_pos = None
        
        # Build WorldView for this agent
        world = build_world_view_for_agent(agent, sim)
        
        # Call search protocol
        prefs = self.search_protocol.build_preferences(world)
        effects = self.search_protocol.select_target(world)
        
        # Apply search effects immediately
        self._apply_search_effects(agent, effects, sim)
        
        # Store preferences for matching phase
        preferences[agent.id] = prefs
    
    return preferences
```

**Execution Details:**

1. **Paired Agent Handling** (`_handle_paired_agent`, lines 124-148)
   - Validate pairing integrity (partner exists, bidirectional)
   - If corrupted: log unpair event, clear pairing
   - If valid: lock target to partner's position
   - Set `agent._decision_target_type = "trade_paired"`

2. **Foraging Commitment Validation** (`_validate_foraging_commitment`, lines 150-168)
   - Check if resource still exists at `agent.forage_target_pos`
   - If disappeared: delete claim, return False
   - If exists: return True (commitment persists)

3. **WorldView Construction** (`build_world_view_for_agent`, context_builders.py:20-103)
   
   **From Perception Cache:**
   - Extract `neighbors`, `neighbor_quotes`, `resource_cells`
   
   **Build AgentView List:**
   ```python
   visible_agents = []
   for neighbor_id, neighbor_pos in view["neighbors"]:
       neighbor = sim.agent_by_id[neighbor_id]
       visible_agents.append(AgentView(
           agent_id=neighbor.id,
           pos=neighbor.pos,
           quotes=neighbor.quotes.copy(),  # FROZEN
           paired_with_id=neighbor.paired_with_id
       ))
   ```
   
   **Build ResourceView List:**
   ```python
   visible_resources = []
   for cell in view["resource_cells"]:
       visible_resources.append(ResourceView(
           pos=cell.position,
           A=cell.resource.amount if cell.resource.type == "A" else 0,
           B=cell.resource.amount if cell.resource.type == "B" else 0,
           claimed_by_id=sim.resource_claims.get(cell.position)
       ))
   ```
   
   **Build Params Dict:**
   - Includes: grid_size, beta, forage_rate, vision_radius, interaction_radius, move_budget, dA_max, epsilon, money_scale, trade_cooldown_ticks, home_pos
   - Also: resource_claims dict (for claim filtering)
   
   **Return WorldView:**
   ```python
   return WorldView(
       tick=sim.tick,
       mode=sim.current_mode,
       exchange_regime=sim.params["exchange_regime"],
       agent_id=agent.id,
       pos=agent.pos,
       inventory={"A": agent.inventory.A, "B": ..., "M": ...},
       utility=agent.utility,
       quotes=agent.quotes.copy(),
       lambda_money=agent.lambda_money,
       paired_with_id=agent.paired_with_id,
       trade_cooldowns=agent.trade_cooldowns.copy(),
       visible_agents=visible_agents,
       visible_resources=visible_resources,
       params=params,
       rng=sim.rng  # Shared deterministic RNG
   )
   ```

4. **Protocol: SearchProtocol.build_preferences()**
   
   **Interface:**
   ```python
   def build_preferences(self, world: WorldView) -> list[tuple[Target, float, dict]]:
       """
       Returns: List of (target, score, metadata) sorted descending by score
       Target can be: int (agent_id) | Position (x, y)
       """
   ```
   
   **Example: LegacySearchProtocol** (protocols/search/legacy.py)
   
   **For Trade Mode:**
   - Iterate over `world.visible_agents`
   - Skip agents in trade cooldown
   - Calculate surplus using quotes (regime-aware)
     - Barter: `compute_surplus()` - checks bid/ask overlap
     - Money: `estimate_money_aware_surplus()` - checks A<->M, B<->M, A<->B
   - Calculate distance: `|Δx| + |Δy|` (Manhattan)
   - Discount: `discounted_surplus = surplus × β^distance`
   - Sort by `(-discounted_surplus, agent_id)` for deterministic ranking
   
   **For Forage Mode:**
   - Filter claimed resources (exclude claimed by others)
   - For each available resource:
     - Calculate utility gain: `Δu = u(current + harvest) - u(current)`
     - Calculate distance
     - Discount: `discounted_u = Δu × β^distance`
   - Sort by `(-discounted_u, pos[0], pos[1])` for deterministic ranking
   
   **For Both Mode:**
   - Build both trade and forage preferences
   - Combine with type tags in metadata
   - Return combined list (caller will compare top scores)

5. **Protocol: SearchProtocol.select_target()**
   
   **Interface:**
   ```python
   def select_target(self, world: WorldView) -> list[Effect]:
       """
       Returns: 
           [SetTarget(...)] if target selected
           [SetTarget(...), ClaimResource(...)] if foraging target
           [] if no suitable target (idle)
       """
   ```
   
   **Example: LegacySearchProtocol**
   
   **Trade Mode:**
   - Get best from `build_trade_preferences()`
   - Find partner position in `visible_agents`
   - Return `[SetTarget(agent_id=self.id, target=partner_id)]`
   
   **Forage Mode:**
   - Get best from `build_forage_preferences()`
   - Return `[SetTarget(..., target=pos), ClaimResource(..., pos=pos)]`
   
   **Both Mode:**
   - Compare best trade score vs best forage score
   - Select activity with higher discounted score
   - Return effects for chosen activity

6. **Apply Search Effects** (`_apply_search_effects`, lines 170-207)
   
   **For SetTarget(target):**
   
   If `target` is int (agent ID):
   ```python
   partner = sim.agent_by_id[target]
   agent.target_pos = partner.pos
   agent.target_agent_id = target
   agent._decision_target_type = "trade"
   ```
   
   If `target` is Position:
   ```python
   agent.target_pos = target
   agent.target_agent_id = None
   cell = sim.grid.get_cell(target[0], target[1])
   if cell has resource:
       agent._decision_target_type = "forage"
       agent.is_foraging_committed = True
       agent.forage_target_pos = target
   else:
       agent._decision_target_type = "idle_home"
   ```
   
   **For ClaimResource(pos):**
   ```python
   if sim.params["enable_resource_claiming"]:
       sim.resource_claims[pos] = agent.id
   ```
   
   **For ReleaseClaim(pos):**
   ```python
   if pos in sim.resource_claims:
       del sim.resource_claims[pos]
   ```

---

#### Step 2B: Matching Phase (lines 111-122)

**Purpose:** Form bilateral pairings from agent preferences using MatchingProtocol.

**Algorithm:**

```python
def _execute_matching_phase(self, sim: Simulation, preferences: dict) -> None:
    # Build ProtocolContext with global state
    context = build_protocol_context(sim)
    
    # Call matching protocol
    pairing_effects = self.matching_protocol.find_matches(preferences, context)
    
    # Apply pairing effects
    self._apply_pairing_effects(pairing_effects, sim)
```

**ProtocolContext Construction** (`build_protocol_context`, context_builders.py:106-179)

**Contains:**
- `tick`, `mode`, `exchange_regime`
- `all_agent_views`: dict of ALL agents (not just visible)
- `all_resource_views`: list of ALL resources on grid
- `current_pairings`: dict of existing pairs
- `protocol_state`: dict for multi-tick protocol state storage
- `params`: Full simulation parameters PLUS per-agent state:
  - `agent_{id}_inv_A/B/M`: Agent inventories
  - `agent_{id}_utility`: Utility function
  - `agent_{id}_lambda`, `agent_{id}_M_0`, `agent_{id}_money_utility_form`
- `rng`: Shared deterministic RNG

**Why Global Context?** Matching protocols need to:
- See all agents (not just visible neighbors)
- Calculate surplus between any pair
- Make global optimization decisions

**Protocol: MatchingProtocol.find_matches()**

**Interface:**
```python
def find_matches(
    self,
    preferences: dict[int, list[tuple[Target, float, dict]]],
    world: ProtocolContext,
) -> list[Effect]:
    """
    Returns: List of Pair(...) effects
    """
```

**Example: GreedySurplusMatching** (protocols/matching/greedy.py)

**Algorithm:**

1. **Filter to Trade-Seeking Agents**
   ```python
   trade_agents = set()
   for agent_id, prefs in preferences.items():
       trade_prefs = [p for p in prefs if isinstance(p[0], int)]
       if trade_prefs:
           trade_agents.add(agent_id)
   ```

2. **Skip Already-Paired Agents**
   ```python
   available = [aid for aid in trade_agents 
                if aid not in world.current_pairings]
   ```

3. **Enumerate All Potential Pairs**
   ```python
   potential_pairings = []
   for i, agent_a_id in enumerate(sorted(available)):
       for agent_b_id in sorted(available)[i+1:]:
           # Calculate surplus for this pair
           total, discounted, distance = self._calculate_pair_surplus(
               agent_a_id, agent_b_id, world, exchange_regime, epsilon, beta
           )
           if total > 0:
               potential_pairings.append((
                   -discounted,  # Negative for descending sort
                   total, agent_a_id, agent_b_id, distance
               ))
   ```

4. **Calculate Pair Surplus** (`_calculate_pair_surplus`, lines 167-218)
   - Build pseudo-Agent objects from ProtocolContext
   - Call `find_all_feasible_trades(agent_a, agent_b, regime, params, epsilon)`
   - Find trade with max total surplus
   - Calculate distance, apply beta discount
   - Return `(total_surplus, discounted_surplus, distance)`

5. **Sort by Discounted Surplus**
   ```python
   potential_pairings.sort(key=lambda x: (x[0], x[2], x[3]))
   ```

6. **Greedy Pairing Assignment**
   ```python
   paired_this_pass = set()
   for _, _, agent_a_id, agent_b_id, _ in potential_pairings:
       if agent_a_id in paired_this_pass or agent_b_id in paired_this_pass:
           continue  # Already paired
       
       effects.append(Pair(
           protocol_name=self.name,
           tick=world.tick,
           agent_a=agent_a_id,
           agent_b=agent_b_id,
           reason="greedy_welfare_maximization"
       ))
       
       paired_this_pass.add(agent_a_id)
       paired_this_pass.add(agent_b_id)
   ```

**Apply Pairing Effects** (`_apply_pairing_effects`, lines 209-260)

**For Pair(agent_a, agent_b):**

1. **Establish Pairing**
   ```python
   agent_a.paired_with_id = agent_b.id
   agent_b.paired_with_id = agent_a.id
   ```

2. **Update Targets**
   ```python
   agent_a.target_pos = agent_b.pos
   agent_a.target_agent_id = agent_b.id
   agent_b.target_pos = agent_a.pos
   agent_b.target_agent_id = agent_a.id
   ```

3. **Clear Trade Cooldowns**
   ```python
   agent_a.trade_cooldowns.pop(agent_b.id, None)
   agent_b.trade_cooldowns.pop(agent_a.id, None)
   ```

4. **Calculate Surpluses** (for telemetry logging)
   - Call `_calculate_surplus(agent_a, agent_b, sim)`
   - Uses regime-aware surplus estimation

5. **Log Pairing Event**
   ```python
   sim.telemetry.log_pairing_event(
       tick, agent_a.id, agent_b.id, 
       "pair", reason, surplus_a, surplus_b
   )
   ```

**For Unpair(agent_a, agent_b):**

1. **Dissolve Pairing**
   ```python
   agent_a.paired_with_id = None
   agent_b.paired_with_id = None
   agent_a.target_agent_id = None
   agent_b.target_agent_id = None
   ```

2. **Log Unpair Event**
   ```python
   sim.telemetry.log_pairing_event(
       tick, agent_a.id, agent_b.id, "unpair", reason
   )
   ```

---

#### Step 2C: Log Decisions (lines 274-297)

**Purpose:** Record preference rankings to telemetry for analysis.

**Only if:** `sim.params["log_preferences"] == True` (disabled by default for performance)

**Algorithm:**

```python
for agent in sorted(sim.agents, key=lambda a: a.id):
    prefs = preferences.get(agent.id, [])
    trade_prefs = [p for p in prefs if isinstance(p[0], int)]
    
    for rank, (target_id, score, meta) in enumerate(trade_prefs):
        pair_type = meta.get("pair_type", "A<->B")
        surplus = meta.get("surplus", score)
        discounted_surplus = meta.get("discounted_surplus", score)
        distance = meta.get("distance", 0)
        
        sim.telemetry.log_preference(
            tick, agent.id, target_id, rank,
            surplus, discounted_surplus, distance, pair_type
        )
```

---

### PHASE 3: Movement

**Location:** `systems/movement.py` (`MovementSystem.execute()`)

**Purpose:** Agents move toward their selected targets from Decision phase.

**No Protocol Involvement:** Movement is deterministic given target positions.

#### System Implementation

```python
class MovementSystem:
    def execute(self, sim: Simulation) -> None:
        for agent in sim.agents:
            # Determine target position
            if agent.paired_with_id is not None:
                partner = sim.agent_by_id[agent.paired_with_id]
                target_pos = partner.pos
            else:
                target_pos = agent.target_pos
            
            if target_pos is not None:
                # Check if already in interaction range
                if agent.target_agent_id is not None:
                    target_agent = sim.agent_by_id[agent.target_agent_id]
                    distance = sim.grid.manhattan_distance(agent.pos, target_agent.pos)
                    if distance <= sim.params["interaction_radius"]:
                        continue  # Don't move, already in range
                
                # Check for diagonal deadlock
                if agent.target_agent_id is not None:
                    target_agent = sim.agent_by_id[agent.target_agent_id]
                    if target_agent.target_agent_id == agent.id:
                        # Mutual targeting detected
                        if (manhattan_distance == 2 and 
                            abs(dx) == 1 and abs(dy) == 1):
                            # Diagonal deadlock
                            if agent.id < target_agent.id:
                                continue  # Lower ID waits
                
                # Move toward target
                new_pos = next_step_toward(
                    agent.pos, target_pos, sim.params["move_budget_per_tick"]
                )
                agent.pos = new_pos
                
                # Update spatial index
                sim.spatial_index.update_position(agent.id, new_pos)
```

#### Movement Algorithm: `next_step_toward()` (lines 61-109)

**Purpose:** Calculate new position moving toward target by up to `budget` steps.

**Uses Manhattan distance movement with deterministic tie-breaking:**

```python
def next_step_toward(current: Position, target: Position, budget: int) -> Position:
    x, y = current
    tx, ty = target
    dx = tx - x
    dy = ty - y
    
    for _ in range(budget):
        if dx == 0 and dy == 0:
            break  # Reached target
        
        # Tie-breaking rules:
        # 1. Prefer reducing |dx| before |dy|
        # 2. If |dx| == |dy|, prefer x direction
        # 3. Within direction, prefer negative over positive
        
        if abs(dx) >= abs(dy) and dx != 0:
            # Move in x direction
            if dx < 0:
                x -= 1
                dx += 1
            else:
                x += 1
                dx -= 1
        elif dy != 0:
            # Move in y direction
            if dy < 0:
                y -= 1
                dy += 1
            else:
                y += 1
                dy -= 1
    
    return (x, y)
```

**Determinism:** Given same start, target, and budget, always produces same path.

#### Diagonal Deadlock Resolution

**Problem:** Two agents targeting each other, diagonally adjacent (distance=2, |dx|=1, |dy|=1).

**Example:**
```
A . . .
. . . .
. . B .
```
Both move diagonally toward each other, but can't reach (Manhattan movement).

**Solution:** Only higher ID agent moves, lower ID waits.
- Agent A (id=0) waits
- Agent B (id=1) moves
- Next tick: agents are orthogonally adjacent, both can move

**Why This Works:** Deterministic priority breaks symmetry, allows convergence.

---

### PHASE 4: Trade

**Location:** `systems/trading.py` (`TradeSystem.execute()`)

**Purpose:** Paired agents within interaction radius negotiate and execute trades via BargainingProtocol.

**Protocol Involvement:**
- **BargainingProtocol**: Trade negotiation

#### System Implementation

```python
class TradeSystem:
    def __init__(self):
        self.bargaining_protocol: Optional[BargainingProtocol] = None
    
    def execute(self, sim: Simulation) -> None:
        processed_pairs = set()
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            if agent.paired_with_id is None:
                continue
            
            partner_id = agent.paired_with_id
            pair_key = tuple(sorted([agent.id, partner_id]))
            if pair_key in processed_pairs:
                continue  # Already processed
            processed_pairs.add(pair_key)
            
            partner = sim.agent_by_id[partner_id]
            distance = manhattan_distance(agent.pos, partner.pos)
            
            if distance <= sim.params["interaction_radius"]:
                self._negotiate_trade(agent, partner, sim)
            # else: Stay paired, keep moving
```

**Key Points:**
- Only process each pair once (not twice)
- Only negotiate if within interaction radius (typically 1)
- If too far: stay paired, Movement phase will bring them closer

#### Trade Negotiation (`_negotiate_trade`, lines 104-124)

```python
def _negotiate_trade(self, agent_a: Agent, agent_b: Agent, sim: Simulation) -> None:
    # Build WorldView for trade negotiation
    world = build_trade_world_view(agent_a, agent_b, sim)
    
    # Call bargaining protocol
    effects = self.bargaining_protocol.negotiate((agent_a.id, agent_b.id), world)
    
    # Apply effects
    for effect in effects:
        if isinstance(effect, Trade):
            self._apply_trade_effect(effect, sim)
        elif isinstance(effect, Unpair):
            self._apply_unpair_effect(effect, sim)
```

#### WorldView Construction for Trade (`build_trade_world_view`, context_builders.py:182-233)

**Extends** standard WorldView with partner's full state:

```python
def build_trade_world_view(agent_a, agent_b, sim) -> WorldView:
    # Start with agent_a's WorldView
    world = build_world_view_for_agent(agent_a, sim)
    
    # Add partner's inventory to params
    params_with_partner = world.params.copy()
    params_with_partner[f"partner_{agent_b.id}_inv_A"] = agent_b.inventory.A
    params_with_partner[f"partner_{agent_b.id}_inv_B"] = agent_b.inventory.B
    params_with_partner[f"partner_{agent_b.id}_inv_M"] = agent_b.inventory.M
    params_with_partner[f"partner_{agent_b.id}_lambda"] = agent_b.lambda_money
    params_with_partner[f"partner_{agent_b.id}_utility"] = agent_b.utility
    params_with_partner[f"partner_{agent_b.id}_money_utility_form"] = ...
    params_with_partner[f"partner_{agent_b.id}_M_0"] = agent_b.M_0
    
    # Rebuild WorldView with extended params
    return WorldView(..., params=params_with_partner, ...)
```

**Why Needed:** Bargaining protocols need both agents' full utility functions to calculate optimal trades.

#### Protocol: BargainingProtocol.negotiate()

**Interface:**
```python
def negotiate(self, pair: tuple[int, int], world: WorldView) -> list[Effect]:
    """
    Returns:
        [Trade(...)] if agreement reached
        [Unpair(...)] if negotiation fails
        [] if multi-tick protocol still negotiating
    """
```

**Example: SplitDifference** (protocols/bargaining/split_difference.py)

**Algorithm:**

1. **Build Pseudo-Agent Objects**
   ```python
   agent_i = self._build_agent_from_world(world, agent_a_id)
   agent_j = self._build_agent_from_world(world, agent_b_id)
   ```

2. **Find All Feasible Trades**
   ```python
   feasible_trades = find_all_feasible_trades(
       agent_i, agent_j, exchange_regime, params, epsilon
   )
   ```
   
   **`find_all_feasible_trades()` (matching.py:400+):**
   - Determines which pair types to evaluate (based on regime)
   - For each pair type:
     - **A<->B**: Enumerate quantities (1 to dA_max), calculate price, check feasibility
     - **A<->M**: Enumerate quantities, use ask/bid prices from quotes
     - **B<->M**: Similar to A<->M
   - For each candidate trade:
     - Calculate pre-trade utilities
     - Calculate post-trade utilities
     - Calculate surpluses: `Δu_i`, `Δu_j`
     - Check constraints:
       - Both inventories non-negative
       - Both surpluses positive (individually rational)
       - Conservation: goods + money conserved
   - Return list of `(pair_name, trade_tuple)` where:
     ```python
     trade_tuple = (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
     ```

3. **No Feasible Trade → Unpair**
   ```python
   if not feasible_trades:
       return [Unpair(..., reason="no_feasible_trade")]
   ```

4. **Select Trade Closest to Equal Surplus Split**
   ```python
   best_trade = None
   best_evenness = float('inf')
   
   for pair_name, trade_tuple in feasible_trades:
       surplus_i, surplus_j = trade_tuple[6], trade_tuple[7]
       total_surplus = surplus_i + surplus_j
       evenness = abs(surplus_i - total_surplus / 2)
       
       if evenness < best_evenness:
           best_evenness = evenness
           best_trade = trade_tuple
           best_pair_name = pair_name
   ```

5. **Convert to Trade Effect**
   ```python
   return [self._create_trade_effect(
       agent_a_id, agent_b_id, best_pair_name, best_trade, evenness, world
   )]
   ```

#### Apply Trade Effect (`_apply_trade_effect`, lines 126-195)

**Purpose:** Update agent inventories and log trade to telemetry.

**Critical:** Agents REMAIN PAIRED after successful trade (can trade again next tick).

**Algorithm:**

1. **Determine Buyer/Seller from Trade Tuple**
   ```python
   # For A<->B: buyer receives A (dA > 0), seller gives A (dA < 0)
   # For A<->M: buyer receives A, seller receives M
   # For B<->M: buyer receives B, seller receives M
   ```

2. **Convert to Canonical Format**
   - Map `(agent_i, agent_j)` from trade tuple to `(buyer, seller)`
   - Ensure `agent_i.id < agent_j.id` for determinism

3. **Build Trade Tuple for `execute_trade_generic()`**
   ```python
   trade_tuple = (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
   ```

4. **Execute Trade**
   ```python
   execute_trade_generic(agent_i, agent_j, trade_tuple)
   ```
   
   **`execute_trade_generic()` (matching.py:1200+):**
   ```python
   def execute_trade_generic(agent_i, agent_j, trade_tuple):
       dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade_tuple
       
       # Update inventories
       agent_i.inventory.A += dA_i
       agent_i.inventory.B += dB_i
       agent_i.inventory.M += dM_i
       agent_j.inventory.A += dA_j
       agent_j.inventory.B += dB_j
       agent_j.inventory.M += dM_j
       
       # Round to prevent float accumulation
       agent_i.inventory.M = round(agent_i.inventory.M, 2)
       agent_j.inventory.M = round(agent_j.inventory.M, 2)
       
       # Mark inventory changed (for quote refresh)
       agent_i.inventory_changed = True
       agent_j.inventory_changed = True
   ```

5. **Update Trade Counters**
   ```python
   sim._trades_made[buyer.id] += 1
   sim._trades_made[seller.id] += 1
   ```

6. **Log to Telemetry**
   ```python
   sim.telemetry.log_trade(
       tick, x, y, buyer_id, seller_id,
       dA, dB, price, direction, dM, pair_type
   )
   ```

#### Apply Unpair Effect (`_apply_unpair_effect`, lines 197-216)

**Purpose:** Dissolve pairing and set trade cooldown.

```python
def _apply_unpair_effect(self, effect: Unpair, sim: Simulation) -> None:
    agent_a = sim.agent_by_id[effect.agent_a]
    agent_b = sim.agent_by_id[effect.agent_b]
    
    # Dissolve pairing
    agent_a.paired_with_id = None
    agent_b.paired_with_id = None
    
    # Set trade cooldown
    cooldown_until = sim.tick + sim.params["trade_cooldown_ticks"]
    agent_a.trade_cooldowns[effect.agent_b] = cooldown_until
    agent_b.trade_cooldowns[effect.agent_a] = cooldown_until
    
    # Log unpair event
    sim.telemetry.log_pairing_event(
        tick, effect.agent_a, effect.agent_b, "unpair", effect.reason
    )
```

**Trade Cooldown Mechanism:**
- After failed trade attempt, agents can't pair for `trade_cooldown_ticks` (default: 10)
- Cooldown checked in SearchProtocol during preference building
- Prevents infinite pairing loops with same incompatible partner
- Cleared when agents successfully trade OR successfully forage

---

### PHASE 5: Forage

**Location:** `systems/foraging.py` (`ForageSystem.execute()`)

**Purpose:** Agents harvest resources from their current cell.

**No Protocol Involvement:** Harvesting is deterministic given position and forage_rate.

#### System Implementation

```python
class ForageSystem:
    def execute(self, sim: Simulation) -> None:
        harvested_this_tick = set()
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            # Skip paired agents (exclusive commitment to trading)
            if agent.paired_with_id is not None:
                continue
            
            pos = agent.pos
            
            # Enforce single harvester per cell (if enabled)
            if sim.params["enforce_single_harvester"]:
                if pos in harvested_this_tick:
                    continue
            
            # Attempt to forage
            did_harvest, resource_type, amount = forage(
                agent, sim.grid, sim.params["forage_rate"], sim.tick
            )
            
            if did_harvest:
                if resource_type and hasattr(sim, "_gathered_resources"):
                    sim._gathered_resources[agent.id][resource_type] += amount
                if sim.params["enforce_single_harvester"]:
                    harvested_this_tick.add(pos)
```

**Key Points:**
- Paired agents do NOT forage (exclusive commitment to trading)
- Single harvester enforcement: only first agent at cell harvests (if enabled)
- Processing in ID order ensures determinism

#### Forage Function (`forage`, lines 59-116)

```python
def forage(agent, grid, forage_rate, current_tick) -> tuple[bool, Optional[str], int]:
    cell = grid.get_cell(agent.pos[0], agent.pos[1])
    
    if cell.resource.amount == 0 or cell.resource.type is None:
        return (False, None, 0)
    
    # Determine harvest amount
    harvest = min(cell.resource.amount, forage_rate)
    good_type = cell.resource.type
    
    # Update agent inventory
    if good_type == "A":
        agent.inventory.A += harvest
    else:  # "B"
        agent.inventory.B += harvest
    
    # Update cell resource
    cell.resource.amount -= harvest
    cell.resource.last_harvested_tick = current_tick  # Reset cooldown timer
    
    # Track for regeneration
    grid.harvested_cells.add(agent.pos)
    
    # Mark inventory changed
    agent.inventory_changed = True
    
    # Break foraging commitment
    if agent.is_foraging_committed:
        agent.is_foraging_committed = False
        agent.forage_target_pos = None
        agent.trade_cooldowns.clear()  # Productive foraging clears frustration
    
    return (True, good_type, harvest)
```

**Foraging Commitment Model:**
- Commitment set in Decision phase when selecting forage target
- Commitment broken when agent harvests successfully
- All trade cooldowns cleared on successful forage (fresh start)

**Resource Depletion Tracking:**
- `cell.resource.last_harvested_tick` set to current tick
- ANY harvest resets cooldown timer (not just full depletion)
- `grid.harvested_cells` set tracks which cells need regeneration

---

### PHASE 6: Resource Regeneration

**Location:** `systems/foraging.py` (`ResourceRegenerationSystem.execute()`)

**Purpose:** Regenerate depleted resources after cooldown period.

**No Protocol Involvement:** Regeneration is deterministic given growth_rate and cooldown.

#### System Implementation

```python
class ResourceRegenerationSystem:
    def execute(self, sim: Simulation) -> None:
        regenerate_resources(
            sim.grid,
            sim.params["resource_growth_rate"],
            sim.params["resource_max_amount"],
            sim.params["resource_regen_cooldown"],
            sim.tick,
        )
```

#### Regeneration Algorithm (`regenerate_resources`, lines 119-204)

**Optimized with Active Set Tracking:**

```python
def regenerate_resources(grid, growth_rate, max_amount, cooldown_ticks, current_tick):
    if growth_rate <= 0:
        return 0
    
    # Bootstrap: scan once if harvested_cells empty but depleted cells exist
    if not grid.harvested_cells:
        for pos, cell in grid.cells.items():
            if (cell.resource.type and 
                cell.resource.last_harvested_tick and
                cell.resource.amount < cell.resource.original_amount):
                grid.harvested_cells.add(pos)
    
    total_regenerated = 0
    cells_to_remove = []
    
    # Only iterate over harvested cells (O(harvested) not O(N²))
    for pos in grid.harvested_cells:
        cell = grid.cells[pos]
        
        # Remove if no resource type
        if cell.resource.type is None:
            cells_to_remove.append(pos)
            continue
        
        # Remove if fully regenerated
        if cell.resource.amount >= cell.resource.original_amount:
            cells_to_remove.append(pos)
            continue
        
        # Remove if never harvested
        if cell.resource.last_harvested_tick is None:
            cells_to_remove.append(pos)
            continue
        
        # Check cooldown
        ticks_since_harvest = current_tick - cell.resource.last_harvested_tick
        if ticks_since_harvest >= cooldown_ticks:
            # Regenerate
            old_amount = cell.resource.amount
            new_amount = min(old_amount + growth_rate, cell.resource.original_amount)
            regenerated = new_amount - old_amount
            
            cell.resource.amount = new_amount
            total_regenerated += regenerated
            
            # Remove if fully regenerated
            if cell.resource.amount >= cell.resource.original_amount:
                cells_to_remove.append(pos)
    
    # Clean up active set
    for pos in cells_to_remove:
        grid.harvested_cells.discard(pos)
    
    return total_regenerated
```

**Key Features:**

1. **Active Set Optimization**
   - Only track cells that have been harvested
   - Complexity: O(harvested_cells) not O(grid_size²)
   - Critical for large grids with sparse harvesting

2. **Cooldown Mechanism**
   - Regeneration only starts after `cooldown_ticks` with no harvesting
   - ANY harvest resets cooldown (even 1 unit)
   - Prevents instant regeneration exploits

3. **Growth Rate**
   - Regenerate `growth_rate` units per tick
   - Cap at `original_amount` (not `max_amount` - per-cell limit)
   - Growth_rate=0 disables regeneration entirely

4. **Active Set Cleanup**
   - Remove cells that are fully regenerated
   - Remove cells with no resource type
   - Keeps active set minimal

---

### PHASE 7: Housekeeping

**Location:** `systems/housekeeping.py` (`HousekeepingSystem.execute()`)

**Purpose:** Refresh quotes, verify pairing integrity, log telemetry.

**No Protocol Involvement:** Administrative tasks.

#### System Implementation

```python
class HousekeepingSystem:
    def execute(self, sim: Simulation) -> None:
        # Refresh quotes for agents whose inventory changed
        money_scale = sim.params["money_scale"]
        exchange_regime = sim.params["exchange_regime"]
        
        for agent in sim.agents:
            refresh_quotes_if_needed(
                agent, 
                sim.params["spread"], 
                sim.params["epsilon"],
                money_scale=money_scale,
                exchange_regime=exchange_regime
            )
        
        # Verify pairing integrity (defensive)
        self._verify_pairing_integrity(sim)
        
        # Log telemetry snapshots
        sim.telemetry.log_agent_snapshots(sim.tick, sim.agents)
        sim.telemetry.log_resource_snapshots(sim.tick, sim.grid)
```

#### Quote Refresh (`refresh_quotes_if_needed`, systems/quotes.py)

**Purpose:** Recompute reservation prices when inventory changes.

**Algorithm:**

```python
def refresh_quotes_if_needed(agent, spread, epsilon, money_scale, exchange_regime):
    if not agent.inventory_changed:
        return  # No change, skip
    
    # Recompute quotes
    agent.quotes = compute_quotes(agent, spread, epsilon, money_scale)
    
    # Reset flag
    agent.inventory_changed = False
```

**`compute_quotes()` (systems/quotes.py):**

**For Barter (A<->B):**
```python
# Calculate MRS (marginal rate of substitution)
MRS_A_B = utility.MRS_A_B(inventory.A, inventory.B)

# Reservation prices with spread
bid_A_in_B = MRS_A_B * (1 + spread)  # Willing to pay
ask_A_in_B = MRS_A_B * (1 - spread)  # Willing to accept

quotes["bid_A_in_B"] = bid_A_in_B
quotes["ask_A_in_B"] = ask_A_in_B
```

**For Money (A<->M, B<->M):**
```python
# Calculate MRS with money
MRS_A_M = utility.MRS_A_M(inventory.A, inventory.M, lambda_money, ...)
MRS_B_M = utility.MRS_B_M(inventory.B, inventory.M, lambda_money, ...)

# Apply money_scale (liquidity adjustment)
MRS_A_M *= money_scale
MRS_B_M *= money_scale

# Reservation prices with spread
quotes["bid_A_in_M"] = MRS_A_M * (1 + spread)
quotes["ask_A_in_M"] = MRS_A_M * (1 - spread)
quotes["bid_B_in_M"] = MRS_B_M * (1 + spread)
quotes["ask_B_in_M"] = MRS_B_M * (1 - spread)
```

**Quote Stability Within Tick:**
- Quotes computed in Housekeeping (end of previous tick)
- Frozen during current tick (all agents see same quotes)
- Refreshed only if inventory changed
- This ensures consistent perception across all agents

#### Pairing Integrity Verification (`_verify_pairing_integrity`, lines 33-45)

**Purpose:** Defensive check for asymmetric pairings (shouldn't happen).

```python
def _verify_pairing_integrity(self, sim: Simulation) -> None:
    for agent in sim.agents:
        if agent.paired_with_id is not None:
            partner_id = agent.paired_with_id
            partner = sim.agent_by_id.get(partner_id)
            
            if partner is None or partner.paired_with_id != agent.id:
                # Asymmetric pairing - repair
                sim.telemetry.log_pairing_event(
                    tick, agent.id, partner_id, "unpair", "integrity_repair"
                )
                agent.paired_with_id = None
```

#### Telemetry Logging

**Agent Snapshots:**
- Position, inventory (A, B, M), utility value, paired_with_id
- Logged once per agent per tick

**Resource Snapshots:**
- Position, type, amount, original_amount, last_harvested_tick
- Logged for all resource cells (not just visible)

**Why End of Tick?**
- Captures final state after all phase effects applied
- Consistent timing for trend analysis
- Next tick's Perception phase sees this state

---

## Protocol → System Data Flow

### Data Flow Diagram

```
TICK START
│
├─ PHASE 1: PERCEPTION
│  │
│  ├─ PerceptionSystem builds perception_cache for each agent
│  │  - neighbors: list[(id, pos)]
│  │  - neighbor_quotes: dict[id → Quote]
│  │  - resource_cells: list[Cell]
│  │
│  └─ Cached in: agent.perception_cache
│
├─ PHASE 2: DECISION
│  │
│  ├─ STEP 2A: SEARCH
│  │  │
│  │  ├─ For each unpaired agent:
│  │  │  │
│  │  │  ├─ Context Builder: build_world_view_for_agent()
│  │  │  │  - Extract from agent.perception_cache
│  │  │  │  - Build AgentView list (frozen snapshots)
│  │  │  │  - Build ResourceView list (with claims)
│  │  │  │  - Build params dict
│  │  │  │  └─ Return frozen WorldView
│  │  │  │
│  │  │  ├─ SearchProtocol.build_preferences(world)
│  │  │  │  - Evaluate visible agents (trade)
│  │  │  │  - Evaluate visible resources (forage)
│  │  │  │  - Apply distance discounting (β^d)
│  │  │  │  - Sort deterministically
│  │  │  │  └─ Return preference list
│  │  │  │
│  │  │  ├─ SearchProtocol.select_target(world)
│  │  │  │  - Choose best trade or forage
│  │  │  │  └─ Return [SetTarget, ClaimResource] effects
│  │  │  │
│  │  │  └─ DecisionSystem._apply_search_effects()
│  │  │     - Set agent.target_pos, agent.target_agent_id
│  │  │     - Update sim.resource_claims
│  │  │     - Set agent.is_foraging_committed
│  │  │
│  │  └─ Store: preferences dict {agent_id → preference_list}
│  │
│  ├─ STEP 2B: MATCHING
│  │  │
│  │  ├─ Context Builder: build_protocol_context(sim)
│  │  │  - Build all_agent_views (global)
│  │  │  - Build all_resource_views (global)
│  │  │  - Extract current_pairings
│  │  │  - Build params with per-agent inventories/utilities
│  │  │  └─ Return ProtocolContext
│  │  │
│  │  ├─ MatchingProtocol.find_matches(preferences, context)
│  │  │  - Filter to trade-seeking agents
│  │  │  - Enumerate potential pairs
│  │  │  - Calculate surpluses via find_all_feasible_trades()
│  │  │  - Apply distance discounting
│  │  │  - Sort by surplus (descending)
│  │  │  - Greedy pairing assignment
│  │  │  └─ Return [Pair(...)] effects
│  │  │
│  │  └─ DecisionSystem._apply_pairing_effects()
│  │     - Set agent_a.paired_with_id = agent_b.id (bidirectional)
│  │     - Update targets to point at each other
│  │     - Clear trade cooldowns
│  │     - Log pairing event to telemetry
│  │
│  └─ STEP 2C: LOG PREFERENCES
│     - If log_preferences enabled
│     - Log each agent's preference rankings
│
├─ PHASE 3: MOVEMENT
│  │
│  ├─ For each agent:
│  │  - Determine target (partner pos if paired, else target_pos)
│  │  - Check if already in interaction range (skip if yes)
│  │  - Check for diagonal deadlock (lower ID waits)
│  │  - Calculate next_step_toward() with tie-breaking
│  │  - Update agent.pos
│  │  - Update spatial_index.update_position()
│  │
│  └─ No protocol involvement
│
├─ PHASE 4: TRADE
│  │
│  ├─ For each paired agent pair (process once):
│  │  │
│  │  ├─ Check distance <= interaction_radius
│  │  │  - If too far: skip (stay paired)
│  │  │  - If in range: negotiate
│  │  │
│  │  ├─ Context Builder: build_trade_world_view(agent_a, agent_b, sim)
│  │  │  - Build base WorldView for agent_a
│  │  │  - Add partner's inventory/utility to params
│  │  │  └─ Return extended WorldView
│  │  │
│  │  ├─ BargainingProtocol.negotiate(pair, world)
│  │  │  - Build pseudo-agents from world
│  │  │  - Call find_all_feasible_trades()
│  │  │    - Enumerate quantities and prices
│  │  │    - Calculate pre/post utilities
│  │  │    - Check feasibility constraints
│  │  │    - Return list of (pair_name, trade_tuple)
│  │  │  - Select best trade (protocol-specific criteria)
│  │  │    - Split-difference: closest to 50/50 surplus split
│  │  │    - Legacy: first feasible trade found
│  │  │  └─ Return [Trade(...)] or [Unpair(...)] effect
│  │  │
│  │  ├─ TradeSystem._apply_trade_effect()
│  │  │  - Determine buyer/seller from trade tuple
│  │  │  - Call execute_trade_generic()
│  │  │    - Update agent inventories (A, B, M)
│  │  │    - Round money to 2 decimals
│  │  │    - Set inventory_changed = True
│  │  │  - Update trade counters
│  │  │  - Log trade to telemetry
│  │  │  - Agents REMAIN PAIRED
│  │  │
│  │  └─ TradeSystem._apply_unpair_effect()
│  │     - Clear paired_with_id (both agents)
│  │     - Set trade cooldowns (10 ticks default)
│  │     - Log unpair event to telemetry
│  │
│  └─ Only if mode in ["trade", "both"]
│
├─ PHASE 5: FORAGE
│  │
│  ├─ For each unpaired agent (sorted by ID):
│  │  - Skip if paired (exclusive commitment)
│  │  - Skip if cell already harvested (if enforce_single_harvester)
│  │  - Call forage(agent, grid, forage_rate, tick)
│  │    - Check cell has resources
│  │    - Harvest min(amount, forage_rate)
│  │    - Update agent inventory
│  │    - Deplete cell resource
│  │    - Set cell.resource.last_harvested_tick = tick
│  │    - Add pos to grid.harvested_cells
│  │    - Set inventory_changed = True
│  │    - Break foraging commitment
│  │    - Clear trade cooldowns
│  │  - Update gathered_resources counter
│  │
│  └─ Only if mode in ["forage", "both"]
│
├─ PHASE 6: RESOURCE REGENERATION
│  │
│  ├─ For each cell in grid.harvested_cells:
│  │  - Skip if no resource type
│  │  - Skip if fully regenerated (remove from active set)
│  │  - Skip if never harvested
│  │  - Calculate ticks_since_harvest
│  │  - If ticks_since_harvest >= cooldown_ticks:
│  │    - Regenerate growth_rate units
│  │    - Cap at original_amount
│  │    - Remove from active set if fully regenerated
│  │
│  └─ Always executes (mode-independent)
│
├─ PHASE 7: HOUSEKEEPING
│  │
│  ├─ For each agent:
│  │  - If inventory_changed:
│  │    - Call compute_quotes(agent, spread, epsilon, money_scale)
│  │      - Calculate MRS (marginal rate of substitution)
│  │      - Apply spread to get bid/ask prices
│  │      - Store in agent.quotes
│  │    - Reset inventory_changed = False
│  │
│  ├─ Verify pairing integrity:
│  │  - Check all pairings are bidirectional
│  │  - Repair asymmetric pairings (log + unpair)
│  │
│  ├─ Log telemetry:
│  │  - log_agent_snapshots(tick, agents)
│  │  - log_resource_snapshots(tick, grid)
│  │
│  └─ Always executes (mode-independent)
│
└─ TICK INCREMENT (tick += 1)
```

---

## Effect Types and Application

### Effect Hierarchy

All effects inherit from `Effect` base class (protocols/base.py:32-45):

```python
@dataclass
class Effect:
    protocol_name: str  # Which protocol generated this
    tick: int           # When it was generated
```

### Effect Types by Phase

**Phase 2 (Decision):**
- `SetTarget(agent_id, target)` - Set agent's movement target
- `ClaimResource(agent_id, pos)` - Claim exclusive harvesting rights
- `ReleaseClaim(pos)` - Release resource claim
- `Pair(agent_a, agent_b, reason)` - Establish bilateral pairing
- `Unpair(agent_a, agent_b, reason)` - Dissolve pairing

**Phase 3 (Movement):**
- `Move(agent_id, dx, dy)` - Displacement vector (NOT CURRENTLY USED - direct mutation)

**Phase 4 (Trade):**
- `Trade(buyer_id, seller_id, pair_type, dA, dB, dM, price, metadata)` - Execute trade
- `Unpair(agent_a, agent_b, reason)` - Failed negotiation

**Phase 5 (Forage):**
- `Harvest(agent_id, pos, amount)` - Harvest resources (NOT CURRENTLY USED - direct mutation)

**Phase 7 (Housekeeping):**
- `RefreshQuotes(agent_id)` - Recompute quotes (NOT CURRENTLY USED - direct function call)
- `SetCooldown(agent_a, agent_b, ticks)` - Trade cooldown (applied in Unpair)

**Multi-Tick State:**
- `InternalStateUpdate(agent_id, key, value)` - Protocol-specific state storage (for future multi-tick protocols)

### Effect Application Pattern

**Declarative Intent:**
```python
# Protocol returns effect (declarative)
effects = protocol.select_target(world)
# → [SetTarget(agent_id=3, target=(10, 15))]
```

**System Validation and Application:**
```python
# System validates and applies effect (imperative)
for effect in effects:
    if isinstance(effect, SetTarget):
        agent = sim.agent_by_id[effect.agent_id]
        agent.target_pos = effect.target
        # ... additional updates ...
```

**Why This Pattern?**
1. **Testability:** Effects are inspectable without side effects
2. **Composability:** Multiple protocols can emit effects, system applies atomically
3. **Auditability:** All state changes traceable to specific effects
4. **Reproducibility:** Effect log can replay simulation deterministically

---

## Determinism Guarantees

### Sources of Non-Determinism (FORBIDDEN)

1. **Unseeded Randomness**
   - ❌ `random.random()` - Python's global unseeded RNG
   - ❌ `numpy.random.rand()` - NumPy's global unseeded RNG
   - ❌ `time.time()` - Clock-based randomness
   - ✅ `sim.rng.random()` - Seeded generator passed to protocols

2. **Unordered Iteration**
   - ❌ `for agent in set(agents)` - Set order is undefined
   - ❌ `for id in dict.keys()` - Dict order is insertion-order in Python 3.7+, but still risky
   - ✅ `for agent in sorted(agents, key=lambda a: a.id)` - Explicit sorting

3. **Float Accumulation**
   - ❌ `money += 0.1` (100 times) ≠ `money = 10.0` due to float precision
   - ✅ `money = round(money, 2)` after each operation
   - ✅ Store money as integers (cents) when possible

4. **Direct State Mutation (Architecture Violation)**
   - ❌ `agent.pos = (5, 5)` in protocol code
   - ✅ `return [SetTarget(agent_id, (5, 5))]` in protocol, system applies

### Verification Mechanisms

1. **Test Suite: `test_foundational_baseline_trades.py`**
   - Runs same scenario with same seed multiple times
   - Asserts identical telemetry snapshots
   - If non-determinism exists, test fails

2. **Telemetry Comparison Script**
   ```bash
   python scripts/compare_telemetry_snapshots.py run1.db run2.db
   ```
   - Compares agent/resource snapshots tick-by-tick
   - Reports first divergence point

3. **Explicit Sorting Everywhere**
   - `for agent in sorted(sim.agents, key=lambda a: a.id)`
   - `for i, agent_a in enumerate(sorted(available_agents))`
   - `candidates.sort(key=lambda x: (-x.score, x.agent_id))`
   - Tie-breaking always uses agent ID or position components

4. **Shared RNG Stream**
   - Single `sim.rng` passed to all protocols via WorldView
   - All random decisions use this generator
   - Seed set in `Simulation.__init__(seed=...)`

---

## Mode System

### Three Modes

1. **"trade"**: Agents only trade (ForageSystem skipped)
2. **"forage"**: Agents only forage (TradeSystem skipped)
3. **"both"**: Agents choose best between trade and forage

### Mode Schedule

**Configuration** (scenario YAML):
```yaml
mode_schedule:
  - [0, 50, "forage"]    # Ticks 0-49: forage only
  - [50, 100, "both"]    # Ticks 50-99: mixed
  - [100, 200, "trade"]  # Ticks 100-199: trade only
```

**Implementation:**
```python
class ModeSchedule:
    def get_mode_at_tick(self, tick: int) -> str:
        for start, end, mode in self.schedule:
            if start <= tick < end:
                return mode
        return "both"  # Default
```

### Mode Transition Handling

**Triggered in:** `Simulation.step()` (lines 329-338)

**Actions on Mode Change:**
1. Log mode change to telemetry
2. Clear ALL pairings (agents need to re-pair in new mode)
3. Clear ALL foraging commitments
4. NO cooldowns imposed (fresh start in new mode)

**Why Clear Pairings?**
- Trade-mode pairing may not be valid in forage-mode
- Prevents agents stuck in invalid state
- Forces agents to re-evaluate targets in new context

### Mode-Aware System Execution

**Always Execute:**
- PerceptionSystem (agents need to observe)
- DecisionSystem (target selection)
- MovementSystem (move toward targets)
- ResourceRegenerationSystem (background process)
- HousekeepingSystem (maintenance)

**Conditionally Execute:**
- TradeSystem: only if `mode in ["trade", "both"]`
- ForageSystem: only if `mode in ["forage", "both"]`

**Decision Phase Behavior:**
- SearchProtocol receives `world.mode` in WorldView
- Protocol builds appropriate preferences:
  - "trade": only trade preferences
  - "forage": only forage preferences
  - "both": both, agent chooses best
- MatchingProtocol only pairs agents with trade preferences

---

## Exchange Regimes

### Four Regimes

1. **"barter_only"**: A<->B trades only
2. **"money_only"**: A<->M and B<->M trades only (no direct barter)
3. **"mixed"**: All three pairs allowed (A<->B, A<->M, B<->M)
4. **"mixed_liquidity_gated"**: Mixed, but money trades preferred when feasible

### Regime Effects on Protocol Behavior

**SearchProtocol (preference building):**
- Barter: Calculate `bid_A_in_B - ask_A_in_B` overlap
- Money: Calculate `bid_A_in_M - ask_A_in_M` and `bid_B_in_M - ask_B_in_M` overlaps
- Mixed: Calculate all three, use best

**MatchingProtocol (surplus calculation):**
- Calls `find_all_feasible_trades(agent_i, agent_j, regime, ...)`
- Function enumerates only allowed pair types based on regime
- Returns list of feasible trades with surpluses

**BargainingProtocol (trade execution):**
- Receives feasible trades filtered by regime
- Selects best trade (protocol-specific criteria)
- Executes chosen trade

### Money-Aware Quotes

**Barter Quotes:**
```python
quotes = {
    "bid_A_in_B": MRS_A_B * (1 + spread),
    "ask_A_in_B": MRS_A_B * (1 - spread),
}
```

**Money Quotes:**
```python
quotes = {
    "bid_A_in_M": MRS_A_M * money_scale * (1 + spread),
    "ask_A_in_M": MRS_A_M * money_scale * (1 - spread),
    "bid_B_in_M": MRS_B_M * money_scale * (1 + spread),
    "ask_B_in_M": MRS_B_M * money_scale * (1 - spread),
}
```

**Money Scale:** Adjusts prices to account for money supply
- Higher money_scale → higher prices
- Ensures prices are in reasonable integer range
- Default: 1 (no scaling)

---

## Critical Implementation Notes

### 1. Paired Agents Remain Paired After Trade

**Design:** Agents do NOT unpair after successful trade.

**Rationale:**
- Allows multiple trades per pairing (efficient)
- Agents can trade until no mutual gains remain
- Unpair only on: failed negotiation, mode change, or cooldown

**Implications:**
- Paired agents skip Search phase (remain committed)
- Paired agents move toward each other until in range
- Paired agents negotiate every tick until unpair

### 2. Foraging Commitment Model

**Commitment Set:** When agent selects forage target in Decision phase
- `agent.is_foraging_committed = True`
- `agent.forage_target_pos = (x, y)`
- Resource claim placed: `resource_claims[pos] = agent_id`

**Commitment Persists:**
- Across ticks (agent skips search while committed)
- Until resource harvested OR resource disappears OR mode changes

**Commitment Broken:**
- Successful harvest: `is_foraging_committed = False` in ForageSystem
- Resource disappears: validated in Decision phase
- Mode change: cleared in `_handle_mode_transition()`

**Why Commitment?**
- Prevents agent "changing mind" mid-journey
- Reduces clustering on same resource
- More realistic behavior (committed foraging trip)

### 3. Trade Cooldown Mechanism

**Purpose:** Prevent infinite pairing loops between incompatible agents.

**Trigger:** Unpair due to failed negotiation
```python
cooldown_until = tick + trade_cooldown_ticks  # Default: 10
agent_a.trade_cooldowns[agent_b_id] = cooldown_until
agent_b.trade_cooldowns[agent_a_id] = cooldown_until
```

**Check:** During Search phase preference building
```python
if neighbor_id in trade_cooldowns:
    if tick < trade_cooldowns[neighbor_id]:
        continue  # Skip this neighbor
```

**Clear:** On successful trade OR successful forage
- Trade: cooldown cleared in `_apply_pairing_effects()` (Pair effect)
- Forage: `trade_cooldowns.clear()` in `forage()`

**Why Cleared on Forage?**
- Inventory changes after forage
- New inventory may make previously incompatible partner compatible
- Fresh start after productive foraging

### 4. Resource Claiming System

**Purpose:** Reduce clustering - prevent multiple agents targeting same resource.

**Feature Flag:** `enable_resource_claiming` (default: False for backward compatibility)

**Claim Placement:** In Decision phase when selecting forage target
```python
sim.resource_claims[resource_pos] = agent_id
```

**Claim Filtering:** In SearchProtocol during forage preference building
```python
available_resources = [r for r in visible_resources 
                       if r.claimed_by_id is None or 
                          r.claimed_by_id == agent.id]
```

**Claim Persistence:** Until commitment breaks (see above)

**Claim Removal:** In Decision phase stale claim cleanup

**Single Harvester Enforcement:** `enforce_single_harvester` (default: False)
- If enabled: only first agent at cell harvests per tick
- Prevents multiple agents harvesting from same cell simultaneously
- Tracked via `harvested_this_tick` set in ForageSystem

### 5. Quote Stability Within Tick

**Principle:** All agent decisions in a tick see the SAME quotes.

**Implementation:**
- Quotes computed in Housekeeping (Phase 7 of previous tick)
- Quotes frozen during Perception (Phase 1)
- Quotes stored in `agent.perception_cache["neighbor_quotes"]`
- Quotes passed to protocols via WorldView (frozen snapshot)
- Quotes only refresh if `inventory_changed` flag set

**Why Important?**
- Agent A and Agent B must see each other's same quotes
- Otherwise: A's decision based on old quotes, B's decision based on new quotes
- Result: inconsistent pairing decisions, potential non-determinism

**Example Violation:**
```python
# BAD: Refresh quotes immediately after trade
execute_trade(agent_i, agent_j)
agent_i.quotes = compute_quotes(agent_i)  # ❌ Changes visible to later agents
```

**Correct:**
```python
# GOOD: Flag for later refresh
execute_trade(agent_i, agent_j)
agent_i.inventory_changed = True  # ✅ Refresh in Housekeeping
```

### 6. Spatial Index for O(N) Perception

**Problem:** Naive neighbor finding is O(N²):
```python
# BAD: O(N²)
for agent in agents:  # N agents
    neighbors = []
    for other in agents:  # Check all N agents
        if distance(agent, other) <= vision_radius:
            neighbors.append(other)
```

**Solution:** Spatial hashing with buckets:
```python
# GOOD: O(N) average
spatial_index.add_agent(agent_id, pos)  # Hash to bucket
neighbors = spatial_index.query_radius(pos, radius)  # Check nearby buckets only
```

**Bucket Size:** `max(vision_radius, interaction_radius)`
- Ensures all visible neighbors in nearby buckets
- Trade-off: larger buckets → more false positives, fewer buckets
- Optimal for uniformly distributed agents

**Maintenance:**
- Add: `spatial_index.add_agent(id, pos)` during initialization
- Update: `spatial_index.update_position(id, new_pos)` during Movement phase
- Remove: NOT IMPLEMENTED (agents never deleted mid-simulation)

### 7. Diagonal Deadlock Resolution

**Problem:**
```
Agent A (id=0) at (0, 0), targets Agent B at (2, 2)
Agent B (id=1) at (2, 2), targets Agent A at (0, 0)

After one move:
A at (1, 1), B at (1, 1)  ❌ Both move to same cell (conflict)
```

**Detection:**
- Both agents target each other (`target_agent_id` mutual)
- Manhattan distance = 2
- Diagonally adjacent (`|dx| == 1 and |dy| == 1`)

**Resolution:**
- Only higher ID agent moves
- Lower ID agent waits

**Example:**
```
Tick 0: A(0,0) → B(2,2), B(2,2) → A(0,0)
Tick 1: A stays (0,0), B moves to (1,2)  [id=1 > id=0]
Tick 2: A(0,0), B(1,2) - no longer diagonal, both can move
Tick 3: Both reach interaction range
```

**Why This Works:**
- Breaks symmetry with deterministic priority
- Agents eventually converge (one moving, one waiting)
- Next tick: no longer diagonal, both can move

---

## Testing and Verification

### Critical Test Files

1. **`test_foundational_baseline_trades.py`**
   - Purpose: Determinism verification
   - Method: Run same scenario multiple times, compare telemetry
   - Scope: Covers all 7 phases with multiple agent interactions

2. **`test_greedy_surplus_matching.py`**
   - Purpose: Protocol interface compliance
   - Verifies: GreedySurplusMatching implements required interface
   - Checks: name, version, find_matches() signature

3. **`test_myopic_search.py`**
   - Purpose: SearchProtocol interface compliance
   - Verifies: LegacySearchProtocol implements required interface
   - Checks: name, version, build_preferences(), select_target()

4. **`test_split_difference.py`**
   - Purpose: BargainingProtocol interface compliance
   - Verifies: SplitDifference implements required interface
   - Checks: name, version, negotiate() signature

### Determinism Verification Script

```bash
python scripts/compare_telemetry_snapshots.py run1.db run2.db
```

**Output:**
- If identical: "Telemetry snapshots match (deterministic)"
- If divergent: "First divergence at tick X, agent Y: field Z"

### Manual Testing Pattern

```python
# Run same scenario twice with same seed
sim1 = Simulation(scenario, seed=42)
sim1.run(100)

sim2 = Simulation(scenario, seed=42)
sim2.run(100)

# Compare final states
assert sim1.agents[0].inventory.A == sim2.agents[0].inventory.A
assert sim1.agents[0].pos == sim2.agents[0].pos
# ... etc
```

---

## Future Protocol Extensions

### Multi-Tick Protocols

**Example:** Rubinstein Alternating Offers Bargaining

**Mechanism:**
1. Tick 1: Agent A makes offer → `[InternalStateUpdate(agent_id, "offer", {...})]`
2. Tick 2: Agent B accepts/rejects → `[Trade(...)]` or `[InternalStateUpdate(agent_id, "counter_offer", {...})]`
3. Tick 3+: Alternate until agreement or timeout

**State Storage:**
```python
protocol_state = {
    "rubinstein_bargaining": {
        3: {  # agent_id
            "round": 2,
            "last_offer": {"dA": 5, "price": 10},
            "history": [...]
        }
    }
}
```

**Accessed via:** `world.protocol_state[protocol_name][agent_id][key]`

### Learning Protocols

**Example:** Reinforcement Learning Search

**Mechanism:**
1. Agent observes: state = (inventory, visible_agents, quotes)
2. Agent selects action: target = policy(state)
3. Agent receives reward: Δutility from trade
4. Agent updates policy: Q(state, action) ← ...

**State Storage:**
```python
protocol_state = {
    "rl_search": {
        3: {  # agent_id
            "Q_table": {...},
            "epsilon": 0.1,
            "history": [...]
        }
    }
}
```

### Market Protocols

**Example:** Decentralized Market with Limit Orders

**Phase Structure:**
1. Decision: Agents post limit orders → `[PostOrder(agent_id, "buy", price, quantity)]`
2. Matching: Market protocol matches orders → `[Trade(...)] effects`
3. Housekeeping: Clear unfilled orders, update order book

**State Storage:**
```python
protocol_state = {
    "decentralized_market": {
        "order_book": {
            "buy": [(price, quantity, agent_id), ...],
            "sell": [(price, quantity, agent_id), ...]
        }
    }
}
```

---

## Appendix: Key Files Reference

### Core Files

- `simulation.py`: Main orchestrator, step function (lines 321-355)
- `core/agent.py`: Agent state class
- `core/grid.py`: Grid and resource management
- `core/spatial_index.py`: O(N) proximity queries
- `core/state.py`: Position, Inventory, Quote, Cell types

### System Files

- `systems/perception.py`: Phase 1 - build perception cache
- `systems/decision.py`: Phase 2 - search + matching orchestration
- `systems/movement.py`: Phase 3 - pathfinding
- `systems/trading.py`: Phase 4 - bargaining orchestration
- `systems/foraging.py`: Phase 5 - harvesting + Phase 6 - regeneration
- `systems/housekeeping.py`: Phase 7 - maintenance
- `systems/matching.py`: Helper functions (surplus, feasible trades)
- `systems/quotes.py`: Quote computation

### Protocol Files

- `protocols/base.py`: Effect types, protocol interfaces
- `protocols/context.py`: WorldView, ProtocolContext, AgentView, ResourceView
- `protocols/context_builders.py`: Factory functions for contexts
- `protocols/registry.py`: Protocol registration system
- `protocols/search/legacy.py`: LegacySearchProtocol implementation
- `protocols/search/myopic.py`: MyopicSearch implementation
- `protocols/search/random_walk.py`: RandomWalkSearch implementation
- `protocols/matching/legacy.py`: LegacyThreePassMatching implementation
- `protocols/matching/greedy.py`: GreedySurplusMatching implementation
- `protocols/matching/random.py`: RandomMatching implementation
- `protocols/bargaining/legacy.py`: LegacyCompensatingBlocks implementation
- `protocols/bargaining/split_difference.py`: SplitDifference implementation
- `protocols/bargaining/take_it_or_leave_it.py`: TakeItOrLeaveIt implementation

### Test Files (Protocol Compliance)

- `tests/test_greedy_surplus_matching.py`
- `tests/test_myopic_search.py`
- `tests/test_random_matching.py`
- `tests/test_random_walk_search.py`
- `tests/test_split_difference.py`
- `tests/test_take_it_or_leave_it_bargaining.py`

### Test Files (Determinism)

- `tests/test_foundational_baseline_trades.py`
- `tests/test_barter_integration.py`
- `tests/test_mixed_regime_integration.py`

---

## Conclusion

The VMT simulation engine implements a rigorous 7-phase tick cycle with clean separation between infrastructure (Systems) and domain logic (Protocols). The Protocol → Effect → State pattern ensures:

1. **Determinism:** All randomness seeded, all iteration ordered, all state changes auditable
2. **Testability:** Protocols return inspectable effects without side effects
3. **Extensibility:** New protocols plug in without modifying core systems
4. **Clarity:** Each phase has a single responsibility, data flow is explicit

This architecture supports rigorous economic research by ensuring that results are reproducible, mechanisms are composable, and behaviors are traceable to specific protocol implementations.

