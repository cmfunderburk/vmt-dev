# Alternative Protocol Implementation Plan

**Document Status:** Planning - Phase 2  
**Version:** 1.0  
**Created:** 2025-10-27  
**Purpose:** Plan implementation of alternative protocols for comparative analysis

---

## Current Status

### Phase 1 Complete ✅

**What's Done:**
- ✅ Protocol infrastructure in place (`src/vmt_engine/protocols/`)
- ✅ Base classes: `ProtocolBase`, `SearchProtocol`, `MatchingProtocol`, `BargainingProtocol`
- ✅ Effect system: 10+ effect types for declarative state changes
- ✅ WorldView: Immutable context for protocols
- ✅ Registry system: Protocol registration and lookup
- ✅ Legacy adapters: Search, Matching, Bargaining protocols working
- ✅ Systems refactored: DecisionSystem and TradeSystem are now orchestrators

**What This Enables:**
- Implement new protocols without modifying core simulation
- Compare different economic mechanisms side-by-side
- Test economic hypotheses through protocol variation
- Enable pedagogical demonstrations of institutional differences

---

## Protocol Categories

### 1. Search Protocols

**Purpose:** How agents discover trade opportunities and forage locations

**Legacy Implementation:**
- `LegacySearchProtocol` - Distance-discounted utility-based target selection

**Proposed Alternatives:**

#### 1.1 Random Walk Search
```python
class RandomWalkSearch(SearchProtocol):
    """Stochastic exploration for pedagogical scenarios."""
    name = "random_walk"
    version = "2025.10.27"
```

**Behavior:**
- Agent moves randomly within vision radius
- No utility calculation required
- Pure exploration, no exploitation

**Use Cases:**
- Baseline for comparison
- Teaching information economics
- Demonstrating value of rational search

**Effort:** 2-3 hours

#### 1.2 Memory-Based Search
```python
class MemorySearch(SearchProtocol):
    """Agents remember profitable past interactions."""
    name = "memory_based"
    version = "2025.10.27"
```

**Behavior:**
- Maintains history of trading success by location/agent
- Explore vs exploit trade-off parameter
- Spatial price learning

**Use Cases:**
- Information and learning models
- Network formation dynamics
- Teaching adaptive behavior

**Effort:** 6-8 hours (multi-tick state)

#### 1.3 Myopic Search
```python
class MyopicSearch(SearchProtocol):
    """Agent only sees immediate neighbors (1-cell radius)."""
    name = "myopic"
    version = "2025.10.27"
```

**Behavior:**
- Overrides vision_radius to 1
- Demonstrates impact of information constraints
- Otherwise identical to legacy

**Use Cases:**
- Information economics
- Search cost demonstrations
- Network topology effects

**Effort:** 2 hours

---

### 2. Matching Protocols

**Purpose:** How agents form trading pairs

**Legacy Implementation:**
- `LegacyMatchingProtocol` - Three-pass with mutual consent and greedy fallback

**Proposed Alternatives:**

#### 2.1 Greedy Surplus Matching
```python
class GreedyMatching(MatchingProtocol):
    """Pure welfare maximization without mutual consent."""
    name = "greedy_surplus"
    version = "2025.10.27"
```

**Behavior:**
- Rank all possible pairs by total surplus
- Assign pairs greedily (highest surplus first)
- No mutual consent requirement

**Economic Properties:**
- Maximizes total surplus
- May violate individual rationality
- Useful for planner comparison

**Use Cases:**
- Market vs planner outcomes
- Efficiency analysis
- Teaching Pareto efficiency

**Effort:** 4-5 hours

#### 2.2 Random Matching
```python
class RandomMatching(MatchingProtocol):
    """Random pairing for baseline comparison."""
    name = "random"
    version = "2025.10.27"
```

**Behavior:**
- Randomly pair agents who want to trade
- No surplus calculation
- Pure chance

**Use Cases:**
- Baseline for other protocols
- Teaching value of information
- Null hypothesis for statistical testing

**Effort:** 2-3 hours

#### 2.3 Stable Matching (Gale-Shapley)
```python
class StableMatching(MatchingProtocol):
    """Deferred acceptance for stable outcomes."""
    name = "gale_shapley"
    version = "2025.10.27"
```

**Behavior:**
- Men propose, women accept/reject
- Guaranteed stable matching
- Multi-round within single tick

**Economic Properties:**
- No blocking pairs
- Strategy-proof for one side
- Classic matching theory

**Use Cases:**
- Teaching matching theory
- Stability vs efficiency trade-offs
- Market design principles

**Effort:** 6-8 hours

---

### 3. Bargaining Protocols

**Purpose:** How paired agents negotiate trade terms

**Legacy Implementation:**
- `LegacyBargainingProtocol` - Compensating block with feasibility checks

