# Utility Function Documentation Panel

## Overview
The Custom Scenario Builder GUI now includes a comprehensive documentation panel for utility functions. When users open the "Utility Functions" tab, they will see a split-panel interface with configuration controls on the left and detailed documentation on the right.

## Features

### Split-Panel Interface
- **Left Panel (60%)**: Contains the utility function configuration table, buttons for adding/removing utilities, and auto-normalize checkbox
- **Right Panel (40%)**: Contains rich HTML documentation with detailed explanations
- **Resizable**: Users can drag the splitter between panels to adjust the view

### Documentation Content

#### CES Utility Function
The documentation provides:
- **Formula**: Visual representation of U(A, B) = [wA × A^ρ + wB × B^ρ]^(1/ρ)
- **Use Cases**: When to use CES for modeling different types of economic behavior
- **Parameter Documentation**:
  - **ρ (rho)**: Detailed explanation of elasticity parameter with examples for:
    - Complementary goods (ρ < 0)
    - Cobb-Douglas preferences (ρ → 0)
    - Weak substitutes (0 < ρ < 1)
    - Perfect substitutes (ρ → 1)
    - Strong substitutes (ρ > 1)
  - **wA (weight A)**: How changing weight affects agent behavior and trading
  - **wB (weight B)**: Relative importance and its impact on preferences
- **Common Configurations**: Pre-defined examples for typical scenarios

#### Linear Utility Function
The documentation provides:
- **Formula**: Visual representation of U(A, B) = vA × A + vB × B
- **Use Cases**: When to use linear utility for simple, predictable behavior
- **Parameter Documentation**:
  - **vA (value A)**: Constant marginal value and its effect on trading
  - **vB (value B)**: Trading ratios and exchange rates
  - **MRS Explanation**: How the constant MRS = vA/vB determines trading behavior
- **Common Configurations**: Examples showing different valuation ratios

#### Mixed Utilities
The documentation explains:
- How to combine multiple utility functions with weights
- When mixing utilities is useful (e.g., modeling complex preferences)
- Weight normalization and interpretation

### Visual Design
- **Color-coded sections**:
  - Green boxes: "Best for" behavioral descriptions
  - Blue boxes: Parameter explanations
  - Yellow boxes: Common configurations and examples
- **Formatted formulas**: Mathematical notation with proper formatting
- **Hierarchical structure**: Clear H2 and H3 headers for easy navigation
- **Bullet points**: Easy-to-scan lists for parameter effects

## Implementation Details

### Code Structure
Located in: `vmt_launcher/scenario_builder.py`

**Key Methods**:
- `create_utilities_tab()`: Creates the split-panel interface with QSplitter
- `get_utility_documentation()`: Returns HTML-formatted documentation string

**Key Components**:
- `QSplitter`: Provides resizable split between panels
- `QTextBrowser`: Renders HTML documentation with scrolling
- `QTableWidget`: Configuration table (unchanged from previous version)

### HTML Styling
The documentation uses embedded CSS for:
- Professional typography (Arial, hierarchical sizing)
- Color-coded information boxes
- Proper spacing and margins
- Monospace formatting for formulas
- Responsive layout that works at different panel sizes

## User Experience

### Opening the Documentation
1. Launch the GUI via `python launcher.py`
2. Click "Create Custom Scenario"
3. Navigate to the "Utility Functions" tab
4. Documentation panel appears automatically on the right

### Using the Documentation
- **Scroll through documentation**: Use mouse wheel or scroll bar
- **Resize panels**: Drag the splitter between left and right panels
- **Reference while configuring**: Keep documentation visible while setting parameters
- **Learn parameter effects**: Understand how each parameter changes agent behavior

### Workflow Benefits
1. **No context switching**: Documentation is always visible while configuring
2. **Educational**: Helps users understand economic concepts and parameters
3. **Reduces errors**: Clear parameter explanations prevent common mistakes
4. **Examples included**: Common configurations provide starting points

## Technical Notes

### Dependencies
- PyQt5: QSplitter, QTextBrowser added to imports
- No additional external dependencies required

### Performance
- HTML is generated once at tab creation
- No dynamic updates (static content)
- Minimal memory footprint (~10KB for HTML string)

### Extensibility
To add documentation for new utility functions:
1. Edit the `get_utility_documentation()` method
2. Add a new `<h2>` section with utility name
3. Include formula, use cases, parameters, and examples
4. Use existing CSS classes for consistent styling

## Future Enhancements (Optional)
- Interactive examples that update parameter values in the table
- Graphs showing utility functions with different parameters
- Links between documentation sections
- Export documentation as PDF
- Multiple language support

## Testing
To verify the feature works correctly:
1. Run `python launcher.py`
2. Click "Create Custom Scenario"
3. Go to "Utility Functions" tab
4. Verify:
   - Documentation panel appears on right
   - Content is readable and properly formatted
   - Splitter can be dragged to resize panels
   - Formulas display with proper superscripts
   - Color-coded boxes render correctly
   - Text scrolls smoothly

## Summary
The utility function documentation panel significantly improves the user experience by providing in-context help for one of the most complex aspects of scenario configuration. Users can now understand the economic implications of different utility functions and parameter choices without leaving the GUI or consulting external documentation.

