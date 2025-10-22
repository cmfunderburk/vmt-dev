# Protocol Modularization Implementation Guide

**Status:** Active Implementation Plan  
**Created:** 2025-10-22  
**Based On:** `protocol_modularization_plan_v3.md`

---

## Overview

This document breaks down the Protocol Modularization Refactor into atomic, actionable implementation steps. Each step includes specific file changes, acceptance criteria, and validation commands.

**Goal:** Extract search and matching logic from the monolithic `DecisionSystem` into modular protocol interfaces while preserving 100% deterministic behavior and telemetry equivalence.

**Timeline:** ~4-6 weeks total
- Phase 1: 3-5 days (Interfaces + Legacy wrappers)
- Phase 2: 1-2 weeks (Extraction + Alternative protocols)
- Phase 3: 3-4 days (Configuration + Registry)
- Phase 4: 3-5 days (Validation + Performance)

---

## Phase 1: Interfaces + Legacy Wrappers + Delegation

**Goal:** Create protocol interfaces and wire them into the engine WITHOUT changing any behavior.

### Step 1.1: Create Protocol Package Structure (30 min)

**Files to create:**
```
src/vmt_engine/protocols/
├── __init__.py
├── context.py
├── search.py
├── matching.py
├── legacy_search.py
└── legacy_matching.py
```

**Actions:**
1. Create directory: `mkdir -p src/vmt_engine/protocols`
2. Create empty `__init__.py` with package docstring
3. Create skeleton files for each module

**Acceptance:**
- `import vmt_engine.protocols` succeeds
- All modules have docstrings explaining their purpose

---

### Step 1.2: Implement ProtocolContext (1-2 hours)

**File:** `src/vmt_engine/protocols/context.py`

**Implementation:**
```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from vmt_engine.core.grid import Grid
from vmt_engine.core.agent import Agent
from vmt_engine.core.spatial_index import SpatialIndex

@dataclass
class ProtocolContext:
    """Read-only context for protocol operations."""
    
    # Core simulation state
    params: Dict[str, Any]
    current_tick: int
    current_mode: str
    grid: Grid
    agent_by_id: Dict[int, Agent]
    spatial_index: SpatialIndex
    resource_claims: Dict[tuple[int, int], int]  # (x, y) -> agent_id
    trade_cooldown_ticks: int
    
    # Convenience properties
    @property
    def beta(self) -> float:
        return self.params.get("distance_discount_factor", 1.0)
    
    @property
    def vision_radius(self) -> int:
        return self.params.get("vision_radius", 5)
    
    @property
    def interaction_radius(self) -> int:
        return self.params.get("interaction_radius", 1)
    
    @property
    def forage_rate(self) -> int:
        return self.params.get("forage_rate", 1)
    
    @property
    def exchange_regime(self) -> str:
        return self.params.get("exchange_regime", "barter_only")
    
    @property
    def enable_resource_claiming(self) -> bool:
        return self.params.get("enable_resource_claiming", True)
```

**Acceptance:**
- `ProtocolContext` can be instantiated with all required fields
- All properties return correct values
- Type hints pass `mypy` validation

**Validation:**
```bash
# Add to tests/test_protocol_context.py
pytest tests/test_protocol_context.py -v
mypy src/vmt_engine/protocols/context.py
```

---

### Step 1.3: Define SearchProtocol ABC (1 hour)

**File:** `src/vmt_engine/protocols/search.py`

**Implementation:**
```python
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from vmt_engine.core.agent import Agent
from vmt_engine.protocols.context import ProtocolContext

Position = Tuple[int, int]

class SearchProtocol(ABC):
    """
    Protocol for agent search and target selection.
    
    Responsibilities:
    - Evaluate forage opportunities
    - Select optimal forage targets
    - Manage resource claiming
    - Set agent commitment flags
    """
    
    @abstractmethod
    def select_forage_target(
        self,
        agent: Agent,
        perception_cache: dict,
        context: ProtocolContext
    ) -> Optional[Position]:
        """
        Select a forage target for the agent.
        
        Side effects:
        - May set agent.target_pos
        - May set agent.is_committed_to_forage
        - May update context.resource_claims
        
        Returns:
            Position if forage target selected, None otherwise
        """
        pass
    
    @abstractmethod
    def evaluate_resource_opportunity(
        self,
        agent: Agent,
        resource_cell: Position,
        context: ProtocolContext
    ) -> float:
        """
        Evaluate the value of a resource opportunity.
        
        Used for ranking and tie-breaking.
        
        Returns:
            Float score (higher is better)
        """
        pass
```

