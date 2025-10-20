# Final Trade Pairing Implementation Plan
## Hybrid Approach: Mutual Consent + Best-Available Fallback

**Version:** 2025-10-20  
**Status:** Design Specification  
**Approach:** Option 4 - Hybrid mutual-first with ranked fallback

---

## Executive Summary

This document specifies the **trade pairing mechanism** for VMT's Decision Phase. The mechanism uses a **three-pass algorithm**:

1. **Pass 1:** Target selection - each agent independently evaluates neighbors and builds ranked preference list
2. **Pass 2:** Mutual consent pairing - establish pairings where preferences are bidirectional
3. **Pass 3:** Best-available fallback - unpaired agents claim their highest-ranked available partner

This approach maximizes trade opportunities while preserving economic rationality and determinism.

---

## Core Design Principles

### 1. Economic Rationality
- Agents should trade whenever mutually beneficial opportunities exist
- Preference cycles (A→B→C→A) should not block all trades
- Agents use full information from their ranked preference list

### 2. Determinism
- All agent iterations follow ID order
- Tie-breaking uses lowest ID when surplus values are equal
- Preference ranking is deterministic (surplus-based with ID tiebreak)

### 3. Pairing Semantics
- **Mutual pairings:** Both agents prefer each other (strongest commitment)
- **Fallback pairings:** Agent claims available partner from ranked list (practical commitment)
- Once paired, both agents commit regardless of whether pairing was mutual or fallback
- Paired agents move toward each other and attempt trade exclusively
- **Important:** Paired agents continue building preference lists each tick for telemetry/analysis but do not act on them

**Potential problematic behavior (documented):**
- Agents can commit to distant partners and spend many ticks moving toward them
- During this movement period, they ignore all other trading and foraging opportunities
- Once paired, agents execute multiple trades (until opportunities exhausted) before unpairing
- This is by design (commitment model) but may appear suboptimal in some scenarios
- Educational value: demonstrates opportunity cost of commitment decisions and iterative trade

### 4. Performance
- Target: O(N) complexity for decision phase (down from O(N²) in current all-pairs matching)
- Three passes over N agents: O(3N) = O(N)
- Preference list size bounded by vision_radius (typically 5-20 neighbors)

---

## Data Structures

### Agent State (new fields)

```python
@dataclass
class Agent:
    # ... existing fields ...
    
    # NEW: Pairing state
    paired_with_id: Optional[int] = field(default=None, repr=False)
    
    # INTERNAL: Decision context (cleared each tick)
    _preference_list: list[tuple[int, float]] = field(default_factory=list, repr=False)
    _decision_target_type: Optional[str] = field(default=None, repr=False)
```

**Field descriptions:**

- `paired_with_id`: Current trade partner (None if unpaired). Persists across ticks until unpaired.
- `_preference_list`: Ranked list of `(neighbor_id, surplus)` tuples, sorted by `(-surplus, neighbor_id)`. Built in Pass 1, used in Pass 3. Cleared at start of each decision phase.
- `_decision_target_type`: For logging - "trade", "forage", "idle", etc.

### Simulation State (new field)

No new Simulation fields needed. Pairing state lives entirely on agents.

---

## Three-Pass Algorithm

### Pass 1: Target Selection & Preference Ranking

**Purpose:** Each agent independently evaluates all visible neighbors and builds a ranked preference list.

**For each agent (sorted by ID):**

```python
def _pass1_target_selection(self, sim: Simulation) -> None:
    """Pass 1: Each agent builds ranked preference list and selects primary target."""
    
    for agent in sorted(sim.agents, key=lambda a: a.id):
        # Clear stale decision context
        agent._preference_list = []
        agent._decision_target_type = None
        
        view = agent.perception_cache
        
        # Case 1: Agent is already paired
        if agent.paired_with_id is not None:
            self._handle_paired_agent_pass1(agent, sim)
            continue
        
        # Case 2: Trade mode - evaluate trade opportunities
        if sim.current_mode in ("trade", "both"):
            self._evaluate_trade_preferences(agent, view, sim)
        
        # Case 3: Mixed mode with no trade target - fall back to forage
        if sim.current_mode == "both" and agent.target_agent_id is None:
            self._evaluate_forage_target(agent, view, sim)
        
        # Case 4: Pure forage mode
        if sim.current_mode == "forage":
            self._evaluate_forage_target(agent, view, sim)
```

#### Handling Paired Agents (Pass 1)

```python
def _handle_paired_agent_pass1(self, agent: Agent, sim: Simulation) -> None:
    """Validate existing pairing and maintain target lock."""
    partner_id = agent.paired_with_id
    partner = sim.agent_by_id.get(partner_id)
    
    # Defensive integrity check
    if partner is None or partner.paired_with_id != agent.id:
        # Pairing corrupted - log and clear
        sim.telemetry.log_pairing_event(
            sim.tick, agent.id, partner_id, "unpair", "corruption_detected"
        )
        agent.paired_with_id = None
        # Fall through to unpaired logic (will be processed in Pass 2)
        return
    
    # Valid pairing: lock target to partner
    agent.target_pos = partner.pos
    agent.target_agent_id = partner_id
    agent._decision_target_type = "trade_paired"
    
    # Paired agents STILL build preference lists for telemetry/analysis
    # But they maintain exclusive commitment (don't act on preferences)
    view = agent.perception_cache
    self._evaluate_trade_preferences(agent, view, sim)
```

