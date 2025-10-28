# VMT Protocol Modularization Master Plan

**Document Status:** Active - Minimal Implementation Phase  
**Version:** 1.1  
**Created:** 2025-01-27  
**Updated:** 2025-10-26  
**Purpose:** Consolidated master plan for VMT architectural refactoring

---

## IMPLEMENTATION STATUS ✅

**Active Path:** Minimal Implementation (4 weeks)
- Infrastructure and legacy adapters only
- Full protocol system deferred for future work
- See "Minimal Implementation Path" section below

**Approved Architectural Decisions:**
- ✅ Effect Application: Immediate (not batched)
- ✅ Multi-tick State: Effect-based (InternalStateUpdate)
- ✅ Protocol Versioning: Date-based (YYYY.MM.DD format)

---

## Executive Summary

This document consolidates multiple protocol modularization proposals into a single, authoritative implementation plan for the VMT (Visualizing Microeconomic Theory) project. The core objective is to transform the monolithic `DecisionSystem` into a modular protocol architecture that supports advanced market mechanisms while preserving determinism and backward compatibility.

**Key Principle:** "Pure inputs → explicit effects" with the simulation core as the sole state mutator.

**Current Timeline:** 4 weeks for minimal implementation (infrastructure + legacy adapters)  
**Future Work:** Additional protocols can be added incrementally as research needs arise  
**Priority:** Medium - provides extensible foundation  
**Risk:** Low - incremental approach with backward compatibility

---

## Part I: Architectural Vision

### 1.1 Current State (Monolithic)

The VMT engine currently implements a 7-phase deterministic simulation loop:

```
Perception → Decision → Movement → Trade → Forage → Regeneration → Housekeeping
```

**Key Problems:**
- `DecisionSystem` is monolithic (~600 lines)
- Hard-coded three-pass pairing algorithm
- Fixed compensating block bargaining
- Cannot support alternative market mechanisms
- Difficult to test economic hypotheses comparatively

### 1.2 Target State (Protocol-Based)

Transform the 7 phases into protocol seams with strict contracts:

```python
Protocol receives: WorldView (frozen, read-only)
Protocol returns: list[Effect] (declarative intents)
Core applies: validates, executes, logs effects
```

**Each protocol represents a testable economic mechanism:**
- Search protocols (how agents find opportunities)
- Matching protocols (how agents form pairs)
- Bargaining protocols (how pairs negotiate trades)
- Movement policies (spatial navigation strategies)
- Foraging policies (resource collection rules)

### 1.3 Protocol Decomposition

| Phase | Current Implementation | Protocol Interface | Swappable Variants |
|-------|----------------------|-------------------|-------------------|
| **1. Perception** | Core service | None (pure infrastructure) | N/A |
| **2. Decision** | Monolithic DecisionSystem | `SearchProtocol` + `MatchingProtocol` | Distance-discounted, Random walk, Memory-based |
| **3. Movement** | Fixed Manhattan | `MovementPolicy` | Deterministic grid, A*, Random walk |
| **4. Trade** | Compensating blocks | `BargainingProtocol` | Take-it-or-leave-it, Rubinstein, Nash |
| **5. Forage** | Single harvester | `ForagingPolicy` | Single, Multiple, Competitive |
| **6. Regeneration** | Core mechanics | None (pure mechanics) | N/A |
| **7. Housekeeping** | Quote refresh | `HousekeepingPolicy` | Standard, KKT lambda update |

---

## Part II: Core Contracts

### 2.1 WorldView (Read-Only Context)

