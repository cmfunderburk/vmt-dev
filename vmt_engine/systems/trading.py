from __future__ import annotations
from typing import TYPE_CHECKING
from .matching import trade_pair

if TYPE_CHECKING:
    from ..simulation import Simulation


class TradeSystem:
    """Phase 4: Agents trade with nearby partners."""

    def execute(self, sim: "Simulation") -> None:
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

            trade_pair(agent_i, agent_j, sim.params, sim.telemetry, sim.tick)
