# Master Protocol Implementation Plan
**Exhaustive Microeconomic Theory Simulator**

**Document Status:** Active Implementation Roadmap  
**Version:** 1.0  
**Created:** 2025-10-27  
**Author:** Lead Developer + AI Agent  
**Purpose:** Phased implementation plan from quick wins to comprehensive protocol library

---

## Executive Summary

**Vision:** Create an exhaustive microeconomic theory simulation and visualization platform covering the full spectrum of exchange mechanisms - from bilateral barter to centralized market equilibria.

**Approach:** Four-phase incremental implementation (70-90 hours total)

**Current Status:** 
- ✅ Phase 0 & 1 complete and merged to main
- 🚀 Starting Phase 2a: Quick wins validation
- 📋 Full roadmap defined through Phase 5

**Key Milestone:** Centralized market price formation (Phase 3) - moving beyond bilateral spot negotiation to equilibrium price discovery.

---

## Implementation Philosophy

### Incremental Validation
Each phase **validates** the architecture before building more complexity:
1. **Phase 2a** validates basic extensibility (3 simple protocols)
2. **Phase 2b** validates pedagogical value (economic concept demonstrations)
3. **Phase 3** validates centralized mechanisms (key milestone)
4. **Phase 4** validates advanced features (multi-tick, learning, game theory)
5. **Phase 5** achieves comprehensive coverage (exhaustive library)

### Build Quality
Every protocol includes:
- Complete implementation with docstrings
- Unit tests for methods
- Integration tests in simulation
- Property tests for economic invariants
- Comparison scenarios vs legacy/other protocols
- Documentation of economic properties

### Research-Grade Standards
- Deterministic and reproducible
- Comprehensive telemetry
- Performance benchmarked
- Theoretically grounded
- Literature references included

---

## Phase 2a: Quick Wins Validation
**Duration:** 1 week (8-10 hours)  
**Goal:** Validate protocol architecture end-to-end  
**Status:** Ready to start immediately

### Protocols to Implement

#### 1. Random Walk Search Protocol
**File:** `src/vmt_engine/protocols/search/random_walk.py`

**Implementation:**
```python
class RandomWalkSearch(SearchProtocol):
    """
    Stochastic exploration for baseline comparison and pedagogy.
    
    Behavior:
        - Agent selects random direction within vision radius
        - No utility calculation
        - Pure exploration, zero exploitation
        - Useful for teaching value of information
    
    Economic Properties:
        - Zero information efficiency
        - Equivalent to Brownian motion in economics
        - Baseline for rational search comparison
    
    References:
        - Stigler (1961) "The Economics of Information"
        - Random search models in labor economics
    """
    name = "random_walk"
    version = "2025.10.27"
    
    def build_preferences(self, world: WorldView) -> list[tuple]:
        # Randomly rank visible targets
        pass
    
    def select_target(self, world: WorldView) -> list[Effect]:
        # Select random target from preferences
        pass
```

**Tests:**
- Unit: Randomness uses world.rng_stream for determinism
- Unit: All targets have equal probability
- Integration: Agents move randomly in simulation
- Property: Different seeds produce different but reproducible paths
- Comparison: vs LegacySearch - show efficiency gap

**Effort:** 2-3 hours

---

#### 2. Random Matching Protocol
**File:** `src/vmt_engine/protocols/matching/random.py`

**Implementation:**
```python
class RandomMatching(MatchingProtocol):
    """
    Random pairing for null hypothesis testing.
    
    Behavior:
        - Collect all agents wanting to trade
        - Shuffle list deterministically
        - Pair adjacent agents in shuffled list
        - No surplus calculation
    
    Economic Properties:
        - Zero allocative efficiency
        - Null hypothesis for statistical testing
        - Demonstrates value of preference-based matching
    
    Use Cases:
        - Baseline comparison
        - Teaching matching theory
        - Statistical null hypothesis
    """
    name = "random"
    version = "2025.10.27"
    
    def find_matches(
        self, 
        preferences: dict[int, list], 
        world: WorldView
    ) -> list[Effect]:
        # Shuffle agents wanting to trade
        # Pair sequentially
        # Emit Pair effects
        pass
```