```python
@dataclass(frozen=True)
class WorldView:
    """Immutable snapshot provided to protocols."""
    
    # Simulation state
    tick: int
    mode: str  # "trade" | "forage" | "both"
    exchange_regime: str  # "barter_only" | "money_only" | "mixed"
    
    # Agent perspective
    agent_id: int
    pos: Position
    inventory: Inventory
    utility: UtilityFunction
    quotes: dict[str, float]
    lambda_money: float
    paired_with_id: Optional[int]
    trade_cooldowns: dict[int, int]
    
    # Local environment
    visible_agents: list[AgentView]
    visible_resources: list[ResourceView]
    
    # Global parameters
    params: dict[str, Any]
    rng_stream: RandomStream  # Seeded, deterministic
```

### 2.2 Effect Types (Declarative Intents)

```python
@dataclass
class Effect:
    """Base class for all protocol effects."""
    protocol_name: str
    tick: int

# Target selection
@dataclass
class SetTarget(Effect):
    agent_id: int
    target: Union[Position, int, ResourceID]

# Resource management
@dataclass
class ClaimResource(Effect):
    agent_id: int
    pos: Position

@dataclass
class ReleaseClaim(Effect):
    pos: Position

# Pairing
@dataclass
class Pair(Effect):
    agent_a: int
    agent_b: int
    reason: str  # "mutual_consent" | "greedy_fallback"

@dataclass
class Unpair(Effect):
    agent_a: int
    agent_b: int
    reason: str  # "trade_failed" | "timeout" | "mode_change"

# Movement
@dataclass
class Move(Effect):
    agent_id: int
    dx: int
    dy: int

# Trading
@dataclass
class Trade(Effect):
    buyer_id: int
    seller_id: int
    pair_type: str  # "A_for_B" | "A_for_M" | "B_for_M"
    dA: int
    dB: int
    dM: int
    price: float
    metadata: dict[str, Any]

# Foraging
@dataclass
class Harvest(Effect):
    agent_id: int
    pos: Position
    amount: int

# Housekeeping
@dataclass
class RefreshQuotes(Effect):
    agent_id: int

@dataclass
class SetCooldown(Effect):
    agent_a: int
    agent_b: int
    ticks: int

# Multi-tick state
@dataclass
class InternalStateUpdate(Effect):
    protocol_name: str
    agent_id: int
    key: str
    value: Any
```

### 2.3 Protocol Base Classes

```python
class ProtocolBase(ABC):
    """Base class for all protocols."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Protocol identifier."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version for telemetry."""
        pass

class SearchProtocol(ProtocolBase):
    """Protocol for agent search and target selection."""
    
    @abstractmethod
    def build_preferences(
        self, world: WorldView
    ) -> list[tuple[Target, float, dict]]:
        """Build ranked list of targets with scores."""
        pass
    
    @abstractmethod
    def select_target(
        self, world: WorldView
    ) -> list[Effect]:
        """Select target and emit effects."""
        pass

class MatchingProtocol(ProtocolBase):
    """Protocol for agent pairing."""
    
    @abstractmethod
    def find_matches(
        self, preferences: dict[int, list], world: WorldView
    ) -> list[Effect]:
        """Establish pairings from preferences."""
        pass

class BargainingProtocol(ProtocolBase):
    """Protocol for trade negotiation."""
    
    @abstractmethod
    def negotiate(
        self, pair: tuple[int, int], world: WorldView
    ) -> list[Effect]:
        """One negotiation step, may be multi-tick."""
        pass
    
    def on_timeout(
        self, pair: tuple[int, int], world: WorldView
    ) -> list[Effect]:
        """Called when negotiation exceeds max ticks."""
        return [Unpair(*pair, reason="timeout")]
```

---

## Part III: Implementation Phases

**NOTE:** The full 12-week implementation described below is the complete vision. The current approved path is the **Minimal Implementation** (Phases 0-2 only, 4 weeks), with Phases 3-6 deferred for future work as research needs arise.

---

## Minimal Implementation Path (Active - 4 Weeks)

### Overview
The approved minimal implementation includes:
1. **Week 1:** Phase 0 - Infrastructure setup
2. **Week 2:** Phase 1 - Legacy adapters
3. **Week 3:** Phase 2 - Core integration & configuration
4. **Week 4:** Testing, documentation, and cleanup

