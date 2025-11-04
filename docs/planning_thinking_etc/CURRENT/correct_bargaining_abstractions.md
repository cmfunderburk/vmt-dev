# Correcting Bargaining Protocol Abstractions

**Date**: 2025-11-04  
**Status**: Planning  
**Priority**: High (Architectural Correction)

## Problem Identified

The decoupling refactor (v3) correctly separated **matching from bargaining** but incorrectly introduced abstraction **within bargaining protocols** that doesn't make architectural sense.

### What Went Wrong

**Current (incorrect) structure**:
```python
# All 3 protocols inject the SAME discoverer
CompensatingBlockBargaining(discoverer=CompensatingBlockDiscoverer)
SplitDifferenceBargaining(discoverer=CompensatingBlockDiscoverer)  # Wrong!
TakeItOrLeaveItBargaining(discoverer=CompensatingBlockDiscoverer)  # Wrong!
```

**The flaw**: Each bargaining protocol should BE a complete mechanism (search + allocation), not just an allocation rule on top of a shared search.

**Analogy**: This is like implementing:
```python
class NashBargaining:
    def __init__(self, auction_mechanism):
        self.auction = EnglishAuction()  # Why would Nash bargaining use an auction?
```

It doesn't make sense. The protocol IS the mechanism.

### Root Cause

Half-implemented protocols from the old system:
- `split_difference.py` and `take_it_or_leave_it.py` were never fully thought through
- They defaulted to using compensating block search as a placeholder
- The abstraction layer (`TradeDiscoverer`) formalized this placeholder pattern
- Now they appear to be "complete" but are actually just allocation variants

---

## Correct Architecture

### ✅ Keep (Correct Abstractions)

**Matching-Bargaining Separation** - This is correct:
```python
# Matching phase (lightweight heuristic)
TradePotentialEvaluator.evaluate_pair_potential() → TradePotential

# Bargaining phase (full search)
BargainingProtocol.negotiate() → Trade effects
```

**Utility Types**:
- `TradePotential` - Matching evaluation result
- `TradeTuple` - Convenient intermediate format for bargaining protocols (optional)

**Context Passing**:
- Direct agent access (no params hacks)
- `negotiate(pair, agents, world)` signature

### ❌ Remove (Incorrect Abstractions)

**Within-Bargaining Abstraction** - This is wrong:
```python
# Don't do this:
class TradeDiscoverer(ABC):
    def discover_trade(...) -> TradeTuple | None
```

Each protocol should implement its own search inline, not inject discoverers.

---

## Proposed Changes

### 1. Update trade_evaluation.py

**Remove**:
- `TradeDiscoverer` ABC (lines 148-184)

**Keep**:
- `TradePotential` NamedTuple
- `TradePotentialEvaluator` ABC  
- `QuoteBasedTradeEvaluator` implementation
- `TradeTuple` NamedTuple (reframed as utility type)

**Add**:
```python
def trade_tuple_to_effect(
    pair: tuple[int, int],
    trade_tuple: TradeTuple,
    protocol_name: str,
    tick: int
) -> Trade:
    """
    Convert TradeTuple to Trade effect (shared utility function).
    
    Handles agent-centric (i/j) → role-centric (buyer/seller) conversion.
    Reusable across bargaining protocols that use TradeTuple format.
    
    This is a utility function, not an interface requirement. Protocols
    can build Trade effects directly if they prefer a different format.
    
    Args:
        pair: (agent_i_id, agent_j_id)
        trade_tuple: Trade specification in agent-centric format
        protocol_name: Name of protocol creating the trade
        tick: Current simulation tick
        
    Returns:
        Trade effect in role-centric format (buyer/seller)
    """
    agent_a_id, agent_b_id = pair
    
    # Determine buyer/seller from trade direction
    if trade_tuple.dA_i > 0:  # agent_a receives A (buyer)
        buyer_id, seller_id = agent_a_id, agent_b_id
        dA = trade_tuple.dA_i
        dB = -trade_tuple.dB_i
        surplus_buyer = trade_tuple.surplus_i
        surplus_seller = trade_tuple.surplus_j
    else:  # agent_b receives A (buyer)
        buyer_id, seller_id = agent_b_id, agent_a_id
        dA = -trade_tuple.dA_i
        dB = -trade_tuple.dB_i
        surplus_buyer = trade_tuple.surplus_j
        surplus_seller = trade_tuple.surplus_i
    
    return Trade(
        protocol_name=protocol_name,
        tick=tick,
        buyer_id=buyer_id,
        seller_id=seller_id,
        pair_type="A<->B",
        dA=abs(dA),
        dB=abs(dB),
        price=float(trade_tuple.price),
        metadata={
            "surplus_buyer": surplus_buyer,
            "surplus_seller": surplus_seller,
            "total_surplus": trade_tuple.surplus_i + trade_tuple.surplus_j,
        }
    )
```