#### Evaluating Trade Preferences (Pass 1)

```python
def _evaluate_trade_preferences(self, agent: Agent, view: dict, sim: Simulation) -> None:
    """Build ranked preference list and select primary trade target.
    
    Two-stage filtering:
    1. Neighbors must be within vision_radius (perception filter)
    2. Rank by distance-discounted surplus using beta discount factor
    """
    neighbors = view.get("neighbors", [])  # Already filtered by vision_radius in Perception
    beta = sim.params.get("beta", 0.95)  # Same discount factor as foraging
    
    # Build ranked list of all neighbors with positive surplus
    candidates = []
    for neighbor_id, neighbor_pos in neighbors:
        if neighbor_id not in sim.agent_by_id:
            continue
        
        # Check cooldown
        if neighbor_id in agent.trade_cooldowns:
            if sim.tick < agent.trade_cooldowns[neighbor_id]:
                continue  # Still in cooldown
            else:
                # Cooldown expired, remove
                del agent.trade_cooldowns[neighbor_id]
        
        neighbor = sim.agent_by_id[neighbor_id]
        surplus = compute_surplus(agent, neighbor)
        
        if surplus > 0:
            # Compute distance for discounting
            distance = abs(agent.pos[0] - neighbor_pos[0]) + abs(agent.pos[1] - neighbor_pos[1])
            
            # Beta-discounted surplus: surplus × β^distance
            # Treats distance as "time" (number of steps to reach partner)
            # Same discounting approach as foraging for consistency
            discounted_surplus = surplus * (beta ** distance)
            
            candidates.append((neighbor_id, surplus, discounted_surplus, distance))
    
    # Sort by (-discounted_surplus, neighbor_id) for deterministic ranking
    # Negative discounted_surplus for descending order, ID for tiebreaking
    candidates.sort(key=lambda x: (-x[2], x[0]))
    
    # Store ranked preference list (full info for telemetry)
    agent._preference_list = candidates
    
    # Set primary target (top of list) - only if agent is unpaired
    if candidates and agent.paired_with_id is None:
        best_partner_id, best_surplus, best_discounted, best_dist = candidates[0]
        partner = sim.agent_by_id[best_partner_id]
        agent.target_pos = partner.pos
        agent.target_agent_id = best_partner_id
        agent._decision_target_type = "trade"
    elif not candidates and agent.paired_with_id is None:
        agent.target_pos = None
        agent.target_agent_id = None
        agent._decision_target_type = "idle"
    # Else: paired agents keep their existing target
```

#### Evaluating Forage Targets (Pass 1)

```python
def _evaluate_forage_target(self, agent: Agent, view: dict, sim: Simulation) -> None:
    """Choose forage target from available resources."""
    resource_cells = view.get("resource_cells", [])
    
    # Filter claimed resources
    available = self._filter_claimed_resources(resource_cells, sim, agent.id)
    
    # Choose best resource
    target = choose_forage_target(
        agent, available, sim.params["beta"], sim.params["forage_rate"]
    )
    
    # Claim resource and set target
    if target is not None:
        self._claim_resource(sim, agent.id, target)
        agent.target_pos = target
        agent.target_agent_id = None
        agent._decision_target_type = "forage"
    else:
        agent.target_pos = None
        agent.target_agent_id = None
        agent._decision_target_type = "idle"
```

---

### Pass 2: Mutual Consent Pairing

**Purpose:** Detect and establish pairings where both agents list each other as their top preference.

```python
def _pass2_mutual_consent(self, sim: Simulation) -> None:
    """Pass 2: Establish pairings where both agents mutually prefer each other."""
    
    for agent in sorted(sim.agents, key=lambda a: a.id):
        # Skip already-paired agents
        if agent.paired_with_id is not None:
            continue
        
        # Skip agents without trade targets
        if agent.target_agent_id is None:
            continue
        
        partner_id = agent.target_agent_id
        partner = sim.agent_by_id[partner_id]
        
        # Check for mutual consent using CURRENT TICK data
        # Both agents must:
        # 1. Have each other as primary target (target_agent_id)
        # 2. Be unpaired
        if (partner.target_agent_id == agent.id and 
            partner.paired_with_id is None):
            
            # MUTUAL CONSENT DETECTED
            # Process pairing only once (lower ID does the work)
            if agent.id < partner_id:
                agent.paired_with_id = partner_id
                partner.paired_with_id = agent.id
                
                # Clear mutual cooldowns
                agent.trade_cooldowns.pop(partner_id, None)
                partner.trade_cooldowns.pop(agent.id, None)
                
                # Get both agents' surpluses for logging
                surplus_i = compute_surplus(agent, partner)
                surplus_j = compute_surplus(partner, agent)
                
                # Log pairing event
                sim.telemetry.log_pairing_event(
                    sim.tick, agent.id, partner_id, "pair", "mutual_consent",
                    surplus_i, surplus_j
                )
```

