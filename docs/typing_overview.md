# VMT Type System & Data Contracts (v1′)

**Purpose.** Define language-agnostic types, invariants, and serialization contracts for VMT v1′ (foraging + bilateral exchange), scoped to **CES (incl. Cobb–Douglas)** and **Linear** utilities. This doubles as a migration guide for stricter/compiled targets (Rust/Go/TS) and a reference for tests and telemetry.

---

## 0. Principles & Conventions

* **Determinism-first.** All maps/sets keyed by stable identifiers; ordered iteration where specified.
* **Units.** Prices are **B-per-A**. Inventories, resources, ΔA, ΔB are **integers**. Utility values are **floats**.
* **Numerics.** `epsilon = 1e-12` unless scenario overrides. All MRS/ratio divisions use `max(x, epsilon)` guards.
  * Reserve names for future decoupling: `epsilon_mrs` (zero-safe ratios) and `epsilon_du` (ΔU tolerance). In v1′ both alias `epsilon`.
* **Zero-safe MRS**. For CES/CD when `(A,B)=(0,0)`, evaluate MRS/reservation using `(A+epsilon, B+epsilon)` only inside
  the econ module’s price/MRS math. Do not mutate inventories or the inputs to `u(A,B)` for ΔU checks.
* **Serialization.** Human-facing config = YAML; runtime and logs = CSV/JSONL. All top-level docs include `schema_version`.
* **Naming.** Canonical field names mirror planning docs: `move_budget_per_tick`, `vision_radius`, etc.

---

## 1. Core Primitives (language-agnostic)

```text
AgentID     := int (non-negative)
Good        := enum { "A", "B" }
Quantity    := int  // inventory/resource counts
Price       := float  // B per A
UtilityVal  := float
Coord       := tuple<int,int>  // (x,y)
Tick        := int  // ≥0
```

**Invariants.** `Quantity ≥ 0`. Trades conserve integer totals of A and B across agents.

---

## 2. Economic Types

### 2.1 Utility Parameters

```text
CESParams := {
  rho: float  // ρ ≠ 1 (elasticity σ = 1/(1−ρ))
  wA:  float > 0
  wB:  float > 0
}

LinearParams := {
  vA: float > 0,
  vB: float > 0
}
```

**Cobb–Douglas as special case.** Either `rho = 0` with weights `(wA,wB) ∝ (α, 1−α)`, or a thin wrapper mapping to CES.

### 2.2 Utility Discriminated Union

```text
Utility :=
  | { type: "ces",    params: CESParams }
  | { type: "linear", params: LinearParams }
  # Optional: { type: "cobb_douglas", params: { alpha: 0<α<1 } } // internally maps to CES
```

### 2.3 Quotes

```text
Quote := {
  ask_A_in_B: Price,  // seller’s ask in B per 1 A
  bid_A_in_B: Price   // buyer’s bid in B per 1 A
}
```

**Invariant.** For one agent at a time: `ask_A_in_B ≥ bid_A_in_B` given nonzero `spread`.

---

## 3. Agent & Environment State

```text
Agent := {
  id: AgentID,
  pos: Coord,
  inventory: { A: Quantity, B: Quantity },
  utility: Utility,
  quotes: Quote,
  vision_radius: int ≥ 0,
  move_budget_per_tick: int ≥ 0
}

Cell := {
  position: Coord,
  resource: { type: Good, amount: Quantity }
}

Environment := {
  grid_size: int ≥ 1,
  cells: array<Cell>
}
```

---

## 4. Scenario Schema (YAML)

```yaml
schema_version: 1
name: string
N: int  # grid_size
agents: int ≥ 1
initial_inventories:
  A: distribution | int
  B: distribution | int
utilities:
  mix: [ {type: "ces"|"linear"|"cobb_douglas", weight: float, params: {...}} ]
params:
  spread: float ≥ 0
  vision_radius: int ≥ 0
  interaction_radius: int in {0,1}
  move_budget_per_tick: int ≥ 0
  ΔA_max: int ≥ 1
  forage_rate: int ≥ 0
  epsilon: float > 0
  beta: float in (0,1)  # for foraging
resource_seed:
  density: float in [0,1]
  amount: distribution | int
```

**Distribution literals.** Supported forms: `uniform_int(lo,hi)`, `uniform(lo,hi)`. Parser must validate domain constraints.

---

## 5. Simulation Contracts

### 5.1 Tick Order (deterministic)

```text
Perception → Decision → Movement → Trade → Forage → Housekeeping
```

**Ordering contracts.**

* Agent loop ordered by ascending `AgentID`.
* Matching loop ordered by ascending `(min_id, max_id)`.
* Partner selection: argmax of `best_overlap` (then lowest `id`).

### 5.2 Surplus & Price

```text
best_overlap(i,j) := max( bid_i − ask_j,  bid_j − ask_i )  // prices in B per A
price := 0.5 * ( ask_seller + bid_buyer )
```

### 5.3 Trade Block (Compensating Multi-Lot)

```text
Given price p and ΔA_max:
Find minimal integer ΔA ∈ [1..ΔA_max] with ΔB = floor(p*ΔA + 0.5) ≥ 1   // round-half-up (portable)
s.t. improves(buyer, +ΔA, −ΔB) ∧ improves(seller, −ΔA, +ΔB)
```

