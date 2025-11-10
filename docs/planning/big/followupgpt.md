Answering with the missing context restored. You now have three interacting tracks, a unified launcher, an emergence-first ABM, a strategic microfoundation in the Game Theory track, and a neoclassical benchmark layer. Options below respect that architecture.

I keep each question from **questions_to_answer.md** implicit and supply targeted option-sets with pros/cons.

---

# I. Scope and Future Direction

## 1. How many models should VMT support, and how should they coexist?

### **Option A — Three tracks, one shared economic core (your roadmap model)**

Pros: matches roadmap (ABM, GT, Neo) and lets each track build directly on the previous stage; minimizes duplicated code.
Cons: strict type boundaries needed to prevent ABM-state leakage into GT/Neo solvers.

### **Option B — “Engines” as pluggable modules under a common `engine_interface`**

Pros: simplifies launcher integration and allows future modules (auctions, matching markets).
Cons: more abstraction than needed for a three-track design; added overhead to expose compatible APIs for solvers, visualizers, and state logs.

### **Option C — Full integration: ABM ↔ GT ↔ Neo comparative scenario pipeline**

Pros: supports one-click comparisons (emergent vs strategic vs equilibrium) in Stage 4 and Stage 6.
Cons: tight coupling; ABM must provide standardized summary statistics (surplus, allocations, trade ratios) to feed GT/Neo visualizers.

---

## 2. What should the user interact with?

### **Option A — Unified launcher (planned in Stage 4) is the primary surface**

Pros: aligns with roadmap; smooth switching across tracks; one mental model for configuration.
Cons: GUI maintenance cost; slower iteration when adding new protocols.

### **Option B — Launcher + a standalone scripting API**

Pros: gives advanced users a headless mode for batch experiments and reproducible notebooks.
Cons: dual maintenance burden; must freeze public API early.

### **Option C — Launcher orchestrates multiple simulation processes**

Pros: suits ABM (pygame), GT (matplotlib windows), Neo (plots + text output).
Cons: increased complexity for cross-process data sharing; needed anyway for Stage 4 comparison tool.

---

# II. Alignment of Current Codebase

## 1. Where should agent logic live?

### **Option A — `agent/` holds utility, demand, memory, foraging, bargaining adapters**

Pros: consolidates all micro-level behavior; aligns with Stage 3 (bargaining) and Stage 5 (memory).
Cons: utilities used by GT/Neo become transitively dependent on ABM concerns unless strict interfaces enforced.

### **Option B — `econ/` holds preferences/demand; `agent/` imports them**

Pros: matches Stage 3 and Stage 6 solvers; enables pure functional solvers without ABM baggage.
Cons: scattered agent code; harder to see “what an agent is.”

---

## 2. Where should spatial logic live?

### **Option A — `spatial/` owns grid, movement, trade-location utilities**

Pros: clean boundary for Stage 5 market-area detection.
Cons: ABM-only; unused in GT/Neo.

### **Option B — `agent_based/spatial/`**

Pros: explicitly scoped to ABM track.
Cons: mildly redundant top-level separation.

---

## 3. How to structure protocols?

### **Option A — Track-ownership model (already in roadmap)**

* GT owns matching + bargaining.
* ABM owns search.
  Pros: consistent with Stage 3; ABM can import GT bargaining; matches pedagogical story (“institutions travel with you”).
  Cons: cross-track imports require strict dependency direction.

### **Option B — `protocols/` as a central repo with track-specific adapters**

Pros: clean extensibility for user-submitted protocols.
Cons: contradicts current design intent; overshoots needs.

---

# III. Dependencies and Coupling

## 1. How to avoid circular imports?

### **Option A — Enforce a strict layering: core → (agent,econ) → (spatial,protocol) → tracks → launcher**

Pros: handles all stage documents cleanly.
Cons: requires refactor; but aligns with long-term structure.

### **Option B — Introduce interface modules (`interfaces.py`) for cross-track boundaries**

Pros: prevents GT’s solvers from importing ABM state; allows mocking.
Cons: more boilerplate.

