# Phase 2a Quick Start Guide
**Quick Wins: 3 Simple Protocols for Architecture Validation**

**Status:** Ready to implement  
**Duration:** 8-10 hours (1 week)  
**Goal:** Validate protocol architecture end-to-end

---

## Overview

Implement 3 simple protocols (one per category) to prove the protocol system works:

1. **Random Walk Search** - Stochastic exploration baseline
2. **Random Matching** - Random pairing baseline
3. **Split-The-Difference Bargaining** - Fair division baseline

Each is ~2-4 hours of work with straightforward logic.

---

## Protocol 1: Random Walk Search

### Implementation Checklist

**File:** `src/vmt_engine/protocols/search/random_walk.py`

```python
from src.vmt_engine.protocols.base import SearchProtocol, Effect, SetTarget
from src.vmt_engine.protocols.context import WorldView
import random

class RandomWalkSearch(SearchProtocol):
    """Stochastic exploration for baseline comparison."""
    
    name = "random_walk"
    version = "2025.10.27"
    
    def build_preferences(self, world: WorldView) -> list[tuple]:
        """Randomly rank visible targets."""
        visible = world.visible_agents + world.visible_resources
        if not visible:
            return []
        
        # Shuffle using deterministic RNG from world
        shuffled = list(visible)
        world.rng_stream.shuffle(shuffled)
        
        # Return as preferences (all with same score)
        return [(target, 0.0, {}) for target in shuffled]
    
    def select_target(self, world: WorldView) -> list[Effect]:
        """Select random target from preferences."""
        prefs = self.build_preferences(world)
        if not prefs:
            return []
        
        # Select first (random due to shuffle)
        target = prefs[0][0]
        
        return [SetTarget(
            protocol_name=self.name,
            tick=world.tick,
            agent_id=world.agent_id,
            target=target
        )]
```

### Tests

**File:** `tests/test_protocols_random_walk.py`

```python
def test_random_walk_deterministic():
    """Same seed produces same sequence."""
    results = []
    for _ in range(2):
        sim = Simulation(scenario, seed=42)
        sim.search_protocol = RandomWalkSearch()
        sim.run(10)
        results.append(get_agent_positions(sim))
    
    assert results[0] == results[1]

def test_random_walk_different_seeds():
    """Different seeds produce different paths."""
    results = []
    for seed in [42, 43]:
        sim = Simulation(scenario, seed=seed)
        sim.search_protocol = RandomWalkSearch()
        sim.run(10)
        results.append(get_agent_positions(sim))
    
    assert results[0] != results[1]

def test_random_walk_vs_legacy():
    """Random walk less efficient than legacy."""
    # Run both protocols
    sim_random = run_with_protocol(RandomWalkSearch(), seed=42)
    sim_legacy = run_with_protocol(LegacySearchProtocol(), seed=42)
    
    # Random walk should result in lower total surplus
    assert total_surplus(sim_legacy) > total_surplus(sim_random)
```

### Comparison Scenario

**File:** `scenarios/comparison_search_protocols.yaml`

```yaml
# Compare Random Walk vs Legacy Search
grid_size: 30
agent_count: 10
max_steps: 100
seed: 42

initial_inventories:
  A: [5, 0, 5, 0, 5, 0, 5, 0, 5, 0]
  B: [0, 5, 0, 5, 0, 5, 0, 5, 0, 5]

utilities:
  type: CES
  params: {rho: 0.5, w_A: 0.5, w_B: 0.5}

# Run with:
# 1. python main.py scenarios/comparison_search_protocols.yaml --search-protocol random_walk
# 2. python main.py scenarios/comparison_search_protocols.yaml --search-protocol legacy
```

**Effort:** 2-3 hours

---

## Protocol 2: Random Matching

### Implementation Checklist

**File:** `src/vmt_engine/protocols/matching/random.py`

