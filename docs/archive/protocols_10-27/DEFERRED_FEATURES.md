# Deferred Features for Phase 2a

## Per-Agent Protocol Assignments

**Status:** Explicitly deferred  
**Reason:** Global protocol settings are sufficient for validating architecture and observing protocol behavior  
**Decision Date:** 2025-10-28

### Current Approach
- Each simulation uses **one** search, matching, and bargaining protocol globally
- All agents use the same protocols within a simulation run
- Protocol comparison happens across **separate simulation runs**

### Rationale
1. **Architecture Validation First:** Phase 2a goal is to validate the protocol system works, not to compare protocols within a single run
2. **Simpler Implementation:** No schema changes, loader modifications, or per-agent protocol injection needed
3. **Sufficient for Research:** Comparing separate runs with different protocols achieves the same pedagogical/research goals
4. **Future Flexibility:** Can add per-agent assignments later when we have 10+ protocols and need within-simulation heterogeneity

### When to Revisit
- **After Phase 2-3 complete:** Once we have baseline, pedagogical, and centralized market protocols implemented
- **When research needs demand it:** If we need to study heterogeneous populations with mixed protocol usage
- **Phase 4 or later:** When implementing learning/adaptation protocols that benefit from within-population diversity

### Implementation Notes (Future)
When implemented, this would require:
1. Add `ProtocolAssignment` to `scenarios/schema.py`
2. Modify `ScenarioConfig` to include `protocol_assignments: Optional[list[ProtocolAssignment]]`
3. Update scenario loader to parse protocol assignments
4. Modify `Simulation.__init__()` to support per-agent protocol instances
5. Update `DecisionSystem` and `TradeSystem` to use agent-specific protocols
6. Wire `ProtocolRegistry` for dynamic protocol lookup by name/version

**Estimated effort when needed:** 4-6 hours

---

**For now:** Use global protocols, compare across runs. Focus on implementing the protocols themselves.

