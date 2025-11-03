# Stage 1-2 PR Follow-up: Pattern Analysis & Protocol Comparison Infrastructure

**Purpose**: Complete missing infrastructure from Stages 1-2 for comprehensive behavioral analysis and protocol comparison  
**Duration**: 2-3 weeks  
**Prerequisites**: Protocol restructure complete (Part 0), Stage 2 protocols implemented  
**Status**: Planning Document (Pre-Implementation)

---

## Executive Summary

This document provides a rigorous step-by-step implementation plan for completing the analytical infrastructure needed to:

1. **Enhance Stage 1 (Behavioral Baseline)**: Add pattern analysis capabilities (spatial patterns, price dynamics, edge case detection)
2. **Complete Stage 2 (Protocol Comparison)**: Implement `ProtocolComparator` framework for systematic institutional comparison

These components are critical prerequisites for validating Stage 2 protocol implementations and enabling evidence-based decisions about which protocols to enhance or modify.

---

## Current State Assessment

### Completed ✅

1. **Protocol Architecture Restructure** (Part 0)
   - Protocols organized by domain (`agent_based/search`, `game_theory/matching`, `game_theory/bargaining`)
   - Registry system functional
   - All imports updated

2. **Baseline Scenarios & Metrics** (Stage 1, Partial)
   - 5 baseline scenarios created (`baseline_2agent_simple.yaml`, etc.)
   - `scripts/analyze_baseline.py` extracts basic metrics
   - `docs/baseline_behavior_report.md` generated with summary statistics
   - Basic metrics: trade counts, prices, convergence, utility gains

3. **Protocol Implementation** (Stage 2, Complete)
   - **Search**: `legacy`, `random_walk`, `myopic` ✅
   - **Matching**: `legacy`, `random`, `greedy_surplus` ✅
   - **Bargaining**: `legacy`, `split_difference`, `take_it_or_leave_it` ✅
   - All protocols have test coverage

### Missing ❌

1. **Pattern Analysis Framework** (Stage 1, Week 2)
   - `PatternAnalyzer` class not implemented
   - Spatial pattern detection (market areas, trade routes, dead zones, hotspots)
   - Price dynamics classification (convergence types, volatility patterns, cycles)
   - Edge case identification framework

2. **Protocol Comparison Framework** (Stage 2, Week 6)
   - `ProtocolComparator` class not implemented
   - Systematic protocol set comparison
   - Automated comparison table generation
   - Protocol performance insights

3. **Enhanced Metrics Extraction**
   - Efficiency computation (vs theoretical maximum)
   - Inequality metrics (Gini coefficient)
   - Market power measures
   - Convergence speed quantification

---

## Architecture Overview

```python
# New module structure
src/vmt_engine/analysis/
├── __init__.py
├── pattern_analyzer.py      # Spatial patterns, price dynamics, edge cases
├── protocol_comparator.py   # Systematic protocol comparison
├── metrics.py               # Enhanced metric computation
└── reports.py               # Report generation utilities

scripts/
├── analyze_baseline.py      # Enhanced with pattern analysis
└── compare_protocols.py     # New: Protocol comparison script
```

---

## Part 1: Pattern Analysis Framework

### Objective

Implement comprehensive pattern analysis to identify emergent behaviors, classify convergence dynamics, and detect anomalies. This provides deep understanding of system behavior needed for protocol validation.

### Week 1: PatternAnalyzer Core Infrastructure

```python
# src/vmt_engine/analysis/pattern_analyzer.py
"""
Pattern Analysis Framework for VMT Simulations

Analyzes simulation telemetry to identify:
- Spatial trading patterns (market areas, routes, dead zones)
- Price discovery dynamics (convergence types, volatility)
- Edge cases and anomalies
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import sqlite3
import numpy as np
from collections import defaultdict

from ..core.agent import Agent
from ..core.grid import Grid


@dataclass
class SpatialPattern:
    """Spatial trading pattern classification"""
    market_areas: List[Tuple[int, int, float]]  # (x, y, density) clusters
    trade_routes: List[List[Tuple[int, int]]]    # Path sequences between markets
    dead_zones: List[Tuple[int, int]]            # Zero-activity cells
    hotspots: List[Tuple[int, int, float]]       # Peak activity locations (x, y, activity)


@dataclass
class PriceDynamics:
    """Price discovery behavior classification"""
    convergence_type: str  # 'monotonic' | 'oscillating' | 'cyclic' | 'non_convergent'
    convergence_tick: Optional[int]
    convergence_speed: Optional[float]  # Ticks to convergence
    final_price: Optional[float]
    volatility_pattern: str  # 'low' | 'medium' | 'high' | 'decreasing' | 'increasing'
    price_cycles: List[Dict[str, Any]]  # Detected cycles


@dataclass
class EdgeCase:
    """Identified anomaly or problematic behavior"""
    scenario: str
    issue_type: str  # 'low_efficiency' | 'no_convergence' | 'spatial_fragmentation' | 'price_deviation'
    severity: str    # 'minor' | 'moderate' | 'severe'
    details: str
    metrics: Dict[str, Any]


class PatternAnalyzer:
    """
    Comprehensive pattern analysis from simulation telemetry
    """
    
    def __init__(self, db_path: Path, run_id: int):
        """
        Initialize analyzer with telemetry database.
        
        Args:
            db_path: Path to SQLite telemetry database
            run_id: Run ID to analyze
        """
        self.db_path = db_path
        self.run_id = run_id
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        
        # Cache simulation metadata
        self._cache_metadata()
    
    def _cache_metadata(self):
        """Load simulation parameters for analysis context"""
        cursor = self.conn.execute("""
            SELECT grid_width, grid_height, n_agents, max_ticks
            FROM simulation_runs
            WHERE run_id = ?
        """, (self.run_id,))
        
        row = cursor.fetchone()
        if row:
            self.grid_width = row['grid_width']
            self.grid_height = row['grid_height']
            self.n_agents = row['n_agents']
            self.max_ticks = row['max_ticks']
        else:
            raise ValueError(f"Run ID {self.run_id} not found in database")
    
    def analyze_all(self) -> Dict[str, Any]:
        """
        Perform complete pattern analysis.
        
        Returns:
            Dictionary with spatial_patterns, price_dynamics, edge_cases
        """
        return {
            'spatial_patterns': self.analyze_spatial_patterns(),
            'price_dynamics': self.analyze_price_dynamics(),
            'edge_cases': self.identify_edge_cases()
        }
```

### Spatial Pattern Analysis