**Acceptance:**
- `SearchProtocol` cannot be instantiated directly (ABC)
- Type hints are correct for all methods
- Docstrings explain side effects clearly

**Validation:**
```bash
python -c "from vmt_engine.protocols.search import SearchProtocol; SearchProtocol()"
# Should raise: TypeError: Can't instantiate abstract class
```

---

### Step 1.4: Define MatchingProtocol ABC (1 hour)

**File:** `src/vmt_engine/protocols/matching.py`

**Implementation:**
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from vmt_engine.core.agent import Agent
from vmt_engine.protocols.context import ProtocolContext

# Preference tuple: (partner_id, surplus, discounted_surplus, distance, pair_type)
Preference = Tuple[int, float, float, int, str]

class MatchingProtocol(ABC):
    """
    Protocol for agent pairing and matching.
    
    Responsibilities:
    - Build preference lists for agents
    - Establish mutual pairings
    - Handle cooldowns and feasibility
    - Maintain deterministic ordering
    """
    
    @abstractmethod
    def build_preferences(
        self,
        agents: List[Agent],
        context: ProtocolContext
    ) -> Dict[int, List[Preference]]:
        """
        Build ranked preference lists for all agents.
        
        Returns:
            Dict mapping agent_id to list of preferences.
            Each preference is (partner_id, surplus, discounted_surplus, 
            distance, pair_type).
            List must be sorted by (-discounted_surplus, partner_id).
        """
        pass
    
    @abstractmethod
    def find_matches(
        self,
        preferences: Dict[int, List[Preference]],
        context: ProtocolContext
    ) -> List[Tuple[int, int]]:
        """
        Establish pairings from preference lists.
        
        Side effects:
        - Sets agent.paired_with_id
        - Sets agent.target_pos and agent.target_agent_id
        - Clears mutual cooldowns
        
        Returns:
            List of (agent_i_id, agent_j_id) pairs where i < j
        """
        pass
```

**Acceptance:**
- `MatchingProtocol` cannot be instantiated directly (ABC)
- Type aliases are clear and documented
- Return types match telemetry expectations

**Validation:**
```bash
python -c "from vmt_engine.protocols.matching import MatchingProtocol; MatchingProtocol()"
# Should raise: TypeError: Can't instantiate abstract class
```

---

### Step 1.5: Implement LegacySearchProtocol (3-4 hours)

**File:** `src/vmt_engine/protocols/legacy_search.py`

**Strategy:** Extract current forage logic from `DecisionSystem._evaluate_forage_target` and `movement.choose_forage_target`.

**Key behaviors to preserve:**
1. Filter resources within vision
2. Check resource availability (> 0)
3. Apply claiming logic if enabled
4. Distance-based scoring
5. Deterministic tie-breaking (lowest x, then lowest y)
6. Idle-home fallback if no resources available
7. Set commitment flags

**Implementation outline:**
```python
class LegacySearchProtocol(SearchProtocol):
    """Legacy forage search matching current DecisionSystem behavior."""
    
    def select_forage_target(
        self, agent: Agent, perception_cache: dict, context: ProtocolContext
    ) -> Optional[Position]:
        # 1. Extract visible resources from perception_cache
        # 2. Filter by availability (resources > 0)
        # 3. Filter by unclaimed or claimed-by-self
        # 4. Score by distance (negative Manhattan distance)
        # 5. Sort candidates: (-score, x, y) for determinism
        # 6. Select best candidate
        # 7. Claim resource if claiming enabled
        # 8. Set agent.target_pos and agent.is_committed_to_forage = True
        # 9. If no resources, idle-home fallback
        pass
    
    def evaluate_resource_opportunity(
        self, agent: Agent, resource_cell: Position, context: ProtocolContext
    ) -> float:
        # Return negative Manhattan distance for ranking
        pass
