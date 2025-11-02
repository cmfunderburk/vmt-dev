# VMT Comprehensive Implementation Plan with Pseudocode

**Document Purpose**: Rigorous step-by-step implementation guide with detailed pseudocode  
**Created**: November 2, 2025  
**Based On**: Opus plan documents (unified_implementation_overview, actionable_roadmap, protocol_restructure_plan)  
**Status**: Master Implementation Blueprint

---

## Executive Summary

This document provides a comprehensive implementation plan for transforming VMT from a spatial ABM into a multi-paradigm platform with three complementary tracks:
1. **Agent-Based Track** - Emergent market phenomena from spatial bilateral trading
2. **Game Theory Track** - Strategic interactions with Edgeworth Box visualizations  
3. **Neoclassical Track** - Equilibrium benchmarks using traditional solution methods

The implementation follows a 6-stage development plan with detailed pseudocode for each component.

---

## Part 0: Protocol Architecture Restructure (PREREQUISITE)

### Critical Architectural Decision
Before implementing new features, restructure protocol ownership:
- **Game Theory module** owns Bargaining and Matching protocols
- **Agent-Based module** owns Search protocols  
- **Shared infrastructure** stays in `protocols/`

### Implementation Steps

```python
# Step 1: Create new module structure
def restructure_protocol_architecture():
    """
    Reorganize protocol modules to reflect domain ownership
    """
    # Create new directory structure
    directories = [
        "src/vmt_engine/game_theory/bargaining",
        "src/vmt_engine/game_theory/matching",
        "src/vmt_engine/agent_based/search"
    ]
    for dir in directories:
        create_directory(dir)
    
    # Move protocol ABCs to domain modules
    move_file("protocols/base.py::SearchProtocol", 
              "agent_based/search/base.py")
    move_file("protocols/base.py::MatchingProtocol", 
              "game_theory/matching/base.py")
    move_file("protocols/base.py::BargainingProtocol", 
              "game_theory/bargaining/base.py")
    
    # Move implementations
    move_directory("protocols/bargaining/*", "game_theory/bargaining/")
    move_directory("protocols/matching/*", "game_theory/matching/")
    move_directory("protocols/search/*", "agent_based/search/")
    
    # Update all imports
    update_imports_globally()
    
    # Run comprehensive test suite
    run_all_tests()
    assert all_tests_pass()
```

### Updated Import Structure

```python
# In simulation.py and systems modules
from vmt_engine.game_theory.bargaining import BargainingProtocol
from vmt_engine.game_theory.matching import MatchingProtocol  
from vmt_engine.agent_based.search import SearchProtocol
from vmt_engine.protocols.base import Effect, Trade, Pair, Unpair, Move
from vmt_engine.protocols.registry import ProtocolRegistry
```

---

## Stage 1: Understand What You Have (Weeks 1-2)

### Objective
Create comprehensive behavioral documentation of the current system before making changes.

### Week 1: Behavioral Mapping

