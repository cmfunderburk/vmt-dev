# LLM Expansion on new_vision_nov_1.md + cursor chat context
# Created Nov 1 @ 19:30 -- Starting review @ 20:00
# Modular GUI Entrypoint Design: Planning Document

**Date**: November 1, 2025  
**Status**: Planning Phase - Design Discussion  
**Context**: Extending VMT launcher for modular pedagogical applications  
**Related**: [Vision and Architecture](vision_and_architecture.md), [Project Overview](../1_project_overview.md)

---

## Executive Summary

This document plans the architectural redesign of VMT's GUI entrypoint from a single-purpose scenario launcher to a modular hub supporting multiple pedagogical simulation types: Agent-Based simulations (current spatial barter system), Game Theory demonstrations (Edgeworth Box, bargaining protocols), and Standard Neoclassical models (Walrasian auctioneer, equilibrium mechanisms).

**Core Goal**: Create an extensible launcher architecture that cleanly separates different simulation paradigms while maintaining code reuse and a consistent user experience.

---

## Motivation: Why This Matters

### Current Limitation

The existing `LauncherWindow` directly launches spatial agent-based simulations via `main.py`. This works well for the core VMT research agenda (emergent markets from bilateral trading) but creates a conceptual barrier when introducing pedagogically different simulation types:

1. **Game Theory Demonstrations**: Edgeworth Box visualizations, 2-agent bargaining protocols, contract curves—these need specialized interfaces that show utility functions, indifference curves, and trade paths in preference space, not just spatial movement.

2. **Standard Neoclassical Models**: Walrasian auctioneer, tatonnement, competitive equilibrium—these demonstrate price-taking behavior and equilibrium convergence using completely different visualization paradigms (price-quantity graphs, excess demand, convergence plots).

3. **Future Extensions**: Production economies, public goods, network formation, asymmetric information—each may require domain-specific interfaces.

### Pedagogical Alignment

This design aligns with VMT's core pedagogical mission (as articulated in [vision_and_architecture.md](vision_and_architecture.md)):

> **"VMT inverts the pedagogical sequence by asking: Under what institutional conditions do market-like phenomena actually emerge from micro-level interactions?"**

The modular entrypoint enables students to:
- **Compare paradigms**: See both emergent bilateral trading (Agent-Based) and imposed equilibrium mechanisms (Neoclassical) side-by-side
- **Bridge theory**: Move from Game Theory foundations (Edgeworth Box) to spatial agent-based emergence
- **Understand tradeoffs**: When do markets emerge vs when must equilibrium be calculated?

This modular structure makes VMT a **comprehensive pedagogical platform** rather than just an agent-based research tool.

---

## Current Architecture Analysis

### Existing Launcher Structure

```python
# Current: src/vmt_launcher/launcher.py
class LauncherWindow(QMainWindow):
    - Scenario list (recursive YAML discovery)
    - Seed input
    - "Run Simulation" button
    - Launches: subprocess.Popen(["python", "main.py", scenario, "--seed", seed])
```

**Strengths**:
- Clean separation: launcher vs simulation execution
- Recursive scenario discovery (`scenarios/**/*.yaml`)
- Deterministic seed management
- Simple, focused UI

**Limitations**:
- Tightly coupled to spatial agent-based simulation paradigm
- No extensibility for different simulation types
- Single launch mechanism (subprocess to `main.py`)
- No conceptual hierarchy (all scenarios treated equally)

### Simulation Launch Chain

Current flow:
```
launcher.py → LauncherWindow → subprocess → main.py → Simulation → pygame renderer
```

**Observation**: The launch chain assumes a specific simulation type. Other simulation types (Game Theory, Neoclassical) will likely need:
- Different entry points (not `main.py`)
- Different visualization backends (not just pygame)
- Different configuration formats (may share YAML, but different schema)
- Different interaction models (static Edgeworth Box vs animated spatial movement)

---

## Design Requirements

### Functional Requirements

1. **Top-Level Menu**: Three primary buttons (Agent-Based, Game Theory, Standard Neoclassical)
2. **Stacked Widget Navigation**: Use QStackedWidget for clean hierarchical navigation with back button
3. **Agent-Based Path**: Preserve existing functionality (scenario selection → launch)
4. **Game Theory Path**: New interface starting with "Bargaining Protocols" button (future: other game theory modules)
5. **Neoclassical Path**: New interface with "Walrasian Auctioneer" option (future: other equilibrium mechanisms)
6. **Extensibility**: Easy to add new simulation types or sub-modules

