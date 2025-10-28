## Protocol Development Guide

This guide explains how to implement new protocols (search, matching, bargaining) that produce Effects without mutating state directly.

### Where things live
- Base classes and Effects: `src/vmt_engine/protocols/base.py`
- Protocols:
  - Search: `src/vmt_engine/protocols/search/`
  - Matching: `src/vmt_engine/protocols/matching/`
  - Bargaining: `src/vmt_engine/protocols/bargaining/`
- Registry and names: `src/vmt_engine/protocols/registry.py`

### Design rules
- Receive a read-only `WorldView` (no direct state access).
- Return a list of Effects. Do not modify world or agents in-place.
- Use only provided seeded RNGs from context; never global randomness.
- Ensure all iterations are ordered and deterministic.

### Skeleton (illustrative)
```python
from vmt_engine.protocols.base import ProtocolBase, MoveEffect

class ExampleSearchProtocol(ProtocolBase):
    """Select a movement target deterministically from visible cells.
    """
    name = "example_search"

    def execute(self, context) -> list:
        # context provides: self.rng, world_view, agent_view, params
        agent = context.agent_view
        visible_cells = sorted(context.world_view.visible_cells(agent.id))
        if not visible_cells:
            return []
        target = visible_cells[0]  # deterministic choice for illustration
        return [MoveEffect(agent_id=agent.id, new_position=target)]
```

### Adding a new protocol
1. Implement class in the appropriate subpackage; set `name` to the canonical identifier used in YAML and telemetry.
2. Register in `src/vmt_engine/protocols/registry.py` if not auto-discovered.
3. Add tests under `tests/` covering determinism and phase behavior.
4. Update docs if the protocol introduces new parameters.

### YAML configuration
Protocols are configured in scenario YAML (see `docs/structures/comprehensive_scenario_template.yaml`). For example:
```yaml
search_protocol: "legacy_distance_discounted"
matching_protocol: "legacy_three_pass"
bargaining_protocol: "split_difference"
```

### Determinism checklist for protocols
- No unseeded randomness.
- Sorted iteration over agents, candidates, and pairs.
- Stable tie-breaking: use `(min_id, max_id)` or explicit numeric priorities.
- Return Effects only; let systems validate/apply.

### Testing your protocol
- Add focused unit tests plus at least one integration test using a small scenario.
- Re-run deterministic snapshot comparisons if behavior affects outputs.


