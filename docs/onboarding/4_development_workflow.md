## Development Workflow

### Branching and commits
- Keep commits small and descriptive (present tense, imperative mood).
- Group changes logically (engine, protocols, scenarios, docs).

### Code style and clarity
- Favor readability and explicitness over cleverness.
- Use descriptive names (avoid 1–2 letter identifiers).
- Prefer early returns; avoid deep nesting beyond 2–3 levels.
- Only use try/except where exceptions are expected; handle meaningfully.

### Determinism checklist (pre-PR)
- No unseeded randomness.
- Explicitly ordered iterations.
- All state changes via Effects.
- Same-seed reruns produce identical telemetry snapshots.

### Testing
```bash
pytest               # full suite
pytest tests/test_money_phase1_integration.py
pytest -k "pairing or regime"
```
Use `tests/` as executable documentation. Prefer `vmt_engine`, `scenarios`, and `telemetry` import paths in tests (avoid `src.` prefix).

### Documentation
- Co-locate developer-facing docs under `docs/` and `docs/onboarding/`.
- For reviews/annotations, use the standardized format `> model_or_username: comment`.

### Scenarios
- Use `docs/structures/comprehensive_scenario_template.yaml` as reference.
- Keep inventories/resources/ΔA/ΔB as integers; spatial parameters are ints (see `docs/4_typing_overview.md`).

### Performance hygiene
- Prefer O(N) passes over O(N²) all-pairs.
- Avoid per-tick object churn and hidden allocations in tight loops.


