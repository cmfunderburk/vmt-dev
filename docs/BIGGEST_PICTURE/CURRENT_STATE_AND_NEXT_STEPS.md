# VMT: Current State & Next Implementation Steps
## Your Quick Reorientation Guide

**Document Purpose:** Get you back up to speed in 5 minutes and coding in 10  
**Created:** 2025-10-28  
**For:** Solo developer needing clarity after getting lost in the complexity

---

## 🎯 Where You Are Right Now

### The Big Picture
You're building VMT - a spatial agent-based economic simulation that demonstrates how **markets emerge from institutional rules** rather than assumptions. Instead of assuming equilibrium prices, you're showing how different search, matching, and bargaining protocols produce different market outcomes.

### What's Working (Production Ready)
✅ **Core Engine:** Spatial simulation with deterministic 7-phase tick cycle  
✅ **Economic Systems:** 5 utility functions, money system, foraging, trading  
✅ **Protocol Architecture:** Modular system where institutional rules are swappable  
✅ **Legacy Protocols:** Distance-based search, three-pass matching, compensating block bargaining  
✅ **Telemetry:** Comprehensive SQLite logging with PyQt viewer  
✅ **Visualization:** Pygame renderer with GUI launcher  

### What You Just Completed (October 27)
- **Phase 1 DONE:** Legacy protocol adapters merged to main
- **Refactored:** DecisionSystem (-42% LOC) and TradeSystem (-39% LOC) 
- **Fixed:** Critical trading pipeline and CES utility bugs
- **Created:** Massive documentation including strategic vision and 5-phase roadmap

---

## 📍 Your Exact Position in the Roadmap

You're at the **start of Phase 2a** - about to implement your first alternative protocols:

```
Phase 1: Legacy Adapters ✅ COMPLETE (merged to main)
         └─ Search, Matching, Bargaining protocols wrapped
         └─ Systems refactored to use protocol architecture
         
Phase 2a: Quick Win Baselines 👈 YOU ARE HERE (8-10 hours)
         ├─ Random Walk Search (2-3 hours)
         ├─ Random Matching (2-3 hours)  
         └─ Split-the-Difference Bargaining (3-4 hours)

Phase 2b: Pedagogical Protocols (20-25 hours)
         ├─ Greedy Surplus Matching
         ├─ Myopic Search
         └─ Take-It-Or-Leave-It Bargaining

Phase 3: CENTRALIZED MARKETS ⭐ KEY MILESTONE (25-30 hours)
         ├─ Walrasian Auctioneer
         ├─ Posted-Price Market
         └─ Continuous Double Auction
         
Phase 4-5: Advanced & Comprehensive (35-45 hours)
```

**Why Phase 2a?** These three simple protocols validate your architecture and establish baselines for comparison. They're deliberately simple to implement quickly.

**Why This Order?** Quick wins → Teaching tools → CRITICAL centralized markets → Advanced features

---

## 🚀 Next Implementation: Random Walk Search Protocol

### What You're Building (2-3 hours)
A search protocol where agents move randomly instead of rationally. This is your baseline to show the value of information.

### Files to Create/Modify

**1. Create:** `src/vmt_engine/protocols/search/random_walk.py`
```python
from vmt_engine.protocols.base import SearchProtocol, SetTarget
from vmt_engine.protocols.context import WorldView

class RandomWalkSearch(SearchProtocol):
    """
    Stochastic exploration for baseline comparison.
    
    Agents select random directions within vision radius.
    No utility calculation, pure exploration.
    Demonstrates value of information vs rational search.
    """
    
    @property
    def name(self) -> str:
        return "random_walk"
    
    @property
    def version(self) -> str:
        return "2025.10.28"
    
    def build_preferences(self, world: WorldView) -> list[tuple]:
        """Build randomly ordered preferences."""
        # Get visible positions
        visible = self._get_visible_positions(
            world.pos,
            world.params.get("vision_radius", 5),
            world.params.get("grid_size", 32)
        )
        
        # Filter out current position
        targets = [pos for pos in visible if pos != world.pos]
        
        if not targets:
            return []
        
        # Shuffle using deterministic RNG
        shuffled = targets.copy()
        world.rng.shuffle(shuffled)
        
        # Return as preferences with equal scores
        return [(pos, 0.0, {"type": "random_move"}) for pos in shuffled]
    
    def select_target(self, world: WorldView) -> list:
        """Select best target from preferences."""
        prefs = self.build_preferences(world)
        
        if not prefs:
            return []
        
        # Select first (random due to shuffle)
        target_pos, score, metadata = prefs[0]
        
        return [SetTarget(
            protocol_name=self.name,
            tick=world.tick,
            agent_id=world.agent_id,
            target=target_pos
        )]
    
    def _get_visible_positions(self, center, radius, grid_size):
        """Get all positions within Manhattan distance radius."""
        positions = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) + abs(dy) <= radius:
                    x = (center[0] + dx) % grid_size
                    y = (center[1] + dy) % grid_size
                    positions.append((x, y))
        return positions
```

**2. Register in:** `src/vmt_engine/protocols/search/__init__.py`
```python
from .legacy import LegacySearchProtocol
from .random_walk import RandomWalkSearch

__all__ = ["LegacySearchProtocol", "RandomWalkSearch"]
```

**3. Create test:** `tests/test_random_walk_search.py`
```python
import pytest
from vmt_engine.protocols.search.random_walk import RandomWalkSearch
from vmt_engine.protocols.context import WorldView
# ... setup code ...

def test_random_walk_determinism():
    """Same seed produces same random walk."""
    search = RandomWalkSearch()
    
    # Create world with seed 42
    world1 = create_test_world(seed=42)
    effects1 = search.execute(world1)
    
    # Same seed should give same results
    world2 = create_test_world(seed=42)
    effects2 = search.execute(world2)
    
    assert effects1 == effects2
    
def test_random_walk_coverage():
    """Random walk explores all visible positions over time."""
    # Test that distribution is uniform over many iterations
    pass
```

