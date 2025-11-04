Here is a critical code review focused on identifying and updating outdated docstrings, as requested.

The review is based on the project's recent architectural changes as documented in the `CHANGELOG.md`, `docs/1_technical_manual.md`, and `docs/2_typing_overview.md`, specifically:
1.  **Money System Removal**: The project is now a pure barter (A↔B) economy. All references to `dM`, `inventory_M`, `lambda_money`, and `exchange_regime` are legacy.
2.  **Protocol Decoupling**: Matching and Bargaining are separate. Matching uses lightweight heuristics, while Bargaining contains the full trade-finding logic (like `compensating_block`).
3.  **New Protocol Signatures**: Bargaining protocols now receive agents directly, eliminating old "params hacks".

The following files contain outdated docstrings and, in some cases, legacy code that will fail at runtime.

---

### 1. High-Priority Findings (Functionally Broken)

These files contain docstrings and code that reference the removed money system. This code is not just outdated; it is functionally broken and will cause runtime errors because the database schema has been updated to remove these columns.

**Files:**
* `src/vmt_log_viewer/queries.py`
* `src/vmt_log_viewer/csv_export.py`
* `src/vmt_log_viewer/viewer.py`

**Review:**
* **`src/vmt_log_viewer/queries.py`**: This file is entirely outdated. Numerous queries reference columns that no longer exist.
    * `get_trade_statistics`: Queries `SUM(dM)` and `AVG(dM)`.
    * `get_money_trades`: Queries `WHERE dM != 0`.
    * `get_lambda_trajectory`: Queries `lambda_money`.
    * `get_mode_timeline`: Queries `exchange_regime`.
    * `get_money_statistics`: Queries `dM`, `buyer_lambda`, `seller_lambda`.
    * **Recommendation**: All money-related queries must be removed or updated. The docstrings for all remaining queries (like `get_trade_statistics`) must be updated to remove references to money.
* **`src/vmt_log_viewer/csv_export.py`**: The docstrings for `export_agent_snapshots` and `export_trades` explicitly state they export "with money columns". The code queries `inventory_M`, `lambda_money`, and `dM`.
    * **Recommendation**: These functions must be rewritten to query only the existing barter columns (A, B, dA, dB). The docstrings must be updated to reflect this.
* **`src/vmt_log_viewer/viewer.py`**: The UI still creates a "Money" tab via `_create_money_tab` and `load_money_tab`.
    * **Recommendation**: This entire feature must be removed from the UI to prevent calls to the broken queries.

---

### 2. Medium-Priority Findings (Misleading Legacy Logic)

These files contain docstrings that are highly misleading due to the recent protocol decoupling. The code works (as it's part of the legacy implementation), but the docstrings incorrectly describe *what* the code is and *where* the primary logic now lives.

**File:** `src/vmt_engine/systems/matching.py`

**Review:**
This file is the most significant source of confusion. It previously contained all matching and trading logic. It now contains *helpers* and *legacy logic*, but its docstrings have not been updated to reflect this demotion.
* **Module Docstring**: The docstring `"Matching and trading helpers."` is vague. It should clarify that this file contains *helpers for protocols* and the *legacy implementation* of matching, while the core protocol logic is now in `src/vmt_engine/game_theory/` and `src/vmt_engine/agent_based/`.
* **`estimate_money_aware_surplus` Docstring**: The docstring itself admits it's outdated: "This function is named 'estimate_money_aware_surplus' for historical reasons but now only handles barter trades".
    * **Recommendation**: This function should be renamed to `estimate_barter_surplus` and the docstring updated to remove the historical apology.
* **`find_compensating_block` and `trade_pair` Docstrings**: These docstrings describe the core trading logic. This is misleading. The *primary* implementation of this logic is now in `src/vmt_engine/game_theory/bargaining/compensating_block.py`.
    * **Recommendation**: These docstrings must be updated to state: "This is a *legacy helper function* used by the `legacy_three_pass` matching protocol. The primary implementation of this logic is now found in the `CompensatingBlockBargaining` protocol."

---

### 3. Documentation & Planning File Discrepancies

These non-code files are inconsistent with the current codebase and need updating to avoid confusing developers.

* **`docs/2_typing_overview.md`**: This document is internally inconsistent. The "Specification History" section correctly notes the "Money System Removal (2025-10-31)". However, the "Telemetry Schema (SQLite)" section in the *same file* still lists `inventory_M`, `lambda_money`, `dM`, and `exchange_regime`.
    * **Recommendation**: The schema definition in `docs/2_typing_overview.md` must be updated to match the *actual* schema in `src/telemetry/database.py` (which correctly has no money columns).
* **`src/vmt_engine/protocols/telemetry_schema.py`**: This is a planning file, not active code, but its docstring for the `effects table` contains an example `Trade` effect that includes `"dM": 0`.
    * **Recommendation**: This example should be updated to remove `dM` to align with the current barter-only design.
* **`src/vmt_engine/simulation.py`**: The `__init__` docstring states the protocol system is "(Phase 0 - Infrastructure only, not yet wired)". This is critically outdated. The protocols are fully wired and configurable via the `scenario_config`.
    * **Recommendation**: This docstring should be updated to reflect that the protocol system is fully implemented and central to the simulation's operation.

---

### 4. Examples of Good Docstrings

Conversely, several files have been updated *correctly* and serve as excellent templates for how to handle this review:

* **`src/vmt_pygame/renderer.py`**: The module docstring contains a "DEPRECATION NOTICE" explicitly stating that money visualization features are deprecated. Functions like `draw_agents_with_lambda_heatmap` and `draw_hud` have docstrings that clearly state they now fall back to barter-only behavior. This is a model for how to update legacy-facing code.
* **`src/vmt_engine/game_theory/bargaining/split_difference.py`**: The module docstring clearly states "NOT YET IMPLEMENTED - Stub" and the version is "2025.11.04.stub". This is accurate and helpful.
* **`src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py`**: This file also has a clear "NOT YET IMPLEMENTED - Stub" docstring.