**Key properties:**
- Only unpaired agents participate
- Uses `target_agent_id` set in Pass 1 (same tick, fresh data)
- Bidirectional check ensures true mutual preference
- Lower-ID agent executes pairing to avoid duplication

---

### Pass 3: Best-Available Fallback (Surplus-Based Greedy)

**Purpose:** Unpaired agents with remaining preferences claim their highest-ranked available partner using surplus-based greedy matching.

```python
def _pass3_best_available_fallback(self, sim: Simulation) -> None:
    """Pass 3: Surplus-based greedy matching for unpaired agents.
    
    Collect all (agent, partner, discounted_surplus) tuples and process
    in descending surplus order to maximize total welfare.
    """
    # Collect all potential pairings with their discounted surplus
    potential_pairings = []
    
    for agent in sim.agents:
        # Skip already-paired agents
        if agent.paired_with_id is not None:
            continue
        
        # Skip agents with no preferences
        if not agent._preference_list:
            continue
        
        # Add all preferences to potential pairing list
        for rank, (partner_id, surplus, discounted_surplus, distance) in enumerate(agent._preference_list):
            partner = sim.agent_by_id[partner_id]
            
            # Only consider if partner is unpaired
            if partner.paired_with_id is None:
                potential_pairings.append((
                    discounted_surplus,  # Primary sort key
                    agent.id,            # Secondary: lower ID tiebreak
                    partner_id,          # Tertiary: lower partner ID
                    rank,                # For logging
                    surplus              # Undiscounted surplus for logging
                ))
    
    # Sort by (-discounted_surplus, agent_id, partner_id) for welfare-maximizing greedy
    potential_pairings.sort(key=lambda x: (-x[0], x[1], x[2]))
    
    # Greedily assign pairs
    for discounted_surplus, agent_id, partner_id, rank, surplus in potential_pairings:
        agent = sim.agent_by_id[agent_id]
        partner = sim.agent_by_id[partner_id]
        
        # Check if both are still available (may have been claimed earlier)
        if agent.paired_with_id is None and partner.paired_with_id is None:
            # CLAIM PARTNER (fallback pairing)
            agent.paired_with_id = partner_id
            partner.paired_with_id = agent.id
            
            # Update targets for both agents
            agent.target_pos = partner.pos
            agent.target_agent_id = partner_id
            partner.target_pos = agent.pos  # Partner now targets claimer
            partner.target_agent_id = agent.id
            
            # Clear mutual cooldowns
            agent.trade_cooldowns.pop(partner_id, None)
            partner.trade_cooldowns.pop(agent.id, None)
            
            # Get both agents' surpluses for logging
            surplus_i = surplus  # Already computed for this agent
            surplus_j = compute_surplus(partner, agent)
            
            # Log pairing event with rank and surplus information
            sim.telemetry.log_pairing_event(
                sim.tick, agent_id, partner_id, "pair", 
                f"fallback_rank_{rank}_surplus_{discounted_surplus:.4f}", 
                surplus_i, surplus_j
            )
```

**Key properties:**
- **Welfare-maximizing:** Processes pairings in descending discounted-surplus order
- **Deterministic:** ID-based tiebreaking when surplus values are equal
- Agents can claim any available partner from their preference list
- Partner's target is updated to point back at claimer
- Both agents commit once paired (no rejection mechanism)
- Rank indicates where partner appeared in agent's preference list

**Example scenario (surplus-based greedy with β=0.95):**
```
Agent A (ID=1): preference_list = [(3, 1.0, 0.95, 1), (2, 0.8, 0.76, 1)]
                                   (id, surplus, surplus×β^d, distance)
Agent B (ID=2): preference_list = [(3, 1.2, 1.14, 1)]  
Agent C (ID=3): preference_list = [(2, 0.9, 0.855, 1)]

Pass 2 (mutual): No mutual pairs
Pass 3:
  Sorted potential pairings:
    1. B→C (discounted_surplus=1.14)
    2. A→C (discounted_surplus=0.95)
    3. C→B (discounted_surplus=0.855)  
    4. A→B (discounted_surplus=0.76)
  
  Greedy assignment:
    - B→C pair (highest surplus) → B-C paired
    - C→B skipped (both already paired)
    - A→C skipped (C already paired)
    - A→B skipped (B already paired)
  
Result: B-C trade (highest surplus), A unpaired
```

**Key improvement over ID-based:** This resolves the three-way cycle optimally by pairing the highest-surplus pair first.

---

### Pass 4: Decision Logging

**Purpose:** Log final decision state for all agents with complete pairing context.

