# VMT Strategic Roadmap

This document provides the authoritative guide for the VMT project's current status, completed achievements, and future development priorities.

---

## Current Implementation Status (2025-01-27)

### ✅ **Phase A: Foraging & Barter Economy (COMPLETE)**
**Status:** Fully implemented and production-ready

**Achievements:**
- **7-Phase Deterministic Engine** - Robust simulation loop with strict phase ordering
- **5 Utility Functions** - CES, Linear, Quadratic, Translog, Stone-Geary with full parameter support
- **Spatial Dynamics** - Vision radius, movement budgets, resource claiming, foraging mechanics
- **Bilateral Trading** - Reservation-price-based negotiation with deterministic outcomes
- **Comprehensive Testing** - 316+ tests with deterministic validation
- **PyQt6 GUI** - Scenario browser, launcher, and log viewer
- **SQLite Telemetry** - Comprehensive logging with 99% compression over CSV

### ✅ **Phase B: Money System (COMPLETE)**
**Status:** Fully implemented with P0 money-aware pairing resolved (2025-10-22)

**Achievements:**
- **Quasilinear Utility Model** - U_total = U_goods(A,B) + λ·M
- **Exchange Regimes** - `barter_only`, `money_only`, `mixed` (all trade types)
- **Heterogeneous Lambda Values** - Agent-specific money preferences for realistic trading
- **Money-Aware Pairing** - Smart matching algorithm for optimal trade selection
- **Mode Scheduling** - Temporal control with global cycle patterns
- **Money Scale Support** - Fractional prices (cents, dimes, etc.)
- **Comprehensive Integration** - All money features tested and validated

### 🔄 **Phase C: Market Mechanisms (PLANNED)**
**Status:** Next major development priority

**Planned Features:**
- **Posted-Price Markets** - Many-to-many trade with market-clearing prices
- **Local Market Detection** - Connected components for group trading
- **Supply & Demand Dynamics** - Emergent price discovery mechanisms

---

## Long-Term Vision

The VMT project aims to become a comprehensive microeconomic simulation platform that mirrors the progression of a standard graduate curriculum.

### **Educational Philosophy**
- **Visualization-First** - Interactive, simulation-driven environment for economic concepts
- **Deterministic Reproducibility** - Same seed → identical results for reliable teaching
- **Pedagogical Clarity** - Clear demonstration of canonical economic theories
- **Research Flexibility** - Tunable parameters for exploring model boundaries

### **Target Curriculum Progression**
1. **Phase A** ✅ - Foraging & Barter Economy (Complete)
2. **Phase B** ✅ - Introduction of Money (Complete)  
3. **Phase C** 🔄 - Local Market Mechanisms (Planned)
4. **Phase D** 📋 - Production Economy (Future)
5. **Phase E** 📋 - General Equilibrium & Welfare (Future)
6. **Phase F** 📋 - Advanced Topics (Future)

---

## Immediate Development Priorities

### **Priority 1: Protocol Modularization Refactor (Next 2-3 months)**

**Goal:** Refactor the monolithic `DecisionSystem` into modular protocols to support advanced market mechanisms.

**Critical Need:** The current `DecisionSystem` is monolithic and tightly coupled, making it impossible to implement the advanced market mechanisms planned for Phase C. The codebase needs significant refactoring before proceeding.

**Technical Approach:**
- **Protocol Interfaces** - Create `SearchProtocol` and `MatchingProtocol` abstractions
- **Legacy Wrappers** - Maintain existing behavior while extracting logic
- **Incremental Extraction** - Preserve telemetry and determinism throughout
- **Registry System** - Enable protocol selection via configuration

**Success Criteria:**
- [ ] All existing scenarios produce identical telemetry (bitwise identical)
- [ ] No performance regression >10%
- [ ] Protocol interfaces support multiple algorithms
- [ ] YAML configuration for protocol selection
- [ ] Comprehensive test coverage for new modules

