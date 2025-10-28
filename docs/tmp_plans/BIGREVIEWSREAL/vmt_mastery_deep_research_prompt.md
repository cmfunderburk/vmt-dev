VMT-DEV Mastery Deep Research Prompt

Use this prompt to generate a complete, rigorous, step-by-step self-study program that turns a Python-proficient economist into a master of the vmt-dev codebase. The output should be a standalone, production-quality learning guide with hands-on labs, comprehension checks, implementation exercises, and a capstone.

Role and Mission
- You are a senior engineer-educator tasked with producing a comprehensive, high-fidelity study program for the vmt-dev repository. Your reader knows economics and Python but is entirely new to this project.
- Your mission: produce an actionable, end-to-end curriculum that makes the learner fully productive in this codebase, capable of implementing new protocols, running experiments, ensuring deterministic reproducibility, and contributing high-quality code and docs.

Authoritative Context (non-negotiable project rules)
Summarize these rules prominently early in the guide and weave them throughout all exercises:
- Determinism: With the same seed, all runs must produce identical outcomes. Only use seeded RNGs (agents: `self.rng`, engine: `world.rng`). Never use `random.random()`, `numpy.random`, time-based seeds, or any unseeded randomness.
- Ordered iteration: Never iterate unordered structures without sorting. Always enforce deterministic order (e.g., `sorted(agents, key=lambda a: a.id)`).
- Effects-only state changes: All state mutations occur via Effects during the correct phase transitions. Protocols and agents never mutate world state directly.
- Protocol → Effect → State pattern: Protocols produce Effects; the Engine validates/applies Effects; State updates only during the correct phase.
- Seven-phase tick cycle (must be respected): 0 Regeneration; 1 Movement decisions → MoveEffects; 2 Movement execution; 3 Forage/mining decisions → ResourceEffects; 4 Trading negotiations → TradeEffects; 5 Trade execution/inventory updates; 6 Consumption & utility.
- Typing authority: The authoritative typing spec is at `docs/4_typing_overview.md`. Inventories/resources/ΔA/ΔB are integers; spatial params are integers.

Repository Inputs (assume these paths are available for reading and cross-referencing)
- Root: `/home/cmf/projects/vmt-dev`
- Key directories: `src/vmt_engine/`, `src/telemetry/`, `src/vmt_launcher/`, `scenarios/`, `tests/`, `docs/`
- Key docs to mine: `docs/1_project_overview.md`, `docs/2_technical_manual.md`, `docs/4_typing_overview.md`, `docs/onboarding/*`, `docs/protocols_10-27/*`
- Scripts: `scripts/*.py` (e.g., `benchmark_performance.py`, `run_headless.py`)

Audience
- PhD-level economist, strong in theory, familiar with Python, new to this codebase and its architecture.
- Minimize econ 101; focus on mapping theory to implementation and on the project’s architectural invariants.

Deliverables (what you must output)
1) Executive Overview (1–2 pages)
   - What vmt-dev is, where it fits, and what problems it solves.
   - Architectural map: Protocol → Effect → State, seven-phase tick, determinism contract, typing invariants.
   - A high-level repository tour with roles of `protocols/`, `systems/`, `core/`, `telemetry/`, `scenarios/`, and `tests/`.

2) Mastery Curriculum (modular, sequenced)
   - 4–6 modules with explicit prerequisites, learning objectives, estimated time, artifacts to produce, and clear acceptance criteria.
   - For each module include:
     - Target files/folders to read with a recommended reading order.
     - Guided reading prompts, “stop-and-think” questions, and short exercises.
     - Hands-on lab(s) with step-by-step instructions, expected outputs, and validation checks.
     - Common pitfalls and how to avoid violating determinism/architecture rules.
   - Required modules (expand as needed):
     - Module A: Orientation and quickstart (run tests, run a demo scenario headless and with logs).
     - Module B: Core Engine and Phase System (tick cycle, world state flow, Effects lifecycle).
     - Module C: Protocols in depth (decision generation, pairing/matching, trading, money vs barter regimes).
     - Module D: Scenarios and Typing (YAML configs, typed values, seeding, spatial parameters).
     - Module E: Telemetry and Experimentation (logging, metrics, comparing telemetry snapshots, perf benchmarking).
     - Module F: Advanced Topics and Extensions (mode scheduling, quotes/negotiation, utility classes, performance considerations).

