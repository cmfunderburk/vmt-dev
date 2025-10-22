# VMT Protocol Modularization Plan (v3)

Document status: Working Draft
Last updated: 2025-10-22

---

## Executive summary

This v3 plan updates the protocol modularization strategy to align with the current engine, which now includes mode scheduling, money-aware trading primitives, and expanded telemetry. We retain the 7-phase deterministic loop and introduce protocol interfaces for Search and Matching via a low-risk, incremental extraction that preserves behavior and telemetry. Phase 1 focuses on creating interfaces and legacy wrappers, delegating to existing logic. Subsequent phases extract logic into standalone implementations, add a registry and YAML configuration, and introduce alternative algorithms (e.g., Greedy, Stable Matching). Trade/bargaining modularization is deferred; existing generic trade primitives will later become a `TradeProtocol`.

---

## Current state (as of v3)

- 7-phase loop with mode awareness: Perception → Decision → Movement → Trade → Forage → Regeneration → Housekeeping (`src/vmt_engine/simulation.py`).
- Decision system implements three-pass pairing and search/forage selection with resource-claiming and pass 3b cleanup (`src/vmt_engine/systems/decision.py`).
- Money-aware trade primitives exist and are used in Trade phase (barter, A↔M, B↔M) with tie-breaking and telemetry of exchange pair type (`src/vmt_engine/systems/matching.py`, `src/vmt_engine/systems/trading.py`).
- Scenario schema supports `mode_schedule`, `exchange_regime`, `money_mode`, and related parameters (`src/scenarios/schema.py`).
- Telemetry persists decisions, pairings, preferences, trades, tick states, and lambda updates into `logs/telemetry.db` (`src/telemetry/database.py`, `src/telemetry/db_loggers.py`).

Implication: Matching and search remain embedded in `DecisionSystem`; trade execution is already generic and money-aware in `TradeSystem`. The modularization plan should wrap Decision behavior first.

---

## Gaps vs prior proposals (v2)

1. Protocol artifacts missing: No `ProtocolContext`, `SearchProtocol`, `MatchingProtocol` present.
2. Decision remains monolithic: Pass 1/2/3 implemented directly in `DecisionSystem`.
3. Telemetry is richer now: includes `pair_type` and `tick_states`; plan must preserve and validate.
4. Money-aware primitives exist: Plan should acknowledge `estimate_money_aware_surplus`, generic trade search, and not duplicate them.
5. Scenario schema has no `protocols` section yet: Initial integration should use Python defaults; YAML later.
6. PerceptionView unresolved: Engine uses `agent.perception_cache` (dict); plan must defer dataclass migration.

---

## Design decisions (v3)

- Interfaces first, behavior unchanged: Introduce thin protocol interfaces and legacy wrappers that delegate to existing logic to ensure byte-identical telemetry in Phase 1.
- Keep Decision orchestration: `DecisionSystem` stays responsible for pass ordering, pass 3b cleanup, and logging; protocols only compute preferences, matches, and forage targets.
- Determinism preserved: All protocol methods must process agents in sorted order and use explicit tiebreakers.
- Python default injection now; YAML later: Add optional protocol arguments to `Simulation.__init__`. Introduce a registry and optional YAML `protocols` field in a later phase.
- Telemetry separation: Protocols only update agent state; `DecisionSystem` continues to log decisions/preferences/pairings.
- Defer PerceptionView and Target types: Keep `dict` perception cache and `Position` targets for now.

---

## Interfaces to add (Phase 1)

Location: `src/vmt_engine/protocols/`

- `context.py` — ProtocolContext
  - Read-only view of simulation parameters and state that protocols need.
  - Fields: params (dict), current_tick, current_mode, grid, agent_by_id, spatial_index, resource_claims (shared map), trade_cooldown_ticks.
  - Convenience properties: `beta`, `vision_radius`, `interaction_radius`, `forage_rate`.

- `search.py` — SearchProtocol (ABC)
  - `select_forage_target(agent, perception_cache: dict, context: ProtocolContext) -> Optional[Position]`
  - `evaluate_resource_opportunity(agent, resource_cell, context) -> float` (optional for advanced strategies)
  - Responsibilities: filter/claim resources; set `agent.target_pos`, commitment flags if selecting forage; deterministic tie-breaking.

- `matching.py` — MatchingProtocol (ABC)
  - `build_preferences(agents: list[Agent], context) -> dict[int, list[tuple[int, float, float, int, str]]]`
    - Output per-agent ranked list: (partner_id, surplus, discounted_surplus, distance, pair_type)
    - Must enforce cooldown filtering and determinism.
  - `find_matches(preferences, context) -> list[tuple[int, int]]`
    - Establish pairings for unpaired agents; update `paired_with_id`, `target_pos`, `target_agent_id`; clear mutual cooldowns.

Note: Pairing is persistent and exclusive; protocols must not unpair. Unpairing remains a Trade/Housekeeping concern.

---

## Legacy wrappers (Phase 1)

Location: `src/vmt_engine/protocols/legacy_*.py`

- `LegacySearchProtocol`: delegates to current `DecisionSystem` forage logic via `movement.choose_forage_target` and existing claiming rules.
  - Mirrors `_evaluate_forage_target` semantics including commitment flags and idle-home fallback.

- `ThreePassPairingMatching` (LegacyMatching):
  - `build_preferences` mirrors `_evaluate_trade_preferences` (uses `compute_surplus` or `estimate_money_aware_surplus` based on `exchange_regime`).
  - `find_matches` mirrors pass 2 (mutual consent) and pass 3 (greedy fallback) behavior including telemetry-surplus semantics and deterministic ordering.

