# Stage 5: Market Information Systems Implementation

**Purpose**: Add emergent price discovery and information mechanisms to ABM  
**Duration**: Weeks 15-22  
**Prerequisites**: ABM track stable, multiple protocols implemented

**Critical Design Principle**: Information must emerge from actual trades, not external calculation

---

## Architecture Overview

```python
# src/vmt_engine/agent_based/information/
class MarketInformationSystem:
    """
    Emergent price discovery from bilateral trades
    
    Key principles:
    - No external price calculation
    - All signals from actual trades
    - Spatially local information
    - Natural lag and noise
    """
    
    def __init__(self):
        self.market_detector = MarketAreaDetector()
        self.price_aggregator = PriceAggregator()
        self.information_broadcaster = InformationBroadcaster()
        self.memory_system = AgentMemorySystem()
```

---

## Week 15-16: Market Area Detection

### Spatial Clustering of Trades

```python
# src/vmt_engine/agent_based/information/market_detection.py
import numpy as np
from sklearn.cluster import DBSCAN
from collections import defaultdict

class MarketAreaDetector:
    """
    Detect emergent market areas from trade density
    """
    
    def __init__(self, params: dict):
        self.min_trades_for_market = params.get('min_trades', 10)
        self.spatial_radius = params.get('spatial_radius', 3)
        self.time_window = params.get('time_window', 50)
        self.trade_history = defaultdict(list)
        self.current_markets = []
    
    def update(self, trades: List[Trade], current_tick: int):
        """
        Update market detection with new trades
        """
        # Add trades to history with timestamps
        for trade in trades:
            location = self.get_trade_location(trade)
            self.trade_history[location].append({
                'trade': trade,
                'tick': current_tick,
                'agents': trade.agents,
                'quantities': trade.quantities
            })
        
        # Remove old trades outside time window
        self.prune_old_trades(current_tick)
        
        # Detect market areas
        self.current_markets = self.detect_markets()
        
        return self.current_markets
    
    def detect_markets(self):
        """
        Use spatial clustering to identify market areas
        """
        # Get all recent trade locations
        trade_points = []
        trade_data = []
        
        for location, trades in self.trade_history.items():
            if len(trades) >= self.min_trades_for_market:
                for _ in trades:
                    trade_points.append(location)
                    trade_data.append(trades)
        
        if not trade_points:
            return []
        
        # Apply DBSCAN clustering
        trade_array = np.array(trade_points)
        clustering = DBSCAN(
            eps=self.spatial_radius,
            min_samples=self.min_trades_for_market
        ).fit(trade_array)
        
        # Extract market areas
        markets = []
        for cluster_id in set(clustering.labels_):
            if cluster_id == -1:  # Noise points
                continue
            
            cluster_mask = clustering.labels_ == cluster_id
            cluster_points = trade_array[cluster_mask]
            
            market = MarketArea(
                id=cluster_id,
                center=np.mean(cluster_points, axis=0),
                radius=np.std(cluster_points),
                trade_count=len(cluster_points),
                trades=self.get_trades_in_area(cluster_points)
            )
            
            markets.append(market)
        
        return markets
    
    def get_trade_location(self, trade):
        """
        Determine spatial location of a trade
        """
        # Average position of trading agents
        agent_positions = [
            self.get_agent_position(agent_id) 
            for agent_id in trade.agents
        ]
        return tuple(np.mean(agent_positions, axis=0).astype(int))
    
    def prune_old_trades(self, current_tick):
        """
        Remove trades outside the time window
        """
        cutoff_tick = current_tick - self.time_window
        
        for location in list(self.trade_history.keys()):
            self.trade_history[location] = [
                t for t in self.trade_history[location]
                if t['tick'] >= cutoff_tick
            ]
            
            # Remove location if no recent trades
            if not self.trade_history[location]:
                del self.trade_history[location]

class MarketArea:
    """
    Represents an emergent market area
    """
    
    def __init__(self, id, center, radius, trade_count, trades):
        self.id = id
        self.center = center
        self.radius = radius
        self.trade_count = trade_count
        self.trades = trades
        self.price_signal = None
    
    def contains_position(self, position):
        """
        Check if position is within market area
        """
        distance = np.linalg.norm(np.array(position) - self.center)
        return distance <= self.radius * 1.5  # Some buffer
    
    def get_recent_trades(self, window=20):
        """
        Get most recent trades in this market
        """
        sorted_trades = sorted(self.trades, key=lambda t: t['tick'])
        return sorted_trades[-window:] if len(sorted_trades) > window else sorted_trades
```

