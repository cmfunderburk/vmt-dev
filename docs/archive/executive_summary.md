# Executive Summary: Centralized Markets for VMT

## Overview

To extend VMT with centralized markets while preserving spatial grounding, we adopt a **"Market Post" architecture**: explicit market locations on the grid that agents must discover and approach. Each MarketPost has a fixed location and parameters (visibility radius, interaction radius, broadcast radius, commodities) so agents can only trade there when nearby. This hybrid spatial-institutional model preserves the intuition of villages/markets (with distance costs and limited information) while enabling rich price discovery mechanisms (Walrasian auction, posted prices, double auction). 

Agents use an extended search protocol to evaluate markets (like evaluating bilateral partners), moving toward the highest-value opportunity (market or other agent). We add a dedicated Market Phase into the tick cycle: agents reach a market, submit orders (e.g. bid/ask) when within its interaction radius, the market clears at equilibrium prices or by matching, and all trades are executed simultaneously. Crucially, this coexists with existing bilateral trades (agents who don't use a market still barter locally). 

This approach achieves local price formation and arbitrage: multiple MarketPosts create separate local markets (with possibly different prices), yet arbitrage naturally pushes prices toward each other depending on agents' mobility and information spread.

### Key Advantages

- **Spatially Grounded Markets**: Market Posts have coordinates, so discovery has realistic costs
- **Regional Markets**: Multiple posts produce organic regional markets
- **Mixed Exchange Modes**: Supports both local and global exchanges (village fairs vs. a "world market")
- **Efficiency Gains**: Benefits from scale and centralization without "telepathic" trading
- **Deterministic**: No randomness in matching aside from fixed rules
- **Clean Integration**: Works within existing 7-phase protocol architecture

**Timeline**: ~30 hours over 4 weeks to implement and test fully.

## Architectural Design

Our design layers new market concepts onto the existing protocol framework. The core idea is that each MarketPost is a special grid entity with fixed location and interaction radii; agents "see" markets within view and travel to them to trade. Once at a market, agents submit buy/sell orders, and a centralized mechanism (e.g. Walrasian auctioneer or double auction) clears the orders.

### Core Components

#### MarketPost Entity

A dataclass with fields such as:
- `id`: Unique identifier
- `location`: (x,y) grid coordinates
- `visibility_radius`: Distance at which agents can see the market
- `interaction_radius`: Distance at which agents can trade
- `broadcast_radius`: Distance for price information dissemination  
- `mechanism_type`: "walrasian", "posted_price", "cda", etc.
- `handled commodities`: List of tradable goods at this market
- Runtime state: current prices, pending orders, last clear tick
- Mechanism instance: Pointer to market clearing mechanism

Example implementation:

```python
@dataclass
class MarketPost:
    id: int
    location: Position
    visibility_radius: int = 10
    interaction_radius: int = 3
    broadcast_radius: int = 15
    mechanism_type: str = "walrasian"
    commodities: list[str] = field(default_factory=lambda: ["A","B","M"])
    current_prices: dict[str, float] = field(default_factory=dict)
    pending_orders: list = field(default_factory=list)
    mechanism: Optional[MarketMechanism] = None
    
    def can_see(self, agent_pos, grid) -> bool:
        return grid.manhattan_distance(agent_pos, self.location) <= self.visibility_radius
        
    def can_interact(self, agent_pos, grid) -> bool:
        return grid.manhattan_distance(agent_pos, self.location) <= self.interaction_radius
```

#### Search Protocol Extension

We create a `MarketAwareSearchProtocol` that ranks markets alongside agents and resources as potential targets. In each tick's Decision phase, the agent's worldview includes visible markets and their estimated values.

```python
for market in world.visible_markets:
    val = estimate_market_value(market, world)
    dist = manhattan(world.pos, market.location)
    discounted = val * (beta**dist)
    preferences.append(("market", market.id, val, discounted, dist))
preferences.sort(key=lambda x: x[3], reverse=True)
```

#### Market Mechanisms & Order Books

Each MarketPost has an associated `MarketMechanism` object (e.g. `WalrasianAuctioneer`, `PostedPrice`, `ContinuousDoubleAuction`). When agents reach the market, we collect their orders.

For a Walrasian auction, we do iterative tatonnement:

```python
def clear_market(self, orders):
    price = initial_price
    for i in range(max_iter):
        demand = sum(o.quantity for o in orders if o.type=="buy" and o.limit>=price)
        supply = sum(o.quantity for o in orders if o.type=="sell" and o.limit<=price)
        excess = demand - supply
        if abs(excess) < tolerance:
            break
        price += adjustment_speed * excess  # raise price if excess >0
    return price
```

For determinism, we sort buy-orders by descending bid and sell-orders by ascending ask before pairing:

```python
buyers = [o for o in orders if o.direction=="buy" and o.limit_price>=clearing_price]
sellers = [o for o in orders if o.direction=="sell" and o.limit_price<=clearing_price]
buyers.sort(key=lambda o: (-o.limit_price, o.agent_id))
sellers.sort(key=lambda o: (o.limit_price, o.agent_id))
for buyer, seller in zip(buyers, sellers):
    qty = min(buyer.quantity, seller.quantity)
    if qty > 0:
        effects.append(Trade(..., price=clearing_price))
```

#### WorldView and Effects

Extended WorldView includes:
- Visible markets (with last observed prices and staleness)
- Markets the agent can interact with
- Market-price broadcasts received

New Effects:
- `TargetMarket(agent, market_id, market_location)`
- `SubmitOrder(agent, market_id, Order)`
- `MarketClearing(market_id, commodity, clearing_price, clearing_qty, executed_orders)`

#### Phase Structure Integration

We insert a new market-related step into the tick cycle:

1. **Perception**: Agents perceive neighbors, resources and any MarketPosts within visibility
2. **Decision**: Agents target either another agent or a market (via the MarketAware search)
3. **Movement**: Agents move toward chosen target (either an agent or market)
4. **Market Phase (NEW)**: For each market post, collect orders from agents within interaction radius, then clear and execute trades
5. **Trade Phase (Bilateral)**: Remaining agents not in markets match bilaterally as before
6. **Foraging, Resources, Housekeeping**: unchanged

## Implementation Plan (4 Weeks, ~30h)

### Week 1: MarketPost Infrastructure (5-8 hours)
- Define the MarketPost dataclass and add support in the Grid
- Extend perception phase so agents "see" markets
- Modify SearchProtocol to evaluate markets
- Implement `_estimate_market_value()` and `TargetMarket` effect
- **Milestone**: Agents can discover and move toward market posts

### Week 2: Order Submission Logic (5-8 hours)
- Create `MarketMechanism` base class and concrete mechanisms
- Implement `WalrasianAuctioneer` (collect orders, tatonnement price clearing, trade execution)
- Implement simpler mechanisms (posted-price shops, continuous double auction)
- Ensure MarketPost records pending orders, price updates, and broadcasts
- **Milestone**: A single market post can accept orders and clear trades

### Week 3: Integration and Parallel Trading (5-8 hours)
- Modify trade phase to handle both bilateral and centralized trades
- Partition agents by target type (market vs bilateral)
- Apply trade effects and update agents' holdings
- Update telemetry to record market data
- **Milestone**: Mixed regime works without interference

### Week 4: Localization & Testing (5-8 hours)
- Create scenarios with multiple MarketPosts (2-3 posts in different regions)
- Tune parameters (visibility/interact radii, info decay) for local markets
- Test economic outcomes (price divergence/convergence, arbitrage)
- Measure efficiency improvements (total surplus)
- Benchmark performance with 50-100 agents
- **Milestone**: Demonstrate price dynamics and stable mixed trading

## Economic Insights & Literature

### Spatial Markets & Catchment
Economic geography teaches that real markets have "hinterlands". **Christaller's Central Place Theory (1933)** posits that each market serves consumers within some range (maximum travel distance) and needs a minimum threshold population to be viable. In practice, cities, towns and bazaars form a hierarchical hexagonal pattern: larger markets (central places) cover wider areas than villages.

### Agent-Based Spatial Market Models
ABMs of markets often capture this locality. For example:
- JASSS spatial economy models have consumers choose firms by both price and geographic proximity
- Beattie et al. (2022) model a Local Energy Market where agents (homes) in a neighborhood submit bids and asks in an online double-auction, coordinating local supply of renewable energy

### Market Efficiency
Centralized markets tend to be more efficient than ad-hoc bilateral bargaining. A classic result (Gode & Sunder, 1993) shows that even "zero-intelligence" traders achieve nearly the competitive equilibrium in a continuous double auction.

### Price Convergence vs Arbitrage
Arbitrage forces prices toward parity. In theory, any persistent price difference between two markets is exploited until it disappears. In our spatial model, however, arbitrage is imperfect: agents take time to travel and may lack perfect information. We model these frictions with:
- Broadcast radii
- Information decay
- Transport/transaction costs

### Market Thickness & Liquidity
Market "thickness" (number of buyers/sellers) affects stability. Thicker markets yield more reliable clearing and smaller price dispersion. We guard against degenerate cases by:
- Allowing bilateral fallback (agents can still barter if no market is reachable)
- Detecting non-convergence (e.g. failing tatonnement)

## Risk Analysis and Mitigation

Each risk is covered either by design (e.g. distance-based interaction inherently limits congestion) or by providing fallback mechanisms. We will clearly document all assumptions (e.g. agents see only local prices) so students can understand how they affect outcomes.

## Example Code Snippets

### MarketPost and System Setup

```python
# Define market posts in scenario (YAML or code)
market_posts = [
    MarketPost(id=0, location=(10,10), visibility_radius=8, 
               interaction_radius=2, commodities=["A","B","M"]),
    MarketPost(id=1, location=(30,30), visibility_radius=10, 
               interaction_radius=3, commodities=["A","M"])
]
market_system = MarketPostSystem(market_posts)
```

### Search Protocol

```python
class MarketAwareSearchProtocol(SearchProtocol):
    def build_preferences(self, world):
        prefs = []
        # existing agent/resource targets...
        for market in world.visible_markets:
            value = estimate_market_profit(market, world)
            dist = manhattan(world.pos, market.location)
            score = value * (world.beta ** dist)
            prefs.append(("market", market.id, value, score, dist))
        return sorted(prefs, key=lambda x: x[3], reverse=True)
```

### Walrasian Auctioneer

```python
class WalrasianAuctioneer:
    def clear_market(self, orders):
        price = self.initial_price or 1.0
        for _ in range(self.max_iterations):
            demand = sum(o.qty for o in orders if o.dir=="buy" and o.limit>=price)
            supply = sum(o.qty for o in orders if o.dir=="sell" and o.limit<=price)
            excess = demand - supply
            if abs(excess) <= self.price_tolerance:
                break
            price += self.adjustment_speed * excess
        return price  # final clearing price

    def execute_trades(self, orders, clearing_price):
        buyers = sorted([o for o in orders if o.dir=="buy" and o.limit>=clearing_price],
                        key=lambda o: (-o.limit, o.agent_id))
        sellers = sorted([o for o in orders if o.dir=="sell" and o.limit<=clearing_price],
                        key=lambda o: (o.limit, o.agent_id))
        trades = []
        for b, s in zip(buyers, sellers):
            qty = min(b.qty, s.qty)
            if qty > 0:
                trades.append(TradeEffect(b.agent, s.agent, b.commodity, qty, clearing_price))
                b.qty -= qty
                s.qty -= qty
        return trades
```

### Trade Phase Integration

```python
market_agents = defaultdict(list)
bilateral_pairs = []

for agent in sim.agents:
    if agent.target_type == "market" and agent.target_market_id is not None:
        market_agents[agent.target_market_id].append(agent.id)
    elif agent.paired_with is not None:
        bilateral_pairs.append((agent, agent.paired_with))

# Market trades
for mkt_id, agent_ids in market_agents.items():
    if not agent_ids: continue
    orders = sim.market_posts[mkt_id].mechanism.collect_orders(agent_ids, sim.world)
    if orders:
        prices = sim.market_posts[mkt_id].mechanism.clear_market(orders, sim.world)
        effects = sim.market_posts[mkt_id].mechanism.execute_trades(orders, prices, sim.world)
        apply_effects(effects, sim)

# Bilateral trades (as before)...
```

## Key References

1. **Central Place Theory** (Christaller, 1933) - Market thresholds and spatial catchment
2. **Agent-based market models** (Tesfatsion 2006) - Spatial simulations with price & proximity
3. **Zero-Intelligence Double Auction** (Gode & Sunder, 1993) - High efficiency with random traders
4. **Arbitrage Theory** (Kirzner 1973) - Spatial price convergence limited by transport costs
5. **Local Energy Markets** (Beattie et al., 2022) - ABM of double-auction with spatially-distributed agents

## Related VMT Documents

- phase3_centralized_markets_architecture.md
- phase3_market_post_implementation.md
- protocol_implementation_review.md

These sources support our design: markets as explicit spatial institutions, the power of auctions for efficiency, and the importance of distance-dependent discovery.
