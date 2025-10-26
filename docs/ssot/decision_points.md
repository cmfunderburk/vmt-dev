# Critical Decision Points

**Document Status:** ✅ All Decisions Made  
**Version:** 1.1  
**Created:** 2025-01-27  
**Updated:** 2025-10-26  
**Purpose:** Document all key decisions for VMT architectural initiatives

---

## ✅ DECISIONS SUMMARY

**All critical decisions have been resolved and documented below:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Implementation Approach** | Minimal Implementation (4 weeks) | Lower risk, faster delivery, extensible foundation |
| **Utility Base Extraction** | Approved - Proceed Immediately | 2-hour task, zero risk, high clarity value |
| **Effect Application Strategy** | Immediate Application | Simpler implementation, easier debugging |
| **Multi-tick State Storage** | Effect-based (InternalStateUpdate) | Full audit trail, reproducibility, determinism |
| **Protocol Versioning** | Date-based (YYYY.MM.DD) | Aligns with VMT standards, simpler for research |

**Status:** Ready to proceed with implementation

---

## Executive Summary

This document consolidates all design decisions for the VMT architectural initiatives. All decisions have been made and are documented below with full context and rationale.

---

## IMMEDIATE DECISIONS (This Week)

### 1. Overall Implementation Approach ✅ RESOLVED

**Question:** How should we proceed with protocol modularization?

**Option A: Full Implementation**
- 12-week comprehensive refactoring
- All protocols implemented
- Complete documentation
- **Pros:** Unblocks all Phase C features, research-grade system
- **Cons:** 3-month timeline, significant effort

**Option B: Minimal Implementation ✅ SELECTED**
- 4-week infrastructure only
- Legacy adapters only (no new features)
- Extensible foundation
- **Pros:** Lower risk, faster delivery
- **Cons:** No immediate research value

**Option C: Defer Protocol Work**
- Focus on other priorities
- Continue with monolithic system
- **Pros:** No effort required
- **Cons:** Cannot implement Phase C features

**➤ DECISION:** Option B: Minimal Implementation

> cmf: Option B is the official decision - 4-week minimal implementation providing extensible foundation for future protocol work.

### 2. Utility Base Extraction ✅ COMPLETE

**Question:** Should we immediately extract the Utility ABC to base.py?

- **Effort:** 2 hours (actual: ~90 minutes)
- **Risk:** Very Low
- **Benefit:** Cleaner code structure immediately ✅ DELIVERED

**Recommendation:** Yes - proceed immediately

**➤ DECISION:** Yes - Proceed immediately

**➤ STATUS:** ✅ COMPLETE (2025-10-26)
- Created: `src/vmt_engine/econ/base.py` (137 lines)
- Updated: `src/vmt_engine/econ/utility.py` (634 lines, down from 744)
- Tests: 86/86 utility tests passing
- Backward compatibility: Fully maintained

> cmf: decision resolved and implemented -- utility base extraction complete with all verification passed

---

## ARCHITECTURAL DECISIONS (Week 1)

### 3. Effect Application Strategy ✅ RESOLVED

**Question:** How should protocols apply their effects?

**Option A: Immediate Application ✅ SELECTED**
```python
def execute_phase(self):
    effects = protocol.generate_effects()
    for effect in effects:
        self.apply_effect(effect)  # Applied immediately
```
- **Pros:** Simpler, easier debugging
- **Cons:** Less parallelizable

**Option B: Batch Application**
```python
def execute_phase(self):
    all_effects = []
    for protocol in protocols:
        all_effects.extend(protocol.generate_effects())
    self.apply_all_effects(all_effects)  # Applied at end
```
- **Pros:** Better for future parallelization
- **Cons:** Complex conflict resolution

**➤ DECISION:** Option A - Immediate Application

> cmf: this decision resolved in favor of option A - effects applied immediately within each phase for simpler implementation and debugging

### 4. Multi-tick State Storage ✅ RESOLVED

**Question:** How should protocols store state across ticks?

**Option A: Effect-based State ✅ SELECTED**
```python
InternalStateUpdate(
    protocol_name="rubinstein",
    agent_id=0,
    key="round_number",
    value=3
)
```
- **Pros:** Full audit trail, reproducible
- **Cons:** More telemetry overhead

