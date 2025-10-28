## VMT Developer Onboarding

This onboarding is for developers with a background similar to the project’s primary author (~Master's/PhD-level in Economics). It prioritizes determinism, clear economic rationale, and an architecture-first understanding.

### What you’ll get
- **Environment setup** with zero-guesswork
- **Run your first simulations** (GUI and CLI)
- **Architecture overview** (Protocol → Effect → State; 7-phase cycle; determinism)
- **Development workflow** (style, naming, tests, docs)
- **Deep dives** (protocols, systems, scenarios, telemetry, performance)
- **Checklist and glossary** to get productive in 1–2 days

### Prerequisites
- Python 3.11 (recommended)
- Git, make (optional), SQLite tooling (optional)

### Start here (30–60 minutes)
1. Read: [2_quickstart.md](2_quickstart.md)
2. Run: one demo scenario via GUI and one via CLI
3. Skim: [3_architecture_overview.md](3_architecture_overview.md)

### Deep path (1–2 days)
1. Environment: [1_environment_setup.md](1_environment_setup.md)
2. Architecture + determinism: [3_architecture_overview.md](3_architecture_overview.md)
3. Dev workflow: [4_development_workflow.md](4_development_workflow.md)
4. Protocols: [5_protocol_development_guide.md](5_protocol_development_guide.md)
5. Effects & systems: [6_effects_and_systems.md](6_effects_and_systems.md)
6. Scenarios & typing: [7_scenarios_and_types.md](7_scenarios_and_types.md)
7. Telemetry & analysis: [8_telemetry_and_analysis.md](8_telemetry_and_analysis.md)
8. Performance: [9_performance_guide.md](9_performance_guide.md)
9. Testing: [10_testing_guide.md](10_testing_guide.md)
10. Checklist & glossary: [onboarding_checklist.md](onboarding_checklist.md), [glossary.md](glossary.md)

### Cross-references
- Core overview: `docs/1_project_overview.md`
- Technical manual: `docs/2_technical_manual.md`
- Typing spec (authoritative): `docs/4_typing_overview.md`
- Scenario templates: `docs/structures/*.yaml`

### Support
- Example-driven usage: see `tests/` and `scenarios/demos/`
- GUI tools: `launcher.py` (PyQt6), `src/vmt_log_viewer/`


