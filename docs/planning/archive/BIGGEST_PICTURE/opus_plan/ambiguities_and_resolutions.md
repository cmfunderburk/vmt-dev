# VMT Vision: Ambiguities, Inconsistencies, and Resolutions

**Document Purpose**: Identify and resolve contradictions between planning documents  
**Created**: November 2, 2025  
**Status**: Design Clarification

---

## Core Ambiguities Requiring Resolution

### 1. Identity Crisis: Educational Tool vs Research Platform

**The Ambiguity**: 
Documents oscillate between describing VMT as:
- An undergraduate teaching tool with guided tutorials
- A research platform for institutional comparison and publication
- A visualization-first educational experience
- A rigorous computational economics framework

**The Tension**: 
These identities pull in different directions:
- Education wants simplicity and guidance
- Research wants flexibility and rigor
- Students need scaffolding
- Researchers need control

**Resolution**: 
**Build a research-grade engine with an educational wrapper**

```
VMT Architecture
│
├── Research Core (Always Present)
│   ├── Full protocol flexibility
│   ├── Complete parameter space
│   ├── Statistical analysis
│   └── Reproducible experiments
│
└── Educational Interface (Default Mode)
    ├── Guided experiences
    ├── Progressive complexity
    ├── Pre-built scenarios
    └── Simplified controls
```

The same simulation engine serves both audiences through different interfaces. Switch between modes in settings.

---

### 2. Philosophical Contradiction: Emergence vs Equilibrium

**The Ambiguity**:
- Core principle: "No external calculus. All coordination must arise from agent decisions"
- Proposed feature: Walrasian auctioneer—literally an external calculator!
- Mission: Show markets emerge from micro-interactions
- Plan: Include tatonnement and equilibrium solvers

**The Apparent Contradiction**: 
How can you be "emergence-first" while implementing the opposite of emergence?

**Resolution**: 
**Frame equilibrium as a pedagogical contrast, not an equal alternative**

The three tracks answer different questions:
1. **Agent-Based**: "What actually happens when individuals trade?"
2. **Game Theory**: "What happens with perfect strategic reasoning?"
3. **Neoclassical**: "What would an omniscient coordinator achieve?"

The Neoclassical track exists to show what DOESN'T happen naturally. It strengthens the emergence argument by demonstrating the unrealistic assumptions required for equilibrium.

**Implementation Note**: Always present Neoclassical results with caveats about assumptions. Show Scarf counterexamples where tatonnement fails.

---

### 3. Scope Creep: What's Actually Being Built?

**The Ambiguity**:
Documents describe wildly different scopes:
- Sometimes: 2-agent Edgeworth Box demonstrations
- Sometimes: 100-agent spatial markets
- Sometimes: Production, money, public goods, networks
- Sometimes: Just bilateral exchange

**The Confusion**: 
Is this a focused exchange economy simulator or a general-purpose economic modeling platform?

**Resolution**: 
**Define clear scope boundaries by development stage**

```
STAGE 1-4: EXCHANGE ONLY
- No production
- No money (just 2 goods)
- No public goods
- Focus: How exchange institutions affect outcomes

STAGE 5-6: COORDINATION MECHANISMS
- Add information aggregation
- Add equilibrium benchmarks
- Still exchange only
- Focus: How information affects coordination

FUTURE STAGES: EXTENSIONS
- Money emergence
- Production
- Everything else
```

**Hard Rule**: No new economic features until exchange works perfectly across all three tracks.

---

### 4. Technical Confusion: Integration vs Separation

**The Ambiguity**:
- Some documents suggest deep integration (shared Protocol→Effect→State)
- Others suggest separate tracks with different architectures
- Game Theory needs different visualization than ABM
- But they should be comparable

**The Challenge**: 
How much should tracks share vs stay independent?

**Resolution**: 
**Share data models, economic logic, and bargaining protocols; separate presentation and interaction**