These wrappers allow `DecisionSystem` to delegate Pass 1/2/3 logic without changing outcomes.

---

## Engine integration (Phase 1)

Edits:

1) `Simulation.__init__` — add optional args with defaults:
   - `search_protocol: Optional[SearchProtocol] = None`
   - `matching_protocol: Optional[MatchingProtocol] = None`
   - If None, instantiate legacy wrappers.

2) `DecisionSystem` — delegate:
   - Pass 1: For unpaired agents, call `matching.build_preferences` (trade/both) and/or `search.select_forage_target` (forage/both), then run trade-vs-forage comparison in-engine (unchanged), using preference list’s discounted surplus for trade score.
   - Pass 2 and 3: Call `matching.find_matches` with the preference map to establish pairings; keep pass 3b cleanup and pass 4 logging unchanged.

3) Telemetry: No changes to telemetry writers; protocols only mutate agent state that the engine logs.

Acceptance for Phase 1: All existing scenarios produce identical telemetry (bitwise identical where floats allow; otherwise within 1e-10 for surplus fields) and no performance regression >10%.

---

## Phase plan and deliverables

### Phase 1 (Interfaces + Legacy wrappers + Delegation)

Duration: 3–5 days

Deliverables:
- `ProtocolContext`, `SearchProtocol`, `MatchingProtocol` defined
- Legacy wrappers implemented and wired
- `Simulation.__init__` accepts protocol objects
- `DecisionSystem` delegates to protocols for Pass 1/2/3
- Regression suite passes with telemetry equivalence

### Phase 2 (Extraction and new protocols)

Duration: 1–2 weeks

Deliverables:
- Extract forage and pairing logic out of `DecisionSystem` fully into legacy protocol classes (no delegation back)
- Implement `GreedyMatching` as alternative algorithm (max discounted surplus via greedy assignment)
- Optional: Implement `StableMatching` (Gale-Shapley) for pedagogy-only scenarios (static positions)
- Unit tests for protocol classes (>90% coverage for new modules)

### Phase 3 (Configuration & Registry)

Duration: 3–4 days

Deliverables:
- Protocol registry (`ProtocolRegistry.register(name, ctor)`) in `vmt_engine.protocols`
- Scenario schema: optional `protocols` block with `search`, `matching` names; loader resolves via registry
- Precedence: Python args > YAML config > legacy defaults
- Telemetry logs protocol names in `simulation_runs.config_json`

### Phase 4 (Validation & determinism)

Duration: 3–5 days

Deliverables:
- Determinism tests: 10 repeated runs per scenario → identical outputs
- Telemetry diff tool: compare decisions, pairings, trades tables (allow ε for floats)
- Performance baseline vs pre-modular engine (<10% slowdown)

### Phase 5 (Future) — Trade/Bargaining protocolization

Out of scope for this plan’s implementation window. Map `find_best_trade`, `find_all_feasible_trades`, and `find_compensating_block_generic` into a `TradeProtocol` with money-aware pair ranking and execution policy (minimum/maximum). Integrate after Phases 1–4 are complete.

---

## Testing strategy and acceptance criteria

Categories:

1) Unit tests
- SearchProtocol: claims compliance, deterministic target selection, idle-home fallback
- MatchingProtocol: cooldown filtering, preference ranking, mutual consent, greedy fallback

2) Integration tests
- Mode switching: verify pairing clear on mode change; foraging commitments cleared; pass 3b behavior
- Money regimes: barter_only, money_only, mixed; ensure pair_type propagation to preferences and trades

3) Regression tests
- Compare telemetry in `logs/telemetry.db`: runs, decisions, preferences, pairings, trades, tick_states
- Determinism: same seed ⇒ identical telemetry hashes across 10 runs

Acceptance criteria (Phase 1):
- Telemetry-equivalent decisions/pairings/trades (ε ≤ 1e-10 on floats)
- No nondeterminism detected across repeated runs
- Performance regression ≤ 10%

---

## Risks and mitigations

- Hidden coupling inside `DecisionSystem`: mitigate via thin wrappers that read/write agent state identically before extraction.
- Telemetry drift: keep logging centralized in `DecisionSystem`; use a diff tool to validate.
- Performance regressions: preserve data structures and iteration order; avoid extra scans.
- API churn: introduce protocols as optional constructor args; keep YAML unchanged until Phase 3.

---

## Implementation checklist

- [ ] Add protocols package with context and ABCs
- [ ] Add legacy wrappers
- [ ] Inject protocols into Simulation defaults
- [ ] Delegate Decision passes to protocols
- [ ] Regression suite for telemetry equivalence
- [ ] Extract logic fully (Phase 2)
- [ ] Add GreedyMatching and tests
- [ ] Add registry and YAML integration (Phase 3)
- [ ] Determinism/perf validation (Phase 4)

---

## Notes on invariants to preserve

- Process agents sorted by `agent.id` everywhere.
- Preference ranking key: `(-discounted_surplus, partner_id)`.
- Pairing persistence: `paired_with_id` only cleared by Trade failure or mode switch.
- Quotes stable within a tick; refresh in Housekeeping only.
- Resource claiming: only one harvester per tick if enabled; commitments persist until harvest or resource vanishes.
- Money-aware behavior: use `exchange_regime` to control allowed pairs and pair_type propagation.