**Update module docstring**:
```python
"""
Trade Evaluation Utilities

Provides utilities for trade evaluation across protocol phases:

1. TradePotentialEvaluator: Lightweight heuristic for matching phase
   - Separates matching protocols from bargaining implementations
   - Fast quote-based evaluation for pairing decisions

2. TradeTuple: Utility type for bargaining protocols (optional)
   - Convenient intermediate format before Trade effects
   - Shared conversion helper available

This module does NOT prescribe how bargaining protocols search for trades.
Each bargaining protocol implements its own search mechanism.
"""
```

### 2. Update compensating_block.py

**Remove**:
- Discoverer injection from `__init__`
- Import of `CompensatingBlockDiscoverer`
- Import of `TradeDiscoverer`
- `_trade_tuple_to_effect()` method (use shared utility)

**Add**:
- Inline search logic from `CompensatingBlockDiscoverer`

**Structure**:
```python
"""
Compensating Block Bargaining Protocol

Self-contained implementation of VMT's foundational bargaining algorithm.
Searches discrete quantities (1, 2, 3, ...) and returns first mutually
beneficial trade.

Version: 2025.11.04 (Self-Contained)
"""

from typing import TYPE_CHECKING
from decimal import Decimal
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from ...systems.trade_evaluation import TradeTuple, trade_tuple_to_effect
from ...protocols.base import Effect, Trade, Unpair
from ...protocols.context import WorldView
from ...systems.matching import generate_price_candidates
from ...core.decimal_config import quantize_quantity

if TYPE_CHECKING:
    from ...core import Agent


@register_protocol(
    category="bargaining",
    name="compensating_block",
    description="First feasible trade using discrete quantity search (VMT default)",
    properties=["deterministic", "first_feasible"],
    complexity="O(K·P)",
    references=["VMT foundational algorithm"],
    phase="4",
)
class CompensatingBlockBargaining(BargainingProtocol):
    """
    Compensating block bargaining - VMT's foundational algorithm.
    
    Self-contained protocol that searches discrete quantities (1, 2, 3, ...)
    and price candidates to find the first mutually beneficial trade.
    
    Algorithm:
    1. Try both directions (i gives A, j gives A)
    2. For each direction with quote overlap:
       - Search quantities: 1, 2, 3, ... up to inventory
       - Generate price candidates in [ask, bid] range
       - Return first (dA, dB, price) where both ΔU > ε
    3. Return Unpair if no feasible trade
    
    Economic Properties:
    - First-acceptable-trade (satisficing, not optimizing)
    - Discrete quantity search
    - Deterministic (fixed search order)
    """
    
    @property
    def name(self) -> str:
        return "compensating_block"
    
    @property
    def version(self) -> str:
        return "2025.11.04"
    
    VERSION = "2025.11.04"
    
    def negotiate(
        self,
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: WorldView
    ) -> list[Effect]:
        """
        Negotiate trade using compensating block algorithm.
        
        Args:
            pair: (agent_a_id, agent_b_id)
            agents: (agent_a, agent_b) - direct access
            world: Context (tick, params, rng)
        
        Returns:
            [Trade(...)] if successful
            [Unpair(...)] if no mutually beneficial trade
        """
        agent_a, agent_b = agents
        epsilon = world.params.get("epsilon", 1e-9)
        
        # Search for first feasible trade (inline logic)
        trade_tuple = self._search_first_feasible(agent_a, agent_b, epsilon)
        
        if trade_tuple is None:
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=pair[0],
                agent_b=pair[1],
                reason="trade_failed"
            )]
        
        # Use shared utility to convert to Trade effect
        return [trade_tuple_to_effect(pair, trade_tuple, self.name, world.tick)]
    
    def _search_first_feasible(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        epsilon: float
    ) -> TradeTuple | None:
        """
        Search for first mutually beneficial trade.
        
        Searches discrete quantities (1, 2, 3, ...) in both directions
        and returns immediately when a feasible trade is found.
        
        Returns:
            TradeTuple if feasible trade exists, None otherwise
        """
        if not agent_i.utility or not agent_j.utility:
            return None
        
        # Current utilities
        u_i_0 = agent_i.utility.u(agent_i.inventory.A, agent_i.inventory.B)
        u_j_0 = agent_j.utility.u(agent_j.inventory.A, agent_j.inventory.B)
        
        # Try Direction 1: agent_i gives A
        result = self._search_direction(
            agent_i, agent_j,
            giver=agent_i, receiver=agent_j,
            u_i_0=u_i_0, u_j_0=u_j_0,
            epsilon=epsilon
        )
        if result:
            return result
        
        # Try Direction 2: agent_j gives A
        result = self._search_direction(
            agent_i, agent_j,
            giver=agent_j, receiver=agent_i,
            u_i_0=u_i_0, u_j_0=u_j_0,
            epsilon=epsilon
        )
        return result
    
    def _search_direction(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        giver: "Agent",
        receiver: "Agent",
        u_i_0: float,
        u_j_0: float,
        epsilon: float
    ) -> TradeTuple | None:
        """
        Search one direction for feasible trade.
        
        (Logic moved from CompensatingBlockDiscoverer)
        """
        # ... (existing search logic from discovery.py)
```