```python
# SHARED (all tracks use these)
class Agent:
    """Same agents across all paradigms"""
    preferences: UtilityFunction
    inventory: Goods
    
class Trade:
    """Same trade representation"""
    participants: List[Agent]
    quantities: Dict[Good, float]

class BargainingProtocol:
    """Shared bargaining protocols work in both ABM and Game Theory"""
    def negotiate(pair, world_view) -> list[Effect]
    # Context-independent: works with or without spatial info

# TRACK-SPECIFIC (each track has its own)
class SpatialABMRenderer:
    """Pygame real-time visualization"""
    
class EdgeworthBoxRenderer:
    """Matplotlib interactive plots"""
    
class EquilibriumRenderer:
    """Time series convergence plots"""

# AGENT-BASED ONLY (require spatial context)
class SearchProtocol:
    """Spatial search protocols"""
    
class MatchingProtocol:
    """Spatial matching protocols"""
```

This ensures economic consistency and protocol compatibility while allowing optimal visualization for each paradigm. Bargaining protocols bridge the tracks, enabling theoretical understanding before spatial implementation.

---

### 5. Interface Design: Unified or Separate?

**The Ambiguity**:
- Unified launcher with three buttons?
- Completely separate applications?
- Single window with mode switching?
- Multiple windows for different tracks?

**The UX Challenge**: 
Each track needs different interaction patterns but users need coherent experience.

**Resolution**: 
**Unified launcher, track-specific windows**

```
User Flow:
1. Launch VMT → Unified launcher appears
2. Select track → Configure scenario
3. Click "Run" → Track-specific window opens
   - ABM → Pygame spatial simulation
   - Game Theory → Matplotlib interactive plots
   - Neoclassical → Convergence visualizations
4. Results accessible from all tracks for comparison
```

This provides consistency at the entry point while allowing appropriate experiences for each paradigm.

---

### 6. Protocol Confusion: Where Do They Belong?

**The Ambiguity**:
- Protocols are core to Agent-Based track
- But Game Theory also has "protocols" (bargaining solutions)
- Neoclassical has "protocols" (tatonnement rules)
- Are these the same thing?

**The Conceptual Muddle**: 
The word "protocol" means different things in different contexts, and the relationship between tracks is unclear.

**Resolution**: 
**Protocol ownership by domain: Game Theory owns matching and bargaining; Agent-Based owns search**

| Protocol Type | Agent-Based | Game Theory | Neoclassical | Ownership |
|--------------|------------|-------------|--------------|-----------|
| **Bargaining Protocols** | ✓ imports | ✓ home | - | **Game Theory** |
| **Matching Protocols** | ✓ imports | ✓ home | - | **Game Theory** |
| **Search Protocols** | ✓ home | - | - | **Agent-Based** |
| **Solution Methods** | - | ✓ | ✓ | Track-specific |

**Key Distinction**:

1. **Bargaining & Matching Protocols (Game Theory Owned)**: 
   - All implementations live in `game_theory/bargaining/` and `game_theory/matching/`
   - Agent-Based Track imports from Game Theory module
   - Examples: Nash bargaining, Split-the-difference, Gale-Shapley matching, Random matching
   - Interface: `negotiate(pair, world_view) -> effects` or `find_matches(preferences) -> effects`
   - Context-independent: Works in 2-agent Game Theory context and multi-agent spatial context
   - **Purpose**: Theoretical development in Game Theory Track; import to Agent-Based Track

2. **Search Protocols (Agent-Based Owned)**:
   - All implementations live in `agent_based/search/`
   - Game Theory Track doesn't need search (2-agent context)
   - Examples: Random walk, distance-discounted, myopic, memory-based
   - Require spatial context (grid, neighbors, movement, vision)
   - Not applicable to Game Theory Track's isolated 2-agent context

3. **Solution Methods (Track-Specific)**:
   - Game Theory: Mathematical solution concepts (contract curve, Pareto frontier)
   - Neoclassical: Equilibrium computation algorithms (tatonnement, Newton-Raphson)
   - These are calculation/analysis methods, not behavioral protocols

**Implementation Principle**: 
Develop and validate all bargaining and matching protocols in Game Theory Track. Agent-Based Track imports these protocols. This ensures theoretical clarity before observing emergent spatial behavior. See `protocol_restructure_plan.md` for detailed migration path.

---

### 7. Pedagogical Sequencing: Which Track First?

**The Ambiguity**:
- Start with simplest (Game Theory 2-agent)?
- Start with most realistic (Agent-Based)?
- Start with most familiar (Neoclassical)?

**The Pedagogical Challenge**: 
Wrong sequencing could confuse students about what's assumption vs reality.

**Resolution**: 
**Recommended teaching sequence with flexibility**

