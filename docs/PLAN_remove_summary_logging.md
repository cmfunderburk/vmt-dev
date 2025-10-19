# Plan: Remove Summary Logging Level

**Date**: 2025-10-19  
**Rationale**: Benchmark data shows summary logging provides minimal performance benefit (2.5% in exchange scenarios) while removing valuable decision data. Comprehensive logging is vital for pedagogical and research goals. Performance optimization should come from simulation code, not from disabling telemetry.

---

## Executive Summary

**Goal**: Simplify telemetry system by removing `LogLevel.SUMMARY` and `LogConfig.summary()`, leaving only two logging modes:
1. **STANDARD** (default) - Comprehensive production logging
2. **DEBUG** - Additional failed trade attempt logging

**Impact**: 
- Removes 1 of 3 log levels (simplification)
- Eliminates configuration complexity
- Enforces comprehensive logging by default
- Reduces maintenance burden
- ~10 files to modify

---

## Rationale (Data-Driven)

### Benchmark Evidence

From performance baseline testing (500 ticks, 400 agents, seed 42):

| Scenario | No Logging | Summary | Standard | Summary Benefit |
|----------|------------|---------|----------|-----------------|
| Exchange | 4.7 TPS | 4.0 TPS | 4.1 TPS | **-2.5%** (worse!) |
| Forage | 22.9 TPS | ~15 TPS (est.) | 14.0 TPS | ~7% (marginal) |

**Key finding**: In exchange scenarios (the computationally expensive case), summary logging is **slower** than standard logging because:
- Trade logging dominates overhead
- Decision logs are nearly free when agents are in trade cooldown
- Disabling agent snapshots provides no benefit (trades trigger snapshots anyway)

### Architectural Alignment

**Project values** (from always-applied rules):
- Pedagogical use: requires comprehensive agent decision data
- Research use: requires full behavioral telemetry
- Deterministic reproducibility: requires consistent logging behavior

**Summary logging conflicts** with these values by:
- Omitting agent decision logs
- Disabling periodic snapshots
- Creating inconsistent telemetry based on configuration
- Adding complexity without meaningful performance benefit

---

## Implementation Plan

### Phase 1: Code Changes (Core System)

#### 1.1. `src/telemetry/config.py`

**Remove:**
- `LogLevel.SUMMARY` enum value
- `LogConfig.summary()` factory method
- Summary-specific branch in `__post_init__`
- `'summary'` from `from_string()` mapping

**Simplify:**
```python
class LogLevel(IntEnum):
    """Logging verbosity levels."""
    STANDARD = 1   # Decisions + trades + periodic snapshots (default)
    DEBUG = 2      # Everything including failed trade attempts
    
    @classmethod
    def from_string(cls, level: str) -> 'LogLevel':
        """Convert string to LogLevel."""
        level_map = {
            'standard': cls.STANDARD,
            'debug': cls.DEBUG,
        }
        return level_map.get(level.lower(), cls.STANDARD)
```

**Update `__post_init__`:**
```python
def __post_init__(self):
    """Adjust settings based on log level."""
    if self.level == LogLevel.DEBUG:
        self.log_trade_attempts = True
    else:
        self.log_trade_attempts = False
```

**Update `minimal()` factory:**
```python
@classmethod
def minimal(cls) -> 'LogConfig':
    """Create a minimal config for testing (no snapshots, only trades)."""
    return cls(
        level=LogLevel.STANDARD,  # Changed from SUMMARY
        agent_snapshot_frequency=0,
        resource_snapshot_frequency=0,
        log_decisions=False,
        log_trade_attempts=False,
        log_agent_snapshots=False,
        log_resource_snapshots=False
    )
```

**Lines to modify**: 12, 17-24, 56-66, 69-71, 87

---

#### 1.2. `scripts/benchmark_performance.py`

**Remove:**
- `"summary"` from `log_level` parameter documentation
- `if log_level == "summary"` branch

