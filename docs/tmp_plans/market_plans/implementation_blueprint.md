# Market Post Implementation Blueprint
**VMT Phase 3: Centralized Markets**  
**Created:** October 29, 2025  
**Status:** Planning - Ready for Implementation

---

## Executive Summary

This blueprint defines the implementation of centralized market mechanisms for VMT using the **Market Post** architecture. Market Posts are physical entities at fixed grid locations that agents must discover and approach. This preserves spatial grounding while enabling efficient price discovery through Walrasian auction, posted prices, or continuous double auction mechanisms.

### Core Design Decisions (Locked)

1. **Architecture:** Unified Trade Phase (modify existing Phase 4, not separate phase)
2. **Market Valuation:** Last observed prices → simple heuristic fallback
3. **Target Priority:** Markets always preferred over bilateral when visible
4. **Convergence Failure:** No clearing + console warning
5. **Arbitrage:** Emergent from search behavior (not explicit strategy)

### Timeline

4 weeks, ~30 hours total implementation time

---

## Architectural Design

### Market Post Concept

A `MarketPost` is a spatial entity with:
- **Fixed location** on grid (x, y coordinates)
- **Visibility radius** - agents can perceive market within this distance
- **Interaction radius** - agents can submit orders within this distance
- **Broadcast radius** - price information propagates within this distance
- **Mechanism type** - clearing algorithm (Walrasian, posted price, CDA)
- **Commodity set** - which goods are traded at this market

Agents discover markets through perception, move toward them using existing movement protocols, and submit orders when within interaction radius. Markets clear periodically using their mechanism, generating Trade effects.

### Integration with 7-Phase Tick Cycle

**No new phase added.** Instead, Phase 4 (Trade) is modified:

1. **Phase 1 (Perception):** Agents perceive visible MarketPosts (extended)
2. **Phase 2 (Decision):** MarketAwareSearchProtocol evaluates markets alongside bilateral partners (extended)
3. **Phase 3 (Movement):** Agents move toward chosen target (market or agent) (unchanged)
4. **Phase 4 (Trade - MODIFIED):**
   - Partition agents by target type (market vs bilateral)
   - Process market trades FIRST (more efficient)
   - Process bilateral trades for remaining agents
   - Apply all Trade effects
5. **Phase 5 (Foraging):** Unchanged
6. **Phase 6 (Resources):** Unchanged
7. **Phase 7 (Housekeeping):** Unchanged

### Key Advantages

- **Spatially Grounded:** Discovery has realistic costs
- **Regional Markets:** Multiple posts create organic local markets
- **Mixed Modes:** Supports both local and global exchange
- **Efficiency Gains:** Centralization without "telepathic" trading
- **Deterministic:** No randomness beyond seeded RNG
- **Clean Integration:** Works within existing protocol architecture

---

## Implementation Plan: 4 Weeks

### Week 1: Core Infrastructure (6-8 hours)

**Goal:** Agents can perceive and target market posts

#### Files to Create

1. **`src/vmt_engine/core/market.py`** - Core MarketPost entity

```python
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .grid import Grid

Position = tuple[int, int]

@dataclass
class MarketPost:
    """
    A physical market location on the grid.
    Agents must approach to interact.
    """
    id: int
    location: Position
    visibility_radius: int = 10
    interaction_radius: int = 3
    broadcast_radius: int = 15
    mechanism_type: str = "walrasian"
    commodities: list[str] = field(default_factory=lambda: ["A", "B", "M"])
    
    # Runtime state
    current_prices: dict[str, float] = field(default_factory=dict)
    pending_orders: list = field(default_factory=list)
    last_clear_tick: int = -1
    mechanism: Optional['MarketMechanism'] = None
    
    def can_see(self, agent_pos: Position, grid: 'Grid') -> bool:
        """Can agent at agent_pos perceive this market?"""
        return grid.manhattan_distance(agent_pos, self.location) <= self.visibility_radius
    
    def can_interact(self, agent_pos: Position, grid: 'Grid') -> bool:
        """Can agent at agent_pos submit orders?"""
        return grid.manhattan_distance(agent_pos, self.location) <= self.interaction_radius
    
    def can_receive_broadcast(self, agent_pos: Position, grid: 'Grid') -> bool:
        """Can agent at agent_pos receive price broadcasts?"""
        return grid.manhattan_distance(agent_pos, self.location) <= self.broadcast_radius


@dataclass
class MarketView:
    """
    Agent's perception of a market.
    May contain stale information.
    """
    id: int
    location: Position
    distance: int
    prices: dict[str, float]  # may be stale
    price_age: int  # ticks since last observation
    commodities: list[str]
    can_interact: bool  # within interaction_radius now
```

2. **`src/vmt_engine/protocols/market/__init__.py`** - Package initialization
3. **`src/vmt_engine/protocols/market/base.py`** - Abstract base class

```python
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...simulation import Simulation
    from ..base import Effect

class MarketMechanism(ABC):
    """
    Abstract base for market clearing mechanisms.
    Each MarketPost has one mechanism instance.
    """
    
    def __init__(self, market_post: 'MarketPost'):
        self.market_post = market_post
    
    @abstractmethod
    def execute(self, agent_ids: list[int], sim: 'Simulation') -> list['Effect']:
        """
        Main entry point called during Trade Phase.
        
        Args:
            agent_ids: Agents within interaction_radius of this market
            sim: Current simulation state
            
        Returns:
            List of Effects (primarily Trade effects, plus MarketClear for logging)
        """
        pass
```

#### Files to Modify

1. **`src/vmt_engine/core/grid.py`** - Add market storage

