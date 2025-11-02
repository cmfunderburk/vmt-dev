# Stage 6: Neoclassical Benchmarks Implementation

**Purpose**: Implement equilibrium methods for theoretical comparison  
**Duration**: Weeks 23-30  
**Prerequisites**: ABM and Game Theory tracks complete

**Pedagogical Frame**: Show what perfect coordination would achieve, highlighting the strong assumptions required

---

## Architecture Overview

```python
# src/vmt_engine/neoclassical/
class NeoclassicalTrack:
    """
    Traditional equilibrium analysis and tatonnement
    
    Key insight: These methods show what's theoretically possible
    with perfect coordination and information
    """
    
    def __init__(self):
        self.walrasian_auctioneer = WalrasianAuctioneer()
        self.tatonnement_simulator = TatonnementProcess()
        self.equilibrium_solver = GeneralEquilibriumSolver()
        self.stability_analyzer = StabilityAnalyzer()
        self.scarf_demonstrator = ScarfCounterexample()
```

---

## Week 23-24: Walrasian Auctioneer Implementation

### Core Auctioneer Mechanism

```python
# src/vmt_engine/neoclassical/walrasian.py
import numpy as np
from scipy.optimize import fsolve, minimize
from typing import List, Dict, Tuple

class WalrasianAuctioneer:
    """
    Centralized market clearing mechanism
    
    Critical pedagogical point: This requires an omniscient coordinator
    who knows all preferences and can enforce trades
    """
    
    def __init__(self, agents: List[Agent], goods: List[str]):
        self.agents = agents
        self.n_agents = len(agents)
        self.goods = goods
        self.n_goods = len(goods)
        
        # Initial price guess (good 0 is numeraire)
        self.prices = np.ones(self.n_goods)
        self.prices[0] = 1.0  # Numeraire
        
        self.equilibrium_prices = None
        self.equilibrium_allocation = None
        
    def find_equilibrium(self, method='fsolve'):
        """
        Solve for market-clearing prices
        
        Methods:
        - 'fsolve': Direct numerical solution
        - 'tatonnement': Iterative adjustment
        - 'minimize': Minimization of excess demand norm
        """
        if method == 'fsolve':
            self.equilibrium_prices = self.solve_direct()
        elif method == 'tatonnement':
            self.equilibrium_prices = self.solve_tatonnement()
        elif method == 'minimize':
            self.equilibrium_prices = self.solve_minimization()
        
        if self.equilibrium_prices is not None:
            self.equilibrium_allocation = self.compute_allocation(
                self.equilibrium_prices
            )
        
        return self.equilibrium_prices, self.equilibrium_allocation
    
    def solve_direct(self):
        """
        Direct solution using fsolve
        """
        # Only solve for n-1 prices (good 0 is numeraire)
        initial_prices = self.prices[1:]
        
        def excess_demand_system(p):
            # Reconstruct full price vector
            prices = np.concatenate([[1.0], p])
            
            # Compute excess demand for non-numeraire goods
            excess = self.compute_excess_demand(prices)[1:]
            
            return excess
        
        # Solve for equilibrium
        solution = fsolve(
            excess_demand_system,
            initial_prices,
            full_output=True
        )
        
        prices_solution, info, ier, msg = solution
        
        if ier == 1:  # Solution found
            # Reconstruct full price vector
            equilibrium_prices = np.concatenate([[1.0], prices_solution])
            
            # Verify market clearing
            excess = self.compute_excess_demand(equilibrium_prices)
            if np.allclose(excess, 0, atol=1e-6):
                return equilibrium_prices
        
        print(f"Walrasian equilibrium not found: {msg}")
        return None
    
    def compute_excess_demand(self, prices):
        """
        Compute aggregate excess demand at given prices
        
        Z(p) = Total Demand(p) - Total Supply
        """
        total_demand = np.zeros(self.n_goods)
        total_supply = np.zeros(self.n_goods)
        
        for agent in self.agents:
            # Agent's budget from endowment
            endowment_value = np.dot(prices, agent.endowment)
            
            # Agent's optimal demand at prices
            demand = agent.marshallian_demand(prices, endowment_value)
            
            total_demand += demand
            total_supply += agent.endowment
        
        excess_demand = total_demand - total_supply
        
        return excess_demand
    
    def compute_allocation(self, prices):
        """
        Compute equilibrium allocation at market-clearing prices
        """
        allocation = {}
        
        for agent in self.agents:
            # Agent's budget
            budget = np.dot(prices, agent.endowment)
            
            # Agent's optimal consumption
            consumption = agent.marshallian_demand(prices, budget)
            
            allocation[agent.id] = {
                'consumption': consumption,
                'utility': agent.compute_utility(consumption),
                'budget': budget
            }
        
        return allocation
    
    def verify_walras_law(self, prices):
        """
        Verify Walras' Law: p · z(p) = 0
        
        Educational: Shows that markets are interdependent
        """
        excess_demand = self.compute_excess_demand(prices)
        value_of_excess = np.dot(prices, excess_demand)
        
        return abs(value_of_excess) < 1e-10
```

