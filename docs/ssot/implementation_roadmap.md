# VMT Implementation Roadmap

**Document Status:** Active - Minimal Implementation Approved  
**Version:** 1.1  
**Created:** 2025-01-27  
**Updated:** 2025-10-26  
**Purpose:** Prioritized roadmap for VMT architectural initiatives

---

## DECISION SUMMARY ✅

**Implementation Approach:** Minimal Implementation (4 weeks)
- Infrastructure and legacy adapters only
- Extensible foundation for future protocols
- Lower risk, faster delivery
- No new protocols in initial phase  

---

## Current State Assessment

### Completed Work
- ✅ **P0 Money-Aware Pairing** (Completed 2025-10-22)
- ✅ **Core 7-Phase Engine** (Stable, 316+ tests passing)
- ✅ **5 Utility Functions** (CES, Linear, Quadratic, Translog, Stone-Geary)
- ✅ **Money System** (Quasilinear utility with λ parameters)
- ✅ **SQLite Telemetry** (Comprehensive logging system)
- ✅ **PyQt6 GUI** (Scenario browser and launcher)

### Technical Debt
- 🔴 **Monolithic DecisionSystem** (~600 lines, tightly coupled)
- 🟡 **Monolithic utility.py** (~744 lines, but functional)
- 🟡 **Limited extensibility** for new market mechanisms

### Strategic Goals
- Enable Phase C market mechanisms (posted-price, auctions)
- Support comparative institutional analysis
- Maintain pedagogical focus (performance at N=100 agents)
- Preserve determinism and reproducibility

---

## Priority Matrix

| Priority | Initiative | Effort | Risk | Blocks | Value |
|----------|-----------|--------|------|--------|-------|
| **P0 - Critical** | Protocol Modularization | 12 weeks | Low | Phase C | Enables all advanced features |
| **P1 - High** | Utility Base Extraction | 2 hours | Very Low | Nothing | Immediate code clarity |
| **P2 - Medium** | Full Utility Modularization | 2 days | Low | Nothing | Developer experience |
| **P3 - Low** | Developer Onboarding Updates | 1 week | Low | Nothing | New developer productivity |

---

## Implementation Sequence

### Stage 1: Immediate Actions (Week 1)

#### 1.1 Utility Base Extraction (2 hours)
**Why now:** Quick win, zero risk, improves code organization immediately

**Actions:**
1. Extract `Utility` ABC to `base.py`
2. Update imports
3. Run tests
4. Ship independently

**Decision Required:** None - proceed immediately

#### 1.2 Protocol Infrastructure Setup (3 days)
**Why now:** Foundation for all protocol work

**Actions:**
1. Create `src/vmt_engine/protocols/` structure
2. Define base classes and Effect types
3. Create WorldView/ProtocolContext
4. Add protocol fields to Simulation

**Decision Required:** 
- Effect application strategy (immediate vs batch)
- Protocol versioning scheme

### Stage 2: Core Protocol Implementation (Weeks 2-6)

#### 2.1 Legacy Adapters (2 weeks)
**Critical Path - Must Complete First**

**Actions:**
1. Implement LegacySearchProtocol
2. Implement LegacyMatchingProtocol (three-pass)
3. Implement LegacyBargainingProtocol (compensating blocks)
4. Wire into DecisionSystem
5. Verify telemetry equivalence

**Success Criteria:**
- Bit-identical telemetry
- All tests pass
- <10% performance regression

#### 2.2 Effect System Integration (1 week)
**Actions:**
1. Implement effect validation
2. Define application order
3. Add conflict resolution
4. Update telemetry

#### 2.3 First Alternative Protocols (2 weeks)
**Actions:**
1. GreedyMatching (simple, different outcomes)
2. TakeItOrLeaveIt bargaining
3. RandomWalk search
4. Create comparison scenarios

### Stage 3: Configuration & Testing (Weeks 7-8)

#### 3.1 Protocol Registry (3 days)
**Actions:**
1. Implement registry pattern
2. Update scenario schema
3. Add CLI overrides
4. GUI integration

#### 3.2 Comprehensive Testing (1 week)
**Actions:**
1. Golden standard tests
2. Property-based tests
3. Performance benchmarks
4. Economic validation

### Stage 4: Advanced Protocols (Weeks 9-10)

**Choose based on research priorities:**

**Option A: Bargaining Focus**
- Rubinstein alternating offers
- Nash bargaining solution
- Kalai-Smorodinsky solution

**Option B: Search/Matching Focus**
- Memory-based search
- Stable matching (Gale-Shapley)
- Frontier sampling

**Option C: Phase C Preparation**
- Posted-price market protocol
- Sealed-bid auction protocol
- Continuous double auction

### Stage 5: Cleanup & Documentation (Weeks 11-12)

**Actions:**
1. Remove legacy code from DecisionSystem
2. Performance optimization
3. Complete documentation
4. Developer guides
5. Migration guide

