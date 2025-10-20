from __future__ import annotations
from typing import TYPE_CHECKING
from .matching import trade_pair, find_best_trade, execute_trade_generic

if TYPE_CHECKING:
    from ..simulation import Simulation


class TradeSystem:
    """Phase 4: Agents trade with nearby partners."""

    def execute(self, sim: "Simulation") -> None:
        # Check if using money-aware matching (Phase 2+)
        exchange_regime = sim.params.get("exchange_regime", "barter_only")
        use_generic_matching = exchange_regime in ("money_only", "mixed")
        
        # Use spatial index to find agent pairs within interaction_radius efficiently
        # O(N) instead of O(N²) by only checking agents in nearby spatial buckets
        pairs = sim.spatial_index.query_pairs_within_radius(
            sim.params["interaction_radius"]
        )

        # Sort pairs by (min_id, max_id) for deterministic processing
        pairs.sort()

        # Execute trades
        for id_i, id_j in pairs:
            agent_i = sim.agent_by_id[id_i]
            agent_j = sim.agent_by_id[id_j]

            if use_generic_matching:
                # Phase 2+: Money-aware matching
                self._trade_generic(agent_i, agent_j, sim)
            else:
                # Legacy: Barter-only matching
                trade_pair(agent_i, agent_j, sim.params, sim.telemetry, sim.tick)
    
    def _trade_generic(self, agent_i, agent_j, sim):
        """Execute money-aware trade using generic matching primitives."""
        exchange_regime = sim.params.get("exchange_regime", "barter_only")
        
        # Find best trade across allowed pairs
        result = find_best_trade(
            agent_i, agent_j, exchange_regime, sim.params, 
            epsilon=sim.params.get("epsilon", 1e-9)
        )
        
        if result is None:
            # No mutually beneficial trade found - set cooldown
            cooldown_until = sim.tick + sim.params.get('trade_cooldown_ticks', 10)
            agent_i.trade_cooldowns[agent_j.id] = cooldown_until
            agent_j.trade_cooldowns[agent_i.id] = cooldown_until
            return
        
        pair_name, trade = result
        dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade
        
        # Execute the trade
        execute_trade_generic(agent_i, agent_j, trade)
        
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
