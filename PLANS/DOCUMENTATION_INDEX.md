# VMT Documentation Index

**Last Updated:** October 12, 2025  
**Version:** 1.1.0  
**Status:** Production Ready

---

## 📍 Quick Navigation

### For New Developers
1. **Start Here:** [../README.md](../README.md) - Project overview and quick start
2. **Then Read:** [Planning-Post-v1.md](Planning-Post-v1.md) - Complete system specification
3. **Reference:** [docs/CONFIGURATION.md](docs/CONFIGURATION.md) - Parameter reference

### For Maintainers
1. **System Spec:** [Planning-Post-v1.md](Planning-Post-v1.md) - As-built specification
2. **Critical Rules:** See Appendix B in Planning-Post-v1.md
3. **Test Suite:** Run `pytest tests/ -v` (45 tests must pass)

### For Researchers
1. **Implementation Review:** [V1_CHECKPOINT_REVIEW.md](V1_CHECKPOINT_REVIEW.md)
2. **Evaluation:** [Big_Review.md](Big_Review.md)
3. **Key Insights:** Section 14 of Planning-Post-v1.md

---

## 📚 Document Hierarchy

```
vmt-dev/
├── README.md                          ⭐ START HERE - Project overview
├── CHANGELOG.md                       📝 Version history and changes (NEW v1.1)
├── RECENT_UPDATES_OVERVIEW.md         🆕 Recent logging & GUI updates (NEW v1.1)
└── PLANS/
    ├── README.md                      📂 Navigation guide
    ├── DOCUMENTATION_INDEX.md         📋 This file
    │
    ├── Planning-Post-v1.md            🎯 AUTHORITATIVE SPEC (as-built v1.1)
    ├── V1_CHECKPOINT_REVIEW.md        📊 Implementation retrospective
    ├── Big_Review.md                  🔍 Evaluation vs. original plans
    ├── typing_overview.md             📝 Type system documentation
    │
    ├── docs/                          📖 System-specific documentation
    │   ├── CONFIGURATION.md           ⚙️  Parameter reference
    │   ├── NEW_LOGGING_SYSTEM.md      💾 SQLite logging (CONSOLIDATED v1.1)
    │   ├── GUI_LAUNCHER_GUIDE.md      🖥️  GUI launcher (CONSOLIDATED v1.1)
    │   ├── TELEMETRY_IMPLEMENTATION.md
    │   ├── PRICE_SEARCH_IMPLEMENTATION.md
    │   ├── ONE_TRADE_PER_TICK.md
    │   ├── TRADE_COOLDOWN_IMPLEMENTATION.md
    │   ├── RESOURCE_REGENERATION_IMPLEMENTATION.md
    │   ├── REGENERATION_COOLDOWN_FIX.md
    │   ├── BOOTSTRAP_FIX_ANALYSIS.md
    │   ├── DIAGNOSTIC_REPORT.md
    │   ├── IMPLEMENTATION_STATUS.md
    │   ├── UTILITY_FUNCTION_DOCUMENTATION.md
    │   └── UTILITY_DOCUMENTATION_IMPLEMENTATION_SUMMARY.md
    │
    └── archive/                       🗄️  Historical (superseded)
        ├── Planning-FINAL.md          ⚠️  Original v1 plan (obsolete)
        ├── algorithmic_planning.md    ⚠️  Original algorithms (obsolete)
        ├── Developer Checklist v1.md  ⚠️  Original checklist (obsolete)
        ├── LOGGING_UPGRADE_SUMMARY.md ⚠️  Merged into NEW_LOGGING_SYSTEM.md
        ├── LOGGING_BUGS_FIXED.md      ⚠️  Merged into NEW_LOGGING_SYSTEM.md
        ├── GUI_IMPLEMENTATION_SUMMARY.md ⚠️  Merged into GUI_LAUNCHER_GUIDE.md
        └── Log_system_problems.md     ⚠️  Historical problem statement
```

---

## 📖 Document Descriptions

### Active Documentation

