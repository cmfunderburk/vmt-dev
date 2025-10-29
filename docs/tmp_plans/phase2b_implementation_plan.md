# Phase 2b Implementation Plan: Pedagogical Protocols
**Exhaustive Microeconomic Theory Simulator - Phase 2b**

**Document Status:** Detailed Implementation Plan  
**Version:** 1.0  
**Created:** 2025-10-28  
**Author:** AI Assistant + Lead Developer  
**Purpose:** Step-by-step cursor plan for implementing Phase 2b protocols

---

## Executive Summary

**Phase 2b Goal:** Implement 3 pedagogical protocols that demonstrate key economic concepts through clear behavioral differences.

**Duration:** 20-25 hours over 2 weeks  
**Prerequisites:** Phase 2a complete (✅ DONE)  
**Focus:** Teaching value and economic concept demonstration

### Protocols to Implement
1. **Greedy Surplus Matching** - Welfare maximization vs individual rationality
2. **Myopic Search** - Information constraints and search costs  
3. **Take-It-Or-Leave-It Bargaining** - Bargaining power and market power

---

## Implementation Strategy

### Phase 2b Philosophy
- **Pedagogical Focus:** Each protocol teaches specific economic concepts
- **Clear Contrasts:** Behavioral differences must be obvious and measurable
- **Teaching Scenarios:** Create scenarios that highlight key concepts
- **Economic Properties:** Document theoretical foundations and literature

### Quality Standards
- Complete implementation with comprehensive docstrings
- Full test suites (unit, integration, property tests)
- Economic property verification
- Comparison scenarios vs Phase 2a protocols
- Literature references and theoretical grounding

---

## Protocol 1: Greedy Surplus Matching

### Economic Concept
**Efficiency vs Fairness Trade-off**
- Demonstrates central planner perspective
- Shows what happens when we maximize total welfare
- May violate individual rationality (some agents get negative surplus)
- Illustrates market failure vs planner solution

### Implementation Plan

#### Step 1: Create Protocol File
**File:** `src/vmt_engine/protocols/matching/greedy.py`

**Template:**
```python
"""
Greedy Surplus Matching Protocol

Pure welfare maximization without mutual consent requirement.
Demonstrates central planner perspective vs decentralized markets.

Economic Properties:
- Maximizes total surplus across all pairs
- May violate individual rationality (negative surplus for some)
- Not strategy-proof (agents may want to misreport preferences)
- Useful for efficiency benchmarks

Algorithm:
1. Enumerate all possible agent pairs
2. Calculate total surplus for each potential pair
3. Sort pairs by total surplus (descending)
4. Greedily assign pairs (no double-booking)
5. Stop when no more pairs possible

References:
- First-best welfare economics
- Market vs planner comparisons
- Mechanism design literature

Version: 2025.10.28 (Phase 2b - Pedagogical Protocol)
"""

from typing import Any, List
from ..registry import register_protocol
from ..base import MatchingProtocol, Effect, Pair
from ..context import ProtocolContext

@register_protocol(
    category="matching",
    name="greedy_surplus",
    description="Welfare maximization without consent requirement",
    properties=["welfare_maximizing", "central_planner", "pedagogical"],
    complexity="O(n²)",
    references=[
        "First-best welfare economics",
        "Market vs planner comparisons"
    ],
    phase="2b",
)
class GreedySurplusMatching(MatchingProtocol):
    """
    Pure welfare maximization without mutual consent requirement.
    
    Teaching Points:
        - Demonstrates central planner perspective
        - Shows efficiency-fairness trade-off
        - Illustrates market failure (may violate IR)
    
    Economic Properties:
        - Maximizes total surplus
        - May violate individual rationality
        - Not strategy-proof
        - Useful for efficiency benchmarks
    """
    
    name = "greedy_surplus"
    version = "2025.10.28"
    
    def find_matches(
        self, 
        preferences: dict[int, list], 
        context: ProtocolContext
    ) -> List[Effect]:
        """
        Greedily match agents to maximize total surplus.
        
        Args:
            preferences: Agent preferences from search protocols
            context: Protocol execution context
            
        Returns:
            List of Pair effects for optimal welfare assignment
        """
        # TODO: Implement greedy surplus matching algorithm
        pass
```

