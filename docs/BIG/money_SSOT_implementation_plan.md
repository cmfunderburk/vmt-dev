### Money Introduction — Single Source of Truth (SSOT) Implementation Plan

Author: VMT Assistant
Date: 2025-10-19
Last Updated: 2025-10-19

This SSOT specifies the authoritative implementation plan for introducing money into the VMT engine in alignment with approved decisions. It supersedes prior exploratory notes. No code changes should be made outside this plan without updating this document first.

---

### 0) Approved decisions (frozen)

- `M` is an integer inventory tracked in minor units; expose `money_scale ≥ 1` in schema.
- KKT price aggregation uses deterministic median-lower of neighbor asks in money per good, with sorting by `(price, seller_id)` and inclusion of self-ask.
- Execute trades only if both agents' ΔU are strictly positive.
- Money cannot be foraged from the grid; money originates from initial endowments only. `earn_money_enabled` flag is a placeholder for future labor/production markets.
- KKT smoothing defaults: `alpha=0.2`, `λ ∈ [1e-6, 1e6]`.
- **Mode system architecture (Option A-plus)**: Keep existing `mode_schedule` (temporal control: WHEN activities occur). Add orthogonal `exchange_regime` (type control: WHAT bilateral exchanges are permitted within trade phases). Enhance telemetry to log active exchange pairs for observability.
- Exchange regime defaults to `barter_only` for backward compatibility with legacy scenarios.
- Tie-break policy in mixed regimes: Money-first (`A↔M ≺ B↔M ≺ A↔B`) when total surplus ties, to model monetary exchange as preferred institutional form.

---

### 1) Schema and scenario updates

Files: `src/scenarios/schema.py`, `src/scenarios/loader.py`, scenario YAMLs

**1.1) New fields in `ScenarioParams`:**

Add to the `params` section (not top-level):
  - `money_mode: Literal["quasilinear", "kkt_lambda"]` (default: `"quasilinear"`)
  - `money_scale: int` (default: `1`)
  - `lambda_money: float` (quasi-linear only; default: `1.0`)
  - `lambda_update_rate: float` (KKT only; default: `0.2`)
  - `lambda_bounds: dict[str, float]` with keys `lambda_min`, `lambda_max` (KKT only; default: `{"lambda_min": 1e-6, "lambda_max": 1e6}`)
  - `exchange_regime: Literal["barter_only", "money_only", "mixed", "mixed_liquidity_gated"]` (default: `"barter_only"`)
  - `liquidity_gate: dict[str, int]` with key `min_quotes` (only used if `exchange_regime = "mixed_liquidity_gated"`; default: `{"min_quotes": 3}`)
  - `earn_money_enabled: bool` (default: `False`) — placeholder for future labor/production income; currently unused

**1.2) Top-level schema changes:**

- Allow `M` in `initial_inventories` dict as integer minor units (e.g., `M: 100` or `M: [100, 150, 200]`)
- If `M` is not specified, default to `0` for all agents

**1.3) Validation logic:**

- If any money-related param is set (e.g., `money_mode`, `lambda_money`), verify `M` is present in `initial_inventories` or warn
- If `exchange_regime` is `"money_only"`, `"mixed"`, or `"mixed_liquidity_gated"`, require money inventory
- If `exchange_regime` is `"barter_only"` and no money params are set, this is a legacy pure-barter scenario
- `lambda_bounds` must satisfy `lambda_min < lambda_max` and both positive
- `liquidity_gate.min_quotes` must be positive

**1.4) Loader updates:**

- Parse `params.exchange_regime` and all money-related fields
- Map legacy scenarios: if `exchange_regime` is absent, default to `"barter_only"`
- Ensure deterministic field parsing order (use OrderedDict or explicit ordering if needed)

**1.5) Interaction with existing `mode_schedule`:**

The two systems are orthogonal:
- `mode_schedule` (existing): controls WHEN ForageSystem and TradeSystem execute ("forage" | "trade" | "both")
- `exchange_regime` (new): controls WHAT types of exchanges TradeSystem permits when it does execute
- Example: `mode_schedule` might say "trade mode active", and `exchange_regime="money_only"` refines this to "only monetary trades allowed"

