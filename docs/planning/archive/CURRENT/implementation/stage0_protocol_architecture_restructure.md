# Part 0: Protocol Architecture Restructure
## Detailed Step-by-Step Implementation Plan

**Document Purpose**: Surgical implementation guide for restructuring protocol ownership  
**Created**: November 2, 2025  
**Status**: Implementation-Ready Blueprint  
**Estimated Duration**: 4-6 hours (single session recommended)

---

## Table of Contents
1. [Overview](#overview)
2. [Rationale](#rationale)
3. [Pre-Implementation Checklist](#pre-implementation-checklist)
4. [Implementation Steps](#implementation-steps)
5. [Testing Strategy](#testing-strategy)
6. [Rollback Plan](#rollback-plan)
7. [Success Criteria](#success-criteria)
8. [Post-Implementation Verification](#post-implementation-verification)

---

## Overview

### Current Structure
```
src/vmt_engine/
├── protocols/
│   ├── base.py              # All protocol ABCs and Effect types
│   ├── registry.py          # Central registry
│   ├── context.py           # WorldView, ProtocolContext
│   ├── context_builders.py  # Helper functions
│   ├── search/              # Search implementations
│   ├── matching/            # Matching implementations
│   └── bargaining/          # Bargaining implementations
```

### Target Structure
```
src/vmt_engine/
├── protocols/
│   ├── base.py              # Effect types only (Trade, Move, Pair, etc.)
│   ├── registry.py          # Central registry (unchanged)
│   ├── context.py           # WorldView, ProtocolContext (unchanged)
│   └── context_builders.py  # Helper functions (unchanged)
├── game_theory/
│   ├── __init__.py
│   ├── bargaining/
│   │   ├── __init__.py
│   │   ├── base.py          # BargainingProtocol ABC
│   │   ├── legacy.py        # Moved from protocols/bargaining/
│   │   ├── split_difference.py
│   │   └── take_it_or_leave_it.py
│   └── matching/
│       ├── __init__.py
│       ├── base.py          # MatchingProtocol ABC
│       ├── legacy.py        # Moved from protocols/matching/
│       ├── random.py
│       └── greedy.py
└── agent_based/
    ├── __init__.py
    └── search/
        ├── __init__.py
        ├── base.py          # SearchProtocol ABC
        ├── legacy.py        # Moved from protocols/search/
        ├── random_walk.py
        └── myopic.py
```

---

## Rationale

### Why This Restructure?
1. **Domain Clarity**: Protocols belong to their theoretical domains
   - Game Theory owns strategic interaction mechanisms (bargaining, matching)
   - Agent-Based owns emergent behavior mechanisms (search)
   
2. **Future Extensibility**: Enables clean addition of:
   - `game_theory/mechanisms/` (e.g., auctions, voting)
   - `agent_based/learning/` (e.g., Q-learning, gradient descent)
   - `neoclassical/` module (separate from protocols entirely)

3. **Import Clarity**: Makes theoretical foundation explicit
   ```python
   # Clear domain ownership
   from vmt_engine.game_theory.bargaining import SplitDifference
   from vmt_engine.agent_based.search import RandomWalkSearch
   ```

4. **Backward Compatibility**: Registry system ensures YAML configs don't break
   - Protocol registration remains unchanged
   - Factory functions work identically
   - No scenario file modifications needed

---

## Pre-Implementation Checklist

### 1. Version Control Safety
- [ ] Create new branch: `git checkout -b protocol-restructure`
- [ ] Ensure working directory is clean: `git status`
- [ ] Commit any uncommitted changes
- [ ] Tag current state: `git tag pre-protocol-restructure`

### 2. Test Suite Baseline
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Record baseline results (all tests should pass)
- [ ] Verify no linter errors: `ruff check src/`
- [ ] Document any pre-existing failures

### 3. Backup Critical Files
```bash
# Create backup directory
mkdir -p .protocol-restructure-backup

# Backup entire protocols directory
cp -r src/vmt_engine/protocols/ .protocol-restructure-backup/

# Backup systems that import protocols
cp src/vmt_engine/systems/decision.py .protocol-restructure-backup/
cp src/vmt_engine/systems/trading.py .protocol-restructure-backup/

# Backup scenario loader
cp src/scenarios/protocol_factory.py .protocol-restructure-backup/
```

### 4. Identify All Import Sites
Run these searches to catalog what needs updating:
```bash
# Find all imports from protocols
grep -r "from vmt_engine.protocols" src/ tests/ > .protocol-restructure-backup/import_audit.txt
grep -r "from ..protocols" src/ >> .protocol-restructure-backup/import_audit.txt
grep -r "from .protocols" src/ >> .protocol-restructure-backup/import_audit.txt
```

Expected files needing import updates:
- `src/vmt_engine/systems/decision.py`
- `src/vmt_engine/systems/trading.py`
- `src/scenarios/protocol_factory.py`
- `tests/test_protocol_registry.py`
- `tests/test_protocol_yaml_config.py`
- `tests/test_*_search.py` (3 files)
- `tests/test_*_matching.py` (2 files)
- `tests/test_*_bargaining.py` (2 files)

---

## Implementation Steps

### Phase 1: Create Directory Structure (5 minutes)

#### Step 1.1: Create Module Directories
```bash
cd /home/cmf/Work/vmt-dev

# Create game_theory module
mkdir -p src/vmt_engine/game_theory/bargaining
mkdir -p src/vmt_engine/game_theory/matching

# Create agent_based module
mkdir -p src/vmt_engine/agent_based/search
```

#### Step 1.2: Create `__init__.py` Placeholder Files
```bash
# Top-level module inits (empty for now)
touch src/vmt_engine/game_theory/__init__.py
touch src/vmt_engine/agent_based/__init__.py

# Protocol category inits (will populate later)
touch src/vmt_engine/game_theory/bargaining/__init__.py
touch src/vmt_engine/game_theory/matching/__init__.py
touch src/vmt_engine/agent_based/search/__init__.py
```

---

### Phase 2: Extract Protocol ABCs (15 minutes)

#### Step 2.1: Create `agent_based/search/base.py`

**Action**: Extract `SearchProtocol` ABC from `protocols/base.py`

**New File**: `src/vmt_engine/agent_based/search/base.py`
```python
"""
Search Protocol Base Class

Search protocols determine how agents select targets for interaction in spatial environments.
Part of the Agent-Based modeling paradigm - emergent behavior from decentralized decisions.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...protocols.context import WorldView

from ...protocols.base import Effect, SetTarget, ProtocolBase


class SearchProtocol(ProtocolBase):
    """
    Base class for search protocols.
    
    Search protocols implement target selection strategies in spatial environments.
    They answer: "Given what I can see, who should I approach?"
    
    Theoretical Context:
    - Agent-Based Modeling paradigm
    - Bounded rationality and local information
    - Emergent patterns from decentralized search
    
    Returns:
        List of SetTarget effects
    """
    
    @abstractmethod
    def decide_targets(self, world: WorldView) -> list[Effect]:
        """
        Decide which agents should be targeted by which other agents.
        
        Args:
            world: Immutable world view with agent positions, inventories, utilities
        
        Returns:
            List of SetTarget effects specifying who targets whom
        """
        pass
```

#### Step 2.2: Create `game_theory/matching/base.py`

**New File**: `src/vmt_engine/game_theory/matching/base.py`
```python
"""
Matching Protocol Base Class

Matching protocols determine how agents form bilateral pairs for negotiation.
Part of the Game Theory paradigm - strategic pairing mechanisms.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...protocols.context import WorldView

from ...protocols.base import Effect, Pair, Unpair, ProtocolBase


class MatchingProtocol(ProtocolBase):
    """
    Base class for matching protocols.
    
    Matching protocols implement pairing mechanisms that determine which agents
    negotiate together. They answer: "Who negotiates with whom?"
    
    Theoretical Context:
    - Game Theory paradigm (matching theory, mechanism design)
    - Two-sided matching with preferences
    - Strategic considerations in pairing
    
    Returns:
        List of Pair/Unpair effects
    """
    
    @abstractmethod
    def form_pairs(self, world: WorldView) -> list[Effect]:
        """
        Form bilateral pairs from agent preferences.
        
        Args:
            world: Immutable world view with agent targets and preferences
        
        Returns:
            List of Pair effects specifying which agents negotiate together
        """
        pass
    
    def timeout_stale_pairs(self, world: WorldView) -> list[Effect]:
        """
        Unpair agents stuck in negotiation for too long.
        
        Default implementation: unpair after 5 ticks.
        Override for custom timeout logic.
        """
        effects = []
        for pair in world.pairs:
            if world.tick - pair.tick >= 5:
                effects.append(Unpair(*pair.ids, reason="timeout", 
                                    protocol_name=self.name, tick=world.tick))
        return effects
```

#### Step 2.3: Create `game_theory/bargaining/base.py`

**New File**: `src/vmt_engine/game_theory/bargaining/base.py`
```python
"""
Bargaining Protocol Base Class

Bargaining protocols determine how paired agents negotiate trade terms.
Part of the Game Theory paradigm - strategic negotiation mechanisms.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...protocols.context import ProtocolContext

from ...protocols.base import Effect, Trade, Unpair, ProtocolBase


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
    
    @abstractmethod
    def negotiate_trades(self, context: ProtocolContext) -> list[Effect]:
        """
        Negotiate trade terms between paired agents.
        
        Args:
            context: Protocol context with pair info, agent views, and utilities
        
        Returns:
            List of Trade effects (if agreement) or Unpair effects (if no deal)
        """
        pass
    
    def timeout_stale_pairs(self, world) -> list[Effect]:
        """
        Unpair agents stuck in negotiation for too long.
        
        Default implementation: unpair after 5 ticks.
        Override for custom timeout logic.
        """
        return [Unpair(*pair, reason="timeout", protocol_name=self.name, tick=world.tick)
                for pair in world.pairs if world.tick - pair.tick >= 5]
```

#### Step 2.4: Update `protocols/base.py`

**Action**: Remove protocol ABCs, keep only Effect types and `ProtocolBase`

**Edit**: `src/vmt_engine/protocols/base.py`

1. Remove the following class definitions (lines ~289-445):
   - `SearchProtocol`
   - `MatchingProtocol`
   - `BargainingProtocol`

2. Keep all Effect classes:
   - `Effect` (base)
   - `SetTarget`, `ClaimResource`, `ReleaseClaim`
   - `Pair`, `Unpair`
   - `Move`
   - `Trade`
   - `Harvest`
   - `RefreshQuotes`, `SetCooldown`
   - `InternalStateUpdate`

3. Keep `ProtocolBase` abstract class

**Result**: `protocols/base.py` should be ~260 lines (down from ~445)

---

### Phase 3: Move Protocol Implementations (20 minutes)

#### Step 3.1: Move Search Protocols

```bash
# Move implementation files
mv src/vmt_engine/protocols/search/legacy.py src/vmt_engine/agent_based/search/
mv src/vmt_engine/protocols/search/random_walk.py src/vmt_engine/agent_based/search/
mv src/vmt_engine/protocols/search/myopic.py src/vmt_engine/agent_based/search/
```

**Update imports in moved files:**

For each file (`legacy.py`, `random_walk.py`, `myopic.py`):
- Change: `from ..base import SearchProtocol, Effect, SetTarget`
- To: `from .base import SearchProtocol`
- To: `from ...protocols.base import Effect, SetTarget`

#### Step 3.2: Move Matching Protocols

```bash
# Move implementation files
mv src/vmt_engine/protocols/matching/legacy.py src/vmt_engine/game_theory/matching/
mv src/vmt_engine/protocols/matching/random.py src/vmt_engine/game_theory/matching/
mv src/vmt_engine/protocols/matching/greedy.py src/vmt_engine/game_theory/matching/
```

**Update imports in moved files:**

For each file (`legacy.py`, `random.py`, `greedy.py`):
- Change: `from ..base import MatchingProtocol, Effect, Pair`
- To: `from .base import MatchingProtocol`
- To: `from ...protocols.base import Effect, Pair`

#### Step 3.3: Move Bargaining Protocols

```bash
# Move implementation files
mv src/vmt_engine/protocols/bargaining/legacy.py src/vmt_engine/game_theory/bargaining/
mv src/vmt_engine/protocols/bargaining/split_difference.py src/vmt_engine/game_theory/bargaining/
mv src/vmt_engine/protocols/bargaining/take_it_or_leave_it.py src/vmt_engine/game_theory/bargaining/
```

**Update imports in moved files:**

For each file (`legacy.py`, `split_difference.py`, `take_it_or_leave_it.py`):
- Change: `from ..base import BargainingProtocol, Effect, Trade, Unpair`
- To: `from .base import BargainingProtocol`
- To: `from ...protocols.base import Effect, Trade, Unpair`
- Change: `from ..context import ProtocolContext`
- To: `from ...protocols.context import ProtocolContext`

---

### Phase 4: Create Module `__init__.py` Files (15 minutes)

#### Step 4.1: `agent_based/search/__init__.py`

**File**: `src/vmt_engine/agent_based/search/__init__.py`
```python
"""
Search Protocols - Agent-Based Modeling Paradigm

Search protocols determine how agents select targets for interaction in spatial
environments. These protocols implement bounded rationality and local information
processing, leading to emergent market patterns.

Available Protocols:
- legacy_distance_discounted: Original VMT distance-weighted search
- random_walk: Stochastic exploration (pedagogical baseline)
- myopic: Limited-vision search (radius=1, pedagogical)

Theoretical Context:
- Decentralized decision making
- Spatial search with friction
- Bounded rationality

Version: Post-Restructure (Part 0)
"""

from .base import SearchProtocol
from .legacy import LegacySearchProtocol
from .random_walk import RandomWalkSearch
from .myopic import MyopicSearch

# Registry assertion (crash-fast validation)
from ...protocols.registry import ProtocolRegistry
_reg = ProtocolRegistry.list_protocols()
assert "legacy_distance_discounted" in _reg.get("search", []), \
    "Search registry missing 'legacy_distance_discounted'"
assert "random_walk" in _reg.get("search", []), \
    "Search registry missing 'random_walk'"
assert "myopic" in _reg.get("search", []), \
    "Search registry missing 'myopic'"

__all__ = [
    "SearchProtocol",
    "LegacySearchProtocol",
    "RandomWalkSearch",
    "MyopicSearch",
]
```

#### Step 4.2: `game_theory/matching/__init__.py`

**File**: `src/vmt_engine/game_theory/matching/__init__.py`
```python
"""
Matching Protocols - Game Theory Paradigm

Matching protocols determine how agents form bilateral pairs for negotiation.
These protocols implement strategic pairing mechanisms from matching theory.

Available Protocols:
- legacy_three_pass: Original VMT three-pass matching
- random_matching: Random bilateral pairing (baseline)
- greedy_surplus: Greedy matching by expected surplus

Theoretical Context:
- Two-sided matching markets
- Stable matchings
- Mechanism design

Version: Post-Restructure (Part 0)
"""

from .base import MatchingProtocol
from .legacy import LegacyMatchingProtocol
from .random import RandomMatching
from .greedy import GreedySurplusMatching

# Registry assertion (crash-fast validation)
from ...protocols.registry import ProtocolRegistry
_reg = ProtocolRegistry.list_protocols()
assert "legacy_three_pass" in _reg.get("matching", []), \
    "Matching registry missing 'legacy_three_pass'"
assert "random_matching" in _reg.get("matching", []), \
    "Matching registry missing 'random_matching'"
assert "greedy_surplus" in _reg.get("matching", []), \
    "Matching registry missing 'greedy_surplus'"

__all__ = [
    "MatchingProtocol",
    "LegacyMatchingProtocol",
    "RandomMatching",
    "GreedySurplusMatching",
]
```

#### Step 4.3: `game_theory/bargaining/__init__.py`

**File**: `src/vmt_engine/game_theory/bargaining/__init__.py`
```python
"""
Bargaining Protocols - Game Theory Paradigm

Bargaining protocols determine how paired agents negotiate trade terms.
These protocols implement strategic negotiation mechanisms from bargaining theory.

Available Protocols:
- legacy_compensating_block: Original VMT compensating block algorithm
- split_difference: Equal surplus division (Nash bargaining)
- take_it_or_leave_it: Asymmetric bargaining power (ultimatum game)

Theoretical Context:
- Axiomatic bargaining solutions
- Strategic bargaining games
- Nash program

Version: Post-Restructure (Part 0)
"""

from .base import BargainingProtocol
from .legacy import LegacyBargainingProtocol
from .split_difference import SplitDifference
from .take_it_or_leave_it import TakeItOrLeaveIt

# Registry assertion (crash-fast validation)
from ...protocols.registry import ProtocolRegistry
_reg = ProtocolRegistry.list_protocols()
assert "legacy_compensating_block" in _reg.get("bargaining", []), \
    "Bargaining registry missing 'legacy_compensating_block'"
assert "split_difference" in _reg.get("bargaining", []), \
    "Bargaining registry missing 'split_difference'"
assert "take_it_or_leave_it" in _reg.get("bargaining", []), \
    "Bargaining registry missing 'take_it_or_leave_it'"

__all__ = [
    "BargainingProtocol",
    "LegacyBargainingProtocol",
    "SplitDifference",
    "TakeItOrLeaveIt",
]
```

#### Step 4.4: Top-Level Module Inits

**File**: `src/vmt_engine/game_theory/__init__.py`
```python
"""
Game Theory Module

Implements strategic interaction mechanisms: bargaining, matching, and future
game-theoretic protocols (auctions, voting, etc.).

Sub-modules:
- bargaining: Trade negotiation protocols
- matching: Bilateral pairing protocols
"""

from . import bargaining
from . import matching

__all__ = ["bargaining", "matching"]
```

**File**: `src/vmt_engine/agent_based/__init__.py`
```python
"""
Agent-Based Module

Implements emergent behavior mechanisms: search, learning, and future
agent-based protocols.

Sub-modules:
- search: Target selection protocols
"""

from . import search

__all__ = ["search"]
```

---

### Phase 5: Update Protocol Registry Imports (10 minutes)

The protocol registry uses decorators, so implementations auto-register on import.
We need to ensure the registry can still find and load protocols.

#### Step 5.1: Update `protocols/__init__.py`

**Edit**: `src/vmt_engine/protocols/__init__.py`

**Old import section (lines 113-119):**
```python
# -----------------------------------------------------------------------------
# Force protocol module imports to trigger decorator registration
# -----------------------------------------------------------------------------

from . import search as _protocols_search  # noqa: F401
from . import matching as _protocols_matching  # noqa: F401
from . import bargaining as _protocols_bargaining  # noqa: F401
```

**New import section:**
```python
# -----------------------------------------------------------------------------
# Force protocol module imports to trigger decorator registration
# -----------------------------------------------------------------------------
# Protocols are now domain-organized under game_theory/ and agent_based/

from ..game_theory import bargaining as _game_theory_bargaining  # noqa: F401
from ..game_theory import matching as _game_theory_matching  # noqa: F401
from ..agent_based import search as _agent_based_search  # noqa: F401
```

**Update crash-fast assertions (lines 121-128):**

Keep assertions unchanged - they validate registry state, not import paths.

---

### Phase 6: Update System Imports (15 minutes)

#### Step 6.1: Update `systems/decision.py`

**File**: `src/vmt_engine/systems/decision.py`

**Old imports (lines 17-27):**
```python
from ..protocols import (
    SearchProtocol,
    MatchingProtocol,
    SetTarget,
    ClaimResource,
    ReleaseClaim,
    Pair,
    Unpair,
    build_world_view_for_agent,
    build_protocol_context,
)
```

**New imports:**
```python
from ..agent_based.search import SearchProtocol
from ..game_theory.matching import MatchingProtocol
from ..protocols import (
    SetTarget,
    ClaimResource,
    ReleaseClaim,
    Pair,
    Unpair,
    build_world_view_for_agent,
    build_protocol_context,
)
```

#### Step 6.2: Update `systems/trading.py`

**File**: `src/vmt_engine/systems/trading.py`

Find the import section and update:
- Change: `from ..protocols import BargainingProtocol`
- To: `from ..game_theory.bargaining import BargainingProtocol`

Keep other imports from `..protocols` (Effect types, context builders).

---

### Phase 7: Update Scenario Loader (5 minutes)

#### Step 7.1: Update `scenarios/protocol_factory.py`

**File**: `src/scenarios/protocol_factory.py`

**No changes needed!** 

The factory uses `ProtocolRegistry.get_protocol_class()` which looks up by name,
not by import path. Since protocol classes still register themselves with the
same names, the registry system ensures backward compatibility.

**Verify**: Check that imports in each factory function use the registry:
- `from vmt_engine.protocols.registry import ProtocolRegistry` ✓

---

### Phase 8: Update Test Imports (20 minutes)

#### Step 8.1: Protocol-Specific Tests

Update imports in these test files:

**Files needing updates:**
1. `tests/test_random_walk_search.py`
2. `tests/test_myopic_search.py`
3. `tests/test_random_matching.py`
4. `tests/test_greedy_surplus_matching.py`
5. `tests/test_split_difference.py`
6. `tests/test_take_it_or_leave_it_bargaining.py`

**Pattern for each file:**

Old:
```python
from vmt_engine.protocols.search import RandomWalkSearch
```

New (search protocols):
```python
from vmt_engine.agent_based.search import RandomWalkSearch
```

New (matching protocols):
```python
from vmt_engine.game_theory.matching import RandomMatching
```

New (bargaining protocols):
```python
from vmt_engine.game_theory.bargaining import SplitDifference
```

#### Step 8.2: Registry Tests

**File**: `tests/test_protocol_registry.py`

Update any direct imports of protocol classes. If the test uses the registry
for lookup (recommended), no changes needed.

#### Step 8.3: YAML Config Tests

**File**: `tests/test_protocol_yaml_config.py`

Should require no changes - uses protocol factory which uses registry.

---

### Phase 9: Clean Up Old Protocol Directories (5 minutes)

#### Step 9.1: Verify All Files Moved

```bash
# Check that old directories are empty (except __init__.py)
ls -la src/vmt_engine/protocols/search/
ls -la src/vmt_engine/protocols/matching/
ls -la src/vmt_engine/protocols/bargaining/
```

Expected: Only `__init__.py` should remain in each directory.

#### Step 9.2: Remove Old Directories

```bash
# Remove old protocol subdirectories
rm -rf src/vmt_engine/protocols/search/
rm -rf src/vmt_engine/protocols/matching/
rm -rf src/vmt_engine/protocols/bargaining/
```

#### Step 9.3: Update `protocols/__init__.py` Exports

**Edit**: `src/vmt_engine/protocols/__init__.py`

Remove these from `__all__` list:
- `"SearchProtocol"`
- `"MatchingProtocol"`
- `"BargainingProtocol"`

These should now be imported directly from domain modules:
```python
from vmt_engine.agent_based.search import SearchProtocol
from vmt_engine.game_theory.matching import MatchingProtocol
from vmt_engine.game_theory.bargaining import BargainingProtocol
```

---

## Testing Strategy

### Incremental Testing (After Each Phase)

**After Phase 1-2** (Directory Creation + ABC Extraction):
```bash
# Verify new base classes are valid Python
python -c "from vmt_engine.agent_based.search.base import SearchProtocol"
python -c "from vmt_engine.game_theory.matching.base import MatchingProtocol"
python -c "from vmt_engine.game_theory.bargaining.base import BargainingProtocol"
```

**After Phase 3** (Move Implementations):
```bash
# Verify moved files can import their base classes
python -c "from vmt_engine.agent_based.search.legacy import LegacySearchProtocol"
python -c "from vmt_engine.game_theory.matching.random import RandomMatching"
python -c "from vmt_engine.game_theory.bargaining.split_difference import SplitDifference"
```

**After Phase 4** (Module Inits):
```bash
# Verify module-level imports work
python -c "from vmt_engine.agent_based import search"
python -c "from vmt_engine.game_theory import matching, bargaining"
```

**After Phase 5-6** (Registry + Systems):
```bash
# Verify registry can find protocols
python -c "from vmt_engine.protocols.registry import ProtocolRegistry; print(ProtocolRegistry.list_protocols())"

# Expected output: {'search': [...], 'matching': [...], 'bargaining': [...]}
```

**After Phase 7-8** (Scenarios + Tests):
```bash
# Run protocol-specific tests
pytest tests/test_random_walk_search.py -v
pytest tests/test_split_difference.py -v
pytest tests/test_random_matching.py -v
```

### Comprehensive Test Suite

**After Phase 9** (Complete Restructure):
```bash
# Full test suite
pytest tests/ -v

# Specific protocol tests
pytest tests/ -k "protocol" -v

# Integration tests
pytest tests/test_m1_integration.py -v
pytest tests/test_mode_integration.py -v

# Scenario loading tests
pytest tests/test_scenario_loader.py -v
pytest tests/test_protocol_yaml_config.py -v
```

### Verification Checklist

- [ ] All tests pass (same as baseline)
- [ ] No import errors in any module
- [ ] Protocol registry contains all expected protocols
- [ ] YAML scenario files load without errors
- [ ] Example simulation runs successfully

---

## Rollback Plan

### If Tests Fail Mid-Implementation

**Option 1: Rollback to Tagged State**
```bash
# Nuclear option - restore pre-restructure state
git reset --hard pre-protocol-restructure
git clean -fd
```

**Option 2: Restore from Backup**
```bash
# Selective restoration
cp -r .protocol-restructure-backup/protocols/ src/vmt_engine/
cp .protocol-restructure-backup/decision.py src/vmt_engine/systems/
cp .protocol-restructure-backup/trading.py src/vmt_engine/systems/
cp .protocol-restructure-backup/protocol_factory.py src/scenarios/

# Remove partial new modules
rm -rf src/vmt_engine/game_theory/
rm -rf src/vmt_engine/agent_based/
```

**Option 3: Fix Forward**

If only a few tests fail:
1. Check error messages for import issues
2. Verify `__init__.py` files are complete
3. Check relative imports in moved files
4. Verify registry still finds all protocols

---

## Success Criteria

### Functional Requirements
- [ ] All existing tests pass
- [ ] No new linter errors
- [ ] All protocol implementations register correctly
- [ ] YAML scenario loading works identically
- [ ] Simulation runs produce same results as pre-restructure

### Structural Requirements
- [ ] Protocol ABCs moved to domain modules
- [ ] Implementations moved to domain modules
- [ ] Old `protocols/search/`, `protocols/matching/`, `protocols/bargaining/` removed
- [ ] New modules: `game_theory/`, `agent_based/` exist
- [ ] Module `__init__.py` files export correct symbols

### Import Requirements
- [ ] `from vmt_engine.agent_based.search import SearchProtocol` works
- [ ] `from vmt_engine.game_theory.matching import MatchingProtocol` works
- [ ] `from vmt_engine.game_theory.bargaining import BargainingProtocol` works
- [ ] Effect types still importable from `protocols.base`
- [ ] Registry still importable from `protocols.registry`

### Documentation Requirements
- [ ] Module docstrings explain theoretical context
- [ ] README updated to reflect new structure (if exists)
- [ ] This implementation plan marked as completed

---

## Post-Implementation Verification

### Smoke Tests

**Test 1: Simple Simulation**
```bash
# Run minimal 2-agent scenario
python main.py scenarios/demos/minimal_2agent.yaml --seed 42
```

**Test 2: Protocol Swapping**
```bash
# Verify CLI protocol overrides work
python main.py scenarios/demos/minimal_2agent.yaml \
    --search random_walk \
    --matching random_matching \
    --bargaining split_difference \
    --seed 42
```

**Test 3: Registry Introspection**
```python
from vmt_engine.protocols.registry import ProtocolRegistry

# List all registered protocols
protocols = ProtocolRegistry.list_protocols()
print(protocols)

# Expected output:
# {
#   'search': ['legacy_distance_discounted', 'myopic', 'random_walk'],
#   'matching': ['greedy_surplus', 'legacy_three_pass', 'random_matching'],
#   'bargaining': ['legacy_compensating_block', 'split_difference', 'take_it_or_leave_it']
# }

# Get metadata for a protocol
meta = ProtocolRegistry.get_metadata('split_difference', 'bargaining')
print(f"{meta.name}: {meta.description}")
```

### Performance Verification

Run benchmark to ensure no performance regression:
```bash
# Run performance test suite
pytest tests/test_performance.py -v

# Run benchmark script (if exists)
python scripts/benchmark_performance.py
```

### Documentation Updates

After successful restructure:
1. Update `src/vmt_engine/README.md` (if exists) with new structure
2. Update `docs/2_technical_manual.md` with new import paths
3. Add note to `CHANGELOG.md`:
   ```markdown
   ## [Unreleased] - 2025-11-02
   ### Changed
   - **BREAKING**: Restructured protocol architecture
     - Search protocols moved to `vmt_engine.agent_based.search`
     - Matching protocols moved to `vmt_engine.game_theory.matching`
     - Bargaining protocols moved to `vmt_engine.game_theory.bargaining`
     - Effect types remain in `vmt_engine.protocols.base`
     - Registry remains in `vmt_engine.protocols.registry`
     - YAML scenario files unchanged (backward compatible via registry)
   ```

---

## Expected Outcome

After completing this restructure:

1. **Clearer Architecture**: Domain ownership is explicit
   - Game Theory owns strategic mechanisms
   - Agent-Based owns emergent mechanisms
   
2. **Better Extensibility**: Future additions have clear homes
   - `game_theory/mechanisms/` for auctions, voting, etc.
   - `agent_based/learning/` for adaptive agents
   - `neoclassical/` for equilibrium solvers (separate module)

3. **Maintained Compatibility**: No breaking changes for users
   - YAML files work identically
   - Protocol factory unchanged
   - Registry system ensures backward compatibility

4. **Improved Discoverability**: Import paths reflect theory
   ```python
   from vmt_engine.game_theory.bargaining import SplitDifference  # Nash solution
   from vmt_engine.agent_based.search import RandomWalkSearch    # Emergent behavior
   ```

---

## Troubleshooting Guide

### Common Issues

**Issue 1: Import Error - "No module named 'vmt_engine.game_theory'"**
- **Cause**: Missing `__init__.py` files
- **Fix**: Verify all `__init__.py` files created in Phase 1

**Issue 2: Protocol Not Found in Registry**
- **Cause**: Protocol class not imported during registry initialization
- **Fix**: Check `protocols/__init__.py` imports new module locations (Phase 5)

**Issue 3: Circular Import Error**
- **Cause**: Base classes importing from implementations
- **Fix**: Use `TYPE_CHECKING` and forward references in base classes

**Issue 4: Test Failures - "Cannot import SearchProtocol from protocols"**
- **Cause**: Test files using old import paths
- **Fix**: Update test imports per Phase 8

**Issue 5: Relative Import Errors in Moved Files**
- **Cause**: Forgot to update imports in moved protocol files
- **Fix**: Verify Phase 3 import updates for all moved files

---

## Time Estimates

| Phase | Task | Estimated Time |
|-------|------|---------------|
| 0 | Pre-implementation checklist | 10 min |
| 1 | Create directory structure | 5 min |
| 2 | Extract protocol ABCs | 15 min |
| 3 | Move implementations | 20 min |
| 4 | Create module inits | 15 min |
| 5 | Update registry imports | 10 min |
| 6 | Update system imports | 15 min |
| 7 | Update scenario loader | 5 min |
| 8 | Update test imports | 20 min |
| 9 | Clean up old directories | 5 min |
| | **Total Implementation** | **2 hours** |
| | Testing & verification | 1-2 hours |
| | Documentation updates | 30 min |
| | **Total with buffer** | **4-6 hours** |

---

## Next Steps After Completion

Once Part 0 is complete and verified:

1. **Merge to main branch**
   ```bash
   git add .
   git commit -m "Restructure protocol architecture (Part 0)"
   git checkout main
   git merge protocol-restructure
   ```

2. **Tag the restructure**
   ```bash
   git tag post-protocol-restructure
   git push --tags
   ```

3. **Proceed to Stage 1**: "Understand What You Have"
   - Behavioral mapping of current system
   - Baseline metrics collection
   - Comprehensive documentation

---

**Implementation Status**: Ready for execution  
**Prerequisites**: None (this IS the prerequisite)  
**Risk Level**: Medium (many file moves, but systematic approach)  
**Reversibility**: High (version control + backups)

