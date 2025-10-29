# Endogenous Market Formation: Technical Specification
**VMT Phase 3: Emergent Centralized Markets**  
**Created:** October 29, 2025  
**Status:** Planning - Ready for Implementation  
**Approach:** Density-Based Market Emergence

---

## Executive Summary

This specification defines an **endogenous market formation system** for VMT where markets emerge organically from agent clustering rather than being pre-placed. When sufficient agents cluster within interaction range (≥5 agents), a market area forms and those agents trade via centralized clearing mechanisms (Walrasian auction). Markets persist across ticks while density remains above threshold, allowing price convergence. Isolated agents continue bilateral trading.

This approach is pedagogically superior to pre-defined markets: students observe how markets emerge at natural gathering points (resource clusters, trade routes, migration targets) and can study the critical conditions for market formation as an economic research question.

### Core Design Decisions (Finalized)

Based on design review, the following decisions are locked for initial implementation:

1. **Clustering Algorithm:** Grid-based (Option A) - simple, deterministic, sufficient for functionality testing
2. **Market Persistence:** Lifecycle with hysteresis - markets persist across ticks, dissolve after patience period
3. **Agent Assignment:** Exclusive (Approach A) - each agent in at most one market, priority by size/distance/ID
4. **Mechanism Type:** Uniform Walrasian (Option A) - all markets use same mechanism initially
5. **Market Identity:** Location-based - markets reuse ID if formed within 2 cells of previous location
6. **Agent Pairing:** Unpair on market entry - agents cannot be in both bilateral pairing and market simultaneously
7. **Performance:** Not a concern for initial implementation - focus on correctness first, optimize later

### Core Design Principles

1. **Emergence:** Markets form where agents cluster, not by designer fiat
2. **Persistence:** Markets maintain identity and price history across ticks
3. **Coexistence:** Market and bilateral trade modes operate simultaneously
4. **Determinism:** Clustering detection and assignment are fully deterministic
5. **Spatial Grounding:** Physical proximity required; no telepathic markets

### Key Parameters

- `market_formation_threshold`: Minimum agents to form market (default: 5)
- `market_dissolution_threshold`: Minimum agents to sustain market (default: 3)
- `market_dissolution_patience`: Ticks below threshold before dissolving (default: 5)
- `market_mechanism`: Clearing algorithm ("walrasian", "posted_price", "cda")
- `interaction_radius`: Spatial range for market participation (existing param)

---

## Economic Motivation

### Historical Emergence of Markets

Real-world markets did not appear by decree but emerged organically at locations where:
1. **Resource abundance** attracted gatherers (mines, fertile valleys, ports)
2. **Transportation nodes** reduced travel costs (crossroads, river fords, harbors)
3. **Population density** created thick markets (cities, villages, seasonal fairs)
4. **Network effects** reinforced concentration (more buyers → more sellers → more buyers)

Economic geography literature (Christaller 1933, Fujita-Krugman-Venables 1999) explains market location as minimizing total transportation costs while maintaining sufficient "threshold population" for viability.

### Pedagogical Advantages

Students can observe and analyze:
- **Critical density:** What conditions trigger market formation?
- **Location:** Where do markets form? (Near resources? At grid center? Randomly?)
- **Stability:** Do markets persist once formed, or flicker on/off?
- **Efficiency:** Do emergent markets improve welfare compared to pure bilateral trade?
- **Multiple equilibria:** Can multiple stable markets coexist?

This is pedagogically richer than pre-placed markets because it makes market **existence** itself an endogenous outcome of agent behavior.

---

## Architectural Design

### Phase Interactions

**Phase 2 (Decision/Matching) Considerations:**

Currently, the MatchingProtocol in Phase 2 pairs agents based on bilateral trade opportunities without awareness of potential market formation. This creates a potential issue: agents may pair up bilaterally even though they would benefit more from participating in an emerging market.

**For initial implementation:** We handle this by **unpairing agents when they enter markets** (Step 3 of Phase 4). This ensures agents are not in both bilateral and market states simultaneously.

**Future enhancement:** Modify MatchingProtocol to be market-aware:
- Agents detect if they're in a high-density cluster (≥ threshold nearby agents)
- If yes, skip bilateral pairing and wait for market to form
- This prevents wasteful pairing when a market is imminent

This enhancement is **deferred** to avoid modifying Phase 2 logic during initial implementation. The unpair-on-entry approach is simpler and sufficient for basic functionality.

### Modified Phase 4: Trade System

Phase 4 (Trade) is extended with market detection logic executed **before** trade processing:

```
Phase 4 Execution Flow:
┌─────────────────────────────────────────────┐
│ 1. DETECT MARKETS                           │
│    - Scan grid for agent clusters          │
│    - Form new markets if density ≥ 5       │
│    - Update existing markets               │
│    - Dissolve markets if density < 3 (5t)  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 2. ASSIGN AGENTS TO MARKETS                 │
│    - Exclusive assignment (one market max) │
│    - Priority: largest market → lowest ID  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 3. PROCESS MARKET TRADES                    │
│    - For each active market:               │
│      * Collect orders from participants    │
│      * Run clearing mechanism (tatonnement)│
│      * Generate Trade effects              │
│      * Update market prices                │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 4. PROCESS BILATERAL TRADES                 │
│    - Skip agents in markets                │
│    - Existing paired-agent logic           │
│    - Generate Trade/Unpair effects         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 5. APPLY ALL EFFECTS                        │
│    - Update inventories                    │
│    - Log trades to telemetry               │
└─────────────────────────────────────────────┘
```

### Market Detection Algorithm

**Option A: Grid-Based Clustering (To Be Implemented)**

Scan agents sequentially, count neighbors within `interaction_radius`. If count ≥ threshold, create/update market.

