# Deep Economic Logic Research Prompt
## VMT Codebase Review & Issue Resolution (2025-10-21)

**Purpose:** This prompt guides a comprehensive analysis of VMT's economic foundations to (1) address issues raised in `docs/REVIEW/`, (2) validate theoretical correctness of utility functions, matching algorithms, and trade execution, and (3) ensure pedagogical clarity for teaching microeconomics.

**Audience:** AI assistant conducting deep architectural review OR human researcher conducting systematic verification.

**Scope:** Economic primitives (utility functions, marginal utilities, reservation pricing), matching/pairing logic, trade execution, money system integration, and their interactions with determinism requirements.

---

## I. Context: What is VMT?

VMT is a **deterministic spatial agent-based simulation** for teaching microeconomics through visualization. Agents with heterogeneous preferences forage resources and engage in bilateral trade (barter or monetary exchange) on an NxN grid. The system emphasizes:

1. **Pedagogical Clarity:** Economic concepts (MRS, reservation prices, surplus) are visualized and logged for student analysis
2. **Reproducibility:** Same seed → identical outcomes; critical for classroom demos and research
3. **Theoretical Rigor:** All utility functions, marginal utilities, and trade mechanisms must satisfy standard microeconomic axioms

**Architecture:** 7-phase deterministic tick cycle (Perception → Decision → Movement → Trading → Foraging → Resource Regeneration → Housekeeping). All agent loops iterate in sorted ID order.

---

## II. High-Priority Issues from `docs/REVIEW/`

### P0: Pairing-Trading Money-Awareness Mismatch

**Issue:** Decision phase (pairing) ranks neighbors using **barter-only surplus** (`compute_surplus()` in `matching.py`), even when `exchange_regime ∈ {money_only, mixed}`. However, trading phase uses **money-aware generic matching** (`find_best_trade()`, `find_all_feasible_trades()`).

**Educational Impact:** Students may see agents paired with suboptimal partners because the pairing algorithm doesn't recognize monetary trade opportunities. This undermines the pedagogical goal of demonstrating money's role as a medium of exchange.

**Files to Investigate:**
- `src/vmt_engine/systems/decision.py` (lines 95-144: `_evaluate_trade_preferences`)
- `src/vmt_engine/systems/matching.py` (lines 22-76: `compute_surplus`)
- `src/vmt_engine/systems/trading.py` (money-aware trade finding)

**Research Questions:**
1. What is the **quantitative difference** in neighbor rankings between barter-surplus vs money-aware surplus in representative scenarios?
2. Does the mismatch cause **pairing instability** (agents repeatedly pair/unpair searching for better matches)?
3. Can we implement a **lightweight money-aware surplus estimator** for pairing that maintains O(N) performance?
4. What are the **tie-breaking rules** if money-aware surplus introduces new ties?

**Deliverables:**
- [ ] Trace through 3+ scenarios (barter_only, money_only, mixed) to document pairing choices vs theoretically optimal pairings
- [ ] Quantify surplus loss from mismatched pairings (aggregate over 100 ticks)
- [ ] Propose lightweight money-aware ranking algorithm with determinism analysis
- [ ] Design test cases ensuring barter_only scenarios remain bit-identical

### P0: Utility Function Zero-Inventory Handling

**Issue:** Multiple utility types (CES, Translog, Stone-Geary) handle zero inventories with epsilon guards for MRS calculations, but documentation and implementation consistency varies.

**Files to Investigate:**
- `src/vmt_engine/econ/utility.py` (all 5 utility classes)
- Tests: `tests/test_reservation_zero_guard.py`, `tests/test_utility_ces.py`

**Research Questions:**
1. Are epsilon guards applied **consistently** across all utility types?
2. Do `reservation_bounds_A_in_B()` methods correctly handle **boundary cases** (A=0, B=0, both zero)?
3. Are **marginal utilities** (`mu_A`, `mu_B`) well-defined at zero inventories?
4. Does the CES utility correctly implement the **Cobb-Douglas special case** (ρ→0)?
5. For **Stone-Geary** (LES with subsistence levels), are negative effective inventories (A - γ_A < 0) handled correctly?

