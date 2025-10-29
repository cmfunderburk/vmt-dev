# Phase 3: Market Post Implementation Guide

**Document Status:** Implementation Blueprint  
**Version:** 1.0  
**Created:** 2025-10-29  
**Purpose:** Concrete implementation guide for Market Post architecture

---

## Quick Start: What Changes?

### For Users
```yaml
# Your scenario file gets new powers:
market_posts:
  - location: [20, 20]
    mechanism: "walrasian"
    visibility_radius: 10

exchange_regime: "centralized"  # or "mixed_bilateral_centralized"
```

### For Agents
- Agents now see markets like they see resources
- Markets become movement targets
- Orders submitted when close enough
- Prices broadcast from markets

### For the System  
- New `MarketPost` entities on grid
- Extended `SearchProtocol` considers markets
- Phase 4 handles both bilateral AND market trades
- New telemetry for market events

---

## Core Implementation

### 1. Market Post Entity

```python
# src/vmt_engine/core/market.py

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from .state import Position

if TYPE_CHECKING:
    from ..protocols import MarketMechanism

@dataclass
class MarketPost:
    """
    A physical market location where price discovery occurs.
    
    Market posts are discovered by agents through search,
    approached via movement, and interacted with when close enough.
    """
    id: int
    location: Position
    
    # Visibility and interaction  
    visibility_radius: int = 10     # How far away agents can see this market
    interaction_radius: int = 3      # How close agents must be to submit orders
    broadcast_radius: int = 15       # How far price information travels
    
    # Market configuration
    mechanism_type: str = "walrasian"  # Type of price discovery
    commodities: list[str] = field(default_factory=lambda: ["A", "B", "M"])
    
    # Runtime state
    current_prices: dict[str, float] = field(default_factory=dict)
    last_clear_tick: Optional[int] = None
    pending_orders: list = field(default_factory=list)
    
    # Mechanism instance (set during initialization)
    mechanism: Optional["MarketMechanism"] = field(default=None, repr=False)
    
    def can_see(self, agent_pos: Position, grid: "Grid") -> bool:
        """Check if agent can see this market."""
        distance = grid.manhattan_distance(agent_pos, self.location)
        return distance <= self.visibility_radius
    
    def can_interact(self, agent_pos: Position, grid: "Grid") -> bool:
        """Check if agent can submit orders to this market."""
        distance = grid.manhattan_distance(agent_pos, self.location)
        return distance <= self.interaction_radius
    
    def can_receive_broadcast(self, agent_pos: Position, grid: "Grid") -> bool:
        """Check if agent receives price information from this market."""
        distance = grid.manhattan_distance(agent_pos, self.location)
        return distance <= self.broadcast_radius
```

### 2. Extended Grid with Markets

```python
# src/vmt_engine/core/grid.py (additions)

class Grid:
    """Grid with resources AND markets."""
    
    def __init__(self, width: int, height: int):
        # ... existing init ...
        self.market_posts: dict[int, MarketPost] = {}
        self.market_locations: dict[Position, int] = {}  # pos -> market_id
    
    def add_market_post(self, market: MarketPost) -> None:
        """Add a market post to the grid."""
        if market.location in self.market_locations:
            raise ValueError(f"Market already exists at {market.location}")
        
        self.market_posts[market.id] = market
        self.market_locations[market.location] = market.id
        
        # Optionally mark cell as special
        cell = self.get_cell(market.location)
        cell.has_market = True
        cell.market_id = market.id
    
    def get_visible_markets(self, pos: Position, vision_radius: int) -> list[MarketPost]:
        """Get all markets visible from a position."""
        visible = []
        for market in self.market_posts.values():
            if market.can_see(pos, self):
                visible.append(market)
        return visible
```

### 3. WorldView with Markets