**Result:** Extensible protocol foundation with legacy behavior preserved, ready for incremental protocol additions in the future.

**Phases 3-6 (Alternative & Advanced Protocols):** Deferred until research priorities require specific new mechanisms.

---

## Full Implementation Phases (Reference)

### Phase 0: Preparation (Week 1) ✅ ACTIVE

**Goal:** Set up infrastructure without changing behavior.

**Tasks:**
1. Create `src/vmt_engine/protocols/` package
2. Define base classes and Effect types
3. Create `ProtocolContext` wrapper for WorldView
4. Add protocol fields to `Simulation.__init__`
5. Create telemetry extensions (protocol_runs table)

**Deliverables:**
- [ ] Protocol package structure created
- [ ] Base classes and effects defined
- [ ] Type checking passes (mypy)
- [ ] No behavior changes yet

### Phase 1: Legacy Adapters (Week 2) ✅ ACTIVE

**Goal:** Wrap existing logic in protocol interfaces.

**Implementation:**
```python
class LegacySearchProtocol(SearchProtocol):
    """Adapter for existing forage/search logic."""
    name = "legacy_distance_discounted"
    version = "1.0.0"
    
    def select_target(self, world: WorldView) -> list[Effect]:
        # Delegate to existing DecisionSystem._evaluate_forage_target
        # Return equivalent Effect objects
        pass

class LegacyMatchingProtocol(MatchingProtocol):
    """Three-pass pairing algorithm adapter."""
    name = "legacy_three_pass"
    version = "1.0.0"
    
    def find_matches(self, preferences, world) -> list[Effect]:
        # Implement Pass 2 (mutual consent)
        # Implement Pass 3 (greedy fallback)
        # Return Pair effects
        pass

class LegacyBargainingProtocol(BargainingProtocol):
    """Compensating block bargaining adapter."""
    name = "legacy_compensating_block"
    version = "1.0.0"
    
    def negotiate(self, pair, world) -> list[Effect]:
        # Call existing find_compensating_block_generic
        # Return Trade or Unpair effects
        pass
```

**Deliverables:**
- [ ] Legacy adapters implemented
- [ ] DecisionSystem delegates to protocols
- [ ] Telemetry identical (bit-for-bit)
- [ ] All 316+ tests pass

### Phase 2: Core Integration (Week 3) ✅ ACTIVE

**Goal:** Engine applies effects instead of direct mutation.

**Tasks:**
1. Modify `Simulation.tick()` to collect effects
2. Implement effect validation and application
3. Add conflict resolution (deterministic)
4. Update telemetry to log protocol versions

**Effect Application Order:**
```python
def apply_effects(self, effects: list[Effect]) -> None:
    """Apply effects in deterministic order."""
    
    # Group by type
    unpairs = [e for e in effects if isinstance(e, Unpair)]
    pairs = [e for e in effects if isinstance(e, Pair)]
    trades = [e for e in effects if isinstance(e, Trade)]
    moves = [e for e in effects if isinstance(e, Move)]
    
    # Apply in fixed order
    for unpair in sorted(unpairs, key=lambda e: (e.agent_a, e.agent_b)):
        self._apply_unpair(unpair)
    
    for pair in sorted(pairs, key=lambda e: (e.agent_a, e.agent_b)):
        if self._is_valid_pair(pair):
            self._apply_pair(pair)
    
    # ... etc for all effect types
```

**Deliverables:**
- [ ] Effect system integrated
- [ ] Deterministic application order
- [ ] Conflict resolution tested
- [ ] Performance within 10% of baseline

### Phase 3: Alternative Protocols (DEFERRED)

**Status:** Not included in minimal implementation - deferred for future work.

**Goal:** Implement first non-legacy protocols.

