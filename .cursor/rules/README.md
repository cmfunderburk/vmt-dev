# VMT Cursor Rules

This directory contains the core rules that govern AI assistance in the VMT project.

## Active Rules

### Always Applied
- **00_determinism.mdc** - Ensures simulation reproducibility (THE most critical rule)
- **01_vmt_architecture.mdc** - Enforces Protocol → Effect → State pattern and 7-phase tick cycle

### Context-Specific  
- **02_validation.mdc** - Applied to `src/**` and `tests/**` for testing requirements

## Rule Philosophy

These rules represent the **minimal strict core** - only the absolutely essential constraints needed to maintain:
1. Scientific validity (determinism)
2. Architectural integrity (effect-based state management)
3. Correctness verification (testing)

Additional rules can be added as needed, but these three form the non-negotiable foundation.

## Usage

These rules are automatically loaded by Cursor and applied based on their metadata:
- `alwaysApply: true` - Applied to every AI interaction
- `globs: pattern` - Applied when working with matching files
- `description: text` - Can be manually requested by referencing the rule

The AI assistant will follow these rules when generating, modifying, or reviewing code.
