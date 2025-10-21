# ADR-001 Phase 1: Cursor Implementation Plan

**Date**: 2025-10-21  
**Status**: Ready for Implementation  
**Reference**: [ADR-001](../decisions/001-hybrid-money-modularization-sequencing.md)  
**Estimated Total Time**: 20-25 hours  

---

## Overview

This document provides a detailed, step-by-step implementation plan for Phase 1 of ADR-001, optimized for execution by Cursor AI. Phase 1 delivers a production-ready quasilinear money system through three sequential work packages:

1. **Money Phase 3**: Mixed exchange regimes (12-15 hours)
2. **Scenario Generator Phase 2**: Exchange regime selection + presets (2-3 hours)
3. **Money Phase 4**: UI polish, demos, and documentation (8-10 hours)

**Success Criteria**: v1.0 release with production-ready quasilinear money system, comprehensive demos, and complete documentation.

---

## Implementation Philosophy

### For Cursor AI Execution

1. **Sequential Validation**: Complete each subsection fully before proceeding. Run all tests after each major change.
2. **Determinism First**: Every change must preserve 100% deterministic simulation behavior.
3. **Test Coverage**: Maintain >95% test coverage. Add tests before or alongside implementation.
4. **Documentation Inline**: Update documentation immediately after code changes, not as a separate phase.
5. **Performance Monitoring**: Track runtime performance at each checkpoint. Flag any >10% regressions.

### Safety Protocols

- **Branch Strategy**: Create feature branch for each work package
- **Checkpoint Commits**: Commit after each completed subsection
- **Rollback Procedure**: If any phase fails validation, revert to last checkpoint
- **Test Gating**: No code proceeds to next section without all tests passing

---

## Prerequisites Verification

**Before starting, verify Phase 2 completion:**

```bash
# Verify Money Phase 2 tests pass
pytest tests/test_money_phase2*.py -v

# Verify monetary exchange works
python main.py scenarios/money_test_basic.yaml --seed 42

# Check telemetry logs contain money trades
sqlite3 runs.db "SELECT COUNT(*) FROM trades WHERE dM != 0;"
```

**Expected Results:**
- All Phase 2 tests pass (100%)
- Money trades logged with `dM > 0`
- No linter errors in `src/vmt_engine/` or `src/scenarios/`

**If prerequisites fail**: Resolve Money Phase 2 issues before proceeding. See [money_phase2_checklist.md](../BIG/money_phase2_checklist.md).

---

## Work Package 1: Money Phase 3 (Mixed Regimes)

**Time Budget**: 12-15 hours  
**Reference**: [money_phase3_checklist.md](../BIG/money_phase3_checklist.md)  
**Branch**: `feature/money-phase3-mixed-regimes`

### Part 1A: Test Scenarios (1 hour)

Create two comprehensive test scenarios to validate mixed regime functionality.

**Deliverables:**
1. `scenarios/money_test_mixed.yaml` - Basic mixed regime
2. `scenarios/money_test_mode_interaction.yaml` - Mode schedule × regime interaction

**Key Features:**
- Mixed regime allows A↔M, B↔M, and A↔B exchanges
- Varied initial inventories (some agents cash-rich, others goods-rich)
- Mode schedule scenario includes temporal control (`mode_schedule`)

**Validation:**
```bash
python -m src.scenarios.validate scenarios/money_test_mixed.yaml
python -m src.scenarios.validate scenarios/money_test_mode_interaction.yaml
```

**Checkpoint**: Both scenarios validate against schema. Commit: `"Add Money Phase 3 test scenarios"`

---

### Part 1B: Trade Pair Enumeration (2 hours)

Extend `trading.py` to enumerate all permissible exchange pairs based on `exchange_regime`.

**Files Modified:**
- `src/vmt_engine/systems/trading.py`

**Implementation Steps:**

1. **Add `_get_allowed_pairs()` method**
   - Input: `regime: str` (from `sim.params['exchange_regime']`)
   - Output: `list[tuple[str, str]]` where each tuple is `(good_sold, good_paid)`
   - Logic:
     - `"barter_only"` → `[("A", "B"), ("B", "A")]`
     - `"money_only"` → `[("A", "M"), ("B", "M")]`
     - `"mixed"` or `"mixed_liquidity_gated"` → All four pairs

