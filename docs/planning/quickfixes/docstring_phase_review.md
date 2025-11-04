# Docstring Review: Implementation Phase References

**Date:** 2025-11-04  
**Goal:** Remove implementation planning metadata ("Phase X", "milestone", "gate") from docstrings, keeping only code-relevant information.

---

## Executive Summary

Found **67 references** to implementation phases across source code. Need to categorize:
1. **Legitimate references** - Describe simulation mechanics (e.g., "7-phase tick cycle", "matching phase")
2. **Implementation metadata** - Planning milestones that should be removed (e.g., "Phase 1", "Phase 2b", "Phase 0")

**Key Finding:** Version strings and docstrings contain planning metadata that should be removed or simplified to only code-relevant information.

---

## Category 1: Version Strings with Implementation Phases

These are metadata that don't help understand code function. Should be simplified or removed.

### Files with "Phase X" in Version Strings:

1. **`src/vmt_engine/protocols/base.py`** (line 19)
   - Current: `Version: 2025.10.26 (Phase 0 - Infrastructure)`
   - Issue: "Phase 0 - Infrastructure" is planning metadata
   - Recommendation: `Version: 2025.10.26` (date-only)

2. **`src/vmt_engine/protocols/context.py`** (line 13)
   - Current: `Version: 2025.10.26 (Phase 0 - Infrastructure)`
   - Issue: "Phase 0 - Infrastructure" is planning metadata
   - Recommendation: `Version: 2025.10.26` (date-only)

3. **`src/vmt_engine/protocols/telemetry_schema.py`** (line 10)
   - Current: `Version: 2025.10.26 (Phase 0 - Infrastructure)`
   - Issue: "Phase 0 - Infrastructure" is planning metadata
   - Recommendation: `Version: 2025.10.26` (date-only)

4. **`src/vmt_engine/systems/trading.py`** (line 12)
   - Current: `Version: 2025.10.26 (Phase 1 - Refactored for Protocol System)`
   - Issue: "Phase 1" is planning metadata
   - Recommendation: `Version: 2025.10.26` (date-only)

5. **`src/vmt_engine/agent_based/search/myopic.py`** (line 24)
   - Current: `Version: 2025.10.28 (Phase 2b - Pedagogical Protocol)`
   - Issue: "Phase 2b" is planning metadata
   - Recommendation: `Version: 2025.10.28` (date-only)

6. **`src/vmt_engine/game_theory/matching/greedy.py`** (line 26)
   - Current: `Version: 2025.10.28 (Phase 2b - Pedagogical Protocol)`
   - Issue: "Phase 2b" is planning metadata
   - Recommendation: `Version: 2025.10.28` (date-only)

7. **`src/vmt_engine/agent_based/search/distance_discounted.py`** (line 10)
   - Current: `Version: 2025.10.26 (Phase 1 - Distance-Discounted Search Protocol)`
   - Issue: "Phase 1" is planning metadata
   - Recommendation: `Version: 2025.10.26` (date-only)

8. **`src/vmt_engine/game_theory/matching/three_pass.py`** (line 11)
   - Current: `Version: 2025.10.26 (Phase 1 - Three-Pass Matching Protocol)`
   - Issue: "Phase 1" is planning metadata
   - Recommendation: `Version: 2025.10.26` (date-only)

9. **`src/vmt_engine/protocols/context_builders.py`** (line 8)
   - Current: `Version: 2025.10.26 (Phase 1 - Context Builder Infrastructure)`
   - Issue: "Phase 1" is planning metadata
   - Recommendation: `Version: 2025.10.26` (date-only)

10. **`src/vmt_engine/systems/decision.py`** (line 12)
   - Current: `Version: 2025.10.26 (Phase 1 - Refactored for Protocol System)`
   - Issue: "Phase 1" is planning metadata
   - Recommendation: `Version: 2025.10.26` (date-only)

11. **`src/vmt_engine/protocols/registry.py`** (line 12)
   - Current: `Version: 2025.10.28 (Phase 2a - Infrastructure)`
   - Issue: "Phase 2a" is planning metadata
   - Recommendation: `Version: 2025.10.28` (date-only)

