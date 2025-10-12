# Visualizing Microeconomic Theory (VMT) — Planning Document (FINAL)

**Version:** vFinal
**Date:** 2025-10-11

---

## Abstract

This document serves as the **foundational planning document** for the Visualizing Microeconomic Theory (VMT) project. It unifies architectural, theoretical, and algorithmic design decisions into a single, coherent specification. It guides the **implementation of the simulation platform**—initially focused on **agent foraging and bilateral exchange behaviors** on an NxN grid—while remaining extensible for future economic models and research modules.

This document supersedes **Planning-v3** and consolidates all subsequent algorithmic design decisions into the core plan. For v1’, we narrow the utility families to **CES (including Cobb–Douglas as a special case)** and **Linear (perfect substitutes)** via a **family-agnostic reservation-price interface**. Leontief and Stone–Geary are deferred to a later milestone.

---

## 1. Project Overview

### 1.1 Goals and Mission

The VMT project aims to build a **modular, visualization-first simulation environment** that demonstrates and explores microeconomic behavior. The platform has two core missions:

1. **Educational:** Provide intuitive, spatially grounded simulations that build intuition about economic behavior and theory.
2. **Research:** Offer a flexible environment for testing hypotheses, exploring emergent patterns, and experimenting with alternative utility forms and institutions.

### 1.2 Initial Focus (v1)

Agents move on an **NxN grid**, endowed with preferences over two goods (A, B), and are capable of:

* **Foraging:** Gathering resources from the grid based on local availability and utility.
* **Bilateral Exchange (Barter):** Broadcasting buy/sell quotes, moving toward profitable partners, and trading via a deterministic, ΔU-improving algorithm with **compensating multi-lot rounding**.

For v1’, the engine supports **CES (incl. Cobb–Douglas)** and **Linear**. Core mechanics (quotes, matching, ΔU acceptance) remain family-agnostic so that Leontief and Stone–Geary can be added later without touching the engine.

---

## 2. High-Level Architecture

### 2.1 Platform Choice

* **Language:** Python (no JavaScript).
* **Visualization:** Pygame (desktop app; Windows/Mac primary targets).
* **Performance:** NumPy baseline; Numba optional later if needed.

### 2.2 Core Modules

| Module       | Responsibility                                                                       |
| ------------ | ------------------------------------------------------------------------------------ |
| `grid`       | NxN environment, cell properties (resources), utility-free storage                   |
| `agents`     | Agent state, preferences, perception, movement, trading                              |
| `econ`       | Utility families + reservation-price API                                             |
| `simulation` | Tick orchestration: perception → decision → movement → trade → forage → housekeeping |
| `telemetry`  | Logging, statistics, data export                                                     |
| `scenarios`  | Parameter and world initialization via YAML                                          |
| `gui`        | Pygame visualization (agents, resources, perceived quotes)                           |

### 2.3 Tick Structure (Deterministic)

1. **Perception** – observe quotes/resources/agents within `vision_radius`.
2. **Decision** – select targets (partner or resource).
3. **Movement** – move toward targets (respect `move_budget_per_tick`).
4. **Trade** – bilateral exchange between co-located agents (or `interaction_radius` ≤ 1).
5. **Forage** – harvest resources on current cell.
6. **Housekeeping** – refresh quotes after utility changes, telemetry, logs.

---

## 3. Core Economic Models (v1)

### 3.1 Foraging

* Harvest `h = min(cell.resource.amount, agent.forage_rate)` (integer by default).
* Update inventories and cell resource; **refresh quotes** (utility changed).
* Movement policy when not targeting a partner: follow one of two configurable modes (scenario-level setting):
  * distance-discounted-utility-seeking (primary): Within `vision_radius`, compute a time-discounted score for each visible resource cell `c` using discrete-time discounting: `score(c) = ΔU_arrival(c) * β^dist(c)`, where `dist(c)` is the Manhattan distance to `c`, `β ∈ (0,1)` is a per-tick discount factor, and `ΔU_arrival(c)` is the expected utility gain from harvesting up to `forage_rate` units on arrival (bounded by `cell.resource.amount`). Path toward the argmax. If the utility family cannot resolve this choice via marginal tradeoffs (e.g., kinked preferences), fall back to nearest-resource tie-break logic below.
  * random-nearest-resource (fallback): Path to the nearest resource cell. Break ties by resource type ordering (e.g., A before B), then lowest x, then lowest y. If no resource visible, random walk.

