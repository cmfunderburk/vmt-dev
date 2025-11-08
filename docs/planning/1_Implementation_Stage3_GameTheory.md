# Stage 3: Game Theory Track Implementation

**Purpose**: Detailed pseudocode for building the Game Theory Track  
**Duration**: Weeks 7-12  
**Prerequisites**: Protocol restructure complete, Stage 2 protocols implemented

---

## Architecture Overview

> **Terminology Note**: In this stage, reserve verbs like "compute", "determine", or "solve" for coordination tasks that require global information. Use "find" only for local search behaviors that an individual agent could perform autonomously. The pseudocode below follows this convention.

```python
# src/vmt_engine/game_theory/__init__.py
class GameTheoryTrack:
    """
    Main entry point for Game Theory analysis
    """
    
    def __init__(self):
        self.exchange_engine = TwoAgentExchange()
        self.bargaining_solver = BargainingSolver()
        self.visualizer = EdgeworthBoxVisualizer()
        self.protocol_tester = ProtocolTester()
```

---

## Week 7-8: Two-Agent Exchange Engine

### Core Exchange Engine

```python
# src/vmt_engine/game_theory/exchange_engine.py
class TwoAgentExchange:
    """
    Pure exchange economy with two agents and two goods
    """
    
    def __init__(self, agent_a: Agent, agent_b: Agent):
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.total_endowment = agent_a.inventory + agent_b.inventory
        self.contract_curve = None
        self.competitive_equilibrium = None
        
    def compute_contract_curve(self, n_points=100):
        """
        Compute the set of Pareto efficient allocations
        """
        contract_curve = []
        
        # Parameterize allocations along the diagonal
        for alpha in np.linspace(0.01, 0.99, n_points):
            # Start from alpha-weighted allocation
            initial_alloc_a = alpha * self.total_endowment
            
        # Compute Pareto efficient allocation with this utility level
        efficient_alloc = self.compute_efficient_allocation(
                initial_alloc_a,
                self.agent_a.compute_utility(initial_alloc_a)
            )
            
            if efficient_alloc:
                contract_curve.append({
                    'allocation_a': efficient_alloc[0],
                    'allocation_b': efficient_alloc[1],
                    'utility_a': self.agent_a.compute_utility(efficient_alloc[0]),
                    'utility_b': self.agent_b.compute_utility(efficient_alloc[1])
                })
        
        self.contract_curve = contract_curve
        return contract_curve
    
    def compute_efficient_allocation(self, initial_alloc_a, target_utility_a):
        """
        Compute the Pareto efficient allocation consistent with agent A's target utility level
        """
        from scipy.optimize import minimize
        
        def objective(x):
            # x = [good_1_for_a, good_2_for_a]
            alloc_a = np.array(x)
            alloc_b = self.total_endowment - alloc_a
            
            # Maximize B's utility
            return -self.agent_b.compute_utility(alloc_b)
        
        def constraint_a_utility(x):
            # Agent A must achieve target utility
            alloc_a = np.array(x)
            return self.agent_a.compute_utility(alloc_a) - target_utility_a
        
        def constraint_feasibility(x):
            # Allocations must be non-negative and feasible
            alloc_a = np.array(x)
            alloc_b = self.total_endowment - alloc_a
            return np.concatenate([alloc_a, alloc_b])
        
        constraints = [
            {'type': 'eq', 'fun': constraint_a_utility},
            {'type': 'ineq', 'fun': constraint_feasibility}
        ]
        
        result = minimize(
            objective,
            x0=initial_alloc_a,
            method='SLSQP',
            constraints=constraints,
            bounds=[(0, self.total_endowment[0]), 
                   (0, self.total_endowment[1])]
        )
        
        if result.success:
            alloc_a = result.x
            alloc_b = self.total_endowment - alloc_a
            return (alloc_a, alloc_b)
        return None
    
    def compute_competitive_equilibrium(self):
        """
        Compute market-clearing prices and allocation
        """
        from scipy.optimize import fsolve
        
        def excess_demand(prices):
            """
            Compute excess demand at given prices
            """
            # Normalize prices (good 1 as numeraire)
            p = np.array([1.0, prices[0]])
            
            # Agent A's demand
            budget_a = np.dot(p, self.agent_a.inventory)
            demand_a = self.agent_a.optimal_bundle(p, budget_a)
            
            # Agent B's demand
            budget_b = np.dot(p, self.agent_b.inventory)
            demand_b = self.agent_b.optimal_bundle(p, budget_b)
            
            # Total demand and supply
            total_demand = demand_a + demand_b
            total_supply = self.total_endowment
            
            # Excess demand for good 2 (good 1 is numeraire)
            return total_demand[1] - total_supply[1]
        
        # Solve for the equilibrium price ratio
        initial_price = [1.0]  # Initial guess for p2/p1
        eq_price = fsolve(excess_demand, initial_price)[0]
        
        # Compute equilibrium allocation given prices
        prices = np.array([1.0, eq_price])
        
        budget_a = np.dot(prices, self.agent_a.inventory)
        alloc_a = self.agent_a.optimal_bundle(prices, budget_a)
        alloc_b = self.total_endowment - alloc_a
        
        self.competitive_equilibrium = {
            'prices': prices,
            'allocation_a': alloc_a,
            'allocation_b': alloc_b,
            'utility_a': self.agent_a.compute_utility(alloc_a),
            'utility_b': self.agent_b.compute_utility(alloc_b)
        }
        
        return self.competitive_equilibrium
```

