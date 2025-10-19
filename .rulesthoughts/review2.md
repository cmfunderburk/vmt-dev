# VMT Project Code & Documentation Review

The VMT (Visualizing Microeconomic Theory) project is a Python-based, spatial agent-based simulator focused on microeconomic behavior (barter trade, foraging, price discovery, etc.)[^1]. Its documentation hub (in `docs/`) contains a Project Overview (user guide), Technical Manual, Strategic Roadmap, and Type System & Data Contracts guide[^2], reflecting the project vision. For example, the README notes that VMT is a "spatial agent-based simulation for teaching and researching microeconomic behavior"[^1], and the tech docs describe a 7-phase tick cycle (Perception → Decision → Movement → Trade → Forage → Regeneration → Housekeeping) as the core of the engine[^3]. These resources establish the long-term roadmap and design constraints (e.g. determinism, typing invariants) that all code and rules should uphold.

## Codebase Structure and Quality

The repository is well-organized (see `docs/2_technical_manual.md` for structure)[^4], with separate modules for the engine (`vmt_engine/`), GUI (`vmt_launcher/`, `vmt_log_viewer/`, `vmt_pygame/`), scenarios/schema code, telemetry, and tests. Entry points are `main.py` (CLI) and `launcher.py` (PyQt GUI)[^5]. The code adheres to strict determinism (sorting agents by ID, fixed tie-breakers, etc.)[^6] and fully implements its intended features (utility functions, trade algorithms, etc.) as documented. A comprehensive test suite (at least 95 passing tests as of Oct 2025[^7]) confirms functionality and detects regressions.

Importantly, a recent review found no commented-out code, no skipped tests, and minimal dead code[^8]. The only minor issues noted were two unused config fields in `src/telemetry/config.py` (`export_csv`, `csv_dir` were defined but never used)[^9] and a couple of "TODO" comments in the log-viewer widgets for planned features (trajectory visualization and trade filtering)[^10]. These are low-risk (documentation or future work notes) and can be cleaned up or implemented as needed.

**Key findings**: code health is excellent, deterministic invariants are consistently enforced, and feature coverage is thorough. For example, the telemetry system was recently overhauled from CSV to SQLite (yielding ~99% log-size reduction) and all related docs/tests were updated[^11][^7]. The only redundant artifacts are the legacy CSV flags, which could be removed or documented for clarity[^9].

## .cursor Rules Review

The repository includes a `.cursor/rules/` directory containing Cursor AI rule files (`.mdc` format) that guide AI agents. These rules codify project knowledge, style, and workflows. Key rule files are:

### Core Rule Files

- **`vmt-overview.mdc`** – A global summary of the project. This file (marked `alwaysApply: true`) lists the 7-phase tick cycle, determinism rules (e.g. always sort by agent ID, use round-half-up, never mutate quotes mid-tick) and type invariants (e.g. which fields are integers vs floats)[^6][^12]. It also maps the core modules (engine, econ, systems, GUI, etc.) and entry points in one place[^13][^14]. This is an excellent quick-reference for agents and developers.

- **`scenarios-telemetry.mdc`** – Guidelines for scenario files and the telemetry DB. Using `globs: src/scenarios/*.py, scenarios/*.yaml, src/telemetry/*.py`, it provides schema references and examples for YAML scenarios (grid size, agents, utilities, resource params) and instructions for adding new scenarios and telemetry fields[^15][^16]. It also details the SQLite schema and loggers. This rule ensures agents know how to structure scenarios and logging.

- **Money System Rules (`money-*.mdc`)** – A suite of rules governing the new monetary feature, organized by topic. The `money-guide.mdc` file outlines the overall plan: a 6-phase implementation roadmap, key invariants, and links to detailed docs[^17]. It lists companion rules for implementation (architecture decisions, invariants), telemetry (schema extensions), testing (phase-specific test requirements), and pedagogy (teaching objectives and demo scenarios). Together they ensure AI agents follow the money-system vision (backward compatibility, determinism, performance)[^17].

