# VMT: Visualizing Microeconomic Theory
## Vision, Architecture, and Research Agenda

**Document Type:** Strategic Vision and Research Framework  
**Purpose:** High-level overview of project goals, current state, and future directions  
**Date:** 2025-10-27

---

## I. The Fundamental Question

### Standard Economics Pedagogy: Equilibrium First

Traditional microeconomics education follows a well-worn path:
1. **Consumers** → utility functions, preferences, choice theory
2. **Firms** → production functions, cost curves, profit maximization
3. **Markets** → **immediate jump to equilibrium analysis**
4. **Price-taking** → assumed virtually from the start

This approach treats markets and prices as **given primitives** rather than **phenomena to be explained**. Students learn to solve for equilibrium without understanding when, how, or whether markets actually form those equilibria.

### VMT's Alternative: Markets as Emergent Phenomena

VMT inverts this pedagogical sequence by asking:

> **Under what institutional conditions do market-like phenomena actually emerge from micro-level interactions?**

Rather than assuming equilibrium prices exist and agents take them as given, VMT investigates:
- What search protocols, matching algorithms, and bargaining mechanisms lead to price convergence?
- When do bilateral negotiations yield uniform exchange ratios?
- Under what conditions does decentralized exchange approximate Walrasian equilibrium?
- How do spatial patterns, information frictions, and bargaining power affect market formation?

---

## II. Core Design Philosophy

### Markets Don't Just Happen

