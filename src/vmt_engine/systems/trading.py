from __future__ import annotations
from typing import TYPE_CHECKING
from .matching import trade_pair, find_best_trade, execute_trade_generic

if TYPE_CHECKING:
    from ..simulation import Simulation


class TradeSystem:
    """Phase 4: Agents trade with nearby partners."""

    def _get_allowed_pairs(self, regime: str) -> list[str]:
        """
        Get allowed exchange pair types based on exchange regime.
        
        Returns pair identifiers from buyer's perspective:
        - "A<->B": Barter (goods-for-goods)
        - "A<->M": Buy good A with money
        - "B<->M": Buy good B with money
        
        Args:
            regime: Exchange regime string ("barter_only", "money_only", "mixed", "mixed_liquidity_gated")
            
        Returns:
            List of allowed pair type strings. Order is deterministic for reproducibility.
            
        Raises:
            ValueError: If regime is not recognized
        """
        if regime == "barter_only":
            return ["A<->B"]
        elif regime == "money_only":
            return ["A<->M", "B<->M"]
        elif regime in ["mixed", "mixed_liquidity_gated"]:
            # All three exchange types allowed
            # Order matters for deterministic tie-breaking (implemented in Phase 3c)
            return ["A<->B", "A<->M", "B<->M"]
        else:
            raise ValueError(
                f"Unknown exchange_regime: '{regime}'. "
                f"Must be one of: 'barter_only', 'money_only', 'mixed', 'mixed_liquidity_gated'"
            )

    def execute(self, sim: "Simulation") -> None:
        # Check if using money-aware matching (Phase 2+)
        exchange_regime = sim.params.get("exchange_regime", "barter_only")
        use_generic_matching = exchange_regime in ("money_only", "mixed")
        
        # Process ONLY paired agents (pairing replaces spatial matching)
        processed_pairs = set()
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            if agent.paired_with_id is None:
                continue  # Skip unpaired agents
            
            partner_id = agent.paired_with_id
            
            # Skip if pair already processed
            pair_key = tuple(sorted([agent.id, partner_id]))
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)
            
            partner = sim.agent_by_id[partner_id]
            
            # Check distance
            distance = abs(agent.pos[0] - partner.pos[0]) + abs(agent.pos[1] - partner.pos[1])
            
            if distance <= sim.params["interaction_radius"]:
                # Within range: attempt trade
                if use_generic_matching:
                    # Phase 2+: Money-aware matching
                    self._trade_generic(agent, partner, sim)
                else:
                    # Barter-only matching
                    trade_pair(agent, partner, sim.params, sim.telemetry, sim.tick)
            # else: Too far apart, stay paired and keep moving
    
    def _trade_generic(self, agent_i, agent_j, sim):
        """Execute money-aware trade using generic matching primitives."""
        exchange_regime = sim.params.get("exchange_regime", "barter_only")
        
        # Find best trade across allowed pairs
        result = find_best_trade(
            agent_i, agent_j, exchange_regime, sim.params, 
            epsilon=sim.params.get("epsilon", 1e-9)
        )
        
        if result is None:
            # No mutually beneficial trade found - UNPAIR and set cooldown
            # This means trade opportunities are exhausted
            agent_i.paired_with_id = None
            agent_j.paired_with_id = None
            
            cooldown_until = sim.tick + sim.params.get('trade_cooldown_ticks', 10)
            agent_i.trade_cooldowns[agent_j.id] = cooldown_until
            agent_j.trade_cooldowns[agent_i.id] = cooldown_until
            
            # Log unpair event
            sim.telemetry.log_pairing_event(
                sim.tick, agent_i.id, agent_j.id, "unpair", "trade_failed"
            )
            return
        
        pair_name, trade = result
        dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade
        
        # Execute the trade
        execute_trade_generic(agent_i, agent_j, trade)
        
        # REMAIN PAIRED - agents will attempt another trade next tick
        # This is critical for O(N) performance
        
        # Log to telemetry
        self._log_generic_trade(agent_i, agent_j, pair_name, trade, sim)
    
    def _log_generic_trade(self, agent_i, agent_j, pair_name, trade, sim):
        """Log money-aware trade to telemetry."""
        dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade
        
        # Determine buyer/seller and trade direction based on pair
        if pair_name == "A<->B":
            # Barter: whoever gives A is selling A for B
            if dA_i < 0:  # agent_i sells A
                buyer_id, seller_id = agent_j.id, agent_i.id
                dA, dB = -dA_i, dB_i
                direction = "i_sells_A"
            else:  # agent_i buys A
                buyer_id, seller_id = agent_i.id, agent_j.id
                dA, dB = dA_i, -dB_i
                direction = "j_sells_A"
            dM = 0
            
        elif pair_name == "A<->M":
            # Monetary: whoever gives A is selling A for M
            if dA_i < 0:  # agent_i sells A for M
                seller_id, buyer_id = agent_i.id, agent_j.id
                dA, dM = -dA_i, dM_i
                direction = "i_sells_A_for_M"
            else:  # agent_i buys A with M
                seller_id, buyer_id = agent_j.id, agent_i.id
                dA, dM = dA_i, -dM_i
                direction = "j_sells_A_for_M"
            dB = 0
            
        else:  # B<->M
            # Monetary: whoever gives B is selling B for M
            if dB_i < 0:  # agent_i sells B for M
                seller_id, buyer_id = agent_i.id, agent_j.id
                dB, dM = -dB_i, dM_i
                direction = "i_sells_B_for_M"
            else:  # agent_i buys B with M
                seller_id, buyer_id = agent_j.id, agent_i.id
                dB, dM = dB_i, -dM_i
                direction = "j_sells_B_for_M"
            dA = 0
        
        # Compute price
        if dA > 0:
            if dB > 0:
                price = dB / dA  # Price of A in B
            else:  # dM > 0
                price = dM / dA  # Price of A in M
        elif dB > 0:
            price = dM / dB  # Price of B in M
        else:
            price = 0.0
        
        # Log trade (Phase 2+: include dM)
        sim.telemetry.log_trade(
            sim.tick,
            agent_i.pos[0], agent_i.pos[1],
            buyer_id, seller_id,
            dA, dB, price, direction, dM
        )
