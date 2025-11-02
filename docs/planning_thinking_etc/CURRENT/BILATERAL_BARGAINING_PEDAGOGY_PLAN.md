# Bilateral Bargaining Pedagogy Planning Document

**Date**: October 31, 2025  
**Status**: Planning Phase - DO NOT IMPLEMENT  
**Context**: Phase 2.5 - Scenario curation and behavioral validation  
**Focus**: 2-agent bilateral exchange foundation

---

## Executive Summary

This document plans the pedagogical foundation for teaching bilateral bargaining through VMT simulations. The goal is to create a clean, economically accurate demonstration of how two agents with complementary endowments can achieve mutual gains through trade, with clear visualization of the Edgeworth Box framework.

**Core Insight**: Before expanding to multi-agent matching protocols, we need a rock-solid 2-agent foundation that demonstrates core microeconomic concepts: mutual gains from trade, contract curves, competitive equilibrium, and the role of different bargaining mechanisms.

---

## Current State Analysis

### Existing 2-Agent Scenarios

**Scenario**: `scenarios/demos/edgeworth_box_4agent.yaml`
- 4 agents (2 pairs of types), 8×8 grid
- Type 1 (agents 0,1): A-rich (10A, 3B) → want B
- Type 2 (agents 2,3): B-rich (3A, 10B) → want A
- All have CES utility (ρ=0.5, wA=wB=0.5)
- Expected: Movement toward balanced inventories, Pareto improvement

**Issue**: With 4 agents, the scenario introduces multi-agent matching complexity. Not pure bilateral demonstration.

### Existing Bargaining Protocols

1. **`legacy_compensating_block`** (current default)
   - Uses `find_best_trade()` from matching primitives
   - Scans ΔA from 1 to inventory max, tests prices in [ask, bid]
   - Accepts first mutually beneficial trade (ΔU > 0 for both)
   - **Economic behavior**: Finds *a* Pareto improvement, not necessarily *the* optimal one
   - **Not Edgeworth optimal**: May stop short of contract curve

2. **`split_difference`**
   - Simple equal surplus division
   - **Economic behavior**: Nash bargaining solution (symmetric case)
   - **Not Edgeworth optimal**: Finds one-shot trade, doesn't solve for equilibrium

3. **`take_it_or_leave_it`**
   - One agent proposes, other accepts/rejects
   - **Economic behavior**: Ultimatum game, extractive
   - **Not Edgeworth optimal**: Power dynamics, not competitive equilibrium

### What's Missing

**For pedagogical clarity, we need**:
1. A protocol that explicitly solves for Edgeworth Box competitive equilibrium
2. Visualization showing the contract curve and equilibrium point
3. Clear 2-agent scenarios (not 4-agent) to eliminate matching confusion
4. Documentation explaining the economic interpretation of each protocol's behavior

---

## Desired Pedagogical Flow

### Target Student Learning Path

**Lesson 1: The Basic Problem**
- Two agents, different preferences, complementary endowments
- No trade yet → each agent at initial utility level
- **Visualization**: Edgeworth Box showing initial endowment point

**Lesson 2: Potential Gains from Trade**
- Show contract curve (locus of Pareto optimal allocations)
- Show competitive equilibrium (tangency point)
- **Visualization**: Contract curve drawn, equilibrium point marked

**Lesson 3: Bargaining Mechanism Comparison**
- **Competitive equilibrium protocol**: Trades directly toward equilibrium, converges to contract curve
- **Compensating block protocol**: Finds beneficial trades, may not reach equilibrium
- **Split difference protocol**: One-shot Nash solution
- **Visualization**: Different protocols show different paths on Edgeworth Box

**Lesson 4: Convergence Dynamics**
- Agents make repeated trades at equilibrium exchange ratio
- Inventories move along budget line toward equilibrium
- Stop when no further mutually beneficial trades possible
- **Visualization**: Animation showing trade-by-trade movement

---

## Economic Design Questions (ANSWER BEFORE CODING)

### Q1: What is the "correct" bilateral bargaining outcome?

**Theoretical Answer**: In pure exchange with no frictions, competitive equilibrium where:
- MRS₁ = MRS₂ = p_A/p_B (tangency condition)
- Budget constraints satisfied (allocations sum to total endowment)
- No further mutually beneficial trades (Pareto optimal)

