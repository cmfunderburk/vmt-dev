"""
Quick test script to verify protocol scenarios load and run correctly.
"""

import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation

scenarios = [
    "scenarios/pro_tests/protocol_comparison_baseline.yaml",
    "scenarios/pro_tests/legacy_with_random_walk.yaml",
    "scenarios/pro_tests/legacy_with_random_matching.yaml",
    "scenarios/pro_tests/legacy_with_split_difference.yaml",
]

for scenario_path in scenarios:
    try:
        s = load_scenario(scenario_path)
        sim = Simulation(s, seed=42)
        sim.run(3)
        print(f"✓ {s.name:35} search={sim.search_protocol.name:15} matching={sim.matching_protocol.name:20} bargaining={sim.bargaining_protocol.name}")
    except Exception as e:
        print(f"✗ {scenario_path:35} ERROR: {e}")

