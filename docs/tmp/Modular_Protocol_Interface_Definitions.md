# Modular Protocol Interface Definitions

We propose separating "search" and "matching" into distinct strategy interfaces. For example:

```python
class SearchProtocol:
    """How agents explore their environment to find opportunities."""
    def select_search_target(self, agent: Agent, perception: PerceptionView) -> Position:
        """Choose where the agent should move/search next."""
        ...
    
    def evaluate_opportunity(self, agent: Agent, target: Target) -> float:
        """Score a potential target (e.g. resource or partner)."""
        ...

class MatchingProtocol:
    """How agents form bilateral partnerships."""
    def build_preferences(self, agents: list[Agent]) -> dict[int, list[int]]:
        """Compute a ranked list of preferred partner IDs for each agent."""
        ...
    
    def find_matches(self, preferences: dict[int, list[int]]) -> list[tuple[int,int]]:
        """Return a set of matched agent pairs (agent_i, agent_j)."""
        ...
```

These interfaces are analogous to the conceptual sketches in the design proposal[^1][^2]. Each method should be fully deterministic (e.g. sorted loops) to preserve the engine's reproducibility guarantees[^3].

## Initial Concrete Implementations

We will ship several default algorithms implementing these interfaces, starting with simple baselines and well-known strategies:

- **Baseline/Random (Search & Matching)**: A naïve strategy (e.g. `RandomWalkSearch` and `RandomMatching`) that picks targets or partners uniformly at random. This serves as a simple control and ensures minimal behavior.

- **Greedy Matching**: A surplus-maximizing fallback akin to the current engine's decision-phase pass 3 (surplus-based greedy pairing)[^4]. For example, a `GreedyMatching` class can collect all potential pairs with positive surplus, sort by descending surplus, and assign matches greedily (ensuring no agent is double-matched).

- **Deferred Acceptance (Stable Matching)**: Implement the Gale–Shapley stable matching algorithm as a `StableMatching` protocol. Each agent proposes down its preference list until no blocking pairs remain. This guarantees a stable outcome under strict preferences, in contrast to greedy maximization.

For search protocols, we might similarly provide: e.g. a `GradientSearch` that moves toward highest-value opportunities vs. a `RandomWalkSearch`. These correspond to "random walk vs. gradient ascent" in search strategy examples[^5]. Each concrete class will override the protocol methods above. For example, a greedy matching implementation might look conceptually like this (from the design doc):

```python
class GreedyMatching(MatchingProtocol):
    def build_preferences(self, agents):
        # Build preference lists sorted by discounted surplus
        preferences = {}
        for i in agents:
            # Compute surplus with each j and sort
            sorted_partners = sorted(agents, key=lambda j: surplus(i,j), reverse=True)
            preferences[i.id] = [j.id for j in sorted_partners if surplus(i,j)>0]
        return preferences
    
    def find_matches(self, preferences):
        # Flatten all (surplus, i, j) and pick highest first
        all_pairs = []
        for i, pref_list in preferences.items():
            for j in pref_list:
                all_pairs.append((surplus(i,j), i, j))
        all_pairs.sort(reverse=True)
        matched = set()
        matches = []
        for _, i, j in all_pairs:
            if i not in matched and j not in matched:
                matches.append((i, j))
                matched |= {i,j}
        return matches
```

Similarly, a `RandomMatching` would ignore surplus and pair randomly, and a `DeferredAcceptance` class would implement the standard propose-and-reject loop. These implementations will be tested to ensure they obey determinism rules (e.g. breaking ties by agent ID)[^3].

## Migration Path for Core Simulation Loop

We will gradually refactor the main 7-phase loop (currently hardcoded in `DecisionSystem`, etc.) to invoke these protocols. In Phase 1, we add loader hooks so that the simulation can instantiate protocols from scenario config (using a registry or factory). For example, the full engine could initialize as:

```python
# Pseudo-code for integration
class FullSimulation:
    def __init__(self, scenario):
        # Load protocol instances based on scenario or defaults
        self.search_protocol   = load_protocol(scenario.search_protocol)
        self.matching_protocol = load_protocol(scenario.matching_protocol)
        self.bargaining_protocol = load_protocol(scenario.bargaining_protocol)
        ...
    
    def decision_phase(self):
        # Use the search protocol for target selection
        for agent in self.agents:
            if agent.needs_partner:
                target = self.search_protocol.select_search_target(agent, perception)
                agent.set_target(target)
    
    def pairing_phase(self):
        # Build preferences and find matches via MatchingProtocol
        preferences = self.matching_protocol.build_preferences(self.agents)
        matches = self.matching_protocol.find_matches(preferences)
        for i,j in matches:
            pair_agents(i, j)
    
    def trade_phase(self):
        # (Bargaining out of scope for now)
        ...
```

