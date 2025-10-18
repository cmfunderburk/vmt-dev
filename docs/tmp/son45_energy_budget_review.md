# Energy Budget Feature: Comprehensive Review and Design Analysis

**Date:** October 18, 2025  
**Status:** Design Phase  
**Author:** Design Review Session

---

## Executive Summary

This document explores the addition of an **energy budget** system to VMT—a constraint that forces agents to alternate between active economic behavior and rest periods at a designated "home" location. The feature introduces a sleep/wake cycle analogy where agents deplete energy through activity and must periodically return home to regenerate. This document provides theoretical grounding, implementation design, pedagogical analysis, research applications, and a thorough pros/cons evaluation.

---

## 1. Theoretical Foundation

### 1.1 Economic Analogies

The energy budget maps onto several core economic concepts:

**Time Endowment Constraints**  
In standard microeconomic models, agents face time constraints (typically 24 hours) that must be allocated between labor and leisure. The energy budget creates a *structural* time constraint rather than a *choice* variable—agents cannot choose to work indefinitely but are forced into rest periods. This mirrors:
- Mandatory rest requirements in labor law
- Physiological limits on continuous activity
- Fixed costs of maintaining alertness/productivity

**Fixed Costs and Sunk Costs**  
The home location represents a spatial fixed cost:
- **Establishment cost**: Finding and claiming a home (one-time sunk cost)
- **Opportunity cost**: Distance from home to economic activity centers
- **Return cost**: Travel time/effort to return home when energy depletes

This creates natural agglomeration vs. dispersion pressures—agents face a tradeoff between locating homes near resource-rich areas (competition) vs. remote areas (travel costs).

**Intertemporal Allocation**  
Agents must implicitly solve an intertemporal optimization problem:
- How much energy to "spend" on trade vs. foraging vs. movement?
- When to return home proactively vs. wait until forced?
- Where to locate home relative to expected activity patterns?

Unlike traditional savings problems, energy cannot be "borrowed"—agents face a hard constraint at zero, creating **liquidity constraint** dynamics.

### 1.2 Biological and Agent-Based Modeling Foundations

**Circadian Rhythms**  
The sleep/wake cycle is perhaps the most fundamental biological rhythm. In ABM contexts, energy budgets have been used in:
- Foraging models (optimal foraging theory with energy budgets)
- Predator-prey dynamics (hunting requires energy, rest is vulnerable)
- Social insect models (nest-based activity cycles)

**Central Place Foraging**  
The home location transforms VMT into a **central place foraging** model—agents repeatedly travel from a fixed location to exploit distributed resources. This is well-studied in behavioral ecology and provides rich theoretical predictions about:
- Optimal home site selection
- Patch exploitation strategies
- Load size vs. trip frequency tradeoffs

**State-Dependent Behavior**  
Energy level becomes a state variable that modulates behavior:
- **High energy**: Risk-taking, exploration, distant foraging
- **Medium energy**: Conservative, local exploitation
- **Low energy**: Desperate, homeward-oriented, may accept poor trades

This adds behavioral realism and heterogeneity without requiring complex psychological models.

---

## 2. Implementation Design

### 2.1 Core Mechanics

**Energy Parameters** (per agent):
```python
energy_max: int = 24          # Maximum energy capacity
energy_current: int = 24      # Current energy level
energy_cost_per_tick: int = 1 # Energy cost for being active
energy_regen_rate: int = 3    # Energy regained per tick while resting
home_location: Optional[Tuple[int,int]] = None  # Agent's home coordinates
```

**State Machine**:
- `ACTIVE`: Normal behavior, energy > 0, not at home
- `RETURNING_HOME`: Energy depleted, navigating toward home
- `RESTING`: At home, energy < energy_max, regenerating
- `SEEKING_HOME`: Energy depleted, no home exists, searching for unoccupied square

### 2.2 Integration with 7-Phase Tick

The energy system must integrate with VMT's deterministic phase structure:

**Phase 0: Energy Check (NEW)**  
*Before perception*
- Decrement `energy_current` by `energy_cost_per_tick` for all ACTIVE agents
- If `energy_current <= 0`:
  - If `home_location` exists: Set state → `RETURNING_HOME`
  - Else: Set state → `SEEKING_HOME`
