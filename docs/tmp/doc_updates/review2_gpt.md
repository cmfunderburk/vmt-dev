Fantastic—this is exactly the right moment to stop, breathe, and make the docs catch up to the code and to your newer modeling insights. Below is a concrete, soup-to-nuts plan you can execute now, plus a clean way to carve the repo so “pairing” (matching/bargaining) can evolve beside “full” scenarios without stepping on toes.

I’ve verified the repo layout and current README language so this plan aligns with what’s actually there (e.g., the docs hub exists, versioning policy uses timestamped labels, quick-start paths, and current top-level folders like `docs/`, `scenarios/`, `src/`, `tests/`) ([GitHub][1]).

# Phase 0 — One-hour inventory & freeze

1. **Create a working branch**: `git checkout -b docs-refresh-2025-10-20-<hhmm>`.
2. **Snapshot the current “truths”**: copy the rendered contents of:

   * `README.md` sections: “Documentation,” “Versioning policy,” “Quick start.” Save to `docs/_audit/README-snapshot-2025-10-20.md`. ([GitHub][1])
   * A directory listing of top-level folders and files to `docs/_audit/tree-2025-10-20.txt`. (Use `git ls-tree -r --name-only HEAD | sort`.)
3. **Temporary freeze**: avoid changes to `main` until Phase 2 merges.

# Phase 1 — Documentation map & step-by-step update plan

Goal: produce a crisp “what lives where” map and a to-do ledger that ties every doc to a line-item change.

Create/refresh these files:

* `docs/README.md` (hub index):

  * Add a **Docs Map** with four pillars and links:

    1. **Project Overview** (onboarding & goals)
    2. **Technical Manual** (engine, modules, data flows)
    3. **Strategic Roadmap** (milestones & detours)
    4. **Type System & Data Contracts** (schemas, message/event contracts)
  * Keep the **timestamp versioning** guidance from root README, and make the hub the place that repeats/owns it so contributors don’t guess. ([GitHub][1])
* `docs/PLAN.docpass.md` (this is the driver checklist for the pass):

  * Table with columns: *Doc*, *Current Status*, *Required Updates*, *Owner*, *PR Link*, *Done?*
* `docs/overview/PROJECT_OVERVIEW.md` (rewrite last): short, non-technical “what this is, why it exists,” pointing to Quick Start (which currently lives in root README and works—don’t duplicate, just link). ([GitHub][1])
* `docs/tech/TECHNICAL_MANUAL.md` (core):

  * Sections: Engine loop, Entities (Agents, World, Resources), Event system, Scheduling, I/O, Telemetry.
  * Add a **“Scenario Abstraction”** section that explains how different scenario families (full, bargaining, matching) plug into the same runtime (see Phase 3 refactor).
* `docs/roadmap/ROADMAP.md`: owns milestones and detours, with timestamped labels per your versioning policy. ([GitHub][1])
* `docs/types/TYPESPEC.md`: single source of truth for types and data contracts (IDs, state records, action messages, event payloads). This anchors your long-term language-agnostic ambitions.

# Phase 2 — Scenarios folder carve-up (non-breaking, additive)

We keep current behavior working while creating homes for pairing experiments. Implement exactly this:

```
scenarios/
  full/           # current forage + bilateral exchange + future market behavior
    <move existing scenario yamls/scripts here, preserving names>
  bargaining/     # Nash, alternating offers, Rubinstein-style rounds, etc.
    README.md
    examples/
      two_agent_rubinstein.yaml
      n_agent_coalitional_stub.yaml
  matching/       # search/matching models: random search, directed search, Gale-Shapley variants
    README.md
    examples/
      random_search_baseline.yaml
      directed_search_capacity.yaml
```

*Steps:*

1. Move/rename existing scenario files into `scenarios/full/` while maintaining working CLI paths referenced in Quick Start. Update the example CLI invocation in root README to use the new path (e.g., `python main.py scenarios/full/three_agent_barter.yaml 42`). ([GitHub][1])
2. Add minimal `README.md` to `bargaining/` and `matching/` explaining each family’s assumptions, typical parameters, and references.
3. In `docs/tech/TECHNICAL_MANUAL.md`, document how the engine discovers & loads scenarios from these subtrees.

# Phase 3 — Minimal src/ scaffolding to support separation of concerns

You don’t need a large refactor to start—just clean seams. Target is a stable “Scenario API” + thin adaptation layer.

**Add/confirm modules (names illustrative):**

```
src/
  core/
    engine.py            # main loop, ticks, scheduling
    world.py             # grid/world state
    agents.py            # Agent baseclass + capabilities
    events.py            # event definitions, bus, subscriptions
    io.py                # scenario file loader, config parsing
  features/
    forage.py            # resource dynamics
    exchange.py          # existing bilateral trade logic
    bargaining/          # new namespace for bargaining mechanisms
      protocols.py       # interfaces + base protocol types
      alternating_offers.py
      nash_division.py
    matching/            # new namespace for search/matching
      processes.py       # interfaces + base matching process types
      random_search.py
      directed_search.py
  scenarios/
    loader.py            # map scenario files -> configured runtime
  types/
    contracts.py         # python dataclasses / pydantic models mirroring docs/types
```

**Key ideas to implement now (small, high-leverage):**