#### Step 2: Implement Core Algorithm
**Algorithm Details:**
1. **Enumerate Pairs:** Get all agents wanting to trade
2. **Calculate Surplus:** For each pair, compute total surplus from best trade
3. **Sort by Surplus:** Order pairs by total surplus (descending)
4. **Greedy Assignment:** Assign pairs sequentially, skipping if either agent already paired
5. **Emit Effects:** Return Pair effects for assigned pairs

**Key Implementation Questions:**
- How to calculate surplus for a potential pair?
- How to handle cases where surplus calculation fails?
- Should we include distance costs in surplus calculation?

#### Step 3: Create Test Suite
**File:** `tests/test_greedy_surplus_matching.py`

**Test Categories:**
1. **Interface Tests:** Protocol compliance
2. **Algorithm Tests:** Correctness of greedy assignment
3. **Property Tests:** Welfare maximization, potential IR violations
4. **Comparison Tests:** vs Random, vs Legacy, vs Split-Difference
5. **Integration Tests:** Works in full simulation

**Key Test Cases:**
- `test_maximizes_total_surplus()` - Verify greedy assignment achieves max welfare
- `test_may_violate_individual_rationality()` - Some agents may get negative surplus
- `test_no_double_pairing()` - Each agent in at most one pair
- `test_deterministic_with_same_seed()` - Reproducible results

#### Step 4: Create Teaching Scenario
**File:** `scenarios/teaching_efficiency_vs_fairness.yaml`

**Scenario Design:**
- 10 agents with complementary endowments
- Mixed utility functions (CES, Linear, Translog)
- Compare: Greedy vs Random vs Legacy vs Split-Difference
- Metrics: Total surplus, individual surplus distribution, fairness measures

**Expected Learning Outcomes:**
- Students see efficiency gains from greedy matching
- Students observe potential unfairness (some agents worse off)
- Students understand planner vs market trade-offs

### Implementation Effort: 4-5 hours

---

## Protocol 2: Myopic Search

### Economic Concept
**Information Constraints and Search Costs**
- Demonstrates value of information in markets
- Shows how limited search affects market efficiency
- Connects to search models in labor economics
- Illustrates network effects and market "thickness"

### Implementation Plan

#### Step 1: Create Protocol File
**File:** `src/vmt_engine/protocols/search/myopic.py`

**Template:**
```python
"""
Myopic Search Protocol

Constrained search strategy with limited vision radius.
Demonstrates information constraints and search costs.

Economic Properties:
- Limited information (vision radius = 1)
- Slower convergence to efficient outcomes
- Demonstrates value of information
- Shows network effects in markets

Teaching Points:
- Search costs reduce market efficiency
- Information is valuable in markets
- Market "thickness" depends on search range
- Network effects in economic interactions

References:
- Stigler (1961) "The Economics of Information"
- Search models in labor economics
- Network effects in markets

Version: 2025.10.28 (Phase 2b - Pedagogical Protocol)
"""

from typing import Any, List
from ..registry import register_protocol
from ..base import SearchProtocol, Effect, SetTarget
from ..context import WorldView

@register_protocol(
    category="search",
    name="myopic",
    description="Limited vision search (radius=1)",
    properties=["information_constrained", "pedagogical"],
    complexity="O(1)",
    references=[
        "Stigler (1961) Economics of Information",
        "Search models in labor economics"
    ],
    phase="2b",
)
class MyopicSearch(SearchProtocol):
    """
    Constrained search with limited vision radius.
    
    Teaching Points:
        - Information constraints reduce efficiency
        - Search costs matter in markets
        - Network effects and market thickness
        - Value of information in economic decisions
    """
    
    name = "myopic"
    version = "2025.10.28"
    
    def build_preferences(self, world: WorldView) -> List[tuple]:
        """
        Build preferences using limited vision (radius=1).
        
        Args:
            world: Agent's immutable perception snapshot
            
        Returns:
            List of (target, score, metadata) tuples
        """
        # TODO: Implement myopic search with vision radius = 1
        pass
    
    def select_target(self, world: WorldView) -> List[Effect]:
        """
        Select target from myopic preferences.
        
        Args:
            world: Agent's immutable perception snapshot
            
        Returns:
            List of SetTarget effects
        """
        # TODO: Implement target selection
        pass
```

