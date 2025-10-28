# Protocol Test Scenarios (Phase 2a)

Four scenarios for testing and comparing Phase 2a baseline protocols. Each uses an 8×8 grid with 10 agents and mixed utility functions (40% CES, 40% Translog, 20% Linear).

## Scenarios

### 1. protocol_comparison_baseline.yaml
**ALL THREE new protocols together**

```yaml
search_protocol: "random_walk"
matching_protocol: "random"
bargaining_protocol: "split_difference"
```

**Purpose:** Full baseline behavior with minimal optimization  
**Expected:** Lowest efficiency - demonstrates architecture with all Phase 2a protocols  
**Usage:** `python launcher.py scenarios/pro_tests/protocol_comparison_baseline.yaml --seed 42`

---

### 2. legacy_with_random_walk.yaml
**Isolates search protocol impact**

```yaml
search_protocol: "random_walk"
# matching & bargaining: legacy defaults
```

**Purpose:** Measure value of information in search phase  
**Expected:** Lower efficiency than full legacy due to random exploration  
**Comparison:** vs foundational_barter_demo.yaml (all legacy)

---

### 3. legacy_with_random_matching.yaml
**Isolates matching protocol impact**

```yaml
matching_protocol: "random"
# search & bargaining: legacy defaults
```

**Purpose:** Measure value of surplus-based pairing  
**Expected:** Lower efficiency than full legacy due to random pairing  
**Comparison:** Agents find good partners (good search) but pair randomly

---

### 4. legacy_with_split_difference.yaml
**Isolates bargaining protocol impact**

```yaml
bargaining_protocol: "split_difference"
# search & matching: legacy defaults
```

**Purpose:** Compare distributional effects of bargaining protocols  
**Expected:** Similar total efficiency, different surplus distribution  
**Comparison:** Equal splits vs first-feasible trade selection

---

## Protocol Options Reference

### Search Protocols
- `"legacy"` - Distance-discounted utility-based search (default)
- `"random_walk"` - Pure stochastic exploration

### Matching Protocols
- `"legacy_three_pass"` - Mutual consent + greedy surplus fallback (default)
- `"random"` - Random pairing

### Bargaining Protocols
- `"legacy_compensating_block"` - First feasible trade (default)
- `"split_difference"` - Equal surplus division

---

## Running Comparisons

```bash
# Full legacy baseline (for reference)
python launcher.py scenarios/foundational_barter_demo.yaml --seed 42

# All new protocols
python launcher.py scenarios/pro_tests/protocol_comparison_baseline.yaml --seed 42

# Isolated comparisons
python launcher.py scenarios/pro_tests/legacy_with_random_walk.yaml --seed 42
python launcher.py scenarios/pro_tests/legacy_with_random_matching.yaml --seed 42
python launcher.py scenarios/pro_tests/legacy_with_split_difference.yaml --seed 42
```

---

## CLI Override Examples

Protocols in YAML can be overridden at runtime:

```bash
# Override search protocol specified in YAML
python launcher.py scenarios/pro_tests/protocol_comparison_baseline.yaml \
  --search-protocol legacy \
  --seed 42

# Try different protocol combination on same scenario
python launcher.py scenarios/pro_tests/legacy_with_random_walk.yaml \
  --matching-protocol random \
  --seed 42
```

**Resolution Order:** CLI args > YAML config > legacy defaults

---

## Phase 2a Validation

These scenarios validate:
- ✅ Protocol configuration works in YAML
- ✅ Protocols can be mixed and matched
- ✅ CLI overrides work correctly
- ✅ Each protocol category has working baseline
- ✅ Architecture supports comparison experiments

---

> claude-sonnet-4.5: Phase 2a protocol test scenarios created with YAML protocol configuration.

