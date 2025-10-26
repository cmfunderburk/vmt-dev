# Utility Modularization Plan

**Document Status:** Phase 1 Approved - Ready to Implement  
**Version:** 1.1  
**Created:** 2025-01-27  
**Updated:** 2025-10-26  
**Priority:** Low (Quality of Life)  
**Effort:** Phase 1: 2 hours | Full: 2 days

---

## DECISION SUMMARY ✅

**Phase 1 (Base Extraction):** ✅ APPROVED - Proceed immediately
**Phase 2 (Full Modularization):** Deferred for future work (can be assigned as onboarding exercise)  

---

## Executive Summary

The `src/vmt_engine/econ/utility.py` file has grown to ~744 lines containing mixed abstraction levels. This plan proposes a two-phase modularization:

1. **Phase 1 (Immediate):** Extract `Utility` ABC to `base.py` - 2 hours, zero risk
2. **Phase 2 (Optional):** Split utilities into separate modules - 2 days, low risk

---

## Current Problems

### File Statistics
- **Total Lines:** ~744
- **Components:**
  - Utility ABC: ~110 lines
  - UCES implementation: ~110 lines  
  - ULinear: ~45 lines
  - UQuadratic: ~90 lines
  - UTranslog: ~130 lines
  - UStoneGeary: ~110 lines
  - Factory & helpers: ~150 lines

### Issues
1. **Cognitive Load:** Too much in one file
2. **Mixed Abstractions:** Interface mixed with implementations
3. **Poor Discoverability:** Must scroll to find specific utility
4. **Limited Documentation Space:** Can't add extensive economic theory

---

## Phase 1: Base Extraction ✅ APPROVED (2 Hours)

**Status:** Approved - ready for immediate implementation

### What Changes

**Before:**
```
src/vmt_engine/econ/
└── utility.py (744 lines - everything)
```

**After:**
```
src/vmt_engine/econ/
├── base.py (110 lines - Utility ABC only)
└── utility.py (634 lines - implementations)
```

### Implementation Steps

1. **Create base.py** (30 min)
```python
"""Base interface for utility functions."""

from abc import ABC, abstractmethod

class Utility(ABC):
    """Base interface all utility functions must implement."""
    
    @abstractmethod
    def u_goods(self, A: int, B: int) -> float:
        """Compute utility from goods only."""
        pass
    
    @abstractmethod
    def mu_A(self, A: int, B: int) -> float:
        """Marginal utility of good A."""
        pass
    
    @abstractmethod
    def mu_B(self, A: int, B: int) -> float:
        """Marginal utility of good B."""
        pass
    
    # ... other abstract methods
```

2. **Update utility.py imports** (15 min)
```python
from .base import Utility  # Import ABC from base

class UCES(Utility):
    # ... implementation unchanged
```

3. **Update __init__.py** (15 min)
```python
# Re-export for backward compatibility
from .base import Utility
from .utility import UCES, ULinear, UQuadratic, UTranslog, UStoneGeary
```

4. **Test & Verify** (30 min)
```bash
pytest tests/test_utility_*.py  # Should all pass
mypy src/vmt_engine/econ/       # No new errors
```

### Benefits
- ✅ Clear separation of interface vs implementation
- ✅ Zero breaking changes
- ✅ Sets pattern for future modularization
- ✅ Can ship immediately

### Decision ✅
**Approved:** Proceed immediately. Low effort, high clarity value.

---

## Phase 2: Full Modularization (DEFERRED - 2 Days)

**Status:** Deferred - can be assigned as new developer onboarding exercise

### What Changes

**After Full Modularization:**
```
src/vmt_engine/econ/
├── __init__.py           # Backward compatible exports
├── utility.py            # Base + factory only (150 lines)
│   ├── Utility (from base.py)
│   ├── create_utility()
│   └── u_total()
└── utilities/
    ├── __init__.py       # Re-exports
    ├── ces.py           # UCES (120 lines)
    ├── linear.py        # ULinear (80 lines)
    ├── quadratic.py     # UQuadratic (120 lines)
    ├── translog.py      # UTranslog (150 lines)
    └── stone_geary.py   # UStoneGeary (130 lines)
```

### Implementation Steps

1. **Create utilities/ structure** (2-3 hours)
   - One file per utility class
   - Rich documentation per module
   - Consistent structure

2. **Update imports** (1-2 hours)
   - Preserve backward compatibility
   - Update factory function
   - Comprehensive __init__.py files

