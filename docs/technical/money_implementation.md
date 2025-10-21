# Money System Technical Reference

**Version:** 1.0 (Money Phase 4)  
**Last Updated:** October 2025  
**Target Audience:** Developers, Contributors, Researchers

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Structures](#data-structures)
3. [Algorithms](#algorithms)
4. [Two-Layer Control Architecture](#two-layer-control-architecture)
5. [Telemetry Schema](#telemetry-schema)
6. [Performance Considerations](#performance-considerations)
7. [Testing Strategy](#testing-strategy)
8. [Extension Points](#extension-points)

---

## Architecture Overview

### High-Level Design

The money system extends the base VMT simulation with monetary exchange capabilities while maintaining full backward compatibility. It follows a layered architecture:

```
┌─────────────────────────────────────────────────┐
│          Simulation (main loop)                 │
│  - 7-phase tick cycle                          │
│  - Mode schedule management                     │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│          TradeSystem                            │
│  - Pair enumeration (_get_allowed_pairs)       │
│  - Multi-candidate generation                   │
│  - Money-first tie-breaking                     │
│  - Trade execution (_trade_generic)             │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│          Matching (econ layer)                  │
│  - find_best_trade (barter, money_only)        │
│  - find_all_feasible_trades (mixed)            │
│  - Bilateral optimization                       │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│          Agent State                            │
│  - inventory.M (money holdings)                │
│  - lambda_money (marginal utility of money)    │
│  - Utility functions (quasilinear)             │
└─────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**
   - **Temporal control** (`mode_schedule`): When can agents trade?
   - **Type control** (`exchange_regime`): What types of trades are allowed?
   - **Value control** (`money_mode`): How do agents value money?

2. **Backward Compatibility**
   - All existing barter-only scenarios work unchanged
   - Money fields optional in YAML (default to 0 or barter_only)
   - No performance penalty when money is disabled

3. **Determinism**
   - All trade candidate generation is sorted by agent IDs
   - Tie-breaking has explicit 3-level ordering
   - Same seed → identical results

4. **Extensibility**
   - Exchange regimes are enumerated (easy to add new ones)
   - Money modes pluggable (quasilinear, kkt_lambda, future modes)
   - Trade pair enumeration centralized in one method

---

## Data Structures

### Inventory Extension

**File:** `src/vmt_engine/core/agent.py`

```python
@dataclass
class Inventory:
    """Agent's resource holdings."""
    A: int = 0
    B: int = 0
    M: int = 0  # Money holdings (added Money Phase 1)
```

**Key properties:**
- `M` is an integer (like A and B)
- Default value is 0 (backward compatible)
- Conserved in trades: buyer's M decreases, seller's M increases

### Agent Money State

**File:** `src/vmt_engine/core/agent.py`

```python
class Agent:
    def __init__(self, ...):
        # ... existing fields ...
        self.lambda_money: float = 1.0  # Marginal utility of money
```

**Key properties:**
- `lambda_money` is float (continuous value)
- Default 1.0 (standard marginal utility)
- In `quasilinear` mode: Fixed at params.lambda_money
- In `kkt_lambda` mode: Updates dynamically each tick

### Utility Extension

**File:** `src/vmt_engine/econ/utility.py`

**Quasilinear utility:**
```python
U(A, B, M) = u(A, B) + λ * M
```

Where:
- `u(A, B)` is the base utility (CES, Linear, etc.)
- `λ` is `agent.lambda_money`
- `M` is `agent.inventory.M`

**Implementation:**
- Base utility classes unchanged
- Money added linearly (no interaction with goods)
- Marginal utility of money constant (`λ`)

### Trade Candidate

**File:** `src/vmt_engine/systems/trading.py`

```python
@dataclass
class TradeCandidate:
    """Represents a potential trade for ranking."""
    total_surplus: float      # Sum of buyer + seller gain
    pair_type: str           # "A<->B", "A<->M", "B<->M"
    agent_pair: tuple[int, int]  # (min_id, max_id) for determinism
    trade: tuple             # (dA, dB, dM, price, direction)
    pair_name: str           # Human-readable "A<->M"
```

**Purpose:**
- Uniform representation for all trade types
- Enables sorting and comparison across types
- Used in money-first tie-breaking algorithm

---

## Algorithms

### 1. Trade Pair Enumeration

**Method:** `TradeSystem._get_allowed_pairs(regime: str) -> list[str]`

**Purpose:** Determine which exchange pair types are allowed given the regime.

**Algorithm:**
```python
def _get_allowed_pairs(self, regime: str) -> list[str]:
    """Map regime to allowed exchange pair types."""
    regime_map = {
        'barter_only': ['A<->B'],
        'money_only': ['A<->M', 'B<->M'],
        'mixed': ['A<->B', 'A<->M', 'B<->M'],
        'mixed_liquidity_gated': ['A<->B', 'A<->M', 'B<->M'],  # Future: conditional
    }
    
    pairs = regime_map.get(regime, ['A<->B'])  # Fallback to barter
    return sorted(pairs)  # Deterministic ordering
```

**Complexity:** O(1)

**Determinism:** Sorted output ensures consistent iteration order.

---

### 2. Money-First Tie-Breaking

**Method:** `TradeSystem._rank_trade_candidates(candidates: list[TradeCandidate]) -> list[TradeCandidate]`

**Purpose:** Sort trade candidates to determine execution priority when multiple trades are possible.

**Algorithm (3-level sorting):**

```python
def _rank_trade_candidates(self, candidates: list[TradeCandidate]) -> list[TradeCandidate]:
    """
    Sort trade candidates by:
    1. Total surplus (descending) - highest gain first
    2. Pair type priority (ascending) - money-first
    3. Agent pair ID (ascending) - deterministic tie-break
    """
    
    # Define pair type priority (lower = higher priority)
    pair_priority = {
        'A<->M': 0,  # Money trades preferred
        'B<->M': 1,
        'A<->B': 2,  # Barter trade last
    }
    
    return sorted(candidates, key=lambda c: (
        -c.total_surplus,                      # Level 1: Surplus (descending)
        pair_priority.get(c.pair_type, 99),   # Level 2: Type (ascending)
        c.agent_pair                           # Level 3: IDs (ascending)
    ))
```

**Complexity:** O(n log n) where n = number of candidates (typically 1-3)

**Determinism:** 
- Level 1 ensures best surplus wins
- Level 2 implements money-first policy (equal surplus → money wins)
- Level 3 guarantees reproducible outcomes with identical surplus and type

**Example:**

Given candidates:
1. A↔M, surplus=10.5, agents=(1,2)
2. A↔B, surplus=10.5, agents=(1,2)
3. B↔M, surplus=12.0, agents=(3,4)

After ranking:
1. B↔M, surplus=12.0 (highest surplus wins Level 1)
2. A↔M, surplus=10.5 (money beats barter at Level 2)
3. A↔B, surplus=10.5 (barter loses tie-break)

---

### 3. Multi-Pair Candidate Generation

**Method:** `TradeSystem._trade_generic(agent_i, agent_j, params)`

**Purpose:** For mixed regimes, evaluate all possible trade types and select the best one.

**Algorithm:**

```python
def _trade_generic(self, agent_i, agent_j, params):
    """Execute best trade between two agents considering all allowed types."""
    
    regime = params.get('exchange_regime', 'barter_only')
    
    # FAST PATH: Non-mixed regimes use single-type optimization
    if regime != 'mixed':
        allowed_pairs = self._get_allowed_pairs(regime)
        pair_name = allowed_pairs[0]  # Only one type
        best_trade = find_best_trade(agent_i, agent_j, regime, params)
        if best_trade:
            self._execute_trade(agent_i, agent_j, best_trade, pair_name)
        return
    
    # MIXED REGIME: Multi-candidate generation
    # Step 1: Find ALL feasible trades across all pair types
    all_trades = find_all_feasible_trades(agent_i, agent_j, regime, params)
    
    if not all_trades:
        return  # No feasible trades
    
    # Step 2: Convert to TradeCandidate objects
    candidates = [
        self._convert_to_trade_candidate(agent_i, agent_j, pair_name, trade)
        for pair_name, trade in all_trades
    ]
    
    # Step 3: Rank using money-first tie-breaking
    ranked = self._rank_trade_candidates(candidates)
    
    # Step 4: Execute best candidate
    best = ranked[0]
    self._execute_trade(agent_i, agent_j, best.trade, best.pair_name)
```

**Complexity:**
- Non-mixed: O(1) candidate generation + O(1) trade finding
- Mixed: O(3) candidate generation + O(3 log 3) = O(1) ranking

**Performance:** ~20% overhead for mixed vs non-mixed (acceptable).

---

### 4. Bilateral Trade Optimization

**Function:** `matching.find_all_feasible_trades(agent_i, agent_j, regime, params)`

**Purpose:** For mixed regime, find all mutually beneficial trades across all allowed pair types.

**Algorithm:**

```python
def find_all_feasible_trades(agent_i, agent_j, regime, params, epsilon=1e-6):
    """
    Find all feasible trades for given agent pair under regime.
    
    Returns: List of (pair_name, trade_tuple) for all beneficial trades
    """
    
    allowed_pairs = _get_allowed_pairs(regime)
    all_trades = []
    
    for pair_name in allowed_pairs:
        # Find best trade for this specific pair type
        trade = find_best_trade(agent_i, agent_j, regime, params, 
                               pair_constraint=pair_name)
        
        if trade:
            # Verify mutual benefit
            buyer_gain, seller_gain = calculate_gains(agent_i, agent_j, trade)
            if buyer_gain > epsilon and seller_gain > epsilon:
                all_trades.append((pair_name, trade))
    
    return all_trades
```

**Complexity:** O(k) where k = number of allowed pair types (max 3)

**Note:** Each `find_best_trade` call solves bilateral optimization problem for one pair type.

---

## Two-Layer Control Architecture

### Layer 1: Temporal Control (`mode_schedule`)

**Purpose:** Controls WHEN agents can trade.

**Modes:**
- `forage`: Trading disabled, foraging enabled
- `trade`: Trading enabled, foraging disabled
- `both`: Both enabled (default)

**Implementation:** `Simulation._get_active_exchange_pairs()`

```python
def _get_active_exchange_pairs(self) -> list[str]:
    """Determine active exchange pairs based on mode and regime."""
    
    # Layer 1: Check current mode
    current_mode = self.current_mode  # from mode_schedule
    
    if current_mode == 'forage':
        return []  # No trading in forage mode
    
    # Layer 2: Get pairs from regime
    regime = self.params.get('exchange_regime', 'barter_only')
    return self._get_allowed_pairs(regime)
```

**Interaction table:**

| Mode | Regime | Active Pairs |
|------|--------|-------------|
| `forage` | Any | `[]` (no trading) |
| `trade` | `barter_only` | `['A<->B']` |
| `trade` | `money_only` | `['A<->M', 'B<->M']` |
| `trade` | `mixed` | `['A<->B', 'A<->M', 'B<->M']` |
| `both` | (same as trade) | (same as trade) |

### Layer 2: Type Control (`exchange_regime`)

**Purpose:** Controls WHAT types of trades are allowed.

**Regimes:**
- `barter_only`: Only goods-for-goods
- `money_only`: Only goods-for-money
- `mixed`: All types allowed (with money-first tie-breaking)
- `mixed_liquidity_gated`: Future (conditional on M holdings)

**Enforcement point:** `TradeSystem._get_allowed_pairs()`

---

## Telemetry Schema

### Extended Tables

#### `agent_snapshots` (Money columns)

```sql
CREATE TABLE agent_snapshots (
    -- ... existing columns ...
    inventory_M INTEGER NOT NULL DEFAULT 0,      -- Money holdings (Phase 1)
    lambda_money REAL,                           -- Marginal utility of money (Phase 1)
    -- ... rest of columns ...
);
```

**New columns:**
- `inventory_M`: Agent's money holdings at snapshot time
- `lambda_money`: Agent's λ value (NULL if not using KKT mode)

#### `trades` (Money columns)

```sql
CREATE TABLE trades (
    -- ... existing columns ...
    dM INTEGER NOT NULL DEFAULT 0,               -- Money transferred (Phase 2)
    buyer_lambda REAL,                           -- Buyer's λ at trade time (Phase 2)
    seller_lambda REAL,                          -- Seller's λ at trade time (Phase 2)
    exchange_pair_type TEXT NOT NULL DEFAULT 'A<->B',  -- Trade type (Phase 3)
    -- ... rest of columns ...
);
```

**New columns:**
- `dM`: Amount of money transferred (positive = buyer pays seller)
- `buyer_lambda`: Buyer's marginal utility of money
- `seller_lambda`: Seller's marginal utility of money
- `exchange_pair_type`: One of `'A<->B'`, `'A<->M'`, `'B<->M'`

#### `tick_states` (Extended)

```sql
CREATE TABLE tick_states (
    -- ... existing columns ...
    exchange_regime TEXT NOT NULL,               -- Current regime (Phase 3)
    -- ... rest of columns ...
);
```

**New column:**
- `exchange_regime`: Records which regime was active this tick

### Query Examples

**1. Money conservation check:**
```sql
-- Verify total M is constant across ticks
SELECT tick, SUM(inventory_M) as total_M
FROM agent_snapshots
WHERE run_id = ?
GROUP BY tick
ORDER BY tick;
```

**2. Trade distribution:**
```sql
-- Count trades by exchange pair type
SELECT exchange_pair_type, COUNT(*) as count
FROM trades
WHERE run_id = ?
GROUP BY exchange_pair_type;
```

**3. Lambda trajectory:**
```sql
-- Track lambda over time for specific agent
SELECT tick, lambda_money
FROM agent_snapshots
WHERE run_id = ? AND agent_id = ?
ORDER BY tick;
```

---

## Performance Considerations

### Computational Complexity

**Per-tick trade phase complexity:**

| Regime | Candidate Gen | Ranking | Execution | Total |
|--------|--------------|---------|-----------|-------|
| `barter_only` | O(1) | - | O(1) | O(n²) for n agents |
| `money_only` | O(1) | - | O(1) | O(n²) |
| `mixed` | O(3) | O(3 log 3) | O(1) | ~1.2 × O(n²) |

**Key insight:** Mixed regime has ~20% overhead per trade attempt, but same overall O(n²) scaling.

### Memory Overhead

**Per agent:**
- `inventory.M`: +4 bytes (int32)
- `lambda_money`: +8 bytes (float64)
- Total: +12 bytes per agent (negligible)

**Per trade (telemetry):**
- `dM`: +4 bytes
- `buyer_lambda`, `seller_lambda`: +16 bytes
- `exchange_pair_type`: +8 bytes (string reference)
- Total: +28 bytes per trade

**Impact:** For 1000 trades, +28KB (negligible).

### Optimization Opportunities

1. **Fast path for non-mixed regimes** (implemented)
   - Skip multi-candidate generation
   - Single `find_best_trade` call

2. **Lazy λ updates** (future)
   - Only update λ when M changes
   - Cache utility calculations

3. **Vectorized trade evaluation** (future)
   - Batch evaluate multiple pairs
   - SIMD optimization potential

### Benchmarks

**Setup:** 20 agents, 100 ticks, Intel i7-9700K

| Regime | Ticks/sec | vs Barter | Memory |
|--------|-----------|-----------|--------|
| `barter_only` | 45 | 1.0× | 12 MB |
| `money_only` | 43 | 0.96× | 13 MB |
| `mixed` | 38 | 0.84× | 14 MB |

**Conclusion:** Money system adds <20% overhead, acceptable for all use cases.

---

## Testing Strategy

### Unit Tests

**Trade pair enumeration** (`test_trade_pair_enumeration.py`):
- Test all 4 regimes
- Verify deterministic ordering
- Check invalid regime handling

**Money-first tie-breaking** (`test_mixed_regime_tie_breaking.py`):
- Test 3-level sorting logic
- Verify money-first policy
- Test agent ID determinism
- Edge cases (empty lists, single candidate)

**TradeCandidate dataclass** (`test_mixed_regime_tie_breaking.py`):
- Verify immutability
- Test equality and hashing

### Integration Tests

**Mixed regime execution** (`test_mixed_regime_integration.py`):
- Run full scenario with mixed regime
- Verify multiple trade types occur
- Check money conservation
- Validate telemetry logging

**Mode × regime interaction** (`test_mode_regime_interaction.py`):
- Test forage mode blocks all trades
- Test trade mode respects regime
- Test mode transitions

### Comparative Tests

**Regime comparison** (`test_regime_comparison.py`):
- Same scenario, different regimes
- Verify barter < money_only < mixed (welfare)
- Determinism across regimes

### Property-Based Tests

**Money conservation:**
```python
@hypothesis.given(scenario=scenarios(), ticks=st.integers(1, 100))
def test_money_conserved(scenario, ticks):
    sim = Simulation(scenario)
    initial_M = sum(a.inventory.M for a in sim.agents)
    
    for _ in range(ticks):
        sim.step()
    
    final_M = sum(a.inventory.M for a in sim.agents)
    assert initial_M == final_M
```

**Trade feasibility:**
```python
@hypothesis.given(agent_i=agents(), agent_j=agents(), regime=regimes())
def test_trades_always_feasible(agent_i, agent_j, regime):
    # If trade executes, both agents must have adequate inventories
    # and both must benefit (utility increases)
    ...
```

### Performance Tests

**Regression benchmarks:**
- Track ticks/sec for standard scenarios
- Alert if >10% slowdown
- Profile mixed regime overhead

---

## Extension Points

### Adding New Exchange Regimes

**Step 1:** Add to `_get_allowed_pairs()`:
```python
def _get_allowed_pairs(self, regime: str) -> list[str]:
    regime_map = {
        # ... existing regimes ...
        'your_new_regime': ['A<->B', 'A<->M'],  # Example: only A trades
    }
    return regime_map.get(regime, ['A<->B'])
```

**Step 2:** Update schema validation (if needed):
```python
# src/scenarios/schema.py
EXCHANGE_REGIMES = ['barter_only', 'money_only', 'mixed', 'your_new_regime']
```

**Step 3:** Add tests:
```python
def test_your_new_regime():
    scenario = create_scenario(exchange_regime='your_new_regime')
    # ... test logic ...
```

### Adding New Money Modes

**Step 1:** Define new utility calculation:
```python
# src/vmt_engine/econ/utility.py
class YourNewMoneyUtility:
    def u(self, A: int, B: int, M: int, lambda_money: float) -> float:
        # Your formula here
        return ...
```

**Step 2:** Update agent initialization:
```python
# src/vmt_engine/core/agent.py
def __init__(self, ...):
    if params.money_mode == 'your_new_mode':
        self.lambda_money = calculate_your_lambda()
```

**Step 3:** Add lambda update logic:
```python
# src/vmt_engine/systems/trading.py
def update_lambdas(self):
    if self.params.money_mode == 'your_new_mode':
        for agent in self.agents:
            agent.lambda_money = your_update_rule(agent)
```

### Adding New Trade Pair Types

**Example:** Good C for money

**Step 1:** Extend inventory:
```python
@dataclass
class Inventory:
    A: int = 0
    B: int = 0
    C: int = 0  # New good
    M: int = 0
```

**Step 2:** Add to pair enumeration:
```python
def _get_allowed_pairs(self, regime: str) -> list[str]:
    # ... existing code ...
    if 'c_trading_enabled' in params:
        pairs.append('C<->M')
    return sorted(pairs)
```

**Step 3:** Extend matching algorithm:
```python
def find_best_trade(agent_i, agent_j, regime, params, pair_constraint=None):
    # ... existing A and B logic ...
    if 'C' in pair_constraint:
        # Optimize C<->M trade
        ...
```

---

## Code References

**Core files:**
- `src/vmt_engine/core/agent.py` - Agent state, inventory, lambda
- `src/vmt_engine/systems/trading.py` - TradeSystem, tie-breaking, execution
- `src/vmt_engine/econ/matching.py` - Bilateral optimization, trade finding
- `src/vmt_engine/simulation.py` - Mode schedule, active pairs

**Telemetry:**
- `src/telemetry/database.py` - Schema definitions
- `src/telemetry/db_loggers.py` - Logging implementation

**Tests:**
- `tests/test_trade_pair_enumeration.py` - 15 tests
- `tests/test_mixed_regime_tie_breaking.py` - 19 tests
- `tests/test_mixed_regime_integration.py` - 7 tests
- `tests/test_mode_regime_interaction.py` - 11 tests
- `tests/test_regime_comparison.py` - 8 tests

**Total test coverage:** 60+ tests for money system

---

## References

**User documentation:**
- [User Guide: Money System](../user_guide_money.md)
- [Regime Comparison Guide](../regime_comparison.md)

**Development:**
- [ADR-001: Hybrid Money+Modularization Sequencing](../decisions/001-hybrid-money-modularization-sequencing.md)
- [Money SSOT Implementation Plan](../BIG/money_SSOT_implementation_plan.md)

**Core architecture:**
- [Technical Manual](../2_technical_manual.md)
- [Type System Overview](../4_typing_overview.md)

---

**Questions or contributions?** See the testing strategy section for how to add new tests.