```python
@dataclass
class Grid:
    # ... existing fields ...
    
    market_posts: dict[int, MarketPost] = field(default_factory=dict)
    market_locations: dict[Position, int] = field(default_factory=dict)  # pos -> market_id
    
    def add_market_post(self, market: MarketPost) -> None:
        """Register a market post on the grid"""
        self.market_posts[market.id] = market
        self.market_locations[market.location] = market.id
    
    def get_visible_markets(self, position: Position, vision_radius: int) -> list[MarketPost]:
        """Get all markets visible from position"""
        visible = []
        for market in self.market_posts.values():
            if market.can_see(position, self):
                visible.append(market)
        return visible
```

2. **`src/vmt_engine/protocols/context.py`** - Extend WorldView

```python
@dataclass
class WorldView:
    # ... existing fields ...
    
    visible_markets: list[MarketView] = field(default_factory=list)
    market_prices: dict[tuple[int, str], float] = field(default_factory=dict)  # (market_id, commodity) -> price
```

3. **`src/vmt_engine/systems/perception.py`** - Detect markets

```python
def build_perception(self, agent: Agent, sim: Simulation) -> None:
    """Extend to include market perception"""
    # ... existing perception logic ...
    
    # Perceive markets
    visible_markets = sim.grid.get_visible_markets(agent.position, agent.vision_radius)
    agent.perception_cache['visible_markets'] = [
        MarketView(
            id=market.id,
            location=market.location,
            distance=sim.grid.manhattan_distance(agent.position, market.location),
            prices=market.current_prices.copy(),
            price_age=sim.tick - market.last_clear_tick if market.last_clear_tick >= 0 else 999,
            commodities=market.commodities,
            can_interact=market.can_interact(agent.position, sim.grid)
        )
        for market in visible_markets
    ]
```

#### Milestone Tests

```python
# tests/test_market_post_infrastructure.py

def test_market_post_radii():
    """Test visibility/interaction radius logic"""
    grid = Grid(width=30, height=30)
    market = MarketPost(id=0, location=(15, 15), visibility_radius=10, interaction_radius=3)
    
    assert market.can_see((20, 20), grid)  # distance = 10
    assert not market.can_see((26, 26), grid)  # distance = 22
    assert market.can_interact((16, 16), grid)  # distance = 2
    assert not market.can_interact((20, 20), grid)  # distance = 10


def test_agent_perceives_market():
    """Agent can see market in worldview"""
    # Setup: Agent at (10, 10), market at (15, 15), visibility=10
    # Assert: market in agent's perception_cache['visible_markets']
    pass
```

---

### Week 2: Basic Mechanism + Integration (8-10 hours)

**Goal:** Single Walrasian market can clear trades

#### Files to Create

1. **`src/vmt_engine/protocols/market/walrasian.py`** - Walrasian auctioneer

```python
from ..base import Effect, Trade
from .base import MarketMechanism
from ...core.market import MarketPost
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...simulation import Simulation

@register_protocol("market", "walrasian")
class WalrasianAuctioneer(MarketMechanism):
    """
    Tatonnement price adjustment mechanism.
    Iteratively adjusts prices until supply = demand.
    """
    
    def __init__(self, market_post: MarketPost, 
                 adjustment_speed: float = 0.1,
                 tolerance: float = 0.01,
                 max_iterations: int = 100):
        super().__init__(market_post)
        self.adjustment_speed = adjustment_speed
        self.tolerance = tolerance
        self.max_iterations = max_iterations
    
    def execute(self, agent_ids: list[int], sim: 'Simulation') -> list[Effect]:
        """Main entry point called by TradeSystem"""
        effects = []
        
        # Sort for determinism
        agent_ids = sorted(agent_ids)
        
        # Process each commodity separately
        for commodity in self.market_post.commodities:
            # Find clearing price via tatonnement
            clearing_price, converged = self._find_clearing_price(
                agent_ids, commodity, sim
            )
            
            if not converged:
                print(f"WARNING: Market {self.market_post.id} tatonnement failed "
                      f"to converge for {commodity} at tick {sim.tick}")
                continue  # No trades this tick for this commodity
            
            # Execute trades at clearing price
            trade_effects = self._execute_at_price(
                agent_ids, commodity, clearing_price, sim
            )
            effects.extend(trade_effects)
            
            # Update market state
            self.market_post.current_prices[commodity] = clearing_price
            self.market_post.last_clear_tick = sim.tick
            
            # Log clearing event
            effects.append(MarketClear(
                market_id=self.market_post.id,
                commodity=commodity,
                price=clearing_price,
                quantity=sum(e.quantity for e in trade_effects if isinstance(e, Trade)),
                tick=sim.tick,
                num_participants=len(agent_ids)
            ))
        
        return effects
    
    def _find_clearing_price(self, agent_ids: list[int], commodity: str, 
                            sim: 'Simulation') -> tuple[float, bool]:
        """
        Iterative tatonnement to find market clearing price.
        Returns (price, converged_flag)
        """
        # Start from last clearing price if available
        price = self.market_post.current_prices.get(commodity, 1.0)
        
        for iteration in range(self.max_iterations):
            demand = self._compute_demand(agent_ids, commodity, price, sim)
            supply = self._compute_supply(agent_ids, commodity, price, sim)
            excess_demand = demand - supply
            
            # Check convergence
            if abs(excess_demand) < self.tolerance:
                return round(price, 2), True
            
            # Adjust price proportional to excess demand
            price += self.adjustment_speed * excess_demand
            price = max(0.01, price)  # Enforce price floor
        
        # Did not converge
        return round(price, 2), False
    
    def _compute_demand(self, agent_ids: list[int], commodity: str, 
                       price: float, sim: 'Simulation') -> float:
        """Calculate total quantity demanded at this price"""
        total_demand = 0.0
        for agent_id in agent_ids:
            agent = sim.agents[agent_id]
            # Query agent's utility function for optimal quantity at this price
            # This requires agent to compute marginal utility / price
            desired_qty = agent.compute_desired_quantity(commodity, price, sim)
            total_demand += max(0, desired_qty)
        return total_demand
    
    def _compute_supply(self, agent_ids: list[int], commodity: str,
                       price: float, sim: 'Simulation') -> float:
        """Calculate total quantity supplied at this price"""
        total_supply = 0.0
        for agent_id in agent_ids:
            agent = sim.agents[agent_id]
            # Agent supplies if marginal utility < price
            offered_qty = agent.compute_offered_quantity(commodity, price, sim)
            total_supply += max(0, offered_qty)
        return total_supply
    
    def _execute_at_price(self, agent_ids: list[int], commodity: str,
                         price: float, sim: 'Simulation') -> list[Trade]:
        """
        Execute trades at clearing price.
        Match buyers and sellers deterministically.
        """
        # Collect buyers and sellers
        buyers = []
        sellers = []
        
        for agent_id in agent_ids:
            agent = sim.agents[agent_id]
            qty = agent.compute_desired_quantity(commodity, price, sim)
            if qty > 0:
                buyers.append((agent_id, qty))
            elif qty < 0:
                sellers.append((agent_id, -qty))
        
        # Sort for determinism
        buyers.sort(key=lambda x: (x[0]))
        sellers.sort(key=lambda x: (x[0]))
        
        # Match and create Trade effects
        trades = []
        i, j = 0, 0
        while i < len(buyers) and j < len(sellers):
            buyer_id, buy_qty = buyers[i]
            seller_id, sell_qty = sellers[j]
            
            qty = min(buy_qty, sell_qty)
            
            trades.append(Trade(
                buyer_id=buyer_id,
                seller_id=seller_id,
                commodity=commodity,
                quantity=round(qty, 2),
                price=price
            ))
            
            buyers[i] = (buyer_id, buy_qty - qty)
            sellers[j] = (seller_id, sell_qty - qty)
            
            if buyers[i][1] <= 0.01:
                i += 1
            if sellers[j][1] <= 0.01:
                j += 1
        
        return trades
```