**Option B: Protocol-managed State**
```python
class RubinsteinProtocol:
    def __init__(self):
        self.state = {}  # Protocol owns state
```
- **Pros:** Less telemetry overhead
- **Cons:** Harder to debug, reproduce

**➤ DECISION:** Option A - Effect-based State

> cmf: this has been resolved in favor of option A: effect-based state stored via InternalStateUpdate effects for full audit trail and reproducibility

### 5. Protocol Versioning Scheme ✅ RESOLVED

**Question:** How should we version individual protocols?

**Option A: Semantic Versioning**
- Format: `major.minor.patch` (e.g., "1.0.0")
- Clear compatibility rules
- Industry standard

**Option B: Date-based Versioning ✅ SELECTED**
- Format: `YYYY.MM.DD` (e.g., "2025.01.27")
- Matches current VMT practice
- Simpler for research

**Option C: Simple Integers**
- Format: `v1`, `v2`, `v3`
- Simplest approach
- Less information

**➤ DECISION:** Option B - Date-based Versioning

> cmf: this has been resolved in favor of option B - protocols will use YYYY.MM.DD versioning format to align with VMT project standards and simplify research reproducibility

---

## PRIORITY DECISIONS (Week 2) - DEFERRED

**Note:** These decisions are deferred since minimal implementation does not include alternative protocols. These can be revisited when/if full protocol implementation is undertaken.

### 6. First Alternative Protocols ⏸️ DEFERRED

**Question:** After legacy adapters, which protocols should we implement first?

**Status:** Not applicable for minimal implementation. Deferred until research priorities require specific alternative protocols.

**Research Focus Options (for future reference):**

**Option A: Bargaining Mechanisms**
- Take-it-or-leave-it
- Rubinstein alternating offers
- Nash bargaining
- **Use Case:** Test bargaining power theories

**Option B: Search/Matching Algorithms**  
- Random walk search
- Memory-based search
- Greedy matching
- **Use Case:** Test information/learning theories

**Option C: Phase C Preparation**
- Posted-price markets
- Sealed-bid auctions
- Market makers
- **Use Case:** Prepare for market mechanisms

**➤ DECISION:** Deferred - not applicable to minimal implementation

### 7. Performance Targets ✅ RESOLVED

**Question:** What performance regression is acceptable?

**Current Performance:**
- 100 agents: ~12 ticks/second
- 20 agents: ~125 ticks/second
- 3 agents: ~485 ticks/second

**Options:**
- ⬜ <5% regression (may limit features)
- ✅ <10% regression (recommended)
- ⬜ <20% regression (more flexibility)

**➤ DECISION:** <10% regression target (standard for all VMT refactoring work)

---

## RESOURCE DECISIONS

### 8. Development Allocation ✅ RESOLVED

**Question:** How should development effort be allocated?

**Option A: Dedicated Push**
- One developer, full-time for 12 weeks
- Faster completion
- Consistent architecture

**Option B: Part-time Development ✅ SELECTED**
- 50% allocation over 8 weeks (4 weeks calendar for minimal)
- Allows parallel work
- Appropriate for minimal implementation

**Option C: Team Effort**
- Multiple developers
- Requires more coordination
- Risk of inconsistency

**➤ DECISION:** Part-time development - single developer, ~50% allocation over 4-week minimal implementation

### 9. Testing Strategy ✅ RESOLVED

**Question:** What level of testing is required?

**Minimum (Required):**
- All existing tests pass
- Telemetry backward compatible
- Basic property tests

**Recommended: ✅ SELECTED**
- Above plus:
- Golden standard tests (telemetry equivalence)
- Property-based testing
- Economic validation
- Performance benchmarks (<10% regression)

**Comprehensive:**
- Above plus:
- Comparative analysis (deferred - N/A for minimal)
- Multi-protocol scenarios (deferred - N/A for minimal)
- Formal verification (not planned)

**➤ DECISION:** Recommended level testing - includes golden standard tests for legacy adapter equivalence

---

## OPTIONAL DECISIONS

### 10. Utility Modularization (Phase 2) ✅ RESOLVED

**Question:** When should we do full utility modularization?

- ⬜ After protocol modularization
- ✅ Assign to new developer
- ⬜ Defer indefinitely

**Decision:** Assign to new developer as onboarding exercise (Phase 1 base extraction approved for immediate implementation)

### 11. Developer Onboarding Updates ✅ RESOLVED

**Question:** When should we update onboarding materials?