```python
def _pass4_log_decisions(self, sim: Simulation) -> None:
    """Pass 4: Log all agent decisions with final pairing status."""
    
    for agent in sorted(sim.agents, key=lambda a: a.id):
        view = agent.perception_cache
        neighbors = view.get("neighbors", [])
        
        # Determine decision type
        if agent.paired_with_id is not None:
            decision_type = "trade_paired"
            partner_id = agent.paired_with_id
            
            # Get surplus from preference list if available
            surplus = None
            for pid, s, ds, d in agent._preference_list:
                if pid == partner_id:
                    surplus = s
                    break
        
        elif agent._decision_target_type == "trade":
            decision_type = "trade_unpaired"
            partner_id = agent.target_agent_id
            surplus = agent._preference_list[0][1] if agent._preference_list else None
        
        else:
            decision_type = agent._decision_target_type or "idle"
            partner_id = None
            surplus = None
        
        # Log decision (without alternatives - now in separate table)
        target_x = agent.target_pos[0] if agent.target_pos else None
        target_y = agent.target_pos[1] if agent.target_pos else None
        
        sim.telemetry.log_decision(
            sim.tick, agent.id, partner_id, surplus,
            decision_type, target_x, target_y, len(neighbors),
            mode=sim.current_mode,
            is_paired=(agent.paired_with_id is not None)
        )
        
        # Log preferences to separate table
        if agent._preference_list:
            # Determine how many preferences to log
            log_full = sim.params.get("log_full_preferences", False)
            max_prefs = len(agent._preference_list) if log_full else min(3, len(agent._preference_list))
            
            for rank, (pid, surplus, discounted_surplus, distance) in enumerate(agent._preference_list[:max_prefs]):
                sim.telemetry.log_preference(
                    sim.tick, agent.id, pid, rank, surplus, 
                    discounted_surplus, distance
                )
        
        # Clear temporary decision context
        agent._preference_list = []
        agent._decision_target_type = None
```

---

## Movement Phase Integration

Paired agents move toward their paired partner, ignoring other targets:

```python
# In MovementSystem.execute()
for agent in sorted(sim.agents, key=lambda a: a.id):
    if agent.paired_with_id is not None:
        # Paired agents move toward partner
        partner = sim.agent_by_id[agent.paired_with_id]
        target_pos = partner.pos
    else:
        target_pos = agent.target_pos
    
    # Move toward target (existing logic)
    if target_pos is not None:
        move_toward_target(agent, target_pos, sim.grid, sim.params)
```

---

## Trade Phase Integration

### Pre-Trade Pairing Check

Only paired agents within interaction radius execute trades:

```python
# In TradeSystem.execute()
def execute(self, sim: Simulation) -> None:
    # Process ONLY paired agents
    processed_pairs = set()
    
    for agent in sorted(sim.agents, key=lambda a: a.id):
        if agent.paired_with_id is None:
            continue
        
        partner_id = agent.paired_with_id
        
        # Skip if pair already processed
        pair_key = tuple(sorted([agent.id, partner_id]))
        if pair_key in processed_pairs:
            continue
        processed_pairs.add(pair_key)
        
        partner = sim.agent_by_id[partner_id]
        
        # Check distance
        distance = abs(agent.pos[0] - partner.pos[0]) + abs(agent.pos[1] - partner.pos[1])
        
        if distance <= sim.params["interaction_radius"]:
            # Attempt trade
            if sim.params.get("exchange_regime", "barter_only") in ("money_only", "mixed"):
                self._trade_generic(agent, partner, sim)
            else:
                trade_pair(agent, partner, sim.params, sim.telemetry, sim.tick)
        # else: Too far apart, stay paired and keep moving
```

### Trade Success/Failure Handling

```python
def trade_pair(agent_i, agent_j, params, telemetry, tick):
    """Execute trade between paired agents."""
    result = find_compensating_block(agent_i, agent_j, params)
    
    if result is None:
        # Trade failed - no mutually beneficial trade exists
        # This means trade opportunities are exhausted → unpair and set cooldown
        agent_i.paired_with_id = None
        agent_j.paired_with_id = None
        
        cooldown_until = tick + params.get('trade_cooldown_ticks', 10)
        agent_i.trade_cooldowns[agent_j.id] = cooldown_until
        agent_j.trade_cooldowns[agent_i.id] = cooldown_until
        
        # Log unpair event
        telemetry.log_pairing_event(
            tick, agent_i.id, agent_j.id, "unpair", "trade_failed"
        )
        return
    
    # Trade succeeded
    execute_trade(agent_i, agent_j, result)
    
    # Log trade success
    # Note: Agents REMAIN PAIRED after successful trade
    # They will attempt another trade next tick if still within interaction_radius
    # This continues until trade attempt fails (opportunities exhausted)
    telemetry.log_trade_success(tick, agent_i.id, agent_j.id, result)
```

**Key insight:** Paired agents remain paired across multiple ticks, executing repeated trades until opportunities are exhausted (trade attempt fails). This is critical for the O(N) performance benefit.

---

## Forage Phase Integration

Paired agents do NOT forage:

```python
# In ForageSystem.execute()
def execute(self, sim: Simulation) -> None:
    for agent in sorted(sim.agents, key=lambda a: a.id):
        # Skip paired agents (exclusive commitment)
        if agent.paired_with_id is not None:
            continue
        
        # Existing forage logic
        if agent.pos == agent.target_pos:
            self._harvest_resource(agent, sim)
```

