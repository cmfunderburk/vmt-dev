# VMT - Visualizing Microeconomic Theory

[![Tests](https://img.shields.io/badge/tests-316%2B%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![Money System](https://img.shields.io/badge/money%20system-v1.0-gold)]()

A spatial agent-based simulation for teaching and researching microeconomic behavior through interactive visualization. Supports barter economies, monetary exchange, and mixed regimes with comprehensive analysis tools.

---

## 📖 Documentation

The authoritative guides for using, understanding, and extending the VMT platform are located in the **[VMT Documentation Hub](./docs/README.md)**.

**Core Guides:**
- **[Project Overview](./docs/1_project_overview.md)**: User-friendly getting started guide
- **[Technical Manual](./docs/2_technical_manual.md)**: Deep dive into engine architecture
- **[Strategic Roadmap](./docs/3_strategic_roadmap.md)**: Vision and development plan
- **[Type System & Data Contracts](./docs/4_typing_overview.md)**: Formal data specifications

**Money System (New!):**
- **[User Guide: Money System](./docs/user_guide_money.md)**: Complete guide for educators and students
- **[Regime Comparison Guide](./docs/regime_comparison.md)**: Pedagogical framework for comparing exchange regimes
- **[Technical Reference](./docs/technical/money_implementation.md)**: Implementation details for developers

**Quick Links:**
- [Demo Scenarios](./scenarios/demos/) - 5 pedagogical scenarios showcasing money system
- [Quick Reference](./docs/quick_reference.md) - Fast navigation to any document

### Versioning policy
- This project is pre-release. Do not introduce numeric versioning (e.g., SemVer) unless explicitly authorized by the maintainer.
- Use date+time-based identifiers (e.g., `2025-10-19-1430`) for labeling snapshots in docs, branches, tags, and changelogs.
- Treat existing numeric version/status badges as legacy and avoid updating or adding new ones.

## 🚀 Quick Start

```bash
# 1. Create and Activate a Virtual Environment
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Run the GUI Launcher (Recommended)
python launcher.py

# 4. Or Run from the Command Line
python main.py scenarios/three_agent_barter.yaml 42

# 5. Try the Money System (New!)
python main.py scenarios/demos/demo_01_simple_money.yaml --seed 42

# Press 'M' to see money labels, 'I' for mode/regime overlay
```

## 💰 Money System

VMT now includes a comprehensive money system for teaching monetary economics!

### Features

- **Four Exchange Regimes**: `barter_only`, `money_only`, `mixed`, `mixed_liquidity_gated`
- **Money-First Tie-Breaking**: In mixed economies, money trades preferred when surplus is equal
- **Visual Feedback**: See money labels ($M), lambda heatmaps, mode/regime overlays
- **5 Demo Scenarios**: Pre-built pedagogical scenarios in `scenarios/demos/`
- **Rich Analysis**: Trade distribution, money flows, welfare comparisons

### Quick Examples

```bash
# Simple money demo (8 agents)
python main.py scenarios/demos/demo_01_simple_money.yaml --seed 42

# Compare barter vs money
python main.py scenarios/demos/demo_02_barter_vs_money.yaml --seed 42

# Mixed economy (both trade types)
python main.py scenarios/demos/demo_03_mixed_regime.yaml --seed 42
```

### Keyboard Controls (Money-Specific)

| Key | Action |
|-----|--------|
| **M** | Toggle money labels ($M above agents) |
| **L** | Toggle lambda heatmap (blue=low, red=high λ) |
| **I** | Toggle mode/regime info overlay |

See the **[User Guide: Money System](./docs/user_guide_money.md)** for complete documentation.
