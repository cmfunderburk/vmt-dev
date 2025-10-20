### Money Implementation — Phase 6: Polish and Documentation

Author: VMT Assistant
Date: 2025-10-19
**Revised**: 2025-10-20 (moved ahead of Phases 3 & 5 to get demos working with quasilinear)

**Prerequisite**: Phase 4 complete (mixed regimes working with quasilinear)

**Goal**: Polish UI/UX, complete documentation, create demo scenarios, and prepare for release of quasilinear money system.

**Success Criteria**:
- Renderer visualizes money transfers and mode overlays
- Log viewer supports money queries and filters
- Complete documentation for quasilinear money features
- Demo scenarios showcase different regimes (barter_only/money_only/mixed)
- Code review ready for quasilinear implementation
- **Ready for production use with fixed λ**

**Note**: This phase completes the quasilinear money system (Phases 2, 4, 6). Phases 3 (KKT) and 5 (liquidity gating) are advanced features deferred for later.

---

## Pre-Phase 6 Verification

- [ ] **Verify Phase 4 complete**
  ```bash
  pytest tests/test_mixed_regime*.py -v
  python main.py scenarios/money_test_mixed.yaml --seed 42
  # Verify mixed regime works with quasilinear
  ```

- [ ] **Create Phase 6 branch**
  ```bash
  git checkout -b feature/money-phase6-polish
  ```

---

## Part 1: Renderer Enhancements

### 1.1) Money inventory visualization

**File**: `src/vmt_pygame/renderer.py`

- [ ] **Add money display to agent rendering**
  ```python
  def _draw_agent(self, agent: Agent, screen):
      # Existing: draw agent circle, inventory bars
      
      # NEW: Draw money indicator
      if agent.inventory.M > 0:
          # Draw small coin icon or "M" label
          font_small = pygame.font.Font(None, 16)
          money_text = font_small.render(f"${agent.inventory.M}", True, (255, 215, 0))
          screen.blit(money_text, (agent.pos[0] * CELL_SIZE + 5, 
                                   agent.pos[1] * CELL_SIZE + 25))
  ```

- [ ] **Add money transfer animation**
  ```python
  def _animate_trade(self, trade_info: dict, screen):
      """Animate completed trade with money flow."""
      # Existing: draw line between traders
      
      # NEW: If dM > 0, show gold sparkles/flow
      if trade_info.get('dM', 0) > 0:
          # Draw gold particles flowing from buyer to seller
          self._draw_money_flow(
              trade_info['buyer_pos'], 
              trade_info['seller_pos'],
              trade_info['dM']
          )
  
  def _draw_money_flow(self, from_pos, to_pos, amount):
      """Draw animated money transfer."""
      # Golden sparkle effect
      for i in range(5):
          # Interpolate positions
          t = (pygame.time.get_ticks() % 1000) / 1000.0
          x = from_pos[0] + (to_pos[0] - from_pos[0]) * t
          y = from_pos[1] + (to_pos[1] - from_pos[1]) * t
          
          pygame.draw.circle(screen, (255, 215, 0), (int(x), int(y)), 3)
  ```

### 1.2) Mode overlay visualization

- [ ] **Add mode/regime overlay to top-left corner**
  ```python
  def _draw_mode_overlay(self, sim: Simulation, screen):
      """Display current mode and exchange regime."""
      font = pygame.font.Font(None, 24)
      
      # Get mode and regime
      mode = sim.current_mode
      regime = sim.params['exchange_regime']
      active_pairs = sim._get_active_exchange_pairs()
      
      # Choose color based on regime
      if regime == "money_only":
          color = (255, 215, 0)  # Gold
          regime_text = "Monetary Only"
      elif regime == "barter_only":
          color = (0, 255, 0)  # Green
          regime_text = "Barter Only"
      elif regime in ["mixed", "mixed_liquidity_gated"]:
          color = (100, 149, 237)  # Cornflower blue
          regime_text = "Mixed" if regime == "mixed" else "Gated Mixed"
      else:
          color = (128, 128, 128)
          regime_text = regime
      
      # Display mode
      mode_text = font.render(f"Mode: {mode.upper()}", True, (255, 255, 255))
      screen.blit(mode_text, (10, 10))
      
      # Display regime
      regime_text_render = font.render(f"Regime: {regime_text}", True, color)
      screen.blit(regime_text_render, (10, 35))
      
      # Display active pairs
      if active_pairs:
          pairs_str = ", ".join(active_pairs)
          pairs_text = font.render(f"Active: [{pairs_str}]", True, (200, 200, 200))
          screen.blit(pairs_text, (10, 60))
  ```