Telemetry/Docs: update docs/README and UI to reflect new fields; document the two-layer control architecture.

---

### 2) Mode system integration architecture (Option A-plus)

**2.1) Two orthogonal control layers:**

VMT now has two independent but complementary control systems:

| Layer | Config Field | Controls | Values | System Impact |
|-------|-------------|----------|--------|---------------|
| **Temporal** | `mode_schedule` | WHEN activities occur | "forage" \| "trade" \| "both" | Which systems execute |
| **Type** | `exchange_regime` | WHAT exchanges permitted | "barter_only" \| "money_only" \| "mixed" \| "mixed_liquidity_gated" | Which pairs TradeSystem allows |

**2.2) How they compose:**

```python
# In Simulation.step()
current_mode = mode_schedule.get_mode_at_tick(tick)  # Temporal layer

if current_mode == "forage":
    # ForageSystem runs, TradeSystem skipped
    # exchange_regime irrelevant this tick
    
elif current_mode == "trade":
    # TradeSystem runs
    # Within TradeSystem, exchange_regime determines allowed pairs:
    if exchange_regime == "barter_only":
        allowed_pairs = [(A,B), (B,A)]
    elif exchange_regime == "money_only":
        allowed_pairs = [(A,M), (M,A), (B,M), (M,B)]
    # ... etc
    
elif current_mode == "both":
    # Both systems run
    # TradeSystem still respects exchange_regime
```

**2.3) Example configurations:**

| mode_schedule | exchange_regime | Behavior |
|--------------|-----------------|----------|
| None (always "both") | "barter_only" | Legacy pure-barter, both activities always available |
| forage:10, trade:10 | "barter_only" | Alternating time constraints, barter-only when trading |
| forage:10, trade:10 | "money_only" | Alternating time constraints, monetary exchange only |
| None | "money_only" | No time constraints, but only monetary exchange permitted |
| forage:15, trade:5 | "mixed" | Agents choose forage/trade timing AND barter/money type |

**YAML example** (alternating mode with money-only exchanges):
```yaml
# In scenario file
mode_schedule:
  type: global_cycle
  forage_ticks: 15
  trade_ticks: 10
  start_mode: forage

params:
  exchange_regime: money_only  # When trade mode active, only monetary exchanges
  money_mode: quasilinear
  lambda_money: 1.0
  # ... other params

initial_inventories:
  A: 10
  B: 10
  M: 100  # Initial money endowment
```

**2.4) Telemetry combines both:**

Each tick logs both dimensions:
```python
{
    "tick": 42,
    "current_mode": "trade",           # From mode_schedule
    "exchange_regime": "money_only",   # From params
    "active_exchange_pairs": ["A↔M", "B↔M"]  # Derived combination
}
```

**2.5) Renderer displays effective state:**

Top-left overlay shows combined state:
- "FORAGE MODE" (exchange_regime irrelevant)
- "TRADE MODE: Monetary Only [A↔M, B↔M]"
- "TRADE MODE: Barter Only [A↔B]"
- "TRADE MODE: Mixed [A↔M, B↔M, A↔B]"

**2.6) Future extensions align:**

Both systems will eventually support agent-specific and spatial variants:
- `mode_schedule.type = "spatial_zones"` → different grid regions have different temporal schedules
- `exchange_regime_type = "spatial_zones"` → different grid regions permit different exchange types
- These can be mixed: e.g., zone A has forage-only mode + barter-only regime; zone B has trade-only mode + money-only regime

---

### 3) Core state extensions

Files: `src/vmt_engine/core/state.py`

- `Inventory`: add `M: int = 0` with invariant `M ≥ 0`.
- `Agent`:
  - Add `lambda_money: float` state (used differently per mode: constant in quasi-linear; dynamic in KKT).
  - Add flags `lambda_changed` and continue to use `inventory_changed` when A, B, or M mutate.
