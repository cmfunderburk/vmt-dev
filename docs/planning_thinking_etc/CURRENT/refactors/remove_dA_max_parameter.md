# Refactor: Remove `dA_max` Parameter

**Date**: 2025-10-31  
**Status**: PLANNED  
**Rationale**: Eliminate artificial trade size constraint to simplify model validation

---

## Executive Summary

Remove the `dA_max` parameter throughout the VMT codebase. This parameter artificially limits trade size exploration and obscures whether simulation results stem from economic mechanisms or arbitrary search constraints.

**Core Change**: Replace `dA_max`-bounded iterations with natural inventory-based limits.

**Scope**: 
- 4 core system files
- 3 protocol files  
- 2 configuration files
- 15 scenario files
- 3 test helper files
- 6 documentation files

---

## Rationale

### Problems with Current Design

1. **Non-Economic Constraint**: Agents can't explore their full Pareto frontier. A pair with 100 units each is artificially limited to trading 5 units (typical `dA_max` value).

2. **Validation Confusion**: When tests fail or behave unexpectedly, is it because:
   - The utility function is wrong?
   - The bargaining protocol is wrong?
   - We set `dA_max` too low?

3. **Parameter Proliferation**: Every scenario needs tuning of `dA_max` relative to inventory scales. This is pure noise.

4. **False Performance Optimization**: The iteration limit was added for performance, but:
   - Test scenarios have 2-10 agents with inventories of 3-20 units
   - O(20) iterations is trivial
   - Real bottleneck is grid traversal (O(N²) pairs), not trade enumeration

### Design Philosophy

**Before**: "Search up to an arbitrary limit, tune per scenario"  
**After**: "Search up to inventory constraints, let economics constrain behavior"

Natural constraints are sufficient:
- Can't trade more than you have
- Can't buy more than counterparty can pay
- Can't exceed integer arithmetic limits (not a practical concern)

---

## Technical Analysis

### Current Usage Pattern

```python
# Pattern 1: Compensating block search
for dA in range(1, dA_max + 1):
    for price in generate_price_candidates(ask, bid, dA):
        # Test feasibility
        
# Pattern 2: Trade enumeration with inventory cap
for dA in range(1, min(dA_max + 1, agent_i.inventory.A + 1)):
    # Already capped by inventory, dA_max is redundant
```

### Proposed Replacement

```python
# Pattern 1: Use inventory limit directly
max_dA = agent_seller.inventory.A  # Natural constraint
for dA in range(1, max_dA + 1):
    for price in generate_price_candidates(ask, bid, dA):
        # Test feasibility

# Pattern 2: Inventory is the only constraint
for dA in range(1, agent_i.inventory.A + 1):
    # Pure economics, no artificial limits
```

### Barter-Specific Constraints

For A↔B barter between agents i and j where i sells A:

```python
# Maximum dA constrained by:
# 1. Seller's inventory
# 2. Buyer's ability to pay at any valid price
max_dA_inventory = agent_i.A

# For each price p in [ask, bid]:
#   dB = round(p * dA)
#   dA <= agent_j.B / p (approximately)
# Practically, we iterate dA and check dB <= agent_j.B
```

The iteration naturally terminates when `dB > agent_j.B` for all valid prices.

---

## Implementation Plan

### Phase 1: Core Trade Logic (Critical Path)

#### File 1: `src/vmt_engine/systems/matching.py`

**Function**: `find_compensating_block()`

**Current signature** (line 267):
```python
def find_compensating_block(buyer: 'Agent', seller: 'Agent', price: float,
                           dA_max: int, epsilon: float, tick: int = 0,
                           direction: str = "", surplus: float = 0.0,
                           telemetry: Optional['TelemetryManager'] = None)
```

