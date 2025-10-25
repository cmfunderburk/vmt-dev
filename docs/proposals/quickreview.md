Love this direction. Let’s make the “protocol modularization” more formal so it scales, stays deterministic, and doesn’t turn into a thicket of special-cases.

Below is a crisp decomposition of the 7-phase loop into protocol seams, the contracts each seam must satisfy, how they compose, and what you need to log and test so the whole thing remains scientifically respectable.

# 1) Break the 7 phases into protocol seams

Think “pure inputs → explicit effects,” with the simulation core as the only code that mutates world state. Every protocol gets a frozen view in, and returns a list of **Effects** (declarative intents) out.

**Phases & protocol hooks**

1. Perception

   * Core task: build a deterministic `WorldView` snapshot per agent (neighbors, resources, quotes, tick, mode, etc.).
   * No protocol here; this is a core service feeding everyone the same frozen reality.

2. Decision (split into two modular hooks)

   * **SearchProtocol** (optional): chooses *targets* (partner/resource/position).
   * **MatchingProtocol** (optional): given candidates/preferences, emits *Pair* effects.
   * Notes: You can run Search first to populate ranked lists, then Matching to lock pairs.

3. Movement

   * **MovementPolicy** (optional): given target, emit *Move* effects. Default preserves current deterministic tie-breaking.

4. Trade

   * **BargainingProtocol** (swappable): given a matched pair in range, emit zero or more *Trade* effects (and possibly a *PairRelease* on failure). Supports single-tick and multi-tick bargaining.

5. Foraging

   * **ForagingPolicy** (optional): emit *Harvest* effects (respecting single-harvester rules if enabled).

6. Resource Regeneration

   * Core task (purely mechanical, keep it in the kernel unless you want ecological plugins later).

7. Housekeeping

   * **HousekeepingPolicy** (optional): integrity checks, quote refresh hints, pair validation, etc., emitting *RefreshQuotes*, *FixPair*, *Cooldown* effects.

# 2) Canonical data contracts

Keep these boringly strict. Determinism loves boring.

**WorldView (read-only)**

* `tick`, `mode`, `exchange_regime`
* Agent local snapshot: id, pos, inventory {A,B,M}, utility type, quotes (money-aware), pairing/cooldown flags
* Local neighborhood: visible agents/resources within policy-defined “visibility” (SearchProtocol may redefine this)
* Scenario constants (for epsilon, β, movement budgets, dA_max, etc.)
* Randomness source: core hands out a **seeded RNG facade** to protocols; protocols may request substreams by name so runs are bit-stable.

**Effects (write-intents only)**

* `SetTarget(agent_id, {pos|agent_id|resource_id})`
* `ClaimResource(agent_id, pos)` / `ReleaseClaim(pos)`
* `Pair(a_id, b_id, reason)` / `Unpair(a_id, b_id, reason)`
* `Move(agent_id, dx, dy)`
* `Trade(buyer_id, seller_id, pair_type, dA, dB, dM, price, meta)`
* `Harvest(agent_id, pos, amount)`
* `RefreshQuotes(agent_id)` / `SetCooldown(a,b,ticks)`
* `InternalStateUpdate(protocol_name, agent_id, key, value)` (for multi-tick bargaining/search memory)

The **simulation core** is the only place that:

* Validates effects (feasibility, conflicts, invariants)
* Applies them in a **fixed, documented order**
* Logs them

# 3) Interface sketches (tight, but future-proof)

```python
class ProtocolBase:
    name: str
    version: str  # semver for telemetry and compatibility

class SearchProtocol(ProtocolBase):
    def build_preferences(self, agent_id: int, view: WorldView) -> list[Preference]:
        """Return a ranked list of candidate targets with scores (e.g., discounted surplus, distance)."""
    def choose_target(self, agent_id: int, view: WorldView) -> list[Effect]:
        """Usually a SetTarget and optional ClaimResource."""

class MatchingProtocol(ProtocolBase):
    def find_pairs(self, agent_ids: list[int], view: WorldView) -> list[Effect]:
        """Return Pair() effects. May consult per-agent preferences recorded by Search."""

class BargainingProtocol(ProtocolBase):
    def step(self, pair: tuple[int,int], view: WorldView) -> list[Effect]:
        """Single-tick step; emit Trade() and/or Unpair(). May emit InternalStateUpdate for multi-tick flows."""
    def on_unpaired(self, pair, reason, view) -> None:
        """Optional cleanup hook."""

class MovementPolicy(ProtocolBase):
    def plan(self, agent_id: int, view: WorldView) -> list[Effect]:
        """Emit Move() respecting budget and tie-breaking rules."""

class ForagingPolicy(ProtocolBase):
    def harvest(self, agent_id: int, view: WorldView) -> list[Effect]:
        """Emit Harvest() if allowed."""

class HousekeepingPolicy(ProtocolBase):
    def tidy(self, view: WorldView) -> list[Effect]:
        """Emit RefreshQuotes, Pair integrity fixes, cooldown updates, etc."""
```

Notes:

* Protocols never mutate state directly; they only return Effects.
* Multi-tick bargaining/search keep state via `InternalStateUpdate` keyed by `(protocol, agent_id)`.

# 4) Determinism rules (non-negotiable)

* **Sorted iteration** everywhere: agent IDs ascending, then tie-breakers documented (e.g., lower id “wins” claims).
* **Effect application order** per phase: e.g., in Trade phase: `Unpair` → `Trade` → `Cooldown` → `RefreshQuotes`.
* **RNG discipline**: the core hands out per-protocol RNG streams by agent/pair ID and tick. If two protocols both need randomness, they must draw from their distinct named streams.
* **No incidental shared state**: protocols get snapshots and can only write via Effects.