This sketch (adapted from design notes[^6][^7]) shows replacing the hardcoded three-pass pairing with calls to `build_preferences` / `find_matches`. In Phase 2, we retain full compatibility by default: if no protocol is specified, the loader defaults to a "legacy" protocol that encapsulates the existing `DecisionSystem` logic. In Phase 3, we complete the integration: the `DecisionSystem` (or new systems) delegates to the search protocol for target selection and to the matching protocol for pair formation.

Throughout these phases we validate that tick-to-tick behavior is identical under the old and new implementations when the "legacy" protocols are used. Rigorous unit tests will compare outputs (agent targets, pairings, trades, telemetry) before and after refactoring, ensuring no regressions. Detailed steps are outlined in the project roadmap[^8][^9], including prototyping one protocol at a time, then expanding and finally full integration.

## Scenario Schema Adjustments

To enable configurable protocols, we will extend the YAML schema. For backward compatibility, existing scenarios need no changes. For new modular scenarios, we add fields such as:

```yaml
name: three_agent_barter
agents: 3

protocols:
  search:   "perception_based"   # (optional; default uses current implicit search logic)
  matching: "three_pass_pairing" # default is current mutual+greedy algorithm
  # (bargaining omitted for now)
```

This follows the "protocol names in scenarios" pattern suggested in our design docs[^10][^11]. We will update `src/scenarios/schema.py` and `loader.py` to accept optional `protocols.search` and `protocols.matching` entries. For search-only or matching-only scenarios, we may also support a top-level `simulation_type: "search"` or `"matching"` (as in early examples[^12][^13]) to automatically disable irrelevant phases.

By default, if no protocols are specified, the engine behaves exactly as today (using the legacy decision system in place). Over time we will encourage explicitly naming the protocol set, but legacy scenarios remain valid without changes. New example scenarios (e.g. `gradient_climb_search` and `stable_marriage_demo`) demonstrate isolated search or matching runs[^14][^13].

## Telemetry Adjustments

Current telemetry already logs agent states, decisions, preferences and pairings[^15][^16]. We will extend this to capture protocol-specific metrics where relevant. For instance, the matching protocol can continue logging preferences (ranked partner lists) and pairing events (pair/unpair ticks) as before[^15]. If a search protocol has unique diagnostics (e.g. "time to discovery" or "visited cells count"), we can log these to new fields or tables.

We recommend a hybrid telemetry strategy: share core tables for common data (agent positions, chosen targets, match outcomes) and add supplemental tables for protocol-specific info[^17]. For example, we might add a `search_events` table if needed. In existing `pairings` and `preferences` tables, we can include the protocol name or tag (via the run configuration) to distinguish data from different matching algorithms. The design document recommends exactly this hybrid approach[^17]. All protocol implementations should use the `TelemetryManager` API (e.g. `telemetry.log_preference`, `log_pairing_event`) so that data flows into the same DB. We will update the telemetry schema accordingly and ensure new fields (e.g. a "protocol_name" column) do not break backward compatibility.

## Performance Considerations

Because search and matching are now isolated, we can optimize them independently. Each agent's search decision or preference ranking is embarrassingly parallelizable: loops over agents or neighbors can be safely parallelized or vectorized (since we use sorted, deterministic loops[^3]). For example, computing discounted surplus with neighbors uses a spatial index (already O(N) average)[^18]; we can cache distances or reuse neighbor lists across ticks. In matching, building all surplus entries is O(N·k) (k≈neighbors) and sorting is O(n log n). A greedy matcher can be optimized with heaps or GPU-parallel scans if needed. Deferred-acceptance involves multiple rounds, but proposals across agents can be batched. We should explore batch operations (e.g. NumPy for calculations) and caching (e.g. reuse last tick's sorted lists if inventories haven't changed).

Because protocols are decoupled, we can also run different algorithms on separate threads or processes (with care to preserve determinism). In particular, [7] notes that isolated components are "easier to parallelize" and to optimize separately[^19]. We will profile each protocol (with standard scenarios) and set performance targets: ideally overall speed stays within ~10% of the monolithic engine, as suggested in our success criteria[^20]. If a protocol implementation is slow, it can be replaced or tuned without touching the core.

