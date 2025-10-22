VMT – Visualizing Microeconomic Theory: Updated
Project Plan (Oct 2025)
Core Understanding

1. Problem & Success Definition

Problem: VMT remains a spatial agent-based economic simulator for teaching microeconomics by
visualization. The engine runs on an NxN grid where heterogeneous agents forage for two goods and
engage in bilateral trade (barter or monetary exchange) through reservation-price negotiation 1 . This
demonstrates consumer choice, gains from trade, price discovery, and resource management in real time.


Success: The platform’s core mission is intact: provide interactive, deterministic simulations of consumer
theory that align with textbook predictions. Key criteria include: agents behaving as theoretically expected
for each utility type; immediate visual feedback (<1s) when parameters change; accurate data export and
analysis; and smooth performance (30+ FPS on standard hardware). For example, the system now runs with
identical outcomes across runs given the same seed (determinism) 2 . Telemetry logging via SQLite
achieves ~99% log compression over CSV 3 , enabling sub-second statistical queries. The flexible utility API
supports CES/Cobb-Douglas, linear, quadratic, translog, and Stone-Geary functions 4 , all of which produce
distinct, intuitive spatial behaviors in demonstrations.


Current Status vs Vision: The implemented system already delivers on many goals. Agents forage and
trade as planned, the GUI and CLI support custom scenarios, and data is logged for analysis. New features
(e.g. additional utility types and a money system) have been added beyond the original MVP. We still
measure success by education and research outcomes: e.g. instructors can clearly illustrate different
preference structures, students can explore scenarios via the GUI, and researchers can instrument
experiments with full reproducibility.


2. Key User Scenarios (flows)

     - S-01: Instructor teaching preference types. Launch the GUI on a demo scenario. Switch between Cobb–
       Douglas (CES), linear (perfect substitutes), quadratic (bliss points), translog, and Leontief (Stone-
       Geary) utility modes 4 . Watch how agent behavior shifts (e.g. split vs skewed consumption).
       Students predict outcomes before toggling modes. Success: Visual patterns clearly distinguish
       preference regimes. Failure: If all agents act similarly or visuals are cluttered, the educational goal is
       lost.


     - S-02: Student exploring barter vs money. Run two scenarios: one in barter_only and one in
       mixed regime. Observe with real-time HUD and log viewer how prices emerge and trades occur
        5   6. Compare total trades and utility outcomes. Success: Student grasps how introducing money
       changes trading patterns and liquidities. Failure: If money yields counterintuitive matches (due to the
       known pairing mismatch 6 ), clarifications are needed.




                                                       1
      - S-03: Educator building custom scenarios. Use the GUI scenario builder (or CLI generator) to set up a
        new trade scenario: e.g. 5 agents, custom starting inventories, mixed utility mix, and a
         mode_schedule toggling trade/forage. Verify that the scenario schema is validated on load (clear
       errors if invalid 7 ). Share the YAML with colleagues or export data for a lesson plan. Success:
       Scenario config is easy to create, editable via GUI forms, and leads to intended behaviors. Failure: If
       the builder is confusing or scenarios are hard to debug, teachers may avoid using it.


      - S-04: Researcher implementing new economic model. Extend the code by adding a “bargaining”
        strategy: plug in an auction market module without altering the existing 7-phase loop. Run
        simulations, log results (SQLite DB), and compare to analytical predictions. Success: New model
        integrates cleanly (modularity) and reproduces theoretical patterns. Failure: If core architecture
        resists extension or trade execution logic is entangled, the platform is less useful for research.


      - S-05: Graduate student studying system dynamics. Progress through curriculum phases (from simple
        barter to full economy): start with basic foraging, introduce money (w/ λ parameters), then
        experiment with “mixed_liquidity_gated” scenarios and mode schedules. Analyze emergent macro
        patterns in the database (using the PyQt log viewer). Success: The student sees how micro-decisions
        scale to system-wide phenomena (supply/demand, welfare). Failure: If system breaks under
        complexity or lacks guidance, insights are limited.


(Additional scenarios): E.g. exploring the effect of resource regeneration parameters on sustainability, or
benchmarking performance with 1,000+ agents.


3. System Sketch (components + data flow)


