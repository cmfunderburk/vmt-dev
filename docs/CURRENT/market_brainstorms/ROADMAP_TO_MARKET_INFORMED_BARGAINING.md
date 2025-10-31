# Roadmap to Market-Informed Bargaining Protocol

**Date**: December 2024  
**Starting Point**: Main branch (current state)  
**Goal**: Implement market-informed bargaining protocol

## Overview

This document provides a step-by-step roadmap for implementing a market-informed bargaining protocol from the current main branch, avoiding the pitfalls of the previous implementation.

## Current State Analysis

### What Exists on Main Branch
1. **Bargaining Protocol System**: `src/vmt_engine/protocols/bargaining/`
   - `legacy_compensating_block.py` - Current default protocol
   - `split_difference.py` - Alternative protocol
   - Base classes and interfaces

2. **Market System**: `src/vmt_engine/core/market.py`
   - `MarketArea` class with basic functionality
   - Market detection and management
   - No price aggregation (as intended)

3. **Trading System**: `src/vmt_engine/systems/trading.py`
   - Bilateral trade processing
   - Protocol-based negotiation
   - No market price integration (as intended)

## Target Architecture

### New Protocol: `market_informed_bargaining`
```python
class MarketInformedBargainingProtocol(BargainingProtocol):
    def negotiate(self, agent_a: Agent, agent_b: Agent, 
                  trade_type: str, sim: Simulation) -> Optional[Trade]:
        # 1. Get market prices for relevant commodities
        market_prices = self._get_market_prices(agent_a, agent_b, trade_type, sim)
        
        # 2. Use market prices to inform price discovery
        price = self._discover_price_with_market_info(agent_a, agent_b, 
                                                     trade_type, market_prices)
        
        # 3. Proceed with negotiation using market-informed price
        return self._execute_negotiation(agent_a, agent_b, trade_type, price)
```

### Market Price Access
```python
def _get_market_prices(self, agent_a: Agent, agent_b: Agent, 
                      trade_type: str, sim: Simulation) -> dict[str, float]:
    # Find markets visible to both agents
    # Extract relevant price information
    # Return market prices for commodities in trade_type
```

## Implementation Plan

### Phase 1: Market Price Infrastructure
**Goal**: Enable protocols to access market price information

#### 1.1 Extend MarketArea for Price Storage
**File**: `src/vmt_engine/core/market.py`
```python
@dataclass
class MarketArea:
    # ... existing fields ...
    
    # Price information (only when needed)
    current_prices: dict[str, float] = field(default_factory=dict)
    price_history: list[dict[str, float]] = field(default_factory=list)
    
    def update_price(self, commodity: str, price: float) -> None:
        """Update current price for a commodity"""
        self.current_prices[commodity] = price
    
    def get_price(self, commodity: str) -> Optional[float]:
        """Get current price for a commodity"""
        return self.current_prices.get(commodity)
```

#### 1.2 Add Price Recording to TradeSystem
**File**: `src/vmt_engine/systems/trading.py`
```python
def _record_trade_price(self, effect: Trade, sim: Simulation) -> None:
    """Record trade price in relevant markets"""
    # Find markets containing both agents
    # Record price for relevant commodities
    # This is protocol-agnostic infrastructure
```

#### 1.3 Create Market Price Access Interface
**File**: `src/vmt_engine/protocols/base.py`
```python
class MarketPriceProvider:
    def get_market_prices(self, agent: Agent, commodities: list[str], 
                         sim: Simulation) -> dict[str, float]:
        """Get market prices visible to agent for specified commodities"""
        # Implementation for accessing market prices
        # Only used by protocols that need it
```

### Phase 2: Market-Informed Bargaining Protocol
**Goal**: Create the new bargaining protocol

#### 2.1 Create Protocol File
**File**: `src/vmt_engine/protocols/bargaining/market_informed.py`
```python
class MarketInformedBargainingProtocol(BargainingProtocol):
    def __init__(self, market_price_provider: MarketPriceProvider):
        self.market_price_provider = market_price_provider
    
    def negotiate(self, agent_a: Agent, agent_b: Agent, 
                  trade_type: str, sim: Simulation) -> Optional[Trade]:
        # Implementation of market-informed negotiation
        pass
```

#### 2.2 Implement Price Discovery Logic
```python
def _discover_price_with_market_info(self, agent_a: Agent, agent_b: Agent,
                                   trade_type: str, market_prices: dict[str, float]) -> float:
    """Use market prices to inform price discovery"""
    # Combine market prices with agent preferences
    # Implement price discovery algorithm
    # Handle cases where market prices are unavailable
```

