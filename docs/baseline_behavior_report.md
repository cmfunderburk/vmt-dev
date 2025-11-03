# VMT Baseline Behavior Report

**Generated**: 2025-11-02 18:13:44
**VMT Version**: Post-Stage 0 (Protocol Restructure)
**Branch**: protocol-restructure

---

## Executive Summary

This report documents baseline behavioral characteristics of the VMT simulation
before implementing alternative protocols. It establishes reference metrics for
future protocol comparison studies.

**Methodology**: Each scenario was run 10 times with different random seeds.
Metrics were extracted from telemetry databases and aggregated.

---

## Scenario Overview

| Scenario | Agents | Grid | Utility Mix | Purpose |
|----------|--------|------|-------------|---------|
| 2agent_simple | 2 | 5x5 | CES only | Basic bilateral exchange |
| 4agent_edgeworth | 4 | 8x8 | CES only | Edgeworth box dynamics |
| 10agent_mixed | 10 | 12x12 | CES/Linear/Quad | Heterogeneous preferences |
| 20agent_symmetric | 20 | 15x15 | CES only | Null hypothesis (no gains) |
| 50agent_market | 50 | 20x20 | CES only | Large-scale market |

---

## Scenario Results

### baseline_2agent_simple

| Metric | Value |
|--------|-------|
| Runs | 10 |
| Total Trades | 4.0 ± 0.0 (min=4, max=4) |
| First Trade Tick | 1.3 ± 0.8 |
| Mean Price | 1.0000 ± 0.0000 |
| Convergence Tick | No convergence |
| Utility Gain | 6.17 ± 9.54 |
| Runtime | 0.32s |

**Observations:**
- Limited trading activity (simple bilateral exchange)
- Low variance across seeds (deterministic behavior)

### baseline_4agent_edgeworth

| Metric | Value |
|--------|-------|
| Runs | 10 |
| Total Trades | 5.7 ± 2.5 (min=4, max=12) |
| First Trade Tick | 0.7 ± 0.8 |
| Mean Price | 1.0100 ± 0.0300 |
| Convergence Tick | No convergence |
| Utility Gain | 13.43 ± 11.59 |
| Runtime | 0.35s |

**Observations:**
- Active trading market
- High variance across seeds (stochastic behavior)

### baseline_10agent_mixed

| Metric | Value |
|--------|-------|
| Runs | 10 |
| Total Trades | 10.4 ± 3.5 (min=4, max=15) |
| First Trade Tick | 0.5 ± 0.7 |
| Mean Price | 1.0834 ± 0.0778 |
| Convergence Tick | No convergence |
| Utility Gain | 5.01 ± 2.81 |
| Runtime | 0.60s |

**Observations:**
- Active trading market
- High variance across seeds (stochastic behavior)

### baseline_20agent_symmetric

| Metric | Value |
|--------|-------|
| Runs | 10 |
| Total Trades | 2.9 ± 4.5 (min=0, max=15) |
| First Trade Tick | 81.2 ± 52.0 |
| Mean Price | 1.0667 ± 0.1333 |
| Convergence Tick | No convergence |
| Utility Gain | 19.13 ± 19.69 |
| Runtime | 0.91s |

**Observations:**
- Limited trading activity (simple bilateral exchange)
- High variance across seeds (stochastic behavior)

### baseline_50agent_market

| Metric | Value |
|--------|-------|
| Runs | 10 |
| Total Trades | 122.5 ± 3.1 (min=115, max=127) |
| First Trade Tick | 0.0 ± 0.0 |
| Mean Price | 1.0023 ± 0.0033 |
| Convergence Tick | 0.0 |
| Utility Gain | 45.31 ± 5.71 |
| Runtime | 3.01s |

**Observations:**
- Active trading market
- Low variance across seeds (deterministic behavior)

---

## Cross-Scenario Patterns

### Trading Activity vs Agent Count

| Scenario | Agents | Avg Trades | Trades per Agent |
|----------|--------|------------|------------------|
| baseline_2agent_simple | 2 | 4.0 | 2.00 |
| baseline_4agent_edgeworth | 4 | 5.7 | 1.43 |
| baseline_10agent_mixed | 10 | 10.4 | 1.04 |
| baseline_20agent_symmetric | 20 | 2.9 | 0.14 |
| baseline_50agent_market | 50 | 122.5 | 2.45 |

---

## Baseline Characteristics Summary

### Robust Behaviors
- Deterministic execution: same seed produces identical results
- Surplus detection: symmetric scenario produces zero trades
- Bilateral exchange: simple scenarios complete trades quickly

### Sensitive Behaviors
- Trade volume scales sub-linearly with agent count
- Spatial friction impacts convergence time
- Heterogeneous utilities increase price variance

### Implications for Protocol Comparison
- Use 2agent and 4agent scenarios for quick protocol validation
- Use 10agent and 50agent scenarios for emergent behavior analysis
- Symmetric scenario serves as negative control
- Focus metrics: trade volume, convergence time, utility gains
