# Developer Onboarding Integration Plan

**Document Status:** Planning Document  
**Version:** 1.0  
**Created:** 2025-01-27  
**Purpose:** Integrate architectural changes with developer onboarding program  

---

## Overview

The VMT Developer Onboarding Program must be updated to reflect the protocol modularization and utility refactoring. This document outlines the necessary changes and timing.

---

## Current Onboarding Structure

### Existing Modules
1. **Module 0:** Environment Setup (4-6 hours)
2. **Module 1:** Economic Foundations (6-8 hours)
3. **Module 2:** Core Architecture & 7-Phase Cycle (8-10 hours)
4. **Module 3:** Data Structures & Spatial Systems (6-8 hours)
5. **Module 4:** Decision & Matching Systems (10-12 hours)
6. **Module 5:** Money System & Exchange Regimes (8-10 hours)
7. **Module 6:** Testing, Telemetry & Determinism (8-10 hours)

### Optional Tracks
- **Track A:** GUI Development (6-8 hours)
- **Track B:** Protocol Modularization (12-16 hours)

---

## Required Updates After Protocol Implementation

### Module 2: Core Architecture (Major Update)

**Current Content:**
- Monolithic DecisionSystem explanation
- Direct phase implementation
- Inline decision logic

**New Content Needed:**
```markdown
### Section 2.5: Protocol Architecture (NEW - 90 min)

#### Understanding Protocols
- WorldView immutable snapshot
- Effect-based communication
- Protocol lifecycle

#### Protocol Types
- SearchProtocol: Target selection
- MatchingProtocol: Pair formation
- BargainingProtocol: Trade negotiation
- MovementPolicy: Spatial navigation
- ForagingPolicy: Resource collection

#### Effect System
- Effect types and validation
- Application order
- Conflict resolution
- Telemetry integration

#### Hands-on Exercise
1. Trace effects through one tick
2. Implement simple RandomWalk search
3. Compare legacy vs greedy matching
```

### Module 4: Decision & Matching (Complete Rewrite)

**Old Focus:** Monolithic DecisionSystem internals

**New Structure:**
```markdown
## Module 4: Protocols & Market Mechanisms

### Section 4.1: Search Protocols (2 hours)
- Distance-discounted search
- Random walk exploration  
- Memory-based learning
- Implementation exercise

### Section 4.2: Matching Protocols (2 hours)
- Three-pass pairing
- Greedy surplus maximization
- Stable matching (Gale-Shapley)
- Comparative analysis

### Section 4.3: Bargaining Protocols (3 hours)
- Compensating blocks
- Take-it-or-leave-it
- Rubinstein alternating
- Nash bargaining

### Section 4.4: Creating New Protocols (3 hours)
- Protocol template
- Effect generation
- Testing requirements
- Performance considerations
```

### New Module 7: Protocol Development (Add)

```markdown
## Module 7: Developing Custom Protocols

### Learning Objectives
- Implement custom protocol from scratch
- Test protocol properties
- Compare with existing protocols
- Document economic properties

### Project: Implement Ascending Auction Protocol
1. Design protocol interface
2. Implement bid/ask logic
3. Handle multi-tick state
4. Test convergence properties
5. Compare with posted-price

### Deliverables
- Working protocol implementation
- Property-based tests
- Telemetry analysis
- Economic documentation
```

---

## Updates for Utility Modularization

### Module 1: Economic Foundations (Minor Update)

**Section 1.1 Changes:**
```python
# Old import style
from src.vmt_engine.econ.utility import UCES

# New style (after Phase 1)
from src.vmt_engine.econ.base import Utility  # Interface
from src.vmt_engine.econ import UCES         # Implementation

# After full modularization
from src.vmt_engine.econ.utilities.ces import UCES
```

**New Exercise:**
```markdown
### Exercise 1.1.4: Understanding Utility Architecture
1. Read base.py to understand interface
2. Compare two utility implementations
3. Create custom utility following template
4. Add to factory and test
```

---

## Timing of Updates

### Phase 1: Immediate Updates (During Implementation)
- Add warnings to affected modules
- Create "Future Changes" callout boxes
- Document what will change

**Example Warning Box:**
```markdown
⚠️ **Upcoming Change:** This module describes the current 
monolithic DecisionSystem. After protocol modularization 
(Q1 2025), this will be replaced with protocol-based 
architecture. See docs/ssot/ for future design.
```

### Phase 2: Major Updates (After Implementation)
**When:** After protocol system is stable

**Priority Order:**
1. Module 2 (Core Architecture) - Critical
2. Module 4 (Decision/Matching) - Critical  
3. Module 7 (New module) - Important
4. Module 1 (Utilities) - Minor
5. Others - As needed