#### Step 2: Implement Core Algorithm
**Algorithm Details:**
1. **Limited Vision:** Only consider targets within distance 1
2. **Preference Building:** Rank visible targets by utility/distance
3. **Target Selection:** Choose best visible target
4. **Information Constraint:** Ignore distant opportunities

**Key Implementation Questions:**
- Should we use the same preference ranking as legacy but with limited vision?
- How to handle cases where no targets are visible within radius 1?
- Should we include a "stay put" option when no good targets visible?

#### Step 3: Create Test Suite
**File:** `tests/test_myopic_search.py`

**Test Categories:**
1. **Interface Tests:** Protocol compliance
2. **Vision Tests:** Only considers distance-1 targets
3. **Property Tests:** Slower convergence, lower efficiency
4. **Comparison Tests:** vs Random Walk, vs Legacy (full vision)
5. **Integration Tests:** Works in full simulation

**Key Test Cases:**
- `test_only_considers_distance_one_targets()` - Verify vision constraint
- `test_slower_convergence_than_legacy()` - Efficiency comparison
- `test_handles_no_visible_targets()` - Graceful degradation
- `test_deterministic_with_same_seed()` - Reproducible results

#### Step 4: Create Teaching Scenario
**File:** `scenarios/teaching_information_value.yaml`

**Scenario Design:**
- 15 agents on 20x20 grid
- Compare: Myopic (radius=1) vs Legacy (full vision) vs Random Walk
- Metrics: Convergence speed, total surplus, trade frequency
- Visual: Show how limited vision affects agent movement patterns

**Expected Learning Outcomes:**
- Students see efficiency loss from limited information
- Students understand value of information in markets
- Students observe network effects and market thickness

### Implementation Effort: 2-3 hours

---

## Protocol 3: Take-It-Or-Leave-It Bargaining

### Economic Concept
**Bargaining Power and Market Power**
- Demonstrates extreme bargaining power
- Shows how market power affects surplus distribution
- Illustrates hold-up problems
- Connects to monopolistic pricing

### Implementation Plan

#### Step 1: Create Protocol File
**File:** `src/vmt_engine/protocols/bargaining/take_it_or_leave_it.py`

**Template:**
```python
"""
Take-It-Or-Leave-It Bargaining Protocol

Monopolistic offer with single acceptance/rejection.
Demonstrates bargaining power and market power effects.

Economic Properties:
- Asymmetric surplus distribution
- Proposer captures most gains
- Fast resolution (single round)
- Demonstrates bargaining power

Teaching Points:
- Bargaining power affects outcomes
- Market power vs competitive pricing
- Hold-up problems in economics
- Asymmetric information and power

Parameters:
- proposer_power: float [0, 1] - fraction of surplus to proposer
- Default: 0.9 (90% to proposer, 10% to responder)

References:
- Rubinstein (1982) - limiting case of alternating offers
- Market power literature
- Hold-up problem literature

Version: 2025.10.28 (Phase 2b - Pedagogical Protocol)
"""

from typing import Any, List
from ..registry import register_protocol
from ..base import BargainingProtocol, Effect, Trade, Unpair
from ..context import WorldView

@register_protocol(
    category="bargaining",
    name="take_it_or_leave_it",
    description="Monopolistic offer bargaining",
    properties=["asymmetric", "power_based", "pedagogical"],
    complexity="O(1)",
    references=[
        "Rubinstein (1982) alternating offers",
        "Market power literature"
    ],
    phase="2b",
)
class TakeItOrLeaveIt(BargainingProtocol):
    """
    Monopolistic offer with single acceptance/rejection.
    
    Teaching Points:
        - Bargaining power extraction
        - Market power vs competitive price
        - Hold-up problem
        - Asymmetric outcomes from asymmetric power
    """
    
    name = "take_it_or_leave_it"
    version = "2025.10.28"
    
    def __init__(self, proposer_power: float = 0.9, proposer_selection: str = "random"):
        """
        Initialize TIOL bargaining protocol.
        
        Args:
            proposer_power: Fraction of surplus going to proposer [0, 1]
            proposer_selection: How to select proposer. Options:
                - "random": Random selection using RNG
                - "first_in_pair": First agent in pair tuple (deterministic)
                - "higher_id": Agent with higher ID (deterministic)
                - "lower_id": Agent with lower ID (deterministic)
        """
        self.proposer_power = proposer_power
        self.proposer_selection = proposer_selection
    
    def negotiate(
        self, 
        pair: tuple[int, int], 
        world: WorldView
    ) -> List[Effect]:
        """
        Single-round negotiation with monopolistic offer.
        
        Args:
            pair: (agent_a_id, agent_b_id) to negotiate
            world: Context with both agents' states
            
        Returns:
            List of Trade or Unpair effects
        """
        # TODO: Implement TIOL bargaining algorithm
        pass
```