### Agent Optimization Methods

```python
# Extension to Agent class for Game Theory track
class Agent:
    """
    Extended with optimization methods for Game Theory analysis
    """
    
    def optimal_bundle(self, prices: np.ndarray, budget: float) -> np.ndarray:
        """
        Compute optimal consumption bundle given prices and budget
        """
        if self.utility_type == 'cobb_douglas':
            return self.cobb_douglas_demand(prices, budget)
        elif self.utility_type == 'ces':
            return self.ces_demand(prices, budget)
        elif self.utility_type == 'leontief':
            return self.leontief_demand(prices, budget)
        else:
            # General numerical optimization
            return self.numerical_demand(prices, budget)
    
    def cobb_douglas_demand(self, prices, budget):
        """
        Closed-form solution for Cobb-Douglas utility
        """
        # U = x1^alpha * x2^(1-alpha)
        alpha = self.utility_params['alpha']
        
        x1 = alpha * budget / prices[0]
        x2 = (1 - alpha) * budget / prices[1]
        
        return np.array([x1, x2])
    
    def ces_demand(self, prices, budget):
        """
        CES utility demand function
        """
        rho = self.utility_params['rho']
        alpha = self.utility_params['alpha']
        
        # Elasticity of substitution
        sigma = 1 / (1 - rho)
        
        # Demand functions
        price_ratio = prices[1] / prices[0]
        x1_x2_ratio = (alpha / (1 - alpha) * price_ratio) ** sigma
        
        x1 = budget / (prices[0] + prices[1] * x1_x2_ratio)
        x2 = x1 * x1_x2_ratio
        
        return np.array([x1, x2])
    
    def numerical_demand(self, prices, budget):
        """
        General numerical optimization for arbitrary utility
        """
        from scipy.optimize import minimize
        
        def objective(x):
            return -self.compute_utility(x)
        
        def budget_constraint(x):
            return budget - np.dot(prices, x)
        
        constraints = [{'type': 'eq', 'fun': budget_constraint}]
        bounds = [(0, budget/p) for p in prices]
        
        # Initial guess: equal expenditure shares
        x0 = budget / (2 * prices)
        
        result = minimize(
            objective,
            x0=x0,
            method='SLSQP',
            constraints=constraints,
            bounds=bounds
        )
        
        return result.x if result.success else x0
```

---

## Week 9-10: Interactive Edgeworth Box Visualization

### Core Visualization Engine

