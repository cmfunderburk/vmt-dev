## Testing Guide

### Run tests
```bash
pytest                   # full suite
pytest -q                # quiet
pytest -k "money or pairing"  # filter by keyword
```

### Import paths in tests
- Prefer `from vmt_engine...`, `from scenarios...`, `from telemetry...`.
- Avoid `src.` prefixes in tests to prevent duplicate imports/state.
  - See `README.md` → Testing Import Paths.

### Writing tests
- Keep scenarios minimal; use `scenarios/test/` or inline fixtures.
- Validate determinism with fixed seeds and snapshot comparisons where relevant.
- Cover both happy-path and edge cases (e.g., zero-inventory guards, rounding).

### Useful patterns
```python
import pytest

@pytest.mark.parametrize("seed", [1, 2, 3])
def test_deterministic_pairing(seed):
    # Arrange: load small scenario
    # Act: run a few ticks with the seed
    # Assert: identical telemetry or stable invariants
    pass
```

### Performance tests
- Use `scripts/benchmark_performance.py` for manual checks.
- Keep CI-focused tests fast; isolate heavy benchmarks locally.