```python
class BehavioralTestSuite:
    """
    Systematic testing framework for understanding current system behavior
    """
    
    def __init__(self):
        self.test_scenarios = []
        self.results = {}
        self.metrics = {
            'price_convergence': [],
            'trade_efficiency': [],
            'time_to_equilibrium': [],
            'spatial_patterns': []
        }
    
    def create_test_scenarios(self):
        """
        Generate focused test scenarios for behavioral analysis
        """
        scenarios = {
            'two_agent_trade': {
                'agents': 2,
                'grid_size': 3,
                'goods': ['good_a', 'good_b'],
                'utilities': ['cobb_douglas', 'cobb_douglas'],
                'endowments': [[100, 0], [0, 100]],
                'purpose': 'Simplest bilateral exchange'
            },
            'ten_agent_cluster': {
                'agents': 10,
                'grid_size': 10,
                'goods': ['good_a', 'good_b'],
                'utilities': mixed_utilities(),
                'endowments': random_endowments(10),
                'purpose': 'Spatial clustering dynamics'
            },
            'hundred_agent_market': {
                'agents': 100,
                'grid_size': 30,
                'goods': ['good_a', 'good_b'],
                'utilities': mixed_utilities(100),
                'endowments': random_endowments(100),
                'purpose': 'Large-scale emergence patterns'
            },
            'no_trade_equilibrium': {
                'agents': 4,
                'grid_size': 5,
                'goods': ['good_a', 'good_b'],
                'utilities': identical_utilities(4),
                'endowments': identical_endowments(4),
                'purpose': 'Edge case - no gains from trade'
            },
            'price_convergence_test': {
                'agents': 20,
                'grid_size': 15,
                'goods': ['good_a', 'good_b'],
                'utilities': ['cobb_douglas'] * 20,
                'endowments': split_endowments(20),
                'purpose': 'Test price discovery mechanism'
            }
        }
        
        for name, config in scenarios.items():
            self.test_scenarios.append(
                self.create_scenario_yaml(name, config)
            )
    
    def run_behavioral_analysis(self, n_runs=100):
        """
        Run each scenario multiple times with different seeds
        """
        for scenario in self.test_scenarios:
            scenario_results = []
            
            for seed in range(n_runs):
                # Run simulation
                sim = Simulation(scenario, seed=seed)
                result = sim.run(max_ticks=1000)
                
                # Extract metrics
                metrics = self.extract_metrics(result)
                scenario_results.append(metrics)
            
            # Aggregate results
            self.results[scenario.name] = self.aggregate_results(scenario_results)
    
    def extract_metrics(self, simulation_result):
        """
        Extract key behavioral metrics from simulation run
        """
        metrics = {
            'final_prices': self.compute_price_ratios(simulation_result.trades),
            'convergence_tick': self.find_convergence_point(simulation_result.trades),
            'total_surplus': self.compute_total_surplus(simulation_result),
            'trade_volume': len(simulation_result.trades),
            'spatial_clusters': self.detect_spatial_clusters(simulation_result),
            'efficiency': self.compute_efficiency(simulation_result),
            'price_variance': self.compute_price_variance(simulation_result.trades)
        }
        return metrics
    
    def compute_price_ratios(self, trades):
        """
        Calculate implicit price ratios from bilateral trades
        """
        if not trades:
            return None
            
        price_ratios = []
        for trade in trades:
            # Price ratio = amount_good_a / amount_good_b
            ratio = trade.quantities['good_a'] / trade.quantities['good_b']
            price_ratios.append(ratio)
        
        # Return rolling average of last 20 trades
        if len(price_ratios) > 20:
            return mean(price_ratios[-20:])
        return mean(price_ratios)
    
    def find_convergence_point(self, trades, window=50, threshold=0.05):
        """
        Identify when prices converge to stable values
        """
        if len(trades) < window:
            return None
            
        for i in range(window, len(trades)):
            window_trades = trades[i-window:i]
            price_variance = self.compute_price_variance(window_trades)
            
            if price_variance < threshold:
                return i
        
        return None  # No convergence
    
    def generate_report(self):
        """
        Create comprehensive behavioral documentation
        """
        report = BehavioralReport()
        
        for scenario_name, results in self.results.items():
            report.add_section(scenario_name, {
                'summary_statistics': results.summary_stats,
                'convergence_analysis': results.convergence,
                'spatial_patterns': results.spatial,
                'anomalies': results.anomalies,
                'visualizations': self.create_visualizations(results)
            })
        
        report.save_to_file('docs/behavioral_baseline.md')
        return report
```

### Week 2: Pattern Documentation

