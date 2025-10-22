# VMT Protocol Modularization: Implementation Plan

*A synthesis approach combining architectural rigor with VMT-specific pragmatism*

**Document Status:** Working Draft  
**Last Updated:** 2025-10-20  
**Version:** 2.0

---

## Executive Summary

This document specifies a comprehensive refactoring of VMT's Decision phase to enable runtime-swappable behavioral algorithms through the Strategy pattern. The refactoring maintains 100% backward compatibility while establishing a foundation for extensibility in search, matching, and future bargaining protocols.

**Key Architectural Changes:**
- Introduction of `SearchProtocol` and `MatchingProtocol` abstract interfaces
- Creation of `ProtocolContext` for parameter passing and state access
- Phased migration using legacy wrapper pattern
- Zero changes to the 7-phase tick cycle order

**Deferred Design Questions:**
- `PerceptionView` vs. dict inconsistency (Issue 1.1) - requires separate technical decision
- `Target` type definition (Issue 1.2) - respects existing `decision.py` behavior, to be formalized

---

## Part I: Conceptual Foundation

### 1. Why Modularize? Foundational Principles

The current VMT simulation engine, while functionally complete and deterministic, presents significant barriers to extensibility through its monolithic structure. Any modification to search behavior or matching algorithms requires direct changes to the core engine, increasing the risk of introducing bugs and making the system difficult for new contributors to understand and extend safely.

To overcome these limitations, we adopt three foundational principles of modular architecture:

* **Separation of Concerns:** Each module should have a single, well-defined responsibility. In VMT's context, the logic for how an agent *finds* opportunities (Search) must be entirely separate from the logic that *determines partnerships* (Matching), which in turn is separate from *trade execution* (Bargaining - future work).

* **High Cohesion:** Functionality that is conceptually related should be grouped together within a single module. All code related to a specific matching algorithm (e.g., stable matching) should reside in its own dedicated module.

* **Low Coupling:** Modules should have minimal dependencies on one another, interacting through stable, well-defined interfaces. This allows one matching algorithm to be replaced with another with zero impact on the search or trade systems.

By adhering to these principles, the refactored engine becomes more maintainable, testable, and—critically for research and education—extensible.

### 2. The Strategy Pattern: Enabling Runtime Flexibility

The **Strategy design pattern** is the architectural foundation for achieving runtime flexibility in VMT. This behavioral pattern defines a family of algorithms, encapsulates each one, and makes them interchangeable. The pattern consists of three key components that map directly to VMT's architecture:

* **Context:** The `Simulation` engine that orchestrates the 7-phase tick cycle. It holds references to strategy objects but remains unaware of their concrete implementations.

* **Strategy:** The common interfaces—`SearchProtocol` and `MatchingProtocol`—that define the contract all implementations must follow.

* **Concrete Strategy:** The individual implementations—`ThreePassPairingMatching`, `GreedyMatching`, `StableMatching`—that contain the actual algorithmic logic.

#### Example: The Engine as Context

```python
class Simulation:
    """
    The Context class that uses interchangeable protocol strategies.
    """
    def __init__(self, scenario_config, seed, 
                 search_protocol: Optional[SearchProtocol] = None,
                 matching_protocol: Optional[MatchingProtocol] = None):
        """
        The engine is initialized with concrete strategy objects,
        but only knows about them through their abstract interfaces.
        
        If protocols are None, defaults to legacy implementations.
        """
        self.search_protocol = search_protocol or LegacySearchProtocol()
        self.matching_protocol = matching_protocol or ThreePassPairingMatching()
        
        # ... existing initialization code
```

This approach cleanly separates VMT's state management and tick orchestration from the specific algorithmic implementations, preventing the engine's core logic from becoming entangled with protocol details.

### 3. Migration Philosophy: Incremental and Risk-Averse

The transition follows the **Strangler Fig pattern**: gradually replacing pieces of the monolithic system while keeping the entire application functional throughout. This minimizes disruption and allows continuous validation at each step.

**Core Principle:** Start by making the existing behavior available through the new interfaces, validate perfect backward compatibility, then—and only then—introduce novel implementations.

**Critical Constraint:** Search and matching are tightly coupled in the current Decision phase. They must be refactored together—we cannot modularize one without the other. The phased approach handles this by wrapping both simultaneously in Phase 1, then validating them together.

---

## Part II: VMT-Specific Design

### 4. Protocol Context Object

To avoid parameter proliferation and provide protocols with necessary simulation state, we introduce a `ProtocolContext` object:

```python
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import Agent, Grid
    from .core.spatial_index import SpatialIndex

@dataclass(frozen=True)
class ProtocolContext:
    """
    Immutable context providing protocols access to simulation parameters and state.
    
    Design principle: Protocols receive read-only access to simulation state,
    preventing accidental state corruption.
    """
    # Simulation parameters (read-only)
    params: dict[str, Any]  # All scenario parameters
    
    # Current tick state
    current_tick: int
    current_mode: str  # "trade", "forage", or "both"
    
    # Spatial and agent state (read-only access)
    grid: 'Grid'
    agent_by_id: dict[int, 'Agent']
    spatial_index: 'SpatialIndex'
    
    # Resource claiming state (read-write through protocol methods)
    resource_claims: dict[tuple[int, int], int]  # position -> agent_id
    
    # Convenience accessors
    @property
    def beta(self) -> float:
        """Distance discount factor."""
        return self.params['beta']
    
    @property
    def vision_radius(self) -> int:
        """Agent vision radius."""
        return self.params['vision_radius']
    
    @property
    def interaction_radius(self) -> int:
        """Trade interaction radius."""
        return self.params['interaction_radius']
    
    @property
    def enable_resource_claiming(self) -> bool:
        """Whether resource claiming is enabled."""
        return self.params.get('enable_resource_claiming', False)
```

**Design Rationale:**
- **Frozen dataclass:** Prevents protocols from accidentally modifying simulation state
- **Single parameter:** Eliminates 5-10 individual parameters per method call
- **Typed access:** Provides IDE autocomplete and type checking
- **Extensible:** New parameters can be added without changing protocol signatures

### 5. Protocol Interface Definitions

These interfaces are designed specifically for VMT's agent-based, spatial simulation architecture, respecting its unique constraints and patterns.

#### 5.1 SearchProtocol Interface

```python
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING
from vmt_engine.core import Agent, Position, Cell

if TYPE_CHECKING:
    from .protocol_context import ProtocolContext

class SearchProtocol(ABC):
    """
    How agents explore their spatial environment to find opportunities.
    
    Responsibilities:
    - Evaluate forage targets (resource cells)
    - Select movement destinations
    - Respect resource claiming system
    - Handle mode-aware behavior (trade/forage/both)
    
    NOTE: Target type handling is implementation-specific. Current behavior
    defined in src/vmt_engine/systems/decision.py will be preserved.
    """
    
    @abstractmethod
    def select_forage_target(
        self, 
        agent: Agent, 
        perception_cache: dict,  # NOTE: Type TBD (Issue 1.1)
        context: ProtocolContext
    ) -> Optional[Position]:
        """
        Choose a resource cell to move toward and harvest.
        
        Args:
            agent: The foraging agent with inventory and preferences
            perception_cache: Current perception data (structure TBD)
            context: Simulation state and parameters
            
        Returns:
            Position of chosen resource cell, or None if no valid target
            
        Protocol Responsibilities:
        - Filter resource_cells based on context.resource_claims
        - Only return cells NOT claimed by other agents
        - Claim the selected resource by updating context.resource_claims
        - Must be deterministic—use agent.id for tie-breaking
        
        Mode Handling:
        - In "forage" mode: Always called
        - In "trade" mode: Never called
        - In "both" mode: Called as fallback if pairing fails
        """
        pass
    
    @abstractmethod
    def evaluate_resource_opportunity(
        self, 
        agent: Agent, 
        resource_cell: Cell,
        context: ProtocolContext
    ) -> float:
        """
        Score a potential resource target.
        
        Args:
            agent: The evaluating agent
            resource_cell: Cell with resource to evaluate
            context: Simulation parameters (includes beta for discounting)
            
        Returns:
            Numeric score (higher is better, negative means avoid)
            
        Note: Current implementation uses beta-discounted value based on
        distance and forage_rate. See movement.py:choose_forage_target()
        """
        pass
```

#### 5.2 MatchingProtocol Interface

```python
class MatchingProtocol(ABC):
    """
    How agents form bilateral partnerships for trade.
    
    Responsibilities:
    - Build ranked preference lists over potential partners
    - Determine final pairings
    - Respect trade cooldown constraints
    - Handle persistent pairing state
    - Support mode-aware behavior
    """
    
    @abstractmethod
    def build_preferences(
        self, 
        agents: list[Agent],
        context: ProtocolContext
    ) -> dict[int, list[tuple[int, float, float, int]]]:
        """
        Compute a ranked list of preferred partners for each agent.
        
        Args:
            agents: All agents eligible for matching this tick
            context: Simulation state and parameters
            
        Returns:
            Dictionary mapping agent.id -> preference list where each entry is:
                (partner_id, surplus, discounted_surplus, distance)
            List is sorted by (-discounted_surplus, partner_id) for determinism
            
        Protocol Responsibilities:
        - Check agent.trade_cooldowns and exclude partners still in cooldown
        - Compute surplus using shared utility: compute_surplus(agent, partner)
        - Apply beta-discounting: discounted_surplus = surplus * (beta ** distance)
        - Sort deterministically
        - Empty list means agent has no valid trade partners
        
        Mode Handling:
        - Only called in "trade" or "both" modes
        - In "forage" mode: Not invoked
        
        Cooldown Handling:
        - For each potential partner_id, check: agent.trade_cooldowns.get(partner_id)
        - If cooldown_tick exists and context.current_tick < cooldown_tick: skip partner
        - Otherwise, include partner and remove expired cooldown
        """
        pass
    
    @abstractmethod
    def find_matches(
        self, 
        preferences: dict[int, list[tuple[int, float, float, int]]],
        context: ProtocolContext
    ) -> list[tuple[int, int]]:
        """
        Return a set of matched agent pairs based on preferences.
        
        Args:
            preferences: Output from build_preferences()
            context: Simulation state (for accessing paired_with_id)
            
        Returns:
            List of (agent_i_id, agent_j_id) pairs, where i < j
            
        Guarantees:
        - No agent appears in more than one pair
        - Pairs are ordered (smaller ID first) for determinism
        - Result is reproducible given same preferences
        - Respects existing pairings (agents with paired_with_id != None are locked)
        
        Protocol Responsibilities:
        - Skip agents that are already paired (agent.paired_with_id is not None)
        - Update agent.paired_with_id for newly matched agents
        - Update agent.target_pos and agent.target_agent_id to point at partner
        - Clear mutual cooldowns between paired agents
        """
        pass
```

