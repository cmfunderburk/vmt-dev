# VMT Algorithmic Planning — Source of Truth (Foraging + Bilateral Exchange, v1)

> This document specifies the **algorithmic behavior** of agents on the NxN grid for the initial **Foraging** and **Bilateral Exchange (barter)** systems.
> It is **implementation-ready** and encodes all **final decisions** to date, updated to match the multi-utility architecture specified in `Planning-FINAL.md`.
> Future extensions (cash/LOB, advanced bargaining, global signals) are out of scope for v1.

---

## 0) Scope & Assumptions

* Goods: **A**, **B** (integer units). Inventories and cell resources are integers.
* For v1’, agents are endowed with utility functions from **two** supported families: **CES** (including Cobb–Douglas as a special case) and **Linear** (perfect substitutes). Leontief and Stone–Geary (LES) are deferred.
* Quotes are generated using **family-agnostic reservation-price bounds**.
* Agents live on an **NxN grid**, move using **Manhattan distance**, and interact via **short-range broadcast** (quotes within `vision_radius`).
* Trade requires **co-location or adjacency** depending on `interaction_radius`.
* Deterministic processing:
    * Agent loop: **ascending `id`**
    * Partner tie-break: **surplus** then **id**
    * Pair order: **(min_id,max_id)** ascending

---

## 1) Core Economic Quantities & Quote Policy

### 1.1 Reservation Price Bounds

For each agent *i* with inventory `(A_i, B_i)`, compute:

```python
p_min, p_max = agent.utility.reservation_bounds_A_in_B(A_i, B_i, epsilon)
ask_A_in_B_i = p_min * (1 + spread)
bid_A_in_B_i = p_max * (1 - spread)
```

This replaces earlier hardcoded MRS formulas. Each supported family provides `reservation_bounds_A_in_B`. In v1’, bounds are **analytic only** (CES/CD and Linear); discrete ΔU probes are deferred.
#### Zero-inventory guard (A = B = 0)
For CES (incl. Cobb–Douglas), when A = B = 0 the MRS is undefined. In v1′ we resolve this
by applying a zero-safe shift only inside reservation/MRS calculations:

    A′ = A + ε_mrs,  B′ = B + ε_mrs,  with ε_mrs = epsilon

Use (A′, B′) in any ratio/MRS expression; keep raw (A, B) for utility u(·) and inventory.
This keeps quotes well-defined without distorting ΔU checks.

---

### 1.2 Quote Refresh

Quotes are refreshed **whenever an agent’s utility changes**, i.e. after trade, foraging, or any inventory update.

---

### 1.3 Movement & Interaction Radii

* `move_budget_per_tick`: max grid steps per tick.
* `vision_radius`: range for perceiving quotes/resources.
* `interaction_radius`: range for trade (0 = same cell, 1 = adjacent).

---

## 2) Perception

Each tick, each agent builds:

* `neighbors` = agents within `vision_radius` (id, pos, quotes snapshot).
* `quotes_nearby` = broadcasted ask/bid from neighbors.
* `resource_view` = local resource field for foraging heuristics.

---

## 3) Partner Selection & Movement

### 3.1 Surplus Computation

For agent *i* considering neighbor *j*:

```
overlap_dir1 = bid_A_in_B_i - ask_A_in_B_j   # i buys A from j
overlap_dir2 = bid_A_in_B_j - ask_A_in_B_i   # j buys A from i
best_overlap = max(overlap_dir1, overlap_dir2)
```

Positive overlap indicates a feasible price interval in at least one direction.

---

### 3.2 Partner Choice (Deterministic)

Among neighbors with `best_overlap > 0`, pick the partner with:

1. Highest `best_overlap`, then
2. Lowest partner id.

---

### 3.3 Movement Intent

* If a partner exists → move toward partner (respecting `move_budget_per_tick`).
* Else → follow foraging/exploration policy (§6).

Step tie-break (deterministic Manhattan navigation): when multiple next steps are equally short, prefer reducing |dx| before |dy|; within each dimension prefer negative direction over positive; else choose the step that leads to the lowest (x,y).

---

## 4) Trade Execution (Co-located or Interaction Radius ≤ 1)

### 4.1 Price Rule

Price = **midpoint** between crossed quotes in the chosen direction:

```
p = 0.5 * (ask_seller + bid_buyer)
```

---

### 4.2 Compensating Multi-Lot Rounding

For integer transfers:

* Find the **minimal ΔA ≥ 1** such that ΔB = floor(p·ΔA + 0.5) [round-half-up, portable] makes both agents strictly better off (ΔU>0) and is feasible.
* Search ΔA in [1..ΔA_max].
* If none found, skip trade in that direction.

---

### 4.3 Multi-Block Continuation

After executing a block:

1. Refresh both agents’ quotes.
2. Recompute overlap.
3. If still positive and feasible, repeat.
4. Stop when ΔU≤0 or inventory constraints bind.

---

### 4.4 Acceptance Guard

```python
improves(buyer, +ΔA, -ΔB) and improves(seller, -ΔA, +ΔB)
```

where `improves` uses `agent.utility.u()` for ΔU checks, not hardcoded α.

---

### 4.5 Pair Ordering

Process unordered pairs `(i,j)` within `interaction_radius` (0 = co-located, 1 = adjacent) in ascending `(min_id,max_id)`.

---

## 5) Per-Tick Algorithm (Barter Mode)

