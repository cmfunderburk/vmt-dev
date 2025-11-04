# VMT Unified Implementation Overview

**Document Purpose**: Synthesize the VMT vision into a coherent implementation strategy  
**Created**: November 2, 2025  
**Status**: Strategic Planning Document

---

## Executive Summary

VMT (Visualizing Microeconomic Theory) is evolving from a spatial agent-based simulation into a comprehensive pedagogical and research platform with three complementary paradigms:

1. **Agent-Based Track**: Emergent market phenomena from spatial bilateral trading
2. **Game Theory Track**: Strategic interactions with Edgeworth Box visualizations
3. **Neoclassical Track**: Equilibrium benchmarks using traditional solution methods

This document provides a unified vision and pragmatic implementation path based on current realities and pedagogical goals.

---

## Part I: Core Vision & Philosophy

### The Fundamental Premise

Markets are **institutional constructions**, not natural phenomena. VMT demonstrates how market-like behavior emerges (or fails to emerge) from micro-level interactions and institutional rules.

### The Pedagogical Innovation

Rather than teaching markets as abstract equilibria that "just exist," VMT allows students to:
- **Build** markets from individual agent interactions
- **Compare** emergent outcomes with theoretical predictions
- **Understand** why institutional details matter

### The Three Perspectives

1. **Agent-Based**: "What actually emerges from individual interactions?"
2. **Game Theory**: "How do strategic considerations shape outcomes?"
3. **Neoclassical**: "What would perfect coordination achieve?"

By implementing all three, students gain a complete understanding of when each paradigm is appropriate and what assumptions each requires.

---

## Part II: Current State Assessment

### What Exists Today

✅ **Functional Spatial ABM**
- NxN grid world with agent movement
- Bilateral trading with spatial search
- Protocol→Effect→State architecture
- Deterministic simulation engine
- SQLite telemetry system

✅ **Economic Foundations**
- Multiple utility functions (CES, Cobb-Douglas, etc.)
- Pure barter economy (2 goods)
- Resource regeneration via foraging

✅ **Basic Visualization**
- Pygame-based spatial rendering
- Real-time agent movement display

### What's Missing

❌ **Protocol Diversity**: Only one set of search/matching/bargaining rules
❌ **Multi-Track Interface**: No way to access different paradigms
❌ **Game Theory Components**: No Edgeworth Box or bargaining solutions
❌ **Equilibrium Tools**: No tatonnement or Walrasian mechanisms
❌ **Behavioral Documentation**: Unknown emergent patterns from current system

---

## Part III: Architecture Design

### System Architecture

```
VMT Platform
│
├── Core Components (Shared Across All Tracks)
│   ├── Agent Model (preferences, inventories)
│   ├── Utility Functions (CES, Cobb-Douglas, etc.)
│   ├── Trade Recording & Analysis
│   └── Random Number Management (deterministic seeds)
│
├── Shared Infrastructure (protocols/ module)
│   ├── Effect Types (Trade, Pair, Unpair, Move, etc.)
│   ├── ProtocolBase ABC
│   ├── WorldView, ProtocolContext interfaces
│   ├── ProtocolRegistry
│   └── Context builder functions
│
├── Track Implementations
│   │
│   ├── Agent-Based Track
│   │   ├── Spatial World (NxN grid)
│   │   ├── agent_based/search/ - Search Protocols
│   │   │   └── (SearchProtocol ABC + implementations)
│   │   ├── Market Information Systems
│   │   └── Pygame Visualization
│   │
│   ├── Game Theory Track
│   │   ├── game_theory/matching/ - Matching Protocols
│   │   │   └── (MatchingProtocol ABC + implementations)
│   │   ├── game_theory/bargaining/ - Bargaining Protocols
│   │   │   └── (BargainingProtocol ABC + implementations)
│   │   ├── 2-Agent Exchange Engine
│   │   ├── Feasible Set Computation
│   │   ├── Bargaining Solutions (Nash, KS, Rubinstein)
│   │   ├── Contract Curve Analysis
│   │   └── Matplotlib/Interactive Visualization
│   │
│   └── Neoclassical Track
│       ├── Excess Demand Functions
│       ├── Tatonnement Algorithm
│       ├── Equilibrium Solvers
│       ├── Stability Analysis
│       └── Convergence Visualization
│
└── User Interface Layer
    ├── Unified Launcher (PyQt6)
    ├── Track Selection Interface
    ├── Scenario Configuration
    └── Results Comparison Tools

Key Insight: Game Theory Track owns Matching and Bargaining protocols.
Agent-Based Track imports and calls them from Game Theory module.
Search protocols remain Agent-Based only (spatial context required).
```