- If at home and `energy_current < energy_max`: Set state → `RESTING`

**Phase 1: Perception**  
- `RESTING` agents: Skip perception (closed eyes metaphor)
- `RETURNING_HOME` / `SEEKING_HOME`: Perceive only home-relevant info (home direction, nearby vacant squares)
- `ACTIVE`: Normal perception

**Phase 2: Decision**  
- `RESTING`: No decisions
- `RETURNING_HOME`: Set movement target toward home
- `SEEKING_HOME`: Identify nearest vacant square, set as target
- `ACTIVE`: Normal decision-making

**Phase 3: Movement**  
- `RESTING`: No movement (or minimal fidgeting?)
- `RETURNING_HOME` / `SEEKING_HOME`: Execute movement toward target
- `ACTIVE`: Normal movement

**Phase 4: Trade**  
- `RESTING` / `RETURNING_HOME` / `SEEKING_HOME`: Ineligible for trade
- `ACTIVE`: Normal trading

**Phase 5: Foraging**  
- `RESTING` / `RETURNING_HOME` / `SEEKING_HOME`: Cannot forage
- `ACTIVE`: Normal foraging

**Phase 6: Resource Regeneration**  
- Unchanged (resources regenerate regardless of agent states)

**Phase 7: Housekeeping**  
- All agents refresh quotes (even RESTING—they might dream about prices?)
- `RETURNING_HOME`: Check if arrived home → transition to `RESTING`
- `SEEKING_HOME`: Check if arrived at target → claim as `home_location`, transition to `RESTING`
- `RESTING`: Increment `energy_current` by `energy_regen_rate` (cap at `energy_max`)
- `RESTING` with full energy: Transition to `ACTIVE`

### 2.3 Home Location Mechanics

**Initial Home Assignment**  
Design choice: Should agents start with homes or discover them?

*Option A: Pre-assigned homes*  
- Scenario YAML specifies `home_location: [x, y]` per agent
- Agents start at home, fully rested
- Deterministic, simple

*Option B: Emergent homes*  
- Agents start with `home_location = None`
- First energy depletion triggers home search
- More organic, but delays first home establishment

**Recommendation**: Support both—default to `None`, allow YAML override.

**Home Claiming Rules**  
When `SEEKING_HOME`:
1. Identify all vacant squares within `vision_radius`
2. If multiple candidates, choose by:
   - Minimize distance to current position (Manhattan)
   - Tie-break: Lowest (x, y) lexicographically (determinism)
3. If no vacant squares in vision: Move toward nearest vacant square (requires spatial index query)
4. On arrival: Claim square, set `home_location`, transition to `RESTING`

**Home Permanence**  
Design choice: Can agents relocate homes?

*Option A: Permanent homes*  
- Once claimed, `home_location` never changes
- Simple, encourages strategic initial placement

*Option B: Relocatable homes*  
- Agents can "abandon" home and seek new one
- Triggers: Distance from economic activity, resource depletion
- Adds complexity, requires cooldown logic to prevent oscillation

**Recommendation**: Start with permanent homes. Relocation could be a v2 feature.

**Home Conflicts**  
Can multiple agents share a home square?

*Option A: Exclusive homes*  
- Each home square can only be claimed by one agent
- Requires tracking `grid.home_occupancy: Dict[(int,int), agent_id]`
- First-come-first-served (deterministic by agent ID processing order)

*Option B: Shared homes*  
- Multiple agents can rest at same square (e.g., dormitories, villages)
- Simpler, more forgiving for high-density scenarios

**Recommendation**: Start with exclusive homes. Shared homes could be a parameter.

### 2.4 Determinism Considerations

**Critical**: Energy system must preserve VMT's determinism guarantees.

- **Iteration order**: Process agents in ascending `agent.id` order during energy checks, home searches
- **Tie-breaking**: All spatial searches use deterministic tie-breaks (lowest (x,y))
- **Random elements**: If home search uses randomness (e.g., random walk when no visible vacant squares), must use the simulation's seeded RNG
- **State transitions**: All state changes occur in deterministic phases, never mid-phase

