# Alignment vs Initial Planning (2025-10-21)

Audience: Solo developer / project lead

Scope: Compare current project status (code + docs) against the original planning document to surface intentional changes, drift, and their implications for architectural coherence and educational effectiveness.

---

## Headline Alignment

- Visualization-first agent-based simulation with NxN grid, resources, and bilateral exchange is implemented and extended (pairing system, money-aware matching, telemetry, GUI tools).
- Deterministic 7-phase loop matches the planned emphasis on reproducibility and pedagogy.
- Utility architecture is extensible and surpasses MVP scope (CES/Linear plus Quadratic/Translog/Stone-Geary).

## Notable Divergences (Intentional or Pragmatic)

1) Database-Free Plan vs SQLite Telemetry
- Original plan indicated avoiding databases for simplicity.
- Current system uses local SQLite telemetry with a PyQt log viewer and rich analysis (trade attempts, pairings, preferences, tick states).
- Assessment: Strong architectural and educational improvement (reproducibility, fast analysis, compact logs).
- Action: Update planning narrative to explicitly endorse local SQLite as a zero-external-dependency store.

2) PyQt6 Migration (2025-10-22)
- Original plan suggested PyQt6 with Pygame embedding.
- Implementation initially used PyQt5 for pragmatic reasons.
- **Status (2025-10-22): Migrated to PyQt6** - proactive migration completed before accumulating PyQt5-specific dependencies.
- Assessment: Forward-looking choice; ensures compatibility with modern Qt ecosystem.

3) MVP Utility Scope vs Implemented Breadth
- MVP emphasized three classic preferences (Cobb-Douglas/CES, Perfect Substitutes, Leontief).
- Implementation adds Quadratic (bliss points), Translog, Stone-Geary, with careful zero-handling and marginal utilities.
- Assessment: Positive for pedagogy and research demos; architecture remains coherent under a money-aware utility API.
- Action: Update MVP narrative and add explicit learning objectives for each new utility function.

4) Money System Scope and Mixed Regime
- Plan anticipated quasilinear money and later market mechanisms.
- Code implements bilateral money-aware exchange with mixed regimes and money-first tie-breaking; strong telemetry integration.
- Gap: Decision pairing ranks partners using a barter-only surplus measure even in money/mixed regimes, while trading is money-aware.
- Assessment: This reduces architectural coherence and may obscure money’s liquidity benefits in demonstrations.
- Action: Align pairing rankings with money-aware surplus in money/mixed regimes (see roadmap).

5) “Zero External Services” vs Practical Self-Containment
- The platform remains fully offline and deterministic; all data is local.
- Assessment: Fully aligned with the spirit of the requirement; SQLite is internal.

---

## Impact Summary

- Divergences are largely pragmatic improvements that enhance reproducibility, analysis, and pedagogy.
- The main misalignment affecting educational clarity is the pairing system’s barter-only ranking in money/mixed regimes.

---

## Recommended Updates to Planning/Docs

- Add an ADR set acknowledging:
  - Local SQLite telemetry adoption and rationale.
  - PyQt6 migration completed (2025-10-22).
  - Expanded utility scope and educational rationale.
- Adopt SemVer 0.0.1 and update README badges/policy; maintain a CHANGELOG (Keep a Changelog).
- Add the missing guides or stubs with status/ETA: user_guide_money.md, regime_comparison.md, technical/money_implementation.md, quick_reference.md, guides/scenario_generator.md.

---

## Minimal Action List (to close alignment gaps)

- Pairing: Introduce money-aware neighbor scoring when exchange_regime ∈ {money_only, mixed}; keep deterministic tie-breaking; add tests.
- Docs: Replace broken links with real content or stubs; update dependency targets (PyQt6) and the "local database" rationale.
- Versioning: Switch to 0.0.1 and harmonize badges and policy text.

---

## Notes for Future Curriculum Extensions

- With the money-aware bilateral engine stabilized, layer posted-price or auction markets as pluggable “Bargain” strategies without disrupting the 7-phase engine or determinism guarantees (see Modularization Roadmap).
