Below is a direct mapping of options to every question in **questions_to_answer.md**, using your Stage docs and roadmap as constraints. I keep options terse with pros/cons. Citations point to the specific lines in your docs.

# I. Scope & Future Direction

## I.1 Economic Models & Simulation Modes

* What models?
  **Option A**: Three tracks (ABM, Game Theory, Neoclassical) with shared primitives. Pros: matches launcher and comparison plans. Cons: needs strict layer rules.  
  **Option B**: Engines-first API with a `shared/` core. Pros: clear entry points. Cons: more upfront interfaces. 
  **Option C**: Minimal consolidation now; revisit once Stage 3 lands. Pros: fastest. Cons: weaker theory alignment. 

* Coexist vs runtime choice?
  **Coexist** via launcher + comparison tool. Pros: side-by-side results; pedagogy. Cons: cross-process data hand-off.  

* Shared code?
  **Shared** agents/utilities across tracks. Pros: single source of truth for preferences. Cons: ABM must not import GT/Neo. 

* Side-by-side comparison?
  **Yes**, via ComparisonTool. Pros: charts and table already scaffolded. Cons: harmonize metrics. 

## I.2 Future Extensibility

* New search/matching/bargaining/utilities expected?
  **Option A**: Registry-centered growth per track with adapters. Pros: unified listing per track. Cons: registry upkeep. 
  **Option B**: Track-local additions only. Pros: isolation. Cons: harder cross-track reuse. (Implied by separate track managers) 

* External researchers?
  **Option A**: Public registry + documented extension points. Pros: discoverable. Cons: versioning/compat checks. 

## I.3 User Entry Points

* Beyond launcher (API, batch)?
  **Option A**: Batch runner + analyzer in launcher. Pros: built-in. Cons: dual surface to support. 
  **Option B**: Headless scripting API mirroring launcher configs. Pros: reproducibility. Cons: API freeze pressure. (Tracks + scenario manager suggest feasible) 

* Multiple engines simultaneously?
  **Option A**: Yes via LaunchManager. Pros: isolated processes, trackable IDs. Cons: interprocess results merge.  

* Hot swapping protocols mid-run?
  **Option A**: Not required. Keep per-run immutability. Pros: simpler validation. Cons: less interactive exploration. (UI does not imply dynamic swaps) 

# II. Current Codebase Alignment

## II.1 Agent-Based Components

* Where do agents live?
  **Option A**: `agent/` owns Agent + utilities; tracks depend on it. Pros: one home for preferences. Cons: avoid GT/Neo upstream pulls. 
  **Option B**: `econ/` utilities independent; agents import utilities. Pros: clean solvers. Cons: two places to touch. (Edgeworth/GT expects reusable utilities) 

* Do utilities belong with agents?
  **Option A**: Yes, if you want single discovery path. Pros: clarity. Cons: tighter coupling to ABM. 
  **Option B**: No, keep domain-independent for GT/Neo reuse. Pros: solver purity. Cons: another layer. 

## II.2 Spatial Components

* Group grid/index/movement?
  **Option A**: `agent_based/spatial/`. Pros: scope limited to ABM and Stage 5 market detection. Cons: unused by GT/Neo. 
  **Option B**: Data vs behavior split. Pros: separation of concerns. Cons: more modules.

* Where does foraging belong?
  **Option A**: ABM systems with spatial hooks. Pros: aligns with trade logs and market detection. Cons: straddles agent vs spatial. 

## II.3 Protocol Architecture

* Fixed pipeline vs reorderable?
  **Option A**: Fixed per track, composable across tracks by registry. Pros: simpler inside each track; still extensible. Cons: cross-track adapter work. 
  **Option B**: Fully composable pipeline. Pros: research flexibility. Cons: higher surface for bugs.

## II.4 Systems / Subsystems

* Keep 11 systems together or split by domain?
  **Option A**: Split by domain (agent | spatial | protocol). Pros: maps to stages and registry. Cons: one-time churn.  
  **Option B**: Keep systems but add orchestration module. Pros: fewer moves. Cons: harder discoverability. 

# III. Dependencies & Coupling

## III.1 Import Flow

* What should the hierarchy be?
  **Option A**: Core → (agent,econ) → (spatial,protocol) → tracks → launcher. Pros: prevents upward imports; suits LaunchManager and TrackManagers. Cons: interfaces needed.  
  **Option B**: Engines-first (`engines/`) import `shared/`. Pros: fewer cross-imports. Cons: `shared/` still needs structure. 

## III.2 Coupling Risks

* What breaks if files move?
  **Option A**: Registry and ScenarioManager isolate churn. Pros: stable external interface. Cons: write shims.  

## III.3 Shared State & Configuration