### 6. Mapping to the 7-Phase Tick Cycle

The protocols integrate into VMT's existing phases without disrupting the sacred order:

1. **Perception Phase:** Unchanged—agents observe environment snapshot
2. **Decision Phase:** **REFACTORED**
   - **Pass 1:** Target selection
     - Paired agents: maintain existing targets (skip protocols)
     - Unpaired agents in trade/both mode: `MatchingProtocol.build_preferences()`
     - Unpaired agents needing forage: `SearchProtocol.select_forage_target()`
   - **Pass 2:** Mutual consent pairing (handled by `MatchingProtocol.find_matches()`)
   - **Pass 3:** Best-available fallback pairing (handled by `MatchingProtocol.find_matches()`)
   - **Pass 3b:** Unpaired trade target cleanup (see Section 6.2)
   - **Pass 4:** Logging and state cleanup
3. **Movement Phase:** Unchanged—agents move toward chosen targets
4. **Trade Phase:** Unchanged—paired agents execute trades
5. **Foraging Phase:** Unchanged—unpaired agents harvest resources
6. **Resource Regeneration:** Unchanged—environment updates
7. **Housekeeping:** Unchanged—quotes refresh, telemetry logs

This preserves VMT's deterministic execution order while allowing flexibility within Phase 2.

### 6.1 Pairing Lifecycle Management

**Critical Concept:** Trade pairings in VMT are **persistent across multiple ticks**, not ephemeral single-tick relationships.

#### Pairing Establishment

Pairings are created during Decision phase (Phase 2) through two mechanisms:

1. **Mutual Consent (Pass 2):** Both agents rank each other as their #1 choice
2. **Best-Available Fallback (Pass 3):** Greedy surplus-maximizing assignment of remaining agents

Once established, paired agents:
- Lock their `target_pos` to their partner's position
- Lock their `target_agent_id` to their partner's ID
- Set `paired_with_id` to create bidirectional link
- Clear mutual trade cooldowns
- Skip all search and matching logic in future ticks (until unpaired)

#### Pairing Persistence

In subsequent ticks, paired agents:
- **Skip matching protocol entirely** in Pass 1 (see `decision.py:38`)
- Maintain target lock on partner
- Move toward partner in Movement phase
- Attempt trade if within interaction radius
- Continue ignoring foraging opportunities (even in "both" mode)

This creates **exclusive commitment** between partners.

#### Pairing Termination

Pairings are cleared only under these conditions:

1. **Trade Failure:** After a trade attempt fails (no mutually beneficial exchange found)
   - Both agents unpaired
   - Mutual cooldowns set: `agent.trade_cooldowns[partner_id] = tick + cooldown_ticks`
   - Prevents immediate re-pairing
   
2. **Mode Switch:** Global mode change (e.g., "trade" → "forage")
   - All agents unpaired
   - NO cooldowns set (can re-pair immediately when mode returns)
   - Logged as `"mode_switch_{old}_to_{new}"` event

3. **Pairing Corruption:** Defensive integrity check detects bidirectional link broken
   - Rare edge case (should never happen in correct implementation)
   - Logged and cleared

#### Protocol Implications

**MatchingProtocol implementations MUST:**
- Check `agent.paired_with_id` before including agent in matching
- Never unpair agents (unpairing happens in Trade/Housekeeping phases)
- Respect that pairing is a long-term state, not a per-tick decision

**SearchProtocol implementations MUST:**
- Never be called for paired agents (engine guarantees this)
- Assume unpaired agents have cleared targets

### 6.2 Pass 3b: Unpaired Trade Target Cleanup

After Passes 2 and 3 complete, some agents may have selected a trade partner (`target_agent_id != None`) but failed to form a pairing. This happens when:
- Agent i wants to trade with agent j
- Agent j was paired with someone else
- Agent i remains unpaired with unfulfilled trade target

**Pass 3b Responsibilities:**

```python
def handle_unpaired_trade_targets(self, agents: list[Agent], context: ProtocolContext):
    """
    Clear unfulfilled trade targets and provide fallback activities.
    
    Executed after find_matches() completes.
    """
    for agent in sorted(agents, key=lambda a: a.id):
        # Skip paired agents (they're fine)
        if agent.paired_with_id is not None:
            continue
        
        # Skip agents without trade targets
        if agent.target_agent_id is None:
            continue
        
        # This agent wanted to trade but didn't get paired
        agent.target_agent_id = None
        agent.target_pos = None
        
        # Mode-specific fallback:
        if context.current_mode == "both":
            # Fall back to foraging
            forage_target = self.search_protocol.select_forage_target(
                agent, agent.perception_cache, context
            )
            agent.target_pos = forage_target
            agent._decision_target_type = "forage"
        else:
            # In pure "trade" mode, just idle (no foraging allowed)
            agent._decision_target_type = "idle"
```