Overall, the `.cursor` rules comprehensively capture the project's domain knowledge (trade mechanisms, learning goals, file conventions). They align well with the documented vision. For instance, the VMT overview rule enforces the "sacred" tick order and type invariants[^6], exactly as required by the engine design[^3]. The scenarios-telemetry rule reminds agents to use integer spatial parameters and weight-sum=1 for utilities, matching the schema constraints. The money-system rules reflect the strategic roadmap's phased plan and invariant checks (e.g. sorting by `(price, seller_id)` for stability[^17]).

## Suggested Improvements to .cursor Rules

### Clean Up and Maintenance

- **Remove obsolete rules or fields.** If any code or config has been deprecated (e.g. the unused CSV flags), update or prune related guidance so agents aren't misled. For example, remove references to CSV export flags if those are no longer active[^9].

- **Update rule content for new features.** Ensure the rules stay in sync with docs and code. If the strategic roadmap adds new features beyond the money system, create corresponding rule files. Likewise, refine existing rules as implementations solidify (e.g. finalize any placeholders in the money-implementation plan).

### Targeting and Scoping

- **Refine granularity and targeting.** The current rules are well-organized by topic, but consider adding `globs` metadata where appropriate. For instance, the money rules could use `globs:` to apply only to money-related modules. This prevents irrelevant info injection when working on unrelated code. The scenarios-telemetry example already shows good use of `globs: src/scenarios/*.py, scenarios/*.yaml, src/telemetry/*.py`[^18].

### Consistency and Documentation

- **Ensure style consistency.** Use consistent format (headings, bullet lists) across all rule files. For example, the overview rule uses clear headings and lists of rules. Apply the same style in money-implementation, money-testing, etc., for readability.

- **Link to authoritative sources.** Where possible, link rule statements to docs or code (as done in `vmt-overview`). For instance, rules about utility functions could point to `src/vmt_engine/econ/utility.py` or the Type System doc. This reinforces alignment between AI guidance and actual implementation.

- **Add missing guidelines.** If any important coding conventions or design decisions are only in the docs (e.g. YAML versioning, random-seed handling, logging best practices), consider summarizing them in rules. The project's Strategic Roadmap and Type System docs contain vision and formal invariants that agents should use. Embedding key points (like "use date-time labels, not semantic versions"[^19]) helps keep AI outputs aligned.

### Version Control

- **Clean up and version rules.** Finally, treat the `.cursor` directory as part of the living specification: update front-matter (e.g. descriptions, globs) as code evolves. Remove any rule files that no longer apply. For example, if a feature is fully implemented, its "checklist" can become a historical reference or be archived.

## Best Practices for Cursor Rules

General guidelines for managing `.cursor` (or `.cursorrules`) files include:

### Project-Specific Instructions

- **Use project-specific instructions.** Put a rules directory (or `.cursorrules` file) in the root so the AI always loads your custom rules. These rules should reflect your project's needs: coding style, architectural constraints, and domain context[^20]. As the awesome-cursorrules guide notes, defining standards ensures the AI's output aligns with your style and knowledge[^20].

### Targeting and Scope

- **Target rules with front-matter.** Use the YAML header in each `.mdc` file to control application. The `globs:` field lets you specify which files the rule applies to (e.g. scenario YAMLs, engine code), avoiding off-topic influence. Set `alwaysApply: true` only for truly global guidance. The VMT rules example shows this: the overview rule is `alwaysApply` (it covers fundamental invariants)[^6], while the scenarios rule uses specific globs[^18].

### Content Quality

- **Keep rules concise and factual.** Write rules as bullet points or short sections. Focus on what must be done (e.g. "Always sort agents by ID") or must be true (type invariants), rather than long explanations. Use links to code or docs for details. For example, the overview rule succinctly lists determinism guarantees with minimal text[^6]. Clear formatting (headers, lists) makes it easy for the AI to parse.