```pseudo
for tick in 1..T:

  # (1) Perception
  for agent i (id ascending):
      neighbors_i := within vision_radius
      quotes_i := snapshot of neighbors' quotes
      resources_i := local resource snapshot

  # (2) Decision
  for agent i (id ascending):
      partner := argmax_surplus(neighbors_i)
      if partner:
          move toward partner (budget)
      else:
          forage/explore

  # (3) Movement
  apply_moves_for_all()

    # (4) Matching & trade
    for each unordered pair (i,j) with Manhattan distance ≤ interaction_radius, ordered by (min_id,max_id):
      pick surplus direction
    p := 0.5 * (ask_seller + bid_buyer)
      find compensating ΔA block using reservation-based ΔU
      if found: execute, refresh, repeat until no ΔU gain

  # (5) Foraging
  if agent on resource: harvest; refresh quotes

  # (6) Logging
  update telemetry
```

Order (trade → forage) is fixed for determinism.

---

## 6) Foraging Policy

On a resource cell with `resource.amount > 0`:

* Harvest `h = min(resource.amount, forage_rate)` (integer).
* Update inventory and cell.
* Refresh quotes (utility changed).

When not targeting a partner, movement follows one of two configurable modes:

1) distance-discounted-utility-seeking (primary)
    * Within `vision_radius`, compute a time-discounted score for each visible resource cell `c` using Manhattan distance as a proxy for time to arrival:
      * `score(c) = ΔU_arrival(c) * β^dist(c)` where `dist(c)` is the Manhattan distance to `c` and `β ∈ (0,1)` is a per-tick discount factor.
      * `ΔU_arrival(c)` is the expected utility gain from harvesting up to `forage_rate` units upon arrival, bounded by `c.resource.amount`.
    * Path toward the cell with maximal score. If a utility family cannot resolve marginal trade-offs, fall back to the nearest-resource tie-break logic below.

2) random-nearest-resource (fallback)
    * Path to the nearest resource cell by Manhattan distance.
    * Tie-breaks: resource type (A before B), then lowest x, then lowest y. If no resource is visible, perform a random walk.

---

## 7) Determinism & Fairness

* Fixed agent iteration and pair ordering.
* Partner tie-breaking by surplus then id.
* Multi-lot block search starts at ΔA=1; first acceptable block chosen.
* Quotes during movement are snapshots; trade recomputes on updated quotes.
* Matching considers unordered pairs within `interaction_radius` (0 = co-located, 1 = adjacent), ordered by `(min_id,max_id)`.

---

## 8) Parameters (Defaults)

```
spread = 0.05
vision_radius = 3
interaction_radius = 1
move_budget_per_tick = 1
ΔA_max = 5
forage_rate = 1
epsilon = 1e-12
# p_scan_max = 100   # deferred (unused in v1’)
beta = 0.95
```

---

## 9) Telemetry & Logging

* **Trades log**: `tick,x,y,buyer_id,seller_id,ΔA,ΔB,price,direction`.
* **Agent snapshot**: includes `utility_type` for mixed populations.
* **Resource snapshot** optional.

---

## 10) Edge Cases & Guards

* Reservation bounds handle A=0 gracefully per utility definition.
* If no feasible ΔA block exists, skip trade.
* If both directions feasible, pick larger surplus.
* Prevent self-trade and double counting.
* Deferred families (Leontief, Stone–Geary): probe-based reservation bounds are not implemented in v1’.
* CES zero point: when A=B=0, compute reservation bounds using (A+ε, B+ε) for MRS/ratios only. Do not modify inventories or u(·) arguments.

---

## 11) Utility-Agnostic Integration

* All trading and movement logic uses **reservation bounds** and `u()` rather than family-specific formulas.
* This allows **mixed utility populations** to trade deterministically with strict ΔU>0 guards.

---

## 12) Clean Pseudocode (Updated)

### 12.1 Quote Computation

```python
def compute_quotes(agent, spread, epsilon):
    A, B = agent.inventory['A'], agent.inventory['B']
    p_min, p_max = agent.utility.reservation_bounds_A_in_B(A, B, epsilon)
    agent.quotes['ask_A_in_B'] = p_min * (1 + spread)
    agent.quotes['bid_A_in_B'] = p_max * (1 - spread)
    agent.quote_ts = tick
```

---

### 12.2 Counterparty Selection

Unchanged except uses updated quotes (already family-agnostic).

---

### 12.3 Compensating Multi-Lot Trade Block

```python
def find_comp_block(buyer, seller, p, A_max=5, eps=1e-12):
    for dA in range(1, A_max+1):
        # round-half-up (portable across languages)
        from math import floor
        dB = int(floor(p * dA + 0.5))
        if dB <= 0: continue
        if seller.inventory['A'] < dA or buyer.inventory['B'] < dB: continue
        if improves(buyer, +dA, -dB, eps) and improves(seller, -dA, +dB, eps):
            return dA, dB
    return None
```

---

### 12.4 ΔU Check (Utility-Agnostic)

```python
def improves(agent, dA, dB, eps=1e-12):
    A0, B0 = agent.inventory['A'], agent.inventory['B']
    u0 = agent.utility.u(A0, B0)
    u1 = agent.utility.u(A0 + dA, B0 + dB)
    return u1 > u0 + eps
```

This `return u1 > u0 + eps` line implements a strict utility improvement check for trade acceptance.

---

## 13) Final Notes

This updated spec:

* Removes Cobb–Douglas hardcoding.
* Aligns quote logic, matching, and trade with **family-agnostic reservation-price API**.
* Supports **mixed utility populations** deterministically.
* Preserves the pedagogical simplicity of compensating multi-lot barter while extending to richer preference structures.

---

✅ **This version fully supersedes the original algorithmic_planning.md** and should be used as the authoritative specification for implementation going forward.