---

## 2. How should shared config be handled?

### **Option A — Immutable simulation-level context object**

Pros: fits all three tracks; supports runtime precision switching (Decimal) without global state.
Cons: more parameters passed around.

### **Option B — Track-local configs**

Pros: simplifies track isolation.
Cons: Stage 4 comparison tool becomes harder.

---

# IV. Testing and Validation

## 1. How to ensure refactor safety?

### **Option A — Track-level test suites**

ABM: trade logs, spatial dynamics
GT: contract curve, equilibrium solver
Neo: tatonnement convergence
Pros: aligns with stages; isolates failures.
Cons: more code.

### **Option B — Scenario regression tests**

Pros: good for cross-track comparison consistency.
Cons: non-determinism in ABM must be tamed with seeds.

---

# V. Implementation Effort

## 1. What refactor path is viable given Stage 3–6?

### **Option A — Minimal surgical moves now, large reorg after Stage 3**

Pros: GT track is the next critical milestone; avoid blocking it.
Cons: work duplicated later.

### **Option B — Full reorg before Stage 3**

Pros: clean foundation.
Cons: halts progress; GT pseudocode is long and brittle to change.

### **Option C — Two-phase path**

Phase 1: clarify `econ` vs `agent` vs `spatial` vs `protocol`.
Phase 2: after Stage 3, reorganize tracks cleanly.
Pros: best compromise with roadmap.
Cons: still involves churn twice.

---

# VI. Documentation and Maintainability

## 1. How to document structure?

### **Option A — One architecture map aligned to stages**

Pros: explains what belongs to ABM vs GT vs Neo; ideal for contributors.
Cons: must be updated each stage.

### **Option B — Track-specific READMEs**

Pros: meets the needs of Stage 3–6 transitions.
Cons: loses global picture.

---

# VII. Theory Alignment

## 1. How faithful should code structure be to economic theory?

### **Option A — Mirror theory: preferences, demand, bargaining, equilibrium**

Pros: supports pedagogy; GT and Neo tracks plug in naturally.
Cons: ABM needs practical deviations (e.g., search, market detection).

### **Option B — Mirror simulation pipeline: agents → world → protocols → effects → simulation**

Pros: consistent with Stage 0 restructuring; good for ABM.
Cons: GT/Neo feel bolted on unless carefully mapped.

The roadmap implies **Option A for GT/Neo, B for ABM; unify with a shared core**.

---

# VIII. Risk and Rollback

## 1. How to reduce failure risk?

### **Option A — Track-level version tags**

Pros: revert ABM → GT → Neo independently.
Cons: complex git workflow.

### **Option B — Keep master stable; develop in staged branches (`stage3-gt`, `stage4-launcher`)**

Pros: maps onto roadmap.
Cons: merge overhead.

---

# IX. Organizational

## 1. How to define code ownership?

### **Option A — Track ownership**

ABM = spatial + search + emergent info
GT = matching + bargaining + Edgeworth
Neo = equilibrium + tatonnement
Pros: clear boundaries; consistent with roadmap.
Cons: shared primitives require coordination.

### **Option B — Functional ownership (economics vs simulation vs UI)**

Pros: centralizes solver knowledge.
Cons: mismatched with three-track pedagogy.

---

# X. Decision Criteria

## 1. What matters for choosing between the above?

### Required:

* Tracks must interoperate cleanly for Stage 4 comparisons.
* GT/Neo must use the same utility/demand primitives.
* ABM must remain the emergence-first backbone.
* Market info (Stage 5) must depend only on ABM effects, not GT/Neo code.
* Neo must remain purely functional solvers with no state mutation.

### Relaxable:

* Perfect separation between ABM and GT bargaining (GT can own bargaining fully).
* Location of utility functions (econ/ vs agent/).
* Whether protocols are centralized or track-local.

### Tradeoffs to accept:

* Short-term duplication of demand functions between GT and Neo until unified.
* Two-phase refactor (before/after Stage 3).
* GUI and engine process separation.

---