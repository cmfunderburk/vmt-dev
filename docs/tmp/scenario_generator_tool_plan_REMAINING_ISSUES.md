# Scenario Generator Tool - Remaining Issues for Discussion

**Date:** 2025-10-21  
**Status:** Pre-Implementation Review Complete  
**Document:** Updates applied to scenario_generator_tool_plan.md

---

## Summary

All critical and high-priority issues have been addressed in the plan. The tool is **ready for Phase 1 implementation** with one outstanding design question for Phase 2.

---

## ✅ Resolved Issues (Applied to Plan)

### Critical Issues (All Fixed)
1. ✅ Added `schema_version: 1` to generated YAML
2. ✅ Fixed parameter structure (resource params now in main `params` dict)
3. ✅ Clarified CES weight normalization (convention, not requirement)

### High Priority Issues (All Addressed)
4. ✅ Validation deferred to Phase 2 with `--validate` flag
5. ✅ Added inventory range validation (MIN >= 1)
6. ✅ Subsistence validation deferred (non-critical with gamma=0 default)
7. ✅ Refactored parameter generation to explicit approach (no reflection)
8. ⚠️ Phase 2 exchange regime marked as needing resolution (see below)
9. ✅ Money inventory generation documented in section 2.6
10. ✅ Type safety documented (integers for inventories, 2-decimal floats)
11. ✅ `_uniform_excluding` deferred (current implementation sufficient)
12. ✅ Parameter names disambiguated (`gamma_quad` vs `gamma_A_SG`/`gamma_B_SG`)
13. ✅ Agent positioning documented (section 2.7)
14. ✅ Resource distributions noted as future enhancement

---

## ✅ All Issues Resolved

### Phase 2: Exchange Regime Design (RESOLVED)

**Decision:** Keep simple - no mode schedule support in CLI.

**Rationale:**
- Mode schedules (temporal cycling between forage/trade phases) are a power-user feature
- Uncommon use case that adds CLI complexity
- Users who need mode schedules can manually edit YAML post-generation

**Phase 2 Implementation:**
```bash
# Exchange regime selection
--exchange-regime barter_only  # Default (Phase 1)
--exchange-regime money_only   # Phase 2
--exchange-regime mixed        # Phase 2
--exchange-regime mixed_liquidity_gated  # Phase 2

# Money configuration (Phase 2)
--money-range 100,500          # M inventory range
--money-scale 100              # Money scale
--lambda-money 1.0             # Marginal utility of money
--money-mode quasilinear       # quasilinear | kkt_lambda
```

**Mode schedules:** NOT supported in CLI. Manual YAML editing only.

---

## 🟢 Ready for Implementation

### Phase 1 Scope (Clear & Unblocked)
- ✅ CLI with 6 required args + 2 optional
- ✅ All 5 utility types with conservative ranges
- ✅ `barter_only` exchange regime only
- ✅ Integer inventories (A, B)
- ✅ 2-decimal float parameters
- ✅ Seeded randomization
- ✅ Schema-compliant YAML output
- ✅ Inventory validation (MIN >= 1)

### Phase 1 Deliverables
1. `src/vmt_tools/generate_scenario.py` - CLI
2. `src/vmt_tools/param_strategies.py` - Parameter generation
3. `src/vmt_tools/__init__.py` - Package init
4. Unit tests for parameter generation
5. Integration test: generate + load + run scenario

### Estimated Timeline
- **Phase 1:** 1-2 days (no blockers)
- **Phase 2:** 1-2 days (after resolving exchange regime question)
- **Phase 3:** 1 day (Python API refactor)

---

## 📋 Pre-Implementation Checklist

Before starting implementation, confirm:

- [x] Plan reviewed and understood
- [x] Critical issues resolved
- [x] High-priority issues addressed or deferred appropriately
- [x] Phase 1 scope clearly defined
- [x] Phase 2 design question resolved (no mode schedules in CLI)
- [x] **User approval to proceed with Phase 1** ✅

---

## Next Steps

1. ✅ **Review complete** - All issues resolved
2. ✅ **Phase 1 scope approved** - Ready to implement
3. ✅ **Phase 2 design resolved** - No mode schedules in CLI
4. 🚀 **Begin implementation** - Start with Phase 1 MVP

---

## Final Status

**All issues resolved.** The plan is comprehensive, well-specified, and ready for implementation.

- ✅ Schema compliance verified
- ✅ Parameter generation strategy clear
- ✅ Type safety documented
- ✅ Validation approach defined
- ✅ Phase 1 scope unblocked
- ✅ Phase 2 design complete

**Recommendation: Proceed with Phase 1 implementation immediately.**

