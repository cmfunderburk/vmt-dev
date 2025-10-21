# Exchange Regime Comparison Guide

**Pedagogical Resource for VMT Money System**  
**Version:** 1.0  
**Last Updated:** October 2025

---

## Overview

This guide provides a systematic framework for comparing VMT's four exchange regimes. It's designed for educators preparing classroom exercises, students conducting comparative analysis, and researchers studying market structures.

---

## The Four Exchange Regimes

| Regime | Allowed Trades | Money Required | Use Case |
|--------|---------------|----------------|----------|
| `barter_only` | A↔B | No | Baseline, teaching double coincidence problem |
| `money_only` | A↔M, B↔M | Yes | Pure monetary economy, measuring efficiency gains |
| `mixed` | A↔B, A↔M, B↔M | Yes | Realistic hybrid economy, coexistence study |
| `mixed_liquidity_gated` | Conditional | Yes | Future: Liquidity constraints (Phase 5) |

---

## Regime 1: Barter Only

### Configuration

```yaml
params:
  exchange_regime: barter_only
  # Money parameters ignored
```

### Characteristics

**Allowed trades:**
- A↔B (goods for goods)

**Money behavior:**
- Even if `M` inventory is present, it's not used
- Lambda values (if present) are ignored

**Agent strategy:**
- Must find partner with complementary needs (double coincidence)
- Direct bilateral exchange only
- Trade success depends on inventory overlap

### Pedagogical Use

**Perfect for:**
- Introducing the double coincidence of wants problem
- Establishing baseline efficiency metrics
- Demonstrating coordination failures

**Teaching exercise:**
> "Run demo_02_barter_vs_money.yaml with `barter_only`. Count successful trades and final utilities. Now predict: how much will adding money help?"

**Expected outcomes:**
- Lower trade frequency than monetary regimes
- Some agents "stuck" with undesirable inventories
- Utility gains concentrated among lucky pairs

### Metrics to Track

- **Total trades**: Typically 30-50% fewer than money_only
- **Final utility**: Lower aggregate welfare
- **Idle agents**: More agents with no trading partners
- **Trade clustering**: Trades occur in tight groups

---

## Regime 2: Money Only

### Configuration

```yaml
params:
  exchange_regime: money_only
  money_mode: quasilinear
  money_scale: 1
  lambda_money: 1.0

initial_inventories:
  M: [100, 100, 100, ...]  # Required!
```

### Characteristics

**Allowed trades:**
- A↔M (good A for money)
- B↔M (good B for money)

**Money behavior:**
- Required for all trades
- Agents can buy OR sell, not barter
- Money flows from buyers to sellers

**Agent strategy:**
- Sell goods to earn money
- Use money to buy desired goods
- Indirect exchange: A→M→B

### Pedagogical Use

**Perfect for:**
- Demonstrating money as medium of exchange
- Measuring efficiency gains vs barter
- Teaching price formation

**Teaching exercise:**
> "Run the same scenario as barter_only, but with `money_only`. Compare:
> - Number of trades (+30-50%)
> - Final aggregate utility (+20-40%)
> - Trade network structure (more connections)"

**Expected outcomes:**
- Higher trade frequency (no double coincidence needed)
- More agents trade successfully
- Emergent price patterns (A and B have market prices)

### Metrics to Track

- **Total trades**: 30-50% more than barter_only
- **Money flow**: Track M circulation (some agents accumulate)
- **Price stability**: Are prices for A and B converging?
- **Welfare gain**: 20-40% utility improvement typical

---

## Regime 3: Mixed

### Configuration

```yaml
params:
  exchange_regime: mixed
  money_mode: quasilinear
  money_scale: 1
  lambda_money: 1.0

initial_inventories:
  M: [100, 100, 100, ...]  # Required!
```

### Characteristics

**Allowed trades:**
- A↔B (barter)
- A↔M (monetary)
- B↔M (monetary)

**Money behavior:**
- Optional for trades
- Money-first tie-breaking: when surplus is equal, money wins
- Coexistence of trade types