- [ ] **Call overlay in main render loop**
  ```python
  def render(self, sim: Simulation):
      # ... existing rendering ...
      
      # Add mode overlay
      self._draw_mode_overlay(sim, self.screen)
      
      pygame.display.flip()
  ```

### 1.3) Lambda heatmap (optional)

- [ ] **Add lambda visualization toggle**
  ```python
  def _draw_lambda_heatmap(self, sim: Simulation, screen):
      """Draw heatmap of lambda values across agents."""
      if not self.show_lambda:
          return
      
      # Get lambda range
      lambdas = [a.lambda_money for a in sim.agents]
      min_lambda = min(lambdas)
      max_lambda = max(lambdas)
      
      for agent in sim.agents:
          # Normalize lambda to color
          if max_lambda > min_lambda:
              normalized = (agent.lambda_money - min_lambda) / (max_lambda - min_lambda)
          else:
              normalized = 0.5
          
          # Color: blue (low λ) to red (high λ)
          color = self._lambda_to_color(normalized)
          
          # Draw circle at agent position
          pos_px = (agent.pos[0] * CELL_SIZE, agent.pos[1] * CELL_SIZE)
          pygame.draw.circle(screen, color, pos_px, CELL_SIZE // 3, 2)
  ```

---

## Part 2: Log Viewer Enhancements

### 2.1) Money trade filter

**File**: `src/vmt_log_viewer/queries.py` (or wherever queries are defined)

- [ ] **Add money trade query**
  ```python
  def get_money_trades(db_path: str, run_id: int) -> list:
      """Get all trades involving money."""
      conn = sqlite3.connect(db_path)
      cursor = conn.execute("""
          SELECT tick, buyer_id, seller_id, 
                 dA, dB, dM, price, exchange_pair_type,
                 buyer_surplus, seller_surplus
          FROM trades
          WHERE run_id = ? AND dM != 0
          ORDER BY tick
      """, (run_id,))
      result = cursor.fetchall()
      conn.close()
      return result
  ```

### 2.2) Lambda trajectory view

**File**: `src/vmt_log_viewer/` (UI components)

- [ ] **Add lambda plot tab**
  ```python
  class LambdaTrajectoryView(QWidget):
      """Widget for plotting lambda trajectories."""
      
      def __init__(self, db_path: str, run_id: int):
          super().__init__()
          self.db_path = db_path
          self.run_id = run_id
          self.init_ui()
      
      def init_ui(self):
          layout = QVBoxLayout()
          
          # Agent selector
          self.agent_selector = QComboBox()
          self.agent_selector.addItem("All Agents")
          # Populate with agent IDs from database
          layout.addWidget(QLabel("Select Agent:"))
          layout.addWidget(self.agent_selector)
          
          # Plot canvas
          self.canvas = MatplotlibCanvas()
          layout.addWidget(self.canvas)
          
          # Update button
          update_btn = QPushButton("Update Plot")
          update_btn.clicked.connect(self.update_plot)
          layout.addWidget(update_btn)
          
          self.setLayout(layout)
      
      def update_plot(self):
          """Query database and update plot."""
          # Query lambda values
          # Plot on canvas
          pass
  ```

### 2.3) Mode timeline view

- [ ] **Add mode timeline visualization**
  ```python
  class ModeTimelineView(QWidget):
      """Widget for visualizing mode transitions."""
      
      def __init__(self, db_path: str, run_id: int):
          super().__init__()
          # Query tick_states table
          # Display timeline with color-coded modes
          # Show exchange regime changes
          pass
  ```

### 2.4) CSV export enhancements

- [ ] **Include money columns in CSV export**
  ```python
  def export_to_csv(db_path: str, run_id: int, output_path: str):
      """Export run data to CSV including money columns."""
      conn = sqlite3.connect(db_path)
      
      # Export trades with money columns
      df_trades = pd.read_sql_query("""
          SELECT tick, buyer_id, seller_id,
                 dA, dB, dM, price, exchange_pair_type,
                 buyer_surplus, seller_surplus,
                 buyer_lambda, seller_lambda
          FROM trades
          WHERE run_id = ?
      """, conn, params=(run_id,))
      
      df_trades.to_csv(f"{output_path}_trades.csv", index=False)
      
      # Export agent snapshots with money
      df_agents = pd.read_sql_query("""
          SELECT tick, agent_id, x, y,
                 inventory_A, inventory_B, inventory_M,
                 lambda_money, utility,
                 ask_A_in_M, bid_A_in_M, ask_B_in_M, bid_B_in_M
          FROM agent_snapshots
          WHERE run_id = ?
      """, conn, params=(run_id,))
      
      df_agents.to_csv(f"{output_path}_agents.csv", index=False)
      
      conn.close()
  ```