### Non-Functional Requirements

1. **Backward Compatibility**: Existing workflow (launch → select scenario → run) should remain unchanged
2. **Code Reuse**: Common components (seed input, scenario browsing) should be shareable
3. **Clean Separation**: Each simulation type should be independently implementable
4. **Consistent UX**: Similar interaction patterns across different simulation types
5. **Deterministic**: Seed management should work across all simulation types

---

## Proposed Architecture

### High-Level Structure

```
MainMenuWindow (QStackedWidget)
  ├─ Stack 0: Main Menu (3 buttons)
  ├─ Stack 1: Agent-Based Window
  │   └─ Scenario selection (current LauncherWindow refactored)
  ├─ Stack 2: Game Theory Menu
  │   ├─ "Bargaining Protocols" button
  │   └─ Future: Other game theory modules
  ├─ Stack 3: Bargaining Protocols Window
  │   ├─ Scenario/config selection
  │   └─ Launch Edgeworth Box visualization
  └─ Stack 4: Neoclassical Menu
      ├─ "Walrasian Auctioneer" button
      └─ Future: Other equilibrium mechanisms
```

### Component Design

#### 1. MainMenuWindow (New Top-Level)

**Responsibilities**:
- Display three primary buttons
- Manage QStackedWidget navigation
- Provide "back" button functionality
- Set window title and styling

**Design Decisions**:
- **Stacked Widgets**: Cleaner than modal windows; allows navigation history if needed
- **Back Button**: Appears when depth > 0, hides on main menu
- **Consistent Styling**: Bold buttons, clear labels, optional descriptions

#### 2. AgentBasedWindow (Refactored from LauncherWindow)

**Responsibilities**:
- Scenario file discovery (`find_scenario_files()`)
- Scenario list display
- Seed input
- Launch via `main.py` subprocess

**Changes from Current**:
- Inherits from `QWidget` instead of `QMainWindow` (becomes a stack page)
- Removes window management (handled by MainMenuWindow)
- Keeps all current functionality

**Launch Mechanism**: Unchanged—`subprocess.Popen([sys.executable, "main.py", scenario, "--seed", seed])`

#### 3. GameTheoryMenu (New)

**Responsibilities**:
- Display sub-module buttons (initially just "Bargaining Protocols")
- Navigate to specific game theory interfaces

