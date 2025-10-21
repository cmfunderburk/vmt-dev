# Discussion: Modularizing Search, Matching, and Bargaining Protocols

**Date**: 2025-10-20  
**Author**: VMT Development Team  
**Status**: Strategic Discussion Document  
**Purpose**: Explore the architectural pivot towards modular economic protocols

---

## Executive Summary

This document explores the strategic pivot to treat search, matching, and bargaining as first-class, modular components within VMT. The vision is to create atomic, composable economic protocols that can be studied in isolation or combined into rich, full simulations without requiring complex refactoring of the existing engine.

---

## 1. Architectural Vision

### Current State: Monolithic Integration

Currently, VMT's economic logic is deeply embedded within the 7-phase tick cycle:
- **Search** happens implicitly in Perception + Decision phases
- **Matching** is hardcoded in the 3-pass pairing algorithm  
- **Bargaining** is implicit in the compensating block search

This works well for the integrated simulation but makes it difficult to:
- Study individual mechanisms in isolation
- Compare different matching algorithms
- Test alternative bargaining protocols
- Extend the system with new economic behaviors

### Proposed State: Protocol-Based Architecture

```
┌─────────────────────────────────────────────────┐
│                 Full Simulation                  │
│  (Composes protocols via ScenarioAdapter)        │
└─────────────────┬───────────────────────────────┘
                  │ Uses
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌─────────┐ ┌──────────┐ ┌────────────┐
│ Search  │ │ Matching │ │ Bargaining │
│Protocol │ │ Protocol │ │  Protocol  │
└─────────┘ └──────────┘ └────────────┘
    △             △             △
    │             │             │
┌─────────┐ ┌──────────┐ ┌────────────┐
│Isolated │ │Isolated  │ │ Isolated   │
│Scenarios│ │Scenarios │ │ Scenarios  │
└─────────┘ └──────────┘ └────────────┘
```

Each protocol would:
1. Define a clear interface/contract
2. Be testable in isolation with minimal scenarios
3. Be composable into full simulations
4. Have its own telemetry and analysis tools

---

## 2. Benefits of Modularization

### 2.1 Research Advantages

**Controlled Experiments**
- Test matching algorithms in isolation (random, greedy, stable matching, etc.)
- Compare bargaining protocols without confounding factors (alternating offers, Nash bargaining, take-it-or-leave-it)
- Study search behaviors independently (random walk, gradient following, memory-based)

**Clean Baselines**
- Establish theoretical benchmarks for each component
- Easier to prove properties (efficiency, stability, fairness)
- Clear performance metrics per module

**Rapid Prototyping**
- New matching algorithm? Just implement the protocol interface
- Alternative bargaining model? Swap it in without touching core engine
- Custom search heuristic? Test it in isolation first

### 2.2 Pedagogical Advantages

**Progressive Complexity**
- Teach search theory with search-only scenarios
- Explain matching markets without spatial complications
- Demonstrate bargaining power without movement dynamics

**Clear Conceptual Boundaries**
- Students can focus on one economic concept at a time
- Easier to map classroom theory to simulation behavior
- Better alignment with textbook chapters

**Interactive Learning**
- "What happens if we change the matching algorithm?"
- "How does bargaining protocol affect surplus division?"
- "Can you design a search strategy that outperforms random walk?"

### 2.3 Engineering Advantages

**Maintainability**
- Clear separation of concerns
- Easier to locate and fix bugs
- Simpler unit testing

**Extensibility**
- New protocols can be added without modifying core engine
- Community contributions become easier
- Plugin-style architecture

**Performance**
- Optimize each protocol independently
- Swap in specialized implementations for different use cases
- Easier to parallelize isolated components

---

## 3. Challenges and Mitigation

### 3.1 Backward Compatibility

**Challenge**: Existing scenarios and analysis code expect the current integrated behavior.

**Mitigation**:
- Keep full simulation as default mode
- Existing scenarios run unchanged (they implicitly use "full" mode)
- New modular scenarios opt-in to isolated protocols
- Maintain legacy telemetry alongside new protocol-specific logging

### 3.2 Inter-Protocol Dependencies

**Challenge**: In reality, search, matching, and bargaining are interdependent.

**Mitigation**:
- Define clear data contracts between protocols
- Use event bus for loose coupling
- Allow protocols to share state through well-defined interfaces
- Full simulation mode orchestrates the interaction

### 3.3 Increased Complexity

**Challenge**: More abstractions, interfaces, and configuration options.

