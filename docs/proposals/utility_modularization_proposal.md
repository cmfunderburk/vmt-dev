# Utility Module Modularization Proposal

**Document Version:** 1.0  
**Created:** 2025-10-25  
**Status:** Draft Proposal  
**Priority:** Low (Quality-of-Life / Architectural Hygiene)  
**Estimated Effort:** 8-12 hours  
**Blockers:** None  

---

## Executive Summary

This proposal recommends refactoring the monolithic `src/vmt_engine/econ/utility.py` (~700 lines) into a modular package structure where each utility function type resides in its own module. This change improves maintainability, discoverability, and extensibility without altering any public APIs or simulation behavior.

**Key Benefits:**
1. **Separation of Concerns** - Base abstractions separated from concrete implementations
2. **Easier Navigation** - Developers can quickly locate specific utility implementations
3. **Extensibility** - Adding new utility types becomes a clear, templated process
4. **Testing Granularity** - Per-utility test organization and coverage analysis
5. **Documentation Clarity** - Each utility type can have extensive module-level documentation

**Backward Compatibility:** 100% - All existing imports continue to work via `__init__.py` re-exports.

**Risk Assessment:** Very Low - This is a pure refactoring with comprehensive test coverage to verify bit-identical behavior.

---

## Current State Analysis

### File Structure (As-Is)

```
src/vmt_engine/econ/
└── utility.py (~700 lines)
    ├── Utility (base ABC)
    ├── UCES
    ├── ULinear
    ├── UQuadratic
    ├── UTranslog
    ├── UStoneGeary
    ├── create_utility()
    └── u_total()
```

### Problems with Current Structure

1. **Monolithic File Length**
   - 697 lines in a single module
   - Difficult to navigate during development
   - High cognitive load for code reviews

2. **Mixed Abstraction Levels**
   - Base interface (`Utility` ABC) mixed with concrete implementations
   - Factory functions mixed with utility calculations
   - Hard to distinguish "what you extend" vs "what exists"

3. **Discoverability Issues**
   - New developers must scroll through entire file to find a specific utility
   - No clear visual separation between utility types
   - Documentation for each utility is embedded in class docstrings

4. **Extension Pattern Unclear**
   - Adding a new utility type requires:
     - Finding the right place in a large file
     - Ensuring proper ordering (no logical structure)
     - Remembering to update `create_utility()` factory
   - No template or clear "copy this structure" example

5. **Testing Granularity**
   - Tests reference `src.vmt_engine.econ.utility` as one monolith
   - Hard to see test coverage per utility type at a glance
   - Integration of new utility requires touching existing test structure

---

## Proposed Structure

### Directory Layout (To-Be)

```
src/vmt_engine/econ/
├── __init__.py           # Re-exports for backward compatibility
├── utility.py            # Base abstractions only (~150 lines)
│   ├── Utility (ABC)
│   ├── u_total()
│   └── create_utility() [factory delegates to registry]
└── utilities/
    ├── __init__.py       # Re-exports all concrete utilities
    ├── ces.py            # UCES (~120 lines)
    ├── linear.py         # ULinear (~80 lines)
    ├── quadratic.py      # UQuadratic (~120 lines)
    ├── translog.py       # UTranslog (~150 lines)
    └── stone_geary.py    # UStoneGeary (~130 lines)
```

### Module Responsibilities

#### `src/vmt_engine/econ/__init__.py`
```python
"""
Economic primitives for VMT simulation.

This module provides:
- Utility function abstractions and implementations
- Total utility calculation (goods + money)
- Factory for creating utilities from configuration
"""

# Re-export base abstractions
from .utility import Utility, u_total, create_utility

# Re-export concrete utilities
from .utilities import (
    UCES,
    ULinear,
    UQuadratic,
    UTranslog,
    UStoneGeary,
)

__all__ = [
    # Base
    "Utility",
    "u_total",
    "create_utility",
    # Concrete implementations
    "UCES",
    "ULinear",
    "UQuadratic",
    "UTranslog",
    "UStoneGeary",
]
```

**Purpose:** Maintain 100% backward compatibility. All existing imports continue to work:
```python
# All of these continue to work unchanged
from src.vmt_engine.econ.utility import UCES, ULinear
from src.vmt_engine.econ import UCES
from src.vmt_engine.econ.utility import Utility
```

#### `src/vmt_engine/econ/utility.py` (New Version)
**Reduced to ~150 lines**

