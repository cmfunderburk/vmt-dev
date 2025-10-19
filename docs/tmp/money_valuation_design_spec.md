### Money Valuation Design Spec (with Decisions)

Author: VMT Assistant
Date: 2025-10-19

---

### 1) Decisions confirmed

- M type and units: `M` is an integer tracked in minor units with `money_scale ≥ 1`.
- KKT price aggregation: use deterministic median-lower of neighbor asks in money per good; include self-ask to avoid empty sets; sort by `(price, seller_id)`.
- Tie-breaking order across pairs: requires further discussion (see §6).
- Surplus threshold: require strictly positive ΔU for both parties to execute.
- Money sources: forbid foraging of money. Money enters via initial endowments; future production/labor markets may add sources.
- KKT smoothing defaults: `alpha=0.2`, `λ ∈ [1e-6, 1e6]`.

---

### 2) Modes and utility contracts

- Quasi-linear mode: `U_total(A,B,M) = U_goods(A,B) + λ·M`, with constant λ provided by scenario.
- KKT mode: Money does not enter `U_goods` directly; instead, λ is estimated from local perceived money prices via KKT identities and smoothed in Housekeeping. Quotes in money use the current λ.

Goods utility engines (UCES, ULinear) expose `u_goods`, `mu_A`, `mu_B`. Prices remain floats. Inventories `A,B,M` remain integers; ΔY from prices uses round-half-up mapping.

---

### 3) Quotes, reservation prices, and spreads

For a good `G ∈ {A,B}`:

- Reservation price in money: `p*_{G in M} = MU_G / λ` (λ constant in quasi-linear; λ dynamic in KKT).
- Ask/bid construction with deterministic spreads and clamps:
  - `ask_G_in_M = max(p*_{G in M}, p_min) · (1 + s_ask)`
  - `bid_G_in_M = min(p*_{G in M}, p_max) · (1 − s_bid)`
- Good-good reservation prices unchanged: `p*_{A in B} = MU_A/MU_B`, `p*_{B in A} = MU_B/MU_A` with existing guards.

Quotes are stored generically by ordered pair `(sell, buy)` for `(A,B)`, `(B,A)`, `(A,M)`, `(B,M)`; reverse money directions optional for later.

---

### 4) KKT λ estimation protocol (deterministic)

Per agent, during Housekeeping:

1) Perceive neighbor asks in money: `ask_A_in_M`, `ask_B_in_M` within radius; include self-ask; sort `(price, neighbor_id)`.
2) Aggregate price by median-lower per good to get `p̂_A`, `p̂_B`. Fallback: infer via cross quotes if empty.
3) Compute MU at current `(A,B)`, then `λ̂_A = MU_A/max(p̂_A,ε)`, `λ̂_B = MU_B/max(p̂_B,ε)`; choose `λ̂ = min(λ̂_A, λ̂_B)`.
4) Smooth: `λ_{t+1} = (1−α)·λ_t + α·λ̂`; clamp to `[λ_min, λ_max]`.
5) If `|λ_{t+1} − λ_t| > tol`, mark quotes dirty for recomputation next tick; quotes remain stable within the current tick.

---

### 5) Matching and surplus across heterogeneous media

Generic `find_compensating_block(X,Y)` supports `Y ∈ {A,B,M}` with price `p_Y_per_X`. For each `ΔX ∈ [1..dX_max]`:

- Compute `ΔY = round_half_up(p_Y_per_X · ΔX)`.
- Buyer and seller utility changes:
  - If `Y=M`: use `ΔU_buyer = ΔU_goods − λ·ΔM`, `ΔU_seller = −ΔU_goods_partner + λ·ΔM` (λ = constant or KKT-smoothed).
  - If `Y ∈ {A,B}`: compute `ΔU` purely via `u_goods` changes.
- Execute only if `ΔU_buyer > 0` and `ΔU_seller > 0` and budgets/constraints hold; else set cooldown as per existing rules.

Candidate trades across pairs are ranked by total surplus with deterministic tie-breaking (see §6 pending decision).

---

### 6) Open design: barter vs money-only when money exists

