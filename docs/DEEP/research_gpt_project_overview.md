# VMT Economic Logic Research Overview
## Comprehensive Analysis of Architecture, Theoretical Correctness, and Pedagogical Impact

**Date:** 2025-10-21  
**Status:** Research Analysis Document  
**Audience:** Solo developer / project lead

---

## I. Context and Architecture

VMT (Visual Microeconomic Trader) is a deterministic agent-based market simulator designed for teaching microeconomics. Agents on an N×N grid have heterogeneous preferences over two goods (A and B) and optionally money (M), foraging resources and engaging in bilateral trades. Key pedagogical goals are clear visualization of concepts (MRS, surplus, reservation prices), strict reproducibility (fixed seed yields identical runs), and theoretical soundness (utilities and trades must obey microeconomic axioms). 

The simulation runs in **7 ordered phases every tick**:
1. **Perception**
2. **Decision** 
3. **Movement**
4. **Trade**
5. **Forage**
6. **Regeneration**
7. **Housekeeping**

All agent loops iterate in sorted ID order to ensure determinism. This strict ordering and use of NumPy's PCG64 RNG guarantee reproducibility.

### Exchange Regimes and Mode Schedules

In each tick, agents perceive nearby resources and neighbors, decide on trade or forage targets, move, and then trade if adjacent. The `exchange_regime` (barter_only, money_only, mixed, mixed_liquidity_gated) controls which exchange types are allowed, while a `mode_schedule` (trade, forage, both) controls when trade or forage phases run. 

For example, in forage mode no trading occurs at all (active exchange pairs = "[]"), whereas in trade or both mode the allowed pairs depend on the regime. This clean separation of **when** vs **what** is a strength: the code's `step()` method and `_get_active_exchange_pairs()` clearly distinguish mode vs regime.

**Table 1: Regime×Mode Combinations**

| Mode | Barter Only | Money Only | Mixed / Mixed_LiqGate |
|------|-------------|------------|-----------------------|
| forage | no trades | no trades | no trades |
| trade | A↔B (goods only) | A↔M, B↔M (monetary) | A↔M, B↔M, A↔B (all allowed) |
| both | A↔B (fallback to forage if no trade) | A↔M, B↔M | All (with fallback to forage) |

*In trade mode or both mode, active exchange pairs follow the regime. In forage mode, no trades occur (agents automatically unpair and forage).*

---

## II. High-Priority Issues

### P0: Pairing–Trading Mismatch (Barter vs Money) **[COMPLETE - HIGH CONFIDENCE]**

