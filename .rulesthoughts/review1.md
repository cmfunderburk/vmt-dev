## VMT Project Code & Documentation Review (2025-10-19)

Overall, the VMT project is **exceptionally well-structured, documented, and maintained**, especially for a solo developer project. The codebase demonstrates strong adherence to deterministic principles, a clear separation of concerns, and a thoughtful approach to simulation design. The documentation is comprehensive and serves as a solid foundation. The `.cursor/rules` are already quite detailed and show a good understanding of how to guide AI agents.

---

### 1. Project Vision Alignment

* **Vision:** To create a "visualization-first" computational laboratory for exploring microeconomic principles (foraging, barter, money, markets, production, GE), supporting both educational and research modes.
* **Alignment:** The current codebase (Phase A - Foraging & Barter) strongly aligns with this vision. The architecture (7-phase tick cycle, deterministic rules, agent-based approach) provides a robust foundation for future phases. The documentation clearly articulates this vision and roadmap.

---

### 2. Codebase Structure Review

* **Organization:** The `src/` layout with clear separation for `vmt_engine`, `vmt_launcher`, `vmt_log_viewer`, `telemetry`, and `scenarios` is excellent.
* **Engine (`src/vmt_engine/`):**
    * `core/`: Well-defined state objects (`Agent`, `Inventory`, `Quote`, `Grid`) and `SpatialIndex`.
    * `econ/`: Clear separation of economic primitives (`utility.py`).
    * `systems/`: Perfect mapping to the 7-phase tick cycle, promoting modularity.
* **GUI (`src/vmt_launcher/`, `src/vmt_log_viewer/`, `src/vmt_pygame/`):** Good separation from the core engine. Standard PyQt5 and Pygame patterns are used.
* **Telemetry (`src/telemetry/`):** Robust SQLite implementation with clear schema (`database.py`), configuration (`config.py`), and logging logic (`db_loggers.py`).
* **Scenarios (`src/scenarios/`, `scenarios/`):** Clean separation of schema/loader logic from user-facing YAML files.
* **Tests (`tests/`):** Well-organized, covering core components, integration, performance, and specific features (e.g., mode toggles, money infrastructure).

**Assessment:** The structure is logical, scalable, and easy to navigate. It directly supports the phased roadmap.

---

### 3. Documentation Review

* **Core Docs (`docs/`):** Excellent. The numbered documents (`1_project_overview.md` to `4_typing_overview.md`) provide a clear, layered understanding from user guide to technical deep-dive. They accurately reflect the project vision and current state.
* **Roadmap (`docs/3_strategic_roadmap.md`):** Clear articulation of the phased approach (A to F) and detailed checklists for immediate milestones.
* **Technical Manual (`docs/2_technical_manual.md`):** Good overview of the 7-phase cycle, determinism, and core algorithms.
* **Type Contracts (`docs/4_typing_overview.md`):** Essential for maintaining consistency, especially as the project grows. Good use of `[IMPLEMENTED]` vs. `[PLANNED]` status markers.
* **Engine README (`src/vmt_engine/README.md`):** Provides a concise technical summary, perfectly complementing the main docs.
* **Code Comments/Docstrings:** Generally good, especially in core engine files like `utility.py` and `matching.py`, explaining economic rationale and invariants.
* **Planning Docs (`docs/BIG/`):** Extremely detailed and well-structured, particularly the SSOT and phased checklists for the money system. The post-mortem analysis (`phase2_postmortem.md`) is insightful.
* **Recent Code Review (`docs/CODE_REVIEW_2025-10-19.md`):** Demonstrates proactive quality assessment.

**Assessment:** Documentation is a major strength. It's comprehensive, up-to-date (as of Oct 19, 2025), and clearly aligns with the project vision. The detailed planning documents in `docs/BIG/` are particularly valuable.

---

### 4. Cursor Rules (`.cursor/rules/`) Review

