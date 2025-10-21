# Cursor Rules Creation Summary

**Date**: 2025-10-21  
**Purpose**: Keep AI agents aligned with strategic decision (ADR-001)  
**Related**: [Documentation Cleanup](2025-10-21_documentation_cleanup_summary.md)

---

## Rules Created (3)

All rules set to `alwaysApply: true` to ensure consistent guidance across all AI interactions.

### 1. Strategic Priority Rule

**File**: `.cursor/rules/strategic-priority.mdc`  
**Purpose**: Enforce hybrid sequencing decision from ADR-001

**Key Content**:
- Current implementation sequence (Money Track 1 → Modularization → Track 2)
- Clear "DO NOW" vs "DEFER" sections
- When-to-suggest decision logic for AI agents
- Success criteria for each phase
- Quick reference to all relevant documentation

**Impact**: AI agents will:
- ✅ Suggest Money Phase 3 work (approved)
- ⚠️ Check prerequisites before suggesting Scenario Gen Phase 2
- 🛑 Stop and remind user when protocol modularization is suggested
- 🛑 Stop and explain deferral for Money Track 2 features

### 2. Documentation Navigation Rule

**File**: `.cursor/rules/documentation-navigation.mdc`  
**Purpose**: Guide AI agents to use reorganized documentation structure

**Key Content**:
- Complete directory structure with status indicators
- Common lookup patterns ("What should I implement next?", "How does X work?")
- Phase numbering reconciliation (all three systems)
- Document update policy
- Quick Reference Guide as starting point

**Impact**: AI agents will:
- ✅ Reference Quick Reference Guide first
- ✅ Use correct documentation paths (no more docs/tmp/)
- ✅ Specify which "Phase" system when referencing phases
- ✅ Link to specific sections with context

### 3. Phase Numbering Clarity Rule

**File**: `.cursor/rules/phase-numbering-clarity.mdc`  
**Purpose**: Eliminate confusion from three different phase numbering schemes

**Key Content**:
- All three phase systems explicitly listed:
  - Strategic Roadmap: Phases A-F
  - Money System: Money Phases 1-6
  - Scenario Generator: Scenario Generator Phases 1-3
  - Modularization: Modularization Phases 1-4 (proposed)
- Required prefixes table
- Common confusions with correct alternatives
- Current status of all active phases
- Writing guidelines for commits, PRs, issues

**Impact**: AI agents will:
- ✅ Always prefix phase numbers with system context
- ✅ Correct ambiguous "Phase X" references
- ✅ Use descriptive names ("mixed regimes") alongside numbers
- ✅ Write clear commit messages and PR descriptions

---

## Rule Integration

All three rules work together:

```
┌─────────────────────────────────────────────┐
│  Strategic Priority Rule                    │
│  "What should I work on?"                   │
│  → Money Phase 3 is current priority        │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│  Documentation Navigation Rule              │
│  "Where do I find information about X?"     │
│  → Use Quick Reference Guide first          │
│  → Link to money_phase3_checklist.md       │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│  Phase Numbering Clarity Rule               │
│  "How do I refer to phases clearly?"        │
│  → Use 'Money Phase 3' not 'Phase 3'       │
│  → Include descriptive name                 │
└─────────────────────────────────────────────┘
```

**Result**: AI agents have clear, unambiguous guidance at every step.

---

## Testing the Rules

### Scenario 1: AI suggests work

**User asks**: "What should I implement next?"

**AI response** (guided by strategic-priority.mdc):
```
Per ADR-001, the current priority is Money Phase 3 (mixed regimes).

See the detailed checklist at docs/BIG/money_phase3_checklist.md

Key tasks:
1. Enable exchange_regime = "mixed" in matching algorithm
2. Implement money-first tie-breaking
3. Test mode × regime interaction
...
```

### Scenario 2: AI suggests deferred work

**User asks**: "Should we start on protocol modularization?"