# 5) Complexity budgets (keep it fast)

* Search: O(k) per agent where k = visible candidates; visibility radius or sampler belongs to the SearchProtocol.
* Matching: O(n)–O(n log n) typical; document worst-case if protocol tries global sorts.
* Bargaining: per-pair step must be O(dA_max × n_prices) or better; multi-tick algorithms must yield quickly and store continuation state.
* Movement/Foraging: keep O(1)–O(log n) per agent.

Publish these budgets in docs so contributors don’t sneak in O(n²) surprises.

# 6) Telemetry schema additions

Layered, so core analytics don’t explode:

* `protocol_runs(run_id, tick, simulation_type, search_name@ver, matching_name@ver, bargaining_name@ver, ...)`
* `protocol_events(run_id, tick, protocol, kind, agent_id?, pair? json, payload json)`
* `bargaining_states(run_id, tick, pair, state_key, state_val)` when debug enabled
* Extend existing `pairings`, `preferences`, `trade_attempts`, `trades` with `protocol_version` columns

This lets you compare apples to apples across protocols and reproduce results from a single screenshot of settings.

# 7) Scenario config (clean and boring)

```yaml
protocols:
  search:      { name: "distance_discounted", version: "1.x", params: { beta: 0.95, vision_policy: "circle" } }
  matching:    { name: "three_pass_pairing",  version: "1.x" }
  bargaining:  { name: "compensating_block",  version: "2.x", params: { dA_max: 5, price_grid: "min_mid_max" } }
movement_policy: { name: "deterministic_grid_v1" }
foraging_policy: { name: "single_harvester_v1", params: { enforce: true } }
```

Defaults should reproduce current behavior exactly.

# 8) Examples of swappable bargaining/search

**Bargaining**

* *Current*: “first acceptable trade” via compensating blocks (integer rounding, strict ΔU > 0).
* *Rubinstein alternating offers* (multi-tick): protocol stores `(offer_price, proposer, round, deadline)` as internal state; each tick emits accept/counter or unpair on deadline; discounting captured in utilities or a separate cost-of-delay term.
* *Nash/Kalai–Smorodinsky* (single-tick): compute cooperative solution within feasible set, emit one Trade; needs a fallback if set is empty (then Unpair+Cooldown).
* *Take-it-or-leave-it* (single-tick): seller’s monopolistic offer subject to buyer’s acceptance region; easy to run and compare.

**Search**

* *Distance-discounted surplus* (current default).
* *Memory-based search*: agents maintain a local price map; revisit profitable regions with some exploration rate ε.
* *Frontier sampling*: sample a subset of candidates stochastically from a larger radius; reduces O(k).
* *Information-limited search*: cap candidate list length to simulate attention constraints.

# 9) Conflict resolution & safety

* If two Effects conflict (e.g., two `Pair()`s claim the same agent), the core resolves by rule: lowest `(min_id, max_id)` wins; losers receive `Unpair(reason="conflict")`.
* Timeouts: multi-tick protocols must emit `Unpair(reason="timeout")` by a bounded number of ticks.
* Feasibility checks live in the core: trades that violate inventory non-negativity or regime rules are dropped and a `protocol_events` row is logged.

# 10) Test strategy (the joyless but necessary bit)

**Golden reproduction**

* For each protocol set, run canonical scenarios and assert: same trades, same inventories, same DB checksum for fixed seed.

**Cross-protocol invariants**

* If a bargaining protocol claims to implement Nash, verify symmetry and Pareto efficiency in stylized 2-agent cases.
* Matching protocols: verify no agent appears in two active pairs; verify claimed stability properties where applicable (e.g., DA).

**Property-based tests**

* Utilities monotone and well-behaved; reservation bounds finite under zero-inventory guard.
* Bargaining never yields ΔU ≤ 0; price rounding consistent.

**Performance**

* Upper bounds on time per tick with N=400, k~neighbors, documented budgets.

# 11) Migration plan (sane, reversible)

1. Ship **default protocol adapters** that exactly mirror current behavior:

   * `distance_discounted_search`
   * `three_pass_pairing`
   * `compensating_block_bargaining`
   * `deterministic_grid_movement`
   * `single_harvester_foraging`
     These keep `simulation_type: full` identical to today.

2. Add one alternative per surface:

   * `random_walk_search`
   * `greedy_surplus_matching`
   * `take_it_or_leave_it_bargaining`

3. Wire scenario flags + GUI dropdown. Log protocol names+versions each run.

4. Only then refactor internal engine code to depend on the protocol interfaces, removing old inlined logic.

# 12) Tiny “do next” list (atomic and safe)

* Create `protocols/` with ABCs and a minimal **Effect** type + validator.
* Implement default adapters that call the existing code paths; return Effects identical to current outcomes.
* Add `protocol_runs` table and log names/versions.
* Add `random_walk_search` + simple scenario to prove isolation works.
* Add `take_it_or_leave_it_bargaining` (single-tick, very small) and a 2-agent money scenario to compare prices with current method.

This gives you a plug-point architecture without breaking anything, a playground for new bargaining/search ideas, and a clean scientific trail (telemetry + determinism) for comparing protocols. When you’re ready, we can sketch the exact code scaffolding (files, stubs, and first tests) to drop straight into your repo.
