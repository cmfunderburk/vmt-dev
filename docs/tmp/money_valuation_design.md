### Money in VMT: Quasi-Linear vs Lagrange-Multiplier Valuation — Design and Integration

Author: VMT Assistant
Date: 2025-10-19

---

### 1) Motivation and scope

We want to introduce money (M) into the deterministic, discrete-time VMT ABM while preserving the engine’s invariants: integer inventories/resources, stable quotes per tick, and round-half-up quantity mapping. There are two theoretically grounded ways to value money:

- Quasi-linear utility: U_total = U_goods(A, B) + λ · M, where λ > 0 is a constant marginal utility of money (MU of money). This treats money as a perfect, linear utility addend.
- Lagrange-multiplier (KKT) interpretation: In the standard consumer problem with budget constraint p_A·A + p_B·B ≤ M, the Lagrange multiplier μ equals the marginal utility of income. Shadow prices satisfy ∂U/∂A = μ·p_A and ∂U/∂B = μ·p_B. Here, the value of money is endogenous via μ.

This document proposes concrete, compatible implementations for both modes, integrated with the existing 7-phase tick and determinism rules, and identifies decision points that require your approval.

---

### 2) Baseline assumptions (engine contracts)

- Inventories and resources are integers. Prices are floats. ΔA, ΔB are integers; ΔB is computed from prices using round-half-up.
- Quotes are computed only in Housekeeping when `agent.inventory_changed` or other marked flags change. Quotes are stable within a tick.
- Perception uses `SpatialIndex.query_radius` and collects neighbor quotes as inputs into decision/matching.
- Matching tries at most one trade per unordered pair per tick, with pair sorting by (min_id, max_id).

Implication for money: We strongly prefer `M` to be an integer inventory entry to retain the same arithmetic guarantees and determinism. If sub-unit precision is required, we introduce a `money_scale` (e.g., cents = 100) so M tracks integer minor units. See §10 for the int-vs-float decision.

---

### 3) Two valuation modes for money

#### 3.1 Quasi-linear mode

- Utility: U_total(A, B, M) = U_goods(A, B) + λ · M, with λ a scenario-level (or agent-level) constant.
- Interpretation: Constant marginal utility of income; money and utility are linearly convertible at rate λ.
- Reservation prices in money for a good G ∈ {A, B}:
  - MU_G = ∂U_goods/∂G at current inventory (A, B)
  - Sell reservation price p_res_sell(G→M) = MU_G / λ
  - Buy reservation price p_res_buy(G←M) = MU_G / λ
  - Asks/bids apply spreads around these bounds, respecting invariants: ask ≥ p_min, bid ≤ p_max.

Because λ is constant, quotes in money are straightforward and stable except when inventories change (MU changes). This is the simplest and most deterministic pathway to add money.

#### 3.2 Lagrange-multiplier (KKT) mode

- Standard consumer problem: maximize U_goods(A, B) subject to p_A·A + p_B·B ≤ M, A, B ≥ 0. L(A, B, λ) = U_goods(A, B) + λ(M − p_A·A − p_B·B).
- First-order conditions at interior optimum: ∂U/∂A = λ p_A and ∂U/∂B = λ p_B. Hence λ = MU_A/p_A = MU_B/p_B.
- Interpretation: λ is the marginal utility of income (value of a unit of money in utility terms); it depends on prices and the current consumption point.

Embedding in an ABM without global prices:
  - Each agent derives a local price vector in money p̂ = (p̂_A, p̂_B) from perceived neighbor quotes (e.g., median or deterministic aggregator of neighbor asks in M). Determinism requires tie-broken, sorted aggregation (see §6).
  - Given current inventories (A, B), the agent computes MU_A, MU_B, then estimates λ̂_A = MU_A/p̂_A and λ̂_B = MU_B/p̂_B. At KKT optimum they match; out of equilibrium they differ. We choose a deterministic combiner (e.g., min{λ̂_A, λ̂_B}) to avoid overestimating λ and to preserve feasibility.
  - The agent smooths λ via λ_{t+1} = (1−α)·λ_t + α·λ̂, updated in Housekeeping. Quotes for money then use λ_{t+1} exactly as in the quasi-linear formulas, but with λ dynamic.

