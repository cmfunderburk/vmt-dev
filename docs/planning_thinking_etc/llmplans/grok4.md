# Brainstorming Plan for Implementing Standard Neoclassical Theory Track in VMT

**Date**: November 2, 2025  
**Status**: Early-Stage Brainstorming - Conceptual Planning  
**Context**: This document builds on the expanded vision in `new_vision_nov_1_llm_input.md` (modular GUI for Agent-Based, Game Theory, and Neoclassical tracks) and the foundational ideas in `initial_planning (ORIGINAL).md` (visualization-first approach starting from preferences and choice functions in a spatial context). The focus is on the Standard Neoclassical track, integrating it as a modular component while ensuring pedagogical coherence. Brainstorming addresses GUI presentation of Jehle & Reny chapters, backend frameworks, visualizations, and Game Theory module pedagogy (with bargaining as a starting point for crossover to agent-based simulations).  

**Key Assumptions**: 
- Build on existing VMT architecture (protocol-effect-state pattern, spatial grid core).
- Prioritize extensibility without disrupting Agent-Based track.
- Align with pedagogical inversion: Show imposed equilibria first, then contrast with emergent phenomena.
- No code changes yet; focus on planning resolutions to identified problems.

---

## 1. Overall Implementation Strategy for Neoclassical Track

### Problem: Integrating Neoclassical Models Without Fragmenting the Platform
Neoclassical models (e.g., Walrasian equilibrium) differ fundamentally from agent-based bilateral trading—no spatial search, no protocols, just price-taking and centralized clearing. Resolution: Treat this track as a distinct simulation type in the modular GUI (as proposed in `new_vision_nov_1_llm_input.md`), with shared core elements like agent preferences and endowments from the spatial foundation in `initial_planning (ORIGINAL).md`.

- **Modular Entry Point**: Extend `NeoclassicalMenu` with sub-modules mapped to textbook chapters (e.g., "Consumer Theory", "General Equilibrium"). Use QStackedWidget for navigation, sharing YAML config schemas for agents/utilities where possible.
- **Backend Separation**: Create a new `src/vmt_engine/neoclassical/` directory for equilibrium solvers, distinct from `protocols/` and `systems/`. Reuse `core/` primitives (e.g., Agent, Utility functions) for consistency.
- **Crossover Potential**: Include "Compare to Agent-Based" buttons that launch parallel simulations with identical parameters, highlighting differences (e.g., imposed vs. emergent prices).

### Risk Considerations
- Overlap with Game Theory track (e.g., Edgeworth Box as a bridge). Resolution: Use shared visualization tools (e.g., contract curves) but keep menus separate.
- Scalability for complex models. Resolution: Start with 2-good, 2-agent cases, scale via configurable parameters.

---

## 2. Jehle & Reny Chapter Presentation: GUI and Backend Planning

Jehle & Reny's *Advanced Microeconomic Theory* (3rd ed.) structures content progressively: preferences/choice (Ch.1), consumer theory (Ch.2-3), production (Ch.4), equilibrium (Ch.5), welfare (Ch.6), and extensions (Ch.7-9). Problem: Translate this abstract, mathematical presentation into an interactive GUI while preparing backend for calculations/visualizations. Resolution: Map chapters to hierarchical GUI modules with interactive demos, using a visualization-first approach to build intuition (per `initial_planning (ORIGINAL).md`).

### 2.1 GUI Presentation Ideas
- **Hierarchical Structure**: In `NeoclassicalMenu`, use chapter-based buttons (e.g., "Ch.1: Preferences and Choice"). Each opens a sub-window with:
  - **Theory Panel**: Scrollable text summaries with key equations (e.g., WARP for Ch.1), hyperlinked to full proofs.
  - **Interactive Demo**: Parameter sliders (e.g., adjust alpha in Cobb-Douglas utility) with real-time updates.
  - **Assessment Tools**: Quiz widgets (e.g., "Predict the demand curve shift") with feedback, tying to `initial_planning (ORIGINAL).md`'s educational scenarios.
  - **Progression Lock**: Optional mode where users must complete Ch.1 demo before unlocking Ch.2, enforcing pedagogical sequence.

- **Pedagogical Flow**: Start with simple 2-good cases (visualized in preference space), progress to multi-good equilibria. Include "Spatial View" toggle to show concepts in a grid (e.g., agents optimizing positions as metaphor for choice sets), bridging to agent-based track.

- **User Experience Resolutions**:
  - Problem: Overwhelming math. Resolution: Layered explanations—basic intuition first, toggle for proofs/derivations.
  - Problem: Static vs. Dynamic. Resolution: Animate processes (e.g., tatonnement price adjustment as a time-series plot).
  - Integration with Vision: Invert sequence by including "Emergence Challenge" buttons (e.g., "See if agents can reach this equilibrium without auctioneer").

### 2.2 Backend Framework for Calculations
- **Core Components**: Build on existing `econ/` (utilities) and `core/` (agents). Add `neoclassical/solvers.py` for algorithms like tatonnement or Scarf's method for equilibrium computation.
  - **Data Structures**: Use NumPy for matrices (e.g., excess demand functions). Extend Agent class with price-taking behavior (e.g., `compute_demand(prices, income)`).
  - **Calculation Pipeline**: Input (YAML config: endowments, utilities) → Compute (e.g., solve for Walrasian prices) → Output (equilibrium allocations, stats).

- **Resolutions to Backend Problems**:
  - Problem: Numerical Stability (e.g., non-convergence in tatonnement). Resolution: Implement safeguards (e.g., max iterations, fallback to analytical solutions for simple cases) and error visualization (plot excess demand at failure).
  - Problem: Scalability (multi-agent, multi-good). Resolution: Use SciPy optimizers; start with low-dimensional cases, add parallel computation via multiprocessing for large N.
  - Problem: Validation. Resolution: Unit tests comparing outputs to textbook examples (e.g., Jehle Ch.5 exercises); integrate with existing telemetry for logging convergence paths.

