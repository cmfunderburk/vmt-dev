Excellent choice! Extract-and-refactor will give us a much cleaner architecture. Let me present a detailed plan for Phase 1 with this approach.

[4 tools called]

Now let me create a comprehensive plan for Phase 1 with the extract-and-refactor approach:

## Phase 1 Plan: Legacy Adapters (Extract & Refactor)

### Overview

Extract core decision-making logic from DecisionSystem into protocol classes, then refactor DecisionSystem into an orchestrator that builds WorldViews, calls protocols, and applies Effects. This achieves clean separation while maintaining bit-identical behavior.

### Architecture Changes

**Current Flow:**
```
DecisionSystem.execute(sim)
  → Mutate agent state directly (target_pos, paired_with_id, etc.)
  → Tight coupling to Simulation internals
```

**New Flow:**
```
DecisionSystem.execute(sim)
  → Build WorldView per agent
  → Call protocol methods (search/matching)
  → Protocols return Effects
  → Apply Effects to update agent state
  → Log to telemetry
```

### Implementation Tasks

#### Task 1: LegacySearchProtocol (3-4 hours)

**File:** `src/vmt_engine/protocols/search/legacy.py`

**Extract from DecisionSystem:**
- `_evaluate_forage_target()` - Forage target selection
- `_evaluate_trade_preferences()` - Trade preference building  
- `_evaluate_trade_vs_forage()` - Mixed mode comparison
- Helper: `_filter_claimed_resources()` - Resource claiming filter

**Dependencies to move:**
- `choose_forage_target()` from `movement.py` - becomes method or helper
- `compute_surplus()` / `estimate_money_aware_surplus()` from `matching.py` - import

**Key Methods:**
```python
class LegacySearchProtocol(SearchProtocol):
    name = "legacy_distance_discounted"
    version = "2025.10.26"
    
    def build_preferences(self, world: WorldView) -> list[tuple[Target, float, dict]]:
        """Build ranked preference list (trade or forage targets)."""
        # Extract from _evaluate_trade_preferences + _evaluate_forage_target
        # Returns [(target, score, metadata), ...]
    
    def select_target(self, world: WorldView) -> list[Effect]:
        """Select best target and return SetTarget effect."""
        # Implements mode-aware selection logic
        # Returns [SetTarget(agent_id, target)] or []
```

**Challenges:**
- Handling foraging commitment state (currently on Agent)
- Resource claiming needs access to sim.resource_claims dict
- Mixed mode comparison requires both trade AND forage evaluation

**Solution:** 
- Pass resource_claims through WorldView.params
- Foraging commitment tracked via InternalStateUpdate effects
- Mixed mode: build both preferences, compare in select_target()

---

#### Task 2: LegacyMatchingProtocol (4-5 hours)

**File:** `src/vmt_engine/protocols/matching/legacy.py`

**Extract from DecisionSystem:**
- `_pass2_mutual_consent()` - Mutual consent pairing (Pass 2)
- `_pass3_best_available_fallback()` - Greedy fallback (Pass 3)
- `_pass3b_handle_unpaired_trade_targets()` - Unpaired cleanup (Pass 3b)

**Key Methods:**
```python
class LegacyMatchingProtocol(MatchingProtocol):
    name = "legacy_three_pass"
    version = "2025.10.26"
    
    def find_matches(
        self, 
        preferences: dict[int, list[tuple[Target, float, dict]]],
        world: ProtocolContext
    ) -> list[Effect]:
        """Three-pass matching algorithm."""
        # Pass 2: Mutual consent
        # Pass 3: Greedy fallback with inventory feasibility
        # Pass 3b: Clear invalid targets for unpaired
        # Returns [Pair(...), Pair(...), ...] effects
```

**Challenges:**
- Pass 2 requires checking if both agents rank each other as #1
- Pass 3 needs to pair in sorted order (agent_id) with feasibility checks
- Pass 3b clears target_agent_id for unpaired agents wanting trade
- Trade cooldown enforcement (agent.trade_cooldowns dict)

**Solution:**
- Preferences dict passed from search phase contains full ranking
- ProtocolContext includes all_agent_views and current_pairings
- Trade cooldowns passed via WorldView per agent
- Unpair effects can clear invalid targets