```
  ┌──────────────────────┐              ┌────────────────────┐                 ┌─────────────────────┐
  │     Core Engine      │  ◄───►       │  Visualization/HUD │     ◄───►       │   User Interface    │
  │ (Grid, Agents, IB,   │              │    (PyGame 2.5)    │                 │   (PyQt6 Launcher /CLI Entrypoint)         │
  │   Foraging, Trading) │              │ with real-time HUD)│                 │     CLI Entrypoint)         │
  └──────────────────────┘              └────────────────────┘                 └─────────────────────┘
               │                                     │                                 │
               └─────────────────────────┼─────────────────────────┘
                                                     ▼
                                   ┌─────────────────────────┐
                                   │           Telemetry               │
                                   │   (Local SQLite DB +              │
                                   │   PyQt6 Log Viewer)               │
                                   └─────────────────────────┘
```


Data Flow: Each simulation tick moves through 7 phases: perception, decision, movement, trade matching,
execution, foraging, and housekeeping       8   . Agent states (positions, inventories, utilities) → DecisionSystem
(compute neighbor surplus, form pairings) → TradeSystem (execute barter or money exchange) →
MovementSystem (agents move toward targets) → ForageSystem (collect resources) → Housekeeping. At each
step, the Pygame renderer visualizes the current state with agents (color-coded by utility type 9 ) and
optional target arrows. Simultaneously, all events (trades, preferences, tick states) are logged to SQLite 10




                                                          2
 3   . The GUI allows parameter input and toggles (pause, reset, arrows, etc.), while the CLI ( main.py ) can
load scenarios in headless mode.


4. Risk Radar (top concerns)

      - R-01: Pairing vs Money Consistency. Description: Currently, the DecisionSystem still ranks potential
        trade partners using barter-only surplus (ignoring money) 6 . In a money or mixed regime, this can
        select suboptimal pairs, obscuring the liquidity advantage of money. Impact: High (misleading
        educational outcomes) | Likelihood: Medium. Mitigation: Rework neighbor-scoring to use money-
        aware surplus when money is enabled 6 .
      - R-02: Documentation & Guidance Gaps. Description: Several user guides referenced in README are
        not yet written (e.g. user_guide_money.md, regime_comparison.md) 11 . This may confuse new
        users and instructors. Impact: Medium | Likelihood: High. Mitigation: Prioritize writing or stubbing
        missing guides and fixing broken links before release 11 . Provide in-app help text (the GUI has built-
        in tooltips).
      - R-03: Performance and Scalability. Description: If many agents or high tick counts are used, the
        simulation might slow or exceed 30 FPS. The pairing system is O(P) per tick (P = paired count), and
        spatial indexing is used for efficiency 12 . Impact: High | Likelihood: Medium. Mitigation: Rigorously
        benchmark with 500+ agents. The code is optimized (spatial indexing, commitment of pairs to
        reduce repeated work 13 ). If needed, implement further partitioning or LOD rendering.
      - R-04: System Complexity for Learners. Description: The growing number of parameters (multiple
        utility types, exchange regimes, modes) may overwhelm new users. Impact: Medium | Likelihood:
        Medium. Mitigation: Provide sensible defaults and tutorial scenarios. Emphasize core concepts first
        (e.g. start with barter only, one utility type).
      - R-05: User Interface Learning Curve. Description: The GUI and scenario builder offer many options.
        Users might struggle with creating valid scenarios or interpreting HUD details (arrows, labels).
        Impact: Medium | Likelihood: Medium. Mitigation: Create a guided “foundational” demo (with
        comments, as planned) and quick-reference guide. Use clear, consistent UI icons (already done) and
        comprehensive validation errors.

(Note: The primary architectural misalignment is R-01, which directly affects teaching clarity 14 . Other risks are
mitigated by planned documentation and optimization.)


