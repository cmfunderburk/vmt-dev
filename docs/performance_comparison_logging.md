# VMT Performance: Logging Impact Comparison

**Date**: 2025-10-19  
**Phase**: Phase 1 (Money infrastructure, no behavioral changes)  
**Hardware**: WSL2 on Linux 6.6.87.2-microsoft-standard-WSL2  
**Configuration**: 500 ticks, 400 agents, 50×50 grid, seed 42

> **Note (2025-10-19)**: Summary logging has been removed. Benchmark data showed it provided minimal performance benefit (<3% in exchange scenarios) while removing valuable decision data. All logging now uses STANDARD level by default. Historical summary logging data is preserved below for reference. See [PLAN_remove_summary_logging.md](PLAN_remove_summary_logging.md) for full rationale.

## Quick Reference

### Performance by Logging Level

| Scenario | No Logging | Summary† | Standard | Slowdown (Standard) |
|----------|------------|---------|----------|---------------------|
| **Forage** | 22.9 TPS | ~15 TPS* | 14.0 TPS | **1.64× / 38.9%** |
| **Exchange** | 4.7 TPS | 4.0 TPS | 4.1 TPS | **1.15× / 12.8%** |
| **Both** | 8.7 TPS | ~8 TPS* | 7.5 TPS | **1.16× / 13.8%** |

*Estimated  
†Summary logging removed 2025-10-19 (historical data)

### Key Findings

1. **Forage scenarios show highest logging overhead (38.9%)**
   - Decision logging every tick for 400 agents
   - Frequent inventory changes from harvesting
   - Movement is computationally cheap → logging dominates

2. **Exchange scenarios show lowest logging overhead (12.8%)**
   - Already bottlenecked by compensating block search
   - Logging is small relative to O(N²) trade matching
   - Trade computation: ~210 ms/tick, logging adds only ~32 ms

3. **Summary logging removed (historical finding)**
   - Historical data: Summary 4.0 TPS vs Standard 4.1 TPS (only 2.5% difference)
   - Trade logging dominated overhead regardless of level
   - **Removed 2025-10-19**: Minimal benefit didn't justify losing decision data

## Detailed Metrics

### Forage-Only Scenario

| Metric | No Logging | Standard Logging | Difference |
|--------|------------|------------------|------------|
| TPS | 22.9 | 14.0 | -8.9 TPS (-38.9%) |
| ms/tick | 43.66 | 71.27 | +27.61 ms (+63.2%) |
| Total time (500 ticks) | 21.83s | 35.64s | +13.81s |

**Analysis**: Decision and snapshot logging dominate. Every agent logs movement decisions and inventory changes each tick.

### Exchange-Only Scenario

| Metric | No Logging | Summary Logging | Standard Logging | 
|--------|------------|-----------------|------------------|
| TPS | 4.7 | 4.0 | 4.1 |
| ms/tick | 210.82 | 247.90 | 242.73 |
| Total time (500 ticks) | 105.41s | 123.93s | 121.36s |
| Overhead | 0% | +14.9% | +12.8% |

**Analysis**: 
- Compensating block search dominates (210 ms base)
- Summary logging adds 37 ms (trade logging)
- Standard logging adds only 32 ms (less than summary!)
- Decision logs nearly free because most agents in trade cooldown

**Surprising result**: Standard logging actually faster than summary logging for exchange scenarios.

### Both Modes Scenario

| Metric | No Logging | Standard Logging | Difference |
|--------|------------|------------------|------------|
| TPS | 8.7 | 7.5 | -1.2 TPS (-13.8%) |
| ms/tick | 114.37 | 132.54 | +18.17 ms (+15.9%) |
| Total time (500 ticks) | 57.19s | 66.27s | +9.08s |

**Analysis**: Balanced overhead profile. Mode transitions reduce logging bursts.

## Overhead Breakdown

### What Gets Logged at Each Level

| Feature | Off | Summary | Standard |
|---------|-----|---------|----------|
| Trade events | ❌ | ✅ | ✅ |
| Agent decisions | ❌ | ❌ | ✅ |
| Agent snapshots | ❌ | ❌ | ✅ (every tick) |
| Resource snapshots | ❌ | ❌ | ✅ (every 10 ticks) |
| Failed trade attempts | ❌ | ❌ | ❌ |