**Test requirement**: Two runs with same seed must produce identical energy states, home locations, and activity patterns.

---

## 3. Behavioral and Strategic Implications

### 3.1 Emergent Behaviors

**Spatial Clustering**  
Agents may form "neighborhoods" if homes cluster near resource-rich areas or trade hubs. This creates:
- **Agglomeration economies**: Reduced travel costs for trade
- **Congestion externalities**: Resource competition, movement blocking
- **Path dependence**: Early arrivals claim best locations

**Temporal Synchronization**  
If agents start with same energy levels and similar depletion rates, they may synchronize sleep/wake cycles—creating "rush hours" when most agents are active and "quiet periods" when most rest. This is economically interesting:
- **Peak trading periods**: More opportunities but more competition
- **Off-peak advantages**: Less competition but fewer partners

**Desynchronization** could emerge if:
- Agents have heterogeneous `energy_max` or `energy_regen_rate`
- Random shocks (trade failures, long foraging trips) desynchronize cycles

**Strategic Home Placement**  
Forward-looking agents might optimize home location based on:
- Proximity to frequently visited resource patches
- Centrality for trade opportunities (minimize average distance to other agents)
- Avoiding competition (claim remote homes if energy budget is large)

This requires agents to "learn" or have prior knowledge—an area for future enhancement.

**Energy Hoarding**  
Agents might return home proactively before energy fully depletes to avoid being caught far from home. This is rational risk aversion but requires:
- Agents to track distance to home
- Compare energy remaining vs. travel cost
- Proactive decision-making (not yet implemented)

### 3.2 Economic Equilibrium Effects

**Effective Labor Supply**  
Energy budgets reduce effective "labor supply" in the economy:
- If `energy_max = 24`, `energy_cost_per_tick = 1`, `energy_regen_rate = 3`
- Full depletion → 24 ticks active
- Full regeneration → 24/3 = 8 ticks resting
- **Duty cycle**: 24/(24+8) = 75% active

This creates **idle capacity**—resources that could be exploited but aren't because agents are resting.

**Wealth Inequality**  
Home location quality may drive wealth divergence:
- Agents with centrally located homes spend less time traveling, more time trading/foraging
- Agents with remote homes incur higher opportunity costs
- Over many cycles, this compounds into wealth inequality

**Trade Network Topology**  
Active agents at any given time form a subset of the full population. Trade networks become **temporally dynamic**:
- Some edges (agent pairs) may never be simultaneously active if sleep cycles anti-synchronize
- Network density fluctuates over time
- Potential for "bridge" agents who connect otherwise isolated temporal clusters

---

## 4. Pedagogical Value

### 4.1 Microeconomic Concepts

**Time Constraints and Labor-Leisure Choice**  
While VMT's energy budget is *imposed* rather than *chosen*, it introduces students to:
- Scarcity of time as a binding constraint
- Opportunity cost of time allocation
- Difference between *constraint* (must rest) vs. *preference* (choose rest)

**Extension**: Future version could let agents *choose* to rest early (voluntary leisure) vs. forced rest.

**Fixed Costs and Location Theory**  
The home location decision is a miniature version of:
- Urban economics (where to live relative to work?)
- Industrial organization (firm location decisions)
- Trade theory (port vs. inland production)

Students can observe emergent location patterns and discuss:
- Why do agents cluster or disperse?
- What makes a location "good"?
- How do first-mover advantages affect spatial equilibria?

**Inequality and Initial Conditions**  
If homes are assigned or claimed early, students can explore:
- Path dependence (does starting position determine long-run wealth?)
- Policy interventions (randomized home assignments, home swapping mechanisms)
- Equity vs. efficiency tradeoffs

### 4.2 Behavioral Economics

**Bounded Rationality**  
Agents without perfect foresight may:
- Claim suboptimal home locations (myopic)
- Fail to return home proactively (present bias?)
- Engage in risky long-distance foraging despite low energy

This provides concrete examples of:
- Satisficing vs. optimizing
- Consequences of imperfect information
- Learning and adaptation over time (if agents update strategies)

