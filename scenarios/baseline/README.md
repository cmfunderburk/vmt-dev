# Baseline Scenarios for VMT

This directory contains minimal test scenarios used to establish baseline behavioral characteristics of the VMT system before implementing alternative protocols.

## Purpose

These scenarios serve as:
1. **Behavioral baseline** - Document current system behavior
2. **Regression tests** - Verify no breaking changes during protocol development
3. **Comparison reference** - Baseline for evaluating new protocols in Stage 2+

## Scenarios

### baseline_2agent_simple.yaml
- **Agents**: 2
- **Grid**: 5x5
- **Endowments**: Complementary (10A,2B) and (2A,10B)
- **Utilities**: Identical CES (rho=0.5)
- **Purpose**: Simplest bilateral exchange case
- **Expected**: ~4 trades, quick convergence

### baseline_4agent_edgeworth.yaml
- **Agents**: 4
- **Grid**: 8x8
- **Endowments**: Two types - A-rich (8A,3B) x2, B-rich (3A,8B) x2
- **Utilities**: Identical CES (rho=0.5)
- **Purpose**: Classic Edgeworth box dynamics with spatial friction
- **Expected**: Multiple trades, type-based clustering

### baseline_10agent_mixed.yaml
- **Agents**: 10
- **Grid**: 12x12
- **Endowments**: Heterogeneous (5-15 range)
- **Utilities**: Mixed - 50% CES, 30% Linear, 20% Quadratic
- **Purpose**: Heterogeneous preferences, emergent price discovery
- **Expected**: Varied trade volumes, spatial patterns

### baseline_20agent_symmetric.yaml
- **Agents**: 20
- **Grid**: 15x15
- **Endowments**: All identical (10A, 10B)
- **Utilities**: Identical CES (rho=0.5, wA=0.5, wB=0.5)
- **Purpose**: Edge case - no gains from trade (null hypothesis)
- **Expected**: Zero trades (validates surplus detection)

### baseline_50agent_market.yaml
- **Agents**: 50
- **Grid**: 20x20
- **Endowments**: Bimodal - 25 A-rich (15A,5B), 25 B-rich (5A,15B)
- **Utilities**: Identical CES (rho=0.5)
- **Purpose**: Larger-scale market formation, spatial clustering
- **Expected**: High trade volume (~120+), price convergence

## Analysis

Run the analysis script to generate baseline metrics:

```bash
python scripts/analyze_baseline.py
```

This generates:
- Telemetry databases in `logs/baseline/` (10 seeds per scenario)
- Analysis report in `docs/baseline_behavior_report.md`

## Key Findings (Stage 0)

From 50 simulation runs (10 seeds x 5 scenarios):

- **Deterministic**: Same seed produces identical results
- **Surplus detection**: Symmetric scenario validates that agents only trade when mutually beneficial
- **Trade volume**: Scales sub-linearly with agent count (except for bimodal distributions)
- **Price convergence**: Occurs quickly in large homogeneous markets (50-agent scenario)
- **Heterogeneity**: Mixed utilities increase price variance but don't prevent trading

## Usage

These scenarios are designed for:
1. **Protocol comparison** (Stage 2): Run new protocols on these scenarios and compare metrics
2. **Regression testing**: Verify behavior remains consistent after code changes
3. **Performance benchmarks**: Track simulation runtime as codebase evolves
4. **Research**: Minimal reproducible examples for documentation

