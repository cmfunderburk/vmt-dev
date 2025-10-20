# VMT Protocol Modularization: Implementation Plan

*A synthesis approach combining architectural rigor with VMT-specific pragmatism*

---

## Part I: Conceptual Foundation

### 1. Why Modularize? Foundational Principles

The current VMT simulation engine, while functionally complete and deterministic, presents significant barriers to extensibility through its monolithic structure. Any modification to search behavior or matching algorithms requires direct changes to the core engine, increasing the risk of introducing bugs and making the system difficult for new contributors to understand and extend safely.

To overcome these limitations, we adopt three foundational principles of modular architecture:

* **Separation of Concerns:** Each module should have a single, well-defined responsibility. In VMT's context, the logic for how an agent *finds* opportunities (Search) must be entirely separate from the logic that *determines partnerships* (Matching), which in turn is separate from *trade execution* (Bargaining).

* **High Cohesion:** Functionality that is conceptually related should be grouped together within a single module. All code related to a specific matching algorithm (e.g., stable matching) should reside in its own dedicated module.

* **Low Coupling:** Modules should have minimal dependencies on one another, interacting through stable, well-defined interfaces. This allows one matching algorithm to be replaced with another with zero impact on the search or trade systems.

By adhering to these principles, the refactored engine becomes more maintainable, testable, and—critically for research and education—extensible.

### 2. The Strategy Pattern: Enabling Runtime Flexibility

The **Strategy design pattern** is the architectural foundation for achieving runtime flexibility in VMT. This behavioral pattern defines a family of algorithms, encapsulates each one, and makes them interchangeable. The pattern consists of three key components that map directly to VMT's architecture:

* **Context:** The `SimulationEngine` that orchestrates the 7-phase tick cycle. It holds references to strategy objects but remains unaware of their concrete implementations.

* **Strategy:** The common interfaces—`SearchProtocol` and `MatchingProtocol`—that define the contract all implementations must follow.

* **Concrete Strategy:** The individual implementations—`ThreePassPairingMatching`, `GreedyMatching`, `StableMatching`—that contain the actual algorithmic logic.

#### Example: The Engine as Context

```python
class SimulationEngine:
    """
    The Context class that uses interchangeable protocol strategies.
    """
    def __init__(self, search_protocol: SearchProtocol, matching_protocol: MatchingProtocol):
        """
        The engine is initialized with concrete strategy objects,
        but only knows about them through their abstract interfaces.
        """
        self.search_protocol = search_protocol
        self.matching_protocol = matching_protocol
        self.state = SimulationState()
    
    def run_decision_phase(self):
        """
        Phase 2 of the 7-phase cycle: Decision
        """
        for agent in sorted(self.state.agents, key=lambda a: a.id):  # Deterministic ordering
            perception = self.perception_system.get_view(agent)
            target = self.search_protocol.select_search_target(agent, perception)
            agent.set_forage_target(target)
        
        # Build preferences and find matches via MatchingProtocol
        preferences = self.matching_protocol.build_preferences(self.state.agents)
        matches = self.matching_protocol.find_matches(preferences)
        for agent_i, agent_j in matches:
            self.state.pair_agents(agent_i, agent_j)
```

This approach cleanly separates VMT's state management and tick orchestration from the specific algorithmic implementations, preventing the engine's core logic from becoming entangled with protocol details.

### 3. Migration Philosophy: Incremental and Risk-Averse

The transition follows the **Strangler Fig pattern**: gradually replacing pieces of the monolithic system while keeping the entire application functional throughout. This minimizes disruption and allows continuous validation at each step.

**Core Principle:** Start by making the existing behavior available through the new interfaces, validate perfect backward compatibility, then—and only then—introduce novel implementations.

---

## Part II: VMT-Specific Design

### 4. Protocol Interface Definitions

These interfaces are designed specifically for VMT's agent-based, spatial simulation architecture, respecting its unique constraints and patterns.

#### SearchProtocol Interface