**Deliverables:**
- [ ] Comparative table: All 5 utility types × zero-handling strategies × theoretical correctness
- [ ] Verify MRS continuity and monotonicity properties at boundaries
- [ ] Check that `u_goods()` (canonical API) never uses epsilon shifts (only MRS ratios should)
- [ ] Validate Stone-Geary subsistence constraints against economic textbooks (Deaton & Muellbauer, etc.)

### P1: Exchange Regime vs Mode Schedule Interaction

**Issue:** `exchange_regime` (barter_only, money_only, mixed, mixed_liquidity_gated) controls **what** trades are allowed. `mode_schedule` (forage, trade, both) controls **when** systems run. Interactions need validation.

**Files to Investigate:**
- `src/vmt_engine/simulation.py` (lines 215-247: `step()` method, lines 309-336: `_get_active_exchange_pairs`)
- `src/scenarios/schema.py` (regime and mode definitions)
- Tests: `tests/test_mode_regime_interaction.py`

**Research Questions:**
1. What happens when mode changes from `trade` → `forage` with active pairings? (Expected: unpair without cooldown)
2. In `mixed` regime, is **money-first tie-breaking** correctly logged in telemetry? (`exchange_pair_type` field)
3. Does `mixed_liquidity_gated` correctly enforce liquidity constraints, or is it partially implemented?
4. Are there **edge cases** where mode and regime conflict (e.g., forage mode in money_only regime)?

**Deliverables:**
- [ ] Decision tree: all regime × mode combinations → expected system behavior
- [ ] Verify telemetry logs capture mode transitions and unpair reasons
- [ ] Review `mixed_liquidity_gated` implementation status; document as [PLANNED] if incomplete
- [ ] Test suite additions for mode toggle edge cases

### P1: Money-Aware API Consistency

**Issue:** Utility functions expose both **legacy API** (`u()`, `mu()`) and **money-aware API** (`u_goods()`, `mu_A()`, `mu_B()`, future `u_total()`). Consistency and deprecation path unclear.

**Files to Investigate:**
- `src/vmt_engine/econ/utility.py` (base class `Utility` and all subclasses)
- `src/vmt_engine/systems/matching.py` (quote calculation usage)
- Agent class: inventory and lambda (marginal utility of money) integration

**Research Questions:**
1. Are all utility subclasses **consistently implementing** both APIs?
2. Is `u_total(inventory, params)` defined anywhere? (Expected: U_goods + λ·M for quasilinear money)
3. Do agents' `lambda` values update correctly after trades? (Expected: λ = mu_M = constant initially, may evolve)
4. Are quotes (`bid_A_in_B`, `ask_A_in_B`) computed using `u_goods()` or legacy `u()`?

**Deliverables:**
- [ ] API compliance matrix: 5 utility types × (u_goods, mu_A, mu_B, reservation_bounds) implementation status
- [ ] Trace quote calculation through one agent lifecycle (spawn → forage → trade → quote refresh)
- [ ] Propose `u_total()` signature and integration plan if not yet implemented
- [ ] Document deprecation timeline for legacy API

---

## III. Theoretical Verification Checklist

### Utility Function Properties

For **each utility type** (CES, Linear, Quadratic, Translog, Stone-Geary), verify:

**[ ] Non-Satiation (Weak Monotonicity)**
- ∂U/∂A ≥ 0 and ∂U/∂B ≥ 0 for all feasible (A, B)
- Exception: Quadratic may have bliss points where MU = 0

**[ ] Convex Preferences (Diminishing MRS)**
- MRS_A_in_B = MU_A / MU_B is non-increasing in A (holding B constant)
- Check numerical derivatives or analytic second-order conditions