```python
# src/vmt_engine/game_theory/visualization.py
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.widgets import Slider, Button
import numpy as np

class EdgeworthBoxVisualizer:
    """
    Interactive Edgeworth Box with real-time updates
    """
    
    def __init__(self, exchange_engine: TwoAgentExchange):
        self.engine = exchange_engine
        self.fig = None
        self.ax = None
        self.current_allocation = None
        self.setup_plot()
    
    def setup_plot(self):
        """
        Initialize the Edgeworth Box plot
        """
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        plt.subplots_adjust(bottom=0.25)
        
        # Box dimensions = total endowment
        self.width = self.engine.total_endowment[0]
        self.height = self.engine.total_endowment[1]
        
        # Draw box
        box = Rectangle((0, 0), self.width, self.height, 
                       fill=False, edgecolor='black', linewidth=2)
        self.ax.add_patch(box)
        
        # Labels
        self.ax.set_xlabel('Good 1 for Agent A →', fontsize=12)
        self.ax.set_ylabel('Good 2 for Agent A ↑', fontsize=12)
        self.ax.text(self.width, self.height, 'Agent B Origin', 
                    ha='right', va='top', fontsize=10)
        self.ax.text(0, 0, 'Agent A Origin', 
                    ha='left', va='bottom', fontsize=10)
        
        # Set axis limits
        self.ax.set_xlim(-0.5, self.width + 0.5)
        self.ax.set_ylim(-0.5, self.height + 0.5)
        
        # Initial allocation (endowment point)
        self.current_allocation = self.engine.agent_a.inventory
        
        # Plot elements (to be updated)
        self.allocation_point = None
        self.indiff_curve_a = None
        self.indiff_curve_b = None
        self.contract_curve_line = None
        
        # Add sliders for allocation
        self.add_sliders()
        
        # Add buttons
        self.add_buttons()
        
        # Initial draw
        self.update_plot()
    
    def add_sliders(self):
        """
        Add sliders to control allocation
        """
        # Slider for good 1 allocation to agent A
        ax_slider1 = plt.axes([0.2, 0.1, 0.6, 0.03])
        self.slider1 = Slider(
            ax_slider1, 'Good 1 to A', 
            0, self.width, 
            valinit=self.current_allocation[0]
        )
        
        # Slider for good 2 allocation to agent A
        ax_slider2 = plt.axes([0.2, 0.05, 0.6, 0.03])
        self.slider2 = Slider(
            ax_slider2, 'Good 2 to A', 
            0, self.height, 
            valinit=self.current_allocation[1]
        )
        
        # Connect sliders to update function
        self.slider1.on_changed(self.on_slider_change)
        self.slider2.on_changed(self.on_slider_change)
    
    def add_buttons(self):
        """
        Add control buttons
        """
        # Button to show contract curve
        ax_contract = plt.axes([0.05, 0.9, 0.15, 0.04])
        self.btn_contract = Button(ax_contract, 'Contract Curve')
        self.btn_contract.on_clicked(self.toggle_contract_curve)
        
        # Button to find competitive equilibrium
        ax_equilibrium = plt.axes([0.25, 0.9, 0.15, 0.04])
        self.btn_equilibrium = Button(ax_equilibrium, 'Equilibrium')
        self.btn_equilibrium.on_clicked(self.show_equilibrium)
        
        # Button to test bargaining protocol
        ax_bargain = plt.axes([0.45, 0.9, 0.15, 0.04])
        self.btn_bargain = Button(ax_bargain, 'Test Protocol')
        self.btn_bargain.on_clicked(self.test_bargaining)
    
    def on_slider_change(self, val):
        """
        Update allocation when sliders change
        """
        self.current_allocation = np.array([
            self.slider1.val,
            self.slider2.val
        ])
        self.update_plot()
    
    def update_plot(self):
        """
        Redraw all plot elements
        """
        self.ax.clear()
        self.setup_plot()  # Redraw box and labels
        
        # Current allocation point
        self.draw_allocation_point()
        
        # Indifference curves
        self.draw_indifference_curves()
        
        # Display utility values
        self.display_utilities()
        
        # Redraw if contract curve is visible
        if hasattr(self, 'show_contract') and self.show_contract:
            self.draw_contract_curve()
        
        self.fig.canvas.draw_idle()
    
    def draw_allocation_point(self):
        """
        Draw current allocation as a point
        """
        x, y = self.current_allocation
        
        # Plot point
        self.ax.plot(x, y, 'ro', markersize=10, label='Current Allocation')
        
        # Draw lines to both origins
        self.ax.plot([0, x], [0, y], 'r--', alpha=0.3)
        self.ax.plot([x, self.width], [y, self.height], 'b--', alpha=0.3)
    
    def draw_indifference_curves(self):
        """
        Draw indifference curves through current allocation
        """
        # Agent A's indifference curve
        u_a = self.engine.agent_a.compute_utility(self.current_allocation)
        curve_a = self.compute_indifference_curve(
            self.engine.agent_a, u_a, 'a'
        )
        
        if curve_a:
            self.ax.plot(curve_a[:, 0], curve_a[:, 1], 
                        'r-', alpha=0.6, label='Agent A IC')
        
        # Agent B's indifference curve (from their origin)
        alloc_b = self.engine.total_endowment - self.current_allocation
        u_b = self.engine.agent_b.compute_utility(alloc_b)
        curve_b = self.compute_indifference_curve(
            self.engine.agent_b, u_b, 'b'
        )
        
        if curve_b:
            # Transform to A's coordinate system
            curve_b_transformed = self.engine.total_endowment - curve_b
            self.ax.plot(curve_b_transformed[:, 0], curve_b_transformed[:, 1], 
                        'b-', alpha=0.6, label='Agent B IC')
    
    def compute_indifference_curve(self, agent, utility_level, agent_label):
        """
        Compute points on indifference curve for given utility level
        """
        points = []
        
        if agent_label == 'a':
            x_range = np.linspace(0.01, self.width, 100)
        else:
            x_range = np.linspace(0.01, self.width, 100)
        
        for x1 in x_range:
            # Solve for x2 given x1 and utility level
            x2 = self.solve_for_x2(agent, x1, utility_level)
            
            if x2 is not None and 0 <= x2 <= self.height:
                points.append([x1, x2])
        
        return np.array(points) if points else None
    
    def solve_for_x2(self, agent, x1, target_utility):
        """
        Solve for x2 given x1 and target utility
        """
        from scipy.optimize import brentq
        
        def objective(x2):
            bundle = np.array([x1, x2])
            return agent.compute_utility(bundle) - target_utility
        
        try:
            x2 = brentq(objective, 0.001, self.height)
            return x2
        except:
            return None
    
    def draw_contract_curve(self):
        """
        Draw the contract curve (Pareto efficient allocations)
        """
        if self.engine.contract_curve is None:
            self.engine.compute_contract_curve()
        
        # Extract points
        points = np.array([
            [point['allocation_a'][0], point['allocation_a'][1]]
            for point in self.engine.contract_curve
        ])
        
        # Plot curve
        self.ax.plot(points[:, 0], points[:, 1], 
                    'g-', linewidth=2, label='Contract Curve')
        
        # Mark endowment point
        endow = self.engine.agent_a.inventory
        self.ax.plot(endow[0], endow[1], 'ks', 
                    markersize=8, label='Endowment')
    
    def show_equilibrium(self, event):
        """
        Compute and display competitive equilibrium
        """
        if self.engine.competitive_equilibrium is None:
            self.engine.compute_competitive_equilibrium()
        
        eq = self.engine.competitive_equilibrium
        
        # Plot equilibrium point
        self.ax.plot(eq['allocation_a'][0], eq['allocation_a'][1], 
                    'g*', markersize=15, label='Competitive Eq.')
        
        # Draw budget line
        prices = eq['prices']
        endow_value = np.dot(prices, self.engine.total_endowment)
        
        # Budget line points
        x1_max = endow_value / prices[0]
        x2_max = endow_value / prices[1]
        
        self.ax.plot([0, x1_max], [x2_max, 0], 
                    'k--', alpha=0.5, label=f'Budget (p={prices[1]/prices[0]:.2f})')
        
        self.fig.canvas.draw_idle()
```