### Design Principles

1. **Modularity**: Each track can be developed independently while sharing core components
2. **Consistency**: Protocol→Effect→State pattern applies across all paradigms
3. **Comparison**: Built-in tools to compare outcomes across tracks
4. **Extensibility**: New protocols/mechanisms can be added without architectural changes
5. **Protocol Compatibility**: Bargaining protocols must work in both Agent-Based and Game Theory tracks

### Protocol Compatibility Architecture

**Critical Requirement**: Bargaining protocols must be compatible between the Agent-Based Track and Game Theory Track. This enables:
- **Theoretical Understanding**: Users analyze protocols in simplified Game Theory context before seeing them in spatial simulations
- **Consistency**: Same bargaining logic produces comparable results in both tracks
- **Pedagogical Flow**: Students understand strategic mechanics theoretically, then observe emergent behavior spatially

**Implementation Strategy**:

**CRITICAL**: All Bargaining and Matching protocols live in `game_theory/` module. ABM imports and calls them.

1. **Domain Ownership**: 
   - `game_theory/bargaining/` owns all bargaining protocol classes
   - `game_theory/matching/` owns all matching protocol classes
   - `agent_based/search/` owns all search protocol classes

2. **Shared Protocol Core**: All bargaining and matching protocols extend base classes in `game_theory/` with context-independent interfaces:
   - Agent pair (two agent IDs)
   - Agent states (inventories, utility functions, preferences)
   - Parameters (epsilon, negotiation timeouts, etc.)
   - Random number generator (for stochastic protocols)

3. **Context Independence**: Protocols do not depend on:
   - Spatial coordinates or grid layout
   - Movement or search mechanisms
   - Other agents' locations
   - Telemetry or logging systems

4. **Game Theory Track Implementation**: Direct use of protocols in canonical home:
   - Provides simplified 2-agent context (no spatial world)
   - Directly calls `negotiate()` or `find_matches()` with minimal state
   - Visualizes results in Edgeworth Box

5. **Agent-Based Track Usage**: Imports and calls protocols from Game Theory:
   - `from vmt_engine.game_theory.bargaining import BargainingProtocol`
   - `from vmt_engine.game_theory.matching import MatchingProtocol`
   - Embeds in spatial matching/search context
   - Provides full WorldView with spatial neighbors
   - Executes as part of multi-agent 7-phase simulation

**Example Flow**:
```
Nash Bargaining Protocol Development:
  1. Implement in game_theory/bargaining/nash.py
  2. Test in Game Theory Track (2 agents, Edgeworth Box visualization)
  3. Verify theoretical properties (Pareto efficiency, symmetry)
  4. Compare with textbook solutions
  5. Import same protocol class to Agent-Based Track
  6. Observe how Nash bargaining emerges (or fails) in spatial context

Gale-Shapley Matching Development:
  1. Implement in game_theory/matching/gale_shapley.py
  2. Test stability properties theoretically
  3. Import to Agent-Based Track for spatial matching
  4. Compare stable matching vs greedy matching
```