5. Assumptions & Validation

      - A-01: SQLite Logging Advantages. We assume that embedding a local database (SQLite) significantly
        improves reproducibility and analysis. Counterpoint: DB overhead might complicate simplicity.
        Validation: Empirical comparisons show ~99% log-size reduction and sub-second queries 3 , so the
        benefit outweighs costs. Experiment: Compare running time and log analysis speed with/without
        SQLite logging; adjust logging granularity if needed.


      - A-02: Self-Contained Toolchain Works. We assume Python 3.11 + PyQt6 + Pygame can be packaged for
        educators. Counterpoint: Cross-platform install issues (C++ dependencies) might hinder adoption.
        Validation: The README and install instructions have been tested on Linux/Mac/Windows. The core
        only requires standard Python libs (no external API calls) 15 . Experiment: Create platform-specific
        installers (e.g. with PyInstaller) and verify on target systems.




                                                        3
    - A-03: Additional Utilities Aid Learning. We assume adding Quadratic, Translog, and Stone–Geary
      utilities helps pedagogy without undue confusion. Counterpoint: Too many choices might overwhelm
      students. Validation: In solo testing, each utility type produced clearly distinct patterns (e.g. Stone–
      Geary enforces subsistence) 16 . Experiment: A/B test with learners: compare understanding using
      the three classic types vs the extended set.


    - A-04: Visual-First Development is Beneficial. We assume that seeing immediate results leads to better
      intuition. Counterpoint: Visual focus could trade off engineering rigour. Validation: The 316+ test suite
        2   and quantitative outputs ensure correctness despite visual complexity. Experiment: Elicit
      feedback from educators on simulation clarity vs debug complexity.




Phase 2: Design Contracts

6. Domain Model (core entities + relationships)

    - Agent: Has id , pos (x,y), and an Inventory of goods (A, B) and money (M). Each agent holds a
      Utility function (with type and parameters) and dynamic quotes for possible trades 17 . Runtime
     fields track pairing ( paired_with_id ), forage targets, and cash lambda_money .
    - Inventory: Records resource counts. Extended to include money (Inventory.M) and agent-specific λ
      (marginal utility of money).
    - Utility: Encapsulates the agent’s preference (CES, linear, quadratic, etc.) and computes utility,
      marginal utilities, and reservation prices. A factory ( create_utility ) instantiates the right
      subclass.
    - Grid/Resources: The Grid holds resource amounts at each cell. Agents move on this grid and
      harvest. Grid size = N×N, seeded at start.
    - ScenarioConfig: Represents a scenario (schema version, N, agent count, initial inventories, utility
      mix, system params, mode schedule) 18 . Validated via scenario.validate() 7 .
    - Simulation: Manages the overall state each tick (agents list, grid, systems, RNG, telemetry).
    - TelemetryManager: Manages SQLite tables for runs, agent_snapshots, trades, decisions, etc. It
      records every tick’s state and events.
    - GUI/CLI Components: The launcher and renderer integrate with the engine but hold no business
      logic.

7. Core Interfaces (key APIs)

    - Simulation API: The Simulation class ( src/vmt_engine/simulation.py ) is the main
     entrypoint for a run. Notable methods: __init__(scenario, seed) , which initializes Grid and
     Agents; and step() which executes the 7-phase tick. User scripts call sim.run(max_steps) or
      use the GUI.
    - Scenario Loader: load_scenario(path) in src/scenarios/loader.py parses YAML into a
      ScenarioConfig . It raises clear errors on missing fields     7   .
    - Telemetry: The TelemetryManager API allows logging events (e.g.
      telemetry.log_trade(...) , log_tick_state(...) ) during the simulation. The log viewer
      uses Qt models to query these.
    - GUI Launcher: Provides methods to list scenario files, load/edit parameters via forms, and start/stop
      simulations. (See src/vmt_launcher/ ).




                                                     4
    - Scenario Builder CLI: vmt_tools.scenario_builder.generate_scenario(...)
      programmatically creates valid scenarios given high-level inputs 19 . It enforces parameter
      constraints and utility setup.
    - Utility Factory: create_utility(type, params) in src/vmt_engine/econ/utility.py
     returns an object with methods u() and mu() . All utility interfaces are unified under this factory.

8. Error Handling Strategy

    - Input Validation: Scenario YAMLs are validated on load: missing keys or wrong types produce a
       ValueError with a message 7 . Example: supplying an unknown utility type or invalid numeric
      range immediately triggers an exception.
    - State Invariants: Agents perform defensive checks (e.g. Agent.__post_init__ raises on
     negative id or non-positive move budget 20 ). These prevent invalid runtime states.
    - Runtime Errors: In the GUI, unhandled exceptions bubble up to a Qt message box (currently). No
      network or async operations exist, so errors are locally trapped or crash the sim loop with logs.
    - Debug Logging: All major operations (trades, pairing events, mode changes) are logged in telemetry
      for post-mortem inspection. We rely on the extensive test suite to catch logic errors.

