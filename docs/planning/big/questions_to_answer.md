# Decision Framework: Questions to Answer

This document outlines the comprehensive set of questions that need answers before committing to a refactoring approach. Use this as a checklist during brainstorming—each question narrows the design space.

---

## Preamble: Why These Questions Matter

The three options in `a.md` are fundamentally different in their scope and philosophy. Before choosing, we need to understand:
- **What the codebase will need to support** (economic models, simulation types, user interfaces)
- **What makes maintenance easier or harder** (dependencies, file discovery, extension points)
- **What risks exist** (circular imports, breaking changes, test complexity)
- **What effort we can justify** (ROI on refactoring time)

These questions help surface hidden assumptions and trade-offs.

---

## I. SCOPE & FUTURE DIRECTION

### I.1 Economic Models & Simulation Modes
- What economic models do we plan to support? (agent-based, game-theoretic, neoclassical, others?)
- Will these models **coexist** in the same simulation, or are they **mutually exclusive** runtime choices?
- How distinct are their implementations? (e.g., do they share agent/spatial/protocol code?)
- Do we expect users to **compare** model outputs side-by-side, or pick one per run?

### I.2 Future Extensibility
- Are we planning new **search protocols**? How many? (affects where search code should live)
- Are we planning new **matching algorithms**? How many?
- Are we planning new **bargaining protocols**? How many?
- Are we planning new **utility functions**? How many?
- Will these be added by **core team only**, or by **external researchers**? (affects documentation/clarity needs)

### I.3 User Entry Points
- Beyond the launcher, will there be other ways to invoke the system? (API, library mode, batch processing?)
- Will users ever need to **instantiate multiple engines simultaneously**? (affects whether engines can share state)
- Do we need to support **"hot swapping"** protocols during a simulation run?

---

## II. CURRENT CODEBASE ALIGNMENT

### II.1 Agent-Based Components
- **Where does agent definition logically belong?** Currently split between `core/agent.py` and `econ/utility.py`. Should they be:
  - Together in one `agent/` module?
  - Separate with clear dependency flow?
  - Something else?

- **Do utilities (CES, linear, etc.) belong with agents?** Or should they be:
  - Domain-independent economic components?
  - Tightly coupled to agent class?

### II.2 Spatial Components
- **Should grid, spatial_index, and movement be grouped?** All three are "spatial concerns," but:
  - Grid and spatial_index are data structures
  - Movement is behavior (agents move)
  - Should behavior and data live together?

- **Where does foraging logic belong?** Currently in `systems/foraging.py`, but foraging is:
  - Agent decision-making (systems?)
  - Movement-related (spatial?)
  - Part of the broader simulation flow (systems?)

### II.3 Protocol Architecture
- **Are search, matching, and bargaining always used as a fixed pipeline?** Or might future protocols:
  - Use only matching (centralized market)?
  - Skip bargaining (fixed prices)?
  - Reorder these steps?

- **Do protocols need to be "composable"?** (e.g., mix greedy matching with compensating-block bargaining?)
  - If yes: more flexible architecture needed
  - If no: simpler to treat as fixed combinations

### II.4 Systems / Subsystems
- **Are the 11 files in `systems/` really all simulation subsystems?** Current breakdown:
  - `decision.py`, `trading.py`, `perception.py` — agent decision-making
  - `movement.py` — spatial/behavioral
  - `foraging.py` — agent behavior
  - `housekeeping.py` — resource management
  - `matching.py`, `trade_evaluation.py` — protocol helpers (?)
  - Others?
  
  Question: Do these belong in **one module** that coordinates subsystems, or should they be **split across domain modules** (agent, spatial, protocol)?

---

## III. DEPENDENCIES & COUPLING

### III.1 Import Flow
- **What currently imports from what?** (We need a dependency audit)
  - Are there circular dependencies hiding?
  - Do protocols depend on systems? (suggests poor layering)
  - Do systems depend on protocols? (suggests unclear responsibility)

