# VMT Protocol System Review
**Date**: October 2025
**Purpose**: Comprehensive review of protocol architecture, phase responsibilities, and return type compliance

---

## Executive Summary

The VMT protocol system has been successfully implemented with three protocol categories (Search, Matching, Bargaining) following the Protocol → Effect → State architecture pattern. However, several critical findings require attention:

1. **7-Phase Cycle**: Properly implemented; protocols are correctly integrated into phases 2 (Decision) and 4 (Trading)
2. **Protocol Return Types**: Most protocols comply with their intended return signatures; some discrepancies found
3. **Registration**: All protocols properly registered via decorator pattern
4. **Missing Protocol**: Edgeworth Box bargaining protocol is designed but not yet implemented

---

## Part 1: Protocol Inventory

### Search Protocols (3 total)

#### 1. LegacySearchProtocol (`legacy_distance_discounted`)
- **File**: `src/vmt_engine/protocols/search/legacy.py`
- **Version**: 2025.10.26
- **Phase**: 2 (Decision)
- **Methods**:
  - `build_preferences()` → `list[tuple[Target, float, dict]]`
  - `select_target()` → `list[Effect]`
- **Return Type Compliance**: ✅ CORRECT
  - Returns `SetTarget` effects for trade targets
  - Returns `SetTarget + ClaimResource` effects for forage targets
  - Returns empty list when no suitable target found
- **Notes**: Bit-compatible with pre-protocol DecisionSystem

#### 2. RandomWalkSearch (`random_walk`)
- **File**: `src/vmt_engine/protocols/search/random_walk.py`
- **Version**: 2025.10.28
- **Phase**: 2b
- **Methods**: Same as above
- **Return Type Compliance**: ✅ CORRECT
  - Returns `SetTarget` effects with random positions
- **Notes**: Pure stochastic exploration baseline

#### 3. MyopicSearch (`myopic`)
- **File**: `src/vmt_engine/protocols/search/myopic.py`
- **Version**: 2025.10.28
- **Phase**: 2b
- **Methods**: Same as above
- **Return Type Compliance**: ✅ CORRECT
  - Returns `SetTarget` effects within vision radius 1
- **Notes**: Limited vision search for pedagogical comparison

### Matching Protocols (3 total)

#### 1. LegacyMatchingProtocol (`legacy_three_pass`)
- **File**: `src/vmt_engine/protocols/matching/legacy.py`
- **Version**: 2025.10.26
- **Phase**: 2 (Decision)
- **Methods**:
  - `find_matches(preferences, world)` → `list[Effect]`
- **Return Type Compliance**: ✅ CORRECT
  - Returns `Pair` effects for successful matches
  - Returns `Unpair` effects in pass 3b (unused in current implementation)
- **Algorithm**: Three-pass (mutual consent + greedy fallback)
- **Notes**: Bit-compatible with pre-protocol matching

#### 2. RandomMatching (`random_matching`)
- **File**: `src/vmt_engine/protocols/matching/random.py`
- **Version**: 2025.10.28
- **Phase**: 2a
- **Methods**: Same as above
- **Return Type Compliance**: ✅ CORRECT
  - Returns `Pair` effects for random pairs
- **Notes**: Null hypothesis baseline

#### 3. GreedySurplusMatching (`greedy_surplus`)
- **File**: `src/vmt_engine/protocols/matching/greedy.py`
- **Version**: 2025.10.28
- **Phase**: 2b
- **Methods**: Same as above
- **Return Type Compliance**: ✅ CORRECT
  - Returns `Pair` effects for welfare-maximizing matches
- **Notes**: Central planner perspective

### Bargaining Protocols (3 total)

#### 1. LegacyBargainingProtocol (`legacy_compensating_block`)
- **File**: `src/vmt_engine/protocols/bargaining/legacy.py`
- **Version**: 2025.10.26
- **Phase**: 4 (Trade)
- **Methods**:
  - `negotiate(pair, world)` → `list[Effect]`
