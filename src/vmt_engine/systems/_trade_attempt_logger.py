from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Agent
    from telemetry import TelemetryManager

def log_trade_attempt(
    telemetry: TelemetryManager,
    tick: int,
    buyer: Agent,
    seller: Agent,
    direction: str,
    price: float,
    surplus: float,
    dA: int,
    dB: int,
    buyer_improves: bool,
    seller_improves: bool,
    buyer_feasible: bool,
    seller_feasible: bool,
    status: str,
    reason: str,
):
    """Helper to log a single trade attempt."""
    buyer_A_init, buyer_B_init = buyer.inventory.A, buyer.inventory.B
    seller_A_init, seller_B_init = seller.inventory.A, seller.inventory.B
    
    buyer_U_init = buyer.utility.u(buyer_A_init, buyer_B_init) if buyer.utility else 0.0
    seller_U_init = seller.utility.u(seller_A_init, seller_B_init) if seller.utility else 0.0

    buyer_A_final = buyer_A_init + dA
    buyer_B_final = buyer_B_init - dB
    seller_A_final = seller_A_init - dA
    seller_B_final = seller_B_init + dB

    buyer_U_final = buyer.utility.u(buyer_A_final, buyer_B_final) if buyer.utility else 0.0
    seller_U_final = seller.utility.u(seller_A_final, seller_B_final) if seller.utility else 0.0

    telemetry.log_trade_attempt(
        tick, buyer.id, seller.id, direction, price,
        buyer.quotes.ask_A_in_B, buyer.quotes.bid_A_in_B,
        seller.quotes.ask_A_in_B, seller.quotes.bid_A_in_B, surplus,
        dA, dB,
        buyer_A_init, buyer_B_init, buyer_U_init,
        buyer_A_final, buyer_B_final, buyer_U_final, buyer_improves,
        seller_A_init, seller_B_init, seller_U_init,
        seller_A_final, seller_B_final, seller_U_final, seller_improves,
        buyer_feasible, seller_feasible, status, reason
    )