```python
def _detect_market_areas(self, sim: 'Simulation') -> list[MarketArea]:
    """
    Detect dense agent clusters that form markets.
    
    Algorithm:
    1. Sort agents by ID (determinism)
    2. For each agent not yet assigned:
       a. Count agents within interaction_radius
       b. If count >= formation_threshold:
          - Check if existing market nearby (reuse ID)
          - Otherwise create new market
       c. Mark all participants as processed
    3. Update existing markets' participant lists
    4. Check dissolution criteria
    
    Returns:
        List of active MarketArea objects
    """
    markets_by_center: dict[Position, MarketArea] = {}
    assigned_agents: set[int] = set()
    
    # Sort for determinism
    sorted_agents = sorted(sim.agents, key=lambda a: a.id)
    
    for agent in sorted_agents:
        if agent.id in assigned_agents:
            continue
        
        # Find all agents within interaction_radius
        nearby = self._find_agents_within_radius(
            agent.pos,
            sim.params['interaction_radius'],
            sim
        )
        
        if len(nearby) >= sim.params['market_formation_threshold']:
            # Compute geometric center of cluster
            center = self._compute_cluster_center(nearby, sim)
            
            # Check if market already exists at this location
            market = self._find_or_create_market(center, sim)
            market.participant_ids = [a.id for a in nearby]
            market.last_active_tick = sim.tick
            market.ticks_below_threshold = 0
            
            markets_by_center[center] = market
            assigned_agents.update(market.participant_ids)
    
    # Update existing markets not found this tick
    self._update_inactive_markets(markets_by_center, sim)
    
    return list(markets_by_center.values())


def _find_agents_within_radius(self, center: Position, radius: int, 
                                sim: 'Simulation') -> list['Agent']:
    """Return all agents within Manhattan distance <= radius"""
    nearby = []
    for agent in sim.agents:
        dist = abs(agent.pos[0] - center[0]) + abs(agent.pos[1] - center[1])
        if dist <= radius:
            nearby.append(agent)
    return sorted(nearby, key=lambda a: a.id)  # Deterministic ordering


def _compute_cluster_center(self, agents: list['Agent']) -> Position:
    """
    Compute geometric center of agent cluster.
    Round to grid coordinates.
    """
    if not agents:
        return (0, 0)
    
    avg_x = sum(a.pos[0] for a in agents) / len(agents)
    avg_y = sum(a.pos[1] for a in agents) / len(agents)
    
    # Round to nearest integer grid cell
    return (round(avg_x), round(avg_y))


def _find_or_create_market(self, center: Position, 
                           sim: 'Simulation') -> MarketArea:
    """
    Check if market already exists near this location.
    If yes, reuse (maintaining price history).
    If no, create new market.
    """
    # Check existing markets
    for market_id, market in self.active_markets.items():
        dist = abs(market.center[0] - center[0]) + abs(market.center[1] - center[1])
        if dist <= 2:  # Within 2 cells counts as "same location"
            market.center = center  # Update center (may drift slightly)
            return market
    
    # Create new market
    market_id = self.next_market_id
    self.next_market_id += 1
    
    mechanism_type = sim.params.get('market_mechanism', 'walrasian')
    mechanism = self._create_mechanism(mechanism_type, sim)
    
    market = MarketArea(
        id=market_id,
        center=center,
        radius=sim.params['interaction_radius'],
        participant_ids=[],
        mechanism=mechanism,
        formation_tick=sim.tick
    )
    
    self.active_markets[market_id] = market
    return market


def _update_inactive_markets(self, active_centers: dict[Position, MarketArea],
                             sim: 'Simulation') -> None:
    """
    Update markets that didn't appear in current scan.
    Implement dissolution logic with hysteresis.
    """
    to_dissolve = []
    
    for market_id, market in self.active_markets.items():
        if market.center not in active_centers:
            # Market didn't form this tick
            market.ticks_below_threshold += 1
            market.participant_ids = []
            
            if market.ticks_below_threshold >= sim.params['market_dissolution_patience']:
                print(f"Market {market_id} dissolved at tick {sim.tick} "
                      f"(insufficient density for {market.ticks_below_threshold} ticks)")
                to_dissolve.append(market_id)
    
    # Remove dissolved markets
    for market_id in to_dissolve:
        del self.active_markets[market_id]
```

**Deferred Options (Document as Extensions):**

- **Option B: DBSCAN Clustering** - Use sklearn or custom DBSCAN for more sophisticated cluster detection
- **Option C: Voronoi Tessellation** - Partition grid into market catchment areas matching Christaller's model

---

### Market Persistence & Lifecycle

**Implementation: Persistent Markets with Hysteresis**

Markets maintain identity across ticks, allowing price convergence:

```python
@dataclass
class MarketArea:
    """
    An emergent market formed by agent clustering.
    Persists across ticks while density remains above threshold.
    """
    # Identity
    id: int
    center: Position  # May drift slightly as cluster moves
    radius: int  # Equal to interaction_radius
    
    # Current state
    participant_ids: list[int] = field(default_factory=list)
    
    # Market mechanism
    mechanism: 'MarketMechanism' = None
    current_prices: dict[str, float] = field(default_factory=dict)
    
    # Lifecycle tracking
    formation_tick: int = 0
    last_active_tick: int = 0
    ticks_below_threshold: int = 0  # Consecutive ticks with low density
    
    # Statistics (for telemetry)
    total_trades_executed: int = 0
    total_volume_traded: dict[str, float] = field(default_factory=dict)
    historical_prices: dict[str, list[tuple[int, float]]] = field(default_factory=dict)  # commodity -> [(tick, price), ...]


# Lifecycle Rules:
# - FORMATION: density >= market_formation_threshold (default: 5)
# - ACTIVE: density >= market_dissolution_threshold (default: 3)
# - DISSOLUTION: density < market_dissolution_threshold for market_dissolution_patience ticks (default: 5)
#
# Hysteresis prevents markets from flickering: harder to form than to sustain.
```

**Design Rationale:**

1. **Hysteresis:** Formation requires 5 agents, but dissolution only happens if density drops below 3 for 5 consecutive ticks. This prevents "flickering" markets.

2. **Price Continuity:** Persistent markets maintain `current_prices` across ticks, enabling tatonnement convergence.

3. **Location-Based Identity:** Markets reuse IDs if they form within 2 cells of a previous market's location. This allows natural drift as agent clusters move.

4. **Lifecycle Logging:** Formation and dissolution events are logged to telemetry for analysis.

**Deferred Options:**

- **Ephemeral Markets (Option A):** Form/dissolve each tick - simpler but no price convergence
- **Permanent Markets (Option C):** Never dissolve - eventually converges to pre-defined market behavior

---

### Agent Assignment to Markets

**Implementation: Exclusive Assignment**

Each agent participates in at most one market per tick. If multiple markets are in range, deterministic priority:

```python
def _assign_agents_to_markets(self, markets: list[MarketArea],
                              sim: 'Simulation') -> dict[int, list[int]]:
    """
    Assign each agent to at most one market.
    
    Priority for overlapping markets:
    1. Largest market (most participants)
    2. Closest market (by Manhattan distance to center)
    3. Lowest market ID (tie-breaker)
    
    Returns:
        dict mapping market_id -> [agent_ids]
    """
    assignment: dict[int, list[int]] = {m.id: [] for m in markets}
    assigned_agents: set[int] = set()
    
    # Pre-compute which markets each agent can reach
    agent_eligible_markets: dict[int, list[MarketArea]] = {}
    for agent in sim.agents:
        eligible = []
        for market in markets:
            dist = abs(agent.pos[0] - market.center[0]) + abs(agent.pos[1] - market.center[1])
            if dist <= market.radius:
                eligible.append(market)
        agent_eligible_markets[agent.id] = eligible
    
    # Assign agents deterministically
    for agent in sorted(sim.agents, key=lambda a: a.id):
        if agent.id in assigned_agents:
            continue
        
        eligible = agent_eligible_markets[agent.id]
        if not eligible:
            continue  # No markets in range
        
        # Sort markets by priority
        eligible_sorted = sorted(
            eligible,
            key=lambda m: (
                -len(m.participant_ids),  # Largest first (negative for descending)
                abs(agent.pos[0] - m.center[0]) + abs(agent.pos[1] - m.center[1]),  # Closest first
                m.id  # Lowest ID first
            )
        )
        
        # Assign to highest-priority market
        chosen_market = eligible_sorted[0]
        assignment[chosen_market.id].append(agent.id)
        assigned_agents.add(agent.id)
    
    return assignment
```

**Design Rationale:**

- **Exclusive:** Simplifies mechanism logic; each agent has single price vector
- **Deterministic:** Sorting and tie-breaking ensure reproducibility
- **Market Power:** Larger markets attract more agents (realistic agglomeration)

**Deferred Option:**

- **Allow Overlap (Approach B):** Agent can submit orders to multiple markets, splitting their budget/inventory

---

### Market Clearing Mechanism

**Implementation: Uniform Walrasian Auctioneer**

All emergent markets use the same clearing mechanism type (configured via scenario params):