---

## Housekeeping Phase Integration

### Pairing Integrity Checks

```python
# In HousekeepingSystem.execute()
def execute(self, sim: Simulation) -> None:
    # ... existing quote refresh logic ...
    
    # Verify pairing integrity
    self._verify_pairing_integrity(sim)

def _verify_pairing_integrity(self, sim: Simulation) -> None:
    """Defensive check: ensure all pairings are bidirectional."""
    for agent in sim.agents:
        if agent.paired_with_id is not None:
            partner_id = agent.paired_with_id
            partner = sim.agent_by_id.get(partner_id)
            
            if partner is None or partner.paired_with_id != agent.id:
                # Asymmetric pairing - repair
                sim.telemetry.log_pairing_event(
                    sim.tick, agent.id, partner_id, "unpair", "integrity_repair"
                )
                agent.paired_with_id = None
```

---

## Mode Management Integration

### Mode Switch Behavior

When `current_mode` changes, all pairings are cleared:

```python
# In Simulation.set_mode() or mode switching logic
def _clear_pairings_on_mode_switch(self, old_mode: str, new_mode: str) -> None:
    """Clear all pairings when mode changes."""
    if old_mode == new_mode:
        return
    
    # Log unpair events for all paired agents
    for agent in self.agents:
        if agent.paired_with_id is not None:
            # Only log once per pair (lower ID does it)
            if agent.id < agent.paired_with_id:
                self.telemetry.log_pairing_event(
                    self.tick, agent.id, agent.paired_with_id,
                    "unpair", f"mode_switch_{old_mode}_to_{new_mode}"
                )
            agent.paired_with_id = None
```

**Design decision:** No cooldowns on mode-switch unpairings (they can re-pair immediately when mode switches back).

---

## Telemetry Schema Updates

### Modified `decisions` Table

```python
# In TelemetryDatabase.create_schema()
CREATE TABLE decisions (
    tick INTEGER,
    agent_id INTEGER,
    partner_id INTEGER,      # Target or paired partner
    expected_surplus REAL,
    decision TEXT,           # "trade_paired", "trade_unpaired", "forage", "idle"
    target_x INTEGER,
    target_y INTEGER,
    num_neighbors INTEGER,
    mode TEXT,
    is_paired INTEGER,       # NEW: 1 if agent.paired_with_id is not None
    PRIMARY KEY (tick, agent_id)
)
```

**Note:** Removed `alternatives` column - now tracked in separate `preferences` table.

### New Table: `pairings`

```python
CREATE TABLE pairings (
    tick INTEGER,
    agent_i INTEGER,
    agent_j INTEGER,
    event TEXT,              # "pair" or "unpair"
    reason TEXT,             # "mutual_consent", "fallback_rank_0_surplus_0.6000", "trade_failed", etc.
    surplus_i REAL,          # Agent i's undiscounted surplus with agent j (NULL for unpair)
    surplus_j REAL,          # Agent j's undiscounted surplus with agent i (NULL for unpair)
    PRIMARY KEY (tick, agent_i, agent_j, event)
)
```

**Note:** Both surpluses logged for complete information, especially useful for analyzing mutual vs fallback pairings.

### New Table: `preferences`

```python
CREATE TABLE preferences (
    tick INTEGER,
    agent_id INTEGER,
    partner_id INTEGER,
    rank INTEGER,                    # 0 = top choice, 1 = second choice, etc.
    surplus REAL,                    # Undiscounted surplus
    discounted_surplus REAL,         # Distance-discounted surplus used for ranking
    distance INTEGER,                # Manhattan distance to partner
    PRIMARY KEY (tick, agent_id, partner_id)
)
```

**Purpose:** Captures top-ranked preferences (default: top 3, configurable to full list), enabling detailed analysis of:
- How often agents get their top choice vs fallback options
- Impact of distance discounting on pairing outcomes
- Counterfactual analysis for decision-relevant alternatives
- Market thickness and competition metrics

**Configuration:**
- Default: Logs top 3 preferences per agent per tick
- With `log_full_preferences: True`: Logs all positive-surplus preferences
- Estimated size (default, 1000 agents, 1000 ticks): ~3M rows (~1.5 GB)
- Estimated size (full logging, 15 avg neighbors): ~15M rows (~7.5 GB)

**Logging example:**
```python
# Pairing event (mutual consent)
telemetry.log_pairing_event(
    tick=15, agent_i=3, agent_j=7, event="pair", 
    reason="mutual_consent", surplus_i=0.85, surplus_j=0.92
)

# Pairing event (fallback)
telemetry.log_pairing_event(
    tick=15, agent_i=3, agent_j=7, event="pair", 
    reason="fallback_rank_1_surplus_0.6500", surplus_i=0.85, surplus_j=0.45
)

# Unpair event (trade failed - opportunities exhausted)
telemetry.log_pairing_event(
    tick=18, agent_i=3, agent_j=7, event="unpair",
    reason="trade_failed", surplus_i=None, surplus_j=None
)

# Preference logging (for each agent each tick)
telemetry.log_preference(
    tick=15, agent_id=3, partner_id=7, rank=0, 
    surplus=0.85, discounted_surplus=0.425, distance=2
)
telemetry.log_preference(
    tick=15, agent_id=3, partner_id=12, rank=1,
    surplus=0.75, discounted_surplus=0.375, distance=2
)
```