```python
class PatternAnalyzer:
    """
    Document emergent patterns and unexpected behaviors
    """
    
    def analyze_spatial_patterns(self, simulation_history):
        """
        Detect and classify spatial trading patterns
        """
        patterns = {
            'market_areas': [],
            'trade_routes': [],
            'dead_zones': [],
            'hotspots': []
        }
        
        # Analyze trade density over space
        trade_density = self.compute_trade_density_map(simulation_history)
        
        # Detect market areas (high-density clusters)
        market_areas = self.detect_clusters(trade_density, threshold=0.7)
        patterns['market_areas'] = market_areas
        
        # Identify trade routes (paths between markets)
        trade_routes = self.trace_agent_paths(simulation_history)
        patterns['trade_routes'] = self.classify_routes(trade_routes)
        
        # Find dead zones (no trading activity)
        dead_zones = self.find_zero_activity_regions(trade_density)
        patterns['dead_zones'] = dead_zones
        
        # Locate hotspots (maximum activity)
        hotspots = self.find_peak_activity_cells(trade_density, top_n=5)
        patterns['hotspots'] = hotspots
        
        return patterns
    
    def analyze_price_dynamics(self, trades):
        """
        Characterize price discovery and convergence behavior
        """
        dynamics = {
            'convergence_type': None,
            'convergence_speed': None,
            'final_price': None,
            'volatility_pattern': None,
            'price_cycles': []
        }
        
        price_series = [self.extract_price(t) for t in trades]
        
        # Classify convergence type
        if self.is_monotonic_convergence(price_series):
            dynamics['convergence_type'] = 'monotonic'
        elif self.is_oscillating_convergence(price_series):
            dynamics['convergence_type'] = 'oscillating'
        elif self.is_cyclic(price_series):
            dynamics['convergence_type'] = 'cyclic'
            dynamics['price_cycles'] = self.detect_cycles(price_series)
        else:
            dynamics['convergence_type'] = 'non_convergent'
        
        # Measure convergence speed
        if dynamics['convergence_type'] in ['monotonic', 'oscillating']:
            dynamics['convergence_speed'] = self.measure_convergence_rate(price_series)
            dynamics['final_price'] = price_series[-1]
        
        # Analyze volatility
        dynamics['volatility_pattern'] = self.classify_volatility(price_series)
        
        return dynamics
    
    def identify_edge_cases(self, results):
        """
        Find and document unexpected or problematic behaviors
        """
        edge_cases = []
        
        for scenario, result in results.items():
            # Check for anomalies
            if result.efficiency < 0.5:
                edge_cases.append({
                    'scenario': scenario,
                    'issue': 'low_efficiency',
                    'details': f"Only {result.efficiency*100}% of possible gains captured"
                })
            
            if result.convergence_tick is None:
                edge_cases.append({
                    'scenario': scenario,
                    'issue': 'no_convergence',
                    'details': "Prices never stabilized"
                })
            
            if result.spatial_patterns['dead_zones']:
                edge_cases.append({
                    'scenario': scenario,
                    'issue': 'spatial_fragmentation',
                    'details': f"{len(result.spatial_patterns['dead_zones'])} isolated regions"
                })
            
            # Check for unexpected equilibria
            theoretical_price = self.compute_theoretical_equilibrium(scenario)
            if abs(result.final_price - theoretical_price) > 0.2:
                edge_cases.append({
                    'scenario': scenario,
                    'issue': 'price_deviation',
                    'details': f"Converged to {result.final_price} vs theoretical {theoretical_price}"
                })
        
        return edge_cases
```

### Deliverable: Behavioral Baseline Document

```markdown
# VMT Behavioral Baseline

## Current System Behavior Analysis

### Price Convergence Patterns
- Two-agent scenarios: Converge to theoretical equilibrium in ~50 ticks
- Ten-agent clusters: Slower convergence (~200 ticks) with spatial variation
- Hundred-agent markets: Multiple local price equilibria, global convergence rare

### Spatial Trading Patterns  
- Market areas form at grid intersections (high traffic zones)
- Agents create stable trade routes after ~100 ticks
- Dead zones persist in corners (low accessibility)

### Efficiency Analysis
- Average efficiency: 75-85% of theoretical maximum
- Efficiency decreases with agent count (coordination failure)
- Spatial constraints reduce efficiency by ~15%

### Edge Cases and Failures
- No-trade equilibrium: System handles correctly (no trades executed)
- Heterogeneous utilities: Price convergence significantly slower
- Large grids: Fragmentation into isolated sub-markets

### Key Insights
1. Current system exhibits reasonable price discovery
2. Spatial constraints create interesting market fragmentation
3. Protocol modifications could improve efficiency
4. Need for information mechanisms evident in large scenarios
```

