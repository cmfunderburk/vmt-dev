## Scenarios and Typing

### Authoring scenarios
- Start from `docs/structures/comprehensive_scenario_template.yaml`.
- Keep scenarios minimal for tests; expand for demos.

### Typing constraints (authoritative)
- See `docs/4_typing_overview.md`.
- Inventories, resources, ΔA, ΔB: integers (no floats).
- Spatial parameters (`vision_radius`, `interaction_radius`, `move_budget`): integers.

### Protocol configuration in YAML
```yaml
search_protocol: "legacy_distance_discounted"
matching_protocol: "legacy_three_pass"
bargaining_protocol: "split_difference"
```

### Seeds and determinism
- Always set an explicit `seed` when comparing outputs across runs.
- Use identical seeds to validate reproducibility.

### Common validation checks
- Parameter ranges (non-negative, within caps).
- Utility-specific invariants (e.g., Stone–Geary subsistence levels).


