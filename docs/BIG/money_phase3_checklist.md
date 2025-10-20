### Money Implementation — Phase 3: Mixed Regimes

Author: VMT Assistant
Date: 2025-10-19
**Revised**: 2025-10-20 (moved ahead of Phase 3 to validate quasilinear first)

**Prerequisite**: Phase 2 complete (quasilinear money trades working)

**Goal**: Enable `mixed` exchange regime where agents can trade both goods-for-money and goods-for-goods, with deterministic tie-breaking (money-first).

**Success Criteria**:
- `exchange_regime = "mixed"` allows all six exchange pairs
- Tie-breaking policy (money-first) implemented and tested
- Mode transitions (temporal × type control) work correctly
- Test scenarios demonstrate regime interaction with mode_schedule
- **All working with quasilinear utility (fixed λ)**

**Note**: This phase uses `money_mode: quasilinear` with fixed λ. Phase 3 (KKT adaptive λ) is deferred to validate simple case first.

---

## Pre-Phase 4 Verification

- [ ] **Verify Phase 2 complete**
  ```bash
  pytest tests/test_money_phase2*.py -v
  python main.py scenarios/money_test_basic.yaml --seed 42
  # Verify money trades occur (money_only regime)
  ```

- [ ] **Create Phase 4 branch**
  ```bash
  git checkout -b feature/money-phase4-mixed-regimes
  ```

- [ ] **Create mixed regime test scenarios**
  ```bash
  # Create scenarios/money_test_mixed.yaml
  # Create scenarios/money_test_mode_interaction.yaml
  ```

---

## Part 1: Test Scenario Creation

### 1.1) Create mixed regime scenario

**File**: `scenarios/money_test_mixed.yaml` (create new)

- [ ] **Write mixed regime scenario**
  ```yaml
  schema_version: 1
  name: "Mixed Exchange Regime Test"
  N: 12
  agents: 8
  
  initial_inventories:
    A: [10, 8, 6, 4, 2, 0, 5, 7]
    B: [0, 2, 4, 6, 8, 10, 3, 5]
    M: [50, 100, 150, 50, 100, 150, 75, 125]
  
  utilities:
    mix:
      - type: ces
        weight: 1.0
        params:
          rho: 0.5
          wA: 0.55
          wB: 0.45
  
  params:
    spread: 0.1
    vision_radius: 12
    interaction_radius: 1
    move_budget_per_tick: 1
    dA_max: 4
    forage_rate: 1
    
    # Mixed regime params
    exchange_regime: mixed
    money_mode: quasilinear
    money_scale: 1
    lambda_money: 1.0
  
  resource_seed:
    density: 0.2
    amount: 4
  ```

### 1.2) Create mode × regime interaction scenario

**File**: `scenarios/money_test_mode_interaction.yaml` (create new)

- [ ] **Write mode interaction scenario**
  ```yaml
  schema_version: 1
  name: "Mode Schedule × Exchange Regime Interaction"
  N: 15
  agents: 6
  
  # Scenario with mode_schedule (temporal control)
  mode_schedule:
    type: global_cycle
    forage_ticks: 10
    trade_ticks: 15
    start_mode: forage
  
  initial_inventories:
    A: [10, 5, 0, 8, 3, 2]
    B: [0, 5, 10, 2, 7, 8]
    M: [100, 100, 100, 100, 100, 100]
  
  utilities:
    mix:
      - type: ces
        weight: 1.0
        params:
          rho: 0.3
          wA: 0.6
          wB: 0.4
  
  params:
    spread: 0.05
    vision_radius: 15
    interaction_radius: 1
    move_budget_per_tick: 2
    dA_max: 3
    forage_rate: 2
    
    # Mixed regime with mode schedule
    exchange_regime: mixed
    money_mode: kkt_lambda
    money_scale: 1
    lambda_money: 1.0
    lambda_update_rate: 0.15
    lambda_bounds:
      lambda_min: 0.00001
      lambda_max: 100000.0
  
  resource_seed:
    density: 0.25
    amount: 5
  ```