```

**Acceptance:**
- Forage target selection matches current behavior exactly
- Resource claiming works identically
- Commitment flags set correctly
- Idle-home fallback triggered when appropriate

**Validation:**
```bash
# Create test comparing old vs new behavior
pytest tests/test_legacy_search_protocol.py -v
# Run existing forage tests
pytest tests/test_resource_claiming.py -v
```

---

### Step 1.6: Implement ThreePassPairingMatching (4-6 hours)

**File:** `src/vmt_engine/protocols/legacy_matching.py`

**Strategy:** Extract Pass 1, Pass 2, Pass 3 logic from `DecisionSystem`.

**Key behaviors to preserve:**
1. **Pass 1 (build_preferences):**
   - Filter neighbors within vision
   - Skip agents in cooldown
   - Use `compute_surplus()` for barter_only
   - Use `estimate_money_aware_surplus()` for money_only/mixed
   - Apply distance discounting: `discounted = surplus * beta^distance`
   - Sort by `(-discounted_surplus, partner_id)`
   - Return dict with pair_type included

2. **Pass 2 (find_matches - mutual consent):**
   - Process agents by sorted ID
   - Check if both agents list each other as top choice
   - Lower ID establishes pairing (avoid duplication)
   - Set `paired_with_id`, `target_pos`, `target_agent_id`
   - Clear mutual cooldowns

3. **Pass 3 (find_matches - greedy fallback):**
   - Collect all potential pairs from preferences
   - Sort by `(-discounted_surplus, min_id, max_id)`
   - Greedy assignment: first available pair wins
   - Set reciprocal commitment (target points back)

**Implementation outline:**
```python
class ThreePassPairingMatching(MatchingProtocol):
    """Legacy three-pass pairing matching current DecisionSystem behavior."""
    
    def build_preferences(
        self, agents: List[Agent], context: ProtocolContext
    ) -> Dict[int, List[Preference]]:
        preferences = {}
        
        for agent in sorted(agents, key=lambda a: a.id):
            if agent.paired_with_id is not None:
                continue  # Skip already-paired
            
            # Get neighbors from perception
            perception = agent.perception_cache or {}
            neighbors = perception.get("neighbors", [])
            
            pref_list = []
            for neighbor_id in neighbors:
                neighbor = context.agent_by_id.get(neighbor_id)
                if not neighbor:
                    continue
                
                # Check cooldown
                if self._in_cooldown(agent, neighbor, context):
                    continue
                
                # Calculate surplus based on exchange_regime
                if context.exchange_regime == "barter_only":
                    surplus = compute_surplus(agent, neighbor)
                    pair_type = "A_for_B"
                else:
                    surplus, pair_type = estimate_money_aware_surplus(
                        agent, neighbor, context.exchange_regime
                    )
                
                if surplus <= 0:
                    continue
                
                # Distance discounting
                distance = manhattan_distance(agent.pos, neighbor.pos)
                discounted_surplus = surplus * (context.beta ** distance)
                
                pref_list.append((
                    neighbor_id, surplus, discounted_surplus, 
                    distance, pair_type
                ))
            
            # Sort deterministically
            pref_list.sort(key=lambda p: (-p[2], p[0]))
            preferences[agent.id] = pref_list
        
        return preferences
    
    def find_matches(
        self, preferences: Dict[int, List[Preference]], context: ProtocolContext
    ) -> List[Tuple[int, int]]:
        matched_pairs = []
        
        # Pass 2: Mutual consent
        matched_pairs.extend(self._mutual_consent_pass(preferences, context))
        
        # Pass 3: Greedy fallback
        matched_pairs.extend(self._greedy_fallback_pass(preferences, context))
        
        return matched_pairs
    
    def _mutual_consent_pass(self, preferences, context):
        # Implementation of Pass 2
        pass
    
    def _greedy_fallback_pass(self, preferences, context):
        # Implementation of Pass 3
        pass
```

**Acceptance:**
- Preference lists match current Decision system exactly
- Pass 2 mutual consent works identically
- Pass 3 greedy fallback produces same pairings
- Deterministic ordering preserved
- Cooldown filtering correct

**Validation:**
```bash
pytest tests/test_legacy_matching_protocol.py -v
pytest tests/test_pairing_money_aware.py -v
pytest tests/test_mixed_regime_tie_breaking.py -v
```

---

### Step 1.7: Wire Protocols into Simulation.__init__ (1 hour)

**File:** `src/vmt_engine/simulation.py`

**Changes:**
```python
class Simulation:
    def __init__(
        self,
        scenario: ScenarioConfig,
        seed: int = 42,
        log_config: Optional[LogConfig] = None,
        search_protocol: Optional[SearchProtocol] = None,
        matching_protocol: Optional[MatchingProtocol] = None,
    ):
        # ... existing initialization ...
        
        # Initialize protocols with legacy defaults
        if search_protocol is None:
            from vmt_engine.protocols.legacy_search import LegacySearchProtocol
            search_protocol = LegacySearchProtocol()
        
        if matching_protocol is None:
            from vmt_engine.protocols.legacy_matching import ThreePassPairingMatching
            matching_protocol = ThreePassPairingMatching()
        
        self.search_protocol = search_protocol
        self.matching_protocol = matching_protocol
        
        # Store protocol context (updated each tick)
        self.protocol_context = None  # Created in tick()