The existing rules are already very good, demonstrating a strong understanding of how to guide AI agents effectively within this specific project context. They cover architecture, testing, specific subsystems (economics, GUI, telemetry), and the ongoing money implementation.

**Strengths:**

* **Comprehensive Coverage:** Rules exist for major components and workflows.
* **Specificity:** Rules like `systems-development.mdc` provide phase-specific guidance and critical invariants.
* **Critical Gotchas:** Key issues like the `venv` name and the database deletion requirement are highlighted.
* **Cross-Referencing:** Effective use of `mdc:` links connects rules to relevant code and documentation.
* **Money Implementation Guidance:** Dedicated rules (`money-guide.mdc`, `money-implementation.mdc`, etc.) provide excellent, context-specific instructions aligned with the SSOT.

**Areas for Improvement & Suggestions:**

1.  **Dead Code / Deprecation Rule:**
    * **Problem:** You mentioned issues with dead code and lingering deprecated functionality.
    * **Suggestion:** Create a new rule, perhaps `refactoring-and-deprecation.mdc`, specifically for guiding AI agents during refactoring tasks.
    * **Content:**
        * Define the project's deprecation policy (e.g., use `DeprecationWarning`, timeline for removal, update SSOT/checklists).
        * Instruct the AI to **always** search for usages of a function/class before modifying or removing it (using search tools or IDE features).
        * Provide steps for safe removal: 1) Add `DeprecationWarning`, 2) Update all callers, 3) Run tests, 4) (Later) Remove the code, 5) Run tests again.
        * Explicitly tell the AI to update relevant documentation (docstrings, technical manual, phase checklists) when deprecating or removing features.
        * Mention the `compare_telemetry_snapshots.py` script as a tool for verifying that refactoring didn't change behavior in legacy scenarios.
        * Link to the recent code review (`docs/CODE_REVIEW_2025-10-19.md`) as an example of identifying unused code.

2.  **Consolidate Core Invariants:**
    * **Observation:** Critical rules like determinism (sorting loops, no mid-tick mutation) are repeated across multiple files (e.g., `vmt-overview.mdc`, `systems-development.mdc`, `money-guide.mdc`).
    * **Suggestion:** While repetition ensures visibility, consider creating a dedicated `core-invariants.mdc` rule that is *always applied*. Other rules can then briefly reference it (e.g., "Remember to adhere to core determinism rules"). This reduces maintenance overhead if an invariant needs updating.
    * **Content for `core-invariants.mdc`:** Determinism rules (sorting, rounding, quote stability), Type invariants (int vs. float), Backward compatibility policy.

3.  **Enhance Testing Workflow Rule:**
    * **Observation:** `testing-workflow.mdc` is good but could be more explicit about *when* to run which tests.
    * **Suggestion:** Add guidance based on the type of change:
        * Small bug fix: Run relevant unit tests + `pytest -q`.
        * Refactoring: Run full suite (`pytest -q`), potentially use `compare_telemetry_snapshots.py`.
        * New Feature (e.g., adding to a system): Write new unit/integration tests for the feature, run relevant system tests, then full suite.
        * Money System Phase: Follow the specific phase checklist testing requirements (reference `money-testing.mdc`).

4.  **Rule for Adding New Features:**
    * **Suggestion:** Create a `feature-development-checklist.mdc` rule.
    * **Content:**
        * Refer to the strategic roadmap (`docs/3_strategic_roadmap.md`).
        * Steps: Design (update SSOT if major), Implement, Unit Test, Integration Test, Document (code comments, core docs), Update Telemetry Schema (if needed, remember `rm logs/telemetry.db`), Update `.cursor/rules` (if architecture changes).
        * Emphasize adding tests *before* or *during* implementation.

5.  **Minor Refinements:**
    * **`vmt-overview.mdc`:** Update the test count from 63 to 95. Add a note about the `llm_counter` directory being ignored.
    * **`scenarios-telemetry.mdc`:** Update log levels (SUMMARY removed). Correct test count.
    * **Consistency:** Ensure consistent terminology (e.g., "tick cycle phases" vs. "systems").