**Changes**:
1. Remove `dA_max` parameter from signature
2. Compute max_dA from seller inventory (line 297):
   ```python
   # OLD
   for dA in range(1, dA_max + 1):
   
   # NEW
   max_dA = seller.inventory.A
   if max_dA <= 0:
       return None  # Seller has nothing to sell
   for dA in range(1, max_dA + 1):
   ```
3. Update docstring to remove `dA_max` documentation

**Function**: `find_all_feasible_trades()`

**Current usage** (line 516):
```python
dA_max = params.get('dA_max', 5)
```

**Changes**:
1. Remove `dA_max` extraction from params
2. Direction 1 (i sells A, j buys A) - line 532:
   ```python
   # OLD
   for dA in range(1, min(dA_max + 1, agent_i.inventory.A + 1)):
   
   # NEW  
   for dA in range(1, agent_i.inventory.A + 1):
   ```

3. Direction 1 maximum mode - line 551:
   ```python
   # OLD
   for dA in range(1, min(dA_max + 1, agent_i.inventory.A + 1)):
   
   # NEW
   for dA in range(1, agent_i.inventory.A + 1):
   ```

4. Direction 1 maximum surplus mode - line 573:
   ```python
   # OLD
   for dA in range(1, min(dA_max + 1, agent_i.inventory.A + 1)):
   
   # NEW
   for dA in range(1, agent_i.inventory.A + 1):
   ```

5. Repeat for Direction 2 (j sells A, i buys A) - lines 600, 618, 640

**Function calls to update**:

Find all calls to `find_compensating_block()` in this file and remove `dA_max` argument:
```bash
grep -n "find_compensating_block" src/vmt_engine/systems/matching.py
```

Expected locations:
- Line ~440 in legacy matching functions

**Testing checkpoint**:
```bash
bash -c "source venv/bin/activate && python -m pytest tests/test_barter_integration.py -v"
```

---

#### File 2: `src/vmt_engine/protocols/matching/greedy.py`

**Function**: `execute()` 

**Current usage** (line 185-186):
```python
params = {
    "dA_max": world.params.get("dA_max", 50),
}
```

**Changes**:
1. Remove the params dict entirely (line 185-187)
2. Update `find_all_feasible_trades()` call (line 189):
   ```python
   # OLD
   feasible_trades = find_all_feasible_trades(
       agent_a, agent_b, params, epsilon
   )
   
   # NEW
   feasible_trades = find_all_feasible_trades(
       agent_a, agent_b, {}, epsilon  # Empty params dict
   )
   ```
   
**Note**: We pass empty dict `{}` to maintain signature compatibility during transition. In Phase 1B we'll remove params dict entirely.

**Testing checkpoint**:
```bash
bash -c "source venv/bin/activate && python -m pytest tests/test_greedy_surplus_matching.py -v"
```

---

#### File 3: `src/vmt_engine/protocols/bargaining/take_it_or_leave_it.py`

**Current usage** (line 130):
```python
"dA_max": world.params.get("dA_max", 50),
```

**Changes**:
1. Remove `dA_max` from params dict construction
2. If params dict becomes empty, remove it entirely from context builder calls

**Testing checkpoint**:
```bash
bash -c "source venv/bin/activate && python -m pytest tests/test_take_it_or_leave_it_bargaining.py -v"
```

---

#### File 4: `src/vmt_engine/protocols/context_builders.py`

**Function**: `build_world_view_for_decentralized_matching()`

**Current usage** (line 67):
```python
"dA_max": sim.params.get("dA_max", 50),
```

**Changes**: Remove line 67

**Function**: `build_world_view_for_bargaining()`

**Current usage** (line 150):
```python
"dA_max": sim.params.get("dA_max", 50),
```

**Changes**: Remove line 150

---

### Phase 1B: Clean Up Function Signatures

After Phase 1 passes tests, clean up unnecessary params arguments:

1. `find_all_feasible_trades()`: If params dict is now unused, consider removing it entirely
2. Review all param dict usages - only keep what's actually needed

---

### Phase 2: Configuration Layer