### Agent Demand Functions

```python
# Extension to Agent class for neoclassical analysis
class Agent:
    """
    Agent with Marshallian demand functions
    """
    
    def marshallian_demand(self, prices: np.ndarray, income: float) -> np.ndarray:
        """
        Compute optimal consumption bundle given prices and income
        
        This is the solution to:
        max U(x) subject to p·x = m
        """
        if self.utility_type == 'cobb_douglas':
            return self.cobb_douglas_demand(prices, income)
        elif self.utility_type == 'ces':
            return self.ces_demand(prices, income)
        elif self.utility_type == 'leontief':
            return self.leontief_demand(prices, income)
        else:
            return self.numerical_demand(prices, income)
    
    def cobb_douglas_demand(self, prices, income):
        """
        Closed-form Cobb-Douglas demand
        U = Π(x_i^α_i) where Σα_i = 1
        """
        alphas = self.utility_params['alphas']  # Share parameters
        
        demand = np.zeros(self.n_goods)
        for i in range(self.n_goods):
            demand[i] = alphas[i] * income / prices[i]
        
        return demand
    
    def ces_demand(self, prices, income):
        """
        CES (Constant Elasticity of Substitution) demand
        """
        rho = self.utility_params['rho']
        alphas = self.utility_params['alphas']
        
        # Elasticity of substitution
        sigma = 1 / (1 - rho)
        
        # Price index
        price_index = sum(
            alphas[i] * prices[i]**(1-sigma) 
            for i in range(self.n_goods)
        )**(1/(1-sigma))
        
        # Demand for each good
        demand = np.zeros(self.n_goods)
        for i in range(self.n_goods):
            demand[i] = (alphas[i] * income * 
                        (prices[i] / price_index)**(-sigma) / prices[i])
        
        return demand
    
    def leontief_demand(self, prices, income):
        """
        Leontief (perfect complements) demand
        """
        coefficients = self.utility_params['coefficients']
        
        # Find cheapest bundle satisfying proportions
        bundle_cost = sum(coefficients[i] * prices[i] 
                         for i in range(self.n_goods))
        
        # Scale by income
        scale = income / bundle_cost
        
        return coefficients * scale
    
    def numerical_demand(self, prices, income):
        """
        Numerical optimization for general utility functions
        """
        from scipy.optimize import minimize
        
        def objective(x):
            return -self.compute_utility(x)
        
        def budget_constraint(x):
            return income - np.dot(prices, x)
        
        constraints = [
            {'type': 'eq', 'fun': budget_constraint}
        ]
        
        bounds = [(0, income/prices[i]) for i in range(self.n_goods)]
        
        # Initial guess: equal expenditure shares
        x0 = np.array([income/(self.n_goods * prices[i]) 
                      for i in range(self.n_goods)])
        
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

## Week 25-26: Tatonnement Process

### Iterative Price Adjustment

```python
# src/vmt_engine/neoclassical/tatonnement.py
class TatonnementProcess:
    """
    Iterative price adjustment process
    
    Educational insight: Shows how prices might adjust if there
    were a coordinator calling out prices until markets clear
    """
    
    def __init__(self, auctioneer: WalrasianAuctioneer):
        self.auctioneer = auctioneer
        self.adjustment_speed = 0.1
        self.max_iterations = 1000
        self.convergence_tolerance = 1e-6
        
        # History tracking
        self.price_history = []
        self.excess_demand_history = []
        
    def run(self, initial_prices=None):
        """
        Run tatonnement process until convergence or max iterations
        """
        # Initialize prices
        if initial_prices is None:
            prices = np.ones(self.auctioneer.n_goods)
        else:
            prices = initial_prices.copy()
        
        prices[0] = 1.0  # Numeraire
        
        for iteration in range(self.max_iterations):
            # Record current state
            self.price_history.append(prices.copy())
            
            # Compute excess demand
            excess_demand = self.auctioneer.compute_excess_demand(prices)
            self.excess_demand_history.append(excess_demand.copy())
            
            # Check convergence
            if np.allclose(excess_demand[1:], 0, atol=self.convergence_tolerance):
                print(f"Tatonnement converged in {iteration} iterations")
                return prices
            
            # Adjust prices (not numeraire)
            prices = self.adjust_prices(prices, excess_demand)
            
            # Ensure positive prices
            prices = np.maximum(prices, 1e-8)
            
            # Re-normalize (keep good 0 as numeraire)
            prices = prices / prices[0]
        
        print(f"Tatonnement did not converge after {self.max_iterations} iterations")
        return None
    
    def adjust_prices(self, prices, excess_demand):
        """
        Price adjustment rule
        
        Various rules possible:
        - Simple: p_new = p_old + λ * excess_demand
        - Proportional: p_new = p_old * (1 + λ * excess_demand/supply)
        - Newton: Use Jacobian for faster convergence
        """
        new_prices = prices.copy()
        
        # Don't adjust numeraire
        for i in range(1, self.auctioneer.n_goods):
            # Simple adjustment proportional to excess demand
            adjustment = self.adjustment_speed * excess_demand[i]
            
            # Proportional adjustment (more stable)
            new_prices[i] = prices[i] * (1 + adjustment)
        
        return new_prices
    
    def analyze_convergence(self):
        """
        Analyze convergence properties
        """
        if not self.price_history:
            return None
        
        analysis = {
            'converged': len(self.price_history) < self.max_iterations,
            'iterations': len(self.price_history),
            'final_excess': np.linalg.norm(self.excess_demand_history[-1]),
            'price_path': np.array(self.price_history),
            'oscillations': self.detect_oscillations(),
            'convergence_rate': self.estimate_convergence_rate()
        }
        
        return analysis
    
    def detect_oscillations(self):
        """
        Check if prices are oscillating
        """
        if len(self.price_history) < 3:
            return False
        
        # Check for sign changes in price changes
        price_changes = np.diff(self.price_history, axis=0)
        sign_changes = np.diff(np.sign(price_changes), axis=0)
        
        # Oscillation if frequent sign changes
        oscillation_count = np.sum(np.abs(sign_changes) > 0)
        
        return oscillation_count > len(self.price_history) / 2
