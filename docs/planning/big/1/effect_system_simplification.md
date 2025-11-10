# Effect System Simplification Proposal

**Date:** 2025-11-10  
**Status:** Draft for Discussion  
**Context:** Current Effect/Command pattern is over-engineered for actual needs

---

## Executive Summary

The current architecture uses a Command pattern (Effects) that adds significant complexity without delivering its promised benefits. This document proposes removing the Effect abstraction layer and using direct protocol execution instead.

**Key Finding:** The "effects table" telemetry schema exists in code but is never instantiated, never populated, and provides zero actual value. Effects are immediately unpacked and discarded after protocol execution.

---

## Current Architecture Problems

### 1. Vapor Architecture

The system **claims** to provide:
```python
# From base.py docstring:
Protocol receives: WorldView (frozen, read-only)
Protocol returns: list[Effect] (declarative intents)
Core applies: validates, executes, logs effects
```

What **actually happens**:
```python
# 1. Protocol creates effect
effect = Trade(buyer_id=1, seller_id=2, dA=5, dB=10, price=2.0, ...)

# 2. TradeSystem unpacks it immediately
buyer = sim.agent_by_id[effect.buyer_id]
seller = sim.agent_by_id[effect.seller_id]

# 3. State is mutated IMMEDIATELY (no validation)
execute_trade_generic(buyer, seller, trade_tuple)  # MUTATES

# 4. AFTER mutation, assertions check constraints (crashes if violated)
assert agent_i.inventory.A >= 0  # Too late to rollback!

# 5. Effect is logged to OLD schema and discarded
sim.telemetry.log_trade(...)  # Uses legacy 'trades' table
```

**Verification:**
- `telemetry_schema.py` defines an `effects` table
- `database.py` never imports or creates this table
- No `log_effect()` method exists anywhere
- `grep "INSERT INTO effects"` returns zero results
- Effects are unpacked and thrown away

### 2. Data Structure Ping-Pong

```python
# Protocol computes trade
dA, dB, price, surplus = ...  # Meaningful calculation

# Pack into Trade effect
trade_effect = Trade(
    buyer_id=buyer.id,
    seller_id=seller.id,
    dA=dA, dB=dB, price=price,
    metadata={"surplus_buyer": surplus_buyer, "surplus_seller": surplus_seller}
)

# Unpack from Trade effect
buyer = sim.agent_by_id[effect.buyer_id]
seller = sim.agent_by_id[effect.seller_id]
dA = effect.dA
dB = effect.dB

# Repack into different format
if buyer.id < seller.id:
    dA_i, dB_i = effect.dA, -effect.dB
    dA_j, dB_j = -effect.dA, effect.dB
else:
    dA_i, dB_i = -effect.dA, effect.dB
    dA_j, dB_j = effect.dA, -effect.dB

surplus_buyer = effect.metadata.get("surplus_buyer", 0.0)
trade_tuple = (dA_i, dB_i, dA_j, dB_j, surplus_i, surplus_j)

# Finally execute
execute_trade_generic(agent_i, agent_j, trade_tuple)
```

**Why?** The effect dataclass adds zero value here.

### 3. False Promises

The pattern claims to provide:
- ❌ **Pre-execution validation**: Assertions run AFTER mutation (crash instead of rollback)
- ❌ **Transaction semantics**: No batching or rollback capability exists
- ❌ **Intent vs execution separation**: Effects logged to old schema, immediately discarded
- ❌ **Reproducibility**: Old telemetry schema already provides this
- ❌ **Protocol isolation**: Protocols receive Agent objects directly, can read state

What it **actually** provides:
- ✅ Type safety (but so do function signatures)
- ✅ Protocol swappability (but so does ABC with methods)

### 4. Developer Cognitive Load

To trace a trade through the system:

1. Read `CompensatingBlockBargaining.negotiate()` (230 lines)
2. Understand it returns `list[Effect]`
3. Find where effects are consumed (`TradeSystem._negotiate_trade()`)
4. Read `isinstance(effect, Trade)` dispatch logic
5. Trace into `_apply_trade_effect()`
6. See buyer/seller unpacking
7. See dA/dB coordinate transformation logic
8. See metadata extraction
9. See tuple reconstruction
10. Finally reach `execute_trade_generic()`

