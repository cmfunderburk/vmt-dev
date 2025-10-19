#!/usr/bin/env python3
"""
Performance benchmark suite for VMT engine.

Runs standardized performance scenarios and reports timing metrics.
Use as baseline for detecting performance regressions across development phases.

Usage:
    python scripts/benchmark_performance.py
    python scripts/benchmark_performance.py --ticks 1000
    python scripts/benchmark_performance.py --scenario forage
"""

import argparse
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation
from telemetry.config import LogConfig


SCENARIOS = {
    "forage": {
        "path": "scenarios/perf_forage_only.yaml",
        "description": "Forage-only: 100 agents, 50x50 grid, high resource density"
    },
    "exchange": {
        "path": "scenarios/perf_exchange_only.yaml",
        "description": "Exchange-only: 100 agents, large inventories, barter trading"
    },
    "both": {
        "path": "scenarios/perf_both_modes.yaml",
        "description": "Combined: 100 agents, alternating forage/trade modes"
    }
}


def run_benchmark(scenario_name: str, ticks: int, seed: int = 42, log_level: str = "standard"):
    """
    Run a single benchmark scenario and return timing metrics.
    
    Args:
        scenario_name: Key from SCENARIOS dict
        ticks: Number of simulation ticks to run
        seed: Random seed for reproducibility
        log_level: Logging level ("standard", "debug", or "off")
    
    Returns:
        dict with timing metrics
    """
    info = SCENARIOS[scenario_name]
    scenario_path = info["path"]
    
    print(f"\n{'='*70}")
    print(f"Benchmark: {scenario_name.upper()}")
    print(f"Description: {info['description']}")
    print(f"Scenario: {scenario_path}")
    print(f"Ticks: {ticks}, Seed: {seed}, Logging: {log_level}")
    print('='*70)
    
    # Configure logging
    if log_level == "standard":
        log_cfg = LogConfig.standard()
    elif log_level == "debug":
        log_cfg = LogConfig.debug()
    else:
        log_cfg = LogConfig(use_database=False)
    
    # Load scenario
    print("Loading scenario...", end=" ", flush=True)
    load_start = time.perf_counter()
    config = load_scenario(scenario_path)
    load_time = time.perf_counter() - load_start
    print(f"✓ ({load_time:.3f}s)")
    
    # Initialize simulation
    print("Initializing simulation...", end=" ", flush=True)
    init_start = time.perf_counter()
    sim = Simulation(config, seed=seed, log_config=log_cfg)
    init_time = time.perf_counter() - init_start
    print(f"✓ ({init_time:.3f}s)")
    
    n_agents = len(sim.agents)
    grid_size = sim.config.N
    
    # Run simulation
    print(f"Running {ticks} ticks...", end=" ", flush=True)
    run_start = time.perf_counter()
    sim.run(max_ticks=ticks)
    run_time = time.perf_counter() - run_start
    print(f"✓ ({run_time:.3f}s)")
    
    # Close simulation
    print("Finalizing...", end=" ", flush=True)
    close_start = time.perf_counter()
    sim.close()
    close_time = time.perf_counter() - close_start
    print(f"✓ ({close_time:.3f}s)")
    
    # Calculate metrics
    total_time = load_time + init_time + run_time + close_time
    ticks_per_second = ticks / run_time if run_time > 0 else 0
    seconds_per_tick = run_time / ticks if ticks > 0 else 0
    
    # Report metrics
    print(f"\n{'─'*70}")
    print("RESULTS:")
    print(f"  Total time:        {total_time:7.3f}s")
    print(f"  Simulation time:   {run_time:7.3f}s")
    print(f"  Ticks/second:      {ticks_per_second:7.1f}")
    print(f"  Seconds/tick:      {seconds_per_tick:7.4f}s")
    print(f"  Grid size:         {grid_size}x{grid_size} ({grid_size**2:,} cells)")
    print(f"  Agents:            {n_agents}")
    print(f"  Agent-ticks:       {n_agents * ticks:,}")
    print('─'*70)
    
    return {
        "scenario": scenario_name,
        "ticks": ticks,
        "agents": n_agents,
        "grid_size": grid_size,
        "total_time": total_time,
        "load_time": load_time,
        "init_time": init_time,
        "run_time": run_time,
        "close_time": close_time,
        "ticks_per_second": ticks_per_second,
        "seconds_per_tick": seconds_per_tick,
    }


def run_all_benchmarks(ticks: int, seed: int = 42, log_level: str = "summary"):
    """Run all benchmark scenarios and print summary."""
    results = []
    
    for scenario_name in SCENARIOS.keys():
        try:
            result = run_benchmark(scenario_name, ticks, seed, log_level)
            results.append(result)
        except Exception as e:
            print(f"\n❌ ERROR in {scenario_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Print summary table
    if results:
        print(f"\n\n{'='*70}")
        print("SUMMARY")
        print('='*70)
        print(f"{'Scenario':<15} {'Ticks':>8} {'Time (s)':>10} {'TPS':>10} {'ms/tick':>10}")
        print('─'*70)
        for r in results:
            print(f"{r['scenario']:<15} {r['ticks']:>8} {r['run_time']:>10.2f} "
                  f"{r['ticks_per_second']:>10.1f} {r['seconds_per_tick']*1000:>10.2f}")
        print('='*70)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run VMT performance benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available scenarios:
  forage    - Forage-only mode
  exchange  - Exchange-only mode
  both      - Combined forage+exchange mode
  all       - Run all benchmarks (default)

Examples:
  python scripts/benchmark_performance.py
  python scripts/benchmark_performance.py --ticks 1000
  python scripts/benchmark_performance.py --scenario exchange --ticks 250
  python scripts/benchmark_performance.py --log-level off
        """
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()) + ["all"],
        default="all",
        help="Which benchmark to run (default: all)"
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=500,
        help="Number of simulation ticks (default: 500)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--log-level",
        choices=["standard", "debug", "off"],
        default="standard",
        help="Telemetry logging level (default: standard)"
    )
    
    args = parser.parse_args()
    
    print("VMT Performance Benchmark Suite")
    print(f"Python path: {sys.executable}")
    print(f"Working directory: {Path.cwd()}")
    
    if args.scenario == "all":
        run_all_benchmarks(args.ticks, args.seed, args.log_level)
    else:
        run_benchmark(args.scenario, args.ticks, args.seed, args.log_level)


if __name__ == "__main__":
    main()

