Let me open the two planning docs you referenced plus the broader vision doc, and scan existing econ/protocol modules to align the brainstorming with what's already in the codebase.

[5 tools called]

I'll quickly open `src/vmt_engine/econ/base.py` and `src/vmt_engine/econ/utility.py` to align proposed calculators with existing econ abstractions.

[2 tools called]

Here’s a comprehensive brainstorming document. Planning-only, no code edits yet [[memory:10554320]].

## Standard Neoclassical Theory Track and Game Theory Modules: Planning Brainstorm

### Purpose
- Build a cohesive neoclassical theory track that complements the ABM core by providing exact, textbook-aligned calculators and visualizations.
- Present Jehle & Reny material pedagogically in the GUI and design backend components to compute and render results.
- Integrate Game Theory modules (starting with bargaining) so users can see how protocols implemented in the ABM relate to standard theory (Kreps; Osborne & Rubinstein).

### Constraints and Architecture Touchpoints
- Use VMT’s separation-of-concerns: Protocol → Effect → State for ABM; calculators for theory are deterministic solvers and can live outside engine phases.
- Keep theory modules modular and side-by-side with ABM in the launcher (see `new_vision_nov_1_llm_input.md`).
- Reuse existing utility infrastructure in `src/vmt_engine/econ/utility.py`; add demand/duality/equilibrium solvers as new modules without changing ABM engine rules.

---

## A. Neoclassical Track: Jehle & Reny-Aligned Plan

### A1. What users see in the GUI (module cards + interactive panels)
- Consumer Theory (Ch. 1–3)
  - Utility Family Explorer: sliders for parameters; display indifference curves; switch families (CES, Cobb-Douglas, Leontief, Stone-Geary, Translog).
  - Budget + Demand: set prices/income; compute Marshallian demands; draw budget line; mark optimal bundle; show Hicksian vs Marshallian via a toggle.
  - Slutsky Decomposition: small price shock; animate substitution vs income effects; show Slutsky matrix entries for chosen point.
  - Welfare: Compensating/Equivalent Variation via expenditure function; annotate areas on the graph.
- Producer Theory (Ch. 4)
  - Isoquant/Isocost Explorer: choose production function (Cobb-Douglas, CES, Leontief); set target output and input prices; show cost-minimizing input bundle; Shephard’s lemma live.
  - Cost Curves: Short/long-run cost, MC, AC, AVC; toggle technology parameters and watch curves move.
  - Profit Maximization: given p, w, r—compute supply, input demands; show shutdown region.
- General Equilibrium (Ch. 5)
  - Edgeworth Box: two agents, two goods; show initial endowments, indifference curves, contract curve; compute competitive equilibria; annotate core vs competitive allocations.
  - Walrasian Equilibrium + Tatonnement: show excess demand; animate price adjustment path; show convergence metrics (norm of excess demand, Lyapunov-like decrease).
  - First/Second Welfare Theorems: overlay Pareto set; demonstrate decentralized vs lumpsum transfers to decentralize target allocations.
- Uncertainty (later): Expected utility and state pricing (optional, future).
- Market Failures (later): externalities/public goods (optional, future).

Presentation patterns
- Every module card has: “Concept,” “Controls,” “Show math,” “Compare to ABM” toggles.
- Visuals are “graph-first”: budget sets, indifference maps, isoquants, and equilibrium overlays, with sparse but precise labels.

### A2. Backend calculation framework (new modules)
Add a dedicated theory stack alongside existing `econ/utility.py`.

Option A (co-locate): extend `src/vmt_engine/econ/`:
- `demand.py`: Marshallian/Hicksian demands, indirect utility, expenditure function; Slutsky matrix.
- `production.py`: cost functions, Shephard’s lemma, conditional input demands; profit maximization.
- `equilibrium.py`: pure exchange GE (2×2 first), excess demand map, tatonnement/newton solvers; welfare objects (Pareto set/contract curve).
- `calibration.py`: parameter inference for families (e.g., CES elasticity; Stone-Geary subsistence from Engel shares).
- `viz_payloads.py`: pure data specs for curves/points/polygons.

