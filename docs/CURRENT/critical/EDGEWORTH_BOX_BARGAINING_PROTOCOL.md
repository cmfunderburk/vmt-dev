# Edgeworth Box Bargaining Protocol Design

**Date**: October 2025  
**Status**: Design Phase - Ready for Implementation  
**Scope**: 2-Agent Bilateral Exchange Only

## Overview

This document outlines the design for a new bargaining protocol that solves for the theoretical Edgeworth Box competitive equilibrium and executes trades to reach that solution. This protocol provides a clean contrast to the current "compensating block" approach by demonstrating how decentralized agents can converge to competitive equilibrium through bilateral trading.

## Core Concept

Instead of finding the first mutually beneficial trade (compensating block approach), the Edgeworth Box protocol:

1. **Solves for competitive equilibrium** - Finds the theoretical Edgeworth Box solution
2. **Remembers the target** - Stores the equilibrium allocation and exchange ratio
3. **Executes incrementally** - Trades toward the target each tick using the equilibrium exchange ratio
4. **Converges to target** - Stops when inventories match the target allocation (within integer constraints)
5. **Unpairs** - Agents separate once target is reached

## Design Decisions

### **Scope**: 2-Agent Only
- Simple, focused implementation for bilateral exchange
- Separate protocols can be created for N-agent cases later
- Avoids computational complexity of multi-agent equilibrium

### **Equilibrium Method**: MRS Equalization
- Find allocation where MRS_A = MRS_B = p_A/p_B
- Use numerical methods (e.g., Newton-Raphson) to solve for equilibrium
- Generic solver that works for all utility types (CES, Translog, Linear)

### **Convergence Criteria**: Integer Feasibility
- Target allocation = equilibrium solution rounded to respect total endowment
- "At equilibrium" = current inventories exactly match target allocations
- Rounding strategy: Round down/up to preserve total endowment constraints

### **Trade Strategy**: Equilibrium Exchange Ratio
- Calculate exchange ratio from target allocations
- Round to minimum integer ratio form (e.g., 0.5 → 1:2)
- Execute trades at this fixed ratio until convergence

### **Protocol Name**: `"edgeworth_box"`

### **Error Handling**: Fail Fast
- If cannot solve for equilibrium → raise error
- No fallback to compensating block approach

## Algorithm Overview

```python
class EdgeworthBoxBargainingProtocol(BargainingProtocol):
    def negotiate(self, pair: tuple[int, int], world: WorldView) -> list[Effect]:
        agent_a_id, agent_b_id = pair
        
        # Step 1: Solve for Edgeworth Box equilibrium
        equilibrium = self._solve_edgeworth_equilibrium(agent_a, agent_b)
        
        # Step 2: Check if already at equilibrium
        if self._is_at_equilibrium(agent_a, agent_b, equilibrium):
            return [Unpair(agent_a_id, agent_b_id)]
        
        # Step 3: Find trade toward equilibrium at fixed exchange ratio
        trade = self._find_convergence_trade(agent_a, agent_b, equilibrium)
        
        if trade:
            return [Trade(...)]
        else:
            return [Unpair(agent_a_id, agent_b_id)]  # No beneficial trade possible
```

## Implementation Details

### **Equilibrium Solution Algorithm**
```python
def _solve_edgeworth_equilibrium(agent_a, agent_b):
    # 1. Calculate MRS for both agents at current inventories
    # 2. Use numerical method to find price ratio where MRS_A = MRS_B
    # 3. Calculate target allocations using budget constraints
    # 4. Round to nearest feasible integers while preserving total endowment
    # 5. Derive exchange ratio from target allocations
    # 6. Return (target_A_a, target_B_a, target_A_b, target_B_b, exchange_ratio)
```

### **Convergence Check**
```python
def _is_at_equilibrium(agent_a, agent_b, equilibrium):
    target_A_a, target_B_a, target_A_b, target_B_b, _ = equilibrium
    return (agent_a.inventory.A == target_A_a and 
            agent_a.inventory.B == target_B_a and
            agent_b.inventory.A == target_A_b and 
            agent_b.inventory.B == target_B_b)
```