---

## Part 3: Demo Scenarios

### 3.1) Create showcase scenarios

**Files**: Create in `scenarios/demos/` directory

- [ ] **Demo 1: Simple monetary exchange**
  ```yaml
  # scenarios/demos/demo_01_simple_money.yaml
  # 3 agents, clear complementary needs, money enables exchange
  # Pedagogical: "Why money?"
  ```

- [ ] **Demo 2: KKT convergence**
  ```yaml
  # scenarios/demos/demo_02_kkt_convergence.yaml
  # Show λ converging to equilibrium
  # Pedagogical: "How do agents learn prices?"
  ```

- [ ] **Demo 3: Mixed regime dynamics**
  ```yaml
  # scenarios/demos/demo_03_mixed_regime.yaml
  # Both money and barter coexist
  # Pedagogical: "When is barter efficient?"
  ```

- [ ] **Demo 4: Liquidity emergence**
  ```yaml
  # scenarios/demos/demo_04_liquidity_zones.yaml
  # Spatial variation in liquidity
  # Pedagogical: "Market thickness and exchange types"
  ```

- [ ] **Demo 5: Mode interaction**
  ```yaml
  # scenarios/demos/demo_05_mode_schedule_money.yaml
  # Alternating forage/trade with money
  # Pedagogical: "Time constraints with monetary exchange"
  ```

### 3.2) Create demo runner script

**File**: `scripts/run_demos.py` (create new)

- [ ] **Automated demo runner**
  ```python
  import subprocess
  import sys
  from pathlib import Path
  
  DEMOS = [
      ("demo_01_simple_money.yaml", "Simple Monetary Exchange", 50),
      ("demo_02_kkt_convergence.yaml", "KKT Lambda Convergence", 100),
      ("demo_03_mixed_regime.yaml", "Mixed Regime Dynamics", 80),
      ("demo_04_liquidity_zones.yaml", "Liquidity Zones", 100),
      ("demo_05_mode_schedule_money.yaml", "Mode Schedule + Money", 150),
  ]
  
  def run_demo(scenario_file: str, title: str, ticks: int):
      """Run a single demo scenario."""
      print(f"\n{'='*60}")
      print(f"Demo: {title}")
      print(f"Scenario: {scenario_file}")
      print(f"Running for {ticks} ticks...")
      print(f"{'='*60}\n")
      
      result = subprocess.run([
          sys.executable, "main.py",
          f"scenarios/demos/{scenario_file}",
          "--seed", "42"
      ])
      
      if result.returncode != 0:
          print(f"✗ Demo failed: {title}")
          return False
      else:
          print(f"✓ Demo completed: {title}")
          return True
  
  def main():
      print("Running all money demo scenarios...")
      
      results = []
      for scenario, title, ticks in DEMOS:
          success = run_demo(scenario, title, ticks)
          results.append((title, success))
      
      print(f"\n{'='*60}")
      print("Demo Summary:")
      print(f"{'='*60}")
      for title, success in results:
          status = "✓ PASS" if success else "✗ FAIL"
          print(f"{status}: {title}")
      
      all_passed = all(success for _, success in results)
      sys.exit(0 if all_passed else 1)
  
  if __name__ == '__main__':
      main()
  ```

---

## Part 4: Documentation Completion

### 4.1) User documentation

**File**: `docs/user_guide_money.md` (create new)

- [ ] **Write comprehensive user guide**
  ```markdown
  # VMT Money System User Guide
  
  ## Introduction
  - What is the money system?
  - Why was it added?
  - Pedagogical goals
  
  ## Quick Start
  - Simplest money scenario
  - Running your first money simulation
  - Interpreting results
  
  ## Configuration Reference
  - money_mode: quasilinear vs kkt_lambda
  - exchange_regime: barter_only, money_only, mixed, mixed_liquidity_gated
  - lambda_money and lambda_bounds
  - liquidity_gate parameters
  
  ## Scenarios
  - Example configurations
  - When to use each regime
  - Classroom exercises
  
  ## Interpreting Results
  - Understanding λ values
  - Trade type distributions
  - Liquidity depth metrics
  
  ## Troubleshooting
  - Common issues
  - Performance tips
  - FAQ
  ```

