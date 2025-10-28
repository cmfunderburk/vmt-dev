## Quickstart

### Run the GUI (recommended)
```bash
python launcher.py
```
Then select `scenarios/demos/demo_01_foundational_barter.yaml` and launch.

### Run via CLI
```bash
python main.py scenarios/demos/demo_01_foundational_barter.yaml
```

### Run headless with logging
```bash
python scripts/run_headless.py \
  --scenario scenarios/demos/demo_01_foundational_barter.yaml \
  --ticks 200 \
  --seed 42 \
  --db out/demo_01.sqlite
```

### Inspect telemetry
```bash
python -m src.vmt_log_viewer.main --db out/demo_01.sqlite
```

### Next steps
- Read the architecture overview: [3_architecture_overview.md](3_architecture_overview.md)
- Explore scenarios in `scenarios/demos/` and templates in `docs/structures/`


