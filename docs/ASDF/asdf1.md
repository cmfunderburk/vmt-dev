I'll scan the codebase to verify the protocol architecture is present (registry, base classes, and protocol directories) so the next-step plan can be grounded in what's actually implemented. Then I'll outline the minimal implementation steps for Phase 2a with file-level targets.

[5 tools called]

I scanned the protocol package and confirmed the base classes, registry, and legacy implementations are present. I'll open the key files to see exact method signatures and how protocols are wired into the simulation and scenarios, then propose a concise Phase 2a implementation plan with file targets.

[8 tools called]

I'll open the decision and trading systems to confirm how protocols are invoked and what effects are expected, so the implementation plan aligns with current orchestration.

[2 tools called]

I'll open the context builders to see if there's an RNG or deterministic tie-breaking we can use for random protocols.

[1 tool called]

Let me quickly open the CLI and launcher entry points to see how simulations are created so I can suggest how to select protocols (via code, CLI, or scenario fields).

[3 tools called]

I verified the protocol architecture and where protocols are invoked in decision and trade phases. Below is a tight next-steps plan and minimal code stubs to get Phase 2a baselines in cleanly.

### What the code already provides (relevant anchors)
- Protocol ABCs and effects:
```294:342:src/vmt_engine/protocols/base.py
class SearchProtocol(ProtocolBase):
    """
    Protocol for agent search and target selection.
    
    Search protocols determine:
    - Which opportunities agents perceive
    - How agents rank potential targets
    - Which target an agent commits to
    
    Examples:
    - Distance-discounted search (legacy)
    - Random walk exploration
    - Memory-based search
    """
    
    @abstractmethod
    def build_preferences(
        self, world: "WorldView"
    ) -> list[tuple[Target, float, dict[str, Any]]]:
        """
        Build ranked list of targets with scores.
        ...
        """
        pass
    
    @abstractmethod
    def select_target(self, world: "WorldView") -> list[Effect]:
        """
        Select target and emit effects.
        ...
        """
        pass
```

```345:366:src/vmt_engine/protocols/base.py
class MatchingProtocol(ProtocolBase):
    """
    Protocol for agent pairing.
    ...
    """
    
    @abstractmethod
    def find_matches(
        self,
        preferences: dict[int, list[tuple[Target, float, dict[str, Any]]]],
        world: "WorldView",
    ) -> list[Effect]:
        """
        Establish pairings from agent preferences.
        ...
        """
        pass
```

```400:429:src/vmt_engine/protocols/base.py
class BargainingProtocol(ProtocolBase):
    """
    Protocol for trade negotiation.
    ...
    """
    
    @abstractmethod
    def negotiate(
        self, pair: tuple[int, int], world: "WorldView"
    ) -> list[Effect]:
        """
        One negotiation step (may be single-tick or multi-tick).
        ...
        """
        pass
    
    def on_timeout(self, pair: tuple[int, int], world: "WorldView") -> list[Effect]:
        """
        Called when negotiation exceeds max ticks.
        ...
        """
        return [Unpair(*pair, reason="timeout", protocol_name=self.name, tick=world.tick)]
```

- Where protocols are called in the engine:
```96:104:src/vmt_engine/systems/decision.py
            # Build WorldView for this agent
            world = build_world_view_for_agent(agent, sim)
            
            # Call search protocol
            prefs = self.search_protocol.build_preferences(world)
            effects = self.search_protocol.select_target(world)
            
            # Apply search effects immediately
            self._apply_search_effects(agent, effects, sim)
```

```115:122:src/vmt_engine/systems/decision.py
        # Build ProtocolContext with global state
        context = build_protocol_context(sim)
        
        # Call matching protocol
        pairing_effects = self.matching_protocol.find_matches(preferences, context)
        
        # Apply pairing effects
        self._apply_pairing_effects(pairing_effects, sim)
```

