# VMT Developer Checklist — v1 (Foraging + Bilateral Exchange, **Multi-Utility Updated**)

## 0) Setup & Structure

* [ ] Python 3.11
* [ ] Dependencies: `pygame`, `numpy` (optional later: `numba`, `matplotlib`)
* [ ] Project layout:

  ```
  vmt_engine/
    core/
    econ/
    systems/
  vmt_pygame/
  tests/
  scenarios/
  ```
* [ ] Determinism: process agents by **ascending `id`**; process pairs within `interaction_radius` by **(min_id,max_id)** ordering.

---

## 1) State & Defaults

* [ ] **Agent**

  ```yaml
  id: int
  pos: (x, y)
  inventory:
    A: int
    B: int
  utility:
    type: ces | linear   # Optional: cobb_douglas maps internally to CES
    params: {...}   # depends on type
  quotes:
    ask_A_in_B: float
    bid_A_in_B: float
  vision_radius: int = 3
  move_budget_per_tick: int = 1   # standardized name
  ```

* [ ] **Environment**

  * `grid_size: N`
  * `cells[(x,y)]: {resource:int}`

* [ ] **Scenario Parameters (Defaults)**

  * `spread = 0.05`
  * `interaction_radius = 1`
  * `ΔA_max = 5`
  * `forage_rate = 1`
  * `epsilon = 1e-12`
  * `vision_radius = 3`
  * `move_budget_per_tick = 1`
  * `beta = 0.95`
  # * `p_scan_max = 100`  (deferred; unused in v1’)

---

## 2) Core Econ Helpers

* [ ] **Utility families implemented in `econ/utility.py` (v1’ scope):**
  * `UCES` (CES; supports CD as a special case or via thin wrapper)
  * `ULinear` (Linear, perfect substitutes)

* [ ] Each utility must implement:

  ```python
  u(A, B)
  mu(A, B) -> optional marginal utilities
  mrs_A_in_B(A, B) -> optional analytic MRS
  reservation_bounds_A_in_B(A, B, eps) -> tuple[p_min, p_max]
  # CES/CD MUST handle (A=B=0) via zero-safe shift (A+eps, B+eps) for MRS/ratios only.
  ```

* [ ] Leontief & LES deferred; no discrete ΔU probes in v1’.

* [ ] `improves(agent, dA, dB)` uses `agent.utility.u()` for ΔU checks (no hardcoded α).

---

## 3) Per-Tick Loop (Deterministic)

1. **Perception**

   * [ ] For each agent: detect neighbors within `vision_radius`.
   * [ ] Read **broadcast quotes** (read-only snapshot).
   * [ ] Snapshot local resources.
2. **Decision**

   * [ ] Compute surplus overlap using ask/bid quotes:

     ```
     s1 = bid_i - ask_j   # i buys A from j
     s2 = bid_j - ask_i   # j buys A from i
     ```
   * [ ] Choose partner with **highest max(s1,s2)**; tie → lowest id.
3. **Movement**

  * [ ] Move toward partner (respecting `move_budget_per_tick`), else follow foraging movement policy (`distance-discounted-utility-seeking` or `random-nearest-resource`).
  * [ ] Step tie-break (deterministic): when multiple next steps are equally short, prefer reducing |dx| before |dy|; within each dimension prefer negative over positive; else lowest (x,y).
4. **Trade (pairs within `interaction_radius`)**

   * [ ] Select direction with positive surplus.
   * [ ] **Price** = midpoint between seller ask and buyer bid.
   * [ ] **Compensating multi-lot search**:

  * Find minimal ΔA ∈ [1..ΔA_max] s.t. ΔB=floor(p·ΔA+0.5) [round-half-up] gives ΔU>0 for both and is feasible.
   * [ ] Execute block; refresh both quotes; recompute; repeat until no ΔU improvement.
5. **Foraging**

   * [ ] If on resource: harvest `h = min(resource, forage_rate)` (integer).
   * [ ] Update inventory and cell; refresh quotes.