**Design Note:** This pass ensures no agent enters Movement phase with invalid targets. It's critical for mode correctness and telemetry accuracy.

**Protocol Responsibility:** The engine handles Pass 3b, not the protocols themselves. Protocols only need to handle Passes 1-3.

### 7. Shared Utilities

Certain functions are used across multiple protocols and remain as shared utilities:

#### 7.1 compute_surplus()

**Location:** `src/vmt_engine/systems/matching.py`

```python
def compute_surplus(agent_i: Agent, agent_j: Agent) -> float:
    """
    Calculate trading surplus between two agents.
    
    Surplus measures the overlap between bid and ask prices.
    Positive surplus indicates potential for mutually beneficial trade.
    
    Returns:
        Maximum surplus across both trade directions (i→j and j→i)
        
    Note: This will eventually move to TradeProtocol/BargainingProtocol
    in future phases. For now, remains a shared utility.
    """
    # Implementation details in matching.py
    ...
```

**Usage by Protocols:**
```python
from vmt_engine.systems.matching import compute_surplus

class MyMatchingProtocol(MatchingProtocol):
    def build_preferences(self, agents, context):
        for agent_i in agents:
            for agent_j in agents:
                surplus = compute_surplus(agent_i, agent_j)
                # ... use surplus for ranking
```

**Future Work:** When `TradeProtocol`/`BargainingProtocol` is introduced (Phase 4+), `compute_surplus()` will become a method on that protocol interface. For this refactoring, it remains a shared utility to minimize scope.

### 8. Telemetry Responsibilities at Protocol Boundaries

Protocols focus on decision logic; the engine handles telemetry logging. This separation ensures consistent data structure across all protocol implementations.

#### 8.1 Telemetry Architecture

```
┌─────────────────────────────────────────────────────────┐
│ SimulationEngine (Phase 2: Decision)                    │
│                                                         │
│  1. Call protocol methods                               │
│  2. Protocols update agent state                        │
│  3. Engine logs state to telemetry                      │
└─────────────────────────────────────────────────────────┘
```

#### 8.2 What Protocols DO:

**MatchingProtocol responsibilities:**
- Store preference list on agent: `agent._preference_list = [(partner_id, surplus, ds, dist), ...]`
- Update pairing state: `agent.paired_with_id = partner_id`
- Update target state: `agent.target_agent_id`, `agent.target_pos`
- Set decision type: `agent._decision_target_type = "trade"`

**SearchProtocol responsibilities:**
- Update target state: `agent.target_pos = resource_position`
- Update claiming state: `context.resource_claims[pos] = agent.id`
- Set decision type: `agent._decision_target_type = "forage"`

#### 8.3 What Protocols DO NOT DO:

**Engine responsibilities (in Pass 4):**
```python
def _pass4_log_decisions(self, sim: Simulation):
    """
    Log all agent decisions after protocols complete.
    
    Reads state written by protocols and writes to telemetry database.
    """
    for agent in sorted(sim.agents, key=lambda a: a.id):
        # Read protocol output from agent state
        partner_id = agent.target_agent_id if agent.paired_with_id else None
        
        # Log to telemetry
        sim.telemetry.log_decision(
            tick=sim.tick,
            agent_id=agent.id,
            partner_id=partner_id,
            surplus=...,  # From agent._preference_list
            decision_type=agent._decision_target_type,
            ...
        )
        
        # Log preferences if enabled
        if sim.params.get('log_preferences', False):
            for rank, (pid, surplus, ds, dist) in enumerate(agent._preference_list):
                sim.telemetry.log_preference(
                    tick=sim.tick,
                    agent_id=agent.id,
                    partner_id=pid,
                    rank=rank,
                    surplus=surplus,
                    ...
                )
        
        # Clear temporary state
        agent._preference_list = []
        agent._decision_target_type = None
```

**Pairing event logging:**
```python
# Engine logs pairing events during Pass 2 and Pass 3
sim.telemetry.log_pairing_event(
    tick, agent_i_id, agent_j_id, 
    "pair", "mutual_consent",
    surplus_i, surplus_j
)
```

#### 8.4 Design Rationale

**Why this separation?**
1. **Consistency:** All telemetry follows same schema regardless of protocol
2. **Simplicity:** Protocol authors don't need to learn telemetry API
3. **Flexibility:** Telemetry format can evolve without changing protocols
4. **Debugging:** Engine can validate protocol output before logging

**State Contract:**
Protocols communicate with engine through well-defined agent state fields:
- `agent._preference_list` (temporary, cleared each tick)
- `agent._decision_target_type` (temporary, cleared each tick)
- `agent.target_pos` (persistent until reassigned)
- `agent.target_agent_id` (persistent until reassigned)
- `agent.paired_with_id` (persistent until unpaired)

