"""
Price signal learning system.

This system handles the flow of price information from perception to agent learning.
It updates agent price observations and triggers learning updates.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..simulation import Simulation


class PriceLearningSystem:
    """
    Phase 6: Update agent price observations and trigger learning.
    
    This system runs after trading to allow agents to learn from observed
    market prices and update their money utility parameters accordingly.
    """
    
    def execute(self, sim: "Simulation") -> None:
        """
        Update all agents' price observations and trigger learning.
        
        Args:
            sim: Current simulation state
        """
        for agent in sim.agents:
            # Get recent trade prices from perception cache
            if "recent_trade_prices" in agent.perception_cache:
                recent_prices = agent.perception_cache["recent_trade_prices"]
                
                # Store old lambda for logging
                old_lambda = agent.lambda_money
                
                # Update agent's price observations
                agent.update_price_observations(recent_prices)
                
                # Trigger learning from prices
                agent.learn_from_prices()
                
                # Log learning events if lambda changed
                if agent.lambda_changed and sim.telemetry:
                    for commodity, prices in recent_prices.items():
                        if prices:  # Only log if there were actual prices observed
                            sim.telemetry.log_price_learning(
                                tick=sim.tick,
                                agent_id=agent.id,
                                commodity=commodity,
                                old_lambda=old_lambda,
                                new_lambda=agent.lambda_money,
                                observed_prices=prices,
                                learning_rate=agent.price_learning_rate
                            )
