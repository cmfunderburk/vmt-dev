# VMT-DEV Mastery: A Self-Study Program

**Target Audience:** PhD-level economist, proficient in Python, new to the `vmt-dev` codebase.
**Goal:** Achieve full productivity within the `vmt-dev` repository, enabling implementation of new protocols, rigorous experimentation, deterministic validation, and high-quality contributions.
**Estimated Time:** 2-3 Weeks (Full-time equivalent)

---

## 1. Executive Overview

### What is VMT-DEV?

VMT (Visualizing Microeconomic Theory) is a spatial agent-based simulation platform designed to investigate how market phenomena **emerge** from the micro-level interactions of autonomous agents governed by explicit institutional rules. Unlike traditional economic models that often assume equilibrium and price-taking behavior, VMT allows researchers and students to explore the conditions under which different market structures and outcomes arise from fundamental principles. It provides a virtual laboratory for comparative institutional analysis, focusing on how different protocols for search, matching, and bargaining shape economic dynamics in a spatial context.

### Core Architectural Principles & Invariants

Mastery of VMT requires strict adherence to its core principles, designed for scientific validity and reproducibility:

1.  **Determinism**: Non-negotiable. Given the same initial configuration (scenario file) and random seed, every simulation run MUST produce identical, bit-for-bit results. This necessitates:
    * **Seeded RNG ONLY**: Use only the provided seeded random number generators (`self.rng` in agents, `world.rng` in the engine). Never use global `random`, `numpy.random`, time-based seeds, or any unseeded source.
    * **Ordered Iteration**: Never iterate over unordered collections (sets, dicts) without explicit sorting, typically by agent ID (`sorted(agents, key=lambda a: a.id)`).

2.  **Protocol → Effect → State Pattern**: The fundamental architectural pattern. Protocols make decisions based on immutable state snapshots and return declarative `Effects` representing *intended* actions. The engine's `Systems` then validate and apply these effects deterministically during specific phase transitions.
    * **Read-Only WorldView**: Protocols receive immutable `WorldView` objects (`src/vmt_engine/protocols/context.py`) providing a snapshot of the simulation state. They cannot directly modify the world.
    * **Effects-Only State Changes**: All modifications to the simulation state (agent positions, inventories, grid resources) MUST occur exclusively through the application of `Effect` objects (`src/vmt_engine/protocols/base.py`) by the engine's systems. Direct state mutation within protocols is strictly forbidden.

3.  **Seven-Phase Tick Cycle**: Each discrete time step (`tick`) follows an invariant sequence of seven phases, ensuring consistent order of operations and separation of decision-making from state updates. See `src/vmt_engine/simulation.py` and `docs/2_technical_manual.md`.
    * Phase 0: Resource Regeneration
    * Phase 1: Agent Movement Decisions → `MoveEffect`s
    * Phase 2: Movement Execution
    * Phase 3: Foraging/Mining Decisions → `ResourceEffect`s (e.g., `Harvest`)
    * Phase 4: Trading Negotiations → `TradeEffect`s, `Unpair` effects
    * Phase 5: Trade Execution & Inventory Updates
    * Phase 6: Housekeeping (Quote Refresh, Telemetry Logging)

4.  **Typing Authority**: Strict adherence to type contracts defined in `docs/4_typing_overview.md` is mandatory. Key types include:
    * `int` for Agent IDs, Ticks, Quantities (Inventories, Resources, ΔA, ΔB, ΔM), Spatial parameters (N, radii, budgets).
    * `float` for Prices, Utility values, Lambda_money.
    * `(int, int)` tuples for Positions/Coords.

### Repository Tour

* **`src/vmt_engine/`**: The core simulation engine.
    * `core/`: Fundamental data structures (Agent, Grid, Inventory, Position, SpatialIndex).
    * `econ/`: Economic logic, primarily Utility function implementations.
    * `protocols/`: Institutional rules – search, matching, bargaining algorithms. Contains `base.py` (Effects, abstract protocols) and `registry.py` (protocol discovery).
    * `systems/`: Implementations of the 7 tick phases (Perception, Decision, Movement, Trading, Foraging, Housekeeping).
    * `simulation.py`: Orchestrates the tick cycle and manages overall state.
* **`src/telemetry/`**: SQLite-based logging system for simulation data.
    * `database.py`: Schema definition.
    * `db_loggers.py`: `TelemetryManager` class for writing logs.
* **`src/scenarios/`**: Python code related to scenarios.
    * `schema.py`: Defines the structure and validation rules for YAML scenario files.
    * `loader.py`: Parses YAML files into configuration objects.
    * `protocol_factory.py`: Instantiates protocols based on names in YAML/CLI.
* **`scenarios/`**: User-facing YAML files defining simulation setups.
    * `demos/`: Pedagogical examples.
    * `test/`: Minimal scenarios used in automated tests.
* **`tests/`**: Pytest suite ensuring correctness, determinism, and economic properties. Key files test integration (`test_*_integration.py`), specific utilities (`test_utility_*.py`), protocols (`test_random_*.py`), and core components (`test_core_*.py`).
* **`docs/`**: Comprehensive documentation (overview, technical manual, typing spec, onboarding, protocol plans).
* **`scripts/`**: Utility scripts for running headless simulations, comparing telemetry, benchmarking.
* **`src/vmt_launcher/` & `src/vmt_log_viewer/`**: PyQt6 applications for GUI simulation launching and telemetry inspection.

---

## 2. Mastery Curriculum

This curriculum is designed to be completed sequentially. Each module builds upon the previous ones.

### Module A: Orientation and Quickstart (Estimated Time: 2-4 hours)

**Prerequisites:** Python 3.11 environment set up (see `docs/onboarding/1_environment_setup.md`).

**Learning Objectives:**
* Successfully install dependencies and run the test suite.
* Execute demo scenarios using both the GUI launcher and headless scripts.
* Understand the basic workflow of running a simulation and inspecting its output.
* Internalize the critical importance of determinism.