```

**Acceptance:**
- Simulation initializes with default legacy protocols
- Custom protocols can be injected via constructor
- No behavior changes when using defaults

**Validation:**
```bash
pytest tests/test_simulation_init.py -v
```

---

### Step 1.8: Create ProtocolContext in Tick Loop (30 min)

**File:** `src/vmt_engine/simulation.py`

**Changes in `tick()` method:**
```python
def tick(self):
    # At start of tick, create protocol context
    from vmt_engine.protocols.context import ProtocolContext
    
    self.protocol_context = ProtocolContext(
        params=self.params,
        current_tick=self.tick_count,
        current_mode=self.current_mode,
        grid=self.grid,
        agent_by_id={a.id: a for a in self.agents},
        spatial_index=self.spatial_index,
        resource_claims=self.resource_claims,
        trade_cooldown_ticks=self.params.get("trade_cooldown_ticks", 5),
    )
    
    # Run 7 phases...
```

**Acceptance:**
- Context created at start of every tick
- All fields populated correctly
- Properties accessible

**Validation:**
```bash
# Add assertions in test
pytest tests/test_protocol_context_creation.py -v
```

---

### Step 1.9: Delegate DecisionSystem Pass 1 to Protocols (2-3 hours)

**File:** `src/vmt_engine/systems/decision.py`

**Strategy:** Replace inline logic with protocol calls while keeping orchestration in `DecisionSystem`.

**Changes:**
```python
class DecisionSystem:
    def advance(self, sim):
        # Pass 1: Build preferences via protocol
        unpaired_agents = [a for a in sim.agents if a.paired_with_id is None]
        
        # Build trade preferences
        if sim.current_mode in ["trade", "both"]:
            preferences = sim.matching_protocol.build_preferences(
                unpaired_agents, sim.protocol_context
            )
        else:
            preferences = {}
        
        # Select forage targets
        if sim.current_mode in ["forage", "both"]:
            for agent in sorted(unpaired_agents, key=lambda a: a.id):
                perception = agent.perception_cache or {}
                forage_target = sim.search_protocol.select_forage_target(
                    agent, perception, sim.protocol_context
                )
                # Store for comparison if mode="both"
        
        # Trade vs Forage comparison (mode="both")
        if sim.current_mode == "both":
            # Use existing comparison logic
            # Compare top preference discounted_surplus with forage score
            pass
        
        # Continue with Pass 2, 3, 3b, 4 as before...
```

**Acceptance:**
- Pass 1 uses protocol methods
- Behavior identical to before
- Telemetry unchanged

**Validation:**
```bash
pytest tests/test_barter_integration.py -v
pytest tests/test_money_phase1_integration.py -v
```

---

### Step 1.10: Delegate DecisionSystem Pass 2/3 to Protocols (2-3 hours)

**File:** `src/vmt_engine/systems/decision.py`

**Changes:**
```python
class DecisionSystem:
    def advance(self, sim):
        # ... Pass 1 (from Step 1.9) ...
        
        # Pass 2 & 3: Establish matches via protocol
        matched_pairs = sim.matching_protocol.find_matches(
            preferences, sim.protocol_context
        )
        
        # Pass 3b: Cleanup (keep existing logic)
        self._cleanup_stale_commitments(sim)
        
        # Pass 4: Logging (keep existing logic)
        self._log_decisions(sim, preferences, matched_pairs)
