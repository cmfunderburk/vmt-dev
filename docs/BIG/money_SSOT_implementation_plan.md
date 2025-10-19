### Money Introduction — Single Source of Truth (SSOT) Implementation Plan

Author: VMT Assistant
Date: 2025-10-19

This SSOT specifies the authoritative implementation plan for introducing money into the VMT engine in alignment with approved decisions. It supersedes prior exploratory notes. No code changes should be made outside this plan without updating this document first.

---

### 0) Approved decisions (frozen)

- `M` is an integer inventory tracked in minor units; expose `money_scale ≥ 1` in schema.
- KKT price aggregation uses deterministic median-lower of neighbor asks in money per good, with sorting by `(price, seller_id)` and inclusion of self-ask.
- Execute trades only if both agents’ ΔU are strictly positive.
- Forbid foraging of money; money originates from initial endowments only (until production/labor markets exist).
- KKT smoothing defaults: `alpha=0.2`, `λ ∈ [1e-6, 1e6]`.
- Open item: exchange regime control (money-only vs mixed vs mixed-liquidity-gated) and tie-break policy in mixed regimes — to be finalized before enabling mixed mode.

---

### 1) Schema and scenario updates

Files: `src/scenarios/schema.py`, `src/scenarios/loader.py`, scenario YAMLs

- Add fields:
  - `money_mode: {quasilinear, kkt_lambda}` (default: `quasilinear`)
  - `money_scale: int` (default: 1)
  - `lambda_money: float` (quasi-linear only; default: 1.0)
  - `lambda_update_rate: float` (KKT only; default: 0.2)
  - `lambda_bounds: {lambda_min: float, lambda_max: float}` (KKT only; default: `[1e-6, 1e6]`)
  - `exchange_regime: {money_only, mixed, mixed_liquidity_gated}` (default: `money_only`)
  - `liquidity_gate: {min_quotes: int}` (only used if `exchange_regime = mixed_liquidity_gated`)
  - `forage_money: bool` (default: false)
- Allow `M` in `initial_inventories` as integer minor units.
- Loader: validate inter-field constraints; map legacy scenarios with missing fields to defaults.

Telemetry/Docs: update docs/README and UI to reflect new fields; ensure deterministic parsing order.

---

### 2) Core state extensions

Files: `src/vmt_engine/core/state.py`

- `Inventory`: add `M: int = 0` with invariant `M ≥ 0`.
- `Agent`:
  - Add `lambda_money: float` state (used differently per mode: constant in quasi-linear; dynamic in KKT).
  - Add flags `lambda_changed` and continue to use `inventory_changed` when A, B, or M mutate.
- `Quote` and quote container:
  - Generalize to support ordered pairs `(sell, buy)` ∈ {(A,B), (B,A), (A,M), (B,M)}.
  - Provide deterministic iteration order for stored pairs.

---

### 3) Utility module contracts

Files: `src/vmt_engine/econ/utility.py`

- Expose `u_goods(A,B)`, `mu_A(A,B)`, `mu_B(A,B)` for UCES and ULinear.
- Add `u_total(A,B,M,λ, mode)`:
  - `quasilinear`: `u_goods(A,B) + λ·M`
  - `kkt_lambda`: `u_goods(A,B)` (M excluded; λ used only for surplus conversion when money transfers occur)
- Maintain zero-safe ratio for MRS only; do not perturb utility levels.

---

### 4) Quotes system generalization

Files: `src/vmt_engine/systems/quotes.py`

- Compute reservation prices:
  - Goods-for-money: `p*_{G in M} = MU_G / λ`
  - Goods-for-goods: `p*_{A in B} = MU_A / MU_B`, `p*_{B in A} = MU_B / MU_A`
- Apply spreads and clamps to produce asks/bids with invariants `ask ≥ p_min`, `bid ≤ p_max`.
- Store quotes per ordered pair `(sell, buy)` using a stable key order.
- Recompute only in Housekeeping when `inventory_changed` or `lambda_changed`.

---

### 5) KKT λ estimation in Housekeeping

Files: `src/vmt_engine/systems/housekeeping.py` (or a dedicated λ updater)

- Per agent, compute perceived money prices:
  - Gather neighbor `ask_A_in_M`, `ask_B_in_M` within radius; include self; sort `(price, neighbor_id)`.
  - Aggregate by median-lower to get `p̂_A`, `p̂_B`. If empty, infer via cross quotes deterministically.
