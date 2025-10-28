# Testing and Validation Strategy

**Document Status:** Test Planning  
**Version:** 1.0  
**Created:** 2025-01-27  
**Purpose:** Comprehensive testing approach for architectural refactoring  

---

## Overview

This document defines the testing and validation strategy for the protocol modularization and utility refactoring initiatives. The goal is to ensure zero behavioral regression while enabling new functionality.

---

## Testing Principles

### Core Requirements
1. **Determinism:** Same input → same output, always
2. **Backward Compatibility:** Existing scenarios produce identical results
3. **Performance:** <10% regression from baseline
4. **Coverage:** >90% for new protocol code
5. **Economic Validity:** Protocols satisfy theoretical properties

### Testing Levels
1. **Unit Tests:** Individual methods and functions
2. **Integration Tests:** Protocol interactions
3. **System Tests:** Full simulation runs
4. **Property Tests:** Economic invariants
5. **Performance Tests:** Speed and memory benchmarks

---

## Phase-Specific Test Plans

### Phase 1: Legacy Adapter Testing

**Goal:** Prove behavioral equivalence

#### 1.1 Telemetry Equivalence Tests

```python
class TestLegacyAdapterEquivalence:
    """Verify legacy adapters produce identical behavior."""
    
    def test_telemetry_identical(self):
        """Compare telemetry with and without protocols."""
        
        # Run without protocols (baseline)
        sim_old = Simulation(scenario, seed=42)
        sim_old.run(max_ticks=100)
        telemetry_old = extract_telemetry(sim_old)
        
        # Run with legacy protocols
        sim_new = Simulation(
            scenario, seed=42,
            search_protocol=LegacySearchProtocol(),
            matching_protocol=LegacyMatchingProtocol(),
            bargaining_protocol=LegacyBargainingProtocol()
        )
        sim_new.run(max_ticks=100)
        telemetry_new = extract_telemetry(sim_new)
        
        # Assert identical
        assert_telemetry_equal(telemetry_old, telemetry_new)
```

#### 1.2 Determinism Verification

```python
def test_deterministic_across_runs():
    """Verify multiple runs produce identical results."""
    
    telemetries = []
    for i in range(10):
        sim = Simulation(scenario, seed=42, protocols=legacy)
        sim.run(max_ticks=100)
        telemetries.append(hash_telemetry(sim))
    
    # All hashes must be identical
    assert len(set(telemetries)) == 1
```

#### 1.3 Test Scenarios

| Scenario | Purpose | Key Metrics |
|----------|---------|-------------|
| three_agent_barter | Basic trade mechanics | Trades, final inventories |
| money_test_basic | Money system | Money flows, prices |
| mixed_regime | All trade types | Pair type distribution |
| mode_toggle | Mode transitions | Pairing persistence |
| large_100_agents | Scale testing | Performance, convergence |

### Phase 2: Alternative Protocol Testing

**Goal:** Validate new protocol behaviors

#### 2.1 Property-Based Tests

```python
class TestMatchingProtocolProperties:
    """Properties all matching protocols must satisfy."""
    
    @given(scenario=scenarios(), seed=integers())
    def test_no_double_pairing(self, scenario, seed):
        """No agent can be in multiple pairs."""
        
        for protocol in all_matching_protocols:
            pairs = protocol.find_matches(preferences, context)
            agents_in_pairs = set()
            
            for a, b in pairs:
                assert a not in agents_in_pairs
                assert b not in agents_in_pairs
                agents_in_pairs.update([a, b])
    
    def test_pairing_symmetry(self):
        """If A paired with B, then B paired with A."""
        
        for pair in pairs:
            assert (pair[1], pair[0]) in reciprocal_pairs
```

#### 2.2 Economic Property Tests

```python
class TestBargainingProperties:
    """Economic properties of bargaining protocols."""
    
    def test_positive_surplus(self, protocol):
        """All trades must have positive surplus."""
        
        trades = protocol.negotiate(pair, world)
        for trade in trades:
            surplus_buyer = compute_delta_u(buyer, trade)
            surplus_seller = compute_delta_u(seller, trade)
            assert surplus_buyer > 0
            assert surplus_seller > 0
    
    def test_pareto_improvement(self, protocol):
        """Trades must be Pareto improvements."""
        
        u_before = (u(buyer.inventory), u(seller.inventory))
        execute_trade(trade)
        u_after = (u(buyer.inventory), u(seller.inventory))
        
        assert u_after[0] >= u_before[0]
        assert u_after[1] >= u_before[1]
        assert u_after != u_before  # Strict improvement
```

#### 2.3 Comparative Tests

