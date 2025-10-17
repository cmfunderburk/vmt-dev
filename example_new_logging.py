#!/usr/bin/env python3
"""
Example demonstrating the new SQLite-based logging system.
"""

import sys
import os

# Add the 'src' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from vmt_engine.simulation import Simulation
from telemetry import LogConfig, LogLevel
from scenarios.loader import load_scenario


def run_with_summary_logging():
    """Run simulation with SUMMARY logging (minimal)."""
    print("Running with SUMMARY logging...")
    scenario = load_scenario("scenarios/three_agent_barter.yaml")
    log_config = LogConfig.summary()
    
    sim = Simulation(scenario, seed=42, log_config=log_config)
    sim.run(max_ticks=100)
    sim.close()
    print("✓ Summary log saved to: ./logs/telemetry.db")


def run_with_standard_logging():
    """Run simulation with STANDARD logging (recommended)."""
    print("\nRunning with STANDARD logging...")
    scenario = load_scenario("scenarios/three_agent_barter.yaml")
    log_config = LogConfig.standard()
    
    sim = Simulation(scenario, seed=42, log_config=log_config)
    sim.run(max_ticks=100)
    sim.close()
    print("✓ Standard log saved to: ./logs/telemetry.db")


def run_with_debug_logging():
    """Run simulation with DEBUG logging (verbose)."""
    print("\nRunning with DEBUG logging...")
    scenario = load_scenario("scenarios/three_agent_barter.yaml")
    log_config = LogConfig.debug()
    
    sim = Simulation(scenario, seed=42, log_config=log_config)
    sim.run(max_ticks=100)
    sim.close()
    print("✓ Debug log saved to: ./logs/telemetry.db")


def run_with_custom_config():
    """Run simulation with custom logging configuration."""
    print("\nRunning with custom logging config...")
    scenario = load_scenario("scenarios/three_agent_barter.yaml")
    
    # Custom configuration
    log_config = LogConfig(
        level=LogLevel.STANDARD,
        agent_snapshot_frequency=5,    # Every 5 ticks instead of 1
        resource_snapshot_frequency=20,  # Every 20 ticks instead of 10
        log_decisions=True,
        log_trades=True,
        log_trade_attempts=False,
        batch_size=200  # Larger batch for better performance
    )
    
    sim = Simulation(scenario, seed=42, log_config=log_config)
    sim.run(max_ticks=100)
    sim.close()
    print("✓ Custom log saved to: ./logs/telemetry.db")


def run_and_export_to_csv():
    """Run simulation and export database to CSV (for backward compatibility)."""
    print("\nRunning simulation and exporting to CSV...")
    scenario = load_scenario("scenarios/three_agent_barter.yaml")
    
    # Run with standard logging
    sim = Simulation(scenario, seed=42, log_config=LogConfig.standard())
    sim.run(max_ticks=100)
    sim.close()
    
    # Export database to CSV
    from telemetry.database import TelemetryDatabase
    from vmt_log_viewer.csv_export import CSVExporter
    
    db = TelemetryDatabase("./logs/telemetry.db")
    runs = db.get_runs()
    if runs:
        exporter = CSVExporter(db)
        output_dir = "./logs/csv_export"
        exporter.export_run(runs[0]['run_id'], output_dir)
        db.close()
        print(f"✓ CSV files exported to: {output_dir}/")


def query_database_example():
    """Example of querying the database programmatically."""
    print("\nQuerying database...")
    from telemetry.database import TelemetryDatabase
    from vmt_log_viewer.queries import QueryBuilder
    
    db = TelemetryDatabase("./logs/telemetry.db")
    
    # Get all runs
    runs = db.get_runs()
    if not runs:
        print("No runs in database. Run a simulation first!")
        db.close()
        return
    
    run = runs[0]
    print(f"\nMost recent run:")
    print(f"  Run ID: {run['run_id']}")
    print(f"  Scenario: {run['scenario_name']}")
    print(f"  Agents: {run['num_agents']}")
    print(f"  Ticks: {run['total_ticks']}")
    
    # Get trade statistics
    query, params = QueryBuilder.get_trade_statistics(run['run_id'])
    stats = db.execute(query, params).fetchone()
    
    if stats and stats['total_trades']:
        print(f"\nTrade Statistics:")
        print(f"  Total Trades: {stats['total_trades']}")
        print(f"  Average dA: {stats['avg_dA']:.2f}")
        print(f"  Average dB: {stats['avg_dB']:.2f}")
        print(f"  Average Price: {stats['avg_price']:.4f}")
    else:
        print("\n  No trades recorded")
    
    # Get agent 0's trajectory
    query, params = QueryBuilder.get_agent_trajectory(run['run_id'], agent_id=0, end_tick=10)
    trajectory = db.execute(query, params).fetchall()
    
    print(f"\nAgent 0 trajectory (first 10 ticks):")
    for point in trajectory[:10]:
        tick = int(point['tick']) if point['tick'] else 0
        x = int(point['x']) if point['x'] else 0
        y = int(point['y']) if point['y'] else 0
        inv_a = int(point['inventory_A']) if point['inventory_A'] else 0
        inv_b = int(point['inventory_B']) if point['inventory_B'] else 0
        utility = float(point['utility']) if point['utility'] else 0.0
        print(f"  Tick {tick:3d}: ({x:2d}, {y:2d}) "
              f"A={inv_a:2d} B={inv_b:2d} U={utility:8.2f}")
    
    db.close()


def main():
    """Run all examples."""
    print("=" * 60)
    print("VMT New Logging System Examples")
    print("=" * 60)
    
    # Choose which example to run
    print("\nChoose an example:")
    print("1. SUMMARY logging (minimal)")
    print("2. STANDARD logging (recommended)")
    print("3. DEBUG logging (verbose)")
    print("4. Custom configuration")
    print("5. Export database to CSV")
    print("6. Query database")
    print("7. All examples")
    
    choice = input("\nEnter choice (1-7): ").strip()
    
    if choice == "1":
        run_with_summary_logging()
    elif choice == "2":
        run_with_standard_logging()
    elif choice == "3":
        run_with_debug_logging()
    elif choice == "4":
        run_with_custom_config()
    elif choice == "5":
        run_and_export_to_csv()
    elif choice == "6":
        query_database_example()
    elif choice == "7":
        run_with_summary_logging()
        run_with_standard_logging()
        run_with_debug_logging()
        run_with_custom_config()
        run_and_export_to_csv()
        query_database_example()
    else:
        print("Invalid choice")
        return
    
    print("\n" + "=" * 60)
    print("Done! View logs with: python view_logs.py")
    print("=" * 60)


if __name__ == '__main__':
    main()

