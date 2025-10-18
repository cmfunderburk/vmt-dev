### Energy Budget and Sleep/Wake Cycle for Agents (Proposal)

This document proposes an energy budget and sleep/wake cycle for VMT agents. The intent is to introduce a biologically-inspired temporal constraint that creates daily-like rhythms while preserving determinism, economic coherence, and the fixed 7-phase tick order.

---

## Motivation and Intuition

- Agents currently operate continuously, bounded by movement, visibility, and interaction radius. Adding a finite energy budget introduces rest cycles that:
  - Bound the time-averaged intensity of search, trade, and foraging.
  - Create natural phases of activity (wake) and inactivity (rest), potentially leading to periodic market intensity.
  - Provide a tunable lever for pedagogy (temporal tradeoffs, labor/leisure analogies) and research (emergent synchronization, clustering around “homes”).

---

## Behavioral Summary (Default Values)

- Parameters (defaults in parentheses):
  - energy_max (24): maximum energy capacity
  - energy_awake_cost_per_tick (1): energy spent per tick while awake
  - energy_rest_rate_per_tick (3): energy restored per tick while resting at home
  - enable_energy_system (false initially, for backward compatibility)

- Wake behavior:
  - While energy > 0, agent engages in normal behaviors during the 7 phases (perception, decision, movement, trade, forage, regeneration, housekeeping).
  - At Housekeeping, awake agents pay energy_awake_cost_per_tick (default 1).

- Depletion and rest behavior:
  - Once energy reaches 0, the agent enters a homebound/rest cycle:
    1) If the agent has a home, it becomes homebound: target its home and move toward it each tick until arrival.
    2) If the agent has no home, it must claim one deterministically: choose the nearest unoccupied square (ties deterministically), set it as home, and move to it; if the current square is unoccupied, it can claim immediately and begin resting without movement.
  - Resting at home: Regain energy_rest_rate_per_tick (default 3) each tick until energy == energy_max.
  - While homebound or resting, the agent suspends normal economic behavior: no trading, no foraging, and decisions are restricted to going home or staying put to rest.
  - Upon reaching full energy (energy == energy_max), the agent exits rest and resumes normal behavior next tick.

Duty cycle intuition (with defaults): 24 awake ticks, then 8 resting ticks to recharge (3 per tick), for a 24 : 8 ≈ 75% awake time share. This creates periodic bursts of market activity without changing the 7-phase order.

---

## Deterministic Integration with the 7-Phase Tick

Preserve strict order: 1) Perception → 2) Decision → 3) Movement → 4) Trade → 5) Forage → 6) Resource Regeneration → 7) Housekeeping.

- Where energy effects apply:
  - Decision (2): If energy == 0, override normal decisions:
    - If at home and not full: choose “rest” (no movement target, no trade/forage intent).
    - If not at home but home exists: set movement target to home (homebound).
    - If no home exists: deterministically select a target home square (nearest unoccupied) and set movement target.
  - Movement (3): Homebound agents move toward home with normal deterministic tie-breaking and move_budget_per_tick.
  - Trade/Forage (4–5): Suppressed when energy == 0 (homebound) or when resting.
  - Housekeeping (7): Apply energy updates after all actions that could have occurred this tick:
    - If awake this tick: energy = max(0, energy − energy_awake_cost_per_tick).
    - If resting at home: energy = min(energy_max, energy + energy_rest_rate_per_tick).

Notes on ordering inside Housekeeping:
  - Keep quotes refresh and telemetry logging consistent; if energy should be visible in telemetry for this tick, update energy before logging snapshots.
  - Never reorder systems; implement energy bookkeeping as part of Housekeeping.

---

## Data Model Additions

Agent (runtime state additions):

```text
energy: int                 // 0..energy_max
energy_max: int             // from params
home_pos: optional<Position>
is_resting: bool            // true when at home and recharging
```

Scenario params (schema defaults):

```text
enable_energy_system: bool = false
energy_max: int = 24
energy_awake_cost_per_tick: int = 1
energy_rest_rate_per_tick: int = 3
```

Initialization:
- On Simulation init, set agent.energy = energy_max, agent.home_pos = None, agent.is_resting = false.
- Gate the entire feature by enable_energy_system to preserve existing tests and scenarios.

Telemetry (optional, v1.1+ extension):
- Add energy, is_resting, and home_pos to agent snapshot table/record.

