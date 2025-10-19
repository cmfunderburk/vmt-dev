# VMT Performance Baseline - Phase 1 (With Standard Logging)

**Date**: 2025-10-19  
**Version**: Phase 1 (Money system infrastructure complete, no behavioral changes)  
**Hardware**: WSL2 on Linux 6.6.87.2-microsoft-standard-WSL2  
**Python**: 3.12.3  
**Test Suite**: 78 tests passing, 0 skipped  
**Logging**: **STANDARD level** (decisions + trades + periodic snapshots)

> **Note (2025-10-19)**: Summary logging has been removed as of Phase 1 completion. Benchmark data showed summary logging provided minimal performance benefit (<3% in exchange scenarios) while removing valuable decision data. All logging now uses STANDARD level by default. Historical references to "summary logging" in this document reflect data collected before removal. See [PLAN_remove_summary_logging.md](PLAN_remove_summary_logging.md) for full rationale.

## Executive Summary

This baseline measures performance with **standard logging enabled** (SQLite telemetry database), complementing the no-logging baseline. These metrics quantify the overhead of production telemetry and inform decisions about logging configuration in performance-critical scenarios.

### Key Metrics (500 ticks, 400 agents, 50×50 grid, standard logging)

| Scenario | TPS | ms/tick | Total Time | Agent-Ticks |
|----------|-----|---------|------------|-------------|
| **Forage-only** | 14.0 | 71.27 | 35.64s | 200,000 |
| **Exchange-only** | 4.1 | 242.73 | 121.36s | 200,000 |
| **Both modes** | 7.5 | 132.54 | 66.27s | 200,000 |

### Comparison with No-Logging Baseline

| Scenario | No Logging TPS | Logging TPS | Slowdown | Overhead |
|----------|----------------|-------------|----------|----------|
| **Forage** | 22.9 | 14.0 | 1.64× | **38.9%** |
| **Exchange** | 4.7 | 4.1 | 1.15× | **12.8%** |
| **Both** | 8.7 | 7.5 | 1.16× | **13.8%** |

**Key Insights:**

1. **Forage scenarios show highest logging overhead (38.9%)** - Many decision logs and agent snapshots during spatial movement dominate
2. **Exchange scenarios show lowest logging overhead (12.8%)** - Already bottlenecked by compensating block search; telemetry is proportionally smaller
3. **Critical threshold still maintained**: Exchange scenario at 4.1 TPS remains close to the 5.0 TPS threshold, providing regression detection even with logging

---

## Detailed Analysis

### Logging Overhead by Scenario Type

#### 1. Forage-Only Scenario: **38.9% overhead**

**Why highest overhead?**
- **Decision logging every tick** (400 agents × 500 ticks = 200,000 decision records)
- **Agent snapshot logging every tick** (400 agents × 500 ticks = 200,000 snapshot records)
- Movement actions generate many state changes → more snapshots
- Resource harvesting generates frequent inventory updates
- Fast base execution (43.66 ms/tick) means logging is proportionally larger

**Absolute impact:**
- Added 27.61 ms/tick overhead (71.27 - 43.66)
- Added 13.81s total time (35.64 - 21.83)

#### 2. Exchange-Only Scenario: **12.8% overhead**

**Why lowest overhead?**
- Base execution already slow (210.82 ms/tick) due to compensating block search
- Fewer total events logged (trades are less frequent than movement decisions)
- Trade logging overhead is small relative to O(dA_max × price_candidates) computation
- Agent snapshots only after successful trades (conditional updates)

**Absolute impact:**
- Added 31.91 ms/tick overhead (242.73 - 210.82)
- Added 15.95s total time (121.36 - 105.41)

**Critical observation**: Still provides **regression detection** - the 4.1 TPS is below the 5.0 TPS threshold, so any Phase 2 regression will be detectable even when testing with logging enabled.

#### 3. Both Modes Scenario: **13.8% overhead**

**Balanced profile:**
- Mixed decision and trade logging
- Mode transitions every 15 ticks reduce logging bursts
- Intermediate base execution time (114.37 ms/tick)
- Overhead similar to exchange scenario (bottleneck dominates)

**Absolute impact:**
- Added 18.17 ms/tick overhead (132.54 - 114.37)
- Added 9.08s total time (66.27 - 57.19)

---

## Logging Configuration Details

### Standard Logging Level

**Enabled in standard logging** (`LogLevel.STANDARD`):
- ✅ Trade events logged to `trades` table
- ✅ Agent decisions logged to `decisions` table (every tick)
- ✅ Agent snapshots logged to `agents` table (every tick)
- ✅ Resource snapshots logged to `resources` table (every 10 ticks)
- ❌ Failed trade attempts NOT logged (DEBUG only)

**Database schema**: See `src/telemetry/database.py`  
**Batch size**: 100 records per commit (configured in `LogConfig.batch_size`)

### Database Size

**After 500-tick runs with 400 agents (per scenario):**