#### File 5: `src/scenarios/schema.py`

**Current** (line 75):
```python
dA_max: int = 5  # Maximum trade size to search (formerly ΔA_max)
```

**Current validation** (lines 116-117):
```python
if self.dA_max <= 0:
    raise ValueError(f"dA_max must be positive, got {self.dA_max}")
```

**Changes**:
1. Remove `dA_max` field from `ParametersSection` class
2. Remove validation block

**Testing checkpoint**:
```bash
bash -c "source venv/bin/activate && python -c 'from src.scenarios.schema import ParametersSection; print(ParametersSection.__annotations__)'"
```

---

#### File 6: `src/scenarios/loader.py`

**Current** (lines 50-51):
```python
# Support both dA_max (new) and ΔA_max (legacy) for backward compatibility
dA_max_value = params_data.get('dA_max') or params_data.get('ΔA_max', 5)
```

**Current usage** (line 57):
```python
dA_max=dA_max_value,
```

**Changes**:
1. Remove lines 50-51 (extraction logic)
2. Remove `dA_max=dA_max_value` from ParametersSection construction (line 57)

**Testing checkpoint**:
```bash
bash -c "source venv/bin/activate && python -m pytest tests/test_scenario_loader.py -v"
```

---

#### File 7: `src/vmt_engine/simulation.py`

**Current** (line 86):
```python
'dA_max': scenario_config.params.dA_max,
```

**Changes**: Remove from params dict construction

**Testing checkpoint**:
```bash
bash -c "source venv/bin/activate && python -m pytest tests/test_simulation_init.py -v"
```

---

### Phase 3: Scenario Files

Remove `dA_max` line from all YAML files. This is mechanical cleanup.

#### Demo Scenarios (5 files)
- `scenarios/demos/minimal_2agent.yaml` (line 31)
- `scenarios/demos/edgeworth_box_4agent.yaml` (line 32)
- `scenarios/demos/bargaining_comparison_6agent.yaml` (line 30)
- `scenarios/demos/protocol_comparison_4agent.yaml` (line 30)
- `scenarios/foundational_barter_demo.yaml` (line 23)

#### Test Scenarios (7 files)
- `scenarios/test/test_linear.yaml` (line 40)
- `scenarios/test/test_ces.yaml` (line 41)
- `scenarios/test/test_mixed.yaml` (line 74)
- `scenarios/test/test_translog.yaml` (line 44)
- `scenarios/test/test_stone_geary.yaml` (line 42)
- `scenarios/test/test_quadratic.yaml` (line 43)
- `scenarios/test/phase1_complete.yaml` (line 110)

#### Large Scenarios (1 file)
- `scenarios/curated/large_100_agents.yaml` (line 83)

**Verification**:
```bash
grep -r "dA_max" scenarios/ --include="*.yaml"
# Should return no results
```

**Testing checkpoint**:
```bash
bash -c "source venv/bin/activate && python -m pytest tests/test_new_utility_scenarios.py -v"
bash -c "source venv/bin/activate && python -m pytest tests/test_barter_integration.py -v"
```

---

### Phase 4: Test Infrastructure

#### File 8: `tests/helpers/builders.py`

**Current** (line 39):
```python
dA_max=3,
```

**Changes**: Remove from default params

**Affected tests**: Check all tests importing from builders.py
```bash
grep -r "from.*helpers.builders import" tests/
```

**Testing checkpoint**:
```bash
bash -c "source venv/bin/activate && python -m pytest tests/ -v"
```

---

#### File 9: Direct test usages

Check for any hardcoded dA_max in test files:
```bash
grep -r "dA_max" tests/ --include="*.py"
```

Expected hit:
- `tests/test_greedy_surplus_matching.py` (line 51): `params={"beta": 0.95, "epsilon": 1e-9, "dA_max": 50}`

**Changes**: Remove `"dA_max": 50` from params dict

---