- **Return Type Compliance**: ✅ CORRECT
  - Returns `[Trade]` for successful negotiations
  - Returns `[Unpair]` for failed negotiations
- **Notes**: Uses compensating block search with money-aware matching

#### 2. SplitDifference (`split_difference`)
- **File**: `src/vmt_engine/protocols/bargaining/split_difference.py`
- **Version**: 2025.10.28
- **Phase**: 2a
- **Methods**: Same as above
- **Return Type Compliance**: ✅ CORRECT
  - Returns `[Trade]` for equal surplus division
  - Returns `[Unpair]` for no feasible trade
- **Notes**: Nash bargaining approximation

#### 3. TakeItOrLeaveIt (`take_it_or_leave_it`)
- **File**: `src/vmt_engine/protocols/bargaining/take_it_or_leave_it.py`
- **Version**: 2025.10.28
- **Phase**: 2b
- **Methods**: Same as above
- **Return Type Compliance**: ✅ CORRECT
  - Returns `[Trade]` for accepted offers
  - Returns `[Unpair]` for rejected offers
- **Notes**: Monopolistic offer protocol; has initialization parameters

### Missing Protocol

#### EdgeworthBoxBargainingProtocol (`edgeworth_box`) - NOT IMPLEMENTED
- **Design Document**: `docs/CURRENT/critical/EDGEWORTH_BOX_BARGAINING_PROTOCOL.md`
- **Status**: Design phase complete, implementation pending
- **Expected Behavior**: 
  - Solves for Edgeworth Box equilibrium
  - Trades toward equilibrium exchange ratio
  - Single-tick trade intent
- **Notes**: Ready for implementation when approved

---

## Part 2: 7-Phase Cycle Integration

### Current Implementation

#### Phase 1: Perception (No Protocol)
- System: `PerceptionSystem`
- Location: `src/vmt_engine/systems/perception.py`
- **Protocol Involvement**: NONE
- **Functionality**: Builds perception cache for each agent (neighbors, quotes, resources)
- **Status**: ✅ Correct

#### Phase 2: Decision (Search + Matching Protocols)
- System: `DecisionSystem`
- Location: `src/vmt_engine/systems/decision.py`
- **Protocol Involvement**: 
  1. Search: `build_preferences()` → `select_target()` → `list[Effect]`
  2. Matching: `find_matches(preferences, context)` → `list[Effect]`
- **Effect Types**:
  - `SetTarget`: Agent movement targets
  - `ClaimResource`: Resource claiming
  - `Pair`: Establish pairings
  - `Unpair`: Break pairings
- **Status**: ✅ Correct integration

**Orchestration Flow**:
```python
# DecisionSystem.execute()
1. _clear_stale_claims()  # No protocol call - clears expired resource claims
2. _execute_search_phase() → call search_protocol.build_preferences() + select_target()
   - Handles already-paired agents (skip search, maintain pairing)
   - Handles foraging-committed agents (validate commitment)
   - Builds preferences and applies effects for each agent
3. _execute_matching_phase() → call matching_protocol.find_matches(preferences, context)
   - Builds global ProtocolContext
   - Calls matching protocol
   - Applies pairing effects (Pair/Unpair)
4. _log_decisions()  # No protocol call - logs preferences to telemetry if enabled
```

#### Phase 3: Movement (No Protocol)
- System: `MovementSystem`
- Location: `src/vmt_engine/systems/movement.py`
- **Protocol Involvement**: NONE
- **Functionality**: 
  - Paired agents move toward partner position
  - Unpaired agents move toward target_pos (from Phase 2)
  - Diagonal deadlock resolution (higher ID moves)
  - Distance checking (skip movement if already in interaction range)
  - Updates spatial index after movement
- **Status**: ✅ Correct (movement is deterministic, no protocol needed)

#### Phase 4: Trading (Bargaining Protocols)
- System: `TradeSystem`
- Location: `src/vmt_engine/systems/trading.py`
- **Protocol Involvement**:
  - Bargaining: `negotiate(pair, world)` → `list[Effect]`
