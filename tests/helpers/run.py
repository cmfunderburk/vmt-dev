from typing import Any


def run_ticks(sim, steps: int) -> dict[str, Any]:
    """Run a simulation for a number of ticks and return a small summary."""
    sim.run(steps)
    return {
        "tick": sim.tick,
        "trade_count": len(sim.telemetry.recent_trades_for_renderer),
    }


def recent_trades(sim):
    """Return recent trades from telemetry (DB-free, stable)."""
    return list(sim.telemetry.recent_trades_for_renderer)


def trade_count(sim) -> int:
    """Return number of recent trades."""
    return len(sim.telemetry.recent_trades_for_renderer)