2. **Unit test creation**
   - File: `tests/test_trade_pair_enumeration.py`
   - Tests:
     - Each regime returns correct pair set
     - No duplicates in pair lists
     - Invalid regime raises error

**Validation:**
```bash
pytest tests/test_trade_pair_enumeration.py -v
```

**Checkpoint**: Tests pass. Commit: `"Implement trade pair enumeration for mixed regimes"`

---

### Part 1C: Money-First Tie-Breaking (3 hours)

Implement deterministic tie-breaking for mixed regimes when multiple trade types have equal surplus.

**Files Modified:**
- `src/vmt_engine/systems/trading.py`

**Algorithm Specification:**

When ranking trade candidates, sort by:
1. **Total surplus** (descending) - maximize welfare
2. **Pair type priority** (ascending) - money-first policy:
   - Priority 0: A↔M
   - Priority 1: B↔M
   - Priority 2: A↔B (barter)
3. **Agent pair** `(min_id, max_id)` (ascending) - deterministic tie-breaker

**Implementation Steps:**

1. **Define `TradeCandidate` dataclass** (if not exists)
   ```python
   @dataclass
   class TradeCandidate:
       buyer_id: int
       seller_id: int
       good_sold: str
       good_paid: str
       dX: int
       dY: int
       buyer_surplus: float
       seller_surplus: float
   ```

2. **Implement `_rank_trade_candidates()` method**
   - Define `PAIR_PRIORITY` dict mapping pair types to priority integers
   - Create sort key function with three-level sorting
   - Return sorted list of candidates

3. **Unit test creation**
   - File: `tests/test_mixed_regime_tie_breaking.py`
   - Tests:
     - Money trades preferred when surplus equal
     - Barter trades selected when surplus higher
     - Deterministic ordering (repeated sorts identical)
     - Agent ID tie-breaking works correctly

**Validation:**
```bash
pytest tests/test_mixed_regime_tie_breaking.py -v
```

**Checkpoint**: All tie-breaking tests pass. Commit: `"Implement money-first tie-breaking policy"`

---

### Part 1D: Multi-Pair Candidate Generation (3 hours)

Extend `TradeSystem.execute()` to generate trade candidates for all allowed pair types.

**Files Modified:**
- `src/vmt_engine/systems/trading.py`

**Implementation Steps:**

1. **Refactor `execute()` to enumerate all pairs**
   - For each agent pair within interaction radius:
     - For each `(good_sold, good_paid)` in `_get_allowed_pairs(regime)`:
       - Get quotes for that pair type
       - Search for feasible compensating block
       - If feasible, create `TradeCandidate` and add to list

2. **Rank all candidates**
   - Call `_rank_trade_candidates()` on full list
   - Return ranked list

3. **Execute trades with one-per-pair-per-tick constraint**
   - Track executed agent pairs in `set()`
   - Execute highest-ranked candidate first
   - Skip candidates involving already-traded agents

4. **Add pair type logging**
   - Log `exchange_pair_type` field (e.g., "A<->M", "B<->A")
   - Enables post-hoc analysis of trade type distribution

**Integration test creation:**
- File: `tests/test_mixed_regime_integration.py`
- Tests:
  - Mixed scenario runs to completion
  - Both money and barter trades occur (if opportunities exist)
  - Telemetry logs contain multiple `exchange_pair_type` values
  - Performance within 20% of Phase 2 baseline

**Validation:**
```bash
pytest tests/test_mixed_regime_integration.py -v
pytest tests/test_money_phase2*.py -v  # Regression check
```

**Checkpoint**: Integration tests pass, Phase 2 tests still pass. Commit: `"Implement multi-pair candidate generation"`

---

### Part 1E: Mode × Regime Interaction (2 hours)

Verify two-layer control architecture: temporal control (`mode_schedule`) × type control (`exchange_regime`).

**Files Modified:**
- `src/vmt_engine/simulation.py`

**Implementation Steps:**

1. **Implement `_get_active_exchange_pairs()` method**
   - Combines temporal and type control
   - Logic:
     - If `current_mode == "forage"` → return `[]` (no trades)
     - If `current_mode == "trade"` or `"both"` → return pairs from `exchange_regime`

