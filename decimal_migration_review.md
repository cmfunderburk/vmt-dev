# Review: Int-to-Decimal Migration for Goods Quantities

## Executive Summary

The migration from `int` to `Decimal` for goods quantities is partially complete. Core data structures (`Inventory`, `Resource`) have been updated, but several inconsistencies remain in protocol effects, type hints, and conversion boundaries. This review identifies gaps requiring attention before the migration can be considered complete.

## Commits Reviewed

- **6b7637e**: Planning document (`docs/planning_thinking_etc/goods_to_decimal.md`)
- **c8592f1**: Implementation commit - core changes

## ✅ What Was Done Well

1. **Central Configuration**: `decimal_config.py` provides centralized precision management with proper validation
2. **Core State Structures**: `Inventory` and `Resource` classes properly use `Decimal` with quantization
3. **Database Storage**: Telemetry properly converts `Decimal` to integer minor units using `to_storage_int()`
4. **Utility Functions**: All utility functions correctly handle `Decimal` inputs (convert to float internally)
5. **Documentation**: Type documentation updated in `docs/4_typing_overview.md`

## ❌ Critical Gaps and Inconsistencies

### 1. Protocol Effect Types (HIGH PRIORITY)

**Location**: `src/vmt_engine/protocols/base.py`

**Issue**: The `Trade` and `Harvest` effect dataclasses still use `int` for quantity fields:

```178:202:src/vmt_engine/protocols/base.py
    dA: int  # Change in good A (negative for seller, positive for buyer)
    dB: int  # Change in good B
```

```190:202:src/vmt_engine/protocols/base.py
class Harvest(Effect):
    """
    Harvest resources from a cell.
    
    The simulation core validates:
    - Cell is claimed by this agent
    - Sufficient resources available
    - Agent is within interaction_radius
    """
    
    agent_id: int
    pos: Position
    amount: int
```

**Impact**: 
- Trade effects created by bargaining protocols must use integer amounts
- Harvest effects cannot represent fractional harvests
- Inconsistent with core `Inventory`/`Resource` types

**Recommendation**: Change to `Decimal`:
```python
dA: Decimal
dB: Decimal
amount: Decimal  # For Harvest
```

### 2. Protocol Context Type Definitions (MEDIUM PRIORITY)

**Location**: `src/vmt_engine/protocols/context.py`

**Issue**: Type aliases and annotations still reference `int`:

```24:24:src/vmt_engine/protocols/context.py
Inventory = dict[str, int]
```

```66:67:src/vmt_engine/protocols/context.py
    A: int  # Available A resources
    B: int  # Available B resources
```

```105:105:src/vmt_engine/protocols/context.py
    inventory: Inventory  # {"A": int, "B": int}
```

**Impact**: 
- Type hints are misleading - actual `Inventory` is Decimal
- `ResourceView` exposes `int` amounts when resources are `Decimal`
- Protocols consuming `WorldView` may make incorrect assumptions

**Recommendation**: Update type hints:
```python
from decimal import Decimal
Inventory = dict[str, Decimal]  # or import from core.state

@dataclass(frozen=True)
class ResourceView:
    A: Decimal
    B: Decimal
    # ...
```

**Note**: Need to verify how `WorldView` is constructed - may require conversion from `Decimal` to match type hints, or update type hints to match reality.

### 3. Foraging Function Return Types (MEDIUM PRIORITY)

**Location**: `src/vmt_engine/systems/foraging.py`

**Issue**: Function signature returns `int` but internally uses `Decimal`:

```59:64:src/vmt_engine/systems/foraging.py
def forage(
    agent: 'Agent',
    grid: 'Grid',
    forage_rate: int,
    current_tick: int = 0
) -> tuple[bool, Optional[str], int]:
```

```120:121:src/vmt_engine/systems/foraging.py
    # Return amount as int for backward compatibility
    return (True, good_type, int(harvest_decimal))
```

**Impact**: 
- Information loss when returning `int` from `Decimal` harvest
- Comment indicates "backward compatibility" - suggests intentional temporary behavior
- `regenerate_resources()` also returns `int` total