**3.1 Greedy Matching**
```python
class GreedyMatching(MatchingProtocol):
    """Pure welfare maximization without mutual consent."""
    name = "greedy_surplus"
    version = "1.0.0"
    
    def find_matches(self, preferences, world) -> list[Effect]:
        # Collect all possible pairs
        # Sort by total surplus
        # Greedily assign (first-come, first-served)
        pass
```

**3.2 Take-It-Or-Leave-It Bargaining**
```python
class TakeItOrLeaveIt(BargainingProtocol):
    """Monopolistic offer with single response."""
    name = "take_it_or_leave_it"
    version = "1.0.0"
    
    def negotiate(self, pair, world) -> list[Effect]:
        # Seller makes monopoly offer
        # Buyer accepts or rejects
        # Single-tick resolution
        pass
```

**3.3 Random Walk Search**
```python
class RandomWalkSearch(SearchProtocol):
    """Stochastic exploration for pedagogical scenarios."""
    name = "random_walk"
    version = "1.0.0"
    
    def select_target(self, world) -> list[Effect]:
        # Random direction selection
        # Uses world.rng_stream for determinism
        pass
```

**Deliverables:**
- [ ] Three alternative protocols implemented
- [ ] Property-based tests for each
- [ ] Comparative scenarios created
- [ ] Performance benchmarked

### Phase 4: Configuration System (Week 3) ✅ INCLUDED IN MINIMAL

**Goal:** YAML-based protocol selection.

**Note:** Basic configuration system included in minimal implementation (Week 3) to support legacy protocol selection and future extensibility.

**4.1 Protocol Registry**
```python
class ProtocolRegistry:
    """Central registry for protocol implementations."""
    
    _registry: dict[str, type[ProtocolBase]] = {}
    
    @classmethod
    def register(cls, protocol_class: type[ProtocolBase]) -> None:
        key = f"{protocol_class.name}@{protocol_class.version}"
        cls._registry[key] = protocol_class
    
    @classmethod
    def get(cls, name: str, version: str = "latest") -> ProtocolBase:
        # Resolve and instantiate protocol
        pass
```

**4.2 Scenario Schema Extension**
```yaml
protocols:
  search:
    name: "distance_discounted"
    version: "1.0.0"
    params:
      beta: 0.95
      vision_policy: "circle"
  
  matching:
    name: "greedy_surplus"
    version: "1.0.0"
  
  bargaining:
    name: "take_it_or_leave_it"
    version: "1.0.0"
    params:
      seller_power: 0.7
```

**Deliverables:**
- [ ] Registry implemented
- [ ] Schema updated
- [ ] CLI supports protocol override
- [ ] GUI dropdown for protocol selection

### Phase 5: Advanced Protocols (DEFERRED)

**Status:** Not included in minimal implementation - deferred for future work.

**Goal:** Implement economically sophisticated protocols.

**5.1 Rubinstein Bargaining (Multi-tick)**
```python
class RubinsteinBargaining(BargainingProtocol):
    """Alternating offers with discounting."""
    name = "rubinstein_alternating"
    version = "1.0.0"
    
    def negotiate(self, pair, world) -> list[Effect]:
        # Check internal state for round number
        # Alternate proposer/responder
        # Apply discount factor
        # Multi-tick resolution
        pass
```

**5.2 Memory-Based Search**
```python
class MemorySearch(SearchProtocol):
    """Agents remember profitable locations."""
    name = "memory_based"
    version = "1.0.0"
    
    def select_target(self, world) -> list[Effect]:
        # Maintain price map in InternalStateUpdate
        # Exploit vs explore trade-off
        # Spatial learning
        pass
```

**5.3 Stable Matching (Gale-Shapley)**
```python
class StableMatching(MatchingProtocol):
    """Deferred acceptance for stability."""
    name = "gale_shapley"
    version = "1.0.0"
    
    def find_matches(self, preferences, world) -> list[Effect]:
        # Men propose, women reject/accept
        # Guaranteed stable matching
        # For static pedagogical scenarios
        pass
```