### 4.2) Technical documentation

**File**: `docs/technical/money_implementation.md` (create new)

- [ ] **Write technical reference**
  ```markdown
  # Money System Technical Reference
  
  ## Architecture Overview
  - Two-layer control (mode_schedule × exchange_regime)
  - Quote system extensions
  - Trading mechanism generalization
  
  ## Algorithms
  - KKT λ estimation (median-lower aggregation)
  - Liquidity depth calculation
  - Tie-breaking policy
  
  ## Data Structures
  - Inventory.M field
  - Agent lambda state
  - Quote extensions
  
  ## Telemetry Schema
  - Reference to money_telemetry_schema.md
  
  ## Performance Considerations
  - Complexity analysis
  - Optimization techniques
  
  ## Testing Strategy
  - Unit test coverage
  - Integration test scenarios
  - Determinism guarantees
  ```

### 4.3) Update main README

**File**: `docs/README.md`

- [ ] **Add money system section**
  ```markdown
  ## Money System
  
  VMT now includes a comprehensive money system for teaching monetary economics:
  
  - **Multiple modes**: Quasi-linear utility or endogenous λ estimation (KKT)
  - **Flexible regimes**: Barter-only, money-only, mixed, or liquidity-gated
  - **Full observability**: Track λ convergence, trade types, liquidity depth
  - **Pedagogical scenarios**: Pre-built demos for classroom use
  
  See [Money User Guide](user_guide_money.md) for details.
  ```

### 4.4) API documentation

- [ ] **Generate docstrings for all money-related functions**
- [ ] **Run docstring coverage check**
  ```bash
  interrogate src/vmt_engine src/scenarios src/telemetry --verbose
  ```

---

## Part 5: Code Quality and Polish

### 5.1) Code review prep

- [ ] **Self-review checklist**
  - [ ] All functions have docstrings
  - [ ] Type hints consistent
  - [ ] No TODO comments left in code
  - [ ] Magic numbers replaced with named constants
  - [ ] No dead code
  - [ ] Error messages clear and helpful

- [ ] **Run linters**
  ```bash
  flake8 src/vmt_engine src/scenarios src/telemetry
  black --check src/
  mypy src/vmt_engine src/scenarios src/telemetry
  ```

- [ ] **Fix all linter warnings**

### 5.2) Performance profiling

- [ ] **Profile large money scenario**
  ```bash
  python -m cProfile -o money_profile.prof main.py scenarios/large_money_scenario.yaml --seed 42
  python -m pstats money_profile.prof
  # Check: no unexpected O(N²) hotspots
  ```

- [ ] **Memory profiling**
  ```bash
  python -m memory_profiler main.py scenarios/large_money_scenario.yaml
  # Verify: no memory leaks with money features
  ```

### 5.3) Error handling audit

- [ ] **Check all money-related error paths**
  - [ ] Invalid money_mode value → clear error
  - [ ] Missing M in money_only regime → helpful error
  - [ ] Negative M value → caught early
  - [ ] Lambda bounds validation → clear message

---

## Part 6: Testing and Validation

### 6.1) End-to-end test suite

**File**: `tests/test_money_e2e.py` (create new)

- [ ] **Comprehensive E2E tests**
  ```python
  def test_e2e_all_regimes():
      """Run simulation through all regimes."""
      regimes = ["barter_only", "money_only", "mixed", "mixed_liquidity_gated"]
      for regime in regimes:
          # Run scenario with each regime
          # Verify: completes without errors
          # Verify: telemetry logs correctly
          pass
  
  def test_e2e_both_money_modes():
      """Run with both quasilinear and kkt_lambda."""
      for mode in ["quasilinear", "kkt_lambda"]:
          # Run scenario
          # Verify: mode-specific behavior
          pass
  
  def test_e2e_mode_schedule_interaction():
      """Run with mode_schedule × exchange_regime."""
      # Run scenario with both controls
      # Verify: correct interaction
      pass
  ```

### 6.2) Regression test suite

- [ ] **Run full regression suite**
  ```bash
  pytest tests/ -v --tb=short
  ```

- [ ] **Verify all phases still pass**
  ```bash
  for phase in {1..5}; do
      echo "Testing Phase $phase..."
      pytest tests/test_money_phase${phase}*.py -v
  done
  ```