### 3. Update split_difference.py (Stub)

```python
"""
Split-the-Difference Bargaining Protocol

NOT YET IMPLEMENTED - Stub for future development.

Intended Behavior:
- Search ALL possible trades exhaustively
- Rank by surplus evenness: |surplus_i - surplus_j|
- Select trade with most equal surplus split
- If tied, use deterministic tie-breaker (e.g., lower quantity)

Economic Properties:
- Nash bargaining solution approximation
- Fairness criterion: equal gains from trade
- Pareto efficient
- Computationally expensive (exhaustive search)

References:
- Nash (1950) "The Bargaining Problem"
- Kalai-Smorodinsky (1975) alternative fairness criterion

Version: 2025.11.04 (Stub)
"""

from typing import TYPE_CHECKING
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from ...protocols.base import Effect, Unpair
from ...protocols.context import WorldView

if TYPE_CHECKING:
    from ...core import Agent


@register_protocol(
    category="bargaining",
    name="split_difference",
    description="Equal surplus division (NOT IMPLEMENTED - stub)",
    properties=["stub", "not_implemented"],
    complexity="O(K·P) exhaustive",
    references=["Nash (1950)"],
    phase="future",
)
class SplitDifference(BargainingProtocol):
    """
    Equal surplus division bargaining - NOT IMPLEMENTED.
    
    This is a stub protocol for future development. Currently returns
    Unpair with reason="not_implemented" for any negotiation attempt.
    
    TODO: Implement exhaustive search for equal split trade.
    """
    
    @property
    def name(self) -> str:
        return "split_difference"
    
    @property
    def version(self) -> str:
        return "2025.11.04.stub"
    
    VERSION = "2025.11.04.stub"
    
    def negotiate(
        self,
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: WorldView
    ) -> list[Effect]:
        """
        NOT IMPLEMENTED - Returns Unpair.
        
        Future implementation will search all trades and select most balanced.
        """
        return [Unpair(
            protocol_name=self.name,
            tick=world.tick,
            agent_a=pair[0],
            agent_b=pair[1],
            reason="not_implemented"
        )]
```

### 4. Update take_it_or_leave_it.py (Stub)