### 2.3 Preparing Visualizations
- **Types**: Static plots (indifference curves, budget sets via Matplotlib), dynamic animations (price convergence via PyQtGraph), and hybrid (embed in PyQt6 windows).
- **Backend Prep**: Create `neoclassical/visualizers.py` with functions like `plot_excess_demand(prices, demands)`. Reuse Pygame for any spatial metaphors.
- **Resolutions**:
  - Problem: Visualization Overload. Resolution: Modular widgets—e.g., tabbed views for "Graph", "Table", "Animation".
  - Problem: Accuracy. Resolution: Ensure plots match calculations (e.g., auto-scale axes based on equilibrium values).
  - Crossover: Export visualization data to agent-based scenarios for comparison.

---

## 3. Pedagogical Presentation of Game Theory Modules

Standard texts like Kreps' *Microeconomic Foundations II* start with strategic form games and Nash equilibrium, while Osborne & Rubinstein's *A Course in Game Theory* begins with extensive form and bargaining. Problem: VMT's agent-based focus suggests starting with bargaining for protocol crossover, but this inverts standard pedagogy. Resolution: Design a flexible module sequence that starts with bargaining (for relevance) but includes pathways to standard progression.

### 3.1 Starting with Bargaining: Resolutions and Crossover
- **Rationale for Start Point**: Bargaining directly ties to existing protocols (e.g., SplitDifference in `protocols/bargaining.py`), allowing users to explore "indepth understanding" via Edgeworth Box demos. Aligns with `new_vision_nov_1_llm_input.md`'s Game Theory path.
- **GUI Presentation**: In `GameTheoryMenu`, prioritize "Bargaining Protocols" button leading to a window with:
  - Protocol selector (e.g., Nash solution, Rubinstein model).
  - 2-agent Edgeworth Box viewer (indifference curves, contract curve).
  - "Link to Simulation" button: Auto-generate agent-based scenario with same parameters for emergence comparison.

- **Pedagogical Resolutions**:
  - Problem: Deviation from Standard Texts. Resolution: Include "Standard Path" mode following Kreps (Ch.11: Extensive Form) or Osborne (Ch.1: Nash Equilibrium), with bargaining as Module 3-4. Use branching navigation: "Quick Start: Bargaining" vs. "Textbook Sequence".
  - Problem: Abstract vs. Concrete. Resolution: Anchor in spatial visuals (e.g., agents "negotiating" on grid as metaphor), per `initial_planning (ORIGINAL).md`.
  - Crossover to Protocols: Embed explanations linking to VMT's implemented protocols (e.g., "This Nash solution approximates SplitDifference outcomes in large N simulations").

### 3.2 Overall Game Theory Progression
- **Module Sequence Brainstorm** (Hybrid Approach):
  1. **Bargaining Foundations** (Crossover Entry): Nash solution, alternating offers (Osborne Ch.16, Kreps Ch.15).
  2. **Strategic Form Games** (Standard Start): Prisoner's Dilemma, Nash equilibrium (Kreps Ch.10, Osborne Ch.2).
  3. **Extensive Form** (Progression): Backward induction, subgame perfection (Kreps Ch.11-12, Osborne Ch.5).
  4. **Applications**: Mechanism design, auctions (Kreps Ch.18, Osborne Ch.9).
- **GUI/Backend Ideas**: Similar to Neoclassical—interactive demos (e.g., payoff matrix editor), backend solvers (e.g., Nash equilibrium finder using SciPy), visualizations (payoff trees, best-response plots).
- **Resolutions to Related Problems**:
  - Problem: Depth vs. Breadth. Resolution: Core modules mandatory, extensions optional with prerequisites.
  - Problem: Integration with Neoclassical. Resolution: Shared modules (e.g., welfare theorems in bargaining link to Jehle Ch.6).

---

## 4. Related Problems and Brainstormed Resolutions

- **Problem: Shared Config and Data Flow**: Neoclassical/Game Theory configs may differ from agent-based YAML. Resolution: Extend `scenarios/schema.py` with type-specific sections; use protocol_factory for hybrid scenarios.
- **Problem: Performance for Visualizations**: Complex plots could lag. Resolution: Offload to background threads; use efficient libs (PyQtGraph for real-time).
- **Problem: Educational Assessment**: How to measure learning. Resolution: Integrate simple quizzes with telemetry logging, exporting to CSV for analysis.
- **Problem: Extensibility for Future Tracks**: E.g., adding production (Jehle Ch.4). Resolution: Design backend as plugin-based (e.g., register new solvers in a registry, similar to protocols).
- **Problem: Consistency with Vision**: Ensure neoclassical track doesn't overshadow emergence focus. Resolution: Mandatory "Comparison Mode" in demos, showing agent-based deviations.

---

## Conclusion and Next Steps

This brainstorm provides a structured plan to implement the Neoclassical track, resolving GUI/backend challenges while aligning with the visions in the referenced files. It emphasizes pedagogical flexibility, starting Game Theory with bargaining for VMT relevance, and uses modular design for extensibility.

**Next Actions**:
- Refine chapter mappings with specific Jehle examples.
- Prototype wireframes for GUI modules (e.g., via Figma).
- Discuss with potential users (e.g., educators) for feedback.
- Once approved, move to detailed design docs before implementation.

**Related Documents**: `new_vision_nov_1_llm_input.md`, `initial_planning (ORIGINAL).md`, Jehle & Reny (Ch.1-6), Kreps Vol.II (Ch.10-15), Osborne & Rubinstein (Ch.1-16).