**Tests:**
- Unit: Deterministic shuffle with same seed
- Unit: No agent paired twice
- Integration: Pairs form in simulation
- Property: All valid pairs equally likely
- Comparison: vs LegacyMatching - show surplus differences

**Effort:** 2-3 hours

---

#### 3. Split-The-Difference Bargaining Protocol
**File:** `src/vmt_engine/protocols/bargaining/split_difference.py`

**Implementation:**
```python
class SplitDifference(BargainingProtocol):
    """
    Equal surplus division for fairness baseline.
    
    Behavior:
        - Calculate total surplus from trade
        - Divide equally between agents
        - Find prices achieving 50/50 split
        - Single-tick resolution
    
    Economic Properties:
        - Pareto efficient
        - Symmetric (equal treatment)
        - Fair division baseline
        - Fast resolution
    
    Mathematical Details:
        Given trade (ΔA, ΔB, ΔM):
        - Surplus_buyer = U(inv + Δ) - U(inv) - λ·ΔM
        - Surplus_seller = U(inv - Δ) - U(inv) + λ·ΔM
        - Find price p where Surplus_buyer = Surplus_seller
    
    References:
        - Kalai-Smorodinsky bargaining solution
        - Symmetric Nash bargaining
    """
    name = "split_difference"
    version = "2025.10.27"
    
    def negotiate(
        self, 
        pair: tuple[int, int], 
        world: WorldView
    ) -> list[Effect]:
        # Calculate feasible trades
        # For each, compute surplus split
        # Select trade maximizing total surplus with 50/50 split
        # Emit Trade or Unpair effects
        pass
```

**Tests:**
- Unit: Surplus split is equal (within epsilon)
- Unit: Trade is Pareto improving
- Integration: Trades execute in simulation
- Property: Both agents gain equally
- Comparison: vs LegacyBargaining - show price differences

**Effort:** 3-4 hours

---

### Phase 2a Deliverables

**Code:**
- [ ] 3 protocol implementations (one per category)
- [ ] Unit tests for each protocol
- [ ] Integration tests in full simulation
- [ ] Property tests for economic invariants

**Scenarios:**
- [ ] `scenarios/comparison_search_protocols.yaml` - Random Walk vs Legacy
- [ ] `scenarios/comparison_matching_protocols.yaml` - Random vs Legacy
- [ ] `scenarios/comparison_bargaining_protocols.yaml` - Split-Difference vs Legacy

**Documentation:**
- [ ] Docstrings with economic properties
- [ ] `docs/protocols_10-27/phase2a_results.md` - Comparison analysis
- [ ] Update `docs/ASDF/SESSION_STATE.md` with completion

**Validation Criteria:**
- [ ] All tests passing
- [ ] Determinism verified (10 runs with same seed → identical)
- [ ] Performance <10% regression
- [ ] Clear behavioral differences demonstrated
- [ ] Protocol architecture validated ✅

**Timeline:** Days 1-5 (8-10 hours)

---

## Phase 2b: Pedagogical Protocols
**Duration:** 2 weeks (20-25 hours)  
**Goal:** Implement protocols demonstrating key economic concepts  
**Prerequisites:** Phase 2a complete

### Protocols to Implement

#### 4. Greedy Surplus Matching Protocol
**File:** `src/vmt_engine/protocols/matching/greedy.py`

**Concept:** Welfare maximization vs individual rationality

**Implementation:**
```python
class GreedyMatching(MatchingProtocol):
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
    
    Algorithm:
        1. Enumerate all possible pairs
        2. Calculate surplus for each potential pair
        3. Sort by total surplus (descending)
        4. Greedily assign pairs (no double-booking)
        5. Stop when no more pairs possible
    
    References:
        - First-best welfare economics
        - Market vs planner comparisons
    """
    name = "greedy_surplus"
    version = "2025.10.27"
    
    def find_matches(
        self, 
        preferences: dict[int, list], 
        world: WorldView
    ) -> list[Effect]:
        # Enumerate all potential pairs
        # Calculate surplus for each
        # Sort by total surplus
        # Greedy assignment
        pass
```

**Pedagogical Value:** 
- Compare efficiency: Greedy vs Legacy vs Random
- Show trade-off: Total welfare vs fairness
- Teach: First-best vs second-best outcomes

