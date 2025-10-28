# Removed Features

## Scenario Generation Tools (2025-10-27)

Removed broken CLI and GUI scenario generation tools:
- `src/vmt_tools/generate_scenario.py`
- `src/vmt_tools/scenario_builder.py`
- `src/vmt_tools/param_strategies.py`
- `src/vmt_launcher/scenario_builder.py`
- `src/vmt_launcher/validator.py`

**Reason:** Outdated after protocol refactoring. Don't support current parameters (money_utility_form, M_0, protocols, etc.).

**Replacement:** Manual YAML editing using templates in `docs/structures/`:
- `minimal_working_example.yaml`
- `comprehensive_scenario_template.yaml`
- `money_example.yaml`
- `parameter_quick_reference.md`

See working examples in `scenarios/demos/` and `scenarios/test/`.