**Implementation Question**: How do we computationally find this equilibrium?

**Options**:
1. **Analytical solution** (if utility functions permit)
   - CES: Closed-form solution exists
   - Quadratic: May have analytical solution
   - Translog: Requires numerical methods

2. **Numerical optimization**
   - Minimize |MRS₁ - MRS₂| subject to budget constraints
   - Use Newton-Raphson or similar
   - Must be deterministic and robust

3. **Grid search**
   - Enumerate all feasible allocations
   - Find the one with MRS₁ closest to MRS₂
   - Computationally intensive but guaranteed to work

**Decision needed**: Which approach for each utility type?

### Q2: How should agents execute trades toward equilibrium?

**Options**:

**A. Fixed exchange ratio (from equilibrium)**
- Solve for equilibrium once at pairing
- Calculate p* = MRS at equilibrium
- Trade at this fixed ratio each tick until convergence
- **Pros**: Theoretically clean, demonstrates price-taking behavior
- **Cons**: Requires solving equilibrium first, integer rounding issues

**B. Greedy MRS-based**
- Each tick, calculate current MRS for both agents
- If MRS₁ ≠ MRS₂, trade in direction that equalizes them
- Use current MRS as trade price
- **Pros**: Works with any starting point, adaptive
- **Cons**: May oscillate, path-dependent

**C. One-shot to equilibrium**
- Solve for equilibrium allocation
- Execute single large trade to reach it (if feasible)
- **Pros**: Fastest convergence, clean
- **Cons**: May not be integer-feasible, less pedagogical (no path shown)

**Decision needed**: Which approach is most pedagogically valuable?

### Q3: How to handle integer constraints?

**The Problem**: Equilibrium may require fractional inventories (e.g., 6.7A, 6.3B)

**Options**:

**A. Round to nearest integers**
- Risk violating budget constraint (inventories may not sum to total)
- Need coordinated rounding strategy

**B. Accept near-equilibrium**
- Stop trading when within 1 unit of equilibrium
- Test for mutually beneficial trades at that point
- Natural stopping condition

**C. Use exchange ratios**
- Trade at integer ratio approximating equilibrium price
- E.g., p* = 1.5 → trade 2B for 3A
- Continue until no beneficial integer ratio exists

**Decision needed**: Which approach is most economically sound?

### Q4: When should agents unpair?

**Options**:

**A. When at equilibrium** (within integer tolerance)
- Test: |MRS₁ - MRS₂| < threshold
- **Risk**: May unpair before exhausting gains

**B. When trade fails**
- Attempt trade, if ΔU ≤ 0 for either agent, unpair
- **Current behavior**: This is what legacy protocol does
- **Risk**: May unpair far from equilibrium

**C. When no beneficial integer trade exists**
- Test all possible integer trade sizes
- If none improve both utilities, unpair
- **Most conservative**: Exhausts all Pareto improvements

**Decision needed**: What's the correct stopping condition?

---

## Visualization Design Questions

### Q5: What should the Edgeworth Box panel show?

**Essential Elements**:
1. **Box dimensions**: Total endowment (W_A, W_B)
2. **Initial endowment point**: Where agents start
3. **Current allocation point**: Where agents are now
4. **Contract curve**: Locus of tangency points (where MRS₁ = MRS₂)
5. **Indifference curves** (optional): Agent 1 from bottom-left, Agent 2 from top-right
6. **Budget line**: From initial endowment at equilibrium price ratio
7. **Equilibrium point**: Target allocation

**Questions**:
- Should we draw indifference curves? (Computationally intensive, may clutter)
- Should we show the price ratio line? (Pedagogically useful)
- Should we animate trade-by-trade movement? (Cool but complex)
- Should we show numerical values (utility, MRS)? (Yes for pedagogy)

**Technical Constraint**: Must integrate with existing pygame renderer architecture

### Q6: How to handle different utility functions in visualization?

**Issue**: Contract curve shape depends on utility functions
- CES with ρ=0 (Cobb-Douglas): Diagonal line
- CES with ρ≠0: Curved
- Linear: Straight line (corner solutions possible)
- Quadratic: Curved with potential satiation

**Options**:

