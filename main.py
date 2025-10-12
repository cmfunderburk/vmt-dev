"""
Main entry point for VMT simulation with Pygame visualization.
"""

import sys
import pygame
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario
from vmt_pygame.renderer import VMTRenderer


def main():
    """Run VMT simulation with visualization."""
    # Load scenario
    if len(sys.argv) > 1:
        scenario_path = sys.argv[1]
    else:
        scenario_path = "scenarios/three_agent_barter.yaml"
    
    print(f"Loading scenario: {scenario_path}")
    scenario = load_scenario(scenario_path)
    
    # Parse seed from command line if provided
    seed = 42
    if len(sys.argv) > 2:
        seed = int(sys.argv[2])
    
    print(f"Initializing simulation with seed {seed}...")
    sim = Simulation(scenario, seed=seed)
    
    print("Starting visualization...")
    renderer = VMTRenderer(sim, cell_size=50)
    
    clock = pygame.time.Clock()
    running = True
    paused = False
    tick_rate = 5  # Ticks per second
    
    print("\nControls:")
    print("  SPACE: Pause/Resume")
    print("  R: Reset simulation")
    print("  S: Step one tick (when paused)")
    print("  UP/DOWN: Increase/decrease speed")
    print("  Q: Quit")
    print()
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                    print("Paused" if paused else "Resumed")
                
                elif event.key == pygame.K_r:
                    print("Resetting simulation...")
                    sim = Simulation(scenario, seed=seed)
                    renderer.sim = sim
                    renderer.recent_trades = []
                    print("Reset complete")
                
                elif event.key == pygame.K_s and paused:
                    print(f"Step: tick {sim.tick}")
                    sim.step()
                
                elif event.key == pygame.K_UP:
                    tick_rate = min(60, tick_rate + 1)
                    print(f"Speed: {tick_rate} ticks/sec")
                
                elif event.key == pygame.K_DOWN:
                    tick_rate = max(1, tick_rate - 1)
                    print(f"Speed: {tick_rate} ticks/sec")
                
                elif event.key == pygame.K_q:
                    running = False
        
        # Update simulation
        if not paused:
            sim.step()
        
        # Render
        renderer.render()
        
        # Control frame rate
        clock.tick(tick_rate)
    
    print("\nSimulation ended.")
    print(f"Final tick: {sim.tick}")
    print("Logs saved to ./logs/")
    
    pygame.quit()


if __name__ == "__main__":
    main()