```python
def test_greedy_vs_three_pass():
    """Compare matching algorithms."""
    
    # Same scenario, different protocols
    results = {}
    for protocol in [ThreePassMatching(), GreedyMatching()]:
        sim = Simulation(scenario, seed=42, matching=protocol)
        sim.run(100)
        results[protocol.name] = {
            'total_surplus': calculate_total_surplus(sim),
            'pairs_formed': count_pairs(sim),
            'stability': check_stability(sim)
        }
    
    # Greedy should have higher total surplus
    assert results['greedy']['total_surplus'] >= results['three_pass']['total_surplus']
    
    # Three-pass might have more stable pairs
    # Document differences for research
```

### Phase 3: System Integration Testing

#### 3.1 Configuration Tests

```python
def test_yaml_protocol_loading():
    """Verify YAML configuration works."""
    
    yaml_config = """
    protocols:
      search:
        name: "distance_discounted"
        version: "1.0.0"
      matching:
        name: "greedy_surplus"
        version: "1.0.0"
    """
    
    scenario = load_scenario(yaml_config)
    sim = Simulation(scenario)
    
    assert isinstance(sim.search_protocol, DistanceDiscountedSearch)
    assert isinstance(sim.matching_protocol, GreedyMatching)
```

#### 3.2 Multi-tick Protocol Tests

```python
def test_rubinstein_bargaining():
    """Test multi-tick bargaining protocol."""
    
    protocol = RubinsteinBargaining(discount=0.9, max_rounds=10)
    
    # Should take multiple ticks
    tick_outcomes = []
    for tick in range(10):
        effects = protocol.negotiate(pair, world)
        tick_outcomes.append(effects)
        
        if any(isinstance(e, Trade) for e in effects):
            break
    
    # Verify alternating offers
    assert len(tick_outcomes) > 1  # Multi-tick
    assert any(isinstance(e, Trade) for e in flatten(tick_outcomes))
```

---

## Performance Testing

### Baseline Establishment

```python
class PerformanceBenchmark:
    """Establish performance baselines."""
    
    def setup(self):
        self.scenarios = [
            ('small', 'three_agent_barter.yaml'),
            ('medium', 'mixed_regime.yaml'),
            ('large', 'large_100_agents.yaml')
        ]
    
    def benchmark_baseline(self):
        """Run without protocols (current system)."""
        
        results = {}
        for name, scenario_file in self.scenarios:
            scenario = load_scenario(scenario_file)
            
            start = time.perf_counter()
            sim = Simulation(scenario, seed=42)
            sim.run(100)
            duration = time.perf_counter() - start
            
            results[name] = {
                'ticks_per_second': 100 / duration,
                'memory_mb': get_memory_usage()
            }
        
        save_baseline(results)
```

### Performance Regression Tests

```python
def test_performance_regression():
    """Ensure <10% performance loss."""
    
    baseline = load_baseline()
    current = run_benchmark_suite()
    
    for scenario in scenarios:
        tps_baseline = baseline[scenario]['ticks_per_second']
        tps_current = current[scenario]['ticks_per_second']
        
        regression = (tps_baseline - tps_current) / tps_baseline
        assert regression < 0.10, f"{scenario} regressed by {regression:.1%}"
```

### Performance Targets

| Scenario | Agents | Baseline TPS | Target TPS | Max Regression |
|----------|--------|--------------|------------|----------------|
| three_agent | 3 | 485 | 436 | 10% |
| mixed_regime | 20 | 125 | 112 | 10% |
| large | 100 | 12.3 | 11.0 | 10% |

---

## Regression Test Suite

### Critical Scenarios

These scenarios must produce identical results:

1. **scenarios/three_agent_barter.yaml**
   - Tests basic trading
   - Validates pairing logic
   - Checks inventory updates

2. **scenarios/money_test_basic.yaml**
   - Tests money system
   - Validates price calculation
   - Checks money conservation

3. **scenarios/mixed.yaml**
   - Tests all trade types
   - Validates pair type selection
   - Checks tie-breaking

4. **scenarios/mode_toggle_demo.yaml**
   - Tests mode transitions
   - Validates pairing persistence
   - Checks state cleanup

5. **scenarios/resource_claiming_demo.yaml**
   - Tests foraging
   - Validates claiming logic
   - Checks commitment

### Telemetry Comparison Tool

```python
# scripts/compare_telemetry.py

def compare_telemetry(db1_path, db2_path, epsilon=1e-10):
    """Compare two telemetry databases."""
    
    tables_to_compare = [
        'simulation_runs',
        'agent_snapshots',
        'trades',
        'decisions',
        'preferences',
        'pairings'
    ]
    
    differences = []
    
    for table in tables_to_compare:
        rows1 = fetch_table(db1_path, table)
        rows2 = fetch_table(db2_path, table)
        
        if len(rows1) != len(rows2):
            differences.append(f"{table}: row count mismatch")
            continue
        
        for i, (r1, r2) in enumerate(zip(rows1, rows2)):
            diff = compare_rows(r1, r2, epsilon)
            if diff:
                differences.append(f"{table}[{i}]: {diff}")
    
    return differences
```