```python
"""
Take-It-Or-Leave-It Bargaining Protocol

NOT YET IMPLEMENTED - Stub for future development.

Intended Behavior:
- Select proposer based on power/randomness
- Proposer searches for their optimal offer
- Subject to responder IR constraint: ΔU_responder ≥ ε
- Maximize proposer surplus
- Responder accepts (trade) or rejects (unpair)

Economic Properties:
- Asymmetric surplus distribution
- Models bargaining power
- Rubinstein bargaining limiting case
- Demonstrates hold-up problems

Parameters (Future):
- proposer_power: [0,1] - How much surplus proposer captures
- proposer_selection: "random" | "higher_id" | "lower_id" | "first_in_pair"

References:
- Rubinstein (1982) "Perfect Equilibrium in a Bargaining Model"
- Market power literature
- Hold-up problem (Williamson 1985)

Version: 2025.11.04 (Stub)
"""

from typing import TYPE_CHECKING
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from ...protocols.base import Effect, Unpair
from ...protocols.context import WorldView

if TYPE_CHECKING:
    from ...core import Agent


@register_protocol(
    category="bargaining",
    name="take_it_or_leave_it",
    description="Asymmetric power bargaining (NOT IMPLEMENTED - stub)",
    properties=["stub", "not_implemented"],
    complexity="O(K·P) proposer-optimal",
    references=["Rubinstein (1982)"],
    phase="future",
)
class TakeItOrLeaveIt(BargainingProtocol):
    """
    Asymmetric bargaining with proposer power - NOT IMPLEMENTED.
    
    This is a stub protocol for future development. Currently returns
    Unpair with reason="not_implemented" for any negotiation attempt.
    
    TODO: Implement proposer-optimal search algorithm.
    """
    
    @property
    def name(self) -> str:
        return "take_it_or_leave_it"
    
    @property
    def version(self) -> str:
        return "2025.11.04.stub"
    
    VERSION = "2025.11.04.stub"
    
    def negotiate(
        self,
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: WorldView
    ) -> list[Effect]:
        """
        NOT IMPLEMENTED - Returns Unpair.
        
        Future implementation will find proposer's optimal offer.
        """
        return [Unpair(
            protocol_name=self.name,
            tick=world.tick,
            agent_a=pair[0],
            agent_b=pair[1],
            reason="not_implemented"
        )]
```

### 5. Delete discovery.py

**File to delete**: `src/vmt_engine/game_theory/bargaining/discovery.py`

The `CompensatingBlockDiscoverer` logic will be inlined into `compensating_block.py` as `_search_first_feasible()` and `_search_direction()` methods.

### 6. Update __init__.py

**File**: `src/vmt_engine/game_theory/bargaining/__init__.py`

**Update docstring**:
```python
"""
Bargaining Protocols - Game Theory Paradigm

Bargaining protocols determine how paired agents negotiate trade terms.
Each protocol implements a complete mechanism (search + allocation).

Available Protocols:
- compensating_block: First feasible trade (VMT default) [IMPLEMENTED]
- split_difference: Equal surplus division [STUB - NOT IMPLEMENTED]
- take_it_or_leave_it: Asymmetric power [STUB - NOT IMPLEMENTED]

Theoretical Context:
- Axiomatic bargaining solutions
- Strategic bargaining games
- Nash program

Version: 2025.11.04 (Corrected Architecture)
"""
```

---

## Testing Strategy

### Update Existing Tests

**1. test_trade_evaluation.py**
- Remove all `TestCompensatingBlockDiscoverer` tests (4 tests)
- Keep all `TradePotentialEvaluator` tests (6 tests)
- Keep all `TradeTuple` NamedTuple tests (3 tests)
- Net: 9 tests remain (was 13)

**2. test_bargaining_refactor_integration.py**
- All tests still valid (test protocol signatures, not discoverers)
- 7 tests remain unchanged

**3. test_split_difference.py**
- Delete all implementation tests (~9 tests)
- Keep 1-2 stub tests:
  ```python
  def test_split_difference_not_implemented():
      """Verify stub returns not_implemented."""
      protocol = SplitDifference()
      # ... setup ...
      effects = protocol.negotiate(pair, agents, world)
      
      assert len(effects) == 1
      assert isinstance(effects[0], Unpair)
      assert effects[0].reason == "not_implemented"
  
  def test_split_difference_registers_correctly():
      """Verify protocol is in registry as stub."""
      metadata = ProtocolRegistry.get_metadata("split_difference", "bargaining")
      assert "stub" in metadata.properties
      assert "not_implemented" in metadata.properties
  ```