2. **`src/vmt_engine/protocols/search/market_aware.py`** - Extended search

```python
from ..base import SearchProtocol, Effect, TargetMarket
from ..context import WorldView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...simulation import Simulation

@register_protocol("search", "market_aware_search")
class MarketAwareSearchProtocol(SearchProtocol):
    """
    Extension of SearchProtocol that evaluates markets as potential targets.
    Decision rule (for initial implementation): Always prefer markets over bilateral.
    """
    
    def build_preferences(self, world: WorldView) -> list[tuple]:
        """
        Build preference ordering over all targets: agents, resources, markets.
        
        Returns:
            List of (target_type, target_id, value, discounted_value, distance) tuples
        """
        prefs = []
        
        # Evaluate markets FIRST (they have priority)
        for market in world.visible_markets:
            value = self._estimate_market_value(market, world)
            dist = market.distance
            discounted = value * (world.beta ** dist)
            prefs.append(("market", market.id, value, discounted, dist))
        
        # Then evaluate bilateral partners (existing logic)
        for agent in world.visible_agents:
            value = self._estimate_bilateral_value(agent, world)
            dist = world.grid.manhattan_distance(world.position, agent.position)
            discounted = value * (world.beta ** dist)
            prefs.append(("agent", agent.id, value, discounted, dist))
        
        # Then evaluate resources (existing logic)
        for resource in world.visible_resources:
            value = self._estimate_resource_value(resource, world)
            dist = world.grid.manhattan_distance(world.position, resource.position)
            discounted = value * (world.beta ** dist)
            prefs.append(("resource", resource.id, value, discounted, dist))
        
        # Sort by discounted value (highest first)
        prefs.sort(key=lambda x: x[3], reverse=True)
        return prefs
    
    def _estimate_market_value(self, market: MarketView, world: WorldView) -> float:
        """
        Estimate expected surplus from trading at this market.
        
        Initial implementation:
        - If market has recent prices: calculate surplus at those prices
        - Otherwise: return optimistic heuristic value
        """
        # If we have recent price information, use it
        if market.prices and market.price_age < 10:  # prices less than 10 ticks old
            return self._surplus_at_market_prices(market, world)
        else:
            # Heuristic: markets are "promising" but unknown
            # This ensures agents explore markets even without price info
            return 100.0  # Arbitrary large positive value
    
    def _surplus_at_market_prices(self, market: MarketView, world: WorldView) -> float:
        """
        Calculate expected surplus if trading at market's posted prices.
        """
        total_surplus = 0.0
        
        for commodity, price in market.prices.items():
            if commodity not in market.commodities:
                continue
            
            # Calculate marginal utility vs. price
            marginal_utility = world.agent.compute_marginal_utility(commodity)
            current_qty = world.agent.inventory.get(commodity, 0)
            
            # If MU > price, we want to buy (positive surplus)
            # If MU < price, we want to sell (positive surplus)
            surplus = abs(marginal_utility - price) * min(current_qty, 1.0)
            total_surplus += surplus
        
        return total_surplus
    
    def generate_effects(self, world: WorldView, prefs: list[tuple]) -> list[Effect]:
        """
        Generate movement/targeting effects based on preferences.
        """
        if not prefs:
            return []
        
        target_type, target_id, value, _, distance = prefs[0]
        
        if target_type == "market":
            market = next(m for m in world.visible_markets if m.id == target_id)
            return [TargetMarket(
                agent_id=world.agent.id,
                market_id=target_id,
                market_location=market.location
            )]
        elif target_type == "agent":
            # Existing bilateral targeting logic
            return self._target_agent(target_id, world)
        else:
            # Resource targeting
            return self._target_resource(target_id, world)
```

#### Files to Modify

1. **`src/vmt_engine/protocols/base.py`** - New effect types