---

## Stage 2: Diversify Protocols (Weeks 3-6)

### Objective
Implement alternative protocols to demonstrate how institutions affect outcomes.

### Week 3: Baseline Search Protocols

```python
# In src/vmt_engine/agent_based/search/random_walk.py
class RandomWalkSearch(SearchProtocol):
    """
    Zero-information baseline: pure random movement
    """
    
    def __init__(self, params: dict):
        self.name = "random_walk"
        self.params = params
    
    def select_target(self, agent_id: int, world_view: WorldView) -> List[Effect]:
        """
        Move in random direction regardless of opportunities
        """
        current_pos = world_view.get_agent_position(agent_id)
        
        # All possible directions (including stay)
        directions = [
            (0, 0),   # stay
            (0, 1),   # north
            (1, 0),   # east
            (0, -1),  # south
            (-1, 0),  # west
            (1, 1),   # northeast
            (1, -1),  # southeast
            (-1, -1), # southwest
            (-1, 1)   # northwest
        ]
        
        # Choose random direction
        direction = world_view.random.choice(directions)
        
        # Check if move is valid (within bounds)
        new_pos = (current_pos[0] + direction[0], 
                   current_pos[1] + direction[1])
        
        if world_view.is_valid_position(new_pos):
            return [MoveEffect(agent_id, new_pos)]
        else:
            # Stay in place if move would be out of bounds
            return [MoveEffect(agent_id, current_pos)]


# In src/vmt_engine/agent_based/search/myopic.py  
class MyopicSearch(SearchProtocol):
    """
    Greedy search: move toward best visible opportunity
    """
    
    def __init__(self, params: dict):
        self.name = "myopic"
        self.vision_radius = params.get('vision_radius', 3)
    
    def select_target(self, agent_id: int, world_view: WorldView) -> List[Effect]:
        """
        Find and move toward best trade opportunity in vision
        """
        agent = world_view.get_agent(agent_id)
        current_pos = world_view.get_agent_position(agent_id)
        
        # Get all agents within vision radius
        visible_agents = self.get_visible_agents(agent_id, world_view)
        
        if not visible_agents:
            # No one visible, random walk
            return self.random_move(agent_id, world_view)
        
        # Evaluate trade potential with each visible agent
        best_partner = None
        best_surplus = 0
        
        for other_id in visible_agents:
            other = world_view.get_agent(other_id)
            
            # Estimate surplus from potential trade
            surplus = self.estimate_trade_surplus(agent, other)
            
            if surplus > best_surplus:
                best_surplus = surplus
                best_partner = other_id
        
        if best_partner:
            # Move toward best partner
            target_pos = world_view.get_agent_position(best_partner)
            direction = self.compute_direction(current_pos, target_pos)
            new_pos = self.step_toward(current_pos, direction, world_view)
            return [MoveEffect(agent_id, new_pos)]
        else:
            # No profitable trades visible, random walk
            return self.random_move(agent_id, world_view)
    
    def estimate_trade_surplus(self, agent_a: Agent, agent_b: Agent) -> float:
        """
        Quick estimate of gains from trade between two agents
        """
        # Current utilities
        u_a_current = agent_a.compute_utility(agent_a.inventory)
        u_b_current = agent_b.compute_utility(agent_b.inventory)
        
        # Estimate post-trade utilities (simplified)
        # Assume equal split of total endowment
        total_inventory = agent_a.inventory + agent_b.inventory
        split_inventory = total_inventory / 2
        
        u_a_trade = agent_a.compute_utility(split_inventory)
        u_b_trade = agent_b.compute_utility(split_inventory)
        
        # Total surplus
        surplus = (u_a_trade - u_a_current) + (u_b_trade - u_b_current)
        return max(0, surplus)
```