**Tests:**
- Property: Total surplus maximized (vs other protocols)
- Property: Pareto efficient allocation
- Property: May violate participation constraints
- Comparison: Efficiency gains quantified

**Effort:** 4-5 hours

---

#### 5. Myopic Search Protocol
**File:** `src/vmt_engine/protocols/search/myopic.py`

**Concept:** Information constraints and search costs

**Implementation:**
```python
class MyopicSearch(SearchProtocol):
    """
    Agents with limited information (1-cell vision radius).
    
    Teaching Points:
        - Value of information
        - Search costs and market thickness
        - Network topology effects
    
    Behavior:
        - Override vision_radius to 1
        - Otherwise identical to legacy search
        - Demonstrates information constraints
    
    Economic Properties:
        - Reduced match quality
        - Slower convergence
        - Higher search costs
        - Network effects amplified
    
    References:
        - Information economics literature
        - Search and matching models
        - Network formation
    """
    name = "myopic"
    version = "2025.10.27"
    
    def build_preferences(self, world: WorldView) -> list[tuple]:
        # Override vision to 1 cell
        # Otherwise legacy algorithm
        pass
```

**Pedagogical Value:**
- Compare outcomes: Myopic vs Full Vision
- Show: Information value quantified
- Teach: Search costs and market efficiency

**Tests:**
- Property: Vision limited to 1 cell
- Property: Match quality lower than legacy
- Comparison: Efficiency loss from myopia

**Effort:** 2 hours

---

#### 6. Take-It-Or-Leave-It Bargaining Protocol
**File:** `src/vmt_engine/protocols/bargaining/take_it_or_leave_it.py`

**Concept:** Bargaining power and market power

**Implementation:**
```python
class TakeItOrLeaveIt(BargainingProtocol):
    """
    Monopolistic offer with single acceptance/rejection.
    
    Teaching Points:
        - Bargaining power extraction
        - Market power vs competitive price
        - Hold-up problem
    
    Behavior:
        - Proposer makes single offer (captures most surplus)
        - Responder accepts/rejects
        - Acceptance if surplus > 0 (slightly)
        - Single-tick resolution
    
    Parameters:
        - proposer_power: float [0, 1] - fraction of surplus to proposer
        - Default: 0.9 (90% to proposer, 10% to responder)
    
    Economic Properties:
        - Asymmetric surplus distribution
        - Proposer advantage
        - Fast resolution
        - Demonstrates bargaining power
    
    References:
        - Rubinstein (1982) - limiting case
        - Market power literature
    """
    name = "take_it_or_leave_it"
    version = "2025.10.27"
    
    def __init__(self, proposer_power: float = 0.9):
        self.proposer_power = proposer_power
    
    def negotiate(
        self, 
        pair: tuple[int, int], 
        world: WorldView
    ) -> list[Effect]:
        # Determine proposer (could be by role, random, or parameter)
        # Calculate optimal offer for proposer
        # Check responder acceptance (surplus > epsilon)
        # Emit Trade or Unpair
        pass
```

**Pedagogical Value:**
- Compare surplus: TIOL vs Split-Difference vs Legacy
- Show: Bargaining power effects
- Teach: Market power and efficiency

**Tests:**
- Property: Proposer gets ~90% of surplus
- Property: Responder gets minimal surplus (but > 0)
- Property: All trades Pareto improving
- Comparison: Welfare distribution vs other protocols

**Effort:** 4-5 hours

---

### Phase 2b Deliverables

**Code:**
- [ ] 3 more protocols (6 total with Phase 2a)
- [ ] Full test suites
- [ ] Property tests for each

**Scenarios:**
- [ ] `scenarios/teaching_efficiency.yaml` - Greedy vs Legacy vs Random
- [ ] `scenarios/teaching_information.yaml` - Myopic vs Full Vision
- [ ] `scenarios/teaching_bargaining_power.yaml` - TIOL vs Split-Difference

**Documentation:**
- [ ] Teaching guide: `docs/protocols_10-27/pedagogical_guide.md`
- [ ] Economic properties documented
- [ ] Comparison tables and graphs

**Validation Criteria:**
- [ ] Clear pedagogical demonstrations
- [ ] Economic concepts quantified
- [ ] Comparison scenarios working
- [ ] Ready for classroom use