```python
def _create_mechanism(self, mechanism_type: str, sim: 'Simulation') -> 'MarketMechanism':
    """Instantiate market mechanism based on type"""
    if mechanism_type == "walrasian":
        return WalrasianAuctioneer(
            adjustment_speed=sim.params.get('walrasian_adjustment_speed', 0.1),
            tolerance=sim.params.get('walrasian_tolerance', 0.01),
            max_iterations=sim.params.get('walrasian_max_iterations', 100)
        )
    elif mechanism_type == "posted_price":
        # To be implemented in Week 4+
        raise NotImplementedError("Posted price markets not yet implemented")
    elif mechanism_type == "cda":
        # To be implemented in Week 4+
        raise NotImplementedError("Continuous double auction not yet implemented")
    else:
        raise ValueError(f"Unknown market mechanism: {mechanism_type}")


class WalrasianAuctioneer(MarketMechanism):
    """
    Tatonnement price adjustment mechanism for emergent markets.
    Identical to pre-defined market version.
    """
    
    def __init__(self, adjustment_speed: float = 0.1,
                 tolerance: float = 0.01,
                 max_iterations: int = 100):
        self.adjustment_speed = adjustment_speed
        self.tolerance = tolerance
        self.max_iterations = max_iterations
    
    def execute(self, market: MarketArea, sim: 'Simulation') -> list['Effect']:
        """
        Clear market for all commodities.
        
        Returns:
            List of Trade and MarketClear effects
        """
        effects = []
        commodities = sim.params.get('commodities', ['A', 'B', 'M'])
        
        for commodity in commodities:
            # Find clearing price via tatonnement
            clearing_price, converged = self._find_clearing_price(
                market, commodity, sim
            )
            
            if not converged:
                print(f"WARNING: Market {market.id} tatonnement failed to converge "
                      f"for {commodity} at tick {sim.tick}")
                continue
            
            # Execute trades at clearing price
            trade_effects = self._execute_at_price(
                market, commodity, clearing_price, sim
            )
            effects.extend(trade_effects)
            
            # Update market state
            market.current_prices[commodity] = clearing_price
            market.total_trades_executed += len(trade_effects)
            
            # Track price history
            if commodity not in market.historical_prices:
                market.historical_prices[commodity] = []
            market.historical_prices[commodity].append((sim.tick, clearing_price))
            
            # Log clearing event
            effects.append(MarketClear(
                market_id=market.id,
                commodity=commodity,
                price=clearing_price,
                quantity=sum(e.quantity for e in trade_effects if isinstance(e, Trade)),
                tick=sim.tick,
                num_participants=len(market.participant_ids),
                converged=True
            ))
        
        return effects
    
    def _find_clearing_price(self, market: MarketArea, commodity: str,
                            sim: 'Simulation') -> tuple[float, bool]:
        """
        Iterative tatonnement to find equilibrium price.
        
        Starts from last clearing price if available (warm start).
        """
        # Warm start from previous price
        price = market.current_prices.get(commodity, 1.0)
        
        for iteration in range(self.max_iterations):
            demand = self._compute_demand(market, commodity, price, sim)
            supply = self._compute_supply(market, commodity, price, sim)
            excess_demand = demand - supply
            
            # Check convergence
            if abs(excess_demand) < self.tolerance:
                return round(price, 2), True
            
            # Adjust price proportional to excess demand
            price += self.adjustment_speed * excess_demand
            price = max(0.01, price)  # Price floor
        
        return round(price, 2), False  # Did not converge
    
    def _compute_demand(self, market: MarketArea, commodity: str,
                       price: float, sim: 'Simulation') -> float:
        """
        Calculate total quantity demanded at this price.
        
        For each agent in market, query their utility function to determine
        optimal purchase quantity at given price.
        
        Note: This is a simplified demand model for initial implementation.
        Full utility maximization with budget constraints to be added later.
        """
        total_demand = 0.0
        
        for agent_id in sorted(market.participant_ids):
            agent = sim.agent_by_id[agent_id]
            
            # Get marginal utility for the commodity
            if commodity == 'A':
                mu = agent.utility.mu_A(agent.inventory.A, agent.inventory.B)
            elif commodity == 'B':
                mu = agent.utility.mu_B(agent.inventory.A, agent.inventory.B)
            elif commodity == 'M':
                # Money has constant marginal utility (for now)
                mu = agent.lambda_money
            else:
                continue  # Unknown commodity
            
            # Simple demand rule: buy if MU > price
            # More sophisticated: solve utility maximization with budget constraint
            if mu > price:
                # Quantity demanded is proportional to (MU - price)
                # Limited by budget (money holdings)
                budget = agent.inventory.M / 100.0  # Convert from cents to dollars
                desired_qty = min(
                    (mu - price) / price,  # Quantity from utility gap
                    budget / price  # Budget constraint
                )
                total_demand += max(0, desired_qty)
        
        return total_demand
    
    def _compute_supply(self, market: MarketArea, commodity: str,
                       price: float, sim: 'Simulation') -> float:
        """
        Calculate total quantity supplied at this price.
        
        Note: Simplified supply model for initial implementation.
        """
        total_supply = 0.0
        
        for agent_id in sorted(market.participant_ids):
            agent = sim.agent_by_id[agent_id]
            
            # Get marginal utility for the commodity
            if commodity == 'A':
                mu = agent.utility.mu_A(agent.inventory.A, agent.inventory.B)
                current_stock = agent.inventory.A
            elif commodity == 'B':
                mu = agent.utility.mu_B(agent.inventory.A, agent.inventory.B)
                current_stock = agent.inventory.B
            elif commodity == 'M':
                mu = agent.lambda_money
                current_stock = agent.inventory.M / 100.0  # Convert to dollars
            else:
                continue  # Unknown commodity
            
            # Simple supply rule: sell if price > MU
            if price > mu and current_stock > 0:
                # Quantity supplied is proportional to (price - MU)
                # Limited by current inventory
                offered_qty = min(
                    (price - mu) / mu if mu > 0.01 else 1.0,
                    current_stock
                )
                total_supply += max(0, offered_qty)
        
        return total_supply
    
    def _execute_at_price(self, market: MarketArea, commodity: str,
                         price: float, sim: 'Simulation') -> list['Trade']:
        """
        Match buyers and sellers at clearing price.
        Deterministic pairing by agent ID.
        """
        buyers = []
        sellers = []
        
        for agent_id in sorted(market.participant_ids):
            agent = sim.agent_by_id[agent_id]
            
            # Get marginal utility for the commodity
            if commodity == 'A':
                mu = agent.utility.mu_A(agent.inventory.A, agent.inventory.B)
                current_stock = agent.inventory.A
            elif commodity == 'B':
                mu = agent.utility.mu_B(agent.inventory.A, agent.inventory.B)
                current_stock = agent.inventory.B
            elif commodity == 'M':
                mu = agent.lambda_money
                current_stock = agent.inventory.M / 100.0
            else:
                continue
            
            if mu > price:
                # Buyer
                budget = agent.inventory.M / 100.0
                max_qty = budget / price
                desired_qty = min(max_qty, (mu - price) / price)
                if desired_qty > 0.01:
                    buyers.append((agent_id, desired_qty))
            
            elif price > mu:
                # Seller
                offered_qty = min(current_stock, (price - mu) / mu if mu > 0.01 else 1.0)
                if offered_qty > 0.01:
                    sellers.append((agent_id, offered_qty))
        
        # Match buyers and sellers deterministically
        trades = []
        i, j = 0, 0
        
        while i < len(buyers) and j < len(sellers):
            buyer_id, buy_qty = buyers[i]
            seller_id, sell_qty = sellers[j]
            
            qty = min(buy_qty, sell_qty)
            qty = round(qty, 2)  # Precision
            
            if qty > 0.01:
                trades.append(Trade(
                    buyer_id=buyer_id,
                    seller_id=seller_id,
                    commodity=commodity,
                    quantity=qty,
                    price=price,
                    market_id=market.id  # Tag trade as market-based
                ))
            
            buyers[i] = (buyer_id, buy_qty - qty)
            sellers[j] = (seller_id, sell_qty - qty)
            
            if buyers[i][1] <= 0.01:
                i += 1
            if sellers[j][1] <= 0.01:
                j += 1
        
        return trades
```

**Deferred Options:**

- **Density-Dependent Mechanisms (Option B):** Large markets use Walrasian, small markets use posted-price
- **Posted-Price Markets:** Simpler mechanism for thin markets
- **Continuous Double Auction:** Order book with bid-ask spread

---

