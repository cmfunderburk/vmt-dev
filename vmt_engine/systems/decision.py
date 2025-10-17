from __future__ import annotations
from typing import TYPE_CHECKING
from .matching import choose_partner
from .movement import choose_forage_target

if TYPE_CHECKING:
    from ..simulation import Simulation
    from ..core import Agent


class DecisionSystem:
    """Phase 2: Agents make decisions about targets."""

    def execute(self, sim: "Simulation") -> None:
        for agent in sim.agents:
            # Try to find a trading partner first
            neighbors = agent.perception_cache.get("neighbors", [])
            partner_id, surplus, all_candidates = choose_partner(
                agent, neighbors, sim.agent_by_id, sim.tick
            )

            if partner_id is not None:
                # Move toward partner
                partner = sim.agent_by_id[partner_id]
                agent.target_pos = partner.pos
                agent.target_agent_id = partner_id

                # Log decision
                alternatives_str = "; ".join(
                    [f"{nid}:{s:.4f}" for nid, s in all_candidates]
                )
                sim.telemetry.log_decision(
                    sim.tick,
                    agent.id,
                    partner_id,
                    surplus,
                    "trade",
                    partner.pos[0],
                    partner.pos[1],
                    len(neighbors),
                    alternatives_str,
                )
            else:
                # Fall back to foraging
                resource_cells = agent.perception_cache.get("resource_cells", [])
                target = choose_forage_target(
                    agent,
                    resource_cells,
                    sim.params["beta"],
                    sim.params["forage_rate"],
                )
                agent.target_pos = target
                agent.target_agent_id = None

                # Log decision
                target_type = "forage" if target is not None else "idle"
                target_x = target[0] if target is not None else None
                target_y = target[1] if target is not None else None
                alternatives_str = "; ".join(
                    [f"{nid}:{s:.4f}" for nid, s in all_candidates]
                )
                sim.telemetry.log_decision(
                    sim.tick,
                    agent.id,
                    None,
                    None,
                    target_type,
                    target_x,
                    target_y,
                    len(neighbors),
                    alternatives_str,
                )