- **Effect Types**:
  - `Trade`: Execute trade
  - `Unpair`: Trade negotiation failed
- **Status**: ✅ Correct integration

**Orchestration Flow**:
```python
# TradeSystem.execute()
1. Iterate through all agents, find those with pairings
2. Skip if pair already processed (avoid double-processing)
3. Check distance: must be within interaction_radius to trade
4. For each valid pair: _negotiate_trade() → call bargaining_protocol.negotiate(pair, world)
5. Apply effects: either _apply_trade_effect() or _apply_unpair_effect()
6. _log_trade()  # No protocol call - logs to telemetry
```

#### Phase 5: Foraging (No Protocol)
- System: `ForageSystem`
- Location: `src/vmt_engine/systems/foraging.py`
- **Protocol Involvement**: NONE
- **Functionality**:
  - Skips paired agents (exclusive commitment to trading)
  - Forages resources at agent's current position
  - Enforces single harvester per cell (lowest ID wins)
  - Updates agent inventory
  - Sets `inventory_changed` flag for quote refresh
  - Breaks foraging commitment after harvest
- **Notes**: Foraging targets selected in Phase 2 (Search protocol), executed in Phase 5
- **Status**: ✅ Correct

#### Phase 6: Resource Regeneration (No Protocol)
- System: `ResourceRegenerationSystem`
- Location: `src/vmt_engine/systems/foraging.py`
- **Protocol Involvement**: NONE
- **Functionality**:
  - Only processes harvested cells (efficient active set tracking)
  - Waits for cooldown_ticks after last harvest before regeneration
  - Regenerates at fixed growth_rate per tick
  - Stops when cell reaches original_amount
  - Removes cells from active set when fully regenerated
- **Status**: ✅ Correct

#### Phase 7: Housekeeping (No Protocol)
- System: `HousekeepingSystem`
- Location: `src/vmt_engine/systems/housekeeping.py`
- **Protocol Involvement**: NONE
- **Functionality**:
  - Refreshes quotes for agents with `inventory_changed` flag set
  - Verifies pairing integrity (bidirectional validation)
  - Logs agent snapshots to telemetry
  - Logs resource snapshots to telemetry
- **Status**: ✅ Correct

---

## Part 3: Return Type Analysis

### Search Protocols

**Intended Return Types**:
- `build_preferences()` → `list[tuple[Target, float, dict]]`
  - Target can be: `int` (agent_id), `Position` (tuple[int, int]), or `str` (resource_id)
  - Score: `float` (discounted surplus or utility gain)
  - Metadata: `dict` with keys like `surplus`, `distance`, `pair_type`, etc.
- `select_target()` → `list[Effect]`
  - Effect types: `SetTarget`, `ClaimResource`, `ReleaseClaim` (unused)
  - Empty list if no suitable target

**Compliance Audit**:

| Protocol | build_preferences() | select_target() | Notes |
|----------|-------------------|-----------------|-------|
| LegacySearchProtocol | ✅ Correct | ✅ Correct | Returns SetTarget + ClaimResource for forage |
| RandomWalkSearch | ✅ Correct | ✅ Correct | Returns SetTarget with random positions |
| MyopicSearch | ✅ Correct | ✅ Correct | Returns SetTarget + ClaimResource for forage |

### Matching Protocols

**Intended Return Types**:
- `find_matches(preferences, context)` → `list[Effect]`
  - Effect types: `Pair`, `Unpair`
  - Empty list if no matches

**Compliance Audit**:

| Protocol | find_matches() | Notes |
|----------|----------------|-------|
| LegacyMatchingProtocol | ✅ Correct | Returns Pair effects in passes 2 & 3 |
| RandomMatching | ✅ Correct | Returns Pair effects for random pairs |
| GreedySurplusMatching | ✅ Correct | Returns Pair effects for welfare-maximizing matches |

### Bargaining Protocols

