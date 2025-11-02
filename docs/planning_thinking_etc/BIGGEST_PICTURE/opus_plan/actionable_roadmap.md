# VMT Actionable Roadmap

**Document Purpose**: Pragmatic, step-by-step path from current state to multi-track platform  
**Created**: November 2, 2025  
**Principle**: Ship working software incrementally, validate constantly

---

## Starting Point: Honest Assessment

### What's Actually Working
- ✅ Spatial grid with agents moving and trading
- ✅ Basic protocols for search, matching, and bargaining
- ✅ Multiple utility functions
- ✅ Deterministic simulation engine
- ✅ Pygame visualization

### What's Not Working or Unknown
- ❓ No idea what patterns emerge from current system
- ❓ No performance benchmarks established
- ❌ Only one set of institutional rules
- ❌ No way to compare different approaches
- ❌ No Game Theory or Neoclassical capabilities

### The Reality Check
You have a working spatial ABM but don't fully understand its behavior. Before adding complexity, you need to understand what you've built.

---

## Development Stages: A Pragmatic Sequence

### 🔍 Stage 1: Understand What You Have
**Duration**: 2-3 weeks  
**Why First**: Can't build on unknown foundations

#### Week 1: Behavioral Mapping
Create focused test scenarios:
```python
# scenarios/test/basic_behaviors.yaml
- two_agent_trade.yaml        # Simplest possible case
- ten_agent_cluster.yaml       # Spatial dynamics  
- hundred_agent_market.yaml    # Large-scale emergence
- no_trade_equilibrium.yaml    # Edge case
- price_convergence_test.yaml  # Does it happen?
```

Run each scenario 100 times with different seeds. Document:
- Do prices converge? To what values?
- How long does trade take?
- What spatial patterns emerge?
- Where does the system break?

#### Week 2: Performance Baseline
```bash
# Profile current implementation
python -m cProfile -o baseline.prof main.py scenarios/demos/minimal_2agent.yaml
python -m memory_profiler main.py scenarios/demos/protocol_comparison_4agent.yaml

# Benchmark at different scales
for n in 10 25 50 100 200; do
    python scripts/benchmark_performance.py --agents $n
done
```

Document:
- FPS at different agent counts
- Memory usage patterns
- CPU bottlenecks (computation vs rendering)
- Maximum practical agent count

#### Week 3: Create Behavioral Documentation
Write up findings in `docs/behavioral_baseline.md`:
- Expected vs actual behaviors
- Emergent patterns discovered
- Performance limits
- Edge cases and failures

**Deliverable**: Complete understanding of current system behavior  
**Success Metric**: Can predict outcomes for any scenario configuration

---

### 🔧 Stage 2: Diversify Your Protocols
**Duration**: 3-4 weeks  
**Why Second**: Need comparisons to show institutions matter

#### Week 1: Baseline Protocols
Implement the simplest alternatives:
```python
class RandomWalkSearch(SearchProtocol):
    """Zero information - pure randomness"""
    def execute(self, world_view: WorldView) -> List[Effect]:
        return [MoveEffect(agent_id, random_direction())]

class RandomMatching(MatchingProtocol):
    """No preferences - random pairing"""
    def execute(self, world_view: WorldView) -> List[Effect]:
        agents = list(world_view.agents)
        random.shuffle(agents)
        return [PairEffect(agents[i], agents[i+1]) 
                for i in range(0, len(agents)-1, 2)]
```

#### Week 2: Strategic Protocols
Add protocols with clear strategic logic:
```python
class GreedySurplusMatching(MatchingProtocol):
    """Match to maximize total surplus"""
    
class TakeItOrLeaveItBargaining(BargainingProtocol):
    """One agent makes ultimatum offer"""
    
class SplitTheDifference(BargainingProtocol):
    """Always divide surplus equally"""
```

#### Week 3-4: Comparison Framework
Run same scenarios with different protocol combinations:
```
Protocol Set         | Price Convergence | Efficiency | Time to Trade
--------------------|-------------------|------------|---------------
Legacy (current)     | Yes (200 ticks)   | 85%        | 5 ticks
All Random          | No                | 60%        | 8 ticks  
Greedy + Split      | Yes (150 ticks)   | 92%        | 4 ticks
Mixed               | Partial           | 75%        | 6 ticks
```

**Deliverable**: 5+ working protocols with documented behavioral differences  
**Success Metric**: Can demonstrate that institutional rules affect outcomes

---

### 🎮 Stage 3: Build the Game Theory Track
**Duration**: 5-6 weeks  
**Why Third**: Natural bridge from many-agent to strategic analysis

#### Week 1-2: Two-Agent Exchange Engine
```python
class TwoAgentExchange:
    """Pure exchange between two strategic agents"""
    
    def __init__(self, agent_a: Agent, agent_b: Agent):
        self.agents = (agent_a, agent_b)
        self.endowment = agent_a.inventory + agent_b.inventory
        
    def compute_contract_curve(self) -> List[Allocation]:
        """Find all Pareto efficient allocations"""
        # Points where MRS_a = MRS_b
        
    def find_competitive_equilibrium(self) -> Tuple[Allocation, Prices]:
        """Compute market-clearing prices and allocation"""
        # Price ratio where both agents optimize
```