**Implementation Phases:**
1. **Phase 1 (3-5 days)** - Interfaces + Legacy wrappers + Delegation
2. **Phase 2 (1-2 weeks)** - Extract logic into standalone implementations
3. **Phase 3 (3-4 days)** - Configuration & Registry system
4. **Phase 4 (3-5 days)** - Validation & determinism testing

### **Priority 2: Phase C Market Prototype (After Refactor)**

**Goal:** Implement the first true market mechanism in VMT - a "Local Posted-Price Auction" system.

**Prerequisites:** Protocol modularization must be completed first.

**Technical Approach:**
- **Connected Components Detection** - Identify groups of agents within interaction radius
- **Market Clearing Logic** - Aggregate bids/asks to determine clearing prices
- **Deterministic Matching** - Sort by agent ID for reproducible outcomes
- **Fallback to Bilateral** - Use existing bilateral system for small groups

**Success Criteria:**
- [ ] Market mechanism handles 5+ agent groups
- [ ] Deterministic price discovery
- [ ] Comprehensive telemetry logging
- [ ] Integration with existing bilateral system
- [ ] Performance benchmarks for large scenarios

### **Priority 3: Advanced Money Features (Future)**

**Planned Enhancements:**
- **KKT Lambda Mode** - Endogenous λ estimation from market prices
- **Mixed Liquidity Gated** - Barter fallback when money market is thin
- **Distribution Syntax** - Random inventory generation
- **Advanced Mode Scheduling** - Agent-specific and spatial zone patterns

### **Priority 4: Visualization Enhancements (Ongoing)**

**Completed:**
- ✅ **Smart Co-location Rendering** (2025-10-19) - Geometric layouts for multiple agents

**Planned:**
- **Hover Tooltips** - Mouse hover detection with agent details
- **Trade Indicators** - Animated lines showing recent trades
- **Configurable Layouts** - Toggle between visualization styles

---

## Technical Debt & Refactoring Needs

### **Critical Architecture Issues**

**Monolithic DecisionSystem:** The current `DecisionSystem` is a monolithic class that handles all decision logic in a tightly coupled manner. This creates several problems:

1. **Impossible to Extend** - Cannot add new matching algorithms without modifying core logic
2. **Testing Complexity** - Difficult to test individual components in isolation
3. **Code Duplication** - Similar logic scattered across different methods
4. **Performance Bottlenecks** - All logic runs in single thread with no optimization opportunities

**Missing Abstractions:** The codebase lacks proper protocol interfaces for:
- **Search Protocols** - How agents select forage targets
- **Matching Protocols** - How agents find and pair with trading partners
- **Trade Protocols** - How agents execute trades (future)

### **Refactoring Strategy**

**Phase 1: Protocol Interfaces**
- Create `SearchProtocol` and `MatchingProtocol` abstract base classes
- Define clear contracts for protocol behavior
- Maintain backward compatibility with legacy wrappers

**Phase 2: Logic Extraction**
- Extract existing logic into standalone protocol implementations
- Preserve all existing behavior and telemetry
- Enable multiple algorithm implementations

**Phase 3: Configuration System**
- Add protocol registry for algorithm selection
- Enable YAML configuration for protocol choice
- Maintain Python API for programmatic control

**Phase 4: Validation & Testing**
- Comprehensive regression testing
- Performance benchmarking
- Determinism validation across all scenarios

### **Benefits of Refactoring**

1. **Extensibility** - Easy to add new matching algorithms (Greedy, Stable Matching, etc.)
2. **Testability** - Individual protocols can be tested in isolation
3. **Performance** - Opportunities for optimization and parallelization
4. **Maintainability** - Clear separation of concerns and responsibilities
5. **Research** - Enable experimentation with different economic mechanisms

---

## Technical Architecture

### **Core Systems (Implemented)**
- **7-Phase Engine** - Perception, Decision, Movement, Trade, Forage, Regeneration, Housekeeping
- **Utility System** - 5 utility functions with money-aware calculations
- **Trading System** - Bilateral negotiation with money-aware pairing
- **Resource System** - Foraging, claiming, regeneration mechanics
- **Telemetry System** - SQLite logging with comprehensive data capture