**With direct execution:**
1. Read `CompensatingBlockBargaining.negotiate()` 
2. See `sim.execute_trade()` call
3. Done

---

## Proposed Simplified Architecture

### Core Principle

**Protocols execute directly, not through intermediate data structures.**

### Simplified Base Classes

```python
# protocols/base.py (SIMPLIFIED)

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Agent, Simulation

class SearchProtocol(ABC):
    """Protocol for agent target selection."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass
    
    @abstractmethod
    def select_target(
        self,
        agent: "Agent",
        sim: "Simulation"
    ) -> None:
        """
        Select and set agent's target.
        
        Directly modifies:
        - agent.target_pos
        - agent.target_agent_id
        - agent.target_resource_type
        """
        pass


class MatchingProtocol(ABC):
    """Protocol for bilateral agent pairing."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass
    
    @abstractmethod
    def find_matches(
        self,
        preferences: dict[int, list[tuple[int, float]]],
        sim: "Simulation"
    ) -> None:
        """
        Create pairings between agents.
        
        Directly modifies:
        - agent.paired_with_id for paired agents
        
        Calls:
        - sim.telemetry.log_pairing_event() for each pair
        """
        pass


class BargainingProtocol(ABC):
    """Protocol for bilateral trade negotiation."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass
    
    @abstractmethod
    def negotiate(
        self,
        agent_a: "Agent",
        agent_b: "Agent", 
        sim: "Simulation"
    ) -> bool:
        """
        Attempt to negotiate a trade between two paired agents.
        
        Returns:
            True if trade succeeded, False if agents should unpair
        
        If successful, directly calls:
        - sim.execute_trade(agent_a, agent_b, dA, dB, price, metadata)
        
        If failed, directly calls:
        - sim.unpair(agent_a, agent_b, reason="no_feasible_trade")
        """
        pass
```

### Simplified Bargaining Protocol Example