---

## Decision and Movement Logic Changes

Decision (Phase 2):

Deterministic priority when enable_energy_system:
1) If agent.energy == 0:
   - If agent.home_pos is not None:
     - If agent.pos == home_pos: agent.is_resting = true; clear trade/forage intents
     - Else: set target_pos = home_pos; agent.is_resting = false
   - Else (no home yet): choose a home square deterministically and set target_pos; agent.is_resting = false
2) Else (agent.energy > 0):
   - agent.is_resting = false
   - proceed with existing trade/forage decision logic as today

Home selection algorithm (deterministic, nearest unoccupied):
- Search rings of increasing Manhattan distance d = 0, 1, 2, ...
- Within a ring, enumerate positions with a fixed order:
  - Reduce |dx| before |dy|, prefer negative directions on ties, then lowest (x, y) as final tiebreaker to match movement’s determinism flavor.
- Unoccupied means no current agent at that position (use SpatialIndex agent_positions).
- If no unoccupied found within grid bounds:
  - Fallback: claim current position, even if co-located; this preserves progress in overloaded grids.

Movement (Phase 3):
- If homebound (energy == 0 and pos != home_pos), move toward target_pos using existing deterministic rules and budget. This allows “getting to bed” at zero energy without consuming “awake” action privileges.
- If is_resting, do not move.

Trade and Forage (Phases 4–5):
- When energy == 0 (homebound) or is_resting == true, skip trade and forage attempts for the agent.

---

## Housekeeping Energy Update (Phase 7)

Apply in a fixed sub-order for all agents iterated by ascending id:
1) If is_resting and pos == home_pos:
   - energy = min(energy_max, energy + energy_rest_rate_per_tick)
   - If energy == energy_max: is_resting = false (ready to resume next tick)
2) Else:
   - If agent performed an awake tick (not resting): energy = max(0, energy − energy_awake_cost_per_tick)
   - If energy reaches 0 and agent not at home, the agent will become homebound in the next Decision phase.

This ordering ensures that an agent who became resting this tick (because it arrived home during Movement and declared rest in Decision) receives rest credit, and that awake agents always pay the awake cost for the tick just completed.

Clamping invariants:
- Maintain 0 ≤ energy ≤ energy_max

---

## Invariants and Edge Cases

- Deterministic iteration: Always iterate agents by ascending id in all energy/bookkeeping operations.
- Home conflicts: Multiple agents may target the same candidate home deterministically; if a conflict arises (another agent occupies the square at arrival), re-run the selection next Decision; if no unoccupied squares exist, allow claiming current position.
- Path deadlocks: Movement already uses deterministic tie-breaking and a diagonal deadlock rule (only higher ID moves). Homebound travel inherits these rules without change.
- Trading cooldowns: Unaffected; resting/homebound agents simply suspend new attempts.
- Quote refresh: Still driven by inventory_changed; rest state does not change quotes unless inventory changed for other reasons.

---

## Pros

- Temporal realism: Introduces a tractable analog to circadian cycles without adding stochasticity.
- Endogenous cycles: Activity clusters (trade/forage) can emerge at predictable intervals, potentially creating “rush hours.”
- Spatial anchoring: Home selection encourages local clustering and repeated interactions, highlighting spatial frictions and neighborhood effects.
- Pedagogical clarity: Clear, tunable “duty cycle” for students to explore temporal constraints vs. outcomes.
- Backward compatibility: Gated by enable_energy_system; default off avoids breaking existing tests and demos.

---

## Cons / Risks

- Reduced throughput: Agents spend a share of time resting, reducing steady-state trade volumes; parameter tuning required for demos.
- Edge-case congestion: In dense grids, home selection can lead to congestion and rerouting churn; fallback to claiming current position mitigates but allows co-located homes.
- Complex interactions: Rest gating can amplify or dampen resource regeneration impacts in unintuitive ways; requires careful documentation and examples.
- Implementation surface: Requires additions to Agent state, Scenario schema, Decision/Movement/Housekeeping, and optionally Telemetry and Renderer.

---

## Pedagogical Value (Speculative)

- Labor vs. leisure: The wake phase as “labor/search/trade” and the rest phase as “leisure/recuperation,” making intertemporal tradeoffs visible.
- Peak-load economics: Periodic demand/supply thickening during wake phases exposes matching dynamics and the value of coordination.
- Spatial microfoundations: Anchoring to home illustrates commuting costs analogies and localized markets.
- Comparative statics labs: Students can vary energy_max, rest_rate, and move budgets to see effects on prices, quantities, and network structure over time.

