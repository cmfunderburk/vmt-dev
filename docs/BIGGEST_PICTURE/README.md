# BIGGEST_PICTURE Documentation

**Purpose:** Strategic vision and high-level architecture documentation

---

## What This Directory Contains

This directory holds **strategic, enduring documentation** that captures:
- The fundamental vision and research questions
- Economic and pedagogical philosophy
- High-level architecture (conceptual, not implementation)
- Long-term research agenda

**These documents are:**
- ✅ Code-agnostic (concepts, not implementation)
- ✅ Stable (updated infrequently, only for major direction changes)
- ✅ Strategic (the "why" and "what", not the "how")
- ✅ Accessible (readable by non-programmers: economists, educators, collaborators)

**These documents are NOT:**
- ❌ Implementation guides (see `docs/protocols_10-27/` or `docs/ssot/`)
- ❌ Living/evolving plans (see `docs/ASDF/SESSION_STATE.md`)
- ❌ Code documentation (see source code docstrings)
- ❌ Technical manuals (see `docs/2_technical_manual.md`)

---

## Current Documents

### [`vision_and_architecture.md`](vision_and_architecture.md)

**The master strategic document** covering:

1. **The Fundamental Question**
   - Why standard economics pedagogy is limiting
   - VMT's alternative: markets as emergent phenomena

2. **Core Design Philosophy**
   - Markets don't just happen—they emerge from institutions
   - Institutional comparative analysis as research program
   - Spatial and temporal dynamics matter

3. **Economic Foundations**
   - Basic exchange economy structure
   - From utility to prices: the emergence question

4. **Protocol Categories**
   - Search, Matching, Bargaining, Market Mechanisms
   - Economic and pedagogical value of each

5. **Current State**
   - What exists and works
   - What's possible now
   - What's missing for full vision

6. **Research Agenda**
   - Protocol development phases (2a through 5)
   - Key research themes and questions
   - Phase 3 as critical milestone

7. **Pedagogical Applications**
   - Rethinking intermediate micro
   - Teaching markets as constructions

8. **Future Extensions**
   - Production economies
   - Public goods and externalities
   - Asymmetric information
   - Network formation

9. **Long-Term Vision**
   - 3-5 year roadmap
   - Ultimate goals

**Read this to understand:**
- What VMT is trying to accomplish and why
- The research questions driving development
- How protocols connect to economic theory
- Long-term vision and priorities

---

## When to Update These Documents

### Rarely (Major Changes Only)

Update `vision_and_architecture.md` when:
- ✓ Fundamental research questions change
- ✓ Major strategic pivots occur
- ✓ Long-term vision shifts significantly
- ✓ After major milestones (e.g., Phase 3 completion)

**Do NOT update for:**
- ✗ Implementation details
- ✗ Protocol completion (that's in ASDF or ssot)
- ✗ Bug fixes or refactoring
- ✗ Session-to-session progress

---

## Relationship to Other Documentation

### For Strategic Vision → Read BIGGEST_PICTURE
```
docs/BIGGEST_PICTURE/
  └── vision_and_architecture.md  ← "Why does VMT exist?"
```

### For Current Implementation State → Read ASDF
```
docs/ASDF/
  ├── SESSION_STATE.md             ← "Where are we right now?"
  └── PHASE_1_COMPLETION.md        ← "What was accomplished?"
```

### For Implementation Plans → Read ssot or protocols_10-27
```
docs/ssot/
  └── protocol_modularization_master_plan.md  ← "How is it architected?"

docs/protocols_10-27/
  ├── master_implementation_plan.md           ← "What are we building next?"
  ├── phase2a_quick_start.md                  ← "How do I start coding?"
  └── protocol_implementation_review.md       ← "Why each protocol?"
```

### For Technical Details → Read Technical Manual
```
docs/
  ├── 1_project_overview.md        ← "What is VMT?"
  ├── 2_technical_manual.md        ← "How does the code work?"
  └── 4_typing_overview.md         ← "What are the types?"
```

---

## Audience Guide

### For Potential Collaborators
**Read:** `vision_and_architecture.md`  
**Focus on:** Sections I-III (fundamental question, philosophy, economics)  
**Skip:** Implementation details

### For Economics Educators
**Read:** `vision_and_architecture.md`  
**Focus on:** Sections I-II, VIII (pedagogy), XIII-XIV (vision)  
**Supplementary:** `docs/protocols_10-27/protocol_implementation_review.md` (economic theory per protocol)

### For Researchers
**Read:** `vision_and_architecture.md`  
**Focus on:** Sections VII (research themes), IX (extensions)  
**Follow up with:** Protocol implementation review for theoretical grounding

### For Developers
**Start with:** `vision_and_architecture.md` Section X (conceptual architecture)  
**Then read:** `docs/protocols_10-27/master_implementation_plan.md`  
**Then read:** `docs/2_technical_manual.md`

---

## Document History

| Date | Document | Change | Reason |
|------|----------|--------|--------|
| 2025-10-27 | vision_and_architecture.md | Created | Consolidate strategic vision after Phase 1 completion |

---

**Directory Purpose:** Enduring strategic vision, not ephemeral implementation details  
**Update Frequency:** Rarely (major milestones only)  
**Audience:** Broad (economists, educators, researchers, collaborators)  
**Maintained By:** Project lead