#### File 10-12: Test scenario parameter usage

Files using dA_max in params construction:
- `tests/test_resource_claiming.py` (line 70)
- `tests/test_performance.py` (line 27)
- `tests/test_mode_integration.py` (line 21)

**Changes**: Remove `dA_max=X` from all SimulationParams constructions

---

### Phase 5: Documentation

#### File 13: `docs/structures/comprehensive_scenario_template.yaml`

**Lines to remove**:
- Line 115: Parameter definition
- Lines 256-258: Usage guidance
- Line 269: CES/Translog note
- Line 304: Trading parameters note
- Line 360: Complexity note

**Changes**: Delete all references, update complexity discussion to note that trade search is O(inventory_size × prices)

---

#### File 14: `docs/structures/minimal_working_example.yaml`

**Line to remove**:
- Line 32: `# - dA_max: 5`

---

#### File 15: `docs/structures/parameter_quick_reference.md`

**Lines to remove**:
- Line 40: Parameter table entry
- Lines 192-194: Typical values guidance

**Changes**: Remove all references to `dA_max`

---

#### File 16: `docs/structures/README.md`

**Lines to update**:
- Line 101: Remove `dA_max` from trading parameters list
- Line 146: Remove trade size guidance

---

#### File 17: `docs/2_technical_manual.md`

**Line 38**: Update complexity note:

**OLD**:
```markdown
O(1) per neighbor vs O(dA_max × prices) for exact calculation
```

**NEW**:
```markdown
O(1) per neighbor vs O(inventory_A × prices) for exact calculation
```

**Line 49**: Update bargaining description:

**OLD**:
```markdown
Scans trade sizes ΔA from 1 to dA_max
```

**NEW**:
```markdown
Scans trade sizes ΔA from 1 to seller's inventory
```

---

#### File 18: `docs/4_typing_overview.md`

**Lines to remove**:
- Line 204: `// 1. Iterate through trade sizes ΔA from 1 to dA_max`
- Line 316: `dA_max: int` field definition

**Changes**: Update algorithm descriptions to reference inventory limits

---

#### File 19: `docs/CURRENT/comprehensive_7_phase_tick_review.md`

**Lines to update**:
- Line 385: Remove `dA_max` from parameter list
- Line 945: Update trade enumeration description to use inventory

---

#### File 20: `docs/structures/PARAMETER_AUDIT_SUMMARY.md`

**Line to remove**:
- Line 79: `- ✅ dA_max`
- Line 165: Validation warning about dA_max and trade_execution_mode

---

#### File 21: `src/vmt_engine/README.md`

**Line 32**: Update bargaining description:

**OLD**:
```markdown
scan ΔA ∈ [1..dA_max]
```

**NEW**:
```markdown
scan ΔA ∈ [1..inventory_A]
```

---

### Phase 6: Final Verification

#### Comprehensive test suite
```bash
bash -c "source venv/bin/activate && python -m pytest tests/ -v --tb=short"
```

#### No remaining references
```bash
# Should find ZERO matches
grep -r "dA_max" src/ tests/ scenarios/ --include="*.py" --include="*.yaml"
grep -r "ΔA_max" src/ tests/ scenarios/ --include="*.py" --include="*.yaml"
```

#### Documentation references acceptable
```bash
# These are OK - documentation of the refactor
grep -r "dA_max" docs/CURRENT/refactors/
```

#### Load and run a scenario
```bash
bash -c "source venv/bin/activate && python main.py --scenario scenarios/demos/minimal_2agent.yaml --headless --ticks 10"
```

---

## Testing Strategy

### Unit Tests (Per Phase)
- Phase 1: Test each modified function in isolation
- Phase 2: Test scenario loading with and without dA_max in YAML
- Phase 3: Test all scenarios load successfully
- Phase 4: Run full test suite

