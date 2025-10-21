# Critical Problems Report: Architectural Coherence

**Date**: 2025-10-21  
**Focus**: Architectural Coherence (as requested)  
**Codebase Size**: ~16,000 lines of Python across engine, tools, and tests  
**Test Count**: 316+ passing tests

---

## Executive Summary

Your VMT codebase demonstrates **strong architectural discipline** overall. The 7-phase tick cycle is clearly implemented, determinism is maintained rigorously, and the money system integration was executed cleanly. However, several architectural tensions have emerged as the system has grown, primarily around:

1. **Decision phase complexity** - Mixing partner selection, pairing logic, and resource claiming
2. **System responsibility boundaries** - Trade/Decision/Matching overlap
3. **Configuration sprawl** - 20+ parameters in `ScenarioParams` with unclear orthogonality
4. **Telemetry coupling** - System logic intertwined with logging concerns

These are **not bugs** but **architectural debt** that will compound as you add features (markets, production, game theory).

---

## Critical Problem 1: Decision Phase Overload

### Severity: HIGH
### Impact: Feature Velocity, Testability, Cognitive Load

### The Problem

`src/vmt_engine/systems/decision.py` currently handles:
- Partner preference ranking (economic logic)
- Three-pass pairing algorithm (matching logic)
- Resource claiming (spatial coordination logic)
- Stale claim clearing (housekeeping logic)
- Target validation for paired agents (state management)

**This violates Single Responsibility Principle at the system level.**

### Evidence from Codebase

```python
# decision.py line ~50-150: All mixed together
def execute(self, sim):
    # Clear stale claims (housekeeping)
    self._clear_stale_claims(sim)
    
    # Build preferences (economic)
    for agent in sorted(sim.agents, key=lambda a: a.id):
        preferences = self._build_preference_list(agent, ...)
    
    # Pairing algorithm (matching)
    pass1_mutual_consent(...)
    pass2_greedy_fallback(...)
    
    # Resource claiming (spatial coordination)
    if agent.target_type == "forage":
        sim.resource_claims[pos] = agent.id
```

### Why This Matters

As you add new features:
- **Markets**: Need alternative matching algorithms (posted-price, auction, continuous double auction)
- **Production**: Need firm-worker pairing (different logic than trade pairing)
- **Strategic Behavior**: Need to swap in bounded-rationality decision rules

**Current architecture makes these extensions require modifying DecisionSystem**, which is already complex and tested extensively. This creates high-risk change zones.

### Architectural Recommendation

**Extract three separate systems:**

```
DecisionSystem (Phase 2)
  → Builds agent preference lists only
  → Economic logic: surplus calculation, distance discounting
  → Output: Each agent has ranked list of potential partners

MatchingSystem (Phase 2 - new)
  → Takes preference lists as input
  → Runs pairing algorithm (mutual consent, greedy fallback)
  → Swappable algorithms: ThreePassMatching, PostedPriceMatching, AuctionMatching
  → Output: Paired agents, forage targets

ResourceCoordinationSystem (Phase 5)
  → Handles resource claiming logic
  → Clears stale claims
  → Enforces single-harvester rule
  → Separate from agent decision-making
```

**Benefit**: Matches your existing Protocol Modularization proposal in `docs/proposals/`, which you've already deferred correctly. This confirms the architectural tension you sensed.

### Migration Path

1. **Phase 1** (Low risk): Extract `ResourceCoordinationSystem` from DecisionSystem
   - Pure refactor, no behavior change
   - Reduces DecisionSystem complexity by ~100 lines
   - Better aligns with "7 distinct phases" principle

2. **Phase 2** (Medium risk): Extract `MatchingSystem` interface
   - Keep current three-pass as `ThreePassMatchingProtocol`
   - Enables Protocol Modularization work (currently deferred per ADR-001)

3. **Phase 3** (Future): Implement alternative matching protocols
   - PostedPriceMarket, ContinuousDoubleAuction, etc.
   - Swappable via scenario configuration

---

## Critical Problem 2: Trade vs. Matching Responsibility Blur

### Severity: MEDIUM-HIGH
### Impact: Code Clarity, Testing Isolation

### The Problem

`matching.py` contains price search logic (`find_compensating_block_generic`), while `trading.py` contains both:
- Trade execution (`execute_trade`)
- Trade candidate ranking (`_rank_trade_candidates`)

**The boundary between "finding a trade" (matching) and "executing a trade" (trading) is inconsistent.**