---

#### Task 3: LegacyBargainingProtocol (3-4 hours)

**File:** `src/vmt_engine/protocols/bargaining/legacy.py`

**Extract from TradeSystem:**
- Trade execution logic using `find_compensating_block_generic()`
- Money-aware surplus calculation
- Trade candidate ranking

**Dependencies:**
- `find_compensating_block_generic()` from `matching.py` - becomes helper function in protocol

**Key Methods:**
```python
class LegacyBargainingProtocol(BargainingProtocol):
    name = "legacy_compensating_block"
    version = "2025.10.26"
    
    def negotiate(self, pair: tuple[int, int], world: WorldView) -> list[Effect]:
        """Find compensating block trade or unpair."""
        # Get both agents' states from world
        # Determine exchange regime and allowed pairs
        # For each pair type, search compensating block
        # Rank by surplus, pick best
        # Return [Trade(...)] or [Unpair(..., reason="trade_failed")]
```

**Challenges:**
- Must try all allowed pair types (A↔B, A↔M, B↔M for mixed regime)
- Ranking uses 3-level tie-breaking (surplus → money-first → lexical)
- Distance check (interaction_radius) before attempting trade
- Inventory feasibility and conservation laws

**Solution:**
- WorldView contains both agents' full state
- Exchange regime passed via world.exchange_regime
- Helper function reuses existing compensating block logic
- Trade validation happens in effect application (Phase 2)

---

#### Task 4: Refactor DecisionSystem (5-6 hours)

**File:** `src/vmt_engine/systems/decision.py`

**Transform into orchestrator:**

```python
class DecisionSystem:
    """Phase 2: Orchestrate protocol-based decision making."""
    
    def __init__(self):
        # Protocols will be injected from Simulation
        self.search_protocol: Optional[SearchProtocol] = None
        self.matching_protocol: Optional[MatchingProtocol] = None
    
    def execute(self, sim: Simulation) -> None:
        # Phase 2a: Clear stale claims
        self._clear_stale_claims(sim)
        
        # Phase 2b: Search - build preferences and select targets
        preferences = self._execute_search_phase(sim)
        
        # Phase 2c: Matching - establish pairings
        pairing_effects = self._execute_matching_phase(sim, preferences)
        self._apply_pairing_effects(sim, pairing_effects)
        
        # Phase 2d: Log decisions
        self._log_decisions(sim)
    
    def _execute_search_phase(self, sim) -> dict[int, list]:
        """Call search protocol for each agent."""
        preferences = {}
        for agent in sorted(sim.agents, key=lambda a: a.id):
            # Skip if already paired
            if agent.paired_with_id is not None:
                self._handle_paired_agent(agent, sim)
                continue
            
            # Build WorldView for this agent
            world = self._create_world_view(agent, sim)
            
            # Call search protocol
            prefs = self.search_protocol.build_preferences(world)
            effects = self.search_protocol.select_target(world)
            
            # Apply effects immediately
            self._apply_search_effects(agent, effects, sim)
            
            # Store preferences for matching phase
            preferences[agent.id] = prefs
        
        return preferences
    
    def _execute_matching_phase(self, sim, preferences) -> list[Effect]:
        """Call matching protocol with global view."""
        # Build ProtocolContext
        context = self._create_protocol_context(sim)
        
        # Call matching protocol
        effects = self.matching_protocol.find_matches(preferences, context)
        
        return effects
    
    def _create_world_view(self, agent, sim) -> WorldView:
        """Build WorldView from agent's perception cache."""
        # Extract from perception_cache
        # Build AgentView/ResourceView lists
        # Return frozen WorldView
        pass
    
    def _apply_search_effects(self, agent, effects, sim):
        """Apply SetTarget, ClaimResource effects."""
        for effect in effects:
            if isinstance(effect, SetTarget):
                agent.target_pos = effect.target
                # etc.
            elif isinstance(effect, ClaimResource):
                sim.resource_claims[effect.pos] = agent.id
        pass
    
    def _apply_pairing_effects(self, sim, effects):
        """Apply Pair/Unpair effects."""
        for effect in effects:
            if isinstance(effect, Pair):
                agent_a = sim.agent_by_id[effect.agent_a]
                agent_b = sim.agent_by_id[effect.agent_b]
                agent_a.paired_with_id = effect.agent_b
                agent_b.paired_with_id = effect.agent_a
                # Log to telemetry
            elif isinstance(effect, Unpair):
                # Similar logic
        pass
```

