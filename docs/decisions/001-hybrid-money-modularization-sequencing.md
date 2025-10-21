# ADR-001: Hybrid Money+Modularization Sequencing

**Status**: Accepted  
**Date**: 2025-10-21  
**Decider**: Project Lead  
**Context**: Strategic planning for VMT development priorities

---

## Context

After completing Money System Phases 1-2 (quasilinear utility, bilateral monetary exchange), the project faced a strategic decision about next steps. Three major development tracks were available:

1. **Money Track 1 (Core)**: Complete quasilinear money system (Phases 3-4, ~20-25 hours)
2. **Money Track 2 (Advanced)**: Add KKT λ estimation and liquidity gating (Phases 5-6, ~25-30 hours)
3. **Protocol Modularization**: Refactor Decision phase for extensibility (~160-200 hours, 6-9 weeks)

The tension: Should we complete the money system before architectural refactoring, or refactor first to build money features on top of modular architecture?

## Decision

**We will follow a hybrid sequencing approach:**

```
Phase 1: Complete Money Track 1 (Phases 3-4)
  → Money Phase 3: Mixed regimes (12-15 hrs)
  → Scenario Generator Phase 2 (2-3 hrs)
  → Money Phase 4: Polish & documentation (8-10 hrs)
  → Release v1.0 (Production-ready quasilinear money system)

Phase 2: Protocol Modularization (6-9 weeks)
  → Refactor Decision phase for extensibility
  → Enable swappable Search and Matching protocols
  → Validate on stable money system

Phase 3: Advanced Money Features (Track 2)
  → Money Phase 6: KKT λ estimation (on modular architecture)
  → Money Phase 5: Liquidity gating
  → OR: Other features based on user feedback
```

**Key Decision Points:**
1. Complete Track 1 first (low risk, high value)
2. Thoroughly test with users
3. Tackle modularization next (informed by real usage)
4. Add advanced features on modular foundation (if needed)

## Consequences

### Positive

1. **Lower Risk**: Complete proven money features before major refactoring
2. **User Value**: Educators get production-ready system in ~20-25 hours
3. **Informed Design**: Real usage patterns guide protocol interface design
4. **Natural Gates**: Can release v1.0 and gather feedback before committing to modularization
5. **Stable Foundation**: Refactor from working system, not incomplete features

### Negative

1. **Delayed Extensibility**: Modularization delayed by 3-4 weeks
2. **Potential Rework**: Some Track 1 code may need adjustment during modularization
3. **Opportunity Cost**: Alternative matching algorithms not available immediately

### Neutral

1. **Track 2 Flexibility**: Can defer KKT/liquidity gating until after modularization (or skip entirely based on feedback)
2. **Timeline**: Total time roughly equivalent to alternative sequencing, just reordered

## Alternatives Considered

### Alternative A: Money First (All 6 Phases)

Complete entire money system (Phases 3-6) before any modularization.

**Pros:**
- Feature complete money system
- No interruption in money development

**Cons:**
- KKT/liquidity gating are complex (medium risk)
- Delays modularization by 2-3 months
- Advanced features may not be needed based on user feedback

**Rejected Because:** Track 2 features are research-grade and may not be needed. Better to validate with users first.

### Alternative B: Modularization First

Pause money development after Phase 2, implement full modularization, then continue money on modular architecture.

**Pros:**
- All future features built on extensible foundation
- Community contributions possible sooner

**Cons:**
- High risk (major refactoring on incomplete system)
- Delays production-ready system by 2-3 months
- No user validation of money system before refactoring

**Rejected Because:** Too much architectural risk without user validation. Better to ship working system first.

### Alternative C: Parallel Development

Implement Track 1 and modularization simultaneously.

**Pros:**
- Fastest total timeline

**Cons:**
- Extremely high risk (two major changes at once)
- Testing complexity (which change caused bugs?)
- Merge conflicts likely

**Rejected Because:** Compounds risk unacceptably. Violates principle of incremental progress.

## Related Decisions

- Money system two-track approach (documented in `docs/BIG/money_implementation_strategy.md`)
- Protocol modularization proposal (documented in `docs/proposals/protocol_modularization_discussion.md`)

## References

- [Comprehensive Documentation Audit](../audit/2025-10-21_comprehensive_documentation_audit.md) - Section 5.1
- [Money Implementation Strategy](../BIG/money_implementation_strategy.md) - Two-track approach
- [Money SSOT Implementation Plan](../BIG/money_SSOT_implementation_plan.md) - Phase specifications
- [Protocol Modularization Implementation Plan](../proposals/protocol_modularization_plan.md) - Refactoring details

---

**Next Review**: After Money Phase 4 completion (v1.0 release), reassess modularization priority based on user feedback.