---

## Part III: Implementation Strategy

### 9. Phase 1: Add Protocol Interfaces + Legacy Wrappers

**Duration:** 2-3 weeks

**Objectives:**
- Define `ProtocolContext` dataclass
- Define `SearchProtocol` and `MatchingProtocol` Abstract Base Classes
- Create `LegacySearchProtocol` wrapper around existing search logic
- Create `ThreePassPairingMatching` wrapper around existing pairing logic
- Add protocol fields to `Simulation.__init__()` with default instantiation
- Refactor `DecisionSystem` to delegate to protocols
- Ensure all existing tests pass unchanged

**Deliverable:** The engine runs through new interfaces but with identical behavior.

**Validation:** Run regression suite—all scenarios produce byte-identical telemetry logs.

### 10. Phase 1 Design Decisions

#### 10.1 Legacy Wrapper Implementation Approaches

**Decision Required:** How to wrap existing monolithic `DecisionSystem` logic?

##### Option A: Extraction with Shared State

**Approach:** Extract existing methods into protocol classes, sharing simulation state.

```python
class LegacySearchProtocol(SearchProtocol):
    """Wraps existing forage target selection logic."""
    
    def select_forage_target(self, agent, perception_cache, context):
        # Extract logic from decision.py:_evaluate_forage_target()
        resource_cells = perception_cache.get("resource_cells", [])
        
        # Filter claimed resources
        available = self._filter_claimed_resources(
            resource_cells, context.resource_claims, agent.id
        )
        
        # Call existing utility
        from vmt_engine.systems.movement import choose_forage_target
        target = choose_forage_target(
            agent, available, context.beta, context.params['forage_rate']
        )
        
        # Claim resource
        if target and context.enable_resource_claiming:
            context.resource_claims[target] = agent.id
        
        return target
```

**Pros:**
- Clean separation—protocols are standalone
- Easier to test in isolation
- Future protocols don't carry legacy baggage
- Clear migration path to full refactor

**Cons:**
- Requires extracting and duplicating some logic initially
- More upfront implementation work
- Need to ensure extracted code is truly identical

##### Option B: Delegation to Existing DecisionSystem

**Approach:** Keep existing `DecisionSystem` intact, protocols delegate to it.

```python
class LegacySearchProtocol(SearchProtocol):
    """Thin wrapper delegating to existing DecisionSystem."""
    
    def __init__(self, decision_system: DecisionSystem):
        self.decision_system = decision_system
    
    def select_forage_target(self, agent, perception_cache, context):
        # Build minimal simulation-like object for legacy code
        sim_adapter = SimulationAdapter(context)
        
        # Directly call existing method
        self.decision_system._evaluate_forage_target(
            agent, perception_cache, sim_adapter
        )
        
        return agent.target_pos  # Read result from agent state
```

**Pros:**
- Minimal initial implementation effort
- Guaranteed behavioral equivalence (using exact same code)
- Lower risk of introducing bugs during Phase 1

**Cons:**
- Creates dependency on legacy code structure
- Harder to test protocols in isolation
- SimulationAdapter is a code smell
- Delays the actual refactoring work

##### Option C: Hybrid Approach

**Approach:** Start with delegation (Phase 1), extract methods (Phase 2).

**Phase 1:**
```python
class LegacySearchProtocol(SearchProtocol):
    """Phase 1: Delegate to existing code."""
    def select_forage_target(self, agent, perception_cache, context):
        return self._legacy_delegate(agent, perception_cache, context)
```

**Phase 2:**
```python
class LegacySearchProtocol(SearchProtocol):
    """Phase 2: Extracted and refactored."""
    def select_forage_target(self, agent, perception_cache, context):
        # Now uses extracted, tested, standalone implementation
        return self._select_forage_target_impl(agent, perception_cache, context)
```

**Pros:**
- Balances risk and progress
- Establishes interfaces quickly (Phase 1)
- Allows validation before full refactor (Phase 2)
- Can test both implementations side-by-side

**Cons:**
- Two-step process delays full benefit
- Need to maintain both paths temporarily
- Requires discipline to complete Phase 2

#### 10.2 Backward Compatibility Implementation

**Decision Required:** How to ensure scenarios without `protocols` field work?

##### Option A: Simulation __init__() Default Arguments

**Approach:** Protocols are optional parameters with legacy defaults.

```python
class Simulation:
    def __init__(
        self,
        scenario_config: ScenarioConfig,
        seed: int,
        log_config: Optional[LogConfig] = None,
        search_protocol: Optional[SearchProtocol] = None,
        matching_protocol: Optional[MatchingProtocol] = None
    ):
        # Default to legacy if not provided
        if search_protocol is None:
            search_protocol = LegacySearchProtocol()
        if matching_protocol is None:
            matching_protocol = ThreePassPairingMatching()
        
        self.search_protocol = search_protocol
        self.matching_protocol = matching_protocol
        # ... rest of init
```

**Usage:**
```python
# Old code (no changes required)
sim = Simulation(scenario, seed=42)

# New code with custom protocols
sim = Simulation(
    scenario, 
    seed=42,
    matching_protocol=StableMatching()
)
```

