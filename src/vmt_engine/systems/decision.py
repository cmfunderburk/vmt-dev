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
        # Clear stale claims at start of tick
        if sim.params.get("enable_resource_claiming", False):
            self._clear_stale_claims(sim)
        
        # Process agents in ID order (deterministic)
        for agent in sorted(sim.agents, key=lambda a: a.id):
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
        """Choose forage target from available (unclaimed) resources."""
        resource_cells = view.get("resource_cells", [])
        
        # Filter out resources claimed by other agents
        available_resources = self._filter_claimed_resources(resource_cells, sim, agent.id)
        
        # Choose from available resources
        target = choose_forage_target(
            agent, available_resources, sim.params["beta"], sim.params["forage_rate"]
        )
        
        # Claim the resource if target selected
        if target is not None:
            self._claim_resource(sim, agent.id, target)
        
        target_type = "forage" if target is not None else "idle"
        return target, target_type
    
    def _log_decision(self, sim, agent, partner_id, surplus, target_type, target_pos, view, candidates=None):
        """Log decision with mode context and claimed resource."""
        neighbors = view.get("neighbors", [])
        target_x = target_pos[0] if target_pos is not None else None
        target_y = target_pos[1] if target_pos is not None else None
        
        # Determine claimed resource position (only for forage targets)
        claimed_pos = None
        if target_type == "forage" and target_pos is not None:
            claimed_pos = target_pos
        
        alternatives_str = ""
        if candidates:
            alternatives_str = "; ".join([f"{nid}:{s:.4f}" for nid, s in candidates])
        
        sim.telemetry.log_decision(
            sim.tick, agent.id, partner_id, surplus,
            target_type, target_x, target_y, len(neighbors),
            alternatives_str, mode=sim.current_mode, claimed_resource_pos=claimed_pos
        )
    
    def _clear_stale_claims(self, sim: "Simulation") -> None:
        """Remove claims from agents that reached target or changed target."""
        claims_to_remove = []
        
        for pos, agent_id in sim.resource_claims.items():
            agent = sim.agent_by_id.get(agent_id)
            
            # Remove claim if:
            # 1. Agent doesn't exist (shouldn't happen but defensive)
            # 2. Agent reached the resource (pos == target)
            # 3. Agent changed target (target_pos != claimed pos)
            if agent is None or agent.pos == pos or agent.target_pos != pos:
                claims_to_remove.append(pos)
        
        for pos in claims_to_remove:
            del sim.resource_claims[pos]
    
    def _filter_claimed_resources(self, resource_cells, sim: "Simulation", current_agent_id: int):
        """Filter out resources claimed by OTHER agents."""
        if not sim.params.get("enable_resource_claiming", False):
            return resource_cells  # Feature disabled, return all
        
        available = []
        for cell in resource_cells:
            claiming_agent = sim.resource_claims.get(cell.position)
            
            # Include if: unclaimed OR claimed by current agent
            if claiming_agent is None or claiming_agent == current_agent_id:
                available.append(cell)
        
        return available
    
    def _claim_resource(self, sim: "Simulation", agent_id: int, resource_pos: tuple[int, int]) -> None:
        """Record that agent is claiming this resource."""
        if sim.params.get("enable_resource_claiming", False):
            sim.resource_claims[resource_pos] = agent_id