```114:121:src/vmt_engine/systems/trading.py
        # Build WorldView for trade negotiation
        world = build_trade_world_view(agent_a, agent_b, sim)
        
        # Call bargaining protocol
        effects = self.bargaining_protocol.negotiate((agent_a.id, agent_b.id), world)
        
        # Apply effects
        for effect in effects:
            if isinstance(effect, Trade):
                self._apply_trade_effect(effect, sim)
            elif isinstance(effect, Unpair):
                self._apply_unpair_effect(effect, sim)
```

### Fit with your documents
- SESSION_STATE.md confirms Phase 1 merged and Phase 2a targets: Random Walk Search, Random Matching, Split-the-Difference Bargaining.
- vision_and_architecture.md frames these as quick baselines to enable institutional comparisons.

### Logical next steps (Phase 2a, 8–10 hours)
- Random Walk Search
  - Deterministic pseudo-random movement using a tick/position/id hash (no RNG injection required).
  - Emit one SetTarget per agent within grid bounds; do not claim resources.
- Random Matching
  - Pair unpaired agents by a deterministic pseudo-random ordering based on tick and positions; ignore preferences.
  - Emit Pair effects with a clear reason tag (e.g., "random_matching").
- Split-the-Difference Bargaining
  - For allowed pair types under current regime, use midpoint price: p = (ask + bid)/2.
  - For each direction, scan dA (or dB) to find the first mutually beneficial discrete block at that fixed midpoint; emit Trade or Unpair.
  - Keep integer invariants and use existing utility checks; tie-breaking order can be regime-aware.

Recommended tiny plumbing (safe/minimal):
- Add grid size into WorldView params to keep SetTarget in-bounds.
- Optionally add CLI flags to choose protocols (avoid schema changes for now).

### Minimal edits to enable Phase 2a ergonomics
- Add grid size to WorldView params for safe target selection:
```python
# In src/vmt_engine/protocols/context_builders.py (inside params dict in build_world_view_for_agent)
"grid_size": sim.config.N,
```

- Optional: CLI flags to select protocols without schema changes:
```python
# In main.py argparse
parser.add_argument("--search-proto", default="legacy", choices=["legacy","random_walk"])
parser.add_argument("--matching-proto", default="legacy", choices=["legacy","random"])
parser.add_argument("--bargaining-proto", default="legacy", choices=["legacy","split_diff"])

# After loading scenario/seed:
from vmt_engine.protocols.registry import ProtocolRegistry
def make_proto(kind: str, name: str):
    if name == "legacy":
        return None
    mapping = {
        ("search","random_walk"): ("random_walk_search", "2025.10.27"),
        ("matching","random"): ("random_matching", "2025.10.27"),
        ("bargaining","split_diff"): ("split_difference", "2025.10.27"),
    }
    pname, ver = mapping[(kind, name)]
    return ProtocolRegistry.get(pname, ver)()

sim = Simulation(
    scenario, seed=seed,
    search_protocol=make_proto("search", main_args.search_proto),
    matching_protocol=make_proto("matching", main_args.matching_proto),
    bargaining_protocol=make_proto("bargaining", main_args.bargaining_proto),
)
```

### Code stubs (drop-in new files)
- Random Walk Search: `src/vmt_engine/protocols/search/random_walk.py`
```python
from __future__ import annotations
from typing import Any
from ..base import SearchProtocol, Effect, SetTarget
from ..registry import ProtocolRegistry
import hashlib

@ProtocolRegistry.register
class RandomWalkSearchProtocol(SearchProtocol):
    @property
    def name(self) -> str:
        return "random_walk_search"

    @property
    def version(self) -> str:
        return "2025.10.27"

    def build_preferences(self, world) -> list[tuple[int | tuple[int,int], float, dict[str, Any]]]:
        # Random baseline ignores preferences
        return []

    def select_target(self, world) -> list[Effect]:
        x, y = world.pos
        # Deterministic pseudo-random direction based on (tick, agent_id, pos)
        h = hashlib.sha256(f"{world.tick}-{world.agent_id}-{x}-{y}".encode()).digest()
        r = h[0] % 4  # 0..3
        dx, dy = [(1,0), (-1,0), (0,1), (0,-1)][r]
        # Bound within grid using provided grid_size
        N = world.params.get("grid_size", 40)  # requires builder to pass N
        nx = max(0, min(N - 1, x + dx))
        ny = max(0, min(N - 1, y + dy))
        if (nx, ny) == (x, y):
            return []  # already at boundary; no-op
        return [SetTarget(protocol_name=self.name, tick=world.tick, agent_id=world.agent_id, target=(nx, ny))]
```

