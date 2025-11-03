# Decoupling Matching from Bargaining: Implementation Plan v3

**Date**: 2025-11-03  
**Status**: Planning  
**Priority**: Critical (Blocking Technical Debt)  
**Version**: 3.0 (Revised with Direct Agent Passing)

## Revision History

- **v1 (2025-01-XX)**: Initial plan, identified core issues
- **v2 (2025-11-03)**: Fixed critical flaw - legacy.py is not legacy, it's the core implementation
- **v3 (2025-11-03)**: Simplified by passing agents directly to protocols, removing params hack

---

## Executive Summary

Currently, matching protocols (Phase 2) are tightly coupled to a specific bargaining protocol implementation (`find_compensating_block_generic()`). This violates separation of concerns and prevents independent protocol development.

**Key Insights**:
1. The "legacy" bargaining protocol is actually the **default, primary implementation** of the VMT compensating block algorithm
2. Matching protocols should use lightweight heuristics for pairing decisions
3. Bargaining protocols should own their trade discovery algorithms
4. **Current params hack is architectural smell** - partner state is smuggled through WorldView.params with magic keys

**This plan**:
1. Decouples matching from bargaining via abstraction interfaces
2. Fixes the params hack by passing agents directly to bargaining protocols
3. Preserves the compensating block algorithm (it's core functionality)
4. Renames "legacy" to accurate terminology
5. Enables future protocol diversity

**Atomic Change**: Both interface fix and decoupling in one PR for clean migration.

---

## 1. Problem Analysis

### 1.1 Current Architecture Issues

**Issue 1: Tight Coupling Chain**
```
MatchingProtocol.find_matches()
  ↓
find_all_feasible_trades() [in matching.py]
  ↓ (hardcoded)
find_compensating_block_generic() [in matching.py, lines 516-615]
  ↓
Same calculation used by BargainingProtocol.negotiate()
```

**Problems**:
- Matching protocols run full bargaining algorithm just to decide pairings (behavioral issue, not just performance)
- Matching should use fast heuristics ("Can they trade?")
- Bargaining should use precise algorithms ("What exact terms?")
- Code duplication - same logic called in two phases

**Issue 2: The Params Hack**

In `context_builders.py`:
```python
# HACK: Smuggle partner data through params dict
params_with_partner[f"partner_{agent_b.id}_inv_A"] = agent_b.inventory.A
params_with_partner[f"partner_{agent_b.id}_inv_B"] = agent_b.inventory.B
params_with_partner[f"partner_{agent_b.id}_utility"] = agent_b.utility
```

In `legacy.py`:
```python
# Extract from magic keys
inventory = Inventory(
    A=world.params.get(f"partner_{agent_id}_inv_A", 0),
    B=world.params.get(f"partner_{agent_id}_inv_B", 0)
)
```

**Why this is wrong**:
- Magic string keys are fragile
- `params` is meant for configuration, not state passing
- Every protocol needs extraction logic
- `AgentView` intentionally hides this info (only public data), but bargaining needs full state
- Workaround acknowledged in comments: "temporary adapter"

**Root Cause**: WorldView was designed for single-agent perspective (search, movement), but bargaining needs **bilateral state**. Rather than adapting WorldView, we should pass what's needed directly.

**Issue 3: Misleading Naming**
- `legacy.py` is the **default, core algorithm**, not deprecated code
- Should be named after behavior: `compensating_block.py`

### 1.2 What Each Phase Actually Needs

**Matching (Phase 2)**: "Should we pair these agents?"
- Lightweight heuristic evaluation
- Estimated surplus for ranking pairs
- Fast - called for all possible pairs
- Current: Runs full compensating block algorithm (overkill)

**Bargaining (Phase 4)**: "What terms do we negotiate?"
- Full trade discovery with utility calculations
- Precise quantities, prices, surpluses
- Only called for established pairs
- Current: Uses same function as matching (correct, but coupled)

---

## 2. Design Goals

### 2.1 Primary Objectives

1. **Complete Decoupling**: Matching protocols operate independently of bargaining implementations

2. **Fix Params Hack**: Pass agents directly to bargaining protocols (they already exist in TradeSystem)

3. **Protocol Flexibility**: Each bargaining protocol can use its own discovery algorithm

4. **Performance Optimization**: Matching uses fast heuristics, bargaining uses full calculations

5. **Clear Separation**:
   - Matching: Lightweight pairing decisions
   - Bargaining: Full negotiation logic

6. **Preserve Core Algorithm**: Compensating block is fundamental VMT logic

7. **Accurate Naming**: Rename "legacy" to reflect actual purpose

8. **Immutability Enforcement**: Protocols receive mutable agents but must not mutate (convention + debug assertions)

### 2.2 Non-Goals

- Changing protocol phase structure
- Modifying Effect system
- Changing WorldView for other protocol types (search, movement)
- Deprecating compensating block algorithm
- Perfect immutability enforcement (accept convention + testing for now)

---

## 3. Proposed Architecture

### 3.1 Abstraction Layers

```
┌─────────────────────────────────────────────────────────┐
│                 Matching Protocols                       │
│  (Phase 2: Pair Selection)                              │
│  Uses: TradePotentialEvaluator (lightweight)            │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│         TradePotentialEvaluator Interface               │
│  - evaluate_pair_potential(agent_i, agent_j)            │
│  - Returns: TradePotential (surplus estimate)           │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│    QuoteBasedTradeEvaluator (default implementation)    │
│  - Uses compute_surplus() (quote overlaps)              │
│  - Fast heuristic, no full utility calculations         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                 Bargaining Protocols                     │
│  (Phase 4: Trade Negotiation)                           │
│  Receives: (pair, agents, world)                        │
│  Uses: TradeDiscoverer (full calculation)               │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│         TradeDiscoverer Interface                       │
│  - discover_trade(agent_i, agent_j, epsilon)            │
│  - Returns: TradeTuple | None (first feasible)          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ├──► CompensatingBlockDiscoverer (default)
                  │    - Lines 516-615 from matching.py
                  │    - Discrete quantity search
                  │    - First feasible trade
                  │
                  └──► [Future: Other discovery algorithms]
                       - Nash bargaining
                       - Kalai-Smorodinsky
                       - Exhaustive search
```

### 3.2 Key Components

**1. TradePotentialEvaluator (NamedTuple returns)**
```python
class TradePotential(NamedTuple):
    is_feasible: bool
    estimated_surplus: float
    preferred_direction: str | None
    confidence: float

class TradePotentialEvaluator(ABC):
    @abstractmethod
    def evaluate_pair_potential(
        self, agent_i: Agent, agent_j: Agent
    ) -> TradePotential:
        pass
```

**2. TradeDiscoverer (NamedTuple returns)**
```python
class TradeTuple(NamedTuple):
    dA_i: Decimal
    dB_i: Decimal
    dA_j: Decimal
    dB_j: Decimal
    surplus_i: float
    surplus_j: float
    price: float
    pair_name: str

class TradeDiscoverer(ABC):
    @abstractmethod
    def discover_trade(
        self, agent_i: Agent, agent_j: Agent, epsilon: float
    ) -> TradeTuple | None:
        pass
```

**3. Updated BargainingProtocol Signature** (BREAKING CHANGE)
```python
class BargainingProtocol(ProtocolBase):
    @abstractmethod
    def negotiate(
        self,
        pair: tuple[int, int],          # Agent IDs (kept for consistency)
        agents: tuple[Agent, Agent],    # NEW: Direct access to agent states
        world: WorldView                # Simulation context (tick, params, rng)
    ) -> list[Effect]:
        """
        Negotiate trade between paired agents.
        
        Args:
            pair: (agent_a_id, agent_b_id) - agent IDs
            agents: (agent_a, agent_b) - READ-ONLY access to full agent state
                    agents[0].id == pair[0], agents[1].id == pair[1] (guaranteed)
                    Protocols MUST NOT mutate agents (enforced by debug assertions)
            world: Immutable context (tick, mode, params, rng)
        
        Returns:
            [Trade(...)] if agreement reached
            [Unpair(...)] if negotiation fails
        """
        pass
```

**Why this is better**:
- Eliminates params hack entirely
- Agents already exist in TradeSystem, just pass them through
- WorldView remains immutable (controls mutation via Effect system)
- Agents are mutable but convention + debug assertions enforce read-only
- Simpler implementation, clearer intent

**4. Default Implementations**
- `QuoteBasedTradeEvaluator`: Uses `compute_surplus()` from matching.py
- `CompensatingBlockDiscoverer`: Refactored from `find_compensating_block_generic()`

**5. Refactored Core Protocol**
- Rename: `legacy.py` → `compensating_block.py`
- Rename: `LegacyBargainingProtocol` → `CompensatingBlockBargaining`
- Registry name: `"legacy_compensating_block"` → `"compensating_block"`
- Update to new signature (trivial - just pass agents to discoverer)

---

## 4. Implementation Steps

### Step 1: Create Abstraction Interfaces

**Location**: `src/vmt_engine/systems/trade_evaluation.py` (new file)

```python
"""
Trade Evaluation Abstractions

Provides protocol-agnostic interfaces for trade evaluation and discovery.
Decouples matching protocols from bargaining protocol implementations.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, NamedTuple
from decimal import Decimal

if TYPE_CHECKING:
    from ..core import Agent


# =============================================================================
# Matching Phase: Lightweight Trade Potential Evaluation
# =============================================================================

class TradePotential(NamedTuple):
    """
    Lightweight evaluation of trade potential between two agents.
    
    Used by matching protocols for pairing decisions.
    NamedTuple for zero-overhead performance.
    """
    is_feasible: bool                  # Can these agents trade?
    estimated_surplus: float           # Estimated total surplus (heuristic)
    preferred_direction: str | None    # "i_gives_A" or "i_gives_B" or None
    confidence: float                  # 0.0 to 1.0, heuristic confidence


class TradePotentialEvaluator(ABC):
    """
    Abstract interface for evaluating trade potential between agents.
    
    Used by matching protocols to make pairing decisions without
    depending on specific bargaining implementations.
    
    Implementations should be fast heuristics, not full utility calculations.
    """
    
    @abstractmethod
    def evaluate_pair_potential(
        self,
        agent_i: "Agent",
        agent_j: "Agent"
    ) -> TradePotential:
        """
        Evaluate trade potential between two agents (heuristic).
        
        This is a lightweight evaluation for pairing decisions.
        Should not perform full utility calculations or discrete search.
        
        Args:
            agent_i: First agent
            agent_j: Second agent
            
        Returns:
            TradePotential with feasibility and estimated surplus
        """
        pass


class QuoteBasedTradeEvaluator(TradePotentialEvaluator):
    """
    Default trade potential evaluator using quote overlaps.
    
    Fast heuristic based on bid/ask quotes. Does not perform
    full utility calculations. Suitable for matching phase.
    
    Uses existing compute_surplus() logic from matching.py.
    """
    
    def evaluate_pair_potential(
        self,
        agent_i: "Agent",
        agent_j: "Agent"
    ) -> TradePotential:
        """
        Evaluate using quote overlaps (existing compute_surplus logic).
        """
        from .matching import compute_surplus
        
        # Use existing compute_surplus for quote-based evaluation
        best_overlap = compute_surplus(agent_i, agent_j)
        
        if best_overlap <= 0:
            return TradePotential(
                is_feasible=False,
                estimated_surplus=0.0,
                preferred_direction=None,
                confidence=1.0  # High confidence in "no trade" result
            )
        
        # Determine preferred direction from quotes
        bid_i = agent_i.quotes.get('bid_A_in_B', 0.0)
        ask_i = agent_i.quotes.get('ask_A_in_B', 0.0)
        bid_j = agent_j.quotes.get('bid_A_in_B', 0.0)
        ask_j = agent_j.quotes.get('ask_A_in_B', 0.0)
        
        overlap_dir1 = bid_i - ask_j  # i buys A from j
        overlap_dir2 = bid_j - ask_i  # j buys from i
        
        if overlap_dir1 > overlap_dir2:
            preferred_direction = "i_gives_B"  # i buys A
        else:
            preferred_direction = "i_gives_A"  # i sells A
        
        # Confidence based on overlap magnitude (heuristic)
        max_quote = max(bid_i, ask_i, bid_j, ask_j, 1.0)
        confidence = min(1.0, best_overlap / max_quote)
        
        return TradePotential(
            is_feasible=True,
            estimated_surplus=best_overlap,
            preferred_direction=preferred_direction,
            confidence=confidence
        )


# =============================================================================
# Bargaining Phase: Full Trade Discovery
# =============================================================================

class TradeTuple(NamedTuple):
    """
    Complete trade specification.
    
    Used by bargaining protocols for negotiation.
    NamedTuple for performance (tuple overhead, named access).
    """
    dA_i: Decimal      # Change in A for agent_i
    dB_i: Decimal      # Change in B for agent_i
    dA_j: Decimal      # Change in A for agent_j
    dB_j: Decimal      # Change in B for agent_j
    surplus_i: float   # Utility gain for agent_i
    surplus_j: float   # Utility gain for agent_j
    price: float       # Price of A in terms of B
    pair_name: str     # Exchange pair name (e.g., "A<->B")


class TradeDiscoverer(ABC):
    """
    Abstract interface for discovering trade terms between agents.
    
    Each bargaining protocol can implement its own discovery algorithm.
    This allows different bargaining protocols to use different
    trade discovery strategies (compensating block, Nash bargaining, etc.)
    
    Implementations should perform full utility calculations and
    return the first feasible trade (or None if no trade exists).
    """
    
    @abstractmethod
    def discover_trade(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        epsilon: float = 1e-9
    ) -> TradeTuple | None:
        """
        Discover a mutually beneficial trade between two agents.
        
        Returns the first feasible trade found (not exhaustive search).
        Performs full utility calculations and detailed trade search.
        
        Args:
            agent_i: First agent (read-only access)
            agent_j: Second agent (read-only access)
            epsilon: Threshold for utility improvement
            
        Returns:
            TradeTuple if feasible trade exists, None otherwise
        """
        pass
```

### Step 2: Implement CompensatingBlockDiscoverer

**Location**: `src/vmt_engine/game_theory/bargaining/discovery.py` (new file)

```python
"""
Trade Discovery Algorithms

Implements various algorithms for discovering mutually beneficial trades.
These are the computational engines used by bargaining protocols.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from decimal import Decimal
from ...systems.trade_evaluation import TradeDiscoverer, TradeTuple
from ...systems.matching import generate_price_candidates
from ...core.decimal_config import quantize_quantity

if TYPE_CHECKING:
    from ...core import Agent


class CompensatingBlockDiscoverer(TradeDiscoverer):
    """
    Trade discovery using compensating block algorithm.
    
    This is the foundational VMT trade discovery algorithm. It searches
    over discrete quantities (1, 2, 3, ...) and price candidates to find
    the first mutually beneficial trade.
    
    Algorithm:
    1. Check both directions (i gives A, j gives A)
    2. For each direction with quote overlap:
       a. Try quantity dA = 1, 2, 3, ... up to max inventory
       b. Generate price candidates between ask and bid
       c. For each (dA, price) pair:
          - Calculate dB = price * dA
          - Check inventory feasibility
          - Evaluate utility improvement for both agents
          - Return first feasible trade found
    3. Return None if no feasible trade exists
    
    Refactored from find_compensating_block_generic() in matching.py
    (lines 516-615). Logic is identical, interface is cleaner.
    """
    
    def discover_trade(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        epsilon: float = 1e-9
    ) -> TradeTuple | None:
        """
        Discover first feasible trade using compensating block algorithm.
        
        Note: Agents are read-only. This method must not mutate agent state.
        """
        if not agent_i.utility or not agent_j.utility:
            return None
        
        # Current utilities
        u_i_0 = agent_i.utility.u(agent_i.inventory.A, agent_i.inventory.B)
        u_j_0 = agent_j.utility.u(agent_j.inventory.A, agent_j.inventory.B)
        
        # Try Direction 1: agent_i gives A, receives B
        result = self._search_direction(
            agent_i, agent_j,
            giver=agent_i, receiver=agent_j,
            u_i_0=u_i_0, u_j_0=u_j_0,
            epsilon=epsilon
        )
        if result:
            return result
        
        # Try Direction 2: agent_j gives A, agent_i receives A
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
        Search for feasible trade in one direction.
        
        Args:
            agent_i: First agent (for determining dA_i, dB_i)
            agent_j: Second agent (for determining dA_j, dB_j)
            giver: Agent giving A
            receiver: Agent receiving A (giving B)
            u_i_0, u_j_0: Initial utilities
            epsilon: Utility improvement threshold
            
        Returns:
            TradeTuple if feasible trade found, None otherwise
        """
        ask_giver = giver.quotes.get('ask_A_in_B', float('inf'))
        bid_receiver = receiver.quotes.get('bid_A_in_B', 0.0)
        
        if ask_giver > bid_receiver:
            return None  # No quote overlap
        
        max_dA = int(giver.inventory.A)
        if max_dA <= 0:
            return None
        
        # Discrete quantity search: 1, 2, 3, ... up to max_dA
        for dA_int in range(1, max_dA + 1):
            dA = quantize_quantity(Decimal(str(dA_int)))
            
            # Generate price candidates between ask and bid
            price_candidates = generate_price_candidates(ask_giver, bid_receiver, dA_int)
            
            for price in price_candidates:
                dB_raw = Decimal(str(price)) * dA
                dB = quantize_quantity(dB_raw)
                
                if dB <= 0:
                    continue
                
                # Check inventory constraints
                if giver.inventory.A < dA or receiver.inventory.B < dB:
                    continue
                
                # Calculate utilities with proposed trade
                # Note: We're not mutating inventories, just computing hypothetical utilities
                if giver.id == agent_i.id:
                    # agent_i gives A
                    u_i_new = agent_i.utility.u(agent_i.inventory.A - dA, agent_i.inventory.B + dB)
                    u_j_new = agent_j.utility.u(agent_j.inventory.A + dA, agent_j.inventory.B - dB)
                    dA_i, dB_i = -dA, dB
                    dA_j, dB_j = dA, -dB
                else:
                    # agent_j gives A
                    u_i_new = agent_i.utility.u(agent_i.inventory.A + dA, agent_i.inventory.B - dB)
                    u_j_new = agent_j.utility.u(agent_j.inventory.A - dA, agent_j.inventory.B + dB)
                    dA_i, dB_i = dA, -dB
                    dA_j, dB_j = -dA, dB
                
                surplus_i = u_i_new - u_i_0
                surplus_j = u_j_new - u_j_0
                
                # Check mutual benefit
                if surplus_i > epsilon and surplus_j > epsilon:
                    # Found feasible trade - return immediately
                    return TradeTuple(
                        dA_i=dA_i,
                        dB_i=dB_i,
                        dA_j=dA_j,
                        dB_j=dB_j,
                        surplus_i=surplus_i,
                        surplus_j=surplus_j,
                        price=price,
                        pair_name="A<->B"
                    )
        
        return None
```

### Step 3: Update BargainingProtocol Base Class

**Location**: `src/vmt_engine/game_theory/bargaining/base.py`

```python
"""
Bargaining Protocol Base Class

Bargaining protocols determine how paired agents negotiate trade terms.
Part of the Game Theory paradigm - strategic negotiation mechanisms.

Version: 2025.11.03 (v3 - Direct Agent Passing)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...protocols.context import WorldView
    from ...core import Agent

from ...protocols.base import Effect, ProtocolBase


class BargainingProtocol(ProtocolBase):
    """
    Base class for bargaining protocols.
    
    Bargaining protocols implement negotiation mechanisms between paired agents.
    They answer: "What terms do we agree to?"
    
    Theoretical Context:
    - Game Theory paradigm (bargaining theory, Nash program)
    - Axiomatic bargaining solutions (Nash, Kalai-Smorodinsky, etc.)
    - Strategic bargaining (Rubinstein, ultimatum games)
    
    Returns:
        List of Trade/Unpair effects
    """
    
    # Class-level version to avoid instantiation during registration
    VERSION = "unknown"

    @property
    def version(self) -> str:
        return getattr(self.__class__, "VERSION", "unknown")
    
    @abstractmethod
    def negotiate(
        self,
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: "WorldView"
    ) -> list[Effect]:
        """
        One negotiation step (may be single-tick or multi-tick).
        
        Args:
            pair: (agent_a_id, agent_b_id) - agent IDs
            agents: (agent_a, agent_b) - READ-ONLY access to full agent state
                    Guaranteed: agents[0].id == pair[0], agents[1].id == pair[1]
                    WARNING: Agents are mutable but protocols MUST NOT mutate them.
                             Mutations are only allowed via Trade effects.
                             Debug assertions verify this in development.
            world: Immutable context (tick, mode, params, rng)
        
        Returns:
            List of effects:
            - [Trade(...)] if agreement reached
            - [Unpair(..., reason="trade_failed")] if negotiation fails
            - [] if multi-tick protocol still negotiating
            - [InternalStateUpdate(...)] for multi-tick state
        
        Multi-tick protocols maintain state via InternalStateUpdate effects.
        """
        pass
    
    def on_timeout(
        self, 
        pair: tuple[int, int],
        agents: tuple["Agent", "Agent"],
        world: "WorldView"
    ) -> list[Effect]:
        """
        Called when negotiation exceeds max ticks.
        
        Default behavior: dissolve pairing.
        Override for custom timeout handling.
        """
        from ...protocols.base import Unpair
        return [Unpair(
            agent_a=pair[0],
            agent_b=pair[1],
            reason="timeout",
            protocol_name=self.name,
            tick=world.tick
        )]
```

### Step 4: Refactor Core Bargaining Protocol

**Action**: Rename and restructure `legacy.py` → `compensating_block.py`

**Location**: `src/vmt_engine/game_theory/bargaining/compensating_block.py` (rename from legacy.py)

```python
"""
Compensating Block Bargaining Protocol

Implements the foundational VMT compensating block algorithm for bilateral
barter trade negotiation. This protocol searches for the first mutually
beneficial trade using discrete quantity steps and price candidate generation.

This is the default bargaining protocol in VMT.

Version: 2025.11.03 (v3 - Restructured with Direct Agent Passing)
"""

from typing import Optional
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from .discovery import CompensatingBlockDiscoverer
from ...systems.trade_evaluation import TradeDiscoverer, TradeTuple
from ...protocols.base import Effect, Trade, Unpair
from ...protocols.context import WorldView
from ...core import Agent


@register_protocol(
    category="bargaining",
    name="compensating_block",
    description="First feasible trade using compensating block algorithm (default)",
    properties=["deterministic", "first_feasible"],
    complexity="O(K·P)",  # K = quantities tried, P = prices per quantity
    references=["VMT foundational algorithm"],
    phase="4",
)
class CompensatingBlockBargaining(BargainingProtocol):
    """
    Compensating block bargaining - the foundational VMT algorithm.
    
    Searches over discrete quantities (1, 2, 3, ...) and price candidates
    to find the first mutually beneficial barter trade. Returns Trade effect
    if successful, Unpair effect if no feasible trade exists.
    
    This is the default bargaining protocol and implements the core VMT
    trade discovery logic.
    """
    
    def __init__(self, discoverer: TradeDiscoverer | None = None):
        """
        Initialize compensating block bargaining.
        
        Args:
            discoverer: Trade discovery algorithm (default: CompensatingBlockDiscoverer)
        """
        self.discoverer = discoverer or CompensatingBlockDiscoverer()
    
    @property
    def name(self) -> str:
        return "compensating_block"
    
    @property
    def version(self) -> str:
        return "2025.11.03"
    
    VERSION = "2025.11.03"
    
    def negotiate(
        self,
        pair: tuple[int, int],
        agents: tuple[Agent, Agent],
        world: WorldView
    ) -> list[Effect]:
        """
        Negotiate trade between paired agents.
        
        Args:
            pair: (agent_a_id, agent_b_id) tuple
            agents: (agent_a, agent_b) - direct access to agent states
            world: Context (tick, params, rng)
        
        Returns:
            [Trade(...)] if successful
            [Unpair(...)] if no mutually beneficial trade found
        """
        agent_a, agent_b = agents
        epsilon = world.params.get("epsilon", 1e-9)
        
        # Discover trade using injected discovery algorithm
        # Note: discoverer must not mutate agents
        trade_tuple = self.discoverer.discover_trade(agent_a, agent_b, epsilon)
        
        if trade_tuple is None:
            # No mutually beneficial trade - unpair
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=pair[0],
                agent_b=pair[1],
                reason="trade_failed"
            )]
        
        # Convert TradeTuple to Trade effect
        return [self._trade_tuple_to_effect(pair, trade_tuple, world)]
    
    def _trade_tuple_to_effect(
        self,
        pair: tuple[int, int],
        trade_tuple: TradeTuple,
        world: WorldView
    ) -> Trade:
        """
        Convert TradeTuple to Trade effect.
        
        Args:
            pair: (agent_a_id, agent_b_id)
            trade_tuple: Discovered trade specification
            world: Context for tick
        
        Returns:
            Trade effect
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
            dB = trade_tuple.dB_i
            surplus_buyer = trade_tuple.surplus_j
            surplus_seller = trade_tuple.surplus_i
        
        return Trade(
            protocol_name=self.name,
            tick=world.tick,
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

### Step 5: Update TradeSystem to Pass Agents Directly

**Location**: `src/vmt_engine/systems/trading.py`

```python
# BEFORE (lines 104-124):
def _negotiate_trade(self, agent_a: "Agent", agent_b: "Agent", sim: "Simulation") -> None:
    """Negotiate trade between two agents using bargaining protocol."""
    # Build WorldView for trade negotiation
    world = build_trade_world_view(agent_a, agent_b, sim)  # HACK: params smuggling
    
    # Call bargaining protocol
    effects = self.bargaining_protocol.negotiate((agent_a.id, agent_b.id), world)
    
    # Apply effects
    for effect in effects:
        if isinstance(effect, Trade):
            self._apply_trade_effect(effect, sim)
        elif isinstance(effect, Unpair):
            self._apply_unpair_effect(effect, sim)

# AFTER:
def _negotiate_trade(self, agent_a: "Agent", agent_b: "Agent", sim: "Simulation") -> None:
    """Negotiate trade between two agents using bargaining protocol."""
    # Build standard WorldView (no partner state hacking needed)
    world = build_world_view_for_agent(agent_a, sim)
    
    # Add debug assertions if enabled
    if sim.params.get("debug_immutability", False):
        # Snapshot agent state before protocol call
        snapshot_a = (agent_a.inventory.A, agent_a.inventory.B)
        snapshot_b = (agent_b.inventory.A, agent_b.inventory.B)
    
    # Call bargaining protocol with direct agent access
    effects = self.bargaining_protocol.negotiate(
        (agent_a.id, agent_b.id),
        (agent_a, agent_b),  # NEW: Pass agents directly
        world
    )
    
    # Verify immutability in debug mode
    if sim.params.get("debug_immutability", False):
        assert snapshot_a == (agent_a.inventory.A, agent_a.inventory.B), \
            f"Protocol {self.bargaining_protocol.name} mutated agent {agent_a.id} inventory!"
        assert snapshot_b == (agent_b.inventory.A, agent_b.inventory.B), \
            f"Protocol {self.bargaining_protocol.name} mutated agent {agent_b.id} inventory!"
    
    # Apply effects
    for effect in effects:
        if isinstance(effect, Trade):
            self._apply_trade_effect(effect, sim)
        elif isinstance(effect, Unpair):
            self._apply_unpair_effect(effect, sim)
```

### Step 6: Remove build_trade_world_view()

**Location**: `src/vmt_engine/protocols/context_builders.py`

```python
# DELETE: Lines 170-215 (build_trade_world_view function)
# This function was a workaround for the params hack
# Now we pass agents directly, so it's not needed
```

### Step 7: Update Other Bargaining Protocols

**Update**: `src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py`

```python
# OLD signature:
def negotiate(self, pair: tuple[int, int], world: WorldView) -> list[Effect]:
    agent_i = self._build_agent_from_world(world, pair[0])  # HACK
    agent_j = self._build_agent_from_world(world, pair[1])
    # ...

# NEW signature:
def negotiate(
    self, 
    pair: tuple[int, int],
    agents: tuple[Agent, Agent],
    world: WorldView
) -> list[Effect]:
    agent_i, agent_j = agents  # Direct access!
    epsilon = world.params.get("epsilon", 1e-9)
    
    # Use discoverer to find feasible trade
    trade_tuple = self.discoverer.discover_trade(agent_i, agent_j, epsilon)
    
    if trade_tuple is None:
        return [Unpair(...)]
    
    # Apply take-it-or-leave-it surplus allocation
    # ... (rest of protocol logic)
```

**Update**: `src/vmt_engine/game_theory/bargaining/split_difference.py`

Similar changes - update signature, remove `_build_agent_from_world()`, use agents directly.

### Step 8: Update Matching Protocols

**Update**: `src/vmt_engine/game_theory/matching/greedy.py`

```python
# OLD:
from ...systems.matching import find_all_feasible_trades

def _calculate_pair_surplus(...):
    feasible_trades = find_all_feasible_trades(agent_a, agent_b, {}, epsilon)
    # ...

# NEW:
from ...systems.trade_evaluation import TradePotentialEvaluator, QuoteBasedTradeEvaluator

class GreedySurplusMatching(MatchingProtocol):
    def __init__(self, evaluator: TradePotentialEvaluator | None = None):
        """
        Initialize greedy surplus matching.
        
        Args:
            evaluator: Trade potential evaluator (default: QuoteBasedTradeEvaluator)
        """
        self.evaluator = evaluator or QuoteBasedTradeEvaluator()
    
    def _calculate_pair_surplus(self, agent_a, agent_b, distance, beta):
        """Calculate surplus for pairing decision (lightweight)."""
        # Use lightweight evaluation instead of full trade discovery
        potential = self.evaluator.evaluate_pair_potential(agent_a, agent_b)
        
        if not potential.is_feasible:
            return (0.0, 0.0, distance)
        
        # Use estimated surplus for pairing decision
        estimated_surplus = potential.estimated_surplus
        discounted_surplus = estimated_surplus * (beta ** distance)
        
        return (estimated_surplus, discounted_surplus, distance)
```

### Step 9: Update Protocol Factory and Registry

**Update**: `src/scenarios/protocol_factory.py`

```python
def get_bargaining_protocol(protocol_config: Optional[Union[str, dict[str, Any]]]):
    """
    Instantiate a bargaining protocol via the registry.
    
    Args:
        protocol_config: Either a string (protocol name) or dict with 'name' and optional 'params'
            Examples:
                "compensating_block"
                {"name": "split_difference"}
                {"name": "take_it_or_leave_it", "params": {"proposer_power": 0.9}}
    
    Returns:
        Instantiated protocol instance
    """
    from vmt_engine.protocols.registry import ProtocolRegistry
    
    if protocol_config is None:
        name = "compensating_block"  # CHANGED: New default name
        params = {}
    elif isinstance(protocol_config, str):
        name = protocol_config
        params = {}
    elif isinstance(protocol_config, dict):
        name = protocol_config.get('name', "compensating_block")  # CHANGED
        params = protocol_config.get('params', {})
    else:
        raise ValueError(f"protocol_config must be str or dict, got {type(protocol_config)}")
    
    cls = ProtocolRegistry.get_protocol_class(name, "bargaining")
    return cls(**params)
```

**Update**: `src/vmt_engine/game_theory/bargaining/__init__.py`

```python
"""
Bargaining Protocols - Game Theory Paradigm

Bargaining protocols determine how paired agents negotiate trade terms.
These protocols implement strategic negotiation mechanisms from bargaining theory.

Available Protocols:
- compensating_block: Foundational VMT algorithm (first feasible trade) [DEFAULT]
- split_difference: Equal surplus division (Nash bargaining)
- take_it_or_leave_it: Asymmetric bargaining power (ultimatum game)

Theoretical Context:
- Axiomatic bargaining solutions
- Strategic bargaining games
- Nash program

Version: Post-Decoupling (v3)
"""

from .base import BargainingProtocol
from .compensating_block import CompensatingBlockBargaining
from .split_difference import SplitDifference
from .take_it_or_leave_it import TakeItOrLeaveIt

__all__ = [
    "BargainingProtocol",
    "CompensatingBlockBargaining",
    "SplitDifference",
    "TakeItOrLeaveIt",
]
```

### Step 10: Clean Up Legacy Code

**Update**: `src/vmt_engine/systems/matching.py`

```python
# REMOVE:
# - find_all_feasible_trades() [lines 619-662]
# - find_best_trade() [lines 665-710]
# - find_compensating_block_generic() [lines 516-615] ← MOVED to CompensatingBlockDiscoverer

# KEEP:
# - compute_surplus() [used by QuoteBasedTradeEvaluator]
# - choose_partner() [still used by matching protocols]
# - generate_price_candidates() [used by CompensatingBlockDiscoverer]
# - improves() [utility helper]
# - execute_trade_generic() [trade execution]
```

### Step 11: Migrate All Scenarios

**Files to Update**:
- All YAML files in `scenarios/` directories
- `docs/structures/comprehensive_scenario_template.yaml`
- Test helper files
- README.md

**Change Pattern**:
```yaml
# OLD:
bargaining_protocol: "legacy_compensating_block"

# NEW:
bargaining_protocol: "compensating_block"
```

**Automated Migration**:
```bash
# Find and replace in all YAML files
find scenarios/ -name "*.yaml" -type f -exec sed -i 's/legacy_compensating_block/compensating_block/g' {} +
find tests/ -name "*.py" -type f -exec sed -i 's/legacy_compensating_block/compensating_block/g' {} +
find docs/ -name "*.yaml" -type f -exec sed -i 's/legacy_compensating_block/compensating_block/g' {} +
```

---

## 5. Testing Strategy

### 5.1 Unit Tests

**New Components**:

**Test File**: `tests/test_trade_evaluation.py`

```python
import pytest
from decimal import Decimal
from src.vmt_engine.systems.trade_evaluation import (
    TradePotential,
    TradePotentialEvaluator,
    QuoteBasedTradeEvaluator,
    TradeTuple,
    TradeDiscoverer,
)
from src.vmt_engine.game_theory.bargaining.discovery import CompensatingBlockDiscoverer
from tests.helpers.builders import build_agent


class TestTradePotentialEvaluator:
    """Test the lightweight evaluation interface for matching."""
    
    def test_quote_based_evaluator_no_overlap(self):
        """No quote overlap should return infeasible."""
        agent_i = build_agent(id=1, inv_A=10, inv_B=10, quotes={'bid_A_in_B': 1.0, 'ask_A_in_B': 2.0})
        agent_j = build_agent(id=2, inv_A=10, inv_B=10, quotes={'bid_A_in_B': 1.0, 'ask_A_in_B': 2.0})
        
        evaluator = QuoteBasedTradeEvaluator()
        potential = evaluator.evaluate_pair_potential(agent_i, agent_j)
        
        assert not potential.is_feasible
        assert potential.estimated_surplus == 0.0
    
    def test_quote_based_evaluator_with_overlap(self):
        """Quote overlap should return feasible with estimated surplus."""
        agent_i = build_agent(id=1, inv_A=10, inv_B=10, quotes={'bid_A_in_B': 3.0, 'ask_A_in_B': 2.0})
        agent_j = build_agent(id=2, inv_A=10, inv_B=10, quotes={'bid_A_in_B': 2.5, 'ask_A_in_B': 1.0})
        
        evaluator = QuoteBasedTradeEvaluator()
        potential = evaluator.evaluate_pair_potential(agent_i, agent_j)
        
        assert potential.is_feasible
        assert potential.estimated_surplus > 0


class TestCompensatingBlockDiscoverer:
    """Test the compensating block trade discovery algorithm."""
    
    def test_discover_trade_no_overlap(self):
        """No quote overlap should return None."""
        agent_i = build_agent(id=1, inv_A=10, inv_B=10, quotes={'bid_A_in_B': 1.0, 'ask_A_in_B': 2.0})
        agent_j = build_agent(id=2, inv_A=10, inv_B=10, quotes={'bid_A_in_B': 1.0, 'ask_A_in_B': 2.0})
        
        discoverer = CompensatingBlockDiscoverer()
        result = discoverer.discover_trade(agent_i, agent_j, epsilon=1e-9)
        
        assert result is None
    
    def test_discover_trade_with_overlap(self):
        """Quote overlap with utility improvement should return TradeTuple."""
        # Build agents with overlapping quotes and linear utility
        agent_i = build_agent(
            id=1, 
            inv_A=Decimal("5"), 
            inv_B=Decimal("15"),
            quotes={'bid_A_in_B': 3.0, 'ask_A_in_B': 2.0},
            utility_type="linear"
        )
        agent_j = build_agent(
            id=2,
            inv_A=Decimal("15"),
            inv_B=Decimal("5"),
            quotes={'bid_A_in_B': 2.5, 'ask_A_in_B': 1.0},
            utility_type="linear"
        )
        
        discoverer = CompensatingBlockDiscoverer()
        result = discoverer.discover_trade(agent_i, agent_j, epsilon=1e-9)
        
        assert result is not None
        assert isinstance(result, TradeTuple)
        assert result.surplus_i > 0
        assert result.surplus_j > 0
        assert result.price >= 1.0  # Between ask_j and bid_i
        assert result.price <= 3.0
    
    def test_discoverer_matches_legacy_implementation(self):
        """Verify new discoverer produces identical results to old implementation."""
        # This test will compare against the old find_compensating_block_generic
        # before it's removed
        pass  # TODO: Implement comparison test


class TestImmutability:
    """Test that discoverers don't mutate agent state."""
    
    def test_discoverer_does_not_mutate_agents(self):
        """Verify trade discovery doesn't mutate agent inventories."""
        agent_i = build_agent(id=1, inv_A=Decimal("10"), inv_B=Decimal("10"))
        agent_j = build_agent(id=2, inv_A=Decimal("10"), inv_B=Decimal("10"))
        
        # Snapshot state
        inv_i_before = (agent_i.inventory.A, agent_i.inventory.B)
        inv_j_before = (agent_j.inventory.A, agent_j.inventory.B)
        
        # Call discoverer
        discoverer = CompensatingBlockDiscoverer()
        result = discoverer.discover_trade(agent_i, agent_j)
        
        # Verify no mutation
        assert (agent_i.inventory.A, agent_i.inventory.B) == inv_i_before
        assert (agent_j.inventory.A, agent_j.inventory.B) == inv_j_before
```

### 5.2 Integration Tests

**Test File**: `tests/test_bargaining_refactor_integration.py`

```python
def test_compensating_block_protocol_with_direct_agents():
    """Test new protocol signature works end-to-end."""
    from src.vmt_engine.game_theory.bargaining.compensating_block import CompensatingBlockBargaining
    from src.vmt_engine.protocols.context import WorldView
    from tests.helpers.builders import build_agent, build_world_view
    
    # Build agents and world
    agent_a = build_agent(id=1, inv_A=10, inv_B=10)
    agent_b = build_agent(id=2, inv_A=10, inv_B=10)
    world = build_world_view(tick=0)
    
    # Call protocol with new signature
    protocol = CompensatingBlockBargaining()
    effects = protocol.negotiate(
        (agent_a.id, agent_b.id),
        (agent_a, agent_b),
        world
    )
    
    # Should return Trade or Unpair
    assert len(effects) > 0
    assert isinstance(effects[0], (Trade, Unpair))


def test_all_bargaining_protocols_use_new_signature():
    """Verify all bargaining protocols updated to new signature."""
    from src.vmt_engine.protocols.registry import ProtocolRegistry
    import inspect
    
    for name in ProtocolRegistry.list_protocols("bargaining"):
        protocol_cls = ProtocolRegistry.get_protocol_class(name, "bargaining")
        protocol = protocol_cls()
        
        # Check signature
        sig = inspect.signature(protocol.negotiate)
        params = list(sig.parameters.keys())
        
        assert params == ['self', 'pair', 'agents', 'world'], \
            f"Protocol {name} has wrong signature: {params}"
```

### 5.3 Determinism Tests

**Test File**: `tests/test_refactor_determinism.py`

```python
def test_decoupled_simulation_deterministic():
    """Run simulation twice with same seed, verify identical outcomes."""
    from src.scenarios.loader import ScenarioLoader
    from src.vmt_launcher.launcher import run_simulation
    
    scenario_path = "scenarios/baseline/baseline_2agent_simple.yaml"
    
    # Run 1
    sim1 = run_simulation(scenario_path, seed=42, headless=True)
    final_state_1 = (
        sim1.agents[0].inventory.A,
        sim1.agents[0].inventory.B,
        sim1.agents[1].inventory.A,
        sim1.agents[1].inventory.B,
    )
    
    # Run 2
    sim2 = run_simulation(scenario_path, seed=42, headless=True)
    final_state_2 = (
        sim2.agents[0].inventory.A,
        sim2.agents[0].inventory.B,
        sim2.agents[1].inventory.A,
        sim2.agents[1].inventory.B,
    )
    
    # Must be identical
    assert final_state_1 == final_state_2
```

### 5.4 Debug Assertions for Immutability

Enable in test scenarios:

```yaml
# scenarios/test/test_immutability.yaml
parameters:
  debug_immutability: true  # Enable runtime checks
```

Or in test code:

```python
def test_protocol_immutability_enforcement():
    """Test debug assertions catch protocol mutations."""
    sim = create_test_simulation(debug_immutability=True)
    
    # Create protocol that deliberately mutates (for testing)
    class BadProtocol(BargainingProtocol):
        def negotiate(self, pair, agents, world):
            agents[0].inventory.A += 1  # ILLEGAL mutation
            return []
    
    # Should raise assertion error
    with pytest.raises(AssertionError, match="mutated agent"):
        sim.trade_system.bargaining_protocol = BadProtocol()
        sim.step()
```

---

## 6. Migration Strategy (Atomic Change)

### Single PR with Phases

**Phase 1: Add New Code** (non-breaking)
1. Create `trade_evaluation.py`
2. Create `discovery.py`
3. Write unit tests for new components
4. All existing tests still pass

**Phase 2: Update Interfaces** (breaking changes)
1. Update `BargainingProtocol.negotiate()` signature
2. Update `TradeSystem._negotiate_trade()` to pass agents
3. Remove `build_trade_world_view()`
4. Rename `legacy.py` → `compensating_block.py`
5. Update all bargaining protocols to new signature
6. Update all matching protocols to use evaluators
7. Update protocol factory defaults
8. All tests updated and passing

**Phase 3: Cleanup**
1. Remove deprecated functions from `matching.py`
2. Migrate all scenario files
3. Update documentation

**Phase 4: Validation**
1. Run full test suite
2. Run all baseline scenarios
3. Verify determinism
4. Performance benchmarks

---

## 7. Breaking Changes Summary

### API Changes

**1. BargainingProtocol.negotiate() signature**
```python
# OLD:
def negotiate(self, pair: tuple[int, int], world: WorldView) -> list[Effect]:

# NEW:
def negotiate(
    self, 
    pair: tuple[int, int],
    agents: tuple[Agent, Agent],
    world: WorldView
) -> list[Effect]:
```

**2. Protocol registry name**
```python
# OLD:
"legacy_compensating_block"

# NEW:
"compensating_block"
```

**3. Removed functions**
```python
# From src/vmt_engine/systems/matching.py:
- find_all_feasible_trades()
- find_best_trade()
- find_compensating_block_generic()

# From src/vmt_engine/protocols/context_builders.py:
- build_trade_world_view()
```

**4. File renames**
```python
# OLD:
src/vmt_engine/game_theory/bargaining/legacy.py

# NEW:
src/vmt_engine/game_theory/bargaining/compensating_block.py
```

### Migration Path for Custom Protocols

If you have custom bargaining protocols:

```python
# OLD implementation:
class MyBargainingProtocol(BargainingProtocol):
    def negotiate(self, pair, world):
        # Build agents from WorldView (params hack)
        agent_i = self._build_agent_from_world(world, pair[0])
        agent_j = self._build_agent_from_world(world, pair[1])
        
        # ... discovery logic ...

# NEW implementation:
class MyBargainingProtocol(BargainingProtocol):
    def negotiate(self, pair, agents, world):
        # Agents passed directly - no extraction needed!
        agent_i, agent_j = agents
        
        # ... same discovery logic ...
```

---

## 8. File Inventory

### New Files Created

1. `src/vmt_engine/systems/trade_evaluation.py` (~250 lines)
   - `TradePotential` (NamedTuple)
   - `TradePotentialEvaluator` (ABC)
   - `QuoteBasedTradeEvaluator` (implementation)
   - `TradeTuple` (NamedTuple)
   - `TradeDiscoverer` (ABC)

2. `src/vmt_engine/game_theory/bargaining/discovery.py` (~200 lines)
   - `CompensatingBlockDiscoverer` (implementation)

3. `tests/test_trade_evaluation.py` (~150 lines)
   - Unit tests for new abstractions

### Files Renamed

1. `src/vmt_engine/game_theory/bargaining/legacy.py` → `compensating_block.py`

### Files Modified

1. `src/vmt_engine/game_theory/bargaining/base.py`
   - Update `negotiate()` signature

2. `src/vmt_engine/game_theory/bargaining/compensating_block.py`
   - Refactor to use `CompensatingBlockDiscoverer`
   - Update to new signature

3. `src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py`
   - Update to new signature
   - Use `TradeDiscoverer`

4. `src/vmt_engine/game_theory/bargaining/split_difference.py`
   - Update to new signature
   - Use `TradeDiscoverer`

5. `src/vmt_engine/game_theory/bargaining/__init__.py`
   - Update imports

6. `src/vmt_engine/game_theory/matching/greedy.py`
   - Use `TradePotentialEvaluator`

7. `src/vmt_engine/systems/matching.py`
   - Remove deprecated functions
   - Keep `compute_surplus()`, `generate_price_candidates()`

8. `src/vmt_engine/systems/trading.py`
   - Update `_negotiate_trade()` to pass agents
   - Add debug immutability assertions

9. `src/vmt_engine/protocols/context_builders.py`
   - Remove `build_trade_world_view()`

10. `src/scenarios/protocol_factory.py`
    - Update default to `"compensating_block"`

11. All scenario YAML files (~15 files)
    - Replace `"legacy_compensating_block"` → `"compensating_block"`

12. Test files (~10 files)
    - Update protocol names
    - Update to new signatures

13. Documentation files
    - README.md
    - Technical manual
    - Protocol documentation

### Files Deleted

None (removed functions, not files)

### Lines of Code Impact

- **Added**: ~600 lines (new abstractions, implementations, tests)
- **Removed**: ~500 lines (deprecated functions, params hack, old extraction logic)
- **Modified**: ~300 lines (signature updates, refactoring)
- **Net change**: ~+100 lines (abstractions add clarity, slight overhead)

---

## 9. Success Criteria

✅ **Decoupling Achieved**: Matching protocols work independently using `TradePotentialEvaluator`

✅ **Params Hack Eliminated**: Agents passed directly, no magic string keys

✅ **Protocol Independence**: Each bargaining protocol can use different `TradeDiscoverer`

✅ **Behavioral Correctness**: Matching uses heuristics, bargaining uses full discovery

✅ **Performance**: NamedTuples provide zero-overhead data passing

✅ **Code Quality**: Clear separation of concerns, no circular dependencies

✅ **Backward Compatibility**: All scenarios migrated, working with new protocol name

✅ **Immutability Enforcement**: Debug assertions catch protocol violations

✅ **Determinism**: Same seed produces identical outcomes

✅ **Core Algorithm Preserved**: Compensating block maintains exact behavior

✅ **Accurate Naming**: "Legacy" replaced with "compensating_block"

---

## 10. Implementation Checklist

### Phase 1: Add New Code ✓

- [ ] Create `src/vmt_engine/systems/trade_evaluation.py`
  - [ ] Define `TradePotential` (NamedTuple)
  - [ ] Define `TradePotentialEvaluator` (ABC)
  - [ ] Implement `QuoteBasedTradeEvaluator`
  - [ ] Define `TradeTuple` (NamedTuple)
  - [ ] Define `TradeDiscoverer` (ABC)
- [ ] Create `src/vmt_engine/game_theory/bargaining/discovery.py`
  - [ ] Implement `CompensatingBlockDiscoverer`
  - [ ] Copy logic from `find_compensating_block_generic()` (matching.py:516-615)
  - [ ] Adapt to return `TradeTuple | None`
- [ ] Write unit tests (`tests/test_trade_evaluation.py`)
  - [ ] Test `QuoteBasedTradeEvaluator`
  - [ ] Test `CompensatingBlockDiscoverer`
  - [ ] Test immutability (discoverers don't mutate)
- [ ] Verify all existing tests still pass

### Phase 2: Update Interfaces ✓

- [ ] Update `src/vmt_engine/game_theory/bargaining/base.py`
  - [ ] Change `negotiate()` signature to include `agents` parameter
  - [ ] Update docstring
- [ ] Rename `src/vmt_engine/game_theory/bargaining/legacy.py` → `compensating_block.py`
  - [ ] Rename class: `LegacyBargainingProtocol` → `CompensatingBlockBargaining`
  - [ ] Update registry name: `"legacy_compensating_block"` → `"compensating_block"`
  - [ ] Add `discoverer` injection
  - [ ] Update to new `negotiate()` signature
  - [ ] Remove `_build_agent_from_world()` (no longer needed)
  - [ ] Update `_trade_tuple_to_effect()`
- [ ] Update `src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py`
  - [ ] Update to new signature
  - [ ] Add `discoverer` injection
  - [ ] Remove `_build_agent_from_world()`
- [ ] Update `src/vmt_engine/game_theory/bargaining/split_difference.py`
  - [ ] Update to new signature
  - [ ] Add `discoverer` injection
  - [ ] Remove `_build_agent_from_world()`
- [ ] Update `src/vmt_engine/game_theory/bargaining/__init__.py`
  - [ ] Update imports
  - [ ] Update docstring
- [ ] Update `src/vmt_engine/systems/trading.py`
  - [ ] Modify `_negotiate_trade()` to pass agents
  - [ ] Replace `build_trade_world_view()` with `build_world_view_for_agent()`
  - [ ] Add debug immutability assertions
- [ ] Remove `src/vmt_engine/protocols/context_builders.py::build_trade_world_view()`
- [ ] Update `src/vmt_engine/game_theory/matching/greedy.py`
  - [ ] Add `evaluator` injection
  - [ ] Replace `find_all_feasible_trades()` with `TradePotentialEvaluator`
- [ ] Update `src/scenarios/protocol_factory.py`
  - [ ] Change default to `"compensating_block"`
- [ ] Update all tests to new signature
  - [ ] `tests/test_split_difference.py`
  - [ ] `tests/test_mode_integration.py`
  - [ ] `tests/test_performance.py`
  - [ ] `tests/test_resource_claiming.py`
  - [ ] `tests/test_protocol_yaml_config.py`
  - [ ] `tests/helpers/builders.py`
- [ ] Run full test suite - all tests should pass

### Phase 3: Cleanup ✓

- [ ] Remove from `src/vmt_engine/systems/matching.py`:
  - [ ] `find_all_feasible_trades()` (lines 619-662)
  - [ ] `find_best_trade()` (lines 665-710)
  - [ ] `find_compensating_block_generic()` (lines 516-615)
- [ ] Migrate all scenario YAML files:
  - [ ] `scenarios/baseline/*.yaml` (5 files)
  - [ ] `scenarios/demos/*.yaml` (3 files)
  - [ ] `scenarios/curated/*.yaml` (1 file)
  - [ ] `scenarios/test/*.yaml` (6 files)
  - [ ] `docs/structures/comprehensive_scenario_template.yaml`
- [ ] Update documentation:
  - [ ] `README.md`
  - [ ] `docs/2_technical_manual.md`
  - [ ] Protocol documentation
- [ ] Run full test suite - all tests should pass

### Phase 4: Validation ✓

- [ ] Run all baseline scenarios
  - [ ] Verify successful completion
  - [ ] Compare against pre-refactor telemetry snapshots
- [ ] Run determinism tests
  - [ ] Same seed produces identical outcomes
  - [ ] Test with all baseline scenarios
- [ ] Performance benchmarks
  - [ ] Verify no regression
  - [ ] Matching phase should be faster (heuristic vs full calc)
- [ ] Code review
  - [ ] Check for unused imports
  - [ ] Verify naming consistency
  - [ ] Lint/format check
- [ ] Update CHANGELOG.md

---

## 11. Risk Mitigation

### Risk 1: Protocol Mutation Violations

**Likelihood**: Medium  
**Impact**: High (corrupted simulation state)

**Mitigation**:
- Debug assertions in `TradeSystem._negotiate_trade()`
- Unit tests verify discoverers don't mutate
- Clear documentation in `BargainingProtocol.negotiate()` docstring
- Consider adding `@property` wrappers for critical fields in future

### Risk 2: Signature Mismatch Errors

**Likelihood**: Medium (breaking change)  
**Impact**: Medium (compile-time error)

**Mitigation**:
- Update all protocols atomically in one PR
- Comprehensive test coverage catches signature errors
- Grep for all `negotiate()` implementations before committing

### Risk 3: Behavioral Divergence

**Likelihood**: Low  
**Impact**: High

**Mitigation**:
- `CompensatingBlockDiscoverer` is direct refactor of existing logic
- Determinism tests verify identical outcomes
- Baseline scenario comparisons
- Unit test comparing new vs old implementation

### Risk 4: Performance Regression

**Likelihood**: Very Low  
**Impact**: Medium

**Mitigation**:
- NamedTuples have minimal overhead
- Matching phase uses heuristics (faster than before)
- Bargaining phase unchanged algorithmically
- Performance benchmarks in test suite

---

## 12. Future Enhancements

### 12.1 Alternative Discovery Algorithms

Once abstraction is in place:

```python
class NashBargainingDiscoverer(TradeDiscoverer):
    """Find trade maximizing Nash product."""
    def discover_trade(self, agent_i, agent_j, epsilon):
        # Optimization-based Nash solution
        pass

class KalaiSmorodinskyDiscoverer(TradeDiscoverer):
    """Kalai-Smorodinsky bargaining solution."""
    pass

class ExhaustiveSearchDiscoverer(TradeDiscoverer):
    """Return all Pareto-optimal trades for ranking."""
    def discover_all_trades(self, agent_i, agent_j, epsilon) -> list[TradeTuple]:
        pass
```

### 12.2 Enhanced Evaluators

```python
class UtilityBasedEvaluator(TradePotentialEvaluator):
    """Uses full utility calculations with caching."""
    def __init__(self, cache_size=1000):
        self.cache = LRUCache(cache_size)

class MLEvaluator(TradePotentialEvaluator):
    """ML model predicts trade potential from features."""
    pass
```

### 12.3 Composition Patterns

```python
class FallbackDiscoverer(TradeDiscoverer):
    """Try primary, fall back to secondary."""
    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback
    
    def discover_trade(self, agent_i, agent_j, epsilon):
        result = self.primary.discover_trade(agent_i, agent_j, epsilon)
        return result or self.fallback.discover_trade(agent_i, agent_j, epsilon)
```

---

## 13. Summary of Key Decisions

1. **Keep `pair` parameter**: Consistency with other protocol signatures
2. **Convention + debug assertions**: Practical immutability enforcement
3. **Keep WorldView**: No lighter context object, maintain consistency
4. **One atomic PR**: Interface fix + decoupling together
5. **Debug assertions**: Runtime checks for protocol mutations
6. **Agent order guarantee**: `agents[0].id == pair[0]` always true
7. **NamedTuples**: Performance over dataclasses
8. **Direct agent passing**: Eliminates params hack completely

---

**Author**: AI Assistant  
**Reviewers**: [To be filled]  
**Last Updated**: 2025-11-03  
**Version**: 3.0 (Direct Agent Passing)