### 3.2 Bilateral Exchange (Barter)

* Agents **broadcast quotes** (B per 1 A) derived from **family-agnostic reservation bounds** (§6.1).
* Agents **seek partners** with **positive surplus overlap** (bid ≥ ask) and navigate toward them.
* When co-located: trade at **midpoint price** using **compensating multi-lot rounding** to ensure integer transfers and strict **ΔU>0** for both agents.
* Repeat multi-lot blocks until no further mutually beneficial trade exists.

---

## 4. Simulation State Structure

### 4.1 Agent State

```yaml
id: int
pos: (x, y)
inventory:
  A: int
  B: int
utility:
  type: ces | linear   # Optional: cobb_douglas may map internally to CES
  params:
    # ces:          {rho: float ≠ 1, wA: >0, wB: >0}
    # linear:       {vA: >0, vB: >0}
quotes:
  ask_A_in_B: float
  bid_A_in_B: float
vision_radius: int
move_budget_per_tick: int
exchange_mode: barter         # v1 focuses on barter; cash mode later
```

### 4.2 Environment State

```yaml
grid_size: N
cells:
  - position: (x, y)
    resource:
      type: A | B
      amount: int
```

### 4.3 Scenario Parameters (Defaults)

```yaml
spread: 0.05
vision_radius: 3
interaction_radius: 1
move_budget_per_tick: 1
ΔA_max: 5
forage_rate: 1
epsilon: 1e-12
# p_scan_max: 100   # deferred (unused in v1’)
beta: 0.95         # per-tick discount for foraging policy
```

Scenarios may **mix utility families across agents**; parameters can be fixed or sampled.

---

## 5. Perception & Movement

### 5.1 Perception (short-range broadcast)

Each agent gathers:

* Neighbor agent ids and positions within `vision_radius`.
* Neighbor **quotes** (broadcast; read-only snapshot).
* Resource levels in local neighborhood.

### 5.2 Partner Selection (surplus-based)

For neighbor *j*, agent *i* computes:

```
overlap_dir1 = bid_A_in_B_i - ask_A_in_B_j   # i buys A from j
overlap_dir2 = bid_A_in_B_j - ask_A_in_B_i   # j buys A from i
best_overlap = max(overlap_dir1, overlap_dir2)
```

Candidates must have `best_overlap > 0`. Choose partner with **highest best_overlap**, tie → **lowest id**.

### 5.3 Movement

* If partner exists → **path toward partner** (respect movement budget).
* Else → **foraging policy** per §3.1: `distance-discounted-utility-seeking` (primary) or `random-nearest-resource` (fallback).

Agent iteration is deterministic (ascending `id`).

---

## 6. Operational Specifications (Family-Agnostic)

### 6.1 Quotes via Reservation-Price Bounds

All utility families implement a shared interface:

```python
class Utility:
    def u(self, A:int, B:int) -> float: ...
    def mu(self, A:int, B:int) -> tuple[float,float] | None: ...
    def mrs_A_in_B(self, A:int, B:int) -> float | None: ...
    def reservation_bounds_A_in_B(self, A:int, B:int, eps=1e-12) -> tuple[float,float]:
        """
        Return (p_min, p_max) with:
          p_min: min B-per-A s.t. selling 1 A for p >= p_min is non-worsening (ΔU≥0)
          p_max: max B-per-A s.t. buying 1 A paying p <= p_max is non-worsening (ΔU≥0)
        Use analytic MRS when well-defined.
        Note: v1’ is analytic-only (CES/CD and Linear); discrete ΔU probes are deferred.
        """
```