**Change default:**
```python
def run_benchmark(scenario_name: str, ticks: int, seed: int = 42, log_level: str = "standard"):
    """
    Run a single benchmark scenario and return timing metrics.
    
    Args:
        scenario_name: Key from SCENARIOS dict
        ticks: Number of simulation ticks to run
        seed: Random seed for reproducibility
        log_level: Logging level ("standard", "debug", or "off")
    """
```

**Update logic:**
```python
# Configure logging
if log_level == "standard":
    log_cfg = LogConfig.standard()
elif log_level == "debug":
    log_cfg = LogConfig.debug()
else:
    log_cfg = LogConfig(use_database=False)
```

**Update CLI:**
```python
parser.add_argument(
    "--log-level",
    choices=["standard", "debug", "off"],
    default="standard",  # Changed from "summary"
    help="Telemetry logging level (default: standard)"
)
```

**Lines to modify**: 43, 51, 67-68, 139, 206-209

---

#### 1.3. `tests/test_barter_integration.py`

**Replace `LogConfig.summary()` with `LogConfig.standard()`:**

```python
# Line 22
sim1 = Simulation(load_scenario(scenario_path), seed=42, log_config=LogConfig.standard())

# Line 28
sim2 = Simulation(load_scenario(scenario_path), seed=42, log_config=LogConfig.standard())
```

**Rationale**: These tests verify determinism. Standard logging still supports deterministic behavior and is more representative of production use.

**Lines to modify**: 22, 28

---

#### 1.4. `tests/test_mode_integration.py`

**No changes needed** - already uses `LogConfig.minimal()`, which will be updated in config.py

---

### Phase 2: Documentation Updates

#### 2.1. `.cursor/rules/scenarios-telemetry.mdc`

**Update Log Levels section:**

```markdown
#### Log Levels

```python
from telemetry.config import LogConfig

# STANDARD: Production logging (default)
sim = Simulation(scenario, seed=42, log_config=LogConfig.standard())

# DEBUG: Full detail including failed trades
sim = Simulation(scenario, seed=42, log_config=LogConfig.debug())
```
```

**Update table:**
```markdown
| Feature | Off | Standard | Debug |
|---------|-----|----------|-------|
| Trade events | ❌ | ✅ | ✅ |
| Agent decisions | ❌ | ✅ | ✅ |
| Agent snapshots | ❌ | ✅ (every tick) | ✅ (every tick) |
| Resource snapshots | ❌ | ✅ (every 10 ticks) | ✅ (every tick) |
| Failed trade attempts | ❌ | ❌ | ✅ |
```

**Remove all "SUMMARY" references**

---

#### 2.2. Performance Documentation

**Files to update:**
- `docs/performance_baseline_phase1_with_logging.md`
- `docs/performance_comparison_logging.md`

**Add deprecation notice at top:**
```markdown
> **Note (2025-10-19)**: Summary logging has been removed based on benchmark evidence showing minimal performance benefit (<3% in critical scenarios). All logging now uses STANDARD level by default. See [removal plan](PLAN_remove_summary_logging.md) for rationale.
```

**Update tables** to remove "Summary" columns and note historical data

---

#### 2.3. `CHANGELOG.md`

**Add entry:**
```markdown
### 2025-10-19 - Removed Summary Logging Level

**Breaking Change**: Removed `LogLevel.SUMMARY` and `LogConfig.summary()`

**Rationale**: Performance benchmarks showed summary logging provided minimal benefit:
- Exchange scenarios: 2.5% overhead difference (4.0 vs 4.1 TPS)
- Decision logs are nearly free when agents are in trade cooldown
- Trade logging dominates overhead regardless of level
- Comprehensive logging is vital for pedagogical and research use

**Migration**:
- Replace `LogConfig.summary()` → `LogConfig.standard()`
- Remove `--log-level summary` CLI arguments
- Scripts using `log_level="summary"` should use `log_level="standard"`

**Remaining log levels**:
- STANDARD (default): Comprehensive production logging
- DEBUG: Adds failed trade attempt logging

**Impact**: Simplifies telemetry system, enforces comprehensive logging by default.

See `docs/PLAN_remove_summary_logging.md` for full rationale.
```

