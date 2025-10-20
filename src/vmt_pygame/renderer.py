"""
Pygame visualization for VMT simulation.
"""

import pygame
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vmt_engine.simulation import Simulation
    from vmt_engine.core import Agent


class VMTRenderer:
    """Renders VMT simulation using Pygame."""
    
    def __init__(self, simulation: 'Simulation', cell_size: int = None):
        """
        Initialize renderer with automatic display scaling.
        
        Args:
            simulation: The simulation to render
            cell_size: Size of each grid cell in pixels (None = auto-detect)
        """
        pygame.init()
        
        self.sim = simulation
        
        # Get monitor dimensions
        display_info = pygame.display.Info()
        screen_width = display_info.current_w
        screen_height = display_info.current_h
        
        # Reserve space for margins and HUD
        MARGIN = 80
        HUD_HEIGHT = 100
        available_width = screen_width - (2 * MARGIN)
        available_height = screen_height - (2 * MARGIN) - HUD_HEIGHT
        
        # Calculate optimal cell size if not provided
        if cell_size is None:
            grid_size = simulation.grid.N
            optimal_cell_size = min(
                available_width // grid_size,
                available_height // grid_size
            )
            # Enforce minimum of 10px
            self.cell_size = max(10, optimal_cell_size)
        else:
            self.cell_size = cell_size
        
        # Calculate actual grid dimensions
        grid_pixel_size = simulation.grid.N * self.cell_size
        
        # Determine if scrolling is needed
        self.needs_scrolling = (
            grid_pixel_size > available_width or 
            grid_pixel_size > available_height
        )
        
        # Set window size (capped to available space)
        if self.needs_scrolling:
            self.width = min(grid_pixel_size, available_width)
            self.height = min(grid_pixel_size, available_height)
        else:
            self.width = grid_pixel_size
            self.height = grid_pixel_size
        
        # Store HUD height
        self.hud_height = HUD_HEIGHT
        
        # Add HUD height to total window height
        self.window_height = self.height + HUD_HEIGHT
        
        # Initialize camera offset for scrolling
        self.camera_x = 0
        self.camera_y = 0
        
        # Create window
        self.screen = pygame.display.set_mode((self.width, self.window_height))
        scenario_name = simulation.config.name
        seed = simulation.seed
        pygame.display.set_caption(f"VMT v1 - {scenario_name} (seed: {seed})")
        
        # Scale fonts proportionally (minimum 8px, maximum 14px for base, 6-10px for small)
        base_font_size = max(8, min(14, self.cell_size // 4))
        small_font_size = max(6, min(10, self.cell_size // 5))
        self.font = pygame.font.SysFont('arial', base_font_size)
        self.small_font = pygame.font.SysFont('arial', small_font_size)
        
        # Colors
        self.COLOR_WHITE = (255, 255, 255)
        self.COLOR_BLACK = (0, 0, 0)
        self.COLOR_GRAY = (200, 200, 200)
        self.COLOR_LIGHT_GRAY = (240, 240, 240)
        self.COLOR_RED = (255, 100, 100)
        self.COLOR_BLUE = (100, 100, 255)
        self.COLOR_GREEN = (100, 255, 100)
        self.COLOR_PURPLE = (200, 100, 255)
        self.COLOR_YELLOW = (255, 255, 100)
        
        # Track trade events for visualization
        self.recent_trades = self.sim.telemetry.recent_trades_for_renderer
    
    def handle_camera_input(self, keys):
        """Handle camera movement with arrow keys."""
        if not self.needs_scrolling:
            return
        
        SCROLL_SPEED = self.cell_size  # Scroll by one cell at a time
        grid_pixel_size = self.sim.grid.N * self.cell_size
        
        if keys[pygame.K_LEFT]:
            self.camera_x = max(0, self.camera_x - SCROLL_SPEED)
        if keys[pygame.K_RIGHT]:
            max_x = max(0, grid_pixel_size - self.width)
            self.camera_x = min(max_x, self.camera_x + SCROLL_SPEED)
        if keys[pygame.K_UP]:
            self.camera_y = max(0, self.camera_y - SCROLL_SPEED)
        if keys[pygame.K_DOWN]:
            max_y = max(0, grid_pixel_size - self.height)
            self.camera_y = min(max_y, self.camera_y + SCROLL_SPEED)
    
    def to_screen_coords(self, grid_x, grid_y):
        """Convert grid coordinates to screen coordinates with camera offset."""
        return (
            grid_x * self.cell_size - self.camera_x,
            grid_y * self.cell_size - self.camera_y
        )
    
    def is_visible(self, screen_x, screen_y):
        """Check if coordinates are visible in current viewport."""
        return (
            -self.cell_size <= screen_x <= self.width + self.cell_size and
            -self.cell_size <= screen_y <= self.height + self.cell_size
        )
    
    def render(self):
        """Render the current simulation state."""
        self.screen.fill(self.COLOR_WHITE)
        
        self.draw_grid()
        self.draw_resources()
        self.draw_agents()
        self.draw_trade_indicators()
        self.draw_hud()
        
        pygame.display.flip()
    
    def draw_grid(self):
        """Draw grid lines with camera offset and viewport culling."""
        # Only draw visible grid lines
        start_x = self.camera_x // self.cell_size
        end_x = min(self.sim.grid.N, (self.camera_x + self.width) // self.cell_size + 1)
        start_y = self.camera_y // self.cell_size
        end_y = min(self.sim.grid.N, (self.camera_y + self.height) // self.cell_size + 1)
        
        for x in range(start_x, end_x + 1):
            screen_x = x * self.cell_size - self.camera_x
            pygame.draw.line(
                self.screen, self.COLOR_GRAY,
                (screen_x, 0), (screen_x, self.height),
                1
            )
        
        for y in range(start_y, end_y + 1):
            screen_y = y * self.cell_size - self.camera_y
            pygame.draw.line(
                self.screen, self.COLOR_GRAY,
                (0, screen_y), (self.width, screen_y),
                1
            )
    
    def draw_resources(self):
        """Draw resource cells with camera offset and viewport culling."""
        for cell in self.sim.grid.cells.values():
            if cell.resource.amount > 0 and cell.resource.type:
                x, y = cell.position
                screen_x, screen_y = self.to_screen_coords(x, y)
                
                # Skip if not visible
                if not self.is_visible(screen_x, screen_y):
                    continue
                
                # Color based on resource type
                if cell.resource.type == "A":
                    color = self.COLOR_RED
                else:  # "B"
                    color = self.COLOR_BLUE
                
                # Alpha based on amount (lighter for less)
                alpha = min(255, 100 + cell.resource.amount * 30)
                surface = pygame.Surface((self.cell_size, self.cell_size))
                surface.set_alpha(alpha)
                surface.fill(color)
                self.screen.blit(surface, (screen_x, screen_y))
                
                # Draw amount label
                label = self.small_font.render(
                    f"{cell.resource.type}:{cell.resource.amount}",
                    True, self.COLOR_BLACK
                )
                self.screen.blit(label, (screen_x + 2, screen_y + 2))
    
    def group_agents_by_position(self) -> dict[tuple[int, int], list['Agent']]:
        """
        Group agents by their grid position for smart co-location rendering.
        
        Returns:
            Dictionary mapping (x, y) position to list of agents at that position,
            sorted by agent ID for deterministic rendering.
        """
        position_groups = {}
        
        for agent in self.sim.agents:
            pos = agent.pos
            if pos not in position_groups:
                position_groups[pos] = []
            position_groups[pos].append(agent)
        
        # Sort agents within each group by ID for deterministic rendering
        for pos in position_groups:
            position_groups[pos].sort(key=lambda a: a.id)
        
        return position_groups
    
    def calculate_agent_radius(self, cell_size: int, agent_count: int) -> int:
        """
        Calculate optimal agent radius based on co-location count.
        
        Strategy:
        - 1 agent: cell_size // 3 (current behavior)
        - 2 agents: cell_size // 4 (75% scale)
        - 3 agents: cell_size // 5 (60% scale)
        - 4+ agents: cell_size // (count + 2) with floor of 2px
        
        Args:
            cell_size: Size of grid cell in pixels
            agent_count: Number of co-located agents
            
        Returns:
            Radius in pixels (minimum 2px for visibility)
        """
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
        """
        Calculate display position for agent within a co-located group.
        
        Uses geometric layouts to minimize overlap:
        - 1 agent: center (current behavior)
        - 2 agents: diagonal opposite corners
        - 3 agents: triangle pattern (one top, two bottom)
        - 4 agents: one per corner
        - 5+ agents: circle pack around center
        
        Args:
            agent_index: Index of agent in sorted group (0 to total_agents-1)
            total_agents: Total number of agents at this position
            cell_center_x: Center x coordinate of cell in screen pixels
            cell_center_y: Center y coordinate of cell in screen pixels
            
        Returns:
            (px, py) display coordinates for this agent
        """
        if total_agents == 1:
            # Single agent - use center (current behavior)
            return (cell_center_x, cell_center_y)
        
        elif total_agents == 2:
            # Two agents - opposite corners (diagonal)
            # Agent 0: upper-left, Agent 1: lower-right
            offset = self.cell_size // 4
            if agent_index == 0:
                return (cell_center_x - offset, cell_center_y - offset)
            else:
                return (cell_center_x + offset, cell_center_y + offset)
        
        elif total_agents == 3:
            # Three agents - triangle pattern
            # Angles: 90° (top), 210° (bottom-left), 330° (bottom-right)
            offset = self.cell_size // 4
            angles = [90, 210, 330]
            angle_rad = math.radians(angles[agent_index])
            px = cell_center_x + int(offset * math.cos(angle_rad))
            py = cell_center_y - int(offset * math.sin(angle_rad))  # Negative because y increases downward
            return (px, py)
        
        elif total_agents == 4:
            # Four agents - one per corner
            offset = self.cell_size // 4
            corners = [
                (-offset, -offset),  # Upper-left
                (offset, -offset),   # Upper-right
                (-offset, offset),   # Lower-left
                (offset, offset),    # Lower-right
            ]
            dx, dy = corners[agent_index]
            return (cell_center_x + dx, cell_center_y + dy)
        
        else:
            # 5+ agents - circle pack around center
            offset = self.cell_size // 3
            angle_step = 360 / total_agents
            angle_rad = math.radians(agent_index * angle_step)
            px = cell_center_x + int(offset * math.cos(angle_rad))
            py = cell_center_y - int(offset * math.sin(angle_rad))
            return (px, py)
    
    def get_agent_color(self, agent: 'Agent') -> tuple[int, int, int]:
        """
        Get display color for agent based on utility type.
        
        Args:
            agent: The agent to get color for
            
        Returns:
            RGB color tuple
        """
        if agent.utility:
            utility_type = agent.utility.__class__.__name__
            if utility_type == "UCES":
                return self.COLOR_GREEN
            elif utility_type == "ULinear":
                return self.COLOR_PURPLE
            else:
                return self.COLOR_YELLOW
        return self.COLOR_BLACK
    
    def draw_group_inventory_labels(
        self,
        agents: list['Agent'],
        screen_x: int,
        screen_y: int,
        agent_count: int
    ):
        """
        Draw inventory labels for a group of co-located agents.
        
        Strategy:
        - 1 agent: Label below agent (current behavior)
        - 2-3 agents: Stack labels vertically below cell
        - 4+ agents: Show "N agents" summary instead of individual inventories
        
        Args:
            agents: List of co-located agents (sorted by ID)
            screen_x: Screen x coordinate of cell top-left
            screen_y: Screen y coordinate of cell top-left
            agent_count: Number of agents in group
        """
        has_money = (
            any(a.inventory.M > 0 for a in agents) or 
            self.sim.params.get('exchange_regime') in ('money_only', 'mixed')
        )
        
        cell_center_x = screen_x + self.cell_size // 2
        cell_bottom_y = screen_y + self.cell_size
        
        if agent_count == 1:
            # Single agent - draw inventory below (current behavior)
            agent = agents[0]
            if has_money:
                inv_text = f"A:{agent.inventory.A} B:{agent.inventory.B} M:{agent.inventory.M}"
            else:
                inv_text = f"A:{agent.inventory.A} B:{agent.inventory.B}"
            
            inv_label = self.small_font.render(inv_text, True, self.COLOR_BLACK)
            inv_width = inv_label.get_width()
            self.screen.blit(inv_label, (cell_center_x - inv_width // 2, cell_bottom_y + 2))
        
        elif agent_count <= 3:
            # 2-3 agents - stack labels vertically
            for idx, agent in enumerate(agents):
                if has_money:
                    inv_text = f"[{agent.id}] A:{agent.inventory.A} B:{agent.inventory.B} M:{agent.inventory.M}"
                else:
                    inv_text = f"[{agent.id}] A:{agent.inventory.A} B:{agent.inventory.B}"
                
                inv_label = self.small_font.render(inv_text, True, self.COLOR_BLACK)
                inv_width = inv_label.get_width()
                y_offset = cell_bottom_y + 2 + (idx * 12)  # 12px spacing between labels
                
                # Check if label would go off screen
                if y_offset + 12 <= self.height:
                    self.screen.blit(inv_label, (cell_center_x - inv_width // 2, y_offset))
        
        else:
            # 4+ agents - show summary only
            summary_text = f"{agent_count} agents at ({agents[0].pos[0]}, {agents[0].pos[1]})"
            summary_label = self.small_font.render(summary_text, True, self.COLOR_BLACK)
            summary_width = summary_label.get_width()
            self.screen.blit(summary_label, (cell_center_x - summary_width // 2, cell_bottom_y + 2))
    
    def draw_agents(self):
        """
        Draw agents with smart co-location handling.
        
        When multiple agents occupy the same cell, they are rendered with:
        - Scaled-down size (proportional to agent count)
        - Non-overlapping geometric layouts (diagonal, triangle, corners, circle pack)
        - Organized inventory labels
        
        This is a pure visualization enhancement - simulation positions remain unchanged.
        """
        # Group agents by position
        position_groups = self.group_agents_by_position()
        
        for pos, agents in position_groups.items():
            x, y = pos
            screen_x, screen_y = self.to_screen_coords(x, y)
            
            # Skip if not visible
            if not self.is_visible(screen_x, screen_y):
                continue
            
            # Calculate cell center
            cell_center_x = screen_x + self.cell_size // 2
            cell_center_y = screen_y + self.cell_size // 2
            
            # Calculate optimal radius for this group size
            agent_count = len(agents)
            radius = self.calculate_agent_radius(self.cell_size, agent_count)
            
            # Draw each agent in the group
            for idx, agent in enumerate(agents):
                # Get display position for this agent
                px, py = self.calculate_agent_display_position(
                    idx, agent_count, cell_center_x, cell_center_y
                )
                
                # Get agent color
                color = self.get_agent_color(agent)
                
                # Draw agent circle
                pygame.draw.circle(self.screen, color, (px, py), radius)
                pygame.draw.circle(
                    self.screen, self.COLOR_BLACK, (px, py), radius, 
                    max(1, radius // 5)
                )
                
                # Draw agent ID (if space permits)
                if radius >= 5 and self.cell_size >= 15:
                    id_label = self.small_font.render(str(agent.id), True, self.COLOR_BLACK)
                    id_rect = id_label.get_rect(center=(px, py))
                    self.screen.blit(id_label, id_rect)
            
            # Draw inventory labels below the entire group
            if self.cell_size >= 20:
                self.draw_group_inventory_labels(
                    agents, screen_x, screen_y, agent_count
                )
    
    def draw_trade_indicators(self):
        """Draw indicators for recent trades."""
        # This method is now obsolete as trades are drawn on the HUD
        pass
    
    def draw_hud(self):
        """Draw heads-up display with simulation info."""
        hud_y = self.height + 10
        
        # Background for HUD
        pygame.draw.rect(
            self.screen, self.COLOR_LIGHT_GRAY,
            (0, self.height, self.width, self.hud_height)
        )
        
        # Tick counter
        tick_text = f"Tick: {self.sim.tick}"
        tick_label = self.font.render(tick_text, True, self.COLOR_BLACK)
        self.screen.blit(tick_label, (10, hud_y))
        
        # Agent count
        agent_text = f"Agents: {len(self.sim.agents)}"
        agent_label = self.font.render(agent_text, True, self.COLOR_BLACK)
        self.screen.blit(agent_label, (10, hud_y + 20))
        
        # Total inventory across all agents
        total_A = sum(a.inventory.A for a in self.sim.agents)
        total_B = sum(a.inventory.B for a in self.sim.agents)
        total_M = sum(a.inventory.M for a in self.sim.agents)
        
        # Show money if any agent has it or money system is active
        has_money = total_M > 0 or self.sim.params.get('exchange_regime') in ('money_only', 'mixed')
        
        if has_money:
            inv_text = f"Total Inventory - A: {total_A}  B: {total_B}  M: {total_M}"
        else:
            inv_text = f"Total Inventory - A: {total_A}  B: {total_B}"
        
        inv_label = self.font.render(inv_text, True, self.COLOR_BLACK)
        self.screen.blit(inv_label, (10, hud_y + 40))
        
        # Controls (with scrolling if needed)
        if self.needs_scrolling:
            controls_text = "SPACE=Pause R=Reset S=Step ←→↑↓=Scroll/Speed Q=Quit"
        else:
            controls_text = "Controls: SPACE=Pause  R=Reset  S=Step  ↑↓=Speed  Q=Quit"
        controls_label = self.small_font.render(controls_text, True, self.COLOR_BLACK)
        self.screen.blit(controls_label, (10, hud_y + 60))

        # Recent trades (flexible format for barter and monetary)
        trade_hud_y = hud_y
        trade_title = self.font.render("Recent Trades:", True, self.COLOR_BLACK)
        self.screen.blit(trade_title, (250, trade_hud_y))
        
        for i, trade in enumerate(reversed(self.recent_trades)):
            if i >= 5: break
            
            # Format trade based on type
            tick = trade['tick']
            buyer = trade['buyer_id']
            seller = trade['seller_id']
            dA = trade['dA']
            dB = trade['dB']
            dM = trade.get('dM', 0)
            price = trade['price']
            
            # Determine trade type and format appropriately
            if dM != 0:
                # Monetary trade
                if dA > 0:
                    # Good A for money
                    trade_text = f"T{tick}: {buyer} buys {dA}A from {seller} for {dM}M @ {price:.2f}"
                elif dB > 0:
                    # Good B for money
                    trade_text = f"T{tick}: {buyer} buys {dB}B from {seller} for {dM}M @ {price:.2f}"
                else:
                    trade_text = f"T{tick}: Monetary trade"
            else:
                # Barter trade
                trade_text = f"T{tick}: {buyer} buys {dA}A from {seller} for {dB}B @ {price:.2f}"
            
            trade_label = self.small_font.render(trade_text, True, self.COLOR_BLACK)
            self.screen.blit(trade_label, (250, trade_hud_y + 20 + i * 15))
    
    def add_trade_indicator(self, pos: tuple[int, int]):
        """Add a trade indicator at the given position."""
        self.recent_trades.append((self.sim.tick, pos))