**Removed methods (moved to protocols):**
- `_evaluate_trade_preferences()` → LegacySearchProtocol
- `_evaluate_forage_target()` → LegacySearchProtocol  
- `_evaluate_trade_vs_forage()` → LegacySearchProtocol
- `_pass2_mutual_consent()` → LegacyMatchingProtocol
- `_pass3_best_available_fallback()` → LegacyMatchingProtocol
- `_pass3b_handle_unpaired_trade_targets()` → LegacyMatchingProtocol

**Kept methods:**
- `_clear_stale_claims()` - Still housekeeping utility
- `_handle_paired_agent()` - Target validation for already-paired
- `_log_decisions()` - Telemetry logging (preferences table)

---

#### Task 5: Integrate Protocols into Simulation (2-3 hours)

**File:** `src/vmt_engine/simulation.py`

**Changes:**

```python
def __init__(self, scenario_config, seed, log_config=None,
             search_protocol=None, matching_protocol=None, bargaining_protocol=None):
    # ... existing initialization ...
    
    # Initialize default protocols if not provided
    if search_protocol is None:
        from .protocols.search.legacy import LegacySearchProtocol
        search_protocol = LegacySearchProtocol()
    if matching_protocol is None:
        from .protocols.matching.legacy import LegacyMatchingProtocol
        matching_protocol = LegacyMatchingProtocol()
    if bargaining_protocol is None:
        from .protocols.bargaining.legacy import LegacyBargainingProtocol
        bargaining_protocol = LegacyBargainingProtocol()
    
    self.search_protocol = search_protocol
    self.matching_protocol = matching_protocol
    self.bargaining_protocol = bargaining_protocol
    
    # Inject protocols into systems
    self.systems = [
        PerceptionSystem(),
        DecisionSystem(),  # Will use sim.search_protocol and sim.matching_protocol
        MovementSystem(),
        TradeSystem(),     # Will use sim.bargaining_protocol
        ForageSystem(),
        ResourceRegenerationSystem(),
        HousekeepingSystem(),
    ]
    
    # Pass protocol references to systems
    decision_system = self.systems[1]
    decision_system.search_protocol = self.search_protocol
    decision_system.matching_protocol = self.matching_protocol
    
    trade_system = self.systems[3]
    trade_system.bargaining_protocol = self.bargaining_protocol
```

---

#### Task 6: Refactor TradeSystem (2-3 hours)

**File:** `src/vmt_engine/systems/trading.py`

**Changes:**
- Add `bargaining_protocol` field
- Replace `_trade_generic()` with protocol calls
- Apply Trade effects returned by protocol

```python
class TradeSystem:
    def __init__(self):
        self.bargaining_protocol: Optional[BargainingProtocol] = None
    
    def execute(self, sim):
        for pair in self._get_paired_agents_in_range(sim):
            agent_a, agent_b = pair
            
            # Build WorldView for negotiation
            world = self._create_trade_world_view(agent_a, agent_b, sim)
            
            # Call bargaining protocol
            effects = self.bargaining_protocol.negotiate(
                (agent_a.id, agent_b.id), world
            )
            
            # Apply effects
            self._apply_trade_effects(effects, sim)
```

---

#### Task 7: Testing & Verification (4-5 hours)

**Create telemetry comparison script:**

**File:** `scripts/verify_protocol_equivalence.py`

