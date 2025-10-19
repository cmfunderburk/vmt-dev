"""
Headless entry point for running VMT simulations without visualization.

This is used for generating deterministic telemetry data for testing and analysis.
"""
import sys
import os
import argparse

# Add the 'src' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario
from telemetry.config import LogConfig


def main():
    """Run VMT simulation headlessly."""
    parser = argparse.ArgumentParser(description="Run VMT simulation headlessly.")
    parser.add_argument("scenario_file", help="Path to the scenario YAML file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for simulation")
    parser.add_argument("--max-ticks", type=int, default=100, help="Number of ticks to run")
    args = parser.parse_args()

    print(f"Loading scenario: {args.scenario_file}")
    scenario = load_scenario(args.scenario_file)

    print(f"Initializing simulation with seed {args.seed} for {args.max_ticks} ticks...")
    # Use standard log config to ensure all data is captured
    sim = Simulation(scenario, seed=args.seed, log_config=LogConfig.standard())

    # Run for a fixed number of ticks
    sim.run(max_ticks=args.max_ticks)
    
    sim.close()

    print("\nSimulation ended.")
    print(f"Final tick: {sim.tick}")
    print(f"Logs saved to {sim.telemetry.db.db_path}")


if __name__ == "__main__":
    main()
