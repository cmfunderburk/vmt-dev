"""
Pygame visualization for VMT simulation.
"""

import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vmt_engine.simulation import Simulation


class VMTRenderer:
    """Renders VMT simulation using Pygame."""
    
    def __init__(self, simulation: 'Simulation', cell_size: int = 30):
        """
        Initialize renderer.
        
        Args:
            simulation: The simulation to render
            cell_size: Size of each grid cell in pixels
        """
        pygame.init()
        
        self.sim = simulation
        self.cell_size = cell_size
        self.width = simulation.grid.N * cell_size
        self.height = simulation.grid.N * cell_size + 100  # Extra space for HUD
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("VMT v1 - Virtual Market Testbed")
        
        # Fonts
        self.font = pygame.font.SysFont('arial', 14)
        self.small_font = pygame.font.SysFont('arial', 10)
        
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
        self.recent_trades = []  # List of (tick, pos) for trade indicators
    
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
        """Draw grid lines."""
        for x in range(self.sim.grid.N + 1):
            px = x * self.cell_size
            pygame.draw.line(
                self.screen, self.COLOR_GRAY,
                (px, 0), (px, self.width),
                1
            )
        
        for y in range(self.sim.grid.N + 1):
            py = y * self.cell_size
            pygame.draw.line(
                self.screen, self.COLOR_GRAY,
                (0, py), (self.width, py),
                1
            )
    
    def draw_resources(self):
        """Draw resource cells."""
        for cell in self.sim.grid.cells.values():
            if cell.resource.amount > 0 and cell.resource.type:
                x, y = cell.position
                px = x * self.cell_size
                py = y * self.cell_size
                
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
                self.screen.blit(surface, (px, py))
                
                # Draw amount label
                label = self.small_font.render(
                    f"{cell.resource.type}:{cell.resource.amount}",
                    True, self.COLOR_BLACK
                )
                self.screen.blit(label, (px + 2, py + 2))
    
    def draw_agents(self):
        """Draw agents as circles."""
        for agent in self.sim.agents:
            x, y = agent.pos
            px = x * self.cell_size + self.cell_size // 2
            py = y * self.cell_size + self.cell_size // 2
            
            # Color based on utility type
            if agent.utility:
                utility_type = agent.utility.__class__.__name__
                if utility_type == "UCES":
                    color = self.COLOR_GREEN
                elif utility_type == "ULinear":
                    color = self.COLOR_PURPLE
                else:
                    color = self.COLOR_YELLOW
            else:
                color = self.COLOR_BLACK
            
            # Draw agent circle
            radius = self.cell_size // 3
            pygame.draw.circle(self.screen, color, (px, py), radius)
            pygame.draw.circle(self.screen, self.COLOR_BLACK, (px, py), radius, 2)
            
            # Draw agent ID
            id_label = self.small_font.render(str(agent.id), True, self.COLOR_BLACK)
            id_rect = id_label.get_rect(center=(px, py))
            self.screen.blit(id_label, id_rect)
            
            # Draw inventory below agent
            inv_text = f"A:{agent.inventory.A} B:{agent.inventory.B}"
            inv_label = self.small_font.render(inv_text, True, self.COLOR_BLACK)
            self.screen.blit(inv_label, (px - 20, py + radius + 2))
    
    def draw_trade_indicators(self):
        """Draw indicators for recent trades."""
        # Remove old trade indicators (older than 5 ticks)
        self.recent_trades = [
            (tick, pos) for tick, pos in self.recent_trades 
            if self.sim.tick - tick < 5
        ]
        
        # Draw circles around cells with recent trades
        for tick, pos in self.recent_trades:
            x, y = pos
            px = x * self.cell_size + self.cell_size // 2
            py = y * self.cell_size + self.cell_size // 2
            
            # Fade out over time
            age = self.sim.tick - tick
            alpha = 255 - (age * 50)
            
            surface = pygame.Surface((self.cell_size * 2, self.cell_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                surface, (*self.COLOR_YELLOW, alpha),
                (self.cell_size, self.cell_size),
                self.cell_size // 2, 3
            )
            self.screen.blit(surface, (px - self.cell_size, py - self.cell_size))
    
    def draw_hud(self):
        """Draw heads-up display with simulation info."""
        hud_y = self.width + 10
        
        # Background for HUD
        pygame.draw.rect(
            self.screen, self.COLOR_LIGHT_GRAY,
            (0, self.width, self.width, 100)
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
        inv_text = f"Total Inventory - A: {total_A}  B: {total_B}"
        inv_label = self.font.render(inv_text, True, self.COLOR_BLACK)
        self.screen.blit(inv_label, (10, hud_y + 40))
        
        # Controls
        controls_text = "Controls: SPACE=Pause  R=Reset  S=Step  ↑↓=Speed  Q=Quit"
        controls_label = self.small_font.render(controls_text, True, self.COLOR_BLACK)
        self.screen.blit(controls_label, (10, hud_y + 60))
    
    def add_trade_indicator(self, pos: tuple[int, int]):
        """Add a trade indicator at the given position."""
        self.recent_trades.append((self.sim.tick, pos))

