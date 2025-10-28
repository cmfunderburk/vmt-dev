## Telemetry and Analysis

### Writing logs (headless)
```bash
python scripts/run_headless.py \
  --scenario scenarios/demos/demo_02_money.yaml \
  --ticks 400 --seed 123 --db out/money_demo.sqlite
```

### Log viewer (GUI)
```bash
python -m src.vmt_log_viewer.main --db out/money_demo.sqlite
```

### Analysis scripts
- Trade distribution: `python scripts/analyze_trade_distribution.py --db out/money_demo.sqlite`
- Compare snapshots: `python scripts/compare_telemetry_snapshots.py --a out/run_a.sqlite --b out/run_b.sqlite`
- Plot mode timeline: `python scripts/plot_mode_timeline.py --db out/money_demo.sqlite`

### Determinism verification
1. Run the same scenario twice with the same seed → two SQLite files.
2. Compare with `compare_telemetry_snapshots.py`; expect identical outputs.