#### Step 2: Implement Core Algorithm
**Algorithm Details:**
1. **Determine Proposer:** Choose which agent makes the offer (could be random, role-based, or parameter)
2. **Calculate Optimal Offer:** Find trade that gives proposer desired fraction of surplus
3. **Check Acceptance:** Responder accepts if their surplus > epsilon (small positive)
4. **Emit Result:** Trade effect if accepted, Unpair effect if rejected

**Key Implementation Questions:**
- How to determine which agent is the proposer?
- How to handle cases where no trade gives proposer desired power?
- Should proposer power be configurable per scenario?

#### Step 3: Create Test Suite
**File:** `tests/test_take_it_or_leave_it.py`

**Test Categories:**
1. **Interface Tests:** Protocol compliance
2. **Power Tests:** Proposer gets desired fraction of surplus
3. **Property Tests:** Asymmetric distribution, Pareto efficiency
4. **Comparison Tests:** vs Split-Difference, vs Legacy
5. **Integration Tests:** Works in full simulation

**Key Test Cases:**
- `test_proposer_gets_desired_fraction()` - Verify power parameter works
- `test_responder_gets_minimal_surplus()` - Responder gets just above zero
- `test_all_trades_pareto_improving()` - No negative surplus trades
- `test_deterministic_with_same_seed()` - Reproducible results

#### Step 4: Create Teaching Scenario
**File:** `scenarios/teaching_bargaining_power.yaml`

**Scenario Design:**
- 8 agents with complementary endowments
- Compare: TIOL (90/10) vs Split-Difference (50/50) vs Legacy
- Metrics: Surplus distribution, total welfare, fairness measures
- Visual: Show asymmetric outcomes from asymmetric power

**Expected Learning Outcomes:**
- Students see bargaining power effects
- Students understand market power vs competitive outcomes
- Students observe hold-up problems and asymmetric outcomes

### Implementation Effort: 4-5 hours

---

## Phase 2b Integration and Testing

### Step 1: Update Protocol Registry
**File:** `src/vmt_engine/protocols/registry.py`

**Tasks:**
- Verify all 3 protocols register correctly
- Test protocol instantiation from names
- Validate protocol factory integration

### Step 2: Create Comparison Scenarios
**Files:**
- `scenarios/teaching_efficiency_vs_fairness.yaml` - Greedy vs others
- `scenarios/teaching_information_value.yaml` - Myopic vs others  
- `scenarios/teaching_bargaining_power.yaml` - TIOL vs others
- `scenarios/phase2b_comprehensive_comparison.yaml` - All protocols

### Step 3: Comprehensive Testing
**Test Suite:** `tests/test_phase2b_integration.py`

**Test Categories:**
1. **Protocol Loading:** All protocols load from YAML
2. **Protocol Mixing:** Can combine different protocols
3. **Determinism:** All protocols deterministic with same seed
4. **Performance:** No significant performance regression
5. **Pedagogical Value:** Clear behavioral differences demonstrated

### Step 4: Documentation
**Files:**
- `docs/protocols_10-27/phase2b_results.md` - Implementation results
- `docs/protocols_10-27/phase2b_teaching_guide.md` - Pedagogical usage
- Update `docs/3_enhancement_backlog.md` with Phase 2b completion

---

## Implementation Timeline