---

## Part 2: Trade Pair Enumeration and Ranking

### 2.1) Implement full pair enumeration for mixed mode

**File**: `src/vmt_engine/systems/trading.py`

- [ ] **Update `_get_allowed_pairs()` for mixed regime**
  ```python
  def _get_allowed_pairs(self, regime: str) -> list[tuple[str, str]]:
      """
      Get allowed (good_sold, good_paid) pairs based on regime.
      
      Returns list of tuples: (good agent gives up, good agent receives)
      From buyer perspective: receives good_sold, pays good_paid
      """
      if regime == "barter_only":
          return [("A", "B"), ("B", "A")]
      elif regime == "money_only":
          return [("A", "M"), ("B", "M")]
      elif regime in ["mixed", "mixed_liquidity_gated"]:
          # All six permutations
          return [
              ("A", "M"),  # Buy A with money
              ("B", "M"),  # Buy B with money
              ("A", "B"),  # Buy A with B (barter)
              ("B", "A"),  # Buy B with A (barter)
              # Note: We don't typically have agents "buying" money
              # but the pair ("M", "A") would mean: give money, get A
              # which is the seller's perspective of ("A", "M")
              # So we keep pairs from buyer perspective only
          ]
      else:
          return []
  ```

### 2.2) Implement money-first tie-breaking

- [ ] **Add tie-breaking logic to trade ranking**
  ```python
  def _rank_trade_candidates(self, candidates: list[TradeCandidate]) -> list[TradeCandidate]:
      """
      Rank trade candidates by total surplus, with tie-breaking.
      
      Tie-break order (money-first):
      1. Total surplus (descending)
      2. Pair type priority: A↔M < B↔M < A↔B
      3. Agent pair (min_id, max_id) lexicographic
      
      TradeCandidate should include:
          - buyer_id, seller_id
          - good_sold, good_paid
          - dX, dY
          - buyer_surplus, seller_surplus
          - total_surplus
      """
      # Define pair type priority (lower number = higher priority)
      PAIR_PRIORITY = {
          ("A", "M"): 0,
          ("B", "M"): 1,
          ("M", "A"): 2,  # Seller perspective of A<->M
          ("M", "B"): 3,  # Seller perspective of B<->M
          ("A", "B"): 4,
          ("B", "A"): 5,
      }
      
      def sort_key(candidate):
          total_surplus = candidate.buyer_surplus + candidate.seller_surplus
          pair_type = (candidate.good_sold, candidate.good_paid)
          pair_priority = PAIR_PRIORITY.get(pair_type, 99)
          agent_pair = (min(candidate.buyer_id, candidate.seller_id),
                       max(candidate.buyer_id, candidate.seller_id))
          
          # Return tuple for sorting:
          # - Negate surplus for descending order
          # - pair_priority ascending (lower = better)
          # - agent_pair ascending
          return (-total_surplus, pair_priority, agent_pair)
      
      return sorted(candidates, key=sort_key)
  ```

- [ ] **Test tie-breaking**
  ```python
  # In tests/test_mixed_regime_tie_breaking.py (create new)
  def test_money_first_tie_breaking():
      """Verify money-first tie-breaking when surplus equal."""
      from dataclasses import dataclass
      
      @dataclass
      class TradeCandidate:
          buyer_id: int
          seller_id: int
          good_sold: str
          good_paid: str
          dX: int
          dY: int
          buyer_surplus: float
          seller_surplus: float
      
      # Create three candidates with equal total surplus
      candidate_money = TradeCandidate(
          buyer_id=0, seller_id=1,
          good_sold="A", good_paid="M",
          dX=2, dY=10,
          buyer_surplus=5.0, seller_surplus=5.0
      )
      
      candidate_barter = TradeCandidate(
          buyer_id=0, seller_id=1,
          good_sold="A", good_paid="B",
          dX=2, dY=3,
          buyer_surplus=5.0, seller_surplus=5.0
      )
      
      candidates = [candidate_barter, candidate_money]
      ranked = _rank_trade_candidates(candidates)
      
      # Money trade should be first (higher priority)
      assert ranked[0].good_paid == "M"
      assert ranked[1].good_paid == "B"
  ```