```python
# src/vmt_engine/protocols/context.py (additions)

@dataclass
class MarketView:
    """What an agent knows about a market."""
    id: int
    location: Position
    distance: int
    commodities: list[str]
    
    # Price information (may be stale based on distance)
    last_known_prices: dict[str, float]
    price_tick: int  # When prices were observed
    price_confidence: float  # 0-1 based on distance/staleness

@dataclass
class WorldView:
    """Extended with market information."""
    # ... existing fields ...
    
    # Market information
    visible_markets: list[MarketView]
    nearby_markets: list[int]  # Market IDs within interaction radius
    
    # Price broadcasts received
    market_prices: dict[int, dict[str, float]]  # market_id -> commodity -> price
    
    # Agent's market state
    target_market_id: Optional[int] = None
    pending_orders: list["Order"] = field(default_factory=list)
```

### 4. Market-Aware Search Protocol

```python
# src/vmt_engine/protocols/search/market_aware.py

from typing import Optional
from ..base import SearchProtocol, SetTarget, TargetMarket
from ..context import WorldView, MarketView

class MarketAwareSearchProtocol(SearchProtocol):
    """
    Search protocol that considers both agents and markets as targets.
    
    Agents evaluate:
    1. Traditional bilateral trade opportunities with visible agents
    2. Expected value from traveling to visible markets
    3. Resources for foraging (if in forage mode)
    
    The best option (highest expected discounted value) becomes the target.
    """
    
    name = "market_aware_search"
    version = "2025.10.29"
    
    def build_preferences(self, world: WorldView) -> list[tuple]:
        """Build ranked list including markets as potential targets."""
        
        preferences = []
        beta = world.params.get("beta", 0.95)
        
        # Evaluate visible agents (traditional bilateral)
        for neighbor in world.visible_agents:
            if neighbor.id == world.agent_id:
                continue
            
            surplus = self._estimate_bilateral_surplus(world, neighbor)
            if surplus > 0:
                distance = abs(world.pos[0] - neighbor.pos[0]) + abs(world.pos[1] - neighbor.pos[1])
                discounted = surplus * (beta ** distance)
                preferences.append((
                    "agent",          # target type
                    neighbor.id,      # target id
                    surplus,          # raw value
                    discounted,       # discounted value
                    distance          # distance
                ))
        
        # NEW: Evaluate visible markets
        for market in world.visible_markets:
            expected_value = self._estimate_market_value(world, market)
            if expected_value > 0:
                discounted = expected_value * (beta ** market.distance)
                preferences.append((
                    "market",         # target type
                    market.id,        # target id
                    expected_value,   # raw value
                    discounted,       # discounted value
                    market.distance   # distance
                ))
        
        # Evaluate resources (if foraging)
        if world.mode in ["forage", "both"]:
            for resource in world.visible_resources:
                value = self._estimate_resource_value(world, resource)
                if value > 0:
                    distance = abs(world.pos[0] - resource.pos[0]) + abs(world.pos[1] - resource.pos[1])
                    discounted = value * (beta ** distance)
                    preferences.append((
                        "resource",
                        resource.pos,
                        value,
                        discounted,
                        distance
                    ))
        
        # Sort by discounted value (descending)
        preferences.sort(key=lambda x: x[3], reverse=True)
        return preferences
    
    def _estimate_market_value(self, world: WorldView, market: MarketView) -> float:
        """
        Estimate expected surplus from participating in a market.
        
        This is more complex than bilateral because we must estimate:
        1. Likely clearing price (from last known prices)
        2. Our optimal quantity at that price  
        3. Probability of order execution
        4. Competition effects
        """
        
        # Simple version: use last known prices to estimate value
        total_expected_surplus = 0.0
        
        for commodity in market.commodities:
            if commodity == "M":
                continue  # Money is numeraire
            
            last_price = market.last_known_prices.get(commodity, None)
            if last_price is None:
                continue  # No price information
            
            # Would I want to buy or sell at this price?
            my_valuation = self._compute_marginal_utility(world, commodity)
            
            if my_valuation > last_price:
                # I would buy
                quantity = self._optimal_buy_quantity(world, commodity, last_price)
                surplus_per_unit = my_valuation - last_price
                expected_surplus = quantity * surplus_per_unit
            else:
                # I would sell  
                quantity = self._optimal_sell_quantity(world, commodity, last_price)
                surplus_per_unit = last_price - my_valuation
                expected_surplus = quantity * surplus_per_unit
            
            # Discount by price confidence (stale/distant prices less reliable)
            expected_surplus *= market.price_confidence
            
            total_expected_surplus += expected_surplus
        
        return total_expected_surplus
    
    def select_target(self, world: WorldView) -> list["Effect"]:
        """Select best target and return appropriate effect."""
        
        preferences = self.build_preferences(world)
        
        if not preferences:
            # No good targets, idle
            return [SetTarget(
                agent_id=world.agent_id,
                target_type="idle",
                target_position=world.home_pos
            )]
        
        # Best target
        target_type, target_id, _, _, _ = preferences[0]
        
        if target_type == "agent":
            # Traditional bilateral target
            target_agent = world.get_agent_view(target_id)
            return [SetTarget(
                agent_id=world.agent_id,
                target_type="agent",
                target_id=target_id,
                target_position=target_agent.pos
            )]
            
        elif target_type == "market":
            # NEW: Target a market post
            market = world.get_market_view(target_id)
            return [TargetMarket(
                agent_id=world.agent_id,
                market_id=target_id,
                market_location=market.location
            )]
            
        elif target_type == "resource":
            # Foraging target
            return [SetTarget(
                agent_id=world.agent_id,
                target_type="resource",
                target_position=target_id  # resource pos
            )]
```