12. **`src/vmt_engine/game_theory/matching/random.py`** (line 16)
   - Current: `Version: 2025.10.28 (Phase 2a - Baseline Protocol)`
   - Issue: "Phase 2a" is planning metadata
   - Recommendation: `Version: 2025.10.28` (date-only)

13. **`src/vmt_engine/agent_based/search/random_walk.py`** (line 16)
   - Current: `Version: 2025.10.28 (Phase 2a - Baseline Protocol)`
   - Issue: "Phase 2a" is planning metadata
   - Recommendation: `Version: 2025.10.28` (date-only)

---

## Category 2: Docstring References to Implementation Phases

### 2.1 Planning Comments in Docstrings

1. **`src/vmt_engine/protocols/telemetry_schema.py`** (line 14)
   - Current: `# These will be integrated into src/telemetry/database.py in Phase 2`
   - Issue: References future implementation phase
   - Recommendation: Remove or change to: `# To be integrated into src/telemetry/database.py`

2. **`src/vmt_engine/protocols/telemetry_schema.py`** (lines 176-180)
   - Current: Usage notes describing "Phase 0", "Phase 1", "Phase 2", "Phase 3+"
   - Issue: Planning metadata, not code documentation
   - Recommendation: Remove or rewrite to describe current state only

3. **`src/vmt_engine/simulation.py`** (line 280)
   - Current: `7-phase tick order (see PLANS/Planning-Post-v1.md):`
   - Issue: Reference to planning document
   - Recommendation: Keep "7-phase tick order" (legitimate), but remove planning doc reference

---

## Category 3: Protocol Registration Metadata (REDUNDANT - REMOVE)

### 3.1 `phase` Parameter in `@register_protocol`

**Finding:** The `phase` parameter is **completely redundant** - it's stored but never used functionally.

**Analysis:**
- Stored in `ProtocolMetadata` dataclass
- Returned in `describe_all_protocols()` and `get_protocol_info()` dicts
- Only tested in one test that asserts it's a string (no functional check)
- **No code actually uses phase for filtering, logic, or display**
- Pure metadata clutter with no functional purpose

**Files to Update for Removal:**

1. **`src/vmt_engine/protocols/registry.py`**:
   - Remove `phase: str` from `ProtocolMetadata` dataclass (line 30)
   - Remove `phase: str = "1"` parameter from `register_protocol()` decorator (line 94)
   - Remove `phase=phase` from metadata creation (line 130)
   - Remove `'phase': meta.phase` from `describe_all_protocols()` (line 160)
   - Remove `'phase': meta.phase` from `get_protocol_info()` (line 176)

2. **All protocol registration decorators** (remove `phase=` parameter):
   - `src/vmt_engine/agent_based/search/distance_discounted.py` (line 34)
   - `src/vmt_engine/game_theory/matching/three_pass.py` (line 29)
   - `src/vmt_engine/agent_based/search/myopic.py` (line 45)
   - `src/vmt_engine/game_theory/matching/greedy.py` (line 47)
   - `src/vmt_engine/game_theory/bargaining/compensating_block.py` (line 34)
   - `src/vmt_engine/game_theory/bargaining/split_difference.py` (line 42)
   - `src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py` (line 47)
   - `src/vmt_engine/game_theory/matching/random.py` (line 37)
   - `src/vmt_engine/agent_based/search/random_walk.py` (line 37)

3. **Test file**:
   - `tests/test_protocol_registry.py` - Remove `assert isinstance(meta.phase, str)` (line 58)

**Recommendation:** **REMOVE ENTIRELY** - This is pure metadata clutter with no functional purpose.

---

## Category 4: Legitimate Simulation Phase References

These describe simulation mechanics and should be **KEPT**:

### 4.1 Simulation Tick Cycle Phases

These describe **when** in the simulation tick cycle things happen - they are code-relevant:

- "7-phase tick cycle" - Describes simulation structure ✅
- "Phase 1: Perception" - Describes when perception occurs ✅
- "Phase 2: Decision" - Describes when decisions occur ✅
- "Phase 3: Movement" - Describes when movement occurs ✅
- "Phase 4: Trade" - Describes when trading happens ✅
- "Phase 5: Forage" - Describes when foraging occurs ✅
- "Phase 6: Resource Regeneration" - Describes when resources regenerate ✅
- "Phase 7: Housekeeping" - Describes when housekeeping occurs ✅
- "matching phase" - Describes when matching occurs ✅
- "bargaining phase" - Describes when bargaining occurs ✅