**Protocol Interface**:
```python
class BargainingProtocol:
    """Works in both Game Theory and Agent-Based contexts"""
    
    def negotiate(
        self, 
        pair: tuple[int, int],  # Two agent IDs
        world: WorldView        # Agent states + params (spatial info optional)
    ) -> list[Effect]:          # Trade or Unpair effects
        """
        Core negotiation logic that works identically in:
        - Game Theory Track: 2 isolated agents
        - Agent-Based Track: 2 agents in spatial context
        """
        pass
```

---

## Part IV: Implementation Stages

### Stage 1: Protocol Diversification
**Purpose**: Implement alternative protocols to demonstrate institutional variety

**Deliverables**:
- Random walk search (zero-information baseline)
- Random matching (non-strategic pairing)
- Equal-split bargaining (fairness benchmark)
- Greedy surplus matching (efficiency-maximizing)
- Take-it-or-leave-it bargaining (power asymmetry)

**Success Metrics**:
- Different protocols produce measurably different outcomes
- Can demonstrate how institutions affect market efficiency

### Stage 2: Game Theory Track Development
**Purpose**: Build tools for strategic analysis in simplified settings

**Key Requirement**: The Game Theory Track serves as the **theoretical testing ground** and **canonical home** for bargaining and matching protocols before they are deployed in the Agent-Based Track. 

**IMPORTANT**: All Bargaining and Matching protocols live in the `game_theory/` module. ABM imports them from there. See `protocol_restructure_plan.md` for detailed architecture changes.

**Core Components**:
```python
class GameTheoryTrack:
    """2-agent strategic interaction analysis"""
    
    def __init__(self):
        self.exchange_engine = TwoAgentExchange()
        self.visualizer = EdgeworthBoxVisualizer()
        self.bargaining_protocols = BargainingProtocolRegistry()  # Shared with ABM
    
    def compute_contract_curve(self):
        """Find all Pareto efficient allocations"""
        
    def find_competitive_equilibrium(self):
        """Compute market-clearing prices and allocation"""
        
    def test_bargaining_protocol(self, protocol_name: str, agent_a: Agent, agent_b: Agent):
        """
        Test a bargaining protocol in isolated 2-agent context.
        
        Uses the SAME protocol classes as Agent-Based Track:
        - Import from shared bargaining protocol module
        - Create minimal WorldView (no spatial context)
        - Call protocol.negotiate() directly
        - Visualize outcome in Edgeworth Box
        
        This allows users to:
        1. Understand protocol mechanics theoretically
        2. Verify protocol properties (efficiency, fairness, etc.)
        3. Predict outcomes before spatial simulation
        4. Debug protocol logic in simplified context
        """
        protocol = self.bargaining_protocols.get(protocol_name)
        world_view = self._create_minimal_worldview(agent_a, agent_b)
        effects = protocol.negotiate((agent_a.id, agent_b.id), world_view)
        return self._analyze_effects(effects)
```

**Protocol Development Workflow**:
1. **Design Phase**: Implement bargaining logic in Game Theory Track
   - Start with 2-agent Edgeworth Box visualization
   - Test against known theoretical results
   - Verify Pareto efficiency, individual rationality, etc.

2. **Validation Phase**: Confirm protocol behavior
   - Compare with textbook solutions (Nash, Kalai-Smorodinsky, Rubinstein)
   - Test edge cases (corner solutions, no gains from trade)
   - Document economic properties

3. **Integration Phase**: Deploy to Agent-Based Track
   - Import the validated protocol class (no modifications needed)
   - Protocol automatically works in spatial context
   - Compare emergent outcomes with theoretical predictions

**Benefits**:
- **Theoretical Clarity**: Users understand protocols in simplified context first
- **Debugging**: Isolate protocol logic from spatial complexity
- **Validation**: Verify protocols match theoretical expectations
- **Pedagogy**: Bridge between abstract theory and spatial emergence

**Visualization Features**:
- Interactive Edgeworth Box with draggable allocations
- Real-time indifference curve updates
- Contract curve highlighting
- Bargaining solution overlays
- Animation from endowment to equilibrium