- **What should the import hierarchy be?** E.g., should:
  - Lower-tier modules never import from higher tiers?
  - Protocols import from agents/spatial but not vice versa?
  - Simulation import from everything?

### III.2 Coupling Risks
- **If we move files, what breaks?** 
  - How many import statements will need updating?
  - Are imports fragile (would changing a module name break many files)?
  - Are there implicit dependencies (code that works but shouldn't)?

- **Can we decouple any modules?** E.g., is telemetry tightly woven into simulation, or can it be optional?

### III.3 Shared State & Configuration
- **What is truly global/shared state?** E.g.:
  - `decimal_config.py` (precision settings)
  - Anything else?
  - Can it be moved safely?

---

## IV. TESTING & VALIDATION

### IV.1 Test Fragility
- **Will this refactoring break tests?** 
  - How many tests import from the modules being moved?
  - Can tests be updated automatically (search/replace), or do they require logic changes?
  - Are there integration tests that depend on directory structure?

- **How do we validate the refactoring didn't break functionality?**
  - Run full test suite before/after?
  - Run simulations with known seeds and compare outputs?
  - Spot-check key workflows?

### IV.2 Regression Risk
- **What's the risk of silent failures?** (Code compiles but behaves differently)
  - Do we have good coverage of trade execution, matching, bargaining?
  - Do we have tests for edge cases (empty markets, single agent, etc.)?

### IV.3 Incremental Validation
- **Can we validate the refactoring in phases?** E.g.:
  - Move one module, run tests, commit
  - Move next module, run tests, commit
  - Or must we do a "big bang" move?

---

## V. IMPLEMENTATION EFFORT

### V.1 Scope of Work
- **How many files need to be moved/renamed?** (~45 currently)
- **How many import statements need updating?** (rough estimate: 100-200?)
- **How many test files need updating?** (rough estimate based on current tests/)
- **How many scripts/utilities import from vmt_engine?** (launcher, view_logs, etc.)

### V.2 Complexity Assessment
- **Which option is simplest?** (Option C < Option A < Option B?)
- **What's the risk-reward trade-off?** (Quick but partial vs. thorough but slower?)
- **Can we do the refactoring incrementally, or does it need to be atomic?**

### V.3 Developer Bandwidth
- **How many developer-hours can we allocate?** (Affects which option is realistic)
- **Is this blocking other work, or can it happen in parallel?**
- **Do we need to maintain the old structure during refactoring?** (harder but safer)

---

## VI. DOCUMENTATION & MAINTAINABILITY

### VI.1 Self-Documenting Structure
- **Does the proposed structure make sense at a glance?** For a new developer:
  - Where would they add a new search protocol?
  - Where would they find the grid implementation?
  - Where is the main simulation loop?
  - Where do utility functions for agents live?

- **Will the structure match economic/game-theoretic theory?** (Or is it just a filing system?)

### VI.2 Entry Points & Navigation
- **Are there obvious entry points for each "engine"?** (agent-based, game-theoretic, neoclassical?)
- **Is the dependency hierarchy clear?** (Does it prevent upward imports?)
- **Can we document it simply?** (One-page architectural diagram?)

### VI.3 Extension Patterns
- **Are there clear patterns for adding new code?** E.g.:
  - "To add a new protocol, create a file in `interaction/X/`"
  - "To add a new utility function, extend `agent/utility/base.py`"
  - Etc.

---

## VII. ECONOMIC/THEORETICAL ALIGNMENT

### VII.1 Conceptual Clarity
- **Does the structure reflect economic theory?** E.g.:
  - Agents (with preferences, endowments)
  - Space/location (if relevant)
  - Interaction mechanisms (search, matching, bargaining)
  - Outcomes/results
  
- **Would an economist understand the code layout?** Or is it purely computer science?

### VII.2 Future Economic Models
- **How will we support neoclassical equilibrium models?** Will they:
  - Reuse agent/utility modules?
  - Replace them?
  - Coexist?
  - Require separate code paths?

- **How will protocol-theoretic scenarios fit?** (Specific matching rules, price mechanisms, etc.)

---

## VIII. RISK & ROLLBACK

### VIII.1 Failure Scenarios
- **What could go wrong?** 
  - Circular import discovered mid-refactoring
  - Tests fail but we can't identify why
  - Import hell makes everything break
  - Effort exceeds estimate

- **What's our rollback strategy?** 
  - Revert to git commit?
  - Keep old structure in parallel?
  - Incremental approach allows abort after each phase?

### VIII.2 Decision Lock-In
- **How reversible is this decision?** 
  - If we choose Option A and regret it, can we switch to Option B?
  - Or will we get locked into the first structure?
  - Is one option more "future-proof" than others?

### VIII.3 Technical Debt
- **Does the refactoring create any new technical debt?** Or resolve existing debt?
- **Will it make future changes easier or harder?**

---

## IX. TEAM & ORGANIZATIONAL

### IX.1 Code Ownership
- **Who will own each module?** Or is all of vmt_engine collectively owned?
- **Does the refactoring change review/approval workflows?**

### IX.2 Onboarding & Communication
- **Will this structure help new developers onboard faster?**
- **Can we explain the structure in a README?** (Simple or complex?)
- **Are there any "gotchas" that need to be documented?**

### IX.3 Compatibility with Other Tools
- **How will this affect:**
  - The launcher (vmt_launcher/)?
  - The telemetry system (vmt_log_viewer/)?
  - The pygame renderer?
  - Scripts (analyze_baseline.py, etc.)?

---

## X. DECISION CRITERIA

### X.1 Must-Haves
- Is acyclic import hierarchy a hard requirement?
- Must we support multiple economic models? How?
- Must new code be obviously placeable?

### X.2 Nice-to-Haves
- Does the structure match economic theory?
- Can extensions be added without modifying existing files?
- Is documentation self-explanatory?

### X.3 Trade-Offs to Accept
- Are we willing to sacrifice some theoretical purity for implementation simplicity? (Option C instead of Option A?)
- Are we willing to spend more effort now for better maintainability? (Option A instead of Option C?)

---

## Follow-Up Discussion Ideas

### After Answering These Questions, Consider:

1. **Create an import dependency graph** — Use these answers to map current imports and identify violations. This data informs effort estimates.

2. **Prototype the chosen option** — If uncertainty remains, pick one and refactor a small subsystem (e.g., just the `agent/` tier) as a proof-of-concept. See if it works before committing to full refactoring.

3. **Define the import rules explicitly** — Once the structure is chosen, write them down (e.g., "Tier N can import from Tier N-1 and below, but never upward"). This prevents accidental re-fragmentation.

4. **Build an "extension guide"** — Document patterns for adding new protocols, utilities, agents, etc. This becomes part of the developer documentation.

5. **Plan the validation strategy** — Before refactoring, decide:
   - Which tests are critical?
   - How will we compare before/after behavior?
   - What's the rollback criterion? (If this happens, we revert)

6. **Consider a "phase 1" vs. "full" refactoring** — Maybe Option C is phase 1 (quick consolidation), and Option A is phase 2 (when we're confident). This reduces risk.

7. **Align with roadmap** — Is this blocking other work? Does it enable Stages 5-7 (neoclassical, market info, etc.)? That affects priority and urgency.

---

## How to Use This Document

1. **Go through each section** and answer the questions that apply
2. **Flag uncertainties** — If you can't answer a question, mark it as "TBD" and investigate separately
3. **Use answers to evaluate options** — E.g., "If we support multiple engines, Option B is better; otherwise, Option A is cleaner"
4. **Revisit trade-offs** — Some answers will conflict; decisions are about which trade-offs you accept
5. **Document your decisions** — Record which questions led to which choices (helps explain to the team)

This isn't a one-time exercise—revisit these as you refactor to ensure assumptions remain valid.