```

**Acceptance:**
- Pass 2/3 use protocol methods
- Pass 3b cleanup still runs
- Pass 4 logging unchanged
- Pairings identical to before

**Validation:**
```bash
pytest tests/test_pairing_money_aware.py -v
pytest tests/test_mixed_regime_integration.py -v
```

---

### Step 1.11: Phase 1 Regression Testing (2-3 hours)

**Create comprehensive regression test suite.**

**File:** `tests/test_phase1_protocol_regression.py`

**Tests:**
1. **Telemetry Equivalence:**
   - Run 5 scenarios with legacy system (baseline)
   - Run same scenarios with delegated protocols
   - Compare all telemetry tables (decisions, preferences, pairings, trades)
   - Assert float fields within ε=1e-10

2. **Determinism:**
   - Run same scenario 10 times with same seed
   - Assert all runs produce identical telemetry hashes

3. **Performance:**
   - Benchmark 100-agent scenario with legacy vs protocols
   - Assert performance regression < 10%

**Scenarios to test:**
- `scenarios/three_agent_barter.yaml`
- `scenarios/money_test_basic.yaml`
- `scenarios/mixed.yaml`
- `scenarios/mode_toggle_demo.yaml`
- `scenarios/large_100_agents.yaml`

**Validation:**
```bash
pytest tests/test_phase1_protocol_regression.py -v --benchmark
```

**Acceptance Criteria for Phase 1:**
- ✅ All regression tests pass
- ✅ Telemetry equivalence within ε=1e-10
- ✅ Determinism verified (10 runs identical)
- ✅ Performance regression < 10%
- ✅ All existing tests still pass

---

## Phase 2: Extraction + Alternative Protocols

**Goal:** Fully extract logic from DecisionSystem and implement alternative matching algorithms.

### Step 2.1: Extract Logic Fully (3-4 days)

**Goal:** Remove all delegation back to DecisionSystem. Make legacy protocols standalone.

**Files to modify:**
- `src/vmt_engine/protocols/legacy_search.py`
- `src/vmt_engine/protocols/legacy_matching.py`

**Actions:**
1. Copy all helper functions from DecisionSystem into protocol classes
2. Import `compute_surplus`, `estimate_money_aware_surplus` directly
3. Remove any `sim` parameter passing to DecisionSystem methods
4. Ensure protocols only access state via ProtocolContext or Agent objects

**Acceptance:**
- DecisionSystem has minimal logic (orchestration only)
- Legacy protocols are self-contained
- All tests still pass

**Validation:**
```bash
pytest tests/ -v
```

---

### Step 2.2: Implement GreedyMatching Protocol (2-3 days)

**File:** `src/vmt_engine/protocols/greedy_matching.py`

**Algorithm:** Pure greedy matching (no multi-pass).

**Strategy:**
1. Build preferences for all agents (same as legacy)
2. Collect all possible pairs with their scores
3. Sort by `(-discounted_surplus, min_id, max_id)`
4. Greedily assign pairs (first come, first served)
5. Skip pairs if either agent already matched

**Use case:** Maximum welfare (sum of surpluses) without mutual consent constraint.

**Implementation:**
```python
class GreedyMatching(MatchingProtocol):
    """Pure greedy matching for maximum aggregate surplus."""
    
    def build_preferences(self, agents, context):
        # Identical to legacy
        pass
    
    def find_matches(self, preferences, context):
        # Collect all candidate pairs
        all_pairs = []
        for agent_id, pref_list in preferences.items():
            for partner_id, surplus, disc_surplus, dist, pair_type in pref_list:
                if agent_id < partner_id:  # Avoid duplicates
                    all_pairs.append((
                        agent_id, partner_id, disc_surplus
                    ))
        
        # Sort by discounted surplus (descending), then IDs
        all_pairs.sort(key=lambda p: (-p[2], p[0], p[1]))
        
        # Greedy assignment
        matched = set()
        matched_pairs = []
        
        for agent_i, agent_j, _ in all_pairs:
            if agent_i in matched or agent_j in matched:
                continue
            
            # Establish pairing
            self._pair_agents(agent_i, agent_j, context)
            matched.add(agent_i)
            matched.add(agent_j)
            matched_pairs.append((agent_i, agent_j))
        
        return matched_pairs