## Backward Compatibility Strategy

Full backward compatibility is critical. We will not change any default behavior unless a protocol is explicitly specified. To achieve this:

- **Defaults**: The scenario loader will default `search_protocol` and `matching_protocol` to "legacy" implementations that encapsulate the current 3-pass decision logic. In effect, an old scenario with no protocol fields will run exactly as before (with identical inventory, pairing, and trade outcomes).

- **Legacy Mode**: We will maintain a "full-simulation" or "legacy" protocol set that faithfully reproduces the old engine. As noted in our docs, "existing scenarios run unchanged (they implicitly use 'full' mode)"[^21]. We will add regression tests to ensure outputs match the pre-modular engine.

- **Migration Guides**: We will update documentation to show how to opt-in to new protocols, and how to specify the legacy behavior explicitly if desired (e.g. setting `protocols.search: "perception_based"` as in [45]). Existing CLI options and scenario schemas remain valid.

During rollout, we may deprecate the old integrated code paths, but only after verifying that the new protocol-based engine has an identical feature matrix. We will keep both worlds available until confidence is high.

## Testing Plan

A comprehensive test suite will ensure correctness and determinism across the refactoring:

- **Unit tests for each protocol**: Every `SearchProtocol` and `MatchingProtocol` implementation should have targeted tests. For example, test that `GreedyMatching` on a small hand-crafted set of preferences produces the correct pairs, and that `DeferredAcceptance` yields a stable matching. Test that `RandomMatching` respects the random seed (e.g. fixed RNG yields reproducible matchings).

- **Integration scenarios**: Create "search-only" and "matching-only" scenario files (as in the examples[^14][^13]) to test isolated behavior. For instance, verify that a search-only scenario logs discovery metrics and no trades, and that a matching-only scenario produces the expected pairings of agents with static positions.

- **Regression tests vs. legacy engine**: Run the new engine on a suite of existing scenarios and compare key outputs (agent snapshots, trades, telemetry) to the legacy results. Any differences must be zero (up to floating-point tolerances) if legacy protocols are used. We will use deep equality checks on the SQLite telemetry or rerun reference runs. Determinism tests will verify that repeated runs with the same seed produce identical logs[^3].

- **Performance benchmarks**: Continuously measure ticks-per-second on standard scenarios. The new modular implementation should meet our target (e.g. within ~10% of original throughput, per success criteria[^20]).

- **Determinism and Race Conditions**: Even if we parallelize parts of the code, we must preserve the determinism rules (sorted loops, fixed tie-breaks) outlined in the technical manual[^3]. We will include random-seed tests and controlled concurrency tests to ensure no nondeterminism is introduced by the new protocols.

By following this plan, we achieve a gradual, test-driven migration from a monolithic Decision phase into a flexible, high-performance protocol framework. The design is grounded in our current engine architecture[^22][^23] and remains fully backward-compatible by default[^21]. New scenario types (search-only, matching-only) and extensibility via a protocol registry (e.g. naming "gradient_ascent" or "greedy_surplus" in YAML[^10]) become possible without sacrificing performance or correctness.

---

## References

Sources: VMT Technical Manual and design docs[^22][^3][^19][^21][^1][^2][^15][^10][^6]

[^1]: [^2] [^5] [^6] [^7] [^8] [^9] [^10] [^11] [^12] [^13] [^14] [^17] [^19] [^20] [^21] [^23] DISCUSSION_modular_protocols_2025-10-20.md  
https://github.com/cmfunderburk/vmt-dev/blob/169be3a8f3dcd86f6f241036b41632c16dbde3df/docs/DISCUSSION_modular_protocols_2025-10-20.md

[^3]: [^4] [^18] [^22] README.md  
https://github.com/cmfunderburk/vmt-dev/blob/169be3a8f3dcd86f6f241036b41632c16dbde3df/src/vmt_engine/README.md

[^15]: CHANGELOG.md  
https://github.com/cmfunderburk/vmt-dev/blob/169be3a8f3dcd86f6f241036b41632c16dbde3df/CHANGELOG.md

[^16]: db_loggers.py  
https://github.com/cmfunderburk/vmt-dev/blob/169be3a8f3dcd86f6f241036b41632c16dbde3df/src/telemetry/db_loggers.py