---

## Week 17-18: Price Signal Aggregation

### Extracting Price Information from Trades

```python
# src/vmt_engine/agent_based/information/price_aggregation.py
class PriceAggregator:
    """
    Aggregate price signals from bilateral trades
    
    Critical: Prices emerge from actual exchange ratios,
    not from any external calculation
    """
    
    def __init__(self, params: dict):
        self.aggregation_method = params.get('method', 'weighted_average')
        self.confidence_threshold = params.get('confidence_threshold', 0.7)
        self.min_observations = params.get('min_observations', 5)
    
    def compute_price_signal(self, market_area: MarketArea) -> PriceSignal:
        """
        Extract price signal from trades in market area
        """
        recent_trades = market_area.get_recent_trades()
        
        if len(recent_trades) < self.min_observations:
            return None
        
        # Extract exchange ratios from trades
        price_observations = []
        weights = []
        
        for trade_data in recent_trades:
            trade = trade_data['trade']
            
            # Calculate implicit price ratio from trade
            # Price = units_good_a / units_good_b exchanged
            ratio = self.extract_price_ratio(trade)
            
            if ratio:
                price_observations.append(ratio)
                
                # Weight by recency and trade volume
                recency_weight = self.compute_recency_weight(trade_data['tick'])
                volume_weight = self.compute_volume_weight(trade)
                weights.append(recency_weight * volume_weight)
        
        if not price_observations:
            return None
        
        # Aggregate prices
        if self.aggregation_method == 'weighted_average':
            price_estimate = self.weighted_average(price_observations, weights)
        elif self.aggregation_method == 'median':
            price_estimate = np.median(price_observations)
        elif self.aggregation_method == 'trimmed_mean':
            price_estimate = self.trimmed_mean(price_observations, trim=0.1)
        else:
            price_estimate = np.mean(price_observations)
        
        # Compute confidence based on consistency
        confidence = self.compute_confidence(price_observations)
        
        # Create price signal
        signal = PriceSignal(
            location=market_area.center,
            price_ratio=price_estimate,
            confidence=confidence,
            n_observations=len(price_observations),
            timestamp=self.current_tick,
            market_id=market_area.id
        )
        
        return signal
    
    def extract_price_ratio(self, trade):
        """
        Extract implicit price ratio from bilateral trade
        
        Critical: This is where prices emerge naturally from trades
        """
        # Get quantities exchanged
        quantities = trade.quantities
        
        # Assuming two goods for simplicity
        if 'good_a' in quantities and 'good_b' in quantities:
            qty_a = quantities['good_a']
            qty_b = quantities['good_b']
            
            # One agent gives A and receives B, other does opposite
            # Extract the exchange ratio
            if qty_b != 0:
                return abs(qty_a / qty_b)
        
        return None
    
    def compute_recency_weight(self, trade_tick):
        """
        More recent trades get higher weight
        """
        age = self.current_tick - trade_tick
        return np.exp(-age / 20)  # Exponential decay
    
    def compute_volume_weight(self, trade):
        """
        Larger trades are more informative
        """
        total_volume = sum(abs(q) for q in trade.quantities.values())
        return np.log(1 + total_volume)
    
    def compute_confidence(self, price_observations):
        """
        Confidence based on price consistency
        """
        if len(price_observations) < 2:
            return 0.5
        
        # Low variance = high confidence
        variance = np.var(price_observations)
        mean_price = np.mean(price_observations)
        
        if mean_price > 0:
            cv = np.sqrt(variance) / mean_price  # Coefficient of variation
            confidence = np.exp(-cv)  # High CV = low confidence
            return np.clip(confidence, 0, 1)
        
        return 0.5

class PriceSignal:
    """
    Emergent price information from market area
    """
    
    def __init__(self, location, price_ratio, confidence, 
                 n_observations, timestamp, market_id):
        self.location = location
        self.price_ratio = price_ratio
        self.confidence = confidence
        self.n_observations = n_observations
        self.timestamp = timestamp
        self.market_id = market_id
    
    def get_strength_at_distance(self, distance):
        """
        Signal strength decreases with distance
        """
        # Exponential decay with distance
        return self.confidence * np.exp(-distance / 5)
    
    def is_reliable(self):
        """
        Check if signal is reliable enough to use
        """
        return self.confidence > 0.7 and self.n_observations >= 10
```