2. **Integration with trade system**
   - `TradeSystem.execute()` calls `sim._get_active_exchange_pairs()` before enumerating
   - Short-circuits if empty list returned

3. **Test creation**
   - File: `tests/test_mode_regime_interaction.py`
   - Tests:
     - Forage mode blocks all trades regardless of regime
     - Trade mode enables trades per regime
     - Mode transitions work correctly with mixed regime
     - Telemetry `tick_states` table logs correct `current_mode` and `active_pairs`

**Validation:**
```bash
python main.py scenarios/money_test_mode_interaction.yaml --seed 42
pytest tests/test_mode_regime_interaction.py -v
```

**Checkpoint**: Mode × regime interaction verified. Commit: `"Implement mode × regime interaction layer"`

---

### Part 1F: Telemetry Enhancements (1 hour)

Add analysis scripts for mixed regime telemetry.

**Deliverables:**
1. `scripts/analyze_trade_distribution.py` - Count trades by pair type
2. `scripts/plot_mode_timeline.py` - Visualize mode transitions

**Implementation:**
- Query `trades.exchange_pair_type` and `tick_states.current_mode`
- Generate summary statistics and plots
- Output to console or save as PNG

**Validation:**
```bash
python main.py scenarios/money_test_mixed.yaml --seed 42
python scripts/analyze_trade_distribution.py runs.db 1
python scripts/plot_mode_timeline.py runs.db 1
```

**Checkpoint**: Scripts produce expected output. Commit: `"Add mixed regime telemetry analysis scripts"`

---

### Part 1G: Comparative Testing (1 hour)

Run same base scenario with all three regimes and compare outcomes.

**Test Creation:**
- File: `tests/test_regime_comparison.py`
- Run identical initial conditions with:
  1. `exchange_regime: barter_only`
  2. `exchange_regime: money_only`
  3. `exchange_regime: mixed`
- Compare:
  - Total trades
  - Average surplus per trade
  - Final utility distribution
  - Convergence speed (if applicable)

**Validation:**
```bash
pytest tests/test_regime_comparison.py -v --tb=short
```

**Checkpoint**: Comparative test demonstrates regime differences. Commit: `"Add regime comparison test"`

---

### Part 1H: Documentation (1 hour)

Update documentation to reflect mixed regime implementation.

**Files to Update:**
1. `docs/2_technical_manual.md` - Add section on exchange regimes
2. `docs/4_typing_overview.md` - Document `exchange_pair_type` field
3. `docs/BIG/money_SSOT_implementation_plan.md` - Mark Phase 3 complete

**Content:**
- Explain tie-breaking policy and rationale (money-first)
- Provide example scenarios
- Document mode × regime interaction rules
- Add pedagogical notes (when to use each regime)

**Checkpoint**: Documentation updated and reviewed. Commit: `"Document Money Phase 3 (mixed regimes)"`

---

### Money Phase 3 Completion Checklist

- [ ] Both test scenarios created and validated
- [ ] Trade pair enumeration implemented and tested
- [ ] Money-first tie-breaking implemented and tested
- [ ] Multi-pair candidate generation working
- [ ] Mode × regime interaction verified
- [ ] Telemetry analysis scripts working
- [ ] Comparative regime test passing
- [ ] All Phase 2 tests still passing (regression check)
- [ ] Documentation updated
- [ ] Performance within 10% of Phase 2 baseline
- [ ] No linter errors

**Final Validation:**
```bash
pytest tests/ -v --tb=short  # Full test suite
python -m flake8 src/vmt_engine src/scenarios
python -m mypy src/vmt_engine src/scenarios
```

**Phase 3 Merge**: Merge `feature/money-phase3-mixed-regimes` to `main`

---

## Work Package 2: Scenario Generator Phase 2

**Time Budget**: 2-3 hours  
**Reference**: [scenario_generator_phase2_plan.md](../implementation/scenario_generator_phase2_plan.md)  
**Branch**: `feature/scenario-gen-phase2`  
**Prerequisite**: Money Phase 3 complete

### Part 2A: Exchange Regime Support (30 min)