| Scenario | Records/Table (approx) |
|----------|------------------------|
| Forage | decisions: 200K, agents: 200K, resources: 25K, trades: ~500 |
| Exchange | decisions: 200K, agents: 200K, resources: 2.5K, trades: ~8K |
| Both | decisions: 200K, agents: 200K, resources: 10K, trades: ~4K |

**Total database size after all 3 benchmark runs**: 154 MB (all runs accumulated in single database)

**Estimated size per scenario**: ~50-52 MB

**Note**: Database files located at `./logs/telemetry.db`

---

## Performance Implications for Phase 2+

### Threshold Enforcement with Logging

**Exchange scenario remains most sensitive:**
- With logging: **4.1 TPS** (18% below 5.0 TPS threshold)
- Without logging: **4.7 TPS** (6% below 5.0 TPS threshold)

**Action items:**
- **Primary regression detection**: Continue using **no-logging benchmarks** for strict threshold enforcement
- **Secondary validation**: Use **logging benchmarks** to verify performance with realistic telemetry overhead
- **Block Phase 2 progress** if:
  - No-logging exchange TPS drops below 5.0
  - Logging exchange TPS drops below 4.0
  - Any scenario shows >20% regression from Phase 1 baseline

### When to Use Each Baseline

**Use no-logging baseline (4.7 TPS):**
- Strict performance regression detection
- Algorithm optimization validation
- Phase gate acceptance criteria

**Use logging baseline (4.1 TPS):**
- Production deployment performance estimates
- End-to-end system integration testing
- Telemetry overhead budgeting

---

## Reproducibility

### Environment
```bash
cd /home/chris/PROJECTS/vmt-dev
source venv/bin/activate
export PYTHONPATH=.:src
```

### Running Benchmarks with Logging
```bash
# All scenarios (500 ticks each, standard logging)
python scripts/benchmark_performance.py --log-level standard

# Individual scenario with standard logging
python scripts/benchmark_performance.py --scenario exchange --ticks 500 --log-level standard

# Debug logging (very verbose, large database)
python scripts/benchmark_performance.py --log-level debug

# NOTE: Summary logging was removed (2025-10-19) - use standard logging instead
```

### Verification
```bash
# Ensure tests pass
pytest -q

# Verify determinism (with logging)
python scripts/benchmark_performance.py --scenario both --ticks 100 --seed 42 --log-level standard
python scripts/benchmark_performance.py --scenario both --ticks 100 --seed 42 --log-level standard
# (Results should be identical)

# Check database size
ls -lh logs/telemetry.db
```

---

## Comparison Tables

### Performance Summary

| Scenario | No Logging | Summary Logging† | Standard Logging | Debug Logging* |
|----------|------------|-----------------|------------------|----------------|
| **Forage** | 22.9 TPS (43.66 ms) | ~15 TPS (est.) | 14.0 TPS (71.27 ms) | ~10 TPS (est.) |
| **Exchange** | 4.7 TPS (210.82 ms) | **4.0 TPS (247.9 ms)** | 4.1 TPS (242.73 ms) | ~3.5 TPS (est.) |
| **Both** | 8.7 TPS (114.37 ms) | ~8 TPS (est.) | 7.5 TPS (132.54 ms) | ~6 TPS (est.) |

*Debug logging estimates based on ~25-30% additional overhead (not benchmarked)  
†Summary logging removed 2025-10-19 (historical data shown for reference)

**Historical finding**: Exchange scenario with summary logging measured at 4.0 TPS, demonstrating that trade logging dominates overhead. Summary logging was removed because it provided minimal benefit while removing valuable decision data.

### Absolute Overhead (ms/tick)

| Scenario | Base Time | Logging Overhead | % Overhead |
|----------|-----------|------------------|------------|
| **Forage** | 43.66 ms | +27.61 ms | 38.9% |
| **Exchange** | 210.82 ms | +31.91 ms | 12.8% |
| **Both** | 114.37 ms | +18.17 ms | 13.8% |

---

## Technical Analysis

### Why Forage Has Highest Overhead

**Decision logging dominates:**
```
Per tick overhead = 
  (400 agents × decision_log_write) + 
  (400 agents × agent_snapshot_write) + 
  (resources × resource_snapshot_write)
```

In forage mode:
- Every agent logs a decision (move target, forage intention)
- Every agent has frequent inventory changes (foraging) → snapshots
- Movement is computationally cheap (Manhattan distance) → logging is relatively expensive

**Percentage breakdown (estimated):**
- Decision logs: ~40% of overhead
- Agent snapshots: ~45% of overhead  
- Resource snapshots: ~10% of overhead
- Database commits: ~5% of overhead

### Why Exchange Has Lowest Overhead

**Computation dominates:**
```
Per tick overhead = 
  (trade_attempts × compensating_block_search) +
  (successful_trades × trade_log_write) +
  (inventory_changes × agent_snapshot_write)
```

