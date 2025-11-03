## Transition Plan: Goods Quantities from `int` to `Decimal`

### 1. Objectives and Scope
- **Goal:** Replace all integer-based good quantity representations with fixed-precision `Decimal` values while preserving economic invariants and determinism.
- **Scope:** Core simulation engine (`vmt_engine`), serialization layers, documentation, and supporting utilities. Telemetry and analytics are included only insofar as they consume updated types.
- **Out of scope:** User-facing UI tweaks, market protocol redesigns, or monetary pricing logic beyond necessary type adjustments.

### 2. Assumptions and Constraints
- Python `decimal` module is available in the runtime environment.
- Simulation tick determinism must be preserved; no randomness or ordering changes will be introduced by the migration.
- Existing save files or fixtures may contain integer quantities; backward compatibility strategy must be explicit.
- Performance degradation should be measurable; target no worse than 2x slowdown without profiling justification.

### 3. Precision Configuration Strategy
1. **Create central settings module** (`src/vmt_engine/core/decimal_config.py`):
   - Define `DECIMAL_PRECISION`, `QUANTITY_DECIMAL_PLACES`, `QUANTITY_QUANTIZER`, and `DECIMAL_ROUNDING`.
   - Initialize global context (`getcontext().prec`) and document rationale.
   - Provide helper `quantize_quantity(value: Decimal) -> Decimal` to enforce canonical rounding.
2. **Document usage contract** within module docstring and update `docs/4_typing_overview.md` to reference the new configuration source of truth.
3. **Add regression guard**: lightweight unit test ensuring config parameters meet expected relationships (e.g., quantizer matches decimal places).

### 4. Domain Model Migration
1. **Inventory and Resource structures**:
   - Update `Inventory` dataclass fields (`A`, `B`, and money if applicable) to `Decimal` defaults set via helper factory.
   - Inject quantization in `__post_init__` and validations for non-negativity using Decimal comparisons.
   - Mirror changes in `Resource.amount` and any other Quantity-bearing dataclasses.
2. **Type aliases**: Replace `Quantity: int` with descriptive comment noting `Decimal` usage in `docs/4_typing_overview.md`; ensure code references align.
3. **Factory and builder paths** (scenario loaders, fixtures) must convert incoming ints/floats to `Decimal` via `Decimal(str(value))` to avoid binary float artifacts.

### 5. Arithmetic and State Transition Updates
1. **Exchange and inventory operations**:
   - Audit modules performing addition/subtraction on quantities (e.g., trading, foraging, consumption) to ensure all arithmetic uses `Decimal` operands.
   - Wrap results with `quantize_quantity` before persisting to state.
2. **Comparisons and invariants**:
   - Replace `> 0` style checks with Decimal-aware comparisons (`value < Decimal('0')`).
   - Confirm all invariants continue to hold; update error messages to reflect Decimal representations.
3. **Aggregation logic** (totals, averages) must handle Decimal sums; use `sum` with `Decimal('0')` initial value.

### 6. Serialization and Interoperability
1. **Scenario input schemas**:
   - Decide on accepted formats (string vs numeric). Recommend accepting strings to preserve precision.
   - Update validation layers to coerce to Decimal while validating scale (no more than configured decimal places).
2. **Telemetry/database logging**:
   - Ensure serializers convert Decimal to string or integer minor units depending on storage convention.
   - Update Alembic/migration notes if database schema enforces numeric precision.
3. **External APIs/tests**: Review any JSON dumps or fixtures to guarantee deterministic ordering and representation (likely stringified decimals).

### 7. Economic Logic Compatibility
1. **Utility functions (`econ/utility.py`)**:
   - Replace usage of `math` module functions with Decimal-friendly alternatives (`ln`, `exp`, `quantize`, or fallback to float with explicit conversion and quantization).
   - Add targeted unit tests per utility form to verify identical outputs under representative inputs.
2. **Price computations**:
   - Evaluate whether prices remain `float` or migrate to Decimal; document decision and adjust cross-type arithmetic accordingly.
3. **Derived metrics** (MRS, marginal utilities) must return Decimal or clearly cast to float with reasoning.

### 8. Testing and Validation Plan
1. **Unit tests**:
   - Expand coverage for Inventory, Resource, and trade operations to assert Decimal types, precision, and invariants.
   - Add regression tests for rounding behavior (e.g., fractional trades, repeated additions).
2. **Property-based tests**: Consider Hypothesis to validate that arbitrary sequences of trades maintain non-negative inventories and conforming scale.
3. **Integration tests**:
   - Run existing simulation scenarios; compare aggregated outputs against baseline integer runs for qualitative sanity (document expected differences).
   - Monitor performance; record before/after tick throughput.
4. **Static analysis**: Optional mypy plugin or type assertions ensuring Decimal propagation.

### 9. Rollout Checklist
- [ ] Config module introduced and imported without circular dependencies.
- [ ] All quantity fields converted to Decimal and quantized.
- [ ] Serialization paths updated and documented.
- [ ] Utilities and economic logic validated for Decimal compatibility.
- [ ] Documentation refreshed (`typing_overview`, changelog).
- [ ] Test suite passes; new tests added for Decimal behavior.
- [ ] Performance benchmark recorded and evaluated against tolerance.

### 10. Risk Assessment and Mitigations
- **Performance degradation:** Mitigate via profiling; consider selective float usage for hot paths with justifying documentation.
- **Serialization inconsistencies:** Enforce centralized conversion helpers; add end-to-end tests on JSON/DB outputs.
- **Third-party library incompatibility:** Audit any libraries consuming quantities; wrap conversions where needed.
- **Developer ergonomics:** Provide helper functions and documentation to discourage direct Decimal construction with binary float literals.

### 11. Open Questions for Confirmation
- Should monetary holdings adopt the same decimal precision as goods, or retain existing representation?
- Is backward compatibility with saved integer-based state required, and if so, what migration strategy (auto-conversion vs. versioned loader) is preferred?
- Are there scenarios requiring heterogeneous precision per good type (e.g., commodities vs. money)?
- Should price representations transition to Decimal simultaneously for symmetry?

---
**Next Steps:** Await stakeholder confirmation on open questions and precision policies. Once approved, proceed with implementation following sections 3–8 in order, ensuring tests accompany each major step.
