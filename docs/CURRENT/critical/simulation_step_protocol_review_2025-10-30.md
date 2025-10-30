# Simulation Step & Protocol Integration Review (GP5 Codex)

## Scope & Context
- Objective: audit the `Simulation.step()` orchestration and its interaction with search, matching, and bargaining protocols.
- Focus: adherence to the Protocol → Effect → State contract, determinism guarantees, and data flow across the 7-phase tick.

## Step Function Overview
- `Simulation.step()` evaluates mode schedule changes, then executes each registered system in fixed order, conditionally skipping trade/forage phases depending on the active mode.
- Post-phase telemetry captures mode, exchange regime, and active exchange pairs before `tick` increments.

```321:355:src/vmt_engine/simulation.py
        for system in self.systems:
            if self._should_execute_system(system, self.current_mode):
                system.execute(self)
        if self.telemetry:
            active_pairs = self._get_active_exchange_pairs()
            self.telemetry.log_tick_state(
                self.tick,
                self.current_mode,
                self.params.get('exchange_regime', 'barter_only'),
                active_pairs
            )
        self.tick += 1
```

## Phase Walkthrough (7-Phase Cycle)

### Phase 1 – Perception (`PerceptionSystem.execute`)
- Iterates agents in insertion order (initial agent list sorted by id during sim init).
- Uses `SpatialIndex.query_radius` for deterministic neighbor discovery, storing neighbors, quotes, and visible resources in `agent.perception_cache`.
- No protocol involvement; prepares inputs for search protocols by caching observations.

```22:37:src/vmt_engine/systems/perception.py
        for agent in sim.agents:
            nearby_agent_ids = sim.spatial_index.query_radius(
                agent.pos,
                agent.vision_radius,
                exclude_id=agent.id,
            )
            perception = perceive(agent, sim.grid, nearby_agent_ids, sim.agent_by_id)
            agent.perception_cache = {
                "neighbors": perception.neighbors,
                "neighbor_quotes": perception.neighbor_quotes,
                "resource_cells": perception.resource_cells,
            }
```

### Phase 2 – Decision (`DecisionSystem.execute`)
- Clears stale resource claims to keep `sim.resource_claims` aligned with current targets.
- Builds per-agent `WorldView` snapshots via `build_world_view_for_agent`, then delegates to the configured `SearchProtocol` to (a) build ranked preference lists and (b) emit effects (e.g., `SetTarget`, `ClaimResource`).
- Applies search effects immediately, mutating agent targets, foraging commitments, and shared `resource_claims` map.
- Aggregates preference dictionaries and calls the configured `MatchingProtocol`, which returns `Pair` / `Unpair` effects evaluated and applied within the system, updating agent pairing state and trade cooldowns.
- Optional telemetry logs preference rankings.

```51:123:src/vmt_engine/systems/decision.py
        preferences = self._execute_search_phase(sim)
        self._execute_matching_phase(sim, preferences)
        for effect in effects:
            if isinstance(effect, SetTarget):
                agent.target_pos = partner.pos if isinstance(effect.target, int) else effect.target
            elif isinstance(effect, ClaimResource):
                sim.resource_claims[effect.pos] = agent.id
            elif isinstance(effect, ReleaseClaim):
                sim.resource_claims.pop(effect.pos, None)
```

### Phase 3 – Movement (`MovementSystem.execute`)
- For each agent, determines the current target (paired partner or decision target) and moves toward it up to `move_budget_per_tick`, updating the spatial index.
- Contains diagonal deadlock mitigation by halting the lower-id agent when paired agents approach diagonally.
- No protocol invocation; moves are applied directly rather than via `Move` effects.

```17:59:src/vmt_engine/systems/movement.py
        for agent in sim.agents:
            target_pos = partner.pos if agent.paired_with_id is not None else agent.target_pos
            if target_pos is not None:
                if agent.target_agent_id is not None and distance <= sim.params["interaction_radius"]:
                    continue
                new_pos = next_step_toward(
                    agent.pos, target_pos, sim.params["move_budget_per_tick"]
                )
                agent.pos = new_pos
                sim.spatial_index.update_position(agent.id, new_pos)
```

### Phase 4 – Trade (`TradeSystem.execute`)
- Iterates paired agents in sorted id order, ensuring each pair is processed once per tick.
- Checks interaction radius compliance, builds a bilateral `WorldView` via `build_trade_world_view`, and delegates bargaining to the configured `BargainingProtocol`.
- Applies returned `Trade` or `Unpair` effects: `Trade` effects are translated into inventory deltas and passed through `execute_trade_generic`; `Unpair` effects dissolve matches and assign cooldowns.
- Logs successful trades to telemetry with pricing and surplus metadata.

