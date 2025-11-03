# VMT Cursor Rules

Focused, context-specific rules for VMT development. Use these when working on specific aspects of the codebase.

## Available Rules

### Core Development

**`tick-cycle.md`** - The 7-phase simulation cycle
- Phase order and responsibilities
- Phase dependencies
- Common violations
- Debugging phase issues

**`protocols.md`** - Protocol development patterns
- Protocol template and structure
- Domain organization (search/matching/bargaining)
- Effect types and WorldView access
- Registration and testing

### Testing & Debugging

**`testing.md`** - Testing conventions
- Test organization and categories
- Helper utilities and fixtures
- Test naming patterns
- Running tests
- Common test patterns

**`telemetry.md`** - Telemetry and debugging
- Database schema reference
- Logging configuration
- SQL queries for analysis
- Common debugging scenarios
- Performance considerations

### Domain Knowledge

**`economics.md`** - Economic concepts
- Pure barter economy
- Utility function specifications
- Reservation prices and surplus
- Trade feasibility and compensating block search
- Market phenomena

**`scenarios.md`** - Scenario configuration
- YAML structure and templates
- Protocol selection
- Utility configuration (homogeneous vs heterogeneous)
- Parameter reference
- Example scenarios

## How to Use

### In Cursor/Copilot

Reference specific rules when asking for help:

```
Following the determinism rules, implement a new pairing algorithm
that processes agents in sorted order.
```

```
Using the protocol template from protocols.md, create a new 
bargaining protocol called "nash_bargaining".
```

### Quick Reference

**Starting a new protocol?** → `protocols.md`
**Writing tests?** → `testing.md`
**Debugging trades?** → `telemetry.md` + `economics.md`
**Creating scenarios?** → `scenarios.md`
**Non-determinism issues?** → `determinism.md`
**Phase execution problems?** → `tick-cycle.md`

### Rule Combinations

Some tasks require multiple rules:

**Implementing a new protocol**:
1. Read `protocols.md` for structure
2. Follow `determinism.md` for iteration
3. Reference `economics.md` for domain logic
4. Use `testing.md` for test coverage

**Debugging trade issues**:
1. Check `telemetry.md` for SQL queries
2. Review `tick-cycle.md` for phase execution
3. Verify `economics.md` concepts (surplus, feasibility)
4. Examine `determinism.md` for iteration order

**Creating a benchmark scenario**:
1. Use `scenarios.md` templates
2. Consider `economics.md` concepts for meaningful setup
3. Reference `protocols.md` for protocol choices

## Maintenance

When updating rules:
- Keep focused and actionable (no fluff)
- Include code examples from actual codebase
- Reference specific files/functions when helpful
- Update this README if adding new rules

## Rule Design Philosophy

- **Specific over generic**: "Always sort by agent.id" not "maintain consistency"
- **Examples over descriptions**: Show code patterns, not just explain them
- **Actionable over aspirational**: What to do, not what would be nice
- **Discoverable patterns**: Document what exists, not what's planned
- **Context-appropriate**: Each rule file targets specific development context