---

### Phase 3: Testing Strategy

#### 3.1. Unit Tests

**Verify:**
- `LogLevel.STANDARD` and `LogLevel.DEBUG` work correctly
- `LogLevel.from_string()` handles "standard" and "debug"
- `LogLevel.from_string()` returns STANDARD for unknown values
- `LogConfig.standard()` creates correct configuration
- `LogConfig.debug()` creates correct configuration
- `LogConfig.minimal()` works with updated base level

**Test file**: Create `tests/test_telemetry_config_after_removal.py`

```python
def test_loglevel_enum():
    """Verify STANDARD and DEBUG levels exist."""
    assert LogLevel.STANDARD == 1
    assert LogLevel.DEBUG == 2
    assert not hasattr(LogLevel, 'SUMMARY')

def test_from_string():
    """Verify string conversion."""
    assert LogLevel.from_string("standard") == LogLevel.STANDARD
    assert LogLevel.from_string("debug") == LogLevel.DEBUG
    assert LogLevel.from_string("unknown") == LogLevel.STANDARD  # Default
    
def test_factory_methods():
    """Verify factory methods work."""
    cfg_std = LogConfig.standard()
    assert cfg_std.level == LogLevel.STANDARD
    assert cfg_std.log_decisions == True
    assert cfg_std.log_trade_attempts == False
    
    cfg_dbg = LogConfig.debug()
    assert cfg_dbg.level == LogLevel.DEBUG
    assert cfg_dbg.log_trade_attempts == True
    
def test_minimal_config():
    """Verify minimal() factory still works."""
    cfg = LogConfig.minimal()
    assert cfg.level == LogLevel.STANDARD
    assert cfg.log_decisions == False
    assert cfg.log_agent_snapshots == False
```

#### 3.2. Integration Tests

**Run existing test suite:**
```bash
pytest -q
# Expected: All 78 tests still pass
```

**Verify no regressions:**
- Mode integration tests (use `minimal()`)
- Barter integration tests (now use `standard()`)
- Performance scenarios still run

#### 3.3. Performance Validation

**Re-run benchmarks:**
```bash
python scripts/benchmark_performance.py --log-level standard
# Verify results match previous "standard" baseline
```

**Expected results** (should be identical to previous standard logging):
- Forage: 14.0 TPS
- Exchange: 4.1 TPS
- Both: 7.5 TPS

---

### Phase 4: Backward Compatibility Considerations

#### 4.1. Breaking Changes

**Code that will break:**
```python
# BREAKS
LogConfig.summary()
LogLevel.SUMMARY
log_level="summary"
```

**Migration path:**
```python
# BEFORE
config = LogConfig.summary()
sim = Simulation(scenario, log_config=LogConfig.summary())

# AFTER
config = LogConfig.standard()
sim = Simulation(scenario, log_config=LogConfig.standard())
```

#### 4.2. CLI Impact

**Scripts using:**
```bash
python scripts/benchmark_performance.py --log-level summary
```

**Will fail with:**
```
error: argument --log-level: invalid choice: 'summary' (choose from 'standard', 'debug', 'off')
```

**Fix:** Remove `--log-level summary` or change to `--log-level standard`

#### 4.3. User Impact

**Low risk** because:
- Project is pre-Phase 2 (no external users yet)
- Summary logging was never documented in main README
- Only appears in recent performance benchmarks
- Easy migration path (1:1 replacement)

---

## Implementation Checklist

### Code Changes
- [ ] Update `src/telemetry/config.py`
  - [ ] Remove `LogLevel.SUMMARY`
  - [ ] Remove `summary()` factory method
  - [ ] Simplify `__post_init__`
  - [ ] Update `from_string()` mapping
  - [ ] Fix `minimal()` to use STANDARD
- [ ] Update `scripts/benchmark_performance.py`
  - [ ] Change default to "standard"
  - [ ] Remove "summary" branch
  - [ ] Update CLI choices
  - [ ] Update docstrings
