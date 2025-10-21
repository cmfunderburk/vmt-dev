# VMT Architecture and Documentation Review (2025-10-21)

Audience: Solo developer / project lead

Scope: Architectural coherence and educational effectiveness. Highlights critical items to manually review. Includes specific code references and actionable recommendations for a pre-release (0.0.1) readiness pass.

---

## Executive Summary

Overall, the engine presents a clean, deterministic 7-phase simulation loop with strong separation of concerns via system classes and extensive telemetry. The recent money-aware refactors (generic matching, pair-type tie-breaking, mode×regime separation, telemetry extensions) are well-integrated.

However, there are several high-impact misalignments and documentation gaps that will confuse users and constrain future modularization:

- P0 Architecture: Decision pairing still ranks neighbors using a barter-only surplus (`compute_surplus`), while trading is money-aware. In money/mixed regimes this can mis-prioritize partners and undermines the pedagogical goal of showing money’s liquidity benefits.
- P0 Documentation: Multiple referenced guides do not exist (user_guide_money.md, regime_comparison.md, technical/money_implementation.md, quick_reference.md, scenario_generator.md). The README links are broken.
- P1 Versioning Policy: README forbids numeric versioning but the project needs SemVer pre-release (0.0.1). Badges also claim “money system v1.0,” which conflicts with pre-release status.
- P1 Architectural Modularity: Search/Match/Bargain/Execute logic is mostly concentrated in `matching.py`/`trading.py`. It’s coherent, but lacks explicit protocol interfaces to enable swappable strategies.
- P1 Planning Drift: Initial plan emphasized “no databases” and PyQt6; current code uses SQLite telemetry (good choice) and PyQt5. This is fine, but should be acknowledged and aligned in docs.
- P2 Roadmap Claims vs Code: “mixed_liquidity_gated” regime appears in schema but gating logic is marked as future in code comments. The docs imply broader completion than implemented.

Recommended immediate actions before 0.0.1:
- Fix neighbor ranking to be money-aware or explicitly document the limitation and its teaching implications.
- Remove or gate broken doc links; add stubs or deliver the guides referenced by README and docs.
- Adopt SemVer 0.0.1; update README policy; normalize badges to reflect pre-release state.
- Publish a short Architecture Protocols plan (Search/Match/Bargain/Execute) with surface-level interfaces; begin incremental extraction.

---

## Findings (with code references)

### 1) Deterministic 7-phase loop and mode×regime separation

The main loop is clear and deterministic; mode gating is applied at system execution time and logged for observability.

```215:247:src/vmt_engine/simulation.py
    def step(self):
        """Execute one simulation tick with mode-aware phase execution.
        
        7-phase tick order (see PLANS/Planning-Post-v1.md):
        1. Perception → 2. Decision → 3. Movement → 4. Trade → 
        5. Forage → 6. Resource Regeneration → 7. Housekeeping
        """
        # Determine current mode
        if self.config.mode_schedule:
            new_mode = self.config.mode_schedule.get_mode_at_tick(self.tick)
            ...
        # Execute systems conditionally based on mode
        for system in self.systems:
            if self._should_execute_system(system, self.current_mode):
                system.execute(self)
        # Log tick state for observability (Phase 1)
        if self.telemetry:
            active_pairs = self._get_active_exchange_pairs()
            self.telemetry.log_tick_state(
                self.tick,
                self.current_mode,
                self.params.get('exchange_regime', 'barter_only'),
                active_pairs
            )
```

```309:336:src/vmt_engine/simulation.py
    def _get_active_exchange_pairs(self) -> list[str]:
        # If in forage mode, no trading occurs
        if self.current_mode == "forage":
            return []
        regime = self.params.get('exchange_regime', 'barter_only')
        if regime == "barter_only":
            return ["A<->B"]
        elif regime == "money_only":
            return ["A<->M", "B<->M"]
        elif regime in ["mixed", "mixed_liquidity_gated"]:
            return ["A<->M", "B<->M", "A<->B"]
        else:
            return []
```

Educational implication: The explicit separation clarifies “WHEN” (mode) vs “WHAT” (regime), which is excellent for teaching.

### 2) Pairing vs Trading: Money-awareness mismatch (P0)

Decision pairing ranks neighbors using barter-only surplus (`compute_surplus`), even when `exchange_regime` allows money trades. Trading then uses money-aware generic matching.