#### [RECENT_UPDATES_OVERVIEW.md](../RECENT_UPDATES_OVERVIEW.md) 🆕
**Purpose:** Comprehensive overview of logging and GUI enhancements added in v1.1  
**Audience:** All users, especially those returning after v1.0  
**Use When:** You want to understand what's new in v1.1  
**Highlights:**
- SQLite logging system (99%+ space savings)
- Interactive log viewer
- GUI launcher with scenario builder
- Built-in documentation panel
- Performance comparisons
- Migration guides

#### [CHANGELOG.md](../CHANGELOG.md) 📝
**Purpose:** Version history and change tracking  
**Audience:** All users, maintainers  
**Use When:** You need to know what changed between versions  
**Sections:**
- Unreleased changes
- Version 1.1.0 (logging & GUI)
- Version 1.0.0 (initial release)
- Maintenance guidelines

#### [Planning-Post-v1.md](Planning-Post-v1.md) ⭐
**Purpose:** Authoritative specification of the system as actually implemented (v1.1)  
**Audience:** All developers, maintainers, researchers  
**Use When:** You need to understand how the system works  
**Sections:**
- Complete architecture
- All implemented systems (trading, foraging, cooldowns, regeneration, logging, GUI)
- Actual algorithms (price search, one trade per tick)
- Parameter reference with defaults
- Critical production rules
- Key implementation insights

#### [V1_CHECKPOINT_REVIEW.md](V1_CHECKPOINT_REVIEW.md)
**Purpose:** Retrospective of the implementation journey  
**Audience:** Researchers, future developers  
**Use When:** You want to understand what changed and why  
**Highlights:**
- 5 major systems implemented
- Critical discoveries (MRS vs discrete trade gap, bootstrap requirement)
- Design philosophy evolution
- Files created/modified
- Test coverage evolution

#### [Big_Review.md](Big_Review.md)
**Purpose:** Comprehensive evaluation vs. original planning documents  
**Audience:** Project managers, stakeholders, researchers  
**Use When:** You need to assess project completion and deviations  
**Highlights:**
- What was implemented as planned
- What was added beyond scope
- What was deferred
- Key algorithmic deviations
- Completeness: 110%

#### [typing_overview.md](typing_overview.md)
**Purpose:** Type system documentation  
**Audience:** Developers working with the codebase  
**Use When:** You need to understand data structures and type hints  

---

### System-Specific Documentation (docs/)

Each document provides deep-dive implementation details for a specific system:

| Document | System | Key Topics |
|----------|--------|------------|
| **CONFIGURATION.md** | Parameters | All defaults, validation, usage |
| **NEW_LOGGING_SYSTEM.md** | Logging | SQLite database, log levels, log viewer (CONSOLIDATED) |
| **GUI_LAUNCHER_GUIDE.md** | GUI | Launcher, scenario builder, documentation panel (CONSOLIDATED) |
| **TELEMETRY_IMPLEMENTATION.md** | Logging (v1.0) | Original CSV-based telemetry (legacy reference) |
| **PRICE_SEARCH_IMPLEMENTATION.md** | Trading | Price candidate generation, why midpoint failed |
| **ONE_TRADE_PER_TICK.md** | Trading | Flow change, deferred quote refresh |
| **TRADE_COOLDOWN_IMPLEMENTATION.md** | Behavioral | Cooldown lifecycle, partner filtering |
| **RESOURCE_REGENERATION_IMPLEMENTATION.md** | Resources | Growth rates, caps, cooldown |
| **REGENERATION_COOLDOWN_FIX.md** | Resources | Harvest-based tracking fix |
| **BOOTSTRAP_FIX_ANALYSIS.md** | Economics | Zero-inventory problem, solution |
| **DIAGNOSTIC_REPORT.md** | Debugging | Root cause analysis |
| **IMPLEMENTATION_STATUS.md** | Project | Milestone completion, test results |
| **UTILITY_FUNCTION_DOCUMENTATION.md** | GUI | In-context utility function help panel feature |
| **UTILITY_DOCUMENTATION_IMPLEMENTATION_SUMMARY.md** | GUI | Documentation panel implementation details |

---

### Archived Documentation (archive/)

