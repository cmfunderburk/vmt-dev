# Decoupling Matching from Bargaining: Implementation Plan v2

**Date**: 2025-11-03  
**Status**: Planning  
**Priority**: Critical (Blocking Technical Debt)  
**Version**: 2.0 (Revised)

## Revision History

- **v1 (2025-01-XX)**: Initial plan, identified core issues
- **v2 (2025-11-03)**: Fixed critical flaw - legacy.py is not legacy, it's the core implementation. Updated to preserve algorithm while restructuring.

---

## Executive Summary

Currently, matching protocols (Phase 2) are tightly coupled to a specific bargaining protocol implementation (`find_compensating_block_generic()`). This violates separation of concerns and prevents independent protocol development. 

**Critical Insight**: The "legacy" bargaining protocol is actually the **default, primary implementation** of the VMT compensating block algorithm. We're not deprecating this - we're restructuring it into a proper abstraction layer.

This document outlines a comprehensive refactoring plan to:
1. Decouple matching from bargaining
2. Preserve the compensating block algorithm
3. Rename "legacy" to more accurate terminology
4. Enable future protocol diversity

---

## 1. Problem Analysis

### 1.1 Current Architecture Issues

**Tight Coupling Chain:**
```
MatchingProtocol.find_matches()
  ↓
find_all_feasible_trades() [in matching.py]
  ↓ (hardcoded)
find_compensating_block_generic() [in matching.py, lines 516-615]
  ↓
Same calculation used by BargainingProtocol.negotiate()
```

**Problems Identified:**

1. **Violation of Protocol Independence**: Matching protocols cannot operate without knowledge of bargaining implementation details.

2. **Code Duplication**: The same trade calculation runs twice:
   - Phase 2 (Matching): To evaluate pair potential
   - Phase 4 (Bargaining): To discover actual trade terms

3. **Misplaced Responsibility**: `find_compensating_block_generic()` is in `matching.py` but is actually bargaining logic.

4. **Misleading Naming**: `legacy.py` is the DEFAULT protocol, not legacy code to be removed.

5. **Algorithm Location**: The core compensating block algorithm (lines 516-615 in matching.py) is buried in a utility module instead of being in a proper protocol class.

### 1.2 Current Usage Patterns

**What Matching Protocols Actually Need:**
- Lightweight evaluation: "Can these agents trade?"
- Surplus estimation: "What's the potential total surplus?"
- Fast, heuristic-based decisions for pairing

**What Bargaining Protocols Actually Need:**
- Full trade discovery: "What trade terms are mutually beneficial?"
- Detailed trade specification: quantities, prices, surpluses
- Protocol-specific negotiation logic

**Current Reality:**
- Both use `find_all_feasible_trades()` → `find_compensating_block_generic()`
- Matching gets more detail than needed (performance waste)
- Bargaining is constrained to one implementation (no protocol diversity)

### 1.3 The "Legacy" Misnomer

**Current State:**
```python
# src/vmt_engine/game_theory/bargaining/legacy.py
@register_protocol(name="legacy_compensating_block", ...)
class LegacyBargainingProtocol:
    # Uses find_best_trade() → find_compensating_block_generic()
```

**Usage Reality:**
- Default protocol in `protocol_factory.py`
- Used throughout test suite
- Documented as primary protocol in README
- Implements the foundational VMT algorithm

**Conclusion**: This is NOT legacy code to deprecate - it's the **core implementation** that needs proper naming and structure.

---

## 2. Design Goals

### 2.1 Primary Objectives

1. **Complete Decoupling**: Matching protocols must operate independently of bargaining protocol implementations.

2. **Protocol Flexibility**: Bargaining protocols should own their trade discovery algorithms.

3. **Performance Optimization**: Matching should use fast heuristics; bargaining should use full calculations.

4. **Clear Separation of Concerns**:
   - Matching: "Who pairs with whom?" (uses lightweight evaluation)
   - Bargaining: "What terms do we agree on?" (uses full trade discovery)

5. **Preserve Core Algorithm**: The compensating block algorithm (find_compensating_block_generic) is fundamental VMT logic - restructure it, don't remove it.

6. **Accurate Naming**: Rename "legacy" to reflect actual purpose and behavior.

7. **Backward Compatibility During Migration**: Existing scenarios should continue working during transition.

### 2.2 Non-Goals