This yields an endogenous, price- and state-dependent valuation of money consistent with standard theory while keeping the quote mechanics unchanged.

---

### 4) Mapping to existing systems

- State (`core/state.py`): Extend `Inventory` with `M: int` (see §10 for int vs float). Ensure mutation sets `inventory_changed=True`.
- Quotes (`systems/quotes.py`): Generalize to compute quotes for pairs (A↔B, A↔M, B↔M). Internally, prefer a generic representation keyed by ordered pairs (good_to_sell, good_to_buy) to avoid ad-hoc duplication.
- Matching/Trading (`systems/matching.py`, `systems/trading.py`): Parameterize `find_compensating_block` and `execute_trade` for arbitrary (X, Y) with Y ∈ {A, B, M}. Use existing round-half-up mapping for ΔY from price·ΔX.
- Perception/Decision: No special-casing beyond the availability of additional pairs and the computation of λ in KKT mode (see §6 and §7). Quotes remain stable per tick.

---

### 5) Utility engine changes (`econ/utility.py`)

- Keep existing UCES and ULinear implementations for goods. Standardize on `u_goods(A, B)` and marginal utilities `mu_A(A, B)`, `mu_B(A, B)`.
- Provide `u_total(A, B, M, λ)` as:
  - Quasi-linear mode: u_goods(A, B) + λ·M
  - KKT mode: u_goods(A, B) (money does not enter utility directly); we still use λ to convert money transfers to utility differences when evaluating surplus across heterogeneous trade pairs (§8).
- CES MRS must continue to use the zero-safe epsilon only for ratios, not for utility itself, preserving existing documentation contracts.

---

### 6) Price aggregation for KKT λ estimation

Goal: derive p̂_A and p̂_B from perceived neighbor quotes in money in a deterministic way.

- Candidate sources per good G:
  - Neighbor asks `ask_G_in_M` for selling G for M (price agents must pay in M to acquire G)
  - Neighbor bids `bid_G_in_M` (price agents receive in M to sell G)

We choose a conservative, purchase-oriented estimator to avoid infeasible demand:

- Collect all perceived `ask_G_in_M` within interaction radius (stable in tick), include the agent’s own ask to avoid empty sets.
- Deterministically aggregate using median of sorted list; if even cardinality, take lower median. Sort by (price, seller_id) for determinism.
- Fallback if all neighbor prices are missing: infer from cross quotes when available (e.g., `ask_G_in_B` and `ask_B_in_M` ⇒ implied `ask_G_in_M = ask_G_in_B · ask_B_in_M`), applying round-half-up only when mapping to quantities, not when compounding floats.

Given p̂_A, p̂_B and MU_A, MU_B:

- λ̂_A = MU_A / max(p̂_A, ε), λ̂_B = MU_B / max(p̂_B, ε)
- λ̂ = min(λ̂_A, λ̂_B) for feasibility. Deterministically break ties by favoring the good with smaller good-name (A before B).
- Smooth: λ_{t+1} = (1−α)·λ_t + α·λ̂ with α ∈ (0,1], set in scenario as `lambda_update_rate` (default small, e.g., 0.2).
- Clamp: λ_{t+1} ∈ [λ_min, λ_max] to avoid pathological shocks (parameters).

λ refresh occurs in Housekeeping only. If λ changes beyond a small tolerance, mark quotes dirty to recompute next tick, preserving "no mid-tick mutation".

---

### 7) Reservation prices and quotes in money

For any good G ∈ {A, B}, with marginal utility MU_G at current (A, B) and valuation λ (either constant or KKT-smoothed):

- Reservation price in money: p*_{G in M} = MU_G / λ
- Ask/bid with spreads (deterministic, scenario-configurable):
  - ask_G_in_M = max(p*_{G in M}, p_min) · (1 + s_ask)
  - bid_G_in_M = min(p*_{G in M}, p_max) · (1 − s_bid)
- Good-good reservation prices remain p*_{A in B} = MU_A / MU_B and p*_{B in A} = MU_B / MU_A with existing guards.

Quotes are stored generically for (sell, buy) pairs: (A,B), (B,A), (A,M), (B,M), and optionally (M,A), (M,B) if we ever allow market-making in the reverse direction. For now, we only need (G,M) and (G′,G) because money is the medium of exchange, not a consumption good.