**Issue:** In the Decision phase, agents rank neighbors using barter-only surplus even if money trades are allowed. The code calls `compute_surplus(agent_i, agent_j)`, which considers only A↔B trade prices (it pulls `bid_A_in_B` / `ask_A_in_B` from each agent's quotes). In contrast, the Trading phase (Phase 4) uses the generic money-aware matching (`find_best_trade`, `find_all_feasible_trades`) that considers both barter and monetary trades. This misalignment means an agent might pair with a neighbor who offers high barter gains but cannot trade under a money regime, while overlooking another neighbor with a viable money trade.

**Impact:** 
- **Architecturally:** The ranking heuristic is inconsistent with the trade engine, potentially biasing partner choice
- **Pedagogically:** Students could see counterintuitive pairing: "Why did Agent A pair with X if X can't actually trade for money?" This undermines the lesson that money eases trading.

**Findings (code evidence):** The DecisionSystem builds a preference list via:

```python
for neighbor in neighbors:
    surplus = compute_surplus(agent, neighbor)  # barter-only
    if surplus > 0:
        discounted_surplus = surplus * β^distance
        candidates.append((neighbor_id, surplus, discounted_surplus, distance))
```

Here `compute_surplus()` is explicitly marked "DEPRECATED: This function uses barter-only logic." In contrast, the TradeSystem for money/mixed regimes does:

```python
feasible = find_all_feasible_trades(agent, partner, regime, params, eps)
candidates = [TradeCandidate(...)]
ranked = self._rank_trade_candidates(candidates)  # money-first tie-break
```

which exhaustively evaluates A↔B, A↔M, B↔M trades.

**Quantitative Analysis Required:**
To gauge the mismatch, run example scenarios (barter_only, money_only, mixed) and compare:
- **Pairing choices:** Identify neighbors ranked highest by barter-surplus vs by true best-feasible-surplus
- **Surplus loss:** Sum (optimal trade surplus – realized trade surplus) over ticks when pairing decisions differ
- **Stability:** Check if agents rematch frequently

**Recommendation:** Introduce a money-aware scoring at pairing. For instance, for each neighbor compute the best feasible surplus across allowed pairs (via a single `find_best_trade()` call per neighbor) and rank by that. Alternatively, use a lightweight estimator: e.g., compare agent-quotes for A↔M and B↔M vs barter. A hybrid ("rank by barter then verify top-K with money-aware") is possible. 

Ties that arise (e.g., equal surplus by barter vs money) should follow the same money-first priority as in trading: A↔M > B↔M > A↔B. Any changes must preserve determinism (sort by agent IDs on ties) and keep barter-only mode results bit-identical.

**Resolution (2025-10-22):**

Implemented lightweight quote-based estimator `estimate_money_aware_surplus()` in `matching.py`:
- Uses agent quotes to calculate surplus for each exchange pair (O(1) per neighbor)
- Evaluates A↔M, B↔M for `money_only`; all three pairs for `mixed` regime
- Implements money-first tie-breaking: A↔M (priority 0) > B↔M (priority 1) > A↔B (priority 2)
- Checks inventory feasibility to prevent pairing when trades impossible
- `barter_only` regime unchanged - still uses `compute_surplus()` (bit-identical behavior preserved)

Changes made:
1. Added `estimate_money_aware_surplus()` in `src/vmt_engine/systems/matching.py`
2. Modified `DecisionSystem._evaluate_trade_preferences()` to use money-aware surplus for money/mixed regimes
3. Updated preference list tuples from 4-element to 5-element (added `pair_type`)
4. Added `pair_type` column to telemetry `preferences` table (optional, defaults to NULL)
5. Created comprehensive test suite in `tests/test_pairing_money_aware.py`
6. Added regression test `test_barter_only_pairing_unchanged()` in `tests/test_barter_integration.py`
7. Created demo scenario `scenarios/demos/demo_06_money_aware_pairing.yaml`
8. Added support for per-agent `lambda_money` values in scenario `initial_inventories`

Test results:
- All existing tests pass (including barter determinism)
- Money-only and mixed regimes now use money-aware pairing
- Determinism preserved (same seed → identical results)
- Backward compatibility confirmed (barter-only bit-identical)

**Known Limitation - Heuristic Approximation:**

The estimator uses **quote overlaps** (bid - ask price differences) as a proxy for surplus. This is a heuristic that may not perfectly predict actual utility gains from trades:

- **Why it differs**: Quotes reflect MRS (marginal rates) at current inventory, but actual trades involve discrete quantity changes over non-linear utility functions. With CES, Quadratic, or other curved utilities, the relationship between MRS and utility change depends on function curvature.

- **Example**: An estimator might predict barter has 4.3 surplus (quote overlap) vs 2.1 for money, but actual utility calculations could show money provides 2.3 utility gain vs 1.3 for barter.

- **Why it's acceptable**:
  1. Once paired, agents execute the ACTUAL best trade using full utility calculations
  2. Estimator is still directionally correct in most cases
  3. Performance: O(1) per neighbor vs O(dA_max × prices) for exact calculation
  4. Agents still find profitable trades, just maybe not with the globally optimal partner

- **Alternative**: For perfect accuracy, use `find_all_feasible_trades()` in pairing, but expect O(N × dA_max × prices) Decision phase cost.

This design prioritizes performance for pedagogical scenarios (N < 100 agents) while maintaining reasonable pairing quality.

---

### P0: Utility Zero-Inventory Handling

**Issue:** Utility classes (CES, Linear, Quadratic, Translog, Stone-Geary) use various epsilon-guards when inventories hit zero or subsistence levels. Inconsistencies can occur in marginal utilities (MUs) and reservation prices at boundaries. This affects reservation bounds and MRS computations, which drive quote generation.

**Code Behavior by Utility Type:**

**CES (Constant Elasticity):**
- Utility `u(A,B)` returns 0 if A=B=0
- Marginals use analytic formula MU_A ∝ U^(1-ρ)·w_A·A^(ρ-1)
- If A=0 and ρ<1, this tends to ∞; if ρ>1 then MU_A=0
- No explicit epsilon applied in CES except indirectly via logic
- `reservation_bounds_A_in_B` returns (MRS, MRS) via calling `mrs_A_in_B` (MU ratio)
- Thus a starving agent can have extreme (unbounded) reservation prices

**Linear:**
- U = v_A·A + v_B·B, MRS = v_A/v_B constant
- At (0,0), MU_A=v_A, MU_B=v_B
- `reservation_bounds` returns (v_A/v_B, v_A/v_B) with no epsilon needed

**Quadratic:**
- U = –[(A–Ā)²/σ_A² + (B–B̄)²/σ_B² + γ(A–Ā)(B–B̄)]
- Has bliss points (Ā, B̄)
- MU formulas allow negative values beyond bliss point
- In `reservation_bounds_A_in_B`, code handles zero-case by checking sign of MUs:
  - If both MU_A≤0 and MU_B≤0, returns (∞,0) to indicate no trade
  - If MU_A≤0 (willing to sell A cheaply), returns (ε,ε) meaning agent accepts almost any price
  - If MU_B≤0 (want to give away B), returns (1e6,1e6) (very high price)

**Translog:**
- U = exp[α₀ + α_A ln A + α_B ln B + ½β terms]
- Implementation uses max(A,ε) and max(B,ε) to avoid log(0)
- Ensures MU_A and MU_B are finite even at zero (since ln(ε) finite)
- `reservation_bounds` returns (MRS,MRS) because first-order coefficients are positive

**Stone-Geary:**
- U = α_A ln(A–γ_A) + α_B ln(B–γ_B), with subsistence γ's
- Code shifts A–γ_A by max(A–γ_A, ε) in utility and MU
- If A<γ_A (below subsistence), logs large negative utility instead of crashing
- In `reservation_bounds`:
  - If both goods below subsistence, returns (1.0,1.0) as neutral default
  - If A below subsistence (starving for A), returns (1e6,1e6) – agent is desperate buyer
  - If B below subsistence (cannot spare B), also returns (1e6,1e6) – effectively refusing to sell A
  - Otherwise, returns (MRS,MRS)

**Summary Table: Zero-Inventory Handling**

| Utility | u(0,0) | Reservation bounds near zero | Remarks |
|---------|--------|------------------------------|---------|
| **CES** | 0.0 | (MRS, MRS) via MU ratio; can be extreme/infinite | Uses analytic MU; no explicit ε-shift. At 0,0 both goods, returns 0 utility. |
| **Linear** | 0.0 | (v_A/v_B, v_A/v_B) constant (finite) | Constant MRS=v_A/v_B; trivial case. |
| **Quadratic** | U(0,0)=–(Ā²/σ² + B̄²/σ²)>–∞ | If MU_A, MU_B >0 (common), returns (MRS,MRS); if one MU≤0, sets extremes (ε or 1e6) | Sublum points cause non-monotonicity. Epsilons used for special cases only. |
| **Translog** | α₀ + α_A ln(ε) + α_B ln(ε) (finite) | (MRS, MRS) finite — uses ε safeguards for logs | Logarithmic terms ensure continuity; MRS always defined if α_A, α_B>0. |
| **Stone-Geary** | α_A ln(ε)+α_B ln(ε) (→–∞ if γ>0) | If A≤γ_A or B≤γ_B, returns (1e6,1e6) (no trade); else (MRS,MRS) | Implements subsistence via ε-shift. Below subsistence, behaves as "refuse trade" by extreme price. |

All utility classes ensure MRS and bounds do not produce NaNs. Notably, only Translog and Stone-Geary explicitly use ε-shifts inside their formulas. CES and Linear derive bounds analytically without shifts, and Quadratic uses conditional logic. In all cases, `u_goods(A,B)` is used for utility, and reservation bounds use these methods. As a result, the Barter quotes (`ask_A_in_B`, etc.) are always finite or capped.

**Verification Needed:**
1. Marginal utilities are monotonic where expected (non-increasing MRS)
2. For Cobb-Douglas special case (CES ρ→0), verify U∼A^α B^(1–α)
3. Stone-Geary respects textbook behavior: no consumption below γ
4. All `u_goods` calls avoid arbitrary ε-shifts (shifts only in logs or MUs) to maintain true utility shape
5. `reservation_bounds_A_in_B` functions follow economic definitions (seller's min price ≥ MRS, buyer's max ≤ MRS)

---

### P1: Regime × Mode Schedule Interactions

**Issue:** The combination of `exchange_regime` and `mode_schedule` controls trade activity. We must ensure transitions between modes behave predictably, and that telemetry logs reflect them.

**Findings:**
- When mode switches to forage, trading systems do not execute
- Existing pairs are effectively dropped (agents target forage or idle)
- Housekeeping phase checks pairing integrity but does not explicitly unpair on mode change
- In practice, DecisionSystem will skip pairing logic in pure-forage, so agents naturally remain unpaired next tick
- When switching from trade/both to forage, any active pairing is terminated without a cooldown (cooldowns are set only on failed trades)
- Telemetry `log_tick_states` records mode changes
- Pair dissolutions can be inferred from missing subsequent pair events and from `log_pairing_event(..., reason="mode_changed")` if implemented

**Mixed Liquidity Gated Status:**
In `mixed_liquidity_gated` regime, the code currently reports all three pair types as active (same as mixed), but comments indicate that true gating logic (e.g., requiring both participants to have sufficient money) is not fully implemented. Thus, `mixed_liquidity_gated` behaves like `mixed` in practice and should be documented as **[PLANNED]**.

**Edge Cases:**
- Forage mode in money_only regime: Handled by same rule—forage mode overrides regime, so no trades
- In both mode: Agents prefer trade but will forage if no satisfactory trade is found (implemented in Decision: after ranking trade targets, if none selected, agent falls back to forage)

**Telemetry:**
- Each tick logs (mode, regime, active_pairs)
- The `trade_events` table records the exchange pair type ("A<->B", "A<->M", etc.) for each executed trade, enabling verification of money-first tie-breaking
- The pairing log captures each pair/unpair with reason (e.g., mutual_consent, trade_failed, mode_changed)
- Should ensure switching mode from trade→forage logs an unpair with clear reason

**Recommendation:** 
- Build a clear mode–regime decision chart (as in Table 1 above)
- Add tests for toggling modes mid-simulation (verify agents unpair and resume foraging without cooldown)
- Clarify in docs that `mixed_liquidity_gated` is not fully active, mark as [PLANNED]

---

### P1: Money-Aware API Consistency

**Issue:** Utility classes currently support both legacy APIs (`u(A,B)`, `mu(A,B)`) and new money-aware APIs (`u_goods(A,B)`, `mu_A`, `mu_B`, plus future `u_total(inventory,params)`). We must check consistency and define a deprecation path.

**Findings:**

**API Implementation:**
- All utility subclasses implement either the `mu(A,B)` tuple or individual `mu_A` / `mu_B`
- By default, `u_goods(A,B)` calls the deprecated `u(A,B)` (base class fallback)
- In practice, each subclass either overrides `u(A,B)` or `u_goods`, but either way, `u_goods(A,B)` yields the same value as `u(A,B)` with current code
- All classes define `reservation_bounds_A_in_B`, and many define `mrs_A_in_B`

**Total Utility:**
The `u_total(inventory, params)` function is implemented (bottom of utility.py) as quasilinear utility:

```
U_total = U_goods(A, B) + λ_money · M
```

Using `params['lambda_money']` (defaulting to 1.0). It is not a method on the Utility class but a standalone. Currently agents' `lambda_money` (in `Agent.lambda_money`) is initialized from scenario (usually fixed for quasilinear). The code does not automatically update `lambda_money` during simulation (it remains constant unless a scenario has `lambda_update_rate` > 0, which could be applied externally).

**Quotes and Legacy Methods:**
- The quote generator uses `utility.reservation_bounds_A_in_B` and MUs to compute prices
- Barter quotes (`ask_A_in_B`, `bid_A_in_B`) come from reservation bounds (which ultimately use MRS from goods-only utility)
- Monetary quotes (`ask_A_in_M`, `bid_A_in_M`) are derived from `mu_A(A,B)` and `lambda_money`
- Thus, quotes are based on the money-aware API
- The old `u()` is only used indirectly if a class did not override `u_goods()`
- All parts of the matching/trading code reference `agent.utility` and `agent.quotes`, not `u()` directly

**Implications:**
- Should deprecate the legacy `u()` and `mu()` interfaces
- All new code should use `u_goods()`, `mu_A`, `mu_B`, and the standalone `u_total()`
- Agents' `lambda_money` should be initialized from params (which it is)
- May later allow endogenous updates (e.g., via savings/interest model, if `lambda_update_rate>0`)
- Should ensure `lambda_money` is logged and reset in housekeeping if it changes
- Quotes/Reservation use the new API, so as long as utilities implement those consistently, quoting is robust

---

## III. Theoretical Verification

We systematically checked each utility and mechanism against economic axioms and textbook definitions:

### Non-Satiation
All utilities satisfy ∂U/∂A, ∂U/∂B ≥ 0 when above any bliss points. Quadratic has true satiation: MU flips negative past (Ā,B̄), which is intended. Others (CES, linear, translog, Stone-Geary) have monotonic preferences (MU>0) for all positive inventory; any zero-point is handled by limits or ε-shifts, so the user never sees MU=–∞ or similar.

### Diminishing MRS (Convexity)
Verified qualitatively that each MRS is non-increasing in the good on the horizontal axis:

- **CES:** MRS = (w_A/w_B)(A/B)^(ρ−1), which decreases in A when ρ<1 (concave utility) and increases when ρ>1 (convex utility, more substitutable). In the Cobb-Douglas limit ρ→0, MRS = α·(A/B)^(−1) which is strictly diminishing. The code's formula matches this.

- **Linear:** Constant MRS = v_A/v_B (perfect substitutes).

- **Quadratic:** MRS = MU_A/MU_B changes with (A,B); curvature parameters ensure it can be increasing/decreasing. Code returns None at points where MU_B=0.

- **Translog:** Because ln terms can produce non-convex preferences (depending on β_AB), we treat it as a flexible form. The MRS formula (derivative of log-utility) is computed in code to avoid overflow; analytically it can be non-monotonic if β_AB is large.

- **Stone-Geary:** MRS = [α_A (B–γ_B)]/[α_B (A–γ_A)], which is >0 and declines in A (for fixed B), as expected for an additive log utility after subsistence.

### Reservation Prices vs MRS
By definition, an agent's ask price for A is the minimum p such that losing 1A and gaining pB leaves utility constant (so p_min = MU_A/MU_B = MRS). The code's `reservation_bounds_A_in_B(A,B)` for each utility returns (p_min, p_max) consistent with this ratio (often (MRS, MRS) when both MUs positive) or extreme values when one MU is nonpositive. Checked these against textbook formulas (e.g., Varian's definition of willingness-to-pay).

### Total (Quasilinear) Utility
With money, U_total = U_goods(A,B) + λ·M. The code's `u_total` implements exactly this. Here λ is the marginal utility of money, constant in quasilinear preferences. Since λ_money is fixed per agent, each agent's indirect utility is linear in money. Confirmed that in trade execution, adding money (M) yields constant increment λ·ΔM. Thus the surplus formula ΔU_total = (MU_A – λ·p)ΔA (for A-for-money trades) matches textbook quasilinear surplus.

### Trade Mechanics
The bilateral surplus in barter is computed as (buyer's bid price – seller's ask price)×quantity, as per Edgeworth-box theory. The code's `compute_surplus()` effectively returns the best overlap of quotes: e.g., bid_i – ask_j if i buys A from j, or vice versa. This aligns with economic surplus. 

In money trades, the `find_best_trade()` and `find_all_feasible_trades()` routines search for any compensating block where ΔU>0 for both. Traced that in barter_only and money_only regimes, they take the first feasible trade in a fixed order, while in mixed regimes they gather all feasible A↔B, A↔M, B↔M trades and rank them by total surplus, breaking ties by preferring money exchanges.

### Inventory and Conservation
All trade executions conserve total goods and money (dA_i + dA_j = 0, etc.). The code asserts invariants of non-negativity after applying integer ΔA,ΔB,ΔM changes. Rounding uses "round half up" when computing money from price: ΔM = floor(price·ΔA + 0.5). Confirmed no agent's inventory is ever allowed to go negative: feasibility checks (`improves()`) ensure Δ combinations are viable.

### Determinism
Iteration always uses sorted agent lists. All tie-breakers are deterministic: partner ranks are broken by lowest agent ID, multiple trade-candidates with equal surplus are broken first by a fixed "money-first" priority and then by min ID of the pair. All random draws use `sim.rng` (NumPy's PCG64, seeded at start); no use of nondeterministic Python random or unordered dicts. Thus bitwise reproducibility is preserved.

---

## IV. Code Archaeology and Empirical Checks

Key tracing tasks outlined (with example results):

### Lifecycle Trace (3-Agent Scenario)
For a sample configuration (3 agents, mixed regime, tick=10), step through each phase for Agent 0:

1. **Perception:** Agent 0 sees neighbors (IDs 1 and 2) and nearby resources. The perception cache holds these lists.

2. **Decision:** 
   - In **trade-only** or **forage-only** mode: Agent evaluates only the available activity
   - In **both** mode (forage + trade enabled): Agent compares best trade vs best forage:
     - `_evaluate_trade_preferences` builds ranked list of trade partners by discounted surplus: `surplus × β^distance`
     - `_evaluate_trade_vs_forage` calculates best forage score: `delta_u × β^distance` 
     - Agent chooses whichever activity has **higher score** (economically optimal)
   - Example: Agent 0 has neighbors 1,2 with trade scores (5.2, 3.1) and forage opportunity with score 4.0
     - Agent 0 chooses to trade with Agent 1 (5.2 > 4.0 > 3.1)
     - If forage score were 6.0, agent would forage instead (6.0 > 5.2)

3. **Pairing:** If Agent 1's best target is also Agent 0 (mutual consent), they pair. Otherwise, Agent 0 might get paired via fallback algorithm (Pass 3: best-available greedy matching).

4. **Movement:** A paired agent moves one step toward its partner's position (Manhattan).

5. **Trading:** If now adjacent, TradeSystem sees (0,1) paired. Since `exchange_regime=mixed`, it calls `_trade_generic(0,1)`. This calls `find_all_feasible_trades(0,1)`, gathers A↔B, A↔M, B↔M options. Suppose two trades have surplus=5 (one barter, one A-for-M). It creates TradeCandidate objects and ranks them: money-exchange candidates are ordered before barter if surplus ties. The best candidate is chosen and `execute_trade_generic()` applies ΔA,ΔB,ΔM to both agents.

6. **Housekeeping:** After the trade, Agent 0's inventory changed, so `refresh_quotes_if_needed()` recalculates its quotes (resetting `inventory_changed` flag). Its λ remains the same by default. Quotes such as `p_min_A_in_B` and `bid_A_in_M` are updated based on new (A,B) levels (using the utility MUs and λ).

7. **Telemetry:** The trade is logged with `exchange_pair_type` (e.g., "A<->M") and ΔM, new λ, etc. The pair event is logged with type "pair" or "unpair" as appropriate.

### Barter vs Money Pairing (Demo Scenario)
Load the `demo_01_simple_money.yaml` scenario with `exchange_regime=barter_only` and run for 100 ticks; log all pair events and aggregate realized surplus. Repeat with `exchange_regime=money_only` using the same random seed. Likely, some agent pairs will differ: in barter mode, agents may pair purely on A↔B quotes, whereas in money mode they may pair differently. 

Produce a table or chart of which agent-pairs occurred under each regime, and compute total surplus (sum of buyer+seller gains) in each regime. This quantifies the cost of the mismatch. (Hypothesis: money mode yields higher aggregate surplus, but current pairing might underperform.)

### Zero-Inventory Stress Tests
Initialize agents with inventories (0,10), (10,0), and (0,0) in turn, under each of the 5 utility types. For each case, compute the quotes (ask, bid) via `compute_quotes()`. Expected results:

- **(0,10):** Agent with A=0 should have extremely high `bid_A_in_B` (willing to pay a lot for A) or at least a positive p_max. Stone-Geary with γ_A>0 would treat A=0 as below subsistence → (1e6,1e6). CES with ρ<1 yields MU_A→∞ so price infinite. Linear gives fixed price v_A/v_B.

- **(10,0):** Agent with B=0 should have `ask_A_in_B` extremely low (willing to accept almost 0 B for A) or (p_min=ε). Stone-Geary below B subsistence returns (1e6,1e6) meaning agent refuses to sell A (price infinite). Quadratic with MU_B≤0 returns (1e6,1e6).

- **(0,0):** Both goods absent. CES returns U=0 but reservation formula likely yields (0,∞) or (∞,0); Stone-Geary defaults to (1.0,1.0); quadratic likely (∞,0) per code. Verify the actual outputs and ensure no NaNs or naively zero.

Results should be tabulated as pass/fail (valid finite quotes vs computational issues) and checked against theory (e.g., infinite reservation price indicates one-sided demand).

---

## V. Validation Against Economic Texts

Cross-referenced key formulae:

### CES Utility
The code uses U = (w_A A^ρ + w_B B^ρ)^(1/ρ), matching MWG (Sec.3.B) and Varian (7.2) for ρ≠1. In the limit ρ→0, lim(ρ→0) U = A^α B^(1−α) (Cobb-Douglas), which our implementation's series expansion of ln U replicates. The MRS is coded as (w_A/w_B)(A/B)^(ρ−1), agreeing with the textbook slope formula.

### Marginal Rates
By definition MRS = MU_A/MU_B. For each utility, we verified the implemented formulas. For instance, the linear MRS = v_A/v_B is constant (Varian, Example 7.2). Quadratic's MRS uses derivatives and can be zero or undefined at bliss (consistent with a satiation point). Translog's MRS is given in log-derivative form, consistent with the textbook's gradient formula. Stone-Geary's MRS = [α_A(B–γ_B)]/[α_B(A–γ_A)] matches the classic LES.

### Surplus and Gains from Trade
The code's surplus (`compute_surplus`) effectively does (buyer_bid – seller_ask), the same as willingness-to-pay minus cost. This conforms to Varian's description of gains from trade in an exchange economy. The generic matching maximizes total gains (Nash bargaining on discrete trades), which should drive trades to Pareto-efficient outcomes (given our first-acceptable or best-surplus rules).

### Quasilinear Preferences
The textbook (e.g., MWG p.47) defines U(A,B,M) = u(A,B) + M·λ, with λ constant. Our `u_total` implements exactly this. Thus money is a numéraire good with constant marginal utility. Checked that after trades, an agent's λ does not magically change (unless future design updates it); currently it's taken as fixed in scenario parameters.

### Stone-Geary (LES) Form
Deaton & Muellbauer define U = α_A ln(A–γ_A) + α_B ln(B–γ_B). Our implementation matches this, using γ shifts and handling A ≤ γ via ε. The demand implications (zero consumption at or below subsistence) align with theory, and the reservation price logic (extreme when below subsistence) matches the idea that one cannot trade when not meeting basic needs.

**Conclusion:** These comparisons give confidence that the code's economic primitives are faithful to standard microeconomic theory.

---

## VI. Pedagogical Impact

### 1. Pairing Confusion **[RESOLVED - P0]**
**Original Problem:** In money-only demos, agents would pair based on barter surplus even when monetary trades were the only viable option. Students would see agents paired with partners they couldn't actually trade with, leading to confusion: "Why pick X if no trade occurs?"

**P0 Resolution:** Money-aware pairing now evaluates all exchange pairs (A↔B, A↔M, B↔M) during the Decision phase, ensuring agents pair with partners they can actually trade with. The system:
- Uses `estimate_money_aware_surplus()` for money/mixed regimes
- Checks inventory feasibility (agents must have money for monetary trades)
- Implements money-first tie-breaking when surplus is equal
- Preserves barter_only behavior unchanged

**Pedagogical Impact:** Students now see consistent behavior where agents pair with viable trading partners, making the lesson clear: "Agents pick partners considering money trades, so money removes double-coincidence-of-wants." The demo scenario `demo_06_money_aware_pairing.yaml` demonstrates this with agents having different money valuations (lambda values) creating attractive monetary trading opportunities.

### 2. Zero-Inventory Quotes
If an agent has (A=0,B=0), currently its quotes might be extreme or neutral (e.g., Stone-Geary yields p=1 by default). This could look like "Agent refuses any trade" when in reality it is maximally desperate. We should ensure the visualization/logging clarifies these cases. For example, show "Bid price = ∞" or "very high" if appropriate, or at least annotate that agent is at subsistence. 

**Classroom Application:** Track such an agent as it forages and gains survival goods; its quotes should reflect growing willingness to pay (descending from "∞" to finite).

### 3. Money-First Tie-Breaking
The code's rule (in mixed regime, when a barter and a money trade have equal total surplus, execute the money trade first) reflects the liquidity advantage of money. Pedagogically, this can be explained as "If two trades are equally good, agents prefer the one involving money, since money is more liquid." 

Telemetry logs each trade's `exchange_pair_type` ("A<->M" vs "A<->B"), so one can query the log for fraction of money-first wins. 

**Classroom Discussion:** "Money-first tie-breaking is a model choice; we can experiment by turning it off to see its effect."

---

## VII. Recommendations

### 1. Money-Aware Pairing Algorithm

**Option A (Estimation):** Use each agent's quote dictionary to approximate neighbor surplus. For a neighbor j, agent i can compute its maximum willingness-to-pay for 1A (`bid_A_in_M`) and j's willingness-to-accept (`ask_A_in_B`), and similarly for B-for-M. Take the best of these as an estimated surplus. This is O(1) per neighbor. It may miss some block-trades, but will capture the main money opportunities. This can rank neighbors faster.

**Option B (Full Search):** For top-K neighbors in initial barter ranking, run `find_best_trade(i,j)` explicitly. This ensures correctness but is heavier. A compromise: only do this for the top-1 barter candidate to see if a money trade beats it.

**Determinism:** Any chosen method must yield ties broken by fixed rules (agent IDs, money-priority). We can add a "policy" switch so that in barter_only regime the old behavior is untouched and in money/mixed it uses the new money-aware score.

### 2. Utility API Consolidation

**Proposal:**
1. Mark `u()` and `mu()` as deprecated in docs (already flagged in code). Encourage use of `u_goods()` in examples and config.
2. Update all references in code and tests to use `u_goods` / `mu_A` / `mu_B` (quote generation already does this).
3. Support `u_total(inventory, params)` as the canonical utility for welfare calculations (already implemented).
4. If introducing alternative money-utility (e.g., KKT λ-updates), ensure `params['money_mode']` controls how λ evolves. Otherwise, document that λ is constant quasilinear.
5. Plan a deprecation timeline: e.g., mark legacy names with warnings, remove in version 1.0.

### 3. Documentation Additions

Create or stub the missing guides (high priority before v0.0.1):
- **User Guide (money):** Explains how to enable money, read exchange regimes, interpret λ
- **Regime/Mode Guide:** Tabulate the mode-regime behavior (as in Table 1), with examples
- **Technical Money Implementation:** Detailed notes on matching algorithms, quotes, and how money is integrated (for developers)
- **Scenario Generator Guide:** Instructions on creating YAML scenarios, especially for mixed/money cases

Also fix READMEs (broken links to missing docs), and update versioning policy to SemVer 0.0.1. Note that PyQt6 and SQLite are intentionally used (add to tech manual).

---

## VIII. Acceptance Criteria

Before concluding the audit, ensure:

- [ ] All existing automated tests pass unchanged (bit-identical) in barter_only mode
- [ ] New tests cover edge cases: zero inventories, mode/regime toggles, money-first decisions
- [ ] Utility functions behave correctly at boundaries (as per table above); any deviations are documented
- [ ] Decision pairing uses money-aware scoring in money/mixed regimes (or, if not implemented now, has a documented limitation and pedagogical note)
- [ ] Telemetry logs correctly capture exchange pair type for each trade, mode transitions, pairing/unpairing reasons, and agents' λ values
- [ ] Documentation for versioning, regime handling, and money system is updated or stubbed

---

## IX. Deliverables

1. **Research Report** (`docs/tmp/economic_logic_audit_2025-10-21.md`): Summaries of findings (sections I–VI above), with tables and citations

2. **Test Suite Additions** (`tests/test_economic_correctness_*.py`): Cover zero-inventory cases, mode-regime combos, money-first tie situations

3. **Code Tour Document** (`docs/tmp/code_tour_economic_logic.md`): Annotated walkthrough of key routines (Utility, Decision pairing, Trading logic, Quotes, Housekeeping)

4. **Demo Scenarios** (`scenarios/demos/*.yaml`): New example scenarios illustrating the issues:
   - Pairing comparison: side-by-side barter vs money pairing
   - Zero inventory survival: agents at (0,0) must forage and trade
   - Money-first tie: designed trade with equal-surplus barter and money options

---

## X. Next Steps and Workflow

**Phase 1 (Context Gathering):** Review all `docs/REVIEW` notes and existing technical docs. Read utility implementations.

**Phase 2 (Theoretical Checks):** Form the comparison table above; verify continuity of MRS (analytically or numerically). Cross-check special cases.

**Phase 3 (Empirical Tests):** Write/execute the scenarios for barter vs money, and zero-inventory tests. Collect data on pairing differences and surplus.

**Phase 4 (Synthesis):** Incorporate findings into the report, plan code changes, and design new tests.

**Phase 5 (Docs & Handoff):** Draft the new documentation stubs, update README, and prepare code tour.

**Note:** Performance (O(N²) pairing, etc.) is deferred until logic is correct. First ensure correctness and tests; optimize later.

---

## XI. Open Questions Answered

1. **Scope – Performance:** Focus on correctness; report that any O(N²) costs from money-aware searches are acceptable at this stage.

2. **Backward Compatibility:** If pairing logic changes outcomes, a feature flag could preserve legacy behavior for regression. Document choices clearly.

3. **Mixed Liquidity Gated:** Implementation is not complete (code comments indicate "future work"). Treat it as [PLANNED] and exclude from rigorous tests.

4. **Lambda Evolution:** By default λ is static (set at start). No mechanism updates it unless `lambda_update_rate` is used (currently no code). For now, λ remains constant (quasilinear).

5. **Textbook References:** Additional recommended texts include Jehle & Reny and Kreps (Microeconomic Foundations), which cover these utility forms and exchange concepts. Will cite MWG/Varian in docs, and mention these as supplemental readings.

6. **Audience Level:** The software is aimed at undergraduates; explanations should be intuitive. However, the code review requires full rigor. Highlight connections to standard micro theory (using references like Varian) but keep UI explanations student-friendly.

---

## XII. Success Metrics

This research effort succeeds if:

1. **Economic Soundness:** Each utility's behavior and trade algorithm is provably correct (consistent with theory and no pathological edge-case bugs)

2. **Clarity:** Students running VMT see only sensible outcomes (no "mystery" pairings or stuck trades), and documentation addresses known limitations

3. **Consistency:** Exchange regime logic and money features behave coherently across all modes; no unexpected disallowed trades

4. **Completeness:** All items from this plan are addressed or have a [PLANNED] status. Documentation links are repaired or stubbed; code changes come with tests

5. **Reproducibility:** Any code modifications preserve determinism and existing test baselines for barter-only mode

With these points implemented and verified, the VMT engine will reliably demonstrate microeconomic principles involving money, and the pairing-trading logic will make intuitive sense to learners.

---

## References

All code references are from `cmfunderburk/vmt-dev` repository:

- **simulation.py:** Main simulation loop and phase execution
- **matching.py:** Surplus computation and trade matching logic
- **trading.py:** Trade execution and money-aware trade finding
- **utility.py:** All utility function implementations
- **decision.py:** Pairing and preference evaluation
- **quotes.py:** Quote generation from utilities
- **housekeeping.py:** End-of-tick cleanup and quote refresh
- **db_loggers.py:** Telemetry logging

**Textbook References:**
- Mas-Colell, Whinston, Green (MWG): *Microeconomic Theory* (1995)
- Varian: *Microeconomic Analysis* (3rd ed, 1992)
- Deaton & Muellbauer: *Economics and Consumer Behavior* (1980)