```python
@dataclass
class TargetMarket(Effect):
    """Agent chooses to move toward and interact with a market"""
    agent_id: int
    market_id: int
    market_location: Position


@dataclass
class MarketClear(Effect):
    """
    Logging effect for market clearing event.
    Does not modify state, only recorded in telemetry.
    """
    market_id: int
    commodity: str
    price: float
    quantity: float
    tick: int
    num_participants: int
```

2. **`src/vmt_engine/systems/decision.py`** - Use MarketAwareSearchProtocol

```python
def execute(self, sim: Simulation) -> list[Effect]:
    """Phase 2: Decision making"""
    effects = []
    
    for agent in sim.agents:
        world = build_world_view_for_agent(agent, sim)
        
        # Use market-aware search if markets exist
        if sim.grid.market_posts:
            search_protocol = MarketAwareSearchProtocol(sim.params)
        else:
            search_protocol = StandardSearchProtocol(sim.params)
        
        agent_effects = search_protocol.execute(world, sim)
        effects.extend(agent_effects)
    
    return effects
```

3. **`src/vmt_engine/systems/trading.py`** - UNIFIED TRADE PHASE

```python
def execute_trade_phase(self, sim: Simulation) -> list[Effect]:
    """
    Phase 4: Unified trade processing
    
    Process order:
    1. Partition agents by target type
    2. Markets clear FIRST (more efficient)
    3. Bilateral trades for remaining agents
    4. Apply all effects
    """
    effects = []
    
    # ===== PARTITION AGENTS =====
    market_agents = defaultdict(list)  # market_id -> [agent_ids]
    bilateral_pairs = []
    unmatched_agents = set(a.id for a in sim.agents)
    
    for agent in sim.agents:
        # Check if agent is targeting a market and within interaction radius
        if hasattr(agent, 'target_market_id') and agent.target_market_id is not None:
            market = sim.grid.market_posts.get(agent.target_market_id)
            if market and market.can_interact(agent.position, sim.grid):
                market_agents[agent.target_market_id].append(agent.id)
                unmatched_agents.discard(agent.id)
        
        # Check if agent is paired bilaterally
        elif hasattr(agent, 'paired_with') and agent.paired_with is not None:
            if agent.paired_with in unmatched_agents:
                # Ensure we don't double-count pairs
                bilateral_pairs.append((min(agent.id, agent.paired_with),
                                       max(agent.id, agent.paired_with)))
                unmatched_agents.discard(agent.id)
                unmatched_agents.discard(agent.paired_with)
    
    # Remove duplicate pairs
    bilateral_pairs = list(set(bilateral_pairs))
    
    # ===== PROCESS MARKETS =====
    for market_id in sorted(market_agents.keys()):
        agent_ids = market_agents[market_id]
        if not agent_ids:
            continue
        
        market = sim.grid.market_posts[market_id]
        if market.mechanism is None:
            print(f"WARNING: Market {market_id} has no mechanism attached")
            continue
        
        # Market mechanism generates Trade effects
        market_effects = market.mechanism.execute(agent_ids, sim)
        effects.extend(market_effects)
    
    # ===== PROCESS BILATERAL TRADES =====
    for agent_id, partner_id in sorted(bilateral_pairs):
        bilateral_effects = self._process_bilateral_trade(
            agent_id, partner_id, sim
        )
        effects.extend(bilateral_effects)
    
    return effects


def _process_bilateral_trade(self, agent_id: int, partner_id: int, 
                             sim: Simulation) -> list[Effect]:
    """Existing bilateral trade logic (unchanged)"""
    # ... existing implementation ...
    pass
```

#### Milestone Tests

```python
# tests/test_walrasian_mechanism.py

def test_walrasian_market_clears():
    """Basic market clearing with 2 agents"""
    # Setup: 2 agents with complementary endowments
    # Agent 0: has A, wants B
    # Agent 1: has B, wants A
    # Market at (15, 15), both agents within interaction radius
    
    # Run 1 tick
    # Assert: Trade occurred
    # Assert: market.current_prices['A'] > 0
    # Assert: Both agents improved utility


def test_tatonnement_convergence():
    """Tatonnement finds equilibrium"""
    # Setup: 5 agents with various endowments
    # Assert: After clearing, excess demand < tolerance


def test_tatonnement_non_convergence():
    """Graceful failure when no equilibrium exists"""
    # Setup: Pathological case (no overlap in valuations)
    # Assert: Warning printed
    # Assert: No trades executed
    # Assert: Agents can still trade bilaterally if paired


def test_market_preference_over_bilateral():
    """Agents prefer markets when visible"""
    # Setup: Agent can see both market and bilateral partner
    # Assert: Agent generates TargetMarket effect, not SetTarget


def test_unified_trade_phase():
    """Markets and bilateral trades coexist"""
    # Setup: 4 agents, 1 market
    # 2 agents target market, 2 agents pair bilaterally
    # Assert: Both market trades and bilateral trades occur
    # Assert: Telemetry records both types
```

---

### Week 3: Telemetry + Scenario Config (8 hours)

**Goal:** Markets fully integrated, logged, configurable via YAML

#### Files to Create

1. **`scenarios/demos/simple_walrasian_market.yaml`** - Basic market scenario