#### Week 3-4: Interactive Edgeworth Box
```python
class EdgeworthBoxWidget(QWidget):
    """Interactive visualization of 2-agent exchange"""
    
    def __init__(self):
        self.figure = plt.figure()
        self.ax = self.figure.add_subplot(111)
        self.setup_interaction()
        
    def draw_indifference_curves(self, allocation):
        """Update curves based on current allocation"""
        
    def on_drag(self, event):
        """Handle dragging allocation point"""
        new_allocation = self.pixel_to_allocation(event.x, event.y)
        self.update_display(new_allocation)
```

Features:
- Draggable allocation point
- Real-time utility display
- Contract curve overlay
- Competitive equilibrium highlight
- Animation to efficient trades

#### Week 5-6: Bargaining Solutions
```python
class BargainingSolver:
    """Compute theoretical bargaining solutions"""
    
    def nash_solution(self, feasible_set, disagreement):
        """Maximize (u_a - d_a)(u_b - d_b)"""
        
    def kalai_smorodinsky(self, feasible_set, disagreement):
        """Proportional solution"""
        
    def rubinstein_alternating(self, delta_a, delta_b):
        """Infinite horizon alternating offers"""
        
    def compute_all_solutions(self):
        """Return dict of all solutions for comparison"""
```

**Deliverable**: Fully functional Edgeworth Box with multiple bargaining solutions  
**Success Metric**: Can demonstrate Nash, KS, and Rubinstein solutions visually

---

### 🚀 Stage 4: Create Unified Launcher
**Duration**: 2 weeks  
**Why Fourth**: Makes multi-paradigm nature visible

#### Week 1: Basic Navigation Structure
```python
# launcher_v2.py
class UnifiedLauncher(QMainWindow):
    def __init__(self):
        self.setWindowTitle("VMT: Visualizing Microeconomic Theory")
        self.setup_ui()
        
    def setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Select Simulation Paradigm:")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        # Track buttons
        self.abm_btn = QPushButton("Agent-Based Simulation\n"
                                   "Emergent markets from individual interactions")
        self.game_theory_btn = QPushButton("Game Theory Analysis\n"
                                           "Strategic interaction in small groups")
        self.neoclassical_btn = QPushButton("Neoclassical Models\n"
                                            "Equilibrium benchmarks (Coming Soon)")
        
        # Initially disable neoclassical
        self.neoclassical_btn.setEnabled(False)
        
        # Connect signals
        self.abm_btn.clicked.connect(self.launch_abm)
        self.game_theory_btn.clicked.connect(self.launch_game_theory)
```

#### Week 2: Integration and Polish
- Connect existing ABM launcher functionality
- Connect new Game Theory Edgeworth Box
- Add shared configuration widgets (seed, parameters)
- Test cross-platform compatibility
- Add help/documentation links

**Deliverable**: Single entry point for both implemented tracks  
**Success Metric**: Seamless navigation between paradigms

---

### 📊 Stage 5: Add Market Information to ABM
**Duration**: 6-8 weeks  
**Why Fifth**: Natural evolution of spatial trading

This stage enhances the Agent-Based track with emergent price discovery:

#### Weeks 1-2: Detect Market Areas
```python
class MarketAreaDetector:
    """Identify spatial clusters of trading activity"""
    
    def detect_clusters(self, trades: List[Trade]) -> List[MarketArea]:
        # Use spatial clustering (DBSCAN or similar)
        # Markets form where trade density exceeds threshold
```

#### Weeks 3-4: Aggregate Price Signals
```python
class PriceAggregator:
    """Compute local price signals from actual trades"""
    
    def compute_local_prices(self, market_area: MarketArea) -> PriceSignal:
        recent_trades = market_area.get_recent_trades(window=50)
        return PriceSignal(
            price_ratio=weighted_average(recent_trades),
            confidence=compute_variance(recent_trades),
            n_observations=len(recent_trades)
        )
```

#### Weeks 5-6: Information-Aware Protocols
```python
class MarketInformedBargaining(BargainingProtocol):
    """Use local price signals to anchor negotiation"""
    
    def execute(self, world_view: WorldView) -> List[Effect]:
        local_price = world_view.get_nearest_price_signal()
        if local_price and local_price.confidence > threshold:
            # Anchor on market price
            return self.negotiate_around_price(local_price)
        else:
            # Fall back to bilateral negotiation
            return self.bilateral_bargain()
```

#### Weeks 7-8: Comparison Studies
Run experiments:
- Uninformed vs informed trading
- Speed of convergence with/without signals
- Quality of price discovery
- Spatial patterns of information flow

