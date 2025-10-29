"""
Walrasian market clearing via tatonnement.

Implements price adjustment mechanism to find market-clearing prices.
Agents submit demand/supply based on marginal utilities compared to prices.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from ..base import Trade, MarketClear

if TYPE_CHECKING:
    from ...simulation import Simulation
    from ...core.market import MarketArea
    from ...core import Agent


class WalrasianAuctioneer:
    """
    Walrasian tatonnement auctioneer for market clearing.
    
    Process:
    1. For each commodity (A, B), find clearing price via tatonnement
    2. Compute excess demand = sum(demands) - sum(supplies)
    3. Adjust price: p_new = p_old + α * excess_demand
    4. Repeat until |excess_demand| < tolerance or max iterations
    5. Execute trades at clearing price
    """
    
    def __init__(self, adjustment_speed: float = 0.1, tolerance: float = 0.01,
                 max_iterations: int = 100):
        """
        Args:
            adjustment_speed: α in price adjustment (default: 0.1)
            tolerance: Convergence threshold for excess demand (default: 0.01)
            max_iterations: Maximum tatonnement iterations (default: 100)
        """
        self.adjustment_speed = adjustment_speed
        self.tolerance = tolerance
        self.max_iterations = max_iterations
    
    def execute(self, market: MarketArea, sim: Simulation) -> list[Trade]:
        """
        Clear market for all commodities.
        
        Args:
            market: MarketArea to clear
            sim: Simulation state
            
        Returns:
            List of Trade effects for all executed trades
        """
        if not market.participant_ids:
            return []  # No participants
        
        trades = []
        
        # Track committed inventory across all commodity clearings
        committed_B = {agent_id: 0 for agent_id in market.participant_ids}  # B spent buying A
        committed_A = {agent_id: 0 for agent_id in market.participant_ids}  # A spent buying B
        
        # Clear each commodity separately, accounting for commitments
        for commodity in ['A', 'B']:
            commodity_trades, clear_info = self._find_clearing_price(
                market, commodity, sim, committed_A, committed_B
            )
            trades.extend(commodity_trades)
            
            # Update commitments IMMEDIATELY after each trade is created
            # This prevents double-spending across commodity clearings
            for trade in commodity_trades:
                if commodity == 'A':
                    # Buyer paid B to get A
                    committed_B[trade.buyer_id] += abs(trade.dB)
                else:  # commodity == 'B'
                    # Buyer paid A to get B
                    committed_A[trade.buyer_id] += abs(trade.dA)
            
            # Log market clearing to telemetry (Week 3)
            if clear_info['converged']:
                market.total_volume_traded += clear_info['quantity']
                market.total_trades_executed += len(commodity_trades)
                
                sim.telemetry.log_market_clear(
                    tick=sim.tick,
                    market_id=market.id,
                    commodity=commodity,
                    clearing_price=clear_info['price'],
                    quantity_traded=clear_info['quantity'],
                    num_participants=len(market.participant_ids),
                    converged=clear_info['converged']
                )
        
        return trades
    
    def _find_clearing_price(self, market: MarketArea, commodity: str,
                             sim: Simulation, 
                             committed_A: dict[int, int],
                             committed_B: dict[int, int]) -> tuple[list[Trade], dict]:
        """
        Find market-clearing price via tatonnement.
        
        Args:
            market: MarketArea to clear
            commodity: 'A' or 'B'
            sim: Simulation state
            
        Returns:
            Tuple of (list of Trade effects, clearing info dict)
        """
        # Warm start from previous price if available
        if commodity in market.current_prices:
            price = market.current_prices[commodity]
        else:
            # Initialize price at average MRS of participants
            price = self._initial_price_estimate(market, commodity, sim)
        
        converged = False
        iterations = 0
        
        for _ in range(self.max_iterations):
            # Compute excess demand
            excess_demand = self._compute_excess_demand(
                market, commodity, price, sim
            )
            
            # Check convergence
            if abs(excess_demand) < self.tolerance:
                converged = True
                break
            
            # Adjust price: p_new = p_old + α * excess_demand
            price = price + self.adjustment_speed * excess_demand
            
            # Price cannot be negative
            price = max(0.0, price)
            
            iterations += 1
        
        # Execute trades at clearing price
        trades = self._execute_at_price(market, commodity, price, sim, committed_A, committed_B)
        
        # Update market price
        market.current_prices[commodity] = price
        
        # Store in historical prices
        if sim.tick not in market.historical_prices:
            market.historical_prices[sim.tick] = {}
        market.historical_prices[sim.tick][commodity] = price
        
        clear_info = {
            'price': price,
            'quantity': abs(excess_demand) if converged else 0.0,
            'excess_demand': excess_demand,
            'iterations': iterations,
            'converged': converged
        }
        
        return trades, clear_info
    
    def _initial_price_estimate(self, market: MarketArea, commodity: str,
                                sim: Simulation) -> float:
        """Estimate initial price from participant MRS values."""
        mrs_values = []
        
        for agent_id in market.participant_ids:
            agent = sim.agent_by_id[agent_id]
            if not agent.utility:
                continue
            
            A = agent.inventory.A
            B = agent.inventory.B
            
            if commodity == 'A':
                # Price of A in terms of B: MRS_A_in_B
                if B > 0:
                    mu_A = agent.utility.mu_A(A, B)
                    mu_B = agent.utility.mu_B(A, B)
                    if mu_B > 0:
                        mrs_values.append(mu_A / mu_B)
            else:  # commodity == 'B'
                # Price of B in terms of A: MRS_B_in_A = 1 / MRS_A_in_B
                if A > 0:
                    mu_A = agent.utility.mu_A(A, B)
                    mu_B = agent.utility.mu_B(A, B)
                    if mu_A > 0:
                        mrs_values.append(mu_B / mu_A)
        
        if mrs_values:
            return sum(mrs_values) / len(mrs_values)
        else:
            return 1.0  # Default fallback
    
    def _compute_excess_demand(self, market: MarketArea, commodity: str,
                               price: float, sim: Simulation) -> float:
        """
        Compute excess demand = total_demand - total_supply.
        
        Positive excess_demand → price too low → increase price
        Negative excess_demand → price too high → decrease price
        """
        total_demand = 0.0
        total_supply = 0.0
        
        for agent_id in market.participant_ids:
            agent = sim.agent_by_id[agent_id]
            if not agent.utility:
                continue
            
            A = agent.inventory.A
            B = agent.inventory.B
            
            if commodity == 'A':
                # Agent wants to buy A if MU_A > price * MU_B
                # Agent wants to sell A if MU_A < price * MU_B
                mu_A = agent.utility.mu_A(A, B)
                mu_B = agent.utility.mu_B(A, B)
                
                if mu_B > 0:
                    reservation_price = mu_A / mu_B
                    if reservation_price > price:
                        # Willing to buy A: can afford B/price units
                        # Demand limited by budget
                        max_affordable = int(B / price) if price > 0 else 0
                        demand = min(max_affordable, max(0, int((reservation_price - price) * 5)))
                        if demand > 0:
                            total_demand += demand
                    elif reservation_price < price and A > 0:
                        # Willing to sell A: supply up to available A
                        supply = min(A, max(1, int((price - reservation_price) * 5)))
                        if supply > 0:
                            total_supply += supply
            else:  # commodity == 'B'
                # Price of B in terms of A
                mu_A = agent.utility.mu_A(A, B)
                mu_B = agent.utility.mu_B(A, B)
                
                if mu_A > 0:
                    reservation_price = mu_B / mu_A
                    if reservation_price > price:
                        # Willing to buy B: can afford A/price units
                        max_affordable = int(A / price) if price > 0 else 0
                        demand = min(max_affordable, max(0, int((reservation_price - price) * 5)))
                        if demand > 0:
                            total_demand += demand
                    elif reservation_price < price and B > 0:
                        # Willing to sell B: supply up to available B
                        supply = min(B, max(1, int((price - reservation_price) * 5)))
                        if supply > 0:
                            total_supply += supply
        
        return total_demand - total_supply
    
    def _execute_at_price(self, market: MarketArea, commodity: str,
                         price: float, sim: Simulation,
                         committed_A: dict[int, int],
                         committed_B: dict[int, int]) -> list[Trade]:
        """
        Match buyers and sellers at clearing price.
        
        Simplified matching: proportional allocation based on demand/supply.
        """
        buyers = []
        sellers = []
        
        # Classify participants
        for agent_id in market.participant_ids:
            agent = sim.agent_by_id[agent_id]
            if not agent.utility:
                continue
            
            A = agent.inventory.A
            B = agent.inventory.B
            
            if commodity == 'A':
                mu_A = agent.utility.mu_A(A, B)
                mu_B = agent.utility.mu_B(A, B)
                
                if mu_B > 0:
                    reservation_price = mu_A / mu_B
                    if reservation_price > price:
                        # Buyer
                        quantity = max(1, int((reservation_price - price) * 10))
                        quantity = min(quantity, int(B / price) if price > 0 else 0)
                        if quantity > 0:
                            buyers.append((agent_id, quantity))
                    elif reservation_price < price and A > 0:
                        # Seller
                        quantity = min(A, max(1, int((price - reservation_price) * 10)))
                        if quantity > 0:
                            sellers.append((agent_id, quantity))
            else:  # commodity == 'B'
                mu_A = agent.utility.mu_A(A, B)
                mu_B = agent.utility.mu_B(A, B)
                
                if mu_A > 0:
                    reservation_price = mu_B / mu_A
                    if reservation_price > price:
                        # Buyer
                        quantity = max(1, int((reservation_price - price) * 10))
                        quantity = min(quantity, int(A / price) if price > 0 else 0)
                        if quantity > 0:
                            buyers.append((agent_id, quantity))
                    elif reservation_price < price and B > 0:
                        # Seller
                        quantity = min(B, max(1, int((price - reservation_price) * 10)))
                        if quantity > 0:
                            sellers.append((agent_id, quantity))
        
        # Match buyers and sellers
        trades = []
        
        if not buyers or not sellers:
            return trades  # No overlap
        
        # Simple matching: pair buyers and sellers in order
        # Track remaining capacities
        buyer_remaining = {agent_id: qty for agent_id, qty in buyers}
        seller_remaining = {agent_id: qty for agent_id, qty in sellers}
        
        # Track running commitments as we create trades to prevent double-spending
        running_committed_A = committed_A.copy()
        running_committed_B = committed_B.copy()
        
        # Match greedily
        for buyer_id, buyer_max_qty in buyers:
            if buyer_max_qty <= 0 or buyer_remaining[buyer_id] <= 0:
                continue
            
            # Find available seller
            for seller_id, seller_max_qty in sellers:
                if seller_max_qty <= 0:
                    continue
                
                if seller_id not in seller_remaining or seller_remaining[seller_id] <= 0:
                    continue
                
                # Get current agent inventories for validation
                buyer_agent = sim.agent_by_id[buyer_id]
                seller_agent = sim.agent_by_id[seller_id]
                
                # Determine trade quantity
                available_from_seller = seller_remaining[seller_id]
                
                if commodity == 'A':
                    # Buyer needs A, pays B
                    # Calculate max buyer can afford based on actual inventory minus ALL commitments (including running ones)
                    available_B = buyer_agent.inventory.B - running_committed_B[buyer_id]
                    max_buyer_can_afford = int(available_B / price) if price > 0 and available_B > 0 else 0
                    max_buyer_can_afford = min(max_buyer_can_afford, buyer_remaining[buyer_id])
                    trade_qty = min(available_from_seller, max_buyer_can_afford, buyer_max_qty)
                    
                    # DEBUG: Add logging for problematic trades
                    if buyer_id == 2 and trade_qty > 0:
                        print(f"DEBUG A-trade: Agent {buyer_id} has B={buyer_agent.inventory.B}, committed_B={running_committed_B[buyer_id]}, available_B={available_B}, price={price:.3f}, trade_qty={trade_qty}, payment_B={round(trade_qty * price)}")
                    
                    # Recalculate payment based on actual quantity
                    payment_B = round(trade_qty * price)  # Use proper rounding instead of int()
                    # Ensure payment doesn't exceed buyer's available budget
                    if payment_B > available_B:
                        # Reduce quantity to fit budget
                        trade_qty = int(available_B / price) if price > 0 and available_B > 0 else 0
                        payment_B = round(trade_qty * price)
                    
                    # Verify feasibility - all constraints must be satisfied
                    # CRITICAL: Final check that buyer can actually afford this trade
                    if (trade_qty > 0 and 
                        payment_B <= available_B and  # This is the correct check - available_B already accounts for commitments
                        trade_qty <= seller_agent.inventory.A and
                        trade_qty <= buyer_remaining[buyer_id] and
                        trade_qty <= seller_remaining[seller_id]):
                        trade = Trade(
                            buyer_id=buyer_id,
                            seller_id=seller_id,
                            pair_type="A<->B",
                            dA=trade_qty,
                            dB=-payment_B,
                            dM=0,
                            price=price,
                            market_id=market.id,
                            protocol_name="walrasian",
                            tick=sim.tick,
                            metadata={
                                'commodity': 'A',
                                'quantity': trade_qty,
                                'market_cleared': True
                            }
                        )
                        trades.append(trade)
                        
                        # Update remaining capacities
                        buyer_remaining[buyer_id] -= trade_qty
                        seller_remaining[seller_id] -= trade_qty
                        
                        # Update running commitments to prevent double-spending
                        running_committed_B[buyer_id] += payment_B
                        
                        if buyer_remaining[buyer_id] <= 0:
                            break
                else:  # commodity == 'B'
                    # Buyer needs B, pays A
                    # Calculate max buyer can afford based on actual inventory minus ALL commitments (including running ones)
                    available_A = buyer_agent.inventory.A - running_committed_A[buyer_id]
                    max_buyer_can_afford = int(available_A / price) if price > 0 and available_A > 0 else 0
                    max_buyer_can_afford = min(max_buyer_can_afford, buyer_remaining[buyer_id])
                    trade_qty = min(available_from_seller, max_buyer_can_afford, buyer_max_qty)
                    
                    # DEBUG: Add logging for problematic trades
                    if buyer_id == 2 and trade_qty > 0:
                        print(f"DEBUG B-trade: Agent {buyer_id} has A={buyer_agent.inventory.A}, committed_A={running_committed_A[buyer_id]}, available_A={available_A}, price={price:.3f}, trade_qty={trade_qty}, payment_A={round(trade_qty * price)}")
                    
                    # Recalculate payment based on actual quantity
                    payment_A = round(trade_qty * price)  # Use proper rounding instead of int()
                    # Ensure payment doesn't exceed buyer's available budget
                    if payment_A > available_A:
                        # Reduce quantity to fit budget
                        trade_qty = int(available_A / price) if price > 0 and available_A > 0 else 0
                        payment_A = round(trade_qty * price)
                    
                    # Verify feasibility - all constraints must be satisfied
                    # CRITICAL: Final check that buyer can actually afford this trade
                    if (trade_qty > 0 and 
                        payment_A <= available_A and  # This is the correct check - available_A already accounts for commitments
                        trade_qty <= seller_agent.inventory.B and
                        trade_qty <= buyer_remaining[buyer_id] and
                        trade_qty <= seller_remaining[seller_id]):
                        trade = Trade(
                            buyer_id=buyer_id,
                            seller_id=seller_id,
                            pair_type="A<->B",
                            dA=-payment_A,
                            dB=trade_qty,
                            dM=0,
                            price=price,
                            market_id=market.id,
                            protocol_name="walrasian",
                            tick=sim.tick,
                            metadata={
                                'commodity': 'B',
                                'quantity': trade_qty,
                                'market_cleared': True
                            }
                        )
                        trades.append(trade)
                        
                        # Update remaining capacities
                        buyer_remaining[buyer_id] -= trade_qty
                        seller_remaining[seller_id] -= trade_qty
                        
                        # Update running commitments to prevent double-spending
                        running_committed_A[buyer_id] += payment_A
                        
                        if buyer_remaining[buyer_id] <= 0:
                            break
                
                if seller_remaining[seller_id] <= 0:
                    continue  # Move to next seller
        
        return trades