---

## Edge Cases & Invariants

### Edge Case 1: Three-Way Cycle
```
Agent A: preferences = [(B, 0.8, 0.76, 1), (C, 0.6, 0.57, 1)]  # β=0.95
Agent B: preferences = [(C, 1.0, 0.95, 1)]
Agent C: preferences = [(A, 0.9, 0.855, 1), (B, 0.7, 0.665, 1)]

Pass 2: No mutual pairs
Pass 3 (surplus-based greedy):
  Sorted potential pairings:
    1. B→C (discounted_surplus=0.95)
    2. C→A (discounted_surplus=0.855)
    3. A→B (discounted_surplus=0.76)
    4. C→B (discounted_surplus=0.665)
    5. A→C (discounted_surplus=0.57)
  
  Greedy assignment:
    - B→C pair (highest surplus) → B-C paired
    - All others skipped (agents already paired)

Result: B-C trade (optimal), A unpaired
```

**Resolution:** Surplus-based greedy matching breaks cycles optimally by selecting highest-surplus pair first.

### Edge Case 2: Asymmetric Preferences with High Rank

```
Agent A: preferences = [(B, 1.5, 1.425, 1), (C, 1.2, 1.14, 1), (D, 0.8, 0.76, 1)]  # β=0.95
Agent B: preferences = [(C, 1.0, 0.95, 1)]
Agent C: preferences = [(D, 0.9, 0.855, 1)]
Agent D: preferences = [(A, 0.7, 0.665, 1)]

Pass 2: No mutual pairs
Pass 3 (surplus-based greedy):
  Sorted potential pairings:
    1. A→B (discounted_surplus=1.425)  # Highest
    2. A→C (discounted_surplus=1.14)
    3. B→C (discounted_surplus=0.95)
    4. C→D (discounted_surplus=0.855)
    5. A→D (discounted_surplus=0.76)
    6. D→A (discounted_surplus=0.665)
  
  Greedy assignment:
    - A→B pair → A-B paired
    - C→D pair → C-D paired (B and A already claimed)

Result: Two trades (A-B, C-D) - welfare-maximizing
```

### Edge Case 3: Pairing with Cooldown Partner

```
Tick 20: A-B trade fails, cooldown until tick 30
Tick 25: A and B both choose each other as top preference
  → Pass 2: Mutual consent detected
  → BUT: choose_partner in Pass 1 should have filtered B from A's list
  → This case CANNOT occur (cooldown prevents preference formation)
```

**Invariant:** Cooldown filtering in Pass 1 prevents pairing with cooled-down partners.

### Edge Case 4: Partner Dies/Removed Mid-Pairing

```
Tick 10: A-B paired
Tick 11 (before Decision): Agent B removed from simulation
Pass 1: A's pairing validation detects partner missing
  → A unpaired, falls through to normal evaluation
```

**Defensive handling in Pass 1 validation prevents crashes.**

### Edge Case 5: Distant Pairing

```
Tick 10: A-B paired, distance = 1
Tick 11: Mode switches to forage, pairings cleared
Ticks 12-20: Agents wander apart (distance now 15)
Tick 21: Mode switches back to trade
Pass 1: Both agents have positive surplus with each other
Pass 2: Mutual consent → A-B re-paired
Ticks 22-36: They move toward each other (15 ticks at speed 1)
Tick 37: Within interaction_radius → trade executes

Implications:
  - 15 ticks of movement with no other opportunities
  - Both agents ignore foraging during this time
```

**Design decision:** Acceptable. Agents commit to their decision. Could add max-distance check in Pass 2 if this becomes problematic.

---

## Testing Requirements

### Unit Tests

#### Test 1: Mutual Consent Basic
```python
def test_mutual_consent_pairing():
    """Two agents with mutual top preference pair in Pass 2."""
    # Setup: A wants B (surplus 1.0), B wants A (surplus 0.9)
    # Expected: A-B paired via mutual_consent
    # Both agents log as trade_paired
```

#### Test 2: Fallback Pairing
```python
def test_fallback_pairing_rank_0():
    """Agent claims top-preference partner who didn't reciprocate."""
    # Setup: A wants B (surplus 1.0), B wants C (surplus 1.2)
    # Expected: A-B paired via fallback_rank_0 (A claims B)
```

#### Test 3: Fallback with Lower Rank
```python
def test_fallback_pairing_rank_1():
    """Agent claims second choice when first is unavailable."""
    # Setup: A prefs [(B, 1.0), (C, 0.8)], B prefs [(C, 1.2)]
    # After B-C pair, A claims next available
    # Expected: Depends on C's availability
```

#### Test 4: Three-Way Cycle Resolution
```python
def test_three_way_cycle():
    """Deterministic resolution of A→B→C→A cycle."""
    # Setup: A wants B, B wants C, C wants A (all positive surplus)
    # Expected: Highest-surplus pair forms (welfare-maximizing)
```