```

**Acceptance:**
- GreedyMatching produces valid pairings
- Pairings differ from legacy (no mutual consent)
- Higher aggregate surplus in some scenarios
- All invariants preserved (sorted iteration, determinism)

**Validation:**
```bash
pytest tests/test_greedy_matching.py -v
# Run with actual scenario
python main.py scenarios/mixed.yaml --seed 42 --matching greedy
```

---

### Step 2.3: Implement StableMatching Protocol (Optional, 2-3 days)

**File:** `src/vmt_engine/protocols/stable_matching.py`

**Algorithm:** Gale-Shapley deferred acceptance.

**Use case:** Pedagogical scenarios demonstrating matching theory (agents don't move).

**Note:** Only works with static positions (no movement). Best for theory demonstrations.

**Implementation:** Standard Gale-Shapley with agent preferences.

**Acceptance:**
- Produces stable matching (no blocking pairs)
- Works with static agents
- Fails gracefully if agents move

**Validation:**
```bash
pytest tests/test_stable_matching.py -v
```

---

### Step 2.4: Phase 2 Integration Testing (1-2 days)

**Create tests for alternative protocols.**

**File:** `tests/test_alternative_protocols.py`

**Tests:**
1. **Greedy vs Legacy comparison:**
   - Same scenario with both protocols
   - Compare aggregate surplus (Greedy should be ≥)
   - Verify different pairing outcomes

2. **Protocol switching:**
   - Run same scenario with 3 different protocols
   - Verify all produce deterministic results
   - Verify telemetry logs protocol name

3. **Edge cases:**
   - No possible matches (all in cooldown)
   - Single agent
   - Perfect mutual preferences

**Validation:**
```bash
pytest tests/test_alternative_protocols.py -v
```

---

## Phase 3: Configuration + Registry

**Goal:** Allow protocol selection via YAML configuration.

### Step 3.1: Create Protocol Registry (1 day)

**File:** `src/vmt_engine/protocols/registry.py`

**Implementation:**
```python
from typing import Dict, Type, Callable
from vmt_engine.protocols.search import SearchProtocol
from vmt_engine.protocols.matching import MatchingProtocol

class ProtocolRegistry:
    """Central registry for protocol implementations."""
    
    _search_protocols: Dict[str, Type[SearchProtocol]] = {}
    _matching_protocols: Dict[str, Type[MatchingProtocol]] = {}
    
    @classmethod
    def register_search(cls, name: str, protocol_class: Type[SearchProtocol]):
        cls._search_protocols[name] = protocol_class
    
    @classmethod
    def register_matching(cls, name: str, protocol_class: Type[MatchingProtocol]):
        cls._matching_protocols[name] = protocol_class
    
    @classmethod
    def get_search(cls, name: str) -> SearchProtocol:
        if name not in cls._search_protocols:
            raise ValueError(f"Unknown search protocol: {name}")
        return cls._search_protocols[name]()
    
    @classmethod
    def get_matching(cls, name: str) -> MatchingProtocol:
        if name not in cls._matching_protocols:
            raise ValueError(f"Unknown matching protocol: {name}")
        return cls._matching_protocols[name]()

# Register built-in protocols
from vmt_engine.protocols.legacy_search import LegacySearchProtocol
from vmt_engine.protocols.legacy_matching import ThreePassPairingMatching
from vmt_engine.protocols.greedy_matching import GreedyMatching

ProtocolRegistry.register_search("legacy", LegacySearchProtocol)
ProtocolRegistry.register_matching("legacy", ThreePassPairingMatching)
ProtocolRegistry.register_matching("greedy", GreedyMatching)
```

**Acceptance:**
- Registry can register and retrieve protocols
- Unknown protocol names raise clear errors
- Built-in protocols auto-registered

**Validation:**
```bash
pytest tests/test_protocol_registry.py -v
```

---

### Step 3.2: Extend Scenario Schema (1 day)

**File:** `src/scenarios/schema.py`

**Add to `ScenarioParams`:**
```python
@dataclass
class ProtocolConfig:
    """Protocol selection configuration."""
    search: str = "legacy"
    matching: str = "legacy"

@dataclass
class ScenarioParams:
    # ... existing fields ...
    
    protocols: ProtocolConfig = field(default_factory=ProtocolConfig)
```

**Example YAML:**
```yaml
params:
  exchange_regime: "mixed"
  mode_schedule: "both"
  protocols:
    search: "legacy"
    matching: "greedy"
```

**Acceptance:**
- Schema validates with optional `protocols` field
- Defaults to legacy protocols
- Invalid protocol names caught during validation

**Validation:**
```bash
pytest tests/test_scenario_schema.py -v
```

---

### Step 3.3: Wire Registry into Simulation (1 day)

**File:** `src/vmt_engine/simulation.py`

**Changes:**
```python
class Simulation:
    def __init__(
        self,
        scenario: ScenarioConfig,
        seed: int = 42,
        log_config: Optional[LogConfig] = None,
        search_protocol: Optional[SearchProtocol] = None,
        matching_protocol: Optional[MatchingProtocol] = None,
    ):
        # ... existing initialization ...
        
        # Protocol precedence: Python args > YAML config > defaults
        if search_protocol is None:
            protocol_name = scenario.params.protocols.search
            search_protocol = ProtocolRegistry.get_search(protocol_name)
        
        if matching_protocol is None:
            protocol_name = scenario.params.protocols.matching
            matching_protocol = ProtocolRegistry.get_matching(protocol_name)
        
        self.search_protocol = search_protocol
        self.matching_protocol = matching_protocol