## Data Structures & Effects

### New Data Structures

```python
# src/vmt_engine/core/market.py

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..protocols.market.base import MarketMechanism

Position = tuple[int, int]


@dataclass
class MarketArea:
    """
    An emergent market formed by agent clustering.
    
    Unlike pre-defined MarketPosts, MarketAreas:
    - Form dynamically when agents cluster
    - May dissolve if density drops
    - Do not have fixed pre-determined locations
    """
    # Identity
    id: int
    center: Position  # Geometric center of cluster (may drift)
    radius: int  # Interaction radius
    
    # Current state
    participant_ids: list[int] = field(default_factory=list)
    
    # Market mechanism
    mechanism: Optional['MarketMechanism'] = None
    current_prices: dict[str, float] = field(default_factory=dict)
    
    # Lifecycle
    formation_tick: int = 0
    last_active_tick: int = 0
    ticks_below_threshold: int = 0
    
    # Statistics
    total_trades_executed: int = 0
    total_volume_traded: dict[str, float] = field(default_factory=dict)
    historical_prices: dict[str, list[tuple[int, float]]] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        """Is this market currently operating?"""
        return len(self.participant_ids) > 0
    
    @property
    def age(self) -> int:
        """Ticks since formation"""
        return self.last_active_tick - self.formation_tick
```

### Modified Trade Effect

Extend existing `Trade` effect to track market participation:

```python
# src/vmt_engine/protocols/base.py

@dataclass
class Trade(Effect):
    """
    Effect representing a completed trade.
    
    Extended to support both bilateral and market-based trades.
    """
    buyer_id: int
    seller_id: int
    commodity: str
    quantity: float
    price: float
    
    # New field (optional, backward compatible)
    market_id: Optional[int] = None  # None = bilateral trade, int = market trade
    
    @property
    def is_market_trade(self) -> bool:
        return self.market_id is not None
    
    @property
    def is_bilateral_trade(self) -> bool:
        return self.market_id is None
```

### New Effect: MarketLifecycle

```python
@dataclass
class MarketFormation(Effect):
    """Logged when a new market forms"""
    market_id: int
    center: Position
    tick: int
    num_participants: int


@dataclass
class MarketDissolution(Effect):
    """Logged when a market dissolves"""
    market_id: int
    tick: int
    age: int  # How long market existed
    reason: str  # "low_density", "timeout", etc.


@dataclass
class MarketClear(Effect):
    """
    Logged after market clearing.
    Does not modify state, only for telemetry.
    """
    market_id: int
    commodity: str
    price: float
    quantity: float
    tick: int
    num_participants: int
    converged: bool
```

---

## Modified TradeSystem Implementation

### Complete TradeSystem Class