#### 2.3 Add Protocol Registration
**File**: `src/vmt_engine/protocols/bargaining/__init__.py`
```python
from .market_informed import MarketInformedBargainingProtocol

BARGAINING_PROTOCOLS = {
    "legacy_compensating_block": LegacyCompensatingBlockProtocol,
    "split_difference": SplitDifferenceProtocol,
    "market_informed": MarketInformedBargainingProtocol,  # NEW
}
```

### Phase 3: Configuration and Integration
**Goal**: Make the protocol selectable and testable

#### 3.1 Update Scenario Schema
**File**: `src/scenarios/schema.py`
```python
# No changes needed - bargaining_protocol already exists
# Just add "market_informed" as valid option in validation
```

#### 3.2 Update Protocol Resolution
**File**: `src/vmt_engine/protocols/__init__.py`
```python
def get_bargaining_protocol(name: str, **kwargs) -> BargainingProtocol:
    if name == "market_informed":
        # Create with market price provider
        market_provider = MarketPriceProvider()
        return MarketInformedBargainingProtocol(market_provider)
    # ... existing protocols
```

#### 3.3 Create Example Scenario
**File**: `scenarios/market_informed_example.yaml`
```yaml
bargaining_protocol: "market_informed"
# ... other parameters
```

### Phase 4: Testing and Validation
**Goal**: Ensure the protocol works correctly

#### 4.1 Unit Tests
**File**: `tests/test_market_informed_bargaining.py`
```python
class TestMarketInformedBargaining:
    def test_price_discovery_with_market_info(self):
        # Test price discovery using market prices
        pass
    
    def test_fallback_when_no_market_prices(self):
        # Test behavior when market prices unavailable
        pass
    
    def test_determinism(self):
        # Test deterministic behavior
        pass
```

#### 4.2 Integration Tests
```python
class TestMarketInformedIntegration:
    def test_protocol_selection(self):
        # Test that protocol can be selected via config
        pass
    
    def test_market_price_access(self):
        # Test that protocol can access market prices
        pass
```

## Key Design Principles

### 1. Protocol-Centric Approach
- **New protocol** rather than global system modification
- **Selective application** via configuration
- **No impact** on existing protocols

### 2. Minimal Infrastructure
- **Only add** what's needed for the protocol
- **Reuse existing** market and trading systems
- **Avoid over-engineering** the infrastructure

### 3. Backward Compatibility
- **No changes** to existing protocols
- **No changes** to existing system behavior
- **New functionality** only when protocol is selected

### 4. Determinism
- **Reproducible results** with same seed
- **Consistent behavior** across runs
- **Predictable market price access**

## Implementation Steps

### Step 1: Start Fresh
```bash
git checkout main
git checkout -b market-informed-bargaining
```

### Step 2: Add Market Price Infrastructure
1. Extend `MarketArea` for price storage
2. Add price recording to `TradeSystem`
3. Create `MarketPriceProvider` interface

### Step 3: Create Market-Informed Protocol
1. Create `market_informed.py` protocol file
2. Implement negotiation logic
3. Add protocol registration

### Step 4: Test and Validate
1. Create unit tests
2. Create integration tests
3. Test with example scenarios

### Step 5: Documentation
1. Update protocol documentation
2. Create usage examples
3. Update scenario template

## Success Criteria

### Functional Requirements
- [ ] New `market_informed` bargaining protocol exists
- [ ] Protocol can be selected via `bargaining_protocol` parameter
- [ ] Protocol uses market prices during negotiation
- [ ] Protocol falls back gracefully when market prices unavailable
- [ ] No impact on existing protocols

### Technical Requirements
- [ ] Deterministic behavior
- [ ] Comprehensive test coverage
- [ ] Clean, documented code
- [ ] Backward compatibility maintained
- [ ] Performance acceptable

### User Experience
- [ ] Easy to enable via configuration
- [ ] Clear documentation and examples
- [ ] Predictable behavior
- [ ] No breaking changes

## Conclusion

This roadmap provides a clear path from the current main branch to a market-informed bargaining protocol. The approach is protocol-centric, minimal, and maintains backward compatibility while adding the requested functionality.

The key insight is to build **infrastructure for protocols** rather than **global system modifications**, allowing for selective application and maintaining the existing architecture.