**Mitigation**:
- Start with simple, concrete implementations
- Provide sensible defaults
- Extensive documentation with examples
- GUI support for protocol configuration

---

## 4. Concrete Implementation Strategy

### 4.1 Protocol Interfaces

```python
# Conceptual sketches (not final implementations)

class SearchProtocol:
    """How agents explore their environment to find opportunities."""
    
    def select_search_target(self, agent: Agent, perception: PerceptionView) -> Position:
        """Choose where to search next."""
        pass
    
    def evaluate_opportunity(self, agent: Agent, target: Target) -> float:
        """Score a potential opportunity."""
        pass

class MatchingProtocol:
    """How agents form bilateral partnerships."""
    
    def build_preferences(self, agents: List[Agent]) -> Dict[int, List[int]]:
        """Each agent ranks potential partners."""
        pass
    
    def find_matches(self, preferences: Dict) -> List[Tuple[int, int]]:
        """Produce a set of matched pairs."""
        pass

class BargainingProtocol:
    """How matched agents determine terms of trade."""
    
    def negotiate(self, buyer: Agent, seller: Agent, good: str) -> Optional[TradeTerms]:
        """Determine if/how agents trade."""
        pass
    
    def compute_surplus_division(self, terms: TradeTerms) -> Tuple[float, float]:
        """How is surplus split between parties?"""
        pass
```

### 4.2 Isolated Scenario Examples

**Search-Only Scenario** (`scenarios/search/gradient_climb.yaml`)
```yaml
name: gradient_climb_search
simulation_type: search  # New field
agents: 20
# No trading, just movement towards high-value resources
# Telemetry focuses on: path efficiency, discovery time, exploration vs exploitation
```

**Matching-Only Scenario** (`scenarios/matching/stable_marriage.yaml`)
```yaml
name: stable_marriage_demo
simulation_type: matching
agents: 10
# No movement, instant matching based on preferences
# Telemetry focuses on: stability, efficiency, fairness metrics
```

**Bargaining-Only Scenario** (`scenarios/bargaining/ultimatum_game.yaml`)
```yaml
name: ultimatum_game
simulation_type: bargaining
agents: 2
# Fixed pair, multiple rounds of offers
# Telemetry focuses on: offer evolution, acceptance rates, surplus division
```

### 4.3 Composition in Full Simulation

```python
# Conceptual flow in full simulation mode

class FullSimulation:
    def __init__(self, scenario):
        # ScenarioAdapter configures protocols based on scenario
        self.search_protocol = load_protocol(scenario.search_config)
        self.matching_protocol = load_protocol(scenario.matching_config)
        self.bargaining_protocol = load_protocol(scenario.bargaining_config)
    
    def decision_phase(self):
        # Use search protocol for target selection
        for agent in self.agents:
            if agent.needs_partner:
                target = self.search_protocol.select_search_target(agent, perception)
            # ...
    
    def trade_phase(self):
        # Use matching protocol for pairing
        preferences = self.matching_protocol.build_preferences(candidates)
        matches = self.matching_protocol.find_matches(preferences)
        
        # Use bargaining protocol for trade execution
        for buyer_id, seller_id in matches:
            terms = self.bargaining_protocol.negotiate(buyer, seller, good)
            if terms:
                execute_trade(terms)
```

---

## 5. Research Opportunities

### 5.1 Comparative Studies

**Matching Algorithm Comparison**
- Random vs. Greedy vs. Deferred Acceptance
- Efficiency metrics: total surplus, number of trades, convergence time
- Fairness metrics: Gini coefficient of utilities, min/max welfare

**Bargaining Protocol Analysis**
- Nash Bargaining vs. Kalai-Smorodinsky vs. Alternating Offers
- How does protocol affect price discovery?
- Impact on wealth distribution

**Search Strategy Evaluation**
- Random walk vs. gradient ascent vs. memory-based
- Trade-off between exploration and exploitation
- Effect of information constraints

### 5.2 Novel Extensions

**Hybrid Protocols**
- Matching with partial commitment
- Bargaining with outside options
- Search with social learning

**Dynamic Protocol Switching**
- Agents learn which protocols work best
- Protocols evolve based on market conditions
- Meta-protocols that select protocols

**Multi-Stage Games**
- Search → Matching → Bargaining → Execution
- Each stage as a separate strategic game
- Backward induction and strategic sophistication

---

## 6. Pedagogical Applications

### 6.1 Course Modules

