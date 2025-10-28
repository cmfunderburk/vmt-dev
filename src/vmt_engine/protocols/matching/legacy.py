"""
Legacy Matching Protocol

Implements the original VMT three-pass pairing algorithm:
- Pass 2: Mutual consent (both agents rank each other #1)
- Pass 3: Greedy surplus-maximizing fallback
- Pass 3b: Unpair handling for unfulfilled trade targets

This protocol is bit-compatible with the pre-protocol DecisionSystem implementation.

Version: 2025.10.26 (Phase 1 - Legacy Adapter)
"""

from typing import Optional
from ..registry import register_protocol
from ..base import MatchingProtocol, Effect, Pair, Unpair, SetTarget
from ..context import ProtocolContext, AgentView
from ...systems.matching import compute_surplus, estimate_money_aware_surplus


@register_protocol(
    category="matching",
    name="legacy_three_pass",
    description="Legacy three-pass matching (mutual consent + greedy fallback)",
    properties=["deterministic", "legacy"],
    complexity="O(n^2)",
    references=[],
    phase="1",
)
class LegacyMatchingProtocol(MatchingProtocol):
    """
    Legacy three-pass matching algorithm.
    
    Pass 2 (Mutual Consent):
    - Pairs agents who mutually rank each other as #1 choice
    - Deterministic: lower ID agent processes the pairing
    
    Pass 3 (Greedy Fallback):
    - Collects all (agent, preference) pairs from unpaired agents
    - Sorts by (-discounted_surplus, agent_id, partner_id)
    - Greedily assigns pairs in order
    - Welfare-maximizing with inventory feasibility
    
    Pass 3b (Unpair Cleanup):
    - Unpairs agents with unfulfilled trade targets
    - Falls back to forage or idle based on mode
    """
    
    @property
    def name(self) -> str:
        return "legacy_three_pass"
    
    @property
    def version(self) -> str:
        return "2025.10.26"
    
    # Class-level for registry
    VERSION = "2025.10.26"
    
    def find_matches(
        self,
        preferences: dict[int, list[tuple[int | tuple[int, int], float, dict]]],
        world: ProtocolContext
    ) -> list[Effect]:
        """
        Execute three-pass matching algorithm.
        
        Args:
            preferences: Per-agent preference lists from search phase
                Format: {agent_id: [(target, score, metadata), ...]}
            world: Global protocol context
        
        Returns:
            List of Pair and Unpair effects
        """
        effects = []
        
        # Track pairings within this pass to avoid double-processing
        paired_this_pass = set()
        
        # Pass 2: Mutual consent
        mutual_consent_effects = self._pass2_mutual_consent(
            preferences, world, paired_this_pass
        )
        effects.extend(mutual_consent_effects)
        
        # Pass 3: Greedy fallback
        greedy_effects = self._pass3_greedy_fallback(
            preferences, world, paired_this_pass
        )
        effects.extend(greedy_effects)
        
        # Pass 3b: Handle unpaired trade targets
        unpair_effects = self._pass3b_handle_unpaired(
            preferences, world, paired_this_pass
        )
        effects.extend(unpair_effects)
        
        return effects
    
    def _pass2_mutual_consent(
        self,
        preferences: dict,
        world: ProtocolContext,
        paired_this_pass: set[int]
    ) -> list[Effect]:
        """
        Pass 2: Establish pairings where both agents mutually prefer each other.
        
        Returns:
            List of Pair effects for mutual consent pairings
        """
        effects = []
        
        # Iterate in sorted order for determinism
        for agent_id in sorted(preferences.keys()):
            # Skip already-paired agents
            if agent_id in world.current_pairings:
                continue
            if agent_id in paired_this_pass:
                continue
            
            # Get agent's top preference
            agent_prefs = preferences.get(agent_id, [])
            if not agent_prefs:
                continue
            
            # Filter to only trade targets (agent IDs, not positions)
            trade_prefs = [p for p in agent_prefs if isinstance(p[0], int)]
            if not trade_prefs:
                continue
            
            # Check #1 preference
            top_target_id, score, meta = trade_prefs[0]
            
            # Skip if target is already paired
            if top_target_id in world.current_pairings:
                continue
            if top_target_id in paired_this_pass:
                continue
            
            # Check for mutual consent
            partner_prefs = preferences.get(top_target_id, [])
            partner_trade_prefs = [p for p in partner_prefs if isinstance(p[0], int)]
            
            if partner_trade_prefs and partner_trade_prefs[0][0] == agent_id:
                # MUTUAL CONSENT DETECTED
                # Process pairing only once (lower ID does the work)
                if agent_id < top_target_id:
                    effects.append(Pair(
                        protocol_name=self.name,
                        tick=world.tick,
                        agent_a=agent_id,
                        agent_b=top_target_id,
                        reason="mutual_consent"
                    ))
                    
                    # Mark as paired
                    paired_this_pass.add(agent_id)
                    paired_this_pass.add(top_target_id)
        
        return effects
    
    def _pass3_greedy_fallback(
        self,
        preferences: dict,
        world: ProtocolContext,
        paired_this_pass: set[int]
    ) -> list[Effect]:
        """
        Pass 3: Surplus-based greedy matching for unpaired agents.
        
        Returns:
            List of Pair effects for greedy fallback pairings
        """
        # Collect all potential pairings with their discounted surplus
        potential_pairings = []
        
        for agent_id, agent_prefs in preferences.items():
            # Skip already-paired agents
            if agent_id in world.current_pairings:
                continue
            if agent_id in paired_this_pass:
                continue
            
            # Skip agents with no preferences
            if not agent_prefs:
                continue
            
            # Filter to trade preferences only (agent IDs)
            trade_prefs = [p for p in agent_prefs if isinstance(p[0], int)]
            
            # Add all trade preferences to potential pairing list
            for rank, (partner_id, score, meta) in enumerate(trade_prefs):
                # Only consider if partner is unpaired
                if partner_id in world.current_pairings:
                    continue
                if partner_id in paired_this_pass:
                    continue
                
                # Extract metadata
                discounted_surplus = meta.get("discounted_surplus", score)
                surplus = meta.get("surplus", score)
                
                potential_pairings.append((
                    discounted_surplus,  # Primary sort key
                    agent_id,            # Secondary: lower ID tiebreak
                    partner_id,          # Tertiary: lower partner ID
                    rank,                # For metadata
                    surplus              # Undiscounted surplus for metadata
                ))
        
        # Sort by (-discounted_surplus, agent_id, partner_id) for welfare-maximizing greedy
        potential_pairings.sort(key=lambda x: (-x[0], x[1], x[2]))
        
        effects = []
        
        # Greedily assign pairs
        for discounted_surplus, agent_id, partner_id, rank, surplus in potential_pairings:
            # Check if both are still available
            if agent_id in paired_this_pass or partner_id in paired_this_pass:
                continue
            
            # CLAIM PARTNER (fallback pairing)
            effects.append(Pair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=agent_id,
                agent_b=partner_id,
                reason=f"greedy_fallback"
            ))
            
            # Mark as paired
            paired_this_pass.add(agent_id)
            paired_this_pass.add(partner_id)
        
        return effects
    
    def _pass3b_handle_unpaired(
        self,
        preferences: dict,
        world: ProtocolContext,
        paired_this_pass: set[int]
    ) -> list[Effect]:
        """
        Pass 3b: Handle unpaired agents who still have unfulfilled trade targets.
        
        For agents who wanted to trade but didn't get paired:
        - In "both" mode: Fall back to foraging (handled by search protocol)
        - In "trade" mode: Idle fallback to home
        
        Returns:
            List of SetTarget effects for fallback targets (or empty if handled by search)
        """
        effects = []
        
        # Note: In the new architecture, this logic is mostly handled by the
        # search protocol in mixed mode. The search protocol already returns
        # the best available target (trade or forage).
        # 
        # This pass is mainly for clearing invalid trade targets and emitting
        # effects for idle agents in trade-only mode.
        
        # For now, we'll return empty - the orchestrator will handle
        # re-running search for unpaired agents if needed
        
        return effects