In VMT's spatial agent-based framework:
- **Markets emerge** (or fail to emerge) from agent decisions
- **Prices form** (or remain dispersed) based on institutional mechanisms
- **Efficiency arises** (or doesn't) from protocol interactions
- **Equilibria converge** (or cycles persist) depending on adjustment processes

Nothing is assumed. Everything is demonstrated.

### Institutional Comparative Analysis

VMT enables systematic comparison of exchange mechanisms:

**Decentralized Bilateral Exchange:**
- Agents search for partners spatially
- Pairs form through matching protocols
- Prices negotiated bilaterally, pair-by-pair
- Exchange ratios may vary across pairs

**Centralized Market Mechanisms:**
- Agents submit orders to central mechanism
- Prices set by market clearing
- Uniform pricing enforced institutionally
- Equilibrium computed algorithmically

**Key Research Question:** When do these produce similar outcomes? When do they diverge? What explains the differences?

### Spatial and Temporal Dynamics

VMT's spatial foundation matters:
- **Search is costly** → information frictions are endogenous
- **Matching is local** → network effects and market thickness emerge
- **Movement creates patterns** → spatial clustering, market segmentation
- **Time matters** → convergence dynamics observable tick-by-tick

Markets don't exist in abstract Euclidean space. They exist in **physical/social space** where distance, visibility, and search costs shape outcomes.

---

## III. Economic Foundations

### The Basic Exchange Economy

**Agents** possess:
- **Utility functions** over goods (A, B, and money M)
- **Initial endowments** (inventories)
- **Preferences** (various functional forms: CES, linear, quadratic, etc.)

**Resources** regenerate on a spatial grid:
- Agents **forage** to acquire goods
- Foraging serves as rudimentary "production"
- Provides resource flow without production function complexity

**Exchange** occurs through multiple mechanisms:
- **Barter** (A ↔ B)
- **Monetary** (A ↔ M, B ↔ M)
- **Mixed** regimes allow all trade types

**No prices assumed.** Only agents' marginal rates of substitution (MRS) from utility functions.

### From Utility to Prices: The Emergence Question

In standard theory:
```
Utility → Demand → Market Clearing → Equilibrium Price
                    ↑
                    (assumed to exist and work)
```

In VMT:
```
Utility → MRS → Reservation Prices → Search → Matching → Bargaining → Trade
                                                                        ↓
                                                          Observed Exchange Ratios
                                                                        ↓
                                              Do these converge? To what? Why?
```

The middle steps—search, matching, bargaining—are **explicit institutional mechanisms** that may or may not produce price convergence.

---

## IV. Protocol Categories: Institutional Building Blocks

### 1. Search Protocols

**Economic Question:** How do agents discover trading opportunities?

**Mechanisms:**
- **Rational Search** → Distance-discounted utility-based target selection
- **Random Walk** → Zero information, pure exploration
- **Memory-Based** → Learning from past experience (explore vs exploit)
- **Myopic** → Limited vision radius (information constraints)

**Key Insights:**
- Information frictions affect match quality
- Search costs limit market thickness
- Spatial patterns emerge from search strategies

**Pedagogical Value:** Demonstrates value of information, search costs, and market thickness effects.

---

### 2. Matching Protocols

**Economic Question:** How do trading pairs form?

**Mechanisms:**
- **Three-Pass Matching** → Mutual consent with greedy fallback (legacy)
- **Random Matching** → Null hypothesis (no preference consideration)
- **Greedy Surplus** → Welfare maximization (planner perspective)
- **Stable Matching** → No blocking pairs (Gale-Shapley)

**Key Insights:**
- Preference-based vs random allocation
- Efficiency vs fairness tradeoffs
- Stability vs welfare maximization
- Strategy-proofness and incentive compatibility

**Pedagogical Value:** Illustrates matching theory fundamentals, efficiency-fairness tensions, and market design principles.

---

### 3. Bargaining Protocols

**Economic Question:** How are trade terms (prices, quantities) negotiated?

**Mechanisms:**
- **Compensating Blocks** → Feasibility-constrained bilateral negotiation (legacy)
- **Split-the-Difference** → Equal surplus division (fairness benchmark)
- **Take-It-Or-Leave-It** → Monopolistic offer (extreme bargaining power)
- **Nash Bargaining** → Axiomatic cooperative solution
- **Rubinstein Alternating** → Dynamic game with discounting

**Key Insights:**
- Bargaining power shapes surplus division
- Time preferences affect outcomes
- Cooperation vs competition in bilateral exchange
- Multiple equilibrium concepts (Nash, subgame perfect, etc.)

**Pedagogical Value:** Shows how institutional rules affect surplus distribution, demonstrates game theory applications, contrasts cooperative vs noncooperative approaches.

---

### 4. Market Mechanisms (Centralized)

**Economic Question:** How do centralized markets form prices?

**Mechanisms:**
- **Walrasian Auctioneer** → Tatonnement price adjustment to equilibrium
- **Posted-Price Market** → Sellers set prices, buyers choose quantities
- **Continuous Double Auction** → Order book matching (experimental standard)

**Key Insights:**
- Price-taking emerges from institutional design, not assumption
- Uniform pricing enforced by mechanism
- Convergence properties vary by mechanism
- Efficiency depends on institutional details

**Pedagogical Value:** **Critical comparison—** When do bilateral negotiations produce same outcomes as centralized mechanisms? This is the core research question.

---

## V. Current Implementation State

### What Exists (Production-Ready)

**1. Spatial Agent-Based Engine**
- Deterministic simulation with reproducible random seeding
- 7-phase tick cycle (perception → decision → movement → trade → forage → regeneration → housekeeping)
- Comprehensive telemetry (SQLite logging)

**2. Economic Foundations**
- 5 utility function types (CES, linear, quadratic, Stone-Geary, translog)
- Money system with quasilinear utility
- Three exchange regimes (barter, money-only, mixed)
- Foraging as resource generation

**3. Protocol Architecture**
- Modular protocol system with abstract base classes
- Effect-based state mutations (declarative, auditable)
- WorldView pattern (immutable context for protocols)
- Protocol registry and injection system

**4. Legacy Protocols (Implemented)**
- **LegacySearchProtocol** → Distance-discounted utility-based search
- **LegacyMatchingProtocol** → Three-pass pairing (mutual consent + greedy fallback)
- **LegacyBargainingProtocol** → Compensating block negotiation

These implement **decentralized bilateral exchange** with spot negotiation.

### What This Enables

**Current Capabilities:**
✅ Agents forage and trade in spatial environment  
✅ Bilateral negotiations produce pair-specific prices  
✅ Can observe price dispersion across pairs  
✅ Spatial patterns emerge from movement and trading  
✅ Full determinism and reproducibility  
✅ Comprehensive data collection for analysis  

**Current Limitations:**
⚠️ Only one set of search/matching/bargaining rules (legacy protocols)  
⚠️ No institutional comparison possible yet  
⚠️ No centralized market mechanisms  
⚠️ Cannot compare bilateral vs centralized outcomes  
⚠️ Limited ability to explore emergence conditions  

---

## VI. Research Agenda: Protocol Library Development

### Phase 1: Baseline Protocols (Quick Wins)

**Goal:** Establish simple baselines for comparison

**Protocols:**
1. Random Walk Search → Zero-information baseline
2. Random Matching → Null hypothesis for matching
3. Split-the-Difference Bargaining → Equal surplus benchmark

**Research Value:**
- Quantify information value (rational vs random search)
- Demonstrate matching theory basics (preference-based vs random)
- Establish fairness baseline (equal split vs power-based)

**Status:** Detailed implementation plans ready

---

### Phase 2: Pedagogical Protocols

**Goal:** Demonstrate key economic concepts

**Protocols:**
1. Greedy Surplus Matching → Efficiency vs fairness
2. Myopic Search → Information frictions
3. Take-It-Or-Leave-It → Bargaining power

**Research Value:**
- Welfare vs equity tradeoffs
- Search costs and market thickness
- Power asymmetries in bilateral exchange

**Pedagogical Applications:**
- Teaching matching theory and stability
- Information economics demonstrations
- Bargaining theory applications

---

### Phase 3: Centralized Markets ⭐ **KEY MILESTONE**

**Goal:** Enable comparison of bilateral vs centralized exchange

**Protocols:**
1. **Walrasian Auctioneer** → Competitive equilibrium benchmark
2. **Posted-Price Market** → Price rigidity and search
3. **Continuous Double Auction** → Market microstructure

**Critical Research Questions:**
- When do bilateral negotiations converge to Walrasian prices?
- Under what conditions does price-taking approximate spot negotiation?
- How do spatial frictions affect convergence?
- What role does market thickness play?

**This answers the fundamental question:** Under what conditions do markets emerge to approximate equilibrium theory?

---

### Phase 4: Advanced Mechanisms

**Goal:** Dynamic processes and learning

**Protocols:**
1. Memory-Based Search → Learning and adaptation
2. Stable Matching (Gale-Shapley) → Stability and incentives
3. Nash Bargaining → Axiomatic solutions

**Research Value:**
- Bounded rationality and learning dynamics
- Matching market design
- Cooperative game theory

---

### Phase 5: Comprehensive Coverage

**Goal:** Full institutional variety

**Protocols:**
1. Rubinstein Alternating Offers → Dynamic bargaining
2. Various auction mechanisms
3. Network formation
4. Additional market designs

**Research Applications:**
- Publication-quality comparative studies
- Policy analysis (market design)
- Teaching advanced topics

---

## VII. Key Research Themes

### Theme 1: Price Convergence Conditions

**Central Question:** When do exchange ratios converge to uniform "prices"?

**Variables to Explore:**
- Search protocol (information availability)
- Matching algorithm (how pairs form)
- Bargaining mechanism (how prices negotiate)
- Market thickness (number of agents, spatial density)
- Information frictions (vision radius, memory)

**Expected Findings:**
- Thick markets with good information → price convergence
- Thin markets with limited information → price dispersion
- Bargaining power asymmetries → persistent price variation
- Some mechanisms never converge (posted prices with search frictions)

---

### Theme 2: Bilateral vs Centralized Comparison

**Central Question:** When does decentralized exchange approximate centralized equilibrium?

**Comparison Framework:**
```
Decentralized (Legacy):
  Search → Matching → Bilateral Bargaining → Heterogeneous Prices

Centralized (Walrasian):
  Order Submission → Market Clearing → Uniform Prices

Metrics:
  - Price dispersion (variance of exchange ratios)
  - Allocative efficiency (total surplus)
  - Convergence speed (ticks to stable prices)
  - Spatial patterns (clustering, segmentation)
```

**Policy Implications:**
- When is market organization beneficial?
- What frictions justify institutional intervention?
- Design principles for market mechanisms

---

### Theme 3: Institutional Details Matter

**Central Question:** How do specific protocol features affect outcomes?

**Examples:**
- Vision radius in search → information frictions
- Mutual consent in matching → stability properties
- Bargaining power parameters → surplus distribution
- Price adjustment speed → convergence dynamics

**Key Insight:** Small institutional differences can produce large outcome differences. The "invisible hand" depends on visible institutions.

---

### Theme 4: Spatial and Temporal Dynamics

**Central Question:** How do space and time shape market formation?

**Spatial Effects:**
- Market segmentation (different prices in different regions)
- Clustering (agents concentrate near resources)
- Network effects (thick vs thin market areas)

**Temporal Effects:**
- Convergence dynamics (path to equilibrium)
- Oscillations vs monotonic convergence
- Path dependence (history matters)

**Teaching Value:** Markets exist in space-time, not textbook abstractions.

---

## VIII. Pedagogical Applications

### Rethinking Intermediate Micro

**Traditional Sequence:**
1. Consumer theory (utility maximization)
2. Producer theory (profit maximization)
3. **Jump to equilibrium** (prices assumed)
4. Comparative statics (equilibrium shifts)

**VMT-Enhanced Sequence:**
1. Consumer theory (utility maximization)
2. **Foraging** (resource acquisition without production complexity)
3. **Bilateral exchange** (search, matching, bargaining)
4. **Observe emergent prices** (do they converge? why or why not?)
5. **Introduce centralized mechanisms** (auctioneers, order books)
6. **Compare outcomes** (when do they agree? when diverge?)
7. **Equilibrium theory** (as special case, not starting point)

### Key Pedagogical Gains

**1. Markets as Constructions**
- Students see markets built from institutional rules
- "Price-taking" emerges (or doesn't) from mechanisms
- Institutions matter visibly

**2. Comparative Institutional Analysis**
- Different protocols produce different outcomes
- No single "right" way to organize exchange
- Design choices have consequences

**3. Dynamics and Convergence**
- Equilibrium as process, not state
- Convergence speed varies by institution
- Some systems never converge

**4. Spatial Reasoning**
- Information frictions are real (not assumed)
- Search costs affect outcomes
- Geography matters for market thickness

**5. Computational Literacy**
- See theory in action
- Experiment with parameters
- Build intuition through simulation

---

## IX. Research Extensions (Post-Exchange)

### Production Economies

**After exchange mechanisms work well:**
- Traditional production functions (capital, labor, technology)
- Factor markets (labor, capital)
- Firm decision-making (production and pricing)
- Input-output linkages

**Research Questions:**
- How do production possibilities affect exchange patterns?
- Factor price formation
- Industry organization emergence

---

### Public Goods and Externalities

**Extensions:**
- Public good provision mechanisms
- Externality internalization
- Collective action problems

**Research Questions:**
- When do decentralized solutions fail?
- Institutional responses to market failures
- Voluntary vs coercive mechanisms

---

### Asymmetric Information

**Extensions:**
- Hidden characteristics (adverse selection)
- Hidden actions (moral hazard)
- Signaling and screening

**Research Questions:**
- How do information asymmetries affect exchange?
- Emergence of information-revealing mechanisms
- Lemons markets and market breakdown

---

### Network Formation

**Extensions:**
- Endogenous network links
- Trading partnerships
- Intermediation

**Research Questions:**
- Network topology and market efficiency
- Intermediary roles
- Decentralization vs hierarchy

---

## X. Technical Architecture (Conceptual)

### The Protocol Abstraction

**Core Idea:** Separate "what happens" (effects) from "who decides" (protocols)

**Pseudocode:**
```
Protocol Interface:
  - input: WorldView (immutable state snapshot)
  - output: list[Effect] (declarative intents)

Effect Types:
  - SetTarget (search decision)
  - Pair/Unpair (matching decision)
  - Trade (exchange decision)
  - Move (movement decision)
  - Order (market submission)
  - MarketClear (price formation)
  
Simulation Loop:
  foreach phase in [search, matching, trade, ...]:
    protocol = get_protocol_for_phase()
    effects = protocol.execute(worldview)
    apply_effects_to_state(effects)
    log_telemetry(effects)
```

**Key Benefits:**
- Protocols are **interchangeable** (swap algorithms without changing engine)
- Effects are **auditable** (complete record of all decisions)
- System is **deterministic** (replayable from effects log)
- Comparison is **systematic** (same simulation, different protocols)

---

### The WorldView Pattern

**Problem:** How do protocols access state without coupling to implementation?

**Solution:** Immutable data snapshots

**Pseudocode:**
```
WorldView:
  - agent_state (position, inventory, utility, etc.)
  - visible_agents (search radius)
  - visible_resources (forage opportunities)
  - market_state (prices, orders if centralized)
  - parameters (vision radius, trade cooldowns, etc.)
  - rng_stream (deterministic randomness)
```

**Benefits:**
- Protocols can't mutate state directly
- Clear separation of concerns
- Easy to reason about protocol behavior
- Testable in isolation

---

### Telemetry and Analysis

**Comprehensive Logging:**
- Agent states (every tick)
- Trade events (prices, quantities, pair types)
- Spatial positions (movement patterns)
- Protocol decisions (preferences, matches)
- Market events (orders, clears)

**Analysis Capabilities:**
- Price dispersion over time
- Convergence metrics
- Spatial pattern analysis
- Efficiency calculations
- Comparative institutional studies

---

## XI. Success Metrics

### Research Success

**The platform succeeds if it enables answering:**
- ✓ When do bilateral prices converge to uniform exchange ratios?
- ✓ What institutional features promote/prevent convergence?
- ✓ How do spatial frictions affect market efficiency?
- ✓ When does decentralized exchange approximate Walrasian equilibrium?

**Publication Potential:**
- Comparative institutional analysis papers
- Matching theory applications
- Bargaining theory demonstrations
- Market design insights

---

### Pedagogical Success

**The platform succeeds if students can:**
- ✓ Observe markets forming from institutional rules
- ✓ Compare different organizational mechanisms
- ✓ Understand "price-taking" as emergent, not assumed
- ✓ Reason spatially and temporally about market dynamics
- ✓ Develop intuition through experimentation

**Adoption Metrics:**
- Used in intermediate micro courses
- Supplements textbook equilibrium analysis
- Generates classroom discussions about institutions
- Enables student research projects

---

### Technical Success

**The platform succeeds if:**
- ✓ Protocols are easy to implement (< 1 day each)
- ✓ Simulations are deterministic and reproducible
- ✓ Performance scales to pedagogical sizes (N=100 agents)
- ✓ Telemetry supports comprehensive analysis
- ✓ Comparison scenarios are straightforward

---

## XII. Current Status and Next Steps

### Where We Are (October 2025)

**Accomplished:**
- ✅ Spatial agent-based engine production-ready
- ✅ Protocol architecture implemented and validated
- ✅ Legacy protocols working (decentralized bilateral exchange)
- ✅ Comprehensive documentation and planning

**Ready to Implement:**
- 📋 Phase 2a protocols (baseline comparisons) - 8-10 hours
- 📋 Phase 2b protocols (pedagogical demonstrations) - 20-25 hours
- 📋 **Phase 3 protocols (centralized markets)** - 25-30 hours ⭐

### The Critical Path: Phase 3

**Why Phase 3 matters most:**

Phase 3 (Centralized Markets) is the **key milestone** because it enables the fundamental research question:

> **Do decentralized bilateral negotiations converge to centralized equilibrium outcomes?**

Without centralized mechanisms, we can only study bilateral exchange. With them, we can compare:
- Bilateral bargaining vs Walrasian auctioneer
- Spot negotiation vs posted prices
- Decentralized vs centralized organization

**This comparison is the heart of the research program.**

---

### Implementation Priorities

**Recommended Sequence:**
1. **Phase 2a** (1 week) → Validate architecture, establish baselines
2. **Phase 3** (3-4 weeks) → **Enable core comparisons** ⭐
3. **Phase 2b** (2 weeks) → Pedagogical demonstrations (can run parallel to Phase 3)
4. **Phase 4** (3-4 weeks) → Advanced protocols as research needs dictate
5. **Phase 5** (ongoing) → Expand library incrementally

**Rationale:** Jump from baseline validation (2a) to centralized markets (3) as quickly as possible. Phase 2b can fill in pedagogical details later, but Phase 3 unlocks the core research questions.

---

## XIII. Long-Term Vision (3-5 Years)

### Year 1: Exchange Mechanisms (Current Focus)
- Complete protocol library (Phases 2-5)
- Publish comparative institutional analysis
- Develop teaching materials and scenarios
- Establish VMT as research/teaching platform

### Year 2: Production Extension
- Add production functions and factor markets
- Firm decision-making
- Industry organization
- Labor markets

### Year 3: Market Failures
- Public goods and externalities
- Asymmetric information
- Market power and regulation
- Institutional responses

### Year 4-5: Advanced Topics
- General equilibrium with production
- Dynamic stochastic environments
- Network formation and intermediation
- Policy experiments and market design

### Ultimate Goal

**A comprehensive platform where:**
- No market phenomenon is assumed
- All institutions are explicit and comparable
- Emergence conditions are investigated empirically
- Students and researchers can explore "what if" institutional alternatives
- Economics pedagogy moves from equilibrium-first to emergence-first

---

## XIV. Conclusion: Why This Matters

### For Economics Education

Standard pedagogy assumes markets and prices. VMT demonstrates how they emerge (or don't) from institutional details. This is **pedagogically profound** because it:
- Makes institutions visible and comparable
- Shows equilibrium as achievement, not assumption
- Develops institutional reasoning skills
- Connects theory to real market organization

### For Economics Research

VMT provides a **laboratory for institutional comparative analysis**:
- Systematic protocol comparison
- Quantifiable effects of institutional details
- Spatial and temporal dynamics
- Bridge between theory and agent-based modeling

### For Market Design

Understanding **when markets work** (and when they don't) informs:
- Mechanism design choices
- Policy interventions
- Organizational decisions
- Institutional reform

---

## The Core Insight

**Markets are not natural phenomena that "just work" under ideal conditions.**

**Markets are institutional constructions** whose performance depends critically on:
- How agents search for partners
- How trading pairs form
- How prices are negotiated or set
- Whether exchange is bilateral or centralized
- What information is available
- How space and time constrain interactions

VMT makes these institutional details **explicit, manipulable, and comparable**—transforming economics from equilibrium analysis to institutional investigation.

---

**Document Status:** Strategic vision and research framework  
**Date:** 2025-10-27  
**Next Review:** After Phase 3 completion  
**Maintained By:** Project lead and collaborators  

**Location:** `docs/BIGGEST_PICTURE/vision_and_architecture.md`

