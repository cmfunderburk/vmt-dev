"""
Decision System - Protocol Orchestrator

Coordinates search and matching protocols to make agent decisions.

Phase 2 of the 7-phase simulation tick:
1. Clear stale resource claims
2. Search phase: agents build preferences and select targets
3. Matching phase: agents form bilateral pairs
4. Log decisions to telemetry

Version: 2025.10.26 (Phase 1 - Refactored for Protocol System)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from ..protocols import (
    SearchProtocol,
    MatchingProtocol,
    SetTarget,
    ClaimResource,
    ReleaseClaim,
    Pair,
    Unpair,
    build_world_view_for_agent,
    build_protocol_context,
)

if TYPE_CHECKING:
    from ..simulation import Simulation
    from ..core import Agent


class DecisionSystem:
    """
    Phase 2: Orchestrate protocol-based decision making.
    
    Responsibilities:
    - Build WorldView/ProtocolContext from simulation state
    - Call search and matching protocols
    - Apply effects to update agent state
    - Log decisions to telemetry
    
    The actual decision logic is delegated to protocols.
    """
    
    def __init__(self):
        self.search_protocol: Optional[SearchProtocol] = None
        self.matching_protocol: Optional[MatchingProtocol] = None
    
    def execute(self, sim: "Simulation") -> None:
        """Execute decision phase using protocols."""
        
        # Step 1: Clear stale resource claims
        self._clear_stale_claims(sim)
        
        # Step 2: Search phase - build preferences and select targets
        preferences = self._execute_search_phase(sim)
        
        # Step 3: Matching phase - establish pairings
        self._execute_matching_phase(sim, preferences)
        
        # Step 4: Log decisions to telemetry
        self._log_decisions(sim, preferences)
    
    def _execute_search_phase(self, sim: "Simulation") -> dict:
        """
        Execute search phase for all agents.
        
        Returns:
            Dict of {agent_id: preference_list} for matching phase
        """
        preferences = {}
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            # Handle already-paired agents
            if agent.paired_with_id is not None:
                self._handle_paired_agent(agent, sim)
                preferences[agent.id] = []  # Paired agents don't search
                continue
            
            # Handle foraging-committed agents
            if agent.is_foraging_committed and agent.forage_target_pos:
                if self._validate_foraging_commitment(agent, sim):
                    # Commitment still valid, maintain target
                    agent.target_pos = agent.forage_target_pos
                    agent.target_agent_id = None
                    agent._decision_target_type = "forage"
                    preferences[agent.id] = []
                    continue
                else:
                    # Commitment broken, clear and proceed with normal search
                    agent.is_foraging_committed = False
                    agent.forage_target_pos = None
            
            # Build WorldView for this agent
            world = build_world_view_for_agent(agent, sim)
            
            # Call search protocol
            prefs = self.search_protocol.build_preferences(world)
            effects = self.search_protocol.select_target(world)
            
            # Apply search effects immediately
            self._apply_search_effects(agent, effects, sim)
            
            # Store preferences for matching phase
            preferences[agent.id] = prefs
        
        return preferences
    
    def _execute_matching_phase(self, sim: "Simulation", preferences: dict) -> None:
        """
        Execute matching phase using global protocol context.
        """
        # Build ProtocolContext with global state
        context = build_protocol_context(sim)
        
        # Call matching protocol
        pairing_effects = self.matching_protocol.find_matches(preferences, context)
        
        # Apply pairing effects
        self._apply_pairing_effects(pairing_effects, sim)
    
    def _handle_paired_agent(self, agent: "Agent", sim: "Simulation") -> None:
        """
        Handle agents who are already paired from previous tick.
        
        Validate pairing integrity and lock target to partner.
        """
        partner_id = agent.paired_with_id
        partner = sim.agent_by_id.get(partner_id)
        
        # Defensive integrity check
        if partner is None or partner.paired_with_id != agent.id:
            # Pairing corrupted - log and clear
            sim.telemetry.log_pairing_event(
                sim.tick, agent.id, partner_id, "unpair", "corruption_detected"
            )
            agent.paired_with_id = None
            return
        
        # Valid pairing: lock target to partner
        agent.target_pos = partner.pos
        agent.target_agent_id = partner_id
        agent._decision_target_type = "trade_paired"
        
        # Paired agents STILL build preference lists for telemetry/analysis
        # (This happens in search phase, but we skip it for paired agents)
    
    def _validate_foraging_commitment(self, agent: "Agent", sim: "Simulation") -> bool:
        """
        Check if agent's foraging commitment is still valid.
        
        Returns True if resource still exists, False if resource disappeared.
        """
        if not agent.forage_target_pos:
            return False
        
        cell = sim.grid.get_cell(agent.forage_target_pos[0], agent.forage_target_pos[1])
        resource = cell.resource
        
        if resource.type is None or resource.amount == 0:
            # Resource disappeared - break commitment and clear claim
            if agent.forage_target_pos in sim.resource_claims:
                del sim.resource_claims[agent.forage_target_pos]
            return False
        
        return True
    
    def _apply_search_effects(self, agent: "Agent", effects: list, sim: "Simulation") -> None:
        """
        Apply effects from search protocol to agent state.
        
        Handles: SetTarget, ClaimResource, ReleaseClaim
        """
        for effect in effects:
            if isinstance(effect, SetTarget):
                # Set target based on type
                if isinstance(effect.target, int):
                    # Trade target (agent ID)
                    partner = sim.agent_by_id.get(effect.target)
                    if partner:
                        agent.target_pos = partner.pos
                        agent.target_agent_id = effect.target
                        agent._decision_target_type = "trade"
                else:
                    # Position target (forage or home)
                    agent.target_pos = effect.target
                    agent.target_agent_id = None
                    # Determine type based on whether it's a resource
                    cell = sim.grid.get_cell(effect.target[0], effect.target[1])
                    if cell.resource is not None and cell.resource.type is not None:
                        agent._decision_target_type = "forage"
                        agent.is_foraging_committed = True
                        agent.forage_target_pos = effect.target
                    else:
                        agent._decision_target_type = "idle_home"
            
            elif isinstance(effect, ClaimResource):
                # Claim resource
                if sim.params.get("enable_resource_claiming", False):
                    sim.resource_claims[effect.pos] = agent.id
            
            elif isinstance(effect, ReleaseClaim):
                # Release resource claim
                if effect.pos in sim.resource_claims:
                    del sim.resource_claims[effect.pos]
    
    def _apply_pairing_effects(self, effects: list, sim: "Simulation") -> None:
        """
        Apply pairing effects from matching protocol to agent state.
        
        Handles: Pair, Unpair
        """
        for effect in effects:
            if isinstance(effect, Pair):
                agent_a = sim.agent_by_id[effect.agent_a]
                agent_b = sim.agent_by_id[effect.agent_b]
                
                # Establish pairing
                agent_a.paired_with_id = effect.agent_b
                agent_b.paired_with_id = effect.agent_a
                
                # Update targets to point at each other
                agent_a.target_pos = agent_b.pos
                agent_a.target_agent_id = effect.agent_b
                agent_b.target_pos = agent_a.pos
                agent_b.target_agent_id = effect.agent_a
                
                # Clear trade cooldowns
                agent_a.trade_cooldowns.pop(effect.agent_b, None)
                agent_b.trade_cooldowns.pop(effect.agent_a, None)
                
                # Calculate surpluses for logging
                surplus_a = self._calculate_surplus(agent_a, agent_b, sim)
                surplus_b = self._calculate_surplus(agent_b, agent_a, sim)
                
                # Log pairing event
                sim.telemetry.log_pairing_event(
                    sim.tick, effect.agent_a, effect.agent_b, 
                    "pair", effect.reason, surplus_a, surplus_b
                )
            
            elif isinstance(effect, Unpair):
                agent_a = sim.agent_by_id[effect.agent_a]
                agent_b = sim.agent_by_id[effect.agent_b]
                
                # Dissolve pairing
                agent_a.paired_with_id = None
                agent_b.paired_with_id = None
                
                # Clear targets
                agent_a.target_agent_id = None
                agent_b.target_agent_id = None
                
                # Log unpair event
                sim.telemetry.log_pairing_event(
                    sim.tick, effect.agent_a, effect.agent_b,
                    "unpair", effect.reason
                )
    
    def _calculate_surplus(self, agent: "Agent", partner: "Agent", sim: "Simulation") -> float:
        """Calculate surplus for an agent-partner pair (for telemetry)."""
        from .matching import compute_surplus, estimate_money_aware_surplus
        
        exchange_regime = sim.params.get("exchange_regime", "barter_only")
        if exchange_regime in ("money_only", "mixed", "mixed_liquidity_gated"):
            surplus, _ = estimate_money_aware_surplus(agent, partner, exchange_regime)
        else:
            surplus = compute_surplus(agent, partner)
        
        return surplus
    
    def _log_decisions(self, sim: "Simulation", preferences: dict) -> None:
        """Log decision data to telemetry for analysis."""
        # Only log if enabled in params
        if not sim.params.get("log_preferences", False):
            return
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            # Get preferences for this agent
            prefs = preferences.get(agent.id, [])
            
            # Filter to trade preferences (agent IDs only)
            trade_prefs = [p for p in prefs if isinstance(p[0], int)]
            
            # Log each preference
            for rank, (target_id, score, meta) in enumerate(trade_prefs):
                pair_type = meta.get("pair_type", "A<->B")
                surplus = meta.get("surplus", score)
                discounted_surplus = meta.get("discounted_surplus", score)
                distance = meta.get("distance", 0)
                
                sim.telemetry.log_preference(
                    sim.tick, agent.id, target_id, rank, 
                    surplus, discounted_surplus, distance, pair_type
                )
    
    def _clear_stale_claims(self, sim: "Simulation") -> None:
        """Remove resource claims from agents that reached target or changed target."""
        claims_to_remove = []
        
        for pos, agent_id in sim.resource_claims.items():
            agent = sim.agent_by_id.get(agent_id)
            
            # Keep claim if agent is foraging-committed to this resource
            if agent and agent.is_foraging_committed and agent.forage_target_pos == pos:
                continue  # Claim persists until commitment breaks
            
            # Remove claim if:
            # 1. Agent doesn't exist (shouldn't happen but defensive)
            # 2. Agent reached the resource (pos == target)
            # 3. Agent changed target (target_pos != claimed pos)
            if agent is None or agent.pos == pos or agent.target_pos != pos:
                claims_to_remove.append(pos)
        
        for pos in claims_to_remove:
            del sim.resource_claims[pos]