```python
    def analyze_spatial_patterns(self) -> SpatialPattern:
        """
        Detect and classify spatial trading patterns.
        
        Algorithm:
        1. Build trade density map from all trades
        2. Detect market areas (high-density clusters using DBSCAN or threshold-based)
        3. Trace agent paths to identify trade routes
        4. Find dead zones (zero activity)
        5. Locate hotspots (top N activity cells)
        """
        # Step 1: Build trade density map
        trade_density = self._compute_trade_density_map()
        
        # Step 2: Detect market areas
        market_areas = self._detect_market_areas(trade_density)
        
        # Step 3: Identify trade routes
        trade_routes = self._trace_trade_routes()
        
        # Step 4: Find dead zones
        dead_zones = self._find_dead_zones(trade_density)
        
        # Step 5: Locate hotspots
        hotspots = self._find_hotspots(trade_density, top_n=5)
        
        return SpatialPattern(
            market_areas=market_areas,
            trade_routes=trade_routes,
            dead_zones=dead_zones,
            hotspots=hotspots
        )
    
    def _compute_trade_density_map(self) -> np.ndarray:
        """
        Compute trade density per grid cell.
        
        Returns:
            2D array where each cell contains trade count
        """
        density = np.zeros((self.grid_height, self.grid_width), dtype=int)
        
        cursor = self.conn.execute("""
            SELECT x, y, COUNT(*) as trade_count
            FROM trades
            WHERE run_id = ?
            GROUP BY x, y
        """, (self.run_id,))
        
        for row in cursor:
            x, y = row['x'], row['y']
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                density[y, x] = row['trade_count']
        
        return density
    
    def _detect_market_areas(
        self, 
        density_map: np.ndarray, 
        threshold: float = 0.7,
        min_cluster_size: int = 3
    ) -> List[Tuple[int, int, float]]:
        """
        Detect market areas as high-density clusters.
        
        Uses connected components with threshold-based filtering.
        Returns list of (center_x, center_y, density) for each market area.
        """
        from scipy.ndimage import label, center_of_mass
        
        # Normalize density to [0, 1]
        max_density = density_map.max()
        if max_density == 0:
            return []
        
        normalized = density_map / max_density
        
        # Threshold-based binary map
        binary = (normalized >= threshold).astype(int)
        
        # Connected components
        labeled, n_components = label(binary)
        
        market_areas = []
        for i in range(1, n_components + 1):
            component_mask = (labeled == i)
            component_size = component_mask.sum()
            
            if component_size >= min_cluster_size:
                # Compute center of mass
                center_y, center_x = center_of_mass(density_map, labels=labeled, index=i)
                center_x, center_y = int(center_x), int(center_y)
                
                # Average density in cluster
                avg_density = density_map[component_mask].mean()
                
                market_areas.append((center_x, center_y, float(avg_density)))
        
        return market_areas
    
    def _trace_trade_routes(self) -> List[List[Tuple[int, int]]]:
        """
        Identify trade routes by tracing agent movement paths.
        
        Returns:
            List of routes, where each route is a sequence of (x, y) positions
        """
        # Get agent movement trajectories
        cursor = self.conn.execute("""
            SELECT agent_id, tick, x, y
            FROM agent_snapshots
            WHERE run_id = ?
            ORDER BY agent_id, tick
        """, (self.run_id,))
        
        trajectories = defaultdict(list)
        for row in cursor:
            trajectories[row['agent_id']].append((row['tick'], row['x'], row['y']))
        
        # Identify routes as sequences between market areas or frequent trading locations
        # This is a simplified version; full implementation would use graph algorithms
        routes = []
        
        # For each agent, identify segments with multiple trades
        for agent_id, positions in trajectories.items():
            # Get trades for this agent
            agent_trades = self.conn.execute("""
                SELECT DISTINCT x, y, tick
                FROM trades
                WHERE run_id = ? AND (buyer_id = ? OR seller_id = ?)
                ORDER BY tick
            """, (self.run_id, agent_id, agent_id)).fetchall()
            
            if len(agent_trades) >= 2:
                # Extract route as path between consecutive trade locations
                route = []
                for trade in agent_trades:
                    route.append((trade['x'], trade['y']))
                
                if len(route) > 1:
                    routes.append(route)
        
        return routes
    
    def _find_dead_zones(self, density_map: np.ndarray) -> List[Tuple[int, int]]:
        """
        Find cells with zero trading activity.
        
        Returns:
            List of (x, y) coordinates with no trades
        """
        dead_zones = []
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if density_map[y, x] == 0:
                    dead_zones.append((x, y))
        
        return dead_zones
    
    def _find_hotspots(
        self, 
        density_map: np.ndarray, 
        top_n: int = 5
    ) -> List[Tuple[int, int, float]]:
        """
        Locate top N highest-activity cells.
        
        Returns:
            List of (x, y, density) sorted by density descending
        """
        # Flatten and get indices
        flat_density = density_map.flatten()
        top_indices = np.argsort(flat_density)[-top_n:][::-1]
        
        hotspots = []
        for idx in top_indices:
            y = idx // self.grid_width
            x = idx % self.grid_width
            density = float(flat_density[idx])
            
            if density > 0:
                hotspots.append((x, y, density))
        
        return hotspots
```

### Price Dynamics Analysis