**Design**:
- Simple button layout (vertical buttons)
- Placeholder structure for future modules (Nash equilibrium, Prisoner's Dilemma, etc.)
- Each button navigates to a specialized window

**Pedagogical Foundation**:
- Content aligned with **David Kreps' Microeconomic Foundations II** and **Osborne & Rubinstein's A Course in Game Theory**
- Modules will cover strategic interaction, equilibrium concepts, and mechanism design as presented in these texts
- Starting with bargaining protocols provides foundation for understanding strategic behavior before expanding to more complex game-theoretic concepts

#### 4. BargainingProtocolsWindow (New)

**Responsibilities**:
- Configuration for 2-agent (small N) bargaining scenarios
- Selection of bargaining protocol
- Launch Edgeworth Box visualization

**Design Considerations**:
- **Scenario Format**: May share YAML structure but need specialized fields (e.g., explicit 2-agent constraint, visualization options)
- **Protocol Selection**: Dropdown or radio buttons (competitive equilibrium, split difference, etc.)
- **Launch Target**: New entry point (e.g., `game_theory/bargaining_viewer.py`) instead of `main.py`

**Future Visualization Needs**:
- Edgeworth Box with indifference curves
- Trade path animation
- Contract curve overlay
- Utility function plots
- This likely requires a different rendering backend (PyQt6 for static/interactive plots, not pygame for spatial animation)

#### 5. NeoclassicalMenu (New)

**Responsibilities**:
- Display equilibrium model options (initially "Walrasian Auctioneer")
- Navigate to specialized interfaces

**Design**:
- Similar to GameTheoryMenu structure
- Placeholder for future models (tatonnement, Arrow-Debreu, etc.)

**Pedagogical Foundation**:
- Content aligned with **Jehle & Reny's Advanced Microeconomic Theory** and **David Kreps' Microeconomic Foundations I**
- Modules will demonstrate standard neoclassical models (competitive equilibrium, general equilibrium, welfare theorems) as presented in these texts
- Provides contrast with emergent agent-based markets, showing when equilibrium-first modeling is appropriate

#### 6. WalrasianAuctioneerWindow (Future - Not in Initial Scope)

**Responsibilities**:
- Configure agent preferences and endowments
- Select auctioneer algorithm
- Launch equilibrium visualization (price adjustment, excess demand, convergence)

**Design Considerations**:
- **Completely Different Paradigm**: No spatial search, no bilateral matching—just price-taking agents responding to market prices
- **Visualization**: Price-quantity graphs, excess demand curves, tatonnement trajectories
- **Purpose**: Contrast with emergent markets (demonstrate when equilibrium must be imposed vs when it emerges)

---

## Design Questions and Decisions

### Q1: Window Management - Stacked Widgets vs Separate Windows

**Decision**: Stacked widgets with back button navigation

**Rationale**:
- Cleaner UX: Single window, no window clutter
- Navigation history: Can track depth and provide "back" functionality
- Easier state management: All widgets share same application context
- PyQt6 best practice: QStackedWidget is designed for this pattern

**Alternative Considered**: Separate windows (Option C)
- **Rejected**: Creates window management complexity, harder to provide consistent styling/theming

### Q2: Shared Components - Where to Factor Common Code?

**Decision**: Create utility classes/modules for shared functionality

**Proposed Structure**:
```python
# src/vmt_launcher/common.py (new)
class SeedInputWidget(QWidget):
    """Reusable seed input component."""
    - QLineEdit with validation
    - Standardized styling
    - Signal: seed_changed(int)

class ScenarioBrowserWidget(QWidget):
    """Reusable scenario browsing/list component."""
    - QListWidget with recursive file discovery
    - Standardized display format
    - Signal: scenario_selected(str path)
```

**Benefits**:
- Consistent seed handling across all simulation types
- Scenario browsing can be reused (Game Theory may want to share scenario directory structure)
- Easier testing (isolated components)

### Q3: Launch Mechanism Abstraction

**Question**: Should we create a common interface for launching simulations?

**Initial Decision**: Not in first iteration—keep launch mechanisms specific to each window type

**Rationale**:
- Agent-Based: subprocess to `main.py` (works, don't change it)
- Game Theory: will likely need new entry point (e.g., `game_theory/launch_bargaining.py`)
- Neoclassical: will likely need different entry point
- Each may have different parameter passing needs

**Future Consideration**: If launch mechanisms converge (e.g., all use subprocess with config dict), we could abstract later.

**Alternative Considered**: Abstract base class for simulation launchers
- **Deferred**: YAGNI—wait until we have 2+ concrete implementations to see common patterns

### Q4: Scenario File Organization

**Question**: Should Game Theory scenarios live in separate directory structure?

**Initial Decision**: Share `scenarios/` directory but use subdirectories:
```
scenarios/
  ├─ curated/          # Agent-based scenarios
  ├─ demos/            # Agent-based demos
  ├─ game_theory/     # Future: Game theory scenarios
  │   └─ bargaining/   # Edgeworth Box configs
  └─ neoclassical/     # Future: Equilibrium model configs
```

**Rationale**:
- Maintains current structure (backward compatible)
- Clear separation for different paradigms
- Scenario discovery can filter by type if needed
- Flexible for future extensions

**Alternative Considered**: Completely separate directories
- **Rejected**: Unnecessary fragmentation; subdirectories provide sufficient organization

### Q5: Configuration Format Consistency

**Question**: Should Game Theory and Neoclassical simulations use same YAML schema?

**Initial Decision**: Shared base structure, type-specific extensions

**Rationale**:
- Core elements (agents, utilities, initial inventories) are common
- Visualization parameters differ (spatial grid vs Edgeworth Box dimensions)
- Protocol selection differs (search/matching/bargaining vs equilibrium algorithm)
- Can use schema versioning or `simulation_type` field to differentiate

**Implementation Strategy**:
- Extend current schema with optional fields
- Validation: require type-specific fields based on `simulation_type`
- Backward compatible: existing agent-based scenarios work unchanged

---

## Implementation Plan (Conceptual - Not Yet Approved)

### Phase 1: Refactoring and Foundation

**Step 1.1**: Extract `LauncherWindow` functionality into `AgentBasedWindow`
- Create new `AgentBasedWindow(QWidget)` class
- Move scenario discovery, seed input, launch logic
- Remove window management (QMainWindow → QWidget)
- Test: Existing workflow still works

**Step 1.2**: Create `MainMenuWindow`
- QStackedWidget setup
- Three primary buttons
- Navigation to AgentBasedWindow
- Back button (initially hidden, appears when navigating)
- Test: Main menu → Agent-Based → launch simulation works

**Step 1.3**: Extract shared components
- Create `common.py` with `SeedInputWidget`, `ScenarioBrowserWidget`
- Refactor `AgentBasedWindow` to use shared components
- Test: No functionality regression

### Phase 2: Game Theory Infrastructure

**Step 2.1**: Create `GameTheoryMenu`
- Stack page with "Bargaining Protocols" button
- Navigation structure
- Placeholder for future modules

**Step 2.2**: Create `BargainingProtocolsWindow`
- Configuration interface for 2-agent scenarios
- Protocol selection (dropdown/radio buttons)
- Seed input (using shared component)
- Launch button (initially placeholder or calls not-yet-implemented viewer)

**Note**: This phase does NOT implement the Edgeworth Box visualization—just the launcher interface. Visualization implementation is separate project.

### Phase 3: Neoclassical Infrastructure (Future)

**Step 3.1**: Create `NeoclassicalMenu`
- Similar structure to GameTheoryMenu
- "Walrasian Auctioneer" button

**Step 3.2**: Create `WalrasianAuctioneerWindow` (placeholder)
- Configuration interface
- Launch mechanism (to be implemented when visualization is ready)

**Note**: This is explicitly future work; not blocking initial implementation.

---

## Code Structure Proposal

### File Organization

```
src/vmt_launcher/
  ├─ __init__.py
  ├─ main_menu.py              # NEW: MainMenuWindow (top-level)
  ├─ agent_based_window.py     # REFACTORED: Current LauncherWindow
  ├─ game_theory_menu.py       # NEW: Game Theory submenu
  ├─ bargaining_window.py      # NEW: Bargaining Protocols config
  ├─ neoclassical_menu.py      # NEW: Neoclassical submenu (future)
  ├─ common.py                 # NEW: Shared widgets (SeedInput, etc.)
  └─ launcher.py               # DEPRECATED: Keep for backward compat or remove
```

**Backward Compatibility Strategy**:
- `launcher.py` can import and wrap `MainMenuWindow` for existing entry point
- Or update `launcher.py` to directly instantiate `MainMenuWindow`
- Existing `python launcher.py` command should still work

### Class Hierarchy

```python
# Main entry point
class MainMenuWindow(QMainWindow):
    - stacked_widget: QStackedWidget
    - back_button: QPushButton (conditional visibility)
    - Methods: navigate_to(stack_index), navigate_back()

# Agent-Based path (refactored)
class AgentBasedWindow(QWidget):
    - scenario_list: QListWidget
    - seed_input: SeedInputWidget
    - run_button: QPushButton
    - Methods: launch_simulation()

# Game Theory path
class GameTheoryMenu(QWidget):
    - bargaining_button: QPushButton
    - Methods: navigate_to_bargaining()

class BargainingProtocolsWindow(QWidget):
    - config_widgets (protocol selection, scenario/config)
    - seed_input: SeedInputWidget
    - launch_button: QPushButton
    - Methods: launch_bargaining_viewer()

# Shared components
class SeedInputWidget(QWidget):
    - seed_edit: QLineEdit
    - Signal: seed_changed(int)
    - Methods: get_seed() -> int, validate() -> bool

class ScenarioBrowserWidget(QWidget):
    - scenario_list: QListWidget
    - Signal: scenario_selected(str)
    - Methods: refresh_scenarios(), get_selected() -> Optional[str]
```

---

## UI/UX Design Considerations

### Visual Hierarchy

**Main Menu**:
- Three large, centered buttons (equal size)
- Optional: Subtle descriptions under each button
- Clean, minimal styling (no scenario list clutter)
- Window title: "VMT Simulation Launcher" or "VMT Pedagogical Platform"

**Navigation Pattern**:
- Back button (top-left or bottom) when depth > 0
- Clear breadcrumb or title indicating current section
- Consistent button styling across all windows

**Agent-Based Window**:
- Preserve current layout (scenario list + seed + run button)
- Add breadcrumb or title: "Agent-Based Simulation > Scenario Selection"

**Game Theory Windows**:
- Similar layout patterns for consistency
- Clear labeling of current module (e.g., "Game Theory > Bargaining Protocols")

### Styling Consistency

**Proposed Standardization**:
- Primary action buttons: Bold, padding, distinct color
- Secondary buttons (back): Standard styling, less prominent
- Input fields: Consistent validation feedback
- Lists: Standard selection highlighting
- Status labels: Color-coded (gray=ready, blue=selected, green=success, red=error)

---

## Edge Cases and Error Handling

### Scenario Discovery Failures

**Current Behavior**: Shows "No scenarios found" message

**New Context**: Each window type may look in different directories

**Solution**: Window-specific scenario discovery functions that handle empty directories gracefully

### Launch Failures

**Current Behavior**: Shows error message box

**Future Considerations**:
- Different simulation types may have different failure modes
- Some may need more detailed error reporting (e.g., config validation errors)
- Consider standardized error handling with type-specific messages

### Navigation State

**Question**: What happens if user closes main menu window?

**Decision**: Application quits (maintain current behavior via `setQuitOnLastWindowClosed(True)`)

**Question**: Can user launch multiple simulations simultaneously?

**Current Behavior**: Yes—subprocess launches are independent

**Future Consideration**: Should we prevent multiple launches or manage them explicitly?

---

## Testing Strategy (Conceptual)

### Unit Tests

- `SeedInputWidget`: Validation, signal emission
- `ScenarioBrowserWidget`: File discovery, selection handling
- Navigation: Main menu → submenu → back → main menu

### Integration Tests

- Full launch flow: Main menu → Agent-Based → select scenario → launch → verify subprocess starts
- Navigation: All menu paths traverse correctly

### Manual Testing

- UI responsiveness
- Styling consistency
- Error handling scenarios

**Note**: Testing strategy should be refined when implementation begins.

---

## What This Opens Up: Future Possibilities

### Immediate Pedagogical Benefits

#### 1. Side-by-Side Paradigm Comparison

This architecture enables one of VMT's core pedagogical goals: demonstrating that **markets are not natural phenomena but institutional constructions**.

Students can now:
- **Observe emergent markets** (Agent-Based path): See how bilateral trading produces price convergence (or doesn't) through explicit search, matching, and bargaining protocols
- **Contrast with imposed equilibrium** (Neoclassical path): See how Walrasian auctioneer calculates equilibrium prices that agents take as given
- **Bridge theory and practice** (Game Theory path): Start with Edgeworth Box theoretical foundations, then explore how spatial agent-based simulations approximate or deviate from theoretical predictions

This directly supports the vision articulated in [vision_and_architecture.md](vision_and_architecture.md):

> **"VMT inverts this pedagogical sequence by asking: Under what institutional conditions do market-like phenomena actually emerge from micro-level interactions?"**

#### 2. Game Theory Pedagogy Foundation

The Game Theory path, starting with Bargaining Protocols, creates a dedicated space for **2-agent (small N) exchange demonstrations** grounded in established game theory pedagogy:

**Textbook Alignment**:
- **Kreps' Microeconomic Foundations II**: Strategic interaction, extensive form games, backward induction, subgame perfection
- **Osborne & Rubinstein's A Course in Game Theory**: Nash equilibrium, mixed strategies, repeated games, bargaining theory

**Edgeworth Box Visualization**:
- Show contract curves and competitive equilibrium points
- Animate trade-by-trade movement toward equilibrium
- Compare different bargaining protocols' paths to equilibrium
- Demonstrate concepts: mutual gains from trade, Pareto optimality, bargaining power effects
- Bridge to strategic game theory: Show how bargaining protocols relate to Nash bargaining solution, Rubinstein alternating offers, etc.

This addresses the planning in [BILATERAL_BARGAINING_PEDAGOGY_PLAN.md](../CURRENT/BILATERAL_BARGAINING_PEDAGOGY_PLAN.md) by providing a dedicated interface for Edgeworth Box demonstrations, separate from the spatial multi-agent simulation paradigm.

**Future Game Theory Extensions** (following textbook coverage):
- Nash equilibrium demonstrations (Prisoner's Dilemma, Battle of the Sexes)
- Mechanism design (auctions, voting) - Kreps Chapter 18, Osborne & Rubinstein Part IV
- Cooperative vs non-cooperative game comparisons
- Extensive form games and backward induction (Kreps Chapters 11-13)
- Repeated games and folk theorems (Osborne & Rubinstein Chapter 8, Kreps Chapter 15)

#### 3. Neoclassical Model Demonstrations

The Standard Neoclassical path enables teaching **equilibrium-first economics** alongside emergent markets, following established microeconomic theory:

**Textbook Alignment**:
- **Jehle & Reny's Advanced Microeconomic Theory**: Competitive equilibrium, general equilibrium theory, welfare theorems, Arrow-Debreu model
- **Kreps' Microeconomic Foundations I**: Consumer and producer theory, competitive markets, equilibrium existence and uniqueness

**Walrasian Auctioneer**:
- Show tatonnement process (price adjustment toward equilibrium) - Jehle & Reny Chapter 5
- Visualize excess demand curves
- Demonstrate price-taking behavior (agents respond to prices, don't negotiate)
- Contrast with bilateral bargaining (where prices are negotiated, not given)
- Demonstrate welfare theorems (First and Second) - Jehle & Reny Chapter 5.4

**Future Neoclassical Extensions** (following textbook coverage):
- Arrow-Debreu general equilibrium (Jehle & Reny Chapter 5, Kreps Chapters 5-6)
- Competitive equilibrium with production (Jehle & Reny Chapter 4, Kreps Chapter 4)
- Market failures: externalities, public goods (Jehle & Reny Chapter 9)
- Partial equilibrium analysis (Kreps Chapter 3)
- Social choice and welfare (Jehle & Reny Chapter 6)

This creates a **complete pedagogical spectrum**: from imposed equilibrium (Neoclassical) to emergent coordination (Agent-Based), with Game Theory foundations (Edgeworth Box, bargaining theory) as the bridge.

### Research Extensions Enabled

#### 1. Comparative Institutional Analysis at Scale

With multiple simulation paradigms accessible from a single entry point, researchers can:

- **Systematic Protocol Comparison**: Compare bilateral bargaining outcomes (Game Theory) with spatial search-and-match (Agent-Based) to understand when spatial frictions matter
- **Equilibrium Validation**: Use Neoclassical models as theoretical benchmarks, then test whether Agent-Based simulations converge to predicted equilibria
- **Emergence Conditions**: Study under what conditions Agent-Based simulations produce outcomes that match Neoclassical predictions (or don't)

This supports the research agenda in [vision_and_architecture.md](vision_and_architecture.md):

> **"VMT enables systematic comparison of exchange mechanisms... No single 'right' way to organize exchange... Design choices have consequences."**

#### 2. Phase 3+ Implementation Framework

The modular architecture provides a **natural home for future VMT development**:

**Phase 3 (Market Information and Coordination)**: 
- Can be implemented within Agent-Based path (enhanced bilateral trading with price signals)
- OR as a new Neoclassical sub-module (if implementing information-aggregated equilibrium mechanisms)
- Architecture flexibility allows experimentation

**Phase 4 (Commodity Money Emergence)**:
- Naturally fits Agent-Based path (emergent money from trading patterns)
- Can compare with Neoclassical monetary models (if added)

**Phase 5 (Advanced Mechanisms)**:
- New protocols can be added to existing paths or new sub-modules
- Extensibility ensures architecture doesn't constrain future research directions

### Technical Extensibility

#### 1. Independent Development Tracks

Each simulation type can be developed independently:
- Game Theory visualization can be built without touching Agent-Based code
- Neoclassical models can be added without affecting spatial simulations
- Shared components (seed input, scenario browsing) reduce duplication while maintaining separation

This supports the **modular protocol architecture** already established in VMT's engine design: just as protocols are swappable components, simulation types become swappable pedagogical modules.

#### 2. Visualization Backend Flexibility

Different simulation types may require different rendering:
- **Agent-Based**: pygame for real-time spatial animation (current)
- **Game Theory**: PyQt6 for interactive Edgeworth Box (matplotlib/pyqtgraph for plots)
- **Neoclassical**: Static or animated plots (price-quantity graphs, convergence trajectories)

The modular architecture allows each path to use appropriate visualization without forcing all types into a single rendering paradigm.

#### 3. Configuration Schema Evolution

The shared-but-extensible YAML schema approach allows:
- Backward compatibility (existing agent-based scenarios continue to work)
- Progressive enhancement (add visualization-specific fields for Game Theory)
- Type-specific validation (ensure required fields exist for each simulation type)

This aligns with the **scenario curation focus** in Phase 2.5: different pedagogical goals require different scenario designs, but they can share a common foundation.

---

## Alignment with VMT Vision

### Core Philosophy Support

This design directly supports VMT's fundamental question ([vision_and_architecture.md](vision_and_architecture.md)):

> **"Under what institutional conditions do market-like phenomena actually emerge from micro-level interactions?"**

The modular entrypoint makes this question **pedagogically explicit**: students see that there are different ways to organize exchange (imposed vs emergent), and they can explore when each approach is appropriate.

### Research Agenda Compatibility

The architecture supports the full research roadmap:

**Phase 2.5 (Scenario Curation)**: Agent-Based path provides robust scenario management  
**Phase 3 (Market Information)**: Can be implemented as Agent-Based enhancement or new module  
**Phase 4 (Money Emergence)**: Natural fit for Agent-Based path  
**Phase 5+ (Advanced Mechanisms)**: Flexible architecture accommodates new directions

### Pedagogical Mission Alignment

From [1_project_overview.md](../1_project_overview.md):

> **"VMT inverts this approach: Markets don't 'just happen'—they require specific institutions."**

The modular entrypoint makes this inversion **concrete and accessible**: students can launch Agent-Based simulations to see markets emerge, then launch Neoclassical models to see equilibrium imposed, and understand that both are valid approaches depending on institutional context.

---

## Open Questions (For Future Discussion)

1. **Scenario Sharing**: Should Game Theory scenarios be able to reuse Agent-Based scenario structures (2-agent subset of larger scenarios), or are they conceptually separate enough to warrant completely different schemas?

2. **Launch Parallelism**: Should the launcher allow multiple simulations to run simultaneously (current behavior via subprocess), or should it manage a single active simulation at a time?

3. **State Persistence**: Should the launcher remember last selected scenario/seed per simulation type, or always start fresh?

4. **Documentation Integration**: Should each simulation type have built-in help/documentation accessible from its window, or rely on external docs?

5. **Error Recovery**: If a simulation type's entry point fails (e.g., Game Theory viewer not yet implemented), should the launcher show a placeholder, disable the button, or provide graceful degradation?

6. **Extensibility Mechanism**: Should new simulation types be added via code (as proposed) or via plugin architecture (future consideration)?

---

## Conclusion

This modular GUI entrypoint design transforms VMT from a single-purpose agent-based simulation launcher into a **comprehensive pedagogical platform** that supports multiple economic modeling paradigms.

**Immediate Benefits**:
- Preserves existing Agent-Based workflow (backward compatible)
- Creates space for Game Theory demonstrations (Edgeworth Box, bargaining protocols)
- Establishes foundation for Neoclassical model integration

**Long-Term Potential**:
- Enables side-by-side paradigm comparison (emergent vs imposed markets)
- Supports full research agenda (Phases 2-5+)
- Provides extensible architecture for future pedagogical needs

**Next Steps**:
- Review and refine design decisions
- Confirm UI/UX approach (stacked widgets, navigation patterns)
- Clarify implementation scope (Phase 1 + Game Theory infrastructure vs full Neoclassical)
- Begin implementation when approved

---

**Document Status**: Planning Phase - Awaiting Design Approval  
**Next Action**: User review and refinement before implementation begins  
**Related Documents**: 
- [Vision and Architecture](vision_and_architecture.md)
- [Project Overview](../1_project_overview.md)
- [Bilateral Bargaining Pedagogy Plan](../CURRENT/BILATERAL_BARGAINING_PEDAGOGY_PLAN.md)

