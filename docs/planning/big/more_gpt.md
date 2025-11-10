You have three surfaces and one foundation:

* Foundation: ABM.
* Library + GUI: Game-theory protocols used by ABM, with a standalone GT GUI for inspection.
* Separate engine + GUI: Neoclassical benchmark.
* One launcher that orchestrates all.     

Below is a concrete, implementation-ready plan.

# 1) Ownership and import rules

* ABM owns: spatial search, world state, effects, emergent info. ABM may **use** GT protocols. ABM never imports Neo. 
* GT owns: matching, bargaining, small-N exchange primitives, Edgeworth Box GUI. GT exposes a pure protocol API consumed by ABM. 
* Neo owns: equilibrium solvers, tatonnement, stability analysis, Neo GUI. It is a separate engine. No mutation of ABM state. 
* Launcher owns: track selection, process management, scenario config, comparison view. 

Dependency direction:

```
core_econ  →  gt_protocols        →  abm (uses gt)
core_econ  →  neo_engine (separate)
tracks (abm | gt_gui | neo_gui) → launcher
```

# 2) Shared primitives (core_econ)

* Types: `GoodId`, `Bundle`, `UtilityFn`, `Endowment`, `PreferenceParams`.
* Services: `marshallian_demand`, `compute_utility`, `price_ratio` helpers.
* Constraint: no references to spatial state or GUIs. GT and Neo both consume this.  

# 3) GT protocol API (library first, GUI second)

**Interfaces** used by ABM and by the GT GUI:

```python
class WorldView(Protocol):
    def agent_inventory(self, agent_id) -> Bundle: ...
    def agent_utility(self, agent_id, bundle: Bundle) -> float: ...
    def feasible_trade(self, a_id, b_id, trade: dict) -> bool: ...

class MatchingProtocol(Protocol):
    name: str
    def match(self, candidates: list[int], world: WorldView) -> list[tuple[int,int]]: ...

class BargainingProtocol(Protocol):
    name: str
    def negotiate(self, pair: tuple[int,int], world: WorldView) -> list["Effect"]: ...
```

* ABM passes a lightweight `WorldView` over ABM state. Protocols return **Effects** only. No protocol mutates state directly. ABM applies effects. 
* Provide stock protocols: random pairing, greedy surplus, stable matching; split-difference, TIOLI, Nash, Rubinstein, Kalai-Smorodinsky. GT GUI calls the same objects. 

**GT GUI**

* Edgeworth Box with toggles: contract curve, CE point, protocol outcome overlays. The GUI runs on small-N agents built from `core_econ` agents. 

# 4) ABM integration of GT protocols

* ABM loop uses `search → matching (GT) → bargaining (GT) → effects`.
* ABM “effect log” records trades for Stage-5 information systems. GT never reads ABM internals beyond `WorldView`. 

**Effect schema (append-only):**

```json
{
  "tick": 123,
  "agents": [17, 42],
  "quantities": {"good_a": -3, "good_b": +2}, 
  "location": [x, y],
  "protocol": {"matching":"stable", "bargaining":"nash"},
  "surplus": 1.734
}
```

This powers market-area detection, price aggregation, broadcasting, and agent memory. 

# 5) Market information is emergent and optional in protocols

* Information systems consume the **effect log** to detect market areas and infer price signals. No external calculation shortcuts. 
* Provide a **market-informed** bargaining wrapper that anchors offers to local price signals when available; otherwise fall back to a baseline protocol. ABM selects this like any other protocol. 

# 6) Neo engine is separate

* Components: Walrasian auctioneer, tatonnement variants, stability analyzer, Scarf demonstration. Pure functions over `core_econ` agents and endowments. 
* Outputs: equilibrium prices, allocations, utilities, convergence diagnostics.
* **Neo GUI**: displays price paths, excess-demand charts, stability flags; parameter sliders for utility parameters and endowments. 

# 7) Launcher integration (single front door)

* Three tiles: ABM Simulation, Game Theory Analysis, Neoclassical Models.
* Each tile opens track-specific config panes; `LaunchManager` starts each track, often in its own process; `ComparisonTool` records metrics for side-by-side tables and plots. 

**Minimum comparison metrics across tracks:**