**Examples to KEEP:**
- `src/vmt_engine/systems/trading.py` (line 6): `Phase 4 of the 7-phase simulation tick:` ✅
- `src/vmt_engine/systems/decision.py` (line 6): `Phase 2 of the 7-phase simulation tick:` ✅
- `src/vmt_engine/systems/perception.py` (line 22): `Phase 1: Agents perceive their environment.` ✅
- `src/vmt_engine/systems/movement.py` (line 15): `Phase 3: Agents move toward targets.` ✅
- `src/vmt_engine/systems/foraging.py` (line 14): `Phase 5: Agents harvest resources.` ✅
- `src/vmt_engine/systems/housekeeping.py` (line 10): `Phase 7: Update quotes, log telemetry, cleanup.` ✅
- `src/vmt_engine/simulation.py` (line 278): `7-phase tick order` ✅
- `src/vmt_engine/protocols/context.py` (line 212): `perception phase` ✅
- `src/vmt_engine/protocols/context.py` (line 246): `matching phase` ✅
- `src/vmt_engine/systems/trade_evaluation.py` (line 8): `matching phase` ✅

**Note:** System class docstrings like "Phase 1:", "Phase 2:", etc. are **legitimate** because they describe the simulation tick cycle order, not implementation planning phases.

---

## Category 5: Code Comments (Not Docstrings)

These are in code comments, not docstrings, but still worth reviewing:

1. **`src/vmt_engine/systems/matching.py`** (line 282)
   - `# Phase 2b: Trade Execution`
   - Issue: Implementation phase reference
   - Recommendation: `# Trade Execution` or `# Trade Execution Functions`

---

## Category 6: Test Files

Test files have version strings with phases, but these are less critical:

1. **`tests/test_myopic_search.py`** (line 11): `Version: 2025.10.28 (Phase 2b)`
2. **`tests/test_greedy_surplus_matching.py`** (line 12): `Version: 2025.10.28 (Phase 2b)`
3. **`tests/test_random_matching.py`** (line 11): `Version: 2025.10.28 (Phase 2a)`
4. **`tests/test_random_walk_search.py`** (line 11): `Version: 2025.10.28 (Phase 2a)`

**Recommendation:** Update test file version strings to remove phase references, but lower priority than source code.

---

## Summary of Recommendations

### High Priority (Source Code Docstrings):

1. **Remove `phase` parameter entirely** from protocol registration system:
   - Remove from `ProtocolMetadata` dataclass
   - Remove from `register_protocol()` decorator
   - Remove from all protocol decorators (9 files)
   - Remove from test assertions
   - Remove from metadata dict returns

2. **Remove "Phase X" from version strings** in 13 source files (use date-only format):
   - `src/vmt_engine/protocols/base.py`
   - `src/vmt_engine/protocols/context.py`
   - `src/vmt_engine/protocols/telemetry_schema.py`
   - `src/vmt_engine/systems/trading.py`
   - `src/vmt_engine/systems/decision.py`
   - `src/vmt_engine/agent_based/search/myopic.py`
   - `src/vmt_engine/game_theory/matching/greedy.py`
   - `src/vmt_engine/agent_based/search/distance_discounted.py`
   - `src/vmt_engine/game_theory/matching/three_pass.py`
   - `src/vmt_engine/protocols/context_builders.py`
   - `src/vmt_engine/protocols/registry.py`
   - `src/vmt_engine/game_theory/matching/random.py`
   - `src/vmt_engine/agent_based/search/random_walk.py`
   
   **Pattern:** Change `Version: 2025.10.26 (Phase X - Description)` → `Version: 2025.10.26` (date-only)

3. **Remove planning metadata from docstrings**:
   - `src/vmt_engine/protocols/telemetry_schema.py` - Usage notes with Phase 0/1/2/3+
   - `src/vmt_engine/protocols/telemetry_schema.py` - Comment about Phase 2 integration

