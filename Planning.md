# A Comprehensive Implementation Plan for the Visualizing Microeconomic Theory (VMT) Project — **Python-Only, Grid-First Rewrite**

> This draft preserves the **overall structure** of the earlier planning document while updating the architecture and delivery approach to a **pure-Python** desktop app centered on **Pygame** and a unified, grid-based agent system. (We intentionally diverge from the previously proposed Python+JS hybrid and browser execution loop. )

---

## Introduction: A Blueprint for the Next-Generation VMT

This rewrite delivers a single-language, desktop-class simulation that showcases microeconomic behavior with **agents moving and interacting on an NxN grid**. The core concepts:

* **One foundational agent framework** with toggleable behaviors (foraging, bilateral exchange, price discovery/market-clearing).
* **Delta-based engine** (`step → deltas → apply`) for clarity, replay, and performance.
* **Pygame renderer** with a fixed-timestep sim (default **10 Hz**, configurable in-app) and smooth 60 FPS rendering.

We retain the spirit and structure of the prior plan (architecture → engine → phased modules → UX → robustness), adapted to this new runtime.  

---

## Section 1: Foundational Architecture and Technology Stack

### 1.1 Architectural Pattern

* **Decoupled Engine & Renderer**:

  * `vmt_engine` is UI-agnostic (agents, grid, utilities, matching, deltas).
  * `vmt_pygame` owns the event/visual loop and HUD.
* **Deterministic, fixed-timestep simulation** with an accumulator (sim **10 Hz** default, render up to **60 FPS**).
* **Delta log** for replay, testing, and educational “step-through” demonstrations.

*(This mirrors the earlier emphasis on a clean separation of concerns and a well-defined project scaffold, adapted from web/Dash to a desktop loop.)*

### 1.2 Core Technology Stack (Python-only)

* **Runtime**: Python 3.11
* **Rendering/Input**: **Pygame**
* **Numerics**: **NumPy** (required); **Numba** optional for hot paths
* **Analysis (post-run)**: **Matplotlib** (optional)
* **Packaging**: PyInstaller (Win/macOS targets first)

*(Earlier plan foregrounded the scientific Python stack; we keep these foundations while removing Dash/Plotly from the runtime path.)*

### 1.3 Project Scaffolding & Environments

* **Repo layout** (engine vs. app), unit tests, and deterministic seeds.
* **Dependencies** pinned via `pyproject.toml`; optional extras: `numba`, `matplotlib`.
* **Cross-platform packaging** with CI artifacts for Windows and macOS.

*(We preserve the previous emphasis on strong structure and env management; directory roles are adapted to Pygame in place of Dash.)*

---

## Section 2: The Economic Engine — Unified Grid-Based Agent Framework (`vmt_engine`)

### 2.1 State & Schema (NxN grid)

```python
state = {
  "time": 0,
  "params": {
    "N": 32, "sim_dt": 0.1, "rng_seed": 123,
    "behavior": {
      "foraging": True, "search_trade": False, "market_clearing": False,
      "exchange_mode": "barter" | "cash",
      "vision_radius": 3, "interaction_radius": 1,
      "move_budget_per_tick": 1,
      "trade_step": 0.05, "price_adjust_k": 0.02,
      "lot_size": 1, "cash_tick_size": 0.1
    }
  },
  "environment": {
    "grid_size": [N, N],
    "cells": [ { "resource": 0.0,
                 "posted_offers": [],   # bids/asks in cash mode
                 "price_signal": None } for _ in range(N*N) ]
  },
  "agents": [
    {"id": 7, "pos": [x,y],
     "inventory": {"A":2.0, "B":5.0, "$":0.0},
     "traits": {"alpha":0.6, "move_cost":0.05, "forage_eff":1.0},
     "policy": {"forage":True, "seek_trade":True,
                "post_offers":False, "follow_prices":False},
     "beliefs": {"target_price_A":None}, "utility": 0.0}
  ],
  "outputs": {"telemetry": {}, "logs": []}
}
```

### 2.2 Delta-Based Simulation Contract