- `Quote` and quote container:
  - Generalize to support ordered pairs `(sell, buy)` ∈ {(A,M), (M,A), (B,M), (M,B), (A,B), (B,A)}.
  - Provide deterministic iteration order for stored pairs.
  - Filter computed quotes by `exchange_regime` before storage (don't store quotes for disallowed pairs).

---

### 4) Utility module contracts

Files: `src/vmt_engine/econ/utility.py`

- Expose `u_goods(A,B)`, `mu_A(A,B)`, `mu_B(A,B)` for UCES and ULinear.
- Add `u_total(A,B,M,λ, mode)`:
  - `quasilinear`: `u_goods(A,B) + λ·M`
  - `kkt_lambda`: `u_goods(A,B)` (M excluded; λ used only for surplus conversion when money transfers occur)
- Maintain zero-safe ratio for MRS only; do not perturb utility levels.

---

### 5) Quotes system generalization

Files: `src/vmt_engine/systems/quotes.py`

- Compute reservation prices:
  - Goods-for-money: `p*_{G in M} = MU_G / λ`
  - Goods-for-goods: `p*_{A in B} = MU_A / MU_B`, `p*_{B in A} = MU_B / MU_A`
- Apply spreads and clamps to produce asks/bids with invariants `ask ≥ p_min`, `bid ≤ p_max`.
- Store quotes per ordered pair `(sell, buy)` using a stable key order.
- **Filter by exchange_regime**: Only compute and store quotes for pairs permitted by current `exchange_regime`.
- Recompute only in Housekeeping when `inventory_changed` or `lambda_changed`.

---

### 6) KKT λ estimation in Housekeeping

Files: `src/vmt_engine/systems/housekeeping.py` (or a dedicated λ updater)

- Per agent, compute perceived money prices:
  - Gather neighbor `ask_A_in_M`, `ask_B_in_M` within radius; include self; sort `(price, neighbor_id)`.
  - Aggregate by median-lower to get `p̂_A`, `p̂_B`. If empty, infer via cross quotes deterministically.
- Compute `μ_A, μ_B` at current `(A,B)`; form `λ̂_A = μ_A/max(p̂_A, ε)`, `λ̂_B = μ_B/max(p̂_B, ε)`; set `λ̂ = min(λ̂_A, λ̂_B)`.
- Smooth: `λ_{t+1} = (1−α)·λ_t + α·λ̂`; clamp to bounds. If `|λ_{t+1}−λ_t| > tol`, set `lambda_changed=True`.

---

### 7) Matching and trading generalization

Files: `src/vmt_engine/systems/matching.py`, `src/vmt_engine/systems/trading.py`

**7.1) TradeSystem execution control (respects both layers):**

- `TradeSystem.execute(sim)` first checks `sim.current_mode`:
  - If mode is `"forage"`, skip execution entirely (temporal control from `mode_schedule`)
  - If mode is `"trade"` or `"both"`, proceed to matching logic
- Within matching, respect `sim.params['exchange_regime']` to determine allowed pairs (type control)

**7.2) Parameterized trade mechanism:**

- Generalize `find_compensating_block(buyer, seller, X, Y, price_y_per_x, dX_max)` where `X, Y ∈ {A, B, M}`
- For each candidate `ΔX ∈ [1..dX_max]`, compute `ΔY = round_half_up(price_y_per_x · ΔX)` and test feasibility
- Check inventory constraints: `seller.X ≥ ΔX` and `buyer.Y ≥ ΔY`

**7.3) Surplus calculation:**

- If paying in money (`Y = M`): 
  - Buyer: `ΔU_buyer = u_goods(A_new, B_new) − u_goods(A_old, B_old) − λ·ΔM`
  - Seller: `ΔU_seller = u_goods(A_new, B_new) − u_goods(A_old, B_old) + λ·ΔM`
- If paying in goods (`Y ∈ {A,B}`):
  - Both: `ΔU = u_goods(A_new, B_new) − u_goods(A_old, B_old)`
- Execute trade only if `ΔU_buyer > 0` **and** `ΔU_seller > 0` (strictly positive)
- Apply cooldown on failure as before

**7.4) Exchange pair enumeration (exchange_regime control):**

Based on `exchange_regime`, enumerate permissible exchange pairs `(sell, buy)`:
- `"barter_only"`: only `(A,B)` and `(B,A)`
- `"money_only"`: only `(A,M)`, `(M,A)`, `(B,M)`, `(M,B)` — no goods-for-goods
- `"mixed"`: all six pairs allowed
- `"mixed_liquidity_gated"`: monetary pairs always allowed; `(A,B)` and `(B,A)` allowed only if liquidity depth check fails (see §8.1)