**Pros:**
- Zero changes to existing code
- Pythonic default parameter pattern
- Easy to understand and document
- Type hints work correctly

**Cons:**
- Protocols hardcoded in Python, not in YAML
- Can't change protocols without editing Python code
- Less flexible for end users

##### Option B: Scenario YAML with Optional Field

**Approach:** Add optional `protocols` section to YAML schema.

```yaml
# scenarios/my_scenario.yaml
name: stable_matching_demo
agents: 20
grid_size: 10

protocols:  # Optional - omit for legacy behavior
  search: "legacy_perception_based"
  matching: "stable_matching"
```

```python
class ProtocolConfig(BaseModel):
    """Protocol configuration options."""
    search: str = "legacy_perception_based"
    matching: str = "legacy_three_pass"

class ScenarioConfig(BaseModel):
    # ... existing fields
    protocols: Optional[ProtocolConfig] = None
```

```python
# In Simulation.__init__()
if scenario_config.protocols is None:
    # No protocols specified → use legacy
    search_protocol = LegacySearchProtocol()
    matching_protocol = ThreePassPairingMatching()
else:
    # Load from registry
    search_protocol = PROTOCOL_REGISTRY[scenario_config.protocols.search]()
    matching_protocol = PROTOCOL_REGISTRY[scenario_config.protocols.matching]()
```

**Pros:**
- Protocols configurable per scenario
- No Python code changes needed to test new protocols
- Better for research use cases (quick experimentation)
- Telemetry automatically logs which protocols used

**Cons:**
- Need to implement protocol registry
- String-based lookup is more error-prone
- More complex initialization logic
- Harder to debug protocol loading errors

##### Option C: Hybrid (Default + Override)

**Approach:** YAML can specify, but Python can override.

```python
class Simulation:
    def __init__(
        self,
        scenario_config: ScenarioConfig,
        seed: int,
        search_protocol: Optional[SearchProtocol] = None,
        matching_protocol: Optional[MatchingProtocol] = None,
    ):
        # Priority: Python args > YAML config > Legacy defaults
        if search_protocol is None:
            if scenario_config.protocols:
                search_protocol = load_protocol(scenario_config.protocols.search)
            else:
                search_protocol = LegacySearchProtocol()
        
        self.search_protocol = search_protocol
        # ... similar for matching
```

**Pros:**
- Maximum flexibility
- Supports both programmatic and YAML-based usage
- Allows testing without YAML changes
- Production scenarios can use YAML

**Cons:**
- Most complex initialization logic
- Precedence rules must be documented
- Potential confusion about which takes priority

### 11. Phase 2: Validate Backward Compatibility

**Duration:** 1 week

**Objectives:**
- Create comprehensive regression test suite
- Compare telemetry outputs: old engine vs. new with legacy protocols
- Document any floating-point differences (must be < 1e-10)
- Performance benchmarks: ensure < 5% slowdown

**Deliverable:** Proven backward compatibility with performance metrics.

**Key Tests:**
```python
def test_legacy_protocol_equivalence():
    """Ensure legacy wrappers produce identical results."""
    seed = 12345
    scenario = load_scenario("test40grid50agents.yaml")
    
    # Run with refactored engine using legacy protocols
    sim = Simulation(
        scenario, 
        seed,
        search_protocol=LegacySearchProtocol(),
        matching_protocol=ThreePassPairingMatching()
    )
    sim.run(max_ticks=100)
    
    # Compare against baseline telemetry snapshot
    assert_telemetry_matches_baseline(sim.telemetry, "baseline_test40.db")

def test_determinism_with_protocols():
    """Protocols maintain determinism guarantee."""
    scenario = load_scenario("foundational_barter_demo.yaml")
    seed = 42
    
    results = []
    for trial in range(10):
        sim = Simulation(scenario, seed)  # Same seed each time
        sim.run(max_ticks=50)
        results.append(extract_telemetry_hash(sim.telemetry))
    
    # All runs must be identical
    assert len(set(results)) == 1, "Nondeterminism detected!"
```

### 12. Phase 3: Implement New Protocols

**Duration:** 2-3 weeks

**Objectives:**
- Implement `GreedyMatching` with full test coverage
- Implement `StableMatching` (Gale-Shapley)
- Implement `GradientSearch` (moves toward highest-value targets)
- Create demonstration scenarios for each
- Document protocol implementation guide

**Deliverable:** Working alternative protocols with test coverage > 90%.

**Example: GreedyMatching Implementation**