---

## Week 11-12: Bargaining Solutions Implementation

### Nash Bargaining Solution

```python
# src/vmt_engine/game_theory/bargaining/nash.py
class NashBargaining(BargainingProtocol):
    """
    Nash bargaining solution: maximize product of gains
    """
    
    def __init__(self, params: dict):
        self.name = "nash_bargaining"
        self.params = params
    
    def negotiate(self, pair: Tuple[int, int], world_view: WorldView) -> List[Effect]:
        """
        Compute the Nash bargaining solution for the agent pair
        """
        agent_a_id, agent_b_id = pair
        agent_a = world_view.get_agent(agent_a_id)
        agent_b = world_view.get_agent(agent_b_id)
        
        # Compute Nash solution
        solution = self.compute_nash_solution(agent_a, agent_b)
        
        if solution:
            # Convert to trade
            trade = self.solution_to_trade(solution, agent_a, agent_b)
            return [TradeEffect(pair, trade)]
        else:
            return [UnpairEffect(agent_a_id, agent_b_id)]
    
    def compute_nash_solution(self, agent_a, agent_b):
        """
        Maximize (u_a - d_a)(u_b - d_b) subject to feasibility
        """
        from scipy.optimize import minimize
        
        # Disagreement point (current utilities)
        d_a = agent_a.compute_utility(agent_a.inventory)
        d_b = agent_b.compute_utility(agent_b.inventory)
        
        total_endowment = agent_a.inventory + agent_b.inventory
        
        def objective(x):
            # x = allocation for agent A
            alloc_a = x
            alloc_b = total_endowment - alloc_a
            
            u_a = agent_a.compute_utility(alloc_a)
            u_b = agent_b.compute_utility(alloc_b)
            
            # Nash product (negative for minimization)
            if u_a > d_a and u_b > d_b:
                return -((u_a - d_a) * (u_b - d_b))
            else:
                return 1e10  # Penalty for infeasible
        
        # Constraints
        bounds = [
            (0, total_endowment[0]),
            (0, total_endowment[1])
        ]
        
        # Initial guess: midpoint
        x0 = total_endowment / 2
        
        result = minimize(
            objective,
            x0=x0,
            method='L-BFGS-B',
            bounds=bounds
        )
        
        if result.success:
            return {
                'allocation_a': result.x,
                'allocation_b': total_endowment - result.x,
                'nash_product': -result.fun
            }
        return None
```

