Brainstorming: Aligning Next Steps With Current Engine (v1.1)

**Current Status**: Working foraging + bilateral (integer, good-for-good) exchange

**Current Limitations (to address)**
- No budget constraint; no money
- No ability to toggle foraging/trading modes to create emergent budgets
- No market mechanism beyond bilateral matching

Context: The current engine and tests establish strong constraints and guarantees (determinism, ordering, and rounding) that new features must respect. The ideas below are scoped to fit the present architecture and the authoritative spec in `PLANS/Planning-Post-v1.md` and the enforced behaviors in `tests/`.

---

Deterministic guardrails to keep front-and-center

These are the non-negotiables that all proposals must satisfy (see `.github/copilot-instructions.md` and tests):
- Fixed 7-phase tick order (do not reorder): Perception → Decision → Movement → Trade → Forage → Resource Regeneration → Housekeeping.
- Deterministic iteration: agents by ascending `agent.id`; trade pairs by ascending `(min_id,max_id)`; use sorted containers only.
- Quotes derived from reservation bounds via `reservation_bounds_A_in_B(...)`; apply zero-inventory guard only for bounds; never shift inputs to `u()` or ΔU checks.
- Quote rule: `ask = p_min*(1+spread)`, `bid = p_max*(1-spread)`; refresh on any inventory change and again in housekeeping.
- One trade per pair per tick; round-half-up for quantities; compensating multi-lot scan with strict ΔU>0 for both sides.
- Cooldowns: failed trade attempts set mutual cooldown for `trade_cooldown_ticks`.
- Perception uses a frozen snapshot for the tick (no mid-tick information leaks).

---

1) Mode toggles: Foraging-only vs Trading-only windows (emergent budgets)

Goal: Create alternating windows where agents either only forage (accumulate inventories) or only trade (spend inventories), producing an emergent budget constraint without introducing money yet.

High-level design
- Add scenario params to `scenarios/schema.py` under `params` (all defaults keep current behavior):
  - `mode_schedule: {type: "none"|"global_cycle", forage_ticks: int, trade_ticks: int, start_mode: "forage"|"trade"}`
  - Optional refinements (defer if unnecessary): `movement_enabled_during: {forage: bool, trade: bool}`.
- Deterministic switch: At tick t, mode = start_mode, then alternate every X ticks (`(t // window) % 2`). Apply globally first; per-agent schedules are possible later but not needed now.
- Enforcement points across phases (no reordering):
  - Decision/Trade phases: If mode=forage-only, matching/trade attempts are skipped; set/keep cooldown semantics unchanged.
  - Forage phase: If mode=trade-only, foraging actions are skipped; resource regeneration and cooldown mechanics proceed as normal.
  - Quotes: Still refresh on any inventory changes (e.g., from trades), and again in housekeeping.

Assumptions (v1)
- Movement remains enabled in both modes to preserve spatial dynamics; can be toggled later via `movement_enabled_during` if desired.
- Cooldowns operate unchanged; failures in a disallowed phase should not occur (we skip the action earlier rather than attempt and fail).

Acceptance criteria (tests to add)
- When `mode_schedule.type == "global_cycle"`, agents never forage during trade windows and never trade during forage windows.
- Inventories strictly increase only via foraging in forage windows; strictly change only via trades in trade windows (except housekeeping adjustments like quotes refresh that do not change inventories).
- Deterministic switching on exact ticks regardless of agent count or ordering.
- No trade cooldown entries created during forage-only windows (because no trade attempt occurred).

Telemetry additions
- Log `mode_changes` with fields: `{tick, mode}`.
- Extend decision logs with `{tick, agent_id, mode}` to ease analysis of behavior by mode.

Open questions
- Do we want optional “rest” windows (no movement, no foraging, no trading) for clear phase separation experiments?
- Time-varying cycles (e.g., 5-10-5) can be encoded later as a list schedule: `[{mode: forage, ticks: 5}, {mode: trade, ticks: 10}, ...]`.

---

2) Money/numeraire: practical v1 compatible with current engine

Problem framing
- Pure good-for-good with integer blocks works well for two goods. Introducing money raises design choices: utility of money vs. budget-only constraints. Without money in utility, seller trades that increase only money require a way to credit money with utility via opportunity cost.

Design options and recommended path
- Option A (recommended for v1): Quasilinear utility with money as a third good M
  - Utility form: U(A,B,M) = U_goods(A,B) + λ·M, with U_goods from existing CES/Linear family, and λ ≥ 0.
  - Implementation fit: Treat M as a standard good with no foraging spawn and integer units (interpret units as “cents”). This keeps rounding and ΔU>0 checks unchanged and preserves determinism.
  - Quotes and reservation bounds: Money’s reservation bounds vs A/B come from the same bounds API; as usual, apply zero-guard only for bounds.
  - Scenario schema: allow `initial_inventories: {A: int, B: int, M: int}`; utilities mix can include a Quasilinear wrapper or parameter `lambda_money` on the utility factory.
- Option B: Budget-only money (no direct utility), impute value via opportunity cost from quotes
  - Compute a “shadow value” of money each tick from perceived quotes: λ_hat equals the best attainable marginal utility per unit of M given current reservation bounds and price quotes snapshot.
  - Pros: Closer to textbook budget-constraint view. Cons: Requires more perception logic and care to avoid mid-tick feedback; still needs a deterministic snapshot to avoid order dependence.
  - Suggest as Phase 2 after Option A; can keep the same external behavior by dynamically setting λ := λ_hat.