---

## Part 3: TradeSystem Enhancements

### 3.1) Implement multi-pair candidate generation

**File**: `src/vmt_engine/systems/trading.py`

- [ ] **Extend matching logic to try all permissible pairs**
  ```python
  class TradeSystem:
      def execute(self, sim: "Simulation") -> None:
          # Check temporal mode
          if sim.current_mode not in ["trade", "both"]:
              return
          
          # Get permissible pairs based on exchange_regime
          allowed_pairs = self._get_allowed_pairs(sim.params['exchange_regime'])
          
          # Build list of all potential trades
          candidates = []
          
          # Find all agent pairs within interaction radius
          for buyer in sim.agents:
              neighbor_ids = sim.spatial_index.query_radius(
                  buyer.pos, sim.params['interaction_radius']
              )
              
              for seller_id in neighbor_ids:
                  if seller_id == buyer.id:
                      continue
                  
                  seller = sim.agent_by_id[seller_id]
                  
                  # Check cooldown
                  if self._in_cooldown(buyer, seller, sim.tick):
                      continue
                  
                  # Try each allowed pair type
                  for good_sold, good_paid in allowed_pairs:
                      # Get quotes
                      price = self._get_price(buyer, seller, good_sold, good_paid)
                      if price is None:
                          continue
                      
                      # Search for feasible trade
                      result = find_compensating_block_generic(
                          buyer, seller, good_sold, good_paid, 
                          price, sim.params['dA_max'], sim.params['epsilon']
                      )
                      
                      if result is not None:
                          dX, dY, buyer_surplus, seller_surplus = result
                          candidates.append(TradeCandidate(
                              buyer_id=buyer.id,
                              seller_id=seller.id,
                              good_sold=good_sold,
                              good_paid=good_paid,
                              dX=dX, dY=dY,
                              buyer_surplus=buyer_surplus,
                              seller_surplus=seller_surplus
                          ))
          
          # Rank candidates
          ranked = self._rank_trade_candidates(candidates)
          
          # Execute trades (one per agent pair per tick)
          executed_pairs = set()
          for candidate in ranked:
              pair_key = (min(candidate.buyer_id, candidate.seller_id),
                         max(candidate.buyer_id, candidate.seller_id))
              
              if pair_key not in executed_pairs:
                  self._execute_trade(candidate, sim)
                  executed_pairs.add(pair_key)
  ```

### 3.2) Add pair-type selection logging

- [ ] **Log which pair type was chosen**
  ```python
  # In _execute_trade():
  if sim.telemetry:
      sim.telemetry.log_trade(
          # ... existing params ...
          exchange_pair_type=f"{candidate.good_sold}<->{candidate.good_paid}",
          # ...
      )
  ```

---

## Part 4: Mode × Regime Interaction

### 4.1) Verify two-layer control architecture

**File**: `src/vmt_engine/simulation.py`

- [ ] **Ensure `_get_active_exchange_pairs()` respects mode**
  ```python
  def _get_active_exchange_pairs(self) -> list[str]:
      """
      Determine which exchange pairs are currently active.
      Combines temporal (mode_schedule) and type (exchange_regime) control.
      """
      # Temporal control: if not in trade mode, no pairs active
      if self.current_mode == "forage":
          return []
      
      # Type control: which pairs are permissible
      regime = self.params['exchange_regime']
      
      if regime == "barter_only":
          return ["A<->B"]
      elif regime == "money_only":
          return ["A<->M", "B<->M"]
      elif regime in ["mixed", "mixed_liquidity_gated"]:
          return ["A<->M", "B<->M", "A<->B"]
      else:
          return []
  ```