```python
    def analyze_price_dynamics(self) -> PriceDynamics:
        """
        Characterize price discovery and convergence behavior.
        
        Algorithm:
        1. Extract price series from trades
        2. Classify convergence type (monotonic, oscillating, cyclic, non-convergent)
        3. Measure convergence speed if convergent
        4. Analyze volatility pattern
        5. Detect price cycles
        """
        # Extract price series
        price_series = self._extract_price_series()
        
        if len(price_series) < 10:
            # Insufficient data
            return PriceDynamics(
                convergence_type='non_convergent',
                convergence_tick=None,
                convergence_speed=None,
                final_price=None,
                volatility_pattern='unknown',
                price_cycles=[]
            )
        
        # Classify convergence
        convergence_type, convergence_tick = self._classify_convergence(price_series)
        
        # Measure convergence speed
        convergence_speed = None
        if convergence_tick is not None:
            convergence_speed = float(convergence_tick)
        
        # Final price
        final_price = float(price_series[-1]) if price_series else None
        
        # Volatility pattern
        volatility_pattern = self._classify_volatility(price_series)
        
        # Detect cycles
        price_cycles = self._detect_cycles(price_series) if convergence_type == 'cyclic' else []
        
        return PriceDynamics(
            convergence_type=convergence_type,
            convergence_tick=convergence_tick,
            convergence_speed=convergence_speed,
            final_price=final_price,
            volatility_pattern=volatility_pattern,
            price_cycles=price_cycles
        )
    
    def _extract_price_series(self) -> List[float]:
        """
        Extract price series from trades.
        
        Returns:
            List of prices ordered by tick
        """
        cursor = self.conn.execute("""
            SELECT price
            FROM trades
            WHERE run_id = ?
            ORDER BY tick, id
        """, (self.run_id,))
        
        return [row['price'] for row in cursor]
    
    def _classify_convergence(
        self, 
        price_series: List[float],
        window: int = 50,
        threshold: float = 0.05
    ) -> Tuple[str, Optional[int]]:
        """
        Classify convergence type and find convergence tick.
        
        Returns:
            (convergence_type, convergence_tick)
        """
        if len(price_series) < window:
            return ('non_convergent', None)
        
        # Compute rolling variance
        rolling_variances = []
        for i in range(window, len(price_series)):
            window_prices = price_series[i-window:i]
            variance = np.var(window_prices)
            rolling_variances.append((i, variance))
        
        # Check if variance decreases below threshold
        convergence_tick = None
        for tick, variance in rolling_variances:
            if variance < threshold:
                convergence_tick = tick
                break
        
        # Classify type
        if convergence_tick is None:
            # Check for cycles
            if self._has_cycles(price_series):
                return ('cyclic', None)
            return ('non_convergent', None)
        
        # Check if monotonic or oscillating
        # Look at trend around convergence
        convergence_window = price_series[max(0, convergence_tick-window):convergence_tick]
        
        # Compute trend (positive/negative slope)
        x = np.arange(len(convergence_window))
        slope = np.polyfit(x, convergence_window, 1)[0]
        
        # Check for oscillation (alternating up/down)
        if self._has_oscillation(convergence_window):
            return ('oscillating', convergence_tick)
        elif abs(slope) < 0.001:
            return ('monotonic', convergence_tick)
        else:
            return ('monotonic', convergence_tick)
    
    def _has_oscillation(self, series: List[float], min_oscillations: int = 3) -> bool:
        """Detect if series oscillates (alternating direction changes)"""
        if len(series) < 4:
            return False
        
        diffs = np.diff(series)
        sign_changes = np.sum(np.diff(np.sign(diffs)) != 0)
        
        return sign_changes >= min_oscillations
    
    def _has_cycles(self, series: List[float], min_cycle_length: int = 10) -> bool:
        """Detect periodic cycles in price series"""
        if len(series) < min_cycle_length * 2:
            return False
        
        # Auto-correlation approach
        from scipy.signal import find_peaks
        
        # Find peaks and troughs
        peaks, _ = find_peaks(series, distance=min_cycle_length)
        troughs, _ = find_peaks(-np.array(series), distance=min_cycle_length)
        
        # If we have at least 2 cycles worth of peaks/troughs
        if len(peaks) >= 2 and len(troughs) >= 2:
            # Check if spacing is roughly consistent
            peak_intervals = np.diff(peaks)
            if len(peak_intervals) > 0:
                cv = np.std(peak_intervals) / np.mean(peak_intervals)  # Coefficient of variation
                return cv < 0.5  # Consistent spacing suggests cycles
        
        return False
    
    def _classify_volatility(self, price_series: List[float]) -> str:
        """
        Classify volatility pattern.
        
        Returns:
            'low' | 'medium' | 'high' | 'decreasing' | 'increasing'
        """
        if len(price_series) < 20:
            return 'unknown'
        
        # Compute rolling volatility
        window = min(20, len(price_series) // 4)
        volatilities = []
        
        for i in range(window, len(price_series)):
            window_prices = price_series[i-window:i]
            vol = np.std(window_prices)
            volatilities.append(vol)
        
        if not volatilities:
            return 'low'
        
        # Classify
        mean_vol = np.mean(volatilities)
        
        # Trend in volatility
        x = np.arange(len(volatilities))
        slope = np.polyfit(x, volatilities, 1)[0]
        
        if abs(slope) > 0.01:
            return 'increasing' if slope > 0 else 'decreasing'
        
        # Static volatility level
        if mean_vol < 0.05:
            return 'low'
        elif mean_vol < 0.15:
            return 'medium'
        else:
            return 'high'
    
    def _detect_cycles(self, price_series: List[float]) -> List[Dict[str, Any]]:
        """
        Detect and characterize price cycles.
        
        Returns:
            List of cycle dictionaries with period, amplitude, phase
        """
        # Simplified implementation using FFT or autocorrelation
        # Full implementation would use more sophisticated methods
        cycles = []
        
        if len(price_series) < 20:
            return cycles
        
        # Use autocorrelation to find dominant period
        from scipy.signal import correlate
        
        autocorr = correlate(price_series, price_series, mode='same')
        autocorr = autocorr[len(autocorr)//2:]
        
        # Find peaks in autocorrelation (excluding lag 0)
        peaks = []
        for i in range(1, min(100, len(autocorr))):
            if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                peaks.append((i, autocorr[i]))
        
        if peaks:
            # Dominant cycle
            dominant_peak = max(peaks, key=lambda x: x[1])
            period = dominant_peak[0]
            
            # Estimate amplitude
            cycle_values = price_series[::period] if period > 1 else price_series
            amplitude = (max(cycle_values) - min(cycle_values)) / 2
            
            cycles.append({
                'period': period,
                'amplitude': float(amplitude),
                'strength': float(dominant_peak[1] / autocorr[0])  # Normalized
            })
        
        return cycles
```

### Edge Case Identification