### Kalai-Smorodinsky Solution

```python
# src/vmt_engine/game_theory/bargaining/kalai_smorodinsky.py
class KalaiSmorodinsky(BargainingProtocol):
    """
    Kalai-Smorodinsky solution: proportional gains
    """
    
    def compute_ks_solution(self, agent_a, agent_b):
        """
        Compute the allocation where gains are proportional to the maximum attainable gains
        """
        # Disagreement point
        d_a = agent_a.compute_utility(agent_a.inventory)
        d_b = agent_b.compute_utility(agent_b.inventory)
        
        # Compute ideal points (maximum utility each agent could achieve)
        ideal_a = self.compute_ideal_point(agent_a, agent_b, 'a')
        ideal_b = self.compute_ideal_point(agent_a, agent_b, 'b')
        
        # Maximum possible gains
        max_gain_a = ideal_a - d_a
        max_gain_b = ideal_b - d_b
        
        # Determine allocation on Pareto frontier with proportional gains
        from scipy.optimize import minimize_scalar
        
        def objective(t):
            # t parameterizes position on contract curve
            # Interpolate between disagreement and ideal
            target_gain_a = t * max_gain_a
            target_utility_a = d_a + target_gain_a
            
            # Compute Pareto efficient allocation with this utility for A
            alloc = self.compute_efficient_allocation_with_utility(
                agent_a, agent_b, target_utility_a
            )
            
            if alloc:
                u_b = agent_b.compute_utility(alloc['allocation_b'])
                gain_b = u_b - d_b
                
                # Check proportionality
                if max_gain_b > 0:
                    ratio_a = target_gain_a / max_gain_a
                    ratio_b = gain_b / max_gain_b
                    return abs(ratio_a - ratio_b)
            
            return 1e10
        
        result = minimize_scalar(objective, bounds=(0, 1), method='bounded')
        
        if result.success:
            t_star = result.x
            target_utility_a = d_a + t_star * max_gain_a
            
            return self.compute_efficient_allocation_with_utility(
                agent_a, agent_b, target_utility_a
            )
        
        return None
```