**Timeline:** Days 6-15 (20-25 hours total through Phase 2b)

---

## Phase 3: Centralized Market Mechanisms ⭐ KEY MILESTONE
**Duration:** 3-4 weeks (25-30 hours)  
**Goal:** Implement equilibrium price formation (vs spot negotiation)  
**Prerequisites:** Phase 2a complete (2b can be parallel)

### Vision

**Current System:** Bilateral spot negotiation
- Agents form pairs
- Negotiate individual prices via compensating blocks
- Decentralized, heterogeneous prices

**Target System:** Centralized market equilibrium
- Agents submit supply/demand
- Market clears at equilibrium price(s)
- Centralized, uniform pricing (within commodity)

### Architecture Design

#### New Protocol Category: Market Mechanisms

**Base Class:**
```python
class MarketMechanism(ProtocolBase):
    """
    Protocol for centralized market price formation.
    
    Replaces: BargainingProtocol in centralized market regimes
    
    Interface:
        - collect_orders() - agents submit demand/supply schedules
        - clear_market() - find equilibrium prices
        - execute_trades() - allocate goods at equilibrium prices
    """
    
    @abstractmethod
    def collect_orders(
        self, 
        agents: list[int], 
        world: WorldView
    ) -> list[Order]:
        """Collect supply/demand from agents."""
        pass
    
    @abstractmethod
    def clear_market(
        self, 
        orders: list[Order], 
        world: WorldView
    ) -> dict[str, float]:
        """Find market-clearing prices."""
        pass
    
    @abstractmethod
    def execute_trades(
        self, 
        orders: list[Order], 
        prices: dict[str, float], 
        world: WorldView
    ) -> list[Effect]:
        """Allocate goods at equilibrium prices."""
        pass
```

**New Effect Types:**
```python
@dataclass
class Order(Effect):
    """Agent order submission."""
    agent_id: int
    commodity: str  # "A", "B", "M"
    direction: str  # "buy", "sell"
    quantity: int
    limit_price: float  # max willing to pay (buy) or min accept (sell)

@dataclass
class MarketClear(Effect):
    """Market clearing event."""
    commodity: str
    clearing_price: float
    quantity_traded: int
    buyers: list[int]
    sellers: list[int]
```

---

### Protocols to Implement

#### 7. Walrasian Auctioneer
**File:** `src/vmt_engine/protocols/market/walrasian.py`

**Concept:** Competitive equilibrium price discovery

**Implementation:**
```python
class WalrasianAuctioneer(MarketMechanism):
    """
    Tatonnement process for finding competitive equilibrium.
    
    Teaching Points:
        - Competitive equilibrium concept
        - Price adjustment dynamics (tatonnement)
        - Market efficiency
        - Walrasian auctioneer mechanism
    
    Algorithm:
        1. Agents submit demand/supply at current price
        2. Calculate excess demand
        3. Adjust price: p_new = p_old + α * excess_demand
        4. Iterate until |excess_demand| < ε
        5. Execute trades at equilibrium price
    
    Economic Properties:
        - Finds competitive equilibrium
        - Pareto efficient allocation
        - Uniform pricing per commodity
        - No arbitrage opportunities
    
    Parameters:
        - adjustment_speed: α (default 0.1)
        - tolerance: ε (default 0.01)
        - max_iterations: (default 100)
    
    References:
        - Walras (1874) "Elements of Pure Economics"
        - Arrow-Debreu general equilibrium
        - Scarf (1982) tatonnement convergence
    """
    name = "walrasian_auctioneer"
    version = "2025.10.27"
    
    def collect_orders(self, agents, world) -> list[Order]:
        # For each agent, calculate optimal demand at current price
        # Based on utility maximization
        pass
    
    def clear_market(self, orders, world) -> dict[str, float]:
        # Tatonnement process
        # Iterate until equilibrium
        pass
    
    def execute_trades(self, orders, prices, world) -> list[Effect]:
        # Match buyers and sellers at equilibrium price
        # Emit Trade effects
        pass
```

**Tests:**
- Property: Equilibrium prices clear market (supply = demand)
- Property: All trades Pareto improving
- Property: No arbitrage opportunities
- Property: Prices converge (not cycle)
- Integration: Works in full simulation