Option B (clear separation): add `src/vmt_engine/neoclassical/` with the same module names; re-export or import utility families from `econ/utility.py`. This keeps “theory calculators” distinct from ABM engine code while leveraging shared utility classes.

Recommended: Option B for conceptual clarity, with explicit imports from `econ.utility` to avoid duplication.

Core solver APIs (illustrative)
```python
# Consumer
def marshallian_demand(u: Utility, prices: tuple[float,float], income: float) -> tuple[float,float]
def hicksian_demand(u: Utility, prices: tuple[float,float], Ubar: float) -> tuple[float,float]
def indirect_utility(u: Utility, prices: tuple[float,float], income: float) -> float
def expenditure(u: Utility, prices: tuple[float,float], Ubar: float) -> float
def slutsky_matrix(u: Utility, prices: tuple[float,float], income: float) -> list[list[float]]

# Producer
def cost_function(F, w: float, r: float, q: float) -> float
def conditional_factor_demands(F, w: float, r: float, q: float) -> tuple[float,float]
def profit_max_output(F, p: float, w: float, r: float) -> dict

# General Equilibrium (2×2, L agents)
def edgeworth_contract_curve(u1: Utility, u2: Utility, endow_total: tuple[float,float]) -> list[tuple[float,float]]
def walras_equilibrium(agents: list[dict], endow: list[tuple[float,float]]) -> dict
def tatonnement(agents, endow, p0: tuple[float,float], alpha: float) -> dict  # price path + metrics
```

Implementation notes
- Start with 2 goods and small L (2–N) for tractability and visualization parity with Edgeworth.
- Use closed forms where available (Cobb-Douglas, Stone-Geary) and fallback to numerical optimization otherwise.
- Excess demand solver:
  - Normalize prices (e.g., pB = 1, solve for pA) to avoid scaling indeterminacy.
  - Root-finding on aggregate excess demand in 2-good case; line-search damped tatonnement for pedagogy (even if not globally robust).
- Numerical stack:
  - Primary: numpy; optional: scipy.optimize for root finding; provide bisection/Brent fallback for 1D (2-good).
  - Autodiff is optional; analytic derivatives are fine for 2D cases.

### A3. Visualization payload contracts
Define small, renderer-agnostic specs so viewers can plug-and-play:
```python
@dataclass
class CurveSpec:
    x: list[float]
    y: list[float]
    label: str
    style: dict  # color, line, alpha

@dataclass
class PointSpec:
    x: float
    y: float
    label: str
    style: dict

@dataclass
class RegionSpec:
    polygon: list[tuple[float,float]]
    label: str
    style: dict
```
- Edgeworth Box: indifference CurveSpecs for both agents in the same coordinate system; contract curve; initial endowment point; Walrasian allocation point; offer curve pairs (optional).
- Demand panel: budget line CurveSpec, optimal PointSpec, indifference CurveSpecs, Hicksian vs Marshallian toggles produce multiple overlays.
- Tatonnement: price path as a time series; optionally, excess demand curve with moving dot.

### A4. Mapping Jehle & Reny chapters to concrete features
- Ch. 1–3 Consumer Theory
  - Families: CES, Stone-Geary, Translog already exist in `econ/utility.py`. Add demand/duality functions and Slutsky.
  - GUI: “Consumer Theory Lab” tab with three subpanels: Utility Explorer, Budget+Demand, Slutsky.
- Ch. 4 Producer Theory
  - Start with Cobb-Douglas and CES production; provide isoquant/isocost visuals and dual cost function calculators.
  - GUI: “Producer Theory Lab” with Cost Minimization and Profit Maximization subpanels.