### Week 4: Alternative Matching Protocols

```python
# In src/vmt_engine/game_theory/matching/random.py
class RandomMatching(MatchingProtocol):
    """
    Non-strategic baseline: random pairing
    """
    
    def __init__(self, params: dict):
        self.name = "random_matching"
        self.params = params
    
    def find_matches(self, candidates: List[int], world_view: WorldView) -> List[Effect]:
        """
        Randomly pair agents without considering preferences
        """
        effects = []
        
        # Shuffle candidates
        shuffled = list(candidates)
        world_view.random.shuffle(shuffled)
        
        # Pair adjacent agents in shuffled list
        for i in range(0, len(shuffled) - 1, 2):
            agent_a = shuffled[i]
            agent_b = shuffled[i + 1]
            
            # Check if agents are compatible (e.g., close enough)
            if self.can_pair(agent_a, agent_b, world_view):
                effects.append(PairEffect(agent_a, agent_b))
        
        return effects
    
    def can_pair(self, agent_a: int, agent_b: int, world_view: WorldView) -> bool:
        """
        Check basic pairing constraints
        """
        # Must be on same or adjacent cells
        pos_a = world_view.get_agent_position(agent_a)
        pos_b = world_view.get_agent_position(agent_b)
        
        distance = abs(pos_a[0] - pos_b[0]) + abs(pos_a[1] - pos_b[1])
        return distance <= 1


# In src/vmt_engine/game_theory/matching/greedy_surplus.py
class GreedySurplusMatching(MatchingProtocol):
    """
    Match agents to maximize total surplus
    """
    
    def __init__(self, params: dict):
        self.name = "greedy_surplus"
        self.params = params
    
    def find_matches(self, candidates: List[int], world_view: WorldView) -> List[Effect]:
        """
        Greedy algorithm: iteratively match highest-surplus pairs
        """
        effects = []
        unmatched = set(candidates)
        
        while len(unmatched) >= 2:
            # Find best pair among unmatched
            best_pair = None
            best_surplus = 0
            
            for agent_a in unmatched:
                for agent_b in unmatched:
                    if agent_a >= agent_b:
                        continue  # Avoid duplicates
                    
                    if not self.can_pair(agent_a, agent_b, world_view):
                        continue
                    
                    # Compute expected surplus
                    surplus = self.compute_pair_surplus(agent_a, agent_b, world_view)
                    
                    if surplus > best_surplus:
                        best_surplus = surplus
                        best_pair = (agent_a, agent_b)
            
            if best_pair:
                # Match the best pair
                effects.append(PairEffect(best_pair[0], best_pair[1]))
                unmatched.remove(best_pair[0])
                unmatched.remove(best_pair[1])
            else:
                # No more profitable matches
                break
        
        return effects
    
    def compute_pair_surplus(self, agent_a: int, agent_b: int, world_view: WorldView) -> float:
        """
        Estimate total surplus from matching two agents
        """
        a = world_view.get_agent(agent_a)
        b = world_view.get_agent(agent_b)
        
        # Current utilities
        u_a_current = a.compute_utility(a.inventory)
        u_b_current = b.compute_utility(b.inventory)
        
        # Estimate Pareto improvement potential
        # Use contract curve midpoint as proxy
        total_endowment = a.inventory + b.inventory
        
        # Find approximate efficient allocation
        efficient_alloc = self.estimate_efficient_allocation(a, b, total_endowment)
        
        u_a_efficient = a.compute_utility(efficient_alloc[0])
        u_b_efficient = b.compute_utility(efficient_alloc[1])
        
        surplus = (u_a_efficient - u_a_current) + (u_b_efficient - u_b_current)
        return surplus
```

### Week 5: Alternative Bargaining Protocols