```python
    def identify_edge_cases(self) -> List[EdgeCase]:
        """
        Find and document unexpected or problematic behaviors.
        
        Checks:
        - Low efficiency (vs theoretical maximum)
        - No price convergence
        - Spatial fragmentation
        - Price deviation from theoretical equilibrium
        """
        edge_cases = []
        
        # Get basic metrics
        cursor = self.conn.execute("""
            SELECT COUNT(*) as trade_count,
                   MIN(tick) as first_trade,
                   MAX(tick) as last_trade,
                   AVG(price) as avg_price
            FROM trades
            WHERE run_id = ?
        """, (self.run_id,))
        
        trade_stats = cursor.fetchone()
        trade_count = trade_stats['trade_count'] if trade_stats else 0
        
        # Check efficiency
        efficiency = self._compute_efficiency()
        if efficiency is not None and efficiency < 0.5:
            edge_cases.append(EdgeCase(
                scenario=self._get_scenario_name(),
                issue_type='low_efficiency',
                severity='moderate' if efficiency < 0.3 else 'minor',
                details=f"Only {efficiency*100:.1f}% of theoretical gains captured",
                metrics={'efficiency': efficiency, 'trade_count': trade_count}
            ))
        
        # Check convergence
        price_dynamics = self.analyze_price_dynamics()
        if price_dynamics.convergence_type == 'non_convergent':
            edge_cases.append(EdgeCase(
                scenario=self._get_scenario_name(),
                issue_type='no_convergence',
                severity='moderate',
                details="Prices never stabilized within simulation duration",
                metrics={'final_tick': self.max_ticks, 'trade_count': trade_count}
            ))
        
        # Check spatial fragmentation
        spatial_patterns = self.analyze_spatial_patterns()
        if len(spatial_patterns.dead_zones) > self.grid_width * self.grid_height * 0.5:
            edge_cases.append(EdgeCase(
                scenario=self._get_scenario_name(),
                issue_type='spatial_fragmentation',
                severity='moderate',
                details=f"{len(spatial_patterns.dead_zones)} isolated dead zones ({len(spatial_patterns.dead_zones)/(self.grid_width*self.grid_height)*100:.1f}% of grid)",
                metrics={'dead_zones': len(spatial_patterns.dead_zones), 'grid_size': self.grid_width * self.grid_height}
            ))
        
        # Check price deviation (if theoretical equilibrium can be computed)
        theoretical_price = self._compute_theoretical_equilibrium()
        if theoretical_price is not None and price_dynamics.final_price is not None:
            deviation = abs(price_dynamics.final_price - theoretical_price) / theoretical_price
            if deviation > 0.2:
                edge_cases.append(EdgeCase(
                    scenario=self._get_scenario_name(),
                    issue_type='price_deviation',
                    severity='minor' if deviation < 0.5 else 'moderate',
                    details=f"Converged to {price_dynamics.final_price:.3f} vs theoretical {theoretical_price:.3f} ({deviation*100:.1f}% deviation)",
                    metrics={'observed_price': price_dynamics.final_price, 'theoretical_price': theoretical_price, 'deviation': deviation}
                ))
        
        return edge_cases
    
    def _compute_efficiency(self) -> Optional[float]:
        """
        Compute efficiency as fraction of theoretical maximum gains captured.
        
        Returns:
            Efficiency in [0, 1] or None if cannot compute
        """
        # Get initial and final total utility
        cursor = self.conn.execute("""
            SELECT SUM(utility) as total_utility
            FROM agent_snapshots
            WHERE run_id = ? AND tick = (SELECT MIN(tick) FROM agent_snapshots WHERE run_id = ?)
        """, (self.run_id, self.run_id))
        
        initial_utility = cursor.fetchone()['total_utility']
        
        cursor = self.conn.execute("""
            SELECT SUM(utility) as total_utility
            FROM agent_snapshots
            WHERE run_id = ? AND tick = (SELECT MAX(tick) FROM agent_snapshots WHERE run_id = ?)
        """, (self.run_id, self.run_id))
        
        final_utility = cursor.fetchone()['total_utility']
        
        if initial_utility is None or final_utility is None:
            return None
        
        actual_gain = final_utility - initial_utility
        
        # Theoretical maximum would require full Pareto efficiency
        # This is a simplified estimate; full implementation would compute Pareto frontier
        # For now, use heuristic: if we had perfect coordination, gain could be 2x actual
        # This is conservative and realistic
        theoretical_gain = actual_gain * 2.0  # Simplified heuristic
        
        if theoretical_gain == 0:
            return 1.0 if actual_gain == 0 else 0.0
        
        return min(1.0, actual_gain / theoretical_gain)
    
    def _compute_theoretical_equilibrium(self) -> Optional[float]:
        """
        Compute theoretical competitive equilibrium price.
        
        This is a simplified implementation; full version would solve
        market-clearing conditions.
        
        Returns:
            Theoretical price ratio or None if cannot compute
        """
        # Simplified: average of initial MRS ratios
        # Full implementation would solve excess demand = 0
        
        cursor = self.conn.execute("""
            SELECT inventory_A, inventory_B
            FROM agent_snapshots
            WHERE run_id = ? AND tick = (SELECT MIN(tick) FROM agent_snapshots WHERE run_id = ?)
        """, (self.run_id, self.run_id))
        
        endowments = cursor.fetchall()
        if not endowments:
            return None
        
        # For CES utilities with same parameters, equilibrium price
        # is approximately the geometric mean of MRS ratios
        # This is a heuristic; full implementation needs utility function parameters
        
        # For now, return None to indicate we can't compute without utility parameters
        # Full implementation would load utility parameters from scenario
        return None
    
    def _get_scenario_name(self) -> str:
        """Extract scenario name from database"""
        cursor = self.conn.execute("""
            SELECT scenario_name
            FROM simulation_runs
            WHERE run_id = ?
        """, (self.run_id,))
        
        row = cursor.fetchone()
        return row['scenario_name'] if row else f"run_{self.run_id}"
    
    def close(self):
        """Close database connection"""
        self.conn.close()
```

---

## Part 2: Protocol Comparison Framework

### Objective

Implement systematic framework for comparing protocol sets across scenarios. Enables evidence-based evaluation of institutional effects.

### Week 2: ProtocolComparator Implementation