---

## Week 19-20: Information Broadcasting

### Spatial Information Diffusion

```python
# src/vmt_engine/agent_based/information/broadcasting.py
class InformationBroadcaster:
    """
    Broadcast price signals with spatial decay
    
    Key principle: Information is local and imperfect
    """
    
    def __init__(self, params: dict):
        self.broadcast_radius = params.get('broadcast_radius', 10)
        self.noise_level = params.get('noise_level', 0.1)
        self.delay_per_distance = params.get('delay_per_distance', 0.5)
        self.signal_cache = {}
    
    def broadcast_signals(self, price_signals: List[PriceSignal], 
                         world_state) -> Dict:
        """
        Make price signals available to agents based on location
        """
        # Clear old cache
        self.signal_cache = {}
        
        # Process each signal
        for signal in price_signals:
            self.propagate_signal(signal, world_state)
        
        return self.signal_cache
    
    def propagate_signal(self, signal: PriceSignal, world_state):
        """
        Propagate signal through space with decay and noise
        """
        # Get all positions within broadcast radius
        affected_positions = self.get_affected_positions(
            signal.location, 
            self.broadcast_radius,
            world_state.grid_size
        )
        
        for position in affected_positions:
            distance = self.compute_distance(signal.location, position)
            
            # Signal strength decreases with distance
            strength = signal.get_strength_at_distance(distance)
            
            if strength > 0.1:  # Minimum threshold
                # Add noise proportional to distance
                noisy_price = self.add_noise(signal.price_ratio, distance)
                
                # Delay increases with distance
                delay = int(distance * self.delay_per_distance)
                
                # Store in cache for agents at this position
                if position not in self.signal_cache:
                    self.signal_cache[position] = []
                
                self.signal_cache[position].append({
                    'price': noisy_price,
                    'confidence': strength,
                    'delay': delay,
                    'source': signal.market_id,
                    'original': signal.price_ratio
                })
    
    def add_noise(self, price, distance):
        """
        Add noise to price signal based on distance
        """
        noise_std = self.noise_level * (1 + distance / 10)
        noise = np.random.normal(0, noise_std)
        return price * (1 + noise)
    
    def get_signal_for_agent(self, agent_position, current_tick):
        """
        Get available price signals for agent at position
        """
        if agent_position not in self.signal_cache:
            return None
        
        # Filter signals by delay
        available_signals = [
            s for s in self.signal_cache[agent_position]
            if current_tick >= s['delay']
        ]
        
        if not available_signals:
            return None
        
        # Return best (highest confidence) signal
        return max(available_signals, key=lambda s: s['confidence'])
```

### Agent Memory System