**[ ] Reservation Pricing Consistency**
- For seller with (A, B): reservation price p_ask ≥ MRS (lose 1A, need p_ask·B to maintain utility)
- For buyer: reservation price p_bid ≤ MRS (gain 1A, willing to pay p_bid·B)
- Verify `reservation_bounds_A_in_B()` returns (p_ask, p_bid) in correct order

**[ ] Money-Aware Total Utility (if implemented)**
- U_total = U_goods(A, B) + λ·M should be quasilinear in M
- λ (marginal utility of money) should equal mu_M and be constant for linear money utility

**[ ] Special Cases**
- CES: Verify ρ→0 limit reproduces Cobb-Douglas (log-linear utility)
- Linear: Verify MRS = vA/vB is constant (perfect substitutes)
- Quadratic: Verify bliss point behavior and non-negativity constraints

### Matching and Trade Execution

**[ ] Bilateral Surplus Definition**
- Surplus = (buyer's max price - seller's min price) × quantity
- Verify `compute_surplus()` implements this for barter (direction-agnostic)
- For money trades: Verify `find_best_trade()` considers A↔M and B↔M separately

**[ ] First-Acceptable Trade Principle**
- In barter_only and money_only: First feasible trade with positive surplus is executed
- In mixed regime: All feasible trades ranked, money trades preferred on ties

**[ ] Inventory Conservation**
- For barter (A↔B): ΔA_i + ΔA_j = 0, ΔB_i + ΔB_j = 0
- For money trades (A↔M): ΔA_i = -ΔM_buyer / price, ΔM_seller = ΔM_buyer
- Check rounding: `floor(price * ΔA + 0.5)` for round-half-up

**[ ] Non-Negativity Constraints**
- No trade executes if any agent's inventory would go negative
- Verify pre-trade feasibility checks in `execute_trade()`

**[ ] Quote Refresh Discipline**
- Quotes refresh **only in Housekeeping phase** for agents with inventory changes
- No mid-tick quote mutations (violates determinism)

### Determinism Properties

**[ ] Sorted Agent Iteration**
- All agent loops use `sorted(sim.agents, key=lambda a: a.id)`
- Verify in: Perception, Decision, Movement, Trading, Foraging, Housekeeping

**[ ] Tie-Breaking Rules**
- Pairing: If multiple neighbors have equal surplus, choose **lowest ID**
- Trading: If multiple pair types have equal surplus in mixed regime, choose **money-first**
- Movement: On ties, prioritize x-axis, then negative direction

**[ ] RNG Discipline**
- All randomness uses `sim.rng` (numpy PCG64 with explicit seed)
- No usage of Python `random` module or unsorted dict iteration

---

## IV. Code Archaeology Tasks

### Task A: Trace One Complete Trade Lifecycle

**Scenario:** Three agents (ID 0, 1, 2) in a triangle, mixed regime, both mode. Tick 10.

**Trace:**
1. **Perception (Phase 1):** What does Agent 0 observe? (neighbors, resources, frozen snapshot)
2. **Decision (Phase 2):** How does Agent 0 rank neighbors? (compute_surplus calls, distance discounting)
3. **Pairing (Phase 2):** Does Agent 0 pair? (mutual consent? greedy fallback?)
4. **Movement (Phase 3):** Where does Agent 0 move? (toward partner, resource, or hold position?)
5. **Trading (Phase 4):** If paired and adjacent, what trades are evaluated? (find_all_feasible_trades output)
6. **Execution (Phase 4):** Which trade executes? (money-first tie-breaking? inventory updates?)
7. **Housekeeping (Phase 7):** Does Agent 0's quote refresh? (inventory changed? lambda updated?)
8. **Telemetry:** What gets logged? (trade_events row with exchange_pair_type, dM, lambdas)

**Deliverable:** Annotated code walkthrough with actual variable values (use debugger or print statements).

### Task B: Compare Barter vs Money Pairing Outcomes

**Scenario:** Load `scenarios/demos/demo_01_simple_money.yaml` with two seeds.