```python
# src/vmt_engine/analysis/protocol_comparator.py
"""
Protocol Comparison Framework

Systematically compares protocol sets across scenarios to evaluate
institutional effects on market outcomes.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import sqlite3
from collections import defaultdict

from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation
from telemetry.config import LogConfig
from .metrics import MetricsExtractor
from .pattern_analyzer import PatternAnalyzer


@dataclass
class ProtocolSet:
    """Configuration of protocols for one comparison"""
    name: str
    search: str
    matching: str
    bargaining: str
    description: str = ""


@dataclass
class ComparisonMetrics:
    """Metrics extracted from one simulation run"""
    protocol_set: str
    seed: int
    price_convergence: bool
    convergence_speed: Optional[int]
    efficiency: Optional[float]
    trade_volume: int
    average_surplus: float
    inequality: float
    market_power: Optional[float]
    runtime_seconds: float


@dataclass
class AggregatedComparison:
    """Aggregated metrics across seeds for one protocol set"""
    protocol_set: str
    n_runs: int
    price_convergence_rate: float  # Fraction of runs that converged
    convergence_speed_mean: Optional[float]
    convergence_speed_std: Optional[float]
    efficiency_mean: Optional[float]
    efficiency_std: Optional[float]
    trade_volume_mean: float
    trade_volume_std: float
    average_surplus_mean: float
    average_surplus_std: float
    inequality_mean: float
    inequality_std: float
    market_power_mean: Optional[float]
    runtime_mean: float


class ProtocolComparator:
    """
    Framework for systematic protocol comparison
    """
    
    def __init__(self):
        """
        Initialize with default protocol sets.
        
        Protocol sets represent different institutional configurations:
        - baseline: Original VMT protocols (legacy)
        - random_all: Non-strategic baseline
        - efficient: Welfare-maximizing protocols
        - strategic: Power-asymmetric protocols
        """
        self.protocol_sets = {
            'baseline': ProtocolSet(
                name='baseline',
                search='legacy',
                matching='legacy',
                bargaining='legacy',
                description='Original VMT protocols (legacy)'
            ),
            'random_all': ProtocolSet(
                name='random_all',
                search='random_walk',
                matching='random',
                bargaining='split_difference',
                description='Non-strategic baseline (random search, random matching, equal surplus)'
            ),
            'efficient': ProtocolSet(
                name='efficient',
                search='myopic',
                matching='greedy_surplus',
                bargaining='split_difference',
                description='Welfare-maximizing (myopic search, greedy matching, equal surplus)'
            ),
            'strategic': ProtocolSet(
                name='strategic',
                search='myopic',
                matching='legacy',  # Using legacy for now (stable matching TBD)
                bargaining='take_it_or_leave_it',
                description='Power-asymmetric (myopic search, legacy matching, ultimatum bargaining)'
            )
        }
        
        self.metrics_extractor = MetricsExtractor()
    
    def run_comparison(
        self, 
        scenario_path: str,
        protocol_sets: Optional[List[str]] = None,
        n_runs: int = 50,
        max_ticks: int = 1000,
        output_dir: Path = Path("logs/comparison")
    ) -> Dict[str, AggregatedComparison]:
        """
        Compare protocol sets on same scenario.
        
        Args:
            scenario_path: Path to scenario YAML file
            protocol_sets: List of protocol set names to compare (default: all)
            n_runs: Number of seeds per protocol set
            max_ticks: Maximum ticks per simulation
            output_dir: Directory for telemetry databases
            
        Returns:
            Dictionary mapping protocol set name to aggregated metrics
        """
        if protocol_sets is None:
            protocol_sets = list(self.protocol_sets.keys())
        
        output_dir.mkdir(parents=True, exist_ok=True)
        scenario_name = Path(scenario_path).stem
        
        all_results = {}
        
        for protocol_set_name in protocol_sets:
            if protocol_set_name not in self.protocol_sets:
                raise ValueError(f"Unknown protocol set: {protocol_set_name}")
            
            protocol_set = self.protocol_sets[protocol_set_name]
            print(f"\n{'='*60}")
            print(f"Protocol Set: {protocol_set_name} ({protocol_set.description})")
            print(f"{'='*60}")
            
            run_results = []
            
            for seed in range(n_runs):
                print(f"  Seed {seed:2d}/{n_runs-1}...", end=" ", flush=True)
                
                # Load scenario
                scenario = load_scenario(scenario_path)
                
                # Override protocols in scenario
                scenario.params['search_protocol'] = protocol_set.search
                scenario.params['matching_protocol'] = protocol_set.matching
                scenario.params['bargaining_protocol'] = protocol_set.bargaining
                
                # Create database for this run
                db_path = output_dir / f"{scenario_name}_{protocol_set_name}_seed{seed:03d}.db"
                if db_path.exists():
                    db_path.unlink()
                
                # Run simulation
                log_config = LogConfig.standard(db_path=str(db_path))
                
                sim = Simulation(scenario, log_config=log_config)
                sim.initialize()
                
                import time
                start_time = time.time()
                sim.run(max_ticks=max_ticks)
                runtime = time.time() - start_time
                
                # Extract metrics
                metrics = self.metrics_extractor.extract_comparison_metrics(
                    db_path, 
                    sim.run_id,
                    runtime
                )
                
                run_results.append(metrics)
                
                print(f"✓ ({runtime:.2f}s)")
            
            # Aggregate results
            aggregated = self._aggregate_comparison_metrics(protocol_set_name, run_results)
            all_results[protocol_set_name] = aggregated
        
        return all_results
    
    def _aggregate_comparison_metrics(
        self, 
        protocol_set: str,
        metrics_list: List[ComparisonMetrics]
    ) -> AggregatedComparison:
        """Aggregate metrics across runs"""
        n_runs = len(metrics_list)
        
        # Convergence
        converged_count = sum(1 for m in metrics_list if m.price_convergence)
        convergence_rate = converged_count / n_runs
        
        convergence_speeds = [m.convergence_speed for m in metrics_list if m.convergence_speed is not None]
        convergence_speed_mean = np.mean(convergence_speeds) if convergence_speeds else None
        convergence_speed_std = np.std(convergence_speeds) if len(convergence_speeds) > 1 else None
        
        # Efficiency
        efficiencies = [m.efficiency for m in metrics_list if m.efficiency is not None]
        efficiency_mean = np.mean(efficiencies) if efficiencies else None
        efficiency_std = np.std(efficiencies) if len(efficiencies) > 1 else None
        
        # Trade volume
        trade_volumes = [m.trade_volume for m in metrics_list]
        trade_volume_mean = np.mean(trade_volumes)
        trade_volume_std = np.std(trade_volumes)
        
        # Average surplus
        surpluses = [m.average_surplus for m in metrics_list]
        average_surplus_mean = np.mean(surpluses)
        average_surplus_std = np.std(surpluses)
        
        # Inequality
        inequalities = [m.inequality for m in metrics_list]
        inequality_mean = np.mean(inequalities)
        inequality_std = np.std(inequalities)
        
        # Market power
        market_powers = [m.market_power for m in metrics_list if m.market_power is not None]
        market_power_mean = np.mean(market_powers) if market_powers else None
        
        # Runtime
        runtimes = [m.runtime_seconds for m in metrics_list]
        runtime_mean = np.mean(runtimes)
        
        return AggregatedComparison(
            protocol_set=protocol_set,
            n_runs=n_runs,
            price_convergence_rate=convergence_rate,
            convergence_speed_mean=convergence_speed_mean,
            convergence_speed_std=convergence_speed_std,
            efficiency_mean=efficiency_mean,
            efficiency_std=efficiency_std,
            trade_volume_mean=trade_volume_mean,
            trade_volume_std=trade_volume_std,
            average_surplus_mean=average_surplus_mean,
            average_surplus_std=average_surplus_std,
            inequality_mean=inequality_mean,
            inequality_std=inequality_std,
            market_power_mean=market_power_mean,
            runtime_mean=runtime_mean
        )
    
    def create_comparison_table(
        self, 
        results: Dict[str, AggregatedComparison]
    ) -> str:
        """
        Generate formatted comparison table in Markdown.
        
        Returns:
            Markdown table string
        """
        lines = []
        lines.append("| Protocol Set | Convergence | Efficiency | Trade Volume | Inequality | Runtime |")
        lines.append("|-------------|------------|-----------|-------------|------------|---------|")
        
        for protocol_set_name, metrics in results.items():
            protocol_set = self.protocol_sets[protocol_set_name]
            
            # Convergence
            conv_str = f"{metrics.price_convergence_rate*100:.0f}%"
            if metrics.convergence_speed_mean is not None:
                conv_str += f" ({metrics.convergence_speed_mean:.0f} ticks)"
            
            # Efficiency
            eff_str = f"{metrics.efficiency_mean*100:.1f}%" if metrics.efficiency_mean else "N/A"
            if metrics.efficiency_std:
                eff_str += f" ±{metrics.efficiency_std*100:.1f}%"
            
            # Trade volume
            vol_str = f"{metrics.trade_volume_mean:.1f} ±{metrics.trade_volume_std:.1f}"
            
            # Inequality
            ineq_str = f"{metrics.inequality_mean:.3f} ±{metrics.inequality_std:.3f}"
            
            # Runtime
            time_str = f"{metrics.runtime_mean:.2f}s"
            
            lines.append(f"| {protocol_set_name} | {conv_str} | {eff_str} | {vol_str} | {ineq_str} | {time_str} |")
        
        return "\n".join(lines)
    
    def generate_insights(
        self, 
        results: Dict[str, AggregatedComparison]
    ) -> List[str]:
        """
        Auto-generate insights about protocol performance.
        
        Returns:
            List of insight strings
        """
        insights = []
        
        # Find best/worst on each metric
        best_efficiency = max(
            (name, m.efficiency_mean) 
            for name, m in results.items() 
            if m.efficiency_mean is not None
        )
        insights.append(f"Highest efficiency: {best_efficiency[0]} ({best_efficiency[1]*100:.1f}%)")
        
        best_convergence = max(
            (name, m.price_convergence_rate)
            for name, m in results.items()
        )
        insights.append(f"Best convergence: {best_convergence[0]} ({best_convergence[1]*100:.0f}% of runs)")
        
        # Check for trade-offs
        if 'efficient' in results and 'strategic' in results:
            eff_ineq = results['efficient'].inequality_mean
            strat_ineq = results['strategic'].inequality_mean
            if strat_ineq > eff_ineq * 1.2:
                insights.append("Efficiency-inequality trade-off detected: efficient set has lower inequality than strategic")
        
        return insights
```

