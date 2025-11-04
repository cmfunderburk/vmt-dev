"""
Random Matching Protocol

Random pairing for null hypothesis baseline. Agents are paired randomly without
regard to potential gains from trade, distance, or preferences.

Economic Properties:
- Zero allocative efficiency (no welfare maximization)
- Useful baseline for comparison with strategic matching
- Demonstrates value of preference-aware pairing

References:
- Random assignment as null hypothesis in market design
- Benchmark for stable matching algorithms (Gale-Shapley)

Version: 2025.10.28
"""

from typing import Any
from ...protocols.registry import register_protocol

from .base import MatchingProtocol
from ...protocols.base import Effect, Pair
from ...protocols.context import ProtocolContext


@register_protocol(
    category="matching",
    name="random_matching",
    description="Random pairing baseline (null hypothesis)",
    properties=["stochastic", "baseline"],
    complexity="O(n)",
    references=[
        "Random assignment as null in market design",
        "Gale-Shapley benchmarking"
    ],
)
class RandomMatching(MatchingProtocol):
    """
    Random pairing for null hypothesis.
    
    Behavior:
        - Collect all agents wanting to trade
        - Shuffle deterministically using world RNG
        - Pair sequentially (first with second, third with fourth, etc.)
        - No optimization, no distance checking, no surplus consideration
    
    Economic Properties:
        - Zero information efficiency
        - No allocative efficiency
        - Baseline for measuring value of strategic matching
    
    Note: This protocol ignores agent preferences entirely. It only uses the
    preferences dict to identify which agents want to trade.
    """
    
    @property
    def name(self) -> str:
        return "random_matching"
    
    @property
    def version(self) -> str:
        return "2025.10.28"
    
    # Class-level for registry
    VERSION = "2025.10.28"
    
    def find_matches(
        self,
        preferences: dict[int, list[tuple[int | tuple[int, int], float, dict]]],
        world: ProtocolContext
    ) -> list[Effect]:
        """
        Randomly pair agents wanting to trade.
        
        Args:
            preferences: Per-agent preference lists (only used to identify trade seekers)
            world: Global protocol context with RNG
        
        Returns:
            List of Pair effects
        """
        # Collect agents wanting to trade
        # An agent wants to trade if they have trade targets (agent IDs) in preferences
        trade_seekers = []
        
        for agent_id, prefs in preferences.items():
            # Skip if already paired
            if agent_id in world.current_pairings:
                continue
            
            # Check if agent has trade targets (agent IDs, not positions/resources)
            has_trade_target = any(isinstance(target, int) for target, _, _ in prefs)
            
            if has_trade_target:
                trade_seekers.append(agent_id)
        
        # Need at least 2 agents to pair
        if len(trade_seekers) < 2:
            return []
        
        # Shuffle deterministically using world RNG
        shuffled = list(trade_seekers)
        world.rng.shuffle(shuffled)
        
        # Pair sequentially
        effects = []
        for i in range(0, len(shuffled) - 1, 2):
            agent_a = shuffled[i]
            agent_b = shuffled[i + 1]
            
            effects.append(Pair(
                protocol_name=self.name,
                tick=world.tick,
                agent_a=agent_a,
                agent_b=agent_b,
                reason="random"
            ))
        
        return effects

