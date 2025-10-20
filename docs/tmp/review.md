## Critical Review: VMT Protocol Modularization Implementation Plan

I've completed a thorough review of the implementation plan against the codebase, workspace rules, and type specifications. Here are the **critical issues** that must be addressed before this can serve as a single source of truth:

---

### **Category 1: Type System & Interface Mismatches**

#### **Issue 1.1: PerceptionView vs. perception_cache Discrepancy**

**Problem:** The `SearchProtocol` interface (line 92) expects a `PerceptionView` object:
```python
def select_search_target(self, agent: Agent, perception: PerceptionView) -> Position:
```

However, the actual codebase stores perception data as a **plain dict** on agents:
```python
agent.perception_cache = {
    "neighbors": perception.neighbors,
    "resource_cells": perception.resource_cells,
}
```

The `PerceptionView` dataclass exists in `perception.py` but is **not** what gets stored or passed around during the decision phase. The current `DecisionSystem` uses `view = agent.perception_cache` (a dict).

**Impact:** Critical—protocols can't be implemented without knowing the correct type contract.

**Resolution Required:** Either:
1. Change the existing code to store `PerceptionView` objects instead of dicts, OR
2. Update the interface specification to accept `dict` and document the expected keys

***RESOLUTION:***

This is an *unresolved* issue. We need to discuss this further before we can proceed. In the meantime, the remaining issues should be resolved.

---

#### **Issue 1.2: Undefined "Target" Type**

**Problem:** Line 108 references a `Target` type that doesn't exist in the codebase:
```python
def evaluate_opportunity(self, agent: Agent, target: Target) -> float:
```

The comment says "Either a ResourceCell or another Agent" but there's no such union type defined.

**Impact:** High—makes the interface unimplementable without clarification.

**Resolution Required:** Define the Target type explicitly:
```python
Target = Union[Cell, Agent]  # Or Position | Agent, depending on design intent
```

***RESOLUTION:***

Targets are currently handled by in src/vmt-engine/systems/decision.py. If a new `Target` type is needed, it should respect the existing behavior.
---

### **Category 2: Missing Behavioral Context**

#### **Issue 2.1: Mode-Aware Behavior Not Addressed**

**Problem:** The current `DecisionSystem` is deeply mode-aware (lines 42-51 in `decision.py`):
- In "trade" mode: only evaluate trade partners
- In "forage" mode: only evaluate resources  
- In "both" mode: try trade first, fall back to forage

The protocol interfaces have **no mechanism** to communicate the current mode to the protocol implementations.

**Impact:** Critical—protocols cannot replicate existing behavior without mode context.

**Resolution Required:** Add mode parameter to protocol methods:
```python
def select_search_target(
    self, 
    agent: Agent, 
    perception: PerceptionView,
    current_mode: str,  # "trade", "forage", or "both"
    params: dict  # Access to simulation parameters
) -> Position:
```

---

#### **Issue 2.2: Resource Claiming System Not Integrated**

**Problem:** The plan doesn't address how `SearchProtocol` implementations interact with the resource claiming system (enabled by default per the rules). Current code:
- Filters claimed resources before passing to target selection
- Claims resources after target selection
- This state management happens **around** the protocol, not within it

**Impact:** High—new search protocols won't respect existing claiming behavior.

**Resolution Required:** Document whether:
1. Filtering happens before protocol invocation (protocol sees only available resources), OR
2. Protocol receives all resources and must respect claims itself

---

#### **Issue 2.3: Trade Cooldowns Missing from MatchingProtocol**

**Problem:** The current pairing algorithm filters out partners with active cooldowns (lines 89-94 in `decision.py`). The `MatchingProtocol.build_preferences()` interface (line 129) doesn't show how protocols access cooldown state.

**Impact:** Medium-High—new matching protocols might violate cooldown constraints.

**Resolution Required:** Clarify that agents are pre-filtered OR provide cooldown access through the interface.

---

### **Category 3: Pairing System Semantics**

#### **Issue 3.1: Persistent Pairing Not Explained**

**Problem:** The plan describes the three-pass algorithm but **doesn't explain** that pairings persist across multiple ticks (until trade fails or mode switches). This is critical because:
- Paired agents in Pass 1 skip the matching algorithm entirely (line 38 in `decision.py`)
- They maintain target locks to their partner
- They skip foraging even in "both" mode

**Impact:** Critical—without understanding persistence, protocol implementations will break existing pairing semantics.

**Resolution Required:** Add section "6.3 Pairing Lifecycle Management" explaining:
- When pairings are established
- When pairings are cleared
- How protocols interact with existing pairings

---

#### **Issue 3.2: Pass 3b Unpaired Target Handling Missing**

**Problem:** The plan describes Passes 1-3 but omits Pass 3b (`_pass3b_handle_unpaired_trade_targets`, lines 253-277), which is responsible for:
- Clearing unfulfilled trade targets
- Falling back to foraging in "both" mode
- Setting idle state in "trade" mode

**Impact:** Medium—incomplete specification of the decision phase flow.

**Resolution Required:** Add Pass 3b to Section 5 (Mapping to 7-Phase Tick Cycle).

---