**Quote rule (family-agnostic):**

* `(p_min, p_max) = utility.reservation_bounds_A_in_B(A,B,eps)`
* `ask_A_in_B = p_min * (1 + spread)`
* `bid_A_in_B = p_max * (1 - spread)`
* **Broadcast** within `vision_radius`.
* **Refresh quotes** any time utility changes (inventory change from trade/forage).

**Reservation implementation hints (per family):**

**Reservation implementation hints (v1’ only):**
* **CES**: `MRS = (wA/wB) * (A/B)^(ρ−1)` with `A = max(A, ε)`, `B = max(B, ε)`; set `p_min = p_max = MRS`.
* **Cobb–Douglas (as CES special case)**: `MRS = (α/(1−α)) * (B/max(A,ε))`.
* **Linear (perfect substitutes)**: `MRS = vA / vB` (constant); set `p_min = p_max = vA/vB`.
* **Zero point (CES/CD) A=B=0**: use the zero-safe shift `(A+ε, B+ε)` for MRS/ratio evaluation only; do not alter raw inventories or u(·).
* **Deferred**: Leontief and Stone–Geary (LES) discrete-probe bounds.

### 6.2 Matching & Trading

1. **Pick direction** with positive surplus (overlap).
2. **Price**: midpoint between ask (seller) and bid (buyer).
3. **Compensating multi-lot rounding**:

  * Find the **minimal ΔA ≥ 1** such that `ΔB = round(p * ΔA)` yields **ΔU > 0 for both** and is feasible.
   * Search `ΔA ∈ [1..ΔA_max]`. If none exists, skip this pair/direction.
4. **Execute** the block; update inventories.
5. **Refresh quotes** for both agents (utility changed).
6. **Recompute** overlap and midpoint; **repeat** while ΔU-improving and feasible.

**Determinism & fairness:**

* Process co-located unordered pairs in ascending `(min_id, max_id)`.
* If both directions feasible, pick the **larger surplus** direction first.
* Tie-break partners by **surplus** then **id**.

### 6.3 Foraging Order

Recommended order per tick: **trade first, then forage**. Keep the choice consistent across runs.

---

## 7. Scenario Configuration (YAML)

Scenarios define grid size, agents, resources, and parameter defaults. v1’ supports **mixed CES/Linear populations**:

```yaml
schema_version: 1
name: barter_demo_v1
N: 32
agents: 40
initial_inventories:
  A: uniform_int(3,12)
  B: uniform_int(3,12)
utilities:
  mix:
    - {type: ces,    weight: 0.7, params: {rho: -0.5, wA: 1.0, wB: 1.0}}
    - {type: linear, weight: 0.3, params: {vA: 1.0, vB: 1.2}}
  # Optional: expose Cobb–Douglas explicitly and map internally to CES
  # - {type: cobb_douglas, weight: 0.0, params: {alpha: uniform(0.2,0.8)}}
params:
  spread: 0.05
  vision_radius: 3
  interaction_radius: 1
  move_budget_per_tick: 1
  ΔA_max: 5
  forage_rate: 1
  epsilon: 1e-12
  beta: 0.95
resource_seed:
  density: 0.1
  amount: uniform_int(1,3)
```

Validation in v1 is minimal; missing fields default to project defaults.

---

## Appendix: Types & Compatibility (v1’)

This planning document is paired with the source-of-truth typing spec in `typing_overview.md`. For quick reference:

```text
schema_version: 1  // bump when adding fields or breaking semantics
compat:
  - v1’ supports ces, linear (and optional cobb_douglas alias)
  - reserved fields: p_scan_max (future), discrete_probe (future)
```

See `typing_overview.md` for full schemas, invariants, telemetry formats, and cross-language mappings.

---