- Ch. 5 General Equilibrium + Welfare
  - Edgeworth Box + Walrasian solver + tatonnement plot; welfare overlays for Pareto set; First/Second Welfare Theorems as overlays/annotations and “transfer tool”.
  - GUI: “General Equilibrium Lab” with Exchange (Edgeworth) and “Price Adjustment” tabs.

### A5. “Compare to ABM” bridges
- For a given 2-agent `Edgeworth` configuration, offer “simulate” to spawn a matching ABM scenario with identical utilities/endowments. Show:
  - Theoretical CE allocation vs realized ABM trade outcomes (averages and dispersion).
  - Tatonnement price vs distribution of bilateral exchange ratios in ABM.
  - Display deviations with reasons rooted in institutional details (search, matching, bargaining; 7-phase tick discipline).
- For specific bargaining protocols (e.g., `take_it_or_leave_it` in `src/vmt_engine/protocols/bargaining/take_it_or_leave_it.py`), show:
  - Theoretical surplus split benchmarks (e.g., Nash bargaining solution) vs ABM realized splits.

### A6. Testing and validation
- Theory unit tests: closed-form validations for Cobb-Douglas/Stone-Geary demands; Slutsky symmetry; duality checks (expenditure vs indirect utility consistency); GE equilibria in canonical Edgeworth cases.
- Golden scenarios: JSON fixtures for “known” equilibria and curve shapes; numerical tolerances documented.
- Cross-validated integration: ABM vs theory comparison tests (aggregate prices vs CE; allocation distances).

---

## B. Game Theory Modules (Bargaining-first, aligned to Kreps; Osborne & Rubinstein)

### B1. Pedagogical stance
- Start with 2-agent exchange in Edgeworth Box to build intuition.
- Present cooperative and noncooperative bargaining side-by-side:
  - Cooperative benchmarks: Nash Bargaining Solution (NBS), Kalai-Smorodinsky.
  - Noncooperative: Rubinstein alternating-offers (with δA, δB), ultimatum/TIOLI.
- Explicitly separate equilibrium concepts from ABM protocols while bridging them in controlled demos.

### B2. GUI modules
- Bargaining Playground
  - Select utility families/parameters and initial endowment.
  - Choose disagreement point (status quo utilities).
  - Compute and plot:
    - NBS point (maximize product of utility gains).
    - Kalai-Smorodinsky point.
    - Rubinstein SPE outcome (map discount factors to allocation/path).
    - TIOLI outcomes under proposer power.
  - Animate trade path under different “procedures”:
    - Cooperative path to NBS
    - Alternating-offers trajectory
    - Split-the-difference iterative path
- Best-Response and Normal-Form (later): 2×2 games, mixed NE; optional replicator dynamics view.

### B3. Backend solvers
- `game_theory/bargaining.py`
  - `nash_bargaining(uA, uB, feasible_set, d_point) -> allocation`
  - `kalai_smorodinsky(uA, uB, feasible_set, d_point) -> allocation`
  - `rubinstein_outcome(uA, uB, d_point, deltaA, deltaB) -> allocation`
  - Helpers to generate feasible sets in utility space (mapped from Edgeworth feasible allocations).
- Edgeworth integration
  - Use the same Edgeworth Box calculator to produce feasible allocations; push through bargaining solvers to establish correspondence between space-of-goods and space-of-utilities.

### B4. Bridges to ABM protocols
- Direct mappings
  - `take_it_or_leave_it` protocol: compare with TIOLI theoretical outcomes under matching utility and outside options.
  - `split_difference` protocol: compare with equal surplus division and contrast to NBS.
  - Future: alternating-offers protocol in ABM to compare to Rubinstein.
- Show protocol dependence (institutional features)
  - Control “bargaining power” parameters in ABM and visualize shift in surplus split; contrast with NBS invariance axioms.

---

## C. Launcher and UX Integration