3. **Test thoroughly** (2-3 hours)
   - All existing tests pass
   - Determinism preserved
   - Import patterns work

4. **Documentation** (1-2 hours)
   - Update technical manual
   - Add "Creating New Utilities" guide

### Benefits
- ✅ Each utility in focused file
- ✅ Rich economic documentation possible
- ✅ Clear extension template
- ✅ Better test organization

### Trade-offs
- ⚠️ More files to navigate
- ⚠️ Potential import complexity
- ⚠️ 2 days of effort

### Decision
**Recommendation:** Defer until after protocol modularization. Can assign to new developer as onboarding exercise.

---

## Backward Compatibility

### Guaranteed Compatible Imports
All existing code continues to work unchanged:

```python
# All of these continue working:
from src.vmt_engine.econ.utility import UCES
from src.vmt_engine.econ import UCES
from src.vmt_engine.econ.utility import Utility
from src.vmt_engine.econ.utility import create_utility
```

### No Code Updates Needed
- ✅ Scenario loading (uses factory)
- ✅ All tests (imports unchanged)
- ✅ Simulation engine (uses protocol)
- ✅ Quotes system (duck-typed)

---

## Implementation Checklist

### Phase 1 Checklist (Do Now)
- [ ] No pending PRs on utility.py
- [ ] Create base.py with Utility ABC
- [ ] Update utility.py to import from base
- [ ] Update __init__.py with re-exports  
- [ ] Run full test suite
- [ ] Verify both import patterns work
- [ ] Run mypy and ruff
- [ ] Commit and ship

### Phase 2 Checklist (Future)
- [ ] Create utilities/ directory
- [ ] Split into individual modules
- [ ] Update all imports
- [ ] Full test suite passes
- [ ] Update documentation
- [ ] Performance verification

---

## Risks and Mitigations

### Phase 1 Risks
- **Risk:** Import issues
- **Mitigation:** Test both import patterns
- **Severity:** Very Low

### Phase 2 Risks  
- **Risk:** Circular imports
- **Mitigation:** Careful design, type: ignore if needed
- **Severity:** Low

- **Risk:** IDE confusion
- **Mitigation:** Explicit __all__ exports
- **Severity:** Low

---

## Alternative Approaches Considered

### Alternative 1: Do Nothing
- **Pros:** Zero effort
- **Cons:** File continues growing
- **Decision:** Rejected - proactive improvement worthwhile

### Alternative 2: Region Comments
```python
# region CES Utility
class UCES(Utility):
    ...
# endregion
```
- **Pros:** Minimal change
- **Cons:** Still monolithic
- **Decision:** Rejected - insufficient improvement

### Alternative 3: Separate Package
```
src/
├── vmt_engine/
└── vmt_utilities/  # Separate package
```
- **Pros:** Maximum separation
- **Cons:** Over-engineering
- **Decision:** Rejected - utilities are core, not plugins

---

## Relationship to Protocol Modularization

### Similarities
- Separation of interface from implementation
- Backward compatibility via re-exports
- Phased approach (adapters → refactor)

### Differences
- Utility modularization is simpler (no behavior changes)
- Lower priority (not blocking features)
- Can be done independently

### Timing
- Phase 1: Do immediately (before protocols)
- Phase 2: After protocol modularization complete

---

## Decisions Made ✅

### Question 1: Proceed with Phase 1? ✅ RESOLVED
**Decision:** Yes - approved for immediate implementation (2-hour task)

### Question 2: Schedule Phase 2? ✅ RESOLVED
**Decision:** Deferred - assign to new developer as onboarding exercise when available

**Rationale:** Phase 2 provides good learning opportunity without blocking critical work

---

## Summary

### Phase 1 (Base Extraction) ✅ APPROVED
- **Effort:** 2 hours
- **Risk:** Very Low  
- **Value:** High
- **Status:** Approved - ready to implement

### Phase 2 (Full Modularization) ⏸️ DEFERRED
- **Effort:** 2 days
- **Risk:** Low
- **Value:** Medium
- **Status:** Deferred - assign as onboarding exercise

**Next Action:** Implement Phase 1 base extraction immediately

---

**Document Status:** Phase 1 approved and ready for implementation  
**Owner:** Lead developer (Phase 1), New developer (Phase 2 - future)  
**Review:** Not required for Phase 1  
**Timeline:** Implement Phase 1 before protocol work begins
