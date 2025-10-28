"""
Unit tests for trade pair enumeration (Money Phase 3).

Tests the get_allowed_exchange_pairs() function that determines which exchange
types are permitted based on the exchange_regime parameter.
"""

import pytest
from vmt_engine.systems.matching import get_allowed_exchange_pairs


class TestTradePairEnumeration:
    """Test trade pair enumeration for different exchange regimes."""
    
    def test_barter_only_regime(self):
        """Barter-only regime should return only goods-for-goods pair."""
        pairs = get_allowed_exchange_pairs("barter_only")
        
        assert pairs == ["A<->B"], "Barter-only should only allow A<->B"
        assert len(pairs) == 1, "Barter-only should have exactly 1 pair type"
    
    def test_money_only_regime(self):
        """Money-only regime should return only monetary pairs."""
        pairs = get_allowed_exchange_pairs("money_only")
        
        assert "A<->M" in pairs, "Money-only should allow A<->M"
        assert "B<->M" in pairs, "Money-only should allow B<->M"
        assert "A<->B" not in pairs, "Money-only should NOT allow barter"
        assert len(pairs) == 2, "Money-only should have exactly 2 pair types"
    
    def test_mixed_regime(self):
        """Mixed regime should return all three exchange types."""
        pairs = get_allowed_exchange_pairs("mixed")
        
        assert "A<->B" in pairs, "Mixed should allow barter (A<->B)"
        assert "A<->M" in pairs, "Mixed should allow A<->M"
        assert "B<->M" in pairs, "Mixed should allow B<->M"
        assert len(pairs) == 3, "Mixed should have exactly 3 pair types"
    
    def test_mixed_liquidity_gated_regime(self):
        """Mixed liquidity-gated regime should return all three types."""
        pairs = get_allowed_exchange_pairs("mixed_liquidity_gated")
        
        assert "A<->B" in pairs, "Mixed liquidity-gated should allow barter"
        assert "A<->M" in pairs, "Mixed liquidity-gated should allow A<->M"
        assert "B<->M" in pairs, "Mixed liquidity-gated should allow B<->M"
        assert len(pairs) == 3, "Mixed liquidity-gated should have 3 pair types"
    
    def test_invalid_regime_raises_error(self):
        """Unknown regime should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_allowed_exchange_pairs("invalid_regime")
        
        assert "Unknown exchange_regime" in str(exc_info.value)
        assert "invalid_regime" in str(exc_info.value)
    
    def test_pair_order_deterministic(self):
        """Pair order should be deterministic for reproducibility."""
        # Call multiple times to ensure consistency
        pairs1 = get_allowed_exchange_pairs("mixed")
        pairs2 = get_allowed_exchange_pairs("mixed")
        pairs3 = get_allowed_exchange_pairs("mixed")
        
        assert pairs1 == pairs2 == pairs3, "Pair order must be deterministic"
        
        # Expected order for tie-breaking (A<->B first, then monetary)
        assert pairs1 == ["A<->B", "A<->M", "B<->M"], \
            "Pairs should be in documented order: barter, then monetary"
    
    def test_no_duplicates(self):
        """No regime should return duplicate pairs."""
        for regime in ["barter_only", "money_only", "mixed", "mixed_liquidity_gated"]:
            pairs = get_allowed_exchange_pairs(regime)
            assert len(pairs) == len(set(pairs)), \
                f"Regime '{regime}' returned duplicate pairs: {pairs}"
    
    def test_barter_excludes_money(self):
        """Barter-only should not include money pairs."""
        pairs = get_allowed_exchange_pairs("barter_only")
        
        for pair in pairs:
            assert "M" not in pair, f"Barter-only should not include money: {pair}"
    
    def test_money_only_excludes_barter(self):
        """Money-only should not include barter pairs."""
        pairs = get_allowed_exchange_pairs("money_only")
        
        for pair in pairs:
            assert "M" in pair, f"Money-only pairs must involve M: {pair}"
        
        # Should not allow goods-for-goods
        assert "A<->B" not in pairs, "Money-only should not allow A<->B"
    
    def test_return_type(self):
        """Method should return a list of strings."""
        pairs = get_allowed_exchange_pairs("mixed")
        
        assert isinstance(pairs, list), "Should return a list"
        assert all(isinstance(p, str) for p in pairs), "All elements should be strings"
    
    def test_empty_regime_string_raises_error(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError):
            get_allowed_exchange_pairs("")
    
    def test_case_sensitive_regime(self):
        """Regime strings should be case-sensitive."""
        # Correct case should work
        pairs = get_allowed_exchange_pairs("barter_only")
        assert pairs == ["A<->B"]
        
        # Wrong case should fail
        with pytest.raises(ValueError):
            get_allowed_exchange_pairs("Barter_Only")
        
        with pytest.raises(ValueError):
            get_allowed_exchange_pairs("MONEY_ONLY")


class TestTradePairSemantics:
    """Test semantic correctness of pair types."""
    
    def test_pair_format(self):
        """All pairs should follow X<->Y format."""
        all_pairs = []
        for regime in ["barter_only", "money_only", "mixed"]:
            all_pairs.extend(get_allowed_exchange_pairs(regime))
        
        # Remove duplicates
        unique_pairs = list(set(all_pairs))
        
        for pair in unique_pairs:
            assert "<->" in pair, f"Pair should contain '<->': {pair}"
            parts = pair.split("<->")
            assert len(parts) == 2, f"Pair should have exactly 2 goods: {pair}"
            assert all(len(p) == 1 for p in parts), \
                f"Each good should be single character: {pair}"
    
    def test_valid_good_types(self):
        """All pairs should only use valid goods: A, B, M."""
        valid_goods = {'A', 'B', 'M'}
        
        all_pairs = []
        for regime in ["barter_only", "money_only", "mixed"]:
            all_pairs.extend(get_allowed_exchange_pairs(regime))
        
        for pair in all_pairs:
            parts = pair.split("<->")
            for good in parts:
                assert good in valid_goods, \
                    f"Invalid good '{good}' in pair '{pair}'. Valid: {valid_goods}"
    
    def test_no_self_exchange(self):
        """No pair should have same good on both sides (e.g., A<->A)."""
        all_pairs = []
        for regime in ["barter_only", "money_only", "mixed"]:
            all_pairs.extend(get_allowed_exchange_pairs(regime))
        
        for pair in all_pairs:
            parts = pair.split("<->")
            assert parts[0] != parts[1], \
                f"Pair should not have same good on both sides: {pair}"