```python
def verify_equivalence(scenario_path, seed=42):
    """Run same scenario with old vs new system, compare telemetry."""
    
    # Run with legacy protocols (new system)
    config = load_scenario(scenario_path)
    sim = Simulation(config, seed=seed)
    sim.run(max_ticks=100)
    telemetry_new = extract_telemetry(sim)
    
    # Compare key metrics
    differences = compare_telemetry(telemetry_baseline, telemetry_new)
    
    if differences:
        print(f"❌ Differences found: {differences}")
        return False
    else:
        print(f"✅ Telemetry identical")
        return True

# Test on all critical scenarios
scenarios = [
    "scenarios/three_agent_barter.yaml",
    "scenarios/money_test_basic.yaml",
    "scenarios/mixed.yaml",
    "scenarios/mode_toggle_demo.yaml",
]

for scenario in scenarios:
    verify_equivalence(scenario)
```

**Verification checklist:**
- [ ] All 345+ tests pass
- [ ] Telemetry comparison shows identical results for 5+ scenarios
- [ ] Determinism check: 10 runs → same hash
- [ ] Performance within 10% of baseline

---

### Implementation Order

**Week 1 (Days 1-3):**
1. LegacySearchProtocol implementation
2. WorldView creation helpers
3. Unit tests for search protocol

**Week 1 (Days 4-5):**
4. LegacyMatchingProtocol implementation
5. ProtocolContext creation helpers
6. Unit tests for matching protocol

**Week 2 (Days 1-2):**
7. LegacyBargainingProtocol implementation
8. Unit tests for bargaining protocol

**Week 2 (Days 3-4):**
9. Refactor DecisionSystem to orchestrator
10. Integrate protocols into Simulation
11. Refactor TradeSystem

**Week 2 (Days 4-5):**
12. Integration testing
13. Telemetry equivalence verification
14. Performance benchmarking
15. Documentation updates

---

### Critical Risks & Mitigations

**Risk 1: Behavioral Drift**
- **Problem:** Subtle logic changes during extraction
- **Mitigation:** Copy-paste logic first, refactor minimally, verify at each step

**Risk 2: State Management**
- **Problem:** Agent state (target_pos, paired_with_id) must update correctly
- **Mitigation:** Effect application carefully mirrors old direct mutations

**Risk 3: Execution Order**
- **Problem:** Determinism requires exact same order
- **Mitigation:** Maintain sorted iteration by agent.id, document order dependencies

**Risk 4: Resource Claiming**
- **Problem:** Claims dict is global sim state, protocols need access
- **Mitigation:** Pass via WorldView.params or add to ProtocolContext

**Risk 5: Performance**
- **Problem:** WorldView creation overhead, effect object allocation
- **Mitigation:** Profile hot paths, optimize if >10% regression

---

### Success Criteria

**Phase 1 Complete when:**
- [x] All 3 legacy protocols implemented and registered
- [x] DecisionSystem refactored to orchestrator
- [x] TradeSystem integrated with bargaining protocol
- [x] All 345+ tests passing
- [x] Telemetry bit-identical for 5+ test scenarios
- [x] 10-run determinism check passes
- [x] Performance <10% regression
- [x] Code review complete
- [x] Documentation updated

---

## Discussion Points

**1. WorldView Creation Performance**
- Creating WorldView per agent per tick = 100 agents × 1 WorldView = overhead
- **Options:**
  - a) Accept overhead (simpler, cleaner)
  - b) Cache/reuse WorldViews within tick (complex)
  - c) Lazy creation only when protocol called (best balance?)

**2. Effect Application Timing**
- Plan shows "immediate application" within each phase
- **Confirm:** This matches DEC-003 decision (immediate, not batched)
- **Implication:** Search effects applied before matching, maintains current behavior

**3. Resource Claiming State**
- Currently `sim.resource_claims: dict[Position, int]`
- **Options:**
  - a) Pass via WorldView.params (less clean)
  - b) Add to ProtocolContext.resource_claims (cleaner)
  - c) ClaimResource/ReleaseClaim effects handle it (cleanest)
- **Recommendation:** Option (c) - protocols emit effects, DecisionSystem applies to sim.resource_claims

**4. Preference List Storage**
- Currently stored in `agent._preference_list`
- **Options:**
  - a) Keep on agent (current behavior)
  - b) Return from protocol, store in DecisionSystem
  - c) Log to telemetry only, don't persist
- **Recommendation:** Option (b) - DecisionSystem stores preferences dict, passes to matching