**Agent strategy:**
- Evaluate all three trade types simultaneously
- Choose highest-surplus option
- Barter if bilateral gains are strong
- Use money for moderate gains or mismatched partners

### Pedagogical Use

**Perfect for:**
- Studying when barter persists in monetary economies
- Understanding money-first tie-breaking
- Realistic economic modeling

**Teaching exercise:**
> "Run demo_03_mixed_regime.yaml. Use analyze_trade_distribution.py to see breakdown:
> - What percentage are monetary vs barter?
> - Why do agents still barter sometimes?
> - Under what conditions does barter win?"

**Expected outcomes:**
- 60-90% monetary trades (typical)
- 10-40% barter trades (when bilateral surplus is high)
- Highest total welfare (combines benefits of both)

### Metrics to Track

- **Trade type ratio**: Monetary/barter split
- **Surplus distribution**: Compare surplus for money vs barter trades
- **Total welfare**: Should equal or exceed money_only
- **Money circulation**: Does money concentrate or distribute?

---

## Regime 4: Mixed Liquidity Gated (Future)

### Configuration

```yaml
params:
  exchange_regime: mixed_liquidity_gated
  money_mode: quasilinear
  money_scale: 1
  lambda_money: 1.0
  liquidity_threshold: 10  # Future parameter
```

### Characteristics

**Status:** Planned for Money Phase 5 (not yet implemented)

**Concept:**
- Monetary trades require M ≥ threshold
- Agents with low M forced to barter
- Models liquidity constraints

**Pedagogical use (future):**
- Teaching cash-in-advance constraints
- Studying inequality effects
- Demonstrating liquidity crises

---

## Comparative Analysis Framework

### Step 1: Design Identical Scenarios

**Critical: Same initial conditions for fair comparison**

```yaml
# Use same values for all regimes:
N: 15
agents: 10
initial_inventories:
  A: [8, 2, 0, 10, 5, 0, 7, 3, 9, 1]
  B: [0, 8, 10, 0, 4, 9, 2, 7, 0, 10]
  M: [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
utilities: # Same for all
params:
  spread: 0.1      # Same for all
  vision_radius: 15
  # ... other params same
  
  # ONLY THIS CHANGES:
  exchange_regime: barter_only  # or money_only, or mixed
```

### Step 2: Run Multiple Times with Same Seeds

```bash
# Barter run
python main.py comparison_scenario.yaml --seed 42 --headless --max-ticks 75

# Money run (edit YAML to money_only)
python main.py comparison_scenario.yaml --seed 42 --headless --max-ticks 75

# Mixed run (edit YAML to mixed)
python main.py comparison_scenario.yaml --seed 42 --headless --max-ticks 75
```

**Why same seed?** Ensures initial conditions, resource spawns, and random decisions are identical except for regime.

### Step 3: Collect Metrics

Open `runs.db` in log viewer and for each run record:

**Trade frequency:**
```sql
SELECT COUNT(*) FROM trades WHERE run_id = ?
```

**Final utility:**
```sql
SELECT SUM(utility) 
FROM agent_snapshots 
WHERE run_id = ? AND tick = (SELECT MAX(tick) FROM agent_snapshots WHERE run_id = ?)
```

**Trade type distribution (mixed only):**
```bash
python scripts/analyze_trade_distribution.py runs.db <run_id>
```

### Step 4: Calculate Efficiency Gains

**Baseline:** Barter only
```
Barter trades: 42
Barter welfare: 856.3
```

**Money only:**
```
Money trades: 67
Money welfare: 1034.7
Gain: (1034.7 - 856.3) / 856.3 = +20.8%
```

**Mixed:**
```
Total trades: 71 (55 money, 16 barter)
Mixed welfare: 1067.2
Gain vs barter: +24.6%
Gain vs money: +3.1%
```

**Interpretation:**
- Money provides ~21% welfare gain (typical range: 15-35%)
- Mixed slightly beats money_only (barter captures high bilateral surplus)
- Gain magnitude depends on initial complementarity

---

## Pedagogical Scenarios