**Intended Return Types**:
- `negotiate(pair, world)` → `list[Effect]`
  - Effect types: `Trade`, `Unpair`
  - Empty list for multi-tick protocols (not implemented)
  - `InternalStateUpdate` for multi-tick state (not implemented)

**Compliance Audit**:

| Protocol | negotiate() | Notes |
|----------|-------------|-------|
| LegacyBargainingProtocol | ✅ Correct | Returns Trade or Unpair |
| SplitDifference | ✅ Correct | Returns Trade or Unpair |
| TakeItOrLeaveIt | ✅ Correct | Returns Trade or Unpair |
| EdgeworthBox | ⚠️ Not implemented | Should return Trade or Unpair |

**Special Cases**:
- All bargaining protocols are **single-tick** (not multi-tick)
- All return exactly **one effect**: either `[Trade(...)]` or `[Unpair(...)]`
- No protocols return empty lists or multiple effects

---

## Part 4: Critical Findings

### ✅ Strengths

1. **Architecture Compliance**: All protocols follow Protocol → Effect → State pattern
2. **Determinism**: All protocols use world RNG for reproducibility
3. **Separation of Concerns**: Search, matching, and bargaining properly separated
4. **Return Type Consistency**: All protocols return intended effect types
5. **Registration System**: All protocols properly registered via decorator
6. **Phase Integration**: Protocols correctly integrated into 7-phase cycle

### ⚠️ Issues

#### 1. **LegacyMatchingProtocol: Pass 3b Unused**
- **Issue**: `_pass3b_handle_unpaired()` returns empty list
- **Location**: `src/vmt_engine/protocols/matching/legacy.py:239-267`
- **Impact**: Low (functionality handled elsewhere in DecisionSystem)
- **Recommendation**: Document that search protocol handles idle fallback, or remove pass 3b

#### 2. **EdgeworthBox Not Implemented**
- **Issue**: Design document exists but no implementation
- **Location**: `docs/CURRENT/critical/EDGEWORTH_BOX_BARGAINING_PROTOCOL.md`
- **Impact**: Medium (educational scenario gap)
- **Recommendation**: Implement when approved

#### 3. **Market Directory Empty**
- **Issue**: `src/vmt_engine/protocols/market/` directory exists but is empty (except `__pycache__`)
- **Impact**: Low (likely future-proofing)
- **Recommendation**: Document intended purpose or remove if not planned

### 🔍 Potential Improvements

#### 1. **Multi-Tick Bargaining**
- **Current**: All bargaining protocols are single-tick
- **Potential**: Could add Rubinstein alternating offers or other multi-round protocols
- **Requirement**: Would need `InternalStateUpdate` effect support

#### 2. **Protocol State Storage**
- **Current**: No cross-tick protocol state (besides agent internal state)
- **Potential**: Could add protocol-specific state in `ProtocolContext`
- **Example**: Store offer history for multi-tick bargaining

#### 3. **Search Protocol Consistency**
- **Current**: All search protocols support all three modes (trade/forage/both)
- **Potential**: Could add specialized protocols (e.g., forage-only)
- **Benefit**: Would reduce complexity

---

## Part 5: Testing Recommendations

### Missing Test Coverage

1. **Protocol Return Type Validation**
   - Test that all protocols return correct effect types
   - Test that effect contents are valid (e.g., Trade has buyer_id < seller_id)

2. **Protocol Integration Tests**
   - End-to-end tests for each protocol combination
   - Ensure protocol output correctly applied by systems

3. **Multi-Protocol Scenarios**
   - Test scenarios with different search/matching/bargaining combinations
   - Verify deterministic behavior across protocol mixes

4. **Protocol State Management** (when implemented)
   - Test `InternalStateUpdate` effect handling
   - Test multi-tick protocol behavior

### Existing Test Coverage

Based on codebase search:
- Protocol registry tests exist
- Individual protocol tests exist
- Integration tests for legacy protocols exist
- Need to verify coverage for new protocols (RandomWalk, Myopic, SplitDifference, TIOL)