```python
# src/vmt_engine/agent_based/information/memory.py
class AgentMemorySystem:
    """
    Agents remember past trades and prices
    """
    
    def __init__(self, params: dict):
        self.memory_capacity = params.get('capacity', 20)
        self.memory_decay = params.get('decay_rate', 0.95)
        self.agent_memories = defaultdict(lambda: AgentMemory(self.memory_capacity))
    
    def record_trade(self, agent_id, trade, outcome):
        """
        Agent records trade experience
        """
        memory = self.agent_memories[agent_id]
        memory.add_trade({
            'partner': trade.other_agent(agent_id),
            'price_ratio': self.extract_realized_price(trade, agent_id),
            'surplus': outcome.surplus_gained,
            'tick': self.current_tick
        })
    
    def record_observed_price(self, agent_id, price_signal):
        """
        Agent observes market price signal
        """
        memory = self.agent_memories[agent_id]
        memory.add_observation({
            'price': price_signal['price'],
            'confidence': price_signal['confidence'],
            'tick': self.current_tick
        })
    
    def get_agent_price_belief(self, agent_id):
        """
        Agent's belief about current market price
        """
        memory = self.agent_memories[agent_id]
        
        # Combine personal experience with market signals
        personal_prices = memory.get_recent_trade_prices()
        observed_prices = memory.get_recent_observations()
        
        if not personal_prices and not observed_prices:
            return None
        
        # Weight personal experience more heavily
        all_prices = []
        all_weights = []
        
        for price, age in personal_prices:
            weight = 2.0 * (self.memory_decay ** age)  # Personal weight = 2x
            all_prices.append(price)
            all_weights.append(weight)
        
        for obs in observed_prices:
            age = self.current_tick - obs['tick']
            weight = obs['confidence'] * (self.memory_decay ** age)
            all_prices.append(obs['price'])
            all_weights.append(weight)
        
        # Weighted average
        if sum(all_weights) > 0:
            return np.average(all_prices, weights=all_weights)
        return np.mean(all_prices)

class AgentMemory:
    """
    Individual agent's memory
    """
    
    def __init__(self, capacity):
        self.capacity = capacity
        self.trades = deque(maxlen=capacity)
        self.observations = deque(maxlen=capacity)
    
    def add_trade(self, trade_data):
        """
        Remember a trade
        """
        self.trades.append(trade_data)
    
    def add_observation(self, observation):
        """
        Remember a price observation
        """
        self.observations.append(observation)
    
    def get_recent_trade_prices(self, n=10):
        """
        Get prices from recent trades
        """
        recent = list(self.trades)[-n:]
        return [(t['price_ratio'], self.current_tick - t['tick']) 
                for t in recent if t.get('price_ratio')]
    
    def get_recent_observations(self, n=10):
        """
        Get recent price observations
        """
        return list(self.observations)[-n:]
```

---

## Week 21-22: Information-Aware Protocols

### Market-Informed Bargaining