```python
class GreedyMatching(MatchingProtocol):
    """
    Maximize total discounted surplus across all pairs.
    
    Algorithm:
    1. Build preferences for all agents (with cooldown filtering)
    2. Create list of all potential pairs with their surplus values
    3. Sort by surplus (descending)
    4. Greedily assign pairs (each agent matched at most once)
    """
    
    def build_preferences(
        self, 
        agents: list[Agent], 
        context: ProtocolContext
    ) -> dict[int, list[tuple[int, float, float, int]]]:
        """Build beta-discounted preference lists."""
        from vmt_engine.systems.matching import compute_surplus
        
        preferences = {}
        
        for agent_i in sorted(agents, key=lambda a: a.id):
            # Skip already paired agents
            if agent_i.paired_with_id is not None:
                continue
            
            potential_partners = []
            
            for agent_j in agents:
                if agent_i.id == agent_j.id:
                    continue
                
                # Check cooldown
                if agent_j.id in agent_i.trade_cooldowns:
                    cooldown_until = agent_i.trade_cooldowns[agent_j.id]
                    if context.current_tick < cooldown_until:
                        continue  # Still in cooldown
                    else:
                        # Expired - remove
                        del agent_i.trade_cooldowns[agent_j.id]
                
                # Compute surplus
                surplus = compute_surplus(agent_i, agent_j)
                if surplus <= 0:
                    continue
                
                # Compute distance
                dx = abs(agent_i.pos[0] - agent_j.pos[0])
                dy = abs(agent_i.pos[1] - agent_j.pos[1])
                distance = dx + dy
                
                # Beta-discount
                discounted_surplus = surplus * (context.beta ** distance)
                
                potential_partners.append((
                    agent_j.id, surplus, discounted_surplus, distance
                ))
            
            # Sort by (-discounted_surplus, partner_id)
            potential_partners.sort(key=lambda x: (-x[2], x[0]))
            preferences[agent_i.id] = potential_partners
        
        return preferences
    
    def find_matches(
        self,
        preferences: dict[int, list[tuple[int, float, float, int]]],
        context: ProtocolContext
    ) -> list[tuple[int, int]]:
        """Greedy maximum-surplus matching."""
        
        # Collect all potential pairs with surplus
        all_pairs = []
        for agent_i_id, pref_list in preferences.items():
            for partner_id, surplus, ds, dist in pref_list:
                if agent_i_id < partner_id:  # Avoid duplicates
                    all_pairs.append((ds, agent_i_id, partner_id, surplus))
        
        # Sort by (-discounted_surplus, agent_i_id, partner_id)
        all_pairs.sort(key=lambda x: (-x[0], x[1], x[2]))
        
        # Greedy assignment
        matched = set()
        matches = []
        
        for ds, i, j, surplus in all_pairs:
            agent_i = context.agent_by_id[i]
            agent_j = context.agent_by_id[j]
            
            # Check availability
            if i not in matched and j not in matched:
                if agent_i.paired_with_id is None and agent_j.paired_with_id is None:
                    # Create pairing
                    agent_i.paired_with_id = j
                    agent_j.paired_with_id = i
                    
                    agent_i.target_pos = agent_j.pos
                    agent_i.target_agent_id = j
                    agent_j.target_pos = agent_i.pos
                    agent_j.target_agent_id = i
                    
                    # Clear cooldowns
                    agent_i.trade_cooldowns.pop(j, None)
                    agent_j.trade_cooldowns.pop(i, None)
                    
                    matches.append((i, j))
                    matched.update({i, j})
        
        return matches
```

### 13. Phase 4: Configuration & Extensibility

**Duration:** 1-2 weeks

**Objectives:**
- Finalize protocol registry system
- Complete YAML configuration integration
- Write protocol implementation tutorial
- Document testing requirements for custom protocols

**Deliverable:** End-to-end protocol customization pipeline.

---

## Part IV: Testing & Validation

### 14. Testing Requirements

#### Test Categories

1. **Unit Tests per Protocol**
   - Input/output validation
   - Edge cases (empty agents, no valid matches)
   - Determinism verification (same seed → same result)
   - Cooldown enforcement
   - Resource claiming compliance

2. **Integration Tests**
   - Search-only scenarios (agents explore, no trading)
   - Matching-only scenarios (static positions, form pairs)
   - Full simulation with mixed protocols
   - Mode switching behavior

3. **Regression Tests**
   - Suite of 10+ existing scenarios
   - Compare telemetry: legacy vs. modular engine
   - Performance benchmarks (must stay within 10% of baseline)

4. **Determinism Tests**
   ```python
   def test_protocol_determinism():
       """Ensure protocols are fully deterministic."""
       context = create_test_context(seed=42)
       protocol = GreedyMatching()
       agents = create_test_agents(count=50, seed=42)
       
       # Run 100 times with same input
       results = []
       for _ in range(100):
           # Reset agent state
           reset_agent_state(agents)
           preferences = protocol.build_preferences(agents, context)
           matches = protocol.find_matches(preferences, context)
           results.append(matches)
       
       # All results must be identical
       assert all(r == results[0] for r in results)
   ```

#### Critical Determinism Rules

Every protocol implementation MUST:
- Use sorted iteration: `for agent in sorted(agents, key=lambda a: a.id)`
- Break ties consistently: lowest agent.id wins
- Never use non-deterministic structures (sets for iteration, etc.)
- Document any random number usage (must use seeded RNG)

---

## Part V: Success Criteria & Design Decisions

### 15. Success Criteria

The modularization is successful when:

