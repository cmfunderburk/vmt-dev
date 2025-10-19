# VMT Project Orientation & Comprehensive Action Plan
**Date:** October 18, 2025  
**Status:** Production Ready (Core) / Planning Next Features

---

## Executive Summary

The VMT (Visualizing Microeconomic Theory) project is a **deterministic spatial agent-based simulation** for teaching and researching microeconomic behavior. The core engine successfully demonstrates bilateral barter exchange with foraging in a spatial grid environment. While the core is production-ready with 54+ passing tests, several critical documentation tasks and planned features await implementation.

## Current Project State

### ✅ What's Working Well

1. **Core Engine** - Fully functional 7-phase deterministic simulation
   - Perception → Decision → Movement → Trade → Forage → Resource Regeneration → Housekeeping
   - Strict determinism with seeded reproducibility
   - Spatial grid with agent movement and resource dynamics

2. **Economic Systems**
   - CES and Linear utility functions with zero-inventory guards
   - Bilateral barter with reservation-price negotiation
   - Sophisticated price search algorithm handling discrete goods
   - Trade cooldown system preventing futile loops

3. **Infrastructure**
   - SQLite telemetry (99% space savings over CSV)
   - PyQt5 GUI launcher and log viewer
   - Comprehensive test suite (54+ tests)
   - YAML-based scenario configuration

4. **Innovation Beyond Original Vision**
   - Compensating discrete price search (solves integer rounding issues)
   - Trade/resource cooldown mechanisms
   - Production-quality logging infrastructure

### ⚠️ Current Limitations

1. **No monetary system** - Pure barter economy only
2. **No markets** - Only bilateral (1:1) trades
3. **No production** - Pure exchange economy with foraging
4. **No advanced features** - No game theory, information asymmetry, or mechanism design

---

## Critical Open Issues & Gaps

### 🔴 HIGH PRIORITY - Foundational Polish (from Strategic Roadmap)

Based on `docs/tmp/code_review.md`, these items from the initial milestone remain **incomplete**:

1. **Core Engine Documentation** (`vmt_engine/README.md`)
   - **Status:** ❌ Does not exist
   - **Impact:** Developers lack quick reference for engine architecture
   - **Action:** Create technical overview of 7-phase cycle and system responsibilities

2. **Foundational Scenario** (`scenarios/foundational_barter_demo.yaml`)
   - **Status:** ❌ Does not exist
   - **Impact:** No executable tutorial for new users
   - **Action:** Create heavily-commented 3-4 agent scenario as learning example

3. **Integration Test** (`tests/test_barter_integration.py`)
   - **Status:** ❌ Missing (only a foraging integration test exists)
   - **Impact:** No end-to-end validation of barter scenarios
   - **Action:** Create deterministic multi-agent barter scenario test

4. **Code Clarity Pass**
   - **Status:** ⚠️ Partially complete
   - **Issues:** 
     - Economic "why" comments missing in `matching.py` and `utility.py`
     - Complex telemetry in `find_compensating_block` obscures logic
   - **Action:** Add explanatory comments, consider refactoring telemetry

### 🟡 MEDIUM PRIORITY - Code Quality Issues

From `docs/tmp/lintcetera.md` analysis:

1. **Type Inconsistencies**
   - **Issue:** Schema uses `float` for `vision_radius`, `interaction_radius`, `bucket_size` but code expects `int`
   - **Impact:** Type mismatches could cause runtime errors
   - **Action:** Fix schema.py to use `int` for spatial parameters

2. **Naming Inconsistencies**
   - **Issue:** `ΔA_max` in docs vs `dA_max` in code
   - **Impact:** Documentation/code mismatch
   - **Action:** Standardize to `dA_max` everywhere

3. **Code Organization**
   - **Issue:** Self-import in `foraging.py:24`
   - **Impact:** Architectural smell suggesting circular dependencies
   - **Action:** Refactor module structure

4. **Minor Code Issues**
   - Unused imports (4 files)
   - Bare except clause in `db_loggers.py:397`
   - TODO comments in log viewer (trajectory visualization, trade filtering)

### 🟢 LOW PRIORITY - Documentation & Infrastructure

1. **Type System Documentation**
   - `docs/4_typing_overview.md` exists but needs:
     - SQLite telemetry section (v1.1+)
     - Missing parameters (`resource_growth_rate`, `trade_cooldown_ticks`)
     - Note that Section 11 (cross-language) is aspirational

2. **Whitespace/Style Issues**
   - 85% of flake8 errors are trailing whitespace
   - No automated formatter in use
   - Consider adopting `black` + pre-commit hooks

---

## Comprehensive Action Plan

### Phase 1: Foundational Polish (1-2 days)
**Goal:** Solidify foundation before adding features

- [ ] **1.1 Create `vmt_engine/README.md`**
  - Document 7-phase tick cycle with diagram
  - Explain each system's responsibility
  - Include determinism guarantees

- [ ] **1.2 Create `foundational_barter_demo.yaml`**
  - 3-4 agents with different utilities
  - Extensive inline comments explaining each parameter
  - Expected outcomes documented

- [ ] **1.3 Create `test_barter_integration.py`**
  - Run foundational demo for fixed ticks
  - Assert final inventories match expected
  - Verify specific trades occurred
  - Check conservation of goods

- [ ] **1.4 Add Code Comments**
  - `matching.py`: Explain price-probing economic rationale
  - `utility.py`: Document zero-inventory guard logic
  - Mark telemetry-heavy sections for future refactoring

- [ ] **1.5 Fix Inconsistencies**
  - Global replace `ΔA_max` → `dA_max` in docs
  - Update `matching.py` docstring
  - Fix type hints: `vision_radius: int`, etc.