```

**File:** `src/telemetry/database.py`

**Add to `simulation_runs` table:**
```python
CREATE TABLE IF NOT EXISTS simulation_runs (
    ...
    config_json TEXT,  -- Add: protocol names in JSON
    ...
)
```

**Log protocol names:**
```python
config_json = json.dumps({
    "search_protocol": type(self.search_protocol).__name__,
    "matching_protocol": type(self.matching_protocol).__name__,
})
```

**Acceptance:**
- Protocols loaded from YAML
- Python args override YAML
- Defaults work when no config provided
- Protocol names logged to telemetry

**Validation:**
```bash
pytest tests/test_protocol_configuration.py -v
```

---

### Step 3.4: Update CLI to Support Protocol Selection (1 day)

**File:** `main.py`

**Add arguments:**
```python
parser.add_argument(
    "--search-protocol",
    type=str,
    choices=["legacy"],
    help="Override search protocol from scenario file"
)
parser.add_argument(
    "--matching-protocol",
    type=str,
    choices=["legacy", "greedy"],
    help="Override matching protocol from scenario file"
)
```

**Wire into simulation:**
```python
search_proto = None
if args.search_protocol:
    search_proto = ProtocolRegistry.get_search(args.search_protocol)

matching_proto = None
if args.matching_protocol:
    matching_proto = ProtocolRegistry.get_matching(args.matching_protocol)

sim = Simulation(
    scenario, 
    seed=args.seed,
    search_protocol=search_proto,
    matching_protocol=matching_proto
)
```

**Acceptance:**
- CLI args override YAML config
- Help text clear and accurate
- Invalid protocol names show friendly error

**Validation:**
```bash
python main.py scenarios/mixed.yaml --matching-protocol greedy --seed 42
```

---

## Phase 4: Validation + Performance

**Goal:** Comprehensive validation of determinism, telemetry equivalence, and performance.

### Step 4.1: Create Telemetry Diff Tool (2 days)

**File:** `scripts/compare_telemetry.py`

**Features:**
1. Load two telemetry databases
2. Compare all tables row-by-row
3. Allow epsilon tolerance for floats
4. Generate detailed diff report

**Usage:**
```bash
python scripts/compare_telemetry.py \
  logs/baseline.db \
  logs/protocols.db \
  --epsilon 1e-10 \
  --output diff_report.txt