```

### Advanced Tatonnement Variants

```python
class NewtonTatonnement(TatonnementProcess):
    """
    Newton-Raphson method for faster convergence
    """
    
    def adjust_prices(self, prices, excess_demand):
        """
        Use Jacobian of excess demand for Newton step
        """
        # Compute Jacobian numerically
        jacobian = self.compute_jacobian(prices)
        
        # Newton step (for non-numeraire goods)
        try:
            # Solve J * Δp = -z for price adjustment
            from scipy.linalg import solve
            
            # Extract sub-matrix for non-numeraire goods
            J_sub = jacobian[1:, 1:]
            z_sub = excess_demand[1:]
            
            # Compute adjustment
            delta_p = solve(J_sub, -z_sub)
            
            # Apply adjustment with dampening
            new_prices = prices.copy()
            new_prices[1:] += self.adjustment_speed * delta_p
            
            return new_prices
            
        except:
            # Fall back to simple adjustment if Newton fails
            return super().adjust_prices(prices, excess_demand)
    
    def compute_jacobian(self, prices, epsilon=1e-6):
        """
        Numerical Jacobian of excess demand function
        """
        n = self.auctioneer.n_goods
        jacobian = np.zeros((n, n))
        
        base_excess = self.auctioneer.compute_excess_demand(prices)
        
        for j in range(n):
            # Perturb price j
            perturbed_prices = prices.copy()
            perturbed_prices[j] += epsilon
            
            # Re-normalize if necessary
            if j == 0:
                continue  # Skip numeraire
            
            perturbed_excess = self.auctioneer.compute_excess_demand(perturbed_prices)
            
            # Finite difference
            jacobian[:, j] = (perturbed_excess - base_excess) / epsilon
        
        return jacobian