**Estimated Effort:** 2-3 days total

### Phase 3: Enhanced Materials (Optional)
**When:** After first cohort feedback

**Additions:**
- Video walkthroughs
- Interactive exercises
- Protocol comparison labs
- Research paper implementations

---

## New Onboarding Exercises

### Exercise Set A: Protocol Basics
1. **Trace Effects:** Follow effects through complete tick
2. **Compare Protocols:** Run same scenario with different protocols
3. **Analyze Telemetry:** Compare surplus across protocols
4. **Debug Protocol:** Fix intentionally broken protocol

### Exercise Set B: Protocol Implementation
1. **Simple Protocol:** Implement RandomWalk search
2. **Intermediate:** Implement FirstPrice auction
3. **Advanced:** Implement DoubleAuction market
4. **Research:** Recreate protocol from economics paper

### Exercise Set C: Utility Extensions
1. **Read Structure:** Navigate new utility organization
2. **Add Utility:** Implement Leontief (perfect complements)
3. **Test Utility:** Write comprehensive tests
4. **Document:** Add economic theory documentation

---

## Learning Path Adjustments

### For New Developers (Post-Implementation)

**Week 1:**
- Module 0: Environment (unchanged)
- Module 1: Economics (updated imports)

**Week 2:**  
- Module 2: Architecture (NEW protocol content)
- Module 3: Data Structures (unchanged)

**Week 3:**
- Module 4: Protocols (REWRITTEN)
- Start Module 7 project

**Week 4:**
- Complete Module 7 project
- Module 5: Money System
- Module 6: Testing

### For Existing Developers (Transition)

**Upgrade Path:**
1. Read protocol master plan (2 hours)
2. Complete Module 4 new content (4 hours)
3. Implement one protocol (4 hours)
4. Review own code for updates (2 hours)

**Total Retraining:** ~12 hours

---

## Documentation Dependencies

### Must Update
- Line number references in exercises
- Import statements in code examples
- Architectural diagrams
- System flow descriptions

### Should Update
- Performance benchmarks
- Debugging strategies
- Best practices
- Extension guides

### Nice to Update
- Historical context
- Theory explanations
- Reference links
- Appendices

---

## Success Criteria

### Immediate Success
- [ ] Warnings added to current materials
- [ ] No broken exercises
- [ ] Clear migration path documented

### Post-Implementation Success
- [ ] All modules reflect new architecture
- [ ] New exercises test protocol understanding
- [ ] Onboarding time remains ~50 hours
- [ ] New developers can implement protocols

### Long-term Success
- [ ] Reduced onboarding confusion
- [ ] Faster protocol development
- [ ] Better economic understanding
- [ ] Research-quality contributions

---

## Recommended Approach

### Step 1: Add Warnings (This Week)
```python
# Add to modules 2, 4, 5:
print("⚠️ Protocol modularization in progress - content will update Q1 2025")
```

### Step 2: Create Transition Guide (During Implementation)
- What's changing
- Why it's changing
- How to prepare
- Timeline

### Step 3: Rewrite Affected Modules (After Implementation)
- Focus on Modules 2 and 4
- Add Module 7
- Update exercises

### Step 4: Test with New Developer (Validation)
- Have new developer complete updated program
- Gather feedback
- Iterate based on experience

---

## Resource Requirements

### Documentation Update
- **Effort:** 2-3 days
- **Skills:** Technical writing, Python, Economics
- **Dependencies:** Protocol implementation complete

### Exercise Development
- **Effort:** 3-4 days
- **Skills:** Python, Testing, Pedagogy
- **Dependencies:** Stable protocol system

### Video/Interactive Content (Optional)
- **Effort:** 1-2 weeks
- **Skills:** Video production, Web development
- **Dependencies:** Final architecture

---

## Risk Mitigation

### Risk: Outdated Materials During Transition
**Mitigation:** Clear warnings and timeline

### Risk: Confusion Between Old/New Systems
**Mitigation:** Version all materials clearly

### Risk: Increased Onboarding Time
**Mitigation:** Modular updates, optional advanced content

### Risk: Missing Economic Context
**Mitigation:** Preserve Module 1, enhance theory docs

---

## Summary

### Immediate Actions
1. Add transition warnings to Modules 2, 4
2. Document expected changes
3. Prepare transition guide

### During Protocol Implementation
1. Draft new module content
2. Design new exercises
3. Update code examples

### After Protocol Implementation  
1. Deploy updated modules
2. Test with new developer
3. Iterate based on feedback
4. Archive old materials

**Total Effort:** 5-7 days spread over implementation period

---

**Document Status:** Planning complete, awaiting implementation timeline  
**Owner:** Documentation team  
**Dependencies:** Protocol modularization completion