**4. test_take_it_or_leave_it_bargaining.py**
- Delete all implementation tests (~20 tests)
- Keep 1-2 stub tests (same pattern as split_difference)

**5. New Tests for compensating_block**
- Add tests for inline search methods
- Test `_search_first_feasible()` directly
- Test `_search_direction()` directly

### Summary
- **Before**: 97 tests in refactor areas
- **After**: ~25 tests deleted (stubs), ~5 new tests (compensating block internals)
- **Net**: ~77 tests

---

## File Inventory

### Files Modified (6)

1. **`src/vmt_engine/systems/trade_evaluation.py`**
   - Remove `TradeDiscoverer` ABC (~36 lines)
   - Add `trade_tuple_to_effect()` function (~40 lines)
   - Update module docstring
   - Net: ~+4 lines

2. **`src/vmt_engine/game_theory/bargaining/compensating_block.py`**
   - Remove discoverer injection from `__init__`
   - Remove `TradeDiscoverer` import
   - Add inline search methods from discovery.py (~100 lines)
   - Remove `_trade_tuple_to_effect()` (use shared utility)
   - Import shared `trade_tuple_to_effect`
   - Net: ~+60 lines (logic moved in)

3. **`src/vmt_engine/game_theory/bargaining/split_difference.py`**
   - Replace entire implementation with stub (~150 lines removed, ~60 added)
   - Net: ~-90 lines

4. **`src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py`**
   - Replace entire implementation with stub (~280 lines removed, ~60 added)
   - Net: ~-220 lines

5. **`src/vmt_engine/game_theory/bargaining/__init__.py`**
   - Update docstring
   - Net: ~+5 lines

6. **`docs/2_technical_manual.md`**
   - Update bargaining section to remove discoverer injection
   - Clarify only compensating_block is implemented
   - Net: ~+10 lines

### Files Deleted (1)

1. **`src/vmt_engine/game_theory/bargaining/discovery.py`** (~194 lines)

### Tests Modified (4)

1. **`tests/test_trade_evaluation.py`**
   - Remove `CompensatingBlockDiscoverer` tests
   - Keep rest

2. **`tests/test_split_difference.py`**
   - Replace with stub tests

3. **`tests/test_take_it_or_leave_it_bargaining.py`**
   - Replace with stub tests

4. **`tests/test_bargaining_refactor_integration.py`**
   - No changes needed (protocols still have correct signatures)

---

## Implementation Steps

### Step 1: Update trade_evaluation.py

1. Remove `TradeDiscoverer` ABC (lines 148-184)
2. Update module docstring to clarify purpose
3. Add `trade_tuple_to_effect()` utility function
4. Update `TradeTuple` docstring to clarify it's a utility type

### Step 2: Inline Logic in compensating_block.py

1. Remove `from .discovery import CompensatingBlockDiscoverer`
2. Remove `from ...systems.trade_evaluation import TradeDiscoverer`
3. Remove `discoverer` parameter from `__init__`
4. Copy `_search_direction()` logic from discovery.py
5. Rename `_trade_tuple_to_effect()` call to use shared `trade_tuple_to_effect()`
6. Add `_search_first_feasible()` and `_search_direction()` as methods

### Step 3: Stub Out split_difference.py

1. Delete all implementation (lines ~70-230)
2. Replace with stub that returns Unpair(reason="not_implemented")
3. Keep comprehensive docstring explaining intended future behavior
4. Update @register_protocol properties to include "stub"

### Step 4: Stub Out take_it_or_leave_it.py

1. Delete all implementation (lines ~80-345)
2. Replace with stub that returns Unpair(reason="not_implemented")
3. Keep comprehensive docstring explaining intended future behavior
4. Update @register_protocol properties to include "stub"

### Step 5: Delete discovery.py

1. Remove entire file
2. Verify no imports remain

### Step 6: Update Tests

1. Update `test_trade_evaluation.py` - remove discoverer tests
2. Update `test_split_difference.py` - stub tests only
3. Update `test_take_it_or_leave_it_bargaining.py` - stub tests only
4. Add tests for compensating_block's new methods

### Step 7: Update Documentation

1. Update `docs/2_technical_manual.md`
2. Update `bargaining/__init__.py` docstring
3. Update `CHANGELOG.md` to note correction

