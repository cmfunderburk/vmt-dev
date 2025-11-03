# Economic Domain Concepts

VMT simulates microeconomic exchange. Understanding these economic concepts helps write correct, meaningful code.

## Pure Barter Economy

VMT currently implements **only bilateral barter** (A↔B direct exchanges):
- No money
- No centralized markets (yet—planned for Stage 3)
- All trades are bilateral agent-to-agent negotiations
- Prices emerge from decentralized bargaining, not imposed by auctioneer

**Implementation**: `src/vmt_engine/systems/matching.py:find_best_trade()`

## Utility Functions

Agents have preferences represented by utility functions `U(A, B)`.

### CES (Constant Elasticity of Substitution)

```python
U(A, B) = ((wA * A^rho) + (wB * B^rho))^(1/rho)
```

**Parameters**:
- `rho`: Elasticity parameter
  - `rho < 0`: Complements (prefer balanced bundles)
  - `rho > 0`: Substitutes (don't mind imbalanced bundles)
  - `rho → 0`: Cobb-Douglas (special case)
- `wA`, `wB`: Preference weights

**Use cases**: Standard microeconomic analysis, variety-seeking behavior

### Linear (Perfect Substitutes)

```python
U(A, B) = vA * A + vB * B
```

**Parameters**:
- `vA`, `vB`: Per-unit values

**Properties**:
- Constant MRS = vA/vB
- Willing to trade at any price within MRS bounds
- Simple arbitrage scenarios

### Quadratic (Bliss Points)

```python
U(A, B) = -(sigma_A * (A - A_star)^2 + sigma_B * (B - B_star)^2 + gamma * (A - A_star) * (B - B_star))
```

**Parameters**:
- `A_star`, `B_star`: Bliss points (optimal amounts)
- `sigma_A`, `sigma_B`: Curvature parameters
- `gamma`: Cross-curvature

**Properties**:
- Non-monotonic (satiation beyond bliss points)
- Agents refuse trades when saturated (MU ≤ 0)
- Models gift economies, satiation behavior

### Translog (Transcendental Logarithmic)

```python
ln(U) = alpha_0 + alpha_A * ln(A) + alpha_B * ln(B) 
        + 0.5 * (beta_AA * ln(A)^2 + beta_BB * ln(B)^2 + 2 * beta_AB * ln(A) * ln(B))
```

**Properties**:
- Flexible functional form
- Variable elasticity of substitution
- Second-order Taylor approximation in log space
- Useful for empirical estimation

### Stone-Geary (Subsistence Constraints)

```python
U(A, B) = (A - gamma_A)^alpha_A * (A - gamma_B)^alpha_B
```

**Parameters**:
- `gamma_A`, `gamma_B`: Subsistence levels (minimum needs)
- `alpha_A`, `alpha_B`: Preference weights

**Properties**:
- Hyperbolic marginal utility near subsistence
- Models basic needs vs. discretionary consumption
- Foundation of Linear Expenditure System (LES)

**Invariant**: Inventories must exceed subsistence: `A > gamma_A`, `B > gamma_B`

## Reservation Prices

Agent's willingness to trade based on **Marginal Rate of Substitution (MRS)**:

```python
MRS = MU_A / MU_B  # Marginal utilities

# Reservation bounds
p_min = MRS / (1 + epsilon)  # Minimum price to sell A
p_max = MRS * (1 + epsilon)  # Maximum price to buy A
```

**Zero-inventory guard**: When inventory is zero, add small epsilon to prevent division by zero in ratio calculations.

**Bid-ask spread**: Configured via `spread` parameter:
```python
ask = p_min * (1 + spread)  # Seller's asking price
bid = p_max * (1 - spread)  # Buyer's bid price
```

## Surplus

**Definition**: Utility gain from trade

```python
surplus_i = U_after - U_before  # For agent i
```

**Distance-discounted surplus**: Used in pairing decisions:
```python
discounted_surplus = surplus * (beta^distance)
```

Where `beta` (0 < β < 1) is time discount factor—agents prefer nearby trading partners (lower travel cost).

## Trade Feasibility

For trade to execute:
1. **Mutual benefit**: `ΔU_i > 0` and `ΔU_j > 0`
2. **Inventory feasibility**: Can't trade more than possessed
3. **Price agreement**: Buyer's bid ≥ Seller's ask
4. **Integer quantities**: Round-half-up for discrete goods

## Compensating Block Search

VMT's price discovery algorithm for discrete goods:

```python
def find_compensating_block(agent_i, agent_j):
    # Scan trade sizes
    for delta_A in range(1, seller.inventory.A + 1):
        # Test candidate prices in [seller.ask, buyer.bid]
        for price in linspace(seller.ask, buyer.bid, n_samples):
            delta_B = floor(price * delta_A + 0.5)  # Round-half-up
            
            # Check mutual benefit
            if utility_gain(agent_i, delta_A, delta_B) > 0 and \
               utility_gain(agent_j, delta_A, delta_B) > 0:
                return Trade(delta_A, delta_B, price)
    
    return None  # No mutually beneficial trade found
```

**First-acceptable-trade principle**: Accept first valid trade, not highest surplus.

## Market Phenomena

### Price Convergence

**Question**: When do bilateral negotiations produce uniform prices?

**Factors**:
- Protocol choice (bargaining mechanism)
- Spatial clustering (market thickness)
- Preference heterogeneity
- Search costs (distance)

**Not assumed**: VMT observes whether prices converge, doesn't impose convergence.

### Market Thickness

Number of potential trading partners within interaction range.

**Effects**:
- Thick markets: More competition, faster price convergence
- Thin markets: Bilateral monopoly, wider price dispersion

### Spatial Friction

Distance costs affect trade:
- Movement costs (limited `move_budget_per_tick`)
- Vision limits (`vision_radius`)
- Distance discounting (`β^distance`)

## Economic Validation

When implementing features, verify:

1. **Individual rationality**: Agents never trade at loss
2. **Inventory non-negativity**: Can't have negative goods
3. **Conservation**: Total goods constant (except foraging/consumption)
4. **Monotonicity**: (For CES, Linear) More goods → higher utility
5. **Convexity**: (For CES) Diminishing MRS

**Example test**:
```python
def test_trade_mutual_benefit():
    # Execute trade
    u_before_i = agent_i.utility.u(agent_i.inventory.A, agent_i.inventory.B)
    u_before_j = agent_j.utility.u(agent_j.inventory.A, agent_j.inventory.B)
    
    execute_trade(agent_i, agent_j, delta_A=5, delta_B=3)
    
    u_after_i = agent_i.utility.u(agent_i.inventory.A, agent_i.inventory.B)
    u_after_j = agent_j.utility.u(agent_j.inventory.A, agent_j.inventory.B)
    
    # Both must benefit
    assert u_after_i > u_before_i
    assert u_after_j > u_before_j
```

## Pedagogical Notes

VMT demonstrates:
- **Markets as constructions**: Institutional rules determine outcomes
- **Price formation**: Emergent from bilateral bargaining
- **Institutional comparison**: Different protocols → different results
- **Spatial dynamics**: Geography and search matter

**Anti-pattern**: Don't assume equilibrium exists or prices converge. Observe what happens.

## Research Questions

Code should enable investigating:
1. When do bilateral prices converge to uniform "market price"?
2. How do different bargaining protocols affect surplus division?
3. What role does spatial structure play in market efficiency?
4. How does preference heterogeneity affect trade patterns?

## Future Extensions (Stage 3)

Planned features:
- **Walrasian auctioneer**: Centralized price-setting
- **Posted-price market**: Take-it-or-leave-it offers
- **Double auction**: Centralized order book

**Research goal**: Compare bilateral vs. centralized exchange efficiency.