### Scenario A: Severe Double Coincidence Problem

**Design:**
- Agents with very mismatched inventories
- High preference complementarity (A-lovers paired with B-holders)
- Expected: Large gains from money (>30%)

```yaml
initial_inventories:
  A: [10, 0, 10, 0, 10, 0, 10, 0]  # Alternating
  B: [0, 10, 0, 10, 0, 10, 0, 10]
```

**Teaching point:** Money's value is highest when double coincidence is hardest.

---

### Scenario B: Easy Barter Baseline

**Design:**
- Agents with moderate inventories of both goods
- Less extreme preferences
- Expected: Smaller gains from money (10-20%)

```yaml
initial_inventories:
  A: [6, 5, 6, 5, 6, 5, 6, 5]  # Less extreme
  B: [5, 6, 5, 6, 5, 6, 5, 6]
```

**Teaching point:** When barter works well, money's benefit is smaller.

---

### Scenario C: Spatial Variation

**Design:**
- Large grid with clustered agents
- Dense center vs sparse periphery
- Expected: Money helps thin markets more

```yaml
N: 40  # Large grid
agents: 20
# Place agents in clusters (use demo_05 as template)
```

**Teaching point:** Money's value varies by market thickness.

---

### Scenario D: Time Constraints

**Design:**
- Mode schedule with limited trade windows
- Expected: Money enables faster matches in short windows

```yaml
mode_schedule:
  type: global_cycle
  forage_ticks: 20
  trade_ticks: 10  # Short window!
```

**Teaching point:** Time pressure increases value of money's efficiency.

---

## Classroom Exercises

### Exercise 1: Basic Comparison

**Objective:** Understand money's efficiency gain

**Steps:**
1. Run `demo_02_barter_vs_money.yaml` with `barter_only`
2. Record final total utility
3. Change to `money_only`, run with same seed
4. Calculate percentage improvement
5. Discuss: Why did money help?

**Expected time:** 15 minutes

**Expected outcome:** 20-30% welfare gain from money

---

### Exercise 2: Trade Distribution Analysis

**Objective:** Understand mixed regime behavior

**Steps:**
1. Run `demo_03_mixed_regime.yaml`
2. Use `analyze_trade_distribution.py` for breakdown
3. Identify: What % are monetary vs barter?
4. Hypothesis: Why do agents still barter?
5. Test: Increase `lambda_money` to 5.0, re-run
6. Result: Does barter decrease? Why?

**Expected time:** 20 minutes

**Expected outcome:** Understand when barter persists

---

### Exercise 3: Creating Custom Comparisons

**Objective:** Design and test own scenarios

**Steps:**
1. Use scenario generator to create base scenario:
   ```bash
   python -m src.vmt_tools.generate_scenario my_test --agents 12 --exchange-regime barter_only
   ```
2. Run and record baseline metrics
3. Edit YAML to change regime to `money_only`
4. Run and compare metrics
5. Repeat with `mixed`
6. Write 1-paragraph analysis

**Expected time:** 30 minutes

**Expected outcome:** Hands-on understanding of comparative methodology

---

### Exercise 4: Parameter Sensitivity

**Objective:** Understand how parameters affect regime differences

**Steps:**
1. Start with `demo_01_simple_money.yaml`
2. Run with `money_only`, record welfare
3. Test variations:
   - `lambda_money: 0.5` (low) - record welfare
   - `lambda_money: 2.0` (high) - record welfare
4. Graph: lambda vs welfare gain
5. Discuss: Why does lambda matter?

**Expected time:** 25 minutes

**Expected outcome:** Understand role of money valuation

---

## Statistical Considerations

### Multiple Runs for Robustness

**Problem:** Single run may be unrepresentative (random variation)

**Solution:** Run each regime 5-10 times with different seeds

```bash
for seed in 42 43 44 45 46; do
    python main.py scenario.yaml --seed $seed --headless --max-ticks 75
done
```

**Analysis:** Report mean ± std dev for welfare and trades

### Fair Comparison Checklist

