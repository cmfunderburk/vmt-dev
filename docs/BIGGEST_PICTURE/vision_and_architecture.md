# VMT: Visualizing Microeconomic Theory
## Vision, Architecture, and Research Agenda

**Document Type:** Strategic Vision and Research Framework  
**Purpose:** High-level overview of project goals, current state, and future directions  
**Last Updated:** 2025-10-31 (Major revision: emergence-focused paradigm)

---

## Paradigm Shift Notice (October 2025)

**Critical Update:** This document has been fundamentally revised to reflect VMT's core philosophical commitment to **emergence over imposition** and **validation before extension**.

**What Changed:**
- ❌ **Removed:** Phase 3 "Centralized Markets" (Walrasian auctioneer, imposed clearing)
- ✅ **Added:** Phase 2.5 "Scenario Curation and Behavioral Validation" (understand baseline first)
- ✅ **Added:** Phase 3 "Market Information and Coordination" (emergent price signals)
- ✅ **Added:** Phase 4 "Commodity Money Emergence" (money from trading patterns)
- 🔄 **Reordered:** Phase 2.5 is now the **priority starting point**

**Why:** 
1. **Emergence over Imposition:** VMT demonstrates how market phenomena **emerge** from micro-interactions, not from imposed equilibrium mechanisms
2. **Validation before Extension:** Must understand current bilateral behavior deeply before building new mechanisms
3. **Markets as Information:** Markets should aggregate information from bilateral trades, not replace them
4. **Money as Emergent:** Money should arise from marketability differences, not be assumed in utility functions

**Core Principle:** No external calculus. All coordination must arise from agent decisions and institutional protocols. Validate before you innovate.

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
- Under what conditions does price information aggregation produce coordination?
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

**Pure Bilateral Exchange (Current State):**
- Agents search for partners spatially
- Pairs form through matching protocols
- Prices negotiated bilaterally, pair-by-pair
- Exchange ratios may vary across pairs
- No information sharing beyond immediate partners

**Information-Enhanced Bilateral Exchange (Phase 3 Target):**
- Same bilateral trading structure
- Market areas detect spatial clustering
- Price signals aggregated from actual trades
- Information broadcast to nearby agents
- Bilateral bargaining informed by price signals

**Key Research Question:** How does information aggregation affect price convergence in decentralized bilateral trading? When do informed bilateral negotiations produce uniform exchange ratios?

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
- **Utility functions** over goods (A and B)
- **Initial endowments** (inventories)
- **Preferences** (various functional forms: CES, linear, quadratic, Stone-Geary, translog)

**Resources** regenerate on a spatial grid:
- Agents **forage** to acquire goods
- Foraging serves as rudimentary "production"
- Provides resource flow without production function complexity

**Exchange** occurs through bilateral mechanisms:
- **Pure barter** (A ↔ B direct exchange only)
- Future: Money mechanisms to be designed and implemented fresh

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

### 4. Information and Coordination Mechanisms

**Economic Question:** How does information aggregation affect decentralized price discovery?

**Mechanisms:**
- **Market-Informed Bargaining** → Bilateral negotiation anchored by aggregated price signals
- **Price Signal Broadcasting** → Information flow from dense trading areas
- **Information-Seeking Search** → Agents value access to price information
- **Spatial Market Detection** → Identification of trading hotspots

**Key Insights:**
- Price convergence emerges from information flow, not imposed coordination
- Market thickness affects information quality and price stability
- Spatial clustering creates natural "market areas"
- Information gradients produce realistic market structure

**Pedagogical Value:** **Demonstrates emergence—** Shows how markets form as information-processing institutions from bilateral trading patterns, not from external design.

---

## V. Current Implementation State

### What Exists (Production-Ready)

**1. Spatial Agent-Based Engine**
- Deterministic simulation with reproducible random seeding
- 7-phase tick cycle (perception → decision → movement → trade → forage → regeneration → housekeeping)
- Comprehensive telemetry (SQLite logging)

