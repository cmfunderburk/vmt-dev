# Pedagogical Guide: Phase 2b Protocols
**Preliminary AI-Generated Document - Subject to Review**

**Created:** 2025-01-XX  
**Status:** Preliminary - Needs Human Review  
**Purpose:** Guide for using Phase 2b pedagogical protocols in teaching

---

## ⚠️ Document Status

**This document is PRELIMINARY and AI-GENERATED.** It has been created automatically based on code analysis and implementation plans. It requires:

1. **Human review** for accuracy and completeness
2. **Verification** that all scenarios and examples work correctly
3. **Testing** of all pedagogical exercises
4. **Review** of economic interpretations and teaching points

Please use this as a starting point and refine based on actual classroom experience.

---

## Overview

Phase 2b protocols demonstrate fundamental economic concepts through computational simulations. These protocols are designed to:

- **Visualize** abstract economic ideas
- **Compare** different institutional arrangements
- **Quantify** economic effects (efficiency, fairness, information value)
- **Teach** microeconomic theory through interactive exploration

This guide covers three pedagogical protocols:

1. **Greedy Surplus Matching** - Efficiency vs Fairness trade-offs
2. **Myopic Search** - Value of information in markets
3. **Take-It-Or-Leave-It Bargaining** - Bargaining power and market power

---

## Protocol 1: Greedy Surplus Matching

### Economic Concept

**Welfare Maximization vs Individual Rationality**

The Greedy Surplus Matching protocol demonstrates the classic tension between:
- **First-best efficiency** (total welfare maximization)
- **Individual rationality** (voluntary participation)

### Key Teaching Points

1. **Central Planner Perspective**
   - A central planner can maximize total surplus by forcing beneficial pairings
   - This may violate individual rationality (some agents worse off)

2. **Efficiency-Fairness Trade-off**
   - Maximum efficiency may require unfair distributions
   - Real markets require mutual consent, reducing efficiency

3. **Market Failure Illustration**
   - Shows why markets may not achieve first-best outcomes
   - Demonstrates value of market design

### Protocol Behavior

**Algorithm:**
1. Enumerate all possible agent pairs
2. Calculate total surplus for each potential pair
3. Apply distance discounting (β^distance)
4. Sort pairs by total discounted surplus (descending)
5. Greedily assign pairs (no double-booking)
6. Stop when no more pairs possible

**Economic Properties:**
- ✅ Maximizes total discounted surplus
- ⚠️ May violate individual rationality (negative surplus for some agents)
- ❌ Not strategy-proof (agents may want to misreport preferences)
- ✅ Useful for efficiency benchmarks

### Teaching Scenario

**File:** `scenarios/teaching_efficiency_vs_fairness.yaml`

**How to Run:**

```bash
# Option 1: GUI Launcher
python launcher.py
# Select: scenarios/teaching_efficiency_vs_fairness.yaml
# Set matching_protocol to "greedy_surplus"

# Option 2: Command Line (modify YAML first)
python main.py scenarios/teaching_efficiency_vs_fairness.yaml 42
```

**Comparison Exercise:**

Run the scenario **three times** with different matching protocols:

1. **Greedy Surplus Matching** (welfare maximization)
   ```yaml
   matching_protocol: "greedy_surplus"
   ```

2. **Legacy Three-Pass Matching** (mutual consent + greedy fallback)
   ```yaml
   matching_protocol: "legacy_three_pass"
   ```

3. **Random Matching** (baseline/null hypothesis)
   ```yaml
   matching_protocol: "random_matching"
   ```

**Metrics to Compare:**

- **Total Surplus:** Sum of all agent surpluses across all trades
- **Surplus Distribution:** Gini coefficient or variance of surpluses
- **Individual Welfare Changes:** Per-agent utility changes
- **Fairness Measures:** Min/max surplus, ratio of worst-off to best-off
- **Trade Count:** Number of trades executed

**Expected Outcomes:**

- Greedy matching should produce **highest total surplus**
- Greedy matching may show **wider surplus distribution** (less fair)
- Some agents may have **negative surplus** under greedy (violates IR)
- Legacy matching balances efficiency with fairness

### Discussion Questions

1. Under what conditions would greedy matching violate individual rationality?
2. Why do real markets require mutual consent?
3. How would you design a mechanism that balances efficiency and fairness?
4. What policy interventions could achieve first-best outcomes?

---

## Protocol 2: Myopic Search

### Economic Concept

**Value of Information in Markets**

Myopic search demonstrates how information constraints affect market efficiency:
- Limited information (vision radius = 1 cell)
- Search costs reduce market efficiency
- Network effects and market "thickness"

