"""
Trading System - Protocol Orchestrator

Coordinates bargaining protocols to execute trades between paired agents.

Phase 4 of the 7-phase simulation tick:
1. Process paired agents within interaction radius
2. Call bargaining protocol to negotiate
3. Apply trade or unpair effects
4. Log trades to telemetry

Version: 2025.10.26 (Phase 1 - Refactored for Protocol System)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
from ..protocols import (
    BargainingProtocol,
    Trade,
    Unpair,
    build_trade_world_view,
)
from ..core.market import MarketArea
from ..core.state import Position
from ..protocols.market import WalrasianAuctioneer
from .matching import execute_trade_generic

if TYPE_CHECKING:
    from ..simulation import Simulation
    from ..core import Agent


@dataclass
class TradeCandidate:
    """
    Represents a potential trade between two agents.
    
    DEPRECATED: This class is kept for backward compatibility with tests.
    The protocol system uses Effect types instead.
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
    """
    Phase 4: Orchestrate protocol-based trade negotiation.
    
    Responsibilities:
    - Find paired agents within interaction radius
    - Build WorldView for trade negotiation
    - Call bargaining protocol
    - Apply trade/unpair effects
    - Log trades to telemetry
    
    The actual bargaining logic is delegated to protocols.
    """
    
    def __init__(self):
        self.bargaining_protocol: Optional[BargainingProtocol] = None
        
        # Market state (persists across ticks)
        self.active_markets: dict[int, MarketArea] = {}
        self.next_market_id: int = 0
        
        # Market mechanism (created on first use)
        self.market_mechanism: Optional[WalrasianAuctioneer] = None
        
        # Statistics
        self.market_formations: int = 0
        self.market_dissolutions: int = 0
    
    def execute(self, sim: "Simulation") -> None:
        """
        Execute trade phase using bargaining protocol.
        
        Week 2: Markets are cleared before bilateral trades.
        """
        
        # ===== STEP 1: DETECT MARKETS =====
        markets = self._detect_market_areas(sim)
        
        # ===== STEP 2: ASSIGN AGENTS TO MARKETS (Week 2) =====
        market_assignments = self._assign_agents_to_markets(markets, sim)
        market_participants = set()
        for agent_ids in market_assignments.values():
            market_participants.update(agent_ids)
        
        # ===== STEP 3: UNPAIR MARKET PARTICIPANTS =====
        for agent_id in market_participants:
            agent = sim.agent_by_id[agent_id]
            if agent.paired_with_id is not None:
                partner_id = agent.paired_with_id
                partner = sim.agent_by_id[partner_id]
                
                # Unpair both agents
                agent.paired_with_id = None
                partner.paired_with_id = None
                
                # Log unpair event
                sim.telemetry.log_pairing_event(
                    sim.tick, agent_id, partner_id, "unpair", "entered_market"
                )
        
        # ===== STEP 4: PROCESS MARKET TRADES (Week 2) =====
        all_market_trades = []
        for market_id, agent_ids in sorted(market_assignments.items(), key=lambda x: x[0]):
            market = self.active_markets[market_id]
            market.participant_ids = agent_ids  # Update with actual assignments
            
            # Create mechanism if needed
            if self.market_mechanism is None:
                self.market_mechanism = self._create_mechanism(sim)
            
            # Clear market
            trades = self.market_mechanism.execute(market, sim)
            all_market_trades.extend(trades)
        
        # Apply market trade effects
        for trade in all_market_trades:
            self._apply_trade_effect(trade, sim)
        
        # ===== STEP 5: PROCESS BILATERAL TRADES (skip market participants) =====
        # Track processed pairs to avoid double-processing
        processed_pairs = set()
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            # Skip if agent is in a market
            if agent.id in market_participants:
                continue
            
            if agent.paired_with_id is None:
                continue  # Skip unpaired agents
            
            partner_id = agent.paired_with_id
            
            # Skip if partner is in a market
            if partner_id in market_participants:
                continue
            
            # Skip if pair already processed
            pair_key = tuple(sorted([agent.id, partner_id]))
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)
            
            partner = sim.agent_by_id[partner_id]
            
            # Check distance
            distance = abs(agent.pos[0] - partner.pos[0]) + abs(agent.pos[1] - partner.pos[1])
            
            if distance <= sim.params["interaction_radius"]:
                # Within range: attempt trade via bargaining protocol
                self._negotiate_trade(agent, partner, sim)
            # else: Too far apart, stay paired and keep moving
    
    def _negotiate_trade(self, agent_a: "Agent", agent_b: "Agent", sim: "Simulation") -> None:
        """
        Negotiate trade between two agents using bargaining protocol.
        
        Args:
            agent_a: First agent in pair
            agent_b: Second agent in pair
            sim: Current simulation state
        """
        # Build WorldView for trade negotiation
        world = build_trade_world_view(agent_a, agent_b, sim)
        
        # Call bargaining protocol
        effects = self.bargaining_protocol.negotiate((agent_a.id, agent_b.id), world)
        
        # Apply effects
        for effect in effects:
            if isinstance(effect, Trade):
                self._apply_trade_effect(effect, sim)
            elif isinstance(effect, Unpair):
                self._apply_unpair_effect(effect, sim)
    
    def _apply_trade_effect(self, effect: Trade, sim: "Simulation") -> None:
        """
        Apply trade effect: update inventories and log to telemetry.
        
        Note: Agents REMAIN PAIRED after successful trade (can trade again next tick).
        """
        buyer = sim.agent_by_id[effect.buyer_id]
        seller = sim.agent_by_id[effect.seller_id]
        
        # Determine trade tuple format for execute_trade_generic
        # Need to convert from Trade effect to (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
        
        # Determine which agent is buyer/seller relative to agent_i/agent_j
        if buyer.id < seller.id:
            agent_i, agent_j = buyer, seller
            is_i_buyer = True
        else:
            agent_i, agent_j = seller, buyer
            is_i_buyer = False
        
        # Build trade tuple based on pair type and direction
        if effect.pair_type == "A<->B":
            if is_i_buyer:
                # agent_i (buyer) receives A, pays B
                dA_i, dB_i, dM_i = effect.dA, -effect.dB, 0
                dA_j, dB_j, dM_j = -effect.dA, effect.dB, 0
            else:
                # agent_i (seller) pays A, receives B
                dA_i, dB_i, dM_i = -effect.dA, effect.dB, 0
                dA_j, dB_j, dM_j = effect.dA, -effect.dB, 0
        
        elif effect.pair_type == "A<->M":
            if is_i_buyer:
                # agent_i (buyer) receives A, pays M
                dA_i, dB_i, dM_i = effect.dA, 0, -effect.dM
                dA_j, dB_j, dM_j = -effect.dA, 0, effect.dM
            else:
                # agent_i (seller) pays A, receives M
                dA_i, dB_i, dM_i = -effect.dA, 0, effect.dM
                dA_j, dB_j, dM_j = effect.dA, 0, -effect.dM
        
        else:  # "B<->M"
            if is_i_buyer:
                # agent_i (buyer) receives B, pays M
                dA_i, dB_i, dM_i = 0, effect.dB, -effect.dM
                dA_j, dB_j, dM_j = 0, -effect.dB, effect.dM
            else:
                # agent_i (seller) pays B, receives M
                dA_i, dB_i, dM_i = 0, -effect.dB, effect.dM
                dA_j, dB_j, dM_j = 0, effect.dB, -effect.dM
        
        # Get surpluses from metadata
        surplus_buyer = effect.metadata.get("surplus_buyer", 0.0)
        surplus_seller = effect.metadata.get("surplus_seller", 0.0)
        
        if is_i_buyer:
            surplus_i, surplus_j = surplus_buyer, surplus_seller
        else:
            surplus_i, surplus_j = surplus_seller, surplus_buyer
        
        # Execute trade
        trade_tuple = (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
        execute_trade_generic(agent_i, agent_j, trade_tuple)
        
        if hasattr(sim, "_trades_made"):
            sim._trades_made[effect.buyer_id] = sim._trades_made.get(effect.buyer_id, 0) + 1
            sim._trades_made[effect.seller_id] = sim._trades_made.get(effect.seller_id, 0) + 1
        
        # Log to telemetry
        self._log_trade(effect, sim)
    
    def _apply_unpair_effect(self, effect: Unpair, sim: "Simulation") -> None:
        """
        Apply unpair effect: dissolve pairing and set trade cooldown.
        """
        agent_a = sim.agent_by_id[effect.agent_a]
        agent_b = sim.agent_by_id[effect.agent_b]
        
        # Dissolve pairing
        agent_a.paired_with_id = None
        agent_b.paired_with_id = None
        
        # Set trade cooldown
        cooldown_until = sim.tick + sim.params.get('trade_cooldown_ticks', 10)
        agent_a.trade_cooldowns[effect.agent_b] = cooldown_until
        agent_b.trade_cooldowns[effect.agent_a] = cooldown_until
        
        # Log unpair event
        sim.telemetry.log_pairing_event(
            sim.tick, effect.agent_a, effect.agent_b, "unpair", effect.reason
        )
    
    def _log_trade(self, effect: Trade, sim: "Simulation") -> None:
        """Log trade to telemetry."""
        buyer = sim.agent_by_id[effect.buyer_id]
        seller = sim.agent_by_id[effect.seller_id]
        
        # Determine direction string
        if effect.pair_type == "A<->B":
            direction = "A_traded_for_B"
            dA, dB, dM = effect.dA, effect.dB, 0
        elif effect.pair_type == "A<->M":
            direction = "A_traded_for_M"
            dA, dB, dM = effect.dA, 0, effect.dM
        elif effect.pair_type == "B<->M":
            direction = "B_traded_for_M"
            dA, dB, dM = 0, effect.dB, effect.dM
        else:
            direction = "unknown"
            dA, dB, dM = effect.dA, effect.dB, effect.dM
        
        # Log trade event (using original API signature)
        # Note: log_trade() will be extended to accept market_id in Week 3
        sim.telemetry.log_trade(
            tick=sim.tick,
            x=buyer.pos[0],
            y=buyer.pos[1],
            buyer_id=effect.buyer_id,
            seller_id=effect.seller_id,
            dA=dA,
            dB=dB,
            price=effect.price,
            direction=direction,
            dM=dM,
            exchange_pair_type=effect.pair_type
        )
    
    # =============================================================================
    # Market Detection Methods (Week 1)
    # =============================================================================
    
    def _detect_market_areas(self, sim: 'Simulation') -> list[MarketArea]:
        """
        Detect dense agent clusters that qualify as markets.
        
        Algorithm:
        1. Sort agents by ID (determinism)
        2. For each agent not yet assigned:
           a. Count agents within interaction_radius
           b. If count >= formation_threshold:
              - Check if existing market nearby (reuse ID)
              - Otherwise create new market
           c. Mark all participants as processed
        3. Update existing markets' participant lists
        4. Check dissolution criteria
        
        Returns:
            List of active MarketArea objects
        """
        formation_threshold = sim.params.get('market_formation_threshold', 5)
        dissolution_threshold = sim.params.get('market_dissolution_threshold', 3)
        dissolution_patience = sim.params.get('market_dissolution_patience', 5)
        interaction_radius = sim.params['interaction_radius']
        
        markets_active_this_tick: set[int] = set()
        assigned_agents: set[int] = set()
        
        # Scan for clusters
        for agent in sorted(sim.agents, key=lambda a: a.id):
            if agent.id in assigned_agents:
                continue
            
            # Find nearby agents
            nearby = self._find_agents_within_radius(
                agent.pos,
                interaction_radius,
                sim
            )
            
            if len(nearby) >= formation_threshold:
                # Compute cluster center
                center = self._compute_cluster_center(nearby)
                
                # Find or create market
                market = self._find_or_create_market(center, sim)
                market.participant_ids = [a.id for a in nearby]
                market.last_active_tick = sim.tick
                market.ticks_below_threshold = 0
                
                # Log formation if new market
                if market.formation_tick == sim.tick:
                    print(f"Market {market.id} formed at {center} on tick {sim.tick} "
                          f"with {len(market.participant_ids)} participants")
                
                markets_active_this_tick.add(market.id)
                assigned_agents.update(market.participant_ids)
        
        # Update existing markets not seen this tick
        self._update_inactive_markets(markets_active_this_tick, sim, 
                                       dissolution_threshold, dissolution_patience)
        
        return list(self.active_markets.values())
    
    def _find_agents_within_radius(self, center: Position, radius: int,
                                   sim: 'Simulation') -> list['Agent']:
        """Return all agents within Manhattan distance <= radius"""
        nearby = []
        for agent in sim.agents:
            dist = abs(agent.pos[0] - center[0]) + abs(agent.pos[1] - center[1])
            if dist <= radius:
                nearby.append(agent)
        return sorted(nearby, key=lambda a: a.id)  # Deterministic ordering
    
    def _compute_cluster_center(self, agents: list['Agent']) -> Position:
        """Compute geometric center of cluster"""
        if not agents:
            return (0, 0)
        
        avg_x = sum(a.pos[0] for a in agents) / len(agents)
        avg_y = sum(a.pos[1] for a in agents) / len(agents)
        
        return (round(avg_x), round(avg_y))
    
    def _find_or_create_market(self, center: Position, 
                               sim: 'Simulation') -> MarketArea:
        """
        Check if market exists near this location (reuse ID and prices).
        Otherwise create new market.
        """
        # Check existing markets
        for market in self.active_markets.values():
            dist = abs(market.center[0] - center[0]) + abs(market.center[1] - center[1])
            if dist <= 2:  # Within 2 cells = same market
                market.center = center  # Update center (may drift slightly)
                return market
        
        # Create new market
        market_id = self.next_market_id
        self.next_market_id += 1
        
        market = MarketArea(
            id=market_id,
            center=center,
            radius=sim.params['interaction_radius'],
            formation_tick=sim.tick
        )
        
        self.active_markets[market_id] = market
        self.market_formations += 1
        
        # Log formation event (telemetry will be added in Week 3)
        # Note: participant_ids will be set by caller after market is returned
        
        return market
    
    def _update_inactive_markets(self, active_market_ids: set[int],
                                 sim: 'Simulation',
                                 dissolution_threshold: int,
                                 dissolution_patience: int) -> None:
        """Update markets not found this tick; dissolve if necessary"""
        to_dissolve = []
        
        for market_id, market in self.active_markets.items():
            if market_id not in active_market_ids:
                # Market didn't form this tick
                market.participant_ids = []
                market.ticks_below_threshold += 1
                
                if market.ticks_below_threshold >= dissolution_patience:
                    to_dissolve.append(market_id)
        
        # Dissolve markets
        for market_id in to_dissolve:
            market = self.active_markets[market_id]
            
            print(f"Market {market_id} dissolved at tick {sim.tick} "
                  f"(existed for {market.age} ticks)")
            
            del self.active_markets[market_id]
            self.market_dissolutions += 1
    
    # =============================================================================
    # Market Assignment and Clearing (Week 2)
    # =============================================================================
    
    def _assign_agents_to_markets(self, markets: list[MarketArea],
                                   sim: 'Simulation') -> dict[int, list[int]]:
        """
        Assign agents to markets with exclusive assignment.
        
        Priority (for agents eligible for multiple markets):
        1. Largest market (most participants)
        2. Closest market (minimum Manhattan distance)
        3. Lowest market ID (deterministic tie-breaker)
        
        Args:
            markets: List of active markets
            sim: Simulation state
            
        Returns:
            dict mapping market_id to list of assigned agent_ids
        """
        if not markets:
            return {}
        
        # Build eligibility map: agent_id -> list of (market, distance) tuples
        eligibility: dict[int, list[tuple[MarketArea, int]]] = {}
        
        for agent in sorted(sim.agents, key=lambda a: a.id):
            for market in markets:
                # Check if agent is within market radius
                dist = abs(agent.pos[0] - market.center[0]) + abs(agent.pos[1] - market.center[1])
                if dist <= market.radius:
                    if agent.id not in eligibility:
                        eligibility[agent.id] = []
                    eligibility[agent.id].append((market, dist))
        
        # Assign agents (greedy: process agents in ID order)
        assignments: dict[int, list[int]] = {}
        assigned_agents: set[int] = set()
        
        # Sort agents by ID for deterministic processing
        eligible_agents = sorted(eligibility.keys())
        
        for agent_id in eligible_agents:
            if agent_id in assigned_agents:
                continue  # Already assigned
            
            options = eligibility[agent_id]
            
            # Sort by priority: size (desc), distance (asc), market_id (asc)
            options.sort(key=lambda x: (
                -len(x[0].participant_ids),  # Larger markets first
                x[1],  # Closer markets first
                x[0].id  # Lower ID first (tie-breaker)
            ))
            
            # Assign to highest priority market
            market = options[0][0]
            market_id = market.id
            
            if market_id not in assignments:
                assignments[market_id] = []
            
            assignments[market_id].append(agent_id)
            assigned_agents.add(agent_id)
        
        # Sort agent lists for determinism
        for market_id in assignments:
            assignments[market_id].sort()
        
        return assignments
    
    def _create_mechanism(self, sim: 'Simulation') -> WalrasianAuctioneer:
        """
        Create market mechanism from scenario parameters.
        
        Args:
            sim: Simulation state
            
        Returns:
            Market mechanism instance
        """
        mechanism_type = sim.params.get('market_mechanism', 'walrasian')
        
        if mechanism_type == 'walrasian':
            adjustment_speed = sim.params.get('walrasian_adjustment_speed', 0.1)
            tolerance = sim.params.get('walrasian_tolerance', 0.01)
            max_iterations = sim.params.get('walrasian_max_iterations', 100)
            
            return WalrasianAuctioneer(
                adjustment_speed=adjustment_speed,
                tolerance=tolerance,
                max_iterations=max_iterations
            )
        elif mechanism_type == 'posted_price':
            raise NotImplementedError("Posted price mechanism deferred to future phase")
        elif mechanism_type == 'cda':
            raise NotImplementedError("Continuous double auction deferred to future phase")
        else:
            raise ValueError(f"Unknown market mechanism: {mechanism_type}")
