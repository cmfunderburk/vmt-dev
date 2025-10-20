# Phase 2 PR Review Guide

**For**: Code reviewers  
**PR**: Phase 2: Monetary Exchange System  
**Date**: 2025-10-19  
**Commits**: 5 (to be squashed to 1)

---

## Quick Start

### Prerequisites

```bash
cd /path/to/vmt-dev
git fetch origin
git checkout 2025-10-19-1730-phase2c-integration
source venv/bin/activate
export PYTHONPATH=.:src
```

### Verify Build

```bash
# Full test suite (should take ~4 seconds)
pytest -q

# Expected output:
# 152 passed, 2486 warnings in ~4s
```

### Try Money-Only Demo

```bash
# Run monetary exchange scenario
python scripts/run_headless.py scenarios/money_test_basic.yaml --seed 42 --max-ticks 20

# Or with visualization:
python main.py scenarios/money_test_basic.yaml --seed 42
```

---

## Review Strategy

### Time Budget Recommendation

| Phase | Files | Time Estimate | Priority |
|-------|-------|---------------|----------|
| Background | Read docs | 15 min | High |
| Phase 2a | 5 files + 2 tests | 30 min | Medium |
| Phase 2b | 1 file + 1 test | 45 min | **Critical** |
| Phase 2c | 3 files + 1 test | 30 min | High |
| Documentation | 2 rule files | 15 min | Medium |
| **Total** | **19 files** | **~2.5 hours** | |

**Priority areas:**
1. 🔴 **Critical**: Economic correctness in `matching.py` (Phase 2b)
2. 🟡 **High**: Conservation laws in `execute_trade_generic()`
3. 🟡 **High**: Backward compatibility (legacy tests passing)
4. 🟢 **Medium**: Test coverage and documentation

---

## Phase-by-Phase Review

### Phase 2a - Data Structures (No Behavior Change)

**Goal**: Verify that generalizations don't break legacy code

#### Files to Review

**`src/vmt_engine/econ/utility.py` (+162 lines)**

**What to check:**
- [ ] `u_goods()` implementation matches legacy `u()` behavior
- [ ] `mu_A()` and `mu_B()` correctly extract from `mu()` tuple
- [ ] `u_total()` adds quasilinear money utility: `u_goods + λ*M`
- [ ] `mu()` implemented for both `UCES` and `ULinear`

**Key code sections:**
```python
# Lines 41-88: New money-aware API methods
def u_goods(self, A, B):
    return self.u(A, B)  # Routes to legacy for compatibility

# Lines 178-220: UCES.mu() implementation
def mu(self, A, B, eps=1e-12):
    # Analytic marginal utilities for CES
    
# Lines 325-357: u_total() with quasilinear money
def u_total(inventory, params):
    u_goods = utility.u_goods(A, B)
    u_money = lambda_money * M
    return u_goods + u_money
```

**Test verification:**
```bash
pytest tests/test_utility_money.py -v
# All 16 tests should pass
```

---

**`src/vmt_engine/systems/quotes.py` (+149 lines)**

**What to check:**
- [ ] `compute_quotes()` returns dict with 8+ keys
- [ ] Barter quotes: ask_A_in_B, bid_A_in_B, ask_B_in_A, bid_B_in_A
- [ ] Monetary quotes: ask_A_in_M, bid_A_in_M, ask_B_in_M, bid_B_in_M
- [ ] `filter_quotes_by_regime()` correctly hides keys based on regime
- [ ] Monetary prices based on MU: `price = (MU / λ) × money_scale`

**Key code sections:**
```python
# Lines 25-118: compute_quotes() - all pairs
# Lines 121-161: filter_quotes_by_regime()
# Lines 164-186: refresh_quotes_if_needed() with regime filter
```

**Test verification:**
```bash
pytest tests/test_quotes_money.py -v
# All 20 tests should pass
```

---

**`src/vmt_engine/core/agent.py`**

**What to check:**
- [ ] `quotes` changed from `Quote` to `dict[str, float]`
- [ ] Default is empty dict (not None)

**Code:**
```python
# Line 24
quotes: dict[str, float] = field(default_factory=dict)
```

---

**Consumer Files (3 files)**

