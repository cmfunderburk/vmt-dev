# VMT - Visualizing Microeconomic Theory

[![Tests](https://img.shields.io/badge/tests-54%2B%2F54%2B%20passing-brightgreen)]()

A development project for a spatial agent-based simulation to research and visualize microeconomic behavior.

---

## 📖 Documentation

The authoritative guides for using, understanding, and extending the VMT platform are located in the **[VMT Documentation Hub](./docs/README.md)**.

The hub contains:
- **Project Overview**: A user-friendly guide for getting started.
- **Technical Manual**: A deep dive into the engine's architecture.
- **Strategic Roadmap**: The vision and plan for future development.
- **Type System & Data Contracts**: The formal specification for all data structures.

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
```
