# Target Architecture Discussion

This document focuses on the **end-state architecture** for VMT, with three coexisting tracks (ABM, GT, Neo) orchestrated by a unified launcher.

---

## Core Architectural Principles

1. **ABM is foundational** — spatial, emergent, agent-based simulation
2. **GT is dual-purpose** — library consumed by ABM + standalone GUI for protocol inspection
3. **Neo is separate** — pure equilibrium solver with its own GUI
4. **Launcher orchestrates** — single entry point, comparison across tracks
5. **Emergence first** — market info derives from trade logs, not shortcuts
6. **Clean dependencies** — no upward imports, clear ownership

---

## High-Level Module Map

```
core_econ/          # Shared primitives (utilities, bundles, demand)
    ├── types       # GoodId, Bundle, PreferenceParams
    ├── utilities   # CES, Cobb-Douglas, utility functions
    └── demand      # Marshallian demand helpers

gt_protocols/       # Game theory library (consumed by ABM and GT GUI)
    ├── worldview   # Protocol interfaces
    ├── matching/   # Random, greedy, stable, three-pass
    └── bargaining/ # Split-diff, TIOLI, Nash, Rubinstein, K-S

abm/                # Agent-based model (foundation)
    ├── world       # Spatial grid, world state
    ├── agents      # SpatialAgent (extends core_econ primitives)
    ├── search/     # Spatial search protocols
    ├── effects     # Effect log, trade records
    ├── sim_loop    # Main simulation orchestrator
    └── info/       # Market detection, price aggregation, broadcasting

gt_gui/             # Game theory standalone GUI
    └── edgeworth   # Edgeworth box + protocol overlays

neo_engine/         # Neoclassical equilibrium solver
    ├── auctioneer  # Walrasian auctioneer
    ├── tatonnement # Convergence algorithms
    └── stability   # Stability analysis, Scarf demo

neo_gui/            # Neoclassical GUI
    └── dashboard   # Price paths, excess demand charts

launcher/           # Unified launcher
    ├── app         # Main window, track selection
    ├── managers    # Track process management
    └── comparison  # Cross-track metric comparison
```

---

## Key Architectural Questions

### Q1: What exactly goes in `core_econ`?

**Confirmed**:
- Types: `GoodId`, `Bundle`, `PreferenceParams`, `Endowment`
- Utilities: CES, linear, quadratic, Stone-Geary, translog + base interface
- Demand helpers: marshallian_demand, utility computation

**Unresolved**:
- **Agent class**: Does `core_econ` define a minimal `Agent` class (just prefs + endowment)?
  - **Option A**: Yes, minimal Agent in core_econ. ABM extends to SpatialAgent.
  - **Option B**: No Agent class; just primitives. ABM/GT/Neo construct their own.
  - **Leaning**: Option B (GT GUI just needs `(utility_fn, endowment)` tuples)

- **Demand computation**: Is marshallian_demand a function or a method?
  - `compute_demand(utility_fn, endowment, prices)` vs `agent.compute_demand(prices)`
  - **Leaning**: Function (more flexible, GT/Neo can use directly)

### Q2: How does ABM consume GT protocols?

**The WorldView boundary**:

ABM implements `WorldView` protocol, which GT protocols consume:

```python
class WorldView(Protocol):
    """Base tier - sufficient for all GT protocols"""
    def agent_inventory(self, agent_id: int) -> Bundle: ...
    def agent_utility(self, agent_id: int, bundle: Bundle) -> float: ...
    def feasible_trade(self, a_id: int, b_id: int, trade: dict) -> bool: ...
```

GT protocols call `matching_protocol.match(candidates, world_view)` and return pairs/effects.

**Unresolved**:
- **Spatial filtering**: If a matching protocol needs "agents within distance D", who does that?
  - **Option A**: ABM filters candidates before calling GT (GT stays pure)
  - **Option B**: Extend WorldView with spatial queries (couples GT to spatial concepts)
  - **Leaning**: Option A (ABM pre-filters, GT protocols stay reusable)

- **Market info access**: If a bargaining protocol wants to anchor to local prices, how?
  - **Option A**: ABM passes price signals as context in WorldView
  - **Option B**: Separate "market-informed wrapper" that calls base protocol + adjusts
  - **Option C**: WorldView has optional `market_signal()` method
  - **Open question**: Which feels least coupled?

### Q3: What does GT GUI actually need from the system?