```python
# In src/vmt_engine/game_theory/bargaining/split_difference.py
class SplitTheDifference(BargainingProtocol):
    """
    Always divide surplus equally between agents
    """
    
    def __init__(self, params: dict):
        self.name = "split_difference"
        self.params = params
    
    def negotiate(self, pair: Tuple[int, int], world_view: WorldView) -> List[Effect]:
        """
        Find efficient trade that splits surplus equally
        """
        agent_a_id, agent_b_id = pair
        agent_a = world_view.get_agent(agent_a_id)
        agent_b = world_view.get_agent(agent_b_id)
        
        # Current utilities (disagreement point)
        u_a_current = agent_a.compute_utility(agent_a.inventory)
        u_b_current = agent_b.compute_utility(agent_b.inventory)
        
        # Find trade that equalizes gains
        trade = self.find_equal_gains_trade(agent_a, agent_b, u_a_current, u_b_current)
        
        if trade:
            return [TradeEffect(pair, trade)]
        else:
            # No mutually beneficial trade found
            return [UnpairEffect(agent_a_id, agent_b_id)]
    
    def find_equal_gains_trade(self, agent_a, agent_b, u_a_0, u_b_0):
        """
        Search for trade where both agents gain equally
        """
        total_endowment = agent_a.inventory + agent_b.inventory
        
        # Binary search over possible allocations
        def objective(alpha):
            # Alpha parameterizes position on contract curve
            alloc_a = alpha * total_endowment
            alloc_b = (1 - alpha) * total_endowment
            
            u_a = agent_a.compute_utility(alloc_a)
            u_b = agent_b.compute_utility(alloc_b)
            
            gain_a = u_a - u_a_0
            gain_b = u_b - u_b_0
            
            return gain_a - gain_b  # Zero when gains are equal
        
        # Find alpha where gains are equal
        from scipy.optimize import brentq
        try:
            alpha_star = brentq(objective, 0.001, 0.999)
            
            # Compute final allocations
            final_a = alpha_star * total_endowment
            final_b = (1 - alpha_star) * total_endowment
            
            # Convert to trade quantities
            trade = {
                'from_a': agent_a.inventory - final_a,
                'from_b': agent_b.inventory - final_b
            }
            
            return trade
        except:
            return None


# In src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py
class TakeItOrLeaveIt(BargainingProtocol):
    """
    One agent makes ultimatum offer, other accepts or rejects
    """
    
    def __init__(self, params: dict):
        self.name = "take_it_or_leave_it"
        self.proposer_power = params.get('proposer_power', 0.5)
    
    def negotiate(self, pair: Tuple[int, int], world_view: WorldView) -> List[Effect]:
        """
        Proposer takes most surplus, leaves minimum to accepter
        """
        agent_a_id, agent_b_id = pair
        
        # Randomly select proposer
        if world_view.random.random() < self.proposer_power:
            proposer_id = agent_a_id
            accepter_id = agent_b_id
        else:
            proposer_id = agent_b_id
            accepter_id = agent_a_id
        
        proposer = world_view.get_agent(proposer_id)
        accepter = world_view.get_agent(accepter_id)
        
        # Proposer finds best trade for themselves
        trade = self.compute_ultimatum(proposer, accepter)
        
        if trade and self.accepter_accepts(accepter, trade):
            return [TradeEffect(pair, trade)]
        else:
            return [UnpairEffect(agent_a_id, agent_b_id)]
    
    def compute_ultimatum(self, proposer, accepter):
        """
        Proposer takes maximum subject to accepter's participation
        """
        # Accepter's reservation utility
        u_accepter_min = accepter.compute_utility(accepter.inventory)
        
        # Find trade that maximizes proposer utility
        # subject to accepter getting u_accepter_min + epsilon
        epsilon = 0.01
        
        best_trade = None
        best_proposer_utility = proposer.compute_utility(proposer.inventory)
        
        # Search over possible trades (simplified grid search)
        for trade_size in np.linspace(0.1, 0.9, 20):
            trade = self.construct_trade(proposer, accepter, trade_size)
            
            # Check accepter's constraint
            accepter_final = accepter.inventory + trade['from_proposer'] - trade['from_accepter']
            u_accepter = accepter.compute_utility(accepter_final)
            
            if u_accepter >= u_accepter_min + epsilon:
                # Check proposer's utility
                proposer_final = proposer.inventory - trade['from_proposer'] + trade['from_accepter']
                u_proposer = proposer.compute_utility(proposer_final)
                
                if u_proposer > best_proposer_utility:
                    best_proposer_utility = u_proposer
                    best_trade = trade
        
        return best_trade
```