3) Hands-on Labs
   - Provide concrete labs with commands, files to edit, and verification steps. Examples:
     - Lab 1: Environment setup, `pip install -r requirements.txt`, `pytest -q`, run a small scenario from `scenarios/demos/` using `scripts/run_headless.py`.
     - Lab 2: Determinism check: run the same scenario twice with the same seed; show identical telemetry snapshots; demonstrate how a violation would show up.
     - Lab 3: Reading the Engine loop: trace a tick across phases, identify where Effects are batched, validated, and applied.
     - Lab 4: Implement a minimal new Protocol variant (scaffold only); ensure it returns Effects and never mutates state directly.
     - Lab 5: Add a new scenario variant in `scenarios/`, tune parameters, and benchmark with `scripts/benchmark_performance.py`.
     - Lab 6: Telemetry drill: instrument a new metric or selection filter (if applicable) and compare runs using `scripts/compare_telemetry_snapshots.py`.

4) Capstone Project
   - Design and implement a simple but nontrivial Protocol or a significant enhancement to an existing protocol (e.g., a deterministic tie-breaking strategy in trading) that:
     - Strictly follows Protocol → Effect → State and seven-phase discipline.
     - Includes tests in `tests/` demonstrating correctness and determinism (same-seed reproducibility with identical telemetry).
     - Adds a `scenarios/` YAML to showcase the new behavior; includes performance characterization.
     - Provides a short technical note connecting the economics to the code design.
   - Deliver acceptance criteria and a review checklist.

5) Reference Appendices
   - Glossary (economics → code mapping): e.g., “reservation value” → which class/method; “quotes” → where stored and how matched.
   - Repository map: concise table of major modules, key classes/functions, and responsibilities.
   - Test index: what each major test validates and why it matters (connect to theory and architecture rules).
   - Common violations and how to detect them (e.g., unseeded randomness, unordered iteration, direct mutation).

Formatting and Citation Requirements
- Output must be a single, navigable Markdown document with clear `##` and `###` headings, skimmable lists, and short code/command blocks.
- When quoting existing repository code, cite file paths and include minimal excerpts. Prefer this format when showing existing code:
  ```startLine:endLine:filepath
  // code excerpt here
  ```
- Keep code excerpts small and purposeful; reference functions/classes by file path and name when possible instead of dumping large blocks.
- Use fenced code blocks for new example code or shell commands with appropriate language tags (e.g., `python`, `bash`).

Evaluation and Acceptance Criteria
- Each module must specify “Evidence of Mastery” (e.g., passing specific tests, reproducing identical telemetry across runs, producing a working scenario, or implementing a small protocol change).
- Include an end-to-end checklist to verify:
  - No unseeded randomness anywhere in new or modified code.
  - All iterations over sets/dicts are explicitly ordered.
  - All state changes are via Effects in the proper phases.
  - Same-seed runs produce identical telemetry (document the exact commands to prove it).

Explicit Guidance on Where to Look (seed the learner’s exploration)
- Docs: `docs/1_project_overview.md`, `docs/2_technical_manual.md`, `docs/4_typing_overview.md`, `docs/onboarding/*.md`, `docs/protocols_10-27/*`
- Engine/Architecture hotspots: `src/vmt_engine/core/`, `src/vmt_engine/systems/`, `src/vmt_engine/protocols/`, `src/vmt_engine/protocols/base.py`
- Scenarios: `scenarios/*.yaml`, `src/scenarios/*.py`
- Telemetry: `src/telemetry/*.py`
- Launchers/CLI: `src/vmt_launcher/*.py`, `scripts/*.py`
- Tests: `tests/*.py` (pay special attention to integration tests and those that validate determinism, protocol registry, and mode scheduling)

Proposed Learning Timeline (adapt as needed)
- Week 1: Orientation, Engine and Effects, running and verifying scenarios, determinism fundamentals.
- Week 2: Protocols deep dive, scenarios & telemetry, basic extension (small protocol change), performance/benchmark basics.
- Optional Week 3: Advanced features (money vs barter, quotes, matching, utility forms) and capstone implementation.

Hands-on Commands (include in labs; adapt to the learner’s environment)
```bash
# From repository root
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest -q
python scripts/run_headless.py --scenario scenarios/demos/foundational_barter_demo.yaml --seed 42 --out logs/demo_run
python scripts/compare_telemetry_snapshots.py --a logs/demo_run/seed42 --b logs/demo_run_again/seed42
python scripts/benchmark_performance.py --scenario scenarios/perf_both_modes.yaml --seed 123 --ticks 200
```

Process Expectations for Your Output
- Start with a short plan (outline), then produce the full guide.
- Embed cross-references to files and tests directly in the text.
- Make each module self-contained with clear objectives, tasks, and acceptance criteria.
- Include frequent “stop-and-think” questions to focus attention on invariants (determinism, ordered iteration, effects-only updates).
- Provide a final “Mastery Review” checklist and rubric.

Quality Bar
- The guide should be clear and actionable for a solo learner. It must be sufficiently detailed that they can complete labs and the capstone without additional help.
- It should emphasize determinism and the Protocol → Effect → State architecture in every module.
- It should connect economics concepts to concrete code locations and tests for validation.

Now produce the complete study guide as a single Markdown document following these instructions.