Contents:
- `Utility` abstract base class with protocol definition
- `u_total(inventory, params)` - top-level utility calculator
- `create_utility(config)` - factory function (delegates to registry)
- Module-level documentation on money-aware API

**Rationale:** This file becomes the "contract" that all utilities must implement. It's the first place a developer looks to understand what methods a new utility needs.

#### `src/vmt_engine/econ/utilities/__init__.py`
```python
"""
Concrete utility function implementations.

Each utility type is in its own module for clarity and maintainability.
"""

from .ces import UCES
from .linear import ULinear
from .quadratic import UQuadratic
from .translog import UTranslog
from .stone_geary import UStoneGeary

__all__ = [
    "UCES",
    "ULinear", 
    "UQuadratic",
    "UTranslog",
    "UStoneGeary",
]
```

#### Individual Utility Modules

Each utility module (e.g., `ces.py`, `linear.py`) contains:

1. **Comprehensive Module Docstring**
   - Economic theory background
   - Mathematical formulation
   - Parameter constraints and interpretations
   - Example use cases
   - Caveats and edge cases

2. **Single Utility Class**
   - `__init__` with parameter validation
   - `u()` / `u_goods()` implementations
   - `mu_A()`, `mu_B()` analytic marginal utilities
   - `mrs_A_in_B()` marginal rate of substitution
   - `reservation_bounds_A_in_B()` for trading

3. **Helper Functions** (if needed)
   - E.g., `_ln_u()` for Translog
   - Zero-safe calculations
   - Overflow protection

**Example:** `src/vmt_engine/econ/utilities/ces.py`
```python
"""
CES (Constant Elasticity of Substitution) Utility Function.

Economic Theory
---------------
The CES utility function represents preferences with constant elasticity 
of substitution σ = 1/(1-ρ):

    U(A, B) = [wA · A^ρ + wB · B^ρ]^(1/ρ)

Special Cases:
- ρ → 0: Cobb-Douglas utility (U = A^wA · B^wB)
- ρ → 1: Linear utility (perfect substitutes)
- ρ → -∞: Leontief utility (perfect complements)

Parameters
----------
ρ (rho): Elasticity parameter (ρ ≠ 1)
    - ρ < 0: Goods are complements (balanced bundles preferred)
    - ρ > 0: Goods are substitutes (imbalance tolerated)
    - ρ close to 0: Approaches Cobb-Douglas

wA, wB: Positive weights
    - Relative importance of goods A and B
    - Do NOT need to sum to 1 (arbitrary scale)
    - Ratio wA/wB affects relative valuation

Marginal Rate of Substitution
------------------------------
    MRS = (wA/wB) · (A/B)^(ρ-1)

The MRS decreases as A increases (diminishing marginal utility) when ρ < 1.

Zero-Handling
-------------
For ρ < 0 (complements), zero inventory in either good causes utility → 0.
This is economically meaningful: you cannot substitute one good for another.

For ρ > 0 (substitutes), zero inventory in one good is less catastrophic.

Implementation Notes
--------------------
- Uses epsilon-shift (1e-12) for A/B ratio when either is zero
- Utility calculation itself is NOT epsilon-shifted (preserves true zeros)
- Analytic MRS with careful zero-guarding

References
----------
- Arrow, K. J., Chenery, H. B., Minhas, B. S., & Solow, R. M. (1961). 
  "Capital-labor substitution and economic efficiency." 
  The Review of Economics and Statistics, 225-250.
"""

from __future__ import annotations
from src.vmt_engine.econ.utility import Utility


class UCES(Utility):
    """CES (Constant Elasticity of Substitution) utility function."""
    
    def __init__(self, rho: float, wA: float, wB: float):
        """
        Initialize CES utility: U = [wA * A^ρ + wB * B^ρ]^(1/ρ)
        
        Args:
            rho: Elasticity parameter (ρ ≠ 1)
            wA: Weight for good A (> 0)
            wB: Weight for good B (> 0)
            
        Raises:
            ValueError: If rho == 1.0 or weights are non-positive
        """
        if rho == 1.0:
            raise ValueError("CES utility cannot have rho=1.0")
        if wA <= 0 or wB <= 0:
            raise ValueError("CES weights must be positive")
        
        self.rho = rho
        self.wA = wA
        self.wB = wB
    
    # ... rest of implementation ...
```

---

## Migration Strategy

### Phase 1: Create New Structure (Non-Breaking)

**Duration:** 2-3 hours

1. Create `src/vmt_engine/econ/utilities/` directory
2. Create individual utility modules (ces.py, linear.py, etc.)
3. Copy implementations from current `utility.py`
4. Add comprehensive module docstrings to each
5. Create `utilities/__init__.py` with re-exports