- **Include relevant context.** Provide any background the AI might need: key file paths, configuration details, or business logic. For instance, the scenarios rule lists the YAML schema and common mistakes, giving agents concrete examples[^15][^21]. Always mention where configuration lives (e.g. mention `ScenarioParams.validate()` if checking a new param) so agents can correctly navigate the code.

### Security and Maintenance

- **Avoid secrets in rules.** Do not include actual API keys or sensitive data in rule files. Use placeholders and instruct agents to keep keys out of version control[^22]. In general, treat `.cursor` rules as public project documentation.

- **Iterate rules with development.** As your codebase and vision evolve, regularly update the rules. Remove outdated guidance and add new ones. The Cursor community recommends keeping the rules in sync with project changes so the AI assistant remains aligned[^23]. In practice, treat `.cursor/rules/` like additional documentation that requires version control and peer review (as was done for VMT's feature changes).

By following these practices and keeping the VMT rules current, AI agents will generate code and suggestions that match the project's goals and quality standards.

## Summary

The VMT codebase is well-maintained and documented. Key improvements include trimming minor dead code (unused CSV flags), and refining the `.cursor` rule set to match the final architecture. Ensuring each `.cursor` file is scoped, up-to-date, and reflective of project vision will help AI tools remain a useful partner in development.

---

## References

[^1]: [README.md](https://github.com/cmfunderburk/vmt-dev/blob/707fda6f8796ab986952797ba161af6320a4e171/README.md)

[^2]: [1_project_overview.md](https://github.com/cmfunderburk/vmt-dev/blob/707fda6f8796ab986952797ba161af6320a4e171/docs/1_project_overview.md)

[^3]: [2_technical_manual.md](https://github.com/cmfunderburk/vmt-dev/blob/707fda6f8796ab986952797ba161af6320a4e171/docs/2_technical_manual.md)

[^4]: docs/2_technical_manual.md (structure)

[^5]: main.py and launcher.py entry points

[^6]: [vmt-overview.mdc](https://github.com/cmfunderburk/vmt-dev/blob/dbdc5928538537ffa99923727b4b2878fdeed731/.cursor/rules/vmt-overview.mdc)

[^7]: [CODE_REVIEW_2025-10-19.md](https://github.com/cmfunderburk/vmt-dev/blob/dbdc5928538537ffa99923727b4b2878fdeed731/docs/CODE_REVIEW_2025-10-19.md)

[^8]: CODE_REVIEW_2025-10-19.md (no commented code)

[^9]: CODE_REVIEW_2025-10-19.md (unused CSV flags)

[^10]: CODE_REVIEW_2025-10-19.md (TODO comments)

[^11]: Telemetry system overhaul notes

[^12]: vmt-overview.mdc (type invariants)

[^13]: vmt-overview.mdc (module mapping)

[^14]: vmt-overview.mdc (entry points)

[^15]: [scenarios-telemetry.mdc](https://github.com/cmfunderburk/vmt-dev/blob/dbdc5928538537ffa99923727b4b2878fdeed731/.cursor/rules/scenarios-telemetry.mdc)

[^16]: scenarios-telemetry.mdc (schema references)

[^17]: [money-guide.mdc](https://github.com/cmfunderburk/vmt-dev/blob/dbdc5928538537ffa99923727b4b2878fdeed731/.cursor/rules/money-guide.mdc)

[^18]: scenarios-telemetry.mdc (globs example)

[^19]: vmt-overview.mdc (versioning policy)

[^20]: [GitHub - PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules)

[^21]: scenarios-telemetry.mdc (common mistakes)

[^22]: [README.mdc](https://github.com/phamhung075/cursor-agentic-ai/blob/0f9724948af01c637864460c90bef7b026bb225e/.cursor/rules/README.mdc)

[^23]: awesome-cursorrules (keeping rules current)