**A. Pre-compute contract curve**
- Numerically solve MRS₁(A,B) = MRS₂(W_A-A, W_B-B) for all A,B
- Cache the curve
- Draw curve on panel

**B. Draw on-demand**
- Only calculate contract curve when Edgeworth panel is visible
- Update when utility functions change (unlikely mid-sim)

**C. Don't draw contract curve**
- Only show current point and equilibrium point
- Simpler but less pedagogical

**Decision needed**: What's the minimum viable visualization?

---

## Protocol Design Specification (DRAFT)

### Edgeworth Box Bargaining Protocol

**Name**: `edgeworth_competitive_equilibrium`

**Economic Mechanism**: Solves for the 2-agent pure exchange competitive equilibrium where MRS₁ = MRS₂, then executes trades at the equilibrium price ratio until convergence.

**Algorithm Sketch**:

```python
class EdgeworthBoxBargaining(BargainingProtocol):
    def negotiate(self, pair: tuple[int, int], world: WorldView) -> list[Effect]:
        # 1. Check if agents are already near equilibrium
        if self._is_near_equilibrium(agent_a, agent_b, tolerance=0.1):
            return [Unpair(reason="equilibrium_reached")]
        
        # 2. Solve for equilibrium if not cached
        if not self._has_cached_equilibrium(pair):
            equilibrium = self._solve_equilibrium(agent_a, agent_b)
            self._cache_equilibrium(pair, equilibrium)
        else:
            equilibrium = self._get_cached_equilibrium(pair)
        
        # 3. Find trade toward equilibrium at fixed ratio
        trade = self._find_convergence_trade(
            agent_a, agent_b, equilibrium.price_ratio
        )
        
        if trade is None:
            # No beneficial integer trade exists
            return [Unpair(reason="no_beneficial_trade")]
        
        # 4. Execute trade
        return [Trade(...)]
```

**Key Design Decisions**:
1. **Equilibrium solver**: Numerical method (Newton-Raphson) for all utility types
2. **Trade execution**: Fixed price ratio from equilibrium solution
3. **Integer handling**: Accept near-equilibrium when no beneficial integer trade exists
4. **Stopping condition**: Unpair when trade attempt fails (ΔU ≤ 0)

**State Management**:
- Store equilibrium solution per pair (price ratio, target allocations)
- Clear cache on unpair
- Recalculate if inventories differ significantly from expected path

### Alternative Protocols for Comparison

**For pedagogical contrast, implement simpler protocols first**:

1. **`myopic_barter`** - Current compensating block (already exists as `legacy`)
2. **`nash_symmetric`** - Split surplus equally (already exists as `split_difference`)
3. **`walrasian_tatonnement`** - Iterative price adjustment (NEW, simpler than full equilibrium)
4. **`edgeworth_competitive_equilibrium`** - Full equilibrium solver (NEW, most sophisticated)

---

## Scenario Design Specification (DRAFT)

### Scenario 1: Pure Barter, Identical Utilities

**File**: `scenarios/demos/bilateral_ces_identical.yaml`

**Setup**:
- 2 agents only
- Small grid (5×5)
- Agent 0: 8A, 2B
- Agent 1: 2A, 8B
- Both: CES utility (ρ=0, wA=wB=0.5) → Cobb-Douglas
- Vision radius = 5 (can see entire grid)

**Expected Outcome**:
- Equilibrium: Both agents end with 5A, 5B (equal split)
- Price ratio: p* = 1.0 (symmetric preferences)
- Utility increase: ~3.16 → ~5.0 (both agents)

**Pedagogical Goal**: Show simplest case, symmetric gains

### Scenario 2: Different Preferences

**File**: `scenarios/demos/bilateral_ces_different.yaml`

**Setup**:
- 2 agents only
- Agent 0: 8A, 2B, CES (ρ=0, wA=0.7, wB=0.3) → values A more
- Agent 1: 2A, 8B, CES (ρ=0, wA=0.3, wB=0.7) → values B more

**Expected Outcome**:
- Equilibrium: Agent 0 ends with more A, Agent 1 with more B (asymmetric)
- Price ratio: p* ≠ 1.0 (reflects preference differences)
- Both agents gain utility

**Pedagogical Goal**: Show how preference differences determine equilibrium prices

### Scenario 3: Linear vs CES

**File**: `scenarios/demos/bilateral_linear_ces.yaml`