---

## Parallel Tracks

These can proceed independently of the main protocol work:

### Track A: Utility Modularization (After Stage 1.1)
**When:** After base extraction, during protocol Stages 2-3

**Full modularization (optional):**
1. Split utilities into separate files
2. Update imports and registry
3. Enhance documentation

**Can be assigned to:** New developer as onboarding exercise

### Track B: Developer Onboarding Updates
**When:** After Stage 3 (protocols stable)

**Actions:**
1. Update Module 2 (Architecture) with protocols
2. Add Module 7 (Protocol Development)
3. Create exercises for new protocols

---

## Decision Gates

### Gate 1: Start Protocol Implementation (Week 1) ✅ RESOLVED
**Required Decisions:**
1. ✅ Proceed with protocol modularization? **YES - Minimal Implementation**
2. ✅ Effect application strategy? **Immediate Application**
3. ✅ Protocol versioning scheme? **Date-based (YYYY.MM.DD)**
4. ✅ Multi-tick state approach? **Effect-based State (InternalStateUpdate)**

### Gate 2: Alternative Protocol Selection (Week 6)
**Required Decisions:**
1. Which protocols to implement first?
2. Research priorities (bargaining vs search)?
3. Performance vs feature trade-offs?

### Gate 3: Phase C Direction (Week 9)
**Required Decisions:**
1. Which Phase C mechanisms to prioritize?
2. Posted-price vs auction focus?
3. Integration with money system?

---

## Resource Requirements

### Developer Time
- **Lead Developer:** 12 weeks @ 50% = 6 FTE weeks
- **Testing:** 2 weeks @ 100% = 2 FTE weeks
- **Documentation:** 1 week @ 100% = 1 FTE week
- **Total:** ~9 FTE weeks

### Dependencies
- No external libraries required
- Python 3.11+ (already required)
- Existing test infrastructure sufficient

### Risks
- **Highest Risk:** Hidden coupling in DecisionSystem
- **Mitigation:** Legacy adapters preserve exact behavior
- **Fallback:** Can ship with legacy adapters only

---

## Success Metrics

### Technical Metrics
- [ ] All 316+ tests pass
- [ ] Telemetry backward compatible
- [ ] <10% performance regression
- [ ] >90% test coverage for protocols

### Functional Metrics
- [ ] 3+ search protocols
- [ ] 3+ matching protocols  
- [ ] 3+ bargaining protocols
- [ ] YAML configuration working
- [ ] GUI protocol selection

### Economic Metrics
- [ ] Can compare surplus across protocols
- [ ] Properties documented (efficiency, stability)
- [ ] Pedagogical scenarios created
- [ ] Research-grade telemetry

---

## Recommended Action Plan

### This Week (Week 1)
1. **Today:** Complete utility base extraction (2 hours)
2. **Tomorrow:** Review and finalize protocol design decisions
3. **Days 3-5:** Create protocol infrastructure

### Next Month (Weeks 2-5)
1. Focus exclusively on legacy adapters
2. Achieve telemetry equivalence
3. One alternative protocol as proof

### Following Month (Weeks 6-10)
1. Expand protocol library
2. Research-specific protocols
3. Phase C preparation

### Final Month (Weeks 11-12)
1. Optimization
2. Documentation
3. Knowledge transfer

---

## Active Path: Minimal Implementation ✅ APPROVED

**This is the approved implementation approach.**

### Minimal Protocol System (4 weeks)
1. **Week 1:** Infrastructure only
2. **Week 2:** Legacy adapters only
3. **Week 3:** Configuration system
4. **Week 4:** Documentation & Testing

**Result:** Extensible system, no new features yet

### Benefits ✅
- Unblocks future development
- Preserves all current behavior
- Lower risk and effort
- Can add protocols incrementally
- Faster time to completion (4 weeks vs 12 weeks)

### Trade-offs (Accepted)
- No immediate research value
- Doesn't demonstrate advantages initially
- New protocols can be added later as needed

---

## Conclusion

### Active Implementation Path ✅
1. **Immediate:** Utility base extraction (2 hours) ✅ APPROVED
2. **This Month:** Minimal protocol implementation (4 weeks) ✅ APPROVED
3. **Future:** Additional protocols can be added incrementally as research needs arise
4. **Parallel:** Developer onboarding updates after protocols stable

### Decision Made ✅
**Approved: 4-week minimal implementation**

This decision provides:
- ✅ Lower risk, faster delivery
- ✅ Extensible foundation for future work
- ✅ Preservation of all current behavior
- ✅ Ability to add protocols incrementally

---

**Document Status:** Implementation approach approved - ready to proceed  
**Next Action:** Begin utility base extraction, then protocol Phase 0  
**Timeline:** 4 weeks for minimal implementation
**Point of Contact:** Lead Developer