### Rubinstein Alternating Offers

```python
# src/vmt_engine/game_theory/bargaining/rubinstein.py
class RubinsteinBargaining(BargainingProtocol):
    """
    Rubinstein alternating offers with discounting
    """
    
    def __init__(self, params: dict):
        self.name = "rubinstein"
        self.delta_a = params.get('discount_a', 0.9)
        self.delta_b = params.get('discount_b', 0.9)
        self.max_rounds = params.get('max_rounds', 100)
    
    def compute_subgame_perfect_equilibrium(self, agent_a, agent_b):
        """
        Solve for unique subgame perfect equilibrium
        """
        # In infinite horizon with discounting, there's a unique SPE
        # Agent A gets: (1 - delta_b) / (1 - delta_a * delta_b) of surplus
        # Agent B gets: delta_b * (1 - delta_a) / (1 - delta_a * delta_b) of surplus
        
        # Compute total surplus
        total_endowment = agent_a.inventory + agent_b.inventory
        
        # Compute efficient frontier
        contract_curve = self.compute_contract_curve(agent_a, agent_b)
        
        # Disagreement utilities
        d_a = agent_a.compute_utility(agent_a.inventory)
        d_b = agent_b.compute_utility(agent_b.inventory)
        
        # Maximum achievable utilities
        max_surplus = self.compute_maximum_surplus(agent_a, agent_b, contract_curve)
        
        # Rubinstein shares
        share_a = (1 - self.delta_b) / (1 - self.delta_a * self.delta_b)
        share_b = self.delta_b * (1 - self.delta_a) / (1 - self.delta_a * self.delta_b)
        
        # Target utilities
        target_u_a = d_a + share_a * max_surplus
        target_u_b = d_b + share_b * max_surplus
        
        # Determine allocation achieving these utilities
        return self.compute_allocation_with_utilities(
            agent_a, agent_b, target_u_a, target_u_b
        )
    
    def simulate_alternating_offers(self, agent_a, agent_b):
        """
        Simulate actual alternating offer process
        """
        offers = []
        current_proposer = 'a'
        
        for round in range(self.max_rounds):
            if current_proposer == 'a':
                # Agent A makes offer
                offer = self.compute_optimal_offer(
                    agent_a, agent_b, 
                    rounds_left=self.max_rounds - round,
                    is_proposer=True
                )
                
                # Agent B accepts or rejects
                if self.agent_accepts(agent_b, offer, round):
                    return offer
                
                current_proposer = 'b'
                
            else:
                # Agent B makes offer
                offer = self.compute_optimal_offer(
                    agent_b, agent_a,
                    rounds_left=self.max_rounds - round,
                    is_proposer=True
                )
                
                # Agent A accepts or rejects
                if self.agent_accepts(agent_a, offer, round):
                    return offer
                
                current_proposer = 'a'
            
            offers.append(offer)
        
        # If no agreement, return disagreement
        return None
```

---

## Protocol Testing Framework