**What to check:**
- [ ] All use `dict.get(key, default)` not direct attribute access
- [ ] No `agent.quotes.ask_A_in_B` (would fail with dict)
- [ ] All use `agent.quotes.get('ask_A_in_B', 0.0)`

**Files:**
- `src/vmt_engine/systems/housekeeping.py` (lines 13-24)
- `src/vmt_engine/systems/matching.py` (lines 40-48, legacy functions)
- `src/vmt_engine/systems/_trade_attempt_logger.py` (lines 40-44)
- `src/telemetry/db_loggers.py` (lines 121-125)

---

**Gate Verification:**
```bash
# All baseline tests must pass
pytest -q -k "not money" 
# Should be ~95 passing (all non-Phase2 tests)

# Legacy scenario unchanged
python scripts/run_headless.py scenarios/three_agent_barter.yaml --seed 42 --max-ticks 10
# Verify: runs without errors
```

---

### Phase 2b - Generic Matching (MOST CRITICAL)

**Goal**: Verify economic correctness and search algorithm

#### **🔴 CRITICAL REVIEW: Economic Correctness**

**File**: `src/vmt_engine/systems/matching.py` lines 385-614

**What to verify very carefully:**

##### ❌ The plan said (line 161):
> "Return the block with maximal total surplus (ΔU_i + ΔU_j)"

##### ✅ The code actually does:
> "Return the FIRST block where both ΔU_i > 0 AND ΔU_j > 0"

**Why this matters:**
- Utilities are **ordinal** (order matters, not magnitude)
- Cannot meaningfully compare ΔU_i and ΔU_j (different utility scales)
- Agents don't care about partner's surplus, only their own
- Maximizing total surplus is economically illiterate

**Code to check** (lines 474-477, 501-503, etc.):
```python
if surplus_i > epsilon and surplus_j > epsilon:
    # Return FIRST mutually beneficial trade found
    return (-dA, dB, 0, dA, -dB, 0, surplus_i, surplus_j)
    # ↑ Immediate return - no further searching!
```

**What you should NOT see:**
```python
# ❌ BAD (not in our code):
best_total_surplus = 0.0
for ...:
    if total_surplus > best_total_surplus:
        best_trade = ...
return best_trade  # After trying everything
```

**What you SHOULD see:**
```python
# ✅ GOOD (our actual code):
for dA in range(1, dA_max + 1):
    for price in generate_price_candidates(...):
        if both_improve:
            return trade  # Immediate return
return None  # Only if nothing works
```

##### Verification Questions

- [ ] Does code return immediately on first success? (Yes ✓)
- [ ] Is there any `max_surplus` tracking? (No ✓)
- [ ] Is there any exhaustive search? (No ✓)
- [ ] Does it match legacy algorithm strategy? (Yes ✓)

---

#### Search Strategy Verification

**Expected behavior** (matching legacy):

```
For each exchange pair (A<->B, A<->M, or B<->M):
  For dA = 1 to dA_max:
    For price in generate_price_candidates(ask, bid, dA):  # Sorted low→high
      Compute dB or dM = floor(price × dA + 0.5)  # Round-half-up
      
      Check feasibility:
        - Inventory constraints (non-negative after trade)
        - Utility improvement: ΔU_i > ε AND ΔU_j > ε
      
      If feasible:
        return trade  ← EARLY EXIT
  
  return None  # No trade found for this pair
```

**Code locations to verify:**
- Lines 445-503: A↔B pair (barter)
- Lines 505-557: A↔M pair (monetary)
- Lines 559-611: B↔M pair (monetary)

---

#### Conservation Law Enforcement

**File**: `src/vmt_engine/systems/matching.py` lines 688-735

**What to check:**
```python
def execute_trade_generic(agent_i, agent_j, trade):
    dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade
    
    # VERIFY: Assertions present
    assert dA_i + dA_j == 0  # Good A conserved
    assert dB_i + dB_j == 0  # Good B conserved
    assert dM_i + dM_j == 0  # Money conserved
    
    # Apply updates...
    
    # VERIFY: Non-negativity checks
    assert agent_i.inventory.A >= 0
    assert agent_i.inventory.M >= 0
    # ... (all 6 inventories)
```

**Questions:**
- [ ] Are all conservation assertions present? (Yes ✓)
- [ ] Are all non-negativity assertions present? (Yes ✓)
- [ ] Are inventory_changed flags set? (Yes ✓)