## 8. Telemetry & Logging

### 8.1 Logs (minimal v1)

* **Trades** (every trade):

```
tick, x, y, buyer_id, seller_id, ΔA, ΔB, price, direction
```

* **Agent snapshot** (every K ticks):

```
tick, id, x, y, A, B, U, partner_id(optional), utility_type
```

* **Resource snapshot** (optional, every K):

```
tick, cell_id, x, y, resource
```

### 8.2 Aggregation

* Keep per-tick trades; snapshot agents/resources every `K` ticks (e.g., 10) for size control.
* Derived measures (e.g., price dispersion) computed offline from trade logs.

---

## 9. Implementation Roadmap (v1)

| Stage | Feature                      | Description                                                                    |
| ----- | ---------------------------- | ------------------------------------------------------------------------------ |
| M0    | Core loop & telemetry        | Deterministic loop; telemetry hooks; seeds                                     |
| M1    | Foraging                     | Resource harvesting; movement & perception                                     |
| M2    | Quotes & partner targeting   | Utility registry; reservation bounds; broadcast; surplus-based movement        |
| M3    | Matching & trade             | Midpoint pricing; compensating multi-lot; ΔU guards; mixed utility populations |
| M4    | Telemetry refinement & tests | Trade logs, snapshots, deterministic tests                                     |

All milestones are unit-testable.

---

## 10. Econ Module (Utility Families)

Implement in `econ/utility.py` (v1’ scope):

* `UCES` (CES): `u`, `mu`, `mrs_A_in_B`, `reservation_bounds_A_in_B` (analytic).
* `ULinear` (Linear): same (analytic MRS constant).
* Optional thin wrapper `UCD` (Cobb–Douglas) mapping to CES special case.

Deferred to a later milestone: `ULeontief`, `ULES` and any discrete ΔU probe helpers.

---

## 11. Type Discipline & Naming

| Entity      | Convention                     |
| ----------- | ------------------------------ |
| Agent IDs   | Integers, globally unique      |
| Grid coords | `(x, y)` tuples, 0-indexed     |
| Goods       | `"A"`, `"B"`                   |
| Floats      | Utility values, prices, MRS    |
| Integers    | Inventories, ΔA, ΔB, resources |

All trades are **integer-conserving** for goods A and B.

---

## 12. Testing (v1)

* **Utility/MRS** sanity for each family.
* **Reservation bounds** yield sensible quotes (analytic for CES/CD and Linear).
* **Compensating block** search finds ΔA,ΔB when feasible; none otherwise.
* **Pair trade loop** terminates correctly; multi-block trade sequences are deterministic.
* **Mixed utility populations**: trades occur only when **both** ΔU>0.
* **Foraging**: inventory/cell conservation; quote refresh after harvest.
* **Determinism**: fixed seed → identical logs.

---

## 13. Economic Rationale (Brief)

* **Reservation-price quotes** unify marginal and kinked preferences in a single engine.
* **Bid/ask spreads** encode friction and avoid self-crossing.
* **Surplus-based targeting** drives agents toward mutually beneficial partners.
* **Midpoint + compensating multi-lot** ensures integer transfers and strict ΔU>0.
* **ΔU guard** preserves mutual benefit across all utility families.

---

## 14. Version History

| Version | Date       | Notes                                                                                                                        |
| ------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------- |
| v1      | 2025-09    | Initial planning draft                                                                                                       |
| v2      | 2025-09    | Integrated architectural revisions                                                                                           |
| v3      | 2025-10    | Added operational specs, cleaned structure                                                                                   |
| vFinal  | 2025-10-11 | **Multi-utility** architecture (CD, CES, Leontief, Linear, Stone–Geary); reservation-price API; full algorithmic integration |
| v1’     | 2025-10-11 | Scope reduction for prototype: **CES (incl. CD)** and **Linear** only; Leontief/LES deferred; `beta` added to scenarios     |

---

**END OF DOCUMENT**