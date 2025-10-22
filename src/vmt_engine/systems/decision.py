from __future__ import annotations
from typing import TYPE_CHECKING
from .matching import compute_surplus, estimate_money_aware_surplus
from .movement import choose_forage_target

if TYPE_CHECKING:
    from ..simulation import Simulation
    from ..core import Agent


class DecisionSystem:
    """Phase 2: Agents make decisions about targets with three-pass pairing algorithm."""

    def execute(self, sim: "Simulation") -> None:
        # Clear stale claims at start of tick
        if sim.params.get("enable_resource_claiming", False):
            self._clear_stale_claims(sim)
        
        # Three-pass decision algorithm
        self._pass1_target_selection(sim)
        self._pass2_mutual_consent(sim)
        self._pass3_best_available_fallback(sim)
        self._pass3b_handle_unpaired_trade_targets(sim)
        self._pass4_log_decisions(sim)
    
    def _pass1_target_selection(self, sim: "Simulation") -> None:
        """Pass 1: Each agent builds ranked preference list and selects primary target."""
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            # Clear stale decision context
            agent._preference_list = []
            agent._decision_target_type = None
            
            view = agent.perception_cache
            
            # Case 0: Agent is foraging-committed - check if target still valid
            if agent.is_foraging_committed and agent.forage_target_pos:
                # Check if committed resource still exists
                cell = sim.grid.get_cell(agent.forage_target_pos[0], agent.forage_target_pos[1])
                resource = cell.resource
                if resource.type is None or resource.amount == 0:
                    # Resource disappeared - break commitment and clear claim
                    agent.is_foraging_committed = False
                    if agent.forage_target_pos in sim.resource_claims:
                        del sim.resource_claims[agent.forage_target_pos]
                    agent.forage_target_pos = None
                else:
                    # Resource still valid - maintain commitment and target
                    agent.target_pos = agent.forage_target_pos
                    agent.target_agent_id = None
                    agent._decision_target_type = "forage"
                    continue  # Skip rest of decision logic
            
            # Case 1: Agent is already paired
            if agent.paired_with_id is not None:
                self._handle_paired_agent_pass1(agent, sim)
                continue
            
            # Case 2: Trade mode - evaluate trade opportunities
            if sim.current_mode in ("trade", "both"):
                self._evaluate_trade_preferences(agent, view, sim)
            
            # Case 3: Mixed mode - compare best trade vs best forage, choose higher
            if sim.current_mode == "both":
                self._evaluate_trade_vs_forage(agent, view, sim)
            
            # Case 4: Pure forage mode
            elif sim.current_mode == "forage":
                self._evaluate_forage_target(agent, view, sim)
    
    def _handle_paired_agent_pass1(self, agent: "Agent", sim: "Simulation") -> None:
        """Validate existing pairing and maintain target lock."""
        partner_id = agent.paired_with_id
        partner = sim.agent_by_id.get(partner_id)
        
        # Defensive integrity check
        if partner is None or partner.paired_with_id != agent.id:
            # Pairing corrupted - log and clear
            sim.telemetry.log_pairing_event(
                sim.tick, agent.id, partner_id, "unpair", "corruption_detected"
            )
            agent.paired_with_id = None
            # Fall through to unpaired logic
            return
        
        # Valid pairing: lock target to partner
        agent.target_pos = partner.pos
        agent.target_agent_id = partner_id
        agent._decision_target_type = "trade_paired"
        
        # Paired agents STILL build preference lists for telemetry/analysis
        view = agent.perception_cache
        self._evaluate_trade_preferences(agent, view, sim)
    
    def _evaluate_trade_preferences(self, agent: "Agent", view: dict, sim: "Simulation") -> None:
        """Build ranked preference list and select primary trade target."""
        neighbors = view.get("neighbors", [])
        beta = sim.params.get("beta", 0.95)
        
        # Build ranked list of all neighbors with positive surplus
        candidates = []
        for neighbor_id, neighbor_pos in neighbors:
            if neighbor_id not in sim.agent_by_id:
                continue
            
            neighbor = sim.agent_by_id[neighbor_id]
            
            # Skip neighbors who are foraging-committed (not available for trade)
            if neighbor.is_foraging_committed:
                continue
            
            # Check cooldown
            if neighbor_id in agent.trade_cooldowns:
                if sim.tick < agent.trade_cooldowns[neighbor_id]:
                    continue  # Still in cooldown
                else:
                    # Cooldown expired, remove
                    del agent.trade_cooldowns[neighbor_id]
            
            # Use regime-appropriate surplus calculation
            exchange_regime = sim.params.get("exchange_regime", "barter_only")
            if exchange_regime in ("money_only", "mixed", "mixed_liquidity_gated"):
                surplus, pair_type = estimate_money_aware_surplus(agent, neighbor, exchange_regime)
            else:
                surplus = compute_surplus(agent, neighbor)
                pair_type = "A<->B"  # Barter only
            
            if surplus > 0:
                # Compute distance for discounting
                distance = abs(agent.pos[0] - neighbor_pos[0]) + abs(agent.pos[1] - neighbor_pos[1])
                
                # Beta-discounted surplus: surplus × β^distance
                discounted_surplus = surplus * (beta ** distance)
                
                candidates.append((neighbor_id, surplus, discounted_surplus, distance, pair_type))
        
        # Sort by (-discounted_surplus, neighbor_id) for deterministic ranking
        candidates.sort(key=lambda x: (-x[2], x[0]))
        
        # Store ranked preference list
        agent._preference_list = candidates
        
        # Set primary target (top of list) - only if agent is unpaired
        if candidates and agent.paired_with_id is None:
            # Unpack candidate tuple (now 5 elements with pair_type)
            best_partner_id = candidates[0][0]
            best_surplus = candidates[0][1]
            best_discounted = candidates[0][2]
            best_dist = candidates[0][3]
            # pair_type = candidates[0][4]  # Available but not used here
            
            partner = sim.agent_by_id[best_partner_id]
            agent.target_pos = partner.pos
            agent.target_agent_id = best_partner_id
            agent._decision_target_type = "trade"
        elif not candidates and agent.paired_with_id is None:
            agent.target_pos = None
            agent.target_agent_id = None
            agent._decision_target_type = "idle"
        # Else: paired agents keep their existing target
    
    def _evaluate_forage_target(self, agent: "Agent", view: dict, sim: "Simulation") -> None:
        """Choose forage target from available resources."""
        resource_cells = view.get("resource_cells", [])
        
        # Filter claimed resources
        available = self._filter_claimed_resources(resource_cells, sim, agent.id)
        
        # Choose best resource
        target = choose_forage_target(
            agent, available, sim.params["beta"], sim.params["forage_rate"]
        )
        
        # Claim resource and set target
        if target is not None:
            self._claim_resource(sim, agent.id, target)
            agent.target_pos = target
            agent.target_agent_id = None
            agent._decision_target_type = "forage"
            
            # Set foraging commitment (persists until harvest)
            agent.is_foraging_committed = True
            agent.forage_target_pos = target
        else:
            # Idle fallback: return to home position
            if agent.home_pos is not None:
                agent.target_pos = agent.home_pos
                agent.target_agent_id = None
                agent._decision_target_type = "idle_home"
            else:
                agent.target_pos = None
                agent.target_agent_id = None
                agent._decision_target_type = "idle"
    
    def _evaluate_trade_vs_forage(self, agent: "Agent", view: dict, sim: "Simulation") -> None:
        """
        In 'both' mode, compare best trade opportunity vs best forage opportunity.
        Choose whichever has higher distance-discounted utility gain.
        
        Both are measured in comparable utility units with β^distance discount,
        so direct comparison is economically valid.
        """
        # Get best trade score from preference list (already computed in _evaluate_trade_preferences)
        best_trade_score = 0.0
        has_trade_target = False
        if agent._preference_list:
            # Preference list is sorted by discounted_surplus descending
            # Format: (partner_id, surplus, discounted_surplus, distance, pair_type)
            best_trade_score = agent._preference_list[0][2]  # discounted_surplus
            has_trade_target = agent.target_agent_id is not None
        
        # Calculate best forage score using existing helper
        resource_cells = view.get("resource_cells", [])
        available = self._filter_claimed_resources(resource_cells, sim, agent.id)
        
        best_forage_target = choose_forage_target(
            agent, available, sim.params["beta"], sim.params["forage_rate"]
        )
        
        # Calculate forage score for comparison
        best_forage_score = 0.0
        if best_forage_target and agent.utility:
            current_u = agent.utility.u(agent.inventory.A, agent.inventory.B)
            distance = abs(best_forage_target[0] - agent.pos[0]) + abs(best_forage_target[1] - agent.pos[1])
            
            # Determine resource type and calculate utility gain
            cell = sim.grid.get_cell(best_forage_target[0], best_forage_target[1])
            harvest_amount = min(cell.resource.amount, sim.params["forage_rate"])
            
            if cell.resource.type == "A":
                new_u = agent.utility.u(agent.inventory.A + harvest_amount, agent.inventory.B)
            else:  # "B"
                new_u = agent.utility.u(agent.inventory.A, agent.inventory.B + harvest_amount)
            
            delta_u = new_u - current_u
            best_forage_score = delta_u * (sim.params["beta"] ** distance)
        
        # Decision: Choose activity with higher score
        if has_trade_target and best_trade_score > best_forage_score:
            # Keep trade target (already set by _evaluate_trade_preferences)
            # agent.target_agent_id and agent.target_pos are already correct
            pass
        elif best_forage_target is not None:
            # Override trade target with forage target
            self._claim_resource(sim, agent.id, best_forage_target)
            agent.target_pos = best_forage_target
            agent.target_agent_id = None
            agent._decision_target_type = "forage"
            agent.is_foraging_committed = True
            agent.forage_target_pos = best_forage_target
        else:
            # No good options (both scores <= 0) - idle fallback to home
            if agent.home_pos is not None:
                agent.target_pos = agent.home_pos
                agent.target_agent_id = None
                agent._decision_target_type = "idle_home"
            else:
                agent.target_pos = None
                agent.target_agent_id = None
                agent._decision_target_type = "idle"
    
    def _pass2_mutual_consent(self, sim: "Simulation") -> None:
        """Pass 2: Establish pairings where both agents mutually prefer each other."""
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            # Skip already-paired agents
            if agent.paired_with_id is not None:
                continue
            
            # Skip agents without trade targets
            if agent.target_agent_id is None:
                continue
            
            partner_id = agent.target_agent_id
            partner = sim.agent_by_id[partner_id]
            
            # Check for mutual consent using CURRENT TICK data
            if (partner.target_agent_id == agent.id and 
                partner.paired_with_id is None):
                
                # MUTUAL CONSENT DETECTED
                # Process pairing only once (lower ID does the work)
                if agent.id < partner_id:
                    agent.paired_with_id = partner_id
                    partner.paired_with_id = agent.id
                    
                    # Clear mutual cooldowns
                    agent.trade_cooldowns.pop(partner_id, None)
                    partner.trade_cooldowns.pop(agent.id, None)
                    
                    # Get both agents' surpluses for logging
                    # Use regime-appropriate surplus calculation
                    exchange_regime = sim.params.get("exchange_regime", "barter_only")
                    if exchange_regime in ("money_only", "mixed", "mixed_liquidity_gated"):
                        surplus_i, _ = estimate_money_aware_surplus(agent, partner, exchange_regime)
                        surplus_j, _ = estimate_money_aware_surplus(partner, agent, exchange_regime)
                    else:
                        surplus_i = compute_surplus(agent, partner)
                        surplus_j = compute_surplus(partner, agent)
                    
                    # Log pairing event
                    sim.telemetry.log_pairing_event(
                        sim.tick, agent.id, partner_id, "pair", "mutual_consent",
                        surplus_i, surplus_j
                    )
    
    def _pass3_best_available_fallback(self, sim: "Simulation") -> None:
        """Pass 3: Surplus-based greedy matching for unpaired agents."""
        
        # Collect all potential pairings with their discounted surplus
        potential_pairings = []
        
        for agent in sim.agents:
            # Skip already-paired agents
            if agent.paired_with_id is not None:
                continue
            
            # Skip agents with no preferences
            if not agent._preference_list:
                continue
            
            # Add all preferences to potential pairing list
            for rank, pref_tuple in enumerate(agent._preference_list):
                # Handle both old 4-tuple and new 5-tuple formats
                if len(pref_tuple) == 5:
                    partner_id, surplus, discounted_surplus, distance, pair_type = pref_tuple
                else:
                    partner_id, surplus, discounted_surplus, distance = pref_tuple
                    pair_type = "A<->B"  # Default for backward compatibility
                
                partner = sim.agent_by_id[partner_id]
                
                # Only consider if partner is unpaired
                if partner.paired_with_id is None:
                    potential_pairings.append((
                        discounted_surplus,  # Primary sort key
                        agent.id,            # Secondary: lower ID tiebreak
                        partner_id,          # Tertiary: lower partner ID
                        rank,                # For logging
                        surplus              # Undiscounted surplus for logging
                    ))
        
        # Sort by (-discounted_surplus, agent_id, partner_id) for welfare-maximizing greedy
        potential_pairings.sort(key=lambda x: (-x[0], x[1], x[2]))
        
        # Greedily assign pairs
        for discounted_surplus, agent_id, partner_id, rank, surplus in potential_pairings:
            agent = sim.agent_by_id[agent_id]
            partner = sim.agent_by_id[partner_id]
            
            # Check if both are still available
            if agent.paired_with_id is None and partner.paired_with_id is None:
                # CLAIM PARTNER (fallback pairing)
                agent.paired_with_id = partner_id
                partner.paired_with_id = agent.id
                
                # Update targets for both agents
                agent.target_pos = partner.pos
                agent.target_agent_id = partner_id
                partner.target_pos = agent.pos
                partner.target_agent_id = agent.id
                
                # Clear mutual cooldowns
                agent.trade_cooldowns.pop(partner_id, None)
                partner.trade_cooldowns.pop(agent.id, None)
                
                # Get both agents' surpluses for logging
                surplus_i = surplus  # Already computed for this agent
                # Use regime-appropriate surplus calculation
                exchange_regime = sim.params.get("exchange_regime", "barter_only")
                if exchange_regime in ("money_only", "mixed", "mixed_liquidity_gated"):
                    surplus_j, _ = estimate_money_aware_surplus(partner, agent, exchange_regime)
                else:
                    surplus_j = compute_surplus(partner, agent)
                
                # Log pairing event with rank and surplus information
                sim.telemetry.log_pairing_event(
                    sim.tick, agent_id, partner_id, "pair", 
                    f"fallback_rank_{rank}_surplus_{discounted_surplus:.4f}", 
                    surplus_i, surplus_j
                )
    
    def _pass3b_handle_unpaired_trade_targets(self, sim: "Simulation") -> None:
        """Pass 3b: Handle unpaired agents who still have unfulfilled trade targets."""
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            # Skip paired agents (they're fine)
            if agent.paired_with_id is not None:
                continue
            
            # Skip agents without trade targets
            if agent.target_agent_id is None:
                continue
            
            # This agent has a trade target but didn't get paired
            # Clear the trade target and fall back to alternative activities
            agent.target_agent_id = None
            agent.target_pos = None
            
            # In "both" mode, fall back to foraging
            if sim.current_mode == "both":
                view = agent.perception_cache
                self._evaluate_forage_target(agent, view, sim)
            
            # In "trade" mode, idle fallback to home (no foraging allowed)
            else:
                if agent.home_pos is not None:
                    agent.target_pos = agent.home_pos
                    agent.target_agent_id = None
                    agent._decision_target_type = "idle_home"
                else:
                    agent.target_pos = None
                    agent.target_agent_id = None
                    agent._decision_target_type = "idle"
    
    def _pass4_log_decisions(self, sim: "Simulation") -> None:
        """Pass 4: Log all agent decisions with final pairing status."""
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            view = agent.perception_cache
            neighbors = view.get("neighbors", [])
            
            # Determine decision type
            if agent.paired_with_id is not None:
                decision_type = "trade_paired"
                partner_id = agent.paired_with_id
                
                # Get surplus from preference list if available
                surplus = None
                for pref_tuple in agent._preference_list:
                    # Handle both old 4-tuple and new 5-tuple formats
                    if len(pref_tuple) >= 4:
                        pid = pref_tuple[0]
                        s = pref_tuple[1]
                        if pid == partner_id:
                            surplus = s
                            break
            
            elif agent._decision_target_type == "trade":
                decision_type = "trade_unpaired"
                partner_id = agent.target_agent_id
                # Handle both old 4-tuple and new 5-tuple formats
                if agent._preference_list:
                    surplus = agent._preference_list[0][1]
                else:
                    surplus = None
            
            else:
                decision_type = agent._decision_target_type or "idle"
                partner_id = None
                surplus = None
            
            # Determine claimed resource position
            claimed_pos = None
            if decision_type == "forage" and agent.target_pos is not None:
                claimed_pos = agent.target_pos
            
            # Legacy alternatives string (for backward compatibility)
            alternatives_str = ""
            if agent._preference_list:
                alt_parts = []
                for pref_tuple in agent._preference_list[:5]:
                    # Handle both old 4-tuple and new 5-tuple formats
                    if len(pref_tuple) >= 4:
                        pid = pref_tuple[0]
                        s = pref_tuple[1]
                        alt_parts.append(f"{pid}:{s:.4f}")
                alternatives_str = "; ".join(alt_parts)
            
            # Log decision
            target_x = agent.target_pos[0] if agent.target_pos else None
            target_y = agent.target_pos[1] if agent.target_pos else None
            
            sim.telemetry.log_decision(
                sim.tick, agent.id, partner_id, surplus,
                decision_type, target_x, target_y, len(neighbors),
                alternatives_str, mode=sim.current_mode, 
                claimed_resource_pos=claimed_pos,
                is_paired=(agent.paired_with_id is not None),
                is_foraging_committed=agent.is_foraging_committed
            )
            
            # Log preferences to separate table (opt-in via log_preferences parameter)
            if agent._preference_list and sim.params.get("log_preferences", False):
                # Determine how many preferences to log
                log_full = sim.params.get("log_full_preferences", False)
                max_prefs = len(agent._preference_list) if log_full else min(3, len(agent._preference_list))
                
                for rank, pref_tuple in enumerate(agent._preference_list[:max_prefs]):
                    # Handle both old 4-tuple and new 5-tuple formats
                    if len(pref_tuple) == 5:
                        pid, surplus, discounted_surplus, distance, pair_type = pref_tuple
                    else:
                        pid, surplus, discounted_surplus, distance = pref_tuple
                        pair_type = "A<->B"  # Default for backward compatibility
                    
                    sim.telemetry.log_preference(
                        sim.tick, agent.id, pid, rank, surplus, 
                        discounted_surplus, distance, pair_type=pair_type
                    )
            
            # Clear temporary decision context
            agent._preference_list = []
            agent._decision_target_type = None
    
    def _clear_stale_claims(self, sim: "Simulation") -> None:
        """Remove claims from agents that reached target or changed target."""
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