**Proposed Alternatives:**

#### 3.1 Take-It-Or-Leave-It
```python
class TakeItOrLeaveIt(BargainingProtocol):
    """Monopolistic offer with single response."""
    name = "take_it_or_leave_it"
    version = "2025.10.27"
```

**Behavior:**
- One agent makes offer (based on parameter or role)
- Other agent accepts/rejects
- Single-tick resolution
- Extracts all or most surplus

**Economic Properties:**
- Bargaining power demonstration
- Extreme case of asymmetric information
- Fast resolution

**Use Cases:**
- Teaching bargaining power
- Market power analysis
- Comparison with bilateral bargaining

**Effort:** 4-5 hours

#### 3.2 Split-The-Difference
```python
class SplitDifference(BargainingProtocol):
    """Equal surplus division."""
    name = "split_difference"
    version = "2025.10.27"
```

**Behavior:**
- Calculate total surplus
- Divide equally between agents
- Find prices that achieve 50/50 split

**Economic Properties:**
- Fair division
- Symmetric outcome
- Simple and fast

**Use Cases:**
- Baseline fairness comparison
- Teaching surplus division
- Cooperative bargaining

**Effort:** 3-4 hours

#### 3.3 Nash Bargaining Solution
```python
class NashBargaining(BargainingProtocol):
    """Game-theoretic bargaining solution."""
    name = "nash_bargaining"
    version = "2025.10.27"
```

**Behavior:**
- Maximize product of surpluses
- Finds Nash bargaining solution
- Takes outside options into account

**Economic Properties:**
- Pareto efficient
- Symmetric (if agents are)
- Axiomatically derived

**Use Cases:**
- Teaching game theory
- Cooperative bargaining models
- Optimal mechanism comparison

**Effort:** 6-8 hours

#### 3.4 Rubinstein Alternating Offers (Advanced)
```python
class RubinsteinBargaining(BargainingProtocol):
    """Multi-tick alternating offers with discounting."""
    name = "rubinstein"
    version = "2025.10.27"
```

**Behavior:**
- Agents alternate making offers over multiple ticks
- Discount factor applied each round
- Subgame perfect equilibrium

**Economic Properties:**
- Multi-period dynamics
- Time preference effects
- Strategic behavior

**Use Cases:**
- Teaching dynamic games
- Time preference analysis
- Patience and bargaining power

**Effort:** 10-12 hours (multi-tick complexity)

---

## Implementation Priority Recommendations

### Tier 1: Quick Wins (1 week)
**Goal:** Demonstrate protocol system with minimal effort

1. **Random Walk Search** (2-3h)
2. **Random Matching** (2-3h)  
3. **Split-The-Difference Bargaining** (3-4h)

**Result:** 3 complete alternatives, one per category, fully functional system

**Value:** 
- Proves extensibility
- Enables first comparisons
- Simple implementations build confidence

### Tier 2: Pedagogical Value (2 weeks)
**Goal:** Implement protocols with teaching value

4. **Greedy Surplus Matching** (4-5h)
5. **Take-It-Or-Leave-It Bargaining** (4-5h)
6. **Myopic Search** (2h)

**Result:** Demonstrate key economic concepts (efficiency, power, information)

**Value:**
- Teaching material for courses
- Comparative scenarios
- Research-grade analysis

### Tier 3: Research Grade (4+ weeks)
**Goal:** Advanced protocols for research

7. **Stable Matching (Gale-Shapley)** (6-8h)
8. **Nash Bargaining** (6-8h)
9. **Memory-Based Search** (6-8h)
10. **Rubinstein Bargaining** (10-12h)

**Result:** Full protocol library for institutional analysis

**Value:**
- Publication-quality research
- Comprehensive comparative analysis
- Advanced economic theory demonstrations

---

## Implementation Strategy

### Approach 1: Vertical Slice (Recommended)
**One complete protocol per category first**

**Week 1:** Random Walk + Random Matching + Split-Difference
- Proves system works end-to-end
- Minimal complexity
- Can run full comparison scenarios

**Pros:**
- Fast validation of architecture
- Early demonstration value
- Builds confidence

**Cons:**
- Less depth initially
- May need refactoring

### Approach 2: Horizontal Depth
**Complete one category at a time**

**Week 1-2:** All matching protocols
**Week 3-4:** All bargaining protocols  
**Week 5:** All search protocols

**Pros:**
- Deep understanding of one category
- Can optimize within category
- Easier testing

**Cons:**
- Longer until full demo
- May miss cross-category issues

### Approach 3: Research-Driven
**Implement what you need for specific research**

**Based on your current research questions**

**Pros:**
- Immediate research value
- Motivated by real questions
- Efficient use of time

**Cons:**
- May leave gaps
- Less systematic

