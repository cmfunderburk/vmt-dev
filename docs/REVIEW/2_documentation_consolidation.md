# Documentation Consolidation & Restructuring Recommendations

**Date**: 2025-10-21  
**Current State**: 18 core documents + 4 directories of supplementary docs  
**Total Documentation**: ~25,000 words across 22+ files

---

## Executive Summary

Your documentation has grown **organically** as features evolved, which is natural for a solo project. However, this has created:
1. **Navigation friction** - Users must consult 3-4 documents to understand a single topic
2. **Information fragmentation** - Money system documented in 8 separate files
3. **Maintenance burden** - Updates require changes across multiple locations
4. **Phase numbering confusion** - Three different "Phase 3" meanings (money, scenario gen, roadmap)

**Good news:** Your recent consolidation efforts (Oct 20-21) are moving in the right direction. The quick reference guide and ADR system are excellent additions. This review provides the **next level** of consolidation.

---

## Current Documentation Landscape

### Core Documents (4)
✅ **Well-structured, authoritative:**
- `1_project_overview.md` (395 lines) - User guide
- `2_technical_manual.md` (252 lines) - Developer reference  
- `3_strategic_roadmap.md` (153 lines) - Long-term vision
- `4_typing_overview.md` (595 lines) - Type specifications

### Money System (8 files, 2000+ lines)
🟡 **Fragmented across directories:**
- `BIG/money_SSOT_implementation_plan.md` (475 lines) - Implementation spec
- `BIG/money_implementation_strategy.md` (263 lines) - Two-track approach
- `BIG/money_phase3_checklist.md` (checklist)
- `BIG/money_phase4_checklist.md` (checklist)
- `BIG/money_phase5_checklist.md` (checklist)
- `BIG/money_phase6_checklist.md` (checklist)
- `BIG/PHASE1_COMPLETION_SUMMARY.md` (historical)
- `BIG/PHASE2_PR_DESCRIPTION.md` (historical)

### Implementation Plans (3 files)
🟡 **Mixed active/historical:**
- `implementation/scenario_generator_phase2_plan.md` (COMPLETE)
- `implementation/scenario_generator_status.md` (UPDATE NEEDED)
- Plus: 5 archived phase 1 files in `archive/`

### Proposals (3 files)
✅ **Clear status:**
- `proposals/protocol_modularization_plan.md` (DEFERRED)
- `proposals/protocol_modularization_discussion.md` (context)
- `proposals/protocol_modularization_v2_resolution.md` (decision)

### Meta-Documentation (4 files)
✅ **Recently added, very helpful:**
- `quick_reference.md` (252 lines) - Lookup table
- `decisions/001-hybrid-money-modularization-sequencing.md` (ADR)
- `README.md` (hub)
- `_audit/2025-10-21_comprehensive_documentation_audit.md`

---

## Problem 1: Money System Fragmentation

### Current Structure (8 files)
```
BIG/
├── money_SSOT_implementation_plan.md    ← "SSOT" but 475 lines, dense
├── money_implementation_strategy.md     ← Overlaps with SSOT
├── money_phase[3-6]_checklist.md       ← 4 separate checklists
├── PHASE1_COMPLETION_SUMMARY.md        ← Historical
└── PHASE2_PR_DESCRIPTION.md            ← Historical
```

**Problem:** To understand "What is Money Phase 4?", I need to read:
1. `money_SSOT_implementation_plan.md` (overview)
2. `money_implementation_strategy.md` (two-track context)
3. `money_phase4_checklist.md` (details)
4. `quick_reference.md` (phase number reconciliation)

That's **4 files** for one question.

### Recommendation: Three-Tier Structure

#### Tier 1: User-Facing Guide (1 file)
**Create: `docs/user_guide_money_system.md`** (replace `BIG/` with single doc)