**Validation:** Import each utility class from new location manually in Python REPL.

### Phase 2: Refactor Base Module

**Duration:** 1-2 hours

1. Trim `utility.py` to only base abstractions:
   - Keep `Utility` ABC
   - Keep `u_total()`
   - Keep `create_utility()` (update imports)
2. Update imports in `utility.py` to reference `utilities/` modules
3. Update `econ/__init__.py` to re-export from both places

**Validation:** Ensure `create_utility()` factory still works with all utility types.

### Phase 3: Update Package Imports

**Duration:** 1-2 hours

1. Update `src/vmt_engine/econ/__init__.py` with comprehensive re-exports
2. Add deprecation comments (not warnings) to guide future developers
3. Document import patterns in module docstrings

**Validation:** Run test suite - should be 100% green with zero code changes.

### Phase 4: Update Tests (Optional Reorganization)

**Duration:** 3-4 hours

While not required for backward compatibility, tests could be reorganized:

**Current:** `tests/test_utility_*.py` (one file per utility type - already good!)

**Enhancement:**
```
tests/
├── test_utility_base.py          # Test Utility ABC, u_total(), factory
└── test_utility_implementations/
    ├── test_ces.py
    ├── test_linear.py
    ├── test_quadratic.py
    ├── test_translog.py
    └── test_stone_geary.py
```

**Optional:** Mirror the source structure in tests for clarity.

### Phase 5: Update Documentation

**Duration:** 1-2 hours

1. Update `docs/2_technical_manual.md` to reference new structure
2. Update `docs/CODE_REVIEW_GUIDE.md` section on utility functions
3. Update `docs/proposals/developer_onboarding_program.md` Module 1 references
4. Add "Adding a New Utility Type" guide to technical manual

**Validation:** Verify all documentation links and code references.

### Phase 6: Determinism Verification

**Duration:** 30 minutes

Run comprehensive determinism tests to ensure bit-identical behavior:

```bash
# Run each scenario 3 times with same seed
for scenario in scenarios/*.yaml; do
    for run in 1 2 3; do
        python main.py "$scenario" 42
    done
    # Diff telemetry outputs - must be identical
done

# Run full test suite
pytest -v

# Run regression tests
pytest tests/test_barter_integration.py
pytest tests/test_money_phase1_integration.py
pytest tests/test_utility_*.py
```

**Success Criteria:** 
- All tests pass
- Zero test changes required
- Telemetry outputs bit-identical across runs

---

## Backward Compatibility Guarantee

### Import Compatibility Matrix

All existing import patterns continue to work:

| Import Statement | Status | Notes |
|-----------------|--------|-------|
| `from src.vmt_engine.econ.utility import UCES` | ✅ Works | Re-exported via `__init__.py` |
| `from src.vmt_engine.econ import UCES` | ✅ Works | Re-exported via `econ/__init__.py` |
| `from src.vmt_engine.econ.utility import Utility` | ✅ Works | Still in `utility.py` |
| `from src.vmt_engine.econ.utility import create_utility` | ✅ Works | Still in `utility.py` |
| `from src.vmt_engine.econ.utility import u_total` | ✅ Works | Still in `utility.py` |
| `from src.vmt_engine.econ.utilities import UCES` | ✅ Works | New explicit path (preferred) |
| `from src.vmt_engine.econ.utilities.ces import UCES` | ✅ Works | New direct path |

### Code That Does NOT Need Updating

1. **Scenario Loading** - `src/scenarios/loader.py` uses `create_utility()` factory (unchanged)
2. **Simulation Engine** - References `Utility` protocol, not concrete classes
3. **Testing** - Tests import from `utility` module (re-exports work)
4. **Quotes System** - Uses `agent.utility` (duck-typed, no imports)
5. **Matching System** - Uses `Utility` protocol methods (unchanged)

### Code That COULD Be Updated (Optional)

For clarity and best practices, these could switch to explicit imports:

```python
# Current (still works)
from src.vmt_engine.econ.utility import UCES, ULinear

# New explicit style (preferred for new code)
from src.vmt_engine.econ.utilities import UCES, ULinear

# Or even more explicit (for one-off use)
from src.vmt_engine.econ.utilities.ces import UCES
```

**Decision:** Update these opportunistically during future refactors, not as part of this migration.

---

## Benefits Analysis

### 1. Developer Experience