---

## Testing Requirements

### Per Protocol Tests

Each new protocol needs:

1. **Unit Tests**
   - Method-level correctness
   - Edge cases handled
   - Determinism verified

2. **Property Tests**
   - Protocol-specific invariants
   - Economic properties satisfied
   - Comparison with legacy

3. **Integration Tests**
   - Works within full simulation
   - Telemetry logging correct
   - Performance acceptable

### Comparative Scenarios

Create scenarios that highlight differences:

```yaml
# scenarios/comparison_matching_protocols.yaml
# Run same scenario with different matching protocols

base_scenario: mixed_regime.yaml

variants:
  - name: "legacy_three_pass"
    protocols:
      matching: {name: "legacy_three_pass", version: "2025.10.27"}
  
  - name: "greedy_surplus"
    protocols:
      matching: {name: "greedy_surplus", version: "2025.10.27"}
  
  - name: "random"
    protocols:
      matching: {name: "random", version: "2025.10.27"}
```

### Economic Validation

**Key Metrics to Track:**
- Total surplus generated
- Distribution of surplus
- Number of trades
- Trade prices
- Agent welfare
- Efficiency measures

---

## Documentation Requirements

### Per Protocol Documentation

```python
class NewProtocol(ProtocolBase):
    """
    One-line description.
    
    Behavior:
        - How it works
        - Key parameters
        - Decision logic
    
    Economic Properties:
        - Efficiency guarantees
        - Strategic considerations
        - Theoretical references
    
    Use Cases:
        - When to use this protocol
        - What it demonstrates
        - Comparison points
    
    References:
        - Academic papers
        - Textbook chapters
        - Related protocols
    """
```

### Comparative Analysis Guide

Create `docs/protocol_comparisons.md`:
- When to use each protocol
- Expected differences in outcomes
- Pedagogical use cases
- Research applications

---

## Next Steps - Discussion Points

### Decision 1: Implementation Priority

**Question:** Which tier should we start with?

**Options:**
- **Tier 1:** Quick wins (1 week) - demonstrates system
- **Tier 2:** Pedagogical (2 weeks) - teaching value
- **Tier 3:** Research (4+ weeks) - publication quality

**Recommendation:** Start with Tier 1 to validate architecture, then reassess

### Decision 2: Specific Protocols

**Question:** Which specific protocols first?

**Recommendation for Week 1:**
1. Random Walk Search (2-3h)
2. Random Matching (2-3h)
3. Split-The-Difference Bargaining (3-4h)

**Rationale:**
- Simplest implementations
- One per category
- Proves extensibility
- Enables first comparisons

### Decision 3: Testing Depth

**Question:** How comprehensive should initial tests be?

**Options:**
- **Minimal:** Basic functionality only
- **Standard:** Unit + integration tests
- **Comprehensive:** Above + property tests + comparisons

**Recommendation:** Standard for Tier 1, Comprehensive for Tier 2+

### Decision 4: Documentation Timing

**Question:** When to write documentation?

**Options:**
- **During:** Write as you implement
- **After:** Implement all, then document
- **Incremental:** Document each protocol as complete

**Recommendation:** Incremental - prevents accumulating doc debt

---

## Success Criteria

### Tier 1 Complete (1 week)
- [ ] 3 alternative protocols implemented (one per category)
- [ ] All tests passing
- [ ] Comparison scenario working
- [ ] Basic documentation complete
- [ ] Telemetry captures protocol choices

### Tier 2 Complete (3 weeks)
- [ ] 6+ protocols across categories
- [ ] Economic properties validated
- [ ] Teaching scenarios created
- [ ] Comparative analysis guide written
- [ ] Performance benchmarked

### Tier 3 Complete (2+ months)
- [ ] 10+ protocols implemented
- [ ] Research-grade validation
- [ ] Publication-quality documentation
- [ ] Full protocol library
- [ ] Advanced mechanisms (multi-tick, learning)

---

## Questions for You

1. **Research Goals:** Do you have specific research questions that would benefit from particular protocols?

2. **Teaching Needs:** Are you planning to use VMT for teaching? Which economic concepts are priority?

3. **Time Available:** How much time can you dedicate to protocol implementation in the next month?

4. **Depth vs Breadth:** Would you rather have 3 well-tested protocols or 6 minimally-tested protocols?

5. **Multi-tick Protocols:** Are dynamic (multi-tick) bargaining protocols interesting to you, or prefer single-tick resolution?

---

**Document Status:** Planning complete - ready to implement  
**Recommended Start:** Tier 1 Quick Wins (Random Walk, Random Matching, Split-Difference)  
**Estimated Effort:** 8-10 hours for Tier 1  
**Next Session:** Implement first alternative protocol or discuss priorities