### Week 1: Core Protocols (12-15 hours)
**Day 1-2:** Greedy Surplus Matching (4-5 hours)
- Implement core algorithm
- Create test suite
- Basic integration testing

**Day 3-4:** Myopic Search (2-3 hours)
- Implement limited vision search
- Create test suite
- Integration testing

**Day 5:** Take-It-Or-Leave-It Bargaining (4-5 hours)
- Implement TIOL algorithm
- Create test suite
- Integration testing

### Week 2: Integration and Scenarios (8-10 hours)
**Day 6-7:** Teaching Scenarios (4-5 hours)
- Create comparison scenarios
- Test pedagogical value
- Document learning outcomes

**Day 8-9:** Comprehensive Testing (2-3 hours)
- Integration test suite
- Performance benchmarking
- Determinism verification

**Day 10:** Documentation (2 hours)
- Implementation results
- Teaching guide
- Update project documentation

---

## Success Criteria

### Technical Success
- ✅ All 3 protocols implemented and tested
- ✅ All tests passing (unit, integration, property)
- ✅ Deterministic and reproducible results
- ✅ Performance within 10% of baseline
- ✅ Clear behavioral differences demonstrated

### Pedagogical Success
- ✅ Teaching scenarios highlight key concepts
- ✅ Clear contrasts between protocols
- ✅ Measurable differences in outcomes
- ✅ Documentation supports classroom use

### Research Success
- ✅ Protocols ready for research applications
- ✅ Comparison scenarios enable systematic analysis
- ✅ Telemetry captures all relevant metrics
- ✅ Foundation ready for Phase 3 (centralized markets)

---

## Ambiguous Decisions Requiring Input

### 1. Greedy Surplus Matching
**Question:** How should we calculate surplus for potential pairs?
- **Option A:** Use existing trade calculation logic from legacy protocols
- **Option B:** Implement simplified surplus calculation for efficiency
- **Option C:** Make surplus calculation configurable

**Recommendation:** Option A (use existing logic) for consistency and accuracy. Use `find_all_feasible_trades()` and select trade maximizing total surplus (surplus_i + surplus_j), then apply distance discounting using β^distance parameter.

### 2. Myopic Search
**Question:** How to handle cases where no targets are visible within radius 1?
- **Option A:** Agent stays in place (no movement)
- **Option B:** Agent moves randomly (like random walk)
- **Option C:** Agent moves toward center of grid

**Recommendation:** Option A (stay in place) to clearly demonstrate information constraint

### 3. Take-It-Or-Leave-It Bargaining
**Question:** How to determine which agent is the proposer?
- **Option A:** Random selection using world RNG
- **Option B:** First agent in pair (deterministic)
- **Option C:** Agent with higher ID (deterministic)
- **Option D:** Make proposer selection configurable

**Recommendation:** Option D (make configurable) with Option A as default. Add `proposer_selection` parameter with options: "random" (default), "first_in_pair", "higher_id", "lower_id". This enables deterministic scenarios when needed while defaulting to randomness for fairness.

### 4. Teaching Scenarios
**Question:** What specific metrics should we track for pedagogical value?
- **Option A:** Focus on efficiency metrics (total surplus, convergence speed)
- **Option B:** Focus on fairness metrics (surplus distribution, individual welfare)
- **Option C:** Comprehensive metrics covering both efficiency and fairness

**Recommendation:** Option C (comprehensive) to support diverse teaching objectives

---

## Next Steps After Phase 2b

### Option A: Continue to Phase 3 (Centralized Markets) ⭐
**Duration:** 25-30 hours  
**Goal:** Implement Walrasian Auctioneer, Posted-Price Market, CDA  
**Key Milestone:** Enables core research question about decentralized vs centralized outcomes

### Option B: Additional Phase 2b Protocols
**Duration:** 15-20 hours  
**Goal:** Add more pedagogical protocols (e.g., Nash Bargaining, Stable Matching)  
**Value:** More comprehensive teaching toolkit

### Option C: Focus on Research Applications
**Duration:** 10-15 hours  
**Goal:** Create research-ready scenarios and analysis tools  
**Value:** Immediate research utility

---

**Ready for implementation? Please review ambiguous decisions and provide guidance on implementation approach.**