* **Engine API**

  * `initialize_state(params) -> dict`
  * `step(state, dt) -> list[delta]` (no mutation)
  * `apply_delta(state, deltas) -> None` (single mutation point)
  * `analytics(state) -> dict` (optional)
* **Delta vocabulary** (grid-first, works for all scenarios)

  * Movement: `{"op":"move","id":i,"to":[x,y]}`
  * Cell interaction: `{"op":"harvest"| "deposit","id":i,"cell":[x,y],"resource":"A","d":float}`
  * Offers: `{"op":"post_offer"| "retract_offer","cell":[x,y],...}`
  * Trades (barter or cash):
    `{"op":"trade","i":i,"j":j,"give":{"A":2},"take":{"B":1}}` *(barter, integers)*
    `{"op":"trade","i":i,"j":j,"give":{"A":2},"take":{"$":3.4}}` *(cash: good=integer lots, money=float)*
  * Signals/HUD: `{"op":"set_cell",...}`, `{"op":"telemetry",...}`, `{"op":"set_utility",...}`, `{"op":"set_belief",...}`

### 2.3 Five-Stage Step Pipeline (per tick)

1. **Perception**: neighborhood scan (resources, offers, neighbors, price signals).
2. **Decision**: movement intent; barter proposals; order posting rules.
3. **Matching**:

   * **Barter mode**: integer bundle search with ΔU>0 for both sides.
   * **Cash mode**: cell **bulletin-board** matcher crossing bids/asks (lot size, TTL, tick size).
4. **Transitions**: craft deltas for moves, trades, updates.
5. **Apply & Housekeeping**: apply deltas once; update cached utility/beliefs; emit telemetry/logs.

---

## Section 3: Scenario Presets (Educational Modules over One Engine)

> We keep the “phased module” spirit of the earlier plan but express them as **presets** that flip behaviors and seeds rather than switching model classes. 

### 3.1 Foraging (Instantiation & Spatial Behavior)

* **Toggles**: `foraging=True`, trading off; resource seeding on grid.
* **Goal**: demonstrate utility/choice functions and movement/search dynamics.
* **HUD**: inventory distributions, total harvested, utility snapshots.

### 3.2 Bilateral Exchange (Search on the Grid)

* **Mode**: `exchange_mode="barter"`, `search_trade=True`, `interaction_radius=1`.
* **Logic**: local integer bundle proposals; mutual ΔU>0 acceptance; lot cap per tick.
* **HUD**: accepted trades count, per-agent utility changes, convergence hints.

### 3.3 Market-Clearing / Price Discovery (Local Order Books)

* **Mode**: `exchange_mode="cash"`, `post_offers=True`, optional tatonnement smoothing per cell.
* **Logic**: per-cell bid/ask matcher (FIFO within price); price signal updated on fills.
* **HUD**: last trade price per cell, global avg price & excess demand estimate.

---

## Section 4: Crafting the Interactive User Experience with **Pygame**

*(This section mirrors the original “UX” chapter but focuses on a desktop loop and HUD rather than Dash pages.)*

### 4.1 App Loop & Controls

* **Loop**: accumulator-based fixed timestep (sim **10 Hz** default; GUI slider for 5–60 Hz), render up to 60 FPS.
* **Hotkeys**: `Space` pause/resume, `R` reset, `1/2` slower/faster, `Esc` quit.
* **Preset Menu**: scenario presets selectable at start.

### 4.2 Rendering

* **Grid**: static background surface; agents as circles/rects; cell overlays for price/resource heatmaps.
* **HUD**: FPS, tick, sim speed, aggregates (trades, average price, total utility).
* **Order Book Peek** (cash mode): optional minimal panel listing top-of-book for the current cell under cursor.

### 4.3 Pedagogical Overlays

* Toggleable MRS arrows for sample agents; utility contours (sparse); markers at most recent trades.

---

## Section 5: Ensuring Robustness and Planning for the Future

### 5.1 Testing & Validation

* **Engine unit tests**: conservation, ΔU>0 acceptance, integer invariants (barter), matcher fairness, determinism via seeds.
* **Analytics checks**: tatonnement vs. analytic benchmarks where applicable.
* **Smoke tests**: app boots, runs fixed ticks, no exceptions.