**Deliverables:**
- [ ] Three advanced protocols
- [ ] Multi-tick state management tested
- [ ] Economic properties verified
- [ ] Documentation complete

### Phase 6: Cleanup and Optimization (Week 4) ✅ INCLUDED IN MINIMAL

**Goal:** Testing, documentation, and verification.

**Note:** In minimal implementation, this phase focuses on verification that legacy behavior is preserved, not on removing legacy code (which will remain as the primary implementation).

**Tasks:**
1. Remove inlined logic from DecisionSystem
2. Profile and optimize hot paths
3. Complete documentation
4. Create migration guide

**Deliverables:**
- [ ] Legacy code removed
- [ ] Performance meets targets
- [ ] Documentation complete
- [ ] All tests green

---

## Part IV: Testing Strategy

### 4.1 Regression Testing

**Golden Standard Tests:**
```python
def test_legacy_protocols_preserve_behavior():
    """Legacy adapters produce identical telemetry."""
    
    # Run scenario with old engine
    old_telemetry = run_old_engine(scenario, seed=42)
    
    # Run with legacy protocols
    new_telemetry = run_with_protocols(
        scenario, seed=42,
        search="legacy_distance_discounted",
        matching="legacy_three_pass",
        bargaining="legacy_compensating_block"
    )
    
    # Assert telemetry identical
    assert_telemetry_equal(old_telemetry, new_telemetry, epsilon=1e-10)
```

### 4.2 Protocol Property Tests

```python
def test_matching_protocol_properties(matching_protocol):
    """All matching protocols satisfy core properties."""
    
    # No agent in multiple pairs
    assert no_double_pairing(matching_protocol.find_matches(...))
    
    # Pairs are bidirectional
    assert pairs_are_mutual(matching_protocol.find_matches(...))
    
    # Deterministic with same input
    assert is_deterministic(matching_protocol.find_matches)
```

### 4.3 Economic Validation

```python
def test_bargaining_surplus_positive():
    """All bargaining protocols ensure positive surplus."""
    
    for protocol in all_bargaining_protocols:
        trades = protocol.negotiate(pair, world)
        for trade in trades:
            assert compute_surplus(trade) > 0
```

### 4.4 Performance Benchmarks

| Scenario | Agents | Legacy (TPS) | With Protocols (TPS) | Regression |
|----------|--------|--------------|---------------------|------------|
| three_agent_barter | 3 | 485 | 465 | 4.1% |
| mixed_regime | 20 | 125 | 118 | 5.6% |
| large_100_agents | 100 | 12.3 | 11.8 | 4.1% |

**Target:** < 10% performance regression

---

## Part V: Risk Mitigation

### 5.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hidden coupling in DecisionSystem | High | High | Phase 1 uses delegation, preserves behavior |
| Telemetry drift | Medium | High | Automated diff tool, regression tests |
| Performance regression | Medium | Medium | Profile hot paths, optimize effect application |
| Circular dependencies | Low | Medium | Careful module design, test imports early |
| Multi-tick state corruption | Medium | High | Immutable WorldView, explicit state updates |

### 5.2 Process Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep | High | Medium | Fixed phase deliverables, time-boxed |
| Merge conflicts | Medium | Low | Feature branch, announce freeze period |
| Breaking existing experiments | Low | High | Backward compatibility, legacy adapters |

---

## Part VI: Success Criteria

### Phase 1 Success (Legacy Adapters)
- [ ] All 316+ tests pass without modification
- [ ] Telemetry bit-identical for legacy protocols
- [ ] Performance regression < 10%
- [ ] No changes to existing imports

### Phase 3 Success (Alternative Protocols)
- [ ] Three new protocols implemented
- [ ] Each protocol has >90% test coverage
- [ ] Comparative scenarios demonstrate differences
- [ ] Documentation explains economic properties

