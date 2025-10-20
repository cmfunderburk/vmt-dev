Visualizing Microeconomic Theory — Engine Overview

Purpose
This document explains the deterministic Phase A barter engine: the 7-phase tick order, core responsibilities by system, determinism rules, key type invariants, and how scenarios flow into a running simulation with telemetry.

Seven-phase tick (fixed order)
1) Perception
   - Build a read-only view for each agent:
     - neighbors within vision (IDs and positions)
     - neighbor quotes (snapshotted; quotes are stable within the tick)
     - visible resource cells
   - Uses SpatialIndex.query_radius for O(N) average proximity checks.

2) Decision
   - Three-pass pairing algorithm:
     - Pass 1: Build ranked preference lists (distance-discounted surplus = surplus × β^distance)
     - Pass 2: Establish mutual consent pairings (both agents prefer each other)
     - Pass 3: Surplus-based greedy fallback (highest-surplus unmatched pairs)
   - Resource claiming: agents claim forage targets to reduce clustering; stale claims cleared at tick start
   - Paired agents maintain exclusive commitment; unpaired agents select best available target
   - Records target position and pairing state for movement phase

3) Movement
   - Manhattan steps up to move_budget_per_tick toward target.
   - Tie-breaking: reduce |dx| before |dy|; prefer negative direction on ties.
   - Diagonal deadlock resolution: if two agents target each other and are diagonally adjacent, only the higher id moves.
   - Updates the SpatialIndex after movement.

4) Trade
   - Only paired agents within interaction_radius attempt trades (commitment model)
   - Generic money-aware matching: selects best exchange pair (A↔B, A↔M, or B↔M) based on exchange_regime
     - "barter_only": Only A↔B trades (default, backward compatible)
     - "money_only": Only A↔M and B↔M trades
     - "mixed": All exchange pairs allowed
   - Price search is discrete and compensating: scan ΔA ∈ [1..dA_max]; for each ΔA, try candidate prices in [ask, bid]
   - Map price to quantity with round-half-up: ΔB = floor(price*ΔA + 0.5)
   - First-acceptable-trade principle: accept first (ΔA, ΔB, price) with ΔU > 0 for both
   - Successful trades maintain pairing; failed trades unpair and set cooldown until tick + trade_cooldown_ticks

5) Forage
   - Paired agents skip foraging (exclusive commitment to trading partner)
   - Unpaired agents harvest up to forage_rate units from their current cell when resources are available
   - Single-harvester enforcement: first agent (by ID order) at a cell claims the harvest for that tick

6) Resource Regeneration
   - Regenerate resources per cell using resource_growth_rate, resource_max_amount, and resource_regen_cooldown.

7) Housekeeping
   - Refresh quotes only for agents whose inventory_changed or lambda_changed flags are set
   - Pairing integrity checks: detect and repair asymmetric pairings
   - Lambda updates (KKT mode, Phase 3+): adaptive marginal utility estimation from neighbor prices
   - Batch telemetry: agent snapshots, resource snapshots, tick states according to LogConfig

Determinism rules (must hold everywhere)
- Always process agents sorted by agent.id
- Always process trade pairs sorted by (min_id, max_id)
- Do not mutate quotes mid-tick; quotes refresh in Housekeeping only
- Pairing establishes exclusive commitment until unpair event
- Successful trades maintain pairing; failed trades unpair and set mutual cooldown
- Use SpatialIndex for proximity queries; avoid O(N^2) scans
- When mapping prices to integer quantities, use round-half-up: floor(x + 0.5)
- Preference ranking uses distance-discounted surplus: surplus × β^distance
- Fallback pairing uses surplus-based greedy matching for welfare maximization

Type and invariant contracts
- Inventories (A, B, M), resources, positions, ΔA, ΔB, ΔM are integers
- Money holdings (M) stored in minor units (e.g., cents); money_scale parameter for conversion
- Spatial parameters (vision_radius, interaction_radius, move_budget_per_tick) are integers
- Utility values, prices, lambda_money are floats
- Quote constraints: ask ≥ p_min and bid ≤ p_max for all exchange pairs
- Agent.quotes is dict[str, float] with keys for active exchange pairs (e.g., "ask_A_in_B", "bid_A_in_M")

Data flow
- YAML scenario → scenarios/loader.py → Simulation(...)
  - Simulation constructs Grid, Agents, SpatialIndex, and initializes quotes.
  - Systems advance the world in the fixed 7-phase order.
  - Telemetry batches to SQLite via TelemetryManager (./logs/telemetry.db).

Quickstart
- CLI with visualization (Pygame renderer):
  python main.py scenarios/three_agent_barter.yaml --seed 42

- Programmatic run:
  from vmt_engine.simulation import Simulation
  from scenarios.loader import load_scenario
  from telemetry.config import LogConfig
  sim = Simulation(load_scenario("scenarios/three_agent_barter.yaml"), seed=42, log_config=LogConfig.debug())
  sim.run(max_ticks=100)

Implementation tips
- Keep loops deterministically ordered; avoid nondeterministic dict iteration for side effects
- Set agent.inventory_changed = True when inventories mutate; quotes are recomputed in Housekeeping only
- Set agent.lambda_changed = True when lambda updates occur (KKT mode)
- Use SpatialIndex for all proximity and pair constructions
- Be strict about integer math for goods, positions, and discrete trade quantities
- Pairing state (paired_with_id) persists across ticks until unpair event
- Preference lists (_preference_list) are cleared each tick after logging
- Money-aware code should check exchange_regime to determine allowed exchange pairs