**Invariants.**

* Trades update inventories atomically; recompute quotes immediately after each block.
* Repeat until no ΔU gain or constraints bind.

### 5.4 Foraging

```text
Harvest h = min(cell.resource.amount, forage_rate)
score(c) = ΔU_arrival(c) * beta^{dist(c)}  // primary policy
```

---

## 6. APIs & Interfaces (engine ↔ econ module)

```text
trait UtilityAPI {
  u(A:int, B:int) -> UtilityVal
  mu(A:int, B:int) -> (float,float) | null   // optional
  mrs_A_in_B(A:int, B:int) -> float | null   // optional
  reservation_bounds_A_in_B(A:int, B:int, eps:float) -> (Price, Price)
    // Must apply zero-safe MRS rule for CES/CD when A=B=0.
}
```

**v1′ requirement.** Bounds are **analytic only** (CES/Linear); no probe API exposed yet. Future: `reservation_bounds_discrete(...)` helper.

---

## 7. Telemetry Contracts

### 7.1 Logs (CSV/JSONL)

```text
TradeLog := {
  tick: Tick, x:int, y:int,
  buyer_id: AgentID, seller_id: AgentID,
  ΔA:int, ΔB:int, price:Price, direction:"i_buys_A"|"j_buys_A"
}

AgentSnapshot := {
  tick: Tick, id:AgentID, x:int, y:int,
  A:int, B:int, U:UtilityVal,
  partner_id:int|null,
  utility_type:"ces"|"linear"|"cobb_douglas"
}

ResourceSnapshot := { tick:Tick, cell_id:int, x:int, y:int, resource:int }
```

**Frequency.** Trades: every event. Snapshots: every `K` ticks (configurable, default 10).

---

## 8. Determinism & Reproducibility

* Random seeds recorded in run header. RNG sources centralized.
* No iteration over hash-map non-deterministic orders; use sorted keys/IDs.
* Quote reads during movement are **snapshots**; trades recompute on updated quotes.
* Matching considers unordered pairs within `interaction_radius in {0,1}` (0 = co-located, 1 = adjacent), processed by ascending (min_id,max_id).

---

## 9. Validation Rules

* Scenario validation ensures parameter domains (see §4).
* Agent validation ensures `A,B ≥ 0`, known utility `type`, well-formed params.
* Runtime guards: prevent self-trade; skip ΔB≤0; skip infeasible inventories.

---

## 10. Versioning & Compatibility

```text
schema_version: 1  // bump when adding fields or breaking semantics
compat:
  - v1′ supports ces, linear (and optional cobb_douglas alias)
  - reserved fields: p_scan_max (future), discrete_probe (future)
```

**Migration notes.** Any addition must be backwards-compatible or gated behind `schema_version`.

---

## 11. Cross-Language Mappings

### 11.1 Rust (serde + strong enums)

```rust
enum Good { A, B }
struct Quote { ask_a_in_b: f64, bid_a_in_b: f64 }
struct Inventory { a: i32, b: i32 }
struct CESParams { rho: f64, w_a: f64, w_b: f64 }
struct LinearParams { v_a: f64, v_b: f64 }

enum Utility {
  Ces(CESParams),
  Linear(LinearParams),
  CobbDouglas { alpha: f64 }, // optional alias
}
```

### 11.2 TypeScript (zod)

```ts
const Utility = z.union([
  z.object({ type: z.literal("ces"),    params: z.object({ rho: z.number(), wA: z.number().positive(), wB: z.number().positive() }) }),
  z.object({ type: z.literal("linear"), params: z.object({ vA: z.number().positive(), vB: z.number().positive() }) }),
  z.object({ type: z.literal("cobb_douglas"), params: z.object({ alpha: z.number().gt(0).lt(1) }) })
]);
```

### 11.3 Go (encoding/json)

```go
type Utility struct {
  Type   string      `json:"type"`
  Params interface{} `json:"params"`
}
```

---

## 12. Testable Invariants (Property-Based)

* **Midpoint price** symmetric: swapping roles flips direction only.
* **ΔU guard** monotonicity: if a block improves both, any subset block with smaller ΔA may fail; pick minimal ΔA.
* **Integer conservation**: sum of A and B across agents + cells is invariant except for foraging harvest from cells.
* **Spread sanity**: for a single agent, `ask > bid` whenever `spread > 0`.
* **Partner choice stability**: given fixed quotes, the chosen partner is argmax of `best_overlap` with id tie-break.

---

## 13. Future Hooks (not in v1′)

* `reservation_bounds_discrete(u_fn, ...)` helper for Leontief/LES.
* `p_scan_max` scenario param reinstatement.
* Multi-good extension: `Good := enum { A, B, ... }`, vectorized inventories and prices.

---

## 14. Glossary

* **MRS (marginal rate of substitution):** rate of tradeoff B-for-A that keeps utility constant.
* **Reservation price bounds:** [p_min, p_max] s.t. selling 1 A at `p≥p_min` or buying 1 A at `p≤p_max` is non-worsening.
* **Compensating multi-lot rounding:** Integer block trade with ΔU>0 for both sides at rounded price.