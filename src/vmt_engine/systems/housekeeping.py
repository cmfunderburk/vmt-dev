from __future__ import annotations
from typing import TYPE_CHECKING
from .quotes import refresh_quotes_if_needed

if TYPE_CHECKING:
    from ..simulation import Simulation


class HousekeepingSystem:
    """Phase 7: Update quotes, log telemetry, cleanup."""

    def execute(self, sim: "Simulation") -> None:
        # Refresh quotes for agents whose inventory changed (money-aware API)
        money_scale = sim.params.get("money_scale", 1)
        exchange_regime = sim.params.get("exchange_regime", "barter_only")
        
        for agent in sim.agents:
            refresh_quotes_if_needed(
                agent, 
                sim.params["spread"], 
                sim.params["epsilon"],
                money_scale=money_scale,
                exchange_regime=exchange_regime
            )

        # Log telemetry
        sim.telemetry.log_agent_snapshots(sim.tick, sim.agents)
        sim.telemetry.log_resource_snapshots(sim.tick, sim.grid)