---

## Test Organization

### Directory Structure

```
tests/
├── test_protocols/
│   ├── test_legacy_adapters.py
│   ├── test_search_protocols.py
│   ├── test_matching_protocols.py
│   ├── test_bargaining_protocols.py
│   ├── test_effect_system.py
│   └── test_protocol_properties.py
├── test_regression/
│   ├── test_telemetry_equivalence.py
│   ├── test_determinism.py
│   └── golden/
│       └── baseline_telemetry.db
├── test_performance/
│   ├── test_benchmarks.py
│   └── baseline_metrics.json
└── test_utilities/
    ├── test_base_extraction.py
    └── test_modularization.py
```

### Test Naming Convention

```python
# Unit tests
def test_<protocol>_<method>_<condition>():
    """Test specific method behavior."""
    pass

# Integration tests
def test_integration_<component1>_<component2>():
    """Test component interactions."""
    pass

# Property tests
def test_property_<property_name>():
    """Test economic/mathematical property."""
    pass

# Regression tests
def test_regression_<scenario>_<metric>():
    """Test for behavioral regression."""
    pass
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Protocol Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run unit tests
      run: pytest tests/test_protocols/ -v
    
    - name: Run regression tests
      run: pytest tests/test_regression/ -v
    
    - name: Run performance tests
      run: pytest tests/test_performance/ --benchmark-only
    
    - name: Check determinism
      run: python scripts/check_determinism.py
    
    - name: Upload telemetry artifacts
      uses: actions/upload-artifact@v2
      with:
        name: telemetry-comparison
        path: logs/
```

---

## Validation Checkpoints

### Phase 1 Checkpoint (Legacy Adapters)
- [ ] All 316+ existing tests pass
- [ ] Telemetry bit-identical for 5 key scenarios
- [ ] 10 deterministic runs produce same hash
- [ ] Performance within 10% of baseline
- [ ] No memory leaks detected

### Phase 2 Checkpoint (Alternative Protocols)
- [ ] Property tests pass for all protocols
- [ ] Economic invariants satisfied
- [ ] Comparative analysis documented
- [ ] Coverage >90% for protocol code
- [ ] Performance benchmarked

### Phase 3 Checkpoint (Full System)
- [ ] YAML configuration tested
- [ ] GUI integration tested
- [ ] Multi-tick protocols tested
- [ ] All regression tests pass
- [ ] Documentation complete

### Final Validation
- [ ] Run 24-hour stress test
- [ ] Test with all scenarios in repo
- [ ] Verify reproducibility across platforms
- [ ] Performance meets requirements
- [ ] No critical bugs in 1 week

---

## Testing Tools

### Required Tools
- **pytest:** Test framework
- **hypothesis:** Property-based testing
- **pytest-benchmark:** Performance testing
- **coverage:** Code coverage analysis
- **mypy:** Type checking
- **ruff:** Linting

### Helper Scripts
- `scripts/compare_telemetry.py` - Compare databases
- `scripts/check_determinism.py` - Verify reproducibility
- `scripts/benchmark_suite.py` - Run performance tests
- `scripts/generate_golden.py` - Create baseline data

---

## Risk Mitigation

### Test Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hidden behavior change | High | High | Comprehensive telemetry comparison |
| Performance degradation | Medium | Medium | Continuous benchmarking |
| Non-determinism | Low | Critical | Multiple run verification |
| Memory leaks | Low | High | Memory profiling |
| Platform differences | Medium | Medium | CI on multiple platforms |

### Rollback Plan

If critical issues found:
1. Revert to commit before protocols
2. Keep protocol infrastructure
3. Fix issues in feature branch
4. Re-attempt integration
5. Smaller incremental changes

---

## Success Criteria

### Minimum Acceptable
- All existing tests pass
- No behavioral regression
- <10% performance loss
- Determinism preserved

### Target
- Above plus:
- 3+ working protocols
- Property tests comprehensive
- Performance improved in some cases
- Documentation complete

### Stretch Goals
- 10+ protocols implemented
- Formal verification
- Performance optimization
- Research paper validation

---

## Summary

This testing strategy ensures:
1. **No regression** in existing functionality
2. **Validated** new protocol behaviors
3. **Performance** within acceptable bounds
4. **Determinism** absolutely preserved
5. **Economic properties** properly tested

**Total Test Development Effort:** 2-3 weeks
**Ongoing Test Maintenance:** 10% of development time

---

**Document Status:** Complete test strategy defined  
**Next Steps:** Implement Phase 1 regression tests  
**Owner:** QA Team / Lead Developer