**Before:** "Where is the Translog implementation?"
- Open `utility.py` (700 lines)
- Scroll or search
- Context-switch between multiple classes

**After:** "Where is the Translog implementation?"
- Navigate to `utilities/translog.py`
- See complete implementation with theory documentation
- No cognitive overload from unrelated utilities

### 2. Code Review Quality

**Before:** PR adding new utility type
- Reviewer sees 700-line file with +80 lines somewhere
- Hard to see "what changed" vs "what was already there"
- Comments scattered across large diff

**After:** PR adding new utility type
- Reviewer sees new file `utilities/new_utility.py` (clean, isolated)
- Clear template structure (copy from `linear.py` as simplest example)
- Factory update in `create_utility()` is obvious
- Re-export in `utilities/__init__.py` is obvious

### 3. Documentation Richness

**Before:** Class docstrings must be concise (file already long)
- Economic theory compressed to 2-3 lines
- No space for examples or derivations
- References omitted

**After:** Module docstrings can be extensive
- Full economic theory exposition (10-20 lines)
- Mathematical derivations shown explicitly
- Special cases documented (e.g., ρ→0 for Cobb-Douglas)
- Caveats and edge cases explained
- Academic references included

### 4. Testing Organization

**Before:** `tests/test_utility_translog.py` imports from monolithic module
- Coverage reports show "utility.py: 87%" (which parts?)
- Hard to see if new utility is well-tested

**After:** `tests/test_utility_implementations/test_translog.py`
- Coverage reports show "utilities/translog.py: 95%"
- Clear 1:1 mapping between source and test files
- Template for new utility tests

### 5. Extensibility Template

**Adding a New Utility: Before**
1. Open 700-line `utility.py`
2. Find where to insert (alphabetical? by complexity?)
3. Copy an existing class (which one?)
4. Implement methods
5. Scroll to find `create_utility()` factory (line 622)
6. Add new case to factory
7. Hope you didn't miss anything

**Adding a New Utility: After**
1. Copy `utilities/linear.py` → `utilities/new_utility.py` (simplest template)
2. Rename class, update parameters
3. Implement methods (all in one place)
4. Add to `utilities/__init__.py` re-exports (one line)
5. Add case to `create_utility()` factory in `utility.py` (one line)
6. Create `tests/test_utility_implementations/test_new_utility.py` (mirror structure)

**Documentation:** Add "Adding a New Utility Type" section to technical manual with explicit steps.

---

## Risks and Mitigations

### Risk 1: Import Confusion
**Description:** Developers might not know which import path to use.

**Mitigation:**
- Comprehensive `__init__.py` re-exports ensure all paths work
- Documentation shows preferred style: `from src.vmt_engine.econ import UCES`
- Code review enforces consistency in new code

### Risk 2: Circular Import Issues
**Description:** If `utilities/` modules need to import from `utility.py`, cycles could occur.

**Mitigation:**
- Careful import design: utilities import `Utility` ABC from parent
- Use `from __future__ import annotations` for type hints
- Test imports during Phase 1 validation

### Risk 3: IDE Tooling Breaks
**Description:** Auto-complete or refactoring tools might break.

**Mitigation:**
- Re-exports in `__init__.py` preserve IDE auto-complete
- Test in VSCode, PyCharm, Cursor before finalizing
- Explicit `__all__` declarations guide IDEs

### Risk 4: Test Fragility
**Description:** Moving code might expose hidden dependencies.

**Mitigation:**
- Run full test suite after each phase
- Determinism verification catches any behavioral changes
- Comprehensive test coverage (316+ tests) catches issues early

### Risk 5: Merge Conflicts
**Description:** If multiple developers have PRs touching `utility.py`, conflicts arise.

**Mitigation:**
- Announce refactoring in advance (freeze `utility.py` changes)
- Perform migration when no other PRs are pending
- Complete migration in single PR to minimize conflict window

---

## Timeline and Effort Estimate

**Total Effort:** 8-12 hours (single developer, full-time equivalent: 1-2 days)

| Phase | Task | Duration | Dependencies |
|-------|------|----------|--------------|
| 1 | Create new utilities/ modules | 2-3 hours | None |
| 2 | Refactor base utility.py | 1-2 hours | Phase 1 |
| 3 | Update package imports | 1-2 hours | Phase 2 |
| 4 | Reorganize tests (optional) | 3-4 hours | Phase 3 |
| 5 | Update documentation | 1-2 hours | Phase 3 |
| 6 | Determinism verification | 30 min | Phase 5 |