```python
# src/vmt_engine/game_theory/bargaining/market_informed.py
class MarketInformedBargaining(BargainingProtocol):
    """
    Bargaining protocol that uses market price signals
    
    Agents anchor on market prices when available
    """
    
    def __init__(self, params: dict):
        self.name = "market_informed"
        self.anchor_strength = params.get('anchor_strength', 0.7)
        self.fallback_protocol = params.get('fallback', 'split_difference')
    
    def negotiate(self, pair: Tuple[int, int], world_view: WorldView) -> List[Effect]:
        """
        Negotiate using market information if available
        """
        agent_a_id, agent_b_id = pair
        
        # Check for available price signals
        price_a = self.get_agent_price_belief(agent_a_id, world_view)
        price_b = self.get_agent_price_belief(agent_b_id, world_view)
        
        if price_a or price_b:
            # At least one agent has price information
            return self.informed_negotiation(
                pair, world_view, price_a, price_b
            )
        else:
            # No price information, use fallback
            return self.fallback_negotiation(pair, world_view)
    
    def informed_negotiation(self, pair, world_view, price_a, price_b):
        """
        Negotiate with price anchoring
        """
        agent_a_id, agent_b_id = pair
        agent_a = world_view.get_agent(agent_a_id)
        agent_b = world_view.get_agent(agent_b_id)
        
        # Determine anchor price
        if price_a and price_b:
            # Both have prices, average them
            anchor_price = (price_a + price_b) / 2
        elif price_a:
            anchor_price = price_a
        else:
            anchor_price = price_b
        
        # Find trade at anchor price
        trade = self.find_trade_at_price(
            agent_a, agent_b, anchor_price
        )
        
        if trade:
            # Adjust based on anchor strength
            if self.anchor_strength < 1.0:
                # Allow some deviation from anchor
                bilateral_trade = self.bilateral_bargain(agent_a, agent_b)
                if bilateral_trade:
                    # Weighted average of anchor and bilateral
                    trade = self.blend_trades(
                        trade, bilateral_trade, 
                        self.anchor_strength
                    )
            
            return [TradeEffect(pair, trade)]
        else:
            return [UnpairEffect(agent_a_id, agent_b_id)]
    
    def find_trade_at_price(self, agent_a, agent_b, price_ratio):
        """
        Find mutually beneficial trade at given price ratio
        """
        total_endowment = agent_a.inventory + agent_b.inventory
        
        # Search along price line for Pareto improvement
        from scipy.optimize import minimize_scalar
        
        def objective(trade_amount):
            # Trade amount of good_a for good_b at price_ratio
            trade_a_to_b = trade_amount
            trade_b_to_a = trade_amount * price_ratio
            
            # Check feasibility
            if trade_a_to_b > agent_a.inventory['good_a']:
                return -1e10
            if trade_b_to_a > agent_b.inventory['good_b']:
                return -1e10
            
            # New inventories
            new_a = agent_a.inventory.copy()
            new_a['good_a'] -= trade_a_to_b
            new_a['good_b'] += trade_b_to_a
            
            new_b = agent_b.inventory.copy()
            new_b['good_a'] += trade_a_to_b
            new_b['good_b'] -= trade_b_to_a
            
            # Compute utilities
            u_a = agent_a.compute_utility(new_a)
            u_b = agent_b.compute_utility(new_b)
            
            # Original utilities
            u_a_0 = agent_a.compute_utility(agent_a.inventory)
            u_b_0 = agent_b.compute_utility(agent_b.inventory)
            
            # Total surplus (negative for minimization)
            surplus = (u_a - u_a_0) + (u_b - u_b_0)
            return -surplus
        
        result = minimize_scalar(
            objective,
            bounds=(0, min(agent_a.inventory['good_a'], 
                          agent_b.inventory['good_b'] / price_ratio)),
            method='bounded'
        )
        
        if result.success and -result.fun > 0:
            trade_amount = result.x
            return {
                'from_a_to_b': {'good_a': trade_amount},
                'from_b_to_a': {'good_b': trade_amount * price_ratio}
            }
        
        return None
```

### Information-Aware Search

```python
# src/vmt_engine/agent_based/search/information_guided.py
class InformationGuidedSearch(SearchProtocol):
    """
    Search guided by market price signals
    """
    
    def __init__(self, params: dict):
        self.name = "information_guided"
        self.exploitation_rate = params.get('exploitation_rate', 0.7)
    
    def select_target(self, agent_id: int, world_view: WorldView) -> List[Effect]:
        """
        Move toward areas with favorable price signals
        """
        agent = world_view.get_agent(agent_id)
        current_pos = world_view.get_agent_position(agent_id)
        
        # Get available price signals
        signals = world_view.get_price_signals_near(current_pos)
        
        if signals and np.random.random() < self.exploitation_rate:
            # Exploit: Move toward favorable prices
            best_direction = self.find_favorable_direction(
                agent, current_pos, signals
            )
            
            if best_direction:
                new_pos = self.step_toward(current_pos, best_direction)
                return [MoveEffect(agent_id, new_pos)]
        
        # Explore: Random movement
        return self.random_move(agent_id, world_view)
    
    def find_favorable_direction(self, agent, current_pos, signals):
        """
        Find direction with most favorable prices
        """
        # Agent's relative valuation
        agent_valuation = self.compute_agent_valuation(agent)
        
        best_score = -np.inf
        best_direction = None
        
        for signal in signals:
            # Is this price favorable for agent?
            score = self.evaluate_price_signal(
                agent_valuation, 
                signal['price'],
                signal['confidence']
            )
            
            if score > best_score:
                best_score = score
                best_direction = self.direction_to(
                    current_pos, 
                    signal['location']
                )
        
        return best_direction
    
    def evaluate_price_signal(self, agent_valuation, market_price, confidence):
        """
        Score price signal based on agent's preferences
        """
        # If agent values good_a more and market price is low, favorable
        price_deviation = agent_valuation - market_price
        return price_deviation * confidence
```