**2. Economic Foundations**
- 5 utility function types (CES, linear, quadratic, Stone-Geary, translog)
- Pure barter economy (A↔B direct goods exchange only)
- Foraging as resource generation
- Clean slate for future money mechanism design

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
⚠️ No information aggregation mechanisms  
⚠️ No price signal broadcasting or market-informed bargaining  
⚠️ Limited ability to explore price convergence conditions  
⚠️ Cannot yet study market information effects or money emergence  

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

### Phase 2.5: Scenario Curation and Behavioral Validation

**Goal:** Validate and demonstrate bilateral exchange behavior through carefully designed scenarios

**Philosophy:** Before building new mechanisms, establish clear empirical understanding of existing protocol behavior. Well-designed scenarios serve as both validation tests and pedagogical demonstrations.

**Key Activities:**

1. **Curated Scenario Development**
   - Design scenarios that isolate specific behavioral patterns
   - Create pedagogical examples demonstrating core mechanisms
   - Build scenarios that stress-test edge cases and corner behaviors
   - Establish baseline expectations for protocol comparison

2. **Behavioral Validation**
   - Verify that existing protocols produce expected outcomes
   - Document actual vs theoretical behavior
   - Identify gaps between implemented and intended behavior
   - Build intuition about system dynamics

3. **Demonstration Scenarios**
   - Edgeworth box cases (2-agent bilateral exchange)
   - Complementary endowments (gains from trade)
   - Homogeneous vs heterogeneous utility populations
   - Spatial clustering patterns
   - Resource scarcity and abundance cases

**Why This Matters:**
- **Foundation for Phase 3:** Can't understand information effects without knowing baseline bilateral behavior
- **Protocol Comparison:** Need clear expectations before adding alternatives
- **Research Validity:** Scenarios become reproducible empirical demonstrations
- **Teaching Value:** Curated scenarios are pedagogical tools

**Deliverables:**
- Suite of curated scenarios in `scenarios/curated/`
- Documentation of expected vs observed behaviors
- Behavioral validation reports
- Scenario design templates and guidelines

**Status:** This phase should be prioritized before Phase 3 implementation begins.

---

### Phase 3: Market Information and Coordination

**Goal:** Enable emergence of price signals and coordination from bilateral trading

**Philosophy:** Markets don't replace bilateral trading—they **enhance** it through information aggregation and broadcast. Instead of imposing external price calculators (Walrasian auctioneer), we create mechanisms for **emergent price discovery** through aggregated bilateral trading patterns.

**Core Mechanisms:**

1. **Spatial Market Detection**
   - Dense agent clusters become "market areas"
   - No institutional imposition—just observation of where trading happens
   - Market areas emerge and dissolve based on agent movement

2. **Price Signal Aggregation**
   - Market areas record bilateral trade prices within their zones
   - Compute volume-weighted average prices (VWAP)
   - Price signals emerge from actual trading, not theoretical calculation

3. **Information Broadcasting**
   - Agents observe price signals from nearby market areas
   - Market prices become part of agent WorldView
   - Information spreads spatially (closer agents have better information)

**Protocols to Implement:**

1. **Market-Informed Bargaining** → Uses aggregated price signals to anchor bilateral negotiations
   - Still bilateral (not centralized clearing)
   - Uses market prices as reference points
   - Natural evolution from pure bilateral trading
   - Demonstrates how information improves price convergence

2. **Information-Seeking Search** → Agents seek high-information areas
   - Prefer moving toward market zones
   - Balance direct partner search with information access
   - Demonstrates value of information in price discovery

3. **Thick-Market Matching** → Prefer partners in dense trading areas
   - Recognition that thick markets improve match quality
   - Endogenous market thickness effects
   - Clustering becomes strategic, not just spatial

**Critical Research Questions:**
- How does price information aggregation affect bilateral price convergence?
- Under what conditions do dispersed bilateral prices converge to uniform ratios?
- What role does market thickness play in information quality?
- How does spatial clustering enhance or impede price discovery?
- When do information-enhanced bilateral negotiations approximate theoretical equilibrium?