Add `--exchange-regime` flag to scenario generator CLI.

**Files Modified:**
1. `src/vmt_tools/generate_scenario.py` - Add CLI argument
2. `src/vmt_tools/scenario_builder.py` - Add regime logic

**Implementation Steps:**

1. **Add CLI argument**
   ```python
   parser.add_argument(
       '--exchange-regime',
       choices=['barter_only', 'money_only', 'mixed', 'mixed_liquidity_gated'],
       default='barter_only',
       help='Exchange regime for trade system'
   )
   ```

2. **Generate M inventories when needed**
   ```python
   if exchange_regime in ['money_only', 'mixed', 'mixed_liquidity_gated']:
       M_inventories = generate_inventories(n_agents, inv_min, inv_max)
       initial_inventories['M'] = M_inventories
       params['exchange_regime'] = exchange_regime
       params['money_mode'] = 'quasilinear'
       params['money_scale'] = 1
       params['lambda_money'] = 1.0
   ```

**Validation:**
```bash
# Generate money scenario
python -m src.vmt_tools.generate_scenario test_money \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces --resources 0.3,5,1 \
  --exchange-regime money_only

# Validate schema
python -m src.scenarios.validate scenarios/test_money.yaml

# Run scenario
python main.py scenarios/test_money.yaml --seed 42
```

**Checkpoint**: Money scenarios generate, validate, and run. Commit: `"Add exchange regime support to scenario generator"`

---

### Part 2B: Preset System (45 min)

Add scenario presets to eliminate repetitive typing.

**Files Modified:**
1. `src/vmt_tools/param_strategies.py` - Add `PRESETS` dict
2. `src/vmt_tools/generate_scenario.py` - Add preset logic

**Presets to Define:**

1. **`minimal`** - Quick testing (10 agents, 20×20 grid)
2. **`standard`** - Default demo (30 agents, 40×40 grid, all utility types)
3. **`large`** - Performance testing (80 agents, 80×80 grid)
4. **`money_demo`** - Money-only economy (20 agents, `money_only` regime)
5. **`mixed_economy`** - Hybrid (40 agents, `mixed` regime)

**Implementation:**
- Define `PRESETS` dict with complete parameter sets
- Add `get_preset(name)` function
- Add `--preset` CLI argument
- Make other arguments optional when preset used
- Explicit flags override preset values

**Validation:**
```bash
# Generate with each preset
for preset in minimal standard large money_demo mixed_economy; do
  python -m src.vmt_tools.generate_scenario test_$preset --preset $preset --seed 42
  python -m src.scenarios.validate scenarios/test_$preset.yaml
done

# Test override
python -m src.vmt_tools.generate_scenario test_override \
  --preset money_demo --agents 50 --seed 42
# Verify: 50 agents (not preset's 20)
```

**Checkpoint**: All presets work, overrides work. Commit: `"Add scenario preset system"`

---

### Part 2C: Documentation (30 min)

Update scenario generator documentation.

**Files to Update:**
- `src/vmt_tools/README.md`

**Content to Add:**
- Exchange regime flag usage and examples
- All 5 presets with use cases
- Combined examples (preset + overrides)
- Backward compatibility note

**Checkpoint**: Documentation complete. Commit: `"Document Scenario Generator Phase 2 features"`

---

### Part 2D: Testing (30 min)

Create comprehensive integration tests for Phase 2 features.

**Test Scenarios to Generate:**
1. `test_money_only.yaml` - Money-only regime
2. `test_mixed.yaml` - Mixed regime
3. `test_preset_minimal.yaml` - Minimal preset
4. `test_preset_money_demo.yaml` - Money demo preset
5. `test_preset_mixed_economy.yaml` - Mixed economy preset

**Validation Checklist:**
- [ ] All test scenarios validate against schema
- [ ] Money scenarios have `M` field in inventories
- [ ] Money parameters set correctly
- [ ] Presets produce expected configurations
- [ ] Preset overrides work
- [ ] Phase 1 commands still work identically (backward compat)

**Checkpoint**: All validation passes. Commit: `"Add Scenario Generator Phase 2 tests"`

---

### Scenario Generator Phase 2 Completion Checklist