* Allocation efficiency relative to Pareto frontier or CE.
* Trade volume and match rate (ABM only).
* Price ratio vs Neo equilibrium price ratio.
* Convergence flags and iterations (Neo). 

# 8) File layout (proposed)

```
src/
  core_econ/
    __init__.py
    utilities.py        # utility fns, demand, preferences
    types.py            # GoodId, Bundle, etc.
  gt_protocols/
    __init__.py
    matching/*.py       # random, greedy, stable
    bargaining/*.py     # split, TIOLI, nash, rubinstein, ks
    worldview.py        # Protocol types
  abm/
    world.py
    search/*.py
    effects.py
    sim_loop.py
    info/               # detection, price_agg, broadcasting, memory
  gt_gui/
    edgeworth.py        # Edgeworth visualizer + overlays
  neo_engine/
    auctioneer.py
    tatonnement.py
    stability.py
    scarf.py
  neo_gui/
    dashboard.py        # price paths, diagnostics
  launcher/
    app.py
    managers.py
    comparison.py
```

Matches your Stage designs and keeps GT library separable and reusable.    

# 9) Data contracts

**WorldView contract (ABM → GT):**

* Read-only methods for inventories, utilities, and feasibility checks.
* No state mutation; GT returns effects only. 

**Effect log contract (ABM → Info systems → ABM/GT):**

* Immutable records per tick, with location, quantities, protocol labels, surplus.
* Info systems output `PriceSignal` objects with location, price_ratio, confidence, n, timestamp. 

**Neo contract (Launcher/GUI ↔ Neo engine):**

* Inputs: list of `core_econ.Agent` with `utility_params`, endowments.
* Outputs: `Equilibrium(prices, allocations, utilities)`, plus diagnostics. 

# 10) Testing plan

Unit:

* GT protocols on canned 2×2 economies; compare Nash/KS/Rubinstein outputs. 
* Info pipeline: deterministic clustering seed; price aggregation variance thresholds. 
* Neo: Walras Law checks; tatonnement convergence where applicable; Scarf non-convergence demonstration. 

Integration:

* ABM uses GT protocols via `WorldView`; assert effect counts and conservation.
* Launcher starts each track; `ComparisonTool` logs metrics.

Golden runs:

* Fixed seeds for ABM scenarios; snapshot metrics; alert on drift.

# 11) Pedagogical flows

ABM-first:

1. Run ABM with simple GT protocols. Observe emergent trades and price signals. 
2. Open GT GUI for the same preferences/endowments. Inspect contract curve, CE, and protocol outcomes in isolation. 
3. Open Neo GUI with same inputs. Compare equilibrium allocations and price ratios, note coordination assumptions. 
4. Use launcher comparison to place all three outputs side-by-side. 

# 12) Incremental delivery (low risk)

Phase A — Library seams first

* Extract `core_econ`.
* Stand up `gt_protocols` with `WorldView` and adapters.
* Replace ABM’s internal matching/bargaining with GT calls. 

Phase B — GT GUI

* Edgeworth Box with protocol overlays and CE toggle.
* Import same `gt_protocols` used in ABM. 

Phase C — Market information

* Effect log, market detection, price aggregation, broadcasting, agent memory, and optional market-informed bargaining wrapper. 

Phase D — Launcher + Comparison

* Track tiles, process management, results table, minimal charts. 

Phase E — Neoclassical engine + GUI

* Auctioneer, tatonnement, stability, Scarf; GUI visualizations; hook into launcher and comparison. 

# 13) Risks and mitigations

* Coupling creep: enforce protocol boundaries and read-only `WorldView`.
* Info leakage: keep market info as a consumer of effect logs only. 
* GUI drift: tie both GUIs to the same `core_econ` types.
* Non-determinism: seed ABM, threshold comparisons for metrics.

# 14) Immediate next tasks (actionable)

1. Define `core_econ.types` and `core_econ.utilities` with tests.
2. Implement `gt_protocols.worldview` and port one matching + one bargaining protocol. Wire ABM to them. 
3. Add ABM effect log and write the first info step (price extraction from trades). 
4. Ship GT Edgeworth GUI using the same agents/utilities. 
5. Scaffold launcher pages and basic comparison table. 

This keeps ABM as the foundation, uses GT twice (as library and as GUI), and keeps Neo separate yet comparable.