```

---

## Week 27-28: Stability Analysis

### Analyzing Equilibrium Stability

```python
# src/vmt_engine/neoclassical/stability.py
class StabilityAnalyzer:
    """
    Analyze stability of competitive equilibrium
    """
    
    def __init__(self, auctioneer: WalrasianAuctioneer):
        self.auctioneer = auctioneer
    
    def analyze_local_stability(self, equilibrium_prices):
        """
        Check local stability via eigenvalues of Jacobian
        """
        # Compute Jacobian at equilibrium
        jacobian = self.compute_jacobian_at_equilibrium(equilibrium_prices)
        
        # Compute eigenvalues
        eigenvalues = np.linalg.eigvals(jacobian[1:, 1:])  # Exclude numeraire
        
        # Check stability conditions
        stability = {
            'locally_stable': np.all(np.real(eigenvalues) < 0),
            'eigenvalues': eigenvalues,
            'max_eigenvalue': np.max(np.real(eigenvalues)),
            'oscillatory': np.any(np.abs(np.imag(eigenvalues)) > 1e-6)
        }
        
        return stability
    
    def analyze_global_stability(self, n_trials=100):
        """
        Test global stability from random starting points
        """
        convergence_results = []
        
        for trial in range(n_trials):
            # Random initial prices
            initial_prices = np.random.exponential(1.0, self.auctioneer.n_goods)
            initial_prices[0] = 1.0  # Numeraire
            
            # Run tatonnement
            tatonnement = TatonnementProcess(self.auctioneer)
            final_prices = tatonnement.run(initial_prices)
            
            convergence_results.append({
                'converged': final_prices is not None,
                'initial': initial_prices,
                'final': final_prices,
                'iterations': len(tatonnement.price_history)
            })
        
        # Analyze results
        convergence_rate = sum(r['converged'] for r in convergence_results) / n_trials
        
        return {
            'global_convergence_rate': convergence_rate,
            'average_iterations': np.mean([r['iterations'] for r in convergence_results if r['converged']]),
            'results': convergence_results
        }
    
    def compute_jacobian_at_equilibrium(self, equilibrium_prices):
        """
        Compute Jacobian of excess demand at equilibrium
        """
        epsilon = 1e-6
        n = self.auctioneer.n_goods
        jacobian = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if j == 0:  # Skip numeraire column
                    continue
                
                # Partial derivative of excess demand i w.r.t. price j
                prices_plus = equilibrium_prices.copy()
                prices_plus[j] += epsilon
                
                prices_minus = equilibrium_prices.copy()
                prices_minus[j] -= epsilon
                
                excess_plus = self.auctioneer.compute_excess_demand(prices_plus)[i]
                excess_minus = self.auctioneer.compute_excess_demand(prices_minus)[i]
                
                jacobian[i, j] = (excess_plus - excess_minus) / (2 * epsilon)
        
        return jacobian