**Confirmed**:
- Utility functions from `core_econ`
- Endowments (initial bundles)
- GT protocols from `gt_protocols`
- No spatial info, no ABM state

**Architecture implication**:
GT GUI constructs its own mini-world:
```python
# GT GUI creates a small-N scenario
agents = [
    (utility_fn=CES(...), endowment=Bundle(x=10, y=5)),
    (utility_fn=CES(...), endowment=Bundle(x=5, y=10)),
]

# GT GUI implements its own WorldView over this data
gt_world = GTWorldView(agents)

# GT GUI calls the same protocols as ABM
matching_result = stable_matching.match([0, 1], gt_world)
bargaining_result = nash_bargaining.negotiate((0, 1), gt_world)
```

**Unresolved**:
- **Does GT GUI emit Effects?** Or just visualize outcomes?
  - If it emits Effects, location field is meaningless
  - If it doesn't, how do we track "what happened" for display?
  - **Leaning**: GT GUI has its own lightweight result format, doesn't use ABM's Effect schema

### Q4: How does market information emerge in ABM?

**Confirmed**:
- Market info derives ONLY from effect log (trades that actually happened)
- No shortcuts, no global price calculations
- ABM's `info/` subsystem processes effects

**Process**:
1. ABM executes trades → appends to effect log
2. Info systems read effect log → detect market areas (spatial clustering)
3. Info systems aggregate prices within clusters → produce `PriceSignal` objects
4. Info systems optionally broadcast signals to nearby agents
5. Agents optionally use signals to inform future decisions

**Unresolved**:
- **When does info processing happen?** Every tick? Every N ticks? On-demand?
- **How do agents access price signals?** Do they query, or receive broadcasts?
  - **Option A**: Agents have `.price_memory` that info system writes to
  - **Option B**: Agents query world state for nearby signals
  - **Option C**: Hybrid (broadcast to radius, agents store in memory)

- **Market-informed bargaining**: How does it work?
  - **Option A**: Separate protocol that wraps base bargaining + adjusts using price signals
  - **Option B**: Base bargaining protocols check if agent has price beliefs, use if available
  - **Leaning**: Option A (wrapper pattern keeps base protocols pure)

### Q5: How does Neo engine fit in?

**Confirmed**:
- Neo is completely separate from ABM
- Neo uses `core_econ` utilities and endowments
- Neo has no spatial state, no effects, no mutation
- Neo outputs: `Equilibrium(prices, allocations, utilities, diagnostics)`

**Architecture**:
```python
# Launcher passes scenario to Neo
scenario = [
    (utility_fn=CES(...), endowment=Bundle(x=10, y=5)),
    (utility_fn=CES(...), endowment=Bundle(x=5, y=10)),
]

# Neo solver is pure function
equilibrium = walrasian_auctioneer(scenario)
convergence = tatonnement(scenario, initial_prices=...)
```

**Unresolved**:
- **How does comparison work?** Launcher needs to:
  - Extract allocation from ABM (sum of final bundles)
  - Extract allocation from Neo (equilibrium allocations)
  - Compare efficiency, price ratios, etc.
  - **Implication**: ABM needs a "summary stats" API for launcher

- **Can Neo use ABM's final allocation as input?** E.g., "Given these final bundles, how far from equilibrium?"
  - Useful for pedagogical comparison
  - **Needs**: ABM exports final state in a Neo-compatible format

### Q6: How does the launcher orchestrate everything?

**Confirmed**:
- Single window, three tiles (ABM, GT, Neo)
- Each track runs in its own process (ABM+pygame, GT+matplotlib, Neo+GUI)
- Comparison tool aggregates metrics

**Process flow**:
1. User selects track + scenario in launcher
2. Launcher spawns process for that track
3. Track runs, produces results
4. Launcher collects results (via files, pipes, or shared memory?)
5. Comparison tool displays side-by-side

**Unresolved**:
- **How do tracks report results?** 
  - **Option A**: Write to files (e.g., `results/abm_run_123.json`)
  - **Option B**: Pipe to launcher via stdout
  - **Option C**: Shared database (e.g., telemetry DB)
  - **Leaning**: Option C if lightweight, else Option A

- **Can launcher run multiple tracks simultaneously?** Or one at a time?
  - Simultaneous allows "run ABM + Neo in parallel, compare when done"
  - Sequential is simpler
  - **Probably**: Sequential for MVP, parallel later

---

## Dependency Flow (Target State)