```yaml
name: "Simple Walrasian Market Demo"
description: "Single market with 10 agents demonstrating price convergence"

grid:
  width: 30
  height: 30

market_posts:
  - id: 0
    location: [15, 15]
    visibility_radius: 12
    interaction_radius: 3
    broadcast_radius: 15
    mechanism_type: "walrasian"
    mechanism_params:
      adjustment_speed: 0.1
      tolerance: 0.01
      max_iterations: 100
    commodities: ["A", "B", "M"]

params:
  ticks: 100
  exchange_regime: "centralized"
  
protocols:
  search:
    name: "market_aware_search"
    params:
      beta: 0.95
  
  utility:
    name: "cobb_douglas"

agents:
  - count: 5
    utility_type: "cobb_douglas"
    utility_params:
      alpha_A: 0.7
      alpha_B: 0.3
    endowment:
      A: 10.0
      B: 2.0
      M: 5.0
    spawn_region: [5, 5, 25, 25]
  
  - count: 5
    utility_type: "cobb_douglas"
    utility_params:
      alpha_A: 0.3
      alpha_B: 0.7
    endowment:
      A: 2.0
      B: 10.0
      M: 5.0
    spawn_region: [5, 5, 25, 25]

resources:
  - commodity: "A"
    count: 5
    regeneration_rate: 0.1
  - commodity: "B"
    count: 5
    regeneration_rate: 0.1
```

2. **`tests/test_market_post_integration.py`** - Integration tests

```python
def test_yaml_market_loading():
    """Markets load correctly from YAML"""
    scenario = load_scenario("scenarios/demos/simple_walrasian_market.yaml")
    sim = Simulation(scenario)
    
    assert len(sim.grid.market_posts) == 1
    market = sim.grid.market_posts[0]
    assert market.location == (15, 15)
    assert market.mechanism_type == "walrasian"
    assert "A" in market.commodities


def test_market_telemetry_recorded():
    """Market events logged to telemetry"""
    scenario = load_scenario("scenarios/demos/simple_walrasian_market.yaml")
    sim = Simulation(scenario)
    
    sim.run(ticks=10)
    
    # Query telemetry
    conn = sqlite3.connect(sim.telemetry.db_path)
    clears = pd.read_sql("SELECT * FROM market_clears", conn)
    
    assert len(clears) > 0
    assert 'clearing_price' in clears.columns
    assert clears.clearing_price.min() > 0


def test_price_convergence():
    """Prices stabilize over time"""
    scenario = load_scenario("scenarios/demos/simple_walrasian_market.yaml")
    sim = Simulation(scenario)
    
    sim.run(ticks=50)
    
    conn = sqlite3.connect(sim.telemetry.db_path)
    df = pd.read_sql("SELECT tick, clearing_price FROM market_clears WHERE commodity='A'", conn)
    
    early_prices = df[df.tick < 10].clearing_price.std()
    late_prices = df[df.tick >= 40].clearing_price.std()
    
    # Prices should stabilize (lower variance later)
    assert late_prices < early_prices
```

#### Files to Modify

1. **`src/telemetry/database.py`** - New tables

```python
def create_market_tables(conn):
    """Create tables for market telemetry"""
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS market_posts (
            market_id INTEGER PRIMARY KEY,
            location_x INTEGER,
            location_y INTEGER,
            visibility_radius INTEGER,
            interaction_radius INTEGER,
            broadcast_radius INTEGER,
            mechanism_type TEXT,
            commodities TEXT  -- JSON array
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS market_clears (
            tick INTEGER,
            market_id INTEGER,
            commodity TEXT,
            clearing_price REAL,
            quantity_traded REAL,
            num_buyers INTEGER,
            num_sellers INTEGER,
            num_participants INTEGER,
            converged INTEGER,  -- 1 if tatonnement converged, 0 otherwise
            PRIMARY KEY (tick, market_id, commodity)
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS market_orders (
            tick INTEGER,
            market_id INTEGER,
            agent_id INTEGER,
            commodity TEXT,
            direction TEXT,  -- 'buy' or 'sell'
            quantity REAL,
            limit_price REAL,
            PRIMARY KEY (tick, market_id, agent_id, commodity)
        )
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_market_clears_tick 
        ON market_clears(tick)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_market_clears_market 
        ON market_clears(market_id)
    """)
```

2. **`src/telemetry/db_loggers.py`** - Logging methods

```python
def log_market_clear(self, effect: MarketClear):
    """Log market clearing event"""
    self.conn.execute("""
        INSERT INTO market_clears 
        (tick, market_id, commodity, clearing_price, quantity_traded, 
         num_participants, converged)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        effect.tick,
        effect.market_id,
        effect.commodity,
        effect.price,
        effect.quantity,
        effect.num_participants,
        1  # Assume converged if we're logging (non-converged don't create effect)
    ))


def log_market_post(self, market: MarketPost):
    """Log market post metadata at simulation start"""
    self.conn.execute("""
        INSERT OR REPLACE INTO market_posts
        (market_id, location_x, location_y, visibility_radius, 
         interaction_radius, broadcast_radius, mechanism_type, commodities)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        market.id,
        market.location[0],
        market.location[1],
        market.visibility_radius,
        market.interaction_radius,
        market.broadcast_radius,
        market.mechanism_type,
        json.dumps(market.commodities)
    ))
```

3. **`src/scenarios/loader.py`** - Parse market_posts from YAML

```python
def load_market_posts(yaml_dict: dict) -> list[MarketPost]:
    """Parse market_posts section from scenario YAML"""
    market_posts = []
    
    for mkt_config in yaml_dict.get('market_posts', []):
        market = MarketPost(
            id=mkt_config['id'],
            location=tuple(mkt_config['location']),
            visibility_radius=mkt_config.get('visibility_radius', 10),
            interaction_radius=mkt_config.get('interaction_radius', 3),
            broadcast_radius=mkt_config.get('broadcast_radius', 15),
            mechanism_type=mkt_config.get('mechanism_type', 'walrasian'),
            commodities=mkt_config.get('commodities', ['A', 'B', 'M'])
        )
        
        # Mechanism will be instantiated by Simulation.__init__
        market_posts.append(market)
    
    return market_posts
```

4. **`src/vmt_engine/simulation.py`** - Initialize markets