- [ ] `--exchange-regime` flag working for all 4 regimes
- [ ] M inventories generated when needed
- [ ] Money parameters set appropriately
- [ ] 5 presets defined and tested
- [ ] Preset overrides work correctly
- [ ] Documentation updated with examples
- [ ] 5 test scenarios generated and validated
- [ ] Backward compatibility verified
- [ ] No linter errors

**Phase 2 Merge**: Merge `feature/scenario-gen-phase2` to `main`

---

## Work Package 3: Money Phase 4 (Polish & Documentation)

**Time Budget**: 8-10 hours  
**Reference**: [money_phase4_checklist.md](../BIG/money_phase4_checklist.md)  
**Branch**: `feature/money-phase4-polish`  
**Prerequisite**: Money Phase 3 + Scenario Generator Phase 2 complete

### Part 3A: Renderer Enhancements (2 hours)

Add money visualization to PyGame renderer.

**Files Modified:**
- `src/vmt_pygame/renderer.py`

**Features to Implement:**

1. **Money inventory display**
   - Show `M` value as gold text near each agent
   - Format: `$123` or `M:123`

2. **Money transfer animation**
   - Gold sparkle effect flowing from buyer to seller
   - Triggered when `dM > 0` in trade

3. **Mode/regime overlay**
   - Top-left corner display showing:
     - Current mode (forage/trade/both)
     - Exchange regime (barter_only/money_only/mixed)
     - Active exchange pairs
   - Color-coded by regime type

4. **Lambda heatmap** (optional, low priority)
   - Toggle with keyboard shortcut
   - Color agents by λ value (blue = low, red = high)

**Validation:**
```bash
python main.py scenarios/money_test_mixed.yaml --seed 42 --render
# Visual inspection: verify money displays, animations, overlays
```

**Checkpoint**: Visual features working. Commit: `"Add money visualization to renderer"`

---

### Part 3B: Log Viewer Enhancements (2 hours)

Add money-specific queries and views to log viewer GUI.

**Files Modified:**
- `src/vmt_log_viewer/queries.py`
- `src/vmt_log_viewer/widgets.py` (or equivalent)

**Features to Implement:**

1. **Money trade filter**
   - Query: `SELECT * FROM trades WHERE dM != 0`
   - Display in table view

2. **Lambda trajectory plot**
   - Plot λ over time for selected agents
   - Multi-agent comparison

3. **Mode timeline view**
   - Visualize mode transitions over ticks
   - Color-coded by mode type

4. **CSV export with money columns**
   - Include dM, buyer_lambda, seller_lambda in trade exports
   - Include inventory_M, lambda_money in agent snapshot exports

**Validation:**
```bash
python main.py scenarios/money_test_mixed.yaml --seed 42
python -m src.vmt_log_viewer.main runs.db
# Test each new feature in GUI
```

**Checkpoint**: Log viewer features working. Commit: `"Add money features to log viewer"`

---

### Part 3C: Demo Scenarios (2 hours)

Create 5 pedagogically-sound demo scenarios showcasing money features.

**Directory**: Create `scenarios/demos/`

**Demos to Create:**

1. **`demo_01_simple_money.yaml`** - Simple monetary exchange
   - 6-8 agents, clear complementarity
   - Money enables beneficial trades
   - Pedagogical: "Why money?"

2. **`demo_02_barter_vs_money.yaml`** - Regime comparison
   - Same initial conditions, two variants (barter_only vs money_only)
   - Demonstrate efficiency gains from money
   - Pedagogical: "Double coincidence of wants"

3. **`demo_03_mixed_regime.yaml`** - Hybrid economy
   - 20 agents, mixed regime
   - Both trade types coexist
   - Pedagogical: "When is barter still used?"

4. **`demo_04_mode_schedule.yaml`** - Temporal + type control
   - Mode schedule with mixed regime
   - Alternating forage/trade cycles
   - Pedagogical: "Time constraints with money"

5. **`demo_05_liquidity_zones.yaml`** - Spatial variation (if applicable)
   - Large grid, clustered agents
   - Liquidity varies by location
   - Pedagogical: "Market thickness"