### 5. Market Mechanisms

```python
# src/vmt_engine/protocols/market/walrasian.py

from dataclasses import dataclass
from typing import Optional
from ..base import MarketMechanism, Order, MarketClear, Trade
from ..context import ProtocolContext

@dataclass
class WalrasianAuctioneer(MarketMechanism):
    """
    Tatonnement process for finding competitive equilibrium.
    
    Algorithm:
    1. Collect supply and demand schedules from agents
    2. Find price where supply equals demand (tatonnement)
    3. Execute trades at clearing price
    """
    
    name = "walrasian_auctioneer"
    version = "2025.10.29"
    
    # Parameters
    adjustment_speed: float = 0.1
    price_tolerance: float = 0.01
    max_iterations: int = 100
    initial_price: Optional[float] = None
    
    def collect_orders(self, agent_ids: list[int], world: ProtocolContext) -> list[Order]:
        """
        Collect orders from agents near the market.
        
        For Walrasian, we need full demand/supply schedules,
        not just single orders. In practice, we might:
        1. Query agents for quantity demanded at current price
        2. Adjust price and re-query (tatonnement)
        """
        
        orders = []
        
        for agent_id in agent_ids:
            agent = world.get_agent(agent_id)
            
            # For each commodity the market handles
            for commodity in self.commodities:
                # Agent's optimal quantity at current price
                # This is a simplification - real implementation would
                # query utility functions directly
                
                current_price = self.current_price.get(commodity, 1.0)
                
                # Buy orders
                desired_buy = self._compute_demand(agent, commodity, current_price, world)
                if desired_buy > 0:
                    orders.append(Order(
                        agent_id=agent_id,
                        commodity=commodity,
                        direction="buy",
                        quantity=desired_buy,
                        limit_price=current_price * 1.1  # Willing to pay 10% more
                    ))
                
                # Sell orders
                desired_sell = self._compute_supply(agent, commodity, current_price, world)
                if desired_sell > 0:
                    orders.append(Order(
                        agent_id=agent_id,
                        commodity=commodity,
                        direction="sell", 
                        quantity=desired_sell,
                        limit_price=current_price * 0.9  # Willing to accept 10% less
                    ))
        
        return orders
    
    def clear_market(self, orders: list[Order], world: ProtocolContext) -> dict[str, float]:
        """
        Find market-clearing prices via tatonnement.
        
        For each commodity:
        1. Start with initial price guess
        2. Calculate excess demand
        3. Adjust price up if excess demand > 0, down if < 0
        4. Repeat until convergence
        """
        
        clearing_prices = {}
        
        for commodity in self.commodities:
            if commodity == "M":
                clearing_prices["M"] = 1.0  # Money is numeraire
                continue
            
            # Filter orders for this commodity
            commodity_orders = [o for o in orders if o.commodity == commodity]
            if not commodity_orders:
                continue
            
            # Tatonnement process
            price = self.initial_price or 1.0
            
            for iteration in range(self.max_iterations):
                # Calculate demand and supply at current price
                demand = sum(o.quantity for o in commodity_orders 
                           if o.direction == "buy" and o.limit_price >= price)
                supply = sum(o.quantity for o in commodity_orders
                           if o.direction == "sell" and o.limit_price <= price)
                
                excess_demand = demand - supply
                
                # Check convergence
                if abs(excess_demand) < self.price_tolerance:
                    clearing_prices[commodity] = price
                    break
                
                # Adjust price
                price_adjustment = self.adjustment_speed * excess_demand
                price = max(0.01, price + price_adjustment)  # Keep price positive
            
            else:
                # Failed to converge
                self._log_convergence_failure(commodity, price, excess_demand)
                clearing_prices[commodity] = price  # Use last price anyway
        
        return clearing_prices
    
    def execute_trades(
        self, 
        orders: list[Order], 
        prices: dict[str, float], 
        world: ProtocolContext
    ) -> list["Effect"]:
        """
        Execute trades at clearing prices.
        
        Match buyers and sellers for each commodity.
        All trades occur at the clearing price.
        """
        
        effects = []
        
        for commodity, clearing_price in prices.items():
            if commodity == "M":
                continue
            
            # Get executable orders at clearing price
            buyers = [o for o in orders 
                     if o.commodity == commodity 
                     and o.direction == "buy"
                     and o.limit_price >= clearing_price]
            
            sellers = [o for o in orders
                      if o.commodity == commodity
                      and o.direction == "sell"  
                      and o.limit_price <= clearing_price]
            
            # Sort for deterministic matching
            buyers.sort(key=lambda o: (-o.limit_price, o.agent_id))  # Highest bid first
            sellers.sort(key=lambda o: (o.limit_price, o.agent_id))   # Lowest ask first
            
            # Match buyers and sellers
            for buyer, seller in zip(buyers, sellers):
                quantity = min(buyer.quantity, seller.quantity)
                
                if quantity > 0:
                    # Create trade effect
                    effects.append(Trade(
                        buyer_id=buyer.agent_id,
                        seller_id=seller.agent_id,
                        commodity=commodity,
                        quantity=quantity,
                        price=clearing_price,
                        market_id=self.market_id
                    ))
                    
                    # Update remaining quantities
                    buyer.quantity -= quantity
                    seller.quantity -= quantity
        
        # Record market clearing event
        effects.append(MarketClear(
            market_id=self.market_id,
            tick=world.tick,
            commodities=list(prices.keys()),
            prices=prices,
            total_volume=len(effects)
        ))
        
        return effects
```