---

#### `find_best_trade()` Logic

**File**: `src/vmt_engine/systems/matching.py` lines 617-666

**What to check:**
```python
def find_best_trade(agent_i, agent_j, exchange_regime, params):
    # Determine allowed pairs
    if exchange_regime == "barter_only":
        candidate_pairs = ["A<->B"]
    elif exchange_regime == "money_only":
        candidate_pairs = ["A<->M", "B<->M"]
    elif exchange_regime == "mixed":
        candidate_pairs = ["A<->B", "A<->M", "B<->M"]
    
    # Try each pair in ORDER
    for pair in candidate_pairs:
        trade = find_compensating_block_generic(...)
        if trade is not None:
            return (pair, trade)  # Return FIRST success
    
    return None  # No trade in any pair
```

**Questions:**
- [ ] Correct regime filtering? (Yes ✓)
- [ ] Returns first successful pair? (Yes ✓)
- [ ] No maximization across pairs? (Yes ✓)

---

**Test Verification:**
```bash
pytest tests/test_matching_money.py -v
# All 14 tests should pass
# Pay attention to:
# - test_barter_only_regime
# - test_money_only_regime  
# - test_conservation_monetary
```

---

### Phase 2c - Integration

**Goal**: Verify end-to-end functionality and backward compatibility

#### **`src/vmt_engine/systems/trading.py` (+99 lines)**

**What to check:**

**Regime detection** (lines 13-36):
```python
def execute(self, sim):
    exchange_regime = sim.params.get("exchange_regime", "barter_only")
    use_generic = exchange_regime in ("money_only", "mixed")
    
    for id_i, id_j in pairs:
        if use_generic:
            self._trade_generic(...)  # Phase 2 code path
        else:
            trade_pair(...)  # Legacy code path (preserved)
```

- [ ] Legacy path preserved for barter_only? (Yes ✓)
- [ ] Generic path used for money_only and mixed? (Yes ✓)

**Generic trade execution** (lines 38-62):
```python
def _trade_generic(self, agent_i, agent_j, sim):
    result = find_best_trade(agent_i, agent_j, exchange_regime, sim.params)
    
    if result is None:
        # Set cooldown on both agents
        cooldown_until = sim.tick + sim.params['trade_cooldown_ticks']
        agent_i.trade_cooldowns[agent_j.id] = cooldown_until
        agent_j.trade_cooldowns[agent_i.id] = cooldown_until
        return
    
    pair_name, trade = result
    execute_trade_generic(agent_i, agent_j, trade)
    self._log_generic_trade(...)  # Log with dM
```

- [ ] Cooldown set on failure? (Yes ✓)
- [ ] Trade executed on success? (Yes ✓)
- [ ] Telemetry includes dM? (Yes ✓)

---

#### **`src/vmt_engine/simulation.py` (M inventory fix)**

**What to check** (lines 123-171):

**Before:**
```python
# M inventory was ignored!
inventory = Inventory(A=inv_A[i], B=inv_B[i])  # M defaulted to 0
```

**After:**
```python
inv_M = self.config.initial_inventories.get('M', 0)

# Convert to list if scalar
if isinstance(inv_M, int):
    inv_M = [inv_M] * n_agents

M_val = inv_M[i] if isinstance(inv_M, list) else inv_M
inventory = Inventory(A=inv_A[i], B=inv_B[i], M=M_val)
```

- [ ] Handles scalar M? (Yes ✓)
- [ ] Handles list M? (Yes ✓)
- [ ] Defaults to 0 if missing? (Yes ✓)

---

#### **`src/telemetry/db_loggers.py`**

**What to check** (lines 203-226, 391-395):

**Updated signature:**
```python
def log_trade(self, tick, x, y, buyer_id, seller_id,
              dA, dB, price, direction, dM=0):  # Added dM parameter
```

- [ ] dM parameter with default 0? (Yes ✓)
- [ ] Backward compatible? (Yes - existing callers work)