---

### 8) Matching across heterogeneous pairs and surplus metric

We must compare trade candidates that pay in different media (goods vs money) using a common surplus metric. We standardize on ΔU_total measured in utility units.

- For a candidate trade of ΔX units of X for Y at price p (Y per X):
  - ΔY = round_half_up(p · ΔX)
  - Utility change if agent receives ΔX of X and pays ΔY of Y:
    - If Y ∈ {A,B}: ΔU = U_goods(A+ΔX, B−ΔY) − U_goods(A, B)
    - If Y = M: ΔU = U_goods(A+ΔX, B) − U_goods(A, B) − λ · ΔY (quasi-linear) or − λ_t · ΔY (KKT)
  - The partner's ΔU is computed symmetrically. Only execute if both sides have non-negative ΔU (strictly positive if we want strict Pareto gains) and respect budgets/feasibility.

`compute_surplus` thus becomes media-aware but remains purely deterministic. As before, we sort candidate pairs and only attempt one trade per unordered pair per tick.

---

### 9) Generic `find_compensating_block` for arbitrary (X, Y)

We generalize the search routine to take (good_to_buy=X, medium_to_pay=Y) and price p_Y_per_X from the chosen quote. It scans ΔX ∈ [1..dX_max] and computes ΔY via round-half-up, checking feasibility and mutual ΔU ≥ 0.

```python
def find_compensating_block(buyer, seller, good_to_buy, pay_with, price_y_per_x, dX_max):
    best = None
    for dX in range(1, dX_max + 1):
        dY = round_half_up(price_y_per_x * dX)
        if not feasible(buyer, seller, good_to_buy, pay_with, dX, dY):
            continue
        dU_buyer, dU_seller = surplus_changes(buyer, seller, good_to_buy, pay_with, dX, dY)
        if dU_buyer >= 0 and dU_seller >= 0:
            cand = (dU_buyer + dU_seller, dX, dY)
            best = max(best, cand) if best is not None else cand
    return best  # tie-break deterministically by dX, then agent ids if needed
```

`surplus_changes` uses λ (constant or KKT-smoothed) only when pay_with == M.

---

### 10) Type choice for M: int vs float

The roadmap draft mentioned `M: float`. That conflicts with the core convention that inventories are integers. To preserve determinism and avoid cumulative floating error, we propose:

- Represent `M` as an integer count of minor units (e.g., cents). Add `money_scale` to the scenario schema (default 1). Display/UI can render M/money_scale.
- Keep prices as floats. As with goods, convert money-to-quantity using round-half-up only at the last step when mapping to ΔM from price·ΔX.

If you require `M: float`, we can support it, but we will need stronger round-half-up and tolerance guards and may lose some determinism guarantees over long runs.

---

### 11) Scenario and schema updates

`src/scenarios/schema.py` additions (names indicative):

- money_mode: enum {"quasilinear", "kkt_lambda"}
- lambda_money: float (used only in quasilinear mode)
- lambda_update_rate: float in (0,1] (used in KKT mode)
- lambda_bounds: {lambda_min: float, lambda_max: float}
- money_scale: int ≥ 1
- initial_inventories may include M (integer minor units)

Backwards compatibility: default `money_mode = "quasilinear"` with λ=1.0 and `money_scale=1` keeps behavior simple.

---

### 12) Housekeeping integration

- Recompute λ in KKT mode during Housekeeping using perceived prices from the prior tick. Only then mark quotes dirty.
- Set `inventory_changed=True` whenever A, B, or M change; quotes recompute next tick. Separate flag `lambda_changed=True` may be used to trigger quote recomputation when λ moves.
- Telemetry: Log λ_t per agent, price aggregators p̂_A, p̂_B, and selected trade pairs. Extend `recent_trades_for_renderer` with ΔM when applicable.

---

### 13) Determinism and tie-breaking

- Sort agents by `agent.id` whenever iterating for λ updates or quote recomputation.
- Price aggregation: sort (price, neighbor_id) and use lower median for even counts.
- Candidate trades: when multiple pairs yield identical total surplus, break ties by a fixed ordering of pairs (A↔B precedes A↔M precedes B↔M) and then by agent ids.
- Keep one attempt per unordered pair per tick, unchanged.

---