### Week 6: Protocol Comparison Framework

```python
class ProtocolComparator:
    """
    Framework for systematic protocol comparison
    """
    
    def __init__(self):
        self.protocol_sets = {
            'baseline': {
                'search': 'legacy',
                'matching': 'legacy',
                'bargaining': 'legacy'
            },
            'random_all': {
                'search': 'random_walk',
                'matching': 'random',
                'bargaining': 'split_difference'
            },
            'efficient': {
                'search': 'myopic',
                'matching': 'greedy_surplus',
                'bargaining': 'nash'  # To be implemented in Stage 3
            },
            'strategic': {
                'search': 'myopic',
                'matching': 'stable',  # To be implemented  
                'bargaining': 'take_it_or_leave_it'
            }
        }
        
        self.metrics = {}
    
    def run_comparison(self, test_scenario, n_runs=50):
        """
        Compare protocol sets on same scenario
        """
        results = {}
        
        for protocol_set_name, protocols in self.protocol_sets.items():
            set_results = []
            
            for seed in range(n_runs):
                # Configure simulation with protocol set
                sim = Simulation(
                    scenario=test_scenario,
                    search_protocol=protocols['search'],
                    matching_protocol=protocols['matching'],
                    bargaining_protocol=protocols['bargaining'],
                    seed=seed
                )
                
                # Run and collect metrics
                result = sim.run(max_ticks=1000)
                metrics = self.extract_comparison_metrics(result)
                set_results.append(metrics)
            
            # Aggregate results for this protocol set
            results[protocol_set_name] = self.aggregate_metrics(set_results)
        
        return self.create_comparison_table(results)
    
    def extract_comparison_metrics(self, sim_result):
        """
        Extract metrics relevant for institutional comparison
        """
        return {
            'price_convergence': self.check_convergence(sim_result),
            'convergence_speed': self.measure_convergence_speed(sim_result),
            'efficiency': self.compute_efficiency(sim_result),
            'trade_volume': len(sim_result.trades),
            'average_surplus': self.compute_average_surplus(sim_result),
            'inequality': self.compute_gini_coefficient(sim_result),
            'market_power': self.measure_market_power(sim_result)
        }
    
    def create_comparison_table(self, results):
        """
        Generate formatted comparison table
        """
        table = ComparisonTable()
        
        # Headers
        table.add_header(['Protocol Set', 'Convergence', 'Efficiency', 
                         'Trade Volume', 'Inequality', 'Notes'])
        
        # Add row for each protocol set
        for name, metrics in results.items():
            table.add_row([
                name,
                f"{metrics['price_convergence']} ({metrics['convergence_speed']} ticks)",
                f"{metrics['efficiency']*100:.1f}%",
                metrics['trade_volume'],
                f"{metrics['inequality']:.3f}",
                self.generate_notes(name, metrics)
            ])
        
        return table
    
    def generate_notes(self, protocol_set, metrics):
        """
        Auto-generate insights about protocol performance
        """
        notes = []
        
        if metrics['efficiency'] < 0.6:
            notes.append("Low efficiency - coordination failure")
        
        if not metrics['price_convergence']:
            notes.append("No price convergence")
        
        if metrics['inequality'] > 0.5:
            notes.append("High inequality in outcomes")
        
        if protocol_set == 'strategic' and metrics['market_power'] > 0.3:
            notes.append("Significant exercise of market power")
        
        return "; ".join(notes) if notes else "Normal behavior"
```

### Deliverable: Protocol Comparison Report