---

## Success Criteria

✅ **Architectural Correctness**
- No `TradeDiscoverer` abstraction (removed)
- No discoverer injection (removed)
- Each protocol is self-contained (search + allocation)

✅ **Code Quality**
- `compensating_block` is fully implemented and self-contained
- `split_difference` and `take_it_or_leave_it` are clear stubs
- No confusion about half-implemented features

✅ **Functionality**
- All tests pass (fewer tests, but correct ones)
- Baseline scenarios still work (only use compensating_block)
- Determinism maintained

✅ **Documentation**
- Technical manual accurate
- CHANGELOG reflects correction
- Stubs have clear "not implemented" markers

---

## Breaking Changes

**API Changes** (Minor):
1. `TradeDiscoverer` interface removed
2. `CompensatingBlockDiscoverer` class removed
3. Discoverer injection removed from all protocol `__init__` methods
4. `split_difference` and `take_it_or_leave_it` now return Unpair(reason="not_implemented")

**Non-Breaking**:
- `TradeTuple` remains available (just reframed)
- `compensating_block` protocol behavior unchanged
- Scenarios continue working (only use compensating_block)
- Protocol registry names unchanged

**Impact on Users**:
- If using only `compensating_block`: No impact
- If using `split_difference` or `take_it_or_leave_it`: Now get explicit "not implemented" (better than silent wrong behavior)

---

## Migration Guide

### For Custom Bargaining Protocols

**OLD pattern (discouraged)**:
```python
class MyProtocol(BargainingProtocol):
    def __init__(self, discoverer=None):
        self.discoverer = discoverer or CompensatingBlockDiscoverer()
    
    def negotiate(self, pair, agents, world):
        trade_tuple = self.discoverer.discover_trade(...)
```

**NEW pattern (correct)**:
```python
class MyProtocol(BargainingProtocol):
    def negotiate(self, pair, agents, world):
        # Implement your own search logic inline
        trade_tuple = self._my_search_algorithm(agents[0], agents[1], epsilon)
        
        if trade_tuple is None:
            return [Unpair(...)]
        
        # Optionally use shared conversion utility
        from ...systems.trade_evaluation import trade_tuple_to_effect
        return [trade_tuple_to_effect(pair, trade_tuple, self.name, world.tick)]
```

**TradeTuple is optional** - you can build Trade effects directly if you prefer.

---

## Philosophical Clarity

### What IS an Abstraction Interface?

**TradePotentialEvaluator** - YES, this is an abstraction:
- **Question**: "How should matching protocols evaluate pairs?"
- **Answer**: Multiple valid approaches (quotes, utilities, ML, etc.)
- **Use case**: Matching protocols need to evaluate without knowing bargaining details
- **Substitutability**: Can swap evaluators independently

**TradeDiscoverer** - NO, this is NOT an abstraction:
- **Question**: "How should bargaining protocols find trades?"
- **Answer**: That's what DEFINES each protocol!
- **Use case**: Each protocol implements its own complete mechanism
- **Substitutability**: You substitute the whole protocol, not the discoverer

### The Design Principle

**Abstraction makes sense when**:
- Multiple protocols need the same capability
- The capability can be implemented differently
- Substitution adds value

**Abstraction is wrong when**:
- The capability IS what defines the protocol
- Forcing shared implementation masks incomplete work
- It creates confusion about what the protocol actually does

---

## Risks & Mitigation

### Risk 1: Tests Will Break

**Likelihood**: High (intentional)  
**Impact**: Medium (need to update/delete tests)

**Mitigation**:
- Delete stub protocol tests (they tested wrong behavior)
- Keep 1-2 tests verifying stub returns "not_implemented"
- Update compensating_block tests to test inline methods
- All changes are improvements (removing confusion)

### Risk 2: Scenarios Using Stub Protocols

**Likelihood**: Low (check first)  
**Impact**: High if any exist

**Mitigation**:
```bash
grep -r "split_difference\|take_it_or_leave_it" scenarios/
```

If any scenarios use these, they'll get Unpair(reason="not_implemented") - immediate clear feedback.

### Risk 3: Loss of Working Code?

**Concern**: Are we throwing away working implementations?

