from __future__ import annotations
from typing import TYPE_CHECKING
from .quotes import refresh_quotes_if_needed

if TYPE_CHECKING:
    from ..simulation import Simulation


class HousekeepingSystem:
    """Phase 7: Update quotes, log telemetry, cleanup."""

    def execute(self, sim: "Simulation") -> None:
        # Refresh quotes for agents whose inventory changed
        for agent in sim.agents:
            refresh_quotes_if_needed(
                agent, 
                sim.params["spread"], 
                sim.params["epsilon"]
            )
        
        # Verify pairing integrity
        self._verify_pairing_integrity(sim)

        # Log telemetry
        sim.telemetry.log_agent_snapshots(sim.tick, sim.agents)
        sim.telemetry.log_resource_snapshots(sim.tick, sim.grid)
    
    def _verify_pairing_integrity(self, sim: "Simulation") -> None:
        """Defensive check: ensure all pairings are bidirectional."""
        for agent in sim.agents:
            if agent.paired_with_id is not None:
                partner_id = agent.paired_with_id
                partner = sim.agent_by_id.get(partner_id)
                
                if partner is None or partner.paired_with_id != agent.id:
                    # Asymmetric pairing - repair
                    sim.telemetry.log_pairing_event(
                        sim.tick, agent.id, partner_id, "unpair", "integrity_repair"
                    )
                    agent.paired_with_id = None