### **Data Flow**
```
Scenario YAML → Schema Validation → Simulation Engine → Telemetry → Analysis
```

### **Key Design Principles**
- **Determinism First** - All operations must be reproducible
- **Modular Architecture** - Clean separation of concerns
- **Comprehensive Testing** - Every feature must be tested
- **Performance Awareness** - Scalable to large scenarios

---

## Development Guidelines

### **Code Quality Standards**
- **Type Safety** - 100% Mypy type coverage goal
- **Formatting** - Black for consistent style
- **Linting** - Ruff for code quality
- **Testing** - All new features require tests

### **Versioning Strategy**
- **No SemVer** until developer manually pushes 0.0.1 prerelease
- **Date-Based Tracking** - Use descriptive commit messages
- **Manual Release** - Developer controls all versioning

### **Testing Philosophy**
- **Deterministic Tests** - Same seed → identical results
- **Integration Tests** - End-to-end scenario validation
- **Performance Tests** - Benchmark large scenarios
- **Regression Tests** - Prevent breaking changes

---

## Research Applications

### **Current Capabilities**
- **Microeconomic Theory** - Utility maximization, gains from trade
- **Money & Banking** - Quasilinear utility, heterogeneous preferences
- **Spatial Economics** - Local interactions, transportation costs
- **Agent-Based Modeling** - Emergent behavior from individual decisions

### **Planned Research Extensions**
- **Market Microstructure** - Price discovery, liquidity dynamics
- **Behavioral Economics** - Bounded rationality, learning heuristics
- **Experimental Economics** - Controlled laboratory environments
- **Policy Analysis** - Tax systems, regulation effects

---

## Community & Documentation

### **Documentation Status**
- ✅ **Project Overview** - Complete feature overview
- ✅ **Technical Manual** - Implementation details
- ✅ **Scenario Configuration Guide** - Comprehensive parameter reference
- ✅ **Parameter Reference** - Quick lookup tables and examples
- ✅ **Type Specifications** - Type system documentation

### **User Support**
- **Demo Scenarios** - Tutorial and example scenarios
- **GUI Launcher** - Intuitive scenario browser
- **Log Viewer** - Analysis and visualization tools
- **Comprehensive Examples** - Working scenario templates

---

## Success Metrics

### **Technical Metrics**
- **Test Coverage** - 316+ tests passing
- **Performance** - Sub-second query times for telemetry
- **Determinism** - 100% reproducible simulations
- **Documentation** - Complete parameter reference

### **User Experience Metrics**
- **Ease of Use** - GUI launcher for scenario selection
- **Educational Value** - Clear demonstration of economic concepts
- **Research Utility** - Comprehensive telemetry for analysis
- **Reproducibility** - Deterministic outcomes for reliable results

---

## Next Steps

### **Immediate Actions (Next 30 days)**
1. **Protocol Modularization Planning** - Detailed technical specification for refactoring
2. **Legacy Wrapper Implementation** - Create backward-compatible protocol interfaces
3. **Regression Testing Setup** - Ensure telemetry equivalence validation
4. **Performance Baseline** - Establish benchmarks before refactoring

### **Medium-term Goals (Next 6 months)**
1. **Protocol Modularization Completion** - Full refactoring with multiple algorithms
2. **Phase C Market Prototype** - Implement posted-price market mechanisms
3. **Advanced Money Features** - KKT lambda mode, liquidity gating
4. **Research Applications** - Demonstrate advanced economic modeling

### **Long-term Vision (Next 2 years)**
1. **Production Economy** - Firm agents and factor markets
2. **General Equilibrium** - Multi-market price discovery
3. **Advanced Topics** - Game theory, asymmetric information
4. **Research Platform** - Comprehensive economic modeling toolkit

---

**Last Updated:** 2025-01-27  
**Status:** Phase A & B Complete, Protocol Modularization Required  
**Next Milestone:** Protocol Interfaces & Legacy Wrappers