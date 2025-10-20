Here is a unified plan that synthesizes the recommendations from both `review1_gem.md` and `review2_gpt.md`. This plan prioritizes the strategic direction and existing file structure from `review1` while incorporating the valuable, non-conflicting procedural details and code sketches from `review2` to create a single, actionable source of truth.

The synthesis is organized into two main parts: first, a comprehensive documentation update to solidify the project's current state, and second, a clear plan for the strategic pivot towards modular pairing and bargaining models.

---

## Unified Plan for Documentation and Roadmap

### **Part 1: Comprehensive Documentation Update**

This phase brings all documentation in line with the current codebase, establishing a solid foundation before any major refactoring.

**Phase A: Preparation & Audit**

This combines the procedural rigor of `review2` with the content focus of `review1`.

1.  **Create a dedicated branch** for this work: `git checkout -b docs-refresh-2025-10-20`.
2.  **Snapshot Current State (`review2`):** Create a temporary `docs/_audit/` directory. In it, save a snapshot of the root `README.md` and a full file listing (`git ls-tree -r --name-only HEAD | sort > docs/_audit/tree-2025-10-20.txt`). This provides a clear baseline.
3.  **Audit Against Existing Structure (`review1`):** Perform a comprehensive review of all documents listed in `review1`'s "Phase 1: Review & Audit". This list is authoritative as it pertains to the project's *current* file structure.
4.  **Create a To-Do Ledger (`review2`):** The output of the audit will be a master checklist, `docs/PLAN_OF_RECORD.md`. This file will list each document to be updated, the required changes, and will serve to track progress.

**Phase B: Content Update**

This phase executes the updates identified in the audit, following the detailed, file-by-file plan from `review1`'s "Phase 2". The focus is on updating existing documents in place, not reorganizing them into a new structure.

*   The updates will proceed in the logical order specified in `review1`, starting with foundational documents like `docs/4_typing_overview.md` and proceeding through the `src/vmt_engine/README.md`, technical manual, user guide, money system SSOTs, and finally the `CHANGELOG.md` and `.cursor/rules/`.
*   This ensures that all recent features (Target Arrows, Resource Claiming, Money System P1/P2, updated pairing logic) are correctly documented where they are currently referenced.

**Phase C: Review & Finalize**

This phase combines the review processes from both inputs to ensure high quality.

1.  **Peer Review (`review1`):** Conduct a full read-through of all updated documents for clarity, accuracy, and consistency.
2.  **Link Check (`review1`):** Verify all internal documentation links.
3.  **Acceptance Checklist (`review2`):** Before merging, validate against a concrete checklist:
    *   Does the Quick Start command in the root `README.md` work with the updated scenario paths (see Part 2)?
    *   Do all key links in the `docs/README.md` hub resolve correctly?
    *   Are the core data contracts (Agent state, Trades, etc.) accurately reflected in `docs/4_typing_overview.md`?
    *   Have new tests been added to cover the scenario loading from the new structure (see Part 2)?

### **Part 2: Roadmap Pivot & Code Refactoring**

This part outlines the strategic shift to treat matching and bargaining as first-class, modular components, as endorsed by both reviews.

**Step 1: Reorganize Scenarios (Agreement)**

Both reviews converge on the same logical separation for scenarios. This change is additive and non-breaking.

1.  **Create New Directories:**
    ```
    scenarios/
    ├── full/
    ├── bargaining/
    └── matching/
    ```
2.  **Move Existing Scenarios:** Relocate all current `.yaml` files into `scenarios/full/`.
3.  **Update Entry Points:** Update the root `README.md` and any other relevant scripts to reflect the new path for default scenarios (e.g., `... scenarios/full/three_agent_barter.yaml`).
4.  **Add Placeholders:** Add minimal `README.md` files to `bargaining/` and `matching/` explaining their purpose.

**Step 2: Code Refactoring Strategy (A Synthesis)**

This follows `review1`'s preference for a lighter-touch refactor while using `review2`'s excellent, detailed implementation ideas.

*   **Architectural Goal (`review1`):** The primary goal is to abstract the matching and bargaining logic out of the core `DecisionSystem` and `TradeSystem` without a full rewrite of the `src/` directory.
*   **Proposed Implementation:**
    1.  **Define Protocol Interfaces (`review1`):** Establish formal `MatchingProtocol` and `BargainingProtocol` interfaces. The detailed code sketches from `review2` provide an excellent starting point for these definitions.
    2.  **Create New Modules (`review1`):** House the new protocol implementations in dedicated directories: `src/vmt_engine/protocols/matching/` and `src/vmt_engine/protocols/bargaining/`.
    3.  **Use a Scenario Adapter (`review2`):** Introduce a `ScenarioAdapter` pattern. The scenario loader will use this adapter to configure the main simulation loop with the correct protocols (`Forage`, `MatchingProtocol`, `BargainingProtocol`) based on the scenario's type.
    4.  **Consider an Event Bus (`review2`):** To further decouple systems, implement a simple event bus with hooks like `BeforeMatch`, `AfterBargain`, etc. This allows different modules to interact without direct dependencies.
    5.  **Update Scenario Schema (`review1`):** Add a top-level `simulation_type: Literal["full", "bargaining", "matching"]` to `src/scenarios/schema.py` to drive the scenario adapter logic.

**Step 3: Updated Strategic Roadmap**

This adopts `review1`'s pragmatic, four-step approach for de-risking the pivot, while defining the "Pairing Detour" with the clarity from `review2`. The `docs/3_strategic_roadmap.md` will be updated to reflect this sequence:

1.  **Immediate Priority: Complete the Documentation Update.** Solidify the current state first.
2.  **Prototype a Simple Matching Scenario.** Create a minimal scenario (e.g., `scenarios/matching/random_search.yaml`) and a corresponding `MatchingProtocol` implementation. The goal is to prove the feasibility of the new, decoupled architecture.
3.  **Evaluate the Prototype.** Assess the clarity and robustness of the protocol interfaces and the adapter pattern.
4.  **Commit and Refine Roadmap.** Based on the successful prototype, formally commit to the "Pairing Detour" and update the roadmap. This detour will include the specific, measurable deliverables outlined in `review2`:
    *   **Matching v0:** Implement a random search baseline.
    *   **Bargaining v0:** Implement an alternating-offers protocol.
    *   **Telemetry & Plots:** Ensure new scenarios produce clear, plottable outputs for analysis.
    *   **Comparative Analysis:** Plan for experiments that compare outcomes across different pairing regimes.

This unified plan provides a clear, step-by-step path forward that leverages the strengths of both reviews, respects your stated preferences, and manages technical risk by prioritizing documentation and prototyping before committing to a full-scale refactor.