**Demo Runner Script:**
- File: `scripts/run_demos.py`
- Runs all 5 demos sequentially
- Reports pass/fail for each
- Exit code 0 if all pass

**Validation:**
```bash
python scripts/run_demos.py
# Expected: All 5 demos pass
```

**Checkpoint**: All demos working and pedagogically sound. Commit: `"Add money system demo scenarios"`

---

### Part 3D: User Documentation (2 hours)

Write comprehensive user guide for money system.

**Files to Create:**
1. `docs/user_guide_money.md` - Complete user guide
2. `docs/regime_comparison.md` - Pedagogical guide to regimes

**Content Structure for User Guide:**

1. **Introduction**
   - What is the money system?
   - Pedagogical goals
   - Quick start

2. **Configuration Reference**
   - `money_mode`: quasilinear vs kkt_lambda
   - `exchange_regime`: all 4 types
   - Money parameters (λ, scaling, bounds)

3. **Example Scenarios**
   - Annotated YAML examples
   - When to use each regime
   - Classroom exercises

4. **Interpreting Results**
   - Understanding λ values
   - Trade type distributions
   - Liquidity metrics

5. **Troubleshooting**
   - Common issues and solutions
   - Performance tips
   - FAQ

**Checkpoint**: User documentation complete and reviewed. Commit: `"Add money system user guide"`

---

### Part 3E: Technical Documentation (1 hour)

Write technical reference for developers and researchers.

**File to Create:**
- `docs/technical/money_implementation.md`

**Content:**
1. Architecture overview (two-layer control)
2. Algorithms (tie-breaking, pair enumeration)
3. Data structures (Inventory.M, quotes extensions)
4. Telemetry schema reference
5. Performance considerations
6. Testing strategy

**Checkpoint**: Technical documentation complete. Commit: `"Add money system technical reference"`

---

### Part 3F: Main Documentation Updates (30 min)

Update core documentation files to reference money system.

**Files to Update:**
1. `README.md` - Add money system section to main README
2. `docs/1_project_overview.md` - Add money features to feature list
3. `docs/2_technical_manual.md` - Add money system architecture section
4. `docs/4_typing_overview.md` - Mark Money Phase 3 complete

**Checkpoint**: Core docs updated. Commit: `"Update core documentation for money system"`

---

### Part 3G: Code Quality Pass (1 hour)

Final code quality checks before release.

**Tasks:**

1. **Docstring completion**
   - All public functions have docstrings
   - All classes have docstrings
   - All modules have module-level docstrings

2. **Linter pass**
   ```bash
   flake8 src/ --max-line-length=100
   black src/ --check
   mypy src/vmt_engine src/scenarios src/telemetry
   ```

3. **Type hints audit**
   - All function signatures have type hints
   - Return types specified
   - No `Any` types unless necessary

4. **Dead code removal**
   - Remove commented-out code
   - Remove unused imports
   - Remove TODO comments (convert to issues)

5. **Magic numbers**
   - Replace with named constants
   - Add comments explaining values

**Checkpoint**: All linters pass with zero warnings. Commit: `"Code quality pass for Money Phase 4"`

---

### Part 3H: Performance Validation (30 min)

Ensure money features don't introduce performance regressions.

**Benchmarks to Run:**

1. **Small scenario** (20 agents, 100 ticks)
   ```bash
   time python main.py scenarios/money_test_mixed.yaml --seed 42
   ```
   Expected: < 5 seconds

2. **Large scenario** (80 agents, 200 ticks)
   ```bash
   time python main.py scenarios/large_money_scenario.yaml --seed 42
   ```
   Expected: < 60 seconds

3. **Memory profiling**
   ```bash
   python -m memory_profiler main.py scenarios/money_test_mixed.yaml
   ```
   Expected: No memory leaks

4. **Comparison with Phase 2 baseline**
   - Runtime should be within 10% of Phase 2 for equivalent scenarios
   - If regression > 10%, profile and optimize

**Checkpoint**: Performance within acceptable bounds. Document in `docs/performance_baseline_phase4.md`.

---

### Part 3I: Testing and Validation (1 hour)

Comprehensive end-to-end testing before release.

**Test Suite:**