**Recommendation**: 
- Change return type to `Decimal` or `tuple[bool, Optional[str], Decimal]`
- Update all call sites to handle `Decimal`
- Remove "backward compatibility" conversion

### 4. Trade Search Logic Uses Integer Iteration (MEDIUM PRIORITY)

**Location**: `src/vmt_engine/systems/matching.py`

**Issue**: Trade search iterates over integer range despite `Decimal` inventories:

```308:311:src/vmt_engine/systems/matching.py
    # Convert to int for range iteration
    max_dA_int = int(max_dA)
    
    # Iterate over trade sizes
    for dA in range(1, max_dA_int + 1):
```

**Impact**: 
- Cannot find trades with fractional `dA` (e.g., 0.5 units)
- May miss mutually beneficial trades
- Inconsistent with Decimal precision goals

**Recommendation**: 
- Implement fractional trade size search (use step size based on `QUANTITY_DECIMAL_PLACES`)
- Or document this as intentional limitation (integer-only trades)

### 5. Function Parameters Accept `int | Decimal` Union (LOW PRIORITY)

**Location**: Multiple files

**Issue**: Several functions accept `int | Decimal` to support both types:

```209:209:src/vmt_engine/systems/matching.py
def improves(agent: 'Agent', dA: int | Decimal, dB: int | Decimal, eps: float = 1e-12) -> bool:
```

```382:382:src/vmt_engine/systems/matching.py
def execute_trade(buyer: 'Agent', seller: 'Agent', dA: int | Decimal, dB: int | Decimal):
```

```17:18:src/vmt_engine/systems/_trade_attempt_logger.py
    dA: int | Decimal,
    dB: int | Decimal,
```

**Impact**: 
- Allows mixing types, increasing complexity
- Hides potential type inconsistencies

**Recommendation**: 
- Once all call sites use `Decimal`, remove `int` from union types
- Or keep if intentionally supporting both (document decision)

### 6. Scenario Schema Still Uses `int` (CONFIGURATION)

**Location**: `src/scenarios/schema.py`

**Issue**: Schema types still use `int` for initial inventories and resource amounts:

```131:131:src/scenarios/schema.py
    initial_inventories: dict[str, int | list[int]]
```

```28:28:src/scenarios/schema.py
    amount: int | dict[str, Any]  # Can be int or distribution spec
```

**Note**: This may be intentional - YAML inputs can be integers/floats that get converted to `Decimal` during loading. Need to verify loader converts properly.

**Recommendation**: 
- Verify `scenarios/loader.py` converts all numeric inputs to `Decimal` via `decimal_from_numeric()`
- Document that YAML can contain int/float but will be converted

### 7. Display/Serialization Conversions (DOCUMENTATION)

**Location**: `src/vmt_engine/simulation.py`

**Issue**: Summary displays convert `Decimal` to `int`:

```153:154:src/vmt_engine/simulation.py
                "A": int(agent.inventory.A),
                "B": int(agent.inventory.B),
```

**Impact**: 
- Display may truncate fractional amounts
- User may not see precision in outputs

**Recommendation**: 
- Display as `Decimal` (preserves precision) or format to show decimal places
- Document this as intentional for readability vs. precision preservation

### 8. Bargaining Protocol Trade Creation (HIGH PRIORITY)

**Location**: `src/vmt_engine/game_theory/bargaining/legacy.py`

**Issue**: Trade effects created with `abs()` of Decimal values passed to `int` fields:

```191:205:src/vmt_engine/game_theory/bargaining/legacy.py
        return Trade(
            protocol_name=self.name,
            tick=world.tick,
            buyer_id=buyer_id,
            seller_id=seller_id,
            pair_type="A<->B",
            dA=abs(dA),
            dB=abs(dB),
            price=abs(price),
```

**Note**: Need to check if `dA`/`dB` are `Decimal` here and if so, `abs()` returns `Decimal`, which would fail type check if `Trade.dA` is `int`.