```python
class Simulation:
    def __init__(self, scenario: Scenario):
        # ... existing initialization ...
        
        # Initialize market posts
        for market in scenario.market_posts:
            self.grid.add_market_post(market)
            
            # Instantiate mechanism
            mechanism_class = get_protocol("market", market.mechanism_type)
            params = scenario.market_mechanism_params.get(market.id, {})
            market.mechanism = mechanism_class(market, **params)
        
        # Log market metadata to telemetry
        for market in self.grid.market_posts.values():
            self.telemetry.log_market_post(market)
```

#### Milestone Tests

See integration tests above.

---

### Week 4: Multiple Markets + Refinement (6-8 hours)

**Goal:** Demonstrate local markets, price differences, emergent arbitrage

#### Files to Create

1. **`scenarios/demos/two_regional_markets.yaml`** - Multi-market scenario

```yaml
name: "Two Regional Markets"
description: "Spatially separated markets demonstrating price divergence and arbitrage"

grid:
  width: 60
  height: 30

market_posts:
  # Western market - abundant in A
  - id: 0
    location: [15, 15]
    visibility_radius: 10
    interaction_radius: 3
    broadcast_radius: 12
    mechanism_type: "walrasian"
    mechanism_params:
      adjustment_speed: 0.1
      tolerance: 0.01
    commodities: ["A", "B", "M"]
  
  # Eastern market - abundant in B
  - id: 1
    location: [45, 15]
    visibility_radius: 10
    interaction_radius: 3
    broadcast_radius: 12
    mechanism_type: "walrasian"
    mechanism_params:
      adjustment_speed: 0.1
      tolerance: 0.01
    commodities: ["A", "B", "M"]

params:
  ticks: 200
  exchange_regime: "centralized"

protocols:
  search:
    name: "market_aware_search"
    params:
      beta: 0.95

agents:
  # Western agents - produce A
  - count: 8
    utility_type: "cobb_douglas"
    utility_params:
      alpha_A: 0.4
      alpha_B: 0.6
    endowment:
      A: 15.0
      B: 3.0
      M: 5.0
    spawn_region: [5, 5, 25, 25]
  
  # Eastern agents - produce B
  - count: 8
    utility_type: "cobb_douglas"
    utility_params:
      alpha_A: 0.6
      alpha_B: 0.4
    endowment:
      A: 3.0
      B: 15.0
      M: 5.0
    spawn_region: [35, 5, 55, 25]
  
  # Mobile arbitrageurs (spawn in middle)
  - count: 4
    utility_type: "cobb_douglas"
    utility_params:
      alpha_A: 0.5
      alpha_B: 0.5
    endowment:
      A: 8.0
      B: 8.0
      M: 20.0  # Extra money for arbitrage
    spawn_region: [25, 10, 35, 20]
    move_budget: 5  # Can move farther

resources:
  # A resources near western market
  - commodity: "A"
    count: 8
    spawn_region: [5, 5, 25, 25]
    regeneration_rate: 0.15
  
  # B resources near eastern market
  - commodity: "B"
    count: 8
    spawn_region: [35, 5, 55, 25]
    regeneration_rate: 0.15
```

2. **`scripts/analyze_market_prices.py`** - Price analysis tool

```python
#!/usr/bin/env python3
"""
Analyze market price dynamics from telemetry database.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def analyze_market_prices(db_path: str):
    """Generate price convergence/divergence plots"""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM market_clears ORDER BY tick", conn)
    
    if df.empty:
        print("No market clearing data found")
        return
    
    # Plot price dynamics for each commodity
    commodities = df.commodity.unique()
    markets = df.market_id.unique()
    
    fig, axes = plt.subplots(len(commodities), 1, figsize=(12, 4*len(commodities)))
    if len(commodities) == 1:
        axes = [axes]
    
    for ax, commodity in zip(axes, commodities):
        for market_id in sorted(markets):
            data = df[(df.commodity == commodity) & (df.market_id == market_id)]
            ax.plot(data.tick, data.clearing_price, 
                   label=f"Market {market_id}", marker='o', markersize=2)
        
        ax.set_title(f"{commodity} Price Dynamics")
        ax.set_xlabel("Tick")
        ax.set_ylabel("Price")
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("market_price_analysis.png", dpi=150)
    print("Saved plot to market_price_analysis.png")
    
    # Calculate price convergence metrics
    print("\n=== Price Convergence Analysis ===")
    for commodity in commodities:
        commodity_data = df[df.commodity == commodity]
        
        # Price difference between markets over time
        if len(markets) >= 2:
            pivot = commodity_data.pivot(index='tick', columns='market_id', values='clearing_price')
            if len(pivot.columns) >= 2:
                price_diff = abs(pivot.iloc[:, 0] - pivot.iloc[:, 1])
                
                early_diff = price_diff[:20].mean()
                late_diff = price_diff[-20:].mean()
                
                print(f"\n{commodity}:")
                print(f"  Early price difference: {early_diff:.3f}")
                print(f"  Late price difference: {late_diff:.3f}")
                print(f"  Convergence: {(early_diff - late_diff) / early_diff * 100:.1f}%")


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "logs/telemetry.db"
    analyze_market_prices(db_path)
```

3. **`tests/test_regional_markets.py`** - Multi-market tests