- Random Matching: `src/vmt_engine/protocols/matching/random.py`
```python
from __future__ import annotations
from typing import Any
from ..base import MatchingProtocol, Effect, Pair
from ..registry import ProtocolRegistry
import hashlib

@ProtocolRegistry.register
class RandomMatchingProtocol(MatchingProtocol):
    @property
    def name(self) -> str:
        return "random_matching"

    @property
    def version(self) -> str:
        return "2025.10.27"

    def find_matches(
        self,
        preferences: dict[int, list[tuple[Any, float, dict[str, Any]]]],
        world,  # ProtocolContext
    ) -> list[Effect]:
        # Collect unpaired agents
        unpaired = [aid for aid, view in world.all_agent_views.items() if view.paired_with_id is None]
        # Deterministic pseudo-random ordering by hash(tick, id, pos)
        def key(aid: int) -> tuple[int, int]:
            v = world.all_agent_views[aid]
            h = hashlib.sha256(f"{world.tick}-{aid}-{v.pos[0]}-{v.pos[1]}".encode()).digest()
            return (int.from_bytes(h[:4], "big"), aid)  # stable tie-break by id
        unpaired.sort(key=key)
        # Pair consecutive in sorted order
        effects: list[Effect] = []
        for i in range(0, len(unpaired) - 1, 2):
            a, b = unpaired[i], unpaired[i + 1]
            effects.append(Pair(protocol_name=self.name, tick=world.tick, agent_a=a, agent_b=b, reason="random_matching"))
        return effects
```

