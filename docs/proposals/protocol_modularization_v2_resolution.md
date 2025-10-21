# VMT Protocol Modularization Plan - Issue Resolution Status

**Review Date:** 2025-10-20  
**Plan Version:** 2.0  
**Status:** Ready for Project Lead Review

---

## Issues Addressed in Version 2.0

### ✅ RESOLVED

#### Issue 2.1: Mode-Aware Behavior
**Resolution:** Added `current_mode` parameter to `ProtocolContext` object (Section 4).
- All protocol methods now receive mode through context
- Documented mode-specific behavior in method docstrings
- See: Lines 92-100 (ProtocolContext), Lines 151-155 (SearchProtocol), Lines 216-220 (MatchingProtocol)

#### Issue 2.2: Resource Claiming Integration
**Resolution:** SearchProtocol handles claims directly (Section 5.1).
- Protocol receives all resources
- Protocol must filter based on `context.resource_claims`
- Protocol updates claims map after selection
- Documented in `select_forage_target()` docstring lines 133-143

#### Issue 2.3: Trade Cooldowns Integration
**Resolution:** MatchingProtocol handles cooldowns (Section 5.2).
- Protocol filters cooldowns in `build_preferences()`
- Documented cooldown logic lines 222-229
- Example implementation in `GreedyMatching` lines 606-616

#### Issue 3.1: Pairing Lifecycle Management
**Resolution:** Added comprehensive Section 6.1.
- Explains pairing establishment (mutual consent + fallback)
- Explains pairing persistence across ticks
- Explains pairing termination conditions
- Documents protocol implications

#### Issue 3.2: Pass 3b Handling
**Resolution:** Added Section 6.2.
- Explains unfulfilled trade target cleanup
- Shows code example
- Clarifies engine vs. protocol responsibility
- Documents mode-specific fallback behavior

#### Issue 4.1: Parameter Access
**Resolution:** Created `ProtocolContext` object (Section 4).
- Frozen dataclass prevents state corruption
- Provides typed access to all parameters
- Includes convenience properties for common params
- Single parameter instead of 5-10 individual args

#### Issue 4.2: Surplus Computation
**Resolution:** Documented as shared utility (Section 7.1).
- Remains in `matching.py` for now
- Will move to TradeProtocol in future phases
- Import path documented for protocol implementations

#### Issue 5.1: Telemetry Responsibilities
**Resolution:** Added comprehensive Section 8.
- Clear separation: protocols update state, engine logs
- Documented what protocols DO and DO NOT do
- State contract defined (preference_list, etc.)
- Design rationale explained

#### Issue 7.1: Coupled Refactoring
**Resolution:** Revised Section 3 and 6.
- Line 51: "Critical Constraint: Search and matching are tightly coupled"
- Acknowledges they must be refactored together
- Phased approach wraps both simultaneously

#### Issue 8.1: Future Work
**Resolution:** Added Part VI (Sections 17-18).
- TradeProtocol/BargainingProtocol specification
- Market Protocol overview
- Extension points (composition, adaptive, multi-agent)
- Timelines for future phases

---

## Open Design Decisions (Require Input)

### Decision Point 1: Legacy Wrapper Implementation

**Section:** 10.1  
**Question:** How should legacy code be wrapped?

**Options:**
- **A - Extraction:** Extract logic into standalone protocols (cleaner, more work)
- **B - Delegation:** Thin wrappers calling existing DecisionSystem (faster, messier)
- **C - Hybrid:** Start with delegation, extract in Phase 2 (balanced)

**Recommendation:** Option C (Hybrid) - establishes interfaces quickly while allowing validation before full refactor.

**Action Required:** Project lead to select option.

### Decision Point 2: Backward Compatibility

**Section:** 10.2  
**Question:** How should scenarios without `protocols` field behave?

**Options:**
- **A - Python defaults:** `Simulation.__init__()` default args (simple, less flexible)
- **B - YAML optional field:** Protocol registry + YAML config (flexible, more complex)
- **C - Hybrid:** YAML can specify, Python can override (maximum flexibility, most complex)

**Recommendation:** Option A for Phase 1 (minimize risk), migrate to Option C in Phase 3.

**Action Required:** Project lead to select option.

---

## Deferred Technical Issues

### Issue 1.1: PerceptionView vs. dict Inconsistency

**Status:** Deferred - requires separate technical decision  
**Current Approach:** Interfaces use `perception_cache: dict`  
**Impact:** Low - doesn't block implementation  
**Notes:** 
- `PerceptionView` dataclass exists but isn't stored on agents
- Current code uses `agent.perception_cache = {...}` (dict)
- Resolution needed before protocols can be fully type-checked
- Recommendation: Standardize on PerceptionView dataclass for type safety

**Action Required:** Separate technical design discussion.

### Issue 1.2: Target Type Definition

**Status:** Deferred - pending decision on formalization  
**Current Approach:** Interfaces use `Optional[Position]`  
**Impact:** Low - existing behavior in `decision.py` is preserved  
**Notes:**
- Current code uses `agent.target_pos: Optional[Position]`
- Sometimes targets are resource cells, sometimes agent positions
- Formal `Target = Union[Cell, Agent, Position]` type not yet defined
- May not be needed if Position representation is sufficient

**Action Required:** Evaluate if formal type is needed after Phase 1 implementation.

---

## Document Quality Checklist

### Completeness
- [x] All protocol interfaces defined with type signatures
- [x] Mode-awareness integrated throughout
- [x] Resource claiming logic documented
- [x] Trade cooldown logic documented  
- [x] Pairing lifecycle fully explained
- [x] Telemetry responsibilities clarified
- [x] Testing requirements specified
- [x] Future work outlined

### Implementation Readiness
- [x] ProtocolContext object specified
- [x] Concrete implementation examples provided (GreedyMatching)
- [x] Integration with 7-phase cycle mapped
- [x] Migration phases defined with deliverables
- [x] Success criteria measurable

### Open Issues
- [ ] Wrapper implementation approach (awaiting decision)
- [ ] Backward compatibility approach (awaiting decision)
- [ ] PerceptionView type resolution (deferred)
- [ ] Target type formalization (deferred)

---

## Next Steps

### For Project Lead
1. Review Section 10.1 and select wrapper implementation approach
2. Review Section 10.2 and select backward compatibility approach
3. Approve overall plan or request revisions
4. Decide if deferred issues (1.1, 1.2) need resolution before Phase 1

### For Implementation
Once decisions made:
1. Create Phase 1 implementation branch
2. Implement ProtocolContext dataclass
3. Define SearchProtocol and MatchingProtocol ABCs
4. Implement chosen wrapper approach
5. Run regression tests

---

## Critical Success Factors

1. **Zero Regression:** All existing tests must pass with identical telemetry
2. **Determinism:** 100% reproducible results maintained
3. **Performance:** <10% slowdown acceptable
4. **Documentation:** Every protocol implementation includes guide
5. **Type Safety:** All interfaces properly typed and validated

---

## Conclusion

**Plan Status:** Ready for implementation pending two design decisions.

The plan now comprehensively addresses all technical issues identified in the initial review. The architecture is sound, the interfaces are well-defined, and the migration path is clear. The two open design decisions (wrapper approach and backward compatibility) can be made based on project priorities:

- **Risk-averse path:** Delegation wrapper + Python defaults
- **Future-proof path:** Extraction wrapper + YAML config
- **Balanced path:** Hybrid approaches for both

All approaches are viable and fully specified in the document.