```95:144:src/vmt_engine/systems/decision.py
    def _evaluate_trade_preferences(self, agent: "Agent", view: dict, sim: "Simulation") -> None:
        ...
        for neighbor_id, neighbor_pos in neighbors:
            ...
            surplus = compute_surplus(agent, neighbor)
            if surplus > 0:
                distance = abs(agent.pos[0] - neighbor_pos[0]) + abs(agent.pos[1] - neighbor_pos[1])
                discounted_surplus = surplus * (beta ** distance)
                candidates.append((neighbor_id, surplus, discounted_surplus, distance))
```

```22:36:src/vmt_engine/systems/matching.py
def compute_surplus(agent_i: 'Agent', agent_j: 'Agent') -> float:
    """
    ...
    DEPRECATED: This function uses barter-only logic. For money-aware matching,
    use the generic matching primitives in Phase 2b.
    """
```

```258:346:src/vmt_engine/systems/trading.py
        if use_generic_matching:
            # Phase 2+: Money-aware matching
            self._trade_generic(agent, partner, sim)
        else:
            # Barter-only matching
            trade_pair(agent, partner, sim.params, sim.telemetry, sim.tick)
```

Impact:
- Architectural coherence: Rankings select partners on barter criteria even in money/mixed regimes. This can bias pair formation and downplay liquidity benefits of money.
- Educational effectiveness: Students might observe “odd” pair choices in money regimes that are optimal under barter-only measures.

Recommendation:
- Introduce a money-aware neighbor scoring function (e.g., “best feasible surplus across allowed pairs”) and use it in `DecisionSystem` when regime ∈ {money_only, mixed}.
- Alternatively, explicitly log and visualize the limitation if intentionally pedagogical, but this should be a conscious, documented choice.

### 3) Money-aware matching, tie-breaking, and execution

The generic matching primitives are robust and well-structured.

```657:711:src/vmt_engine/systems/matching.py
def find_all_feasible_trades(...):
    if exchange_regime == "barter_only":
        candidate_pairs = ["A<->B"]
    elif exchange_regime == "money_only":
        candidate_pairs = ["A<->M", "B<->M"]
    elif exchange_regime in ["mixed", "mixed_liquidity_gated"]:
        candidate_pairs = ["A<->B", "A<->M", "B<->M"]
    ...
```

```84:139:src/vmt_engine/systems/trading.py
def _rank_trade_candidates(self, candidates: list[TradeCandidate]) -> list[TradeCandidate]:
    # money-first policy when surplus equal: A<->M > B<->M > A<->B
```

This is a strong base for protocol modularization.

### 4) Quotes and reservation bounds (money-aware API)

Quotes correctly compute barter and monetary prices from utility and λ, with sensible epsilon handling.

```25:68:src/vmt_engine/systems/quotes.py
def compute_quotes(agent: 'Agent', spread: float, epsilon: float, money_scale: int = 1) -> dict[str, float]:
    ...
    p_min_A_in_B, p_max_A_in_B = agent.utility.reservation_bounds_A_in_B(A, B, epsilon)
    ...
    mu_A = agent.utility.mu_A(A, B)
    price_A_in_M = (mu_A / lambda_m) * money_scale if lambda_m > epsilon else 1e6 * money_scale
```

Educationally, this enables clear explanation of reservation prices and quasilinear money.

### 5) Telemetry and integrity

Housekeeping refreshes quotes conditionally and validates pairings; telemetry coverage appears comprehensive.

```12:25:src/vmt_engine/systems/housekeeping.py
    def execute(self, sim: "Simulation") -> None:
        ...
        for agent in sim.agents:
            refresh_quotes_if_needed(...)
        # Verify pairing integrity
        self._verify_pairing_integrity(sim)
        # Log telemetry snapshots
```

### 6) Schema and loader – regimes and money

Scenario params include regimes, money mode, and validation for money inventory in money/mixed regimes.

```88:114:src/scenarios/schema.py
    exchange_regime: Literal["barter_only", "money_only", "mixed", "mixed_liquidity_gated"] = "barter_only"
    money_mode: Literal["quasilinear", "kkt_lambda"] = "quasilinear"
    money_scale: int = 1
```

---

## Documentation Review

### Broken or Missing Documents (P0)

Referenced from README and docs but not present in the repository:
- `docs/user_guide_money.md`
- `docs/regime_comparison.md`
- `docs/technical/money_implementation.md`
- `docs/quick_reference.md`
- `docs/guides/scenario_generator.md`