### Stage 3: Platform Integration
**Purpose**: Create unified interface for all tracks

**Technical Approach**:
```python
class UnifiedLauncher(QMainWindow):
    """Single entry point for all simulation paradigms"""
    
    def __init__(self):
        self.track_selector = TrackSelectionWidget()
        self.scenario_config = ScenarioConfigWidget()
        self.launch_manager = LaunchManager()
        
    def launch_simulation(self, track_type):
        if track_type == "agent_based":
            self.launch_spatial_abm()
        elif track_type == "game_theory":
            self.launch_edgeworth_box()
        elif track_type == "neoclassical":
            self.launch_equilibrium_solver()
```

**User Experience Flow**:
1. Select track (ABM, Game Theory, or Neoclassical)
2. Configure scenario parameters
3. Launch appropriate visualization
4. Compare results across paradigms

### Stage 4: Market Information Systems
**Purpose**: Add emergent price discovery to spatial ABM
> THIS NEEDS A LOT OF WORK -- general ideas are fine, but the specifics for how I get there need expanded upon to insure that the implementation respects the individual agents' information constraints and that price signals arise from natural behaviors/incentives, not from externally-imposed logic

**Key Features**:
- Spatial market area detection (clustering of trades)
- Local price signal aggregation (rolling averages)
- Information broadcasting (distance-limited)
- Market-informed bargaining protocols

**Implementation Strategy**:
- Price signals emerge from actual bilateral trades
- No central coordinator or external calculation
- Agents respond to local information only
- Compare informed vs uninformed trading outcomes

### Stage 5: Neoclassical Benchmarks
**Purpose**: Implement equilibrium methods for comparison

**Components**:
- Walrasian auctioneer mechanism
- Tatonnement price adjustment
- Newton-Raphson equilibrium solver
- Stability analysis tools
- Scarf counterexample demonstrations

**Pedagogical Frame**:
"Here's what perfect coordination would achieve—now let's compare with agent-based emergent approach"

### Stage 6: Extensions

**Potential Extensions**:
- Commodity money emergence
- Production economies -- THIS IS LIKELY TO BE THE FOCUS, BUT NEEDS AN EXPLICIT PLAN WRITTEN UP
- Network formation
- Learning and adaptation
- Large-scale simulations (1000+ agents)

---

## Part V: Technical Specifications

### Technology Stack

**Core**:
- Python 3.11+ (type hints)
- NumPy (numerical computation)
- SciPy (optimization, solvers)

**Visualization**:
- Pygame (spatial ABM)
- Matplotlib (Game Theory)
- PyQtGraph (real-time plots)

**Interface**:
- PyQt6 (launcher and GUI)
- QStackedWidget (navigation)

**Data**:
- SQLite (telemetry)
- CSV/JSON (import/export)
- YAML (scenarios)

---

## Part VI: Key Design Decisions

### Decision 1: Shared Core vs Independent Tracks

**Choice**: Shared core components with track-specific presentation

**Rationale**: 
- Ensures consistency in economic fundamentals
- Reduces code duplication
- Enables meaningful comparison across paradigms

### Decision 2: Protocol Architecture

**Choice**: Maintain Protocol→Effect→State pattern universally

**Rationale**:
- Proven architecture from current implementation
- Clear separation of concerns
- Enables hot-swapping of institutional rules

### Decision 3: Visualization Strategy

**Choice**: Track-appropriate visualization technologies

| Track | Technology | Rationale |
|-------|------------|-----------|
| Agent-Based | Pygame | Real-time spatial dynamics |
| Game Theory | Matplotlib | Interactive mathematical plots |
| Neoclassical | PyQtGraph | Time series and convergence |

### Decision 4: Educational vs Research Modes

**Choice**: Single codebase with modal interface

**Educational Mode**:
- Simplified parameter spaces
- Guided tutorials
- Progressive disclosure
- Pre-configured scenarios