**Week 1-2: Search Theory**
- Random search baseline
- Directed search with information
- Search costs and stopping rules

**Week 3-4: Matching Markets**
- Stable matching (Gale-Shapley)
- Top trading cycles
- School choice mechanisms

**Week 5-6: Bargaining Theory**
- Nash bargaining solution
- Alternating offers (Rubinstein)
- Bargaining with incomplete information

**Week 7-8: Integrated Markets**
- How components interact
- Emergent phenomena from composition
- Market design considerations

### 6.2 Student Projects

- "Design a matching algorithm for [specific context]"
- "Implement and test a new bargaining protocol"
- "Compare search strategies in different environments"
- "Analyze how protocol choice affects market outcomes"

---

## 7. Migration Path

### Phase 0: Documentation & Planning (Current)
- This discussion document
- Gather feedback and refine vision
- Identify minimum viable protocol set

### Phase 1: Prototype Single Protocol
- Choose simplest protocol (likely search)
- Implement interface and one concrete strategy
- Create isolated test scenario
- Validate approach

### Phase 2: Expand Protocol Set
- Add matching protocol with 2-3 algorithms
- Add bargaining protocol with 2-3 strategies
- Create test scenarios for each

### Phase 3: Integration Layer
- Implement ScenarioAdapter
- Enable protocol composition in full simulation
- Ensure backward compatibility

### Phase 4: Migration & Documentation
- Update existing scenarios to explicitly specify protocols
- Document new capabilities
- Create tutorials and examples

### Phase 5: Advanced Features
- GUI protocol configuration
- Protocol-specific telemetry dashboards
- Comparative analysis tools

---

## 8. Key Design Decisions

### 8.1 Protocol Granularity

**Option A: Fine-Grained** (Many small protocols)
- SearchProtocol, MatchingProtocol, BargainingProtocol, PricingProtocol, CommitmentProtocol, etc.
- Pros: Maximum flexibility, clear separation
- Cons: Complex composition, many interfaces

**Option B: Coarse-Grained** (Few large protocols)
- TradingProtocol (includes matching + bargaining), MovementProtocol (includes search)
- Pros: Simpler to understand, fewer abstractions
- Cons: Less flexibility, harder to test in isolation

**Recommendation**: Start coarse, refine as needed.

### 8.2 Configuration Approach

**Option A: Protocol Names in Scenarios**
```yaml
protocols:
  search: "gradient_ascent"
  matching: "greedy_surplus"
  bargaining: "nash_solution"
```

**Option B: Protocol Objects in Code**
```python
sim = Simulation(
    scenario,
    search_protocol=GradientAscentSearch(),
    matching_protocol=GreedySurplusMatching(),
    bargaining_protocol=NashBargaining()
)
```

**Option C: Registry Pattern**
```python
ProtocolRegistry.register("search", "gradient", GradientAscentSearch)
# Scenarios reference registered names
```

**Recommendation**: Registry pattern for flexibility + configuration.

### 8.3 Telemetry Strategy

**Option A: Unified Telemetry**
- All protocols write to same tables
- Pros: Consistent, comparable
- Cons: May not capture protocol-specific metrics

**Option B: Protocol-Specific Tables**
- Each protocol has own telemetry schema
- Pros: Tailored metrics, cleaner
- Cons: More complex analysis

**Option C: Hybrid**
- Core tables for common metrics
- Extension tables for protocol-specific data
- Best of both worlds

**Recommendation**: Hybrid approach.

---

## 9. Success Metrics

### Technical Success
- [ ] Protocols can run in isolation with <100 lines of scenario code
- [ ] Full simulation performance within 10% of current
- [ ] 100% backward compatibility with existing scenarios
- [ ] Each protocol has 3+ implementations

### Research Success
- [ ] Publish comparison of 5+ matching algorithms
- [ ] Demonstrate previously impossible experiments
- [ ] Enable new research questions
- [ ] Community contributions of new protocols

### Pedagogical Success
- [ ] Course materials aligned with protocol structure
- [ ] Students can implement custom protocols
- [ ] Clear learning progression from atomic to composed
- [ ] Improved conceptual understanding metrics

---

## 10. Open Questions for Discussion

1. **Scope**: Should we include "foraging" as a separate protocol, or is it part of "search"?

2. **State Management**: How much state should protocols be allowed to maintain between ticks?

3. **Communication**: Should protocols communicate directly or only through the simulation core?

4. **Determinism**: How do we maintain determinism with pluggable protocols?