**Updated INSERT:**
```sql
INSERT INTO trades
(run_id, tick, x, y, buyer_id, seller_id, dA, dB, dM, price, direction)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

- [ ] dM column included? (Yes ✓)
- [ ] Matches database schema? (Yes, column exists from Phase 1)

---

#### **`src/vmt_pygame/renderer.py` (money display)**

**What to check** (lines 241-252, 279-293, 303-336):

**Conditional money display:**
```python
has_money = (agent.inventory.M > 0 or 
             sim.params.get('exchange_regime') in ('money_only', 'mixed'))

if has_money:
    inv_text = f"A:{A} B:{B} M:{M}"
else:
    inv_text = f"A:{A} B:{B}"
```

- [ ] Only shows M when relevant? (Yes ✓)
- [ ] Handles both regimes? (Yes ✓)

**Monetary trade formatting:**
```python
if dM != 0:
    # "Agent 1 buys 3A from 2 for 20M @ 6.67"
    trade_text = f"{buyer} buys {dA}A from {seller} for {dM}M @ {price:.2f}"
else:
    # "Agent 1 buys 3A from 2 for 5B @ 1.67"
    trade_text = f"{buyer} buys {dA}A from {seller} for {dB}B @ {price:.2f}"
```

- [ ] Distinguishes monetary vs barter? (Yes ✓)
- [ ] Uses dM from trade dict? (Yes ✓)

---

### Integration Tests Review

#### **`tests/test_money_phase2_integration.py` (7 tests)**

**What to verify:**

**Test 1: Monetary trades occur**
```python
# Query database for trades with dM != 0
cursor.execute("SELECT COUNT(*) FROM trades WHERE run_id = ? AND dM != 0")
assert count > 0
```
- [ ] Actually checks dM column? (Yes ✓)

**Test 2: Barter blocked**
```python
# Query for barter trades (dB != 0 and dM == 0)
cursor.execute("SELECT COUNT(*) FROM trades WHERE ... AND dB != 0 AND dM == 0")
assert count == 0
```
- [ ] Correct SQL logic for barter detection? (Yes ✓)

**Test 3: Money conservation**
```python
initial_M = sum(a.inventory.M for a in sim.agents)
sim.run(max_ticks=20)
final_M = sum(a.inventory.M for a in sim.agents)
assert initial_M == final_M
```
- [ ] Checks total money before and after? (Yes ✓)

**Test 4: Determinism**
```python
sim1 = Simulation(scenario, seed=42)
sim2 = Simulation(scenario, seed=42)
# ... run both
assert final_inventories_1 == final_inventories_2
```
- [ ] Uses same seed for both runs? (Yes ✓)
- [ ] Compares final state? (Yes ✓)

**Run tests:**
```bash
pytest tests/test_money_phase2_integration.py -v
# All 7 should pass
```

---

### Scenario Review

#### **`scenarios/money_test_basic.yaml`**

**What to check:**

- [ ] **Agent diversity**: Different utilities for each agent?
  - Agent 1: `{vA: 3.0, vB: 1.0}`
  - Agent 2: `{vA: 1.0, vB: 3.0}` (complementary)
  - ✅ Different preferences guarantee gains from trade

- [ ] **Normalization**: vA + vB = 1.0? (Actually: 3+1=4, 1+3=4)
  - ⚠️ **Note**: These use non-normalized values for clarity
  - Still valid as long as preferences differ

- [ ] **Endowments diverse**: `A: [10, 0, 5]`, `B: [5, 5, 10]`, `M: [0, 100, 50]`?
  - ✅ Heterogeneous

- [ ] **Test conventions**:
  - `interaction_radius: 1` ✅
  - `move_budget_per_tick: 1` ✅

- [ ] **Money system params**:
  - `exchange_regime: "money_only"` ✅
  - `money_mode: "quasilinear"` ✅
  - `lambda_money: 1.0` ✅

---

## Backward Compatibility Verification

### Critical Tests to Run

```bash
# Test 1: All legacy tests pass
pytest tests/test_barter_integration.py -v
pytest tests/test_m1_integration.py -v
pytest tests/test_mode_integration.py -v
pytest tests/test_performance.py -v
# All should be green

# Test 2: Legacy scenarios identical
python -c "
from src.scenarios.loader import load_scenario
from src.vmt_engine.simulation import Simulation
from src.telemetry.config import LogConfig

sim = Simulation(load_scenario('scenarios/three_agent_barter.yaml'), 
                 seed=42, log_config=LogConfig(use_database=False))
