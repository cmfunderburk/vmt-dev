# VMT Developer Onboarding Program

**Document Version:** 1.0  
**Last Updated:** 2025-10-24  
**Status:** Authoritative Onboarding Guide

---

## Executive Summary

This document provides a comprehensive, step-by-step program for developers to achieve thorough mastery of the VMT (Visualizing Microeconomic Theory) codebase. The program is designed as a self-study curriculum with progressive difficulty, hands-on exercises, verification checkpoints, and explicit learning objectives.

**Target Audience:** Developers joining the VMT project who need to understand the architecture, implement features, fix bugs, or conduct research using the simulation engine.

**Prerequisites:**
- **Required:** Proficient Python (3.11+), understanding of Git, basic command-line literacy
- **Strongly Recommended:** Graduate-level microeconomic theory (utility maximization, bilateral exchange, reservation prices)
- **Helpful:** Experience with agent-based modeling, spatial algorithms, or economic simulation

**Time Commitment:** 3-4 weeks for full program (assumes 20-30 hours/week)

**Learning Philosophy:**
1. **Read-Execute-Verify** - Read code/docs, run experiments, verify understanding through tests
2. **Progressive Depth** - Surface-level overview → architectural understanding → implementation mastery
3. **Hands-On Emphasis** - Majority of time spent writing code, not reading
4. **Economic Rigor** - Understand *why* design choices were made, not just *what* they are

---

## Program Structure Overview

The onboarding program is divided into **7 sequential modules** plus **2 optional specialization tracks**:

### Core Modules (Sequential)

1. **Module 0: Environment Setup & Baseline Understanding** (4-6 hours)
   - Install, run scenarios, explore GUI and logs
   - *Outcome:* Can run simulations and interpret telemetry

2. **Module 1: Economic Foundations** (6-8 hours)
   - Utility functions, reservation prices, surplus calculation
   - *Outcome:* Deep understanding of economic primitives

3. **Module 2: Core Architecture & 7-Phase Cycle** (8-10 hours)
   - Understand simulation.py orchestration and phase ordering
   - *Outcome:* Mental model of complete tick cycle

4. **Module 3: Data Structures & Spatial Systems** (6-8 hours)
   - Agent, Grid, SpatialIndex, Inventory
   - *Outcome:* Can navigate and modify core data structures

5. **Module 4: Decision & Matching Systems** (10-12 hours)
   - Three-pass pairing, money-aware surplus, quote generation
   - *Outcome:* Understand most complex system in codebase

6. **Module 5: Money System & Exchange Regimes** (8-10 hours)
   - Quasilinear utility, exchange regimes, generic matching
   - *Outcome:* Can modify money system or add regime types

7. **Module 6: Testing, Telemetry & Determinism** (8-10 hours)
   - Test suite, SQLite schema, regression testing, performance benchmarks
   - *Outcome:* Can write tests and validate changes

### Optional Specialization Tracks

8. **Track A: GUI Development** (6-8 hours)
   - PyQt6 launcher, scenario builder, log viewer
   - *For:* Frontend-focused developers

9. **Track B: Protocol Modularization** (12-16 hours)
   - Prepare for Phase C market mechanisms
   - *For:* Developers implementing new search/matching algorithms

---

## Pre-Program Checklist

Before beginning Module 0, ensure you have:

- [ ] Python 3.11+ installed (`python --version`)
- [ ] Git configured with your name/email
- [ ] Text editor or IDE with Python support (VS Code, PyCharm, Cursor)
- [ ] Comfortable with virtual environments (`venv`)
- [ ] Access to the VMT repository (clone complete)
- [ ] 8GB+ RAM available (for large scenarios)
- [ ] SQLite browser installed (DB Browser for SQLite, or similar)

---

## Module 0: Environment Setup & Baseline Understanding

**Duration:** 4-6 hours  
**Difficulty:** ⭐☆☆☆☆  
**Prerequisites:** None

### Learning Objectives

By the end of this module, you will:
- Have a working VMT development environment
- Be able to run simulations via CLI and GUI
- Understand basic scenario structure
- Know how to view telemetry logs
- Have a high-level mental map of the project

### Section 0.1: Installation & First Run (60 min)

**Task 0.1.1: Environment Setup**

```bash
# Navigate to project root
cd /home/cmf/Work/vmt-dev

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Use venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import numpy; import pygame; import PyQt6; print('✓ All dependencies installed')"
```

**Verification Checkpoint:**
- [ ] No import errors
- [ ] `venv` directory exists
- [ ] Can activate virtual environment

**Task 0.1.2: Run Your First Simulation (CLI)**

```bash
# Run a simple 3-agent barter scenario
python main.py scenarios/three_agent_barter.yaml 42

# Observe the PyGame window:
# - Green/Purple circles = agents with different utilities
# - Yellow/Orange squares = resources (A and B)
# - Numbers on agents = inventory counts
# - Lines connecting agents = trade targets

# Keyboard controls (try them!):
# SPACE - Pause/Resume
# S - Step one tick (when paused)
# +/- - Adjust speed
# T - Toggle target arrows
# Q - Quit
```

**Exercise 0.1.2a:** Run the simulation with 3 different seeds (42, 123, 999). Do agents end up in different positions? Do they execute different trades?

**Expected Observation:** Different seeds → different outcomes (positions, trades), but *same* seed → *identical* outcomes (determinism).

**Verification Checkpoint:**
- [ ] Simulation runs without errors
- [ ] Can control playback with keyboard
- [ ] Understand what visual elements represent
- [ ] Observed that seed affects outcomes

**Task 0.1.3: Run Simulation via GUI Launcher**

```bash
# Launch GUI
python launcher.py

# In the GUI:
# 1. Browse scenarios in left panel
# 2. Select "three_agent_barter.yaml"
# 3. Enter seed: 42
# 4. Click "Launch Simulation"
# 5. Observe same behavior as CLI
```

**Verification Checkpoint:**
- [ ] GUI launches without errors
- [ ] Can browse and select scenarios
- [ ] Simulation launches from GUI matches CLI behavior

### Section 0.2: Exploring Documentation (90 min)

**Task 0.2.1: Read Project Overview**

Read: `docs/1_project_overview.md` (30 min)