```python
# game_theory/bargaining/compensating_block.py (SIMPLIFIED)

from typing import TYPE_CHECKING
from decimal import Decimal
from ..base import BargainingProtocol
from ...core.decimal_config import quantize_quantity
from ...systems.matching import generate_price_candidates

if TYPE_CHECKING:
    from ...core import Agent, Simulation


class CompensatingBlockBargaining(BargainingProtocol):
    """
    Compensating block bargaining - the foundational VMT algorithm.
    
    Searches over discrete quantities and price candidates to find
    the first mutually beneficial barter trade.
    """
    
    @property
    def name(self) -> str:
        return "compensating_block"
    
    @property
    def version(self) -> str:
        return "2025.11.10"
    
    def negotiate(
        self,
        agent_a: "Agent",
        agent_b: "Agent",
        sim: "Simulation"
    ) -> bool:
        """
        Negotiate trade between paired agents.
        
        Returns True if trade succeeded, False if unpaired.
        """
        epsilon = sim.params.get("epsilon", 1e-9)
        
        # Search for first feasible trade
        result = self._search_first_feasible(agent_a, agent_b, epsilon)
        
        if result is None:
            # No feasible trade - unpair agents
            sim.unpair(
                agent_a, agent_b,
                reason="no_feasible_trade",
                protocol_name=self.name
            )
            return False
        
        # Execute trade
        buyer, seller, dA, dB, price, surplus_buyer, surplus_seller = result
        sim.execute_trade(
            buyer=buyer,
            seller=seller,
            dA=dA,
            dB=dB,
            price=price,
            protocol_name=self.name,
            surplus_buyer=surplus_buyer,
            surplus_seller=surplus_seller
        )
        return True
    
    def _search_first_feasible(
        self,
        agent_i: "Agent",
        agent_j: "Agent",
        epsilon: float
    ) -> tuple | None:
        """
        Search for first mutually beneficial trade.
        
        Returns:
            (buyer, seller, dA, dB, price, surplus_buyer, surplus_seller)
            or None if no feasible trade exists
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
    ) -> tuple | None:
        """
        Search one direction for feasible trade.
        
        The giver sells good A, the receiver buys good A (pays with B).
        
        Returns:
            (buyer, seller, dA, dB, price, surplus_buyer, surplus_seller)
            or None if no feasible trade found
        """
        # Get quotes for this direction
        ask_giver = giver.quotes.get('ask_A_in_B', float('inf'))
        bid_receiver = receiver.quotes.get('bid_A_in_B', 0.0)
        
        # Check if there's quote overlap
        if ask_giver > bid_receiver:
            return None
        
        # Maximum quantity giver can sell
        max_dA = int(giver.inventory.A)
        if max_dA <= 0:
            return None
        
        # Discrete quantity search: 1, 2, 3, ... up to max_dA
        for dA_int in range(1, max_dA + 1):
            dA = quantize_quantity(Decimal(str(dA_int)))
            
            # Generate price candidates between ask and bid
            price_candidates = generate_price_candidates(ask_giver, bid_receiver, dA_int)
            
            for price in price_candidates:
                # Calculate dB = price * dA
                dB_raw = Decimal(str(price)) * dA
                dB = quantize_quantity(dB_raw)
                
                if dB <= 0:
                    continue
                
                # Check inventory constraints
                if giver.inventory.A < dA or receiver.inventory.B < dB:
                    continue
                
                # Calculate utilities with proposed trade
                if giver.id == agent_i.id:
                    u_i_new = agent_i.utility.u(agent_i.inventory.A - dA, agent_i.inventory.B + dB)
                    u_j_new = agent_j.utility.u(agent_j.inventory.A + dA, agent_j.inventory.B - dB)
                else:
                    u_i_new = agent_i.utility.u(agent_i.inventory.A + dA, agent_i.inventory.B - dB)
                    u_j_new = agent_j.utility.u(agent_j.inventory.A - dA, agent_j.inventory.B + dB)
                
                surplus_i = u_i_new - u_i_0
                surplus_j = u_j_new - u_j_0
                
                # Check mutual benefit
                if surplus_i > epsilon and surplus_j > epsilon:
                    # Found feasible trade - return details
                    buyer = receiver  # Receiver buys A
                    seller = giver    # Giver sells A
                    
                    if giver.id == agent_i.id:
                        surplus_buyer = surplus_j  # receiver = agent_j
                        surplus_seller = surplus_i  # giver = agent_i
                    else:
                        surplus_buyer = surplus_i  # receiver = agent_i
                        surplus_seller = surplus_j  # giver = agent_j
                    
                    return (buyer, seller, dA, dB, price, surplus_buyer, surplus_seller)
        
        return None
```

### Simplified Simulation Interface

```python
# core/simulation.py (NEW METHODS)

class Simulation:
    # ... existing code ...
    
    def execute_trade(
        self,
        buyer: Agent,
        seller: Agent,
        dA: Decimal,
        dB: Decimal,
        price: float,
        protocol_name: str,
        surplus_buyer: float = 0.0,
        surplus_seller: float = 0.0
    ) -> None:
        """
        Execute a bilateral barter trade.
        
        Validates:
        - Inventory feasibility (non-negative after trade)
        - Conservation laws (goods conserved)
        
        Updates:
        - Agent inventories
        - Inventory change flags
        - Reservation prices (quotes)
        
        Logs:
        - Trade to telemetry database
        """
        # Validate inventory constraints
        if seller.inventory.A < dA:
            raise ValueError(f"Seller {seller.id} has insufficient A: {seller.inventory.A} < {dA}")
        if buyer.inventory.B < dB:
            raise ValueError(f"Buyer {buyer.id} has insufficient B: {buyer.inventory.B} < {dB}")
        
        # Apply inventory changes
        seller.inventory.A -= dA
        seller.inventory.B += dB
        buyer.inventory.A += dA
        buyer.inventory.B -= dB
        
        # Verify non-negativity (should never fail after above checks)
        assert seller.inventory.A >= 0
        assert seller.inventory.B >= 0
        assert buyer.inventory.A >= 0
        assert buyer.inventory.B >= 0
        
        # Mark inventories as changed (triggers quote refresh)
        seller.inventory_changed = True
        buyer.inventory_changed = True
        
        # Log to telemetry
        self.telemetry.log_trade(
            tick=self.tick,
            x=buyer.pos[0],
            y=buyer.pos[1],
            buyer_id=buyer.id,
            seller_id=seller.id,
            dA=dA,
            dB=dB,
            price=price,
            direction="A_traded_for_B",
            exchange_pair_type="A<->B"
        )
        
        # Update trade counters (if tracking)
        if hasattr(self, "_trades_made"):
            self._trades_made[buyer.id] = self._trades_made.get(buyer.id, 0) + 1
            self._trades_made[seller.id] = self._trades_made.get(seller.id, 0) + 1
    
    def unpair(
        self,
        agent_a: Agent,
        agent_b: Agent,
        reason: str,
        protocol_name: str
    ) -> None:
        """
        Dissolve a pairing between two agents.
        
        Updates:
        - Agent pairing state
        - Trade cooldown timers
        
        Logs:
        - Unpair event to telemetry
        """
        # Dissolve pairing
        agent_a.paired_with_id = None
        agent_b.paired_with_id = None
        
        # Set trade cooldown
        cooldown_until = self.tick + self.params.get('trade_cooldown_ticks', 10)
        agent_a.trade_cooldowns[agent_b.id] = cooldown_until
        agent_b.trade_cooldowns[agent_a.id] = cooldown_until
        
        # Log unpair event
        self.telemetry.log_pairing_event(
            self.tick, agent_a.id, agent_b.id, "unpair", reason
        )
```