**Self-Control and Commitment**  
The *mandatory* return home when energy depletes is a form of external commitment device. Students could explore:
- What if agents could override the energy constraint (at a cost)?
- Hyperbolic discounting: Agents always plan to return home "next turn" but delay until forced
- Pre-commitment strategies: Voluntary rest before depletion

### 4.3 Comparative Statics and Parameter Exploration

Students can experiment with:
- **`energy_max`**: Large values → infrequent rest, more flexibility. Small values → frequent rest, more constrained.
- **`energy_regen_rate`**: Slow regen → long rest periods, low activity ratio. Fast regen → short rest, high activity.
- **`energy_cost_per_tick`**: Variable costs (e.g., movement costs more energy than resting in place) → complex energy management.

**Learning objectives**:
- Distinguish parameters vs. endogenous outcomes
- Trace causal mechanisms from parameter changes to behaviors to outcomes
- Develop intuition for dynamic systems

---

## 5. Research Applications

### 5.1 Central Place Foraging Models

VMT becomes a computational implementation of **central place foraging theory**:
- **Classic questions**:
  - Optimal patch residence time (marginal value theorem)
  - Load size vs. trip frequency tradeoffs
  - Prey choice models with travel costs
- **VMT extensions**:
  - Multi-agent competition for patches
  - Endogenous home location choice
  - Trade opportunities en route

**Research contribution**: Most central place models assume a single forager. VMT enables studying N-agent central place systems with strategic interactions.

### 5.2 Spatial Economic Dynamics

**Agglomeration and Dispersion**  
Energy budgets + home locations create incentives for:
- Agglomeration: Locate near other agents for trade
- Dispersion: Avoid competition for resources

This parallels:
- New Economic Geography models (Krugman)
- Urban systems formation
- Industry clustering (Silicon Valley, etc.)

**Research questions**:
- Under what parameters do stable spatial clusters form?
- Do agent characteristics (utility functions, skill levels) predict spatial sorting?
- How do transport costs (movement budget, home distance) affect spatial equilibrium?

### 5.3 Temporal Market Dynamics

**Asynchronous Trading**  
If agents have different wake/sleep schedules:
- **Temporal arbitrage**: Agent A (awake) buys from agent B (awake), stores goods, sells to agent C (awake later)
- **Inventory holdings**: Rational to hold inventory across rest periods if future trade opportunities are predictable
- **Market thinness**: Fewer active agents → less liquidity, worse terms of trade

**Research questions**:
- Do markets "thin out" during periods when many agents rest?
- Can agents strategically time rest to coincide with poor market conditions?
- Do storage/inventory mechanisms emerge endogenously?

### 5.4 Physiological Constraints in Economic Models

**Behavioral macro**:
- Labor supply shocks from rest requirements
- Productivity cycles (are well-rested agents more productive?)

**Development economics**:
- Subsistence agriculture: Farmers must return to homesteads
- Health constraints: Energy budget as metaphor for disease burden, malnutrition

**Mechanism design**:
- How to design markets when participants have limited availability?
- Auction timing, matching markets with temporal constraints (kidney exchange, school choice)

---

## 6. Detailed Pros and Cons Analysis

### 6.1 Advantages (Pros)

#### **P1: Behavioral Realism**
Agents become more lifelike—they're not tireless automata but beings with physiological limits. This enhances:
- **Immersion**: Students/observers relate to rest requirements
- **Plausibility**: Models with rest constraints better mirror real economies

#### **P2: Spatial Structure and Meaning**
The grid gains semantic depth:
- Locations are no longer fungible—home squares are special
- Distance matters more—being far from home has consequences
- Emergent geography: Neighborhoods, trade routes, center/periphery

#### **P3: Dynamic Complexity**
Introduces **non-stationary** dynamics:
- Agent availability fluctuates
- Trade networks rewire over time
- Resource exploitation patterns have temporal rhythms

#### **P4: Rich Pedagogical Opportunities**
Concepts teachable:
- Time constraints, opportunity cost
- Fixed costs, sunk costs, spatial economics
- Path dependence, inequality from initial conditions
- Bounded rationality, myopic vs. forward-looking behavior

