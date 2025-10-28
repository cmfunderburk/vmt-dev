from typing import Callable, Any
from . import builders, run as run_helpers


def assert_deterministic(
    build_sim: Callable[[int], Any],
    steps: int,
    seed: int = 42,
    key_fn: Callable[[Any], Any] | None = None,
):
    """Assert that running twice with same seed yields identical summaries.

    - build_sim(seed) should return a fresh Simulation
    - key_fn(sim) can produce a comparable summary; default uses trade_count
    """
    key_fn = key_fn or (lambda sim: run_helpers.trade_count(sim))

    sim1 = build_sim(seed)
    sim2 = build_sim(seed)

    run_helpers.run_ticks(sim1, steps)
    run_helpers.run_ticks(sim2, steps)

    assert key_fn(sim1) == key_fn(sim2), "Same seed should produce identical summary"


def assert_some_trades(sim):
    """Assert that some trades occurred in the simulation run."""
    assert run_helpers.trade_count(sim) > 0, "Expected some trades to occur"


def assert_nonnegative_prices(sim):
    """Assert that all recent trades have nonnegative prices."""
    for t in run_helpers.recent_trades(sim):
        assert t.get("price", 0.0) >= 0.0