```python
# src/vmt_engine/systems/trading.py

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
from collections import defaultdict
from ..protocols import (
    BargainingProtocol,
    Trade,
    Unpair,
    MarketClear,
    MarketFormation,
    MarketDissolution,
    build_trade_world_view,
)
from ..core.market import MarketArea
from ..protocols.market.walrasian import WalrasianAuctioneer
from .matching import execute_trade_generic

if TYPE_CHECKING:
    from ..simulation import Simulation
    from ..core import Agent


class TradeSystem:
    """
    Phase 4: Trade execution with emergent market formation.
    
    Responsibilities:
    1. Detect dense agent clusters and form/update markets
    2. Execute centralized clearing for market participants
    3. Execute bilateral trades for non-market agents
    4. Apply all trade effects
    5. Log trades and market events to telemetry
    """
    
    def __init__(self):
        self.bargaining_protocol: Optional[BargainingProtocol] = None
        
        # Market state (persists across ticks)
        self.active_markets: dict[int, MarketArea] = {}
        self.next_market_id: int = 0
        
        # Statistics
        self.market_formations: int = 0
        self.market_dissolutions: int = 0
    
    def execute(self, sim: "Simulation") -> None:
        """
        Execute Phase 4: Trade with emergent markets.
        
        Steps:
        1. Detect market areas (dense agent clusters)
        2. Assign agents to markets (exclusive)
        3. Unpair agents entering markets (clear bilateral pairing state)
        4. Process market trades (centralized clearing)
        5. Process bilateral trades (existing logic)
        6. Apply all effects
        """
        effects = []
        
        # ===== STEP 1: DETECT MARKETS =====
        markets = self._detect_market_areas(sim)
        
        # ===== STEP 2: ASSIGN AGENTS =====
        market_assignments = self._assign_agents_to_markets(markets, sim)
        market_participants = set()
        for agent_ids in market_assignments.values():
            market_participants.update(agent_ids)
        
        # ===== STEP 3: UNPAIR MARKET PARTICIPANTS =====
        # Agents entering markets should not also be in bilateral pairings
        for agent_id in market_participants:
            agent = sim.agent_by_id[agent_id]
            if agent.paired_with_id is not None:
                # Unpair both agents
                partner = sim.agent_by_id[agent.paired_with_id]
                agent.paired_with_id = None
                partner.paired_with_id = None
        
        # ===== STEP 4: PROCESS MARKET TRADES =====
        for market in sorted(markets, key=lambda m: m.id):
            if market.id not in market_assignments:
                continue
            
            participant_ids = market_assignments[market.id]
            if len(participant_ids) == 0:
                continue
            
            # Update market participant list
            market.participant_ids = participant_ids
            
            # Execute clearing mechanism
            if market.mechanism is None:
                market.mechanism = self._create_mechanism(sim)
            
            market_effects = market.mechanism.execute(market, sim)
            effects.extend(market_effects)
        
        # ===== STEP 5: PROCESS BILATERAL TRADES =====
        processed_pairs = set()
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            # Skip market participants
            if agent.id in market_participants:
                continue
            
            if agent.paired_with_id is None:
                continue
            
            # Skip if pair already processed
            pair_key = tuple(sorted([agent.id, agent.paired_with_id]))
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)
            
            # Skip if partner is in a market
            if agent.paired_with_id in market_participants:
                continue
            
            partner = sim.agent_by_id[agent.paired_with_id]
            
            # Check distance
            distance = abs(agent.pos[0] - partner.pos[0]) + abs(agent.pos[1] - partner.pos[1])
            
            if distance <= sim.params["interaction_radius"]:
                # Within range: attempt bilateral trade
                bilateral_effects = self._negotiate_trade(agent, partner, sim)
                effects.extend(bilateral_effects)
        
        # ===== STEP 6: APPLY EFFECTS =====
        self._apply_all_effects(effects, sim)
    
    def _detect_market_areas(self, sim: 'Simulation') -> list[MarketArea]:
        """
        Detect dense agent clusters that qualify as markets.
        
        Implementation: Grid-based clustering (Option A)
        """
        formation_threshold = sim.params.get('market_formation_threshold', 5)
        dissolution_threshold = sim.params.get('market_dissolution_threshold', 3)
        dissolution_patience = sim.params.get('market_dissolution_patience', 5)
        interaction_radius = sim.params['interaction_radius']
        
        markets_this_tick: dict[Position, MarketArea] = {}
        assigned_agents: set[int] = set()
        
        # Scan for clusters
        for agent in sorted(sim.agents, key=lambda a: a.id):
            if agent.id in assigned_agents:
                continue
            
            # Find nearby agents
            nearby = self._find_agents_within_radius(
                agent.pos,
                interaction_radius,
                sim
            )
            
            if len(nearby) >= formation_threshold:
                # Compute cluster center
                center = self._compute_cluster_center(nearby)
                
                # Find or create market
                market = self._find_or_create_market(center, sim)
                market.participant_ids = [a.id for a in nearby]
                market.last_active_tick = sim.tick
                market.ticks_below_threshold = 0
                
                markets_this_tick[center] = market
                assigned_agents.update(market.participant_ids)
        
        # Update existing markets not seen this tick
        self._update_inactive_markets(markets_this_tick, sim, 
                                       dissolution_threshold, dissolution_patience)
        
        return list(self.active_markets.values())
    
    def _find_agents_within_radius(self, center: Position, radius: int,
                                   sim: 'Simulation') -> list['Agent']:
        """Return all agents within Manhattan distance <= radius"""
        nearby = []
        for agent in sim.agents:
            dist = abs(agent.pos[0] - center[0]) + abs(agent.pos[1] - center[1])
            if dist <= radius:
                nearby.append(agent)
        return sorted(nearby, key=lambda a: a.id)
    
    def _compute_cluster_center(self, agents: list['Agent']) -> Position:
        """Compute geometric center of cluster"""
        if not agents:
            return (0, 0)
        
        avg_x = sum(a.pos[0] for a in agents) / len(agents)
        avg_y = sum(a.pos[1] for a in agents) / len(agents)
        
        return (round(avg_x), round(avg_y))
    
    def _find_or_create_market(self, center: Position, 
                               sim: 'Simulation') -> MarketArea:
        """
        Check if market exists near this location (reuse ID and prices).
        Otherwise create new market.
        """
        # Check existing markets
        for market in self.active_markets.values():
            dist = abs(market.center[0] - center[0]) + abs(market.center[1] - center[1])
            if dist <= 2:  # Within 2 cells = same market
                market.center = center  # Update center
                return market
        
        # Create new market
        market_id = self.next_market_id
        self.next_market_id += 1
        
        market = MarketArea(
            id=market_id,
            center=center,
            radius=sim.params['interaction_radius'],
            formation_tick=sim.tick
        )
        
        self.active_markets[market_id] = market
        self.market_formations += 1
        
        # Log formation event
        sim.telemetry.log_market_formation(market, sim.tick)
        print(f"Market {market_id} formed at {center} on tick {sim.tick}")
        
        return market
    
    def _update_inactive_markets(self, active_centers: dict[Position, MarketArea],
                                 sim: 'Simulation',
                                 dissolution_threshold: int,
                                 dissolution_patience: int) -> None:
        """Update markets not found this tick; dissolve if necessary"""
        to_dissolve = []
        
        for market_id, market in self.active_markets.items():
            if market.center not in active_centers:
                # Market didn't form this tick
                market.participant_ids = []
                market.ticks_below_threshold += 1
                
                if market.ticks_below_threshold >= dissolution_patience:
                    to_dissolve.append(market_id)
        
        # Dissolve markets
        for market_id in to_dissolve:
            market = self.active_markets[market_id]
            
            sim.telemetry.log_market_dissolution(market, sim.tick)
            print(f"Market {market_id} dissolved at tick {sim.tick} "
                  f"(existed for {market.age} ticks)")
            
            del self.active_markets[market_id]
            self.market_dissolutions += 1
    
    def _assign_agents_to_markets(self, markets: list[MarketArea],
                                   sim: 'Simulation') -> dict[int, list[int]]:
        """
        Assign each agent to at most one market.
        Priority: largest market > closest market > lowest ID
        """
        assignment: dict[int, list[int]] = {m.id: [] for m in markets}
        assigned_agents: set[int] = set()
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            if agent.id in assigned_agents:
                continue
            
            # Find eligible markets
            eligible = []
            for market in markets:
                dist = abs(agent.pos[0] - market.center[0]) + abs(agent.pos[1] - market.center[1])
                if dist <= market.radius:
                    eligible.append((market, dist))
            
            if not eligible:
                continue
            
            # Sort by priority
            eligible.sort(key=lambda x: (
                -len(x[0].participant_ids),  # Largest first
                x[1],  # Closest first
                x[0].id  # Lowest ID first
            ))
            
            chosen_market = eligible[0][0]
            assignment[chosen_market.id].append(agent.id)
            assigned_agents.add(agent.id)
        
        return assignment
    
    def _create_mechanism(self, sim: 'Simulation') -> 'MarketMechanism':
        """Instantiate market clearing mechanism"""
        mechanism_type = sim.params.get('market_mechanism', 'walrasian')
        
        if mechanism_type == "walrasian":
            return WalrasianAuctioneer(
                adjustment_speed=sim.params.get('walrasian_adjustment_speed', 0.1),
                tolerance=sim.params.get('walrasian_tolerance', 0.01),
                max_iterations=sim.params.get('walrasian_max_iterations', 100)
            )
        else:
            raise ValueError(f"Unknown market mechanism: {mechanism_type}")
    
    def _negotiate_trade(self, agent_a: "Agent", agent_b: "Agent",
                        sim: "Simulation") -> list['Effect']:
        """
        Execute bilateral trade negotiation (existing logic).
        
        Returns list of Trade or Unpair effects.
        """
        if self.bargaining_protocol is None:
            # Fallback to legacy trade logic
            world_view = build_trade_world_view(agent_a, agent_b, sim)
            # ... existing bilateral trade logic ...
            return []
        
        # Use protocol-based bargaining
        world_view = build_trade_world_view(agent_a, agent_b, sim)
        effects = self.bargaining_protocol.execute(world_view)
        return effects
    
    def _apply_all_effects(self, effects: list['Effect'], sim: 'Simulation') -> None:
        """Apply all trade effects and log to telemetry"""
        for effect in effects:
            if isinstance(effect, Trade):
                self._apply_trade(effect, sim)
            elif isinstance(effect, Unpair):
                self._apply_unpair(effect, sim)
            elif isinstance(effect, MarketClear):
                sim.telemetry.log_market_clear(effect)
            # MarketFormation/Dissolution already logged in detection phase
    
    def _apply_trade(self, trade: Trade, sim: 'Simulation') -> None:
        """Apply trade effect: update inventories, log to telemetry"""
        buyer = sim.agent_by_id[trade.buyer_id]
        seller = sim.agent_by_id[trade.seller_id]
        
        # Update inventories
        buyer.inventory[trade.commodity] = buyer.inventory.get(trade.commodity, 0) + trade.quantity
        buyer.inventory['M'] = buyer.inventory.get('M', 0) - (trade.price * trade.quantity)
        
        seller.inventory[trade.commodity] = seller.inventory.get(trade.commodity, 0) - trade.quantity
        seller.inventory['M'] = seller.inventory.get('M', 0) + (trade.price * trade.quantity)
        
        # Mark inventory changed
        buyer.inventory_changed = True
        seller.inventory_changed = True
        
        # Log to telemetry
        sim.telemetry.log_trade(trade, sim.tick)
        
        # Unpair agents (trade complete)
        buyer.paired_with_id = None
        seller.paired_with_id = None
    
    def _apply_unpair(self, unpair: Unpair, sim: 'Simulation') -> None:
        """Apply unpair effect: break pairing"""
        agent_a = sim.agent_by_id[unpair.agent_a_id]
        agent_b = sim.agent_by_id[unpair.agent_b_id]
        
        agent_a.paired_with_id = None
        agent_b.paired_with_id = None
```

---

## Telemetry Extensions

### New Database Tables

```sql
-- Market lifecycle tracking
CREATE TABLE IF NOT EXISTS market_formations (
    market_id INTEGER,
    center_x INTEGER,
    center_y INTEGER,
    formation_tick INTEGER,
    num_participants INTEGER,
    PRIMARY KEY (market_id)
);

CREATE TABLE IF NOT EXISTS market_dissolutions (
    market_id INTEGER,
    dissolution_tick INTEGER,
    age INTEGER,  -- Ticks market existed
    reason TEXT,
    PRIMARY KEY (market_id, dissolution_tick)
);

-- Market clearing events (extended from previous spec)
CREATE TABLE IF NOT EXISTS market_clears (
    tick INTEGER,
    market_id INTEGER,
    commodity TEXT,
    clearing_price REAL,
    quantity_traded REAL,
    num_participants INTEGER,
    converged INTEGER,  -- 1 if tatonnement converged
    PRIMARY KEY (tick, market_id, commodity)
);

-- Market snapshots (periodic state dumps)
CREATE TABLE IF NOT EXISTS market_snapshots (
    tick INTEGER,
    market_id INTEGER,
    center_x INTEGER,
    center_y INTEGER,
    num_participants INTEGER,
    age INTEGER,
    total_trades INTEGER,
    PRIMARY KEY (tick, market_id)
);

-- Trade table extension: add market_id column
ALTER TABLE trades ADD COLUMN market_id INTEGER DEFAULT NULL;
-- NULL = bilateral trade, integer = market trade
```