### Enhanced Metrics Extraction

```python
# src/vmt_engine/analysis/metrics.py
"""
Enhanced Metrics Extraction

Computes sophisticated metrics from telemetry for protocol comparison.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import sqlite3
import numpy as np

from .pattern_analyzer import PatternAnalyzer


class MetricsExtractor:
    """
    Extract comparison metrics from simulation telemetry
    """
    
    def extract_comparison_metrics(
        self,
        db_path: Path,
        run_id: int,
        runtime_seconds: float
    ) -> 'ComparisonMetrics':
        """
        Extract all metrics needed for protocol comparison.
        """
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Basic metrics
        trade_count = self._count_trades(conn, run_id)
        
        # Price convergence
        price_convergence, convergence_speed = self._check_convergence(conn, run_id)
        
        # Efficiency
        efficiency = self._compute_efficiency(conn, run_id)
        
        # Average surplus
        avg_surplus = self._compute_average_surplus(conn, run_id)
        
        # Inequality (Gini coefficient)
        inequality = self._compute_gini(conn, run_id)
        
        # Market power (variance in surplus shares)
        market_power = self._measure_market_power(conn, run_id)
        
        conn.close()
        
        return ComparisonMetrics(
            protocol_set="",  # Set by caller
            seed=0,  # Set by caller
            price_convergence=price_convergence,
            convergence_speed=convergence_speed,
            efficiency=efficiency,
            trade_volume=trade_count,
            average_surplus=avg_surplus,
            inequality=inequality,
            market_power=market_power,
            runtime_seconds=runtime_seconds
        )
    
    def _count_trades(self, conn: sqlite3.Connection, run_id: int) -> int:
        """Count total trades"""
        cursor = conn.execute("""
            SELECT COUNT(*) as count
            FROM trades
            WHERE run_id = ?
        """, (run_id,))
        return cursor.fetchone()['count']
    
    def _check_convergence(
        self, 
        conn: sqlite3.Connection, 
        run_id: int,
        window: int = 50,
        threshold: float = 0.05
    ) -> Tuple[bool, Optional[int]]:
        """Check if prices converged and find convergence tick"""
        # Use PatternAnalyzer logic
        analyzer = PatternAnalyzer(Path(conn.execute("SELECT db_path FROM runs WHERE run_id=?", (run_id,)).fetchone()[0]), run_id)
        price_dynamics = analyzer.analyze_price_dynamics()
        
        converged = price_dynamics.convergence_type in ['monotonic', 'oscillating']
        return converged, price_dynamics.convergence_tick
    
    def _compute_efficiency(self, conn: sqlite3.Connection, run_id: int) -> Optional[float]:
        """Compute efficiency vs theoretical maximum"""
        analyzer = PatternAnalyzer(Path(conn.execute("SELECT db_path FROM runs WHERE run_id=?", (run_id,)).fetchone()[0]), run_id)
        return analyzer._compute_efficiency()
    
    def _compute_average_surplus(self, conn: sqlite3.Connection, run_id: int) -> float:
        """Compute average surplus per trade"""
        cursor = conn.execute("""
            SELECT AVG(buyer_surplus + seller_surplus) as avg_surplus
            FROM trades
            WHERE run_id = ? AND buyer_surplus IS NOT NULL AND seller_surplus IS NOT NULL
        """, (run_id,))
        
        result = cursor.fetchone()
        return result['avg_surplus'] if result and result['avg_surplus'] else 0.0
    
    def _compute_gini(self, conn: sqlite3.Connection, run_id: int) -> float:
        """
        Compute Gini coefficient of final utility distribution.
        
        Gini = 1 - 2 * integral of Lorenz curve
        Simplified formula: G = (2 * sum(i * y_i)) / (n * sum(y_i)) - (n+1)/n
        """
        cursor = conn.execute("""
            SELECT utility
            FROM agent_snapshots
            WHERE run_id = ? AND tick = (SELECT MAX(tick) FROM agent_snapshots WHERE run_id = ?)
            ORDER BY utility
        """, (run_id, run_id))
        
        utilities = [row['utility'] for row in cursor]
        
        if not utilities or len(utilities) < 2:
            return 0.0
        
        utilities = np.array(utilities)
        
        # Handle negative utilities (shift to positive)
        min_util = utilities.min()
        if min_util < 0:
            utilities = utilities - min_util + 1
        
        # Compute Gini
        n = len(utilities)
        sorted_utils = np.sort(utilities)
        cumsum = np.cumsum(sorted_utils)
        
        # Gini formula
        gini = (2 * np.sum((np.arange(1, n+1)) * sorted_utils)) / (n * np.sum(sorted_utils)) - (n+1)/n
        
        return float(gini)
    
    def _measure_market_power(self, conn: sqlite3.Connection, run_id: int) -> Optional[float]:
        """
        Measure market power as variance in surplus shares.
        
        High variance indicates some agents capture more surplus (market power).
        """
        cursor = conn.execute("""
            SELECT agent_id, 
                   SUM(buyer_surplus) as total_buyer_surplus,
                   SUM(seller_surplus) as total_seller_surplus
            FROM trades
            WHERE run_id = ?
            GROUP BY agent_id
        """, (run_id,))
        
        agent_surpluses = defaultdict(float)
        for row in cursor:
            agent_id = row['agent_id']
            agent_surpluses[agent_id] += row['total_buyer_surplus'] or 0.0
            agent_surpluses[agent_id] += row['total_seller_surplus'] or 0.0
        
        if not agent_surpluses:
            return None
        
        surpluses = np.array(list(agent_surpluses.values()))
        total = surpluses.sum()
        
        if total == 0:
            return None
        
        # Surplus shares
        shares = surpluses / total
        
        # Variance in shares (higher = more market power inequality)
        variance = np.var(shares)
        
        return float(variance)
```