* **Scenario Adapter interface**

  ```python
  class ScenarioAdapter(Protocol):
      def apply(self, world, agents, rng) -> None: ...
  ```

  * `full` adapter composes `forage + exchange (+ future market)`.
  * `bargaining` adapter registers a bargaining protocol and hooks it into agent decisions.
  * `matching` adapter registers a search/matching process that determines meeting pairs/markets.

* **Event Bus + Phase Hooks**
  Define events like `BeforeTick`, `AfterTick`, `BeforeMatch`, `AfterMatch`, `BeforeBargain`, `AfterBargain`. Feature packs subscribe without knowing each other. This reduces cross-module coupling and lets you swap pairing mechanisms without surgery.

* **Types round-trip**
  Mirror `docs/types/TYPESPEC.md` in `src/types/contracts.py`. During this pass, it’s fine to start with `TypedDict` / `dataclass` and evolve.

Document each of the above in `docs/tech/TECHNICAL_MANUAL.md` with a one-page diagram (ASCII is fine to start).

# Phase 4 — Update the Roadmap with the “pairing detour”

Your instinct is solid: pairing is the beating heart of trade. Let’s make it an explicit milestone track so money/markets resume on firmer ground.

**Proposed roadmap shape (timestamp each item):**

1. **Docs Refresh (this pass)** — *Done when:* hub map exists; TYPESPEC first cut; TECH MANUAL updated; scenarios split and load.
2. **Pairing Track (Detour):**

   * **Matching v0**: random search baseline; parameters: meeting rate λ, neighborhood radius, capacity constraints; outputs: pair logs.
   * **Bargaining v0**: alternating-offers protocol with finite horizon/discounting; outputs: accepted offers, delay stats.
   * **Telemetry & Reproducibility**: scenario-level seeds + JSONL event logs; quick plots in `scripts/`.
   * **Comparative Dash**: run grids comparing welfare, agreement time, and failure rates across pairing regimes.
3. **Rejoin Money/Market**: integrate prices/market-clearing over interchangeable pairing backends; show how posted prices vs bargaining interact with matching congestion.
4. **“Full” Showcase**: scenarios in `scenarios/full/` orchestrate forage + pairing + money; toggles allow ablations.

Put this as `docs/roadmap/ROADMAP.md` and link it from both the repo `README.md` and the docs hub. Keep using timestamp labels instead of semantic versions, as your README already directs. ([GitHub][1])

# Phase 5 — Acceptance checklist (merge gate)

Before merging the docs pass, confirm:

* `README.md` quick-start uses a real `scenarios/full/...yaml` path and runs. ([GitHub][1])
* `docs/README.md` contains the Docs Map and links resolve.
* `docs/types/TYPESPEC.md` covers: IDs, Agent state, World state, Resource records, Meeting/Pair events, Bargain offer/accept events, RNG/seed policy.
* `src/scenarios/loader.py` can load any of the three families.
* `tests/` contains at least:

  * `test_scenarios_discovery.py` (finds examples in all three families)
  * `test_matching_random_baseline.py` (sanity: expected meetings per tick given λ)
  * `test_bargaining_alternating_offers.py` (sanity: with δ close to 1 and symmetric surplus, near-equal split)

# Concrete to-do ledger (copy straight into `docs/PLAN.docpass.md`)

* Root `README.md`: update example CLI path to `scenarios/full/...` and add a one-sentence pointer to pairing families. ([GitHub][1])
* `docs/README.md`: add Docs Map + link to Roadmap + reiterate timestamp policy. ([GitHub][1])
* `docs/tech/TECHNICAL_MANUAL.md`: add **Scenario Abstraction**, **Event Bus**, **Hooks**, **Scenario Adapter** notes.
* `docs/roadmap/ROADMAP.md`: add “Pairing detour” milestones and deliverables.
* `docs/types/TYPESPEC.md`: first pass on contracts.
* `scenarios/`: create `full/`, `bargaining/`, `matching/` and move/seed examples accordingly.
* `src/`: add minimal `features/bargaining/`, `features/matching/`, and `scenarios/loader.py`.
* `tests/`: add three smoke tests above.

# Naming & API sketches (to keep you unblocked)

**Matching interface**

```python
class Matcher(Protocol):
    def initialize(self, world, agents, rng): ...
    def step(self, world, agents, rng) -> list[tuple[int, int]]:
        """Return list of agent-id pairs to attempt bargaining/trade this tick."""
```

**Bargaining interface**

```python
class BargainingProtocol(Protocol):
    def negotiate(self, a, b, context, rng) -> dict:
        """Return {'agreement': bool, 'terms': {...}, 'rounds': int}"""
```

**Scenario adapter composition**

```python
class FullScenario(ScenarioAdapter):
    def apply(self, world, agents, rng):
        # compose features
        enable_forage(world)
        set_matcher(RandomSearch(lambda_rate=0.2))
        set_bargaining(AlternatingOffers(delta_a=0.95, delta_b=0.95, T=10))
```

# Why this detour helps the money track

* You’ll isolate *meeting technology* (matching) from *surplus division* (bargaining) from *price formation/market clearing*. This prevents “pairing glue” from leaking into price logic later.
* You’ll also generate data to calibrate search frictions (λ, capacity, network radius) and bargaining power (discount factors), making later market experiments more interpretable.

---

If you want, I can draft the initial file stubs (the three new READMEs, the TECHNICAL_MANUAL sections, and a first `TYPESPEC.md` skeleton) next so you can paste them straight in and commit.

[1]: https://github.com/cmfunderburk/vmt-dev "GitHub - cmfunderburk/vmt-dev"
