# VMT Documentation Hub

Welcome to the central documentation hub for the Visualizing Microeconomic Theory (VMT) project. This directory contains the authoritative guides for using, understanding, and extending the VMT platform.

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