- [ ] **Test mode × regime interaction**
  ```python
  # In tests/test_mode_regime_interaction.py (create new)
  def test_forage_mode_blocks_all_trades():
      """Verify forage mode blocks all trades regardless of regime."""
      # Load scenario with mode_schedule and mixed regime
      # At tick in forage mode
      # Verify: no trades execute (even if agents adjacent)
      # Verify: active_pairs = []
      pass
  
  def test_trade_mode_respects_regime():
      """Verify trade mode uses correct pairs per regime."""
      # Load mixed regime scenario
      # At tick in trade mode
      # Verify: active_pairs includes both money and barter
      # Verify: trades of both types can occur
      pass
  ```

---

## Part 5: Telemetry Enhancements

### 5.1) Log pair type distribution

- [ ] **Add query for pair type counts**
  ```python
  # In scripts/analyze_trade_distribution.py (create new)
  import sqlite3
  
  def analyze_pair_distribution(db_path: str, run_id: int):
      conn = sqlite3.connect(db_path)
      cursor = conn.execute("""
          SELECT exchange_pair_type, COUNT(*) as count
          FROM trades
          WHERE run_id = ?
          GROUP BY exchange_pair_type
          ORDER BY count DESC
      """, (run_id,))
      
      print(f"Trade pair distribution for run {run_id}:")
      for pair_type, count in cursor:
          print(f"  {pair_type}: {count}")
      
      conn.close()
  
  if __name__ == '__main__':
      import sys
      analyze_pair_distribution(sys.argv[1], int(sys.argv[2]))
  ```

### 5.2) Visualize mode transitions

- [ ] **Create mode timeline visualization**
  ```python
  # In scripts/plot_mode_timeline.py (create new)
  import sqlite3
  import matplotlib.pyplot as plt
  import matplotlib.patches as mpatches
  
  def plot_mode_timeline(db_path: str, run_id: int):
      conn = sqlite3.connect(db_path)
      cursor = conn.execute("""
          SELECT tick, current_mode, exchange_regime 
          FROM tick_states 
          WHERE run_id = ?
          ORDER BY tick
      """, (run_id,))
      
      data = list(cursor)
      conn.close()
      
      if not data:
          print("No tick_states data found")
          return
      
      ticks = [row[0] for row in data]
      modes = [row[1] for row in data]
      
      # Color code modes
      mode_colors = {'forage': 'green', 'trade': 'blue', 'both': 'purple'}
      colors = [mode_colors.get(m, 'gray') for m in modes]
      
      plt.figure(figsize=(12, 3))
      plt.scatter(ticks, [0]*len(ticks), c=colors, marker='|', s=500)
      plt.yticks([])
      plt.xlabel('Tick')
      plt.title('Mode Timeline')
      
      # Legend
      patches = [mpatches.Patch(color=c, label=m) for m, c in mode_colors.items()]
      plt.legend(handles=patches)
      
      plt.tight_layout()
      plt.show()
  
  if __name__ == '__main__':
      import sys
      plot_mode_timeline(sys.argv[1], int(sys.argv[2]))
  ```

---

## Part 6: Testing

### 6.1) Unit tests

**File**: `tests/test_mixed_regime.py` (create new)

- [ ] **Test pair enumeration**
  ```python
  def test_mixed_regime_pair_enumeration():
      """Verify mixed regime returns all pair types."""
      pairs = _get_allowed_pairs("mixed")
      assert ("A", "M") in pairs
      assert ("B", "M") in pairs
      assert ("A", "B") in pairs
      # Should have at least these 3 types (maybe 4 with reverse)
  
  def test_barter_only_excludes_money():
      """Verify barter_only excludes money pairs."""
      pairs = _get_allowed_pairs("barter_only")
      assert all("M" not in pair for pair in pairs)
  
  def test_money_only_excludes_barter():
      """Verify money_only excludes goods-for-goods."""
      pairs = _get_allowed_pairs("money_only")
      # Should only have pairs involving M
      assert all("M" in pair for pair in pairs)
  ```

