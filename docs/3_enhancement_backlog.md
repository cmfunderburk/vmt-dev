# With the exception of Scenario Loader Information Pane -- most of the ideas currently contained were "seeded" by Claude Opus, which went a bit further with a prompt than I expected. Some commentary by me (cmf) is included marked by > cmf: in the text.
---
# VMT Enhancement Backlog
## Small Improvements & Quality-of-Life Ideas

**Document Purpose:** Centralized collection of improvement ideas, tweaks, and fixes orthogonal to main protocol/simulation work  
**Created:** 2025-10-28  
**Status:** Living document - add ideas as they arise  
**Priority:** These are "nice-to-haves" that can be tackled between major features or when taking a break from complex work

---

## 📋 How to Use This Document

- **Add ideas freely** - Don't self-censor; capture the thought
- **No obligation to implement** - These are possibilities, not commitments  
- **Pick items when you need a break** - Good for when you're tired of protocol work
- **Mark status when working on something** - So you remember what's in progress
- **Archive completed items** - Move to "Completed" section with date

### Status Tags
- 🔵 **[IDEA]** - Just a thought, not yet evaluated
- 🟡 **[PLANNED]** - Good idea, will implement when time permits
- 🟢 **[IN PROGRESS]** - Currently being worked on
- ✅ **[DONE]** - Completed (move to archive)
- ❌ **[REJECTED]** - Decided against (keep for historical context)

---

## 🎮 GUI & Visualization Enhancements

### Scenario Loader Information Pane 🟡 **[PLANNED]**
**Problem:** When selecting a scenario in the GUI launcher, users only see the filename/path  
**Solution:** Add an information pane that displays when a scenario is selected showing:
- Scenario name and description (if present in YAML)
- Number of agents
- Grid size
- Exchange regime (barter/money/mixed)
- Utility function types in use
- Key parameters (vision radius, trade cooldown, etc.)
- Estimated complexity/runtime
- Tags or categories (e.g., "demo", "test", "research")

**Benefit:** Users can understand what a scenario does before running it  
**Effort:** 3-4 hours  
**Location:** `src/vmt_launcher/launcher_window.py`

### Pygame Renderer Mini-Map 🔵 [IDEA]
> cmf: while this addresses a real problem that may arise later, currently it can be resolved in all realistic cases by resizing the grid.
**Problem:** Large grids make it hard to see overall patterns  
**Solution:** Add toggleable mini-map in corner showing:
- Full grid overview with agent positions as dots
- Resource density heat map
- Trade activity indicators

**Benefit:** Better understanding of spatial patterns at scale  
**Effort:** 4-5 hours  
**Key:** Make it toggleable (M key?) so it doesn't clutter small simulations

### Trade Success Rate HUD Element 🟡 **[PLANNED]**
**Problem:** Hard to see at a glance how well the economy is functioning  
**Solution:** Add to HUD:
- Trade success rate (last 10 ticks)
- Average surplus per trade
- Price dispersion indicator (if multiple trades)

**Benefit:** Quick economic health metrics visible during simulation  
**Effort:** 2 hours

---

## 📊 Telemetry & Analysis Improvements

### Automated Comparison Reports 🔵 [IDEA]
**Problem:** Comparing protocol effectiveness requires manual analysis  
**Solution:** Script that takes two telemetry databases and generates:
- Side-by-side metrics comparison
- Statistical significance tests
- Automated charts (price convergence, welfare, etc.)
- LaTeX-ready tables for papers

**Benefit:** Faster research iteration  
**Effort:** 6-8 hours  
**Location:** New script in `scripts/generate_comparison_report.py`

### Real-Time Telemetry Dashboard 🔵 [IDEA]
**Problem:** Must wait for simulation to complete to analyze  
**Solution:** Web dashboard that connects to telemetry.db and updates live:
- Use Flask/Dash for simple web server
- Auto-refreshing charts
- Key metrics in real-time
- Early stopping if simulation goes awry

**Benefit:** Catch issues early, watch convergence live  
**Effort:** 8-10 hours (requires web framework)

### Scenario Fingerprinting 🔵 [IDEA]
> cmf: To accompany this, the ability to play back the visual from a telemetry database would be critical. While the logs provide exhaustive details, the visual allows more intuitive high level pattern recognition.
**Problem:** Hard to know if a scenario has been run before with same parameters  
**Solution:** Generate hash of scenario parameters and store in telemetry:
- Hash scenario YAML content (excluding comments)
- Quick lookup: "Have I run this exact configuration?"
- Prevent redundant runs