**Recommended Schedule:**
- **Week 1, Day 1-2:** Phases 1-3 (core refactoring)
- **Week 1, Day 3:** Phase 6 (verification) + buffer time
- **Week 2, Day 4-5:** Phases 4-5 (optional enhancements + docs)

**Parallelization:** Documentation updates (Phase 5) can happen alongside test reorganization (Phase 4).

---

## Priority and Scheduling Recommendation

### Priority Assessment: **Low (Quality-of-Life)**

**Rationale:**
- No blocking issues with current structure
- No performance or correctness problems
- Primarily developer experience improvement
- Low urgency compared to Protocol Modularization (higher priority)

### Recommended Timing

**Option 1: Pair with Protocol Modularization**
- Tackle utility modularization *after* Protocol Modularization completes
- Establishes consistent modularization pattern across codebase
- Lessons learned from protocol refactor applied here

**Option 2: Low-Activity Period**
- Perform during a maintenance phase
- Ideal when no major features are in development
- Reduces risk of merge conflicts

**Option 3: New Developer Onboarding**
- Assign to a new developer completing Module 1 of onboarding program
- Excellent learning exercise (touch all utility implementations)
- Builds deep understanding of economic foundations
- Produces immediately valuable contribution

**Recommendation:** Option 3 (Onboarding Exercise) or Option 2 (Low-Activity Period)

---

## Success Criteria

Upon completion, the refactoring is successful if:

### Functional Criteria
- [ ] All 316+ tests pass without modification
- [ ] Determinism verification succeeds (3 runs with same seed → identical telemetry)
- [ ] No linter errors introduced (Ruff, Black, Mypy)
- [ ] Scenario loading works for all 20+ existing scenarios

### Structural Criteria
- [ ] Each utility type in its own file (<150 lines per file)
- [ ] `utility.py` reduced to <200 lines (base abstractions only)
- [ ] Clear `utilities/__init__.py` with all re-exports
- [ ] Comprehensive module docstrings for each utility (>20 lines)

### Documentation Criteria
- [ ] Technical manual updated with new structure
- [ ] Code review guide updated
- [ ] "Adding a New Utility Type" guide added
- [ ] Developer onboarding references updated

### Developer Experience Criteria
- [ ] New developer can locate specific utility in <30 seconds
- [ ] Adding new utility type follows clear template
- [ ] Import auto-complete works in VSCode/PyCharm/Cursor
- [ ] Code review diffs are clear and isolated

---

## Alternative Approaches Considered

### Alternative 1: Keep Monolithic Structure
**Rationale:** "If it ain't broke, don't fix it."

**Pros:**
- Zero effort required
- No risk of introducing bugs
- Familiar to existing developers

**Cons:**
- File continues to grow (ULeontief, UCobb-Douglas variants, etc.)
- Developer experience remains suboptimal
- Extensibility pattern unclear

**Decision:** Rejected - Proactive refactoring prevents future pain.

---

### Alternative 2: Utilities in Separate Package
**Structure:**
```
src/
├── vmt_engine/...
└── vmt_utilities/        # Separate top-level package
    ├── __init__.py
    ├── ces.py
    ├── linear.py
    └── ...
```

**Pros:**
- Clearest separation (utilities are "pluggable")
- Could be distributed as separate package

**Cons:**
- Over-engineering for current use case
- Adds complexity (two packages to manage)
- Import paths become longer

**Decision:** Rejected - Utilities are core to VMT, not "plugins."

---

### Alternative 3: Single File with Internal Sections
**Structure:** Add `# region` markers in current `utility.py`:
```python
# region Base Abstractions
class Utility(ABC): ...

# region CES Utility
class UCES(Utility): ...

# region Linear Utility
class ULinear(Utility): ...
```

**Pros:**
- Minimal refactoring effort
- Some IDEs support collapsible regions
- Backward compatible by default

**Cons:**
- Still a 700-line file
- Region support varies by IDE
- Doesn't improve test organization
- Doesn't enable rich module documentation

**Decision:** Rejected - Insufficient improvement for effort.

---

### Alternative 4: Class-Per-File with Flat Structure
**Structure:**
```
src/vmt_engine/econ/
├── utility.py          # Base only
├── utility_ces.py
├── utility_linear.py
├── utility_quadratic.py
├── utility_translog.py
└── utility_stone_geary.py
```

**Pros:**
- Simple flat hierarchy
- One-to-one file-class mapping
- No nested imports

**Cons:**
- Namespace pollution (`utility_*` feels repetitive)
- Less clear logical grouping (utilities are a category)
- Doesn't scale well (imagine 20 utility types)