```python
from src.vmt_engine.protocols.base import MatchingProtocol, Effect, Pair
from src.vmt_engine.protocols.context import WorldView

class RandomMatching(MatchingProtocol):
    """Random pairing for null hypothesis."""
    
    name = "random"
    version = "2025.10.27"
    
    def find_matches(
        self, 
        preferences: dict[int, list], 
        world: WorldView
    ) -> list[Effect]:
        """Randomly pair agents wanting to trade."""
        
        # Collect agents wanting to trade
        trade_seekers = [
            agent_id for agent_id, prefs in preferences.items()
            if prefs and is_trade_target(prefs[0])
        ]
        
        if len(trade_seekers) < 2:
            return []
        
        # Shuffle deterministically
        shuffled = list(trade_seekers)
        world.rng_stream.shuffle(shuffled)
        
        # Pair sequentially
        effects = []
        for i in range(0, len(shuffled) - 1, 2):
            agent_a = shuffled[i]
            agent_b = shuffled[i + 1]
            
            # Check basic feasibility
            if is_valid_pair(agent_a, agent_b, world):
                effects.append(Pair(
                    protocol_name=self.name,
                    tick=world.tick,
                    agent_a=agent_a,
                    agent_b=agent_b,
                    reason="random"
                ))
        
        return effects
```

### Tests

**File:** `tests/test_protocols_random_matching.py`

```python
def test_random_matching_deterministic():
    """Same seed produces same pairs."""
    pairs = []
    for _ in range(2):
        sim = Simulation(scenario, seed=42)
        sim.matching_protocol = RandomMatching()
        sim.run(10)
        pairs.append(get_pairs(sim))
    
    assert pairs[0] == pairs[1]

def test_random_matching_no_double_pairing():
    """No agent in multiple pairs."""
    sim = Simulation(scenario, seed=42)
    sim.matching_protocol = RandomMatching()
    sim.run(10)
    
    for tick_pairs in get_all_pairs(sim):
        agents_in_pairs = []
        for (a, b) in tick_pairs:
            assert a not in agents_in_pairs
            assert b not in agents_in_pairs
            agents_in_pairs.extend([a, b])

def test_random_matching_lower_surplus():
    """Random matching produces lower surplus than legacy."""
    sim_random = run_with_protocol(RandomMatching(), seed=42)
    sim_legacy = run_with_protocol(LegacyMatchingProtocol(), seed=42)
    
    assert total_surplus(sim_legacy) > total_surplus(sim_random)
```

**Effort:** 2-3 hours

---

## Protocol 3: Split-The-Difference Bargaining

### Implementation Checklist

**File:** `src/vmt_engine/protocols/bargaining/split_difference.py`

```python
from src.vmt_engine.protocols.base import BargainingProtocol, Effect, Trade, Unpair
from src.vmt_engine.protocols.context import WorldView

class SplitDifference(BargainingProtocol):
    """Equal surplus division for fairness baseline."""
    
    name = "split_difference"
    version = "2025.10.27"
    
    def negotiate(
        self, 
        pair: tuple[int, int], 
        world: WorldView
    ) -> list[Effect]:
        """Find trade that splits surplus equally."""
        
        agent_a = get_agent_from_world(pair[0], world)
        agent_b = get_agent_from_world(pair[1], world)
        
        # Find all feasible trades
        feasible_trades = enumerate_feasible_trades(agent_a, agent_b, world)
        
        if not feasible_trades:
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=pair[0],
                agent_b=pair[1],
                reason="no_feasible_trade"
            )]
        
        # For each trade, calculate surplus split
        best_trade = None
        best_evenness = float('inf')
        
        for trade_params in feasible_trades:
            surplus_a = calculate_surplus(agent_a, trade_params)
            surplus_b = calculate_surplus(agent_b, trade_params)
            
            if surplus_a <= 0 or surplus_b <= 0:
                continue
            
            # Find trade closest to 50/50 split
            total = surplus_a + surplus_b
            evenness = abs(surplus_a - total/2)
            
            if evenness < best_evenness:
                best_evenness = evenness
                best_trade = trade_params
        
        if best_trade is None:
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=pair[0],
                agent_b=pair[1],
                reason="no_positive_surplus"
            )]
        
        return [Trade(
            protocol_name=self.name,
            tick=world.tick,
            buyer_id=best_trade['buyer'],
            seller_id=best_trade['seller'],
            pair_type=best_trade['pair_type'],
            dA=best_trade['dA'],
            dB=best_trade['dB'],
            dM=best_trade['dM'],
            price=best_trade['price'],
            metadata={'surplus_split': 'equal'}
        )]
```