**⚠️ WARNING:** These documents reflect the *intended* design before implementation. They contain algorithms and specifications that were superseded during development.

**Use archived docs for:**
- Historical context
- Understanding original planning assumptions
- Research on design evolution

**DO NOT use archived docs for:**
- Implementation guidance (use Planning-Post-v1.md instead)
- Parameter reference (use CONFIGURATION.md instead)
- Understanding current behavior (use system-specific docs instead)

| Document | Original Purpose | Why Superseded |
|----------|-----------------|----------------|
| **Planning-FINAL.md** | v1 specification | Midpoint pricing assumption failed; missing regeneration/cooldowns |
| **algorithmic_planning.md** | Algorithm details | Price search replaced midpoint; one trade per tick |
| **Developer Checklist v1.md** | Implementation guide | Systems added beyond scope; flow changed |

---

## 🎯 Usage Scenarios

### Scenario 1: "I'm new and want to understand the system"
1. Read [../README.md](../README.md) for overview and quick start
2. Run the simulation: `python main.py scenarios/three_agent_barter.yaml 42`
3. Read [Planning-Post-v1.md](Planning-Post-v1.md) sections 1-8 for core concepts
4. Explore specific systems in [docs/](docs/) as needed

### Scenario 2: "I need to modify trading behavior"
1. Read [Planning-Post-v1.md](Planning-Post-v1.md) section 7 (Trading System)
2. Read [docs/PRICE_SEARCH_IMPLEMENTATION.md](docs/PRICE_SEARCH_IMPLEMENTATION.md)
3. Read [docs/ONE_TRADE_PER_TICK.md](docs/ONE_TRADE_PER_TICK.md)
4. Check `vmt_engine/systems/matching.py`
5. Run tests: `pytest tests/test_trade_*.py -v`

### Scenario 3: "I need to understand why decisions were made"
1. Read [V1_CHECKPOINT_REVIEW.md](V1_CHECKPOINT_REVIEW.md) - implementation journey
2. Read [Big_Review.md](Big_Review.md) - evaluation of deviations
3. Read [Planning-Post-v1.md](Planning-Post-v1.md) section 14 - key insights
4. Compare with [archive/Planning-FINAL.md](archive/Planning-FINAL.md) for original assumptions

### Scenario 4: "Something isn't working"
1. Check [../README.md](../README.md) Troubleshooting section
2. Read [docs/DIAGNOSTIC_REPORT.md](docs/DIAGNOSTIC_REPORT.md) for common issues
3. Check telemetry logs in `logs/` directory
4. Review [Planning-Post-v1.md](Planning-Post-v1.md) Appendix B - Critical Production Rules

### Scenario 5: "I want to add a new feature"
1. Understand current architecture: [Planning-Post-v1.md](Planning-Post-v1.md) sections 1-2
2. Review similar systems in [docs/](docs/)
3. Follow testing patterns in `tests/`
4. Ensure all 45 tests still pass
5. Document your addition

### Scenario 6: "I want to create a custom scenario"
1. Run the GUI launcher: `python launcher.py`
2. Click "Create Custom Scenario"
3. Configure parameters in the tabs
4. Read the utility function documentation panel for guidance
5. Generate and save the YAML file
6. Run your custom scenario from the launcher

---

## 🔍 Finding Specific Information

### "What's new in v1.1?"
→ [RECENT_UPDATES_OVERVIEW.md](../RECENT_UPDATES_OVERVIEW.md)  
→ [CHANGELOG.md](../CHANGELOG.md)

### "How do I use the new SQLite logging system?"
→ [docs/NEW_LOGGING_SYSTEM.md](docs/NEW_LOGGING_SYSTEM.md)

### "How do I view logs interactively?"
→ [docs/NEW_LOGGING_SYSTEM.md](docs/NEW_LOGGING_SYSTEM.md) (Log Viewer section)  
→ Run `python view_logs.py`

### "How do I create custom scenarios?"
→ [docs/GUI_LAUNCHER_GUIDE.md](docs/GUI_LAUNCHER_GUIDE.md)  
→ Run `python launcher.py`