---

## Research Directions (Speculative)

- Synchronization and phase-locking: Do agents spontaneously synchronize wake cycles through market incentives? Under what parameter regions?
- Market thickness dynamics: How do rest-induced cycles shape the distribution of realized surpluses and price dispersion across ticks?
- Spatial clustering: Does home anchoring generate persistent trading neighborhoods? Are there frontier regions with different price levels?
- Resilience and recovery: After shocks (resource depletion, price wedges), do rest cycles accelerate or hinder system recovery?
- Policy experiments: Vary energy_rest_rate as a “rest subsidy” or “infrastructure” and study welfare/efficiency impacts.

---

## Rollout Plan and Backward Compatibility

1) Schema/params: Add enable_energy_system (default false), energy_max, energy_awake_cost_per_tick, energy_rest_rate_per_tick with above defaults.
2) Agent state: Add energy, energy_max, home_pos, is_resting; initialize at sim start.
3) Decision: Gate normal decisions by energy; implement deterministic home selection.
4) Movement: Reuse existing movement; no changes beyond honoring homebound targets.
5) Housekeeping: Add energy bookkeeping before telemetry logging.
6) Telemetry (optional): Include energy/home/is_resting in snapshots.
7) Renderer (optional): Visual hints for home (e.g., small marker) and resting (e.g., dim sprite).
8) Tests: Add unit tests for energy clamping, rest cycle length, deterministic home selection, and interaction with movement deadlock rule.

Enable by scenario-level flag only when intended; existing tests and examples remain unaffected with the default off.

---

## Open Questions and Variants

- Should awake energy cost ever depend on movement distance or actions (trade/forage) rather than a flat per-tick cost? Default proposal: flat cost for simplicity; variants are straightforward.
- Allow partial activity while resting (e.g., accept trades if buyer comes to you)? Default proposal: no, to keep the interpretation clean; could be a future toggle.
- Home relocation policy: Allow agents to opportunistically re-home if the local environment changes? Default proposal: keep first home unless explicitly reset by a scenario action.
- Energy accounting order: Current design restores/charges within Housekeeping; alternative is to charge at start-of-tick. We prefer end-of-tick charging to let the last awake tick complete before homebound behavior engages next tick.

---

## Pseudocode Sketches

Decision (Phase 2):

```python
for agent in agents_sorted_by_id:
    if not params.enable_energy_system:
        normal_decision(agent)
        continue

    if agent.energy == 0:
        if agent.home_pos is None:
            agent.home_pos = select_nearest_unoccupied(agent.pos, spatial_index)
        if agent.pos == agent.home_pos:
            agent.is_resting = True
            clear_intents(agent)  # no trade/forage targets
        else:
            agent.is_resting = False
            agent.target_pos = agent.home_pos
            agent.target_agent_id = None
    else:
        agent.is_resting = False
        normal_decision(agent)
```

Housekeeping (Phase 7 energy bookkeeping):

```python
for agent in agents_sorted_by_id:
    if not params.enable_energy_system:
        continue
    if agent.is_resting and agent.pos == agent.home_pos:
        agent.energy = min(agent.energy_max, agent.energy + params.energy_rest_rate_per_tick)
        if agent.energy == agent.energy_max:
            agent.is_resting = False
    else:
        # awake tick cost
        agent.energy = max(0, agent.energy - params.energy_awake_cost_per_tick)
```

Home selection (deterministic BFS-like ring expansion):

```python
def select_nearest_unoccupied(origin, spatial_index):
    if is_unoccupied(origin, spatial_index):
        return origin
    for d in range(1, grid.N * 2):  # bounded by grid size
        for pos in enumerate_ring_positions(origin, d):  # fixed deterministic order
            if is_in_bounds(pos) and is_unoccupied(pos, spatial_index):
                return pos
    return origin  # fallback
```

---

## Expected Outcomes

- With defaults (24/3), agents follow an 8-tick rest after a 24-tick active phase, seeding visible oscillations in market activity.
- Deterministic, reproducible patterns; no changes to economic primitives or rounding rules.
- Spatial anchoring produces interpretable agent “neighborhoods,” enabling new classroom demos and research probes.