We must decide whether to allow good-for-good (barter) alongside money trades when money is present. This is not merely cosmetic; it affects pedagogy (theory illustration) and dynamics (search frictions, price discovery).

Deterministic options:

- Mode A: Money-only exchanges
  - Enforce `Y = M` in matching. Barter quotes computed but ignored.
  - Pros: Cleanly illustrates budget-constraint KKT theory; prices in money are focal; avoids barter cycles.
  - Cons: Loses illustration of double-coincidence-of-wants and relative price trade when money markets are thin.

- Mode B: Coexistence with priority to money
  - Consider both `(A,M)`, `(B,M)` and `(A,B)` trades; choose the candidate with highest strictly positive surplus, using deterministic tiebreakers.
  - Pros: Shows emergence of money usage under frictions; if money markets are illiquid, barter can still occur.
  - Cons: May blur didactic focus; can generate barter even when money exists unless preferences or liquidity make money strictly better.

- Mode C: Coexistence gated by liquidity signal
  - Enable barter only if perceived money market depth (e.g., number of neighbor money quotes above a threshold) is below a deterministic cutoff.
  - Pros: Captures theoretical transition from barter to monetary exchange as markets deepen.
  - Cons: Adds another parameter and requires careful deterministic aggregation of “depth.”

Pending decision points in this area:

1) Should scenarios declare `exchange_regime ∈ {money_only, mixed, mixed_liquidity_gated}`?
2) In `mixed`, what is the default tie-break when total surplus is equal: prioritize money trades for pedagogy, or favor barter to illustrate relative prices? A suggested deterministic order is `A↔M ≺ B↔M ≺ A↔B` if we want to favor money, or the reverse if we want to favor barter.
3) If `mixed_liquidity_gated`, define a deterministic depth metric (median-lower spread-normalized count of money quotes) and a threshold.

---

### 7) Scenario/schema implications (no code changes yet)

Add (names indicative):

- `money_mode: {quasilinear, kkt_lambda}`
- `money_scale: int ≥ 1`
- `lambda_money: float` (quasi-linear only)
- `lambda_update_rate: float`, `lambda_bounds: {lambda_min, lambda_max}` (KKT only)
- `exchange_regime: {money_only, mixed, mixed_liquidity_gated}`
- `initial_inventories: allow M minor units`
- `forage_money: false` by default; renderer and telemetry updated to log M flows only from trades.

---

### 8) Discussion: Theory vs reality in presence of money (for item 3)

From a Walrasian lens, money is a numeraire and does not change real allocations; with quasilinear utility, λ fixes the value of income and simplifies welfare comparisons. In real decentralized exchange, money lowers search and bargaining costs and serves as a store of value and unit of account; liquidity and acceptance are endogenous.

In the ABM, allowing barter alongside money can highlight how liquidity and acceptance conditions determine the medium of exchange. However, this can obscure the budget-constraint/KKT story unless the exchange protocol deterministically favors money when the expected utility gains are comparable. Conversely, forbidding barter makes the KKT narrative crisp but removes the mechanism by which money becomes focal in the first place.

Three guiding principles to balance pedagogy and realism:

- Deterministic liquidity criterion: permit barter only when the perceived money market is too thin (Mode C). This ties the availability of money exchange to observable market depth while preserving a clear rule students can inspect.
- Surplus dominance with strict positivity: even in mixed regimes, require strictly positive surplus and rank candidates by surplus. Money tends to dominate when λ-based pricing is coherent; barter appears when relative price misalignments make it temporarily better.
- Transparent tie-breaking: publish the deterministic order used when surpluses tie (e.g., favor money to align with theory modules, or flip to favor barter in comparative runs). This preserves reproducibility and makes the didactic choice explicit.

Next discussion items:

1) Choose `exchange_regime` default per course/demo: likely `money_only` for KKT teaching scenarios; `mixed` or `mixed_liquidity_gated` for market microstructure demos.
2) Confirm tie-break order for equal surplus in mixed regimes (favor money or barter).
3) Specify the liquidity depth metric for gating (count threshold, radius, and deterministic aggregation).

---

If approved, we will proceed to incorporate these decisions into the implementation plan and tests without changing any code until you green-light edits.


