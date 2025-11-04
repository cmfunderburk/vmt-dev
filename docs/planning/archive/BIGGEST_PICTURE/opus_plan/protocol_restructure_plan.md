# VMT Protocol Architecture Restructure Plan

**Purpose**: Define concrete restructuring of protocols to reflect their true domain ownership  
**Status**: Planning - NO IMPLEMENTATION until approved  
**Critical**: Following @04_planning_only_mode - design only

---

## The Clarification You Just Made

**Your Core Insight**: 
> "Bargaining and Matching Protocols should be *primarily* housed in the game theory module. The Agent Based Module should call those base functions at the relevant point in its 7-phase system."

This is a **paradigm shift** from current architecture where protocols live in `src/vmt_engine/protocols/` as generic "economic mechanisms."

---

## Current Architecture (What Exists Now)

```
src/vmt_engine/
├── protocols/
│   ├── base.py                   # Effect types, ProtocolBase ABC
│   ├── context.py                # WorldView, ProtocolContext
│   ├── registry.py               # ProtocolRegistry
│   ├── context_builders.py       # WorldView factory functions
│   ├── bargaining/
│   │   ├── __init__.py
│   │   ├── legacy.py             # LegacyBargainingProtocol
│   │   ├── split_difference.py   # SplitDifference
│   │   └── take_it_or_leave_it.py
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── legacy.py             # LegacyMatchingProtocol
│   │   ├── random.py             # RandomMatching
│   │   └── greedy.py             # GreedySurplusMatching
│   └── search/
│       ├── __init__.py
│       ├── legacy.py             # LegacySearchProtocol
│       ├── random_walk.py
│       └── myopic.py

src/vmt_engine/systems/
├── decision.py                   # Calls SearchProtocol + MatchingProtocol
├── trading.py                    # Calls BargainingProtocol
```

**Current Flow**:
1. Simulation loads protocols from `protocols/` module
2. `DecisionSystem.execute()` calls `search_protocol.select_target()` and `matching_protocol.find_matches()`
3. `TradeSystem.execute()` calls `bargaining_protocol.negotiate()`

---

## Proposed Architecture (After Restructure)

```
src/vmt_engine/
├── protocols/                    # SHARED INFRASTRUCTURE ONLY
│   ├── base.py                   # Effect types, ProtocolBase ABC, Effect validation
│   ├── context.py                # WorldView, ProtocolContext (shared interface)
│   ├── registry.py               # ProtocolRegistry
│   └── context_builders.py       # WorldView factory functions
│
├── game_theory/                  # NEW MODULE - Canonical home for strategic protocols
│   ├── __init__.py
│   ├── bargaining/
│   │   ├── __init__.py
│   │   ├── base.py               # BargainingProtocol ABC (moved from protocols.base)
│   │   ├── legacy.py
│   │   ├── split_difference.py
│   │   ├── take_it_or_leave_it.py
│   │   ├── nash.py               # FUTURE: Nash bargaining solution
│   │   ├── kalai_smorodinsky.py  # FUTURE
│   │   └── rubinstein.py         # FUTURE: Alternating offers
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── base.py               # MatchingProtocol ABC (moved from protocols.base)
│   │   ├── legacy.py
│   │   ├── random.py
│   │   ├── greedy.py
│   │   └── gale_shapley.py       # FUTURE: Stable matching
│   ├── exchange_engine.py        # Two-agent exchange (Edgeworth Box)
│   ├── solutions.py              # Nash, KS, contract curve computation
│   └── visualization.py          # Edgeworth Box matplotlib widgets
│
├── agent_based/                  # NEW MODULE - Spatial simulation protocols
│   ├── __init__.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── base.py               # SearchProtocol ABC (ABM-specific)
│   │   ├── legacy.py
│   │   ├── random_walk.py
│   │   ├── myopic.py
│   │   └── memory_based.py       # FUTURE: Learning search
│   └── protocols_adapter.py      # Wraps GT protocols for ABM context
│
src/vmt_engine/systems/
├── decision.py                   # Calls ABM search + GT matching
├── trading.py                    # Calls GT bargaining
```