9. Testing Strategy Outline

    - Automated Tests: Over 300 unit and integration tests cover core functionality 2 . These include
      tests for pairing algorithms, money trading (generic matching), utility computations, and foraging
      behavior. For example, test_money_phase1_integration.py verifies that quasilinear utility yields correct
      trades.
    - Determinism Checks: CI runs identical scenarios multiple times to ensure repeatability (same final
      inventories) given the same seed.
    - Performance Benchmarks: Specific tests measure ticks-per-second (TPS) with increasing agent
      counts. The O(N) pairing algorithm and spatial index should keep performance acceptable.
    - Visual Regression (Planned): Though not fully automated, key visual features (like agent color
      mapping and arrow toggles) will be tested via user review.
    - Coverage Goals: We aim for >90% code coverage. Tests are run via pytest , and new features (e.g.
     new exchange regimes) are accompanied by new tests.

10. Integration Points & Dependencies

    - Core Libraries: Python 3.11+, PyQt6 (GUI framework) 21 , Pygame 2.5+ (visualization engine),
      NumPy (numerical calculations). All rendering and logic run locally – no remote APIs.
    - Database: SQLite is embedded for telemetry 10 . This is not an “external service” but an internal file-
      based DB. It satisfies the original “no external dependencies” requirement 15 while enabling robust
      logging.
    - Dev Tools: Black and Ruff for formatting/linting, Mypy for type checking, PyTest for testing (all
      included in the requirements-dev.txt ). These enforce code quality but are not required for end-
      users.
    - Platforms: Windows, macOS, and Linux builds are supported. (PyQt6 ensures broad compatibility.)
      No GPU or network is required.
    - No External APIs: The tool is fully offline. No web services, no cloud, no streaming data – all
      simulation data is generated or saved locally 15 .




                                                      5
Phase 3: Implementation Readiness

11. Directory Structure & File Plan

The project layout (see README 22 ) organizes code and data clearly. For example:



  vmt-dev/
  ├── src/
  │    ├── vmt_engine/              # Core simulation engine (grid, agents, systems)
  │    ├── vmt_launcher/            # PyQt6-based GUI application
  │    ├── vmt_pygame/              # Pygame renderer
  │    ├── vmt_tools/               # Scenario builder and utilities
  │    └── scenarios/               # Common code for scenario schema and loading
  ├── scenarios/                    # Pre-built YAML scenarios (demos, tutorials)
  ├── tests/                        # pytest test suite
  ├── docs/                         # Documentation (overview, manual, guides)
  ├── launcher.py                   # GUI entry point (runs vmt_launcher)
  └── main.py                       # CLI entry point (runs simulations headlessly)


Each folder contains relevant modules (e.g. matching.py , trading.py in vmt_engine/systems/ ).
The scenarios/ top-level holds example configs (including demo files added for the money module). This
structure was enforced after refactoring to align with initial plans.


12. Tooling & Quality Setup

      - Code Formatting: Black is used project-wide for consistent style. A pre-commit hook or CI check
        auto-formats code on each commit.
      - Linting/Static Analysis: Ruff (Flake8/Mypy) ensures no lint errors. Mypy is configured for full type
        coverage (we strive for 100% type-safe code).
      - Testing: PyTest runs on every push. Coverage reports help identify gaps. Tests are grouped (unit,
        integration, performance) and tagged so critical paths are always validated.
      - CI/CD: A GitHub Actions workflow runs tests, linters, and builds. Documentation builds (MkDocs or
        Sphinx) are validated for link consistency.
      - Release Management: We follow Semantic Versioning. After polishing, the project will be tagged
        v0.0.1 (pre-release) with a CHANGELOG. (Badges and README have been updated to reflect PyQt6
        and the new version 23 .)

14. Implementation Roadmap (Next Steps)