### 14) Testing plan

- Unit tests:
  - MU-based reservation prices vs λ (quasi-linear and KKT) under UCES and ULinear
  - λ KKT estimation from synthetic price vectors; smoothing behavior and clamping
  - Round-half-up correctness mapping price·ΔX → ΔY for money and goods
- Integration tests:
  - Money trades execute when both sides gain utility; cooldowns respected
  - Mixed environment where money and barter both possible; best-surplus pair chosen deterministically
  - Determinism snapshot: fixed seed ⇒ invariant trade sequence across runs
- Performance tests: ensure no O(N²) regressions; price aggregation uses `SpatialIndex` perception outputs only.

---

### 15) Open questions for maintainer decision

1) Type of `M`: adopt integer minor units with `money_scale`, or allow float?
2) Price aggregator: median-lower on asks only, or combine asks and bids (e.g., mid)?
3) Tie-breaking order across pairs when surpluses equal: the proposed (A↔B ≺ A↔M ≺ B↔M) acceptable?
4) Strict vs weak Pareto gain threshold: require strictly positive ΔU on both sides?
5) Do we disable foraging for money (recommended) or allow exogenous money sources in scenarios?
6) Default λ bounds and α in KKT mode: suggested α=0.2, bounds [1e-6, 1e6].

---

### 16) Migration sketch (Milestone 3)

1) Core state: add `M` (int), add money-related flags, and extend `Quote` to generic pair store.
2) Utility: expose `u_goods`, `mu_A`, `mu_B`, and `u_total` wrapper.
3) Quotes: compute reservation prices for all pairs; add spreads.
4) KKT λ: implement deterministic price aggregation and λ update in Housekeeping.
5) Matching/Trading: generic (X, Y) handling; round-half-up for ΔY; budgets and cooldown unchanged.
6) Schema: add money_mode toggles and parameters; allow initial M.
7) Telemetry: log λ, p̂, ΔM; renderer reads ΔM for overlays.
8) Tests: add unit/integration suites; update existing trade tests to call generic matching.

---

### 17) Appendix A: Derivations and identities

- KKT identities at interior optimum: MU_A / p_A = MU_B / p_B = λ.
- Quasi-linear as special case: if U_total = U_goods + λ₀·M and prices are exogenous, the λ that rationalizes FOC is the constant λ₀; hence reservation in money p*_{G in M} = MU_G/λ₀.
- Cross-price inference (fallback): p_{A in M} ≈ p_{A in B} · p_{B in M}, avoiding rounding until quantity mapping.

---

### 18) Appendix B: Reference pseudocode snippets

```python
def compute_lambda_kkt(agent, perceived_money_prices, mu_A, mu_B, alpha, bounds):
    # perceived_money_prices: dict { 'A': list[(price, seller_id)], 'B': list[(price, seller_id)] }
    pA = aggregate_price(perceived_money_prices['A'])  # median-lower over (price, seller_id)
    pB = aggregate_price(perceived_money_prices['B'])
    eps = 1e-12
    lamA = mu_A / max(pA, eps)
    lamB = mu_B / max(pB, eps)
    lam_hat = min(lamA, lamB)
    lam_next = (1.0 - alpha) * agent.lambda_money + alpha * lam_hat
    lam_min, lam_max = bounds
    lam_next = min(max(lam_next, lam_min), lam_max)
    return lam_next
```

```python
def surplus_changes(buyer, seller, x, y, dX, dY, lambda_money):
    # x is good_to_buy ∈ {A,B}, y is medium_to_pay ∈ {A,B,M}
    if y == 'M':
        dUb = u_goods(buyer.A + (dX if x=='A' else 0), buyer.B + (dX if x=='B' else 0)) \
              - u_goods(buyer.A, buyer.B) - lambda_money * dY
        dUs = u_goods(seller.A - (dX if x=='A' else 0), seller.B - (dX if x=='B' else 0)) \
              - u_goods(seller.A, seller.B) + lambda_money * dY
    else:
        # pay in goods
        # move buyer +dX in x, -dY in y; seller symmetric
        # (details omitted for brevity)
        pass
    return dUb, dUs
```

---

If this direction looks right, I’ll proceed to implement the schema toggles, generic quotes, λ estimation, and matching generalization as outlined above.