### 6. Modified Trade Phase

```python
# src/vmt_engine/systems/trading.py (modifications)

class TradeSystem:
    """
    Phase 4: Handle both bilateral and market-based trades.
    
    Agents are partitioned into:
    1. Market participants (near markets)
    2. Bilateral traders (paired agents)
    3. Idle (neither)
    """
    
    def __init__(self):
        self.bargaining_protocol: Optional[BargainingProtocol] = None
        self.market_posts: dict[int, MarketPost] = {}
    
    def execute(self, sim: "Simulation") -> None:
        """Execute trade phase with both mechanisms."""
        
        # Partition agents by trade type
        market_agents = defaultdict(list)  # market_id -> [agent_ids]
        bilateral_pairs = []
        
        for agent in sim.agents:
            # Check if targeting a market
            if hasattr(agent, 'target_market_id') and agent.target_market_id is not None:
                market = sim.grid.market_posts.get(agent.target_market_id)
                if market and market.can_interact(agent.pos, sim.grid):
                    market_agents[market.id].append(agent.id)
                    continue
            
            # Check if paired for bilateral trade
            if agent.paired_with_id is not None:
                if agent.id < agent.paired_with_id:  # Avoid double-processing
                    partner = sim.agent_by_id[agent.paired_with_id]
                    distance = sim.grid.manhattan_distance(agent.pos, partner.pos)
                    if distance <= sim.params["interaction_radius"]:
                        bilateral_pairs.append((agent, partner))
        
        # Process market trades
        self._process_market_trades(market_agents, sim)
        
        # Process bilateral trades
        self._process_bilateral_trades(bilateral_pairs, sim)
    
    def _process_market_trades(
        self, 
        market_agents: dict[int, list[int]], 
        sim: "Simulation"
    ) -> None:
        """Process trades at each market."""
        
        for market_id, agent_ids in market_agents.items():
            if not agent_ids:
                continue
                
            market = self.market_posts[market_id]
            
            # Build world view for market
            world = build_protocol_context_for_market(sim, market_id)
            
            # Collect orders
            orders = market.mechanism.collect_orders(agent_ids, world)
            
            # Clear market
            if orders:
                prices = market.mechanism.clear_market(orders, world)
                market.current_prices = prices  # Update for broadcasts
                
                # Execute trades
                effects = market.mechanism.execute_trades(orders, prices, world)
                
                # Apply effects
                for effect in effects:
                    self._apply_effect(effect, sim)
                
                # Log to telemetry
                self._log_market_event(market_id, prices, effects, sim)
```