**4. Create comparison scenario:** `scenarios/comparison_search_random_vs_legacy.yaml`
```yaml
schema_version: 1
name: search_protocol_comparison
N: 32
agents: 10

# Two populations with different search
protocol_assignments:
  - agent_ids: [0, 1, 2, 3, 4]
    search_protocol: 
      name: "legacy"
      version: "2025.10.26"
  - agent_ids: [5, 6, 7, 8, 9]
    search_protocol:
      name: "random_walk"
      version: "2025.10.28"

# Standard economic parameters...
initial_inventories:
  A: { uniform_int: [5, 15] }
  B: { uniform_int: [5, 15] }
  
utilities:
  mix:
    - type: ces
      weight: 1.0
      params:
        rho: -0.5
        wA: 1.0
        wB: 1.0
```

### How to Test Your Implementation

```bash
# 1. Run unit tests
pytest tests/test_random_walk_search.py -v

# 2. Run comparison scenario
python main.py scenarios/comparison_search_random_vs_legacy.yaml 42

# 3. Analyze results
python scripts/analyze_search_efficiency.py  # You'll create this

# 4. Check determinism (critical!)
python scripts/compare_telemetry_snapshots.py run1.db run2.db
```

---

## 📋 Complete Phase 2a Checklist

### Day 1-2: Random Walk Search
- [ ] Create `src/vmt_engine/protocols/search/random_walk.py`
- [ ] Add to `__init__.py`
- [ ] Write unit tests (determinism, coverage)
- [ ] Create comparison scenario
- [ ] Run side-by-side with legacy
- [ ] Document observations

### Day 3-4: Random Matching  
- [ ] Create `src/vmt_engine/protocols/matching/random.py`
- [ ] Implement shuffle-based pairing
- [ ] Test deterministic shuffle
- [ ] Compare surplus vs legacy matching
- [ ] Document efficiency gap

### Day 5: Split-the-Difference Bargaining
- [ ] Create `src/vmt_engine/protocols/bargaining/split_difference.py`
- [ ] Implement 50/50 surplus division
- [ ] Test equal split property
- [ ] Compare price distributions
- [ ] Document fairness metrics

### Validation
- [ ] All tests passing
- [ ] Determinism verified (10 runs same seed)
- [ ] Performance <10% regression
- [ ] Clear behavioral differences documented

---

## 🎮 How to Work Efficiently

### Your Development Loop
```bash
# 1. Start with the template code above
# 2. Run existing tests to ensure nothing breaks
pytest tests/ -x  # Stop on first failure

# 3. Implement incrementally with test-driven development
# 4. Use the GUI to visualize behavior
python launcher.py  # Select your comparison scenario

# 5. Check telemetry for detailed analysis
python view_logs.py
```

### Key Files You'll Reference
- **Protocol base:** `src/vmt_engine/protocols/base.py` - Effect types and interfaces
- **Legacy examples:** `src/vmt_engine/protocols/search/legacy.py` - Pattern to follow
- **Context types:** `src/vmt_engine/protocols/context.py` - WorldView structure
- **Test patterns:** `tests/test_*_integration.py` - How to test protocols

### Common Pitfalls to Avoid
1. **Use world.rng, not random.random()** - Determinism is critical
2. **Sort all iterations** - Even when order "shouldn't matter"
3. **Honor pairing commitments** - Paired agents don't re-evaluate
4. **Test with multiple seeds** - Ensure true determinism
5. **Start simple** - Get basic version working before optimizing

---

## 🎯 Success Metrics for Phase 2a

You'll know you've succeeded when:

1. **Random Walk Search**
   - Agents move randomly vs rationally
   - Clear efficiency gap vs legacy (fewer successful trades)
   - Deterministic with same seed
   
2. **Random Matching**
   - Pairs form randomly vs by surplus
   - Lower total welfare vs legacy
   - Demonstrates value of smart matching
   
3. **Split-the-Difference**
   - Surplus divided equally (within epsilon)
   - Different price distribution vs legacy
   - Fairness metrics quantified

---

## 💡 Why This Matters (Remind Yourself)

These simple protocols aren't just implementation exercises. They're **foundational comparisons** that demonstrate:

- **Information Value:** Random vs rational search shows how information affects efficiency
- **Matching Theory:** Random vs surplus matching quantifies allocative efficiency
- **Bargaining Power:** Split-difference vs compensating blocks shows price formation mechanisms

Every protocol you implement is a different **institutional rule** that produces different **market outcomes**. This is the core of your research: markets aren't natural phenomena, they're institutional constructions.

---

## 📞 When You Get Stuck

1. **Check legacy implementations** - They show the pattern
2. **Read the effect types** in `base.py` - They define what's possible
3. **Run existing tests** - They reveal the expected behavior
4. **Look at telemetry** - The database shows what actually happened
5. **Keep it simple** - These are meant to be quick wins

---

## 🚦 Go Build!

You have:
- Clear specification for Random Walk Search (2-3 hours)
- Template code to start from
- Test patterns to follow
- Comparison framework ready

**Start here:** Create `src/vmt_engine/protocols/search/random_walk.py` and copy the template above.

**Next checkpoint:** When Random Walk is working, move to Random Matching (even simpler!).

**Remember:** Phase 2a is about validation and baselines. Keep it simple, get it working, move fast.

---

*This document is your north star. When you feel lost, come back here. You're building something important, one protocol at a time.*