### Final Success (Complete System)
- [ ] Protocol registry operational
- [ ] YAML configuration working
- [ ] GUI protocol selection functional
- [ ] 5+ protocols per category available
- [ ] Developer can add new protocol in <1 hour
- [ ] All economic properties documented
- [ ] Performance meets pedagogical requirements

---

## Part VII: Documentation Requirements

### 7.1 Technical Documentation
- Update `docs/2_technical_manual.md` with protocol system
- Create `docs/protocol_implementation_guide.md`
- Add protocol interface reference
- Document effect application order

### 7.2 Economic Documentation
- Mathematical properties per protocol
- Comparative analysis guide
- References to economic literature
- Pedagogical use cases

### 7.3 Developer Documentation
- "Adding a New Protocol" tutorial
- Protocol template files
- Testing requirements
- Performance guidelines

---

## Appendix A: File Structure

```
src/vmt_engine/
├── protocols/
│   ├── __init__.py
│   ├── base.py              # ProtocolBase, Effect types
│   ├── context.py           # WorldView
│   ├── registry.py          # Protocol registry
│   │
│   ├── search/
│   │   ├── __init__.py
│   │   ├── legacy.py        # Legacy adapter
│   │   ├── distance.py      # Distance-discounted
│   │   ├── random.py        # Random walk
│   │   └── memory.py        # Memory-based
│   │
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── legacy.py        # Three-pass
│   │   ├── greedy.py        # Greedy surplus
│   │   └── stable.py        # Gale-Shapley
│   │
│   └── bargaining/
│       ├── __init__.py
│       ├── legacy.py        # Compensating blocks
│       ├── monopoly.py      # Take-it-or-leave-it
│       ├── rubinstein.py    # Alternating offers
│       └── nash.py          # Nash bargaining
```

---

## Appendix B: Decision Points ✅ RESOLVED

**All architectural decisions have been made:**

### 1. Effect Application Strategy ✅ RESOLVED

**Decision:** Option A - Immediate Application

- Effects applied as generated within each phase
- Simpler to implement
- Easier debugging

**Rationale:** Lower complexity for minimal implementation, can refactor to batch application in future if needed.

### 2. Multi-tick State Storage ✅ RESOLVED

**Decision:** Option A - Effect-based State (InternalStateUpdate)

- State stored via effects in telemetry
- Full audit trail
- Reproducible

**Rationale:** Aligns with VMT's determinism requirements and telemetry-first philosophy.

### 3. Protocol Versioning ✅ RESOLVED

**Decision:** Option B - Date-based Versioning

- YYYY.MM.DD format
- Simpler for research
- Matches current VMT practice

**Rationale:** Consistency with VMT project standards, simpler for research reproducibility.

---

## Appendix C: Timeline Summary

### Active Timeline (Minimal Implementation - 4 Weeks)

| Week | Phase | Key Deliverables | Status |
|------|-------|-----------------|--------|
| 1 | Phase 0: Preparation | Infrastructure setup | ✅ Approved |
| 2 | Phase 1: Legacy Adapters | Behavior preservation | ✅ Approved |
| 3 | Phase 2: Core Integration + Config | Effect system & YAML support | ✅ Approved |
| 4 | Phase 6: Testing & Docs | Verification & documentation | ✅ Approved |

**Total Duration:** 4 weeks (1 month)

### Future Work (Deferred)

Additional protocols (Phases 3 & 5) can be added incrementally as research needs arise:
- Alternative matching protocols (greedy, stable matching)
- Alternative bargaining protocols (take-it-or-leave-it, Rubinstein, Nash)
- Advanced search protocols (memory-based, random walk)

---

**Document Status:** Approved for minimal implementation - ready to proceed  
**Next Steps:** Begin Phase 0 (infrastructure setup) after utility base extraction  
**Timeline:** 4 weeks to extensible foundation