### Telemetry Logging Methods

```python
# src/telemetry/db_loggers.py

def log_market_formation(self, market: MarketArea, tick: int):
    """Log market formation event"""
    self.conn.execute("""
        INSERT INTO market_formations
        (market_id, center_x, center_y, formation_tick, num_participants)
        VALUES (?, ?, ?, ?, ?)
    """, (
        market.id,
        market.center[0],
        market.center[1],
        tick,
        len(market.participant_ids)
    ))
    self.conn.commit()


def log_market_dissolution(self, market: MarketArea, tick: int):
    """Log market dissolution event"""
    self.conn.execute("""
        INSERT INTO market_dissolutions
        (market_id, dissolution_tick, age, reason)
        VALUES (?, ?, ?, ?)
    """, (
        market.id,
        tick,
        tick - market.formation_tick,
        "low_density"
    ))
    self.conn.commit()


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
        1 if effect.converged else 0
    ))
    self.conn.commit()


def log_market_snapshot(self, market: MarketArea, tick: int):
    """
    Log periodic market state snapshot.
    Called every N ticks for analysis.
    """
    self.conn.execute("""
        INSERT OR REPLACE INTO market_snapshots
        (tick, market_id, center_x, center_y, num_participants, age, total_trades)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        tick,
        market.id,
        market.center[0],
        market.center[1],
        len(market.participant_ids),
        tick - market.formation_tick,
        market.total_trades_executed
    ))
    self.conn.commit()
```

---

## Visualization

### Pygame Rendering Extensions

```python
# src/vmt_pygame/renderer.py

def render_market_areas(self, screen, sim):
    """
    Render emergent market areas on grid.
    Markets shown as semi-transparent yellow overlays.
    """
    for market in sim.trade_system.active_markets.values():
        # Determine color intensity based on market activity
        base_alpha = 80
        activity_alpha = min(100, market.total_trades_executed * 2)
        alpha = base_alpha + activity_alpha
        
        # Draw market area cells
        for dx in range(-market.radius, market.radius + 1):
            for dy in range(-market.radius, market.radius + 1):
                x = market.center[0] + dx
                y = market.center[1] + dy
                
                # Check Manhattan distance
                if abs(dx) + abs(dy) <= market.radius:
                    if 0 <= x < sim.grid.N and 0 <= y < sim.grid.N:
                        screen_pos = self._grid_to_screen((x, y))
                        
                        # Draw semi-transparent yellow overlay
                        surf = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                        surf.fill((255, 255, 100, alpha))
                        screen.blit(surf, screen_pos)
        
        # Draw market center marker
        center_screen = self._grid_to_screen(market.center)
        pygame.draw.circle(screen, (255, 200, 0), center_screen, 8, 3)
        
        # Draw market ID
        id_text = self.small_font.render(f"M{market.id}", True, (0, 0, 0))
        screen.blit(id_text, (center_screen[0] - 10, center_screen[1] - 20))
        
        # Draw price info
        if market.current_prices:
            price_text = " ".join(f"{k}:{v:.1f}" for k, v in market.current_prices.items())
            text = self.small_font.render(price_text, True, (0, 0, 0))
            screen.blit(text, (center_screen[0] + 10, center_screen[1] + 10))


def render_agent_market_participation(self, screen, sim):
    """
    Highlight agents participating in markets.
    Draw subtle connection lines from agents to market centers.
    """
    for market in sim.trade_system.active_markets.values():
        for agent_id in market.participant_ids:
            agent = sim.agent_by_id[agent_id]
            
            agent_screen = self._grid_to_screen(agent.pos)
            market_screen = self._grid_to_screen(market.center)
            
            # Draw dashed line
            pygame.draw.line(screen, (200, 200, 0), agent_screen, market_screen, 1)
            
            # Add glow to agent
            pygame.draw.circle(screen, (255, 255, 150), agent_screen, 6, 2)
```

---

## Scenario Configuration

### YAML Schema Extension

```yaml
# Example: emergent_market_demo.yaml

name: "Emergent Market Formation Demo"
description: "Markets form dynamically where agents cluster"

grid:
  width: 40
  height: 40

params:
  ticks: 200
  
  # Market formation parameters (NEW)
  market_formation_threshold: 5     # Min agents to form market
  market_dissolution_threshold: 3   # Min agents to sustain market
  market_dissolution_patience: 5    # Ticks below threshold before dissolving
  market_mechanism: "walrasian"     # Clearing algorithm
  
  # Walrasian mechanism parameters (NEW)
  walrasian_adjustment_speed: 0.1
  walrasian_tolerance: 0.01
  walrasian_max_iterations: 100
  
  # Existing parameters
  interaction_radius: 3
  vision_radius: 10
  move_budget_per_tick: 2
  # ...

agents:
  - count: 20
    utility_type: "cobb_douglas"
    utility_params:
      alpha_A: 0.6
      alpha_B: 0.4
    endowment:
      A: 10.0
      B: 5.0
      M: 50.0
    spawn_region: [5, 5, 35, 35]

resources:
  # Resource cluster A (west side)
  - commodity: "A"
    count: 10
    spawn_region: [5, 15, 15, 25]
    regeneration_rate: 0.2
  
  # Resource cluster B (east side)
  - commodity: "B"
    count: 10
    spawn_region: [25, 15, 35, 25]
    regeneration_rate: 0.2

# Expected behavior:
# - Agents cluster near resource patches
# - Markets form at these clusters
# - Prices differ between markets initially
# - Agents may migrate between markets (arbitrage)
# - Markets may dissolve if resources deplete
```

### Loading Markets from Scenario

```python
# src/scenarios/loader.py

def load_scenario(yaml_path: str) -> Scenario:
    """Load scenario from YAML file"""
    with open(yaml_path) as f:
        config = yaml.safe_load(f)
    
    # ... existing loading logic ...
    
    # Market parameters
    market_params = {
        'market_formation_threshold': config['params'].get('market_formation_threshold', 5),
        'market_dissolution_threshold': config['params'].get('market_dissolution_threshold', 3),
        'market_dissolution_patience': config['params'].get('market_dissolution_patience', 5),
        'market_mechanism': config['params'].get('market_mechanism', 'walrasian'),
        'walrasian_adjustment_speed': config['params'].get('walrasian_adjustment_speed', 0.1),
        'walrasian_tolerance': config['params'].get('walrasian_tolerance', 0.01),
        'walrasian_max_iterations': config['params'].get('walrasian_max_iterations', 100),
    }
    
    scenario.params.update(market_params)
    
    return scenario
```

---

## Implementation Plan: 4 Weeks, ~32 Hours

### Week 1: Core Market Detection (8 hours)

**Goal:** Markets can form and dissolve based on agent density

**Tasks:**
1. Create `MarketArea` dataclass in `src/vmt_engine/core/market.py`
2. Add `active_markets` dict to `TradeSystem`
3. Implement `_detect_market_areas()` method
4. Implement `_find_agents_within_radius()` helper
5. Implement `_find_or_create_market()` with location-based identity
6. Implement `_update_inactive_markets()` with dissolution logic
7. Add console logging for market formation/dissolution events