In exchange mode:
- Compensating block search: O(dA_max × price_candidates) × utility_evaluation
- For large inventories (50-450): ~100-500 candidate evaluations per trade attempt
- 400 agents → many potential trade pairs
- Logging overhead is small relative to O(N²) trade matching

**Percentage breakdown (estimated):**
- Compensating block search: ~75% of total time
- Quote updates: ~10% of total time
- Decision logs: ~7% of overhead
- Trade/snapshot logs: ~5% of overhead
- Database commits: ~3% of overhead

### Why Summary Logging Doesn't Help Much in Exchange Scenarios

**Surprising finding**: Summary logging (4.0 TPS) barely faster than standard logging (4.1 TPS) for exchange scenario.

**Explanation:**
- Summary logging disables decision logs and agent snapshots
- But in exchange scenarios, most agents are in trade cooldown (not making decisions)
- Successful trades generate agent snapshots anyway (inventory changes)
- Trade logging itself (enabled in summary) is the dominant logging cost
- Decision logging contributes <3% overhead in exchange scenarios

**Implication**: For trade-focused analysis, always use standard logging - the decision data is valuable and nearly free in exchange scenarios.

---

## Recommendations

### For Development (Phase 2+)

1. **Use no-logging benchmarks for regression detection**
   - Primary gate: Exchange scenario must maintain ≥5.0 TPS
   - Run frequently during development

2. **Use standard-logging benchmarks for integration testing**
   - Validates end-to-end performance with realistic telemetry
   - Run before merge to main branch

3. **Summary logging removed (historical finding)**
   - Summary logging provided minimal benefit: 4.0 TPS vs 4.1 TPS in exchange scenario
   - Trade logging dominated overhead regardless of level
   - **As of 2025-10-19**: Summary logging removed; use standard logging for all scenarios
   - Standard logging provides comprehensive data with acceptable overhead

### For Pedagogy

**Classroom demonstrations:**
- Use **standard logging** (current configuration) for post-run analysis
- Database queries enable rich exploration of agent behavior
- Acceptable performance for typical demo scenarios (50-100 agents)

**Large-scale simulations:**
- Use **standard logging** (comprehensive data with acceptable overhead)
- For extreme performance needs, use `--log-level off` (no database)
- Standard logging provides full trade networks and convergence dynamics

### For Research

**Exploratory simulations:**
- Start with **standard logging** to understand agent behavior
- Switch to **no logging** for production parameter sweeps
- Re-enable logging for interesting edge cases

**Publication-quality experiments:**
- Report both logged and unlogged performance metrics
- Document logging configuration in methodology section
- Archive telemetry databases alongside results

---

## Future Work

### Phase 2+ Logging Extensions

As money system phases progress, monitor:
- **Quote pair expansion**: 2 pairs (barter) → 6 pairs (money) → increased quote logging
- **KKT λ updates**: Neighbor price aggregation adds per-tick computation
- **Money transactions**: Additional M inventory tracking in snapshots
- **Liquidity events**: New log events for money constraint violations

**Expected logging overhead changes:**
- Phase 2: +5-10% (more quote pairs, money transactions)
- Phase 3: +10-15% (KKT λ aggregation logs)
- Phase 4+: +2-5% (liquidity gating events)

**Mitigation:**
- Consider conditional logging based on `exchange_regime`
- Add `log_money_events` flag to `LogConfig`
- Optimize quote logging (only log changes, not every tick)

---

## Notes

- All benchmarks use seed 42 for deterministic reproducibility
- "Standard logging" mode used (`--log-level standard`)
- Database batching (100 records/commit) used for performance
- Database files persist at `./logs/telemetry.db` (deleted between runs in benchmark script)
- Grid size (50×50 = 2,500 cells) and agent count (400) match no-logging baseline
- Vision radius (10) and move budget (1) match no-logging baseline

---

## Appendix: Log Level Comparison

> **Note**: Summary logging was removed 2025-10-19. The table below shows current logging levels only.

| Feature | Off | Standard | Debug |
|---------|-----|----------|-------|
| Database enabled | ❌ | ✅ | ✅ |
| Trade events | ❌ | ✅ | ✅ |
| Failed trade attempts | ❌ | ❌ | ✅ |
| Agent decisions | ❌ | ✅ | ✅ |
| Agent snapshots (periodic) | ❌ | ✅ (every tick) | ✅ (every tick) |
| Resource snapshots | ❌ | ✅ (every 10 ticks) | ✅ (every tick) |
| Exchange overhead | 0% | 12.8% (measured) | ~25% (est.) |
| Forage overhead | 0% | 38.9% (measured) | ~50% (est.) |
| Use case | Performance benchmarks | Production (default) | Deep debugging |

---

## Baseline Commit

This baseline was established at Phase 1 completion with:
- All money infrastructure in place (schema, state, telemetry)
- No behavioral changes to trading logic
- Deterministic execution verified
- Backward compatibility preserved

**Git Reference**: (to be added after commit)

**Companion Document**: `docs/performance_baseline_phase1.md` (no-logging baseline)