**Assessment:** The existing rules are strong. Adding specific guidance for refactoring/deprecation and a general feature development checklist would further enhance AI alignment. Consolidating core invariants could improve maintainability.

---

### 5. Cursor Rules Best Practices (General Discussion)

Effective `.cursor/rules` significantly improve AI collaboration. Here are some best practices relevant to your project:

1.  **Granularity and Scoping:**
    * Use a mix of `alwaysApply: true` (for universal truths like invariants), `globs` (for file-specific context), and `description` (for on-demand workflows like testing). Your current setup does this well.
    * Avoid overly large, monolithic rules. Break down complex topics (like the money system) into focused sub-rules (implementation, telemetry, testing, pedagogy), as you've done.

2.  **Content and Style:**
    * **Be Directive:** Use imperative language (e.g., "Always sort loops...", "Do not mutate...", "Update the schema...").
    * **Explain the "Why":** Briefly explain the rationale behind rules (e.g., "to ensure determinism," "for backward compatibility"). This helps the AI understand the *intent*.
    * **Use Formatting:** Markdown (bolding, lists, code blocks) improves readability for both humans and AI.
    * **Link Extensively:** Use `mdc:` links to connect rules to specific files, documentation, and even other rules. This builds a knowledge graph.
    * **Highlight Critical Info:** Use **bolding**, ⚠️ emojis, or explicit callouts (like "MANDATORY" or "CRITICAL") for non-negotiable requirements (like determinism rules or deleting the DB).

3.  **Maintainability:**
    * **Single Source of Truth (SSOT):** For complex procedures or policies (like the money implementation plan), have a canonical document (`docs/BIG/money_SSOT_implementation_plan.md`) and have rules *refer* to it rather than duplicating large amounts of text.
    * **Review Regularly:** Update rules as the codebase evolves (new modules, changed architecture, updated dependencies, new common errors). Your `RULES_SUMMARY.md` is a good starting point for this review.
    * **Keep Rules Concise:** Focus on *guidance* and *constraints*, linking to detailed documentation for full explanations.

4.  **AI Alignment:**
    * **Anticipate Common Tasks:** Create rules specifically for frequent activities (testing, adding features, refactoring).
    * **Address Known Pain Points:** If you repeatedly encounter certain issues (like dead code), create rules specifically targeting them.
    * **Define Project-Specific Conventions:** Explicitly state deviations from standard practices if they are intentional (like your economic variable naming).

5.  **Structure:**
    * Use YAML frontmatter (`---`) consistently for metadata (`globs`, `description`, `alwaysApply`).
    * Organize rules logically within the `.cursor/rules/` directory (e.g., by component, workflow).

By following these practices, you can create a robust set of rules that effectively guide AI agents to contribute productively and safely to your project, respecting its specific architecture, conventions, and vision. Your current rules already incorporate many of these principles.

---

## Conclusion & Next Steps

The VMT project is in excellent shape. The codebase is clean, the documentation is thorough, and the AI guidance rules are well-developed.

**Recommendations:**

1.  **Implement New Rules:** Create the suggested rules for `refactoring-and-deprecation.mdc` and potentially `core-invariants.mdc` and `feature-development-checklist.mdc`.
2.  **Refine Existing Rules:** Update test counts, log levels, and consolidate invariants as suggested.
3.  **Address Minor Code Issues:** Quickly fix the few remaining linting/typing issues identified in `docs/tmp/lintcetera.md` (bare except, unused imports, float/int mismatch in schema).
4.  **Continue with Roadmap:** Proceed confidently with the detailed plans for Phase 2 (Money System) and beyond, using the AI (guided by the enhanced rules) for assistance.

This review confirms that the project is well-positioned for continued development, and the `.cursor/rules` provide a strong framework for leveraging AI assistance effectively.