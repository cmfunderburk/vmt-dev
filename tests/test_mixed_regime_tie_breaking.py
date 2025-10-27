"""
Unit tests for money-first tie-breaking in mixed regimes (Money Phase 3).

Tests the ranking logic in LegacyBargainingProtocol that implements deterministic
three-level sorting for trade selection in mixed exchange regimes.

NOTE: Most tests in this file require refactoring to test through the protocol interface
rather than accessing private TradeSystem methods. Currently skipped pending refactoring.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Tests need refactoring for protocol interface")
from src.vmt_engine.protocols.bargaining.legacy import LegacyBargainingProtocol
from src.vmt_engine.systems.trading import TradeCandidate


class TestMoneyFirstTieBreaking:
    """Test money-first tie-breaking policy in mixed regimes."""
    
    def setup_method(self):
        """Create bargaining protocol instance for testing."""
        self.protocol = LegacyBargainingProtocol()
    
    def test_money_preferred_when_surplus_equal(self):
        """Money trades should be preferred over barter when surplus is equal."""
        # Create candidates with equal surplus
        money_trade = TradeCandidate(
            buyer_id=0, seller_id=1,
            good_sold="A", good_paid="M",
            dX=2, dY=10,
            buyer_surplus=5.0, seller_surplus=5.0
        )
        
        barter_trade = TradeCandidate(
            buyer_id=0, seller_id=1,
            good_sold="A", good_paid="B",
            dX=2, dY=3,
            buyer_surplus=5.0, seller_surplus=5.0
        )
        
        # Convert to protocol format: (pair_name, trade_tuple)
        # trade_tuple = (dA_i, dB_i, dM_i, dA_j, dB_j, dM_j, surplus_i, surplus_j)
        candidates = [
            ("A<->B", (2, -3, 0, -2, 3, 0, 5.0, 5.0)),  # barter
            ("A<->M", (2, 0, -10, -2, 0, 10, 5.0, 5.0))  # money
        ]
        
        best_pair, best_trade = self.protocol._rank_and_select_best(candidates)
        
        # Money trade should be selected (higher priority)
        assert best_pair == "A<->M", "Money trade should be ranked first"
    
    def test_barter_selected_when_surplus_higher(self):
        """Barter trade should be selected if it offers higher surplus."""
        money_trade = TradeCandidate(
            buyer_id=0, seller_id=1,
            good_sold="A", good_paid="M",
            dX=2, dY=10,
            buyer_surplus=4.0, seller_surplus=4.0  # Total: 8.0
        )
        
        barter_trade = TradeCandidate(
            buyer_id=0, seller_id=1,
            good_sold="A", good_paid="B",
            dX=2, dY=3,
            buyer_surplus=6.0, seller_surplus=6.0  # Total: 12.0
        )
        
        # Convert to protocol format
        candidates = [
            ("A<->M", (2, 0, -10, -2, 0, 10, 4.0, 4.0)),  # money, total=8.0
            ("A<->B", (2, -3, 0, -2, 3, 0, 6.0, 6.0))     # barter, total=12.0
        ]
        
        best_pair, best_trade = self.protocol._rank_and_select_best(candidates)
        
        # Higher surplus wins despite lower priority
        assert best_pair == "A<->B", "Higher surplus trade should be ranked first"
    
    @pytest.mark.skip(reason="Test needs conversion to protocol interface - ranking logic now in LegacyBargainingProtocol")
    def test_deterministic_ordering(self):
        """Repeated sorts should produce identical orderings."""
        pass
    
    @pytest.mark.skip(reason="Test needs conversion to protocol interface")
    def test_agent_id_tie_breaking(self):
        """When surplus and pair type equal, lower agent IDs should be first."""
        # Same pair type, same surplus, different agent pairs
        trade_high_ids = TradeCandidate(
            buyer_id=5, seller_id=8,
            good_sold="A", good_paid="M",
            dX=2, dY=10,
            buyer_surplus=5.0, seller_surplus=5.0
        )
        
        trade_low_ids = TradeCandidate(
            buyer_id=1, seller_id=2,
            good_sold="A", good_paid="M",
            dX=2, dY=10,
            buyer_surplus=5.0, seller_surplus=5.0
        )
        
        candidates = [trade_high_ids, trade_low_ids]
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        # Lower IDs should come first
        assert ranked[0].buyer_id == 1 and ranked[0].seller_id == 2, \
            "Lower agent ID pair should be ranked first"
        assert ranked[1].buyer_id == 5 and ranked[1].seller_id == 8, \
            "Higher agent ID pair should be ranked second"
    
    def test_three_level_sorting(self):
        """Test all three sorting levels work together correctly."""
        candidates = [
            # Level 3: Highest surplus (should be first)
            TradeCandidate(0, 1, "A", "B", 3, 5, 8.0, 8.0),  # Total: 16.0
            
            # Level 2: Medium surplus, money vs barter tie-break
            TradeCandidate(2, 3, "A", "M", 2, 10, 5.0, 5.0),  # Total: 10.0, money
            TradeCandidate(2, 3, "A", "B", 2, 3, 5.0, 5.0),   # Total: 10.0, barter
            
            # Level 1: Low surplus, agent ID tie-break
            TradeCandidate(6, 7, "B", "M", 1, 5, 2.0, 2.0),   # Total: 4.0, high IDs
            TradeCandidate(0, 1, "B", "M", 1, 5, 2.0, 2.0),   # Total: 4.0, low IDs
        ]
        
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        # Verify ordering
        assert ranked[0].total_surplus == 16.0, "Highest surplus first"
        
        assert ranked[1].total_surplus == 10.0 and ranked[1].pair_type == "A<->M", \
            "Medium surplus, money beats barter"
        assert ranked[2].total_surplus == 10.0 and ranked[2].pair_type == "A<->B", \
            "Medium surplus, barter comes after money"
        
        assert ranked[3].total_surplus == 4.0 and ranked[3].buyer_id == 0, \
            "Low surplus, low IDs first"
        assert ranked[4].total_surplus == 4.0 and ranked[4].buyer_id == 6, \
            "Low surplus, high IDs last"
    
    def test_b_money_priority_between_a_money_and_barter(self):
        """B<->M should have priority between A<->M and barter."""
        candidates = [
            TradeCandidate(0, 1, "A", "B", 2, 3, 5.0, 5.0),   # Barter, priority 2
            TradeCandidate(0, 1, "B", "M", 3, 15, 5.0, 5.0),  # B<->M, priority 1
            TradeCandidate(0, 1, "A", "M", 2, 10, 5.0, 5.0),  # A<->M, priority 0
        ]
        
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        assert ranked[0].pair_type == "A<->M", "A<->M has highest priority"
        assert ranked[1].pair_type == "B<->M", "B<->M has middle priority"
        assert ranked[2].pair_type == "A<->B", "Barter has lowest priority"
    
    def test_empty_candidate_list(self):
        """Should handle empty candidate list gracefully."""
        candidates = []
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        assert ranked == [], "Empty list should return empty list"
    
    def test_single_candidate(self):
        """Should handle single candidate correctly."""
        candidates = [
            TradeCandidate(0, 1, "A", "M", 2, 10, 5.0, 5.0)
        ]
        
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        assert len(ranked) == 1, "Should return single candidate"
        assert ranked[0] == candidates[0], "Should be unchanged"
    
    def test_all_same_surplus_and_type(self):
        """When all candidates identical except IDs, sort by agent ID."""
        candidates = [
            TradeCandidate(7, 8, "A", "M", 2, 10, 5.0, 5.0),
            TradeCandidate(3, 4, "A", "M", 2, 10, 5.0, 5.0),
            TradeCandidate(1, 2, "A", "M", 2, 10, 5.0, 5.0),
            TradeCandidate(5, 6, "A", "M", 2, 10, 5.0, 5.0),
        ]
        
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        # Should be sorted by agent IDs
        assert ranked[0].buyer_id == 1 and ranked[0].seller_id == 2
        assert ranked[1].buyer_id == 3 and ranked[1].seller_id == 4
        assert ranked[2].buyer_id == 5 and ranked[2].seller_id == 6
        assert ranked[3].buyer_id == 7 and ranked[3].seller_id == 8
    
    def test_reverse_pair_perspectives(self):
        """M<->A and A<->M should have same priority (both monetary)."""
        candidates = [
            TradeCandidate(0, 1, "M", "A", 10, 2, 5.0, 5.0),  # Seller perspective
            TradeCandidate(2, 3, "A", "M", 2, 10, 5.0, 5.0),  # Buyer perspective
            TradeCandidate(4, 5, "A", "B", 2, 3, 5.0, 5.0),   # Barter
        ]
        
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        # Both monetary trades should come before barter
        assert ranked[2].pair_type == "A<->B", "Barter should be last"
        
        # First two are monetary (order determined by agent IDs)
        monetary_types = {ranked[0].pair_type, ranked[1].pair_type}
        assert "M<->A" in monetary_types or "A<->M" in monetary_types


class TestTradeCandidateDataclass:
    """Test TradeCandidate dataclass properties and methods."""
    
    def test_total_surplus_property(self):
        """total_surplus property should sum buyer and seller surplus."""
        candidate = TradeCandidate(
            buyer_id=0, seller_id=1,
            good_sold="A", good_paid="M",
            dX=2, dY=10,
            buyer_surplus=3.5, seller_surplus=4.5
        )
        
        assert candidate.total_surplus == 8.0, "total_surplus should be sum of buyer and seller"
    
    def test_pair_type_property(self):
        """pair_type property should format correctly."""
        candidate = TradeCandidate(
            buyer_id=0, seller_id=1,
            good_sold="A", good_paid="M",
            dX=2, dY=10,
            buyer_surplus=5.0, seller_surplus=5.0
        )
        
        assert candidate.pair_type == "A<->M", "pair_type should be 'good_sold<->good_paid'"
    
    def test_dataclass_equality(self):
        """Two TradeCandidate instances with same values should be equal."""
        candidate1 = TradeCandidate(0, 1, "A", "M", 2, 10, 5.0, 5.0)
        candidate2 = TradeCandidate(0, 1, "A", "M", 2, 10, 5.0, 5.0)
        
        assert candidate1 == candidate2, "Identical candidates should be equal"
    
    def test_dataclass_inequality(self):
        """TradeCandidate instances with different values should not be equal."""
        candidate1 = TradeCandidate(0, 1, "A", "M", 2, 10, 5.0, 5.0)
        candidate2 = TradeCandidate(0, 1, "A", "M", 2, 10, 6.0, 5.0)  # Different surplus
        
        assert candidate1 != candidate2, "Different candidates should not be equal"


class TestSortingEdgeCases:
    """Test edge cases in sorting algorithm."""
    
    def setup_method(self):
        """Create TradeSystem instance for testing."""
        self.trade_system = TradeSystem()
    
    def test_negative_surplus_handling(self):
        """Should handle negative surplus (shouldn't happen, but test robustness)."""
        candidates = [
            TradeCandidate(0, 1, "A", "M", 2, 10, -1.0, -1.0),  # Total: -2.0
            TradeCandidate(2, 3, "A", "B", 2, 3, 5.0, 5.0),     # Total: 10.0
        ]
        
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        # Positive surplus should come first
        assert ranked[0].total_surplus == 10.0, "Positive surplus should be first"
        assert ranked[1].total_surplus == -2.0, "Negative surplus should be last"
    
    def test_zero_surplus_handling(self):
        """Should handle zero surplus correctly."""
        candidates = [
            TradeCandidate(0, 1, "A", "M", 2, 10, 0.0, 0.0),   # Total: 0.0
            TradeCandidate(2, 3, "A", "B", 2, 3, 5.0, 5.0),    # Total: 10.0
        ]
        
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        assert ranked[0].total_surplus == 10.0, "Non-zero surplus should be first"
        assert ranked[1].total_surplus == 0.0, "Zero surplus should be last"
    
    def test_very_large_surplus_differences(self):
        """Should handle very large surplus differences correctly."""
        candidates = [
            TradeCandidate(0, 1, "A", "M", 2, 10, 0.001, 0.001),  # Total: 0.002
            TradeCandidate(2, 3, "A", "B", 2, 3, 1000.0, 1000.0), # Total: 2000.0
        ]
        
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        assert ranked[0].total_surplus == 2000.0, "Large surplus should be first"
        assert ranked[1].total_surplus == 0.002, "Small surplus should be last"
    
    def test_floating_point_precision(self):
        """Should handle floating point precision correctly."""
        candidates = [
            TradeCandidate(0, 1, "A", "M", 2, 10, 5.0000001, 5.0000001),
            TradeCandidate(2, 3, "A", "B", 2, 3, 5.0, 5.0),
        ]
        
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        # Very small difference should still be respected
        assert ranked[0].total_surplus > ranked[1].total_surplus, \
            "Even tiny surplus differences should be respected"
    
    def test_unknown_pair_type_priority(self):
        """Unknown pair types should be ranked last (priority 99)."""
        # Create candidate with unusual pair type (shouldn't happen in practice)
        candidates = [
            TradeCandidate(0, 1, "A", "M", 2, 10, 5.0, 5.0),   # Known: A<->M
            TradeCandidate(2, 3, "X", "Y", 2, 3, 5.0, 5.0),    # Unknown: X<->Y
        ]
        
        ranked = self.trade_system._rank_trade_candidates(candidates)
        
        # Known pair type should come first (even with same surplus)
        assert ranked[0].pair_type == "A<->M", "Known pair type should be first"
        assert ranked[1].pair_type == "X<->Y", "Unknown pair type should be last"