4. **Update code comments**:
   - `src/vmt_engine/systems/matching.py` - Remove "Phase 2b" from comment (line 282)
   - `src/vmt_engine/simulation.py` - Remove "Phase 1" from comment (line 301)

### Medium Priority (Test Files):

5. **Update test file version strings** (4 files)

### Keep (Legitimate References):

- "7-phase tick cycle" - Simulation mechanics
- "matching phase", "bargaining phase", etc. - When things happen

### Remove (Redundant Metadata):

- `phase` parameter in `@register_protocol` decorators - **Completely unused metadata, remove entirely**

---

## Proposed Cleanup Patterns

### Pattern 0: Phase Parameter Removal (HIGHEST PRIORITY)
**Before:** 
```python
@register_protocol(
    category="search",
    name="distance_discounted_search",
    phase="1",
)
```

**After:**
```python
@register_protocol(
    category="search",
    name="distance_discounted_search",
)
```

### Pattern 1: Version Strings
**Before:** `Version: 2025.10.26 (Phase 1 - Protocol Name)`  
**After:** `Version: 2025.10.26` (date-only, no descriptive text)

### Pattern 2: Planning Comments
**Before:** `# These will be integrated into src/telemetry/database.py in Phase 2`  
**After:** `# To be integrated into src/telemetry/database.py` or remove

### Pattern 3: Usage Notes
**Before:** Planning document-style phase descriptions  
**After:** Current state description only, or remove

---

## Files Requiring Changes

### Phase Parameter Removal (10 files):
1. `src/vmt_engine/protocols/registry.py` - Remove phase from dataclass, decorator, and returns
2. `src/vmt_engine/agent_based/search/distance_discounted.py` - Remove phase= from decorator
3. `src/vmt_engine/game_theory/matching/three_pass.py` - Remove phase= from decorator
4. `src/vmt_engine/agent_based/search/myopic.py` - Remove phase= from decorator
5. `src/vmt_engine/game_theory/matching/greedy.py` - Remove phase= from decorator
6. `src/vmt_engine/game_theory/bargaining/compensating_block.py` - Remove phase= from decorator
7. `src/vmt_engine/game_theory/bargaining/split_difference.py` - Remove phase= from decorator
8. `src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py` - Remove phase= from decorator
9. `src/vmt_engine/game_theory/matching/random.py` - Remove phase= from decorator
10. `src/vmt_engine/agent_based/search/random_walk.py` - Remove phase= from decorator
11. `tests/test_protocol_registry.py` - Remove phase assertion

### Version String Cleanup (13 source files - date-only format):
1. `src/vmt_engine/protocols/base.py`
2. `src/vmt_engine/protocols/context.py`
3. `src/vmt_engine/protocols/telemetry_schema.py`
4. `src/vmt_engine/systems/trading.py`
5. `src/vmt_engine/systems/decision.py`
6. `src/vmt_engine/agent_based/search/myopic.py`
7. `src/vmt_engine/game_theory/matching/greedy.py`
8. `src/vmt_engine/agent_based/search/distance_discounted.py`
9. `src/vmt_engine/game_theory/matching/three_pass.py`
10. `src/vmt_engine/protocols/context_builders.py`
11. `src/vmt_engine/protocols/registry.py`
12. `src/vmt_engine/game_theory/matching/random.py`
13. `src/vmt_engine/agent_based/search/random_walk.py`

### Planning Metadata Removal (2 files):
1. `src/vmt_engine/protocols/telemetry_schema.py` - Remove Phase 0/1/2/3+ usage notes
2. `src/vmt_engine/systems/matching.py` - Remove "Phase 2b" from code comment
3. `src/vmt_engine/simulation.py` - Remove "Phase 1" from code comment

### Test Files (4 files - lower priority):
1. `tests/test_myopic_search.py`
2. `tests/test_greedy_surplus_matching.py`
3. `tests/test_random_matching.py`
4. `tests/test_random_walk_search.py`

---

## Next Steps

1. Review this document for accuracy
2. Confirm which references should be removed vs. kept
3. Create implementation plan for cleanup
4. Execute cleanup systematically