```python
def test_two_markets_different_prices():
    """Markets with asymmetric supply have different prices initially"""
    scenario = load_scenario("scenarios/demos/two_regional_markets.yaml")
    sim = Simulation(scenario)
    
    sim.run(ticks=10)
    
    market0 = sim.grid.market_posts[0]
    market1 = sim.grid.market_posts[1]
    
    # Prices should differ due to local supply/demand
    assert abs(market0.current_prices['A'] - market1.current_prices['A']) > 0.1


def test_arbitrage_convergence():
    """Prices converge over time due to arbitrage"""
    scenario = load_scenario("scenarios/demos/two_regional_markets.yaml")
    sim = Simulation(scenario)
    
    # Early prices
    sim.run(ticks=10)
    early_diff = abs(
        sim.grid.market_posts[0].current_prices['A'] - 
        sim.grid.market_posts[1].current_prices['A']
    )
    
    # Late prices
    sim.run(ticks=100)
    late_diff = abs(
        sim.grid.market_posts[0].current_prices['A'] - 
        sim.grid.market_posts[1].current_prices['A']
    )
    
    # Prices should converge (difference shrinks)
    assert late_diff < early_diff * 0.5


def test_market_choice_by_distance():
    """Agent prefers closer market when prices are similar"""
    # Setup: Agent equidistant to 2 markets
    # Both markets have same prices
    # Assert: Agent targets closer market (or deterministic tie-breaking)
    pass


def test_market_thickness():
    """Market participation correlates with local agent density"""
    scenario = load_scenario("scenarios/demos/two_regional_markets.yaml")
    sim = Simulation(scenario)
    
    sim.run(ticks=20)
    
    conn = sqlite3.connect(sim.telemetry.db_path)
    df = pd.read_sql("SELECT market_id, AVG(num_participants) as avg_participants FROM market_clears GROUP BY market_id", conn)
    
    # Both markets should have participants
    assert all(df.avg_participants > 0)
```

#### Visualization Updates

Add to `src/vmt_pygame/renderer.py`:

```python
def render_market_posts(self, screen, sim):
    """Render market posts on grid"""
    for market in sim.grid.market_posts.values():
        x, y = self._grid_to_screen(market.location)
        
        # Draw market icon (e.g., building)
        pygame.draw.rect(screen, (100, 100, 150), 
                        (x-10, y-10, 20, 20))
        pygame.draw.polygon(screen, (80, 80, 120),
                           [(x, y-15), (x-12, y-5), (x+12, y-5)])
        
        # Draw visibility radius (translucent)
        if self.show_radii:
            radius_px = market.visibility_radius * self.cell_size
            surf = pygame.Surface((radius_px*2, radius_px*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (100, 100, 200, 30), 
                             (radius_px, radius_px), radius_px)
            screen.blit(surf, (x - radius_px, y - radius_px))
        
        # Display current prices
        if market.current_prices:
            price_text = ", ".join(f"{k}:{v:.2f}" for k, v in market.current_prices.items())
            text = self.font.render(price_text, True, (0, 0, 0))
            screen.blit(text, (x + 15, y))


def render_agent_market_targeting(self, screen, agent, sim):
    """Show arrow from agent to target market"""
    if hasattr(agent, 'target_market_id') and agent.target_market_id is not None:
        market = sim.grid.market_posts.get(agent.target_market_id)
        if market:
            agent_pos = self._grid_to_screen(agent.position)
            market_pos = self._grid_to_screen(market.location)
            pygame.draw.line(screen, (0, 200, 0), agent_pos, market_pos, 2)
```

#### Milestone Tests

See tests above.

---

## Key Design Patterns

### 1. Determinism

**Critical for scientific validity.**

- **Sort all agent lists:** `sorted(agent_ids)` before processing
- **Sort all orders:** `sorted(orders, key=lambda o: o.agent_id)`
- **Tie-breaking:** Use agent ID for consistent ordering
- **Float precision:** Round prices to 2 decimals: `round(price, 2)`
- **Seeded RNG only:** Use `sim.rng` for any stochastic elements (none in initial implementation)

### 2. Effect-Based State Changes

**Maintain architectural consistency.**