```markdown
# Protocol Diversification Results

## Institutional Comparison Table

| Protocol Set | Price Convergence | Efficiency | Trade Volume | Time to Trade |
|-------------|------------------|------------|--------------|---------------|
| Legacy (baseline) | Yes (200 ticks) | 85% | 450 | 5 ticks |
| All Random | No | 60% | 380 | 8 ticks |
| Efficient | Yes (100 ticks) | 92% | 420 | 3 ticks |
| Strategic | Partial | 78% | 390 | 6 ticks |

## Key Findings

1. **Random protocols** significantly reduce efficiency (-25%)
2. **Greedy matching** improves efficiency (+7%) but reduces fairness
3. **Take-it-or-leave-it** creates power imbalances but still achieves trades
4. **Myopic search** accelerates price discovery by 50%

## Institutional Insights

The comparison demonstrates that:
- Market outcomes strongly depend on institutional rules
- No single protocol set dominates on all metrics
- Trade-offs exist between efficiency, fairness, and convergence speed
```

---

## Stage 3: Build Game Theory Track (Weeks 7-12)

See `stage3_game_theory_implementation.md` for detailed pseudocode.

---

## Stage 4: Create Unified Launcher (Weeks 13-14)

See `stage4_launcher_implementation.md` for detailed pseudocode.

---

## Stage 5: Market Information Systems (Weeks 15-22)

See `stage5_market_information_implementation.md` for detailed pseudocode.

---

## Stage 6: Neoclassical Benchmarks (Weeks 23-30)

See `stage6_neoclassical_implementation.md` for detailed pseudocode.

---

## Implementation Timeline & Milestones

| Week | Stage | Milestone | Success Criteria |
|------|-------|-----------|------------------|
| 0 | Prereq | Protocol restructure | All tests pass with new architecture |
| 1-2 | Stage 1 | Behavioral baseline | Complete system documentation |
| 3-6 | Stage 2 | Protocol diversity | 5+ working protocols |
| 7-12 | Stage 3 | Game Theory track | Edgeworth Box + bargaining solutions |
| 13-14 | Stage 4 | Unified launcher | Seamless multi-track navigation |
| 15-22 | Stage 5 | Market information | Emergent price discovery |
| 23-30 | Stage 6 | Neoclassical track | Equilibrium benchmarks |

---

## Critical Success Factors

### Technical Requirements
- ✅ Maintain deterministic reproducibility
- ✅ Ensure protocol compatibility between tracks
- ✅ Preserve Protocol→Effect→State architecture
- ✅ Keep computational performance acceptable (100 agents, 1000 ticks < 1 minute)

### Quality Assurance
- ✅ Comprehensive test coverage (>80%)
- ✅ Continuous integration for all changes
- ✅ Performance benchmarks after each stage
- ✅ User acceptance testing with students

### Documentation Standards
- ✅ API documentation for all protocols
- ✅ Tutorial notebooks for each track
- ✅ Theoretical background documents
- ✅ Implementation guides for extensions

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Protocol incompatibility | Medium | High | Design context-independent interfaces |
| Performance degradation | Low | Medium | Profile regularly, optimize hot paths |
| Scope creep | High | High | Strictly enforce stage boundaries |
| Integration complexity | Medium | Medium | Incremental integration, extensive testing |

---

## Next Steps

1. **Immediate** (This Week):
   - Complete protocol architecture restructure
   - Create first test scenario
   - Begin behavioral documentation

2. **Short Term** (Next Month):
   - Implement all Stage 2 protocols
   - Start Game Theory track development
   - Design unified launcher UI

3. **Medium Term** (Next Quarter):
   - Complete Game Theory track
   - Integrate launcher
   - Begin market information design

---

## Appendices

- Appendix A: `stage3_game_theory_implementation.md` - Game Theory Track details
- Appendix B: `stage4_launcher_implementation.md` - Launcher architecture
- Appendix C: `stage5_market_information_implementation.md` - Information systems
- Appendix D: `stage6_neoclassical_implementation.md` - Equilibrium methods
- Appendix E: `testing_strategy.md` - Comprehensive testing approach

---

**Document Status**: Complete  
**Next Review**: After Stage 1 completion  
**Owner**: VMT Development Team