### **Trade Execution**
```python
def _find_convergence_trade(agent_a, agent_b, equilibrium):
    target_A_a, target_B_a, target_A_b, target_B_b, exchange_ratio = equilibrium
    
    # Calculate direction and size of trade needed
    delta_A_a = target_A_a - agent_a.inventory.A
    delta_B_a = target_B_b - agent_a.inventory.B
    
    # Execute trade at fixed exchange ratio
    # Find minimum trade size that moves toward target
```

## Key Implementation Challenges

### **1. Numerical Solver**
- Need robust numerical method for MRS equalization
- Handle different utility functions (CES, Translog, Linear)
- Manage edge cases and convergence issues

### **2. Integer Rounding Strategy**
- Round target allocations to preserve total endowment
- Example: If Agent 1 target = 30.2A, Agent 2 target = 18.8A, total = 49A
- Round down Agent 1 to 30A, round up Agent 2 to 19A

### **3. Exchange Ratio Calculation**
- Derive ratio from target allocations
- Convert to minimum integer form (e.g., 0.5 → 1:2)
- Ensure trades move toward target

### **4. Protocol State Management**
- Store equilibrium solution in protocol instance
- Maintain state between ticks
- Handle agent unpairing and re-pairing

## Expected Behavior

### **Convergence Pattern**
1. **Initial**: Agents have different preferences and endowments
2. **Equilibrium**: Protocol solves for competitive equilibrium
3. **Trading**: Agents trade at equilibrium exchange ratio
4. **Convergence**: Inventories approach target allocation
5. **Completion**: Agents unpair when target reached

### **Contrast with Compensating Block**
- **Compensating Block**: Finds first mutually beneficial trade, may not reach equilibrium
- **Edgeworth Box**: Solves for theoretical equilibrium, trades toward optimal allocation
- **Result**: Clean demonstration of competitive equilibrium convergence

## Use Cases

### **Edgeworth Box Scenarios**
- Perfect for the 2-agent scenarios in `scenarios/curated/edgeworth/`
- Demonstrates convergence to competitive equilibrium
- Shows how different utility functions affect equilibrium

### **Educational Value**
- Clear contrast between "first beneficial trade" vs "equilibrium-seeking" approaches
- Demonstrates theoretical microeconomic concepts in practice
- Shows impact of different utility functions on market outcomes

## Future Extensions

### **N-Agent Generalization**
- Create separate protocol for multi-agent cases
- Use different equilibrium concepts (e.g., Walrasian equilibrium)
- Handle computational complexity of larger systems

### **Market Information Integration**
- Could incorporate market price information into equilibrium calculation
- Use observed prices to inform equilibrium solution
- Bridge between theoretical and empirical price discovery

## Success Criteria

### **Functional Requirements**
- [ ] Solves Edgeworth Box equilibrium for 2-agent scenarios
- [ ] Executes trades at equilibrium exchange ratio
- [ ] Converges to target allocation within integer constraints
- [ ] Unpairs agents when target reached
- [ ] Handles all utility types (CES, Translog, Linear)

### **Technical Requirements**
- [ ] Deterministic behavior with same seed
- [ ] Robust numerical solver
- [ ] Proper integer rounding strategy
- [ ] Clean error handling
- [ ] Integration with existing protocol system

### **Educational Requirements**
- [ ] Clear demonstration of competitive equilibrium
- [ ] Contrast with compensating block approach
- [ ] Shows impact of different utility functions
- [ ] Demonstrates convergence to optimal allocation

## Conclusion

The Edgeworth Box bargaining protocol provides a clean, theoretically sound approach to bilateral exchange that directly demonstrates competitive equilibrium convergence. By solving for the theoretical optimum and trading toward it, this protocol offers a clear contrast to the current compensating block approach and provides valuable educational insights into microeconomic theory.

The protocol is designed to be simple, focused, and robust, with clear success criteria and a well-defined scope. It serves as an excellent foundation for understanding how decentralized agents can converge to competitive equilibrium through bilateral trading.