**Effort:** 10-12 hours

---

#### 8. Posted-Price Market
**File:** `src/vmt_engine/protocols/market/posted_price.py`

**Concept:** Fixed prices with quantity adjustment

**Implementation:**
```python
class PostedPriceMarket(MarketMechanism):
    """
    Sellers post prices, buyers choose quantities.
    
    Teaching Points:
        - Price-posting vs negotiation
        - Monopolistic competition
        - Search frictions with fixed prices
    
    Behavior:
        - Sellers post prices for their goods
        - Buyers observe all posted prices (within vision)
        - Buyers choose seller and quantity
        - Trades execute at posted prices
    
    Economic Properties:
        - Price dispersion possible
        - Search frictions matter
        - Monopolistic competition
        - May not reach competitive equilibrium
    
    References:
        - Burdett-Judd (1983) search model
        - Posted-price institutions literature
    """
    name = "posted_price"
    version = "2025.10.27"
```

**Effort:** 8-10 hours

---

#### 9. Continuous Double Auction (CDA)
**File:** `src/vmt_engine/protocols/market/cda.py`

**Concept:** Experimental economics standard

**Implementation:**
```python
class ContinuousDoubleAuction(MarketMechanism):
    """
    Real-time bid/ask matching mechanism.
    
    Teaching Points:
        - Market microstructure
        - Price discovery process
        - Order book dynamics
    
    Algorithm:
        - Maintain bid/ask order books
        - Match compatible orders (bid ≥ ask)
        - Trade at midpoint (or by priority rule)
        - Real-time price formation
    
    Economic Properties:
        - Fast convergence to equilibrium
        - High allocative efficiency
        - Dynamic price discovery
        - Standard experimental mechanism
    
    References:
        - Smith (1962) experimental markets
        - Friedman (1993) double auction experiments
    """
    name = "continuous_double_auction"
    version = "2025.10.27"
```

**Effort:** 12-15 hours

---

### Phase 3 Integration

**System Changes Required:**

1. **New Exchange Regime:**
```yaml
# scenarios/centralized_market.yaml
exchange_regime: "centralized_market"  # New option
market_mechanism:
  name: "walrasian_auctioneer"
  version: "2025.10.27"
  params:
    adjustment_speed: 0.1
    tolerance: 0.01
```

2. **Modified Trade Phase:**
```python
# In Simulation.tick()
if self.exchange_regime == "centralized_market":
    # Use MarketMechanism instead of BargainingProtocol
    orders = market.collect_orders(agents, world)
    prices = market.clear_market(orders, world)
    effects = market.execute_trades(orders, prices, world)
else:
    # Use bilateral bargaining (legacy)
    effects = bargaining_protocol.negotiate(pairs, world)
```

3. **New Telemetry Tables:**
```sql
CREATE TABLE market_orders (
    run_id INTEGER,
    tick INTEGER,
    agent_id INTEGER,
    commodity TEXT,
    direction TEXT,
    quantity INTEGER,
    limit_price REAL
);

CREATE TABLE market_clears (
    run_id INTEGER,
    tick INTEGER,
    commodity TEXT,
    clearing_price REAL,
    quantity_traded INTEGER,
    excess_demand REAL
);
```

### Phase 3 Deliverables

**Code:**
- [ ] `MarketMechanism` base class
- [ ] 3 market protocols (Walrasian, Posted-Price, CDA)
- [ ] New Effect types (Order, MarketClear)
- [ ] Integration with Simulation.tick()
- [ ] Full test suites

**Scenarios:**
- [ ] `scenarios/market_walrasian.yaml` - Competitive equilibrium
- [ ] `scenarios/market_posted_price.yaml` - Price dispersion
- [ ] `scenarios/market_cda.yaml` - Price discovery
- [ ] `scenarios/comparison_bilateral_vs_centralized.yaml` - Key comparison

**Documentation:**
- [ ] `docs/protocols_10-27/centralized_markets_guide.md`
- [ ] Economic theory behind each mechanism
- [ ] Comparison with bilateral trading
- [ ] Convergence properties