**Reading:**
1.  `README.md` (Project overview and quick start)
2.  `docs/onboarding/1_environment_setup.md` (If setup needed)
3.  `docs/onboarding/2_quickstart.md` (Running simulations)
4.  `.cursor/rules/00_determinism.mdc` (Determinism rules - internalize these!)

**Guided Reading Prompts:**
* What is the primary goal of the VMT project?
* Why is determinism non-negotiable? What are the three mandatory practices for ensuring it?
* What command runs the GUI? What command runs a scenario headlessly?

**Lab:**
* **Lab 1: Environment Setup and First Run** (See Hands-on Labs section below)

**Common Pitfalls:**
* Forgetting to activate the virtual environment.
* Using global `random` instead of the provided seeded RNGs (violates Determinism Rule #1).
* Ignoring test failures. The suite must pass cleanly.

**Acceptance Criteria / Evidence of Mastery:**
* `pytest -q` runs successfully with all tests passing.
* Successfully ran `scenarios/demos/demo_01_foundational_barter.yaml` via GUI (`launcher.py`) and CLI (`scripts/run_headless.py`), generating log files.
* Opened the generated `.sqlite` log file using the log viewer (`view_logs.py`).
* Can explain *why* using an unseeded RNG would invalidate simulation results in VMT.

### Module B: Core Engine and Phase System (Estimated Time: 4-6 hours)

**Prerequisites:** Module A completed.

**Learning Objectives:**
* Understand the role of `Simulation`, `Agent`, `Grid`, and `State` objects (`src/vmt_engine/core/`).
* Explain the 7-phase tick cycle and the purpose of each phase.
* Trace the `Protocol → Effect → State` pattern through a single tick.
* Understand how `Systems` (`src/vmt_engine/systems/`) implement phase logic and apply Effects.
* Recognize violations of the Effects-only state mutation rule.

**Reading:**
1.  `docs/onboarding/3_architecture_overview.md` (Architecture summary)
2.  `docs/2_technical_manual.md` (Sections on Core Architecture, 7-Phase Tick Cycle)
3.  `src/vmt_engine/simulation.py` (Focus on `__init__` and `step` methods)
4.  `src/vmt_engine/protocols/base.py` (Definition of `Effect` types)
5.  `src/vmt_engine/systems/base.py` and browse implementations in `src/vmt_engine/systems/` (e.g., `movement.py`, `foraging.py`).
6.  `.cursor/rules/01_vmt_architecture.mdc` (Architecture rules)

**Guided Reading Prompts:**
* Where is the main simulation loop defined? What method executes a single tick?
* Which phases involve agent decision-making vs. state updates?
* Find an example of a System applying an Effect to change agent state (e.g., `MovementSystem` applying `MoveEffect`).
* How does the architecture prevent protocols from directly modifying the simulation state?

**Exercises:**
1.  **Trace a Tick:** Manually trace the execution flow for `tick=0` of `scenarios/demos/foundational_barter_demo.yaml`. Identify which System runs in each phase and what state changes occur.
2.  **Identify State:** List the core components of the simulation state managed by the `Simulation` class.

**Lab:**
* **Lab 2: Determinism Check** (See Hands-on Labs section below)
* **Lab 3: Reading the Engine Loop** (See Hands-on Labs section below)

**Common Pitfalls:**
* Confusing Effects (intents) with direct actions.
* Misunderstanding the strict phase ordering.
* Trying to modify state directly within a protocol or outside a System's `execute` method.

**Acceptance Criteria / Evidence of Mastery:**
* Can accurately describe the 7 phases and their order.
* Can explain the `Protocol → Effect → State` flow with code examples.
* Successfully completed Labs 2 and 3, demonstrating understanding of determinism and the engine loop.
* Can identify code snippets that violate the Effects-only state mutation rule.

### Module C: Protocols In Depth (Estimated Time: 6-8 hours)

**Prerequisites:** Module B completed.

**Learning Objectives:**
* Understand the roles of Search, Matching, and Bargaining protocols.
* Explain how protocols use the immutable `WorldView`.
* Analyze the implementation of the legacy protocols (`LegacySearchProtocol`, `LegacyMatchingProtocol`, `LegacyBargainingProtocol`).
* Understand how economic concepts (e.g., surplus, MRS, discounting) are implemented in protocols.
* Distinguish between Barter-only and Money-aware logic within protocols.
* Understand the protocol registry and how protocols are selected/configured.

**Reading:**
1.  `docs/onboarding/5_protocol_development_guide.md` (Protocol implementation basics)
2.  `docs/protocols_10-27/README.md` (Protocol roadmap overview)
3.  `src/vmt_engine/protocols/base.py` (Abstract protocol classes, Effect types)
4.  `src/vmt_engine/protocols/context.py` (`WorldView` definition)
5.  `src/vmt_engine/protocols/search/legacy.py`
6.  `src/vmt_engine/protocols/matching/legacy.py`
7.  `src/vmt_engine/protocols/bargaining/legacy.py`
8.  `src/vmt_engine/systems/matching.py` (Helper functions like `compute_surplus`, `estimate_money_aware_surplus`, `find_compensating_block_generic`)
9.  `src/vmt_engine/protocols/registry.py` & `src/scenarios/protocol_factory.py`

**Guided Reading Prompts:**
* What information does `WorldView` provide to a protocol? Why is it immutable?
* How does `LegacySearchProtocol` calculate preference scores? What does `beta` represent?
* Explain the three passes of the `LegacyMatchingProtocol`.
* What is the "compensating block" search in `LegacyBargainingProtocol` trying to find? Why is rounding important (`floor(price * dA + 0.5)`)?
* How does `estimate_money_aware_surplus` differ from `compute_surplus`? When is each used?
* How are protocols specified in a scenario YAML file and loaded by the simulation?

**Exercises:**
1.  **Protocol Inputs/Outputs:** For each legacy protocol, identify its primary input (`WorldView` or `ProtocolContext`) and the main `Effect` types it returns.
2.  **Money vs. Barter:** Find the conditional logic in `LegacySearchProtocol` or `LegacyBargainingProtocol` (or helpers they call in `systems/matching.py`) that handles different `exchange_regime` values.

**Lab:**
* **Lab 4: Implement a Minimal Protocol Variant** (See Hands-on Labs section below)

**Common Pitfalls:**
* Attempting to access mutable simulation state from within a protocol.
* Forgetting to handle different `exchange_regime` settings.
* Incorrectly calculating surplus or discounted surplus.
* Violating determinism through unordered iteration or unseeded randomness.

**Acceptance Criteria / Evidence of Mastery:**
* Can explain the purpose and basic algorithm of each legacy protocol.
* Can identify the key economic calculation within each protocol (e.g., discounted surplus, compensating block search).
* Completed Lab 4, demonstrating the ability to create a new protocol stub that adheres to the architecture.
* Understands how `ProtocolRegistry` and `protocol_factory` work together to load protocols.

### Module D: Scenarios and Typing (Estimated Time: 3-5 hours)

**Prerequisites:** Module C completed.

**Learning Objectives:**
* Understand the structure and validation rules of scenario YAML files.
* Know how to configure different utility functions, initial inventories, and simulation parameters.
* Master the VMT type system, especially distinctions between `int` and `float` usage.
* Understand how seeding works and its role in determinism.
* Learn how to configure protocols via YAML.

**Reading:**
1.  `docs/onboarding/7_scenarios_and_types.md` (Scenario and typing summary)
2.  `docs/4_typing_overview.md` (Authoritative typing spec)
3.  `src/scenarios/schema.py` (Dataclass definitions for scenario structure and validation logic)
4.  `docs/structures/comprehensive_scenario_template.yaml` (Detailed parameter reference)
5.  `docs/structures/minimal_working_example.yaml` & `docs/structures/money_example.yaml` (Basic templates)
6.  Browse examples in `scenarios/demos/` and `scenarios/test/`.

**Guided Reading Prompts:**
* Where are the allowed values for `exchange_regime` defined and validated?
* What is the difference between `params.lambda_money` and `initial_inventories.lambda_money`? When would you use the latter?
* According to the typing spec, should `dA_max` be an `int` or `float`? What about `spread`?
* How do you configure a scenario to use the `RandomWalkSearch` protocol instead of the default?
* What validation rule applies specifically to the `StoneGeary` utility function regarding initial inventories?

**Exercises:**
1.  **Create a Scenario:** Create a new YAML file for a small simulation (e.g., 2 agents, 5x5 grid) with `Linear` utility for both agents but different `vA`/`vB` parameters. Use `money_only` regime and specify per-agent `lambda_money`. Ensure it loads without validation errors.
2.  **Type Check:** Review `src/vmt_engine/core/agent.py` and identify which attributes must be integers according to `docs/4_typing_overview.md`.

**Lab:**
* **Lab 5: Add a New Scenario Variant** (See Hands-on Labs section below)

**Common Pitfalls:**
* Using floats for integer quantities (e.g., inventories, grid size).
* Forgetting required fields in the YAML file.
* Utility mix weights not summing to 1.0.
* Stone-Geary initial inventories below subsistence levels.
* Incorrect protocol names in the YAML configuration.

**Acceptance Criteria / Evidence of Mastery:**
* Can successfully create and validate a new scenario YAML file from scratch, including mixed utilities and money parameters.
* Can correctly identify the required data type for any given parameter based on `docs/4_typing_overview.md`.
* Completed Lab 5, demonstrating scenario creation and parameter tuning.
* Can explain how the `--seed` argument ensures deterministic agent placement and utility assignment.

### Module E: Telemetry and Experimentation (Estimated Time: 4-6 hours)

**Prerequisites:** Module D completed.

**Learning Objectives:**
* Understand the structure of the SQLite telemetry database (`logs/telemetry.db`).
* Know how to use the interactive Log Viewer (`view_logs.py`) to inspect simulation runs.
* Use analysis scripts (`scripts/`) to compare runs and extract metrics.
* Perform determinism checks using `scripts/compare_telemetry_snapshots.py`.
* Configure logging levels (`LogConfig`).
* Understand how to benchmark performance using `scripts/benchmark_performance.py`.

**Reading:**
1.  `docs/onboarding/8_telemetry_and_analysis.md` (Telemetry overview)
2.  `docs/4_typing_overview.md` (Section 6: Telemetry Schema)
3.  `src/telemetry/database.py` (Schema definition)
4.  `src/telemetry/config.py` (`LogConfig` and `LogLevel`)
5.  Browse `scripts/` (Especially `compare_telemetry_snapshots.py` and `benchmark_performance.py`)
6.  `src/vmt_log_viewer/viewer.py` (Skim UI layout) & `src/vmt_log_viewer/queries.py` (SQL queries used by viewer)

**Guided Reading Prompts:**
* Which table stores the state of each agent at every logged tick? What key information is stored there?
* Which table records successful trades? What information distinguishes monetary from barter trades?
* How can you run a simulation without generating a large telemetry database (e.g., for quick tests)?
* What does `scripts/compare_telemetry_snapshots.py` actually compare to verify determinism? (Hint: Check the script's code).
* What is the difference between `LogLevel.STANDARD` and `LogLevel.DEBUG`?

**Exercises:**
1.  **Log Viewer Exploration:** Run `scenarios/demos/demo_03_mixed_regime.yaml` headlessly for 50 ticks. Use the Log Viewer to:
    * Find the tick where the first trade occurred.
    * Identify the pair types (`exchange_pair_type`) of trades that happened. Were both barter and monetary trades present?
    * Track the inventory of `agent_id=0` over the first 20 ticks.
2.  **Telemetry Query:** Write a SQL query to find the average price (`price`) of all `A<->M` trades in a specific run (`run_id=1`, assuming it exists in your `logs/telemetry.db`).

**Lab:**
* **Lab 6: Telemetry Drill** (See Hands-on Labs section below)

**Common Pitfalls:**
* Trying to analyze complex behavior directly from the visualization instead of using telemetry data.
* Forgetting to pass the `--seed` argument when trying to reproduce runs.
* Misinterpreting log levels (e.g., expecting detailed trade attempts without using `DEBUG`).

**Acceptance Criteria / Evidence of Mastery:**
* Can navigate the Log Viewer effectively to inspect agent states, trades, and decisions across ticks.
* Can use `scripts/compare_telemetry_snapshots.py` to confirm or deny deterministic equivalence between two runs.
* Can use `scripts/benchmark_performance.py` to measure the performance of a scenario.
* Completed Lab 6, demonstrating the ability to use telemetry comparison for validation.
* Can write basic SQL queries against the telemetry database to extract key metrics.

### Module F: Advanced Topics and Extensions (Estimated Time: 5-7 hours)

**Prerequisites:** Module E completed.

**Learning Objectives:**
* Understand mode scheduling (`ModeSchedule`) for temporal control of activities.
* Analyze the implementation details of quote generation (`src/vmt_engine/systems/quotes.py`) and its connection to utility functions.
* Explore the different utility function implementations (`src/vmt_engine/econ/utility.py`) and their economic implications (e.g., satiation in `UQuadratic`, subsistence in `UStoneGeary`).
* Understand performance considerations and basic profiling techniques.
* Identify potential areas for extension and contribution.

**Reading:**
1.  `src/scenarios/schema.py` (Review `ModeSchedule` dataclass and validation)
2.  `src/vmt_engine/simulation.py` (Review `_should_execute_system` and mode handling logic)
3.  `src/vmt_engine/systems/quotes.py` (How reservation bounds map to quotes, including spread and money scaling)
4.  `src/vmt_engine/econ/utility.py` (Detailed review of `UQuadratic`, `UTranslog`, `UStoneGeary` implementations)
5.  `docs/onboarding/9_performance_guide.md` (Performance tips and benchmarking)
6.  `docs/3_enhancement_backlog.md` (Ideas for future improvements)
7.  `tests/test_mode_integration.py`, `tests/test_utility_*.py` (Examples of testing advanced features)

**Guided Reading Prompts:**
* How does `ModeSchedule` determine whether the current tick is for 'forage' or 'trade'? How does this interact with `exchange_regime`?
* Explain the formula used in `compute_quotes` to calculate `ask_A_in_M`. How does `lambda_money` affect this? How does `money_scale` affect this?
* Compare the `reservation_bounds_A_in_B` methods for `UQuadratic` and `UStoneGeary`. How do they handle edge cases like satiation or subsistence?
* What are some potential performance bottlenecks mentioned in the performance guide?

**Exercises:**
1.  **Mode Scheduling Scenario:** Modify `scenarios/demos/demo_04_mode_schedule.yaml` to have very short trade periods (e.g., 2 ticks) and long forage periods (e.g., 20 ticks). Run it and observe the impact on trading frequency using the Log Viewer.
2.  **Utility Deep Dive:** Choose one of the advanced utility functions (`UQuadratic`, `UTranslog`, `UStoneGeary`). Read its implementation and corresponding test file (`tests/test_utility_*.py`). Write a brief summary (2-3 sentences) of its key economic behavior and how the implementation captures it.

**Lab:**
* Revisit **Lab 5**, but this time, add a `ModeSchedule` to your custom scenario. Verify its effect using `scripts/plot_mode_timeline.py`.

**Common Pitfalls:**
* Misunderstanding the interaction between `ModeSchedule` (temporal control) and `exchange_regime` (type control).
* Incorrectly interpreting quote calculations, especially regarding `lambda_money` and `money_scale`.
* Introducing performance regressions by adding computationally expensive logic inside tight loops (e.g., within protocol execution).

**Acceptance Criteria / Evidence of Mastery:**
* Can configure and explain the behavior of `ModeSchedule`.
* Can explain how quotes are derived from utility functions, including the role of spread, lambda, and money scale.
* Understands the distinct economic behaviors modeled by `UQuadratic`, `UTranslog`, and `UStoneGeary`.
* Can use `scripts/benchmark_performance.py` and interpret its output.
* Can propose a simple, valid extension to the VMT engine (e.g., a new simple protocol, a new telemetry metric) that respects the core architectural principles.

---

## 3. Hands-on Labs

Complete these labs as part of the corresponding modules.

### Lab 1: Environment Setup and First Run (Module A)

**Goal:** Verify installation and run a basic simulation headlessly.

**Steps:**
1.  Navigate to the repository root in your terminal.
2.  Create and activate the Python virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the test suite to confirm installation:
    ```bash
    pytest -q
    ```
    *(Expected Outcome: All tests should pass)*
5.  Run a demo scenario headlessly with logging enabled:
    ```bash
    python scripts/run_headless.py --scenario scenarios/demos/demo_01_foundational_barter.yaml --seed 42 --max-ticks 50
    ```
    *(Expected Outcome: Simulation runs for 50 ticks, log file created in `logs/telemetry.db`)*
6.  (Optional) Open the generated `logs/telemetry.db` file with the Log Viewer:
    ```bash
    python view_logs.py
    ```
    *(Expected Outcome: Log Viewer opens, allowing inspection of the run)*

**Validation:** All commands execute without error, tests pass, log file is generated.

### Lab 2: Determinism Check (Module B)

**Goal:** Prove that identical seeds produce identical results.

**Steps:**
1.  Run the foundational barter demo headlessly with a specific seed and output directory:
    ```bash
    python scripts/run_headless.py --scenario scenarios/demos/foundational_barter_demo.yaml --seed 123 --max-ticks 20
    ```
    *(This creates `logs/telemetry.db`)*
2.  **Rename the log file** to avoid overwriting:
    ```bash
    # Example command (adjust for your OS/shell):
    mv logs/telemetry.db logs/run_A.db
    ```
3.  Run the **exact same command again**:
    ```bash
    python scripts/run_headless.py --scenario scenarios/demos/foundational_barter_demo.yaml --seed 123 --max-ticks 20
    ```
    *(This creates a new `logs/telemetry.db`)*
4.  Rename the second log file:
    ```bash
    mv logs/telemetry.db logs/run_B.db
    ```
5.  Use the comparison script to verify identical results:
    ```bash
    python scripts/compare_telemetry_snapshots.py logs/run_A.db logs/run_B.db
    ```
    *(Expected Outcome: Script prints "Overall Status: SUCCESS" and confirms identical core data)*
6.  **Introduce a Violation (Optional):**
    * Temporarily modify `src/vmt_engine/systems/movement.py` to use `random.random()` instead of a seeded RNG method for tie-breaking.
    * Repeat steps 1-5.
    * *(Expected Outcome: `compare_telemetry_snapshots.py` should now report "FAILED" due to diverging agent states)*.
    * **Revert the change** you made to restore determinism.

**Validation:** `compare_telemetry_snapshots.py` confirms identical results for the two runs with the same seed.

### Lab 3: Reading the Engine Loop (Module B)

**Goal:** Understand the flow of control and state changes across the 7 phases.

**Steps:**
1.  Open `src/vmt_engine/simulation.py` in your editor.
2.  Focus on the `step()` method.
3.  Add temporary `print()` statements at the beginning of each phase's `System.execute()` method (e.g., in `src/vmt_engine/systems/perception.py`, `decision.py`, `movement.py`, etc.). Example: `print(f"--- Phase X: Executing {self.__class__.__name__} ---")`.
4.  Run a simple scenario for a few ticks:
    ```bash
    python scripts/run_headless.py --scenario scenarios/single_agent_forage.yaml --seed 42 --max-ticks 3
    ```
5.  Observe the printed output in your terminal. Verify that the phases execute in the correct order (Perception → Decision → Movement → Trade → Forage → ResourceRegeneration → Housekeeping) for each tick (0, 1, 2).
6.  **Remove the print statements** after verifying the order.

**Validation:** Output confirms the strict 7-phase execution order for each tick.

### Lab 4: Implement a Minimal Protocol Variant (Module C)

**Goal:** Create a simple new protocol, register it, and configure a scenario to use it, demonstrating adherence to the `Protocol → Effect → State` pattern.

**Steps:**
1.  **Create a New Protocol File:** Create `src/vmt_engine/protocols/search/stationary_search.py`.
2.  **Implement the Protocol:** Define a class `StationarySearch` that inherits from `SearchProtocol`. Implement `name`, `version`, `build_preferences`, and `select_target`.
    * `build_preferences`: Return an empty list `[]`.
    * `select_target`: Return an empty list `[]`. This protocol makes agents do nothing in the search phase.
    * Add the `@register_protocol` decorator (see `src/vmt_engine/protocols/search/random_walk.py` for an example). Use `name="stationary"`.
    ```python
    # src/vmt_engine/protocols/search/stationary_search.py
    from vmt_engine.protocols.base import SearchProtocol, Effect
    from vmt_engine.protocols.context import WorldView
    from vmt_engine.protocols.registry import register_protocol # Import decorator

    @register_protocol(
        category="search",
        name="stationary",
        description="A minimal protocol where agents never select targets.",
        properties=["deterministic", "minimal"],
        complexity="O(1)",
        phase="Lab"
    )
    class StationarySearch(SearchProtocol):
        VERSION = "2025.10.28" # Class-level VERSION

        @property
        def name(self) -> str:
            return "stationary"

        @property
        def version(self) -> str: # Property reads class-level VERSION
            return self.VERSION

        def build_preferences(self, world: WorldView) -> list[tuple]:
            return [] # No preferences

        def select_target(self, world: WorldView) -> list[Effect]:
            return [] # No target selection -> agents stay put
    ```
3.  **Register:** Ensure the new protocol is imported and asserted in `src/vmt_engine/protocols/search/__init__.py`.
    ```python
    # Add near top
    from .stationary_search import StationarySearch
    # Add to __all__
    __all__ = ["LegacySearchProtocol", "RandomWalkSearch", "StationarySearch"]
    # Add assertion at bottom
    assert "stationary" in ProtocolRegistry.list_protocols()['search']
    ```
4.  **Create a Scenario:** Copy `scenarios/single_agent_forage.yaml` to `scenarios/test/stationary_test.yaml`. Modify it to use your new protocol:
    ```yaml
    # scenarios/test/stationary_test.yaml
    schema_version: 1
    name: stationary_search_test
    # ... (keep N, agents, inventories, utilities, resource_seed same)
    params:
      # ... (keep params same)
    search_protocol: "stationary" # Use the new protocol
    # matching_protocol and bargaining_protocol default to legacy
    ```
5.  **Run and Verify:**
    ```bash
    python scripts/run_headless.py --scenario scenarios/test/stationary_test.yaml --seed 42 --max-ticks 10
    ```
    Open `logs/telemetry.db` with the Log Viewer. Check the `agent_snapshots` table.
    *(Expected Outcome: The agent's position (x, y) should remain unchanged across all 10 ticks because the `StationarySearch` protocol never returns a `SetTarget` effect)*.

**Validation:** Scenario loads, simulation runs, and telemetry confirms agents did not move, demonstrating the new protocol was correctly used and followed the architecture (returned no effects, resulting in no state change).

### Lab 5: Add a New Scenario Variant (Module D)

**Goal:** Create a custom scenario, tune parameters, and benchmark it.

**Steps:**
1.  **Copy Existing Scenario:** Duplicate `scenarios/demos/demo_02_barter_vs_money.yaml` to `scenarios/custom/my_high_friction.yaml`. Create the `scenarios/custom/` directory if it doesn't exist.
2.  **Modify Parameters:** Edit `my_high_friction.yaml`:
    * Change the `name` to "High Friction Market".
    * Increase the `params.spread` significantly (e.g., `spread: 0.3`).
    * Increase `params.trade_cooldown_ticks` (e.g., `trade_cooldown_ticks: 15`).
    * Maybe reduce `params.vision_radius` (e.g., `vision_radius: 5`).
    * Ensure `exchange_regime: mixed`.
3.  **Validate:** Run the scenario briefly to ensure it loads and runs without errors:
    ```bash
    python scripts/run_headless.py --scenario scenarios/custom/my_high_friction.yaml --seed 42 --max-ticks 5
    ```
4.  **Benchmark:** Measure the performance of your new scenario:
    ```bash
    python scripts/benchmark_performance.py --scenario scenarios/custom/my_high_friction.yaml --seed 123 --ticks 200
    ```
    *(Expected Outcome: Script runs the simulation for 200 ticks and reports performance metrics like Ticks Per Second)*.
5.  **Analyze (Optional):** Run headlessly for longer (e.g., 200 ticks) and use the Log Viewer to observe how the high friction parameters affect trading frequency and price spreads compared to the original demo scenario.

**Validation:** New scenario loads, runs, benchmarks successfully, and demonstrates altered behavior due to parameter changes.

### Lab 6: Telemetry Drill (Module E)

**Goal:** Use telemetry comparison to validate a code change (or lack thereof).

**Steps:**
1.  **Establish Baseline:**
    * Run a standard scenario headlessly:
        ```bash
        python scripts/run_headless.py --scenario scenarios/demos/demo_03_mixed_regime.yaml --seed 77 --max-ticks 30
        ```
    * Rename the log file: `mv logs/telemetry.db logs/baseline.db`
2.  **Make a Non-Functional Change (Simulated):**
    * Open `src/vmt_engine/systems/movement.py`.
    * Add a comment inside the `execute` method (e.g., `# This is a harmless comment`). Save the file.
    * *(This change should have no impact on simulation behavior)*.
3.  **Run Again:** Execute the exact same command as step 1:
    ```bash
    python scripts/run_headless.py --scenario scenarios/demos/demo_03_mixed_regime.yaml --seed 77 --max-ticks 30
    ```
    * Rename the new log file: `mv logs/telemetry.db logs/modified.db`
4.  **Compare Telemetry:**
    ```bash
    python scripts/compare_telemetry_snapshots.py logs/baseline.db logs/modified.db
    ```
    *(Expected Outcome: SUCCESS. The script should report that core agent and trade data are identical, proving your change didn't break determinism)*.
5.  **Revert Change:** Remove the comment you added.

**Validation:** `compare_telemetry_snapshots.py` confirms identical results, verifying that the (simulated) code change did not affect behavior. This workflow is crucial for validating actual code changes.

---

## 4. Capstone Project

**Goal:** Design, implement, test, and document a simple but non-trivial protocol enhancement, demonstrating mastery of VMT architecture, determinism, and testing.

**Project Idea:** Implement a Deterministic Tie-Breaking Strategy for `LegacyMatchingProtocol`'s Pass 3 (Greedy Fallback).

**Background:** The current `LegacyMatchingProtocol` sorts potential pairs by `(-discounted_surplus, agent_id, partner_id)`. This is deterministic but might not always represent the most economically meaningful tie-break (e.g., it arbitrarily favors lower agent IDs).

**Task:**
1.  **Design:** Propose an alternative, deterministic tie-breaking rule for Pass 3 when multiple pairs offer the *exact same* highest discounted surplus. Examples:
    * Prioritize pairs with the smallest distance.
    * Prioritize pairs involving agents with lower inventory of the good they *need*.
    * (Choose one simple rule).
2.  **Implement:**
    * Create a new protocol class, e.g., `EnhancedLegacyMatching`, inheriting from `LegacyMatchingProtocol` or modifying a copy.
    * Locate the sorting logic in `_pass3_greedy_fallback`.
    * Modify the `potential_pairings.sort(key=...)` logic to incorporate your new tie-breaking rule *after* the primary sort by `-discounted_surplus`. Ensure the overall sort remains deterministic (e.g., use agent IDs as the final tie-breaker if your new rule still results in ties).
    * Ensure your protocol is registered using `@register_protocol` with a unique name (e.g., `"legacy_enhanced_tiebreak"`).
3.  **Test:**
    * Create new tests in `tests/test_matching_enhanced_legacy.py`.
    * **Crucially:** Design a test case (potentially requiring a custom small scenario) where two potential pairs have the *exact same* maximum discounted surplus but differ according to your new tie-breaking criterion. Assert that your protocol consistently chooses the pair favored by your rule.
    * Include tests confirming determinism: run multiple times with the same seed and assert identical pairing outcomes (check the `pairings` table in telemetry). Use `scripts/compare_telemetry_snapshots.py` on generated logs.
4.  **Scenario:**
    * Create a scenario file in `scenarios/custom/enhanced_tiebreak_demo.yaml` that uses your new matching protocol (`matching_protocol: "legacy_enhanced_tiebreak"`).
    * Optionally, design the scenario endowments/positions specifically to showcase the tie-breaking behavior difference compared to the standard `legacy_three_pass`.
5.  **Benchmark:** Run `scripts/benchmark_performance.py` with your scenario and the baseline `legacy_three_pass` scenario. Report any significant performance differences.
6.  **Document:** Write a short technical note (`docs/capstone/enhanced_tiebreak_note.md`) explaining:
    * The economic rationale for your chosen tie-breaking rule.
    * How you implemented it while maintaining determinism and respecting the `Protocol → Effect → State` architecture.
    * How your tests validate the correctness and determinism of the implementation.

**Acceptance Criteria:**
* New protocol (`EnhancedLegacyMatching`) is implemented and registered.
* Protocol correctly applies the new tie-breaking rule.
* Protocol strictly adheres to VMT architecture (returns Effects, uses seeded RNG if needed, ensures ordered operations).
* Tests in `tests/` pass, specifically demonstrating the new tie-breaking logic and proving determinism (identical telemetry snapshots for same seed).
* A demo scenario (`scenarios/custom/`) successfully uses the new protocol.
* Performance impact is measured and documented.
* Technical note clearly explains the design, implementation, and validation.

**Review Checklist:**
* [ ] Does the new protocol inherit correctly and use `@register_protocol`?
* [ ] Is the tie-breaking logic implemented correctly in the sort key?
* [ ] Is the final sort order fully deterministic (e.g., using IDs as ultimate tie-breaker)?
* [ ] Does the protocol only return `Effect` objects?
* [ ] Does the protocol avoid direct state mutation?
* [ ] Do tests specifically validate the tie-breaking scenario?
* [ ] Do determinism tests (snapshot comparison) pass?
* [ ] Does the demo scenario load and run?
* [ ] Is the performance impact acceptable?
* [ ] Does the technical note clearly articulate the rationale and implementation?

---

## 5. Reference Appendices

### Appendix A: Glossary (Economics → Code)

* **Agent**: `src/vmt_engine/core/agent.py:Agent` - Represents an individual decision-maker.
* **Utility Function**: Classes inheriting from `src/vmt_engine/econ/base.py:Utility`, implemented in `src/vmt_engine/econ/utility.py`. Configured in scenario `utilities.mix`.
* **Marginal Rate of Substitution (MRS)**: `Utility.mrs_A_in_B(A, B)` method. Used implicitly to calculate reservation bounds.
* **Reservation Value / Price**: `Utility.reservation_bounds_A_in_B(A, B, eps)` method. Returns `(p_min, p_max)`.
* **Quotes**: `Agent.quotes: dict[str, float]`. Calculated in `src/vmt_engine/systems/quotes.py:compute_quotes` based on reservation bounds and spread. Includes keys like `ask_A_in_B`, `bid_A_in_B`, `ask_A_in_M`, etc.
* **Surplus (Potential Gains from Trade)**: Calculated heuristically in `src/vmt_engine/systems/matching.py:compute_surplus` (barter) and `estimate_money_aware_surplus` (money-aware) using quote overlaps. Used for partner ranking in `LegacySearchProtocol` and `LegacyMatchingProtocol`.
* **Actual Utility Gain (from Trade)**: Calculated during bargaining (`find_compensating_block_generic`) using `u_total` or `Utility.u_goods` to check `ΔU > epsilon`. Stored in `TradeEffect.metadata` and `trades` telemetry table (`buyer_surplus`, `seller_surplus`).
* **Search**: Implemented by classes inheriting `SearchProtocol` (`src/vmt_engine/protocols/search/`). Example: `LegacySearchProtocol` uses distance-discounted surplus.
* **Matching**: Implemented by classes inheriting `MatchingProtocol` (`src/vmt_engine/protocols/matching/`). Example: `LegacyMatchingProtocol` uses 3-pass algorithm.
* **Bargaining**: Implemented by classes inheriting `BargainingProtocol` (`src/vmt_engine/protocols/bargaining/`). Example: `LegacyBargainingProtocol` uses compensating block search.
* **Determinism**: Ensured by seeded RNG (`sim.rng`), sorted iteration (e.g., `sorted(agents, key=lambda a: a.id)`), and fixed phase order (`src/vmt_engine/simulation.py:step`).
* **Tick**: One cycle through the 7 phases in `src/vmt_engine/simulation.py:step`.
* **Scenario**: YAML configuration file parsed by `src/scenarios/loader.py` into a `ScenarioConfig` object defined in `src/scenarios/schema.py`.

### Appendix B: Repository Map

| Directory/File                      | Responsibility                                                     | Key Classes/Functions                             |
| :---------------------------------- | :----------------------------------------------------------------- | :------------------------------------------------ |
| `src/vmt_engine/core/`              | Fundamental data structures                                        | `Agent`, `Grid`, `Inventory`, `Position`, `SpatialIndex` |
| `src/vmt_engine/econ/`              | Economic calculations, Utility functions                           | `Utility` (base), `UCES`, `ULinear`, `UQuadratic`, etc. |
| `src/vmt_engine/protocols/`         | Institutional rules (Search, Match, Bargain)                     | `SearchProtocol`, `MatchingProtocol`, `BargainingProtocol` |
| `src/vmt_engine/protocols/base.py`  | Abstract protocols, All `Effect` types                           | `Effect`, `Trade`, `Move`, `Pair`, etc.             |
| `src/vmt_engine/protocols/context.py`| Immutable context objects for protocols                          | `WorldView`, `ProtocolContext`, `AgentView`       |
| `src/vmt_engine/protocols/registry.py`| Protocol registration and discovery                              | `ProtocolRegistry`, `@register_protocol`          |
| `src/vmt_engine/systems/`           | Implementation of the 7 tick phases                              | `PerceptionSystem`, `DecisionSystem`, `MovementSystem`, etc. |
| `src/vmt_engine/simulation.py`      | Main simulation orchestrator, tick loop                          | `Simulation`                                      |
| `src/telemetry/`                    | SQLite logging system                                              | `TelemetryManager`, `TelemetryDatabase`, `LogConfig` |
| `src/scenarios/`                    | Scenario definition (`schema.py`), loading (`loader.py`)         | `ScenarioConfig`, `load_scenario`, `protocol_factory` |
| `scenarios/`                        | User-facing YAML scenario definition files                       | `.yaml` files                                     |
| `tests/`                            | Pytest test suite                                                | `test_*.py` files                                 |
| `scripts/`                          | Helper scripts (headless run, compare logs, benchmark)           | `run_headless.py`, `compare_telemetry_snapshots.py` |
| `launcher.py` / `src/vmt_launcher/` | GUI application for launching simulations                          | `LauncherWindow`                                  |
| `view_logs.py` / `src/vmt_log_viewer/`| GUI application for inspecting telemetry                         | `LogViewerWindow`                                 |
| `main.py`                           | CLI entry point for running simulations with visualization       | `main()`                                          |
| `docs/`                             | Project documentation                                              | `.md` files                                       |

### Appendix C: Test Index

| Test File                             | Validates                                                                 | Key Concepts / Rules Tested                                       |
| :------------------------------------ | :------------------------------------------------------------------------ | :---------------------------------------------------------------- |
| `test_barter_integration.py` | End-to-end barter simulation, determinism                               | Determinism, Basic Trade Execution                             |
| `test_core_state.py`       | Grid, Inventory, Agent initialization                                     | Core Data Structures, Type Invariants                             |
| `test_determinism_*.py` (various)   | Identical outcomes for same seed                                          | Determinism (RNG, Ordered Iteration)                              |
| `test_money_*.py` | Money system infrastructure, regimes, quotes, telemetry                 | Money Implementation, Exchange Regimes, Effects-only              |
| `test_pairing_money_aware.py` | Money-aware surplus estimation and pairing logic                      | Economic Logic, Protocol Implementation                           |
| `test_protocol_registry.py` | Protocol registration, lookup, factory integration                    | Architecture (Protocol Registry)                                  |
| `test_protocol_yaml_config.py` | Loading protocols from scenario files, CLI overrides                  | Configuration, Architecture                                       |
| `test_random_*.py`  | Baseline protocol implementations (RandomWalk, RandomMatching)            | Protocol Implementation, Determinism (Seeded RNG)                 |
| `test_split_difference.py`| Split-the-Difference bargaining protocol                                | Protocol Implementation, Economic Logic (Fairness)                |
| `test_resource_claiming.py` | Resource claiming mechanism, single-harvester rule                    | Coordination Mechanisms, Determinism (ID tie-breaking)            |
| `test_telemetry_*.py`     | Logging configuration, database schema                                    | Telemetry System                                                  |
| `test_utility_*.py` | Correctness of utility calculations, MRS, reservation bounds          | Economic Logic, Edge Cases (Zero Inventory)                     |
| `compare_telemetry_snapshots.py`| Script (not pytest) comparing DBs for identical results             | Determinism (End-to-End Validation)                               |

### Appendix D: Common Violations and Detection

* **Violation:** Using `random.random()` or `np.random` directly.
    * **Rule:** Determinism (Seeded RNG Only).
    * **Detection:** Code review for `import random` or `import numpy as np` followed by direct calls. Determinism tests (`compare_telemetry_snapshots.py`) will fail.
* **Violation:** Iterating `dict.keys()` or `set` without `sorted()`.
    * **Rule:** Determinism (Ordered Iteration).
    * **Detection:** Code review for loops over sets or dictionaries without explicit sorting. Determinism tests may fail intermittently or on different machines/Python versions.
* **Violation:** Modifying `agent.inventory`, `agent.pos`, or `grid.cells` inside a Protocol.
    * **Rule:** Protocol → Effect → State; Effects-only state changes.
    * **Detection:** Code review of protocol implementations for assignment to state variables. Harder to detect automatically, relies on discipline. May cause unexpected behavior or break determinism if not done carefully.
* **Violation:** Using floats for `inventory` quantities or spatial parameters.
    * **Rule:** Typing Authority.
    * **Detection:** Type checkers (mypy), code review, potential runtime errors or unexpected rounding behavior. `compare_telemetry_snapshots.py` might fail due to floating-point inaccuracies if floats are used where ints are expected.
* **Violation:** Mixing decision logic (calculating *what* to do) with state update logic (actually *doing* it) within the same function or phase.
    * **Rule:** Phase Discipline; Protocol → Effect → State.
    * **Detection:** Code review. Look for Systems that both calculate optimal actions *and* modify state, or Protocols that attempt to modify state. Can lead to complex bugs and make reasoning about state difficult.

---

## 6. Mastery Review Checklist

Use this checklist to verify your understanding and readiness to contribute effectively.

**Conceptual Understanding:**
* [ ] Can you explain the VMT project's core research question regarding market emergence?
* [ ] Can you articulate the three non-negotiable rules (Determinism, Protocol→Effect→State, 7-Phase Cycle) and why they are critical?
* [ ] Can you describe the purpose of each of the 7 phases in the tick cycle?
* [ ] Do you understand the difference between `WorldView` (immutable, for protocols) and the simulation `State` (mutable, managed by systems)?
* [ ] Can you explain the different roles of Protocols vs. Systems?

**Practical Skills:**
* [ ] Can you set up the development environment and run the test suite?
* [ ] Can you run simulations using both the GUI and headless scripts?
* [ ] Can you create a valid scenario YAML file from scratch?
* [ ] Can you use the Log Viewer to inspect agent states and trade histories?
* [ ] Can you use `compare_telemetry_snapshots.py` to verify determinism?
* [ ] Can you implement a simple new protocol that adheres to the architecture (returns Effects, uses `WorldView`, maintains determinism)?

**Code Navigation:**
* [ ] Can you locate the implementation of a specific utility function?
* [ ] Can you find the code responsible for a specific tick phase (e.g., Movement)?
* [ ] Can you identify where a specific `Effect` type is defined and where it is applied?
* [ ] Can you find the schema definition for the telemetry database?

**Economic Mapping:**
* [ ] Can you map core economic concepts (MRS, Surplus, Reservation Price) to their corresponding code implementations?
* [ ] Can you explain how different utility functions lead to different agent behaviors?
* [ ] Do you understand how the `exchange_regime` and `money_mode` parameters affect simulation dynamics?

**Contribution Readiness:**
* [ ] Do you understand the testing requirements for new code?
* [ ] Are you confident you can write code that maintains determinism?
* [ ] Do you know where to find relevant documentation (technical manual, typing spec, etc.)?

**Final Check:**
* [ ] Have you completed all modules and labs?
* [ ] Have you successfully completed the Capstone Project, meeting all acceptance criteria?

**Self-Assessment:** Rate your confidence (1-5, 5=High) in contributing a new feature (e.g., a new protocol) while adhering to all project rules: _____

---
*End of VMT-DEV Mastery Guide*