```76:216:src/vmt_engine/systems/trading.py
        for agent in sorted(sim.agents, key=lambda a: a.id):
            if agent.paired_with_id is None:
                continue
            if distance <= sim.params["interaction_radius"]:
                effects = self.bargaining_protocol.negotiate((agent_a.id, agent_b.id), world)
                for effect in effects:
                    if isinstance(effect, Trade):
                        execute_trade_generic(...)
                    elif isinstance(effect, Unpair):
                        agent_a.paired_with_id = None
                        agent_b.paired_with_id = None
                        cooldown_until = sim.tick + sim.params.get('trade_cooldown_ticks', 10)
```

### Phase 5 – Forage (`ForageSystem.execute`)
- Processes unpaired agents in id order, harvesting resources at their positions subject to `enforce_single_harvester` gating.
- Harvesting updates inventories, grid resources, and telemetry counters directly; foraging commitments are cleared post-harvest, and trade cooldowns are reset.
- Protocol layer is bypassed; no `Harvest` effects are generated or validated.

### Phase 6 – Resource Regeneration (`ResourceRegenerationSystem.execute`)
- Invokes `regenerate_resources` with global parameters to replenish depleted cells after cooldowns.
- Operates deterministically over the tracked `grid.harvested_cells` set.
- No protocol participation.

### Phase 7 – Housekeeping (`HousekeepingSystem.execute`)
- Refreshes agent quotes after inventory changes, performs pairing integrity checks, and records telemetry snapshots for agents and resources.
- Ensures data consistency before the next tick begins.

## Protocol Touchpoints & Data Flow
- **Search Protocols:** Consume Phase-1 perception cache via `WorldView`, produce `SetTarget` / `ClaimResource` / `ReleaseClaim` effects that are executed immediately. Targets directly influence Phase 3 movement decisions.
- **Matching Protocols:** Receive global `ProtocolContext` with agent states, produce `Pair` / `Unpair` effects. Pairings steer both movement (Phase 3) and eligibility for trading (Phase 4) or foraging (Phase 5).
- **Bargaining Protocols:** Operate exclusively when agent pairs are co-located. Returned `Trade` effects update inventories, tweak cooldowns, and feed telemetry; `Unpair` effects drop agents back into search/forage flow.
- **Non-protocol Phases:** Movement, foraging, regeneration, and housekeeping are system-driven with no protocol hooks, relying on imperative updates.

## Determinism Considerations
- Agent lists and protocol invocations are explicitly sorted by id, ensuring repeatability when combined with the seeded RNG (`np.random.PCG64`).
- Mode scheduling gates trade/forage systems but leaves perception, decision, movement, regeneration, and housekeeping always active for consistent bookkeeping.
- Telemetry captures tick-by-tick mode, pairings, trades, and resource states, enabling regression validation across seeds.

## Review Findings

### Critical
- **Effect contract bypassed in multiple phases:** Movement and foraging mutate agent positions and inventories directly instead of emitting and applying `Move` / `Harvest` effects. This violates the Protocol → Effect → State rule and makes it impossible to centrally validate or replay state transitions.
- **Decision system applies effects imperatively:** `SetTarget`, `ClaimResource`, and `Pair` effects are executed inline without validation or ordering guarantees beyond loop order, undermining the deterministic effect pipeline described in `protocols/base.py`.

### Major
- **Trade execution translates effects ad hoc:** `Trade` effects are decomposed into a bespoke tuple before calling `execute_trade_generic`, creating drift between effect definitions and actual state changes; price and surplus validation occurs downstream, making auditing harder.
- **Housekeeping lacks protocol-driven quote refresh:** Although `RefreshQuotes` effect exists, quote updates are triggered procedurally, limiting flexibility for future protocol-based quote management.

### Minor
- **Mode gating relies on class-based `isinstance` checks:** Extending system list with subclasses that should be mode-gated requires touching `_should_execute_system`; consider explicit phase metadata to avoid fragile `isinstance` logic.
- **Decision telemetry optionality obscures preference audits:** When `log_preferences` is false, there is no record of protocol-generated preference orderings, complicating debugging of matching anomalies.

## Recommended Next Steps
- Introduce a centralized effect dispatcher for all phases, ensuring systems collect effects and apply them via a uniform validation layer.
- Migrate movement, foraging, and housekeeping updates to emit and process `Move`, `Harvest`, and `RefreshQuotes` effects respectively, aligning code with architectural rules.
- Define explicit phase descriptors (name, order, mode eligibility) on system classes to make `Simulation.step()` scheduling declarative and extensible.
- Expand telemetry hooks to record decision-phase preferences even when not persisted to the database, facilitating protocol-level regression tests.