Core engine implications
- Keep integer accounting for M for now; extend to float later only if tests and rounding rules are broadened.
- Foraging: no generation of M; it’s exchange-only by design.
- Price search: unchanged; A↔M or B↔M trades use the same search and rounding semantics because M is “just another good.”

Acceptance criteria (tests to add)
- Quasilinear: Increasing M by 1 raises U by exactly λ; ΔU checks for trades involving M respect round-half-up and remain deterministic.
- Zero-guard: Bounds with M when A or B is zero behave per `tests/test_reservation_zero_guard.py` logic.
- Money-only scenarios execute without foraging of M and maintain one-trade-per-pair-per-tick.

Telemetry additions
- New table or extended schema: `money_flows` or `trades` augmented with `{is_money_leg: bool, good_pair: (X,M)}`.
- Summary stats: money velocity per component, money holdings distribution over time.

Open questions
- Choose λ calibration: constant per scenario param vs. dynamically imputed λ_hat (Option B).
- Do we normalize prices in money (M as numeraire) or allow cross-rates among goods including M? For v1, treat M as numeraire in UI.

---

3) Transition path from bilateral exchange to markets

Motivation: When many agents are transitively connected (within interaction distance via chains), bilateral matching may be a poor proxy for a market. We can switch mechanism within connected components while preserving determinism and one-trade constraints per tick.

Minimal viable market mechanism (Phase 1): posted-price market per component
- Component detection: In Perception, compute connected components using current `interaction_radius` graph; assign `market_id` deterministically by min agent id in the component.
- Price source: Use existing quote rule. Sellers post asks, buyers post bids; the market price per component can be a deterministic functional of these (e.g., mid of median ask and median bid, or simply select the lowest ask that is ≤ highest bid; ties broken by agent id).
- Matching rule per tick: Build ordered queues (by agent id) of willing buyers/sellers at the market price; pair in ascending `(buyer_id, seller_id)` and execute at most one block per agent per tick (preserve “one trade per tick” per agent). Quantity scan and ΔU>0 remain in force.
- Determinism: All sets and queues are sorted; perception snapshot fixed; same seven-phase order.

Phase 2: simple double auction (optional)
- Retain discrete time: clear once per tick per component.
- Orders: integer quantities, limit prices; time priority by agent id; price-time priority forms the book.
- Clearing: match best bid/ask with tie-breaks by id; execute integer blocks until exhaustion or one block per agent per tick.

Acceptance criteria (tests to add)
- For a connected component above a size threshold `market_min_size`, bilateral matching is disabled within the component and market matching is enabled; below threshold, bilateral remains.
- For equal conditions and seed, market outcomes are deterministic across runs.
- Price computation fulfills quote rule constraints and never violates ΔU>0 strictness for executed blocks.

Telemetry additions
- `market_events`: `{tick, market_id, component_size, price, matched_pairs}`.
- Price history and depth snapshots for educational visualization.

Open questions
- Threshold setting: fixed param vs. adaptive (e.g., based on density or turnover).
- Education-first design: start with posted-price for clarity, then consider double auction.

---

4) Testing plan (incremental, low-risk)

New unit tests (names illustrative)
- `test_mode_schedule_cycle.py`: verifies global cycle enforcement, no attempts occur in disallowed windows, deterministic switching.
- `test_money_quasilinear.py`: validates λ, ΔU>0, and reservation bounds behavior with a money good M.
- `test_market_component_switch.py`: checks component size detection and deterministic enable/disable of market mechanism.
- `test_market_posted_price_matching.py`: ensures deterministic pairing, one-trade-per-agent-per-tick, and ΔU>0.

Non-regression coverage
- Re-run existing tests for zero-guard, rounding, cooldowns, regeneration, and deterministic tick ordering to ensure no regressions.

---

5) Telemetry and tools updates (v1.1+ alignment)

Schema/logging deltas
- Add `mode_changes` table and add `mode` field to decision logs.
- Extend trades logging to mark money legs and market-id (if market mechanism enabled).
- Viewer: add simple overlays for current mode, money holdings distribution, and per-component price series.

Performance considerations
- Batch new writes similarly to current SQLite strategy to maintain performance.
- Avoid logging in inner loops beyond what’s needed for determinism and pedagogy.

---

6) Roadmap and migration to a new source-of-truth planning doc

Near-term deliverables
- Implement mode toggles (global cycle) with tests and minimal telemetry; ship as 1.2.x.
- Implement money as quasilinear third good (Option A), guarded behind scenario flags; ship as 1.3.x.
- Prototype posted-price market per connected component behind a feature flag; ship as 1.4.x.

Documentation consolidation
- Create `PLANS/Planning-Post-v2.md` as the new authoritative spec once the three features stabilize.
- Keep `PLANS/docs/*` synced with implementation and tests; add a short migration note in `DOCUMENTATION_INDEX.md` pointing to v2.

Open questions for v2 drafting
- Do we standardize on quasilinear money or evolve to budget-only money with dynamic λ_hat?
- Do we keep one-trade-per-agent-per-tick in markets, or allow multiple small matches with strict deterministic ordering?

---

Appendix: small, low-risk adjacent improvements
- Add a tiny `scenarios/mode_cycle_demo.yaml` showcasing a short forage/trade cycle.
- Add a `scenarios/money_quasilinear_demo.yaml` with simple λ and no resource spawning for M.
- Update the GUI launcher to expose the `mode_schedule` and money toggle when present in schema (optional, after core engine support).

Notes
- All proposals deliberately reuse existing reservation-bounds/quotes logic and rounding rules, minimizing surface area and risk.
- Determinism is preserved by design: snapshot-based perception, sorted structures, single-clearing per tick where applicable.