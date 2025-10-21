from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
from .matching import trade_pair, find_best_trade, find_all_feasible_trades, execute_trade_generic

if TYPE_CHECKING:
    from ..simulation import Simulation
    from ..core import Agent


@dataclass
class TradeCandidate:
    """
    Represents a potential trade between two agents.
    
    Used for ranking and selecting trades in mixed exchange regimes where
    multiple trade types (barter, monetary) may be available simultaneously.
    
    Attributes:
        buyer_id: ID of the agent receiving the good
        seller_id: ID of the agent providing the good
        good_sold: Good being sold ("A" or "B")
        good_paid: Good used for payment ("A", "B", or "M")
        dX: Quantity of good being sold (positive integer)
        dY: Quantity of good used for payment (positive integer)
        buyer_surplus: Surplus gained by buyer (ΔU > 0)
        seller_surplus: Surplus gained by seller (ΔU > 0)
    """
    buyer_id: int
    seller_id: int
    good_sold: str
    good_paid: str
    dX: int
    dY: int
    buyer_surplus: float
    seller_surplus: float
    
    @property
    def total_surplus(self) -> float:
        """Total welfare gain from this trade."""
        return self.buyer_surplus + self.seller_surplus
    
    @property
    def pair_type(self) -> str:
        """Exchange pair type (e.g., 'A<->M', 'B<->A')."""
        return f"{self.good_sold}<->{self.good_paid}"


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
    
    def _rank_trade_candidates(self, candidates: list[TradeCandidate]) -> list[TradeCandidate]:
        """
        Rank trade candidates with deterministic three-level tie-breaking.
        
        Sorting priority (money-first policy for mixed regimes):
        1. Total surplus (descending) - maximize welfare
        2. Pair type priority (ascending) - money-first:
           - Priority 0: A↔M (good A for money)
           - Priority 1: B↔M (good B for money) 
           - Priority 2: A↔B (barter)
        3. Agent pair (min_id, max_id) (ascending) - deterministic tie-breaker
        
        This ensures that when multiple trade types offer equal surplus,
        monetary exchanges are preferred (liquidity advantage), and remaining
        ties are broken deterministically by agent ID for reproducibility.
        
        Args:
            candidates: List of TradeCandidate objects to rank
            
        Returns:
            Sorted list of candidates (highest priority first)
            
        Example:
            If two trades both offer surplus=10.0, and one is A↔M while the 
            other is A↔B, the A↔M trade will be ranked higher (executed first).
        """
        # Define pair type priority for money-first policy
        # Lower number = higher priority (executed first when surplus equal)
        PAIR_PRIORITY = {
            "A<->M": 0,  # Highest priority: monetary exchange for A
            "B<->M": 1,  # Second priority: monetary exchange for B
            "A<->B": 2,  # Lowest priority: barter
            "B<->A": 2,  # Barter (equivalent to A<->B)
            "M<->A": 0,  # Seller perspective of A↔M (treated same as A<->M)
            "M<->B": 1,  # Seller perspective of B↔M (treated same as B<->M)
        }
        
        def sort_key(candidate: TradeCandidate) -> tuple:
            """Generate sort key for a candidate."""
            # 1. Negate surplus for descending order (higher surplus first)
            surplus_key = -candidate.total_surplus
            
            # 2. Get pair type priority (lower is better)
            pair_type = candidate.pair_type
            pair_priority = PAIR_PRIORITY.get(pair_type, 99)  # Unknown pairs last
            
            # 3. Agent pair for deterministic tie-breaking (ascending)
            agent_pair = (
                min(candidate.buyer_id, candidate.seller_id),
                max(candidate.buyer_id, candidate.seller_id)
            )
            
            return (surplus_key, pair_priority, agent_pair)
        
        # Sort and return
        return sorted(candidates, key=sort_key)

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
    
    def _convert_to_trade_candidate(
        self, 
        agent_i: 'Agent', 
        agent_j: 'Agent', 
        pair_name: str, 
        trade: tuple
    ) -> TradeCandidate:
        """
        Convert a trade tuple from matching to a TradeCandidate object.
        
        Args:
            agent_i: First agent
            agent_j: Second agent
            pair_name: Pair type ("A<->B", "A<->M", "B<->M")
            trade: Tuple (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
            
        Returns:
            TradeCandidate with buyer/seller roles determined by trade direction
        """
        dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j = trade
        
        # Determine buyer/seller and good/payment based on pair type
        if pair_name == "A<->B":
            # Barter: whoever receives A is the buyer
            if dA_i > 0:  # agent_i receives A (buyer)
                return TradeCandidate(
                    buyer_id=agent_i.id, seller_id=agent_j.id,
                    good_sold="A", good_paid="B",
                    dX=dA_i, dY=-dB_i,
                    buyer_surplus=surplus_i, seller_surplus=surplus_j
                )
            else:  # agent_j receives A (buyer)
                return TradeCandidate(
                    buyer_id=agent_j.id, seller_id=agent_i.id,
                    good_sold="A", good_paid="B",
                    dX=-dA_i, dY=dB_i,
                    buyer_surplus=surplus_j, seller_surplus=surplus_i
                )
        
        elif pair_name == "A<->M":
            # Monetary: whoever receives A is the buyer
            if dA_i > 0:  # agent_i receives A (buyer)
                return TradeCandidate(
                    buyer_id=agent_i.id, seller_id=agent_j.id,
                    good_sold="A", good_paid="M",
                    dX=dA_i, dY=-dM_i,
                    buyer_surplus=surplus_i, seller_surplus=surplus_j
                )
            else:  # agent_j receives A (buyer)
                return TradeCandidate(
                    buyer_id=agent_j.id, seller_id=agent_i.id,
                    good_sold="A", good_paid="M",
                    dX=-dA_i, dY=dM_i,
                    buyer_surplus=surplus_j, seller_surplus=surplus_i
                )
        
        else:  # "B<->M"
            # Monetary: whoever receives B is the buyer
            if dB_i > 0:  # agent_i receives B (buyer)
                return TradeCandidate(
                    buyer_id=agent_i.id, seller_id=agent_j.id,
                    good_sold="B", good_paid="M",
                    dX=dB_i, dY=-dM_i,
                    buyer_surplus=surplus_i, seller_surplus=surplus_j
                )
            else:  # agent_j receives B (buyer)
                return TradeCandidate(
                    buyer_id=agent_j.id, seller_id=agent_i.id,
                    good_sold="B", good_paid="M",
                    dX=-dB_i, dY=dM_i,
                    buyer_surplus=surplus_j, seller_surplus=surplus_i
                )
    
    def _trade_generic(self, agent_i, agent_j, sim):
        """
        Execute money-aware trade using generic matching primitives.
        
        For mixed regimes (Phase 3+), evaluates ALL feasible trade types,
        ranks them using money-first tie-breaking, and executes the best trade.
        
        For barter_only and money_only regimes, uses Phase 2 logic (first feasible trade).
        """
        exchange_regime = sim.params.get("exchange_regime", "barter_only")
        epsilon = sim.params.get("epsilon", 1e-9)
        
        # Phase 3: Mixed regime logic with tie-breaking
        if exchange_regime in ["mixed", "mixed_liquidity_gated"]:
            # Find ALL feasible trades
            feasible_trades = find_all_feasible_trades(
                agent_i, agent_j, exchange_regime, sim.params, epsilon
            )
            
            if not feasible_trades:
                # No mutually beneficial trade found - UNPAIR and set cooldown
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
            
            # Convert to TradeCandidate objects
            candidates = [
                self._convert_to_trade_candidate(agent_i, agent_j, pair_name, trade)
                for pair_name, trade in feasible_trades
            ]
            
            # Rank using money-first tie-breaking
            ranked_candidates = self._rank_trade_candidates(candidates)
            
            # Execute the best trade
            best_candidate = ranked_candidates[0]
            
            # Find the original trade tuple for execution
            # (need to match it back to the pair_name, trade format)
            best_pair_name = best_candidate.pair_type
            best_trade = None
            for pair_name, trade in feasible_trades:
                if pair_name == best_pair_name:
                    best_trade = trade
                    break
            
            if best_trade is None:
                # Should never happen, but defensive programming
                return
            
            # Execute the trade
            execute_trade_generic(agent_i, agent_j, best_trade)
            
            # REMAIN PAIRED - agents will attempt another trade next tick
            
            # Log to telemetry
            self._log_generic_trade(agent_i, agent_j, best_pair_name, best_trade, sim)
        
        else:
            # Phase 2 logic: barter_only or money_only (first feasible trade)
            result = find_best_trade(
                agent_i, agent_j, exchange_regime, sim.params, epsilon
            )
            
            if result is None:
                # No mutually beneficial trade found - UNPAIR and set cooldown
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
            
            # Execute the trade
            execute_trade_generic(agent_i, agent_j, trade)
            
            # REMAIN PAIRED - agents will attempt another trade next tick
            
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
        
        # Log trade (Phase 2+: include dM and exchange_pair_type)
        sim.telemetry.log_trade(
            sim.tick,
            agent_i.pos[0], agent_i.pos[1],
            buyer_id, seller_id,
            dA, dB, price, direction, dM,
            exchange_pair_type=pair_name  # Phase 3: log pair type for analysis
        )