**Validation Criteria:**
- [ ] Equilibrium prices computed correctly
- [ ] Market clears (supply = demand)
- [ ] Pareto efficiency achieved
- [ ] Comparison vs bilateral demonstrates differences
- [ ] **KEY MILESTONE ACHIEVED** ✅

**Timeline:** Days 16-35 (25-30 hours cumulative for Phase 3)

---

## Phase 4: Advanced Protocols
**Duration:** 3-4 weeks (25-30 hours)  
**Goal:** Multi-tick dynamics, learning, game theory  
**Prerequisites:** Phase 3 complete

### Protocols to Implement

#### 10. Memory-Based Search
**File:** `src/vmt_engine/protocols/search/memory_based.py`

**Concept:** Learning and adaptation

**Features:**
- Agents remember past trading success by location/partner
- Explore vs exploit trade-off (ε-greedy)
- Spatial price learning
- Multi-tick state via InternalStateUpdate

**Effort:** 8-10 hours

---

#### 11. Stable Matching (Gale-Shapley)
**File:** `src/vmt_engine/protocols/matching/stable.py`

**Concept:** Matching theory and stability

**Features:**
- Deferred acceptance algorithm
- Guaranteed stable matching
- Strategy-proofness for one side
- Classic matching market design

**Effort:** 8-10 hours

---

#### 12. Nash Bargaining Solution
**File:** `src/vmt_engine/protocols/bargaining/nash.py`

**Concept:** Cooperative game theory

**Features:**
- Maximize product of surpluses
- Axiomatically derived solution
- Outside options consideration
- Unique equilibrium

**Effort:** 8-10 hours

---

### Phase 4 Deliverables

**Code:**
- [ ] 3 advanced protocols
- [ ] Multi-tick state management tested
- [ ] Full test coverage

**Scenarios:**
- [ ] Learning dynamics demonstrations
- [ ] Stability analysis
- [ ] Cooperative bargaining

**Documentation:**
- [ ] `docs/protocols_10-27/advanced_protocols_guide.md`
- [ ] Game-theoretic analysis
- [ ] Convergence properties

**Timeline:** Days 36-55 (25-30 hours for Phase 4)

---

## Phase 5: Comprehensive Library
**Duration:** 2-3 weeks (15-20 hours)  
**Goal:** Complete protocol coverage  
**Prerequisites:** Phase 4 complete

### Remaining Protocols

#### 13. Rubinstein Alternating Offers
**File:** `src/vmt_engine/protocols/bargaining/rubinstein.py`

**Concept:** Dynamic bargaining with discounting

**Features:**
- Multi-tick negotiation
- Alternating offers
- Time preferences and impatience
- Subgame perfect equilibrium

**Effort:** 12-15 hours

---

#### 14-18. Additional Protocols
Based on emerging research needs:
- Frontier sampling search
- Auction mechanisms (sealed-bid, ascending, descending)
- Network formation protocols
- Learning algorithms (reinforcement learning)
- Additional market mechanisms

**Effort:** 5-10 hours each

---

### Phase 5 Deliverables

**Code:**
- [ ] Comprehensive protocol library (18+ protocols)
- [ ] All categories fully covered
- [ ] Publication-quality implementation

**Documentation:**
- [ ] Complete protocol reference guide
- [ ] Comparative analysis framework
- [ ] Research applications guide

**Validation:**
- [ ] All tests passing
- [ ] Performance benchmarked
- [ ] Economic properties verified
- [ ] Literature references complete

**Timeline:** Days 56-70+ (cumulative 70-90 hours total)

---

## Success Metrics

### Technical Metrics
- [ ] 18+ protocols implemented across all categories
- [ ] >95% test coverage for protocol code
- [ ] <10% performance regression vs baseline
- [ ] 100% deterministic (verified with 10+ seeds)
- [ ] Zero memory leaks (profiled)

### Economic Metrics
- [ ] All protocols satisfy stated properties (tested)
- [ ] Comparative analysis quantified
- [ ] Efficiency measures calculated
- [ ] Welfare distributions analyzed
- [ ] Convergence properties documented

### Research Metrics
- [ ] Publication-quality implementation
- [ ] Comprehensive telemetry
- [ ] Literature references complete
- [ ] Reproducibility verified
- [ ] Ready for research use