```
                    ┌─────────────┐
                    │  launcher/  │
                    └─────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
  ┌──────────┐      ┌──────────┐     ┌───────────┐
  │ abm/     │      │ gt_gui/  │     │ neo_gui/  │
  └──────────┘      └──────────┘     └───────────┘
        │                 │                 │
        │                 │                 │
        └────────┬────────┴────────┬────────┘
                 │                 │
                 ▼                 ▼
         ┌──────────────┐   ┌──────────────┐
         │ gt_protocols/│   │ neo_engine/  │
         └──────────────┘   └──────────────┘
                 │                 │
                 └────────┬────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │  core_econ/  │
                  └──────────────┘
```

**Import rules**:
- `core_econ` imports nothing internal (stdlib only)
- `gt_protocols` imports `core_econ` only
- `neo_engine` imports `core_econ` only
- `abm` imports `core_econ` + `gt_protocols`
- `gt_gui` imports `core_econ` + `gt_protocols`
- `neo_gui` imports `core_econ` + `neo_engine`
- `launcher` imports all top-level modules

No circular dependencies. No upward imports.

---

## Unresolved Design Tensions

### Tension 1: WorldView purity vs. power

**Pure WorldView** (just inventory/utility/feasibility):
- Pros: GT protocols maximally reusable, testable in isolation
- Cons: ABM does more pre-filtering, some protocols can't express spatial/info constraints

**Extended WorldView** (spatial queries, market signals):
- Pros: GT protocols can be more sophisticated
- Cons: Couples GT to ABM concepts, makes GT GUI implementation harder

**Middle ground**: Tiered WorldView with base + optional extensions?
```python
class WorldView(Protocol):  # Base
    def agent_inventory(...) ...

class SpatialWorldView(WorldView):  # Extension
    def agent_position(...) ...
    def agents_within_radius(...) ...

class InformedWorldView(WorldView):  # Extension
    def market_signal(...) ...
```

Then GT protocols declare which tier they need. ABM can provide all tiers; GT GUI provides base only.

**Your concern**: Overengineering. Is tiered worth the complexity?

### Tension 2: Effect schema ownership

**ABM-owned** (Effect is in `abm/effects.py` with location field):
- Pros: ABM controls its own data structures
- Cons: GT GUI can't emit Effects if it wants to log for demo purposes

**Shared** (Effect is in `core_econ` or `gt_protocols`, optional location):
- Pros: GT GUI can also use it
- Cons: Messy optional fields, unclear ownership

**Alternative**: GT protocols return lightweight results, ABM wraps into Effects:
```python
# GT protocol returns
MatchResult = list[tuple[int, int]]
BargainResult = (agent_a_delta: Bundle, agent_b_delta: Bundle, success: bool)

# ABM wraps into Effect
effect = Effect(
    agents=[a_id, b_id],
    quantities=bargain_result.agent_a_delta,
    location=world.agent_position(a_id),
    protocol={"matching": "stable", "bargaining": "nash"},
    surplus=computed_surplus,
)
```

This keeps GT protocols lightweight and ABM in control of Effect schema.

### Tension 3: Market info timing and storage

**When processed**:
- Every tick (expensive but responsive)?
- Every N ticks (cheaper, but agents work with stale info)?
- On-demand when agent queries (lazy, but inconsistent)?

**Where stored**:
- In agent memory (`.price_beliefs: dict[GoodId, float]`)?
- In world state (`.price_signals: list[PriceSignal]`)?
- External info system that agents query?

**How accessed**:
- Push (info system writes to agent memory)?
- Pull (agents query world state)?
- Hybrid (broadcast within radius, agents store)?

This affects both ABM architecture and whether WorldView needs market info methods.

---

## Questions to Sharpen the Architecture

1. **Agent class**: Confirm no Agent class in `core_econ`, just primitives?

2. **WorldView tiers**: Is tiered WorldView worth it, or just keep base + ABM pre-filters?

3. **Effect ownership**: Should GT protocols return lightweight results, or full Effects?

4. **Market info timing**: Every tick, every N ticks, or on-demand?

5. **Market info storage**: Agent memory, world state, or external system?

6. **Launcher communication**: How do tracks report results back to launcher?

7. **Neo comparison**: Does ABM need a "summary stats API" for comparison tool?

---

## Next Step

Once these questions are answered, we'll have a clear target architecture. Then—and only then—should we think about how to get from current state to target state.

For now, let's focus on getting the end-state design right.