#### **P5: Research Novelty**
To our knowledge, no multi-agent economic model combines:
- Central place foraging
- Endogenous home location choice
- Strategic trade and resource competition
- Fully deterministic implementation

This is a **unique research platform**.

#### **P6: Configurable Complexity**
Parameters allow tuning from:
- **Minimal impact**: `energy_max = 10000`, `energy_regen_rate = 1000` → agents almost never rest
- **Severe constraint**: `energy_max = 10`, `energy_regen_rate = 1` → agents rest frequently

Users can gradually introduce the feature.

#### **P7: Emergent Strategic Depth**
Even without AI/learning:
- Home placement matters
- Energy management matters
- Timing of activities matters

With learning agents (future), this becomes a rich strategic space.

---

### 6.2 Disadvantages (Cons)

#### **C1: Implementation Complexity**
Non-trivial additions:
- New agent state machine (`ACTIVE`, `RESTING`, `RETURNING_HOME`, `SEEKING_HOME`)
- Home location tracking and claiming logic
- Phase-specific behavior switches
- Extensive testing required (home conflicts, edge cases, determinism)

**Estimated effort**: 2-3 days implementation + 1-2 days testing.

#### **C2: Scenario Design Burden**
Scenario authors must consider:
- Initial home assignments (if any)
- Grid size relative to agent count (enough space for homes?)
- Energy parameters (what's reasonable for scenario length?)

**Mitigation**: Provide sensible defaults, good documentation.

#### **C3: Performance Overhead**
Additional per-tick computations:
- Energy checks for all agents
- Home pathfinding for `RETURNING_HOME` / `SEEKING_HOME` agents
- Home occupancy tracking (if exclusive homes)

**Estimated impact**: 5-10% slowdown for typical scenarios.

**Mitigation**: Optimize hot paths, use spatial indices for home searches.

#### **C4: Interpretation Complexity**
Observing simulations becomes harder:
- Why is agent X not trading? (Oh, they're resting)
- Why is agent Y moving oddly? (Oh, they're returning home)
- Did agent Z's wealth decrease because of poor trades or because they spent time resting?

**Mitigation**: UI indicators (sleeping emoji?), telemetry logs state transitions, documentation.

#### **C5: Potential for Uninteresting Equilibria**
Risk: Agents spend most time resting, little activity occurs.
- If `energy_regen_rate` is too low, agents "hibernate" for long periods
- If homes are far from resources, agents spend energy commuting

**Mitigation**: Careful default parameter tuning, example scenarios showcasing interesting dynamics.

#### **C6: Pedagogical Overwhelm**
Adding energy budget on top of:
- Utility functions
- Trade mechanics
- Foraging
- Movement
- Resource regeneration

Could be **too much** for introductory students.

**Mitigation**: Make energy optional (disable with `energy_max = inf`), introduce gradually in curriculum.

#### **C7: Home Location as Exogenous Shock**
If homes are pre-assigned, this introduces **initial condition sensitivity**:
- Two agents with identical preferences but different home locations → divergent outcomes
- This is interesting (see P4) but also confounding—harder to isolate effects of other parameters

**Mitigation**: Offer modes—fixed homes, random homes, emergent homes—document tradeoffs.

#### **C8: Determinism Edge Cases**
Home claiming with multiple agents simultaneously seeking homes in same area:
- Agent 5 and Agent 7 both target square (10, 10)
- Agent 5 arrives first (processed earlier) → claims it
- Agent 7 must reroute → non-obvious to observer

**Mitigation**: Careful logging, clear rules documented, extensive tests.

---

### 6.3 Pros/Cons Balance

**Net assessment**: The energy budget is a **high-value, medium-complexity** feature.

**Best use cases**:
- Advanced pedagogy (second-semester course, after students grasp basics)
- Research applications (spatial economics, temporal dynamics)
- Demos showcasing VMT's unique capabilities

**Caution cases**:
- Introductory teaching (may overwhelm)
- Large-scale performance-critical simulations (non-negligible overhead)
- Scenarios where spatial structure is already complex (avoid over-complication)

---

## 7. Design Choices and Open Questions

### 7.1 Key Design Decisions

**D1: Energy as State vs. Emergent**  
*Choice*: Energy is an explicit agent state variable.  
*Alternative*: Energy as shadow price from time allocation optimization.  
*Justification*: Explicit state is simpler, more intuitive, easier to observe.

**D2: Mandatory vs. Voluntary Rest**  
*Choice*: Rest is mandatory when energy depletes.  
*Alternative*: Agents can choose to continue (at a penalty).  
*Justification*: Mandatory rest is clearer, avoids complex decision logic (for now).

**D3: Home Permanence**  
*Choice*: Homes are permanent once claimed.  
*Alternative*: Agents can relocate homes.  
*Justification*: Permanence simplifies implementation, mirrors homeownership irreversibility.

**D4: Exclusive vs. Shared Homes**  
*Choice*: Homes are exclusive to one agent.  
*Alternative*: Multiple agents can share a home square.  
*Justification*: Exclusivity creates interesting scarcity, mimics private property.

**D5: Initial Home Assignment**  
*Choice*: Support both pre-assigned and emergent homes.  
*Alternative*: Only one mode.  
*Justification*: Flexibility for different pedagogical/research uses.

### 7.2 Open Questions

**Q1: Should energy costs vary by activity?**  
- Currently: 1 energy per tick regardless of action.
- Alternative: Movement costs more than staying still? Trading costs more than resting?
- Implication: Adds realism but complicates energy management.

**Q2: Should energy regen rate depend on home quality?**  
- Currently: Fixed `energy_regen_rate`.
- Alternative: Homes near resources → faster regen? Crowded areas → slower regen?
- Implication: Introduces home quality heterogeneity, deeper strategic layer.

**Q3: Should agents perceive others' energy states?**  
- Currently: Not specified.
- Alternative: Agents can see neighbors' energy → avoid trading with exhausted agents.
- Implication: Enables energy-based discrimination, signaling games.

**Q4: Should energy transfer between agents (sharing)?**  
- Currently: Energy is non-transferable.
- Alternative: Agents can "gift" energy (e.g., carry exhausted agent home, share food that restores energy).
- Implication: Enables cooperation, altruism, but complex to implement.

**Q5: Should rest be interruptible?**  
- Currently: Agents rest until full.
- Alternative: Urgent opportunities (valuable trade, resource appears) wake agents early.
- Implication: Adds responsiveness but requires priority/threshold logic.

**Q6: Should energy be a hard cap or soft constraint?**  
- Currently: Hard cap—zero energy forces rest.
- Alternative: Soft constraint—agents can "overdraw" energy into negative (debt) but accumulate penalties.
- Implication: Soft constraints more realistic (people do pull all-nighters) but harder to reason about.

---

## 8. Implementation Roadmap

### Phase 1: Core Mechanics (MVP)
**Goal**: Get basic energy depletion and rest working.

1. Add agent attributes: `energy_current`, `energy_max`, `energy_cost_per_tick`, `energy_regen_rate`, `home_location`, `agent_state`
2. Implement energy depletion in new Phase 0
3. Implement rest state: agents at home regain energy, skip other phases
4. Manual home assignment in YAML scenarios
5. Test: Single agent depletes energy at home, rests, resumes activity

**Estimated time**: 1 day

### Phase 2: Home Seeking
**Goal**: Agents can find and claim homes when needed.

1. Implement `SEEKING_HOME` state
2. Pathfinding logic: Find nearest vacant square
3. Home claiming: Mark square as occupied
4. Transition to `RESTING` on arrival
5. Test: Agent with no home depletes energy, finds home, claims it, rests

**Estimated time**: 1 day

### Phase 3: Home Return
**Goal**: Agents with homes return when energy depletes.

1. Implement `RETURNING_HOME` state
2. Pathfinding logic: Navigate toward `home_location`
3. Transition to `RESTING` on arrival
4. Test: Agent with home depletes energy away from home, returns, rests

**Estimated time**: 0.5 days

### Phase 4: Determinism and Edge Cases
**Goal**: Ensure feature is fully deterministic and robust.

1. Audit all home-related logic for determinism (iteration order, tie-breaks)
2. Test home conflicts: Multiple agents seek same square
3. Test edge cases: Agent stranded far from home, no vacant squares visible, etc.
4. Seed-based regression tests

**Estimated time**: 1 day

### Phase 5: Telemetry and Visualization
**Goal**: Make energy states observable.

1. Log energy levels to telemetry DB
2. Log state transitions (`ACTIVE` → `RETURNING_HOME`, etc.)
3. Log home locations (when claimed)
4. Pygame visualization: Show energy bars, home markers, state colors
5. Log viewer: Query agents by energy state

**Estimated time**: 1 day

### Phase 6: Scenario Tuning and Documentation
**Goal**: Make feature usable for pedagogy/research.

1. Create reference scenarios showcasing energy dynamics
2. Document all parameters in schema
3. Write tutorial: "Understanding Energy Budgets in VMT"
4. Performance profiling and optimization

**Estimated time**: 1 day

**Total estimated time**: 5.5 days ≈ **1-1.5 weeks** for full feature.

---

## 9. Alternative Designs Considered

### 9.1 Energy as Inventory Good
**Concept**: Instead of abstract "energy," agents have an inventory good "food" that depletes and must be replenished.

**Pros**:
- Integrates with existing inventory/trade system
- Agents can trade food → market for energy emerges
- More economically interesting (endogenous energy prices)

**Cons**:
- Much more complex implementation
- Food production/distribution must be designed
- Hard to balance (food too scarce → agents starve; too abundant → no constraint)

**Verdict**: Interesting for future research extension, but too complex for initial implementation.

### 9.2 Fatigue as Declining Productivity
**Concept**: Agents don't stop acting but become less effective as energy depletes (e.g., lower foraging rates, worse trade surplus extraction).

**Pros**:
- No hard state transitions—gradual degradation
- Simpler (no home location logic)
- Mirrors real fatigue effects

**Cons**:
- Less visually/pedagogically clear
- Doesn't capture forced rest (sleep is mandatory, not optional)
- Harder to tune (how much productivity loss per energy point?)

**Verdict**: Could complement energy budget (rested agents are more productive) but doesn't replace the core mechanic.

### 9.3 Stochastic Energy Shocks
**Concept**: Instead of deterministic depletion, agents face random energy shocks (illness, injury) forcing rest.

**Pros**:
- Models unpredictability of health/fatigue
- Desynchronizes agents naturally

**Cons**:
- Breaks determinism (major architectural issue)
- Harder to reason about—students can't predict outcomes
- Risk becomes dominant factor, obscuring other mechanisms

**Verdict**: Incompatible with VMT's determinism requirement. Ruled out.

---

## 10. Integration with Existing Features

### 10.1 Trade System
**Interaction**: Resting agents cannot trade.

**Implications**:
- Trade networks are time-varying subgraphs
- Agents may "miss" trade opportunities if resting
- Strategic timing: Return home when few trade opportunities exist?

**No conflicts**: Energy system cleanly disables trade for non-`ACTIVE` agents.

### 10.2 Foraging System
**Interaction**: Resting agents cannot forage.

**Implications**:
- Resources may accumulate near agents' homes (others avoid)
- Agents face tradeoff: Forage distant high-value patches (risk being far when energy depletes) vs. near low-value patches (safer)

**Potential enhancement**: Foraging costs extra energy? Long-distance foraging is risky.

### 10.3 Movement System
**Interaction**: `RETURNING_HOME` / `SEEKING_HOME` agents move toward home, not toward resources/trade.

**Implications**:
- Agents may move "against" their economic incentives when energy-depleted
- Creates inefficiency—travel solely for rest, not production

**Potential conflict**: If movement budget is shared between economic movement and home-return movement, agents may fail to reach home in time (strand themselves). 

**Solution**: Separate budgets? Or ensure agents always return home proactively when energy is low (requires AI enhancement).

### 10.4 Resource Regeneration
**Interaction**: Resources regenerate independently of agent states.

**No conflicts**: Energy system doesn't affect resource dynamics.

**Potential enhancement**: Resources near homes regenerate faster (agents "tend" their home patch)?

### 10.5 Perception System
**Interaction**: Resting agents may have reduced perception (closed eyes).

**Implications**:
- Can't update knowledge of resource locations while resting
- Must rely on pre-rest information

**Design choice**: Full perception blackout during rest, or limited perception (home awareness only)?

---

## 11. Testing Strategy

### 11.1 Unit Tests

1. **Energy depletion**: Agent with `energy_max=10`, `energy_cost_per_tick=1` depletes to 0 after 10 ticks.
2. **Energy regeneration**: Agent with `energy_regen_rate=3` at home regains 3 energy per tick.
3. **State transitions**: Correct transitions between `ACTIVE`, `RESTING`, `RETURNING_HOME`, `SEEKING_HOME`.
4. **Home claiming**: Agent claims nearest vacant square deterministically.
5. **Home conflicts**: Multiple agents seeking homes claim unique squares (no collisions).

### 11.2 Integration Tests

1. **Full cycle**: Agent starts active, depletes energy, returns home, rests, resumes activity—all phases execute correctly.
2. **Trade while active**: Agent trades normally when energy > 0.
3. **No trade while resting**: Agent at home with low energy does not participate in trade.
4. **Forage while active**: Agent forages normally when energy > 0.
5. **No forage while returning**: Agent returning home does not forage en route.

### 11.3 Determinism Tests

1. **Seed invariance**: Two simulations with same seed produce identical energy states, home locations, activity patterns.
2. **Iteration order**: Agents processed in ascending ID order for all energy-related logic.
3. **Tie-breaking**: Home search tie-breaks consistently choose lowest (x, y).

### 11.4 Scenario Tests

1. **Minimal scenario**: 1 agent, small grid, verify basic energy cycle.
2. **Multi-agent scenario**: 3+ agents, verify independent energy states, home conflicts handled.
3. **Dense scenario**: 50 agents on 40x40 grid, verify performance, all agents find homes.
4. **Extreme parameters**: `energy_max=1` (rest almost always), `energy_max=1000` (rest almost never).

---

## 12. Conclusion and Recommendation

### 12.1 Summary

The energy budget feature is a **theoretically grounded, pedagogically valuable, and research-enabling** addition to VMT. It introduces:
- Behavioral realism (sleep/wake cycles)
- Spatial depth (home locations matter)
- Dynamic complexity (time-varying agent availability)
- Rich strategic interactions (home placement, energy management)

### 12.2 Recommendation

**Proceed with implementation**, prioritizing:
1. **MVP first**: Get core energy depletion and rest working with manual home assignment. Validate the concept.
2. **Iterate on home mechanics**: Add home seeking, home claiming, ensure robustness.
3. **Tune parameters**: Develop reference scenarios with interesting energy dynamics, avoid pathological cases.
4. **Defer extensions**: Save advanced features (energy transfer, variable costs, home relocation) for future versions once core is stable.

### 12.3 Success Criteria

The feature will be considered successful if:
- **Determinism preserved**: Seeded runs produce identical results.
- **Performance acceptable**: <10% slowdown for typical scenarios.
- **Pedagogically useful**: Students can observe and reason about energy-driven behaviors.
- **Research-enabling**: Supports novel questions about spatial-temporal economic dynamics.
- **Configurable**: Users can tune from negligible impact to dominant constraint.

### 12.4 Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Implementation complexity exceeds estimate | Start with MVP, iterate; defer advanced features |
| Performance overhead too high | Profile hotspots, optimize spatial indexing for home searches |
| Pedagogical overwhelm | Make energy optional (off by default), provide graduated examples |
| Uninteresting dynamics (too much resting) | Careful default tuning, parameter sensitivity analysis |
| Determinism bugs | Extensive testing, clear iteration order rules, regression tests |

---

## 13. Next Steps

1. **Review this document**: Discuss design choices, address open questions.
2. **Finalize specification**: Lock down parameter defaults, state machine transitions, home mechanics.
3. **Create GitHub issue**: Track implementation progress, link to this document.
4. **Implement Phase 1 (MVP)**: Core energy depletion and rest at pre-assigned homes.
5. **Validate concept**: Run preliminary scenarios, assess whether dynamics are interesting.
6. **Proceed to full implementation**: If MVP is promising, complete all phases.

---

**End of Document**