**Default Sequence** (Emergence-First):
1. Start with Agent-Based (show what happens naturally)
2. Add Game Theory (understand strategic reasoning)
3. Contrast with Neoclassical (see what perfect coordination would achieve)

**Alternative Sequence** (Theory-First):
1. Start with Neoclassical (learn standard theory)
2. Question with Agent-Based (see why reality differs)
3. Bridge with Game Theory (understand strategic foundations)

**Implementation**: Launcher includes "Guided Course" option that presents tracks in chosen sequence.

---

## Specific Document Conflicts to Resolve

### Conflict: Treatment of Bargaining

**In Agent-Based context**: Bargaining is a protocol for bilateral price determination
**In Game Theory context**: Bargaining is the entire focus with multiple solution concepts
**In documentation**: Sometimes conflated, sometimes separated, sometimes suggested as separate implementations

**Resolution**: 
- **Bargaining protocols are SHARED between Agent-Based and Game Theory tracks**
- Same protocol classes work in both contexts (context-independent design)
- Game Theory Track serves as theoretical testing ground before spatial deployment
- All bargaining protocols (simple and sophisticated) must be compatible with both tracks:
  - Simple: Split-the-difference, take-it-or-leave-it (already implemented)
  - Sophisticated: Nash, Kalai-Smorodinsky, Rubinstein (to be developed in Game Theory Track first)
- Protocols developed in Game Theory Track are directly importable to Agent-Based Track
- This enables: theoretical understanding → validation → spatial emergence observation

### Conflict: Role of Edgeworth Box

**Sometimes**: It's part of Game Theory track
**Sometimes**: It's a teaching tool for Agent-Based
**Sometimes**: It's mentioned in Neoclassical context

**Resolution**: 
Edgeworth Box is **primarily** a Game Theory track feature but can be **referenced** by other tracks:
- Game Theory: Full interactive implementation
- Agent-Based: Can show 2-agent subset in Edgeworth space
- Neoclassical: Can show equilibrium in Edgeworth coordinates

### Conflict: Market Information Mechanisms

**Original**: No central information (pure emergence)
**Proposed**: Market areas that broadcast prices
**Question**: Is this still emergent or quasi-centralized?

**Resolution**: 
Information aggregation is emergent if:
- It comes from actual trades (not calculation)
- It's spatially local (not global)
- Agents can ignore it (not mandatory)
- It has lag and noise (not perfect)

Frame as "emergent information" not "market mechanism."

---

## Documentation Cleanup Recommendations

### Consolidate Into:

1. **VISION.md** - Core philosophy and pedagogical mission (single source of truth)
2. **ARCHITECTURE.md** - Technical design across all tracks
3. **IMPLEMENTATION_GUIDE.md** - Stage-by-stage development plan
4. **CURRENT_STATE.md** - What actually exists now

### Archive:
- All "more_thinking_*.md" files (superseded by consolidated docs)
- Old phase-based plans (replaced by stage-based approach)

### Update:
- README.md to reference new consolidated documentation
- Remove references to old phase numbering system

---

## Critical Decisions Needed

### Must Decide Now:

1. **Primary audience**: Students or researchers? (Affects default mode)
2. **Development priority**: Which track after Agent-Based is solidified?
3. **Scope commitment**: Will you resist adding production/money for v1.0?

### Can Decide Later:

1. **Technology migration**: Stick with current stack or modernize?
2. **Distribution method**: Package as executable or Python environment?
3. **Community features**: Open source? User contributions?

---

## Summary

The apparent contradictions in the documentation stem from:
1. **Evolution of thinking** (not bad, just needs reconciliation)
2. **Multiple audiences** (students and researchers)
3. **Ambitious scope** (needs staging)
4. **Terminological confusion** (same words, different meanings)

The resolutions are straightforward:
1. **Dual-mode interface** (educational wrapper on research core)
2. **Equilibrium as contrast** (not replacement for emergence)
3. **Staged development** (exchange first, extensions later)
4. **Clear boundaries** (what's shared vs track-specific)
5. **Protocol compatibility** (bargaining protocols shared between tracks; search/matching ABM-only)

With these clarifications, the path forward is clear: Build a solid foundation of bilateral exchange across three complementary paradigms, each illuminating different aspects of how markets work (or don't).

---

**Next Steps**: Address the critical decisions above, then proceed with Stage 1 (Foundation Solidification) of the implementation plan.