### Integration Tests
After Phase 4, run:
1. `test_barter_integration.py` - Core trading still works
2. `test_greedy_surplus_matching.py` - Matching protocol still works
3. `test_foundational_baseline_trades.py` - Known-good outcomes still achieved
4. `test_new_utility_scenarios.py` - All utility functions still work

### Regression Testing
Compare telemetry before/after on `foundational_barter_demo.yaml`:
- Same number of trades completed
- Same final utilities (within floating point tolerance)
- Trade sizes may differ (can now explore larger trades)

### Performance Testing
Run `scripts/benchmark_performance.py` before and after:
- Small scenarios (2-10 agents): Should be identical
- Large scenarios (100 agents): May be slower if inventories >> 5
- If unacceptable, add early termination based on diminishing surplus

---

## Rollback Plan

If critical issues arise:

1. **Immediate rollback**: Revert all commits from this refactor
2. **Git tag**: Tag the commit before starting as `pre-dA_max-removal`
3. **Branch strategy**: Do all work on `refactor/remove-dA-max` branch
4. **Merge only when**: All tests pass + visual inspection of 3+ scenarios confirms behavior

---

## Success Criteria

### Functional
- [ ] All existing tests pass
- [ ] `foundational_barter_demo.yaml` produces reasonable trades
- [ ] No runtime errors in any scenario
- [ ] Greedy surplus matching still finds optimal trades

### Code Quality  
- [ ] No references to `dA_max` in source code
- [ ] No references to `dA_max` in scenario files
- [ ] Documentation updated consistently
- [ ] No orphaned default values or fallbacks

### Performance
- [ ] Small scenarios (≤10 agents) runtime unchanged (±10%)
- [ ] Large scenarios (100 agents) runtime acceptable (<2x slower)
- [ ] No infinite loops or hangs

### Validation
- [ ] Can manually inspect trades and confirm they make economic sense
- [ ] Trade sizes range from 1 to reasonable inventory-based maxima
- [ ] No artificial "stopped at 5 units" artifacts in logs

---

## Estimated Effort

- **Phase 1**: 45 min (core logic, requires careful testing)
- **Phase 2**: 15 min (configuration, straightforward)
- **Phase 3**: 20 min (scenarios, mechanical)
- **Phase 4**: 15 min (tests, mechanical)
- **Phase 5**: 30 min (documentation, careful reading)
- **Phase 6**: 20 min (verification, testing)

**Total**: ~2.5 hours

---

## Dependencies & Risks

### Dependencies
- None. This is pure simplification.

### Risks

**Risk 1**: Performance degradation on large inventories
- **Likelihood**: Medium
- **Impact**: Low (can add smart early termination later)
- **Mitigation**: Benchmark before/after

**Risk 2**: Hidden assumptions about bounded search
- **Likelihood**: Low  
- **Impact**: High (infinite loops, crashes)
- **Mitigation**: Comprehensive testing, code review of all iteration logic

**Risk 3**: Test scenarios assume specific dA_max behavior
- **Likelihood**: Low
- **Impact**: Medium (tests fail, need updating)
- **Mitigation**: Review test expectations, update assertions if needed

---

## Post-Refactor Validation Questions

After completion, verify:

1. **Economic sanity**: Do agents trade reasonable quantities given their inventories?
2. **Pareto efficiency**: Can agents reach deeper into the contract curve?
3. **Determinism**: Do repeated runs with same seed produce identical results?
4. **Edge cases**: What happens with inventory of 1? Of 100? Of 1000?

---

## Notes

- This refactor is prerequisite to adding more realistic bargaining (sequential offers, etc.)
- Removing artificial constraints makes the model more scientifically defensible
- If performance becomes an issue, add *economically motivated* early stopping (e.g., stop when marginal surplus < ε)

---

## References

- Original discussion: 2025-10-31 chat
- Related docs: `docs/BIGGEST_PICTURE/vision_and_architecture.md`
- Architecture rules: `.github/copilot-instructions.md`