**7.5) Candidate pair ranking:**

- For each agent pair `(i, j)` within interaction radius, enumerate permissible exchange pairs
- Compute total surplus `ΔU_i + ΔU_j` for each feasible exchange
- Sort by total surplus descending
- On ties, apply deterministic tie-break:
  - **Money-first**: `(A,M) ≺ (B,M) ≺ (M,A) ≺ (M,B) ≺ (A,B) ≺ (B,A)` (lexicographic on pair type)
  - If still tied, break by `(min_id, max_id)` of agent pair
- Execute the top-ranked trade (one trade per pair per tick)

---

### 8) Exchange regime controls and liquidity gating

**8.1) Liquidity gate metric (for `mixed_liquidity_gated` regime):**

When `exchange_regime = "mixed_liquidity_gated"`, barter pairs `(A,B)` and `(B,A)` are conditionally enabled based on perceived money market depth:

- **Per-agent depth check**: For each agent considering barter, count distinct neighbor `ask_*_in_M` quotes within `vision_radius` (after deduplication by seller_id)
- **Threshold**: If count of distinct monetary quotes < `liquidity_gate.min_quotes`, enable barter pairs for that agent
- **Determinism**: Sort neighbors by `agent.id` before counting; include self-quotes in count
- **Rationale**: Agents fall back to barter when monetary markets are thin

**8.2) Tie-breaking policy (finalized):**

When multiple exchange pairs have equal total surplus, break ties deterministically:

1. **Pair type priority** (money-first): `(A,M) ≺ (B,M) ≺ (M,A) ≺ (M,B) ≺ (A,B) ≺ (B,A)`
   - Monetary exchanges preferred over barter (models institutional preference)
   - Lexicographic ordering for determinism
2. **Agent pair priority**: If pair types also tie, use `(min_id, max_id)` of trading agents
3. **Pedagogical note**: Money-first tie-breaking models the real-world preference for monetary exchange due to lower transaction costs and greater divisibility

---

### 9) Telemetry and UI

Files: `src/telemetry/*`, `src/vmt_pygame/renderer.py`, `src/vmt_log_viewer/*`

**9.1) Tick-level telemetry (enhanced for Option A-plus):**

Log per-tick state including:
- `current_mode` (from `mode_schedule`: "forage" | "trade" | "both")
- `active_exchange_pairs`: list of exchange pair types permitted this tick (e.g., `["A↔M", "B↔M"]` or `["A↔B"]`)
- Derived from combination of `mode` and `exchange_regime`

**9.2) Agent-level telemetry:**

Log per-agent per-tick:
- `λ_t` (marginal utility of money)
- `lambda_changed` flag
- Perceived prices `p̂_A`, `p̂_B` (from neighbor quote aggregation)
- If KKT mode: log intermediate `λ̂_A`, `λ̂_B`, and clamping events

**9.3) Trade-level telemetry:**

Log per-trade:
- `exchange_pair_type`: string like "A→M" (agent sold A for M) or "A→B"
- `ΔA`, `ΔB`, `ΔM` (quantity changes; 0 if good not involved)
- `price_realized`: the effective price `ΔY/ΔX`
- `ΔU_buyer`, `ΔU_seller` (surplus achieved)
- `buyer_lambda`, `seller_lambda` (if money involved)

**9.4) Renderer enhancements:**

- **Mode overlay**: Display `current_mode` and `active_exchange_pairs` in top-left corner
  - Example: "TRADE MODE: Monetary Only [A↔M, B↔M]"
  - Color-code: Gold for monetary, Green for barter, Blue for mixed
- **Money visualization**: 
  - Show `M` inventory as a small coin icon or numeric overlay
  - Animate money transfers with gold sparkles/flow
- **Lambda overlay** (optional toggle): Display `λ` as heatmap or per-agent value

**9.5) Log viewer updates:**