### 5.2 Logging, Exports, and Analysis

* **CSV output** every *N* ticks (prices, trades, utilities).
* Optional **Matplotlib** post-run charts (non-blocking).
* **Delta logs** enable replay and classroom “step” demonstrations.

### 5.3 Roadmap & Optional Extensions

* Larger agent counts with **Numba** acceleration (opt-in).
* Replay/snapshot scrubbing UI.
* Alternate renderer (Qt/PyQtGraph) without changing the engine.

*(This section carries forward the prior plan’s robustness and roadmap emphasis, adjusted to the new stack.)*

---

## Project Structure (Concrete)

```
vmt/
├─ vmt_engine/
│  ├─ core/            # state.py, grid.py, agent.py, delta.py
│  ├─ econ/            # utility.py (registry: Cobb-Douglas, CES, Leontief, Linear, LES, Quasi-linear), pricing.py
│  ├─ systems/         # perception.py, decision.py, matching.py, transitions.py, housekeeping.py
│  ├─ models/          # base.py (BaseSimulationModel)
│  └─ presets/         # foraging.py, exchange.py, market.py
├─ vmt_pygame/
│  ├─ app.py           # main loop, sim_dt control, pause/reset/speed
│  ├─ renderers.py     # grid/agents/overlays/HUD
│  └─ input.py         # hotkeys, preset picker
├─ scripts/            # run_pygame.py, export_run.py
├─ tests/              # engine + matcher + utility suites
└─ pyproject.toml
```

*(This adapts the earlier “directory structure” guidance to our Python-only desktop design.)*

---

## Milestones

* **M1 (Week 1)**: Engine skeleton + Pygame loop + Foraging preset end-to-end; CSV logging.
* **M2 (Week 2)**: Barter mode (integer bundles), acceptance tests, HUD deltas.
* **M3 (Week 3)**: Cash mode (cell order books), matching, price signals, telemetry.
* **M4 (Week 4)**: Presets polish, packaging (Win/macOS), teacher notes, example lesson scripts.

---

## Risks & Mitigations

* **Complexity creep** in matcher rules → start with strict cash-and-carry and short TTLs.
* **Performance** with many agents → NumPy arrays and optional Numba; render-only moving elements; cap per-cell order book size.
* **Pedagogical clarity** → default overlays (MRS hints), consistent color/legend semantics.

---

## Open Decision Points (to finalize before implementation)

1. **Barter heuristics (integer bundles):**

   * Max lots per tick; good-pair selection; candidate window size; tie-breaking rule.

2. **Order-posting rules (cash mode):**

   * Reservation price derivation (from MU/MRS), initial spread, decay/TTL policy, and `cash_tick_size`.

3. **Utility function defaults:**

   * **Which set ships by default** (Cobb-Douglas, CES, Leontief, Linear are must-haves; confirm **Stone–Geary** and **Quasi-linear** for v1).
   * **Multi-good MRS** beyond two goods for barter demos (priority/deferral).

4. **GUI exposure vs. presets:**

   * Which params are adjustable in-app (sim_dt, N, lot size, TTL, tick size, vision/interaction radii) vs. preset-only.

5. **Price visualization:**

   * Preferred default: per-cell last-trade “spark” + global moving average; confirm.

6. **Packaging targets:**

   * Win/macOS (v1); Linux later.

---

## Conclusion

This Python-only rewrite delivers a cohesive, performant, and extensible foundation for grid-based microeconomic simulations—expressing foraging, bilateral exchange, and market-clearing as **configurations of one engine**. The delta architecture gives you rigor (testing, replay) without sacrificing speed, while Pygame provides a straightforward, portable UI for classrooms and research demos.

---

### Notes on lineage and structure

* This draft **retains the high-level structure** (architecture → engine → phased modules → UX → robustness) from your earlier planning document while replacing the web stack with a desktop loop.  
* It **supersedes** the previously suggested Python+JS browser loop in *Revision.md* in favor of a single-language design aligned with your preferences. 

---

If this layout looks right, I’ll turn it into repository scaffolding (files + stubs), plus a short “teacher’s guide” outline for each preset.