**Benefit:** Avoid duplicate experiments  
**Effort:** 2 hours

### Post-Simulation Summary Output 🟡 [PLANNED]
**Problem:** No quick summary is shown when a simulation ends  
**Solution:** On any simulation termination path (renderer quit, headless completion, launcher exit, or controlled end), print to console:
- Inventory deltas per agent (per good): start → end and Δ
- Utility change per agent: start → end and Δ
- Per-agent totals: resources gathered and trades executed

**Benefit:** Immediate, lightweight sanity check without opening telemetry  
**Effort:** 1-2 hours  
**Location:** Centralized in `src/vmt_engine/simulation.py` (e.g., `Simulation.close()` or `print_summary()`), invoked from `main.py`, `scripts/run_headless.py`, `src/vmt_launcher/launcher.py`, and `src/vmt_pygame/renderer.py`

---

## 🛠️ Development Experience

### Test Scenario Generator 🔵 [IDEA]
> cmf: I just had to delete legacy code for this. While it would be an incredibly useful tool, the project is moving quickly and maintaining Generator code is too much overhead for me alone.
**Problem:** Creating test scenarios for specific conditions is tedious  
**Solution:** Python API for programmatically generating scenarios:
```python
scenario = ScenarioBuilder() \
    .with_agents(10, utility="ces", rho=-0.5) \
    .with_grid(32) \
    .with_resource_density(0.15) \
    .with_protocol("random_walk", "search") \
    .build()
```

**Benefit:** Easier to create systematic test suites  
**Effort:** 4-5 hours  
**Location:** `src/scenarios/builder.py`

### Protocol Performance Profiler 🔵 [IDEA]
> cmf: This will be useful in the future, but not currently a priority.
**Problem:** Don't know which protocols are slow or why  
**Solution:** Decorator that tracks protocol execution time:
- Time per execute() call
- Memory allocations
- Hot spots identification
- Automatic regression alerts

**Benefit:** Keep performance in check as complexity grows  
**Effort:** 3-4 hours

### Determinism Verification Tool 🟡 [PLANNED]
> cmf: Essential once all features are implemented and the codebase is stable; however, during rapid development it is actually a liability, as the simulation state itself is intentionally changing with certain protocol implementations or fixes.
**Problem:** Manually checking determinism is tedious  
**Solution:** Script that:
- Runs same scenario N times with same seed
- Compares telemetry databases byte-for-byte
- Reports any divergence with tick number
- Automated pre-commit hook option

**Benefit:** Catch determinism breaks immediately  
**Effort:** 2-3 hours  
**Location:** `scripts/verify_determinism.py`

---

## 📚 Documentation & Learning
> cmf: The following ideas are all good starts, but I need to think them through more carefully.

### Interactive Tutorial Mode 🔵 [IDEA]
**Problem:** New users don't know what to look for in simulations  
**Solution:** Special scenarios with built-in narration:
- Pause at key moments
- Explanatory text overlays
- Highlight important events
- "What to watch for" guides

**Benefit:** Better pedagogical value  
**Effort:** 8-10 hours (needs UI work)

### Scenario Comment Preservation 🔵 [IDEA]
**Problem:** YAML comments are lost when scenarios are loaded/saved  
**Solution:** Use ruamel.yaml to preserve comments:
- Maintain documentation within scenarios
- Allow inline parameter explanations
- Version control friendly

**Benefit:** Better documented scenarios  
**Effort:** 2 hours (library swap)

### Economic Metrics Glossary 🔵 [IDEA]
**Problem:** Users may not understand all metrics in telemetry  
**Solution:** Add to documentation:
- Clear definitions of each metric
- Economic interpretation
- Example values and what they mean
- Quick reference card

**Benefit:** More accessible to non-economists  
**Effort:** 3-4 hours of writing

---

## 🐛 Quality & Robustness

### Scenario Validation Warnings 🔵 [IDEA]
**Problem:** Some parameter combinations are valid but problematic  
**Solution:** Add non-fatal warnings for:
- Vision radius > grid size (wrapping issues)
- Trade cooldown > simulation length
- Incompatible utility parameters
- Suggested alternatives

**Benefit:** Fewer "why isn't this working?" moments  
**Effort:** 3-4 hours