---

## Part 6: Documentation Status

### ✅ Well-Documented
- Protocol base classes: `src/vmt_engine/protocols/base.py`
- Effect types: Comprehensive docstrings
- Legacy protocols: Full documentation

### ⚠️ Needs Improvement
- Protocol registry: Missing usage examples
- Context builders: Limited documentation
- Market directory: No documentation

### 📝 Recommended Additions
1. Protocol usage guide in technical manual
2. Adding new protocol tutorial
3. Protocol comparison table
4. Edgeworth Box implementation guide

---

## Part 7: Conclusions and Next Steps

### Key Findings

1. **Architecture**: ✅ Sound implementation of Protocol → Effect → State pattern
2. **7-Phase Cycle**: ✅ Correctly integrated across Phases 1 (Decision) and 4 (Trade)
3. **Return Types**: ✅ All protocols comply with intended signatures
4. **Registration**: ✅ All protocols properly registered
5. **Gaps**: ⚠️ Edgeworth Box pending; market directory unclear

### Recommendations

#### Priority 1 (Critical)
- None identified (system is functionally correct)

#### Priority 2 (Important)
1. Implement Edgeworth Box bargaining protocol
2. Document market directory purpose or remove
3. Add protocol integration tests for new protocols

#### Priority 3 (Nice to Have)
1. Add multi-tick bargaining example
2. Create protocol comparison guide
3. Document protocol state management patterns

### Verdict

**Overall Assessment**: ✅ The protocol system is well-designed and correctly implemented. The 7-phase cycle integration is sound, and all protocols return their intended effect types. The architecture supports extensibility while maintaining determinism and theoretical soundness.

The system is ready for production use. The identified gaps (Edgeworth Box, empty market directory) are non-critical and can be addressed as needed for specific use cases.

---

## Appendix A: Protocol Registry

```python
# Search Protocols
{
    "legacy_distance_discounted": LegacySearchProtocol,
    "random_walk": RandomWalkSearch,
    "myopic": MyopicSearch,
}

# Matching Protocols
{
    "legacy_three_pass": LegacyMatchingProtocol,
    "random_matching": RandomMatching,
    "greedy_surplus": GreedySurplusMatching,
}

# Bargaining Protocols
{
    "legacy_compensating_block": LegacyBargainingProtocol,
    "split_difference": SplitDifference,
    "take_it_or_leave_it": TakeItOrLeaveIt,
}
```

## Appendix B: Effect Type Reference

### Search Effects
- `SetTarget(agent_id, target)` - Set movement target
- `ClaimResource(agent_id, pos)` - Claim resource cell
- `ReleaseClaim(pos)` - Release resource claim

### Matching Effects
- `Pair(agent_a, agent_b, reason)` - Establish pairing
- `Unpair(agent_a, agent_b, reason)` - Break pairing

### Bargaining Effects
- `Trade(buyer_id, seller_id, pair_type, dA, dB, dM, price, metadata)` - Execute trade
- `Unpair(agent_a, agent_b, reason)` - Trade failed

### State Management Effects
- `InternalStateUpdate(agent_id, key, value)` - Store cross-tick state (unused)

## Appendix C: Phase Flow Diagram

```
Phase 1: Perception (no protocol)
  ↓
Phase 2: Decision
  ├─ Search Protocol: build_preferences() → select_target()
  │   └─ Effects: SetTarget, ClaimResource
  └─ Matching Protocol: find_matches(preferences, context)
      └─ Effects: Pair, Unpair
  ↓
Phase 3: Movement (no protocol)
  ↓
Phase 4: Trading
  └─ Bargaining Protocol: negotiate(pair, world)
      └─ Effects: Trade, Unpair
  ↓
Phase 5: Foraging (no protocol)
  ↓
Phase 6: Resource Regeneration (no protocol)
  ↓
Phase 7: Housekeeping (no protocol)
```

---

**End of Report**

