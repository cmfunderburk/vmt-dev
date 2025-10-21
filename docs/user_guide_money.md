# VMT Money System User Guide

**Version:** 1.0 (Money Phase 4)  
**Last Updated:** October 2025  
**Target Audience:** Educators, Researchers, Students

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Configuration Reference](#configuration-reference)
4. [Demo Scenarios](#demo-scenarios)
5. [Interpreting Results](#interpreting-results)
6. [Visualization Features](#visualization-features)
7. [Analysis Tools](#analysis-tools)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Introduction

### What is the Money System?

The VMT money system extends the basic barter economy with monetary exchange, allowing agents to trade goods for money (M) in addition to goods-for-goods barter. This enables simulation of:

- **Monetary economies** where all trade uses money as a medium of exchange
- **Barter economies** where agents trade goods directly
- **Mixed economies** where both monetary and barter exchange coexist
- **Mode-controlled regimes** with temporal constraints on trading

### Pedagogical Goals

The money system is designed to teach fundamental economic concepts:

1. **Double Coincidence of Wants**: Why barter is inefficient
2. **Money as Medium of Exchange**: How money facilitates trade
3. **Comparative Efficiency**: Measuring welfare gains from money
4. **Market Structure**: How exchange regimes affect outcomes
5. **Liquidity and Trade**: Role of money in thick vs thin markets

### Key Features

- **Four Exchange Regimes**: `barter_only`, `money_only`, `mixed`, `mixed_liquidity_gated`
- **Two Money Modes**: `quasilinear` (simple) and `kkt_lambda` (advanced)
- **Money-First Tie-Breaking**: When multiple trades have equal surplus, monetary trades are preferred
- **Mode × Regime Interaction**: Temporal control (`mode_schedule`) + type control (`exchange_regime`)
- **Rich Telemetry**: Track money flows, lambda values, trade distributions
- **Visual Feedback**: See money labels, lambda heatmaps, mode overlays in renderer

---

## Quick Start

### 1. Run a Simple Money Demo

```bash
python main.py scenarios/demos/demo_01_simple_money.yaml --seed 42
```

**What to observe:**
- Press `M` to see money labels ($M) above agents
- Press `I` to see mode/regime overlay in top-left
- Watch trades in the HUD (shows dM for monetary trades)
- Notice agents with complementary goods finding each other via money

### 2. Compare Barter vs Money

Run the same scenario twice with different regimes:

```bash
# Barter run
python main.py scenarios/demos/demo_02_barter_vs_money.yaml --seed 42
# Note final total utility

# Money run (edit YAML: change exchange_regime to money_only)
python main.py scenarios/demos/demo_02_barter_vs_money.yaml --seed 42
# Compare final utility - should be higher!
```

### 3. Analyze Results

Use the log viewer to examine trade patterns:

```bash
python -m src.vmt_log_viewer.main runs.db
```

Navigate to the **Money** tab to see:
- Trade distribution by exchange pair type
- Money statistics (avg dM, lambda values)
- Monetary trades table

---

## Configuration Reference

### Exchange Regime (`exchange_regime`)

Controls what types of trades are allowed:

#### `barter_only` (Default)
```yaml
params:
  exchange_regime: barter_only
```
- **Allowed trades**: A↔B only (goods for goods)
- **Money inventories**: Ignored (but can be present)
- **Use case**: Baseline for comparison, teaching double coincidence problem

#### `money_only`
```yaml
params:
  exchange_regime: money_only
  money_mode: quasilinear
  money_scale: 1
  lambda_money: 1.0
```
- **Allowed trades**: A↔M, B↔M only (goods for money)
- **No barter**: Agents cannot trade goods directly
- **Use case**: Pure monetary economy, comparing efficiency gains

#### `mixed`
```yaml
params:
  exchange_regime: mixed
  money_mode: quasilinear
  money_scale: 1
  lambda_money: 1.0
```
- **Allowed trades**: A↔B, A↔M, B↔M (all types)
- **Money-first tie-breaking**: When surplus is equal, money trades preferred
- **Use case**: Realistic hybrid economy, studying coexistence

#### `mixed_liquidity_gated` (Future)
```yaml
params:
  exchange_regime: mixed_liquidity_gated
  money_mode: quasilinear
  money_scale: 1
  lambda_money: 1.0
  liquidity_threshold: 10  # Future parameter
```
- **Allowed trades**: Conditional on money holdings
- **Status**: Planned for Money Phase 5 (not yet implemented)
- **Use case**: Studying liquidity constraints

### Money Mode (`money_mode`)

Controls how agents value money:

#### `quasilinear` (Recommended)
```yaml
params:
  money_mode: quasilinear
  money_scale: 1
  lambda_money: 1.0
```
- **Utility**: U(A, B, M) = u(A, B) + λ·M
- **Lambda**: Fixed at `lambda_money` parameter (typically 1.0)
- **Simple**: Easy to understand and explain
- **Use case**: Most classroom scenarios, introductory teaching

#### `kkt_lambda` (Advanced)
```yaml
params:
  money_mode: kkt_lambda
  money_scale: 1
  lambda_money: 1.0  # Initial value
  lambda_update_rate: 0.1
  lambda_bounds:
    lambda_min: 0.00001
    lambda_max: 100000.0
```
- **Utility**: Same as quasilinear, but λ updates dynamically
- **Lambda updates**: Based on KKT conditions (Karush-Kuhn-Tucker)
- **Research-grade**: More realistic, but complex
- **Use case**: Advanced courses, research projects

### Money Parameters

#### `money_scale`
```yaml
params:
  money_scale: 1  # Default
```
- **Purpose**: Scales money values relative to goods
- **Range**: Typically 0.1 to 10
- **Effect**: Higher values make money more valuable

#### `lambda_money`
```yaml
params:
  lambda_money: 1.0  # Default
```
- **Purpose**: Marginal utility of money (quasilinear) or initial λ (KKT)
- **Range**: Typically 0.1 to 10
- **Effect**: Higher values increase money demand

#### `lambda_update_rate` (KKT mode only)
```yaml
params:
  lambda_update_rate: 0.1  # Default
```
- **Purpose**: How quickly λ adjusts (learning rate)
- **Range**: 0.01 to 0.5
- **Effect**: Higher = faster convergence, but less stable

#### `lambda_bounds` (KKT mode only)
```yaml
params:
  lambda_bounds:
    lambda_min: 0.00001
    lambda_max: 100000.0
```
- **Purpose**: Prevents λ from exploding or collapsing
- **Adjust**: If seeing extreme λ values

### Mode Schedule (Optional)

Controls when agents can trade:

```yaml
mode_schedule:
  type: global_cycle
  forage_ticks: 15    # Forage-only period
  trade_ticks: 20     # Trade-only period
  start_mode: forage  # or "trade"
```

- **Forage mode**: Agents harvest resources, no trading
- **Trade mode**: Agents trade with neighbors, no foraging
- **Both mode**: Default when no `mode_schedule` specified
- **Interaction**: Works with any `exchange_regime`

---

## Demo Scenarios

VMT includes 5 pedagogical demo scenarios in `scenarios/demos/`:

### Demo 1: Simple Money (`demo_01_simple_money.yaml`)

**Pedagogical Goal:** "Why Money?"

**Key Features:**
- 8 agents, 12×12 grid
- Clear complementary preferences
- Switchable regime (barter vs money)

**Teaching Exercise:**
1. Run with `money_only`, note final utility
2. Edit to `barter_only`, run again with same seed
3. Compare: Money should enable ~30-50% more trades

**Recommended Duration:** 50 ticks

---

### Demo 2: Barter vs Money (`demo_02_barter_vs_money.yaml`)

**Pedagogical Goal:** "Double Coincidence of Wants"

**Key Features:**
- 10 agents, 15×15 grid
- Identical initial conditions for fair comparison
- Template for rigorous A/B testing

**Teaching Exercise:**
1. Run with `barter_only` (as provided)
2. Edit to `money_only`, run with **same seed**
3. Record final utilities, trade counts
4. Calculate efficiency gain percentage
5. Use log viewer to analyze trade patterns

**Recommended Duration:** 75 ticks

---

### Demo 3: Mixed Regime (`demo_03_mixed_regime.yaml`)

**Pedagogical Goal:** "When is Barter Still Used?"

**Key Features:**
- 15 agents, 20×20 grid
- Both trade types coexist
- Demonstrates money-first tie-breaking

**Teaching Exercise:**
1. Run and watch both A↔M and A↔B trades occur
2. Use `scripts/analyze_trade_distribution.py runs.db <run_id>`
3. Discuss: Why do agents still barter sometimes?
4. Answer: When bilateral gains are high enough to beat money trades

**Recommended Duration:** 100 ticks

---

### Demo 4: Mode Schedule (`demo_04_mode_schedule.yaml`)

**Pedagogical Goal:** "Time Constraints with Money"

**Key Features:**
- 12 agents, 18×18 grid
- Alternating forage/trade cycles (15/20 ticks)
- Mode × regime interaction

**Teaching Exercise:**
1. Press `I` to see mode overlay in top-left
2. Watch trades only happen during "trade" mode
3. Use `scripts/plot_mode_timeline.py runs.db <run_id>`
4. Discuss: How do time constraints affect trade patterns?

**Recommended Duration:** 100+ ticks (multiple cycles)

---

### Demo 5: Liquidity Zones (`demo_05_liquidity_zones.yaml`)

**Pedagogical Goal:** "Market Thickness and Spatial Variation"

**Key Features:**
- 20 agents, 40×40 grid (large!)
- Spatially clustered agents (center vs periphery)
- Thin vs thick markets

**Teaching Exercise:**
1. Use arrow keys to scroll around grid
2. Observe dense center has more trades than sparse periphery
3. Press `T` to show trade arrows, see network structure
4. Try with `barter_only` - money should help thin markets more

**Recommended Duration:** 150+ ticks

---

## Interpreting Results

### Understanding Lambda (λ) Values

**What is λ?**
- λ (lambda) is the marginal utility of money
- Higher λ = agent values money more
- In `quasilinear` mode: λ is fixed (typically 1.0)
- In `kkt_lambda` mode: λ updates dynamically

**Typical λ ranges:**
- **0.1 - 1.0**: Low money value (prefers goods)
- **1.0 - 5.0**: Normal range
- **5.0 - 100**: High money value (hoarding)
- **> 100**: Possible numerical issues

**Viewing λ in renderer:**
- Press `L` to toggle lambda heatmap
- Blue = low λ, Red = high λ
- Helps identify which agents need money

### Trade Type Distributions

Use `scripts/analyze_trade_distribution.py` to see breakdown:

```bash
python scripts/analyze_trade_distribution.py runs.db 1
```

**Example output:**
```
Exchange Pair        Count   Percentage
----------------------------------------------------
A<->M                  45       60.0%
B<->M                  20       26.7%
A<->B                  10       13.3%
----------------------------------------------------
Total                  75      100.0%

Insights:
  - Monetary/Barter ratio: 6.50
  - Monetary trades: 65 (86.7%)
  - Barter trades: 10 (13.3%)
```

**Interpretation:**
- **High monetary ratio (>5)**: Money is very useful (double coincidence problem severe)
- **Low ratio (<2)**: Barter often feasible (agents have complementary goods)
- **Balanced (~2-5)**: Realistic mixed economy

### Final Utility Comparison

**Single run utility:**
- View in HUD: Total inventory shown at bottom
- Log viewer: Overview tab → Final tick agent snapshots
- Sum utilities across all agents for social welfare

**Barter vs Money comparison:**
```
Barter:  Total utility = 850.2
Money:   Total utility = 1024.6
Gain:    +20.5% welfare improvement
```

**Interpretation:**
- **0-10% gain**: Minimal benefit (agents already well-matched)
- **10-30% gain**: Typical for moderate complementarity
- **30%+ gain**: Strong double coincidence problem, money very valuable

---

## Visualization Features

### Renderer Keyboard Controls

**Money-specific controls:**
- `M`: Toggle money labels ($M above agents)
- `L`: Toggle lambda heatmap (blue=low, red=high)
- `I`: Toggle mode/regime info overlay (top-left panel)

**Other useful controls:**
- `T`: Toggle trade arrows (green)
- `F`: Toggle forage arrows (orange)
- `SPACE`: Pause/resume
- `S`: Step one tick (when paused)
- Arrow keys: Scroll (for large grids like demo 5)

### Mode/Regime Overlay

Press `I` to see top-left panel showing:
- **Current mode**: forage, trade, or both (color-coded)
- **Exchange regime**: barter_only, money_only, mixed
- **Active pairs**: Which trade types are currently allowed
- **Avg λ**: Average lambda across agents (if KKT mode)

### Money Labels

Press `M` to see gold `$M` text above each agent showing their money inventory.

**Colors:**
- **Gold**: Normal money amount
- **Outlined in black**: For readability

**Tip:** Combine with lambda heatmap (`L`) to see if agents with low money also have high λ (want money).

---

## Analysis Tools

### 1. Trade Distribution Analysis

**Script:** `scripts/analyze_trade_distribution.py`

```bash
python scripts/analyze_trade_distribution.py runs.db <run_id>
```

**Output:**
- Trade counts by exchange pair type
- Monetary/barter ratio
- Percentage breakdown

**Use case:** Understanding which trade types dominate

### 2. Mode Timeline Visualization

**Script:** `scripts/plot_mode_timeline.py`

```bash
python scripts/plot_mode_timeline.py runs.db <run_id>
```

**Output:**
- Visual timeline of mode transitions
- Color-coded by mode and regime
- Interactive matplotlib plot

**Use case:** Verifying mode schedule works correctly

### 3. Log Viewer GUI

**Launch:**
```bash
python -m src.vmt_log_viewer.main runs.db
```

**Money tab features:**
- Money statistics (trades, avg dM, lambda values)
- Trade distribution table
- Money trades filtered view

**Use case:** Deep dive into specific runs, export CSVs

### 4. CSV Export

From log viewer, click "Export to CSV" to generate:
- `agent_snapshots.csv`: Includes `M` and `lambda_money` columns
- `trades.csv`: Includes `dM`, `buyer_lambda`, `seller_lambda`, `exchange_pair_type`

**Use case:** Custom analysis in Excel, R, Python

---

## Troubleshooting

### Problem: No Monetary Trades Occurring

**Symptoms:**
- In `money_only` or `mixed` regime, all trades are A↔B
- Trade distribution shows 0% monetary trades

**Causes & Solutions:**

1. **Mode schedule blocks trading**
   - Check if `mode_schedule` is set and current mode is "forage"
   - Solution: Remove `mode_schedule` or wait for "trade" mode

2. **Money inventories are zero**
   - Check `initial_inventories.M` in YAML
   - Solution: Ensure all agents have M > 0 (typically 100+)

3. **Lambda too low**
   - If `lambda_money` < 0.1, agents don't value money
   - Solution: Set `lambda_money: 1.0` or higher

4. **Regime set incorrectly**
   - Check `exchange_regime` parameter
   - Solution: Ensure it's `money_only` or `mixed`, not `barter_only`

### Problem: Lambda Values Exploding (KKT mode)

**Symptoms:**
- Agent λ values > 10,000
- Warnings in console about bounds

**Causes & Solutions:**

1. **Update rate too high**
   - `lambda_update_rate` > 0.5 can cause instability
   - Solution: Lower to 0.1 or 0.05

2. **Initial lambda too extreme**
   - `lambda_money` outside 0.1-10 range
   - Solution: Start with 1.0

3. **Bounds too wide**
   - `lambda_max` > 1,000,000 allows runaway
   - Solution: Set `lambda_max: 100` for stability

4. **Use quasilinear instead**
   - KKT is research-grade, complex
   - Solution: Switch to `money_mode: quasilinear` for teaching

### Problem: Performance Slow with Money

**Symptoms:**
- Simulation runs slower than barter-only
- Tick rate drops below 10 ticks/sec

**Causes & Solutions:**

1. **Mixed regime overhead**
   - Mixed regime evaluates 3x more trade candidates
   - Solution: Expected ~20% slowdown, still fast enough
   - Alternative: Use `money_only` for faster runs

2. **Large agent count**
   - More agents = more trade evaluations
   - Solution: Reduce agent count or grid size

3. **KKT lambda updates**
   - Dynamic λ adds computation
   - Solution: Use `quasilinear` mode

4. **Rendering overhead**
   - Money labels and heatmaps add drawing
   - Solution: Press `M` and `L` to toggle off visualizations

### Problem: Unexpected Trade Distribution

**Symptoms:**
- In `mixed` regime, 100% barter or 100% money (not mixed)

**Causes & Solutions:**

1. **Extreme parameter values**
   - `lambda_money` very high → all money trades
   - `lambda_money` very low → all barter trades
   - Solution: Use `lambda_money: 1.0` for balanced

2. **Initial inventories favor one type**
   - If all agents have similar A and B, barter is easy
   - If inventories are very mismatched, money dominates
   - Solution: Design inventories with moderate mismatch

3. **Money-first tie-breaking active**
   - When surplus is equal, money wins
   - Expected behavior in `mixed` regime
   - Solution: This is correct! Barter must offer higher surplus to win

---

## FAQ

### Q: What's the difference between `money_mode` and `exchange_regime`?

**A:** 
- `exchange_regime`: Controls **what trades are allowed** (A↔B, A↔M, B↔M)
- `money_mode`: Controls **how agents value money** (fixed λ vs dynamic λ)

Example: You can have `exchange_regime: money_only` with either `money_mode: quasilinear` or `money_mode: kkt_lambda`.

### Q: Should I use `quasilinear` or `kkt_lambda` for teaching?

**A:** Use `quasilinear` for:
- Undergraduate courses
- First exposure to money concepts
- Clarity and simplicity

Use `kkt_lambda` for:
- Graduate courses
- Research projects
- Studying dynamic λ behavior

### Q: How do I create a custom money scenario?

**A:** Use the scenario generator:

```bash
python -m src.vmt_tools.generate_scenario my_money_scenario \
    --agents 10 \
    --grid-size 15 \
    --exchange-regime money_only \
    --seed 42
```

Or use a preset:
```bash
python -m src.vmt_tools.generate_scenario quick_demo --preset money_demo
```

### Q: Can I have different λ values for different agents?

**A:** Not directly in the YAML. However:
- In `kkt_lambda` mode, agents will naturally develop different λ values over time
- For fixed heterogeneous λ, you'd need to modify the code (advanced)

### Q: What's the "money-first tie-breaking" rule?

**A:** In `mixed` regime, when multiple trades have **equal surplus**, the ranking is:
1. Sort by total surplus (descending)
2. **If tied**: Prefer money trades (A↔M, B↔M) over barter (A↔B)
3. **If still tied**: Use agent ID pair (deterministic)

This gives money a slight advantage when indifferent, making mixed regimes more realistic.

### Q: How much money should agents start with?

**A:** Rules of thumb:
- **Too little** (< 10): Agents can't afford many trades
- **Good range** (50-200): Allows ~5-20 trades per agent
- **Too much** (> 1000): Money becomes less scarce, less interesting

Start with `M: 100` per agent as default.

### Q: Can agents run out of money?

**A:** Yes! Agents can spend all their money and be unable to buy more goods until they sell something. This is realistic and pedagogically valuable (teaches liquidity constraints).

### Q: Why does the total money supply change?

**A:** It shouldn't! Money is conserved in trades:
- Buyer's M decreases by dM
- Seller's M increases by dM
- Total unchanged

If you see money supply changing, that's a bug - please report it.

---

## Additional Resources

- **Technical Manual**: See `docs/2_technical_manual.md` for implementation details
- **Type System**: See `docs/4_typing_overview.md` for data contracts and telemetry schema
- **ADR-001**: See `docs/decisions/001-hybrid-money-modularization-sequencing.md` for development roadmap
- **Test Suite**: Run `pytest tests/test_mixed_regime*.py` to see money system tests

---

**Questions or issues?** Check the troubleshooting section above or consult the technical documentation.

**Happy simulating!** 🎓💰