### 7. Telemetry Extensions

```python
# src/vmt_engine/protocols/telemetry_schema.py (additions)

MARKET_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS market_posts (
        run_id INTEGER,
        market_id INTEGER,
        location_x INTEGER,
        location_y INTEGER,
        visibility_radius INTEGER,
        interaction_radius INTEGER,
        mechanism_type TEXT,
        commodities TEXT
    );
    """,
    
    """
    CREATE TABLE IF NOT EXISTS market_orders (
        run_id INTEGER,
        tick INTEGER,
        market_id INTEGER,
        agent_id INTEGER,
        commodity TEXT,
        direction TEXT,
        quantity INTEGER,
        limit_price REAL,
        status TEXT
    );
    """,
    
    """
    CREATE TABLE IF NOT EXISTS market_clears (
        run_id INTEGER,
        tick INTEGER,
        market_id INTEGER,
        commodity TEXT,
        clearing_price REAL,
        total_demand INTEGER,
        total_supply INTEGER,
        quantity_traded INTEGER,
        convergence_iterations INTEGER
    );
    """,
    
    """
    CREATE TABLE IF NOT EXISTS market_prices (
        run_id INTEGER,
        tick INTEGER,
        market_id INTEGER,
        commodity TEXT,
        price REAL,
        bid_ask_spread REAL
    );
    """
]
```

---

## Scenario Example