1. **Full regression**
   ```bash
   pytest tests/ -v --tb=short
   ```
   Expected: All 152+ tests pass

2. **Demo validation**
   ```bash
   python scripts/run_demos.py
   ```
   Expected: All 5 demos pass

3. **GUI validation**
   - Launch GUI: `python launcher.py`
   - Run each demo from GUI
   - Verify renderer features work
   - Verify no crashes or glitches

4. **Cross-platform check** (if applicable)
   - Test on Linux, Windows, macOS
   - Verify telemetry database compatibility

**Checkpoint**: All tests pass on all platforms. Ready for release.

---

### Part 3J: Release Preparation (30 min)

Prepare for v1.0 release.

**Tasks:**

1. **Update CHANGELOG.md**
   - Add Money System entry
   - List all new features
   - Note backward compatibility

2. **Create release notes**
   - File: `docs/release_notes_v1.0.md`
   - Highlights for users
   - Migration guide (if needed)

3. **Version tagging**
   ```bash
   git tag -a v1.0-quasilinear -m "Release v1.0: Quasilinear Money System"
   ```

4. **Update project status**
   - Mark Money Phases 2-4 complete in all docs
   - Update [ADR-001](../decisions/001-hybrid-money-modularization-sequencing.md) status
   - Update [strategic-priority.mdc](../../.cursor/rules/strategic-priority.mdc)

**Checkpoint**: Release ready. Merge `feature/money-phase4-polish` to `main`.

---

### Money Phase 4 Completion Checklist

- [ ] Renderer enhancements working (money display, animations, overlays)
- [ ] Log viewer enhancements working (filters, plots, exports)
- [ ] All 5 demo scenarios created and validated
- [ ] User guide complete (`docs/user_guide_money.md`)
- [ ] Technical reference complete (`docs/technical/money_implementation.md`)
- [ ] Core documentation updated
- [ ] Code quality pass complete (no linter warnings)
- [ ] Performance benchmarks within acceptable range
- [ ] All tests passing (152+ tests)
- [ ] Demos validated in GUI
- [ ] CHANGELOG.md updated
- [ ] Release notes written
- [ ] Version tagged (`v1.0-quasilinear`)

---

## Phase 1 Final Validation

Before declaring Phase 1 complete, run this comprehensive validation suite:

### 1. Test Suite Validation
```bash
pytest tests/ -v --tb=short --cov=src --cov-report=term-missing
# Expected: 100% pass rate, >95% coverage
```

### 2. Linter Validation
```bash
flake8 src/ --count --statistics
mypy src/vmt_engine src/scenarios src/telemetry --strict
black src/ --check
```

### 3. Demo Validation
```bash
python scripts/run_demos.py
# Expected: All 5 demos pass
```

### 4. Performance Validation
```bash
python scripts/benchmark_money_system.py
# Compare with baseline in docs/performance_baseline_phase1_with_logging.md
```

### 5. Documentation Validation
- [ ] All links in documentation work
- [ ] All code examples in docs run without errors
- [ ] README.md accurately reflects features
- [ ] User guide is comprehensible to target audience

### 6. Cross-Feature Integration
- [ ] Money system works with mode schedules
- [ ] All exchange regimes work in all modes
- [ ] Telemetry captures all money data correctly
- [ ] Scenario generator produces valid money scenarios
- [ ] Renderer displays all money features correctly

### 7. Determinism Validation
```bash
# Run same scenario twice, verify identical results
python main.py scenarios/money_test_mixed.yaml --seed 42
mv runs.db runs_1.db

python main.py scenarios/money_test_mixed.yaml --seed 42
mv runs.db runs_2.db

python scripts/compare_runs.py runs_1.db runs_2.db
# Expected: Bit-identical telemetry
```

---

## Success Criteria Summary

Phase 1 is **complete** when:

✅ **Money Phase 3**: Mixed regimes fully implemented and tested
✅ **Scenario Generator Phase 2**: Exchange regimes and presets working
✅ **Money Phase 4**: UI polished, demos complete, documentation comprehensive
✅ **Test Coverage**: All 152+ tests passing, >95% coverage
✅ **Performance**: Within 10% of Phase 2 baseline
✅ **Documentation**: User guide and technical reference complete
✅ **Demos**: 5 pedagogical scenarios validated
✅ **Release**: v1.0-quasilinear tagged and ready