### Graceful Degradation for Missing Features 🔵 [IDEA]
**Problem:** Old scenarios break when new features are added  
**Solution:** Smart defaults and migration:
- Auto-add missing parameters with sensible defaults
- Migration messages: "Added money_scale=1 (default)"
- Version compatibility checking

**Benefit:** Backward compatibility  
**Effort:** 4-5 hours

### Simulation State Checkpointing 🔵 [IDEA]
**Problem:** Long simulations can't be resumed if interrupted  
**Solution:** Periodic state snapshots:
- Save full state every N ticks
- Resume from checkpoint
- Useful for very long runs

**Benefit:** Robustness for long experiments  
**Effort:** 6-8 hours

---

## 🎯 Research Support

### A/B Testing Framework 🔵 [IDEA]
**Problem:** Comparing protocols requires manual scenario editing  
**Solution:** Built-in A/B testing:
- Split agents into treatment/control groups
- Run different protocols on each group
- Same scenario, side-by-side comparison
- Automatic statistical analysis

**Benefit:** Cleaner experimental design  
**Effort:** 5-6 hours

### Batch Run Orchestrator 🔵 [IDEA]
**Problem:** Running parameter sweeps is manual  
**Solution:** Script that:
- Takes parameter ranges
- Generates all combinations
- Runs in parallel
- Aggregates results
- Creates summary reports

**Benefit:** Systematic parameter exploration  
**Effort:** 5-6 hours  
**Location:** `scripts/batch_runner.py`

### Protocol Complexity Metrics 🔵 [IDEA]
**Problem:** Hard to quantify protocol computational complexity  
**Solution:** Automatic analysis of:
- Time complexity (Big-O)
- Space complexity
- Number of agent interactions
- Communication rounds

**Benefit:** Better protocol comparison  
**Effort:** 4-5 hours

---

## 💡 Future Ideas (Longer Term)

### Multi-Language Protocol Support 🔵 [IDEA]
**Problem:** Protocols must be written in Python  
**Solution:** Protocol API that supports:
- Julia for numerical protocols
- Rust for performance-critical code
- R for statistical methods
- WASM for web deployment

**Benefit:** Use best tool for each job  
**Effort:** 20+ hours

### Cloud Simulation Runner 🔵 [IDEA]
**Problem:** Local machine limits experiment scale  
**Solution:** Deploy to cloud:
- AWS Batch or similar
- Distributed telemetry aggregation
- Web interface for monitoring
- Cost estimation tools

**Benefit:** Larger scale experiments  
**Effort:** 40+ hours

### Machine Learning Integration 🔵 [IDEA]
**Problem:** Protocols are hand-coded  
**Solution:** Learn protocols from data:
- Reinforcement learning agents
- Imitation learning from human players
- Neural protocol architectures
- Evolutionary protocol design

**Benefit:** Discover non-obvious strategies  
**Effort:** 100+ hours (research project)

---

## ✅ Completed Enhancements

### Archive of implemented ideas with completion dates

### Runtime Protocol Configuration via GUI ✅ [DONE - 2025-10-28]
**Problem:** Protocols can only be set via command-line arguments or code  
**Solution:** 
- Protocols now configurable in YAML scenario files
- CLI arguments override YAML settings (for GUI/runtime changes)
- Protocol resolution order: CLI > YAML > legacy defaults
- Added validation for protocol names in schema

**Benefit:** Self-contained reproducible scenarios, enables future GUI protocol selector  
**Implemented in:** Phase 2a completion (protocols_in_yaml feature)  
**Future:** GUI dropdown to change protocols during simulation (deferred to later phase)

---

## 📝 Notes

### Adding New Ideas
Feel free to add ideas in any category or create new categories. Format:
```markdown
### Idea Name 🔵 [IDEA]
**Problem:** What's currently suboptimal  
**Solution:** How to improve it  
**Benefit:** Why it's worth doing  
**Effort:** Rough time estimate  
**Location:** Where in codebase (optional)
```

### Prioritization Guidelines
- **Quick wins:** < 2 hours, clear benefit
- **Break tasks:** 2-5 hours, good for context switching
- **Mini projects:** 5-10 hours, weekend work
- **Defer:** > 10 hours, needs dedicated time

### When to Work on These
- Feeling burned out on protocol work
- Waiting for feedback/review
- Want to improve tool while using it
- Friday afternoon "fun" work
- Preparation for user study or demo

---

**Remember:** This is a wishlist, not a todo list. Pick what interests you when you need a break from the main work.