**AI response** (guided by strategic-priority.mdc):
```
🛑 Protocol modularization is deferred per ADR-001.

Rationale: We need a stable money system to refactor from.
The plan is to complete Money Track 1 first (Phases 3-4),
release v1.0, gather user feedback, THEN tackle modularization.

The modularization proposal is documented at:
docs/proposals/protocol_modularization_plan.md

Current priority: Money Phase 3 (mixed regimes)
Timeline: Start modularization after v1.0 release (3-4 weeks)
```

### Scenario 3: AI references phases ambiguously

**AI initially says**: "We should complete Phase 3 first"

**Self-correction** (guided by phase-numbering-clarity.mdc):
```
Let me clarify: We should complete Money Phase 3 (mixed regimes)
first, as it's the current priority per ADR-001.

This is distinct from:
- Strategic Phase C (markets) - future
- Scenario Generator Phase 3 - future
- Modularization Phase 3 - deferred
```

---

## Benefits

### Before Rules:
- ❌ AI agents might suggest modularization (deferred work)
- ❌ Ambiguous "Phase 3" references cause confusion
- ❌ AI agents might not know where to find documentation
- ❌ Suggestions might not align with strategic decision

### After Rules:
- ✅ AI agents consistently prioritize Money Phase 3
- ✅ All phase references include system context
- ✅ AI agents use Quick Reference Guide and new structure
- ✅ Suggestions always align with ADR-001

---

## Maintenance

### When to Update Rules

**Strategic Priority Rule** - Update when:
- Money Phase 3 completes → Update "YOU ARE HERE" marker
- Track 1 completes → Update to reflect modularization as current
- Strategic decisions change → Create new ADR and update rule

**Documentation Navigation Rule** - Update when:
- Documentation structure changes
- New major documents added
- Directory organization changes

**Phase Numbering Clarity Rule** - Update when:
- New phase numbering system introduced
- Phase completion status changes significantly
- New phases added to existing systems

### Update Process

1. Create new ADR if strategic decision changes
2. Update relevant rule(s)
3. Update Quick Reference Guide
4. Test with sample queries
5. Document update in audit/

---

## Integration with Existing Rules

The three new rules complement existing rules in `.cursor/rules/`:

**Existing rules** (from inspection):
- Core principles (7-phase tick cycle, determinism)
- Economic logic (utility functions, matching)
- Testing conventions
- GUI development
- Etc.

**New rules** (strategic/navigational):
- Strategic priority (what to work on)
- Documentation navigation (where to find info)
- Phase numbering (how to refer clearly)

**No conflicts**: New rules operate at strategic/organizational level, existing rules at implementation level.

---

## Quick Reference for Maintainers

**Rule Locations**:
- `.cursor/rules/strategic-priority.mdc`
- `.cursor/rules/documentation-navigation.mdc`
- `.cursor/rules/phase-numbering-clarity.mdc`

**Related Documents**:
- [ADR-001](../decisions/001-hybrid-money-modularization-sequencing.md) - The strategic decision
- [Quick Reference Guide](../quick_reference.md) - Documentation lookup
- [Documentation Cleanup Summary](2025-10-21_documentation_cleanup_summary.md) - Context

**Testing**:
- Ask AI "What should I implement next?" → Should reference Money Phase 3
- Ask AI about "Phase 3" → Should clarify which system
- Ask AI "Where is the X documentation?" → Should use Quick Reference

---

## Success Metrics

**Measured by AI agent behavior**:

✅ **Alignment**: AI suggestions match ADR-001 priorities  
✅ **Clarity**: No ambiguous phase references  
✅ **Navigation**: Correct documentation references  
✅ **Consistency**: Same guidance across all AI interactions  

**Next validation**: After first week of use, assess if AI agents follow the rules consistently.

---

**Status**: ✅ Rules created and tested  
**Last Updated**: 2025-10-21  
**Next Review**: After Money Phase 4 completion (update priorities)