**Deliverable**: Market information system that emerges from bilateral trades  
**Success Metric**: Demonstrable improvement in price convergence with information

---

### 🎯 Stage 6: Implement Neoclassical Benchmarks
**Duration**: 6-8 weeks  
**Why Sixth**: Provides theoretical contrast to emergence

#### Weeks 1-2: Walrasian Auctioneer
```python
class WalrasianAuctioneer:
    """Centralized market clearing mechanism"""
    
    def __init__(self, agents: List[Agent]):
        self.agents = agents
        self.prices = np.ones(n_goods)  # Initial prices
        
    def compute_excess_demand(self, prices):
        """Sum of desired trades at given prices"""
        total_demand = sum(a.demand(prices) for a in agents)
        total_supply = sum(a.endowment for a in agents)
        return total_demand - total_supply
        
    def find_equilibrium(self):
        """Solve for market-clearing prices"""
        from scipy.optimize import fsolve
        return fsolve(self.compute_excess_demand, self.prices)
```

#### Weeks 3-4: Tatonnement Process
```python
class TatonnementSimulator:
    """Price adjustment process visualization"""
    
    def step(self):
        excess = self.compute_excess_demand(self.prices)
        self.prices += self.adjustment_rate * excess
        self.history.append(self.prices.copy())
        
    def animate_convergence(self):
        """Show price path over time"""
        # May converge, cycle, or diverge depending on parameters
```

#### Weeks 5-6: Stability Analysis
- Implement Scarf's counterexamples
- Show cases where tatonnement fails
- Compare different adjustment rules
- Analyze conditions for convergence

#### Weeks 7-8: Integration and Comparison
Create comparison tools:
- ABM outcome vs Neoclassical equilibrium
- Time to convergence across paradigms
- Efficiency metrics
- Price dispersion analysis

**Deliverable**: Complete Neoclassical track with equilibrium tools  
**Success Metric**: Can show when/why equilibrium predictions fail

---

## Timeline Summary

| Stage | Duration | Key Output | Cumulative Time |
|-------|----------|------------|-----------------|
| 1. Understand | 2-3 weeks | Behavioral baseline | 3 weeks |
| 2. Protocols | 3-4 weeks | 5+ protocol alternatives | 7 weeks |
| 3. Game Theory | 5-6 weeks | Edgeworth Box + bargaining | 13 weeks |
| 4. Launcher | 2 weeks | Unified interface | 15 weeks |
| 5. Market Info | 6-8 weeks | Emergent price signals | 23 weeks |
| 6. Neoclassical | 6-8 weeks | Equilibrium benchmarks | 31 weeks |

**Total**: ~7-8 months to complete multi-paradigm platform

---

## Critical Success Factors

### Do These Things
✅ **Test constantly** - Every new feature needs validation  
✅ **Document behaviors** - Not just code, but what emerges  
✅ **Compare everything** - The power is in contrasts  
✅ **Keep it simple** - Resist feature creep until basics work  
✅ **Ship incrementally** - Working software every 2 weeks

### Avoid These Traps
❌ **Perfection paralysis** - Ship when good enough  
❌ **Scope creep** - No production or money in v1.0  
❌ **Big bang integration** - Build incrementally  
❌ **Assumption making** - Test everything empirically  
❌ **Framework obsession** - Solve problems, don't build frameworks

---

## Next Week's Concrete Tasks

### Monday-Tuesday: Create Test Scenarios
```bash
mkdir -p scenarios/test
# Create the 5 basic test scenarios
# Run each 10 times, document results
```

### Wednesday-Thursday: Performance Profiling
```bash
python -m cProfile main.py scenarios/demos/minimal_2agent.yaml
# Identify bottlenecks
# Document current FPS limits
```

### Friday: Write Behavioral Baseline
- Compile findings into `docs/behavioral_baseline.md`
- Identify surprising behaviors
- List uncertainties requiring investigation

### Weekend: Design First Alternative Protocol
- Choose simplest difference: Random Walk Search
- Plan implementation strategy
- Prepare for Week 2 coding

---

## Measuring Progress

### Weekly Checkpoints
- Can you demonstrate something new each Friday?
- Is the new capability documented?
- Have you compared it to what existed before?

### Stage Completion Criteria
- Stage 1: Can predict system behavior
- Stage 2: Can show institutional effects
- Stage 3: Can demonstrate bargaining solutions
- Stage 4: Can navigate between paradigms
- Stage 5: Can show information effects
- Stage 6: Can contrast with equilibrium

---

## The Essential Insight

Don't try to build everything at once. The power of VMT comes from **comparison** - showing how different institutional arrangements and theoretical frameworks lead to different outcomes.

Build incrementally, validate constantly, and always ask: "What does this comparison teach us about how markets work?"

Start with understanding what you have. Everything else follows from that foundation.

---

**First Action**: Create `scenarios/test/two_agent_trade.yaml` and run it 10 times. Document what happens. You've started.
