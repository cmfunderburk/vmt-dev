# VMT Demonstration Scenarios

Small-scale scenarios (2-10 agents) designed to demonstrate specific functionality and pedagogical concepts.

## 📁 Scenario Catalog

### **Pedagogical Scenarios** (2-4 agents)

#### 1. **`minimal_2agent.yaml`** - Simplest Barter Trade
- **Agents:** 2
- **Grid:** 5×5
- **Purpose:** Show basic A↔B trade between complementary endowments
- **Key Feature:** One agent has more A, other has more B
- **Protocol:** Default (legacy) - deterministic
- **Expected:** 1-2 trades within 10 ticks

#### 2. **`edgeworth_box_4agent.yaml`** - Classic Edgeworth Box
- **Agents:** 4 (2 of each type)
- **Grid:** 8×8
- **Purpose:** Demonstrate gains from trade with 2 agent types
- **Key Feature:** Type 1: A-rich, Type 2: B-rich
- **Protocol:** Default (legacy)
- **Expected:** Multiple trades, convergence to Pareto frontier

#### 3. **`protocol_comparison_4agent.yaml`** - Compare Matching Algorithms
- **Agents:** 4
- **Grid:** 8×8
- **Purpose:** Compare central planner vs decentralized vs random matching
- **Protocol:** Configurable (switch between 3 matching protocols)
- **Expected:** Different match rates and welfare outcomes

### **Intermediate Scenarios** (5-10 agents)

#### 4. **`spatial_search_8agent.yaml`** - Spatial Search Dynamics
- **Agents:** 8
- **Grid:** 12×12
- **Purpose:** Show how spatial distribution affects trade
- **Key Feature:** Resources clustered, agents search spatially
- **Protocol:** Legacy distance-discounted search
- **Expected:** Agents move toward trading partners, spatial clustering

#### 5. **`bargaining_comparison_6agent.yaml`** - Compare Bargaining Protocols
- **Agents:** 6 (3 pairs)
- **Grid:** 10×10
- **Purpose:** Compare split-difference vs first-acceptable bargaining
- **Protocol:** Configurable (switch bargaining protocols)
- **Expected:** Different surplus distributions (fairness vs efficiency)

#### 6. **`utility_mix_10agent.yaml`** - Mixed Utility Functions
- **Agents:** 10
- **Grid:** 15×15
- **Purpose:** Show heterogeneous preferences
- **Key Feature:** Mix of CES, Linear, and Quadratic utilities
- **Protocol:** Default
- **Expected:** Rich trading patterns from heterogeneous preferences

### **Mode Scheduling Demos** (5-8 agents)

#### 7. **`mode_schedule_demo_5agent.yaml`** - Forage vs Trade Modes
- **Agents:** 5
- **Grid:** 10×10
- **Purpose:** Demonstrate mode scheduling (forage → trade → both)
- **Key Feature:** Mode changes every 5 ticks
- **Protocol:** Default
- **Expected:** Behavior changes with mode

#### 8. **`resource_competition_8agent.yaml`** - Resource Claiming
- **Agents:** 8
- **Grid:** 12×12
- **Purpose:** Show single-harvester resource claiming
- **Key Feature:** High resource density, enforce_single_harvester: true
- **Protocol:** Default
- **Expected:** Spatial dispersion to avoid competition

---

## 🎯 **Usage Examples**

### Run a demo scenario:
```bash
python main.py scenarios/demos/minimal_2agent.yaml --ticks 20
```

### Compare protocols:
```bash
# Run with different matching protocols
python main.py scenarios/demos/protocol_comparison_4agent.yaml \
  --override "protocol_config.matching.protocol=greedy_surplus"

python main.py scenarios/demos/protocol_comparison_4agent.yaml \
  --override "protocol_config.matching.protocol=random_matching"
```

### Batch run for comparison:
```bash
for protocol in greedy_surplus legacy_three_pass random_matching; do
  python main.py scenarios/demos/protocol_comparison_4agent.yaml \
    --override "protocol_config.matching.protocol=$protocol" \
    --output "results_${protocol}.db"
done
```

---

## 📊 **Expected Outcomes**

### **Minimal 2-Agent Trade**
- **Trades:** 1-3 total
- **Convergence:** <10 ticks
- **Surplus:** ~2-5 utility units per agent

### **Edgeworth Box (4 agents)**
- **Trades:** 3-6 total
- **Convergence:** 10-15 ticks
- **Pattern:** Type 1 trades A for B, Type 2 trades B for A

### **Protocol Comparison**
- **Greedy Surplus:** Highest total welfare, most trades
- **Legacy Three-Pass:** Medium welfare, mutual consent required
- **Random Matching:** Lowest welfare, baseline comparison

### **Bargaining Comparison**
- **Split Difference:** Equal surplus for both parties
- **Legacy Compensating Block:** First acceptable trade (may favor one party)

---

## 🔬 **Pedagogical Use**

### **Undergraduate Microeconomics:**
- `minimal_2agent.yaml` - Gains from trade
- `edgeworth_box_4agent.yaml` - Pareto efficiency
- `mode_schedule_demo_5agent.yaml` - Opportunity cost

### **Graduate Microeconomics:**
- `protocol_comparison_4agent.yaml` - Matching theory
- `bargaining_comparison_6agent.yaml` - Nash bargaining solution
- `spatial_search_8agent.yaml` - Search and matching models

### **Market Design:**
- Compare welfare under different matching algorithms
- Analyze fairness vs efficiency tradeoffs
- Study spatial frictions and search costs

---

## 📝 **Configuration Notes**

All demo scenarios use:
- **Small grids:** 5×5 to 15×15
- **Short runs:** 10-50 ticks
- **Simple utilities:** CES with σ ∈ [0.3, 0.7]
- **Moderate resources:** 20-30% density
- **No trade cooldowns:** For clearer cause-effect

Scenarios are designed to complete in <10 seconds for rapid iteration and testing.

---

**See individual YAML files for detailed configurations.**