- ⬜ During protocol implementation
- ✅ After protocols complete
- ⬜ As separate project

**Decision:** After protocols complete and stable

### 12. GUI Integration ✅ RESOLVED

**Question:** How should protocol selection work in GUI?

- ⬜ Dropdown menu per protocol type (deferred - for future with multiple protocols)
- ⬜ Advanced settings dialog (deferred)
- ✅ Config file only initially

**Decision:** Config file only for minimal implementation (GUI integration deferred until multiple protocols exist)

---

## DECISION SUMMARY FORM ✅ COMPLETE

All decisions have been made:

**Immediate:** ✅
1. Implementation Approach: [ ] Full | [✅] Minimal | [ ] Defer
2. Utility Base Extraction: [✅] Yes | [ ] No

**Architectural:** ✅
3. Effect Application: [✅] Immediate | [ ] Batch
4. Multi-tick State: [✅] Effect-based | [ ] Protocol-managed
5. Versioning: [ ] Semantic | [✅] Date | [ ] Integer

**Priority:** ✅
6. First Protocols: [ ] Bargaining | [ ] Search | [ ] Phase C | [✅] Deferred (N/A for minimal)
7. Performance Target: [ ] <5% | [✅] <10% | [ ] <20%

**Resource:** ✅
8. Development: [ ] Dedicated | [✅] Part-time | [ ] Team
9. Testing: [ ] Minimum | [✅] Recommended | [ ] Comprehensive

**Optional:** ✅
10. Utility Phase 2: [ ] After | [✅] New Dev | [ ] Defer
11. Onboarding: [ ] During | [✅] After | [ ] Separate
12. GUI: [ ] Dropdown | [ ] Dialog | [✅] Config

---

## BLOCKERS ✅ RESOLVED

**All blockers resolved:**
1. ✅ Overall implementation approach: Minimal Implementation
2. ✅ Effect application strategy: Immediate Application
3. ✅ Multi-tick state storage: Effect-based State

**All decisions made:**
4. ✅ Protocol versioning: Date-based (YYYY.MM.DD)
5. ✅ First alternative protocols: Deferred (N/A for minimal)
6. ✅ Performance targets: <10% regression

**Status:** Ready to proceed with implementation

---

## FINAL DECISIONS SUMMARY ✅

Based on the analysis and user input, these decisions were made:

1. **Minimal Implementation** ✅ - Lower risk, faster delivery, extensible foundation
2. **Yes to Utility Base** ✅ - Quick win, 2-hour task
3. **Immediate Application** ✅ - Simpler implementation and debugging
4. **Effect-based State** ✅ - Better audit trail, determinism
5. **Date-based Versioning** ✅ - Aligns with VMT standards, simpler for research
6. **<10% Performance Target** ✅ - Standard for VMT refactoring
7. **Part-time Development** ✅ - Appropriate for 4-week minimal implementation
8. **Recommended Testing Level** ✅ - Includes golden standard tests
9. **Utility Phase 2 to New Dev** ✅ - Good onboarding exercise
10. **Onboarding Updates After** ✅ - After protocols stable
11. **Config-only GUI** ✅ - Minimal implementation, GUI deferred
12. **Alternative Protocols Deferred** ✅ - Not in minimal implementation scope

---

## NEXT STEPS ✅

All decisions have been made. Implementation in progress:

1. ✅ Review complete - All decisions documented
2. ✅ Decision Summary Form filled out
3. ✅ No additional concerns identified
4. ✅ **COMPLETE:** Utility base extraction
5. 🚀 **NEXT:** Protocol Phase 0 (infrastructure setup)

**Implementation Timeline:**

- **Week 0:** Utility base extraction (2 hours) ✅ **COMPLETE (2025-10-26)**
- **Week 1:** Protocol Phase 0 - Infrastructure setup 🚀 **READY TO START**
- **Week 2:** Protocol Phase 1 - Legacy adapters
- **Week 3:** Protocol Phase 2 - Core integration + configuration
- **Week 4:** Testing, documentation, verification

---

**Document Status:** ✅ Utility extraction complete - protocol work ready to begin  
**Completed:** Utility base extraction (base.py created, 86/86 tests passing)  
**Action Required:** Begin protocol Phase 0 (infrastructure setup)  
**Timeline:** 4 weeks to extensible protocol foundation  
**Next Session:** Protocol implementation Phase 0