---

## Next Steps After Phase 1

**Immediate:**
- Gather user feedback for 2-4 weeks
- Monitor for bugs or usability issues
- Iterate on documentation based on user questions

**Strategic Decision Point** (see [ADR-001](../decisions/001-hybrid-money-modularization-sequencing.md)):
- Evaluate demand for protocol modularization
- Assess need for Money Track 2 (KKT λ, liquidity gating)
- Prioritize based on user feedback

**Possible Phase 2 Tracks:**
1. **Protocol Modularization** (6-9 weeks) - Enable custom matching algorithms
2. **Money Track 2** (3-4 weeks) - Advanced money features (KKT, liquidity gating)
3. **Other Features** - Production, markets, general equilibrium (Strategic Roadmap Phases C-F)

---

## Risk Management

### Potential Issues and Mitigations

**Issue**: Mixed regime introduces non-determinism
- **Mitigation**: Comprehensive tie-breaking tests, determinism validation after each commit
- **Rollback**: Revert to Phase 2 if determinism compromised

**Issue**: Performance regression > 10%
- **Mitigation**: Profile at each checkpoint, optimize hot paths
- **Rollback**: If optimization fails, simplify tie-breaking algorithm

**Issue**: Test suite becomes fragile
- **Mitigation**: Use fixtures, avoid hard-coded values, test invariants not specifics
- **Rollback**: Refactor tests to be more robust

**Issue**: Documentation becomes outdated
- **Mitigation**: Update docs inline with code changes, review before each commit
- **Rollback**: N/A - documentation always fixable

**Issue**: Demos don't demonstrate pedagogy effectively
- **Mitigation**: Iterate with educator feedback, focus on clarity over complexity
- **Rollback**: Simplify demos, add more explanatory comments

---

## Contact and Support

**Questions during implementation?**
- Consult [Quick Reference Guide](../quick_reference.md)
- Check [Technical Manual](../2_technical_manual.md)
- Review [Money SSOT Plan](../BIG/money_SSOT_implementation_plan.md)

**Stuck on a subsection?**
- Re-read the relevant checklist (Phase 3, Phase 4, Scenario Gen Phase 2)
- Run validation scripts to identify specific failure
- Check test output for clues

**Performance issues?**
- Profile with `cProfile`: `python -m cProfile -o output.prof main.py ...`
- Analyze with `snakeviz output.prof`
- Focus optimization on top 3 hotspots

---

## Appendix: Quick Command Reference

### Testing
```bash
# Full test suite
pytest tests/ -v --tb=short

# Phase-specific tests
pytest tests/test_money_phase3*.py -v
pytest tests/test_mixed_regime*.py -v

# Integration tests
pytest tests/test_integration.py -v

# Performance tests
pytest tests/test_performance.py -v --benchmark-only
```

### Scenario Generation
```bash
# Money-only scenario
python -m src.vmt_tools.generate_scenario test --exchange-regime money_only \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces --resources 0.3,5,1

# Using preset
python -m src.vmt_tools.generate_scenario demo --preset money_demo
```

### Running Simulations
```bash
# With rendering
python main.py scenarios/money_test_mixed.yaml --seed 42 --render

# Headless (faster)
python main.py scenarios/money_test_mixed.yaml --seed 42

# With profiling
python -m cProfile -o output.prof main.py scenarios/money_test_mixed.yaml
```

### Analysis
```bash
# Trade distribution
python scripts/analyze_trade_distribution.py runs.db 1

# Mode timeline
python scripts/plot_mode_timeline.py runs.db 1

# Run all demos
python scripts/run_demos.py
```

### Code Quality
```bash
# Linting
flake8 src/ --max-line-length=100
black src/ --check
mypy src/vmt_engine src/scenarios src/telemetry

# Format code
black src/

# Test coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

**Ready to implement Phase 1!** 🚀

This plan provides comprehensive, step-by-step guidance for Cursor AI to implement ADR-001 Phase 1. Each subsection includes explicit validation steps, checkpoint commits, and rollback procedures to ensure high-quality, deterministic implementation.