**Decision:** Rejected - Nested `utilities/` package is cleaner.

---

## Relationship to Other Initiatives

### Protocol Modularization
**Status:** Planned (high priority)  
**Relationship:** Complementary

This utility modularization follows similar principles:
- Separate abstractions from implementations
- Improve extensibility
- Maintain backward compatibility
- Template-driven development

**Lesson Learned from Protocol Modularization:** If protocol refactor establishes a modularization pattern, follow it here for consistency.

### Developer Onboarding Program
**Status:** Active  
**Relationship:** Supportive

Module 1 of onboarding requires deep reading of `utility.py`. Modularization:
- Makes utility implementations easier to study (one at a time)
- Provides clearer template for "add a new utility" exercise
- Reduces cognitive load during initial learning

**Update Required:** Module 1 materials reference line numbers in `utility.py` - update to reference new structure.

### Phase C Market Mechanisms
**Status:** Long-term (6-12 months out)  
**Relationship:** Independent

Phase C focuses on trading protocols, not utility functions. However, clean utility architecture ensures:
- Easy to add experimental utility types for research
- Clear separation between preferences (utilities) and mechanisms (protocols)
- Modular testing of market mechanisms with different utility mixes

---

## Implementation Checklist

### Pre-Implementation
- [ ] Announce refactoring plan to team (if applicable)
- [ ] Check for pending PRs that touch `utility.py`
- [ ] Freeze changes to `utility.py` during migration
- [ ] Create feature branch: `refactor/utility-modularization`

### Phase 1: Create Structure
- [ ] Create `src/vmt_engine/econ/utilities/` directory
- [ ] Create `utilities/ces.py` with comprehensive docstring
- [ ] Create `utilities/linear.py` with comprehensive docstring
- [ ] Create `utilities/quadratic.py` with comprehensive docstring
- [ ] Create `utilities/translog.py` with comprehensive docstring
- [ ] Create `utilities/stone_geary.py` with comprehensive docstring
- [ ] Create `utilities/__init__.py` with re-exports
- [ ] Test imports manually in Python REPL

### Phase 2: Refactor Base
- [ ] Trim `utility.py` to base abstractions only
- [ ] Update imports in `utility.py` to reference `utilities/`
- [ ] Update `create_utility()` to import from `utilities/`
- [ ] Verify `create_utility()` works for all utility types

### Phase 3: Update Package
- [ ] Update `econ/__init__.py` with comprehensive re-exports
- [ ] Add `__all__` declarations
- [ ] Test all import patterns (see compatibility matrix)
- [ ] Run test suite (should be 100% green)

### Phase 4: Tests (Optional)
- [ ] Create `tests/test_utility_implementations/` directory
- [ ] Move tests into subdirectory (or keep flat - TBD)
- [ ] Update imports if reorganized
- [ ] Run full test suite (should be 100% green)

### Phase 5: Documentation
- [ ] Update `docs/2_technical_manual.md`
- [ ] Update `docs/CODE_REVIEW_GUIDE.md`
- [ ] Update `docs/proposals/developer_onboarding_program.md`
- [ ] Add "Adding a New Utility Type" guide
- [ ] Update CHANGELOG.md (mention refactoring)

### Phase 6: Verification
- [ ] Run full test suite: `pytest -v`
- [ ] Run determinism tests (3 runs, same seed)
- [ ] Run type checker: `mypy src/`
- [ ] Run linter: `ruff check .`
- [ ] Run formatter: `black --check .`
- [ ] Test scenario loading for all scenarios
- [ ] Verify telemetry bit-identical

### Post-Implementation
- [ ] Merge to main via PR
- [ ] Tag commit: `refactor-utility-modularization`
- [ ] Update any external documentation
- [ ] Close this proposal (mark as Implemented)

---

## Conclusion

Modularizing the utility module is a low-risk, high-value refactoring that improves developer experience, code clarity, and extensibility. While not urgent, it provides immediate benefits to new developers working through the onboarding program and establishes a clean template for future utility additions.

The proposed structure maintains 100% backward compatibility through careful use of `__init__.py` re-exports, ensuring zero disruption to existing code while enabling better organization going forward.

**Recommendation:** Proceed with refactoring during a low-activity period or assign as an onboarding exercise to a new developer completing Module 1.

---

**Document History:**
- 2025-10-25: Initial draft (v1.0)

**Maintainer:** VMT Core Team  
**Review Status:** Awaiting feedback

---