---

## Experimental Framework

```python
class InformationExperiments:
    """
    Test impact of information systems
    """
    
    def __init__(self):
        self.scenarios = self.create_test_scenarios()
        self.results = {}
    
    def create_test_scenarios(self):
        """
        Scenarios to test information effects
        """
        return {
            'no_information': {
                'information_system': False,
                'protocols': {
                    'search': 'random_walk',
                    'bargaining': 'split_difference'
                }
            },
            'local_information': {
                'information_system': True,
                'broadcast_radius': 5,
                'protocols': {
                    'search': 'information_guided',
                    'bargaining': 'market_informed'
                }
            },
            'global_information': {
                'information_system': True,
                'broadcast_radius': 100,  # Effectively global
                'protocols': {
                    'search': 'information_guided',
                    'bargaining': 'market_informed'
                }
            },
            'noisy_information': {
                'information_system': True,
                'noise_level': 0.3,
                'protocols': {
                    'search': 'information_guided',
                    'bargaining': 'market_informed'
                }
            }
        }
    
    def run_experiments(self):
        """
        Compare scenarios with different information regimes
        """
        for name, config in self.scenarios.items():
            print(f"Running experiment: {name}")
            
            # Run multiple seeds
            scenario_results = []
            for seed in range(30):
                result = self.run_single_experiment(config, seed)
                scenario_results.append(result)
            
            # Analyze results
            self.results[name] = self.analyze_results(scenario_results)
        
        # Generate comparison report
        return self.generate_report()
    
    def analyze_results(self, results):
        """
        Analyze information system impact
        """
        return {
            'convergence_speed': np.mean([r['convergence_tick'] for r in results]),
            'price_variance': np.mean([r['price_variance'] for r in results]),
            'efficiency': np.mean([r['efficiency'] for r in results]),
            'market_formation': np.mean([r['num_markets'] for r in results]),
            'information_quality': np.mean([r['signal_accuracy'] for r in results])
        }
    
    def generate_report(self):
        """
        Create comparison report
        """
        report = InformationSystemReport()
        
        # Compare convergence speeds
        report.add_chart(
            'convergence_comparison',
            self.plot_convergence_speeds()
        )
        
        # Compare price discovery quality
        report.add_chart(
            'price_discovery',
            self.plot_price_discovery()
        )
        
        # Spatial patterns
        report.add_visualization(
            'market_formation',
            self.visualize_market_areas()
        )
        
        return report
```

---

## Deliverables

1. **Market area detection** from trade clustering
2. **Price signal extraction** from bilateral trades
3. **Information broadcasting** with spatial decay
4. **Agent memory system** for price beliefs
5. **Information-aware protocols** for search and bargaining
6. **Experimental framework** comparing information regimes

---

## Success Metrics

- ✅ Price signals emerge naturally from trades (no external calculation)
- ✅ Faster convergence with information system enabled
- ✅ Market areas form spontaneously from trade density
- ✅ Information quality decreases with distance
- ✅ Agents successfully use price signals in decision-making
- ✅ Measurable efficiency improvement with information