```yaml
# scenarios/walrasian_two_markets.yaml
name: "Two Competing Markets"
description: "Agents choose between two market posts with different mechanisms"

grid:
  width: 50
  height: 50
  
market_posts:
  - id: 0
    location: [15, 25]
    visibility_radius: 12
    interaction_radius: 3
    mechanism_type: "walrasian"
    commodities: ["A", "B", "M"]
    mechanism_params:
      adjustment_speed: 0.1
      price_tolerance: 0.01
      
  - id: 1  
    location: [35, 25]
    visibility_radius: 10
    interaction_radius: 2
    mechanism_type: "posted_price"
    commodities: ["A", "M"]  # Doesn't trade B
    mechanism_params:
      price_update_frequency: 5  # Every 5 ticks

params:
  exchange_regime: "mixed_bilateral_centralized"
  centralized_weight: 0.7  # 70% prefer markets when available
  bilateral_weight: 0.3    # 30% still use bilateral
  
  vision_radius: 8
  interaction_radius: 1
  move_budget_per_tick: 2
  
protocols:
  search:
    name: "market_aware_search"
    version: "2025.10.29"
    
  matching:
    name: "legacy"  # Still works for bilateral subset
    version: "2025.10.26"
    
  bargaining:
    name: "legacy"  # For bilateral trades
    version: "2025.10.26"
    
agents:
  count: 40
  initial_positions:
    distribution: "uniform"
  
  inventories:
    A: [10, 20]  # Random range
    B: [10, 20]
    M: [100, 200]
    
  utilities:
    - type: "linear"
      weights: [0.7, 0.3]
      count: 20
    
    - type: "cobb_douglas"  
      exponents: [0.6, 0.4]
      count: 20

resources:
  # Some resources too, for mixed economy
  spawn_rate: 0.1
  types:
    - good: "A"
      quantity: [1, 3]
    - good: "B"
      quantity: [1, 3]
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_market_posts.py

def test_market_visibility():
    """Markets visible at correct distances."""
    market = MarketPost(
        id=0,
        location=(10, 10),
        visibility_radius=5
    )
    
    grid = Grid(20, 20)
    
    # Within visibility
    assert market.can_see((12, 12), grid) == True  # distance = 4
    assert market.can_see((15, 10), grid) == True  # distance = 5
    
    # Outside visibility  
    assert market.can_see((16, 10), grid) == False  # distance = 6

def test_market_interaction():
    """Agents can interact when close enough."""
    market = MarketPost(
        id=0,
        location=(10, 10),
        interaction_radius=2
    )
    
    grid = Grid(20, 20)
    
    # Can interact
    assert market.can_interact((10, 11), grid) == True  # distance = 1
    assert market.can_interact((11, 11), grid) == True  # distance = 2
    
    # Cannot interact
    assert market.can_interact((11, 12), grid) == False  # distance = 3
```

### Integration Tests

```python
# tests/test_centralized_integration.py

def test_walrasian_convergence():
    """Walrasian market finds equilibrium."""
    
    # Create scenario with single market
    scenario = load_scenario("test_walrasian_single_market.yaml")
    sim = Simulation(scenario, seed=42)
    
    # Run for enough ticks to discover market
    sim.run(20)
    
    # Check market discovered
    market = sim.grid.market_posts[0]
    assert market.last_clear_tick is not None
    
    # Check prices converged
    assert "A" in market.current_prices
    assert market.current_prices["A"] > 0
    
    # Check trades occurred
    trades = sim.telemetry.query(
        "SELECT COUNT(*) FROM trades WHERE market_id = 0"
    )
    assert trades[0][0] > 0

def test_market_vs_bilateral_choice():
    """Agents choose between market and bilateral."""
    
    scenario = load_scenario("test_mixed_mechanisms.yaml")
    sim = Simulation(scenario, seed=42)
    
    sim.run(30)
    
    # Some agents should use markets
    market_trades = sim.telemetry.query(
        "SELECT COUNT(*) FROM trades WHERE market_id IS NOT NULL"
    )
    
    # Some agents should trade bilaterally
    bilateral_trades = sim.telemetry.query(
        "SELECT COUNT(*) FROM trades WHERE market_id IS NULL"
    )
    
    assert market_trades[0][0] > 0
    assert bilateral_trades[0][0] > 0
```

### Property Tests

