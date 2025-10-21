# VMT Documentation Hub

Welcome to the central documentation hub for the Visualizing Microeconomic Theory (VMT) project. This directory contains the authoritative guides for using, understanding, and extending the VMT platform.

> **🔍 Looking for something specific?** See the **[Quick Reference Guide](quick_reference.md)** for a comprehensive lookup table.

## Core Documentation

To get started, please see the following documents:

-   **[1. Project Overview](./1_project_overview.md)**
    -   **Audience**: All Users (Educators, Students, Researchers)
    -   **Content**: A user-friendly guide to the VMT project. Covers features (75+ tests, trade pairing, money system, resource claiming, visualization), installation, GUI/CLI usage, and telemetry. **Start here if you are new to VMT.**

-   **[2. Technical Manual](./2_technical_manual.md)**
    -   **Audience**: Developers, Advanced Users
    -   **Content**: The definitive technical reference for the VMT engine. Details the core architecture, the 7-phase tick cycle (including pairing, claiming, money-aware matching), economic and behavioral algorithms (quasilinear utility, generic matching), determinism guarantees, and the testing framework.

-   **[3. Strategic Roadmap](./3_strategic_roadmap.md)**
    -   **Audience**: Developers, Contributors
    -   **Content**: The single source of truth for the project's vision and future development. Outlines the long-term feature roadmap (money Phases 3-6, markets, bargaining protocols) and the immediate, actionable steps and checklists for upcoming versions.

-   **[4. Type System & Data Contracts](./4_typing_overview.md)**
    -   **Audience**: Developers, Contributors, Port Maintainers
    -   **Content**: The authoritative, language-agnostic specification for all data structures (Inventory with M field, money-aware Quotes, Agent pairing state), invariants, economic logic (utility API split, generic matching), telemetry schema (money fields, pairing/preferences tables), and serialization contracts. Essential for understanding the formal data model.

---

## Documentation Organization (Updated 2025-10-21)

The documentation is now organized into clear categories:

### 📚 Core Documents (Above)
Start with the numbered guides (1-4) above for understanding and using VMT.

### 🎯 Current Implementation Plans

-   **[Money System](./BIG/)** - Money Phases 1-6 implementation
    -   ✅ Phases 1-2 complete (quasilinear utility, monetary exchange)
    -   📋 **Next: [Phase 3](./BIG/money_phase3_checklist.md)** (mixed regimes)
-   **[Scenario Generator](./implementation/)** - CLI tool for generating scenarios
    -   ✅ Phase 1 complete (CLI MVP)
    -   📋 **Ready: [Phase 2](./implementation/scenario_generator_phase2_plan.md)** (exchange regimes + presets)

### 💡 Strategic Planning

-   **[Decisions](./decisions/)** - Architecture Decision Records (ADRs)
    -   [ADR-001: Hybrid Sequencing](./decisions/001-hybrid-money-modularization-sequencing.md) - Current strategic direction
-   **[Proposals](./proposals/)** - Features under consideration
    -   [Protocol Modularization](./proposals/protocol_modularization_plan.md) - Deferred until after Money Track 1
-   **[Documentation Audit](./audit/)** - Comprehensive status review
    -   [2025-10-21 Audit](./audit/2025-10-21_comprehensive_documentation_audit.md) - Current state assessment

### 📦 Archives & Historical

-   **[Archive](./archive/)** - Completed implementation plans and historical documents
-   **[BIG/](./BIG/)** - Money system phase completion summaries

---

## Quick Navigation

**Need to find something fast?** → [Quick Reference Guide](quick_reference.md)

**Want to contribute?** → Start with [Technical Manual](2_technical_manual.md), then see [Strategic Roadmap](3_strategic_roadmap.md)

**Confused about "Phase" numbers?** → See [Quick Reference: Phase Numbering](quick_reference.md#by-phase-number-reconciliation)