### Phase 2: Code Quality Pass (1 day)
**Goal:** Clean codebase for maintainability

- [ ] **2.1 Fix Critical Issues**
  - Resolve self-import in `foraging.py`
  - Replace bare except with specific exception
  - Remove unused imports
  - Fix float/int type mismatches in schema

- [ ] **2.2 Setup Code Quality Tools**
  - Configure `black` for formatting
  - Setup `isort` for imports
  - Create `.pylintrc` with domain-appropriate overrides
  - Add pre-commit hooks

- [ ] **2.3 Complete TODOs**
  - Log viewer trajectory visualization (or mark as future)
  - Trade filtering implementation (or document scope)

### Phase 3: Mode Toggles (2-3 days)
**Goal:** Add forage-only/trade-only cycling

- [ ] **3.1 Schema Updates**
  - Add `mode_schedule` to `scenarios/schema.py`
  - Support `forage_ticks` and `trade_ticks` parameters

- [ ] **3.2 Engine Implementation**
  - Modify simulation loop to check current mode
  - Skip trade phase in forage-only mode
  - Skip forage phase in trade-only mode

- [ ] **3.3 Testing & Telemetry**
  - Create `test_mode_toggles.py`
  - Log mode changes to database
  - Add mode column to decisions table

### Phase 4: Money Introduction (3-4 days)
**Goal:** Add quasilinear utility money system

- [ ] **4.1 Core Changes**
  - Add `M: int` to inventory
  - Implement `U_total = U_goods(A,B) + λ*M`
  - Add `lambda_money` parameter

- [ ] **4.2 Trading Updates**
  - Extend quotes for A-M, B-M pairs
  - Generalize matching for money trades
  - Ensure conservation of money

- [ ] **4.3 Testing**
  - Create `test_money_quasilinear.py`
  - Verify utility accounting with money
  - Test money as medium of exchange

### Phase 5: Market Prototype (4-5 days)
**Goal:** Implement posted-price markets

- [ ] **5.1 Market Detection**
  - Find connected components of agents
  - Apply market rules if group size ≥ threshold

- [ ] **5.2 Price Mechanism**
  - Aggregate bids/asks
  - Determine clearing price
  - Match buyers/sellers at market price

- [ ] **5.3 Testing & Analysis**
  - Create market scenario tests
  - Log market events
  - Verify price convergence

---

## Critical Decisions Needed

### 🔴 Must Decide Now

1. **Energy Budget Feature**
   - Three detailed proposals in `tmp/` (800+ lines each!)
   - **Decision Needed:** Implement now or defer?
   - **Recommendation:** Defer - focus on money/markets first

2. **Type System Enforcement**
   - Schema allows floats, code expects ints
   - **Decision Needed:** Strict typing with mypy or stay flexible?
   - **Recommendation:** Fix schema to use ints, add mypy gradually

### 🟡 Decide Soon

3. **Documentation Standard**
   - Multiple overlapping planning docs in `archive/`
   - **Decision Needed:** Single source of truth location?
   - **Recommendation:** Keep `docs/` canonical, archive old versions

4. **Containerization**
   - Detailed Docker analysis in `tmp/`
   - **Decision Needed:** Docker for headless only or full GUI support?
   - **Recommendation:** Start with headless containerization

### 🟢 Decide Later

5. **Money Implementation**
   - Option A: Quasilinear (simple, λ parameter)
   - Option B: Instrumental (emergent value)
   - **Current Plan:** Start with A, consider B for a future iteration

6. **Market Mechanisms**
   - Posted-price vs. double auction
   - Local vs. global markets
   - **Current Plan:** Start with local posted-price

---

## Risk Assessment

### High Risks
1. **Scope Creep** - Energy budget feature could consume weeks
2. **Breaking Changes** - Money introduction affects entire trade system
3. **Performance** - Market mechanisms may slow large simulations

### Mitigation Strategies
1. Strict adherence to roadmap phases
2. Comprehensive testing before each feature
3. Performance benchmarks with 50+ agent scenarios

---

## Next Immediate Steps (This Week)

1. **Monday-Tuesday:** Complete Foundational Polish checklist
2. **Wednesday:** Code quality pass and tooling setup
3. **Thursday-Friday:** Begin mode toggles implementation
4. **Weekend:** Review progress, update this orientation doc

---

## Questions Requiring Your Input

1. **Energy Budget:** The `tmp/` folder has THREE extensive energy budget proposals. Should we:
   - Implement the consensus design now?
   - Defer entirely to focus on money/markets?
   - Create a simplified version?

2. **Documentation:** Should we consolidate the many planning documents in `archive/`?

3. **Testing Strategy:** Current tests are comprehensive but should we add:
   - Performance benchmarks?
   - Scenario replay tests?
   - GUI automation tests?

4. **Release Planning:** How should we batch the upcoming features into releases?

---

## Appendix: File Organization

### Key Documentation
- `docs/1_project_overview.md` - User guide
- `docs/2_technical_manual.md` - Technical reference
- `docs/3_strategic_roadmap.md` - **Authoritative roadmap**
- `docs/4_typing_overview.md` - Type specifications

### Recent Analysis (tmp/)
- `code_review.md` - Comprehensive review finding gaps
- `lintcetera.md` - Code quality analysis
- `*energy_budget*.md` - Multiple competing proposals
- `*containerization*.md` - Docker feasibility studies

### Archive (historical context)
- Various planning documents from earlier phases
- Consider these deprecated unless specifically referenced

---

*This orientation document should be updated weekly as tasks complete and priorities shift.*