- Markets return `Trade` effects (existing type)
- `MarketClear` effect is for logging only (doesn't modify state)
- TradeSystem applies all effects via existing `apply_effects()` logic
- No direct state mutation in protocols

### 3. Spatial Grounding

**Preserve VMT's core principle.**

- Always check `can_interact()` before allowing orders
- Movement toward markets uses existing `MoveEffect`
- Visibility strictly enforced by `visibility_radius`
- Distance matters: `discounted_value = value * (beta ** distance)`

### 4. Protocol Registration

**Follow existing pattern.**

```python
@register_protocol("market", "walrasian")
class WalrasianAuctioneer(MarketMechanism):
    ...

@register_protocol("search", "market_aware_search")
class MarketAwareSearchProtocol(SearchProtocol):
    ...
```

### 5. Backward Compatibility

**Existing scenarios must still work.**

- If `market_posts` section absent in YAML → no markets created
- If no markets exist → `StandardSearchProtocol` used automatically
- Bilateral trading logic unchanged
- All existing tests should pass

---

## Extension Points (Explicitly Deferred)

These features are **intentionally out of scope** for initial implementation but designed to be added later:

### Economic Extensions

1. **Sophisticated market valuation** - agents predict equilibrium prices using utility gradients
2. **Strategic market choice** - agents weigh market vs bilateral based on expected surplus
3. **Market entry costs** - fees or registration to participate
4. **Intertemporal arbitrage** - agents hold inventory speculatively
5. **Credit/debt markets** - money market with interest rates
6. **Heterogeneous information** - agents have different beliefs about prices

### Mechanism Extensions

1. **Posted-price markets** - simpler take-it-or-leave-it mechanism
2. **Continuous double auction** - order book with bid-ask spread
3. **Periodic auctions** - markets clear every N ticks, not every tick
4. **Market makers** - specialized agents providing liquidity
5. **Limit order books** - persistent orders across ticks

### Institutional Extensions

1. **Market hours** - markets only open certain ticks
2. **Transaction costs** - broker fees, taxes
3. **Market segmentation** - some agents excluded from some markets
4. **Information networks** - agents share price knowledge socially
5. **Market emergence** - endogenous market creation at high-traffic locations

---

## Risk Analysis & Mitigation

### Risk: Breaking Determinism

**Probability:** Medium  
**Impact:** Critical

**Mitigation:**
- Rigorous sorting of all collections before iteration
- Use only seeded RNG (`sim.rng`)
- Test with `compare_telemetry_snapshots.py` script
- Property-based testing for invariants

### Risk: Performance Degradation

**Probability:** Low-Medium  
**Impact:** Medium

**Mitigation:**
- Profile market clearing algorithms
- Use efficient data structures (consider `sortedcontainers` for CDA later)
- Spatial indexing for agent lookups near markets
- Benchmark with `scripts/benchmark_performance.py`

### Risk: Architectural Complexity

**Probability:** Medium  
**Impact:** Medium

**Mitigation:**
- Strict adherence to Protocol → Effect → State pattern
- Keep MarketMechanism implementations focused and testable
- Unified trade phase minimizes changes to core loop
- Comprehensive unit tests for each mechanism

### Risk: Theoretical Incorrectness

**Probability:** Low  
**Impact:** High

**Mitigation:**
- Base implementations on established literature (Walras, Smith)
- Property-based testing for economic invariants (market clearing, efficiency)
- Peer review of mechanism logic
- Compare results with known theoretical predictions

### Risk: Spatial Grounding Lost

**Probability:** Low  
**Impact:** Critical

**Mitigation:**
- Strictly enforce interaction radii in code
- Visualize market locations and agent movements
- Test that agents must physically approach markets
- Document spatial parameters clearly

### Risk: Scope Creep

**Probability:** Medium  
**Impact:** Medium

**Mitigation:**
- Explicit extension points document deferred features
- Focus on minimal viable implementation (Walrasian only initially)
- Resist adding "nice to have" features during core development
- Plan refinement phase after basic functionality works

---

## Testing Strategy

### Unit Tests

- `test_market_post_infrastructure.py` - Data structures, radii logic
- `test_walrasian_mechanism.py` - Tatonnement algorithm, convergence
- `test_market_aware_search.py` - Target selection, value estimation

### Integration Tests

- `test_market_post_integration.py` - Full simulation with markets
- `test_regional_markets.py` - Multiple markets, arbitrage
- `test_mixed_trade_modes.py` - Markets + bilateral coexistence

### Regression Tests

- All existing tests must pass
- `test_bilateral_still_works.py` - Scenarios without markets unchanged

### Property Tests

- Market clearing: `sum(demand) ≈ sum(supply)` at equilibrium
- No arbitrage: Prices converge over time (if reachable)
- Efficiency: Total utility increases with markets vs. bilateral-only
- Conservation: Money + goods conserved across all trades

### Performance Tests

- `scripts/benchmark_performance.py` - Measure tick time with markets
- Target: <10% overhead vs. bilateral-only for same number of trades

---

## Documentation Requirements

### Code Documentation

- Docstrings for all new classes and methods
- Inline comments for complex algorithms (tatonnement)
- Type hints throughout

### User Documentation

- Update `docs/2_technical_manual.md` with market concepts
- Create `docs/markets_guide.md` for pedagogical use
- Update scenario YAML documentation with market_posts schema

### Developer Documentation

- This implementation blueprint
- Architecture diagrams (to be created)
- Protocol interaction flowcharts

---

## Success Criteria

### Week 1 Complete When:
- [ ] `MarketPost` class implemented and tested
- [ ] Agents perceive markets in worldview
- [ ] Markets appear on grid
- [ ] Tests pass

### Week 2 Complete When:
- [ ] Walrasian mechanism clears trades
- [ ] Unified trade phase processes both markets and bilateral
- [ ] Market preference over bilateral works
- [ ] Tests pass

### Week 3 Complete When:
- [ ] Markets configurable via YAML
- [ ] Telemetry records market events
- [ ] Price data queryable from database
- [ ] Integration tests pass

### Week 4 Complete When:
- [ ] Multiple markets scenario runs
- [ ] Price convergence observable
- [ ] Analysis script generates plots
- [ ] All tests pass
- [ ] Performance acceptable

### Overall Success When:
- [ ] All 4 weeks complete
- [ ] Determinism verified (same seed → same results)
- [ ] Existing bilateral scenarios still work
- [ ] Documentation updated
- [ ] Ready for pedagogical use

---

## Next Steps

1. **Create Week 1 branch:** `git checkout -b feature/market-posts-week1`
2. **Implement core infrastructure** following Week 1 plan
3. **Run tests:** `bash -c "source venv/bin/activate && python -m pytest tests/test_market_post_infrastructure.py -v"`
4. **Review and iterate** before proceeding to Week 2

---

## References

### Academic Literature

1. **Walras, L. (1874)** - Elements of Pure Economics (tatonnement concept)
2. **Arrow, K. & Debreu, G. (1954)** - General competitive equilibrium
3. **Smith, V. (1962)** - Experimental economics, double auctions
4. **Gode, D. & Sunder, S. (1993)** - Zero-intelligence traders achieve efficiency
5. **Axtell, R. (2005)** - "The Complexity of Exchange" (ABM perspective)
6. **Tesfatsion, L. & Judd, K. (eds.)** - Handbook of Computational Economics, Vol 2
7. **Fujita, M., Krugman, P., Venables, A.** - The Spatial Economy (economic geography)
8. **Christaller, W. (1933)** - Central Place Theory (market catchment areas)

### VMT Project Documents

- `docs/1_project_overview.md` - Core principles
- `docs/2_technical_manual.md` - Existing architecture
- `docs/protocols_10-27/` - Protocol implementation patterns
- `docs/tmp_plans/market_plans/executive_summary.md` - Original market proposal
- `docs/tmp_plans/market_plans/gem.md` - Alternative perspective

---

**Document Version:** 1.0  
**Last Updated:** October 29, 2025  
**Author:** CMF  
**Status:** Ready for Implementation