```markdown
# VMT Money System: Complete Guide

## Part 1: For Educators & Users
- What is the money system?
- How to use exchange regimes (barter/money/mixed)
- Scenario examples
- Teaching applications

## Part 2: For Developers
- Implementation overview
- Data structures (Inventory.M, quotes dict, etc.)
- Money-aware utility API
- Testing strategy

## Part 3: Implementation Status
- ✅ Phase 1: Infrastructure (complete)
- ✅ Phase 2: Monetary exchange (complete)
- 📋 Phase 3: Mixed regimes (current)
- 📋 Phase 4: Polish & docs (next)
- ⏳ Phases 5-6: Advanced (deferred per ADR-001)

## Part 4: Detailed Specifications
- Exchange regime control flow
- Money-first tie-breaking algorithm
- Telemetry schema extensions
- Validation logic

## Appendices
- A: Phase completion summaries (historical)
- B: Two-track strategy rationale
- C: KKT λ estimation (Phase 6 preview)
```

**Benefits:**
- One canonical file (400-500 lines)
- Self-contained (no cross-references needed)
- Versioned (current implementation state clear)
- Maintainable (updates in one place)

#### Tier 2: Active Work Tracker (1 file)
**Consolidate to: `docs/implementation/money_system_tracker.md`**

```markdown
# Money System Implementation Tracker

## Current Sprint: Money Phase 3 (Mixed Regimes)
**Start**: 2025-10-20  
**Estimated Completion**: 2025-10-23  
**Status**: 70% complete

### Completed Tasks
- [x] Implement exchange_regime="mixed" logic
- [x] Add money-first tie-breaking
- [x] Test mode × regime interaction

### In Progress
- [ ] Render mode/regime overlay
- [ ] Log viewer money tab

### Blocked/Deferred
- ⏸️ Phase 5-6 (per ADR-001)

## Upcoming: Money Phase 4 (Polish)
**Dependencies**: Phase 3 complete  
**Estimated Effort**: 8-10 hours

[... brief checklist ...]
```

**Benefits:**
- Live status dashboard
- Single place to update progress
- Historical record built-in (via git commits)

#### Tier 3: Historical Archive (move completed)
**Move to: `docs/archive/money/`**
- `PHASE1_COMPLETION_SUMMARY.md` → archive
- `PHASE2_PR_DESCRIPTION.md` → archive

Keep available but clearly marked as historical.

### Migration Path