**Focus Areas:**
- Core features and motivation
- 7-phase tick cycle (high-level)
- Utility function types (don't worry about math details yet)
- Money system overview
- Telemetry system

**Exercise 0.2.1a:** In your own words, write a 1-paragraph summary of what VMT does and why it exists. Compare with the document's introduction.

**Task 0.2.2: Skim Technical Manual**

Skim: `docs/2_technical_manual.md` (30 min)

**Don't Read Deeply Yet** - just get a sense of:
- What's in each section
- Where to find information later
- Level of detail provided

**Task 0.2.3: Review Code Review Guide**

Read: `docs/CODE_REVIEW_GUIDE.md` (30 min)

**This is Your Map** - bookmark this document. It provides:
- Directory structure overview
- "Relationship to simulation.py" for each module
- Key invariants
- Testing strategy

**Exercise 0.2.3a:** Draw a simple diagram (on paper or digitally) showing the relationship between:
- Scenario YAML files
- `simulation.py`
- The 7 systems
- `telemetry.db`
- Visualization (PyGame/PyQt6)

Compare your diagram to the one in the Code Review Guide (line 680).

**Verification Checkpoint:**
- [ ] Understand VMT's purpose
- [ ] Can locate documentation for specific topics
- [ ] Have mental map of major components

### Section 0.3: Scenario Structure (90 min)

**Task 0.3.1: Examine a Simple Scenario**

Open and read: `scenarios/three_agent_barter.yaml`

```yaml
schema_version: 1
name: three_agent_barter
N: 32  # Grid size (32×32)
agents: 3

initial_inventories:
  A: [8, 4, 6]  # Per-agent initial A
  B: [4, 8, 6]  # Per-agent initial B

utilities:
  mix:
    - type: ces
      weight: 1.0
      params:
        rho: -0.5    # Complementarity
        wA: 1.0
        wB: 1.0

params:
  spread: 0.0
  trade_cooldown_ticks: 5
  resource_growth_rate: 1
  resource_regen_cooldown: 5
  vision_radius: 5
  forage_rate: 1
  beta: 0.95

resource_seed:
  density: 0.15
  amount: 3
```

**Exercise 0.3.1a:** Answer these questions by reading the YAML:
1. How many agents are there?
2. What are agent 0's starting inventories of A and B?
3. What utility function do all agents use?
4. How far can agents see (vision_radius)?
5. What percentage of grid cells have resources?

**Task 0.3.2: Modify the Scenario**

Create a modified copy: `scenarios/my_first_scenario.yaml`

Change:
- `agents: 5` (increase agent count)
- `N: 20` (smaller grid)
- Add heterogeneous inventories: `A: [10, 5, 8, 12, 3]`

```bash
# Run your modified scenario
python main.py scenarios/my_first_scenario.yaml 42
```

**Verification Checkpoint:**
- [ ] Scenario runs without errors
- [ ] Can see 5 agents on 20×20 grid
- [ ] Understand how YAML controls simulation

**Task 0.3.3: Create a Money Scenario**

Reference: `docs/structures/money_example.yaml` or `scenarios/demos/demo_06_money_aware_pairing.yaml`

Create: `scenarios/my_money_test.yaml`

Key changes from barter:
```yaml
initial_inventories:
  A: [10, 5, 8]
  B: [5, 10, 8]
  M: [100, 100, 100]  # Add money

params:
  exchange_regime: "mixed"  # Allow all trade types
  money_mode: "quasilinear"
  money_scale: 1
  lambda_money: 1.0
```

Run and observe: Do agents trade goods for money? (Check telemetry in next section)

**Verification Checkpoint:**
- [ ] Money scenario runs
- [ ] Agents have M in their inventory displays
- [ ] No errors about missing money parameters

### Section 0.4: Telemetry Exploration (60 min)

**Task 0.4.1: View Telemetry Database**

After running any scenario, examine: `logs/telemetry.db`

```bash
# Option 1: GUI Log Viewer
python view_logs.py

# Option 2: SQLite CLI
sqlite3 logs/telemetry.db
sqlite> .tables
sqlite> SELECT * FROM simulation_runs LIMIT 5;
sqlite> SELECT COUNT(*) FROM trades;
sqlite> .quit
```

**Exercise 0.4.1a:** Using the log viewer or SQL queries, answer:
1. How many simulation runs are in the database?
2. How many trades occurred in your last run?
3. What exchange pair types were used? (A<->B, A<->M, B<->M)
4. What was the average utility at tick 50?

**Task 0.4.2: Understand Telemetry Schema**

Reference: `docs/4_typing_overview.md` (Section 6: Telemetry Schema)

**Key Tables to Understand:**
- `simulation_runs` - Metadata for each run
- `agent_snapshots` - Agent state per tick
- `trades` - Successful trades
- `decisions` - Agent decisions per tick
- `pairings` - Pairing/unpairing events

**Exercise 0.4.2a:** Write a SQL query to find the most traded agent pair in your last run:

```sql
SELECT buyer_id, seller_id, COUNT(*) as trade_count
FROM trades
WHERE run_id = (SELECT MAX(run_id) FROM simulation_runs)
GROUP BY buyer_id, seller_id
ORDER BY trade_count DESC
LIMIT 5;
```

**Verification Checkpoint:**
- [ ] Can open and query telemetry database
- [ ] Understand what each major table contains
- [ ] Can write basic SQL queries against logs

### Section 0.5: Project Structure Tour (45 min)

**Task 0.5.1: Explore Directory Structure**

Using your file browser or terminal, examine:

```
vmt-dev/
├── docs/              # ← Read documentation (you're here!)
├── scenarios/         # ← YAML configuration files
├── src/
│   ├── vmt_engine/    # ← Core simulation engine (MOST IMPORTANT)
│   ├── vmt_launcher/  # ← GUI launcher
│   ├── vmt_pygame/    # ← Visualization
│   ├── vmt_log_viewer/# ← Log analysis GUI
│   ├── telemetry/     # ← Database logging
│   └── scenarios/     # ← Schema and loader
├── tests/             # ← 316+ tests
├── scripts/           # ← Analysis scripts
├── main.py            # ← CLI entry point
└── launcher.py        # ← GUI entry point
```

**Task 0.5.2: Identify Key Entry Points**

Open these files in your editor (don't read deeply yet, just locate):

1. `main.py` - CLI entry point (100 lines)
2. `launcher.py` - GUI entry point (50 lines)
3. `src/vmt_engine/simulation.py` - Core orchestrator (600 lines)
4. `src/vmt_engine/systems/decision.py` - Most complex system (600 lines)
5. `src/scenarios/schema.py` - Scenario configuration (500 lines)

**Exercise 0.5.2a:** For each file above, identify:
- What does it import?
- What is its main entry point function/method?
- Approximately how many lines of code?

**Verification Checkpoint:**
- [ ] Can navigate project directory structure
- [ ] Know where to find core engine code
- [ ] Know where to find tests
- [ ] Know where to find documentation

---

## Module 0 Completion: Assessment & Next Steps

### Self-Assessment Quiz

Answer these questions without looking at documentation:

1. What are the 7 phases of a simulation tick? (List in order)
2. What file format is used for scenario configuration?
3. Where are simulation results stored?
4. What is the difference between `barter_only` and `mixed` exchange regimes?
5. What happens if you run the same scenario with the same seed twice?

**Answers:**
1. Perception, Decision, Movement, Trade, Forage, Regeneration, Housekeeping
2. YAML
3. `logs/telemetry.db` (SQLite database)
4. `barter_only` allows only A↔B trades; `mixed` allows A↔B, A↔M, B↔M
5. Identical results (determinism)

**Passing Criteria:** 4/5 correct

### Practical Assessment

Complete these tasks without referring to notes:

1. Create a new scenario with 10 agents, 30×30 grid, Linear utility
2. Run it with seed 777
3. Query telemetry to find total number of trades
4. Modify scenario to use mixed exchange regime
5. Re-run and compare trade counts

**Verification Checkpoint:**
- [ ] Completed all tasks without errors
- [ ] Understand what you did and why

### Module 0 Summary

You should now:
- ✅ Have a working development environment
- ✅ Be able to run simulations via CLI and GUI
- ✅ Understand basic scenario structure
- ✅ Know how to query telemetry
- ✅ Have a high-level mental map of the codebase

**Estimated Time Spent:** 4-6 hours

**Next Module:** Module 1 - Economic Foundations

---

## Module 1: Economic Foundations

**Duration:** 6-8 hours  
**Difficulty:** ⭐⭐☆☆☆  
**Prerequisites:** Module 0, Graduate-level microeconomics

### Learning Objectives

By the end of this module, you will:
- Deeply understand all 5 utility function types
- Know how to compute marginal utilities and MRS
- Understand reservation prices and quote generation
- Be able to hand-calculate surplus for potential trades
- Understand the economic logic behind trade execution

### Section 1.1: Utility Functions Deep Dive (120 min)

**Task 1.1.1: Read Utility Implementation**

Read: `src/vmt_engine/econ/utility.py` (entire file, ~800 lines)

**Reading Strategy:**
1. Start with module docstring
2. Read base `UtilityFunction` protocol
3. Read each utility class (CES, Linear, Quadratic, Translog, StoneGeary)
4. Pay special attention to:
   - `u_goods(A, B)` - Main utility calculation
   - `mu_A(A, B)`, `mu_B(A, B)` - Marginal utilities
   - `reservation_bounds_A_in_B(A, B)` - Reservation prices

**Reference:** `docs/2_technical_manual.md` (Section: Utility Functions)

**Task 1.1.2: CES Utility Exploration**

**Theory Review:**

$$U_{CES}(A, B) = \begin{cases}
\left(w_A \cdot A^\rho + w_B \cdot B^\rho\right)^{1/\rho} & \rho \neq 0 \\
A^{w_A} \cdot B^{w_B} & \rho \to 0 \text{ (Cobb-Douglas)}
\end{cases}$$

**Exercise 1.1.2a:** Create `exercises/module1_utility_test.py`:

```python
from src.vmt_engine.econ.utility import UCES

# Test 1: Basic utility calculation
u_ces = UCES(rho=0.5, wA=0.6, wB=0.4)

# Calculate utility for different bundles
bundles = [(10, 10), (20, 5), (5, 20), (15, 15)]

for A, B in bundles:
    utility = u_ces.u_goods(A, B)
    mu_a = u_ces.mu_A(A, B)
    mu_b = u_ces.mu_B(A, B)
    mrs = mu_a / mu_b  # Marginal rate of substitution
    
    print(f"Bundle ({A:2d}, {B:2d}): U={utility:6.2f}, MU_A={mu_a:6.2f}, MU_B={mu_b:6.2f}, MRS={mrs:6.2f}")

# Test 2: Verify MRS property
# MRS should decrease as A increases (holding B constant)
```

**Exercise 1.1.2b:** Repeat for different `rho` values: -2, -0.5, 0.5, 2

**Expected Observation:**
- Negative rho → strong complementarity (prefer balanced bundles)
- Positive rho → substitutability (less penalty for imbalance)
- MRS decreases as A increases (diminishing marginal utility)

**Task 1.1.3: Compare All Utility Types**

**Exercise 1.1.3a:** Create comparison script:

```python
from src.vmt_engine.econ.utility import UCES, ULinear, UQuadratic, UTranslog, UStoneGeary

# Create one instance of each utility type
utilities = {
    "CES": UCES(rho=0.5, wA=0.6, wB=0.4),
    "Linear": ULinear(vA=1.0, vB=0.8),
    "Quadratic": UQuadratic(A_star=15, B_star=15, sigma_A=5, sigma_B=5, gamma=0),
    "Translog": UTranslog(alpha_0=0, alpha_A=0.6, alpha_B=0.4, beta_AA=-0.1, beta_BB=-0.1, beta_AB=0.05),
    "StoneGeary": UStoneGeary(alpha_A=0.6, alpha_B=0.4, gamma_A=2, gamma_B=2)
}

# Test bundle: (10, 10)
A, B = 10, 10

print("Utility Function Comparison")
print(f"Bundle: A={A}, B={B}\n")

for name, u_func in utilities.items():
    utility = u_func.u_goods(A, B)
    mu_a = u_func.mu_A(A, B)
    mu_b = u_func.mu_B(A, B)
    mrs = mu_a / mu_b
    
    print(f"{name:12s}: U={utility:8.2f}, MRS={mrs:6.2f}")
```

**Exercise 1.1.3b:** Answer these questions:
1. Which utility function has constant MRS?
2. Which utility function can have negative marginal utility?
3. What happens with StoneGeary if A < gamma_A?

**Verification Checkpoint:**
- [ ] Can run utility calculations programmatically
- [ ] Understand how MRS relates to utility function curvature
- [ ] Know the special properties of each utility type

### Section 1.2: Reservation Prices & Quotes (90 min)

**Task 1.2.1: Understand Reservation Price Theory**

**Economic Theory:**
- **Seller's reservation price (p_min):** Minimum price to accept for good A (in terms of B)
- **Buyer's reservation price (p_max):** Maximum price to pay for good A (in terms of B)
- **Economic foundation:** At equilibrium, MRS = price ratio

**Mathematical Relationship:**
$$p_{min} = \frac{MU_A}{MU_B} \text{ (seller) }, \quad p_{max} = \frac{MU_A}{MU_B} \text{ (buyer)}$$

**Task 1.2.2: Compute Reservation Prices by Hand**

**Exercise 1.2.2a:** Given CES utility with ρ=0.5, wA=0.6, wB=0.4:

Agent has inventory A=10, B=20. Calculate:
1. U(10, 20) = ?
2. MU_A(10, 20) = ?
3. MU_B(10, 20) = ?
4. MRS = MU_A / MU_B = ?
5. If this agent wants to *sell* A, what is their reservation price (p_min)?

**Verify your hand calculation:**

```python
from src.vmt_engine.econ.utility import UCES

u = UCES(rho=0.5, wA=0.6, wB=0.4)
A, B = 10, 20

utility = u.u_goods(A, B)
mu_a = u.mu_A(A, B)
mu_b = u.mu_B(A, B)
mrs = mu_a / mu_b

p_min, p_max = u.reservation_bounds_A_in_B(A, B, epsilon=1e-12)

print(f"Hand calculation verification:")
print(f"U({A}, {B}) = {utility:.4f}")
print(f"MU_A = {mu_a:.4f}")
print(f"MU_B = {mu_b:.4f}")
print(f"MRS = {mrs:.4f}")
print(f"p_min = {p_min:.4f}, p_max = {p_max:.4f}")
```

**Task 1.2.3: Quote Generation**

Read: `src/vmt_engine/systems/quotes.py` (lines 1-200)

**Key Function:** `compute_quotes(agent, spread, epsilon, money_scale) -> dict[str, float]`

**Exercise 1.2.3a:** Manually compute quotes for barter:

```python
from src.vmt_engine.core.agent import Agent
from src.vmt_engine.core.state import Inventory
from src.vmt_engine.econ.utility import UCES
from src.vmt_engine.systems.quotes import compute_quotes

# Create test agent
u = UCES(rho=0.5, wA=0.6, wB=0.4)
agent = Agent(
    id=0,
    pos=(0, 0),
    inventory=Inventory(A=10, B=20, M=0),
    utility=u,
    vision_radius=5,
    move_budget_per_tick=1,
    lambda_money=1.0
)

# Compute quotes with zero spread
quotes = compute_quotes(agent, spread=0.0, epsilon=1e-12, money_scale=1)

print("Barter quotes:")
print(f"  ask_A_in_B: {quotes['ask_A_in_B']:.4f}")
print(f"  bid_A_in_B: {quotes['bid_A_in_B']:.4f}")
print(f"  p_min: {quotes['p_min']:.4f}")
print(f"  p_max: {quotes['p_max']:.4f}")

# Verify: with spread=0, ask = p_min and bid = p_max
```

**Exercise 1.2.3b:** Add spread=0.1 and observe changes:
- `ask_A_in_B` should be > `p_min`
- `bid_A_in_B` should be < `p_max`
- Spread creates a "bid-ask gap"

**Verification Checkpoint:**
- [ ] Can compute reservation prices by hand
- [ ] Understand relationship between MRS and prices
- [ ] Know how spread affects quotes

### Section 1.3: Surplus Calculation (90 min)

**Task 1.3.1: Understand Surplus Theory**

**Economic Definition:**
*Surplus* is the total utility gain if two agents trade with each other.

**For a trade where agent i gives ΔA to agent j for ΔB:**
$$\text{surplus}_i = U_i(A_i - \Delta A, B_i + \Delta B) - U_i(A_i, B_i)$$
$$\text{surplus}_j = U_j(A_j + \Delta A, B_j - \Delta B) - U_j(A_j, B_j)$$
$$\text{total surplus} = \text{surplus}_i + \text{surplus}_j$$

**Task 1.3.2: Compute Surplus by Hand**

**Exercise 1.3.2a:** Given two agents with CES utility:
- Agent 0: A=10, B=5
- Agent 1: A=5, B=10
- Both have ρ=0.5, wA=wB=0.5

If they trade ΔA=2 from agent 0 to agent 1 for ΔB=2:

1. Calculate U_0(10, 5) and U_0(8, 7)
2. Calculate surplus_0 = U_0(8, 7) - U_0(10, 5)
3. Calculate U_1(5, 10) and U_1(7, 8)
4. Calculate surplus_1 = U_1(7, 8) - U_1(5, 10)
5. Total surplus = surplus_0 + surplus_1

**Verify:**

```python
from src.vmt_engine.econ.utility import UCES

u = UCES(rho=0.5, wA=0.5, wB=0.5)

# Agent 0 (before trade)
A0_before, B0_before = 10, 5
U0_before = u.u_goods(A0_before, B0_before)

# Agent 0 (after trade: loses 2A, gains 2B)
A0_after, B0_after = 8, 7
U0_after = u.u_goods(A0_after, B0_after)
surplus_0 = U0_after - U0_before

# Agent 1 (before trade)
A1_before, B1_before = 5, 10
U1_before = u.u_goods(A1_before, B1_before)

# Agent 1 (after trade: gains 2A, loses 2B)
A1_after, B1_after = 7, 8
U1_after = u.u_goods(A1_after, B1_after)
surplus_1 = U1_after - U1_before

total_surplus = surplus_0 + surplus_1

print(f"Agent 0: U_before={U0_before:.4f}, U_after={U0_after:.4f}, surplus={surplus_0:.4f}")
print(f"Agent 1: U_before={U1_before:.4f}, U_after={U1_after:.4f}, surplus={surplus_1:.4f}")
print(f"Total surplus: {total_surplus:.4f}")
```

**Expected Observation:** Both agents gain utility (surplus > 0) because they're moving toward more balanced bundles with complementary preferences.

**Task 1.3.3: Code-Based Surplus Calculation**

Read: `src/vmt_engine/systems/matching.py` (lines 1-150)

**Key Functions:**
- `compute_surplus(agent_i, agent_j)` - Legacy barter surplus (quote overlap heuristic)
- `estimate_money_aware_surplus(agent_i, agent_j, exchange_regime)` - Money-aware surplus

**Exercise 1.3.3a:** Understand quote overlap heuristic:

```python
# Surplus approximation using quote overlaps
# For agent i wanting to buy A from agent j:
#   overlap = i.bid_A_in_B - j.ask_A_in_B
# If overlap > 0, trade is potentially profitable

# Example:
# Agent i: bid_A_in_B = 2.5 (willing to pay up to 2.5 B for 1 A)
# Agent j: ask_A_in_B = 1.8 (willing to sell 1 A for at least 1.8 B)
# Overlap = 2.5 - 1.8 = 0.7 > 0 ✓ Trade possible!

# The surplus function returns: max(overlap_i_buy, overlap_j_buy)
```

**Important Note:** Quote overlap is a *heuristic*, not exact utility gain. The actual trade execution uses full utility calculations.

**Verification Checkpoint:**
- [ ] Can compute surplus by hand given inventories and trade quantities
- [ ] Understand quote overlap heuristic
- [ ] Know the difference between surplus estimation (fast) vs. exact calculation (slow)

### Section 1.4: Money System Economics (90 min)

**Task 1.4.1: Quasilinear Utility**

**Theory:**
$$U_{total}(A, B, M) = U_{goods}(A, B) + \lambda \cdot M$$

Where:
- M = money holdings (integer, in minor units like cents)
- λ (lambda) = marginal utility of money (scalar)

**Exercise 1.4.1a:** Calculate total utility with money:

```python
from src.vmt_engine.econ.utility import UCES

u = UCES(rho=0.5, wA=0.6, wB=0.4)

A, B, M = 10, 15, 100
lambda_money = 1.0

u_goods = u.u_goods(A, B)
u_money = lambda_money * M
u_total = u_goods + u_money

print(f"U_goods({A}, {B}) = {u_goods:.2f}")
print(f"U_money({M}) = {u_money:.2f}")
print(f"U_total = {u_total:.2f}")
```

**Exercise 1.4.1b:** Understand lambda heterogeneity:

Different agents can have different λ values:
- High λ → values money highly → less willing to spend
- Low λ → values money less → more willing to spend

```python
# Two agents, same goods utility, different lambda
u = UCES(rho=0.5, wA=0.6, wB=0.4)

A, B, M = 10, 15, 100

lambda_high = 2.0  # Agent 0: values money highly
lambda_low = 0.5   # Agent 1: values money less

u_total_0 = u.u_goods(A, B) + lambda_high * M
u_total_1 = u.u_goods(A, B) + lambda_low * M

print(f"Agent 0 (λ={lambda_high}): U_total = {u_total_0:.2f}")
print(f"Agent 1 (λ={lambda_low}): U_total = {u_total_1:.2f}")

# Agent 0 gets more utility from money, less from goods trade
```

**Task 1.4.2: Monetary Exchange Prices**

**Theory:** For monetary exchange (A↔M or B↔M), the price is:
$$p_{A \text{ in } M} = \frac{MU_A}{\lambda} \times \text{money\_scale}$$

**Exercise 1.4.2a:** Compute monetary quotes:

```python
from src.vmt_engine.core.agent import Agent
from src.vmt_engine.core.state import Inventory
from src.vmt_engine.econ.utility import UCES
from src.vmt_engine.systems.quotes import compute_quotes

u = UCES(rho=0.5, wA=0.6, wB=0.4)
agent = Agent(
    id=0,
    pos=(0, 0),
    inventory=Inventory(A=10, B=20, M=100),
    utility=u,
    vision_radius=5,
    move_budget_per_tick=1,
    lambda_money=1.0
)

quotes = compute_quotes(agent, spread=0.0, epsilon=1e-12, money_scale=1)

print("Monetary quotes:")
print(f"  ask_A_in_M: {quotes.get('ask_A_in_M', 'N/A')}")
print(f"  bid_A_in_M: {quotes.get('bid_A_in_M', 'N/A')}")
print(f"  ask_B_in_M: {quotes.get('ask_B_in_M', 'N/A')}")
print(f"  bid_B_in_M: {quotes.get('bid_B_in_M', 'N/A')}")
```

**Task 1.4.3: Exchange Regimes**

**Exercise 1.4.3a:** Understand regime filtering:

```python
from src.vmt_engine.systems.quotes import filter_quotes_by_regime

# Full quotes dict
quotes_full = {
    'ask_A_in_B': 2.0, 'bid_A_in_B': 1.8,
    'ask_A_in_M': 5.0, 'bid_A_in_M': 4.8,
    'ask_B_in_M': 2.5, 'bid_B_in_M': 2.3,
    'p_min': 1.8, 'p_max': 2.0
}

# Filter by regime
barter_quotes = filter_quotes_by_regime(quotes_full, "barter_only")
money_quotes = filter_quotes_by_regime(quotes_full, "money_only")
mixed_quotes = filter_quotes_by_regime(quotes_full, "mixed")

print("Barter regime quotes:", list(barter_quotes.keys()))
print("Money regime quotes:", list(money_quotes.keys()))
print("Mixed regime quotes:", list(mixed_quotes.keys()))
```

**Expected Output:**
- Barter: Only A↔B keys
- Money: Only A↔M and B↔M keys
- Mixed: All keys

**Verification Checkpoint:**
- [ ] Understand quasilinear utility formula
- [ ] Can compute monetary exchange prices
- [ ] Understand how exchange regimes filter quote visibility

---

## Module 1 Completion: Assessment

### Theoretical Assessment

Answer these questions:

1. What is the marginal rate of substitution (MRS)?
2. How is reservation price related to MRS?
3. What is the economic interpretation of "surplus" from trade?
4. In quasilinear utility, what role does λ play?
5. Why do we use quote overlap as a surplus heuristic instead of exact calculation?

### Practical Assessment

Complete these tasks:

1. Create two agents with different inventories and CES utility
2. Compute their quotes (by hand and verify with code)
3. Determine if they have positive surplus for A↔B trade
4. Calculate exact utility gain if they trade 1 unit of A for 2 units of B
5. Repeat with monetary exchange (A↔M)

### Module 1 Summary

You should now:
- ✅ Deeply understand all 5 utility functions
- ✅ Be able to compute MRS, reservation prices, and quotes
- ✅ Understand surplus calculation (both heuristic and exact)
- ✅ Understand quasilinear utility and monetary exchange
- ✅ Have strong economic foundation for reading engine code

**Estimated Time Spent:** 6-8 hours

**Next Module:** Module 2 - Core Architecture & 7-Phase Cycle

---

## Module 2: Core Architecture & 7-Phase Cycle

**Duration:** 8-10 hours  
**Difficulty:** ⭐⭐⭐☆☆  
**Prerequisites:** Modules 0 and 1

### Learning Objectives

By the end of this module, you will:
- Understand `simulation.py` orchestration logic
- Know the purpose and responsibilities of each phase
- Understand phase ordering constraints and why they matter
- Be able to trace execution flow through a complete tick
- Understand determinism guarantees and how they're enforced

### Section 2.1: Simulation.py Overview (90 min)

**Task 2.1.1: Read simulation.py Structure**

Read: `src/vmt_engine/simulation.py` (entire file, ~600 lines)

**Reading Strategy:**
1. Module docstring and imports
2. `__init__` method - initialization logic
3. `run()` method - main simulation loop
4. `step()` method - single tick execution
5. Helper methods - mode management, system filtering

**Exercise 2.1.1a:** Create a mental map (diagram or outline) showing:

```
Simulation.__init__()
├── Load scenario config
├── Initialize grid
├── Create agents
├── Create spatial index
├── Create 7 systems
└── Initialize telemetry

Simulation.run(max_ticks)
└── Loop: for tick in range(max_ticks):
    └── Call self.step()

Simulation.step()
├── 1. Perception
├── 2. Decision
├── 3. Movement
├── 4. Trade
├── 5. Forage
├── 6. Regeneration
└── 7. Housekeeping
```

**Task 2.1.2: Understand Initialization**

**Exercise 2.1.2a:** Trace agent creation:

```python
# In simulation.py, find _initialize_agents() method
# Trace how agents are created from scenario config

# Exercise: Write pseudocode for agent initialization:
# 1. Load initial inventories from scenario
# 2. Assign utility functions (weighted random sampling)
# 3. Create Agent objects
# 4. Set lambda_money values
# 5. Compute initial quotes
# 6. Return list of agents
```

**Task 2.1.3: Understand Determinism Enforcement**

**Key Principle:** All operations must be deterministic given a seed.

**Determinism Mechanisms:**
1. **Sorted Agent Iteration:** Always process agents in ID order
2. **Seed-Controlled Randomness:** All random operations use seeded RNG
3. **Fixed Tie-Breaking:** Explicit rules for ambiguous situations
4. **Frozen Snapshots:** Perception phase captures immutable world state

**Exercise 2.1.3a:** Find examples of sorted iteration in `simulation.py`:

```python
# Example 1: Agent loop in step()
# for agent in sorted(self.agents, key=lambda a: a.id):

# Exercise: Find at least 3 places where sorted() is used
# Document why sorting is necessary in each case
```

**Verification Checkpoint:**
- [ ] Can explain simulation initialization flow
- [ ] Understand run() vs. step() distinction
- [ ] Know why determinism matters
- [ ] Can identify determinism enforcement mechanisms

### Section 2.2: Phase-by-Phase Deep Dive (240 min)

For each phase, follow this structure:
1. Read the system implementation
2. Understand its inputs and outputs
3. Trace execution with a concrete example
4. Understand phase ordering dependencies

---

#### Phase 1: Perception (30 min)

**File:** `src/vmt_engine/systems/perception.py`

**Purpose:** Agents observe their local environment within vision_radius.

**Inputs:**
- Agent positions
- Agent quotes (broadcasted)
- Resource locations
- `vision_radius` parameter

**Outputs:**
- `agent.perception_cache` - dict containing:
  - `'neighbors'` - list of (agent_id, position) tuples
  - `'neighbor_quotes'` - dict mapping agent_id → quotes dict
  - `'resource_cells'` - list of Cell objects

**Exercise 2.2.1a:** Hand-trace perception for a simple scenario:

```python
# Given:
# - Agent 0 at (5, 5), vision_radius=3
# - Agent 1 at (7, 6)  # Within vision (distance = 3)
# - Agent 2 at (10, 10) # Outside vision (distance = 7)
# - Resource at (6, 7)  # Within vision

# Expected perception_cache for Agent 0:
# - neighbors: [(1, (7, 6))]  # Only Agent 1 visible
# - neighbor_quotes: {1: {...}}
# - resource_cells: [Cell at (6, 7)]
```

**Exercise 2.2.1b:** Understand spatial index usage:

```python
# Perception uses spatial_index for O(N) complexity
# Without spatial index: O(N²) all-pairs distance checks
# With spatial index: O(k*N) where k = avg neighbors

# Find in perception.py: 
# - How spatial_index is queried
# - What data structure spatial_index uses
```

**Key Insight:** Perception creates a *frozen snapshot*. Even if agents move during other phases, perception data remains unchanged until next tick.

---

#### Phase 2: Decision (60 min)

**File:** `src/vmt_engine/systems/decision.py` (600 lines - most complex system!)

**Purpose:** Agents decide targets and establish trade pairings using 3-pass algorithm.

**Three Passes:**

**Pass 1: Target Selection & Preference Ranking**
- Each agent evaluates all visible neighbors
- Computes surplus for potential trades (money-aware or barter)
- Ranks by distance-discounted surplus: `surplus × β^distance`
- Sets `agent.target_agent_id` to top choice
- Stores full preference list in `agent._preference_list`

**Pass 2: Mutual Consent Pairing**
- If agent i targets j AND j targets i → PAIR immediately
- Strongest signal of mutual interest
- Both agents set `paired_with_id`

**Pass 3: Best-Available Fallback**
- Collect all (agent, partner) preferences from unpaired agents
- Sort globally by discounted surplus (welfare-maximizing greedy)
- Greedily assign pairs (highest surplus first)

**Exercise 2.2.2a:** Hand-trace 3-pass algorithm:

```python
# Given 4 agents with preference lists (after Pass 1):
# Agent 0 preferences: [(1, 5.0), (2, 3.0), (3, 1.0)]  # Prefers agent 1
# Agent 1 preferences: [(0, 4.5), (2, 2.0)]            # Prefers agent 0 (mutual!)
# Agent 2 preferences: [(3, 6.0), (0, 2.5)]            # Prefers agent 3
# Agent 3 preferences: [(2, 5.5), (0, 1.5)]            # Prefers agent 2 (mutual!)

# Pass 2 (Mutual Consent):
# - Agent 0 ↔ Agent 1: PAIRED (mutual top choice)
# - Agent 2 ↔ Agent 3: PAIRED (mutual top choice)

# Pass 3 (Fallback):
# - No unpaired agents remain → skip

# Result: 2 pairs established
```

**Exercise 2.2.2b:** Trace money-aware surplus calculation:

Read: Lines in `decision.py` where `estimate_money_aware_surplus()` is called

```python
# Money-aware surplus checks all allowed exchange pairs:
# 1. A↔M (if money regime)
# 2. B↔M (if money regime)
# 3. A↔B (if barter regime or mixed)

# Returns: (best_surplus, best_pair_type)

# Money-first tie-breaking:
# If equal surplus: A↔M (priority 0) > B↔M (priority 1) > A↔B (priority 2)
```

**Key Insight:** Pairing is *persistent*. Once paired, agents remain committed until trade fails or mode changes.

**Verification Checkpoint:**
- [ ] Understand 3-pass algorithm flow
- [ ] Can hand-trace pairing for small examples
- [ ] Know the difference between Pass 2 and Pass 3
- [ ] Understand money-aware surplus estimation

---

#### Phase 3: Movement (30 min)

**File:** `src/vmt_engine/systems/movement.py`

**Purpose:** Agents move toward their targets using Manhattan distance.

**Key Function:** `next_step_toward(current, target, move_budget)` 

**Algorithm:**
1. Calculate Manhattan distance to target
2. If distance ≤ move_budget: move directly to target
3. Otherwise: move `move_budget` steps toward target
4. Tie-breaking: prefer x-axis, then y-axis; prefer negative direction on ties

**Exercise 2.2.3a:** Hand-calculate movement:

```python
# Given:
# - Agent at (10, 10)
# - Target at (15, 7)
# - move_budget_per_tick = 2

# Manhattan distance = |15-10| + |7-10| = 5 + 3 = 8

# Optimal path (many exist due to Manhattan):
# Option 1: (10,10) → (11,10) → (12,10) (move +2 on x-axis)
# Option 2: (10,10) → (11,10) → (11,9)  (move +1 x, -1 y)

# Tie-breaking rule: prefer x-axis first
# → Agent moves to (12, 10)

# Next tick: (12, 10) → (14, 10)
# Next tick: (14, 10) → (15, 9)
# Next tick: (15, 9) → (15, 7) [arrived]
```

**Exercise 2.2.3b:** Understand diagonal deadlock:

```python
# Special case: Two paired agents diagonally adjacent
# Example: Agent 0 at (5,5), Agent 1 at (6,6)
# Both are 1 step apart but not within interaction_radius=1 (need same cell)

# Resolution: Higher ID agent moves first
# If Agent 1 (higher ID) moves to (5,5):
#   → Both agents now co-located
#   → Can trade if within interaction_radius
```

**Verification Checkpoint:**
- [ ] Understand Manhattan distance pathfinding
- [ ] Know tie-breaking rules
- [ ] Understand diagonal deadlock resolution
- [ ] Can hand-calculate movement paths

---

#### Phase 4: Trade (45 min)

**File:** `src/vmt_engine/systems/trading.py`

**Purpose:** Execute trades between paired agents within interaction_radius.

**Algorithm:**
1. Iterate over paired agents (sorted by ID, process each pair once)
2. Check if within `interaction_radius`
3. Call `find_best_trade()` or `find_all_feasible_trades()` (mixed regime)
4. If trade succeeds:
   - Execute inventory transfers
   - Set `inventory_changed = True`
   - Log trade to telemetry
   - Agents REMAIN PAIRED (will try again next tick)
5. If trade fails:
   - UNPAIR both agents
   - Set `trade_cooldown_ticks`
   - Log unpairing event

**Exercise 2.2.4a:** Understand trade execution:

Read: `src/vmt_engine/systems/matching.py` → `find_compensating_block_generic()`

**Compensating Block Search:**
```python
# For each ΔA from 1 to dA_max:
#   For each candidate price in [seller.ask, buyer.bid]:
#     Compute ΔB = round(price * ΔA)  # Round-half-up
#     Check inventory feasibility
#     Compute ΔU_buyer and ΔU_seller
#     If both ΔU > 0:
#       Return trade block (ΔA, ΔB, price)
#       ↑ FIRST ACCEPTABLE TRADE, not maximum surplus!
```

**Exercise 2.2.4b:** Money-first tie-breaking in mixed regimes:

```python
# In mixed regimes, find_all_feasible_trades() returns ALL feasible trades
# Then ranks them by:
# 1. Total surplus (descending)
# 2. Pair type priority (ascending): A↔M=0, B↔M=1, A↔B=2
# 3. Agent pair ID (ascending): (min_id, max_id)

# Example ranking:
# Trade 1: A↔M, surplus=5.0 → rank 1 (highest surplus, money-first)
# Trade 2: A↔B, surplus=5.0 → rank 2 (equal surplus, but barter)
# Trade 3: B↔M, surplus=4.5 → rank 3 (lower surplus)
```

**Key Insight:** Agents can execute *multiple sequential trades* across ticks while paired.

**Verification Checkpoint:**
- [ ] Understand trade execution flow
- [ ] Know when agents unpair
- [ ] Understand first-acceptable-trade principle
- [ ] Know money-first tie-breaking logic

---

#### Phase 5: Forage (20 min)

**File:** `src/vmt_engine/systems/foraging.py` → `ForageSystem`

**Purpose:** Unpaired agents harvest resources at their current position.

**Algorithm:**
1. Skip paired agents (exclusive commitment to trading)
2. Check if agent's position has a resource
3. If resource exists and available:
   - Harvest min(resource.amount, forage_rate)
   - Update agent inventory
   - Set `inventory_changed = True`
   - Update resource amount
   - Track cell in `grid.harvested_cells`
   - Break foraging commitment
   - Clear trade cooldowns

**Exercise 2.2.5a:** Understand single-harvester enforcement:

```python
# If enforce_single_harvester = True:
# Only ONE agent per resource cell can harvest per tick

# Given 3 agents at position (10, 10):
# - Agent 0 (ID=0)
# - Agent 2 (ID=2)
# - Agent 5 (ID=5)

# Only Agent 0 harvests (lowest ID)
# Agents 2 and 5 skip harvest
```

**Verification Checkpoint:**
- [ ] Understand foraging exclusivity (no paired agents)
- [ ] Know single-harvester enforcement
- [ ] Understand foraging commitment lifecycle

---

#### Phase 6: Regeneration (20 min)

**File:** `src/vmt_engine/systems/foraging.py` → `ResourceRegenerationSystem`

**Purpose:** Restore harvested resources over time.

**Algorithm:**
1. Iterate over `grid.harvested_cells` (O(harvested) not O(N²))
2. Check if enough ticks passed: `current_tick - last_harvested >= regen_cooldown`
3. If yes: regenerate `growth_rate` units per tick
4. Cap at `original_amount`
5. If fully regenerated: remove from `harvested_cells` set

**Exercise 2.2.6a:** Hand-trace regeneration:

```python
# Resource cell at (5, 5):
# - original_amount = 10
# - current_amount = 3 (was harvested to 3)
# - last_harvested_tick = 10
# - current_tick = 16
# - resource_regen_cooldown = 5
# - resource_growth_rate = 2

# Check cooldown: 16 - 10 = 6 >= 5 ✓ Can regenerate
# Regenerate: 3 + 2 = 5 (new amount)
# Still below original (5 < 10) → stays in harvested_cells

# Next tick (17): 5 + 2 = 7
# Next tick (18): 7 + 2 = 9
# Next tick (19): 9 + 2 = 11 → capped at 10 (original_amount)
# Now fully regenerated → removed from harvested_cells
```

**Verification Checkpoint:**
- [ ] Understand active set optimization
- [ ] Know regeneration cooldown mechanics
- [ ] Understand growth capping

---

#### Phase 7: Housekeeping (30 min)

**File:** `src/vmt_engine/systems/housekeeping.py`

**Purpose:** Cleanup, quote refresh, integrity checks, telemetry.

**Tasks:**
1. **Quote Refresh:** For agents with `inventory_changed = True`:
   - Recompute quotes via `compute_quotes()`
   - Reset `inventory_changed = False`

2. **Pairing Integrity:** Defensive checks:
   - Verify all pairings are bidirectional
   - Detect asymmetric pairings (shouldn't happen, but verify)

3. **Lambda Updates:** (Planned for KKT mode)
   - Estimate new λ from observed prices
   - Update `agent.lambda_money`
   - Set `lambda_changed = True` if updated

4. **Telemetry Logging:**
   - `log_agent_snapshots()` - Batch insert agent states
   - `log_resource_snapshots()` - Batch insert resource states
   - `log_tick_state()` - Log mode, regime, active pairs

**Exercise 2.2.7a:** Understand quote stability:

```python
# Why only refresh in Housekeeping?
# - Per-tick stability: All agents use same quotes during a tick
# - Determinism: Quote updates don't affect within-tick decisions
# - Performance: Batched updates more efficient

# inventory_changed flag prevents unnecessary recomputation
```

**Verification Checkpoint:**
- [ ] Understand quote refresh timing
- [ ] Know what telemetry is logged when
- [ ] Understand pairing integrity checks

---

### Section 2.3: Phase Ordering & Dependencies (60 min)

**Task 2.3.1: Understand Why Order Matters**

**Critical Invariant:** The 7-phase sequence MUST NEVER change.

**Dependencies:**
1. **Perception → Decision:** Decisions based on frozen snapshot
2. **Decision → Movement:** Agents move toward decided targets
3. **Movement → Trade:** Trade requires proximity (updated positions)
4. **Trade → Forage:** Unpaired agents forage (pairing status determined)
5. **Forage → Regeneration:** Resources harvested this tick regenerate later
6. **Regeneration → Housekeeping:** Quotes refreshed after all changes

**Exercise 2.3.1a:** Explore phase reordering consequences:

**Hypothetical:** What if we swap Movement and Decision?

```
BAD ORDER:
1. Perception
2. Movement    ← Agents move BEFORE deciding
3. Decision    ← Decisions based on wrong positions!

Problem:
- Agents move before seeing neighbors
- Perception snapshot becomes invalid
- Non-deterministic behavior (race conditions)
```

**Hypothetical:** What if we swap Trade and Forage?

```
BAD ORDER:
4. Forage      ← Unpaired agents forage
5. Trade       ← Then paired agents trade

Problem:
- Agents might forage while "intending" to trade
- Pairing status checked AFTER foraging
- Breaks commitment model
```

**Exercise 2.3.1b:** Document phase dependencies:

Create a dependency graph showing which phases depend on outputs from which other phases.

**Verification Checkpoint:**
- [ ] Understand why phase order cannot change
- [ ] Can explain consequences of reordering
- [ ] Know which phases read/write shared state

### Section 2.4: Mode Scheduling (45 min)

**Task 2.4.1: Understand Mode System**

**Three Modes:**
- `"forage"` - Only foraging allowed, no trading
- `"trade"` - Only trading allowed, no foraging
- `"both"` - Both activities allowed

**Task 2.4.2: Mode Schedule Configuration**

Read: `src/scenarios/schema.py` → `ModeSchedule` class

**Exercise 2.4.2a:** Create mode schedule scenario:

```yaml
mode_schedule:
  phases:
    - start_tick: 0
      duration: 50
      mode: "forage"
    - start_tick: 50
      duration: 100
      mode: "trade"
    - start_tick: 150
      duration: 50
      mode: "both"
```

**Exercise 2.4.2b:** Trace mode transitions:

```python
# At tick 49: mode = "forage"
# At tick 50: mode transitions to "trade"
#   → _handle_mode_transition() called
#   → All pairings cleared
#   → All foraging commitments cleared
#   → Agents start fresh in new mode
```

**Verification Checkpoint:**
- [ ] Understand mode types
- [ ] Know how mode schedule works
- [ ] Understand mode transition cleanup

---

## Module 2 Completion: Assessment

### Theoretical Assessment

1. List the 7 phases in order and describe the purpose of each.
2. Why must phases execute in this specific order?
3. What is the purpose of the perception snapshot?
4. Explain the 3-pass pairing algorithm.
5. What happens when a trade fails?

### Practical Assessment

Complete these tasks:

1. Add a print statement in each system's `execute()` method showing tick number
2. Run a small scenario (3 agents, 10 ticks)
3. Trace execution flow through logs
4. Modify Decision system to log preference list length
5. Verify your modification doesn't break determinism (run twice with same seed)

### Code Reading Assessment

Read and understand these functions:
- [ ] `simulation.py` → `step()`
- [ ] `decision.py` → `execute()`
- [ ] `trading.py` → `execute()`
- [ ] `matching.py` → `find_compensating_block_generic()`

### Module 2 Summary

You should now:
- ✅ Understand simulation.py orchestration
- ✅ Know purpose and logic of each phase
- ✅ Understand phase ordering constraints
- ✅ Be able to trace execution through a complete tick
- ✅ Understand determinism guarantees

**Estimated Time Spent:** 8-10 hours

**Next Module:** Module 3 - Data Structures & Spatial Systems

---

## Module 3: Data Structures & Spatial Systems

**Duration:** 6-8 hours  
**Difficulty:** ⭐⭐☆☆☆  
**Prerequisites:** Modules 0, 1, 2

### Learning Objectives

By the end of this module, you will:
- Understand core data structures: Agent, Grid, Inventory
- Know how SpatialIndex enables O(N) neighbor queries
- Be able to navigate and modify agent state
- Understand resource management and regeneration tracking
- Know invariants for all data structures

### Section 3.1: Core State Objects (90 min)

**Task 3.1.1: Inventory**

Read: `src/vmt_engine/core/state.py` → `Inventory` dataclass

**Exercise 3.1.1a:** Understand inventory invariant:

```python
from src.vmt_engine.core.state import Inventory

# Create inventory
inv = Inventory(A=10, B=20, M=100)

# Invariant: All quantities must be ≥ 0
# This is enforced by type system (int) but validated in trades

# Exercise: Write a function to validate inventory:
def is_valid_inventory(inv: Inventory) -> bool:
    """Check if inventory satisfies non-negativity constraint."""
    return inv.A >= 0 and inv.B >= 0 and inv.M >= 0

# Test:
assert is_valid_inventory(Inventory(10, 20, 100))
assert not is_valid_inventory(Inventory(-1, 20, 100))
```

**Task 3.1.2: Position**

```python
# Position is just a type alias for tuple[int, int]
Position = tuple[int, int]

# Manhattan distance between positions:
def manhattan_distance(pos1: Position, pos2: Position) -> int:
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

# Exercise: Calculate distances
p1 = (5, 5)
p2 = (8, 9)
dist = manhattan_distance(p1, p2)  # Should be 7
```

**Verification Checkpoint:**
- [ ] Understand Inventory structure
- [ ] Know non-negativity invariant
- [ ] Understand Position type

### Section 3.2: Agent Deep Dive (120 min)

**Task 3.2.1: Read Agent Implementation**

Read: `src/vmt_engine/core/agent.py` (entire file)

**Agent Anatomy:**

```python
@dataclass
class Agent:
    # Configuration (static)
    id: int
    utility: UtilityFunction
    vision_radius: int
    move_budget_per_tick: int
    
    # State (dynamic)
    pos: Position
    inventory: Inventory
    quotes: dict[str, float]
    lambda_money: float
    
    # Runtime flags
    inventory_changed: bool
    lambda_changed: bool
    
    # Targeting
    target_pos: Position | None
    target_agent_id: int | None
    
    # Pairing
    paired_with_id: int | None
    
    # Cooldowns
    trade_cooldowns: dict[int, int]
    
    # Perception (updated each tick)
    perception_cache: dict[str, Any]
    
    # Internal
    _preference_list: list[tuple[int, float, float, int, str]]
```

**Exercise 3.2.1a:** Trace agent lifecycle:

```python
# Tick 0: Initialization
# - Agent created with initial inventory
# - Utility assigned
# - Quotes computed
# - perception_cache = {}
# - paired_with_id = None

# Tick 1: Perception Phase
# - perception_cache updated with neighbors, resources

# Tick 1: Decision Phase
# - _preference_list populated
# - target_agent_id set
# - paired_with_id = partner_id (if paired)

# Tick 1: Movement Phase
# - pos updated toward target

# Tick 1: Trade Phase
# - If paired and close: trade executed
# - inventory updated
# - inventory_changed = True

# Tick 1: Housekeeping Phase
# - quotes recomputed (if inventory_changed)
# - inventory_changed = False
```

**Task 3.2.2: Understand Pairing State**

**Exercise 3.2.2a:** Pairing lifecycle:

```python
# State 1: Unpaired
# agent.paired_with_id = None
# agent.target_agent_id = best_neighbor_id (from preference list)

# State 2: Paired (Mutual Consent or Fallback)
# agent.paired_with_id = partner_id
# agent.target_agent_id = partner_id
# agent.target_pos = partner.pos

# State 3: Moving Toward Partner
# agent.pos != partner.pos
# Each tick: move closer
# Trade attempts fail (not within interaction_radius)

# State 4: Trading
# manhattan_distance(agent.pos, partner.pos) <= interaction_radius
# Trade executed (if feasible)
# Pairing maintained

# State 5: Unpaired (Trade Failed)
# agent.paired_with_id = None
# agent.trade_cooldowns[partner_id] = current_tick + cooldown_ticks
```

**Task 3.2.3: Understand Trade Cooldowns**

**Exercise 3.2.3a:** Cooldown mechanics:

```python
# Tick 10: Trade fails between Agent 0 and Agent 1
# agent_0.trade_cooldowns[1] = 10 + 5 = 15
# agent_1.trade_cooldowns[0] = 15

# Tick 11-14: Agents cannot target each other
# Cooldown check in decision.py: 
#   if current_tick < agent.trade_cooldowns.get(partner_id, 0):
#       skip partner  # Still in cooldown

# Tick 15: Cooldown expires
# Agents can target each other again
```

**Verification Checkpoint:**
- [ ] Understand Agent structure
- [ ] Know pairing state lifecycle
- [ ] Understand trade cooldown mechanics
- [ ] Can trace agent state through multiple ticks

### Section 3.3: Grid & Resources (90 min)

**Task 3.3.1: Read Grid Implementation**

Read: `src/vmt_engine/core/grid.py`

**Grid Anatomy:**

```python
@dataclass
class Resource:
    type: str  # "A" or "B"
    amount: int
    original_amount: int
    last_harvested_tick: int

@dataclass
class Cell:
    position: Position
    resource: Resource | None

class Grid:
    N: int  # Grid size (N×N)
    cells: dict[Position, Cell]
    harvested_cells: set[Position]  # Active set for regeneration
```

**Exercise 3.3.1a:** Understand resource lifecycle:

```python
# Initialization:
# - Resource seeded with density (e.g., 15% of cells)
# - Each resource has amount and type
# - original_amount stored for regeneration cap

# Foraging:
# - Agent harvests min(resource.amount, forage_rate)
# - resource.amount -= harvested
# - resource.last_harvested_tick = current_tick
# - Cell added to grid.harvested_cells

# Regeneration:
# - For cells in harvested_cells:
#   - If current_tick - last_harvested >= regen_cooldown:
#     - resource.amount += growth_rate
#     - Capped at original_amount
#   - If fully regenerated:
#     - Remove from harvested_cells
```

**Task 3.3.2: Grid Helper Methods**

**Exercise 3.3.2a:** Use grid utilities:

```python
from src.vmt_engine.core.grid import Grid, manhattan_distance, cells_within_radius

# Create grid
grid = Grid(N=20)

# Find cells within radius
center = (10, 10)
radius = 3
nearby_cells = cells_within_radius(center, radius, grid.N)

# Exercise: How many cells are within radius 3 of (10, 10)?
# Manhattan distance ≤ 3:
# - Distance 0: 1 cell (center)
# - Distance 1: 4 cells (cardinal directions)
# - Distance 2: 8 cells
# - Distance 3: 12 cells
# Total: 1 + 4 + 8 + 12 = 25 cells
```

**Verification Checkpoint:**
- [ ] Understand Grid structure
- [ ] Know Resource lifecycle
- [ ] Understand harvested_cells active set
- [ ] Can use grid helper methods

### Section 3.4: Spatial Index (90 min)

**Task 3.4.1: Read SpatialIndex Implementation**

Read: `src/vmt_engine/core/spatial_index.py`

**Purpose:** Enable O(N) proximity queries instead of O(N²).

**Algorithm:** Grid-based spatial hashing (bucket system).

**Exercise 3.4.1a:** Understand bucket system:

```python
# Bucket size = max(vision_radius, interaction_radius)
# Example: vision_radius=5, interaction_radius=1 → bucket_size=5

# Grid divided into buckets:
# Bucket (0,0) covers positions (0,0) to (4,4)
# Bucket (0,1) covers positions (0,5) to (4,9)
# Bucket (1,0) covers positions (5,0) to (9,4)
# etc.

# Agent position → bucket mapping:
# agent at (7, 12):
#   bucket_x = 7 // 5 = 1
#   bucket_y = 12 // 5 = 2
#   bucket = (1, 2)
```

**Task 3.4.2: Query Operations**

**Exercise 3.4.2a:** Hand-trace query_radius:

```python
# Query: Find all agents within radius 5 of position (10, 10)

# Step 1: Identify query bucket
# bucket = (10 // 5, 10 // 5) = (2, 2)

# Step 2: Identify neighboring buckets to check
# Need to check buckets within (radius / bucket_size) + 1
# radius=5, bucket_size=5 → check 1 bucket away
# Buckets to check: (1,1), (1,2), (1,3), (2,1), (2,2), (2,3), (3,1), (3,2), (3,3)

# Step 3: For each bucket, check agents
# For each agent in bucket:
#   if manhattan_distance(agent.pos, query_pos) <= radius:
#     Add to results

# Complexity: O(k) where k = agents in nearby buckets (typically << N)
```

**Task 3.4.3: Update Operations**

**Exercise 3.4.3a:** Understand update_position:

```python
# Called during Movement phase when agent moves

# Old position: (8, 8) → bucket (1, 1)
# New position: (12, 7) → bucket (2, 1)

# Steps:
# 1. Calculate old_bucket and new_bucket
# 2. If different:
#    - Remove agent from old_bucket
#    - Add agent to new_bucket
# 3. If same: no action needed (agent stayed in bucket)
```

**Verification Checkpoint:**
- [ ] Understand bucket-based spatial hashing
- [ ] Know why spatial index is O(N) not O(N²)
- [ ] Can hand-trace query operations
- [ ] Understand when updates are needed

---

## Module 3 Completion: Assessment

### Theoretical Assessment

1. What invariants must Inventory satisfy?
2. What is the difference between agent configuration and agent state?
3. How does SpatialIndex achieve O(N) neighbor queries?
4. What is stored in `grid.harvested_cells` and why?
5. Explain the agent pairing state machine.

### Practical Assessment

Complete these tasks:

1. Write a function to find all agents within radius R of a position (without using SpatialIndex)
2. Write a function to validate pairing integrity (all pairings bidirectional)
3. Create a test agent with specific inventory and compute its quotes
4. Simulate a resource harvest and regeneration cycle
5. Trace agent position through 5 ticks of movement

### Module 3 Summary

You should now:
- ✅ Understand core data structures
- ✅ Be able to navigate agent state
- ✅ Understand spatial indexing optimization
- ✅ Know resource management mechanics
- ✅ Can trace data structure interactions

**Estimated Time Spent:** 6-8 hours

**Next Module:** Module 4 - Decision & Matching Systems

---

## Module 4: Decision & Matching Systems

**Duration:** 10-12 hours  
**Difficulty:** ⭐⭐⭐⭐☆  
**Prerequisites:** Modules 0, 1, 2, 3

### Learning Objectives

By the end of this module, you will:
- Master the 3-pass pairing algorithm
- Understand money-aware surplus estimation
- Know quote generation and filtering
- Understand compensating block search
- Be able to modify decision logic or add algorithms

[Content continues with detailed breakdown of Decision and Matching systems...]

---

## Module 5: Money System & Exchange Regimes

**Duration:** 8-10 hours  
**Difficulty:** ⭐⭐⭐⭐☆  
**Prerequisites:** Modules 0-4

[Content for money system deep dive...]

---

## Module 6: Testing, Telemetry & Determinism

**Duration:** 8-10 hours  
**Difficulty:** ⭐⭐⭐☆☆  
**Prerequisites:** Modules 0-5

[Content for testing and telemetry...]

---

## Track A: GUI Development (Optional)

**Duration:** 6-8 hours  
**For:** Frontend-focused developers

[Content for PyQt6 GUI development...]

---

## Track B: Protocol Modularization (Optional)

**Duration:** 12-16 hours  
**For:** Developers implementing Phase C features

[Content for protocol modularization...]

---

## Program Completion & Certification

### Final Assessment

Complete a comprehensive project:

**Project:** Implement a new utility function type

1. Design a new utility function (e.g., Leontief perfect complements)
2. Implement in `utility.py` with full money-aware API
3. Add to scenario schema
4. Create test scenarios
5. Write unit tests (>90% coverage)
6. Verify determinism
7. Document in scenario guide

**Success Criteria:**
- [ ] Implementation passes all tests
- [ ] Determinism verified (3 runs, same seed)
- [ ] Documentation complete
- [ ] Code review ready

### Ongoing Learning Resources

**Weekly Code Review Sessions:**
- Review recent PRs
- Discuss architectural decisions
- Explore advanced topics

**Research Projects:**
- Implement KKT lambda mode
- Add new matching algorithms
- Design Phase C market mechanisms

**Community Contribution:**
- Write blog posts explaining VMT internals
- Create video tutorials
- Contribute to documentation

---

## Appendix A: Quick Reference Commands

```bash
# Run simulation
python main.py scenarios/SCENARIO.yaml SEED

# Launch GUI
python launcher.py

# View logs
python view_logs.py

# Run tests
pytest
pytest tests/test_SPECIFIC.py
pytest -v  # Verbose
pytest -k "money"  # Filter by keyword

# Code quality
black --check .
ruff check .
mypy src/

# Database queries
sqlite3 logs/telemetry.db
```

---

## Appendix B: Debugging Strategies

**Strategy 1: Print Debugging**
- Add print statements in system execute() methods
- Log agent state at each phase
- Track variable values through execution

**Strategy 2: Telemetry Analysis**
- Query database for specific runs
- Compare expected vs. actual behavior
- Use log viewer GUI for visualization

**Strategy 3: Test-Driven Debugging**
- Write failing test that reproduces bug
- Fix bug until test passes
- Add test to regression suite

**Strategy 4: Determinism Testing**
- Run scenario 3 times with same seed
- Diff telemetry outputs
- Identify non-deterministic code

---

## Appendix C: Common Pitfalls

**Pitfall 1: Breaking Determinism**
- ❌ Using unsorted iteration
- ✅ Always sort by agent ID

**Pitfall 2: Violating Phase Order**
- ❌ Reading state written later in same tick
- ✅ Understand phase dependencies

**Pitfall 3: Forgetting Inventory Constraints**
- ❌ Allowing negative inventories
- ✅ Check feasibility before trades

**Pitfall 4: Quote Refresh Timing**
- ❌ Refreshing quotes mid-tick
- ✅ Only refresh in Housekeeping

**Pitfall 5: Incorrect Surplus Calculation**
- ❌ Using quote overlap as exact surplus
- ✅ Remember it's a heuristic

---

## Appendix D: Further Reading

**Economics Background:**
- Mas-Colell, Whinston, Green: *Microeconomic Theory* (utility theory)
- Varian: *Microeconomic Analysis* (exchange economies)

**Agent-Based Modeling:**
- Wilensky & Rand: *Introduction to Agent-Based Modeling*
- Tesfatsion & Judd: *Handbook of Computational Economics*

**Software Engineering:**
- Martin: *Clean Architecture* (system design)
- Percival & Gregory: *Architecture Patterns with Python*

---

**End of Developer Onboarding Program**

**Version:** 1.0  
**Maintainer:** VMT Core Team  
**Last Updated:** 2025-10-24

---