- [ ] **Test tie-breaking determinism**
  ```python
  def test_tie_breaking_deterministic():
      """Verify same candidates ranked identically across runs."""
      # Create candidate list
      # Rank twice
      # Verify identical order
      pass
  ```

### 6.2) Integration tests

**File**: `tests/test_mixed_regime_integration.py` (create new)

- [ ] **Test mixed regime scenario**
  ```python
  def test_mixed_regime_scenario_runs():
      """Run mixed regime scenario and verify both trade types occur."""
      from vmt_engine.simulation import Simulation
      from scenarios.loader import load_scenario
      from telemetry.config import LogConfig
      import sqlite3
      import tempfile
      
      with tempfile.TemporaryDirectory() as tmpdir:
          db_path = f"{tmpdir}/test.db"
          config = load_scenario("scenarios/money_test_mixed.yaml")
          log_cfg = LogConfig(use_database=True, db_path=db_path)
          
          sim = Simulation(config, seed=42, log_config=log_cfg)
          sim.run(max_ticks=100)
          sim.close()
          
          # Query for different pair types
          conn = sqlite3.connect(db_path)
          cursor = conn.execute("""
              SELECT DISTINCT exchange_pair_type FROM trades 
              WHERE run_id=1
          """)
          pair_types = {row[0] for row in cursor}
          conn.close()
          
          # Should see both money and barter trades
          has_money = any("M" in p for p in pair_types)
          has_barter = any("B" in p and "A" in p and "M" not in p for p in pair_types)
          
          # At least one type should occur
          # (may not have both if agents don't encounter right opportunities)
          assert len(pair_types) > 0
  ```

- [ ] **Test mode × regime interaction**
  ```python
  def test_mode_regime_interaction():
      """Verify mode_schedule and exchange_regime interact correctly."""
      # Load money_test_mode_interaction.yaml
      # Run simulation
      # Query tick_states
      # Verify: forage mode has empty active_pairs
      # Verify: trade mode has active_pairs from regime
      pass
  ```

### 6.3) Comparative test

- [ ] **Compare regime outcomes**
  ```python
  def test_compare_regimes():
      """Compare outcomes under different regimes with same initial conditions."""
      # Run same base scenario with:
      # 1. barter_only
      # 2. money_only
      # 3. mixed
      
      # Compare:
      # - Total trades
      # - Average surplus
      # - Final utility distribution
      
      # Document in test output for pedagogical value
      pass
  ```

---

## Part 7: Documentation

### 7.1) Update user docs

- [ ] **Document mixed regime in README**
  - Explain when to use mixed vs. single-type regimes
  - Show example scenario configuration
  - Explain tie-breaking policy and rationale

- [ ] **Add regime comparison guide**
  - Create docs/regime_comparison.md
  - Discuss emergence of money vs. barter
  - Pedagogical examples

### 7.2) Update technical docs

- [ ] **Document tie-breaking in typing overview**
- [ ] **Update SSOT with any refinements learned during implementation**
- [ ] **Add examples to mode_schedule documentation showing regime interaction**

---

## Completion Criteria

**Phase 4 is complete when**:

✅ `exchange_regime = "mixed"` allows all six exchange pair types
✅ Money-first tie-breaking implemented and tested
✅ Mode × regime interaction works correctly (temporal × type control)
✅ Test scenarios demonstrate mixed trades
✅ Pair type distribution analysis works
✅ Mode timeline visualization works
✅ All Phase 3 tests still pass
✅ Documentation updated with regime comparison

**Ready for Phase 5 when**:
- Can run mixed regime scenarios with both trade types
- Can verify tie-breaking in logs
- Can demonstrate mode_schedule + exchange_regime interaction
- Telemetry shows correct active_pairs per tick

---

**Estimated effort**: 8-10 hours

See also:
- `money_SSOT_implementation_plan.md` §7-8
- `money_phase3_checklist.md` (prerequisite)
- `money_telemetry_schema.md` (tick_states table)