```python
from abc import ABC, abstractmethod
from typing import Optional
from vmt_engine.core import Agent, Position

class SearchProtocol(ABC):
    """How agents explore their spatial environment to find opportunities."""
    
    @abstractmethod
    def select_search_target(self, agent: Agent, perception: PerceptionView) -> Position:
        """
        Choose where the agent should move/search next.
        
        Args:
            agent: The searching agent with inventory and preferences
            perception: Spatial view including neighbors, resources, and prices
            
        Returns:
            Position to move toward (may be current position to stay)
            
        Note: Must be deterministic—use agent.id for tie-breaking
        """
        pass
    
    @abstractmethod
    def evaluate_opportunity(self, agent: Agent, target: Target) -> float:
        """
        Score a potential target (resource cell or trading partner).
        
        Args:
            agent: The evaluating agent
            target: Either a ResourceCell or another Agent
            
        Returns:
            Numeric score (higher is better, negative means avoid)
        """
        pass
```

#### MatchingProtocol Interface

```python
class MatchingProtocol(ABC):
    """How agents form bilateral partnerships for trade."""
    
    @abstractmethod
    def build_preferences(self, agents: list[Agent]) -> dict[int, list[int]]:
        """
        Compute a ranked list of preferred partner IDs for each agent.
        
        Args:
            agents: All agents eligible for matching this tick
            
        Returns:
            Dictionary mapping agent.id -> ordered list of preferred partner IDs
            
        Note: Empty preference list means agent prefers to forage alone
        """
        pass
    
    @abstractmethod
    def find_matches(self, preferences: dict[int, list[int]]) -> list[tuple[int, int]]:
        """
        Return a set of matched agent pairs.
        
        Args:
            preferences: Output from build_preferences()
            
        Returns:
            List of (agent_i_id, agent_j_id) pairs, where i < j
            
        Guarantees:
            - No agent appears in more than one pair
            - Pairs are ordered (smaller ID first) for determinism
            - Result is reproducible given same preferences
        """
        pass
```

### 5. Mapping to the 7-Phase Tick Cycle

The protocols integrate into VMT's existing phases without disrupting the sacred order:

1. **Perception Phase:** Unchanged—agents observe environment snapshot
2. **Decision Phase:** 
   - Agents use `SearchProtocol.select_search_target()` to choose movement
   - Engine uses `MatchingProtocol.build_preferences()` and `.find_matches()` for pairing
3. **Movement Phase:** Unchanged—agents move toward chosen targets
4. **Trade Phase:** Unchanged—paired agents execute trades
5. **Foraging Phase:** Unchanged—unpaired agents harvest resources
6. **Resource Regeneration:** Unchanged—environment updates
7. **Housekeeping:** Unchanged—quotes refresh, telemetry logs

This preserves VMT's deterministic execution order while allowing flexibility within each phase.

### 6. Concrete Implementations

#### 6.1 Legacy Wrapper (Default)

```python
class ThreePassPairingMatching(MatchingProtocol):
    """
    Wraps VMT's current 3-pass pairing algorithm for backward compatibility.
    Pass 1: Distance-based mutual interest
    Pass 2: Price-agreement mutual interest  
    Pass 3: Greedy surplus maximization
    """
    def build_preferences(self, agents: list[Agent]) -> dict[int, list[int]]:
        # Delegate to existing DecisionSystem.build_preferences_three_pass()
        return self.legacy_system.build_preferences_three_pass(agents)
    
    def find_matches(self, preferences: dict[int, list[int]]) -> list[tuple[int, int]]:
        # Delegate to existing DecisionSystem.execute_three_pass_matching()
        return self.legacy_system.execute_three_pass_matching(preferences)
```

#### 6.2 New Implementations