### Simplified System Code

```python
# systems/trading.py (SIMPLIFIED)

class TradeSystem:
    """
    Phase 4: Orchestrate protocol-based trade negotiation.
    """
    
    def __init__(self, bargaining_protocol: BargainingProtocol):
        self.bargaining_protocol = bargaining_protocol
    
    def run(self, sim: "Simulation") -> None:
        """Execute trade negotiations for all paired agents."""
        # Find all paired agents within interaction radius
        paired_agents = [
            (a, sim.agent_by_id[a.paired_with_id])
            for a in sim.agents
            if a.paired_with_id is not None
            and a.id < a.paired_with_id  # Process each pair once
            and self._within_interaction_radius(a, sim.agent_by_id[a.paired_with_id], sim)
        ]
        
        # Negotiate trade for each pair
        for agent_a, agent_b in paired_agents:
            self._negotiate_trade(agent_a, agent_b, sim)
    
    def _negotiate_trade(
        self,
        agent_a: "Agent",
        agent_b: "Agent",
        sim: "Simulation"
    ) -> None:
        """
        Negotiate trade between two paired agents.
        
        Protocol directly executes trade or unpairs agents.
        """
        # Call protocol (it handles execution and logging)
        trade_succeeded = self.bargaining_protocol.negotiate(agent_a, agent_b, sim)
        
        # That's it. Protocol handles everything.
    
    def _within_interaction_radius(
        self,
        agent_a: "Agent",
        agent_b: "Agent",
        sim: "Simulation"
    ) -> bool:
        """Check if agents are within interaction radius."""
        dx = agent_a.pos[0] - agent_b.pos[0]
        dy = agent_a.pos[1] - agent_b.pos[1]
        distance = (dx*dx + dy*dy) ** 0.5
        return distance <= sim.params.get('interaction_radius', 2.0)
```

---

## Comparison

### Lines of Code

**Current System:**
- `protocols/base.py`: 305 lines (12 Effect dataclasses + base classes)
- `systems/trading.py`: 236 lines (effect unpacking/repacking logic)
- `systems/matching.py`: `execute_trade_generic()` 40 lines
- `protocols/telemetry_schema.py`: 185 lines (unused)
- **Total: ~766 lines**

**Proposed System:**
- `protocols/base.py`: ~150 lines (3 ABC classes, clear contracts)
- `core/simulation.py`: ~80 lines (2 new methods)
- `systems/trading.py`: ~50 lines (minimal orchestration)
- **Total: ~280 lines**

**Reduction: 63% less code**

### Developer Workflow

**Current (to add a new bargaining protocol):**
1. Import 8 types: `Effect, Trade, Unpair, WorldView, BargainingProtocol, TradeTuple, trade_tuple_to_effect`
2. Implement `negotiate()` returning `list[Effect]`
3. Build `Trade` effect with 7 fields + metadata dict
4. Return wrapped effect
5. Hope TradeSystem unpacks correctly
6. Debug coordinate transformation issues
7. Wonder why effect isn't in telemetry