**Tests:**
```python
def test_market_forms_at_threshold():
    """Market forms when 5+ agents cluster"""
    # Place 5 agents within interaction_radius=3
    # Run 1 tick
    # Assert: 1 market exists

def test_market_does_not_form_below_threshold():
    """No market when only 4 agents cluster"""
    # Place 4 agents within interaction_radius
    # Run 1 tick
    # Assert: 0 markets exist

def test_market_persists_across_ticks():
    """Market maintains identity if agents remain"""
    # Form market at tick 0
    # Agents stay clustered for ticks 1-10
    # Assert: Same market ID persists

def test_market_dissolves_after_patience():
    """Market dissolves after falling below threshold for patience ticks"""
    # Form market
    # Agents disperse (density drops to 2)
    # Wait market_dissolution_patience ticks
    # Assert: Market dissolved

def test_location_based_market_identity():
    """Market reuses ID if formed near previous location"""
    # Form market at (10, 10)
    # Market dissolves
    # Cluster forms at (11, 11) (within 2 cells)
    # Assert: Same market ID reused
```

**Milestone:** Markets form and dissolve; console logs confirm lifecycle events.

---

### Week 2: Market Clearing Integration (10 hours)

**Goal:** Markets execute centralized trades; bilateral trades continue for non-market agents

**Tasks:**
1. Implement `_assign_agents_to_markets()` with priority logic
2. Create `WalrasianAuctioneer` mechanism
   - `execute()` main entry point
   - `_find_clearing_price()` tatonnement
   - `_compute_demand()` and `_compute_supply()`
   - `_execute_at_price()` matching
3. Modify TradeSystem.execute() to:
   - Call market detection
   - Process market trades first
   - Process bilateral trades for remaining agents
4. Extend `Trade` effect with `market_id` field
5. Create `MarketClear`, `MarketFormation`, `MarketDissolution` effects

**Tests:**
```python
def test_market_clearing_single_commodity():
    """Walrasian clears market for one commodity"""
    # 3 buyers, 3 sellers in market
    # Run market clearing
    # Assert: Trades executed at equilibrium price

def test_tatonnement_convergence():
    """Tatonnement finds equilibrium within max_iterations"""
    # Setup agents with known demand/supply curves
    # Run clearing
    # Assert: Excess demand < tolerance

def test_tatonnement_non_convergence():
    """Graceful failure when no equilibrium exists"""
    # Setup pathological case (no overlap)
    # Run clearing
    # Assert: Warning printed, no trades

def test_market_vs_bilateral_coexistence():
    """Markets and bilateral trades occur simultaneously"""
    # 6 agents: 5 in market cluster, 1 paired bilaterally
    # Run trade phase
    # Assert: Market trades recorded with market_id
    # Assert: Bilateral trade recorded with market_id=None

def test_exclusive_agent_assignment():
    """Agent in multiple market ranges chooses largest"""
    # 2 markets overlap
    # Market A: 8 participants, Market B: 4 participants
    # Agent equidistant from both
    # Assert: Agent assigned to Market A
```

**Milestone:** Markets clear trades; bilateral trades continue; telemetry distinguishes market vs bilateral trades.

---

### Week 3: Telemetry & Visualization (8 hours)

**Goal:** Market events logged; visual indicators on grid

**Tasks:**
1. Add database tables:
   - `market_formations`
   - `market_dissolutions`
   - `market_clears`
   - `market_snapshots`
   - Extend `trades` table with `market_id` column
2. Implement telemetry logging methods
3. Add Pygame rendering:
   - `render_market_areas()` - yellow overlays
   - `render_agent_market_participation()` - connection lines
   - Market center markers with ID labels
   - Price displays
4. Create analysis script `scripts/analyze_emergent_markets.py`:
   - Plot market lifespans
   - Plot price convergence within markets
   - Plot spatial market distribution over time

**Tests:**
```python
def test_market_formation_logged():
    """Formation events recorded in telemetry"""
    # Run scenario until market forms
    # Query market_formations table
    # Assert: 1 row with correct tick, location

def test_market_clearing_logged():
    """Clearing events recorded"""
    # Run market clearing
    # Query market_clears table
    # Assert: Rows for each commodity with prices

def test_trade_market_id_tagged():
    """Market trades have market_id set"""
    # Execute market trade
    # Query trades table
    # Assert: market_id = expected market ID

def test_bilateral_trade_untagged():
    """Bilateral trades have market_id = NULL"""
    # Execute bilateral trade
    # Query trades table
    # Assert: market_id IS NULL
```

**Milestone:** Complete telemetry tracking; visual feedback on grid; analysis script generates plots.

---

### Week 4: Scenarios & Refinement (6 hours)

**Goal:** Demonstrate emergent markets in realistic scenarios; documentation

**Tasks:**
1. Create demonstration scenarios:
   - `scenarios/demos/emergent_market_basic.yaml` - single resource cluster
   - `scenarios/demos/emergent_market_multi.yaml` - two resource clusters
   - `scenarios/demos/emergent_market_nomadic.yaml` - agents migrate between clusters
2. Run experiments:
   - Vary `market_formation_threshold` (3, 5, 7, 10)
   - Vary resource clustering (tight vs dispersed)
   - Measure efficiency (total utility) vs bilateral-only baseline
3. Update documentation:
   - `docs/2_technical_manual.md` - add emergent markets section
   - `docs/markets_guide.md` - pedagogical guide for students
   - README examples
4. Verify correctness:
   - Markets form at expected locations
   - Prices converge as expected
   - No determinism violations

**Tests:**
```python
def test_market_at_resource_cluster():
    """Markets form near resource-rich areas"""
    # Dense resource cluster at (20, 20)
    # Run 50 ticks
    # Assert: Market forms near (20, 20)

def test_multiple_markets_coexist():
    """Two resource clusters create two markets"""
    # Cluster A at (10, 10), Cluster B at (30, 30)
    # Run 100 ticks
    # Assert: 2 markets exist
    # Assert: Markets have different IDs

def test_price_convergence_over_time():
    """Prices stabilize as market persists"""
    # Run 100 ticks
    # Query price history for persistent market
    # Assert: Price variance decreases over time

def test_efficiency_gain_vs_bilateral():
    """Markets improve welfare compared to bilateral-only"""
    # Run scenario with markets
    # Run identical scenario with bilateral-only (threshold=999)
    # Compare total utility
    # Assert: Market scenario has higher utility
```

**Milestone:** Compelling demonstrations; documented for pedagogical use; performance acceptable.

---

## Determinism Checklist

Endogenous markets introduce new sources of potential non-determinism:

### Critical Determinism Requirements

1. **Agent Scanning Order:** `sorted(sim.agents, key=lambda a: a.id)`
2. **Market ID Assignment:** Sequential, deterministic
3. **Cluster Center Calculation:** Deterministic (no float accumulation issues)
4. **Agent-to-Market Assignment:** Deterministic tie-breaking (largest → closest → lowest ID)
5. **Market Processing Order:** `sorted(markets, key=lambda m: m.id)`
6. **Tatonnement:** Deterministic convergence (no randomness)
7. **Trade Pairing:** Sorted by agent ID before matching

### Verification

Run `scripts/compare_telemetry_snapshots.py` with same seed:
```bash
bash -c "source venv/bin/activate && python scripts/compare_telemetry_snapshots.py \
    scenarios/demos/emergent_market_basic.yaml --seed 42 --runs 2"
```

Assert: Byte-for-byte identical telemetry databases.

---

## Deferred Extensions

### Performance Optimization (After Functionality Verified)

**Critical:** Performance optimization is **not a priority** during initial implementation. Focus is on correctness and functionality. Only after markets are working correctly should we consider:

1. **Spatial Indexing** - Grid-based lookup to avoid O(N²) distance calculations
2. **Incremental Market Updates** - Track agent movements to update markets incrementally
3. **Caching** - Cache marginal utility calculations within a tick
4. **Profiling** - Identify actual bottlenecks before optimizing
5. **Parallel Market Clearing** - Process independent markets in parallel

### Economic Extensions

1. **Market Entry Costs** - Agents pay fee to participate in market
2. **Trader Specialization** - Some agents become market makers
3. **Information Diffusion** - Agents learn about distant markets from neighbors
4. **Intertemporal Arbitrage** - Agents hold inventory speculatively
5. **Strategic Market Choice** - Agents forecast prices before committing to market
6. **Market-Aware Matching** - Phase 2 MatchingProtocol skips pairing in high-density areas

### Algorithmic Extensions

1. **DBSCAN Clustering (Option B)** - More sophisticated cluster detection
2. **Voronoi Catchment (Option C)** - Partition grid into market territories
3. **Overlapping Markets (Approach B)** - Agents split orders across markets
4. **Density-Dependent Mechanisms (Option B)** - Thick markets use Walrasian, thin use posted-price

### Mechanism Extensions

1. **Posted-Price Markets** - Simpler mechanism for thin markets
2. **Continuous Double Auction** - Order book with bid-ask spread
3. **Periodic Clearing** - Markets clear every N ticks, not every tick
4. **Two-Sided Auctions** - Buyers and sellers submit sealed bids

### Institutional Extensions

1. **Market Hours** - Markets only operate certain ticks
2. **Market Regulations** - Price floors, ceilings, taxes
3. **Market Hierarchy** - Large central market + small satellite markets
4. **Market Fragmentation** - Competing markets with different rules

---

## Success Criteria

### Week 1 Complete When:
- [ ] Markets form at density threshold
- [ ] Markets dissolve after patience period
- [ ] Location-based identity works
- [ ] Console logs show lifecycle events
- [ ] All unit tests pass

### Week 2 Complete When:
- [ ] Walrasian mechanism clears markets
- [ ] Market and bilateral trades coexist
- [ ] Tatonnement converges reliably
- [ ] Trade effects tagged with market_id
- [ ] All integration tests pass

### Week 3 Complete When:
- [ ] Telemetry captures all market events
- [ ] Pygame displays market areas
- [ ] Analysis script generates plots
- [ ] Price convergence observable
- [ ] All telemetry tests pass

### Week 4 Complete When:
- [ ] Demonstration scenarios run
- [ ] Documentation updated
- [ ] Markets form at expected locations (near resource clusters)
- [ ] Efficiency gains measurable vs bilateral-only
- [ ] All scenario tests pass

### Overall Success When:
- [ ] Determinism verified (same seed → identical results)
- [ ] Markets emerge at natural gathering points
- [ ] Price convergence visible in telemetry
- [ ] Pedagogically compelling demonstrations
- [ ] Ready for classroom use

---

## Key Differences from Pre-Defined Markets

| Aspect | Pre-Defined Markets | Endogenous Markets |
|--------|---------------------|-------------------|
| **Location** | Fixed in YAML | Emerges from agent behavior |
| **Existence** | Guaranteed | Conditional on density |
| **Lifecycle** | Permanent | Dynamic (form/dissolve) |
| **Count** | Designer choice | Emergent |
| **Pedagogy** | Market mechanics | Market emergence + mechanics |
| **Config** | Explicit placement | Threshold parameters |
| **Visualization** | Static markers | Dynamic overlays |
| **Research Questions** | "How do markets work?" | "When/where do markets form?" |

Endogenous markets are **pedagogically superior** for teaching market emergence but **slightly more complex** to implement. The additional complexity is justified by the richer insights students gain.

---

## References

### Economic Theory

1. **Christaller, W. (1933)** - Central Place Theory: market thresholds and spatial catchment
2. **Fujita, M., Krugman, P., Venables, A. (1999)** - The Spatial Economy: agglomeration and market formation
3. **Kirzner, I. (1973)** - Competition and Entrepreneurship: market discovery and arbitrage
4. **Walras, L. (1874)** - Elements of Pure Economics: tatonnement price adjustment

### Agent-Based Modeling

1. **Axtell, R. (2005)** - "The Complexity of Exchange": emergent market structures in ABMs
2. **Tesfatsion, L. (2006)** - "Agent-Based Computational Economics": market mechanisms in simulations
3. **Gode, D. & Sunder, S. (1993)** - "Allocative Efficiency of Markets with Zero-Intelligence Traders"

### Economic Geography

1. **Hotelling, H. (1929)** - "Stability in Competition": spatial competition and market location
2. **Krugman, P. (1991)** - "Increasing Returns and Economic Geography": agglomeration forces

---

## Appendix: Comparison with Original Blueprint

### What Changed

1. **Market Location:** Fixed → Emergent from density
2. **Market Count:** Pre-specified → Endogenous
3. **Market Lifecycle:** Permanent → Form/dissolve dynamically
4. **Agent Target Selection:** Markets in SearchProtocol → Implicit (agents don't "choose" markets)
5. **Phase Structure:** New market phase → Integrated into existing Phase 4
6. **Configuration:** YAML market_posts section → Threshold parameters

### What Stayed the Same

1. **Mechanism Types:** Walrasian, Posted-Price, CDA (same implementations)
2. **Spatial Grounding:** Physical proximity required
3. **Determinism:** Fully reproducible
4. **Coexistence:** Markets + bilateral trades
5. **Telemetry:** Similar schema (extended, not replaced)
6. **Effects:** Trade, MarketClear, etc. (same types)

### Why This Approach is Better

1. **Pedagogical:** Students see markets emerge, not just operate
2. **Realistic:** Matches historical market formation patterns
3. **Flexible:** Can simulate both pre-modern (emergent) and modern (fixed) markets
4. **Research-Oriented:** Market formation becomes an output, not an input
5. **Simpler Config:** No need to pre-place markets in YAML

---

## Revision History

### Version 1.1 (October 29, 2025) - Post-Review Revisions

**Changes based on design review feedback:**

1. **Fixed Agent/Utility API Usage**
   - Corrected `agent.inventory` access: `.A`, `.B`, `.M` (not dict-like `.get()`)
   - Corrected marginal utility calls: `agent.utility.mu_A(A, B)`, `agent.utility.mu_B(A, B)`
   - Added commodity-specific handling in demand/supply calculations
   - Added note about simplified demand model (full optimization deferred)

2. **Added Agent Unpair Logic**
   - Step 3 in Phase 4: Unpair agents when entering markets
   - Prevents agents from being in both bilateral pairing and market states
   - Added note about MatchingProtocol interaction in Phase 2
   - Documented future enhancement: market-aware matching in Phase 2

3. **Removed Performance Concerns**
   - Eliminated performance optimization from Week 1-4 tasks
   - Added dedicated "Performance Optimization" section to Deferred Extensions
   - Changed Week 4 focus from "performance tuning" to "correctness verification"
   - Emphasized: correctness first, performance later

4. **Added Design Decisions Summary**
   - Created "Core Design Decisions (Finalized)" section at top
   - Documents all 7 key decisions for quick reference
   - Makes specification more actionable

5. **Documentation Improvements**
   - Added "Phase Interactions" section explaining Phase 2/4 coordination
   - Clarified market center drift (±2 cells) is acceptable
   - Documented hysteresis gap (5 to form, 3 to sustain) as acceptable
   - Fixed typo in code example (removed errant 'i' character)

**Key Takeaway:** Focus on getting functionality working first. Performance and sophistication can be added incrementally after core mechanics are verified.

---

**Document Version:** 1.1  
**Last Updated:** October 29, 2025  
**Author:** CMF  
**Status:** Ready for Implementation  
**Next Step:** Begin Week 1 implementation