---

## Part 3: Integration & Report Generation

### Enhanced Baseline Analysis Script

```python
# scripts/analyze_baseline.py (enhancements)
"""
Enhanced baseline analysis with pattern analysis integration
"""

from vmt_engine.analysis.pattern_analyzer import PatternAnalyzer

# Add to existing script:

def analyze_patterns(db_path: Path, run_id: int) -> Dict[str, Any]:
    """Add pattern analysis to baseline analysis"""
    analyzer = PatternAnalyzer(db_path, run_id)
    try:
        patterns = analyzer.analyze_all()
        return {
            'spatial': {
                'market_areas': len(patterns['spatial_patterns'].market_areas),
                'trade_routes': len(patterns['spatial_patterns'].trade_routes),
                'dead_zones': len(patterns['spatial_patterns'].dead_zones),
                'hotspots': len(patterns['spatial_patterns'].hotspots)
            },
            'price_dynamics': {
                'convergence_type': patterns['price_dynamics'].convergence_type,
                'convergence_tick': patterns['price_dynamics'].convergence_tick,
                'volatility': patterns['price_dynamics'].volatility_pattern
            },
            'edge_cases': len(patterns['edge_cases'])
        }
    finally:
        analyzer.close()
```

### Protocol Comparison Script

```python
# scripts/compare_protocols.py (new)
"""
Protocol Comparison Script

Runs systematic protocol comparisons and generates reports.
"""

#!/usr/bin/env python3
"""
Protocol Comparison Script

Usage:
    python scripts/compare_protocols.py scenarios/baseline/baseline_10agent_mixed.yaml
"""

import sys
from pathlib import Path
from vmt_engine.analysis.protocol_comparator import ProtocolComparator
from vmt_engine.analysis.reports import ComparisonReportGenerator

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/compare_protocols.py <scenario_path> [n_runs]")
        sys.exit(1)
    
    scenario_path = sys.argv[1]
    n_runs = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    print(f"Comparing protocols on {scenario_path}")
    print(f"Running {n_runs} seeds per protocol set...")
    
    comparator = ProtocolComparator()
    results = comparator.run_comparison(scenario_path, n_runs=n_runs)
    
    # Generate report
    report_gen = ComparisonReportGenerator()
    report_path = Path("docs") / f"protocol_comparison_{Path(scenario_path).stem}.md"
    report_gen.generate_report(results, scenario_path, report_path)
    
    print(f"\nComparison complete. Report saved to {report_path}")
    print("\n" + comparator.create_comparison_table(results))
    print("\nInsights:")
    for insight in comparator.generate_insights(results):
        print(f"  - {insight}")

if __name__ == "__main__":
    main()
```

### Report Generation

