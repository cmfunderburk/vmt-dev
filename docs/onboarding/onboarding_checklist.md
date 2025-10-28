## Onboarding Checklist (Day 0–5)

### Day 0 (30–60 min)
- Create venv; install dependencies.
- Run one demo via GUI and one via CLI.

### Day 1
- Read architecture overview and determinism sections.
- Run a headless job and open the SQLite in the log viewer.

### Day 2
- Add a tiny test covering a corner case you noticed.
- Read through `tests/` for live examples.

### Day 3
- Edit a scenario in `scenarios/demos/` and validate outputs are deterministic across runs.

### Day 4–5
- Implement a small protocol tweak behind a flag (YAML-configurable), with tests.
- Benchmark with `scripts/benchmark_performance.py` and compare telemetry.

### Exit criteria
- You can run any scenario deterministically (seeded) and explain differences between regimes and modes.
- You can add/modify a protocol and validate through tests and telemetry.


