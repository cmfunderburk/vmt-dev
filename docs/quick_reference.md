# VMT Documentation Quick Reference

**Purpose**: Find the right document quickly

**Last Updated**: 2025-10-21

---

## "I want to..."

### Getting Started

| Goal | Document | Location |
|------|----------|----------|
| Install and run VMT | [Project Overview](1_project_overview.md) | docs/ |
| Understand features | [Project Overview](1_project_overview.md#features) | docs/ |
| See quick start commands | [Project Overview](1_project_overview.md#quick-start) | docs/ |

### Understanding the System

| Goal | Document | Location |
|------|----------|----------|
| Understand the 7-phase tick cycle | [Technical Manual](2_technical_manual.md#the-7-phase-tick-cycle) | docs/ |
| Learn about trade pairing | [Technical Manual](2_technical_manual.md#trade-pairing-system) | docs/ |
| Understand money system (Phases 1-2) | [Technical Manual](2_technical_manual.md#money-system-phases-1-2) | docs/ |
| See complete type specifications | [Type System & Data Contracts](4_typing_overview.md) | docs/ |
| Understand telemetry schema | [Type System](4_typing_overview.md#part-2-configuration--telemetry) | docs/ |

### Implementing Features

| Goal | Document | Location |
|------|----------|----------|
| **See money system guide** (v1.0 complete) | [Money System Guide](guides/money_system.md) | docs/guides/ |
| **Check money implementation status** | [Money System Tracker](implementation/money_system_tracker.md) | docs/implementation/ |
| Check scenario generator status | [Scenario Generator Status](implementation/scenario_generator_status.md) | docs/implementation/ |

### Strategic Planning

| Goal | Document | Location |
|------|----------|----------|
| **View strategic decision** (hybrid sequencing) | [ADR-001](decisions/001-hybrid-money-modularization-sequencing.md) | docs/decisions/ |
| See long-term vision | [Strategic Roadmap](3_strategic_roadmap.md) | docs/ |
| Review comprehensive audit | [Documentation Audit](audit/2025-10-21_comprehensive_documentation_audit.md) | docs/_audit/ |
| Understand protocol modularization proposal | [Protocol Modularization Plan](proposals/protocol_modularization_plan.md) | docs/proposals/ |

### Historical Reference

| Goal | Document | Location |
|------|----------|----------|
| Money system history | [Money System Tracker](implementation/money_system_tracker.md#historical-reference) | Git history |
| Scenario Generator Phase 1 details | [Phase 1 Changelog](archive/scenario_generator_phase1_changelog.md) | docs/archive/ |
| Performance baseline (no logging) | [Performance Baseline Phase 1](performance_baseline_phase1_with_logging.md) | docs/ |

---

## By Document Type

### Core Documentation (Read First)

**For Users:**
1. [Project Overview](1_project_overview.md) - Features, installation, usage
2. [README](README.md) - Documentation hub

**For Developers:**
1. [Technical Manual](2_technical_manual.md) - Implementation details
2. [Type System](4_typing_overview.md) - Data contracts and telemetry

**For Contributors:**
1. [Strategic Roadmap](3_strategic_roadmap.md) - Long-term vision
2. [Quick Reference](quick_reference.md) - This document

### Implementation Status

**Money System:**
- ✅ Phases 1-4: COMPLETE (v1.0 quasilinear mode)
- 📖 **Complete Guide**: [Money System Guide](guides/money_system.md) ← **READ THIS**
- 📊 **Status Tracker**: [Money System Tracker](implementation/money_system_tracker.md)
- ⏸️ Phases 5-6: Deferred per [ADR-001](decisions/001-hybrid-money-modularization-sequencing.md)

**Scenario Generator:**
- ✅ Phase 1: [Archive](archive/) - Complete
- 📋 **Phase 2**: [Plan](implementation/scenario_generator_phase2_plan.md) ← **READY**
- 📊 [Status Document](implementation/scenario_generator_status.md)

**Protocol Modularization:**
- 💬 [Discussion](proposals/protocol_modularization_discussion.md)
- 📝 [Implementation Plan](proposals/protocol_modularization_plan.md)
- ⏸️ Status: Deferred until after Money Track 1

### Architecture Decisions

**ADR Index:**
- [ADR-001: Hybrid Money+Modularization Sequencing](decisions/001-hybrid-money-modularization-sequencing.md) - 2025-10-21

### Proposals & Planning

**Active Proposals:**
- [Protocol Modularization](proposals/) - Extensible protocol architecture

**Active Implementation Plans:**
- [Scenario Generator Phase 2](implementation/scenario_generator_phase2_plan.md)
- Money Phases 3-6 checklists in [BIG/](BIG/)

**Completed/Archived:**
- [Scenario Generator Phase 1](archive/)

---

## By Audience

### New Users

Start here:
1. [Project Overview](1_project_overview.md) - What VMT does
2. [Project Overview: Quick Start](1_project_overview.md#quick-start) - Run first simulation
3. [Project Overview: Creating Scenarios](1_project_overview.md#creating-custom-scenarios) - Make your own

### Educators

Relevant sections:
- [Project Overview: Academic Use](1_project_overview.md#academic-use--key-concepts)
- [Technical Manual: Money System](2_technical_manual.md#money-system-phases-1-2)
- Demo scenarios in `scenarios/` directory

### Researchers

Key documents:
- [Technical Manual](2_technical_manual.md) - Complete system description
- [Type System](4_typing_overview.md) - Formal specifications
- [Strategic Roadmap](3_strategic_roadmap.md) - Future features
- [Protocol Modularization Proposal](proposals/)

### Contributors

Read in order:
1. [Quick Reference](quick_reference.md) - This document
2. [Technical Manual](2_technical_manual.md) - Understand the system
3. [Strategic Roadmap](3_strategic_roadmap.md) - See where we're going
4. [ADR-001](decisions/001-hybrid-money-modularization-sequencing.md) - Current strategic direction
5. [Money SSOT Plan](BIG/money_SSOT_implementation_plan.md) - Next implementation steps

---

## By Phase Number (Reconciliation)

**⚠️ Important**: VMT uses multiple "Phase" numbering schemes:

### Money Phases (1-6)
Sequential implementation of money system features:
- **Phase 1**: Infrastructure (✅ Complete)
- **Phase 2**: Monetary exchange basics (✅ Complete)
- **Phase 3**: Mixed regimes (📋 Next)
- **Phase 4**: Polish and documentation (📋 After Phase 3)
- **Phase 5**: Liquidity gating (⏳ Track 2 - ADVANCED)
- **Phase 6**: KKT λ estimation (⏳ Track 2 - ADVANCED)

Documents: `docs/BIG/money_phase*.md`

### Scenario Generator Phases (1-3)
Tool development stages:
- **Phase 1**: CLI MVP (✅ Complete - in archive/)
- **Phase 2**: Exchange regimes + presets (📋 Ready)
- **Phase 3**: Advanced features (🔮 Future)

Documents: `docs/implementation/scenario_generator_*.md`

### Modularization Phases (1-4)
If implemented, protocol refactoring stages:
- **Phase 1**: Interfaces + wrappers (📝 Planned)
- **Phase 2**: Validation (📝 Planned)
- **Phase 3**: New protocols (📝 Planned)
- **Phase 4**: Configuration (📝 Planned)

Documents: `docs/proposals/protocol_modularization_*.md`

**To avoid confusion**: Always prefix with context (e.g., "Money Phase 3", "Scenario Generator Phase 2")

---

## Directory Structure

```
docs/
├── README.md                      # Documentation hub
├── quick_reference.md             # This file (lookup table)
│
├── 1_project_overview.md          # User-facing guide
├── 2_technical_manual.md          # Developer reference
├── 3_strategic_roadmap.md         # Long-term vision
├── 4_typing_overview.md           # Type specifications
├── PLAN_OF_RECORD.md              # Recent doc refresh status
│
├── decisions/                     # Architecture Decision Records
│   ├── README.md
│   └── 001-hybrid-money-modularization-sequencing.md
│
├── guides/                        # User & developer guides
│   └── money_system.md            ← Consolidated money guide (v1.0)
│
├── implementation/                # Active work trackers
│   ├── README.md
│   ├── money_system_tracker.md    ← Money v1.0 status
│   └── scenario_generator_status.md
│
├── proposals/                     # Under consideration
│   ├── README.md
│   ├── protocol_modularization_plan.md
│   ├── protocol_modularization_discussion.md
│   └── protocol_modularization_v2_resolution.md
│
├── archive/                       # Completed/historical
│   ├── README.md
│   ├── scenario_generator_phase1_*.md
│   └── (future completed plans)
│
└── _audit/                        # Audit reports
    └── 2025-10-21_comprehensive_documentation_audit.md
```

---

## Update History

- **2025-10-21**: Initial version after documentation consolidation
  - Created ADR system
  - Reorganized docs/tmp/ → proposals/, implementation/, archive/
  - Established phase numbering reconciliation

---

## Contributing to Documentation

When adding new documentation:

1. **Proposals**: Place in `docs/proposals/` until approved
2. **Active plans**: Place in `docs/implementation/` when approved
3. **Completed work**: Summarize and move to `docs/archive/`
4. **Major decisions**: Create ADR in `docs/decisions/`
5. **Update this file**: Add entry to relevant sections above

**Questions about where a document belongs?** Ask the project lead or check existing patterns in each directory's README.