#### Test 5: Cooldown Prevents Pairing
```python
def test_cooldown_blocks_fallback():
    """Agents with active cooldown don't pair."""
    # Setup: A-B cooldown until tick 30, both choose each other at tick 25
    # Expected: No pairing (cooldown filters preferences in Pass 1)
```

#### Test 6: Pairing Validation in Pass 1
```python
def test_pairing_corruption_detected():
    """Asymmetric pairing is detected and repaired."""
    # Setup: Manually corrupt state (A.paired_with = B, B.paired_with = None)
    # Expected: Pass 1 detects, logs corruption, clears A's pairing
```

#### Test 7: Mode Switch Unpairs
```python
def test_mode_switch_clears_pairings():
    """Mode change unpairs all agents."""
    # Setup: A-B paired in trade mode, switch to forage
    # Expected: Both unpaired, no cooldown set
```

#### Test 8: Trade Success Maintains Pairing
```python
def test_trade_success_maintains_pairing():
    """Successful trade keeps agents paired for subsequent trades."""
    # Setup: A-B paired and adjacent, trade succeeds
    # Expected: Both remain paired, no cooldown
    # Next tick: They attempt another trade
```

#### Test 9: Trade Failure Unpairs with Cooldown
```python
def test_trade_failure_unpairs_with_cooldown():
    """Failed trade clears pairing and sets cooldown."""
    # Setup: A-B paired and adjacent, trade fails (no valid block)
    # Expected: Both unpaired, cooldown set for 10 ticks
```

#### Test 10: Paired Agents Don't Forage
```python
def test_paired_agents_skip_forage():
    """Paired agents on resource don't harvest."""
    # Setup: A-B paired, A standing on resource cell
    # Expected: A doesn't harvest (committed to trading)
```

### Integration Tests

#### Test 11: Full Cycle Test
```python
def test_full_pairing_lifecycle():
    """Complete lifecycle: pair → move → repeated trades → unpair → cooldown."""
    # Multi-tick simulation tracking pairing events
    # Expected: Multiple successful trades before unpair (opportunities exhausted)
```

#### Test 12: Preference List Determinism
```python
def test_preference_list_determinism():
    """Same scenario produces identical preference rankings."""
    # Run same setup with same seed 10 times
    # Expected: Identical pairings every time
```

#### Test 13: Performance Benchmark
```python
def test_pairing_performance():
    """Verify O(N) scaling vs O(N²) baseline."""
    # Measure tick time with 100, 500, 1000 agents
    # Expected: Linear scaling (not quadratic)
```

---

## Performance Expectations

### Complexity Analysis

| Phase | Current (All-Pairs) | With Pairing |
|-------|---------------------|--------------|
| Decision | O(N·k) where k = neighbors | O(3N·k) = O(N·k) |
| Trade | O(N²) distance checks | O(P) where P = paired count |

**Expected speedup:**
- **Best case (high pairing rate):** ~8-10x faster trade phase
- **Typical case (50% pairing):** ~5x faster trade phase
- **Worst case (low pairing):** ~2x faster (fewer failed attempts)

### Memory Overhead

Per agent:
- `paired_with_id`: 8 bytes (int)
- `_preference_list`: ~40 bytes × neighbors (typically < 20)
- **Total:** < 1 KB per agent

For 1000 agents: ~1 MB additional memory (negligible)

---

## Migration Path

### Phase 1: Add Agent Field
- Add `paired_with_id` and `_preference_list` to Agent dataclass
- No behavior changes yet
- Tests: Field initialization

### Phase 2: Implement Three-Pass Algorithm
- Refactor DecisionSystem to three passes
- No pairing establishment yet (just structure)
- Tests: Pass execution order

### Phase 3: Enable Pass 2 (Mutual Consent)
- Implement mutual consent pairing logic
- Add telemetry logging
- Tests: Mutual pairing cases

### Phase 4: Enable Pass 3 (Fallback)
- Implement best-available fallback
- Add rank logging
- Tests: Fallback pairing cases

### Phase 5: Integrate with Trade/Movement/Forage
- Update TradeSystem to use pairings
- Update MovementSystem to respect pairings
- Update ForageSystem to skip paired agents
- Tests: Cross-phase integration

### Phase 6: Mode Management
- Add mode-switch unpair logic
- Tests: Mode transitions

### Phase 7: Housekeeping Integration
- Add integrity checks
- Tests: Corruption detection

### Phase 8: Performance Validation
- Run benchmark suite
- Verify O(N) scaling
- Compare against baseline

---

## Design Decisions (Resolved)

### 1. Commitment Model ✅
**Decision:** Full commitment once paired (no rejection mechanism)

**Pairing persistence:** Agents remain paired across multiple ticks, executing repeated trades until opportunities are exhausted (trade attempt fails).

**Rationale:** 
- Critical for O(N) performance benefit (avoid re-pairing overhead)
- Simpler implementation and clearer semantics
- Reflects realistic bilateral trading relationships
- Agents fully exploit gains from trade before seeking new partners