```

### Scarf's Counterexample

```python
class ScarfCounterexample:
    """
    Demonstrate cases where tatonnement fails
    
    Educational: Shows that convergence is not guaranteed
    even with well-behaved preferences
    """
    
    def __init__(self):
        self.n_agents = 3
        self.n_goods = 3
    
    def create_scarf_economy(self):
        """
        Create Scarf's classic counterexample economy
        """
        # Three agents with specific CES utilities
        agents = []
        
        # Agent 1: Wants goods 1 and 2
        agent1 = Agent(
            id=1,
            utility_type='ces',
            utility_params={'rho': -1, 'alphas': [0.5, 0.5, 0]},
            endowment=np.array([1, 0, 0])
        )
        
        # Agent 2: Wants goods 2 and 3
        agent2 = Agent(
            id=2,
            utility_type='ces',
            utility_params={'rho': -1, 'alphas': [0, 0.5, 0.5]},
            endowment=np.array([0, 1, 0])
        )
        
        # Agent 3: Wants goods 3 and 1
        agent3 = Agent(
            id=3,
            utility_type='ces',
            utility_params={'rho': -1, 'alphas': [0.5, 0, 0.5]},
            endowment=np.array([0, 0, 1])
        )
        
        agents = [agent1, agent2, agent3]
        
        return agents
    
    def demonstrate_instability(self):
        """
        Show that tatonnement cycles in Scarf economy
        """
        agents = self.create_scarf_economy()
        auctioneer = WalrasianAuctioneer(agents, ['good1', 'good2', 'good3'])
        
        # Try to find equilibrium with tatonnement
        tatonnement = TatonnementProcess(auctioneer)
        tatonnement.max_iterations = 500
        
        result = tatonnement.run()
        
        # Analyze the price path
        analysis = tatonnement.analyze_convergence()
        
        # Create visualization
        self.visualize_price_cycles(tatonnement.price_history)
        
        return {
            'converged': result is not None,
            'oscillations': analysis['oscillations'],
            'price_history': tatonnement.price_history,
            'message': "Scarf economy demonstrates non-convergence of tatonnement"
        }
    
    def visualize_price_cycles(self, price_history):
        """
        3D visualization of price cycles
        """
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        prices = np.array(price_history)
        
        # Plot price path in 3D
        ax.plot(prices[:, 0], prices[:, 1], prices[:, 2], 
               'b-', alpha=0.6, linewidth=1)
        
        # Mark starting point
        ax.scatter(prices[0, 0], prices[0, 1], prices[0, 2], 
                  c='green', s=100, label='Start')
        
        # Mark end point
        ax.scatter(prices[-1, 0], prices[-1, 1], prices[-1, 2], 
                  c='red', s=100, label='End')
        
        ax.set_xlabel('Price Good 1')
        ax.set_ylabel('Price Good 2')
        ax.set_zlabel('Price Good 3')
        ax.set_title("Scarf Counterexample: Tatonnement Cycles")
        ax.legend()
        
        plt.show()
```

---

## Week 29-30: Integration and Comparison

### Neoclassical Results Analyzer

```python
class NeoclassicalAnalyzer:
    """
    Compare neoclassical predictions with ABM outcomes
    """
    
    def __init__(self):
        self.abm_results = None
        self.neoclassical_results = None
        self.comparison = None
    
    def compute_theoretical_benchmark(self, scenario):
        """
        Compute neoclassical equilibrium for scenario
        """
        # Extract agents from scenario
        agents = self.create_agents_from_scenario(scenario)
        
        # Create auctioneer
        auctioneer = WalrasianAuctioneer(agents, scenario['goods'])
        
        # Find equilibrium
        eq_prices, eq_allocation = auctioneer.find_equilibrium()
        
        # Compute welfare metrics
        metrics = self.compute_welfare_metrics(eq_allocation)
        
        return {
            'prices': eq_prices,
            'allocation': eq_allocation,
            'total_utility': metrics['total_utility'],
            'efficiency': 1.0,  # Pareto efficient by construction
            'inequality': metrics['gini_coefficient']
        }
    
    def compare_with_abm(self, abm_result, neoclassical_result):
        """
        Compare emergent ABM outcome with theoretical prediction
        """
        comparison = {
            'price_deviation': self.compute_price_deviation(
                abm_result['final_prices'],
                neoclassical_result['prices']
            ),
            'efficiency_gap': (
                neoclassical_result['efficiency'] - 
                abm_result['efficiency']
            ),
            'convergence_speed': {
                'abm': abm_result.get('convergence_tick', None),
                'tatonnement': self.test_tatonnement_speed(neoclassical_result)
            },
            'welfare_comparison': {
                'abm_total_utility': abm_result['total_utility'],
                'neo_total_utility': neoclassical_result['total_utility'],
                'welfare_loss': (
                    neoclassical_result['total_utility'] - 
                    abm_result['total_utility']
                )
            }
        }
        
        return comparison
    
    def create_comparison_report(self):
        """
        Generate comprehensive comparison report
        """
        report = ComparisonReport()
        
        # Add summary table
        report.add_table(
            "ABM vs Neoclassical Outcomes",
            headers=["Metric", "ABM", "Neoclassical", "Gap"],
            rows=[
                ["Final Price Ratio", self.abm_results['price_ratio'], 
                 self.neoclassical_results['price_ratio'], 
                 self.comparison['price_deviation']],
                ["Efficiency", f"{self.abm_results['efficiency']*100:.1f}%",
                 "100%", f"{self.comparison['efficiency_gap']*100:.1f}%"],
                ["Convergence Time", f"{self.abm_results['convergence_tick']} ticks",
                 f"{self.comparison['convergence_speed']['tatonnement']} iterations",
                 "N/A"]
            ]
        )
        
        # Add interpretation
        report.add_interpretation("""
        The neoclassical model achieves perfect efficiency through:
        1. Omniscient auctioneer who knows all preferences
        2. Simultaneous market clearing
        3. Perfect price information for all agents
        4. No transaction costs or spatial constraints
        
        The ABM shows realistic frictions through:
        1. Bilateral negotiations with limited information
        2. Sequential trading with search costs
        3. Spatial constraints on interactions
        4. Heterogeneous information quality
        
        The efficiency gap represents the cost of decentralization.
        """)
        
        return report