**Answer**: No - the current implementations are wrong:
- They all use compensating block search
- They just differ in surplus allocation
- That's not what they claim to be
- Better to be honest (stub) than misleading (half-done)

**What we're actually losing**:
- Surplus allocation variants (can easily re-implement when we do full protocols)
- Not the search algorithms (only one real algorithm exists)

---

## Lines of Code Impact

**Removed**:
- discovery.py: ~194 lines
- TradeDiscoverer ABC: ~36 lines
- split_difference implementation: ~150 lines → ~60 stub
- take_it_or_leave_it implementation: ~280 lines → ~60 stub
- Discoverer tests: ~4 tests
- Stub protocol tests: ~25 tests
- **Total removed**: ~540 lines

**Added**:
- trade_tuple_to_effect(): ~40 lines
- Inline search in compensating_block: ~100 lines (moved from discovery.py)
- Stub implementations: ~120 lines
- Stub tests: ~4 tests
- **Total added**: ~264 lines

**Net**: -276 lines (significant simplification)

---

## Timeline Estimate

**Step-by-step implementation**: 4-6 hours
1. Update trade_evaluation.py (1 hour)
2. Inline compensating_block logic (1 hour)
3. Stub split_difference (30 min)
4. Stub take_it_or_leave_it (30 min)
5. Delete discovery.py (5 min)
6. Update tests (1.5 hours)
7. Update documentation (30 min)
8. Validation (30 min)

---

## Questions & Discussion

### 1. TradeTuple Location

**Current**: `src/vmt_engine/systems/trade_evaluation.py`

**Arguments for keeping it there**:
- Central location for trade-related types
- Used by both matching (TradePotential) and bargaining (TradeTuple)
- Natural grouping

**Arguments for moving to bargaining**:
- Only bargaining protocols use it
- Makes dependency clearer
- trade_evaluation.py focused on matching

**Recommendation**: Keep in `trade_evaluation.py` - it's a cross-cutting utility, and the file already mixes matching and bargaining types.

### 2. Shared Conversion Helper Location

`trade_tuple_to_effect()` function - where should it live?

**Option A**: `trade_evaluation.py` (with TradeTuple)
- Pro: Type and converter together
- Con: trade_evaluation focused on matching

**Option B**: `bargaining/utils.py` (new file)
- Pro: Clear it's bargaining-specific
- Con: New file for one function

**Option C**: Base class helper method
```python
class BargainingProtocol(ProtocolBase):
    @staticmethod
    def _trade_tuple_to_effect(...) -> Trade:
        # Shared static method
```
- Pro: Available to all bargaining protocols
- Con: Mixing interface with utilities

**Recommendation**: **Option A** (trade_evaluation.py) - keep utilities together, file is already mixed-purpose.

### 3. Should We Version the Stubs?

The stub protocols have version `"2025.11.04.stub"`. Should we:
- Keep version tracking on stubs?
- Or use a constant like `"stub"` or `"not_implemented"`?

**Recommendation**: Keep version with `.stub` suffix - shows when stub was created.

### 4. Registry Properties

Stub protocols marked with `properties=["stub", "not_implemented"]`. Should the registry:
- Filter these out from listings?
- Show them but mark as stubs?
- No special handling?

**Recommendation**: No special handling - let them appear in registry with clear stub markers. Users should be able to see what's available vs. what's implemented.

### 5. Future Implementation Priority

When we eventually implement split_difference and take_it_or_leave_it, which first?

**Split Difference**:
- Simpler algorithm (exhaustive search + ranking)
- Clear economic meaning (fairness)
- Good pedagogical value

**Take-It-Or-Leave-It**:
- More complex (power dynamics, proposer selection)
- Richer parameter space
- More game-theoretic

**Recommendation**: Implement split_difference first when ready.

---

## Summary

This correction plan:
1. ✅ Removes incorrect abstraction (`TradeDiscoverer`)
2. ✅ Keeps useful utilities (`TradeTuple`, conversion helper)
3. ✅ Makes protocols self-contained (inline search logic)
4. ✅ Honest about incomplete work (clear stubs)
5. ✅ Maintains all correct abstractions (matching-bargaining separation)

**Ready for review and implementation when you approve.**

What are your thoughts on the location questions (1-2) and registry handling (4)?