The immediate plan is to close the gaps between the current code and the original vision. Key milestones:


      - Phase A (Current) – Finalize Barter+Money Engine:
      - Fix Pairing Metric: Adjust the DecisionSystem to use money-aware surplus ranking when the regime
        is money_only or mixed 6 24 . This ensures demonstrable liquidity benefits.
      - Complete Mixed Regime Logic: Implement the intended gating for "mixed_liquidity_gated"
       (currently it silently falls back to barter). Add tests for this regime.



                                                          6
     - User Documentation: Write or stub the missing guides referenced in README: User Guide for Money
       System, Regime Comparison, Technical Money Implementation, Quick Reference, and Scenario Generator
       Guide 11 . These will aid instructors and developers.
     - Release Prep: Switch versioning to v0.0.1 (as per the review recommendation) 23 . Harmonize
       badges and announce a pre-release. Ensure all dependencies (PyQt6, Pygame, etc.) are up to date.

     - UI/UX Polish: Refine the scenario builder forms for clarity, add helpful default values, and ensure
       any new money parameters have on-screen documentation. Update demos to highlight new
       features (e.g. demo_02_barter_vs_money.yaml ).


     - Phase B (Money Enhancements):


     - Advanced Money Mechanisms: Build on the quasilinear foundation to support variable money
       scale, endogenous λ updates (Bucklin’s algorithm), and toggle earn_money_enabled . Integrate
       findings from Money System Phases 3–6 (e.g. liquidity zones, borrower/lender dynamics).
     - Analytics Extensions: Enhance the log viewer with money-specific analytics (histograms of money
       balances, agent λ trajectories). Ensure CSV exports include all money fields.

     - Pedagogical Demonstrations: Create educational scenarios (with commentary) that contrast barter
       vs money (e.g. demo highlighting welfare improvements).


     - Phase C (Local Market Mechanisms):


     - Introduce Posted-Price/Auction Markets: As noted in the architecture review, layer on simple
       market mechanisms as alternative “Bargain” modules 25 . For example, implement a clearinghouse
       where agents submit bids/asks and the system finds equilibrium prices. This will be a plug-in to the
       existing engine (with minimal disruption to the 7-phase loop).

     - Compare Regimes: Develop a regime comparison guide demonstrating results (prices, surplus) under
       bilateral vs market trading. Add metrics to telemetry for market outcomes.


     - Long-Term Roadmap (Phases D–F): Following the strategic plan 26 , subsequent extensions could
       include:


     - Production/General Equilibrium: Add “firm” agents, labor-goods markets, and price adjustment
       dynamics.
     - Game Theory & Information: Modules for auctions, repeated games, and asymmetric information
       scenarios.
     - Advanced Curriculum: Integrate modules for mechanism design (e.g. auctions/voting) and
       behavioral heterogeneity.

By iterating through these steps, VMT will incrementally fulfill the original vision. Short-term focus is on
robustness and educational completeness (money fixes, documentation, versioning), then expanding the
feature set in planned phases. All work maintains the core architecture’s determinism and visualization-first
ethos.


Sources: Current code and docs from vmt-dev    4   2       6   27   25   7   guided this assessment and plan.




                                                       7
 1    2    3   4    5    9    12   1_project_overview.md
https://github.com/cmfunderburk/vmt-dev/blob/2ad8c592f6918ee985a904830644c2713add7bda/docs/1_project_overview.md

 6   10   11   14   15   16   21   23   24   25   27   2025-10-21_alignment_vs_initial_plan.md
https://github.com/cmfunderburk/vmt-dev/blob/2ad8c592f6918ee985a904830644c2713add7bda/docs/REVIEW/
2025-10-21_alignment_vs_initial_plan.md

 7   18   loader.py
https://github.com/cmfunderburk/vmt-dev/blob/2ad8c592f6918ee985a904830644c2713add7bda/src/scenarios/loader.py

 8   2025-10-21_architecture_and_docs_review.md
https://github.com/cmfunderburk/vmt-dev/blob/2ad8c592f6918ee985a904830644c2713add7bda/docs/REVIEW/
2025-10-21_architecture_and_docs_review.md

13   CHANGELOG.md
https://github.com/cmfunderburk/vmt-dev/blob/2ad8c592f6918ee985a904830644c2713add7bda/CHANGELOG.md

17   20   agent.py
https://github.com/cmfunderburk/vmt-dev/blob/2ad8c592f6918ee985a904830644c2713add7bda/src/vmt_engine/core/agent.py

19   scenario_builder.py
https://github.com/cmfunderburk/vmt-dev/blob/2ad8c592f6918ee985a904830644c2713add7bda/src/vmt_tools/
scenario_builder.py

22   README.md
https://github.com/cmfunderburk/vmt-dev/blob/2ad8c592f6918ee985a904830644c2713add7bda/README.md

26   3_strategic_roadmap.md
https://github.com/cmfunderburk/vmt-dev/blob/2ad8c592f6918ee985a904830644c2713add7bda/docs/3_strategic_roadmap.md




                                                                    8