**Key Insight:** This phase doesn't impose markets—it demonstrates how markets **emerge** as information-processing institutions from bilateral trading patterns. Price convergence becomes an emergent property, not an algorithmic guarantee.

**Sets Up Phase 4 (Money Emergence):**
- Price signals reveal which goods trade most frequently (marketability)
- High-marketability goods become natural intermediaries for indirect exchange
- Agents begin accepting certain goods not for consumption but for re-trade
- Money-like behavior emerges from trading frictions, not utility functions

---

### Phase 4: Commodity Money Emergence

**Goal:** Demonstrate how money emerges endogenously from barter trading patterns

**Philosophy:** Money should not be imposed through utility functions that value it directly. Instead, money should emerge as agents discover that certain goods function better as exchange intermediaries due to higher marketability.

**Core Mechanisms:**

1. **Indirect Exchange Capability**
   - Enable multi-step trades: A→B→C paths
   - Agents can accept goods they don't want for consumption
   - Intermediary goods used for subsequent exchange

2. **Marketability Observation**
   - Track which goods trade most frequently
   - Observe which goods have narrower bid-ask spreads
   - Identify goods with more potential trading partners

3. **Strategic Intermediation**
   - Agents learn to accept high-marketability goods
   - Use marketable goods to overcome double coincidence failures
   - "Money-like" behavior emerges from trading strategy

**Protocols to Implement:**

1. **Indirect Exchange Search** → Agents seek multi-step trading paths
   - Find A→B→C sequences when direct A→C fails
   - Demonstrates solution to double coincidence problem
   - Shows emergence of intermediary goods

2. **Marketability-Weighted Matching** → Prefer partners offering marketable goods
   - Agents value goods partly by re-trading potential
   - High-marketability goods become preferred
   - Natural selection of "money-like" goods

3. **Speculative Bargaining** → Accept goods for re-trade, not consumption
   - Agents trade for goods they plan to exchange further
   - Intermediation becomes profitable strategy
   - Foundation of merchant/market-maker behavior

**Critical Research Questions:**
- Under what conditions do certain goods become preferred exchange intermediaries?
- How does market thickness affect which goods become "money-like"?
- What properties make a good a good money (divisibility, storability, etc.)?
- Can money emerge without being directly valued in utility functions?
- How do spatial patterns affect money emergence?

**Key Insight:** This demonstrates that money is not a primitive to be assumed—it's an **emergent institution** that arises when agents discover certain goods solve coordination problems better than others.

---

### Phase 5: Advanced Mechanisms and Extensions

**Goal:** Dynamic processes, learning, and sophisticated institutions

**Protocols:**
1. **Memory-Based Search** → Learning from experience (explore vs exploit)
2. **Stable Matching (Gale-Shapley)** → Incentive compatibility and stability
3. **Nash Bargaining** → Axiomatic cooperative solutions
4. **Rubinstein Alternating Offers** → Dynamic bargaining with time preferences
5. **Network Formation** → Endogenous trading relationships

**Research Applications:**
- Bounded rationality and learning dynamics
- Matching market design
- Cooperative vs non-cooperative game theory
- Long-term relationship formation
- Publication-quality comparative studies

**Note:** By Phase 5, money has either emerged naturally (Phase 4) or remains absent, demonstrating conditions under which monetary institutions arise.

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

### Theme 2: Information and Price Convergence

**Central Question:** How does information aggregation affect bilateral price discovery?

**Evolution Framework:**
```
Phase 1 - Pure Bilateral:
  Search → Matching → Bilateral Bargaining → Dispersed Prices
  (No information sharing beyond immediate partners)

Phase 3 - Information-Enhanced Bilateral:
  Search → Market Detection → Information-Informed Bargaining → Price Signals
  (Bilateral trading enhanced by aggregated price information)

Metrics:
  - Price dispersion over time (convergence vs persistence)
  - Information quality (VWAP accuracy, signal noise)
  - Spatial information gradients (distance from markets)
  - Convergence speed (ticks to stable prices)
  - Market thickness effects (clustering and efficiency)
```