- Split-the-Difference Bargaining: `src/vmt_engine/protocols/bargaining/split_difference.py`
```python
from __future__ import annotations
from math import floor
from typing import Any
from ..base import BargainingProtocol, Effect, Trade, Unpair
from ..registry import ProtocolRegistry
from ..context import WorldView
from ...econ.utility import u_total

@ProtocolRegistry.register
class SplitDifferenceBargainingProtocol(BargainingProtocol):
    @property
    def name(self) -> str:
        return "split_difference"

    @property
    def version(self) -> str:
        return "2025.10.27"

    def negotiate(self, pair: tuple[int, int], world: WorldView) -> list[Effect]:
        ai, aj = pair
        # Resolve partner info from params
        def pkey(k: str) -> str: return f"partner_{aj}_{k}"
        inv_i = world.inventory
        inv_j = {
            "A": int(world.params.get(pkey("inv_A"), 0)),
            "B": int(world.params.get(pkey("inv_B"), 0)),
            "M": int(world.params.get(pkey("inv_M"), 0)),
        }
        util_i = world.utility
        util_j = world.params.get(pkey("utility"))
        lam_j = float(world.params.get(pkey("lambda"), 1.0))
        muf_j = world.params.get(pkey("money_utility_form"), "linear")
        M0_j = float(world.params.get(pkey("M_0"), 0.0))
        lam_i = world.lambda_money
        muf_i = world.params.get("money_utility_form", "linear")
        M0_i = float(world.params.get("M_0", 0.0))

        regime = world.exchange_regime
        dA_max = int(world.params.get("dA_max", 5))
        eps = float(world.params.get("epsilon", 1e-9))

        # Helper to check utility improvement at fixed price and integer rounding
        def improves_pair(pair_type: str, give: str, take: str, price: float, qty: int):
            # Build new inventories deterministically
            if pair_type == "A<->B":
                dA, dB = qty, int(floor(price * qty + 0.5))
                if dA <= 0 or dB <= 0: return None
                if give == "i_sells":
                    inv_i_new = {"A": inv_i["A"] - dA, "B": inv_i["B"] + dB, "M": inv_i["M"]}
                    inv_j_new = {"A": inv_j["A"] + dA, "B": inv_j["B"] - dB, "M": inv_j["M"]}
                else:
                    inv_i_new = {"A": inv_i["A"] + dA, "B": inv_i["B"] - dB, "M": inv_i["M"]}
                    inv_j_new = {"A": inv_j["A"] - dA, "B": inv_j["B"] + dB, "M": inv_j["M"]}
            elif pair_type == "A<->M":
                dA, dM = qty, int(floor(price * qty + 0.5))
                if dA <= 0 or dM <= 0: return None
                if give == "i_sells":
                    inv_i_new = {"A": inv_i["A"] - dA, "B": inv_i["B"], "M": inv_i["M"] + dM}
                    inv_j_new = {"A": inv_j["A"] + dA, "B": inv_j["B"], "M": inv_j["M"] - dM}
                else:
                    inv_i_new = {"A": inv_i["A"] + dA, "B": inv_i["B"], "M": inv_i["M"] - dM}
                    inv_j_new = {"A": inv_j["A"] - dA, "B": inv_j["B"], "M": inv_j["M"] + dM}
            else:  # "B<->M"
                dB, dM = qty, int(floor(price * qty + 0.5))
                if dB <= 0 or dM <= 0: return None
                if give == "i_sells":
                    inv_i_new = {"A": inv_i["A"], "B": inv_i["B"] - dB, "M": inv_i["M"] + dM}
                    inv_j_new = {"A": inv_j["A"], "B": inv_j["B"] + dB, "M": inv_j["M"] - dM}
                else:
                    inv_i_new = {"A": inv_i["A"], "B": inv_i["B"] + dB, "M": inv_i["M"] - dM}
                    inv_j_new = {"A": inv_j["A"], "B": inv_j["B"] - dB, "M": inv_j["M"] + dM}

            # Inventory feasibility
            if min(inv_i_new.values()) < 0 or min(inv_j_new.values()) < 0:
                return None

            # Utility gains
            u_i0 = u_total(inv_i, {"utility": util_i, "lambda_money": lam_i, "money_utility_form": muf_i, "M_0": M0_i})
            u_j0 = u_total(inv_j, {"utility": util_j, "lambda_money": lam_j, "money_utility_form": muf_j, "M_0": M0_j})
            u_i1 = u_total(inv_i_new, {"utility": util_i, "lambda_money": lam_i, "money_utility_form": muf_i, "M_0": M0_i})
            u_j1 = u_total(inv_j_new, {"utility": util_j, "lambda_money": lam_j, "money_utility_form": muf_j, "M_0": M0_j})
            si, sj = (u_i1 - u_i0), (u_j1 - u_j0)
            if si > eps and sj > eps:
                return inv_i_new, inv_j_new, si, sj
            return None

        # Candidate pairs by regime with fixed order (barter first in barter_only; money first otherwise)
        if regime == "barter_only":
            orders = [("A<->B", ("ask_A_in_B", "bid_A_in_B"))]
        elif regime == "money_only":
            orders = [("A<->M", ("ask_A_in_M", "bid_A_in_M")), ("B<->M", ("ask_B_in_M", "bid_B_in_M"))]
        else:
            orders = [("A<->M", ("ask_A_in_M", "bid_A_in_M")), ("B<->M", ("ask_B_in_M", "bid_B_in_M")), ("A<->B", ("ask_A_in_B", "bid_A_in_B"))]

        # Try midpoint price per pair in both directions; return first feasible block
        for pair_name, (ask_key, bid_key) in orders:
            ask_i = world.quotes.get(ask_key, float("inf"))
            bid_i = world.quotes.get(bid_key, 0.0)
            ask_j = world.visible_agents[0].quotes.get(ask_key, float("inf")) if world.visible_agents else float("inf")
            bid_j = world.visible_agents[0].quotes.get(bid_key, 0.0) if world.visible_agents else 0.0
            # Direction i sells vs j sells
            candidates = []
            if ask_i <= bid_j:
                p = 0.5 * (ask_i + bid_j)
                for q in range(1, dA_max + 1):
                    r = improves_pair(pair_name, "i_sells", "j_buys", p, q)
                    if r:
                        inv_i_new, inv_j_new, si, sj = r
                        candidates.append(("i_sells", q, p, si, sj))
                        break
            if ask_j <= bid_i:
                p = 0.5 * (ask_j + bid_i)
                for q in range(1, dA_max + 1):
                    r = improves_pair(pair_name, "j_sells", "i_buys", p, q)
                    if r:
                        inv_i_new, inv_j_new, si, sj = r
                        candidates.append(("j_sells", q, p, si, sj))
                        break
            if candidates:
                # Choose the one with larger min(si, sj) to approximate equal surplus split
                choice = max(candidates, key=lambda t: min(t[3], t[4]))
                role, q, price, si, sj = choice
                # Build Trade effect consistent with pair_name and direction
                if pair_name == "A<->B":
                    dA = q
                    dB = int(floor(price * q + 0.5))
                    if role == "i_sells":
                        buyer, seller = aj, ai
                    else:
                        buyer, seller = ai, aj
                    return [Trade(protocol_name=self.name, tick=world.tick, buyer_id=buyer, seller_id=seller,
                                  pair_type="A<->B", dA=dA, dB=dB, dM=0, price=price,
                                  metadata={"surplus_buyer": si if buyer == ai else sj, "surplus_seller": sj if buyer == ai else si})]
                elif pair_name == "A<->M":
                    dA = q
                    dM = int(floor(price * q + 0.5))
                    if role == "i_sells":
                        buyer, seller = aj, ai
                    else:
                        buyer, seller = ai, aj
                    return [Trade(protocol_name=self.name, tick=world.tick, buyer_id=buyer, seller_id=seller,
                                  pair_type="A<->M", dA=dA, dB=0, dM=dM, price=price,
                                  metadata={"surplus_buyer": si if buyer == ai else sj, "surplus_seller": sj if buyer == ai else si})]
                else:  # "B<->M"
                    dB = q
                    dM = int(floor(price * q + 0.5))
                    if role == "i_sells":
                        buyer, seller = aj, ai
                    else:
                        buyer, seller = ai, aj
                    return [Trade(protocol_name=self.name, tick=world.tick, buyer_id=buyer, seller_id=seller,
                                  pair_type="B<->M", dA=0, dB=dB, dM=dM, price=price,
                                  metadata={"surplus_buyer": si if buyer == ai else sj, "surplus_seller": sj if buyer == ai else si})]

        # No feasible block at midpoint; unpair and cooldown
        return [Unpair(protocol_name=self.name, tick=world.tick, agent_a=ai, agent_b=aj, reason="trade_failed")]
```