**Setup**:
- Agent 0: Linear utility (vA=1.0, vB=1.5)
- Agent 1: CES utility (ρ=-0.5) → complementary goods

**Expected Outcome**:
- Different contract curves for different utility types
- Linear agent may have corner solution
- Demonstrates generality of approach

**Pedagogical Goal**: Show protocol works with heterogeneous utilities

---

## Implementation Priorities (AFTER PLANNING COMPLETE)

**DO NOT START IMPLEMENTATION UNTIL USER APPROVES PLAN**

When approved, implement in this order:

1. **Equilibrium Solver Module** (`src/vmt_engine/econ/edgeworth.py`)
   - Generic solver for 2-agent competitive equilibrium
   - Works with all utility types
   - Returns: (price_ratio, allocation_a, allocation_b, welfare_gains)

2. **Edgeworth Box Protocol** (`src/vmt_engine/protocols/bargaining/edgeworth_box.py`)
   - Uses equilibrium solver
   - Executes incremental trades
   - Deterministic, robust error handling

3. **Simple Scenarios** (start with simplest)
   - `bilateral_ces_identical.yaml` first
   - Test with all existing protocols for comparison
   - Document actual vs expected behavior

4. **Visualization Panel** (after protocols work)
   - New panel in pygame renderer
   - Shows box, current point, equilibrium
   - Toggle on/off like other panels

5. **Additional Scenarios** (after validation)
   - Different utilities
   - Different endowments
   - Edge cases (corner solutions, satiation)

---

## Open Questions for Discussion

**Before implementing anything, we need to decide**:

1. **Equilibrium solver**: Analytical (where possible) vs numerical (always)? Trade-offs?
2. **Trade execution**: Fixed ratio vs adaptive MRS? Which is more pedagogically clear?
3. **Integer constraints**: How to handle? Accept near-equilibrium or require exact?
4. **Visualization**: Full contract curve or minimal viable? Performance concerns?
5. **Protocol comparison**: Which protocols to implement for pedagogical contrast?
6. **Scenario design**: Which utility function combinations are most instructive?

**Next step**: Discuss these questions, make decisions, THEN start implementation.

---

## Success Criteria

**Pedagogical Success**:
- ✅ Student can see gains from trade visually in Edgeworth Box
- ✅ Student understands difference between "any beneficial trade" vs "equilibrium trade"
- ✅ Student sees how different bargaining protocols lead to different outcomes
- ✅ Student can experiment with different utility functions and see how equilibrium changes

**Technical Success**:
- ✅ Deterministic behavior (same seed → same result)
- ✅ Works with all utility types (CES, Linear, Quadratic, Translog, Stone-Geary)
- ✅ Integer constraints handled gracefully
- ✅ Clean protocol interface (follows existing patterns)
- ✅ Robust error handling (solver failures, edge cases)

**Economic Success**:
- ✅ Equilibrium solution is Pareto optimal
- ✅ Agents reach contract curve (or near-equilibrium given integer constraints)
- ✅ Price ratio reflects true marginal rates of substitution
- ✅ No mutually beneficial trades remain at termination

---

## References

**Existing VMT Documentation**:
- `docs/CURRENT/critical/EDGEWORTH_BOX_BARGAINING_PROTOCOL.md` - Initial design from December 2024
- `docs/2_technical_manual.md` - 7-phase tick cycle, current protocols
- `scenarios/demos/edgeworth_box_4agent.yaml` - Existing 4-agent scenario

**Economic Theory**:
- Mas-Colell, Whinston, Green (1995) - Microeconomic Theory, Chapter 15 (General Equilibrium)
- Varian (2014) - Intermediate Microeconomics, Chapter 32 (Exchange)

**Implementation Patterns**:
- `src/vmt_engine/protocols/base.py` - Protocol interface and Effect types
- `src/vmt_engine/protocols/bargaining/legacy.py` - Example bargaining protocol
- `tests/helpers/builders.py` - Test patterns for protocol development

---

## Document Status: PLANNING ONLY

**🚨 CRITICAL REMINDER**: This is a planning document. No code changes should be made until:
1. All open questions are answered
2. User explicitly approves the design
3. User says "start implementing"

**Current Phase**: Design discussion and decision-making
**Next Phase**: Implementation (AFTER approval)