**Research Implications:**
- How does information access affect market efficiency?
- What market structures emerge from spatial trading?
- When do bilateral negotiations converge without external coordination?
- What role does information play in price formation?

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
4. **Observe emergent prices** (dispersed or converging?)
5. **Introduce information mechanisms** (price aggregation, broadcasting)
6. **Market-informed bilateral trading** (information-enhanced negotiation)
7. **Observe money emergence** (which goods become intermediaries?)
8. **Equilibrium analysis** (compare outcomes to theory, understand deviations)

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
- ✓ How does information aggregation affect decentralized price discovery?
- ✓ Under what conditions does money emerge endogenously from trading patterns?
- ✓ How do spatial frictions and market thickness affect coordination?

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
- 📋 **Phase 2.5 scenario curation (behavioral validation)** - 15-20 hours ⭐ **PRIORITY**
- 📋 Phase 2b protocols (pedagogical demonstrations) - 20-25 hours
- 📋 Phase 3 protocols (market information and coordination) - 25-30 hours

### The Critical Path: Phase 2.5 → Phase 3

**Why Phase 2.5 comes first:**

Before building market information mechanisms (Phase 3) or alternative protocols (Phase 2a/2b), we need **empirical validation** of current bilateral exchange behavior through curated scenarios.

**Phase 2.5 Priority:**
- Understand baseline behavior deeply
- Document what existing protocols actually do (vs what we think they do)
- Create reproducible demonstrations
- Build scenario design expertise

**Without Phase 2.5:** Risk building on unstable foundation; won't know if Phase 3 changes are improvements.

**With Phase 2.5:** Clear baseline → confident Phase 3 implementation → valid comparisons.

**Why Phase 3 matters most (after 2.5):**

Phase 3 (Market Information and Coordination) is the **key conceptual milestone** because it enables the fundamental emergence question:

> **Under what conditions do price signals emerge and propagate from bilateral trading to produce coordination?**

Without information mechanisms, we can only study isolated bilateral exchange. With them, we can investigate:
- How information aggregation affects price dispersion
- When bilateral trading with price signals converges to uniform prices
- How spatial clustering and information flow interact
- Whether markets emerge as information-processing institutions

**This answers whether markets "just work" or require specific institutional features.**

**Phase 3 also sets up Phase 4 (Money Emergence):**

Once we have information-rich bilateral trading, we can observe:
- Which goods trade most frequently (marketability differences)
- Which goods agents accept for re-trade vs consumption
- Whether "money-like" goods emerge naturally from trading frictions
- If agents discover indirect exchange (A→M→B) as solution to double coincidence

**This progression—from pure barter → information-enhanced barter → emergent money—demonstrates how monetary institutions arise endogenously, not from assumption.**

---

### Implementation Priorities

**Recommended Sequence:**
1. **Phase 2.5** (2-3 weeks) → **Scenario curation and behavioral validation** ⭐ **START HERE**
2. **Phase 2a** (1 week) → Baseline protocol implementation (informed by 2.5)
3. **Phase 3** (3-4 weeks) → Market information and coordination
4. **Phase 2b** (2 weeks) → Pedagogical demonstrations (can run parallel to Phase 3)
5. **Phase 4** (4-6 weeks) → Money emergence mechanisms (builds on Phase 3)
6. **Phase 5** (ongoing) → Advanced protocols and extensions

**Rationale:** **Phase 2.5 is the new starting point.** Before implementing alternative protocols or market information, we need deep empirical understanding of existing bilateral behavior through curated scenarios. This creates a solid foundation for all future work. Phase 2a baseline protocols can then be validated against scenarios from 2.5. Phase 3 builds on validated baseline. Phase 2b can run in parallel once baseline is solid.

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