### How to try them (no schema changes)
- Import and pass directly in your runner while we keep CLI/schema stable:
```python
from vmt_engine.protocols.search.random_walk import RandomWalkSearchProtocol
from vmt_engine.protocols.matching.random import RandomMatchingProtocol
from vmt_engine.protocols.bargaining.split_difference import SplitDifferenceBargainingProtocol

sim = Simulation(
    scenario, seed=seed,
    search_protocol=RandomWalkSearchProtocol(),
    matching_protocol=RandomMatchingProtocol(),
    bargaining_protocol=SplitDifferenceBargainingProtocol(),
)
```

### Acceptance checks
- Determinism: fixed seed → identical runs; random walk and random matching vary by initial positions (seeded) and tick.
- Safety: SetTarget always within grid; Pair effects never double-book an agent; Trade effects conserve A, B, M; inventories non-negative.
- Compatibility: No changes to engine loop; telemetry continues to log preferences, pairings, trades.

### Quick decisions to unblock me
- Protocol selection surface now: prefer CLI flags (no schema edits) or add `protocols:` to scenarios? I recommend CLI first; scenario fields later if desired.
- OK to add `grid_size` into WorldView params via builder? This is a 3-line, low-risk enabler for Random Walk.

If you’re good with CLI-first and adding `grid_size`, I’ll finalize the stubs above into the repo and wire up the optional flags.

- Implemented: Verified protocol architecture and call sites in `DecisionSystem` and `TradeSystem`. Proposed Phase 2a baselines with file targets and code stubs. Suggested minimal helper (pass `grid_size`) and optional CLI selection to avoid schema changes.