**Restructured Flow**:
1. Simulation imports `BargainingProtocol` and `MatchingProtocol` from `game_theory/`
2. Simulation imports `SearchProtocol` from `agent_based/search/`
3. `DecisionSystem.execute()` calls:
   - `agent_based.search_protocol.select_target()` (spatial context)
   - `game_theory.matching_protocol.find_matches()` (strategic context)
4. `TradeSystem.execute()` calls:
   - `game_theory.bargaining_protocol.negotiate()` (strategic context)

---

## Rationale: Why This Separation Makes Sense

### 1. Domain Ownership

**Game Theory Module Owns**:
- **Matching**: Who pairs with whom? (Gale-Shapley, stable matching, welfare maximization)
- **Bargaining**: How is surplus divided? (Nash, KS, Rubinstein, ultimatum)
- **Exchange Analysis**: Contract curve, competitive equilibrium, Pareto frontier

**Agent-Based Module Owns**:
- **Search**: How do agents navigate space to find opportunities?
- **Spatial Coordination**: Movement, foraging, resource claiming
- **Temporal Dynamics**: When do agents make decisions given spatial constraints?

### 2. Theoretical Foundation

Bargaining and matching theory originate from Game Theory (Nash, Rubinstein, Gale-Shapley). They apply to:
- 2-agent isolated exchange (Game Theory track)
- Multi-agent spatial contexts (Agent-Based track)

Search protocols are inherently spatial—they make no sense in 2-agent game theory.

### 3. Development Workflow

```
Phase 1: Develop in Game Theory Track
  → Implement Nash bargaining in game_theory/bargaining/nash.py
  → Test with 2 agents, visualize in Edgeworth Box
  → Verify against theoretical predictions

Phase 2: Use in Agent-Based Track
  → Import nash.py from game_theory
  → Call from TradeSystem.execute()
  → Observe emergence in spatial context
  → Compare with GT predictions
```

### 4. Pedagogical Clarity

Students see:
- Strategic protocols in pure theoretical context first
- Same protocols deployed in spatial context
- Clear separation: "This is the game theory part, this is the spatial part"

---

## Implementation Steps (When Approved)

### Step 1: Create New Module Structure

```bash
mkdir -p src/vmt_engine/game_theory/bargaining
mkdir -p src/vmt_engine/game_theory/matching
mkdir -p src/vmt_engine/agent_based/search
```

### Step 2: Move Protocol ABCs

**Move**: `SearchProtocol` class from `protocols/base.py` → `agent_based/search/base.py`
**Move**: `MatchingProtocol` class from `protocols/base.py` → `game_theory/matching/base.py`
**Move**: `BargainingProtocol` class from `protocols/base.py` → `game_theory/bargaining/base.py`

**Keep in `protocols/base.py`**: Effect types, `ProtocolBase` ABC, effect validation

### Step 3: Move Protocol Implementations

**Move**: `bargaining/*.py` → `game_theory/bargaining/*.py`
**Move**: `matching/*.py` → `game_theory/matching/*.py`
**Move**: `search/*.py` → `agent_based/search/*.py`

### Step 4: Update Imports

**In simulation.py**:
```python
from vmt_engine.game_theory.bargaining import BargainingProtocol
from vmt_engine.game_theory.matching import MatchingProtocol
from vmt_engine.agent_based.search import SearchProtocol
```

**In systems/decision.py**:
```python
from vmt_engine.game_theory.matching import MatchingProtocol
from vmt_engine.agent_based.search import SearchProtocol
```

**In systems/trading.py**:
```python
from vmt_engine.game_theory.bargaining import BargainingProtocol
```

### Step 5: Update Protocol Registry

Registry imports remain in `protocols/` but register from new locations:

```python
# game_theory/bargaining/__init__.py
from ..protocols.registry import register_protocol

# Still registers globally, just organized differently
```

### Step 6: Create Import Adapters

Backward compatibility layer if needed:

```python
# protocols/__init__.py (for backward compatibility)
from ..game_theory.bargaining import BargainingProtocol
from ..game_theory.matching import MatchingProtocol
from ..agent_based.search import SearchProtocol
```