- [ ] Same initial inventories (A, B, M)
- [ ] Same utility functions
- [ ] Same grid size and density
- [ ] Same behavioral parameters (spread, vision, etc.)
- [ ] Same random seed (for paired comparison)
- [ ] Same tick count
- [ ] Same mode schedule (if used)

**If any differ:** Comparison is invalid!

---

## Common Pitfalls

### Pitfall 1: Forgetting to Add Money Inventories

**Symptom:** No trades in `money_only` regime

**Cause:** `initial_inventories.M` not set or all zeros

**Fix:** Ensure all agents have M > 0 (typically 100+)

```yaml
initial_inventories:
  M: [100, 100, 100, 100, 100, 100]  # Add this!
```

---

### Pitfall 2: Comparing Different Seeds

**Symptom:** Results vary wildly between regimes

**Cause:** Different random seeds create different initial conditions

**Fix:** Always use `--seed` flag with same value

```bash
python main.py scenario.yaml --seed 42  # Same for all runs!
```

---

### Pitfall 3: Mode Schedule Blocking Trades

**Symptom:** Zero trades despite proper configuration

**Cause:** `mode_schedule` in "forage" mode (trading disabled)

**Fix:** Either remove `mode_schedule` or ensure sufficient trade ticks

```yaml
mode_schedule:
  trade_ticks: 50  # Long enough for trades!
```

---

### Pitfall 4: Extreme Parameter Values

**Symptom:** 100% barter or 100% money in mixed regime

**Cause:** `lambda_money` too extreme (< 0.1 or > 10)

**Fix:** Use moderate values (0.5 to 2.0 range)

```yaml
params:
  lambda_money: 1.0  # Balanced default
```

---

## Advanced Topics

### Heterogeneous Money Valuations

**Question:** What if agents value money differently?

**Current limitation:** In `quasilinear` mode, all agents have same λ

**Workaround:** Use `kkt_lambda` mode - agents develop different λ over time

**Future:** Heterogeneous fixed λ (requires code modification)

---

### Endogenous Money Supply

**Question:** Can money supply grow or shrink?

**Current:** Money supply is fixed (conserved in trades)

**Future possibility:** 
- Money creation (government injection)
- Money destruction (taxation, hoarding costs)
- Money Phase 6+ feature

---

### Multi-Good Extensions

**Question:** What about 3+ goods?

**Current:** A and B only (design choice for pedagogy)

**Future possibility:**
- Extension to N goods
- Would require protocol modularization (see ADR-001)

---

## References

**Primary documentation:**
- [User Guide: Money System](user_guide_money.md) - How to use money features
- [Technical Manual](2_technical_manual.md) - Implementation details
- [ADR-001](decisions/001-hybrid-money-modularization-sequencing.md) - Development roadmap

**Demo scenarios:**
- `scenarios/demos/demo_01_simple_money.yaml`
- `scenarios/demos/demo_02_barter_vs_money.yaml`
- `scenarios/demos/demo_03_mixed_regime.yaml`
- `scenarios/demos/demo_04_mode_schedule.yaml`
- `scenarios/demos/demo_05_liquidity_zones.yaml`

**Analysis tools:**
- `scripts/analyze_trade_distribution.py`
- `scripts/plot_mode_timeline.py`
- Log viewer: `python -m src.vmt_log_viewer.main runs.db`

---

## Summary Table

| Regime | Best For | Expected Welfare | Trade Frequency | Complexity |
|--------|----------|------------------|-----------------|------------|
| `barter_only` | Baseline, teaching DCW problem | Lowest (100%) | Low | Simple |
| `money_only` | Measuring efficiency gains | +20-35% | High | Moderate |
| `mixed` | Realistic modeling | +25-40% | Highest | Advanced |
| `mixed_liquidity_gated` | Liquidity constraints | TBD (Phase 5) | Variable | Advanced |

**DCW = Double Coincidence of Wants**

---

**Questions?** See the [User Guide](user_guide_money.md) or [Technical Manual](2_technical_manual.md).

**Happy teaching!** 📊💰