**Research Mode**:
- Full parameter access
- Batch execution
- Statistical analysis
- Custom protocol development

### Decision 5: Protocol Compatibility Between Tracks

**Choice**: Bargaining protocols must be shared and compatible between Agent-Based and Game Theory tracks

**Rationale**:
- **Pedagogical Value**: Users understand protocols theoretically in Game Theory Track before seeing emergent behavior in Agent-Based Track
- **Consistency**: Same protocol logic produces comparable results in both contexts
- **Development Efficiency**: Develop and validate protocols once, use in both tracks
- **Validation**: Theoretical predictions from Game Theory Track inform expectations for Agent-Based simulations

**Implementation**:
- **Protocol Location**: All bargaining and matching protocols live in `game_theory/` module
- **ABM Usage**: Agent-Based Track imports from `game_theory.bargaining` and `game_theory.matching`
- Protocols designed with context-independent interface (agent pair + state, no spatial dependencies)
- Game Theory Track uses protocols in canonical home with minimal 2-agent context
- Agent-Based Track imports same classes for use in spatial simulation context
- Both tracks import from shared protocol registry (in `protocols/` module)

**Consequence**: 
- Search protocols remain Agent-Based only (inherently spatial)
- Matching and bargaining protocols importable by ABM from Game Theory
- Any protocol that mixes spatial and strategic logic must separate concerns

---

## Part VII: Risk Management

### Technical Risks

**Risk**: Integration complexity between tracks  
**Mitigation**: Keep tracks independent initially, share only data models

**Risk**: Theoretical errors in implementations  
**Mitigation**: Validate against textbook examples, peer review calculations

### Scope Risks

**Risk**: Feature creep beyond exchange economies  
**Mitigation**: Hard freeze on production/money until core complete

**Risk**: Attempting all tracks simultaneously  
**Mitigation**: Sequential development with working software at each stage

### User Experience Risks

**Risk**: Confusion from three different paradigms  
**Mitigation**: Clear labeling, extensive documentation, guided tutorials

**Risk**: Overwhelming complexity for students  
**Mitigation**: Progressive disclosure, start with single track

---

## Part VIII: Success Metrics

### Educational Success
- Students can explain why bilateral trading differs from equilibrium
- Students understand how institutional rules affect outcomes
- Students can predict which paradigm applies to real situations

### Technical Success
- New protocols implementable in <1 day
- Deterministic reproducibility across all modes

### Research Success
- Platform enables institutional comparison studies
- Results suitable for publication
- Community adoption for research

---

## Part IX: Near-Term Priorities

### Next 30 Days
1. Complete behavioral documentation of current system
2. Implement first alternative protocol (random walk search)
3. Prototype Edgeworth Box visualization
4. Design unified launcher interface

### Next Quarter
1. Complete protocol library (5+ alternatives)
2. Launch Game Theory track beta
3. Integrate launcher with both ABM and Game Theory
4. Begin market information design

### Next 6 Months
1. Full three-track platform operational
2. Educational materials developed
3. Research validation completed
4. Community release (v1.0)

---

## Conclusion

VMT's evolution from spatial ABM to multi-paradigm platform represents a natural maturation of the core insight: markets are institutional constructions. By providing three complementary perspectives—emergence (Agent-Based), strategy (Game Theory), and equilibrium (Neoclassical)—the platform enables deep understanding of when and why markets work (or don't).

The implementation path is pragmatic: solidify foundations, diversify protocols, add tracks sequentially, integrate carefully. Each stage produces working software that advances both pedagogical and research goals.

The key is maintaining the emergence-first philosophy while acknowledging that equilibrium models provide valuable context. The Neoclassical track doesn't undermine the emergence message—it strengthens it by showing what assumptions are required for "perfect" markets that rarely exist in reality.

---

**Next Action**: Begin Stage 1 (Foundation Solidification) by creating systematic test scenarios and documenting current system behavior.