**Week 1:** Create `user_guide_money_system.md`
1. Copy all user-facing content from BIG/*.md
2. Copy all developer content from `2_technical_manual.md` money sections
3. Add implementation status from `money_SSOT_implementation_plan.md`
4. Link from `1_project_overview.md`

**Week 2:** Create `money_system_tracker.md`  
1. Consolidate phase 3-6 checklists into single tracker
2. Mark completed items (phases 1-2)
3. Update as work progresses

**Week 3:** Archive historical docs
1. Move phase 1-2 summaries to archive/
2. Add deprecation notices to BIG/*.md files
3. Update all links

**Result:** 8 files → 3 files (1 guide, 1 tracker, 1 archive dir)

---

## Problem 2: Scenario Generator Documentation Staleness

### Current State
```
implementation/
├── scenario_generator_phase2_plan.md   ← OUTDATED (Phase 2 complete!)
├── scenario_generator_status.md        ← Says "Phase 1 complete", but Phase 2 is done
archive/
└── scenario_generator_phase1_*.md      ← 5 files, correctly archived
```

**Evidence from git log:**
```
227a388 Mark Scenario Generator Phase 2 as complete
0e5d26c Add Scenario Generator Phase 2 completion summary
```

**But `scenario_generator_status.md` still says:**
```markdown
## Current Status: Phase 1 Complete ✅
[Last updated: 2025-10-21]
```

### Recommendation: Single Living Document

**Consolidate to: `docs/implementation/scenario_generator.md`**

```markdown
# Scenario Generator Tool

## Overview
CLI tool for generating valid YAML scenarios in <0.1s.

## Current Status: Phase 2 Complete ✅
- ✅ Phase 1: CLI MVP (2025-10-20)
- ✅ Phase 2: Exchange regimes + presets (2025-10-21)
- 🔮 Phase 3: Advanced features (future, based on feedback)

## Usage
[... current usage examples ...]

## Phase 2 Features (NEW)
- Exchange regime selection (--exchange-regime)
- Scenario presets (--preset money_demo)
- Automatic money inventory generation

## Development Notes
[... brief implementation notes ...]

## Historical: Phase 1-2 Completion
[... brief summaries with links to archive/ ...]
```

**Benefits:**
- Always current (one place to update)
- Historical context preserved but de-emphasized
- Clear roadmap (Phase 3 TBD)

### Migration Path

**Immediate** (5 minutes):
1. Update `scenario_generator_status.md` to reflect Phase 2 completion
2. Move Phase 2 completion summary to archive/
3. Delete `scenario_generator_phase2_plan.md` (obsolete, or move to archive)

---

## Problem 3: Technical Manual is Becoming a Monolith

### Current State
`2_technical_manual.md`: 252 lines covering:
- Core architecture (7-phase cycle)
- Key systems (pairing, resource claiming, money)
- Testing strategy
- Telemetry

**Growing to cover:**
- Money system (40+ lines currently)
- Markets (future)
- Production (future)
- Game theory (future)

**At 1000+ lines, this becomes unwieldy.**

### Recommendation: Modular Technical Reference

**Split into:**

#### 1. `docs/2_technical_manual.md` (CORE ONLY)
```markdown
# VMT Technical Manual: Core Architecture

## 7-Phase Tick Cycle (authoritative)
## Determinism & Reproducibility
## Agent Architecture
## Grid & Spatial Indexing
## Testing Philosophy
```
**Target size:** 150-200 lines, stable

#### 2. `docs/tech/money_system.md`
```markdown
# Money System Technical Reference
[Detailed money implementation]
```

#### 3. `docs/tech/markets.md` (future)
```markdown
# Market System Technical Reference
[When implemented]
```

#### 4. `docs/tech/telemetry.md`
```markdown
# Telemetry & Logging Technical Reference
[SQLite schema, logging strategy]
```

**Cross-reference structure:**
```markdown
# 2_technical_manual.md

## Money System (overview)
For complete specification, see [Money System Technical Reference](tech/money_system.md).
```

### Benefits
1. **Core manual stays stable** - Few changes after v1.0
2. **Subsystems documented in depth** - Experts can read just their domain
3. **Easier navigation** - "I want to learn about money" → read one focused doc
4. **Parallel authorship** - Different people can document different subsystems

### Migration Path

**After v1.0:**
1. Extract money content from technical manual → `tech/money_system.md`
2. Leave brief (3-4 paragraph) overview in core manual with link
3. Future subsystems get their own `tech/*.md` files

---

## Problem 4: Phase Numbering Confusion

### Current Issue (from `.cursor/rules/phase-numbering.mdc`)

Three different "Phase" systems:
1. **Strategic Roadmap Phases A-F** (curriculum progression)
2. **Money Phases 1-6** (implementation sequence)
3. **Scenario Generator Phases 1-3** (tool development)

**Example confusion:**
- "Phase 3" could mean:
  - Money Phase 3 (mixed regimes)
  - Scenario Generator Phase 3 (advanced features)
  - Strategic Phase C (local markets)

### Current Mitigation (Good!)
- `.cursor/rules/phase-numbering.mdc` explains the issue
- `quick_reference.md` has reconciliation table
- Docs now use prefixes ("Money Phase 3")

### Recommendation: Retire Numeric Phases

**Replace with descriptive milestones:**

| Old | New |
|-----|-----|
| Money Phase 1 | Money: Infrastructure Milestone |
| Money Phase 2 | Money: Bilateral Exchange Milestone |
| Money Phase 3 | Money: Mixed Regimes Milestone |
| Strategic Phase A | Curriculum: Barter Economy Module |
| Strategic Phase B | Curriculum: Introduction of Money Module |
| Strategic Phase C | Curriculum: Markets Module |
| Scenario Gen Phase 1 | Tool: CLI MVP |
| Scenario Gen Phase 2 | Tool: Exchange Regimes |

**Example documentation:**
```markdown
# Money System Roadmap

## ✅ Completed Milestones
- Infrastructure (Oct 19) - Core data structures, telemetry
- Bilateral Exchange (Oct 20) - Money-only and barter regimes

## 📋 Current Milestone: Mixed Regimes
- Goal: Enable all three exchange pair types
- Status: 70% complete
- Target: Oct 23

## 🔮 Future Milestones
- Polish & Documentation (after Mixed Regimes)
- Advanced Features (deferred per ADR-001)
  - KKT Lambda Estimation
  - Liquidity Gating
```

### Benefits
1. **Self-documenting** - "Mixed Regimes Milestone" is clearer than "Phase 3"
2. **No numbering conflicts** - Can't confuse money milestones with scenario gen milestones
3. **Flexible ordering** - Can swap milestone order without renumbering everything
4. **Better git history** - `git log --grep="Mixed Regimes"` more intuitive than `--grep="Phase 3"`

### Migration Path

**Gradual transition:**
1. **Now:** Keep using current phase numbers, but always prefix (you're already doing this)
2. **v1.0 docs refresh:** Switch to milestone terminology
3. **v1.1+:** Fully retire phase numbers

**File renames** (optional):
- `money_phase3_checklist.md` → `money_mixed_regimes_checklist.md`
- `scenario_generator_phase2_plan.md` → `scenario_generator_regimes_plan.md`

---

## Problem 5: Too Many Top-Level Directories

### Current Structure
```
docs/
├── Core files (4 files)
├── BIG/ (money - 8 files)
├── implementation/ (active plans - 2 files)
├── proposals/ (deferred - 3 files)
├── decisions/ (ADRs - 1 file)
├── archive/ (completed - 5+ files)
├── _audit/ (audits - 1 file)
└── tech/ (doesn't exist yet but recommended)
```

**7 subdirectories is a lot for 20 documents.**

### Recommendation: Two-Tier Structure

```
docs/
├── README.md                          # Hub
├── quick_reference.md                 # Lookup table
│
├── Core Documentation (4 files at root)
│   ├── 1_project_overview.md
│   ├── 2_technical_manual.md
│   ├── 3_strategic_roadmap.md
│   └── 4_typing_overview.md
│
├── guides/                            # User & developer guides
│   ├── money_system.md                # Consolidated from BIG/
│   ├── scenario_generator.md          # Consolidated from implementation/
│   └── regime_comparison.md           # Teaching guide
│
├── implementation/                    # Active work only
│   ├── money_tracker.md               # Live status
│   └── protocol_modularization.md     # When active (currently in proposals/)
│
├── decisions/                         # ADRs
│   ├── README.md
│   └── 001-hybrid-sequencing.md
│
└── archive/                           # Historical
    ├── money/
    │   ├── phase1_summary.md
    │   └── phase2_summary.md
    ├── scenario_generator/
    │   └── phase1_*
    └── audits/
        └── 2025-10-21_audit.md
```

**Key changes:**
1. **BIG/** → merge into `guides/money_system.md` + `implementation/money_tracker.md`
2. **proposals/** → move active to `implementation/`, historical to `archive/`
3. **tech/** → create for modular technical references
4. **_audit/** → move to `archive/audits/`

### Benefits
1. **Clearer hierarchy** - "Is this active work or historical reference?"
2. **Fewer top-level dirs** - 5 instead of 7
3. **Semantic grouping** - All guides in one place, all active work in one place

---

## Consolidated Documentation Structure Proposal

### Final Recommended Structure

```
docs/
├── README.md                          # Documentation hub (unchanged)
├── quick_reference.md                 # Fast lookup (unchanged)
│
├── Core Documentation
│   ├── 1_project_overview.md          # User guide
│   ├── 2_technical_manual.md          # Core architecture only (trimmed)
│   ├── 3_strategic_roadmap.md         # Long-term vision
│   └── 4_typing_overview.md           # Type specifications
│
├── guides/                            # Comprehensive user & developer guides
│   ├── money_system.md                # 🆕 Replaces 8 BIG/ files
│   ├── scenario_generator.md          # 🆕 Replaces implementation/*.md
│   ├── testing_guide.md               # 🆕 Extract from technical manual
│   └── regime_comparison.md           # Teaching guide (existing)
│
├── tech/                              # 🆕 Modular technical references
│   ├── money_implementation.md        # Detailed money specs
│   ├── telemetry_schema.md            # Database & logging
│   └── (future: markets.md, production.md)
│
├── implementation/                    # Active work trackers only
│   └── money_tracker.md               # 🆕 Live status dashboard
│
├── decisions/                         # Architecture Decision Records
│   ├── README.md
│   └── 001-hybrid-sequencing.md
│
└── archive/                           # Historical documents
    ├── money/
    │   ├── phase1_completion.md
    │   └── phase2_completion.md
    ├── scenario_generator/
    │   └── phase1_*.md
    └── audits/
        └── 2025-10-21_comprehensive_audit.md
```

**File count:** 22 files → 18 files (22% reduction)  
**Clarity:** Significant improvement in navigation

---

## Documentation Workflow Improvements

### Current Workflow Issues
1. **No template for new features** - Each feature documented inconsistently
2. **No review process** - Docs can drift out of sync with code
3. **No deprecation policy** - Old docs linger indefinitely

### Recommended Workflow

#### 1. Feature Documentation Template

**When adding a new major feature:**

```markdown
# [Feature Name]: Complete Guide

## Part 1: User Guide
- What problem does this solve?
- How to use it (examples)
- Common patterns

## Part 2: Developer Reference  
- Architecture overview
- Key abstractions
- Testing strategy

## Part 3: Implementation Notes
- Design decisions
- Known limitations
- Future extensions

## Part 4: Status
- Implementation milestones
- Completion criteria
- Version introduced
```

**Location:**
- User-facing content → `docs/guides/[feature].md`
- Technical content → `docs/tech/[feature]_implementation.md`
- Active work → `docs/implementation/[feature]_tracker.md`

#### 2. Documentation Review Checklist

**Before merging feature branch:**
- [ ] User guide updated (`guides/`)
- [ ] Technical reference updated (`tech/`)
- [ ] Quick reference updated (links added)
- [ ] README badges updated (if applicable)
- [ ] Old docs deprecated/archived (if replacing)

#### 3. Deprecation Policy

**When documentation becomes outdated:**

1. **Add deprecation notice** (top of file):
```markdown
> **⚠️ DEPRECATED**: This document is outdated as of 2025-10-23.  
> See [New Location](link) for current information.
```

2. **Move to archive/** after 30 days

3. **Update all links** to point to new location

4. **Track in changelog** (see below)

#### 4. Documentation Changelog

**Create: `docs/CHANGELOG.md`**

```markdown
# Documentation Changelog

## 2025-10-21: Major Consolidation
- Created comprehensive review (REVIEW/ directory)
- Consolidated money system docs (8 files → 2 files)
- Updated scenario generator status
- Added ADR-001 for strategic sequencing

## 2025-10-20: Money Phase 2 Complete
- Added Phase 2 completion summary
- Updated technical manual with money-aware API
- Added money tab to log viewer docs
```

**Benefits:**
- Track documentation evolution
- Easy to see what changed when
- Useful for onboarding new contributors

---

## Automation Opportunities

### 1. Documentation Link Checker

**Problem:** Dead links accumulate as docs move/rename.

**Solution:** Add pre-commit hook:
```bash
#!/bin/bash
# .git/hooks/pre-commit
python scripts/check_doc_links.py
```

```python
# scripts/check_doc_links.py
"""Verify all markdown links are valid."""
import re
from pathlib import Path

def check_links():
    docs = Path("docs").rglob("*.md")
    for doc in docs:
        content = doc.read_text()
        links = re.findall(r'\[.*?\]\((.*?)\)', content)
        for link in links:
            if link.startswith("http"):
                continue  # Skip external
            target = (doc.parent / link).resolve()
            if not target.exists():
                print(f"❌ {doc}: Dead link to {link}")
                return 1
    print("✅ All links valid")
    return 0
```

### 2. Auto-Generate Quick Reference

**Problem:** Quick reference manually maintained, can drift.

**Solution:** Generate from directory structure:
```python
# scripts/generate_quick_ref.py
"""Auto-generate quick_reference.md from directory structure."""

def scan_docs():
    """Scan docs/ and extract metadata from frontmatter."""
    entries = []
    for doc in Path("docs").rglob("*.md"):
        # Parse YAML frontmatter
        # Extract: title, purpose, audience, status
        entries.append(...)
    return entries

def generate_lookup_table(entries):
    """Generate 'I want to...' table."""
    # Group by purpose
    # Output markdown table
```

### 3. Documentation Coverage Report

**Problem:** Hard to know if feature is fully documented.

**Solution:** Coverage report generator:
```python
# scripts/doc_coverage.py
"""Report documentation coverage for each system."""

def find_systems():
    """Find all systems in src/vmt_engine/systems/."""
    return [f.stem for f in Path("src/vmt_engine/systems").glob("*.py")]

def check_coverage(system):
    """Check if system has corresponding docs."""
    has_user_guide = (Path("docs/guides") / f"{system}.md").exists()
    has_tech_ref = (Path("docs/tech") / f"{system}.md").exists()
    has_tests = (Path("tests") / f"test_{system}.py").exists()
    return {
        "user_guide": has_user_guide,
        "tech_ref": has_tech_ref,
        "tests": has_tests
    }

def report():
    systems = find_systems()
    for sys in systems:
        cov = check_coverage(sys)
        status = "✅" if all(cov.values()) else "⚠️"
        print(f"{status} {sys}: {cov}")
```

**Output:**
```
✅ matching: {'user_guide': True, 'tech_ref': True, 'tests': True}
✅ trading: {'user_guide': True, 'tech_ref': True, 'tests': True}
⚠️ perception: {'user_guide': False, 'tech_ref': True, 'tests': True}
```

---

## Migration Timeline

### Phase 1: Immediate (This Week)
**Effort: 2-3 hours**

1. ✅ Update `scenario_generator_status.md` (Phase 2 complete)
2. ✅ Move phase 2 completion summary to archive
3. ✅ Add deprecation notices to obsolete docs
4. ✅ Fix any dead links in quick_reference.md

### Phase 2: Pre-v1.0 (Next Week)
**Effort: 4-5 hours**

1. Create `guides/money_system.md` (consolidate BIG/)
2. Create `implementation/money_tracker.md` (live status)
3. Move historical money docs to `archive/money/`
4. Update all cross-references

### Phase 3: Post-v1.0 (When Ready)
**Effort: 6-8 hours**

1. Split technical manual (core + tech/)
2. Reorganize directory structure (fewer top-level dirs)
3. Implement documentation workflow
4. Add automation scripts (link checker, coverage)

### Phase 4: Future (v1.1+)
**Effort: Ongoing**

1. Migrate to milestone terminology (retire phase numbers)
2. Create feature documentation templates
3. Establish documentation review process
4. Build documentation coverage into CI

---

## Recommended Documentation Principles

### 1. DRY (Don't Repeat Yourself)
❌ **Bad:** Copy-paste same explanation into 3 different docs  
✅ **Good:** Write once in canonical location, link from elsewhere

### 2. Single Source of Truth (SSOT)
❌ **Bad:** "Money system described in 8 places, all slightly different"  
✅ **Good:** One comprehensive guide, all links point to it

### 3. Progressive Disclosure
❌ **Bad:** 500-line technical manual as first introduction  
✅ **Good:** 
- Level 1: Quick start (50 lines)
- Level 2: User guide (200 lines)
- Level 3: Developer reference (400 lines)
- Level 4: Implementation specs (1000 lines)

### 4. Living Documents Over Historical Snapshots
❌ **Bad:** Create "Phase 3 Plan v1", "Phase 3 Plan v2", "Phase 3 Plan FINAL"  
✅ **Good:** One `money_mixed_regimes.md` that evolves via git history

### 5. Clear Status Indicators
❌ **Bad:** No way to tell if document is current or obsolete  
✅ **Good:** Every doc has status indicator:
- ✅ COMPLETE (stable, reference)
- 📋 ACTIVE (in progress, changing)
- ⏸️ DEFERRED (paused, may resume)
- 🔮 PLANNED (future work)
- ⚠️ DEPRECATED (obsolete, see link)

---

## Conclusion

Your documentation is **comprehensive and thorough**, which is rare for a solo project. The issues are purely **organizational**, not content quality.

**Key recommendations:**
1. **Consolidate money docs** (8 files → 2-3 files) - Highest impact
2. **Update scenario generator status** (reflects completion) - Quick win
3. **Adopt modular technical references** (prepare for future growth) - Long-term
4. **Consider milestone terminology** (retire confusing phase numbers) - Nice-to-have
5. **Implement documentation workflow** (prevents future drift) - Process improvement

**Estimated total effort:** 12-16 hours spread across 3 phases.

**Return on investment:** Significantly improved navigation, reduced maintenance burden, clearer communication with future users/contributors.

Your recent consolidation work (quick reference, ADRs) shows you understand these issues. This review provides the **next level** of structure to carry you through v1.0 and beyond.

