## Performance Guide

### Benchmarks
```bash
python scripts/benchmark_performance.py --scenario scenarios/perf_both_modes.yaml --ticks 200 --seed 42
```

### Tips
- Avoid O(N²) all-pairs within ticks; prefer localized neighbor scans.
- Minimize object creation in inner loops; reuse small structs where possible.
- Use integer arithmetic for money and counts to avoid float overhead/rounding.
- Ensure iterations are sorted but avoid unnecessary resorting each tick.

### Profiling workflow
1. Establish baseline with a perf scenario and seed.
2. Make a targeted change; re-run benchmark; compare telemetry and TPS.
3. If output changes unexpectedly, investigate determinism first, then performance.