### "How do I configure...?"
→ [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

### "Why do agents need bootstrap inventories?"
→ [docs/BOOTSTRAP_FIX_ANALYSIS.md](docs/BOOTSTRAP_FIX_ANALYSIS.md)

### "Why does the system use price search instead of midpoint?"
→ [docs/PRICE_SEARCH_IMPLEMENTATION.md](docs/PRICE_SEARCH_IMPLEMENTATION.md)

### "How do cooldowns work?"
→ [docs/TRADE_COOLDOWN_IMPLEMENTATION.md](docs/TRADE_COOLDOWN_IMPLEMENTATION.md)  
→ [docs/REGENERATION_COOLDOWN_FIX.md](docs/REGENERATION_COOLDOWN_FIX.md)

### "What logs are available?"
→ [docs/NEW_LOGGING_SYSTEM.md](docs/NEW_LOGGING_SYSTEM.md) (current system)  
→ [docs/TELEMETRY_IMPLEMENTATION.md](docs/TELEMETRY_IMPLEMENTATION.md) (legacy CSV)

### "What changed from the original plan?"
→ [Big_Review.md](Big_Review.md)

### "What's the tick structure?"
→ [Planning-Post-v1.md](Planning-Post-v1.md) section 2

### "How are utilities implemented?"
→ [Planning-Post-v1.md](Planning-Post-v1.md) section 4

### "What parameters are available?"
→ [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

### "How do I use the GUI launcher?"
→ [docs/GUI_LAUNCHER_GUIDE.md](docs/GUI_LAUNCHER_GUIDE.md)

### "What do utility function parameters mean?"
→ [docs/UTILITY_FUNCTION_DOCUMENTATION.md](docs/UTILITY_FUNCTION_DOCUMENTATION.md)  
→ Or use the built-in documentation panel in the Custom Scenario Builder

---

## 📊 Documentation Status

| Category | Status | Quality |
|----------|--------|---------|
| **Main README** | ✅ Complete | Comprehensive, production-ready |
| **Planning-Post-v1** | ✅ Complete | Authoritative specification |
| **System Docs** | ✅ Complete | 11 detailed documents |
| **Review Docs** | ✅ Complete | Retrospective and evaluation |
| **Code Comments** | ✅ Good | Docstrings in all modules |
| **Test Documentation** | ✅ Good | 45 tests with clear names |
| **Archive** | ✅ Organized | Historical context preserved |

---

## 🔄 Maintenance

### When to Update Documentation

**Update Planning-Post-v1.md when:**
- Core algorithms change
- New systems are added
- Parameters are modified
- Critical behavior changes

**Create new system doc when:**
- Implementing a new major feature
- Fixing a subtle/complex bug
- Making significant architectural changes

**Update README.md when:**
- Adding new dependencies
- Changing installation process
- Adding major features users should know about
- Updating quick start examples

### Documentation Standards

1. **Descriptive, not prescriptive** - Document what exists, not what should be
2. **Include examples** - Show actual code/config/output
3. **Explain "why"** - Not just "what" and "how"
4. **Cross-reference** - Link related documents
5. **Keep changelog** - Track when and why documents change

---

## 📞 Questions?

If you can't find what you need:

1. **Check the main README:** [../README.md](../README.md)
2. **Search this directory:** All docs are markdown, use `grep -r "search term" PLANS/`
3. **Check the code:** Docstrings in `vmt_engine/` are comprehensive
4. **Run the tests:** `pytest tests/ -v` - Test names are descriptive

---

## 🎓 Documentation Philosophy

This project follows a **documentation-first** approach:

> "When something doesn't work, first make it observable."

Every fix, enhancement, and discovery is documented:
- **Problem statements** explain what was wrong
- **Implementation docs** explain what was built
- **Review docs** explain why decisions were made

This creates a **knowledge base** that enables:
- Future maintainers to understand the system
- Researchers to learn from the implementation
- Students to study real software engineering

**The documentation is as important as the code.**

---

**Status:** Documentation Complete and Organized ✅  
**Last Review:** October 12, 2025  
**Next Review:** When major features are added