### Key Teaching Points

1. **Information as Economic Resource**
   - More information leads to better matching
   - Information has value that can be quantified

2. **Search Costs**
   - Limited vision increases search time
   - Slower convergence to efficient outcomes
   - Demonstrates frictions in real markets

3. **Market Thickness**
   - Density of agents affects search success
   - Network topology matters for information flow
   - Spatial markets vs centralized markets

### Protocol Behavior

**Algorithm:**
- Override vision radius to **1 cell** (Manhattan distance)
- Otherwise identical to legacy distance-discounted search
- Agents only consider targets within distance 1
- Demonstrates information constraints

**Economic Properties:**
- ✅ Reduced match quality (lower surplus per trade)
- ✅ Slower convergence (more ticks to reach equilibrium)
- ✅ Higher search costs (agents search longer)
- ✅ Network effects amplified (spatial structure matters more)

### Teaching Scenario

**File:** `scenarios/teaching_information_value.yaml`

**How to Run:**

```bash
# Option 1: GUI Launcher
python launcher.py
# Select: scenarios/teaching_information_value.yaml
# Set search_protocol to "myopic"

# Option 2: Command Line (modify YAML first)
python main.py scenarios/teaching_information_value.yaml 42
```

**Comparison Exercise:**

Run the scenario **three times** with different search protocols:

1. **Myopic Search** (limited vision, radius=1)
   ```yaml
   search_protocol: "myopic"
   ```

2. **Legacy Distance-Discounted Search** (full vision)
   ```yaml
   search_protocol: "legacy_distance_discounted"
   ```

3. **Random Walk Search** (no information)
   ```yaml
   search_protocol: "random_walk"
   ```

**Metrics to Compare:**

- **Convergence Speed:** Ticks to reach equilibrium (stable utility distribution)
- **Total Surplus:** Cumulative surplus over simulation
- **Trade Frequency:** Trades per tick
- **Match Quality:** Average surplus per trade
- **Agent Movement:** Visual patterns (more random with less information)

**Expected Outcomes:**

- Myopic search should show **slower convergence** than full vision
- Myopic search should achieve **lower total surplus**
- Random walk should show **lowest efficiency** (baseline)
- Information value = difference in outcomes

### Discussion Questions

1. How would you quantify the value of information in this simulation?
2. What real-world markets suffer from information constraints?
3. How do search costs affect market efficiency?
4. What technologies reduce information frictions in markets?
5. How does market "thickness" (agent density) affect outcomes?

---

## Protocol 3: Take-It-Or-Leave-It Bargaining

### Economic Concept

**Bargaining Power and Market Power**

TIOL demonstrates how asymmetric bargaining power affects outcomes:
- Proposer captures most surplus
- Responder gets minimal surplus (but > 0)
- Shows market power effects

### Key Teaching Points

1. **Bargaining Power**
   - First-mover advantage
   - Power asymmetries affect distribution
   - Illustrates hold-up problems

2. **Market Power vs Competitive Pricing**
   - Competitive markets: surplus split more evenly
   - Monopolistic markets: surplus captured by powerful party
   - Shows efficiency implications of power

3. **Institutional Design**
   - Different bargaining rules → different outcomes
   - Fairness vs efficiency considerations
   - Policy implications

### Protocol Behavior

**Algorithm:**
1. Select proposer (random or deterministic based on `proposer_selection`)
2. Proposer finds trade maximizing their surplus
3. Responder accepts if surplus ≥ ε (individual rationality)
4. Single-tick resolution (no multi-round negotiation)

**Parameters:**
- `proposer_power`: Fraction of surplus to proposer [0, 1] (default: 0.9)
- `proposer_selection`: How to select proposer
  - `"random"`: Random selection (fair but unpredictable)
  - `"higher_id"`: Agent with higher ID (deterministic)
  - `"lower_id"`: Agent with lower ID (deterministic)
  - `"first_in_pair"`: First agent in pair tuple (deterministic)

**Economic Properties:**
- ✅ Asymmetric surplus distribution
- ✅ Proposer advantage (captures most surplus)
- ✅ Fast resolution (single round)
- ✅ Demonstrates bargaining power effects

### Teaching Scenario

**File:** `scenarios/teaching_bargaining_power.yaml`

**How to Run:**

```bash
# Option 1: GUI Launcher
python launcher.py
# Select: scenarios/teaching_bargaining_power.yaml
# Set bargaining_protocol to take_it_or_leave_it with desired params

# Option 2: Command Line (modify YAML first)
python main.py scenarios/teaching_bargaining_power.yaml 42
```

**Comparison Exercise:**

