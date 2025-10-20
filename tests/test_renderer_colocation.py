"""
Tests for smart co-location rendering in Pygame renderer.

These tests verify the visual positioning logic without requiring a display.
"""

import pytest
import math


class MockRenderer:
    """Mock renderer for testing position calculation methods."""
    
    def __init__(self, cell_size):
        self.cell_size = cell_size
    
    def calculate_agent_radius(self, cell_size: int, agent_count: int) -> int:
        """Calculate optimal agent radius based on co-location count."""
        if agent_count == 1:
            return max(2, cell_size // 3)
        elif agent_count == 2:
            return max(2, cell_size // 4)
        elif agent_count == 3:
            return max(2, cell_size // 5)
        else:
            return max(2, cell_size // (agent_count + 2))
    
    def calculate_agent_display_position(
        self,
        agent_index: int,
        total_agents: int,
        cell_center_x: int,
        cell_center_y: int
    ) -> tuple[int, int]:
        """Calculate display position for agent within a co-located group."""
        if total_agents == 1:
            return (cell_center_x, cell_center_y)
        
        elif total_agents == 2:
            offset = self.cell_size // 4
            if agent_index == 0:
                return (cell_center_x - offset, cell_center_y - offset)
            else:
                return (cell_center_x + offset, cell_center_y + offset)
        
        elif total_agents == 3:
            offset = self.cell_size // 4
            angles = [90, 210, 330]
            angle_rad = math.radians(angles[agent_index])
            px = cell_center_x + int(offset * math.cos(angle_rad))
            py = cell_center_y - int(offset * math.sin(angle_rad))
            return (px, py)
        
        elif total_agents == 4:
            offset = self.cell_size // 4
            corners = [
                (-offset, -offset),
                (offset, -offset),
                (-offset, offset),
                (offset, offset),
            ]
            dx, dy = corners[agent_index]
            return (cell_center_x + dx, cell_center_y + dy)
        
        else:
            offset = self.cell_size // 3
            angle_step = 360 / total_agents
            angle_rad = math.radians(agent_index * angle_step)
            px = cell_center_x + int(offset * math.cos(angle_rad))
            py = cell_center_y - int(offset * math.sin(angle_rad))
            return (px, py)


def test_single_agent_position():
    """Single agent renders at cell center."""
    renderer = MockRenderer(cell_size=30)
    px, py = renderer.calculate_agent_display_position(0, 1, 15, 15)
    assert px == 15 and py == 15, "Single agent should be at center"


def test_two_agents_diagonal():
    """Two agents render in opposite corners (diagonal)."""
    renderer = MockRenderer(cell_size=20)
    px1, py1 = renderer.calculate_agent_display_position(0, 2, 10, 10)
    px2, py2 = renderer.calculate_agent_display_position(1, 2, 10, 10)
    
    # Agent 0 in upper-left
    assert px1 < 10 and py1 < 10, "Agent 0 should be in upper-left quadrant"
    
    # Agent 1 in lower-right
    assert px2 > 10 and py2 > 10, "Agent 1 should be in lower-right quadrant"
    
    # Should be symmetric
    assert abs(px1 - 10) == abs(px2 - 10), "X offsets should be symmetric"
    assert abs(py1 - 10) == abs(py2 - 10), "Y offsets should be symmetric"


def test_three_agents_triangle():
    """Three agents render in triangle pattern."""
    renderer = MockRenderer(cell_size=30)
    positions = [
        renderer.calculate_agent_display_position(i, 3, 15, 15)
        for i in range(3)
    ]
    
    # All should be offset from center
    for px, py in positions:
        distance = ((px - 15)**2 + (py - 15)**2)**0.5
        assert distance > 0, "Agent should be offset from center"
    
    # No two agents should be at same position
    assert len(set(positions)) == 3, "All agents should have unique positions"


def test_four_agents_corners():
    """Four agents render in four corners."""
    renderer = MockRenderer(cell_size=20)
    positions = [
        renderer.calculate_agent_display_position(i, 4, 10, 10)
        for i in range(4)
    ]
    
    # Should have 4 unique positions
    assert len(set(positions)) == 4, "All agents should have unique positions"
    
    # All should be in different quadrants
    quadrants = []
    for px, py in positions:
        x_side = "left" if px < 10 else "right"
        y_side = "top" if py < 10 else "bottom"
        quadrant = f"{y_side}-{x_side}"
        quadrants.append(quadrant)
    
    expected_quadrants = {"top-left", "top-right", "bottom-left", "bottom-right"}
    assert set(quadrants) == expected_quadrants, "Should occupy all four quadrants"


def test_radius_scaling():
    """Radius scales down with agent count."""
    renderer = MockRenderer(cell_size=30)
    
    r1 = renderer.calculate_agent_radius(30, 1)
    r2 = renderer.calculate_agent_radius(30, 2)
    r3 = renderer.calculate_agent_radius(30, 3)
    r4 = renderer.calculate_agent_radius(30, 4)
    
    # Radius should decrease as agent count increases
    assert r1 > r2 > r3 > r4, "Radius should decrease with more agents"
    
    # All should meet minimum radius
    for r in [r1, r2, r3, r4]:
        assert r >= 2, "Minimum radius should be 2px"


def test_radius_minimum_enforced():
    """Minimum radius of 2px is enforced even for tiny cells."""
    renderer = MockRenderer(cell_size=5)
    
    # Even with many agents on a tiny cell, radius should be at least 2
    for agent_count in [1, 2, 3, 5, 10, 20]:
        radius = renderer.calculate_agent_radius(5, agent_count)
        assert radius >= 2, f"Minimum 2px radius violated for {agent_count} agents"


def test_five_plus_agents_circle_pack():
    """5+ agents use circle pack layout with evenly distributed angles."""
    renderer = MockRenderer(cell_size=40)
    
    for agent_count in [5, 6, 8, 10]:
        positions = [
            renderer.calculate_agent_display_position(i, agent_count, 20, 20)
            for i in range(agent_count)
        ]
        
        # All should be unique
        assert len(set(positions)) == agent_count, f"{agent_count} agents should have unique positions"
        
        # All should be roughly same distance from center (circle pack)
        distances = [
            ((px - 20)**2 + (py - 20)**2)**0.5
            for px, py in positions
        ]
        
        # All distances should be similar (within a pixel due to rounding)
        avg_dist = sum(distances) / len(distances)
        for dist in distances:
            assert abs(dist - avg_dist) <= 2, "Circle pack should have uniform radius"


def test_deterministic_positions():
    """Same inputs always produce same outputs (determinism test)."""
    renderer = MockRenderer(cell_size=30)
    
    # Call multiple times with same inputs
    for _ in range(10):
        pos1 = renderer.calculate_agent_display_position(0, 3, 15, 15)
        pos2 = renderer.calculate_agent_display_position(1, 3, 15, 15)
        pos3 = renderer.calculate_agent_display_position(2, 3, 15, 15)
        
        # Results should be identical every time
        assert pos1 == renderer.calculate_agent_display_position(0, 3, 15, 15)
        assert pos2 == renderer.calculate_agent_display_position(1, 3, 15, 15)
        assert pos3 == renderer.calculate_agent_display_position(2, 3, 15, 15)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