sim.run(max_ticks=10)

for a in sorted(sim.agents, key=lambda x: x.id):
    print(f'Agent {a.id}: A={a.inventory.A}, B={a.inventory.B}')
"
# Compare output to baseline (should be identical)
```

### Default Behavior Checklist

- [ ] `exchange_regime` defaults to `"barter_only"`?
  - Check: `src/scenarios/loader.py` line 66
  - ✅ Yes: `exchange_regime=params_data.get('exchange_regime', "barter_only")`

- [ ] M inventory defaults to 0 if not specified?
  - Check: `src/vmt_engine/simulation.py` line 126
  - ✅ Yes: `inv_M = self.config.initial_inventories.get('M', 0)`

- [ ] Monetary quotes filtered in barter_only?
  - Check: `src/vmt_engine/systems/quotes.py` lines 136-141
  - ✅ Yes: Returns only keys with `'in_B'` or `'in_A'`

- [ ] Legacy trade_pair() still used for barter_only?
  - Check: `src/vmt_engine/systems/trading.py` line 36
  - ✅ Yes: `trade_pair(...)` called when not using generic matching

---

## Documentation Review

### Cursor Rules Updates

#### `.cursor/rules/scenarios-telemetry.mdc` (+97 lines)

**What was added:**

**Section: "Creating New Test Scenarios (STRICT REQUIREMENTS)"** (lines 77-158)

**Key points to verify:**
- [ ] Complementary pairing algorithm clearly documented?
- [ ] Strict normalization requirements (vA+vB=1.0)?
- [ ] Test parameter defaults (interaction_radius=1, move_budget=1)?
- [ ] Economic rationale explained?

**Example algorithm (lines 83-98):**
```
1. Agent 1: Random utility (vA ~ Uniform(0.1, 0.9), vB = 1 - vA)
2. Agent 2: Complementary (vA, vB) → (vB, vA)
3. Agent 3: Random utility (new draw)
4. Agent 4: Complementary to Agent 3
... continue pattern
```

**Why this is important:**
- Homogeneous agents → no gains from trade → tests fail non-deterministically
- Discovered when initial scenario had identical utilities
- Critical for future test creation

---

#### `.cursor/rules/gui-development.mdc` (+28 lines)

**What was added:**

**Section: "Scenario Builder - Auto-Generate Diverse Agents"** (lines 23-49)

**Feature spec:**
- Checkbox in GUI Basic Settings tab
- Auto-generates utilities using complementary pairing
- Auto-generates random endowments
- Implementation location: `src/vmt_launcher/scenario_builder.py`

**Not yet implemented** - marked as "Feature request (not yet implemented)"

---

## Common Review Pitfalls

### ❌ Don't Get Confused By

1. **Multiple utility methods with similar names**
   - `u()` - Legacy (deprecated but still works)
   - `u_goods()` - New canonical (goods only)
   - `u_total()` - Top-level (goods + money)
   - **They coexist for backward compatibility**

2. **Quote dict keys with similar patterns**
   - `ask_A_in_B` vs `ask_A_in_M` (different pairs)
   - `ask_A_in_B` vs `bid_A_in_B` (different sides)
   - **Filter function hides irrelevant keys**

3. **Trade tuple with 8 elements**
   - `(dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)`
   - **Explicit representation makes conservation checking clear**

4. **Deprecation warnings in test output**
   - 2,486 warnings from `create_utility()` in legacy tests
   - **Expected and harmless** - just from test helper functions

### ✅ Do Focus On

1. **Economic correctness** - First trade, not max surplus
2. **Conservation enforcement** - All assertions present
3. **Backward compatibility** - Legacy tests green
4. **Search algorithm** - Matches legacy strategy

---

## Spot Checks (Quick Validation)

### 5-Minute Smoke Test

```bash
# 1. Tests pass
pytest -q
# Expect: 152 passed in ~4s

# 2. Money scenario runs
python scripts/run_headless.py scenarios/money_test_basic.yaml --seed 42 --max-ticks 10
# Expect: Completes without error

# 3. Legacy scenario unchanged
python scripts/run_headless.py scenarios/three_agent_barter.yaml --seed 42 --max-ticks 10
# Expect: Completes without error

