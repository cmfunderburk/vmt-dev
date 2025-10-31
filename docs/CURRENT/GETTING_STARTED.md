# Getting Started with VMT Post-Money Removal

**Last Updated:** 2025-10-31  
**Status:** Barter-only economy, 6/9 protocols working

---

## 🎯 **Quick Start: Run a Demo**

```bash
# Activate virtualenv
source venv/bin/activate

# Run simplest 2-agent barter scenario
python main.py scenarios/demos/minimal_2agent.yaml --ticks 15

# Run classic Edgeworth box (4 agents)
python main.py scenarios/demos/edgeworth_box_4agent.yaml --ticks 20

# Compare matching protocols
python main.py scenarios/demos/protocol_comparison_4agent.yaml \
  --override "protocol_config.matching.protocol=greedy_surplus"
```

---

## 📊 **What's Working Right Now**

### **✅ Fully Functional (54 passing tests)**

**Matching Protocols (3/3):**
1. `legacy_three_pass` - Mutual consent + greedy fallback
2. `greedy_surplus` - Welfare-maximizing central planner
3. `random_matching` - Random pairing baseline

**Bargaining Protocols (2/3):**
1. `split_difference` - Equal surplus division (fairness)
2. `legacy_compensating_block` - First acceptable trade

**Search Protocols (1/3):**
1. `legacy_distance_discounted` - Distance-discounted preferences

### **⚠️ Not Yet Working (33 failing tests)**
- `myopic` search (information-constrained)
- `random_walk` search (stochastic exploration)
- `take_it_or_leave_it` bargaining (asymmetric power)

---

## 🎓 **Demo Scenarios** (Ready to Use)

All scenarios in `scenarios/demos/`:

### **1. Minimal 2-Agent** (`minimal_2agent.yaml`)
- **Purpose:** Simplest barter trade demonstration
- **Setup:** Agent 0 has (8A, 2B), Agent 1 has (2A, 8B)
- **Runtime:** ~15 ticks, <1 second
- **Expected:** 1-2 trades, balanced inventories
- **Test Result:** ✅ Trades occurred! (8,2) → (5,7) and (2,8) → (5,5)

### **2. Edgeworth Box** (`edgeworth_box_4agent.yaml`)
- **Purpose:** Classic gains-from-trade with 2 agent types
- **Setup:** 2 A-rich agents, 2 B-rich agents
- **Runtime:** ~20 ticks, <2 seconds
- **Expected:** 3-6 trades, Pareto improvement

### **3. Protocol Comparison** (`protocol_comparison_4agent.yaml`)
- **Purpose:** Compare matching algorithms
- **Protocols:** Switch between `greedy_surplus`, `legacy_three_pass`, `random_matching`
- **Expected:** Different welfare outcomes

### **4. Bargaining Comparison** (`bargaining_comparison_6agent.yaml`)
- **Purpose:** Compare fairness vs efficiency
- **Protocols:** Switch between `split_difference`, `legacy_compensating_block`
- **Expected:** Different surplus distributions

---

## 🔬 **Example Analysis Workflow**

### **Compare Matching Algorithms:**

```bash
# 1. Run with central planner (welfare-optimal)
python main.py scenarios/demos/protocol_comparison_4agent.yaml \
  --override "protocol_config.matching.protocol=greedy_surplus" \
  --output results_greedy.db

# 2. Run with decentralized matching
python main.py scenarios/demos/protocol_comparison_4agent.yaml \
  --override "protocol_config.matching.protocol=legacy_three_pass" \
  --output results_legacy.db

# 3. Run with random matching (baseline)
python main.py scenarios/demos/protocol_comparison_4agent.yaml \
  --override "protocol_config.matching.protocol=random_matching" \
  --output results_random.db

# 4. Compare results
python analysis_tools/compare_runs.py results_*.db
```

### **Metrics to Compare:**
- Total trades executed
- Final total utility (welfare)
- Time to convergence
- Surplus distribution (fairness)

---

## 📖 **Protocol Configuration**

All working protocols can be configured in scenario YAML:

```yaml
protocol_config:
  search:
    protocol: "legacy_distance_discounted"
    params: {}
  
  matching:
    protocol: "greedy_surplus"  # or legacy_three_pass, random_matching
    params:
      beta: 0.95  # Distance discount factor
  
  bargaining:
    protocol: "split_difference"  # or legacy_compensating_block
    params:
      epsilon: 0.000000001  # Surplus threshold
```

---

## 🎯 **Pedagogical Use Cases**

### **Undergraduate Microeconomics:**
- `minimal_2agent.yaml` - Demonstrate gains from trade
- `edgeworth_box_4agent.yaml` - Pareto efficiency & contract curve
- Show how complementary endowments create trade

### **Graduate Microeconomics:**
- `protocol_comparison_4agent.yaml` - Matching theory
- Compare welfare under different institutions
- `bargaining_comparison_6agent.yaml` - Nash bargaining solution

### **Market Design:**
- Central planner vs decentralized matching
- Fairness (equal split) vs efficiency (first acceptable)
- Effect of spatial frictions on trade

---

## 📊 **Current Capabilities**

**✅ Fully Implemented:**
- Pure barter economy (A↔B trades)
- 5 utility functions (CES, Linear, Quadratic, Translog, Stone-Geary)
- Resource foraging & regeneration
- Mode scheduling (trade/forage/both)
- Spatial search with vision radius
- SQLite telemetry logging
- Protocol modularization
- Deterministic reproducibility (seeds)

**✅ Working Protocol Combinations:**
- Default: legacy search + legacy matching + legacy bargaining
- Welfare: legacy search + greedy matching + split difference
- Baseline: legacy search + random matching + split difference

**⚠️ Need Fixes:**
- 3 protocols have test failures (myopic, random_walk, take_it_or_leave_it)
- Protocol context/signature updates needed

---

## 🚀 **Next Steps**

### **Immediate (demonstrations):**
1. ✅ Use working protocols for demos
2. ✅ Create small scenarios (2-10 agents)
3. ⬜ Run protocol comparisons
4. ⬜ Analyze telemetry data

### **Short-term (fixes):**
1. ⬜ Fix failing protocol tests
2. ⬜ Update protocol signatures
3. ⬜ Add protocol documentation

### **Medium-term (enhancements):**
1. ⬜ Add more search protocols
2. ⬜ Create analysis tools
3. ⬜ Build tutorial notebooks

---

## 📚 **Documentation**

- **[Protocol Status Report](PROTOCOL_STATUS_REPORT.md)** - Detailed protocol inventory
- **[Demo Scenarios README](../../scenarios/demos/README.md)** - Scenario catalog
- **[Technical Manual](../2_technical_manual.md)** - Complete system documentation
- **[Architecture](../BIGGEST_PICTURE/vision_and_architecture.md)** - System design

---

## ✨ **Example Output**

```
Testing minimal_2agent.yaml...
✓ Loaded successfully
  Agents: 2
  Agent 0 initial: A=8, B=2
  Agent 1 initial: A=2, B=8
✓ Ran 15 ticks
  Agent 0 final: A=5, B=7  ← Traded A for B
  Agent 1 final: A=5, B=5  ← Traded B for A

Result: Both agents improved utility through trade!
```

---

## 🆘 **Troubleshooting**

**Scenario won't load:**
- Check epsilon format (use `0.000000000001` not `1e-12`)
- Check CES parameter is `rho` not `sigma`
- Verify all required fields present

**No trades occurring:**
- Increase ticks (try 20-30)
- Check `interaction_radius` (must be ≥1)
- Verify agents have complementary endowments
- Check `dA_max` allows sufficient trade size

**Protocol not found:**
- List available: `python -c "from vmt_engine.protocols.registry import list_all_protocols; print(list_all_protocols())"`
- Check spelling matches exactly
- Verify protocol is registered (check imports in `__init__.py`)

---

**Ready to experiment!** 🎉

Start with `minimal_2agent.yaml` and work up to more complex scenarios.