### Tests

**File:** `tests/test_protocols_split_difference.py`

```python
def test_split_difference_equal_surplus():
    """Surplus split is approximately equal."""
    sim = Simulation(scenario, seed=42)
    sim.bargaining_protocol = SplitDifference()
    sim.run(50)
    
    trades = get_trades(sim)
    for trade in trades:
        surplus_buyer = calculate_surplus_from_trade(trade, 'buyer')
        surplus_seller = calculate_surplus_from_trade(trade, 'seller')
        
        # Should be within 5% of equal
        ratio = surplus_buyer / surplus_seller
        assert 0.95 < ratio < 1.05

def test_split_difference_pareto_improving():
    """All trades are Pareto improving."""
    sim = Simulation(scenario, seed=42)
    sim.bargaining_protocol = SplitDifference()
    sim.run(50)
    
    trades = get_trades(sim)
    for trade in trades:
        assert calculate_surplus_from_trade(trade, 'buyer') > 0
        assert calculate_surplus_from_trade(trade, 'seller') > 0

def test_split_difference_vs_legacy_prices():
    """Prices differ from legacy compensating blocks."""
    sim_split = run_with_protocol(SplitDifference(), seed=42)
    sim_legacy = run_with_protocol(LegacyBargainingProtocol(), seed=42)
    
    prices_split = get_average_prices(sim_split)
    prices_legacy = get_average_prices(sim_legacy)
    
    # Prices should differ (not necessarily higher or lower)
    assert prices_split != prices_legacy
```

**Effort:** 3-4 hours

---

## Phase 2a Completion Checklist

### Implementation
- [ ] Random Walk Search implemented
- [ ] Random Matching implemented
- [ ] Split-The-Difference Bargaining implemented
- [ ] All protocols registered in registry

### Testing
- [ ] Unit tests for each protocol passing
- [ ] Integration tests passing
- [ ] Property tests passing
- [ ] Determinism verified (10 runs with same seed)
- [ ] Performance benchmarked (<10% regression)

### Scenarios
- [ ] `scenarios/comparison_search_protocols.yaml` created
- [ ] `scenarios/comparison_matching_protocols.yaml` created
- [ ] `scenarios/comparison_bargaining_protocols.yaml` created
- [ ] All scenarios run successfully

### Documentation
- [ ] Docstrings complete with economic properties
- [ ] `docs/protocols_10-27/phase2a_results.md` written
- [ ] Comparison analysis documented
- [ ] Update `docs/ssot/README.md`
- [ ] Update `docs/ASDF/SESSION_STATE.md`

### Validation
- [ ] **Architecture validated** ✅
- [ ] Clear behavioral differences demonstrated
- [ ] One protocol per category working
- [ ] Ready to proceed to Phase 2b or Phase 3

---

## Next Steps After Phase 2a

**Option A: Continue to Phase 2b** (Pedagogical Protocols)
- Add Greedy Surplus Matching
- Add Myopic Search
- Add Take-It-Or-Leave-It Bargaining
- ~20-25 hours additional

**Option B: Jump to Phase 3** (Centralized Markets) ⭐
- Implement Walrasian Auctioneer
- Implement Posted-Price Market
- Implement CDA
- ~25-30 hours
- **KEY MILESTONE**

**Recommendation:** If Phase 2a goes smoothly, jump to Phase 3 (centralized markets) since that's your key research interest.

---

## Estimated Timeline

**Day 1-2:** Random Walk Search (2-3h)
**Day 3-4:** Random Matching (2-3h)
**Day 5:** Split-The-Difference Bargaining (3-4h)
**Day 6:** Testing and validation (1-2h)
**Day 7:** Documentation and comparison analysis (1-2h)

**Total:** 8-10 hours over 1 week

---

## Tips for Success

1. **Start simple** - Don't overthink the implementations
2. **Copy patterns** - Use legacy protocols as templates
3. **Test early** - Write tests as you implement
4. **Commit often** - Small commits after each milestone
5. **Document as you go** - Don't accumulate doc debt
6. **Validate architecture** - The goal is to prove the system works

---

**Ready to start? Begin with Random Walk Search!**

See `master_implementation_plan.md` for full roadmap through Phase 5.