### 6.3) Demo validation

- [ ] **Run all demo scenarios**
  ```bash
  python scripts/run_demos.py
  ```

- [ ] **Verify demos in GUI**
  ```bash
  python launcher.py
  # Manually run each demo from GUI
  # Verify: renderer shows money features
  # Verify: no crashes or visual glitches
  ```

---

## Part 7: Release Preparation

### 7.1) Changelog

**File**: `CHANGELOG.md` (update)

- [ ] **Add money system entry**
  ```markdown
  ## 2025-10-19 — Money System Implementation
  
  ### Added
  - Money as integer inventory (M field)
  - Quasi-linear utility mode
  - KKT λ estimation mode with endogenous price discovery
  - Four exchange regimes: barter_only, money_only, mixed, mixed_liquidity_gated
  - Money-first tie-breaking in mixed regimes
  - Liquidity depth metric and gating logic
  - Comprehensive telemetry for money trades and λ trajectories
  - Renderer enhancements: money visualization, mode overlays, λ heatmap
  - Log viewer: money trade filters, λ plots, mode timeline
  - Five demo scenarios showcasing money features
  - Complete documentation (user guide + technical reference)
  
  ### Changed
  - Extended Inventory dataclass with M field
  - Generalized trading system for goods-for-goods and goods-for-money
  - Enhanced telemetry schema (9 new columns, 2 new tables)
  
  ### Backward Compatibility
  - All changes backward compatible with defaults
  - Legacy scenarios run identically
  - exchange_regime defaults to "barter_only"
  ```

### 7.2) Migration guide (if needed)

**File**: `docs/migration_money.md` (create if needed)

- [ ] **Write migration guide for existing users**
  ```markdown
  # Migrating to Money System
  
  ## For Existing Scenarios
  - No changes required
  - Add `exchange_regime: money_only` to enable money
  - Add `M` to initial_inventories
  
  ## For Custom Extensions
  - Check if custom code accesses Inventory
  - Update to handle M field
  
  ## For Database Queries
  - New columns available in agent_snapshots and trades
  - See money_telemetry_schema.md for details
  ```

### 7.3) Contributor guide

**File**: `docs/CONTRIBUTING.md` (update)

- [ ] **Add money system development notes**
  - How to add new money modes
  - How to extend exchange regimes
  - Testing requirements for money features

---

## Completion Criteria

**Phase 6 is complete when**:

✅ Renderer visualizes money transfers, mode overlays, optional λ heatmap
✅ Log viewer has money filters, λ plots, mode timeline
✅ All 5 demo scenarios work and are pedagogically sound
✅ User guide complete and tested
✅ Technical documentation complete
✅ Code passes all linters with no warnings
✅ Performance profiling shows no regressions
✅ All E2E tests pass
✅ Changelog and migration guide written
✅ Demos validated in GUI

**Ready for Merge/Release when**:
- Code review approved by maintainer
- All tests pass on CI (if configured)
- Documentation reviewed for accuracy and completeness
- Demo scenarios tested in classroom setting (if possible)

---

## Post-Release

### Future enhancements (not in Phase 6)

- [ ] Agent-specific exchange regimes (per §14.1 of SSOT)
- [ ] Spatial zones for regimes (per §14.1)
- [ ] Endogenous money acquisition via labor/production (per §14.2)
- [ ] Credit and debt (negative M) (per §14.3)
- [ ] Multiple currencies (per §14.4)
- [ ] Dynamic regime switching (per §14.5)

---

**Estimated effort**: 10-14 hours

See also:
- `money_SSOT_implementation_plan.md` (complete reference)
- `money_phase1_checklist.md` through `money_phase5_checklist.md` (prerequisites)
- `money_telemetry_schema.md` (database reference)

---

## Final Checklist

Before declaring Phase 6 complete:

- [ ] All previous phases (1-5) tests passing
- [ ] Renderer enhancements working
- [ ] Log viewer enhancements working
- [ ] All 5 demo scenarios validated
- [ ] User guide complete
- [ ] Technical documentation complete
- [ ] Main README updated
- [ ] Changelog entry added
- [ ] Code quality checks passed
- [ ] Performance profiling clean
- [ ] E2E tests passing
- [ ] Regression tests passing
- [ ] No TODOs left in code
- [ ] All docstrings complete
- [ ] Migration guide (if needed) written

**Congratulations! The money system implementation is complete. 🎉**