**Documented caveat:** Agents may commit to distant partners and spend many ticks moving toward them while ignoring other opportunities. Once paired, they execute multiple sequential trades. This is by design but may appear suboptimal in some scenarios. Has educational value for demonstrating opportunity cost of commitment and iterative bilateral exchange.

### 2. Distance Filtering and Ranking ✅
**Decision:** Two-stage filtering:
1. First filter: Neighbors within `vision_radius` (perception constraint)
2. Second filter: Rank by distance-discounted surplus = `surplus × β^distance`

**Rationale:** 
- Perception radius reflects realistic information constraints
- Beta discounting (same as foraging) creates consistent spatial preference ordering across all agent decisions
- Distance treated as "time" (number of steps to reach partner)
- Nearby partners preferred over distant ones with similar surplus
- Maintains economic rationality while incorporating spatial realism
- Consistent with existing VMT foraging mechanics

### 3. Paired Agent Re-evaluation ✅
**Decision:** Paired agents maintain exclusive commitment but still build preference lists for telemetry

**Rationale:**
- Commitment maintained (no mid-pairing defection)
- Preference lists enable rich analysis and research
- Can study "what if" scenarios and opportunity costs
- Adds minimal computational overhead

### 4. Preference Logging ✅
**Decision:** Hybrid approach - log top 3 preferences by default, with optional full logging

**Schema:** `(tick, agent_id, partner_id, rank, surplus, discounted_surplus, distance)`

**Parameter:** `log_full_preferences: bool = False` (when True, logs all preferences)

**Rationale:**
- Top 3 captures decision-relevant information (90% of research questions)
- Reduces database size by ~80% for typical scenarios (15 neighbors → 3 logged)
- Researchers can enable full logging for specific studies
- Balances data richness with performance and storage

### 5. Cycle-Breaking Algorithm ✅
**Decision:** Surplus-based greedy matching (not ID-based)

**Algorithm:** Sort all potential pairings by descending discounted_surplus, greedily assign pairs

**Rationale:**
- Welfare-maximizing within greedy framework
- Resolves three-way cycles optimally
- Still deterministic (ID tiebreaking when surplus equal)
- Better pedagogical properties (demonstrates surplus maximization)

---

## Success Criteria

Implementation is complete when:

1. ✅ All unit tests pass (10 tests minimum)
2. ✅ All integration tests pass (3 tests minimum)
3. ✅ Performance benchmarks show 5-8× speedup in trade phase
4. ✅ Determinism tests pass (identical results across 100 runs with same seed)
5. ✅ Existing scenarios still work (backward compatibility)
6. ✅ Telemetry captures full pairing lifecycle
7. ✅ No linter errors
8. ✅ Documentation updated

---

## References

- Trade Pairing Implementation Plan (original): `docs/tmp/pairing/trade_pairing_implementation.md`
- Core Invariants: `.cursor/rules/core-invariants.mdc`
- Systems Development Guidelines: `.cursor/rules/systems-development.mdc`
- Economics Guidelines: `.cursor/rules/economics-utilities.mdc`
- Technical Manual: `docs/2_technical_manual.md`

---

## All Design Decisions Finalized ✅

### 1. Distance Discounting Formula ✅
**Decision:** `discounted_surplus = surplus × β^distance`

**Rationale:** Uses same beta discount factor as foraging for consistency. Distance treated as "time" (steps to reach partner).

### 2. Pairing Persistence ✅
**Decision:** No timeout mechanism - pairings persist until trade attempt

**Rationale:** This is intended behavior demonstrating commitment and opportunity cost. Has pedagogical value.

### 3. Preferences Table Size ✅
**Decision:** Hybrid - log top 3 by default, with `log_full_preferences` parameter

**Rationale:** 
- Top 3 captures decision-relevant information for most research questions
- Reduces DB size by ~80% compared to full logging
- Optional full logging available for detailed studies
- 1000 agents × 3 prefs × 1000 ticks = ~3M rows (~1.5 GB) - manageable

### 4. Cooldown Clearing ✅
**Decision:** Clear cooldowns for both mutual and fallback pairings

**Rationale:** Cooldowns are partner-specific. When B pairs with C (even if fallback), B's cooldown with A remains relevant only for A-B future interactions. Clearing maximizes trade opportunities without violating cooldown intent.

---

## Implementation Readiness

**All design decisions finalized.** This specification is complete and ready for implementation.

**Next Steps:**
1. Review the complete specification for any final concerns
2. Proceed with Phase 1: Add `paired_with_id` field to Agent dataclass
3. Follow the 8-phase migration path outlined in the Migration Path section

**Key Parameters to Add:**
- `log_full_preferences: bool = False` (scenario parameter)
- Beta already exists in scenarios for foraging

**Estimated Implementation Time:**
- Phase 1-2 (Structure): 2-3 hours
- Phase 3-4 (Pairing logic): 4-6 hours  
- Phase 5-7 (Integration): 6-8 hours
- Phase 8 (Testing/validation): 4-6 hours
- **Total: 16-23 hours** over 3-4 focused work sessions