**Analysis:**
1. Run in `barter_only` regime for 100 ticks → log all pairing events
2. Run in `money_only` regime for 100 ticks with same seed → log all pairing events
3. Compare: Which agents paired differently? Why?
4. Quantify: Total surplus realized in each regime (sum of trade surpluses)
5. Hypothesize: Would money-aware pairing improve money_only outcomes?

**Deliverable:** Comparative table and surplus graphs.

### Task C: Stress-Test Zero-Inventory Edge Cases

**Scenarios:**
1. Agent starts with (A=0, B=10): Can it buy A with B? (Expected: Yes, quotes valid)
2. Agent starts with (A=10, B=0): Can it sell A for B? (Expected: Yes, quotes valid)
3. Agent starts with (A=0, B=0): What are quotes? (Expected: May be undefined or extreme values)
4. Stone-Geary with γ_A = 5: Agent has A=3 → effective A = -2. What happens? (Expected: Cannot trade A until above subsistence)

**Deliverable:** Test matrix with all 5 utility types × 4 edge cases → pass/fail + explanation.

---

## V. Validation Against Economic Textbooks

### Reference Texts

1. **Mas-Colell, Whinston, Green** (MWG): *Microeconomic Theory* (1995)
   - Chapter 3: Consumer preferences and utility
   - Chapter 10: Competitive markets and equilibrium
   - Appendix on functional forms (CES, translog)

2. **Varian**: *Microeconomic Analysis* (3rd ed, 1992)
   - Chapter 7: Consumer choice
   - Chapter 9: Exchange economy and Edgeworth box
   - Chapter 18: Reservation prices and willingness to pay

3. **Deaton & Muellbauer**: *Economics and Consumer Behavior* (1980)
   - Chapter 3: Linear Expenditure System (Stone-Geary)
   - Subsistence levels and budget constraints

### Validation Tasks

**[ ] CES Utility Form**
- VMT implementation: `U = [wA * A^ρ + wB * B^ρ]^(1/ρ)`
- MWG reference: Section 3.B, page 53
- Verify: ρ < 1 → complementarity, ρ > 1 → substitutability, ρ→0 → Cobb-Douglas

**[ ] Marginal Rate of Substitution**
- VMT implementation: `MRS = (wA/wB) * (A/B)^(ρ-1)` for CES
- Varian reference: Definition 7.2, page 117
- Verify: MRS equals slope of indifference curve; reservation price consistency

**[ ] Bilateral Trade Surplus**
- VMT implementation: `surplus = (p_bid_buyer - p_ask_seller) * quantity`
- Varian reference: Chapter 9 (Edgeworth box), gains from trade
- Verify: Surplus maximization ↔ Pareto efficiency in bilateral setting

**[ ] Quasilinear Utility with Money**
- VMT implementation: (To verify if implemented) `U_total = U(A, B) + λ·M`
- MWG reference: Section 3.B, page 47 (quasilinear preferences)
- Verify: λ is marginal utility of money; budget constraint role

**[ ] Stone-Geary Subsistence**
- VMT implementation: `U = Π_i (x_i - γ_i)^β_i`
- Deaton & Muellbauer reference: Chapter 3, equations (3.1)-(3.4)
- Verify: γ_i are subsistence levels; demand system properties

**Deliverable:** Annotated bibliography with page references and correctness attestations.

---

## VI. Pedagogical Impact Analysis

### Question 1: Does the pairing mismatch confuse students?

**Hypothetical Scenario:** Instructor shows money_only simulation. Agent A can see two neighbors:
- Neighbor X: High barter surplus (both have goods, complementary preferences)
- Neighbor Y: High monetary surplus (X wants to sell A for money, Y wants to buy A with money)

Current pairing algorithm chooses X (barter surplus). Trading phase finds no feasible A↔M trades with X (not in money_only regime). Agent A wastes tick.

**Student Interpretation:** "Why did Agent A pair with X when X can't trade in this regime?" → Confusion about exchange regimes.

**Proposed Fix Impact:** Money-aware pairing chooses Y. Trade executes. Student sees: "Agent A chose partner Y because money trades were possible." → Clear.