Run the scenario **four times** with different bargaining protocols:

1. **TIOL with High Power** (90% to proposer)
   ```yaml
   bargaining_protocol:
     name: "take_it_or_leave_it"
     params:
       proposer_power: 0.9
       proposer_selection: "higher_id"
   ```

2. **TIOL with Moderate Power** (60% to proposer)
   ```yaml
   bargaining_protocol:
     name: "take_it_or_leave_it"
     params:
       proposer_power: 0.6
       proposer_selection: "higher_id"
   ```

3. **Split-Difference** (50/50 split - fair baseline)
   ```yaml
   bargaining_protocol: "split_difference"
   ```

4. **Legacy Compensating Block** (mutual consent - decentralized)
   ```yaml
   bargaining_protocol: "legacy_compensating_block"
   ```

**Metrics to Compare:**

- **Surplus Distribution:** Ratio of proposer to responder surplus
- **Total Welfare:** Sum of all surpluses
- **Fairness Measures:** Gini coefficient, min/max surplus
- **Individual Welfare Changes:** Per-agent utility changes
- **Trade Success Rate:** Fraction of pairs that trade

**Expected Outcomes:**

- TIOL with high power shows **extreme asymmetry** (90/10 split)
- TIOL with moderate power shows **less asymmetry** (60/40 split)
- Split-difference shows **fair distribution** (50/50 split)
- Legacy shows **decentralized negotiation** (variable splits)

### Discussion Questions

1. How does bargaining power affect market efficiency?
2. What real-world markets exhibit asymmetric bargaining power?
3. How do institutional rules affect power distribution?
4. What policies could reduce bargaining power asymmetries?
5. When is asymmetric bargaining efficient vs unfair?

---

## Running Comparison Scenarios

### Method 1: GUI Launcher (Recommended)

```bash
python launcher.py
```

1. Select scenario file
2. Modify protocol settings in YAML editor
3. Run simulation
4. Compare results visually or via telemetry

### Method 2: Command Line with YAML Editing

1. Edit scenario YAML file to set protocol:
   ```yaml
   matching_protocol: "greedy_surplus"
   search_protocol: "myopic"
   bargaining_protocol:
     name: "take_it_or_leave_it"
     params:
       proposer_power: 0.9
   ```

2. Run simulation:
   ```bash
   python main.py scenarios/teaching_efficiency_vs_fairness.yaml 42
   ```

3. Repeat with different protocol settings
4. Compare outcomes

### Method 3: Headless Execution (for Analysis)

```bash
python scripts/run_headless.py scenarios/teaching_efficiency_vs_fairness.yaml --seed 42 --max-ticks 100
```

This generates telemetry data without visualization, useful for:
- Batch comparisons
- Statistical analysis
- Telemetry database queries

---

## Analyzing Results

### Visual Observation

**Watch for:**
- Agent movement patterns (random vs directed)
- Trade frequency and timing
- Spatial clustering or dispersion
- Convergence speed

### Telemetry Analysis

**Access telemetry database:**
```python
import sqlite3
conn = sqlite3.connect('logs/telemetry.db')

# Query total surplus
cursor = conn.execute("""
    SELECT SUM(total_surplus) 
    FROM trades 
    WHERE run_id = ?
""", (run_id,))

# Query surplus distribution
cursor = conn.execute("""
    SELECT buyer_surplus, seller_surplus 
    FROM trades 
    WHERE run_id = ?
""", (run_id,))
```

**Metrics to Calculate:**
- Total surplus across all trades
- Average surplus per trade
- Surplus distribution (Gini coefficient)
- Convergence time (ticks to stability)
- Trade success rate

### Comparison Framework

**Create comparison tables:**

| Protocol | Total Surplus | Avg Surplus/Trade | Gini Coefficient | Convergence (ticks) |
|----------|---------------|-------------------|-------------------|---------------------|
| Greedy   | X.X           | Y.Y               | Z.Z               | N                   |
| Legacy   | X.X           | Y.Y               | Z.Z               | N                   |
| Random   | X.X           | Y.Y               | Z.Z               | N                   |

---

## Classroom Usage Guide

### Lecture Integration

**1. Efficiency vs Fairness (Greedy Matching)**
- **Lecture Topic:** Welfare economics, market failure
- **Exercise:** Run greedy vs legacy matching
- **Discussion:** First-best vs second-best outcomes
- **Takeaway:** Markets require trade-offs

**2. Information Economics (Myopic Search)**
- **Lecture Topic:** Search costs, information asymmetry
- **Exercise:** Run myopic vs full vision search
- **Discussion:** Value of information, market thickness
- **Takeaway:** Information is valuable resource