5. **Performance**: What's the acceptable performance overhead for this flexibility?

6. **Defaults**: What should be the default protocol set for new users?

7. **Visualization**: How do isolated protocol scenarios get visualized?

8. **Migration Timeline**: How aggressive should we be in moving to this architecture?

---

## 11. Next Steps

1. **Gather Feedback**: Share this document with stakeholders
2. **Prototype Decision**: Choose first protocol to prototype
3. **Interface Design**: Draft concrete protocol interfaces
4. **Proof of Concept**: Implement minimal working example
5. **Evaluation**: Assess feasibility and refine approach

---

## Appendix A: Example Protocol Implementations

### A.1 Simple Search Protocol

```python
class RandomWalkSearch(SearchProtocol):
    """Baseline random search strategy."""
    
    def select_search_target(self, agent: Agent, perception: PerceptionView) -> Position:
        # Random direction from current position
        directions = [(0,1), (0,-1), (1,0), (-1,0)]
        dx, dy = random.choice(directions)
        new_x = agent.pos[0] + dx * agent.move_budget_per_tick
        new_y = agent.pos[1] + dy * agent.move_budget_per_tick
        return (new_x, new_y)

class GradientSearch(SearchProtocol):
    """Follow gradient of opportunity value."""
    
    def select_search_target(self, agent: Agent, perception: PerceptionView) -> Position:
        best_value = -inf
        best_pos = agent.pos
        
        for resource in perception.resource_cells:
            value = self.evaluate_opportunity(agent, resource)
            if value > best_value:
                best_value = value
                best_pos = resource.position
        
        return best_pos
```

### A.2 Simple Matching Protocol

```python
class GreedyMatching(MatchingProtocol):
    """Match highest-surplus pairs first."""
    
    def find_matches(self, preferences: Dict) -> List[Tuple[int, int]]:
        # Collect all possible pairs with surplus
        all_pairs = []
        for agent_id, pref_list in preferences.items():
            for partner_id, surplus in pref_list:
                if surplus > 0:
                    all_pairs.append((surplus, agent_id, partner_id))
        
        # Sort by surplus (highest first)
        all_pairs.sort(reverse=True)
        
        # Greedily assign
        matched = set()
        matches = []
        for surplus, a, b in all_pairs:
            if a not in matched and b not in matched:
                matches.append((a, b))
                matched.add(a)
                matched.add(b)
        
        return matches
```

### A.3 Simple Bargaining Protocol

```python
class SplitSurplusBargaining(BargainingProtocol):
    """Equal split of surplus."""
    
    def negotiate(self, buyer: Agent, seller: Agent, good: str) -> Optional[TradeTerms]:
        # Find prices where both benefit
        min_price = seller.quotes[f'ask_{good}_in_M']
        max_price = buyer.quotes[f'bid_{good}_in_M']
        
        if min_price <= max_price:
            # Split the difference
            price = (min_price + max_price) / 2
            return TradeTerms(good, price, quantity=1)
        return None
    
    def compute_surplus_division(self, terms: TradeTerms) -> Tuple[float, float]:
        # Equal split
        total_surplus = terms.buyer_value - terms.seller_cost
        return (total_surplus/2, total_surplus/2)
```

---

## Appendix B: Scenario Evolution Examples

### Current Integrated Scenario
```yaml
name: three_agent_barter
agents: 3
# All behavior emerges from hardcoded systems
```

### With Explicit Protocols (Backward Compatible)
```yaml
name: three_agent_barter
agents: 3
protocols:  # Optional - defaults to current behavior
  search: "perception_based"  # Current implicit search
  matching: "three_pass_pairing"  # Current algorithm
  bargaining: "compensating_block"  # Current method
```

### New Modular Scenario
```yaml
name: test_stable_matching
simulation_type: matching  # Isolated protocol test
agents: 20
protocols:
  matching: "gale_shapley"  # Deferred acceptance algorithm
  
telemetry:
  focus: "matching_stability"  # Protocol-specific metrics
  
# No movement, no bargaining - pure matching
```

---

This discussion document provides a foundation for thinking through the modularization strategy. The key insight is that by treating search, matching, and bargaining as first-class protocols with clear interfaces, we can:

1. Study each mechanism in isolation
2. Compare alternative implementations
3. Compose them into rich simulations
4. Maintain backward compatibility
5. Enable new research and pedagogical applications

The path forward involves careful prototyping, starting with a single protocol to validate the approach before committing to a full architectural change.