1. **Backward Compatibility:** Existing scenarios run unchanged with identical outputs
2. **Performance:** No more than 10% slowdown on standard benchmarks
3. **Extensibility:** A new matching algorithm can be added without modifying core engine
4. **Testing:** >95% code coverage on all protocols
5. **Documentation:** Clear guides for implementing custom protocols
6. **Determinism:** 100% reproducible results with same seed + configuration

### 16. Key Design Decisions Summary

#### Resolved Decisions

1. **ProtocolContext:** Single context object for parameter passing ✓
2. **Mode parameter:** Added to all protocol methods ✓
3. **Claims handled by protocols:** SearchProtocol manages resource_claims ✓
4. **Cooldowns handled by protocols:** MatchingProtocol filters cooldowns ✓
5. **compute_surplus():** Remains shared utility (moves to TradeProtocol later) ✓
6. **Telemetry separation:** Engine logs, protocols update agent state ✓
7. **Coupled refactoring:** Search and matching refactored together ✓

#### Open Decisions (Require Project Lead Input)

1. **Wrapper implementation:** Extraction vs Delegation vs Hybrid? (Section 10.1)
2. **Backward compatibility:** Python defaults vs YAML vs Hybrid? (Section 10.2)

#### Deferred Technical Issues

1. **PerceptionView type:** Dict vs dataclass inconsistency (Issue 1.1)
   - **Status:** Requires separate technical decision
   - **Current approach:** Use `perception_cache: dict` in interfaces
   - **Future work:** Unify once type decision made

2. **Target type:** Union[Cell, Agent, Position] formalization (Issue 1.2)
   - **Status:** Respects existing `decision.py` behavior
   - **Current approach:** Use `Optional[Position]` for now
   - **Future work:** Define formal Target type if needed

---

## Part VI: Future Work & Extensions

### 17. Future Protocol Types

#### 17.1 TradeProtocol / BargainingProtocol (Phase 5+)

**Motivation:** Currently, trade execution uses a monolithic "first-acceptable-trade" algorithm. Future work will modularize this.

**Interface Sketch:**
```python
class TradeProtocol(ABC):
    """How agents negotiate and execute bilateral trades."""
    
    @abstractmethod
    def compute_surplus(self, agent_i: Agent, agent_j: Agent) -> float:
        """Calculate potential gains from trade between two agents."""
        pass
    
    @abstractmethod
    def find_compensating_block(
        self, 
        buyer: Agent, 
        seller: Agent,
        context: ProtocolContext
    ) -> Optional[TradeBlock]:
        """
        Search for mutually beneficial integer exchange.
        
        Returns:
            TradeBlock(dA, dB, dM, price) or None if no valid trade
        """
        pass
```

**Implementations:**
- `FirstAcceptableTrade` (current algorithm)
- `MaxSurplusTrade` (exhaustive search)
- `NashBargaining` (split surplus by bargaining power)
- `AuctionTrade` (double auction mechanism)

**Timeline:** Not part of current refactoring. Estimated 4-6 weeks after Phase 4 complete.

#### 17.2 Market Protocol (Phase 6+)

**Motivation:** Support centralized exchange via market makers and order books.

**New entities:**
- `MarketMaker` agent type
- `LimitOrder` data structure
- `OrderBook` state management

**Would require:** New simulation phases (OrderPlacement, MarketClearing)

**Timeline:** Future research milestone, 3-6 months out.

### 18. Extension Points

#### Protocol Composition

Future work may allow composing protocols:
```yaml
protocols:
  matching:
    type: "composite"
    strategy:
      - "mutual_consent"  # Try this first
      - "stable_matching"  # Fall back to this
```

#### Adaptive Protocols

Protocols that learn and adapt:
```python
class ReinforcementLearningSearch(SearchProtocol):
    """Uses RL policy to select targets."""
    
    def __init__(self, model_path: str):
        self.policy = load_rl_model(model_path)
    
    def select_forage_target(self, agent, perception, context):
        state = self.encode_state(agent, perception)
        action = self.policy.predict(state)
        return self.decode_action(action, perception)
```

#### Multi-Agent Matching

Beyond bilateral pairing:
```python
class CoalitionMatching(MatchingProtocol):
    """Form groups of 3+ agents for coalition trades."""
    
    def find_matches(self, preferences, context):
        # Returns list of tuples with 2+ agents
        return [(agent1, agent2, agent3), ...]
```

---

## References

- VMT Technical Manual (`docs/2_technical_manual.md`)
- VMT Core Principles (`.cursor/rules/00_core_principles.mdc`)
- VMT Type System (`docs/4_typing_overview.md`)
- Current implementation (`src/vmt_engine/systems/decision.py`)
- Telemetry schema (`src/telemetry/database.py`)
- Scenario schema (`src/scenarios/schema.py`)

---

## Document History

**Version 1.0** (2025-10-20): Initial draft
**Version 2.0** (2025-10-20): Comprehensive revision addressing:
- Added ProtocolContext object
- Added mode parameters to interfaces
- Clarified protocol responsibilities for claims and cooldowns
- Added sections on pairing lifecycle, Pass 3b, telemetry responsibilities
- Added open decision sections for wrapper and backward compatibility
- Revised matching-first rationale
- Added future work section
- Documented deferred technical issues

