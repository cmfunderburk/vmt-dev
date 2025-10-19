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
   - Prefer trade when there is positive surplus; otherwise select a forage target.
   - Partner choice: choose best surplus among visible neighbors, breaking ties by lowest partner id; skip partners in cooldown.
   - Records target position (peer to trade with, or resource to forage) for the movement phase.

3) Movement
   - Manhattan steps up to move_budget_per_tick toward target.
   - Tie-breaking: reduce |dx| before |dy|; prefer negative direction on ties.
   - Diagonal deadlock resolution: if two agents target each other and are diagonally adjacent, only the higher id moves.
   - Updates the SpatialIndex after movement.

4) Trade
   - Construct candidate pairs within interaction_radius using SpatialIndex.query_pairs_within_radius.
   - Sort pairs by (min_id, max_id) and attempt at most one trade per pair per tick.
   - Price search is discrete and compensating: scan ΔA ∈ [1..dA_max]; for each ΔA, try candidate prices in [ask, bid] that are likely to yield integer ΔB.
   - Map price to quantity with round-half-up: ΔB = floor(price*ΔA + 0.5).
   - If no feasible block, set mutual cooldown until tick + trade_cooldown_ticks.

5) Forage
   - If no trade target, agents harvest up to forage_rate units from their current cell when resources are available.

6) Resource Regeneration
   - Regenerate resources per cell using resource_growth_rate, resource_max_amount, and resource_regen_cooldown.

7) Housekeeping
   - Refresh quotes only for agents whose inventory_changed flag is set.
   - Batch telemetry: agent snapshots and resource snapshots according to LogConfig.

Determinism rules (must hold everywhere)
- Always process agents sorted by agent.id.
- Always process trade pairs sorted by (min_id, max_id).
- Do not mutate quotes mid-tick; quotes refresh in Housekeeping only.
- Exactly one trade attempt per pair per tick; failed attempts set mutual cooldown.
- Use SpatialIndex for proximity queries; avoid O(N^2) scans.
- When mapping prices to integer quantities, use round-half-up: floor(x + 0.5).

Type and invariant contracts
- Inventories, resources, positions, ΔA and ΔB are integers.
- Spatial parameters (vision_radius, interaction_radius, move_budget_per_tick) are integers.
- Utility values and prices are floats.
- Quote constraints: ask_A_in_B ≥ p_min and bid_A_in_B ≤ p_max.

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
- Keep loops deterministically ordered; avoid nondeterministic dict iteration for side effects.
- Set agent.inventory_changed = True when inventories mutate; quotes are recomputed in Housekeeping only.
- Use SpatialIndex for all proximity and pair constructions.
- Be strict about integer math for goods, positions, and discrete trade quantities.