```

### Visualization Suite

```python
class NeoclassicalVisualizer:
    """
    Visualize neoclassical concepts and results
    """
    
    def visualize_tatonnement_process(self, tatonnement_result):
        """
        Animate tatonnement price adjustment
        """
        import matplotlib.pyplot as plt
        import matplotlib.animation as animation
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        price_history = np.array(tatonnement_result.price_history)
        excess_history = np.array(tatonnement_result.excess_demand_history)
        
        # Price path
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Price')
        ax1.set_title('Tatonnement Price Adjustment')
        
        # Excess demand
        ax2.set_xlabel('Iteration')
        ax2.set_ylabel('Excess Demand')
        ax2.set_title('Market Clearing Progress')
        ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        
        lines1 = []
        lines2 = []
        
        for i in range(price_history.shape[1]):
            line1, = ax1.plot([], [], label=f'Good {i}')
            lines1.append(line1)
            
            if i > 0:  # Skip numeraire
                line2, = ax2.plot([], [], label=f'Good {i}')
                lines2.append(line2)
        
        ax1.legend()
        ax2.legend()
        
        def animate(frame):
            for i, line in enumerate(lines1):
                line.set_data(range(frame), price_history[:frame, i])
            
            for i, line in enumerate(lines2):
                line.set_data(range(frame), excess_history[:frame, i+1])
            
            ax1.relim()
            ax1.autoscale_view()
            ax2.relim()
            ax2.autoscale_view()
            
            return lines1 + lines2
        
        anim = animation.FuncAnimation(
            fig, animate, frames=len(price_history),
            interval=50, blit=True
        )
        
        return anim
    
    def visualize_welfare_comparison(self, abm_allocation, neo_allocation):
        """
        Compare welfare distributions
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Extract utilities
        abm_utilities = [a['utility'] for a in abm_allocation.values()]
        neo_utilities = [a['utility'] for a in neo_allocation.values()]
        
        # Lorenz curves
        self.plot_lorenz_curve(ax1, abm_utilities, label='ABM')
        self.plot_lorenz_curve(ax1, neo_utilities, label='Neoclassical')
        ax1.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='Perfect Equality')
        ax1.set_xlabel('Cumulative Population')
        ax1.set_ylabel('Cumulative Utility')
        ax1.set_title('Lorenz Curves')
        ax1.legend()
        
        # Utility distributions
        ax2.hist(abm_utilities, alpha=0.5, label='ABM', bins=20)
        ax2.hist(neo_utilities, alpha=0.5, label='Neoclassical', bins=20)
        ax2.set_xlabel('Utility')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Utility Distributions')
        ax2.legend()
        
        return fig
```

---

## Deliverables

1. **Walrasian auctioneer** with multiple solution methods
2. **Tatonnement simulator** with convergence analysis
3. **Stability analyzer** for equilibrium testing
4. **Scarf counterexample** demonstration
5. **Comparison framework** ABM vs Neoclassical
6. **Visualization suite** for equilibrium concepts

---

## Success Metrics

- ✅ Can compute competitive equilibrium for any exchange economy
- ✅ Tatonnement convergence matches theoretical predictions
- ✅ Successfully demonstrates Scarf counterexample
- ✅ Clear comparison between ABM and neoclassical outcomes
- ✅ Students understand assumptions required for equilibrium
- ✅ Efficiency gap quantified between emergent and optimal
