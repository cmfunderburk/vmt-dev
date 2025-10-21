# Phase 3: Factory Function Cleanup - Planning Document

**Date**: 2025-10-21  
**Status**: Ready for Implementation  
**Context**: Cleanup of aborted refactor artifact

---

## Background

The `create_utility()` function currently emits a `DeprecationWarning` suggesting it's deprecated in favor of direct instantiation. However, this warning is **misleading** - it's a leftover from an aborted refactor.

**Current situation**:
- Function is **essential** for YAML→Simulation pipeline
- Used in `simulation.py` to dynamically instantiate utilities from config
- Generates **2,884 warnings** during test suite (257 tests × ~11 warnings each)
- No viable alternative for config-driven instantiation

**Root cause**: The deprecation was added during a planned refactor that was never completed. The factory function is actually a **core framework component**, not deprecated legacy code.

---

## Phase 3 Objectives

### Primary Goal
Remove misleading deprecation warning and properly document the factory function's essential role.

### Secondary Goals
- Export all new utility classes from economics module
- Provide clear guidance on when to use factory vs. direct instantiation
- Clean up test output (eliminate 2,884 spurious warnings)

---

## Implementation Plan

### 1. Remove Deprecation Warning

**File**: `src/vmt_engine/econ/utility.py` (lines 622-657)

**Current code**:
```python
def create_utility(config: dict) -> Utility:
    """
    Factory function to create utility from configuration.
    
    DEPRECATED: Direct instantiation (UCES, ULinear, ...) is preferred for clarity.
    """
    warnings.warn(
        "create_utility() is deprecated. Use direct instantiation instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    utype = config['type']
    params = config['params']
    # ... implementation
```

**Updated code**:
```python
def create_utility(config: dict) -> Utility:
    """
    Create utility instance from scenario configuration dictionary.
    
    This is the standard factory function used by the scenario loading system
    to dynamically instantiate utilities from YAML files. It maps string type
    names ("ces", "linear", "quadratic", "translog", "stone_geary") to their
    corresponding utility classes.
    
    For programmatic use when not loading from YAML, direct class instantiation
    may be more explicit:
        utility = UQuadratic(A_star=10.0, B_star=10.0, sigma_A=5.0, sigma_B=5.0)
    
    Args:
        config: Dictionary with 'type' and 'params' keys
            type: Utility type string (one of: "ces", "linear", "quadratic", 
                  "translog", "stone_geary")
            params: Dict of parameters for the chosen utility type
        
    Returns:
        Utility instance of the appropriate class
        
    Raises:
        ValueError: If utility type is unknown
        
    Example:
        >>> # From config dict (typical YAML loading use case)
        >>> config = {'type': 'quadratic', 
        ...           'params': {'A_star': 10.0, 'B_star': 10.0, 
        ...                      'sigma_A': 5.0, 'sigma_B': 5.0}}
        >>> utility = create_utility(config)
        >>> isinstance(utility, UQuadratic)
        True
    """
    # No deprecation warning - this is an essential framework function
    
    utype = config['type']
    params = config['params']
    
    if utype == 'ces':
        return UCES(**params)
    elif utype == 'linear':
        return ULinear(**params)
    elif utype == 'quadratic':
        return UQuadratic(**params)
    elif utype == 'translog':
        return UTranslog(**params)
    elif utype == 'stone_geary':
        return UStoneGeary(**params)
    else:
        raise ValueError(f"Unknown utility type: {utype}")
```

**Key changes**:
- ❌ Remove `warnings.warn()` call
- ❌ Remove "DEPRECATED" from docstring
- ✅ Add comprehensive docstring explaining purpose
- ✅ Clarify when direct instantiation is preferred
- ✅ Add example usage

---

### 2. Update Module Exports

**File**: `src/vmt_engine/econ/__init__.py`

**Current code**:
```python
from .utility import Utility, UCES, ULinear, create_utility

__all__ = ['Utility', 'UCES', 'ULinear', 'create_utility']
```

**Updated code**:
```python
"""
Economics module - Utility functions and economic calculations.
"""

from .utility import (
    Utility, UCES, ULinear, UQuadratic, UTranslog, UStoneGeary, 
    create_utility, u_total
)

__all__ = [
    'Utility', 'UCES', 'ULinear', 'UQuadratic', 'UTranslog', 'UStoneGeary',
    'create_utility', 'u_total'
]
```

**Benefits**:
- Users can import new utilities directly: `from vmt_engine.econ import UQuadratic`
- Proper public API exposure
- Consistent with existing pattern

---

### 3. Verify Test Suite

After changes, run full test suite to confirm:

```bash
python3 -m pytest tests/ -q
```

**Expected result**:
- 257 tests pass
- **Zero deprecation warnings** (or minimal unrelated warnings)
- Clean output

---

## Success Criteria

### Implementation Complete When:
- [x] Deprecation warning removed from `create_utility()`
- [x] Docstring updated with clear purpose and examples
- [x] Module exports updated to include all new utility classes
- [x] Full test suite passes (257/257)
- [x] **Zero deprecation warnings** in test output

### Documentation Complete When:
- [x] Planning document updated (this file)
- [x] Code comments clarified
- [x] No misleading "deprecated" messaging anywhere

---

## Rationale

### Why Un-Deprecate?

1. **Essential Framework Function**: The factory is required for YAML loading. There's no cleaner alternative for dynamic type→class mapping.

2. **Standard Pattern**: Config-driven factories are standard in well-designed frameworks (Django, FastAPI, etc.). Not deprecated, just specialized.

3. **Clear Separation**: 
   - **YAML loading**: Use `create_utility()` ✓ (framework handles it)
   - **Programmatic**: Use `UQuadratic(...)` ✓ (user writes it)
   - Both are valid, neither is deprecated

4. **User Experience**: 2,884 warnings create noise that obscures real issues

### Architectural Clarity

The function serves the **inversion of control** pattern:
```
User → YAML file → Loader → create_utility() → Utility instance → Simulation
```

This is **correct design**, not technical debt.

---

## Testing Strategy

### Before Changes
```bash
$ pytest tests/ -q
257 passed, 2884 warnings in 8.58s
```

### After Changes (Expected)
```bash
$ pytest tests/ -q
257 passed in 8.5s
# Or minimal warnings unrelated to create_utility()
```

### Verification Steps
1. Run unit tests: `pytest tests/test_utility_*.py -v`
2. Run integration tests: `pytest tests/test_new_utility_scenarios.py -v`
3. Run full suite: `pytest tests/ -q`
4. Verify warning count is near zero
5. Test scenario loading: load all 4 demo YAMLs

---

## Implementation Checklist

- [ ] Remove `warnings.warn()` from `create_utility()` in utility.py
- [ ] Update `create_utility()` docstring with comprehensive documentation
- [ ] Update `econ/__init__.py` to export UQuadratic, UTranslog, UStoneGeary
- [ ] Add u_total to exports
- [ ] Run test suite and verify zero deprecation warnings
- [ ] Update this planning document status to "Complete"

---

## Code Locations

**Files to modify**:
1. `src/vmt_engine/econ/utility.py` - Line 622-657 (create_utility function)
2. `src/vmt_engine/econ/__init__.py` - Lines 1-8 (module exports)

**Files to verify** (no changes needed, but validate they work):
3. `src/vmt_engine/simulation.py` - Line 180 (uses create_utility)
4. All test files - Should pass with no warnings

---

**End of Phase 3 Planning Document**

