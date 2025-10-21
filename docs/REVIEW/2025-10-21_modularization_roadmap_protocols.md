# Modularization Roadmap: Search / Match / Bargain / Execute Protocols (2025-10-21)

Audience: Solo developer / project lead

Goal: Enable swappable protocols for Search, Match, Bargain, and Execute without breaking determinism, telemetry, or educational clarity. Prioritize architectural coherence and pedagogical transparency.

---

## Principles and Constraints

- Determinism: All strategies must produce identical results for a given seed; tie-breakers are explicit and stable.
- Separation of Concerns: Distinct protocol surfaces for Search, Match, Bargain, Execute.
- Observability: Telemetry logs the chosen strategy and its rationale; UI can visualize decisions.
- Backward Compatibility: Default strategies match current behavior; tests codify invariants.

---

## Current State (Baseline)

- Search: DecisionSystem ranks neighbors with distance-discounted barter surplus.
- Match: Pairing via three-pass algorithm (mutual consent, greedy fallback), O(N) behavior through persistent pairings.
- Bargain: Bilateral compensating-block search with first-acceptable-trade principle; money-aware generic primitives.
- Execute: Inventory updates with conservation and non-negativity; quotes refreshed in housekeeping; telemetry logging.

Gap: Search scoring is barter-only while Bargain is money-aware under money/mixed regimes.

---

## Target Interfaces

Define protocol interfaces with simple, typed call signatures (Python protocols or ABCs) and deterministic semantics.

1) SearchProtocol
- Input: (agent, neighbors_view, simulation_context)
- Output: Ranked list of partner candidates with scores and distances
- Determinism: Sorting by (-score, partner_id)
- Examples:
  - BarterSurplusSearch (current)
  - MoneyAwareFeasibleSurplusSearch (new; respects exchange_regime)

2) MatchProtocol
- Input: Ranked preferences for all agents
- Output: Pairings (agent_id ↔ partner_id) with reason codes
- Determinism: Mutual-consent pass; greedy fallback with stable tie-breakers
- Examples:
  - ThreePassCommitment (current)
  - MarketLocalCluster (future for posted-price grouping)

3) BargainProtocol
- Input: (agent_i, agent_j, exchange_regime, params)
- Output: Either first feasible trade or ranked feasible trades (depending on regime)
- Determinism: Fixed pair iteration order; price candidate generation stable
- Examples:
  - FirstAcceptableBilateral (current for barter_only/money_only)
  - MixedFeasibleSetWithMoneyFirstTieBreak (current for mixed)

4) ExecuteProtocol
- Input: (trade tuple)
- Output: Mutated inventories; flags; telemetry logging
- Determinism: Inventory conservation; non-negativity; single source of truth for logging
- Examples:
  - InventoryConservingAtomic (current)

---

## Incremental Extraction Plan

Phase 1 (Safe Refactor)
- Extract SearchProtocol and BargainProtocol surfaces, with concrete adapters wrapping the current functions (`compute_surplus`, `find_best_trade`, `find_all_feasible_trades`).
- Add a money-aware Search implementation that approximates “best feasible discounted surplus across allowed pairs.” Option A (fast): use quotes to approximate surplus without full block search; Option B (precise): call into `find_best_trade` per neighbor (bounded by small caps for performance).
- Wire DecisionSystem to choose SearchProtocol by `exchange_regime`.

Phase 2 (Feature Parity and Tests)
- Re-run full test suite; add tests for parity (barter_only unchanged) and correctness in money_only/mixed (pairing decisions differ only when economically justified).
- Extend telemetry with `search_strategy`, `match_strategy`, `bargain_strategy`, and surface them in the log viewer.

Phase 3 (MatchProtocol extraction)
- Encapsulate the three-pass pairing into a pluggable MatchProtocol.
- Prepare an experimental market-based matcher (posted-price within local components) behind a feature flag.

Phase 4 (Docs and Educational Overlays)
- Document protocol interfaces in `docs/technical/`.
- Add UI overlays explaining: why this partner, which pairs were allowed, what tie-break applied, and which bargain protocol executed.

---

## Acceptance Criteria

- Determinism: Bit-identical outcomes for barter_only with default strategies.
- Money-Aware Search: In money_only/mixed regimes, neighbor ranking reflects feasible monetary opportunities; tests show improved educational clarity.
- Observability: Strategy names and key parameters are logged; the viewer can filter by strategy.
- Backward Compatibility: Scenarios and CLI/GUI continue to run unchanged.

---

## Risks and Mitigations

- Performance Regressions: Cap neighbor evaluations; reuse quotes; avoid O(N^2) scans; maintain persistent pairing model.
- Complexity Creep: Keep default strategies simple; use feature flags for experimental protocols.
- Pedagogical Ambiguity: Provide overlays and tooltips that articulate the chosen protocol and economic rationale.

---

## Next Steps (Actionable)

- Implement `SearchProtocol` interface and two implementations:
  - `BarterSurplusSearch` (default for barter_only)
  - `MoneyAwareFeasibleSurplusSearch` (default for money_only/mixed)
- Inject protocol selection into `DecisionSystem` by regime; add unit tests.
- Extract `BargainProtocol` facade over existing generic matching functions.
- Add telemetry fields for `search_strategy`, `bargain_strategy`.
- Prepare doc stubs for the missing guides and update README links.