**Deliverable:** Before/after scenario narratives for classroom use.

### Question 2: Do utility function edge cases mislead?

**Concern:** If zero-inventory quotes are unstable (e.g., CES returns `inf` or `nan`), students see agents "refusing" trades when they should be desperate.

**Test:** Starving agent with (A=0, B=0) encounters resource. Does it forage correctly? Does its desperation show in quotes?

**Deliverable:** Quote visualization examples showing boundary behavior.

### Question 3: Is money-first tie-breaking pedagogically justified?

**Current Rule:** In mixed regime, if A↔B and A↔M have equal surplus, execute A↔M.

**Economic Rationale:** Money provides liquidity; agents prefer monetary trades to avoid "double coincidence of wants" problem.

**Student Clarity:** Is this visible in telemetry? Can students query: "How often did money-first matter?"

**Deliverable:** Telemetry query + classroom discussion guide.

---

## VII. Implementation Recommendations

Based on findings, propose:

### 7.1 Money-Aware Pairing Options

**Option A: Lightweight Estimator**
- Use agents' existing quotes to approximate best feasible surplus across allowed pair types
- Fast: O(1) per neighbor, no compensating-block search
- Trade-off: May miss non-linear opportunities

**Option B: Capped Exhaustive Search**
- Call `find_best_trade()` for top-K neighbors (K=3?)
- Accurate: Uses full bargaining logic
- Trade-off: O(K) per agent per tick; ensure determinism

**Option C: Hybrid**
- Use estimator for ranking; call exhaustive for top-1 candidate only
- Balances performance and accuracy

**Recommendation:** [Choose after performance benchmarking]

### 7.2 Utility API Consolidation

**Proposal:**
1. Deprecate `u()` and `mu()` in favor of `u_goods()`, `mu_A()`, `mu_B()`
2. Implement `u_total(inventory, params)` for all utility types (trivial: just add λ·M)
3. Add `compute_lambda()` method to update λ based on inventory changes
4. Migrate all quote calculations to money-aware API

**Timeline:** Phase 2b (current sprint?)

### 7.3 Documentation Additions

**Create missing guides:**
- [ ] `docs/user_guide_money.md`: End-user walkthrough of money system features
- [ ] `docs/technical/regime_comparison.md`: Architect-level regime logic deep dive
- [ ] `docs/technical/money_implementation.md`: Code-level money-aware API reference
- [ ] `docs/guides/scenario_generator.md`: Template-based scenario creation guide

**Update existing docs:**
- [ ] `README.md`: Fix broken links, align versioning policy (adopt 0.0.1)
- [x] `docs/1_project_overview.md`: Acknowledge SQLite telemetry and PyQt6 as intentional choices
- [ ] `.github/copilot-instructions.md`: Add money-aware pairing status and API migration plan

---

## VIII. Acceptance Criteria

### Before marking this review complete:

**[ ] Zero Regressions**
- All existing tests pass (316+ tests)
- Determinism tests remain bit-identical for barter_only scenarios

**[ ] Economic Correctness Verified**
- All 5 utility types pass zero-inventory stress tests
- Reservation bounds consistent with MRS across all utility types
- Trade surplus calculations validated against textbook definitions

**[ ] Pairing-Trading Alignment**
- Decision phase uses money-aware surplus when `exchange_regime ∈ {money_only, mixed}`
- OR: Limitation documented with pedagogical mitigation strategy

**[ ] Telemetry Integrity**
- All trades log `exchange_pair_type` correctly
- Mode transitions and unpair events logged with reasons
- Lambda values logged in trade_events for post-hoc analysis

**[ ] Documentation Complete**
- Missing guides created or stubbed with [PLANNED] status
- `docs/REVIEW/` issues addressed or tracked in project roadmap
- API migration plan documented if legacy methods remain

---

## IX. Deliverable Artifacts

### A. Research Report

**File:** `docs/tmp/economic_logic_audit_YYYY-MM-DD.md`