### Evidence

```python
# matching.py: Contains price search
def find_compensating_block_generic(buyer, seller, X, Y, ...):
    # Complex multi-lot search with rounding
    # Returns (ΔX, ΔY, price) or None

# trading.py: Contains BOTH
def _rank_trade_candidates(...):
    # Sorting and tie-breaking logic
    # This is matching logic, not trading logic

def execute(self, sim):
    # Actually executes trades
    # This is trading logic
```

### Why This Matters

When you implement **markets** (Phase C in Strategic Roadmap), you'll need:
- Centralized matching (order book, market clearing)
- Decentralized matching (bilateral negotiation)

**Current split makes it unclear where market matching logic belongs.**

### Architectural Recommendation

**Clarify the conceptual boundary:**

| System | Responsibility | Pure Functions |
|--------|---------------|----------------|
| **MatchingSystem** | Find compatible pairs, rank candidates, determine best exchange pair | `find_best_trade()`, `rank_candidates()`, `compute_surplus()` |
| **TradingSystem** | Execute agreed trades, update inventories, log results, enforce cooldowns | `execute_trade()`, `update_inventories()`, `log_trade()` |

**Proposed refactor:**
1. Move `_rank_trade_candidates` from `trading.py` → `matching.py`
2. Move `find_best_trade` (generic matching) from `matching.py` → `matching.py` (it's already there, good!)
3. Make `trading.py` purely about execution: inventory updates, telemetry, cooldowns

### Migration Path

**Low-risk incremental refactor** (can do anytime):
1. Move `_rank_trade_candidates` to `matching.py` as `rank_trade_candidates()` (public)
2. Have `trading.py` call `matching.rank_trade_candidates(...)`
3. Run full test suite (should pass unchanged)
4. Future: When implementing markets, extend `matching.py` with `MarketMatchingProtocol`

---

## Critical Problem 3: Configuration Parameter Explosion

### Severity: MEDIUM
### Impact: User Experience, Validation Complexity, Future Feature Burden

### The Problem

`ScenarioParams` dataclass contains **20+ parameters** with complex interdependencies:

```python
@dataclass
class ScenarioParams:
    # Movement & perception (4)
    vision_radius, interaction_radius, move_budget_per_tick, beta
    
    # Trading (4)
    spread, dA_max, trade_cooldown_ticks, epsilon
    
    # Foraging (5)
    forage_rate, resource_growth_rate, resource_max_amount, 
    resource_regen_cooldown, enable_resource_claiming, enforce_single_harvester
    
    # Money system (8!)
    exchange_regime, money_mode, money_scale, lambda_money,
    lambda_update_rate, lambda_bounds, liquidity_gate, earn_money_enabled
```

**Money system alone added 8 parameters**, and you haven't implemented markets, production, or game theory yet.

### Evidence of Strain

From `schema.py` validation:
```python
def validate(self) -> None:
    # 30+ lines of cross-parameter validation
    if self.exchange_regime == "money_only" and M == 0:
        raise ValueError(...)
    if self.money_mode == "kkt_lambda" and self.exchange_regime == "barter_only":
        raise ValueError(...)
    # More complex conditionals...
```

**This will become unmanageable** when you add:
- Market parameters (order book depth, tick size, clearing algorithm)
- Production parameters (firm count, technology, input requirements)
- Strategic parameters (discount factors, beliefs, learning rates)

### Architectural Recommendation

**Hierarchical parameter structure:**

```python
@dataclass
class ScenarioParams:
    """Top-level params only"""
    # Spatial
    vision_radius: int = 5
    move_budget_per_tick: int = 1
    
    # Economic
    spread: float = 0.0
    beta: float = 0.95
    
    # Subsystem configs (orthogonal)
    foraging: ForagingConfig = field(default_factory=ForagingConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    money: MoneyConfig = field(default_factory=MoneyConfig)
    markets: MarketConfig = field(default_factory=MarketConfig)  # Future
    production: ProductionConfig = field(default_factory=ProductionConfig)  # Future
```

Each subsystem validates itself:
```python
@dataclass
class MoneyConfig:
    enabled: bool = False
    exchange_regime: Literal["money_only", "mixed", ...] = "mixed"
    mode: Literal["quasilinear", "kkt_lambda"] = "quasilinear"
    # ... other money params
    
    def validate(self) -> None:
        if not self.enabled:
            return  # Skip validation
        # Money-specific validation only
```

### Benefits

1. **Clarity**: Each config block is self-documenting
2. **Validation**: Subsystems validate themselves, no cross-cutting concerns
3. **YAML readability**:
```yaml
params:
  vision_radius: 5
  
  money:
    enabled: true
    exchange_regime: mixed
    mode: quasilinear
  
  markets:
    enabled: false
```
4. **Feature flags**: Each subsystem can be `enabled: false` cleanly
5. **Testing**: Mock individual configs without full scenario

### Migration Path

**Breaking change - save for v1.0 milestone:**
1. Define new hierarchy (backward compatible with defaults)
2. Update loader to accept both old flat and new nested formats
3. Deprecate flat format with migration guide
4. Remove flat format support in v2.0

**Alternative (Non-breaking)**: Live with current structure until natural refactor point (e.g., when adding markets).

---

## Critical Problem 4: Telemetry Coupling Throughout Systems

### Severity: MEDIUM
### Impact: System Testability, Performance Profiling, Future Optimization

### The Problem

Many systems directly call `sim.telemetry.log_*()` methods:
- `decision.py`: Logs pairing events, preferences
- `trading.py`: Logs trade attempts, executions
- `housekeeping.py`: Logs agent snapshots, mode changes
- `simulation.py`: Logs tick states

**This creates coupling:** You can't test a system in isolation without also providing telemetry infrastructure.

### Evidence

```python
# decision.py ~line 120
if pairing_successful:
    sim.telemetry.log_pairing_event(
        sim.tick, agent_i.id, agent_j.id, "pair", reason
    )

# trading.py ~line 80
sim.telemetry.log_trade(
    tick=sim.tick,
    buyer_id=buyer.id,
    # ... 15 more parameters
)
```

**Problem**: Testing `DecisionSystem.execute()` requires mocking `TelemetryManager` even if you only care about pairing logic.

### Why This Matters

1. **Unit Testing**: Can't test systems in true isolation
2. **Performance**: Telemetry overhead in hot loops (trade search, perception)
3. **Future Work**: If you want optional logging (e.g., "only log failures"), you need to modify each system

### Architectural Recommendation

**Event-driven telemetry via observer pattern:**

```python
# New: EventBus (lightweight)
class SimulationEventBus:
    def __init__(self):
        self.listeners = []
    
    def emit(self, event: Event):
        for listener in self.listeners:
            listener.handle(event)

# Systems emit events (no direct telemetry calls)
class DecisionSystem:
    def execute(self, sim):
        # Do work
        if pairing_successful:
            sim.events.emit(PairingEvent(
                tick=sim.tick,
                agent_i_id=agent_i.id,
                agent_j_id=agent_j.id,
                reason="mutual_consent"
            ))

# Telemetry is just another listener
class TelemetryManager:
    def handle(self, event: Event):
        if isinstance(event, PairingEvent):
            self.log_pairing(event.tick, event.agent_i_id, ...)
        elif isinstance(event, TradeEvent):
            self.log_trade(...)
```

### Benefits

1. **Testing**: Systems testable without telemetry (just don't attach listener)
2. **Performance**: Can add `NoOpEventBus` for profiling pure logic
3. **Flexibility**: Multiple listeners (e.g., telemetry + live UI updates + metrics)
4. **Clarity**: Systems focus on simulation logic, not logging format

### Migration Path

**Large refactor - save for post-v1.0:**
1. Implement `SimulationEventBus` and event types
2. Migrate one system at a time (e.g., start with DecisionSystem)
3. Keep `sim.telemetry` as fallback during migration
4. Remove direct telemetry calls once all systems migrated

**Alternative**: Document as acceptable coupling, revisit if testing pain increases.

---

## Critical Problem 5: Money System Parameter Validation is Scattered

### Severity: LOW-MEDIUM
### Impact: User Error Messages, Developer Cognitive Load

### The Problem

Money parameter validation logic is split across:
1. `schema.py`: Structural validation (types, ranges)
2. `loader.py`: Cross-field validation (exchange_regime requires M inventory)
3. `simulation.py`: Runtime checks (lambda bounds enforcement)

**Example**: A user sets `exchange_regime: "money_only"` but forgets to set `M` inventory.

**Current error flow:**
1. `schema.py` allows it (M=0 is valid)
2. `loader.py` might warn (but doesn't fail)
3. `simulation.py` initializes agents with M=0
4. **First trade fails mysteriously** with "insufficient inventory"

### Architectural Recommendation

**Fail-fast validation in loader:**

```python
def validate_money_config(config: ScenarioConfig) -> None:
    """Money-specific validation with clear error messages."""
    regime = config.params.exchange_regime
    M_inventory = config.initial_inventories.get('M', 0)
    
    if regime in ["money_only", "mixed", "mixed_liquidity_gated"]:
        if M_inventory == 0:
            raise ValueError(
                f"exchange_regime='{regime}' requires positive M inventory.\n"
                f"Add 'M: 100' to initial_inventories, or set exchange_regime to 'barter_only'."
            )
    
    if config.params.money_mode == "kkt_lambda":
        if regime == "barter_only":
            raise ValueError(
                f"money_mode='kkt_lambda' requires monetary exchange.\n"
                f"Set exchange_regime to 'money_only' or 'mixed'."
            )
    
    # More checks...
```

**Call in loader before simulation construction:**
```python
def load_scenario(path: str) -> ScenarioConfig:
    config = parse_yaml(path)
    validate_money_config(config)  # Fail here with clear message
    return config
```

### Migration Path

**Low-hanging fruit** (can do immediately):
1. Add `validate_money_config()` to `loader.py`
2. Call before returning from `load_scenario()`
3. Write test cases for each error condition
4. Update docs with common validation errors

---

## Architectural Health Summary

### Strengths 🟢

1. **7-Phase Cycle**: Clearly implemented, well-documented, strictly enforced
2. **Determinism**: Excellent adherence (sorted iteration, explicit tie-breaks)
3. **Money Integration**: Clean Phase 1-2 implementation, minimal legacy breakage
4. **Test Coverage**: 316+ tests, comprehensive integration coverage
5. **Type Safety**: Good use of dataclasses, type hints throughout
6. **Separation of Concerns**: `vmt_engine/` vs. `vmt_launcher/` vs. `telemetry/` is clean

### Areas of Concern 🟡

1. **DecisionSystem Overload**: Mixing multiple concerns (HIGH priority to address)
2. **Trade/Match Boundary**: Unclear responsibility split (MEDIUM priority)
3. **Parameter Sprawl**: Flat config structure won't scale (MEDIUM priority)
4. **Telemetry Coupling**: Direct calls throughout systems (LOW-MEDIUM priority)
5. **Money Validation**: Scattered across layers (LOW priority, easy fix)

### Red Flags 🔴

**None observed.** Your codebase does not exhibit critical architectural flaws. The concerns above are **technical debt** that will **slow feature development** but are **not blocking v1.0**.

---

## Recommendations Prioritized

### Now (Before v1.0)
1. ✅ **Extract ResourceCoordinationSystem** from DecisionSystem (low-risk refactor)
2. ✅ **Add comprehensive money validation** to loader (fail-fast with clear errors)
3. ✅ **Document Trade/Match boundary** in technical manual (no code change)

### After v1.0 (Before Markets)
4. ⏳ **Extract MatchingSystem interface** (enables Protocol Modularization per ADR-001)
5. ⏳ **Move trade ranking logic** to MatchingSystem (clarify responsibilities)

### Future (v2.0 or Later)
6. 🔮 **Hierarchical parameter structure** (breaking change, but needed for markets)
7. 🔮 **Event-driven telemetry** (large refactor, nice-to-have)

---

## Alignment with Current Plans

Your current strategic plan (ADR-001) correctly prioritizes:
1. **Complete Money Track 1** (Phases 3-4) ← Finish current features first
2. **Protocol Modularization** (6-9 weeks) ← Addresses DecisionSystem/Matching issues
3. **Advanced Features** ← Build on modular foundation

**This review supports your current sequencing.** The architectural tensions I've identified are exactly what Protocol Modularization is meant to address. Your instinct to defer it until after Money Track 1 is sound.

---

## Final Assessment

**Your architecture is solid for the current feature set.** The issues raised are:
- **Expected growth pains** for a solo-developed, evolving research platform
- **Well-contained technical debt** that doesn't threaten stability
- **Opportunities for improvement** rather than urgent problems

**You have successfully evolved from "simple barter simulation" to "comprehensive monetary economics platform" without major architectural breakage.** That's an achievement.

The main risk is **decision to proceed with markets/production before refactoring**, which would compound the issues raised above. Your ADR-001 strategy (money → modularization → advanced features) mitigates this risk.

**Verdict: Ready for v1.0 as-is. Plan refactoring before Phase C (markets).**