# 4. Check trade types
sqlite3 logs/telemetry.db "SELECT DISTINCT direction FROM trades LIMIT 10"
# Expect: Mix of directions including '_for_M' if money scenario ran
```

### Detailed Verification (If Issues Found)

```bash
# Run specific test suites
pytest tests/test_utility_money.py -v
pytest tests/test_quotes_money.py -v
pytest tests/test_matching_money.py -v
pytest tests/test_money_phase2_integration.py -v

# Check conservation in database
sqlite3 logs/telemetry.db "
  SELECT tick, buyer_id, seller_id, dA, dB, dM, direction 
  FROM trades 
  WHERE dM != 0 
  LIMIT 5
"
# Verify dM values are reasonable (> 0, < 1000)

# Verify money conservation
python -c "
import sqlite3
conn = sqlite3.connect('logs/telemetry.db')

# Get initial inventories
cursor = conn.execute('SELECT inventory_M FROM agent_snapshots WHERE tick=0')
initial = sum(row[0] for row in cursor)

# Get final inventories
cursor = conn.execute('SELECT inventory_M FROM agent_snapshots WHERE tick=(SELECT MAX(tick) FROM agent_snapshots)')
final = sum(row[0] for row in cursor)

print(f'Initial M: {initial}, Final M: {final}, Conserved: {initial == final}')
"
```

---

## Questions to Ask During Review

### Architecture

- [ ] Does the three-regime design make sense?
- [ ] Is the quasilinear utility formulation appropriate?
- [ ] Should Phase 3 extend this or replace parts?

### Economic Theory

- [ ] Is the "first acceptable trade" approach economically sound?
- [ ] Are monetary quote prices (MU/λ) correct?
- [ ] Should money utility be linear, or allow curvature?

### Code Quality

- [ ] Are the function names clear and consistent?
- [ ] Is the code adequately commented?
- [ ] Are magic numbers avoided (all params from config)?

### Testing

- [ ] Is test coverage sufficient?
- [ ] Are mock tests realistic enough?
- [ ] Should integration tests cover more scenarios?

### Performance

- [ ] Any concerns about nested loops in matching?
- [ ] Should price candidate generation be optimized?
- [ ] Monitor TPS in future large scenarios?

---

## Red Flags (What Would Fail Review)

### 🚨 Showstoppers

- ❌ Tests not passing (any failures)
- ❌ Legacy scenarios produce different results
- ❌ Conservation laws not enforced
- ❌ Economic correctness violated (maximizing cardinal utilities)

### ⚠️ Serious Concerns

- ❌ Missing non-negativity checks
- ❌ Non-deterministic behavior
- ❌ Performance regression > 20%
- ❌ Incomplete backward compatibility

### ⚡ Minor Issues (Fixable)

- Documentation typos
- Missing edge case tests
- Unclear variable names
- Redundant code

**Current Status**: ✅ No red flags or serious concerns detected

---

## Approval Checklist

Before approving, verify:

- [ ] Read `PHASE2_IMPLEMENTATION_STATUS.md` (understand deviations)
- [ ] Reviewed economic correctness section (critical!)
- [ ] Spot-checked conservation enforcement
- [ ] Verified backward compatibility (legacy tests green)
- [ ] Ran money_only scenario successfully
- [ ] Confirmed test coverage adequate (57 new tests)
- [ ] Reviewed documentation updates (Cursor Rules)
- [ ] No performance concerns (4s test suite acceptable)

**If all checked: ✅ Approve for merge**

---

## Post-Merge Actions

1. Update `docs/BIG/PHASE1_COMPLETION_SUMMARY.md` with new test count
2. Mark Phase 2 checklists as complete
3. Archive or mark complete:
   - `docs/BIG/implement/phase2_atomic_implementation_plan.md`
   - `docs/BIG/implement/phase2_atomic_checklist.md`
4. Begin Phase 3 planning (KKT λ optimization)

---

## Contact / Questions

**Implementation details**: See `PHASE2_IMPLEMENTATION_STATUS.md`  
**Economic theory**: See `docs/2_technical_manual.md`  
**Type contracts**: See `docs/4_typing_overview.md`  
**Architecture**: See `.cursor/rules/core-invariants.mdc`

**For questions during review**: Reference line numbers and specific files in comments