```

**Acceptance:**
- Detects all differences in telemetry
- Float comparison uses configurable epsilon
- Clear reporting of mismatches

**Validation:**
- Manually create two different runs and verify diff detection

---

### Step 4.2: Determinism Validation Suite (1 day)

**File:** `tests/test_determinism_validation.py`

**Tests:**
1. **Seed Reproducibility:**
   - Run 10 times with same seed
   - Hash all telemetry
   - Assert all hashes identical

2. **Cross-Protocol Determinism:**
   - Run with legacy protocol 10 times
   - Run with greedy protocol 10 times
   - Each protocol set should be internally consistent

3. **Cross-Platform Check:**
   - Document expected telemetry hashes
   - Verify on different machines (manual)

**Validation:**
```bash
pytest tests/test_determinism_validation.py -v --count=10
```

---

### Step 4.3: Performance Benchmarking (2 days)

**File:** `tests/test_performance_protocols.py`

**Benchmarks:**
1. **Baseline comparison:**
   - Pre-modularization snapshot (from git)
   - Post-modularization with legacy protocols
   - Assert < 10% regression

2. **Protocol comparison:**
   - Legacy vs Greedy vs Stable
   - Measure ticks-per-second
   - Document trade-offs

3. **Scaling test:**
   - Run with 10, 25, 50, 100, 200 agents
   - Plot performance curves
   - Identify bottlenecks

**Scenarios:**
- `scenarios/perf_both_modes.yaml`
- `scenarios/large_100_agents.yaml`

**Validation:**
```bash
pytest tests/test_performance_protocols.py --benchmark-only
```

---

### Step 4.4: Final Integration Testing (1-2 days)

**File:** `tests/test_phase4_final_validation.py`

**Comprehensive test suite:**
1. All existing tests pass
2. All scenarios in `scenarios/` directory run successfully
3. Telemetry equivalence for legacy protocols
4. Protocol switching works in all modes
5. Edge cases handled gracefully

**Validation:**
```bash
pytest tests/ -v --cov=src/vmt_engine/protocols --cov-report=html
# Coverage should be > 90% for protocol modules
```

---

## Phase 5: Documentation + Cleanup (Future)

**Tasks:**
1. Update `docs/2_technical_manual.md` with protocol system
2. Create `docs/protocol_guide.md` for implementing custom protocols
3. Add protocol examples to `scenarios/demos/`
4. Update `.github/copilot-instructions.md` with protocol info
5. Create migration guide for custom extensions

---

## Success Criteria Checklist

### Phase 1
- [ ] All protocol interfaces defined and documented
- [ ] Legacy protocols implemented and wired
- [ ] Telemetry equivalence validated (ε ≤ 1e-10)
- [ ] Determinism verified (10 identical runs)
- [ ] Performance regression < 10%
- [ ] All existing tests pass

### Phase 2
- [ ] Logic fully extracted from DecisionSystem
- [ ] GreedyMatching protocol implemented
- [ ] Alternative protocols tested and validated
- [ ] Protocol comparison tests pass

### Phase 3
- [ ] Protocol registry implemented
- [ ] YAML configuration schema extended
- [ ] CLI supports protocol selection
- [ ] Telemetry logs protocol names

### Phase 4
- [ ] Telemetry diff tool working
- [ ] Determinism validation suite passes
- [ ] Performance benchmarks documented
- [ ] All integration tests pass
- [ ] Coverage > 90% for protocol modules

---

## Risk Mitigation

**Risk: Hidden coupling in DecisionSystem**
- Mitigation: Phase 1 uses delegation, preserving all behavior
- Validation: Telemetry equivalence test

**Risk: Telemetry drift**
- Mitigation: Centralized logging in DecisionSystem unchanged
- Validation: Automated diff tool

**Risk: Performance regression**
- Mitigation: Benchmark before/after with same scenarios
- Validation: < 10% threshold, profile if exceeded

**Risk: Breaking existing code**
- Mitigation: Incremental extraction, backward compatibility
- Validation: All existing tests must pass

**Risk: Complex state management**
- Mitigation: ProtocolContext is read-only, protocols mutate agents directly
- Validation: State mutation tests

---

## Daily Workflow

1. **Before starting:** Pull latest, run full test suite
2. **During implementation:** Commit after each step
3. **After each step:** Run relevant tests, validate acceptance criteria
4. **End of day:** Push to feature branch, update progress in this doc
5. **Phase completion:** Run full regression suite, get review

**Commit message format:**
```
[Protocol Modularization] Phase X.Y: <brief description>

- Detailed change 1
- Detailed change 2

Tests: <test commands used>
```

---

## Getting Unstuck

**If tests fail:**
1. Check telemetry diff tool output
2. Add debug logging in protocol methods
3. Compare agent state before/after protocol call
4. Verify sorted iteration order
5. Check cooldown/pairing state

**If performance regresses:**
1. Profile with `python -m cProfile`
2. Check for redundant loops
3. Verify spatial index usage
4. Compare data structure access patterns

**If behavior differs:**
1. Add assert statements for key invariants
2. Log preference lists and compare
3. Trace pairing establishment step-by-step
4. Verify distance calculations and tie-breaking

**Get help:**
- Review `.cursor/rules/vmt-7-phase-engine.mdc`
- Check `docs/2_technical_manual.md`
- Look at similar patterns in existing systems
- Ask for clarification on unclear requirements

---

## Appendix: Quick Reference Commands

```bash
# Run full test suite
pytest tests/ -v

# Run specific phase tests
pytest tests/test_phase1_protocol_regression.py -v

# Check type safety
mypy src/vmt_engine/protocols/

# Format code
black src/vmt_engine/protocols/

# Lint code
ruff check src/vmt_engine/protocols/

# Run with protocol override
python main.py scenarios/mixed.yaml --matching-protocol greedy

# Compare telemetry
python scripts/compare_telemetry.py logs/before.db logs/after.db

# Benchmark performance
pytest tests/test_performance_protocols.py --benchmark-only
```

---

**End of Implementation Guide**