**Impact**: 
- Type mismatch when creating Trade effects
- Potential runtime errors or silent truncation

**Recommendation**: 
- First fix `Trade` effect to use `Decimal`
- Then verify all bargaining protocol implementations

### 9. Trade Execution Path Type Mismatch (HIGH PRIORITY)

**Location**: `src/vmt_engine/systems/trading.py`

**Issue**: Trade effect `dA`/`dB` (currently `int`) converted to `Decimal` for `execute_trade_generic()`:

```149:150:src/vmt_engine/systems/trading.py
            dA_i, dB_i = effect.dA, -effect.dB
            dA_j, dB_j = -effect.dA, effect.dB
```

Since `execute_trade_generic()` expects `Decimal` in trade tuple, this works but is inconsistent.

**Impact**: 
- Type conversion happening at effect application boundary
- Signals design inconsistency

**Recommendation**: 
- Fix `Trade` effect to use `Decimal` (see #1)
- Remove need for implicit conversion

### 10. Price Candidate Generation (LOW PRIORITY)

**Location**: `src/vmt_engine/systems/matching.py`

**Issue**: `generate_price_candidates()` takes `dA: int` parameter:

```232:232:src/vmt_engine/systems/matching.py
def generate_price_candidates(ask: float, bid: float, dA: int) -> list[float]:
```

Called from search that iterates integers (see #4), so currently consistent, but limits precision.

**Recommendation**: 
- If fractional trades are implemented, update to `dA: Decimal`
- Otherwise document limitation

## Testing Gaps

1. **Fractional Trade Tests**: No tests verify fractional quantity trades work end-to-end
2. **Precision Loss Tests**: No tests check for precision loss at conversion boundaries
3. **Effect Creation Tests**: No tests verify Trade/Harvest effects are created with correct Decimal types
4. **Protocol Context Tests**: No tests verify WorldView construction with Decimal inventories

## Migration Checklist Status

From planning document (`goods_to_decimal.md`):

- [x] Config module introduced
- [x] All quantity fields converted to Decimal (core structures)
- [x] Serialization paths updated (telemetry)
- [x] Utilities validated for Decimal compatibility
- [x] Documentation refreshed
- [ ] **Protocol effects updated (Trade, Harvest)**
- [ ] **Type hints updated (context.py)**
- [ ] **Test suite includes Decimal behavior tests**
- [ ] **Performance benchmark recorded**

## Recommendations

### Immediate Actions (Before Next Merge)

1. **Update Protocol Effects**: Change `Trade.dA`, `Trade.dB`, and `Harvest.amount` to `Decimal`
2. **Update Protocol Context**: Fix type hints in `context.py` to reflect `Decimal` usage
3. **Verify Trade Creation**: Check all bargaining protocols create Trade effects with Decimal values
4. **Update Function Signatures**: Remove `int | Decimal` unions where only `Decimal` should be used

### Short-term Follow-up

5. **Implement Fractional Trade Search**: Update `find_compensating_block()` to search fractional trade sizes
6. **Update Foraging Returns**: Change return types from `int` to `Decimal`
7. **Add Decimal Tests**: Create test suite for fractional quantities and precision preservation

### Documentation

8. **Clarify Display Strategy**: Document whether summary displays should preserve or truncate precision
9. **Schema Input Handling**: Document that YAML accepts int/float but converts to Decimal
10. **Trade Size Limitations**: Document whether trades are intentionally integer-only or should support fractional

## Questions for Discussion

1. **Are fractional trades (e.g., 0.5 units) intentionally excluded?** The current integer iteration suggests yes, but this should be explicit.

2. **Should protocol effects match core types exactly?** Current mismatch (int vs Decimal) may be intentional for effect boundaries - clarify design intent.

3. **What precision should user-facing displays show?** Summary truncates to int - intentional or oversight?

4. **Should scenario YAML schemas accept Decimal strings?** Currently accepts int/float - should also accept "0.1234" strings?

5. **Performance impact measured?** Planning document mentions 2x slowdown target - was this benchmarked?