- **Mode filter**: Filter events by mode and active exchange pairs
- **Money trade query**: Dedicated view for trades involving M
- **Lambda trajectory**: Time-series plot of `λ_t` per agent
- **CSV export**: Include `mode`, `active_exchange_pairs`, and all money-related columns

---

### 10) Determinism safeguards

- Sort all agent loops by `agent.id`. Sort trade pairs by `(min_id, max_id)`.
- Use stable sort keys `(price, seller_id)` for price aggregation; lower median for even cardinality.
- Quotes stable within tick; update only in Housekeeping.
- Maintain integer invariants for inventories and round-half-up for quantity mapping.

---

### 11) Testing plan (must-pass gates)

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

### 12) Rollout plan

**Phase 1: Infrastructure (no behavioral changes)**
1. Add money fields to schema with defaults that preserve legacy behavior
   - `exchange_regime` defaults to `"barter_only"`
   - All money-related params optional
   - Loader handles missing fields gracefully
2. Add `M` to `Inventory` and agent state
3. Extend telemetry schema for money and active_exchange_pairs
4. Verify: all existing scenarios run identically

**Phase 2: Monetary exchange basics**
5. Implement quasi-linear utility with `money_mode="quasilinear"`
6. Implement money quotes and reservation prices
7. Enable `exchange_regime="money_only"` mode
8. Create test scenario with money endowments
9. Verify: money trades execute, barter blocked, strict surplus enforcement

**Phase 3: KKT λ estimation**
10. Implement neighbor price aggregation (median-lower)
11. Implement λ smoothing update in Housekeeping
12. Enable `money_mode="kkt_lambda"`
13. Verify: λ converges, determinism maintained, no O(N²) paths

**Phase 4: Mixed regimes**
14. Enable `exchange_regime="mixed"` with money-first tie-breaking
15. Test scenarios with both monetary and barter exchanges
16. Verify: tie-break policy works, mode transitions respected

**Phase 5: Liquidity gating**
17. Implement depth metric for `mixed_liquidity_gated`
18. Test scenarios with heterogeneous money holdings
19. Verify: barter emerges when money markets thin

**Phase 6: Polish and documentation**
20. Enhance renderer with mode overlays and money visualization
21. Extend log viewer with money filters and λ plots
22. Create demo scenarios showcasing each regime
23. Update docs/README with mode system architecture
24. Create pedagogical examples

---

### 13) Resolved design items

All major design decisions are now finalized:

✅ **Tie-break policy**: Money-first lexicographic ordering (§8.2)
✅ **Liquidity depth metric**: Count of distinct neighbor monetary quotes with deterministic sorting (§8.1)
✅ **Mode system integration**: Two-layer architecture with `mode_schedule` (temporal) + `exchange_regime` (type control) (§0, §2)
✅ **Backward compatibility**: `exchange_regime="barter_only"` default preserves legacy behavior (§1)
✅ **Forage money**: Renamed to `earn_money_enabled`, currently a placeholder (§1.1)

### 14) Future extensions (post-initial-rollout)

**14.1) Agent-specific and spatial exchange regimes:**

- Extend `exchange_regime` from global to per-agent or zone-based
- Mirror the planned `mode_schedule` extensions (agent_specific, spatial_zones)
- Example: Some agents have access to money, others don't (heterogeneous market access)
- Implementation: Add `exchange_regime_type` analogous to `ModeType`

**14.2) Endogenous money acquisition:**

- Implement labor markets where agents earn money by foraging
- Implement production where agents sell output for money
- Activate `earn_money_enabled` flag to gate these features
- Requires new systems: LaborSystem, ProductionSystem

**14.3) Credit and debt:**

- Allow negative `M` (debt) with borrowing constraints
- Add interest rate parameters
- Implement credit market matching

**14.4) Multiple currencies:**

- Extend from single `M` to `M1`, `M2`, etc.
- Add exchange rate dynamics
- Model currency competition

**14.5) Dynamic regime switching:**

- Allow `exchange_regime` to change endogenously based on simulation state
- Example: Switch to `barter_only` if aggregate money supply drops below threshold
- Implement as a new system or extend HousekeepingSystem

---

Any change to the core decisions in §0-13 must be reflected in this document before implementation proceeds.