### C1. Launcher structure
- Top-level menu (already planned): Agent-Based, Game Theory, Standard Neoclassical.
- Game Theory: “Bargaining Protocols” opens the Bargaining Playground (Edgeworth-integrated visuals).
- Neoclassical: “Consumer Theory,” “Producer Theory,” “General Equilibrium” tiles; each opens subpanels as above.

### C2. Shared UX patterns
- Uniform sidebar for parameters; center canvas for plot; bottom bar for status/math toggles.
- “Show math” expands derivations and formulas matched to the selected family and current parameter values.
- “Compare to ABM” is a persistent action that generates a corresponding ABM scenario and opens the ABM viewer.

---

## D. Data and Schema

### D1. Scenario and config
- Extend YAML schema with `simulation_type` and type-specific sections:
  - `simulation_type: neoclassical | game_theory | agent_based`
  - `theory:` blocks for utilities/endowments/price/income and panel preferences.
  - `game_theory:` bargaining-specific inputs (δ, disagreement point, protocol).
- Keep current ABM scenarios unchanged; add `scenarios/game_theory/` and `scenarios/neoclassical/` folders.

### D2. Output artifacts
- Visualization payloads (CurveSpec/PointSpec/RegionSpec) are the boundary objects between solvers and GUI.
- Optional CSV/JSON export of solved objects (demands, equilibria, welfare metrics).

---

## E. Phased Implementation (production-viable chunks)

- Milestone 1: Theory foundations
  - Add `neoclassical/` package with demand/duality for 2 goods and Cobb-Douglas + Stone-Geary (closed forms).
  - Minimal “Consumer Theory Lab” GUI: Budget+Demand panel with overlays.
- Milestone 2: Edgeworth + Bargaining
  - Edgeworth Box backend + viewer; NBS and TIOLI calculators; Bargaining Playground GUI.
  - “Compare to ABM” mapping for 2 agents (spawn ABM scenario and overlay results).
- Milestone 3: General Equilibrium + Tatonnement
  - 2×2 exchange GE solver; tatonnement path visualizer; CE overlay on Edgeworth.
- Milestone 4: Producer Theory Basics
  - Cobb-Douglas production isoquant/isocost + cost function + Shephard’s lemma; Cost Minimization panel.
- Milestone 5: Calibration and Slutsky
  - Add expenditure/indirect utility; CE/CV; Slutsky decomposition visual; parameter calibration helpers.

---

## F. Validation and Pedagogy

- Correctness
  - Unit tests for demands (closed-form vs numerical), duality identities, GE equilibria in canonical cases.
  - Slutsky symmetry/negativity and integrability checks where applicable.
- Pedagogical clarity
  - Reduce visual clutter; progressive disclosure; canonical scenarios included; “explain deviations” text where ABM differs from theory.
- ABM coherence
  - Preserve the 7-phase tick discipline and Protocol → Effect → State invariants in ABM; theory calculators never mutate ABM state.

---

## G. Open Decisions

- Module placement: `econ/` vs `neoclassical/` (recommend the latter for clarity).
- Numerical stack: require `scipy` or provide pure-numpy fallbacks with 2-good constraints.
- GUI renderer: continue PyQt6 for panels; use matplotlib or pyqtgraph; keep pygame for ABM only.
- Depth of cooperative GT: include Kalai-Smorodinsky now or defer; prioritize NBS + Rubinstein + TIOLI for ABM bridging.

---

## H. Immediate Next Steps (design work, no code)
- Define the minimal Theory API for Consumer Theory Lab (Marshallian/Hicksian for two families).
- Specify Visualization payload contracts and one Edgeworth Box panel spec.
- Draft 3–5 canonical scenarios for Consumer Theory (budget changes, endowment swaps) and Edgeworth (complementary endowments).
- Outline “Compare to ABM” mapping function for 2-agent scenarios.

---

- Built this as a planning document only, consistent with your preference to design first without code edits [[memory:10554320]].

- If you’d like, I can now draft the minimal API for `neoclassical/demand.py` and a corresponding GUI wireframe for the Consumer Theory Lab for your review.