```python
class GreedyMatching(MatchingProtocol):
    """Maximize total discounted surplus across all pairs."""
    
    def build_preferences(self, agents: list[Agent]) -> dict[int, list[int]]:
        preferences = {}
        for agent_i in agents:
            # Compute surplus with each potential partner
            potential_partners = []
            for agent_j in agents:
                if agent_i.id != agent_j.id:
                    surplus = self._compute_discounted_surplus(agent_i, agent_j)
                    if surplus > 0:
                        potential_partners.append((surplus, agent_j.id))
            
            # Sort by surplus (descending), break ties by agent ID
            potential_partners.sort(key=lambda x: (-x[0], x[1]))
            preferences[agent_i.id] = [partner_id for _, partner_id in potential_partners]
        
        return preferences
    
    def find_matches(self, preferences: dict[int, list[int]]) -> list[tuple[int, int]]:
        # Collect all potential pairs with their surplus values
        all_pairs = []
        surplus_cache = {}
        
        for agent_i_id, pref_list in preferences.items():
            for agent_j_id in pref_list:
                if agent_i_id < agent_j_id:  # Avoid duplicates
                    pair_key = (agent_i_id, agent_j_id)
                    if pair_key not in surplus_cache:
                        surplus = self._get_cached_surplus(agent_i_id, agent_j_id)
                        all_pairs.append((surplus, agent_i_id, agent_j_id))
        
        # Sort by surplus (descending), break ties deterministically
        all_pairs.sort(key=lambda x: (-x[0], x[1], x[2]))
        
        # Greedy assignment
        matched = set()
        matches = []
        for _, i, j in all_pairs:
            if i not in matched and j not in matched:
                matches.append((i, j))
                matched.update({i, j})
        
        return matches

class StableMatching(MatchingProtocol):
    """Gale-Shapley deferred acceptance algorithm."""
    
    def find_matches(self, preferences: dict[int, list[int]]) -> list[tuple[int, int]]:
        # Implementation of propose-and-reject cycles
        # ensuring no blocking pairs in final matching
        ...
```

---

## Part III: Implementation Strategy

### 7. Phase 1: Add Protocol Interfaces + Legacy Wrappers

**Duration:** 1-2 weeks

**Objectives:**
- Define `SearchProtocol` and `MatchingProtocol` Abstract Base Classes
- Create `ThreePassPairingMatching` wrapper around existing logic
- Create `PerceptionBasedSearch` wrapper around existing search
- Add protocol fields to `SimulationEngine` 
- Ensure all existing tests pass unchanged

**Deliverable:** The engine runs through new interfaces but with identical behavior.

**Validation:** Run regression suite—all scenarios produce byte-identical telemetry logs.

### 8. Phase 2: Validate Backward Compatibility

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
    
    # Run with old monolithic engine
    old_engine = LegacySimulation(scenario, seed)
    old_telemetry = old_engine.run()
    
    # Run with new engine + legacy protocols
    new_engine = SimulationEngine(
        search_protocol=PerceptionBasedSearch(),
        matching_protocol=ThreePassPairingMatching()
    )
    new_telemetry = new_engine.run(scenario, seed)
    
    # Deep comparison of all telemetry tables
    assert_telemetry_identical(old_telemetry, new_telemetry)
```

### 9. Phase 3: Implement New Protocols

**Duration:** 2-3 weeks

**Objectives:**
- Implement `GreedyMatching` with full test coverage
- Implement `StableMatching` (Gale-Shapley)
- Implement `GradientSearch` (moves toward highest-value targets)
- Implement `RandomWalkSearch` (baseline random movement)
- Create demonstration scenarios for each

**Deliverable:** Working alternative protocols with test coverage > 90%.

### 10. Phase 4: Extend

**Duration:** Ongoing

**Objectives:**
- Enable protocol selection via YAML configuration
- Create protocol registry for dynamic loading
- Documentation and tutorials for creating custom protocols
- Example: `ReinforcementLearningSearch`, `AuctionMatching`

**Configuration Example:**
```yaml
name: stable_matching_demo
agents: 20
grid:
  size: 10
  
protocols:
  search: "gradient_ascent"      # Move toward highest-value opportunities
  matching: "stable_matching"    # Gale-Shapley algorithm
  