```python
# src/vmt_engine/game_theory/protocol_tester.py
class ProtocolTester:
    """
    Test bargaining protocols in Game Theory context
    """
    
    def __init__(self, exchange_engine):
        self.engine = exchange_engine
        self.results = {}
    
    def test_protocol(self, protocol_name: str, visualize=True):
        """
        Test a bargaining protocol and analyze results
        """
        # Load protocol
        protocol = self.load_protocol(protocol_name)
        
        # Create minimal world view
        world_view = self.create_minimal_worldview()
        
        # Execute negotiation
        effects = protocol.negotiate(
            (self.engine.agent_a.id, self.engine.agent_b.id),
            world_view
        )
        
        # Analyze outcome
        result = self.analyze_outcome(effects)
        
        # Visualize if requested
        if visualize:
            self.visualize_outcome(result, protocol_name)
        
        # Store results
        self.results[protocol_name] = result
        
        return result
    
    def create_minimal_worldview(self):
        """
        Create minimal WorldView for 2-agent testing
        """
        return MinimalWorldView({
            self.engine.agent_a.id: self.engine.agent_a,
            self.engine.agent_b.id: self.engine.agent_b
        })
    
    def analyze_outcome(self, effects):
        """
        Analyze bargaining outcome
        """
        analysis = {
            'trade_executed': False,
            'final_allocation': None,
            'utilities': None,
            'efficiency': None,
            'fairness': None
        }
        
        for effect in effects:
            if isinstance(effect, TradeEffect):
                analysis['trade_executed'] = True
                
                # Compute final allocations
                trade = effect.trade
                final_a = self.engine.agent_a.inventory + trade.net_for_a
                final_b = self.engine.agent_b.inventory + trade.net_for_b
                
                analysis['final_allocation'] = {
                    'agent_a': final_a,
                    'agent_b': final_b
                }
                
                # Compute utilities
                u_a = self.engine.agent_a.compute_utility(final_a)
                u_b = self.engine.agent_b.compute_utility(final_b)
                
                analysis['utilities'] = {
                    'agent_a': u_a,
                    'agent_b': u_b
                }
                
                # Check Pareto efficiency
                analysis['efficiency'] = self.check_pareto_efficiency(final_a, final_b)
                
                # Measure fairness
                analysis['fairness'] = self.measure_fairness(u_a, u_b)
        
        return analysis
    
    def compare_protocols(self, protocol_list):
        """
        Compare multiple protocols on same scenario
        """
        comparison = {}
        
        for protocol_name in protocol_list:
            result = self.test_protocol(protocol_name, visualize=False)
            comparison[protocol_name] = {
                'efficiency': result['efficiency'],
                'fairness': result['fairness'],
                'total_utility': sum(result['utilities'].values()) if result['utilities'] else 0,
                'trade_executed': result['trade_executed']
            }
        
        return self.create_comparison_table(comparison)
```

---

## Integration with Agent-Based Track

```python
class GameTheoryIntegration:
    """
    Bridge between Game Theory and Agent-Based tracks
    """
    
    def import_protocol_to_abm(self, protocol_name: str):
        """
        Import Game Theory protocol for use in ABM
        """
        # Protocol already in game_theory module
        from vmt_engine.game_theory.bargaining import get_protocol
        
        protocol = get_protocol(protocol_name)
        
        # Register for ABM use
        from vmt_engine.protocols.registry import register_protocol
        register_protocol('bargaining', protocol_name, protocol)
        
        return protocol
    
    def validate_protocol_compatibility(self, protocol):
        """
        Ensure protocol works in both contexts
        """
        # Test in Game Theory context
        gt_test = self.test_in_game_theory(protocol)
        
        # Test in ABM context
        abm_test = self.test_in_abm(protocol)
        
        # Compare results
        compatibility = {
            'works_in_gt': gt_test.success,
            'works_in_abm': abm_test.success,
            'consistent_results': self.results_consistent(gt_test, abm_test)
        }
        
        return compatibility
```

---

## Deliverables

1. **Working Edgeworth Box** with interactive allocation control
2. **Contract curve computation** and visualization
3. **Competitive equilibrium** solver and display
4. **Three bargaining solutions** (Nash, KS, Rubinstein)
5. **Protocol testing framework** for theoretical validation
6. **Integration bridge** to Agent-Based track

---

## Success Metrics

- ✅ Can demonstrate Nash bargaining solution visually
- ✅ Can compare different bargaining solutions on same scenario
- ✅ Protocols work in both Game Theory and ABM contexts
- ✅ Students can manipulate allocations and see effects
- ✅ Theoretical predictions match implementation