---

## Open Questions

### Q1: Should Search Protocols Live in ABM or Stay Generic?

**Argument for ABM-only**: Search inherently requires spatial context (vision radius, grid, movement).

**Argument for staying generic**: Some search protocols might work in network contexts too?

**Recommendation**: Start ABM-only. Can refactor if network extension materializes.

### Q2: How Do We Handle Shared Dependencies?

**Context Builders**: Currently in `protocols/context_builders.py`. Should this move?

**Recommendation**: Keep `protocols/context_builders.py` as shared infrastructure. All modules import from it.

### Q3: What About Registry Location?

**Current**: Registry in `protocols/registry.py`

**Options**:
- A: Keep in `protocols/` (shared infrastructure)
- B: Move to `game_theory/` (since GT owns most protocols)
- C: Separate registries per domain

**Recommendation**: **Option A**. Registry is infrastructure, not domain logic.

### Q4: Effect Types - Where Do They Belong?

**Current**: All Effect types (`Trade`, `Pair`, `Unpair`, `Move`, etc.) in `protocols/base.py`

**Analysis**:
- `Trade`, `Pair`, `Unpair` → Used by Game Theory protocols
- `Move`, `SetTarget`, `Harvest` → Used by ABM search/foraging
- `ClaimResource`, `ReleaseClaim` → ABM-specific

**Options**:
- A: Keep all in `protocols/base.py` (shared infrastructure)
- B: Split by domain ownership

**Recommendation**: **Option A**. Effects are the communication language between protocols and systems. They're infrastructure, not domain logic.

---

## Migration Path

### Phase 1: Foundation (No Breaking Changes)

1. Create new directories
2. Copy (don't move yet) protocol files
3. Update imports to point to new locations
4. Run tests to ensure nothing breaks

### Phase 2: Consolidate

1. Remove old `protocols/bargaining/` directory
2. Remove old `protocols/matching/` directory  
3. Remove old `protocols/search/` directory
4. Remove old protocol ABCs from `protocols/base.py`

### Phase 3: Clean Up

1. Remove backward compatibility imports if added
2. Update all documentation
3. Update scenario configs if needed
4. Final test pass

---

## Risk Assessment

### High Risk
- **Import chains**: Many files import protocols. Need careful update order.
- **Registry registration**: Protocols register at import time. Order matters.
- **Test breakage**: Many tests import protocols directly.

### Medium Risk
- **Documentation**: Update READMEs, docstrings, planning docs
- **Scenario configs**: May reference protocol names via string

### Low Risk
- **Protocol interface**: No changes to actual protocol methods
- **Effect types**: Not moving anywhere
- **WorldView**: Not changing

---

## Success Criteria

### Immediate (After Restructure)
- ✅ All tests pass
- ✅ All scenarios run
- ✅ No import errors
- ✅ Protocol registry still works

### Short-term (After Game Theory Track Implements)
- ✅ New protocols (Nash, Gale-Shapley) live in `game_theory/`
- ✅ Edgeworth Box uses protocols from `game_theory/`
- ✅ ABM imports and uses same protocols

### Long-term (Proof of Concept)
- ✅ Clear separation of concerns visible in codebase
- ✅ Students can understand: "GT protocols are here, ABM protocols there"
- ✅ Future development naturally follows domain boundaries

---

## Next Steps

**Pending Approval**:
1. ✅ Get user confirmation this design matches their vision
2. ✅ Clarify any open questions above
3. ✅ Confirm no missed edge cases
4. ✅ Decide on migration timing

**Then Proceed**:
1. Create implementation TODO list
2. Execute Phase 1 (foundation)
3. Execute Phase 2 (consolidate)
4. Execute Phase 3 (clean up)

---

## References

- Current protocols: `src/vmt_engine/protocols/`
- Planning documents: `docs/planning_thinking_etc/BIGGEST_PICTURE/opus_plan/`
- User clarification: "Bargaining and Matching Protocols should be primarily housed in game theory module"
- Memory ID: 10554320 (no implementation until planning complete)

---

**Status**: Awaiting user review and approval