**Proposed (to add a new bargaining protocol):**
1. Import 2 types: `BargainingProtocol, Simulation`
2. Implement `negotiate()` returning `bool`
3. Call `sim.execute_trade(buyer, seller, dA, dB, price, protocol_name, ...)`
4. Done

### What We Lose

1. **Type safety of Effect objects**: Replaced by typed method signatures
2. **Potential for pre-execution validation**: Never implemented anyway
3. **Potential for transaction batching**: Never implemented anyway
4. **Abstraction purity**: Protocols already access Agent objects directly

### What We Gain

1. **Simplicity**: 63% less code, clearer execution path
2. **Transparency**: Direct calls visible in stack traces
3. **Maintainability**: No coordinate transformation logic to debug
4. **Honesty**: Architecture matches actual behavior
5. **Performance**: No object allocation/deallocation overhead
6. **Clarity**: Stack traces show actual execution path

---

## Migration Path

### Phase 1: Add Simulation Methods (Non-Breaking)

```python
# Add execute_trade() and unpair() to Simulation
# Old Effect-based code continues to work
```

### Phase 2: Update Bargaining Protocols

```python
# Change negotiate() signature one protocol at a time:
# - Old: def negotiate(...) -> list[Effect]
# - New: def negotiate(...) -> bool

# Update protocol implementations to call sim methods directly
```

### Phase 3: Update Matching Protocols

```python
# Change find_matches() signature:
# - Old: def find_matches(...) -> list[Effect]
# - New: def find_matches(...) -> None

# Update implementations to directly modify agent.paired_with_id
```

### Phase 4: Update Search Protocols

```python
# Change select_target() signature:
# - Old: def select_target(...) -> list[Effect]
# - New: def select_target(...) -> None

# Update implementations to directly modify agent.target_*
```

### Phase 5: Remove Effect System

```python
# Delete:
# - protocols/base.py effect classes (keep protocol ABCs)
# - protocols/telemetry_schema.py (unused)
# - systems/trading.py effect dispatch logic
# - systems/matching.py effect dispatch logic

# Update:
# - All system classes to use simplified protocols
```

### Phase 6: Update Tests

```python
# Change assertions from:
#   effects = protocol.negotiate(...)
#   assert isinstance(effects[0], Trade)

# To:
#   success = protocol.negotiate(agent_a, agent_b, sim)
#   assert success
#   # Check agent state directly
```

---

## Open Questions

### 1. Do we need protocol state management?

**Current:** `InternalStateUpdate` effect for multi-tick protocols (e.g., Rubinstein)

**Options:**
- A) Protocols maintain state in instance variables (simplest)
- B) Add `sim.set_protocol_state(protocol, agent_id, key, value)` method
- C) Protocols store state in `agent.protocol_state[protocol_name]` dict

**Recommendation:** Start with (A), add (B) only if needed for telemetry auditing

### 2. Do we need batch validation?

**Current:** Claims to support it, doesn't actually implement it

**Questions:**
- Should multiple effects be applied atomically?
- Should we rollback on partial failure?
- Do any protocols need this?

**Recommendation:** YAGNI - add only if concrete use case emerges

### 3. Should protocols see full Simulation or limited interface?

**Current:** Protocols receive WorldView (read-only snapshot)

**Proposed:** Protocols receive full Simulation reference

**Trade-offs:**
- Pro: Simpler, more direct
- Con: Protocols could access things they shouldn't
- Compromise: Create `ProtocolContext` with only allowed methods?

**Recommendation:** Start with full Simulation access, extract interface if protocols abuse it

---

## Recommendation

**Proceed with simplification.** The current Effect system:
- Adds significant complexity (766 lines)
- Delivers zero actual value (effects table never created/populated)
- Makes debugging harder (coordinate transformation bugs)
- Misrepresents system behavior (claims validation doesn't exist)

The proposed approach:
- Reduces code by 63%
- Makes execution path transparent
- Keeps all actual benefits (protocol swappability, telemetry, type safety)
- Removes false promises

**Risk:** Low. The Effect system doesn't provide anything we'd lose.

**Effort:** Medium. ~5 protocols to update, ~3 system classes to simplify, ~20 tests to adjust.

**Payoff:** High. Significantly clearer codebase for future development.