- Changing the protocol interface contracts (search/matching/bargaining base classes)
- Modifying the simulation phase structure
- Changing the Effect system
- Deprecating the compensating block algorithm (it's core functionality)

---

## 3. Proposed Architecture

### 3.1 Abstraction Layers

```
┌─────────────────────────────────────────────────────────┐
│                 Matching Protocols                        │
│  (Phase 2: Pair Selection)                               │
│  Uses: TradePotentialEvaluator (lightweight)              │
└─────────────────┬─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│         TradePotentialEvaluator Interface               │
│  - evaluate_pair_potential(agent_i, agent_j)            │
│  - Returns: TradePotential (surplus estimate, feasibility)│
└─────────────────┬─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│    QuoteBasedTradeEvaluator (default implementation)    │
│  - Uses quote overlaps (fast heuristic)                  │
│  - compute_surplus() logic                               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                 Bargaining Protocols                     │
│  (Phase 4: Trade Negotiation)                           │
│  Uses: TradeDiscoverer (full calculation)               │
└─────────────────┬─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│         TradeDiscoverer Interface                       │
│  - discover_trade(agent_i, agent_j, params)             │
│  - Returns: TradeTuple | None (first feasible)          │
└─────────────────┬─────────────────────────────────────────┘
                  │
                  ├──► CompensatingBlockDiscoverer (default)
                  │    - Lines 516-615 from matching.py
                  │    - Discrete quantity search
                  │    - Price candidate generation
                  │    - First feasible trade
                  │
                  └──► [Future: Other discovery algorithms]
                       - Nash bargaining
                       - Kalai-Smorodinsky
                       - Linear search variants
```

### 3.2 Key Components

**1. TradePotentialEvaluator (Protocol-Agnostic)**
- Interface for matching protocols to evaluate pair potential
- Lightweight, heuristic-based
- Does not depend on bargaining implementations
- Injectable into matching protocols

**2. TradeDiscoverer (Protocol-Specific)**
- Interface for bargaining protocols to discover trade terms
- Each bargaining protocol can implement its own discovery
- Full utility calculations, detailed trade information
- Injectable into bargaining protocols

**3. Default Implementations**
- `QuoteBasedTradeEvaluator`: Fast heuristic using quote overlaps
- `CompensatingBlockDiscoverer`: Current `find_compensating_block_generic()` logic (lines 516-615)

**4. Refactored Core Protocol**
- Rename: `legacy.py` → `compensating_block.py`
- Rename: `LegacyBargainingProtocol` → `CompensatingBlockBargaining`
- Registry name: `"legacy_compensating_block"` → `"compensating_block"`
- Keep as default protocol

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
from dataclasses import dataclass
from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from ..core import Agent


@dataclass
class TradePotential:
    """
    Lightweight evaluation of trade potential between two agents.
    
    Used by matching protocols for pairing decisions.
    """
    is_feasible: bool  # Can these agents trade?
    estimated_surplus: float  # Estimated total surplus (heuristic)
    preferred_direction: str | None  # "i_gives_A" or "i_gives_B" or None
    confidence: float  # 0.0 to 1.0, heuristic confidence in estimate


class TradePotentialEvaluator(ABC):
    """
    Abstract interface for evaluating trade potential between agents.
    
    Used by matching protocols to make pairing decisions without
    depending on specific bargaining implementations.
    """
    
    @abstractmethod
    def evaluate_pair_potential(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        params: dict[str, any] | None = None
    ) -> TradePotential:
        """
        Evaluate trade potential between two agents.
        
        This is a lightweight heuristic evaluation for pairing decisions.
        Does not perform full utility calculations.
        
        Args:
            agent_i: First agent
            agent_j: Second agent
            params: Optional simulation parameters
            
        Returns:
            TradePotential indicating feasibility and estimated surplus
        """
        pass


@dataclass
class TradeTuple:
    """
    Complete trade specification.
    
    Used by bargaining protocols for negotiation.
    """
    dA_i: Decimal  # Change in A for agent_i
    dB_i: Decimal  # Change in B for agent_i
    dA_j: Decimal  # Change in A for agent_j
    dB_j: Decimal  # Change in B for agent_j
    surplus_i: float  # Utility gain for agent_i
    surplus_j: float  # Utility gain for agent_j
    price: float  # Price of A in terms of B
    pair_name: str  # Exchange pair name (e.g., "A<->B")


class TradeDiscoverer(ABC):
    """
    Abstract interface for discovering trade terms between agents.
    
    Each bargaining protocol can implement its own discovery algorithm.
    This allows different bargaining protocols to use different
    trade discovery strategies (e.g., compensating block, Nash bargaining, etc.)
    """
    
    @abstractmethod
    def discover_trade(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        params: dict[str, any] | None = None,
        epsilon: float = 1e-9
    ) -> TradeTuple | None:
        """
        Discover a mutually beneficial trade between two agents.
        
        Returns the first feasible trade found (not exhaustive search).
        This performs full utility calculations and detailed trade search.
        
        Args:
            agent_i: First agent
            agent_j: Second agent
            params: Optional simulation parameters
            epsilon: Threshold for utility improvement
            
        Returns:
            TradeTuple if feasible trade exists, None otherwise
        """
        pass
```

### Step 2: Implement Default TradePotentialEvaluator

**Location**: `src/vmt_engine/systems/trade_evaluation.py` (continued)

```python
class QuoteBasedTradeEvaluator(TradePotentialEvaluator):
    """
    Default trade potential evaluator using quote overlaps.
    
    Fast heuristic based on bid/ask quotes. Does not perform
    full utility calculations. Suitable for matching phase.
    """
    
    def evaluate_pair_potential(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        params: dict[str, any] | None = None
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
        overlap_dir2 = bid_j - ask_i  # j buys A from i
        
        if overlap_dir1 > overlap_dir2:
            preferred_direction = "i_gives_B"  # i buys A (gives B)
        else:
            preferred_direction = "i_gives_A"  # j buys A (i gives A)
        
        # Confidence based on overlap magnitude (heuristic)
        confidence = min(1.0, best_overlap / max(bid_i, ask_i, bid_j, ask_j, 1.0))
        
        return TradePotential(
            is_feasible=True,
            estimated_surplus=best_overlap,
            preferred_direction=preferred_direction,
            confidence=confidence
        )
```

### Step 3: Implement CompensatingBlockDiscoverer

**Location**: `src/vmt_engine/game_theory/bargaining/discovery.py` (new file)

```python
"""
Trade Discovery Algorithms

Implements various algorithms for discovering mutually beneficial trades.
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
    
    This is refactored from find_compensating_block_generic() in matching.py
    (lines 516-615).
    """
    
    def discover_trade(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        params: dict[str, any] | None = None,
        epsilon: float = 1e-9
    ) -> TradeTuple | None:
        """
        Discover first feasible trade using compensating block algorithm.
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

Version: 2025.11.03 (Restructured)
"""

from typing import Optional
from ...protocols.registry import register_protocol
from .base import BargainingProtocol
from .discovery import CompensatingBlockDiscoverer
from ...systems.trade_evaluation import TradeDiscoverer, TradeTuple
from ...protocols.base import Effect, Trade, Unpair
from ...protocols.context import WorldView


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
    
    def negotiate(self, pair: tuple[int, int], world: WorldView) -> list[Effect]:
        """
        Negotiate trade between paired agents.
        
        Args:
            pair: (agent_a_id, agent_b_id) tuple
            world: Context with both agents' states
        
        Returns:
            [Trade(...)] if successful
            [Unpair(...)] if no mutually beneficial trade found
        """
        agent_a_id, agent_b_id = pair
        epsilon = world.params.get("epsilon", 1e-9)
        
        # Build agent objects from WorldView
        agent_i = self._build_agent_from_world(world, agent_a_id)
        agent_j = self._build_agent_from_world(world, agent_b_id)
        
        # Discover trade using injected discovery algorithm
        trade_tuple = self.discoverer.discover_trade(agent_i, agent_j, world.params, epsilon)
        
        if trade_tuple is None:
            # No mutually beneficial trade - unpair
            return [Unpair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=agent_a_id,
                agent_b=agent_b_id,
                reason="trade_failed"
            )]
        
        # Convert TradeTuple to Trade effect
        return [self._create_trade_effect(agent_a_id, agent_b_id, trade_tuple, world)]
    
    def _build_agent_from_world(self, world: WorldView, agent_id: int):
        """
        Build a pseudo-Agent object from WorldView for discovery algorithms.
        
        This is a temporary adapter. Future refactoring may pass protocol
        contexts directly to discovery algorithms.
        """
        from ...core.agent import Agent
        from ...core.state import Inventory
        
        if agent_id == world.agent_id:
            inventory = Inventory(
                A=world.inventory.get("A", 0),
                B=world.inventory.get("B", 0),
            )
            quotes = world.quotes
            utility = world.utility
        else:
            # Find partner in visible agents
            partner_view = None
            for neighbor in world.visible_agents:
                if neighbor.agent_id == agent_id:
                    partner_view = neighbor
                    break
            
            if partner_view is None:
                # Partner not visible - create minimal agent defensively
                inventory = Inventory(A=0, B=0)
                quotes = {}
                utility = None
            else:
                # Extract from AgentView
                inventory = Inventory(
                    A=world.params.get(f"partner_{agent_id}_inv_A", 0),
                    B=world.params.get(f"partner_{agent_id}_inv_B", 0)
                )
                quotes = partner_view.quotes
                utility = world.params.get(f"partner_{agent_id}_utility", None)
        
        # Create minimal agent
        agent = Agent(
            id=agent_id,
            pos=(0, 0),  # Not used in discovery
            inventory=inventory,
            utility=utility,
            quotes=quotes,
        )
        
        return agent
    
    def _create_trade_effect(
        self,
        agent_a_id: int,
        agent_b_id: int,
        trade_tuple: TradeTuple,
        world: WorldView
    ) -> Trade:
        """
        Convert TradeTuple to Trade effect.
        """
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

### Step 5: Update Matching Protocols

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
    
    def _calculate_pair_surplus(...):
        # Use lightweight evaluation instead of full trade discovery
        potential = self.evaluator.evaluate_pair_potential(agent_a, agent_b, {})
        
        if not potential.is_feasible:
            return (0.0, 0.0, distance)
        
        # Use estimated surplus for pairing decision
        estimated_surplus = potential.estimated_surplus
        discounted_surplus = estimated_surplus * (beta ** distance)
        
        return (estimated_surplus, discounted_surplus, distance)
```

### Step 6: Update Other Bargaining Protocols

**Update**: `src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py`

```python
# OLD:
from ...systems.matching import find_all_feasible_trades

def negotiate(...):
    feasible_trades = find_all_feasible_trades(agent_i_obj, agent_j_obj, {}, epsilon)
    # ...

# NEW:
from .discovery import CompensatingBlockDiscoverer
from ...systems.trade_evaluation import TradeDiscoverer, TradeTuple

class TakeItOrLeaveIt(BargainingProtocol):
    def __init__(
        self,
        discoverer: TradeDiscoverer | None = None,
        proposer_power: float = 0.5,
        proposer_selection: str = "random"
    ):
        """
        Initialize take-it-or-leave-it bargaining.
        
        Args:
            discoverer: Trade discovery algorithm (default: CompensatingBlockDiscoverer)
            proposer_power: Allocation of surplus to proposer (0.0 to 1.0)
            proposer_selection: How to select proposer ("random", "buyer", "seller")
        """
        self.discoverer = discoverer or CompensatingBlockDiscoverer()
        self.proposer_power = proposer_power
        self.proposer_selection = proposer_selection
    
    def negotiate(...):
        # Use protocol-specific trade discovery
        trade_tuple = self.discoverer.discover_trade(agent_i_obj, agent_j_obj, {}, epsilon)
        
        if trade_tuple is None:
            return [Unpair(...)]
        
        # Apply take-it-or-leave-it surplus allocation
        # ... (rest of protocol logic)
```

**Update**: `src/vmt_engine/game_theory/bargaining/split_difference.py`

```python
# Similar changes as take_it_or_leave_it.py
from .discovery import CompensatingBlockDiscoverer
from ...systems.trade_evaluation import TradeDiscoverer

class SplitDifference(BargainingProtocol):
    def __init__(self, discoverer: TradeDiscoverer | None = None):
        self.discoverer = discoverer or CompensatingBlockDiscoverer()
    # ...
```

### Step 7: Update Protocol Registry and Factory

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

Version: Post-Decoupling (v2)
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

### Step 8: Clean Up Legacy Code

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
# - execute_trade() [trade execution - may need refactor later]
# - execute_trade_generic() [trade execution]

# ADD DEPRECATION NOTICES (temporary):
def find_all_feasible_trades(*args, **kwargs):
    """
    DEPRECATED: Use TradeDiscoverer interface instead.
    This function will be removed in a future version.
    """
    import warnings
    warnings.warn(
        "find_all_feasible_trades() is deprecated. "
        "Use TradeDiscoverer interface instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Temporary adapter for any remaining callers
    from ..game_theory.bargaining.discovery import CompensatingBlockDiscoverer
    discoverer = CompensatingBlockDiscoverer()
    # ... conversion logic ...
```

### Step 9: Migrate All Scenarios

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

**Automated Migration Script** (optional):
```bash
# Find and replace in all YAML files
find scenarios/ -name "*.yaml" -type f -exec sed -i 's/legacy_compensating_block/compensating_block/g' {} +
find tests/ -name "*.py" -type f -exec sed -i 's/legacy_compensating_block/compensating_block/g' {} +
find docs/ -name "*.yaml" -type f -exec sed -i 's/legacy_compensating_block/compensating_block/g' {} +
```

---

## 5. Migration Strategy

### Phase 1: Add New Abstractions (Non-Breaking)

**Goal**: Introduce new code without breaking existing functionality

1. Create `src/vmt_engine/systems/trade_evaluation.py`
   - Define `TradePotential`, `TradePotentialEvaluator`
   - Define `TradeTuple`, `TradeDiscoverer`
   - Implement `QuoteBasedTradeEvaluator`

2. Create `src/vmt_engine/game_theory/bargaining/discovery.py`
   - Implement `CompensatingBlockDiscoverer`
   - Copy logic from `find_compensating_block_generic()` (lines 516-615)
   - Adapt to return `TradeTuple`

3. **Do not modify or remove existing code yet**

**Validation**: All existing tests pass, new abstractions are tested in isolation

### Phase 2: Update Protocols (Coexistence)

**Goal**: Refactor protocols to use new abstractions while old code still exists

1. Rename `legacy.py` → `compensating_block.py`
   - Update class name: `LegacyBargainingProtocol` → `CompensatingBlockBargaining`
   - Update to use `CompensatingBlockDiscoverer`
   - Keep registry name as `"compensating_block"`

2. Update matching protocols:
   - `GreedySurplusMatching` uses `TradePotentialEvaluator`
   - Other matching protocols as needed

3. Update other bargaining protocols:
   - `TakeItOrLeaveIt` uses `TradeDiscoverer`
   - `SplitDifference` uses `TradeDiscoverer`

4. Update factory defaults to use `"compensating_block"`

**Validation**: All tests pass with new protocols, old functions still present but unused

### Phase 3: Migrate Scenarios and Tests

**Goal**: Update all configuration files to use new protocol names

1. Update all YAML scenario files
2. Update test files
3. Update documentation
4. Update comprehensive template

**Validation**: All scenarios load and run correctly with new names

### Phase 4: Remove Legacy Code and Cleanup

**Goal**: Remove deprecated functions, clean up codebase

1. Remove from `src/vmt_engine/systems/matching.py`:
   - `find_all_feasible_trades()`
   - `find_best_trade()`
   - `find_compensating_block_generic()`

2. Remove deprecated functions from `matching.py`:
   - `trade_pair()` and `find_compensating_block()` (if truly unused)

3. Remove deprecation warnings

4. Final code review and cleanup

**Validation**: All tests pass, no references to removed functions

### Phase 5: Documentation and Communication

**Goal**: Document the changes for users and developers

1. Update protocol documentation
2. Update architecture documentation
3. Add migration guide for custom protocol developers
4. Update CHANGELOG.md
5. Consider blog post or announcement

---

## 6. Testing Strategy

### 6.1 Unit Tests

**New Components**:
- Test `TradePotentialEvaluator` interface and `QuoteBasedTradeEvaluator`
- Test `TradeDiscoverer` interface and `CompensatingBlockDiscoverer`
- Verify `CompensatingBlockDiscoverer` produces identical results to old `find_compensating_block_generic()`

**Test File**: `tests/test_trade_evaluation.py`

```python
def test_compensating_block_discoverer_matches_legacy():
    """Verify new discoverer produces identical trades to old function."""
    # Set up two agents with known inventories and utilities
    # Call old find_compensating_block_generic()
    # Call new CompensatingBlockDiscoverer.discover_trade()
    # Assert trades are identical
```

### 6.2 Integration Tests

**Refactored Components**:
- All matching protocols still produce same pairings
- All bargaining protocols still produce same trades
- End-to-end: matching + bargaining produces same outcomes

**Test File**: `tests/test_protocol_refactor_regression.py`

```python
def test_greedy_matching_unchanged():
    """Verify GreedySurplusMatching pairs same agents after refactor."""
    # Run with old code (via git stash or snapshot)
    # Run with new code
    # Compare pairings at each tick

def test_compensating_block_bargaining_unchanged():
    """Verify CompensatingBlockBargaining produces same trades."""
    # Compare trade outcomes before/after refactor
```

### 6.3 Behavioral Equivalence Tests

**Critical Validation**: Ensure refactoring doesn't change simulation outcomes

```python
def test_baseline_scenarios_unchanged():
    """Run all baseline scenarios and verify identical outcomes."""
    # For each scenario in scenarios/baseline/:
    #   - Load scenario
    #   - Run with compensating_block protocol
    #   - Compare final states, trades, utilities
    #   - Assert bit-for-bit identical to pre-refactor runs
```

### 6.4 Performance Tests

- Verify matching phase is faster with `QuoteBasedTradeEvaluator` (no full utility calc)
- Verify bargaining phase performance unchanged
- No regression in overall simulation speed

**Test File**: `tests/test_refactor_performance.py`

---

## 7. Backward Compatibility

### 7.1 Protocol Name Migration

**Strategy**: Direct migration to new name

- Old name: `"legacy_compensating_block"`
- New name: `"compensating_block"`
- All scenarios and tests updated in Phase 3

**No backward compatibility adapter** - clean break with clear migration

**Rationale**: This is a pre-1.0 project, breaking changes are acceptable if documented

### 7.2 Function Deprecation

**Temporary adapters in Phase 2** (removed in Phase 4):

```python
# src/vmt_engine/systems/matching.py

def find_all_feasible_trades(*args, **kwargs):
    """DEPRECATED: Use TradeDiscoverer instead."""
    warnings.warn("find_all_feasible_trades() is deprecated", DeprecationWarning)
    # Minimal adapter if needed for external code
```

### 7.3 API Stability

**Breaking Changes**:
- Protocol registry name change: `"legacy_compensating_block"` → `"compensating_block"`
- Removal of utility functions: `find_all_feasible_trades()`, `find_best_trade()`
- File rename: `legacy.py` → `compensating_block.py`

**Stable APIs**:
- Protocol base classes unchanged
- Effect system unchanged
- Simulation phase structure unchanged
- WorldView and ProtocolContext unchanged

---

## 8. Implementation Checklist

### Phase 1: New Abstractions ✓

- [ ] Create `src/vmt_engine/systems/trade_evaluation.py`
- [ ] Define `TradePotential` dataclass
- [ ] Define `TradePotentialEvaluator` ABC
- [ ] Implement `QuoteBasedTradeEvaluator`
- [ ] Define `TradeTuple` dataclass
- [ ] Define `TradeDiscoverer` ABC
- [ ] Create `src/vmt_engine/game_theory/bargaining/discovery.py`
- [ ] Implement `CompensatingBlockDiscoverer`
  - [ ] Copy logic from `find_compensating_block_generic()` (matching.py:516-615)
  - [ ] Adapt to return `TradeTuple | None`
  - [ ] Test equivalence to old implementation
- [ ] Write unit tests for new components
- [ ] Verify all existing tests still pass

### Phase 2: Refactor Protocols ✓

- [ ] Rename `src/vmt_engine/game_theory/bargaining/legacy.py` → `compensating_block.py`
- [ ] Refactor `CompensatingBlockBargaining`:
  - [ ] Update registry name to `"compensating_block"`
  - [ ] Add discoverer injection
  - [ ] Update to use `TradeDiscoverer`
  - [ ] Update `_create_trade_effect()` to accept `TradeTuple`
- [ ] Update `GreedySurplusMatching`:
  - [ ] Add evaluator injection
  - [ ] Replace `find_all_feasible_trades()` with `TradePotentialEvaluator`
  - [ ] Verify pairings unchanged
- [ ] Update `TakeItOrLeaveIt`:
  - [ ] Add discoverer injection
  - [ ] Replace `find_all_feasible_trades()` with `TradeDiscoverer`
  - [ ] Verify trades unchanged
- [ ] Update `SplitDifference`:
  - [ ] Add discoverer injection
  - [ ] Replace `find_all_feasible_trades()` with `TradeDiscoverer`
  - [ ] Verify trades unchanged
- [ ] Update `src/vmt_engine/game_theory/bargaining/__init__.py`
- [ ] Update `src/scenarios/protocol_factory.py` default to `"compensating_block"`
- [ ] Run full test suite - all tests should pass

### Phase 3: Migrate Scenarios ✓

- [ ] Update all YAML files in `scenarios/baseline/`
- [ ] Update all YAML files in `scenarios/demos/`
- [ ] Update all YAML files in `scenarios/curated/`
- [ ] Update all YAML files in `scenarios/test/`
- [ ] Update `docs/structures/comprehensive_scenario_template.yaml`
- [ ] Update test files in `tests/`:
  - [ ] `tests/helpers/builders.py`
  - [ ] `tests/test_protocol_yaml_config.py`
  - [ ] `tests/test_split_difference.py`
  - [ ] `tests/test_mode_integration.py`
  - [ ] `tests/test_performance.py`
  - [ ] `tests/test_resource_claiming.py`
  - [ ] Any other files referencing `"legacy_compensating_block"`
- [ ] Update `README.md`
- [ ] Update other documentation files
- [ ] Run full test suite - all tests should pass

### Phase 4: Remove Legacy Code ✓

- [ ] Remove from `src/vmt_engine/systems/matching.py`:
  - [ ] `find_all_feasible_trades()` (lines 619-662)
  - [ ] `find_best_trade()` (lines 665-710)
  - [ ] `find_compensating_block_generic()` (lines 516-615)
  - [ ] `trade_pair()` (if unused)
  - [ ] `find_compensating_block()` (if unused)
- [ ] Remove deprecation warnings
- [ ] Run full test suite - all tests should pass
- [ ] Code review and cleanup

### Phase 5: Documentation ✓

- [ ] Update `docs/2_technical_manual.md`
- [ ] Update architecture documentation
- [ ] Create protocol developer guide showing injection patterns
- [ ] Add examples for implementing custom `TradeDiscoverer`
- [ ] Update CHANGELOG.md with breaking changes
- [ ] Consider migration guide document

---

## 9. File Inventory

### New Files Created

1. `src/vmt_engine/systems/trade_evaluation.py` (~200 lines)
   - Abstractions for trade evaluation and discovery
   
2. `src/vmt_engine/game_theory/bargaining/discovery.py` (~150 lines)
   - `CompensatingBlockDiscoverer` implementation

### Files Renamed

1. `src/vmt_engine/game_theory/bargaining/legacy.py` → `compensating_block.py`

### Files Modified

1. `src/vmt_engine/game_theory/bargaining/__init__.py` (imports)
2. `src/vmt_engine/game_theory/bargaining/compensating_block.py` (refactored)
3. `src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py` (use discoverer)
4. `src/vmt_engine/game_theory/bargaining/split_difference.py` (use discoverer)
5. `src/vmt_engine/game_theory/matching/greedy.py` (use evaluator)
6. `src/vmt_engine/systems/matching.py` (remove deprecated functions)
7. `src/scenarios/protocol_factory.py` (update default name)
8. All scenario YAML files in `scenarios/` (~15 files)
9. Test files using old protocol name (~10 files)
10. Documentation files

### Lines of Code Impact

- **Added**: ~350 lines (new abstractions and implementations)
- **Removed**: ~400 lines (deprecated functions from matching.py)
- **Modified**: ~200 lines (protocol refactoring)
- **Net change**: ~+150 lines (abstractions add some overhead)

---

## 10. Future Enhancements

### 10.1 Alternative Discovery Algorithms

Once the abstraction is in place, new bargaining protocols can use different discovery:

```python
class NashBargainingDiscoverer(TradeDiscoverer):
    """Find trade that maximizes Nash product."""
    def discover_trade(...):
        # Optimization-based search for Nash solution
        pass

class KalaiSmorodinskyDiscoverer(TradeDiscoverer):
    """Kalai-Smorodinsky bargaining solution."""
    pass

class ExhaustiveSearchDiscoverer(TradeDiscoverer):
    """Search all possible trades, return Pareto-optimal set."""
    def discover_all_trades(...) -> list[TradeTuple]:
        # Return multiple trades for ranking
        pass
```

### 10.2 Enhanced Trade Potential Evaluation

Matching protocols could use more sophisticated evaluation:

```python
class UtilityBasedTradeEvaluator(TradePotentialEvaluator):
    """Uses full utility calculations but caches results."""
    def __init__(self, cache_size: int = 1000):
        self.cache = LRUCache(cache_size)

class MachineLearningEvaluator(TradePotentialEvaluator):
    """ML model predicts trade potential from features."""
    pass
```

### 10.3 Caching and Performance

```python
class CachedDiscoverer(TradeDiscoverer):
    """Wraps another discoverer with caching."""
    def __init__(self, inner: TradeDiscoverer, cache_size: int = 1000):
        self.inner = inner
        self.cache = LRUCache(cache_size)
    
    def discover_trade(...):
        key = (agent_i.id, agent_j.id, hash(inventories), hash(quotes))
        if key in self.cache:
            return self.cache[key]
        result = self.inner.discover_trade(...)
        self.cache[key] = result
        return result
```

### 10.4 Protocol Composition

```python
class FallbackDiscoverer(TradeDiscoverer):
    """Try primary discoverer, fall back to secondary if no trade found."""
    def __init__(self, primary: TradeDiscoverer, fallback: TradeDiscoverer):
        self.primary = primary
        self.fallback = fallback
    
    def discover_trade(...):
        result = self.primary.discover_trade(...)
        if result is None:
            result = self.fallback.discover_trade(...)
        return result
```

---

## 11. Risks & Mitigations

### Risk 1: Breaking Existing Scenarios

**Likelihood**: Medium  
**Impact**: High  
**Mitigation**: 
- Comprehensive test suite with behavioral equivalence tests
- Automated find/replace for protocol name migration
- Phase 3 dedicated to scenario migration
- Validation that all scenarios load and run

### Risk 2: Performance Regression

**Likelihood**: Low  
**Impact**: Medium  
**Mitigation**:
- Benchmark before/after refactor
- Performance tests in CI
- `QuoteBasedTradeEvaluator` should be faster (no full utility calc)
- `CompensatingBlockDiscoverer` identical to old implementation

### Risk 3: Subtle Behavioral Changes

**Likelihood**: Medium  
**Impact**: High  
**Mitigation**:
- Detailed unit tests verifying equivalence
- Baseline scenario regression tests
- Manual review of key scenarios
- Git history preserves old implementation for comparison

### Risk 4: Incomplete Migration

**Likelihood**: Low  
**Impact**: Medium  
**Mitigation**:
- Comprehensive file inventory (Section 9)
- Automated search for old protocol name references
- Code review checklist
- grep for `legacy_compensating_block`, `find_all_feasible_trades`, `find_best_trade`

### Risk 5: Documentation Drift

**Likelihood**: Medium  
**Impact**: Low  
**Mitigation**:
- Phase 5 dedicated to documentation
- Checklist for all docs to update
- Protocol developer guide with examples

---

## 12. Success Criteria

✅ **Decoupling Achieved**: Matching protocols work without bargaining protocol knowledge  
✅ **Protocol Independence**: Bargaining protocols can use different discovery algorithms  
✅ **Backward Compatibility**: All existing scenarios work with new protocol names  
✅ **Performance Maintained**: No significant slowdown (actually faster matching)  
✅ **Code Quality**: Clear separation of concerns, no circular dependencies  
✅ **Documentation**: Architecture clearly documented for future protocol developers  
✅ **Accurate Naming**: "Legacy" terminology replaced with descriptive names  
✅ **Core Algorithm Preserved**: Compensating block algorithm maintains same behavior  

---

## 13. Open Questions (RESOLVED)

### ✅ Q1: Should `TradeDiscoverer` be injectable into bargaining protocols?
**Decision**: Yes, via constructor injection with sensible default

### ✅ Q2: Should matching protocols be able to choose their evaluator?
**Decision**: Yes, via constructor injection with sensible default

### ✅ Q3: What about `find_best_trade()`?
**Decision**: Remove it - it's only used by legacy.py which is being refactored

### ✅ Q4: Protocol name for refactored implementation?
**Decision**: `"compensating_block"` - descriptive of algorithm

### ✅ Q5: Backward compatibility strategy?
**Decision**: Option B - migrate all scenarios to new name (clean break)

### ✅ Q6: Keep as default protocol?
**Decision**: Yes, it's the foundational VMT algorithm

### ✅ Q7: Return single trade or list of trades?
**Decision**: Single trade (`TradeTuple | None`) - matches current behavior

---

## 14. Next Steps

1. ✅ **Review this plan** - Address any remaining concerns
2. **Begin Phase 1**: Create new abstractions (non-breaking)
   - Implement `trade_evaluation.py`
   - Implement `CompensatingBlockDiscoverer`
   - Test in isolation
3. **Phase 2**: Refactor protocols to use new abstractions
4. **Phase 3**: Migrate all scenarios
5. **Phase 4**: Remove legacy code
6. **Phase 5**: Update documentation

**Estimated Effort**: 
- Phase 1: 4-6 hours (new code + tests)
- Phase 2: 6-8 hours (refactoring + validation)
- Phase 3: 2-3 hours (find/replace + testing)
- Phase 4: 1-2 hours (cleanup)
- Phase 5: 2-3 hours (documentation)
- **Total**: ~15-22 hours

---

**Author**: AI Assistant  
**Reviewers**: [To be filled]  
**Last Updated**: 2025-11-03  
**Version**: 2.0 (Revised)

