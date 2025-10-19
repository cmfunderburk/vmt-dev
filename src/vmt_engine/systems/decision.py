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
            view = agent.perception_cache
            
            # Mode-aware decision making
            if sim.current_mode == "forage":
                # Only consider resource targets
                target_pos, target_type = self._choose_forage_target(agent, view, sim)
                agent.target_pos = target_pos
                agent.target_agent_id = None
                self._log_decision(sim, agent, None, None, target_type, target_pos, view)
                
            elif sim.current_mode == "trade":
                # Only consider trade partners
                partner_id, surplus, candidates = self._choose_trade_target(agent, view, sim)
                if partner_id is not None:
                    partner = sim.agent_by_id[partner_id]
                    agent.target_pos = partner.pos
                    agent.target_agent_id = partner_id
                    self._log_decision(sim, agent, partner_id, surplus, "trade", partner.pos, view, candidates)
                else:
                    # No partner available, idle
                    agent.target_pos = None
                    agent.target_agent_id = None
                    self._log_decision(sim, agent, None, None, "idle", None, view, candidates)
                    
            else:  # mode == "both"
                # Current behavior - consider both
                partner_id, surplus, candidates = self._choose_trade_target(agent, view, sim)
                if partner_id is not None:
                    partner = sim.agent_by_id[partner_id]
                    agent.target_pos = partner.pos
                    agent.target_agent_id = partner_id
                    self._log_decision(sim, agent, partner_id, surplus, "trade", partner.pos, view, candidates)
                else:
                    # Fall back to foraging
                    target_pos, target_type = self._choose_forage_target(agent, view, sim)
                    agent.target_pos = target_pos
                    agent.target_agent_id = None
                    self._log_decision(sim, agent, None, None, target_type, target_pos, view, candidates)
    
    def _choose_trade_target(self, agent, view, sim):
        """Choose trading partner."""
        neighbors = view.get("neighbors", [])
        partner_id, surplus, all_candidates = choose_partner(
            agent, neighbors, sim.agent_by_id, sim.tick
        )
        return partner_id, surplus, all_candidates
    
    def _choose_forage_target(self, agent, view, sim):
        """Choose forage target."""
        resource_cells = view.get("resource_cells", [])
        target = choose_forage_target(
            agent, resource_cells, sim.params["beta"], sim.params["forage_rate"]
        )
        target_type = "forage" if target is not None else "idle"
        return target, target_type
    
    def _log_decision(self, sim, agent, partner_id, surplus, target_type, target_pos, view, candidates=None):
        """Log decision with mode context."""
        neighbors = view.get("neighbors", [])
        target_x = target_pos[0] if target_pos is not None else None
        target_y = target_pos[1] if target_pos is not None else None
        
        alternatives_str = ""
        if candidates:
            alternatives_str = "; ".join([f"{nid}:{s:.4f}" for nid, s in candidates])
        
        sim.telemetry.log_decision(
            sim.tick, agent.id, partner_id, surplus,
            target_type, target_x, target_y, len(neighbors),
            alternatives_str, mode=sim.current_mode
        )