**5. Trade Cooldown Enforcement**
- Currently checked in Pass 3 before pairing
- **Location in new system:**
  - LegacyMatchingProtocol.find_matches() checks cooldowns
  - Passed via WorldView.trade_cooldowns per agent
  - **Confirm:** This maintains current behavior

---

## Final Thoughts Before Implementation

**Confidence Level:** High (80%)
- Clear separation of concerns
- Maintains determinism through ordered execution
- Effect-based mutations are explicit and auditable
- Extract-and-refactor reduces ambiguity vs wrap-and-delegate

**Biggest Challenge:** WorldView creation overhead and ensuring no behavioral drift during extraction

**Estimated Timeline:** 
- Optimistic: 7 days (if extractions are clean)
- Realistic: 10 days (with debugging and verification)
- Pessimistic: 14 days (if behavioral drift requires deep debugging)

**Recommendation:** Proceed with phased approach - implement protocols one at a time, verify tests pass after each extraction before moving to next.

---

**Ready to proceed?** Any concerns or adjustments to the plan before we begin implementation?

> cmf: 1. accept overhead
> 2. confirmed
> 3. option C
> 4. option b
> 5. confirmed
>
> proceed, check in with me for ambiguous choices or when finished.

Perfect! All design decisions confirmed. Beginning Phase 1 implementation now. I'll start with LegacySearchProtocol and work through the plan systematically.

[4 tools called]

Now I'll begin implementing LegacySearchProtocol by extracting the search logic from DecisionSystem:

[3 tools called]

Excellent! LegacySearchProtocol complete with no errors. Now implementing LegacyMatchingProtocol with the three-pass algorithm:

[1 tool called]

Now implementing LegacyMatchingProtocol with the three-pass algorithm:

[3 tools called]

Great! Now implementing LegacyBargainingProtocol. Let me first examine the trade execution logic:

[3 tools called]

Perfect! Now implementing LegacyBargainingProtocol:

[4 tools called]

Excellent! All three protocols complete. Now I need to create the WorldView/ProtocolContext builder helpers before refactoring the systems. This is critical infrastructure:

[5 tools called]

Perfect! Context builders complete. Now refactoring DecisionSystem to be a protocol orchestrator. This is a major transformation:

[2 tools called]

Now refactoring DecisionSystem (544 lines → much smaller orchestrator). This is a complete rewrite:

[3 tools called]

Excellent! DecisionSystem reduced from 544 → 317 lines (-42%). Now refactoring TradeSystem:

[3 tools called]

Now refactoring TradeSystem to use bargaining protocol:

[3 tools called]

Excellent! TradeSystem reduced from 406 → 202 lines (-50%). Now integrating protocols into Simulation:

[5 tools called]

Perfect! Integration complete with no linter errors. Now running full test suite to verify equivalence:

[2 tools called]

Quick fix - need to restore TradeCandidate class for backward compatibility:

[2 tools called]

Quick fix - Grid attribute name is wrong. Let me check and fix:

[4 tools called]

Now I have a logic error - trades aren't happening. Let me check what the test expects and look for bugs:

[2 tools called]

## Critical Issue Found - Checking In

The refactoring is complete and the code compiles, but I've hit a critical behavior issue:

**Problem:** No trades are occurring in the foundational barter demo (expected ≥1 trade, got 0).

**What's working:**
- All protocol implementations complete (search, matching, bargaining)
- Context builders implemented
- DecisionSystem and TradeSystem refactored to orchestrators
- Everything integrated into Simulation
- No linter errors, code compiles cleanly

**What's broken:**
- The pipeline isn't producing trades (search → matching → trade flow has an issue)

**Possible causes:**
1. Search protocol not emitting proper SetTarget effects for trade targets
2. Matching protocol not finding pairs (might be preference format mismatch)
3. Bargaining protocol not being called or failing silently
4. Effect application logic has subtle bugs

**Need your input:**
- Should I continue debugging this now (could take 1-2 hours)?
- Or would you prefer to review what's been done so far and discuss the architecture before fixing?
- I can add detailed logging to trace where the pipeline breaks

**Current progress:** ~80% complete - all code written, integration done, but behavior verification failing.

What would you like me to do?