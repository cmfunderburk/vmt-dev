"""
Tests for scenario loading and validation.
"""

import pytest
from scenarios.loader import load_scenario


def test_invalid_scenario():
    """Test that invalid scenarios raise errors."""
    with pytest.raises(FileNotFoundError):
        load_scenario("scenarios/nonexistent.yaml")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