**3. Bargaining Theory (TIOL)**
- **Lecture Topic:** Bargaining power, market power
- **Exercise:** Run TIOL with different power levels
- **Discussion:** Institutional design, fairness
- **Takeaway:** Rules affect outcomes

### Assignment Ideas

**1. Protocol Comparison Report**
- Run 3-4 protocols on same scenario
- Calculate quantitative metrics
- Write comparison report
- Discuss economic implications

**2. Parameter Sensitivity Analysis**
- Vary protocol parameters (e.g., proposer_power)
- Measure effect on outcomes
- Create sensitivity plots
- Discuss policy implications

**3. Scenario Design**
- Create custom scenario demonstrating concept
- Test with different protocols
- Document findings
- Present to class

### Laboratory Exercises

**Exercise 1: Efficiency Measurement**
1. Run greedy matching scenario
2. Calculate total surplus
3. Compare with legacy matching
4. Discuss efficiency-fairness trade-off
5. Write report

**Exercise 2: Information Value**
1. Run myopic search scenario
2. Measure convergence time
3. Compare with full vision
4. Calculate information value
5. Discuss search costs

**Exercise 3: Bargaining Power**
1. Run TIOL with different power levels
2. Measure surplus distributions
3. Compare with fair bargaining
4. Discuss policy implications
5. Present findings

---

## Technical Notes

### Protocol Availability

All Phase 2b protocols are available via:
- **YAML configuration:** Set in scenario file
- **CLI override:** Via simulation constructor
- **Protocol registry:** Automatic discovery

### Determinism

All protocols use **seeded RNG** for deterministic behavior:
- Same seed → same results
- Useful for comparisons
- Reproducible research

### Performance

**Typical performance:**
- Greedy matching: O(n²) - enumerates all pairs
- Myopic search: O(1) - limited vision
- TIOL bargaining: O(K) - K = feasible trades

**Benchmarking:**
```bash
python scripts/benchmark_performance.py --scenario exchange
```

---

## Troubleshooting

### Common Issues

**1. Protocol Not Found**
- Check protocol name spelling
- Verify protocol is registered
- Check YAML syntax

**2. Scenario Won't Run**
- Verify YAML file is valid
- Check parameter values
- Review error messages

**3. Unexpected Results**
- Check seed consistency
- Verify protocol parameters
- Review telemetry data

### Getting Help

- **Code Issues:** Check test files for examples
- **Scenario Issues:** Review existing scenario files
- **Protocol Issues:** Check protocol docstrings
- **Documentation:** See `docs/protocols_10-27/README.md`

---

## Next Steps

### For Instructors

1. **Review this guide** for accuracy
2. **Test scenarios** with actual simulations
3. **Develop exercises** tailored to your curriculum
4. **Create handouts** summarizing key concepts
5. **Prepare discussion questions** for lectures

### For Students

1. **Read protocol descriptions** before exercises
2. **Run baseline scenarios** to understand behavior
3. **Experiment with parameters** to see effects
4. **Compare outcomes** quantitatively
5. **Document findings** in reports

### For Developers

1. **Verify all scenarios work** correctly
2. **Test comparison exercises** end-to-end
3. **Add quantitative analysis tools** if needed
4. **Create visualization scripts** for comparisons
5. **Enhance documentation** based on feedback

---

## References

### Economic Theory

- **Welfare Economics:** Mas-Colell, Whinston, Green (1995)
- **Information Economics:** Stigler (1961) "The Economics of Information"
- **Bargaining Theory:** Rubinstein (1982) "Perfect Equilibrium in a Bargaining Model"
- **Matching Theory:** Roth & Sotomayor (1990) "Two-Sided Matching"

### VMT Documentation

- `docs/protocols_10-27/master_implementation_plan.md` - Full roadmap
- `docs/protocols_10-27/README.md` - Protocol overview
- `docs/1_project_overview.md` - Project documentation
- `docs/2_technical_manual.md` - Technical details

---

## Document Status

**Status:** Preliminary - AI-Generated  
**Version:** 0.1  
**Last Updated:** 2025-01-XX  
**Next Review:** After human verification

**TODO:**
- [ ] Verify all scenarios execute correctly
- [ ] Test all comparison exercises
- [ ] Add quantitative examples with actual numbers
- [ ] Create visualization examples
- [ ] Add screenshots or diagrams
- [ ] Review economic interpretations
- [ ] Add troubleshooting examples
- [ ] Create assignment rubrics

---

**Note:** This document will be refined based on actual classroom use and feedback. Please report issues, suggest improvements, and share successful teaching strategies.