- Compute `μ_A, μ_B` at current `(A,B)`; form `λ̂_A = μ_A/max(p̂_A, ε)`, `λ̂_B = μ_B/max(p̂_B, ε)`; set `λ̂ = min(λ̂_A, λ̂_B)`.
- Smooth: `λ_{t+1} = (1−α)·λ_t + α·λ̂`; clamp to bounds. If `|λ_{t+1}−λ_t| > tol`, set `lambda_changed=True`.

---

### 6) Matching and trading generalization

Files: `src/vmt_engine/systems/matching.py`, `src/vmt_engine/systems/trading.py`

- Parameterize `find_compensating_block(buyer, seller, X, Y, price_y_per_x, dX_max)` where `Y ∈ {A,B,M}`.
- For each candidate `ΔX ∈ [1..dX_max]`, compute `ΔY = round_half_up(price_y_per_x · ΔX)` and test feasibility.
- Surplus calculation:
  - If paying in money: buyer uses `ΔU_buyer = u_goods(…new…) − u_goods(old) − λ·ΔM`; seller symmetric with `+ λ·ΔM`.
  - If paying in goods: use `u_goods` deltas only.
- Execute trade only if `ΔU_buyer > 0` and `ΔU_seller > 0`. Apply cooldown on failure as before.
- Candidate selection:
  - Enumerate permissible pairs based on `exchange_regime`:
    - `money_only`: allow only `(A,M)`, `(B,M)`.
    - `mixed`: also allow `(A,B)`.
    - `mixed_liquidity_gated`: allow `(A,B)` only if perceived money depth ≥ deterministic threshold fails.
  - Rank by total surplus; tie-break policy to be finalized (see §7.2).

---

### 7) Exchange regime controls (pending tie-break finalization)

7.1 Liquidity gate metric (deterministic):

- Define perceived depth per good as the count of distinct neighbor asks in money within radius (after dedup), or use a median-lower spread-normalized count. Sort neighbors deterministically; count threshold from `liquidity_gate.min_quotes`.

7.2 Tie-breaking in mixed regimes (to finalize):

- Option M-first: `A↔M ≺ B↔M ≺ A↔B` when total surplus ties.
- Option Barter-first: `A↔B ≺ A↔M ≺ B↔M`.
- Whichever is chosen must be applied consistently and documented for pedagogy.

---

### 8) Telemetry and UI

Files: `src/telemetry/*`, `src/vmt_pygame/renderer.py`, `src/vmt_log_viewer/*`

- Log per-agent `λ_t`, perceived `p̂_A`, `p̂_B`, chosen pair type, and `ΔM` on trades.
- Renderer: visualize money transfers and optionally overlay λ.
- Log viewer: filters for money trades and λ trajectories; CSV export includes `ΔM`.

---

### 9) Determinism safeguards

- Sort all agent loops by `agent.id`. Sort trade pairs by `(min_id, max_id)`.
- Use stable sort keys `(price, seller_id)` for price aggregation; lower median for even cardinality.
- Quotes stable within tick; update only in Housekeeping.
- Maintain integer invariants for inventories and round-half-up for quantity mapping.

---

### 10) Testing plan (must-pass gates)

- Unit tests:
  - λ KKT estimation determinism and smoothing bounds
  - Money reservation price calculations and spread application
  - Round-half-up from `price · ΔX` to `ΔY` for money and goods
  - Strictly positive surplus enforcement
- Integration tests:
  - Money trades execute with correct budgets and cooldowns
  - Exchange regimes: `money_only`, `mixed`, `mixed_liquidity_gated` behave as specified
  - Determinism snapshot with fixed seed across runs
- Performance: perception-based price aggregation does not introduce O(N²) paths.

---

### 11) Rollout plan

1) Implement schema/state changes behind feature flags; keep default scenarios unaffected.
2) Enable `money_only` with quasi-linear mode first; verify tests.
3) Add KKT λ estimation; verify determinism and stability.
4) Introduce `mixed` regime behind a config toggle, pending tie-break decision.
5) Add liquidity gate if selected; finalize documentation and demos.

---

### 12) Open items to finalize before mixed mode

- Tie-break order across pairs on equal surplus.
- Exact liquidity depth definition and default threshold.

Any change to these items must be reflected here before implementation proceeds.