Action: Add these documents or remove/replace links. For 0.0.1, at least publish concise stubs with scope, status, and ETA.

### Versioning Policy Conflicts (P1)

- README currently forbids numeric versioning and instructs date-based labeling, yet the project intends to adopt SemVer 0.0.1 (and badges show “money system v1.0”).
  - Action: Update README to adopt SemVer. Move the date-based guidance to a historical note. Normalize badges to reflect pre-release status.

### Roadmap Claims vs Code (P2)

- `mixed_liquidity_gated` appears in schema and docs but gating logic is marked as future in code comments.
  - Action: Mark status explicitly in docs with [IMPLEMENTED]/[PLANNED] badges like typing overview.

### Educational Clarity (P1)

- Decision pairing using barter-only surplus in money regimes can reduce the clarity of “why money helps.”
  - Action: Either align pairing’s scoring with money-aware surplus or annotate the UI/docs with a pedagogical note and a visualization (e.g., overlay showing barter-only vs money-aware ranking for comparison).

---

## Recommendations (Prioritized)

### P0 – Blockers for 0.0.1
- Fix neighbor ranking in `DecisionSystem` for money/mixed regimes:
  - Introduce a function that computes “best feasible discounted surplus across allowed pairs” per neighbor (reuse `find_best_trade` or a lighter-weight estimator for speed).
  - Wire it under a policy flag (temporary) to keep risk bounded and tests stable.
- Replace/restore broken documentation links with real content or explicit stubs.

### P1 – High Priority for Pre-1.0
- Adopt SemVer 0.0.1; update README and badges; add `__version__` in a top-level package; add CHANGELOG entries using Keep a Changelog.
- Begin protocol extraction for Search/Match/Bargain/Execute (see roadmap document) while maintaining backward compatibility and determinism rules.
- Clarify `mixed_liquidity_gated` as [PLANNED] unless fully implemented; add acceptance criteria.

### P2 – Medium Priority
- Consolidate and elevate “Type System & Contracts” pattern of [IMPLEMENTED]/[PLANNED] badges across all docs to end ambiguity.
- Add a short “Learning Objectives” checklist to the GUI overlays (e.g., toggle to show why a pair was chosen, what quotes overlapped, which tie-break applied).

---

## 0.0.1 Readiness Checklist

- Architecture
  - [ ] Decision pairing money-aware in money/mixed regimes (or documented rationale with UI support)
  - [ ] Determinism preserved; ranking/tie-breakers tested
- Documentation
  - [ ] Broken links resolved or stubs added
  - [ ] SemVer policy adopted in README; badges normalized
  - [ ] Minimal user guide for money + regime comparison published
- Telemetry & Tests
  - [ ] Trades table reliably records `exchange_pair_type` (mixed regimes covered)
  - [ ] One end-to-end test validating money-first tie-breaking in mixed regime
  - [ ] Basic performance sanity run unchanged (O(N) preserved)

---

## Notes on Educational Effectiveness

Strengths:
- Visual toggles (targets, overlays), co-location rendering, telemetry-backed log viewer.
- Deterministic, step-wise convergence behavior aligns with pedagogy.

Improvements:
- Visualize the decision basis: show top-3 partner rankings and indicate whether ranking used barter-only vs money-aware logic.
- Add a “Why this trade?” overlay: quotes, chosen price, rounding to integers, and first-acceptable-trade principle.

---

## Appendix: Additional Code References

- Trade candidate ranking (money-first tie-breaking):
```84:121:src/vmt_engine/systems/trading.py
    def _rank_trade_candidates(self, candidates: list[TradeCandidate]) -> list[TradeCandidate]:
        # Define pair type priority for money-first policy
        PAIR_PRIORITY = {
            "A<->M": 0,
            "B<->M": 1,
            "A<->B": 2,
            "B<->A": 2,
            "M<->A": 0,
            "M<->B": 1,
        }
```

- Housekeeping: pairing integrity repair and snapshots:
```33:46:src/vmt_engine/systems/housekeeping.py
    def _verify_pairing_integrity(self, sim: "Simulation") -> None:
        for agent in sim.agents:
            if agent.paired_with_id is not None:
                partner_id = agent.paired_with_id
                partner = sim.agent_by_id.get(partner_id)
                if partner is None or partner.paired_with_id != agent.id:
                    sim.telemetry.log_pairing_event(
                        sim.tick, agent.id, partner_id, "unpair", "integrity_repair"
                    )
                    agent.paired_with_id = None
```