# No protocol specified = use legacy defaults
```

---

## Part IV: Integration Details

### 11. Scenario Schema Changes

Extend `src/scenarios/schema.py` to support optional protocol specification:

```python
class ProtocolConfig(BaseModel):
    """Protocol configuration options."""
    search: str = "legacy_perception_based"
    matching: str = "legacy_three_pass"
    
class ScenarioConfig(BaseModel):
    """Extended scenario configuration."""
    name: str
    agents: int
    protocols: Optional[ProtocolConfig] = None  # Backward compatible
    # ... other fields unchanged
```

Scenarios without `protocols` field run exactly as before. New scenarios can specify:

```yaml
protocols:
  matching: "greedy_surplus"  # Use new GreedyMatching implementation
```

### 12. Telemetry Extensions

Current telemetry structure remains unchanged. We add:

1. **Protocol metadata** in run_config table:
   ```sql
   ALTER TABLE run_config ADD COLUMN search_protocol TEXT;
   ALTER TABLE run_config ADD COLUMN matching_protocol TEXT;
   ```

2. **Protocol-specific metrics** (optional):
   ```sql
   CREATE TABLE IF NOT EXISTS protocol_metrics (
       tick INTEGER,
       protocol_name TEXT,
       metric_name TEXT,
       metric_value REAL,
       PRIMARY KEY (tick, protocol_name, metric_name)
   );
   ```

All protocols use existing `TelemetryManager` API to ensure data consistency:
```python
self.telemetry.log_pairing_event(tick, agent_i_id, agent_j_id, "paired")
self.telemetry.log_preferences(tick, agent_id, preference_list)
```

### 13. Testing & Determinism Requirements

#### Test Categories

1. **Unit Tests per Protocol**
   - Input/output validation
   - Edge cases (empty agents, no valid matches)
   - Determinism verification (same seed → same result)

2. **Integration Tests**
   - Search-only scenarios (agents explore, no trading)
   - Matching-only scenarios (static positions, form pairs)
   - Full simulation with mixed protocols

3. **Regression Tests**
   - Suite of 10+ existing scenarios
   - Compare telemetry: legacy vs. modular engine
   - Performance benchmarks (must stay within 10% of baseline)

4. **Determinism Tests**
   ```python
   def test_protocol_determinism():
       """Ensure protocols are fully deterministic."""
       protocol = GreedyMatching()
       agents = create_test_agents(count=50, seed=42)
       
       # Run 100 times with same input
       results = []
       for _ in range(100):
           preferences = protocol.build_preferences(agents)
           matches = protocol.find_matches(preferences)
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

## Success Criteria

The modularization is successful when:

1. **Backward Compatibility:** Existing scenarios run unchanged with identical outputs
2. **Performance:** No more than 10% slowdown on standard benchmarks
3. **Extensibility:** A new matching algorithm can be added without modifying core engine
4. **Testing:** >95% code coverage on all protocols
5. **Documentation:** Clear guides for implementing custom protocols
6. **Determinism:** 100% reproducible results with same seed + configuration

---

## Appendix: Key Design Decisions

### Why Not Plugin Manager with `__init_subclass__`?

While elegant for large plugin ecosystems, VMT's focused scope (search, matching, eventually bargaining) makes a simple registry pattern more appropriate. We can always add dynamic discovery later if needed.

### Why Not Order Books and Market Abstractions?

VMT is fundamentally an agent-based spatial simulation, not a centralized market. Agents don't submit orders to a book; they discover opportunities through spatial exploration and form bilateral partnerships. The protocol interfaces reflect this reality.

### Why Start with Matching, Not Search?

Matching algorithms (greedy, stable, auction-based) have well-defined theoretical properties that make them ideal for validation. Search is more contextual and harder to verify correctness for. Starting with matching provides clearer success metrics.

---

## References

- VMT Technical Manual (`src/vmt_engine/README.md`)
- VMT Core Principles (7-phase cycle, determinism requirements)
- Current implementation (`src/vmt_engine/systems/decision.py`)
- Telemetry schema (`src/telemetry/database.py`)
- Scenario schema (`src/scenarios/schema.py`)