**Contents:**
1. Executive summary: Key findings and recommendations
2. Theoretical verification results: Utility function compliance table
3. Pairing-trading mismatch analysis: Quantified impact
4. Edge case stress test results: Pass/fail matrix
5. Textbook cross-references: Correctness attestations
6. Proposed implementation plan: Options and timelines

### B. Test Suite Additions

**Files:** `tests/test_economic_correctness_*.py`

**Coverage:**
- Zero-inventory utility function properties
- Money-aware pairing vs barter pairing outcomes
- Mode × regime interaction edge cases
- Quasilinear utility integration (if implemented)

### C. Annotated Code Tour

**File:** `docs/tmp/code_tour_economic_logic.md`

**Sections:**
1. Utility function architecture walkthrough
2. Pairing algorithm trace (decision.py)
3. Trade execution lifecycle (trading.py, matching.py)
4. Quote refresh discipline (housekeeping.py)
5. Telemetry integration points (db_loggers.py)

### D. Classroom Demo Scenarios

**Files:** `scenarios/demos/demo_XX_*.yaml` (new)

**Scenarios:**
1. `demo_XX_pairing_comparison.yaml`: Barter vs money-aware pairing side-by-side
2. `demo_XX_zero_inventory_survival.yaml`: Agents start with (0, 0), must forage and trade
3. `demo_XX_money_first_tie_breaking.yaml`: Showcase when money-first matters

---

## X. Research Process Workflow

### Phase 1: Context Gathering (2-4 hours)
1. Read all `docs/REVIEW/*.md` files thoroughly
2. Read `docs/1_project_overview.md` and `docs/2_technical_manual.md`
3. Skim all 5 utility class implementations
4. Trace one complete tick cycle in debugger

### Phase 2: Theoretical Verification (4-6 hours)
1. For each utility type: Verify properties checklist (Section III)
2. Cross-reference with textbooks (Section V)
3. Document discrepancies or special cases

### Phase 3: Empirical Analysis (3-5 hours)
1. Run comparative scenarios (Task B)
2. Stress-test edge cases (Task C)
3. Trace trade lifecycle (Task A)

### Phase 4: Synthesis and Recommendations (2-3 hours)
1. Compile findings into research report (Section IX.A)
2. Draft implementation plan (Section VII)
3. Propose test additions (Section IX.B)

### Phase 5: Documentation and Handoff (1-2 hours)
1. Create missing doc stubs or full guides
2. Update copilot instructions and roadmap
3. Prepare code tour for onboarding (Section IX.C)

**Total Estimated Effort:** 12-20 hours for comprehensive review

---

## XI. Open Questions for Investigator

1. **Scope Decision:** Should this review include performance benchmarking (e.g., O(N²) pairing concerns), or focus purely on economic correctness?

2. **Backward Compatibility:** If money-aware pairing changes outcomes for mixed regime, should we add a feature flag for old behavior?

3. **Mixed Liquidity Gated:** Is this regime fully implemented or partially stubbed? Should it be excluded from this audit?

4. **Lambda Evolution:** Are agents' λ values currently static, or do they update based on inventory changes? Should they?

5. **Textbook Selection:** Are there preferred references beyond MWG/Varian/Deaton-Muellbauer? (e.g., Jehle & Reny, Nicholson & Snyder?)

6. **Student Level:** Is target audience undergraduate (simpler explanations) or graduate (full rigor)?

---

## XII. Success Metrics

This research effort succeeds if:

1. **Confidence:** Developer can attest that all economic primitives are theoretically sound
2. **Clarity:** Students using VMT see accurate, pedagogically clear demonstrations of microeconomic concepts
3. **Coherence:** Pairing and trading logic align across all exchange regimes
4. **Completeness:** No broken documentation links; all claims backed by code or marked [PLANNED]
5. **Reproducibility:** Determinism guarantees preserved through any recommended changes

---

**Next Steps:** Review this prompt, prioritize sections, and begin Phase 1 (Context Gathering). Update this document with findings as research progresses.
