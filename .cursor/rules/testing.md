# Testing Conventions

VMT has 316+ tests covering all systems. Follow these patterns for new tests.

## Test Organization

```
tests/
├── test_<feature>.py        # Feature-specific tests
├── test_<system>_integration.py  # Integration tests
└── helpers/                 # Shared test utilities
    ├── scenarios.py         # Test scenario builders
    ├── assertions.py        # Custom assertions
    └── fixtures.py          # Common fixtures
```

## Test Categories

### Unit Tests

Test individual components in isolation:

```python
def test_myopic_search_protocol():
    """Test myopic search target selection logic."""
    # Arrange: Create minimal test context
    world_view = create_world_view(
        agents={
            1: AgentView(id=1, pos=(5, 5), inventory=(10, 10)),
            2: AgentView(id=2, pos=(7, 7), inventory=(5, 15)),
        },
        resources={(8, 8): ResourceView(amount=5, type='A')}
    )
    context = create_protocol_context(agent_id=1, world_view=world_view)
    
    # Act: Execute protocol
    protocol = MyopicSearchProtocol()
    effects = protocol.execute(context)
    
    # Assert: Check effects
    assert len(effects) == 1
    assert isinstance(effects[0], SetTarget)
    assert effects[0].target_pos == (7, 7)  # Should target agent 2
```

### Integration Tests

Test complete simulation flows:

```python
def test_trade_cooldown_prevents_retargeting():
    """Verify trade cooldown prevents immediate retargeting."""
    scenario = load_scenario("scenarios/test/test_trade_cooldown.yaml")
    sim = Simulation(scenario, seed=42, log_config=LogConfig.standard())
    sim.run(max_ticks=20)
    
    # Check telemetry for expected cooldown behavior
    assert any(
        decision.is_paired == False 
        for decision in sim.telemetry._decision_buffer
    )
```

### Determinism Tests

**Required for every feature**:

```python
def test_my_feature_determinism():
    """Verify my_feature produces identical results with same seed."""
    scenario_path = "scenarios/test/test_my_feature.yaml"
    
    # Run 1
    sim1 = Simulation(load_scenario(scenario_path), seed=42)
    sim1.run(max_ticks=20)
    state1 = [(a.inventory.A, a.inventory.B, a.pos) for a in sim1.agents]
    
    # Run 2 (same seed)
    sim2 = Simulation(load_scenario(scenario_path), seed=42)
    sim2.run(max_ticks=20)
    state2 = [(a.inventory.A, a.inventory.B, a.pos) for a in sim2.agents]
    
    # Must be identical
    assert state2 == state1
```

### Performance Tests

Verify complexity bounds:

```python
def test_decision_phase_performance():
    """Verify decision phase scales linearly with agents."""
    import time
    
    sizes = [50, 100, 200]
    times = []
    
    for n in sizes:
        scenario = create_test_scenario(num_agents=n)
        sim = Simulation(scenario, seed=42)
        
        start = time.perf_counter()
        sim.run(max_ticks=10)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    # Should be roughly linear (not quadratic)
    ratio = times[2] / times[0]  # 4x agents
    assert ratio < 6  # Allow overhead, but not quadratic (would be ~16x)
```

## Helper Utilities

### Creating Test Scenarios

```python
from tests.helpers.scenarios import create_minimal_scenario

def test_with_custom_scenario():
    scenario = create_minimal_scenario(
        num_agents=5,
        grid_size=20,
        utility_type='ces',
        utility_params={'rho': -0.5, 'wA': 1.0, 'wB': 1.0}
    )
    sim = Simulation(scenario, seed=42)
    sim.run(max_ticks=10)
```

### Custom Assertions

```python
from tests.helpers.assertions import assert_trade_valid

def test_trade_execution():
    # ... run simulation ...
    trades = sim.telemetry.recent_trades_for_renderer
    
    for trade in trades:
        assert_trade_valid(trade, sim.agents)  # Checks inventory constraints
```

## Test Naming

**Pattern**: `test_<component>_<behavior>_<condition>`

Good names:
- `test_myopic_search_selects_highest_surplus_neighbor()`
- `test_pairing_breaks_on_failed_trade()`
- `test_resource_claiming_prevents_clustering()`

Bad names:
- `test_1()` - Not descriptive
- `test_everything()` - Too broad
- `test_search()` - Missing specifics

## Running Tests

```bash
# Full suite
pytest

# Specific category
pytest tests/test_protocol_*.py

# Specific test
pytest tests/test_myopic_search.py::test_selects_highest_surplus

# With coverage
pytest --cov=src --cov-report=html

# Verbose with output
pytest -v -s tests/test_my_feature.py
```

## Pytest Configuration

See `pytest.ini`:
```ini
[pytest]
pythonpath = . src
```

Tests can import directly:
```python
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario
from telemetry.config import LogConfig
```

## Test Data

**Test scenarios**: `scenarios/test/`
- `test_ces.yaml`, `test_linear.yaml`, etc. - Utility function tests
- `test_mixed.yaml` - Multi-utility population
- `phase1_complete.yaml` - Full feature test

**Use committed scenarios for regression tests**, create minimal scenarios in test code for unit tests.

## Common Test Patterns

### Testing Trade Outcomes

```python
def test_split_difference_equal_surplus():
    scenario = load_scenario("scenarios/test/test_split_difference.yaml")
    sim = Simulation(scenario, seed=42)
    sim.run(max_ticks=10)
    
    trades = sim.telemetry.recent_trades_for_renderer
    for trade in trades:
        # Split-the-difference should give roughly equal surplus
        assert abs(trade['surplus_i'] - trade['surplus_j']) < 0.1
```

### Testing Spatial Behavior

```python
def test_agents_move_toward_targets():
    scenario = create_minimal_scenario(num_agents=2)
    sim = Simulation(scenario, seed=42)
    
    # Record initial positions
    initial_distance = manhattan_distance(
        sim.agents[0].pos, sim.agents[1].pos
    )
    
    sim.run(max_ticks=5)
    
    # Distance should decrease (agents moving toward each other)
    final_distance = manhattan_distance(
        sim.agents[0].pos, sim.agents[1].pos
    )
    assert final_distance < initial_distance
```

### Testing Telemetry

```python
def test_telemetry_logs_preferences():
    scenario = load_scenario("scenarios/test/test_preferences.yaml")
    sim = Simulation(scenario, seed=42, log_config=LogConfig.debug())
    sim.run(max_ticks=5)
    
    # Check database directly
    conn = sqlite3.connect(sim.telemetry.db.db_path)
    cursor = conn.execute(
        "SELECT COUNT(*) FROM preferences WHERE run_id = ?",
        (sim.telemetry.run_id,)
    )
    preference_count = cursor.fetchone()[0]
    
    assert preference_count > 0
```

## Debugging Failed Tests

1. **Add verbose output**: `pytest -v -s`
2. **Use breakpoints**: `import pdb; pdb.set_trace()`
3. **Check telemetry**: Examine `./logs/telemetry.db` after test
4. **Enable debug logging**: Use `LogConfig.debug()` in test
5. **Compare seeds**: Run same seed multiple times to isolate non-determinism

## Continuous Integration

Tests run automatically on:
- Every commit (local pre-commit hook)
- Every pull request (GitHub Actions)
- Nightly builds (full suite with coverage)

**All tests must pass before merging.**

