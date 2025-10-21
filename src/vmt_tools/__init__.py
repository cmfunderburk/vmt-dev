"""
VMT Tools - Developer utilities for the VMT simulation.

This package contains tools for generating, manipulating, and analyzing
VMT scenario files and simulation data.
"""

__version__ = "0.1.0"

# Export main API components
from .param_strategies import generate_utility_params, generate_inventories
from .scenario_builder import generate_scenario

__all__ = [
    'generate_utility_params',
    'generate_inventories',
    'generate_scenario',
]