6. **Housekeeping**

   * [ ] Telemetry/logging.

---

## 4) Quote Logic (Broadcast)

* [ ] On **any utility change** (inventory change): recompute quotes using reservation bounds

  ```python
  p_min, p_max = agent.utility.reservation_bounds_A_in_B(A,B,epsilon)
  ask = p_min * (1 + spread)
  bid = p_max * (1 - spread)
  ```

* [ ] Quotes broadcast within `vision_radius`; trades require co-location or adjacency.

---

## 5) Foraging Rules

* [ ] Harvest only when standing on a resource cell.
* [ ] Ordering: **trade → forage** per tick, consistently.
* [ ] After harvesting, **refresh quotes**.

---

## 6) Determinism & Tie-Breaks

* [ ] Agent iteration: ascending `id`.
* [ ] Partner selection: highest surplus, then lowest id.
* [ ] Pair order: `(min_id,max_id)` ascending.
* [ ] Within pair: if both directions feasible, pick **larger surplus**.

---

## 7) Telemetry & Logging

* [ ] **Trades log** (every trade):

  ```
  tick,x,y,buyer_id,seller_id,ΔA,ΔB,price,direction
  ```
* [ ] **Agent snapshot** (every K ticks):

  ```
  tick,id,x,y,A,B,U,partner_id(optional),utility_type
  ```
* [ ] **Resource snapshot** (optional):

  ```
  tick,cell_id,x,y,resource
  ```

---

## 8) Edge Cases & Guards

* [ ] Handle `A==0` using utility’s reservation logic (no division by zero).
* [ ] Skip trades if inventories insufficient or ΔB ≤ 0.
* [ ] Refresh quotes after each trade block before continuing.
* [ ] Prevent self-trade and double counting.

---

## 9) Utility Module (UPDATED for v1’)

* [ ] Implement **base `Utility` class** with reservation interface.
* [ ] Implement `UCES` and `ULinear` only (optional `UCD` wrapper as CES special case).
* [ ] Ensure mixed-utility populations function seamlessly in trade.

---

## 10) Tests to Implement Early (v1’ scope)

* [ ] **Utility / Reservation Bounds**: correctness for CES (incl. CD limit) and Linear only.
* [ ] **Mixed Utility Trades**: heterogeneous CES/Linear parameters produce trades when surplus exists.
* [ ] **improves()** detects positive ΔU; rejects negative/zero.
* [ ] **Compensating block search** returns feasible ΔA,ΔB or None appropriately.
* [ ] **Pair trade loop** terminates deterministically after multi-block sequence.
* [ ] **Foraging**: harvest amount, inventory/resource conservation.
* [ ] **Determinism**: identical outputs for fixed seeds.
* [ ] Foraging Movement: distance-discounted-utility-seeking mode correctly identifies and paths to the best resource.
* [ ] (Deferred) Probe tests for Leontief/LES.
* [ ] **Integer conservation**: sum of A and B across agents + cells is conserved except for foraging harvest from cells.
* [ ] **Zero-inventory CES bound**: when A=B=0, CES reservation bounds are finite and monotone in params; no NaNs/inf.
* [ ] **Zero-safe scope**: ΔU checks use raw (A,B); changing epsilon must not change trade acceptance when A,B>0.
* [ ] **Direction choice**: when both directions have positive overlap, engine picks the **larger-surplus** direction first.

---

## 11) Minimal Scenario YAML (Example)

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
    - {type: ces,    weight: 0.7, params: {rho:-0.5, wA:1.0, wB:1.0}}
    - {type: linear, weight: 0.3, params: {vA:1.0, vB:1.2}}
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

---

## 12) “Done” Criteria for v1

* [ ] Agents broadcast quotes using **reservation bounds**.
* [ ] Mixed utility populations trade at midpoint with compensating multi-lot rounding.
* [ ] Telemetry and deterministic tick loop implemented.
* [ ] Foraging and quote refresh work.
* [ ] Pygame visualization shows agents/resources, minimal HUD.