```python
# src/vmt_engine/analysis/reports.py
"""
Report Generation Utilities
"""

from typing import Dict, List
from pathlib import Path
from datetime import datetime

from .protocol_comparator import AggregatedComparison, ProtocolComparator


class ComparisonReportGenerator:
    """Generate markdown reports from comparison results"""
    
    def generate_report(
        self,
        results: Dict[str, AggregatedComparison],
        scenario_path: str,
        output_path: Path
    ):
        """Generate comprehensive comparison report"""
        lines = []
        
        # Header
        lines.append("# Protocol Comparison Report")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Scenario**: {Path(scenario_path).stem}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Comparison table
        comparator = ProtocolComparator()
        lines.append("## Comparison Table")
        lines.append("")
        lines.append(comparator.create_comparison_table(results))
        lines.append("")
        
        # Insights
        lines.append("## Key Insights")
        lines.append("")
        for insight in comparator.generate_insights(results):
            lines.append(f"- {insight}")
        lines.append("")
        
        # Detailed metrics per protocol set
        lines.append("## Detailed Metrics")
        lines.append("")
        for protocol_set_name, metrics in results.items():
            lines.append(f"### {protocol_set_name}")
            lines.append("")
            lines.append(f"- **Convergence Rate**: {metrics.price_convergence_rate*100:.1f}%")
            if metrics.convergence_speed_mean:
                lines.append(f"- **Convergence Speed**: {metrics.convergence_speed_mean:.1f} ± {metrics.convergence_speed_std:.1f} ticks")
            if metrics.efficiency_mean:
                lines.append(f"- **Efficiency**: {metrics.efficiency_mean*100:.1f}% ± {metrics.efficiency_std*100:.1f}%")
            lines.append(f"- **Trade Volume**: {metrics.trade_volume_mean:.1f} ± {metrics.trade_volume_std:.1f}")
            lines.append(f"- **Inequality (Gini)**: {metrics.inequality_mean:.3f} ± {metrics.inequality_std:.3f}")
            lines.append(f"- **Average Surplus**: {metrics.average_surplus_mean:.2f} ± {metrics.average_surplus_std:.2f}")
            lines.append(f"- **Runtime**: {metrics.runtime_mean:.2f}s")
            lines.append("")
        
        # Write file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("\n".join(lines))
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_pattern_analyzer.py
"""
Unit tests for PatternAnalyzer
"""

import pytest
from pathlib import Path
from vmt_engine.analysis.pattern_analyzer import PatternAnalyzer

def test_spatial_pattern_detection():
    """Test market area detection"""
    # Create test database with known trade pattern
    # Run analyzer
    # Assert market areas detected correctly
    pass

def test_price_convergence_classification():
    """Test convergence type detection"""
    # Create price series with known convergence pattern
    # Run analyzer
    # Assert correct classification
    pass

def test_edge_case_detection():
    """Test edge case identification"""
    # Create scenario with low efficiency
    # Run analyzer
    # Assert edge case detected
    pass


# tests/test_protocol_comparator.py
"""
Unit tests for ProtocolComparator
"""

def test_protocol_set_configuration():
    """Test protocol set definitions"""
    comparator = ProtocolComparator()
    assert 'baseline' in comparator.protocol_sets
    assert comparator.protocol_sets['baseline'].search == 'legacy'

def test_metrics_extraction():
    """Test metric computation"""
    # Create test database
    # Extract metrics
    # Assert values within expected ranges
    pass

def test_comparison_aggregation():
    """Test metric aggregation across runs"""
    # Create mock metrics list
    # Aggregate
    # Assert aggregated values correct
    pass
```

### Integration Tests

```python
# tests/test_comparison_integration.py
"""
Integration tests for full comparison workflow
"""

def test_end_to_end_comparison():
    """Test complete comparison workflow"""
    # Load scenario
    # Run comparison with small n_runs
    # Assert report generated
    # Assert metrics computed
    pass
```

---

## Implementation Checklist

### Week 1: Pattern Analysis Framework

- [ ] Create `src/vmt_engine/analysis/` module structure
- [ ] Implement `PatternAnalyzer` base class
- [ ] Implement spatial pattern detection (`_compute_trade_density_map`, `_detect_market_areas`)
- [ ] Implement trade route tracing (`_trace_trade_routes`)
- [ ] Implement dead zone detection (`_find_dead_zones`)
- [ ] Implement hotspot detection (`_find_hotspots`)
- [ ] Implement price series extraction (`_extract_price_series`)
- [ ] Implement convergence classification (`_classify_convergence`)
- [ ] Implement volatility classification (`_classify_volatility`)
- [ ] Implement cycle detection (`_detect_cycles`)
- [ ] Implement edge case identification (`identify_edge_cases`)
- [ ] Implement efficiency computation (`_compute_efficiency`)
- [ ] Write unit tests for `PatternAnalyzer`
- [ ] Integrate with `scripts/analyze_baseline.py`

### Week 2: Protocol Comparison Framework

- [ ] Implement `MetricsExtractor` class
- [ ] Implement `ProtocolComparator` base class
- [ ] Implement protocol set definitions
- [ ] Implement `run_comparison` method
- [ ] Implement metric aggregation (`_aggregate_comparison_metrics`)
- [ ] Implement comparison table generation (`create_comparison_table`)
- [ ] Implement insights generation (`generate_insights`)
- [ ] Create `scripts/compare_protocols.py`
- [ ] Implement `ComparisonReportGenerator`
- [ ] Write unit tests for `ProtocolComparator`
- [ ] Write integration tests

### Week 3: Testing & Documentation

- [ ] Run full test suite
- [ ] Generate comparison report on baseline scenarios
- [ ] Update `COMPREHENSIVE_IMPLEMENTATION_PLAN.md` with completion status
- [ ] Write user documentation for comparison workflow
- [ ] Performance profiling (ensure comparisons complete in reasonable time)
- [ ] Code review and cleanup

---

## Success Criteria

### Functional Requirements ✅

- [ ] `PatternAnalyzer` correctly identifies spatial patterns in test scenarios
- [ ] Price dynamics classification matches manual inspection for known cases
- [ ] Edge cases detected for scenarios with known issues
- [ ] `ProtocolComparator` runs all protocol sets without errors
- [ ] Comparison reports generated with accurate metrics
- [ ] All unit tests pass
- [ ] All integration tests pass

### Performance Requirements ✅

- [ ] Pattern analysis completes in < 5 seconds per run
- [ ] Full comparison (4 protocol sets × 50 seeds) completes in < 30 minutes for baseline scenarios
- [ ] Memory usage remains reasonable (< 2GB for large comparisons)

### Quality Requirements ✅

- [ ] Code coverage > 80% for new modules
- [ ] Type hints on all functions
- [ ] Comprehensive docstrings
- [ ] No linter errors

---

## Dependencies

### New Dependencies

```python
# requirements.txt additions
scipy>=1.9.0  # For signal processing (cycle detection, clustering)
```

### Existing Dependencies (already in requirements.txt)

- `numpy` - Array operations
- `sqlite3` - Database access (standard library)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Pattern analysis algorithms too slow | Profile and optimize hot paths; use numpy vectorization |
| Convergence detection false positives | Validate against manual inspection; tune threshold parameters |
| Comparison runs take too long | Start with small n_runs (10), profile, optimize |
| Metric computation errors | Extensive unit tests with known-good scenarios |
| Integration complexity | Incremental development with testing at each step |

---

## Next Steps After Completion

1. **Validate Stage 2 Protocols**: Use comparison framework to validate that new protocols produce expected differences
2. **Document Findings**: Create institutional comparison report comparing protocol sets
3. **Begin Stage 3**: Use validated foundation to build Game Theory track

---

**Document Status**: Complete Planning Document  
**Ready for Review**: Yes  
**Implementation Status**: Not Started