- [ ] Update `tests/test_barter_integration.py`
  - [ ] Replace `summary()` → `standard()` (2 places)

### Documentation
- [ ] Update `.cursor/rules/scenarios-telemetry.mdc`
  - [ ] Remove SUMMARY references
  - [ ] Update code examples
  - [ ] Update tables
- [ ] Update `docs/performance_baseline_phase1_with_logging.md`
  - [ ] Add deprecation notice
  - [ ] Mark summary data as historical
- [ ] Update `docs/performance_comparison_logging.md`
  - [ ] Add deprecation notice
  - [ ] Update recommendations
- [ ] Update `CHANGELOG.md`
  - [ ] Add breaking change entry
  - [ ] Document rationale
  - [ ] Provide migration guide

### Testing
- [ ] Create `tests/test_telemetry_config_after_removal.py`
- [ ] Run full test suite: `pytest -q`
- [ ] Verify 78 tests still pass
- [ ] Run performance benchmarks with `--log-level standard`
- [ ] Verify determinism (seed 42, repeated runs)

### Validation
- [ ] No references to "summary" or "SUMMARY" in `src/`
- [ ] No references to "summary" in `scripts/` (except comments)
- [ ] All tests pass
- [ ] Performance benchmarks match previous standard baseline
- [ ] No linting errors

---

## Timeline Estimate

**Total effort**: 1-2 hours

1. **Code changes**: 30 minutes
   - config.py: 10 min
   - benchmark script: 10 min
   - tests: 10 min

2. **Documentation**: 30 minutes
   - Cursor rules: 10 min
   - Performance docs: 15 min
   - CHANGELOG: 5 min

3. **Testing**: 20 minutes
   - Unit tests: 10 min
   - Integration tests: 5 min
   - Performance validation: 5 min

4. **Verification**: 10 minutes
   - Grep for lingering references
   - Linting
   - Final review

---

## Risks and Mitigations

### Risk 1: External scripts using summary logging

**Likelihood**: Low (project is pre-Phase 2)  
**Impact**: Low (easy migration)  
**Mitigation**: Clear error message points to CHANGELOG

### Risk 2: Performance regression

**Likelihood**: Zero (no behavioral changes to simulation code)  
**Impact**: N/A  
**Mitigation**: Re-run benchmarks to confirm

### Risk 3: Tests break unexpectedly

**Likelihood**: Low (only 2 test files use summary())  
**Impact**: Medium (blocks progress)  
**Mitigation**: Thorough local testing before commit

---

## Success Criteria

**Code:**
- [ ] Zero references to `LogLevel.SUMMARY` in `src/`
- [ ] Zero references to `LogConfig.summary()` in `src/` or `tests/`
- [ ] All 78 tests pass
- [ ] No linting errors

**Documentation:**
- [ ] All log level references updated
- [ ] CHANGELOG entry added
- [ ] Deprecation notices in performance docs

**Performance:**
- [ ] Benchmarks match previous standard baseline (±1%)
- [ ] No unexpected slowdowns

**User Experience:**
- [ ] Clear error messages for invalid log levels
- [ ] Migration path documented
- [ ] Default behavior remains sensible (standard logging)

---

## Post-Removal Benefits

1. **Simplified architecture**: 2 log levels instead of 3
2. **Reduced cognitive load**: No decision about "which logging level?"
3. **Better defaults**: Comprehensive logging by default
4. **Easier maintenance**: Fewer code paths to test
5. **Clearer purpose**: STANDARD (production) vs DEBUG (troubleshooting)
6. **Aligned with values**: Enforces comprehensive telemetry for pedagogy/research

---

## Related Documents

- [Performance Baseline with Logging](performance_baseline_phase1_with_logging.md)
- [Performance Comparison: Logging Impact](performance_comparison_logging.md)
- [Telemetry Config Source](../src/telemetry/config.py)
- [CHANGELOG](../CHANGELOG.md)