* What is global?
  **Option A**: Immutable config objects per run (e.g., Decimal precision). Pros: batch-safe, headless-safe. Cons: pass-through overhead. (Fits “Settings” and track configs) 

# IV. Testing & Validation

## IV.1 Test Fragility

* How to keep tests stable?
  **Option A**: Track-level suites: GT (Edgeworth, bargaining), ABM (trade logs), Neo (tatonnement). Pros: maps to deliverables. Cons: more fixtures.  

## IV.2 Regression Risk

* Silent failures?
  **Option A**: Seeded scenarios + comparison tool metrics. Pros: visible in table and charts. Cons: define canonical metrics. 

## IV.3 Incremental Validation

* Phase by phase?
  **Option A**: Move by domain layer, run GT demos after each step (Nash/KS/Rubinstein). Pros: rapid feedback. Cons: partial duplication.  

# V. Implementation Effort

## V.1 Scope of Work

* Scale of moves?
  **Option A**: Two-phase plan: domain split now, engine unification with Stage 4. Pros: unblocks Stage 3; aligns with launcher. Cons: two rounds of edits. 

## V.2 Complexity Assessment

* Simplest viable?
  **Option C (Minimal)** to land Stage 3 quickly; then fold into A/B. Pros: velocity. Cons: debt to pay. 

## V.3 Developer Bandwidth

* Parallel work?
  **Option A**: Keep launcher scaffold and GT work moving while refactoring agent/econ boundary. Pros: independent branches converge in Stage 4. 

# VI. Documentation & Maintainability

## VI.1 Self-Documenting Structure

* Where do new things go?
  **Option A**: One-page diagram + “extension guide” tied to registry and scenario manager. Pros: obvious locations. 

## VI.2 Entry Points & Navigation

* Obvious engine entry points?
  **Yes**: UnifiedLauncher with TrackManagers. Pros: single window. 

## VI.3 Extension Patterns

* Patterns to add protocols/utilities?
  **Option A**: “Add to registry + adapter if cross-track.” Pros: reproducible pattern. Cons: registry bloat. 

# VII. Economic/Theoretical Alignment

## VII.1 Conceptual Clarity

* Does structure reflect theory?
  **Option A**: Mirror theory in GT/Neo (agents, feasible set, equilibrium), ABM mirrors simulation pipeline. Pros: matches pedagogy and your Stage plans.  

## VII.2 Future Economic Models

* Support for neoclassical equilibrium?
  **Option A**: Separate Neo solvers with shared utilities and comparison against ABM. Pros: clear benchmark; Scarf counterexample planned.  

* Protocol-theoretic scenarios fit?
  **Option A**: GT protocols registered, optionally imported to ABM. Pros: reuse bargaining in ABM. 

# VIII. Risk & Rollback

## VIII.1 Failure Scenarios

* What could go wrong and fallback?
  **Option A**: Stage-scoped branches with revert points; registry and scenario shims to minimize blast radius. Pros: abortable after each phase. 

## VIII.2 Decision Lock-In

* Reversibility?
  **Option A**: Engines-first keeps reversal feasible because `shared/` remains separable. Pros: low lock-in. 

## VIII.3 Technical Debt

* New vs resolved debt?
  **Option A**: Debt reduced if domain split + registry adopted; debt added if you stop at Minimal C. 

# IX. Team & Organizational

## IX.1 Code Ownership

* Who owns what?
  **Option A**: Track ownership, shared core reviewed by all. Pros: matches TrackManagers and deliverables.  

## IX.2 Onboarding & Communication

* Will structure onboard faster?
  **Option A**: Launcher + ComparisonTool + tutorials in Help menu. Pros: guided entry. 

## IX.3 Compatibility with Other Tools

* Effects on launcher, telemetry, pygame, scripts?
  **Option A**: Use LaunchManager as sole integration seam; pygame stays process-isolated; results cached for analysis. Pros: clear seams.  

# X. Decision Criteria

## X.1 Must-Haves

* Acyclic imports, multi-model support, obvious placement:
  **Option A** (component-oriented with registry) best satisfies.  

## X.2 Nice-to-Haves

* Theory-matching, extensions without edits, simple docs:
  **Option A** again, with explicit extension guide. 

## X.3 Trade-Offs to Accept

* If speed matters, pick **C→A** path: minimal move now, converge to A with Stage 4. Pros: keeps Stage 3 momentum.  

---

## Extra mappings tied to stage content (selected high-leverage items)

* Edgeworth Box and bargaining live under GT; export protocols to ABM via registry when needed.  
* Market Info is ABM-only and must emerge from trades, then optionally inform bargaining. Architectural implication: ABM information systems should not import GT/Neo.   
* Neo forms the benchmark, compared via ComparisonTool and dedicated analyzer. Keep Neo solvers functional and stateless.  