```python
# tests/test_market_properties.py

from hypothesis import given, strategies as st

@given(
    demand=st.lists(st.integers(1, 100), min_size=5, max_size=20),
    supply=st.lists(st.integers(1, 100), min_size=5, max_size=20),
    initial_price=st.floats(0.1, 10.0)
)
def test_tatonnement_convergence(demand, supply, initial_price):
    """Tatonnement always converges or reports failure."""
    
    market = WalrasianAuctioneer(
        adjustment_speed=0.1,
        max_iterations=1000
    )
    
    # Create orders from demand/supply
    orders = create_orders_from_schedules(demand, supply, initial_price)
    
    # Should either converge or hit max iterations
    prices = market.clear_market(orders, mock_world())
    
    # Price should be positive
    for commodity, price in prices.items():
        assert price > 0
        
def test_market_welfare_dominance():
    """Centralized markets achieve higher total welfare than random matching."""
    
    # Run same scenario with different mechanisms
    walrasian_welfare = run_scenario_with_mechanism("walrasian")
    random_welfare = run_scenario_with_mechanism("random_bilateral")
    
    # Walrasian should achieve higher total utility
    assert walrasian_welfare > random_welfare
```

---

## Migration Path

### Phase 3a: Basic Infrastructure (Week 1)
1. Implement `MarketPost` class
2. Add markets to `Grid`  
3. Update `WorldView` with market info
4. Create `MarketAwareSearchProtocol`

### Phase 3b: Walrasian Mechanism (Week 2)
1. Implement `WalrasianAuctioneer`
2. Create order collection logic
3. Implement tatonnement
4. Add trade execution

### Phase 3c: Integration (Week 3)
1. Modify `TradeSystem` for dual mechanisms
2. Add market telemetry
3. Update visualization
4. Test mixed scenarios

### Phase 3d: Additional Mechanisms (Week 4)
1. Implement `PostedPriceMarket`
2. Implement `ContinuousDoubleAuction`
3. Comparative testing
4. Performance optimization

---

## Performance Considerations

### Optimization Opportunities

1. **Spatial Indexing for Markets**
```python
class MarketSpatialIndex:
    """Efficient market queries."""
    
    def __init__(self, markets: list[MarketPost]):
        # Build R-tree or similar
        self.index = self._build_index(markets)
    
    def query_visible(self, pos: Position) -> list[int]:
        """Fast lookup of visible markets."""
        # Use spatial index instead of checking all markets
        return self.index.query_radius(pos, max_visibility_radius)
```

2. **Order Book Caching**
```python
class OrderBook:
    """Efficient order management."""
    
    def __init__(self):
        self.buy_orders = SortedList(key=lambda o: -o.limit_price)
        self.sell_orders = SortedList(key=lambda o: o.limit_price)
    
    def add_order(self, order: Order):
        # O(log n) insertion
        if order.direction == "buy":
            self.buy_orders.add(order)
        else:
            self.sell_orders.add(order)
```

3. **Parallel Market Clearing**
```python
def clear_all_markets_parallel(markets: list[MarketPost], sim: Simulation):
    """Clear multiple markets in parallel."""
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for market in markets:
            future = executor.submit(
                clear_single_market, 
                market, 
                sim
            )
            futures.append((market.id, future))
        
        results = {}
        for market_id, future in futures:
            results[market_id] = future.result()
        
        return results
```

---

## Open Questions for Review

1. **Price Information Decay**
   - Should prices decay linearly with distance?
   - Should old prices expire after N ticks?
   - How to handle uncertainty?

2. **Market Competition**
   - Can markets set fees?
   - Should markets compete on mechanism efficiency?
   - How to model market reputation?

3. **Order Complexity**
   - Start with simple limit orders?
   - Add market orders later?
   - Support for conditional orders?

4. **Failure Modes**
   - What if no equilibrium exists?
   - How to handle market manipulation?
   - Fallback to bilateral when markets fail?

---

## Document Status

**Status:** Implementation Blueprint Complete  
**Next Action:** Review and approve Market Post architecture  
**Dependencies:** Core architecture approval from design doc  
**Estimated Effort:** 25-30 hours for full implementation

**Last Updated:** 2025-10-29  
**Maintained By:** Lead Developer + AI Agent