### Measured Overhead by Scenario Type

| Logging Level | Forage | Exchange | Both |
|---------------|--------|----------|------|
| **Summary** | ~10% (est.) | **14.9%** | ~8% (est.) |
| **Standard** | **38.9%** | **12.8%** | **13.8%** |

## Recommendations

### When to Use Each Configuration

**No logging (`--log-level off`):**
- ✅ Performance regression testing
- ✅ Algorithm optimization validation
- ✅ Phase gate acceptance criteria
- ✅ Production parameter sweeps

**Summary logging:**
- ❌ REMOVED (2025-10-19) - Use standard logging instead
- Historical: Provided minimal benefit (<3% in critical scenarios)

**Standard logging (`--log-level standard`):**
- ✅ Development and debugging
- ✅ Pedagogical demonstrations
- ✅ Trade behavior analysis (decision data nearly free)
- ✅ Integration testing
- ✅ End-to-end system validation

**Debug logging (`--log-level debug`):**
- ✅ Investigating failed trades
- ✅ Deep behavioral debugging
- ⚠️ Creates very large databases (~25% additional overhead)

### Specific Use Cases

**For Phase 2 development:**
- Primary benchmarks: no logging (strict threshold enforcement)
- Secondary validation: standard logging (realistic overhead)
- Block progress if exchange TPS drops below 5.0 (no logging) or 4.0 (standard logging)

**For classroom demos:**
- Use standard logging (decision data enriches analysis)
- Overhead acceptable for typical demo scenarios (50-100 agents)
- Database enables rich post-run exploration

**For research:**
- Exploratory: standard logging (understand behavior)
- Production sweeps: no logging (maximize throughput)
- Publication: report both logged and unlogged metrics

## Database Storage

**Per-scenario storage (500 ticks, 400 agents):**
- Forage: ~50 MB (200K decisions, 200K agent snapshots, 25K resource snapshots)
- Exchange: ~52 MB (200K decisions, 200K agent snapshots, 8K trades)
- Both: ~51 MB (200K decisions, 200K agent snapshots, 4K trades)

**All 3 scenarios**: 154 MB total (accumulated in single database)

## Phase 2 Implications

### Threshold Enforcement

**Exchange scenario remains most sensitive:**
- No logging: 4.7 TPS (6% above 5.0 threshold)
- Standard logging: 4.1 TPS (18% below 5.0 threshold)

**Action thresholds:**
- ❌ Block if no-logging exchange drops below 5.0 TPS
- ⚠️ Investigate if standard-logging exchange drops below 4.0 TPS
- ⚠️ Investigate if any scenario regresses >10% from Phase 1

### Expected Changes

**Phase 2+ logging extensions:**
- Quote pairs expand: 2 (barter) → 6 (money)
- Money transaction logging
- Additional M inventory tracking

**Estimated additional overhead:**
- Phase 2: +5-10% (more quote pairs, money transactions)
- Phase 3: +10-15% (KKT λ aggregation logs)

## Reproducibility

```bash
# Environment setup
cd /home/chris/PROJECTS/vmt-dev
source venv/bin/activate
export PYTHONPATH=.:src

# No logging (baseline)
python scripts/benchmark_performance.py --log-level off

# Standard logging (default)
python scripts/benchmark_performance.py --log-level standard

# Debug logging (failed trade attempts)
python scripts/benchmark_performance.py --log-level debug

# Individual scenario
python scripts/benchmark_performance.py --scenario exchange --log-level standard
```

## Related Documents

- **No-logging baseline**: [docs/performance_baseline_phase1.md](mdc:docs/performance_baseline_phase1.md)
- **Standard-logging baseline**: [docs/performance_baseline_phase1_with_logging.md](mdc:docs/performance_baseline_phase1_with_logging.md)
- **Telemetry configuration**: [src/telemetry/config.py](mdc:src/telemetry/config.py)
- **Database schema**: [src/telemetry/database.py](mdc:src/telemetry/database.py)