### **Category 4: Implementation Details**

#### **Issue 4.1: Beta Discounting Not Surfaced**

**Problem:** The current system uses `beta` (β) for distance discounting of both:
- Trade surplus (line 104 in `decision.py`)
- Forage values (passed to `choose_forage_target`)

Protocols need access to `beta` but the interfaces don't show how they get simulation parameters.

**Impact:** Medium-High—protocols can't replicate existing scoring behavior.

**Resolution Required:** Add `params: dict` argument to protocol methods OR create a `ProtocolContext` object containing all needed parameters.

---

#### **Issue 4.2: Surplus Computation Dependency**

**Problem:** The plan shows protocols calling `compute_surplus()` (line 212) but doesn't clarify:
- Where this function lives (currently in `matching.py`)
- Whether it's part of the protocol interface or a shared utility
- How protocols access it

**Impact:** Medium—implementation ambiguity.

**Resolution Required:** Explicitly state that `compute_surplus()` remains a shared utility function and update the import structure diagram.

---

### **Category 5: Telemetry & Testing**

#### **Issue 5.1: Preference Logging Responsibility Unclear**

**Problem:** Current code stores `agent._preference_list` and logs it in Pass 4 (lines 331-340). The plan shows protocols returning preferences but doesn't specify:
- Who stores them on agents?
- Who logs them to telemetry?
- How temporary state is managed?

**Impact:** Medium—could lead to telemetry breakage or state leaks.

**Resolution Required:** Add a "Telemetry Contracts" subsection clarifying logging responsibilities at protocol boundaries.

---

#### **Issue 5.2: Legacy Protocol Wrapper Implementation Incomplete**

**Problem:** Section 6.1 shows skeleton code but doesn't address:
- How `legacy_system` is initialized and accessed
- Whether we're wrapping the existing `DecisionSystem` or extracting methods
- How to maintain identical behavior when the current code uses shared state

**Impact:** High—Phase 1 deliverable is underspecified.

**Resolution Required:** Provide complete implementation sketch showing state management approach.

---

### **Category 6: Scenario Configuration**

#### **Issue 6.1: Backward Compatibility Risk**

**Problem:** Line 365 states scenarios without `protocols` field "run exactly as before," but doesn't specify:
- How the engine detects missing field and instantiates legacy protocols
- Whether this happens in `simulation.py` or `scenario.py`
- What the default instantiation logic looks like

**Impact:** Medium—could lead to silent behavior changes.

**Resolution Required:** Add code example showing default protocol instantiation in `Simulation.__init__()`.

---

### **Category 7: Design Decision Clarifications**

#### **Issue 7.1: "Why Start with Matching, Not Search?" Needs Revision**

**Problem:** Section 476-475 states "Starting with matching provides clearer success metrics," but:
- The actual Decision phase involves **both** search (target selection) and matching (pairing)
- They're tightly coupled (search determines candidates for matching)
- Can't modularize one without the other

**Impact:** Low-Medium—could mislead implementation sequencing.

**Resolution Required:** Revise to acknowledge they must be refactored together, or provide more detailed rationale for doing matching first.

---

### **Category 8: Missing Sections**

#### **Issue 8.1: No Discussion of "BarteringProtocol"**

**Problem:** The plan mentions three protocols (Search, Matching, Bargaining) in line 16, but Bargaining is never defined or discussed further. However, the current trade execution system (`trading.py`, `matching.py`) handles:
- Compensating block search
- First-acceptable-trade principle
- Money-aware generic matching

**Impact:** Low—out of scope for current plan, but creates confusion about completeness.

**Resolution Required:** Either:
1. Add "Future Work: BarteringProtocol" section, OR
2. Remove mention of Bargaining from line 16 to avoid scope creep

---

#### **Issue 8.2: No Error Handling / Edge Cases**

**Problem:** The plan doesn't address:
- What happens if a protocol returns invalid data?
- What happens if preferences are malformed?
- How to handle protocol exceptions without crashing the simulation?

**Impact:** Medium—important for production robustness.

**Resolution Required:** Add "Section 14: Error Handling & Validation" with contracts for protocol failures.

---

## Summary Recommendations

### Before this can be SSOT:

**Must Fix (Blocking):**
1. Resolve PerceptionView vs dict inconsistency (1.1)
2. Define Target type (1.2)
3. Add mode parameter to protocols (2.1)
4. Document pairing persistence semantics (3.1)
5. Show how protocols access simulation parameters (4.1)

**Should Fix (High Priority):**
6. Address resource claiming integration (2.2)
7. Clarify trade cooldown handling (2.3)
8. Complete legacy wrapper specification (5.2)
9. Document telemetry responsibilities (5.1)

**Nice to Have:**
10. Add Pass 3b to spec (3.2)
11. Clarify backward compatibility (6.1)
12. Add error handling section (8.2)

---

The plan is **conceptually sound** and demonstrates strong architectural thinking. The Strategy pattern is the right choice, and the phased migration approach is risk-averse and appropriate. However, the interface definitions need to be **grounded in actual codebase types and state management patterns** before implementation can begin safely.

Would you like me to propose specific fixes for any of these issues, or should we prioritize which ones to address first?