### Pedagogical Metrics
- [ ] Teaching scenarios for all key concepts
- [ ] Comparison visualizations working
- [ ] Documentation clear and complete
- [ ] Ready for classroom use

---

## Resource Requirements

### Development Time
- **Phase 2a:** 8-10 hours (quick wins)
- **Phase 2b:** 12-15 hours (pedagogical)
- **Phase 3:** 25-30 hours (centralized markets) ⭐
- **Phase 4:** 25-30 hours (advanced)
- **Phase 5:** 15-20 hours (comprehensive)
- **Total:** 70-90 hours over 3-4 months

### Testing Time
- 20% of development time per phase
- ~15-20 hours total for comprehensive test suite

### Documentation Time
- 15% of development time
- ~12-15 hours total

### Total Project Time
- **Development:** 70-90 hours
- **Testing:** 15-20 hours
- **Documentation:** 12-15 hours
- **Grand Total:** 100-125 hours (realistic with iterations)

---

## Risk Management

### Technical Risks
| Risk | Mitigation |
|------|------------|
| Protocol interface insufficient | Phase 2a validates early |
| Performance degradation | Benchmark each phase |
| Multi-tick complexity | Start simple, build up |
| Market clearing convergence | Well-studied algorithms |
| Test coverage gaps | TDD approach throughout |

### Research Risks
| Risk | Mitigation |
|------|------------|
| Economic properties violated | Property tests for each protocol |
| Comparison scenarios misleading | Peer review, literature check |
| Telemetry insufficient | Design schema upfront |
| Results not reproducible | Determinism tests throughout |

---

## Immediate Next Steps (Phase 2a)

### Week 1: Days 1-2
**Goal:** Implement Random Walk Search

1. **Day 1 Morning (2-3 hours):**
   - Review `src/vmt_engine/protocols/search/legacy.py` structure
   - Create `src/vmt_engine/protocols/search/random_walk.py`
   - Implement `RandomWalkSearch` class
   - Basic unit tests

2. **Day 1 Afternoon (1 hour):**
   - Integration test in full simulation
   - Create comparison scenario
   - Verify determinism

### Week 1: Days 3-4
**Goal:** Implement Random Matching

3. **Day 2 Morning (2-3 hours):**
   - Create `src/vmt_engine/protocols/matching/random.py`
   - Implement `RandomMatching` class
   - Unit and property tests

4. **Day 2 Afternoon (1 hour):**
   - Integration test
   - Comparison scenario

### Week 1: Day 5
**Goal:** Implement Split-The-Difference Bargaining

5. **Day 3 (3-4 hours):**
   - Create `src/vmt_engine/protocols/bargaining/split_difference.py`
   - Implement `SplitDifference` class
   - Full test suite
   - Integration and comparison

### Week 1: Validation
6. **Final Review:**
   - Run all tests
   - Verify determinism
   - Check performance
   - Create comparison analysis
   - Document results in `docs/protocols_10-27/phase2a_results.md`
   - **VALIDATE ARCHITECTURE** ✅

---

## Long-Term Vision

### Ultimate Goal
An exhaustive microeconomic theory simulator covering:
- ✅ Spatial foraging (complete)
- ✅ Bilateral exchange - spot negotiation (complete)
- 🚀 Alternative bilateral mechanisms (Phase 2)
- 🎯 Centralized market equilibria (Phase 3) ⭐
- 📊 Advanced dynamics and learning (Phase 4)
- 🌟 Comprehensive protocol library (Phase 5)

### Research Applications
- Comparative institutional analysis
- Market design experiments
- Teaching microeconomic theory
- Publication-quality research
- Agent-based modeling platform

### Teaching Applications
- Visualize economic concepts
- Compare mechanisms side-by-side
- Demonstrate equilibrium dynamics
- Show welfare distributions
- Illustrate theoretical results

---

## Document Status

**Status:** Active implementation roadmap  
**Next Action:** Begin Phase 2a with Random Walk Search  
**Timeline:** 70-90 hours over 3-4 months  
**Key Milestone:** Phase 3 centralized markets  
**Ultimate Goal:** Exhaustive microeconomic theory simulator

**Last Updated:** 2025-10-27  
**Maintained By:** Lead Developer + AI Agent  
**Location:** `docs/protocols_10-27/master_implementation_plan.md`

