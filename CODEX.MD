# Production Prompt: Convert Playwright Recording into a QA Module

Copy this prompt after recording the browser flow with Playwright Codegen. Replace every `<...>` placeholder. The recording is reference material only; the resulting code must follow the framework architecture below.

```text
You are editing an existing Python Playwright + Excel QA automation framework.
Convert the supplied Playwright Codegen recording into a production-ready, Excel-driven page module for <MODULE DISPLAY NAME>.

Goal
- Scenario step code: <EXACT STEP CODE, e.g. Payment Entry>
- Python module: `modules/<module_name>_page.py` (lowercase snake_case)
- Excel data sheet: `<sheet_name>`
- Navigation path: <HOW TO OPEN THE PAGE>
- Excel headers: <HEADER 1>, <HEADER 2>, <HEADER 3>
- One-row business action: <ACTION FOR ONE EXCEL ROW>
- Success signal: <EXPECTED RESPONSE, TOAST, OR PERSISTED UI VALUE>
- Failure signals: <ERROR TOASTS, VALIDATIONS, OR NEGATIVE CASES>
- Playwright Codegen recording (reference only):
  <PASTE RECORDING HERE>

Read these files completely before making changes:
1. `modules/common.py` — shared navigation, Action Menu, Save, and other reusable UI helpers.
2. `modules/followup_page.py` — required Excel row-processing and save-response pattern.
3. `modules/listview_page.py` and a similar existing module — locator and module style.
4. `framework/executor.py` — module imports and `MODULE_REGISTRY`.
5. `framework/excel.py`, `framework/report.py`, and `framework/scenario.py` — input, output, and Scenario contracts.
6. `config/settings.py` and `config/urls.py` — runtime configuration and workbook conventions.

Non-negotiable shared-code rule
1. Before creating any helper in the new module, inspect `modules/common.py` and all relevant existing modules for an equivalent flow.
2. Reuse an existing common helper whenever it covers the action. Do not copy its code into the module.
3. If a flow is not present but is likely to be used by another module (navigation, opening a menu, Save/Submit/Delete, selecting a common control, toast handling, dialog handling, search, or reusable verification), add a focused helper to `modules/common.py` first and use it from the new module.
4. Do not create module-specific versions of common UI behavior. In particular, Action Menu → Save must always call `modules.common.click_save(page)`, which is the Follow Up save flow. Never create `save_<module>()`, `open_action_menu_and_save()`, or duplicate Speed Dial handling inside a page module.
5. Keep only feature-specific business actions and feature-specific locators in the new module. If the same helper is needed twice, or could reasonably be needed by another module, it belongs in `modules/common.py`.
6. In your final response, explicitly list each reused common helper and each new common helper added, with a one-line reason.

Implementation rules
1. Do not redesign the framework or modify unrelated files. Use the Playwright sync API.
2. Create `modules/<module_name>_page.py` and export exactly:
   `def run(*, page: Page, excel: ExcelManager, output_excel: ExcelManager, input_sheet: str) -> None:`
3. Resolve the worksheet with `sheet_name_from_input(input_sheet)`. Load rows with `excel.read_sheet_as_dicts(sheet_name)` and raise `RuntimeError` if the sheet has no data.
4. Process independent data rows with `enumerate(rows, start=2)`. Read exact Excel headers, convert values to trimmed strings, and skip only rows missing required test data.
5. Treat Codegen as a recording, not source code. Replace fragile positional, CSS, and generated locators with verified semantic locators: `get_by_role`, `get_by_label`, and stable accessible names. If the UI has no stable semantic locator, inspect the DOM and add the smallest documented fallback.
6. Do not use `time.sleep()`. Use Playwright assertions, explicit element waits, `expect_response`, `wait_for_load_state`, or a narrowly scoped `wait_for_timeout` only for unavoidable UI animation.
7. Verify every Excel-driven value after it is selected or entered. A successful `fill()` or `click()` alone is not proof of success.
8. Save/Submit is not a pass condition. Verify the real success signal: preferably the expected API response; otherwise a fresh success toast or persisted UI value after refresh. Detect and report visible error toasts, validation messages, non-2xx responses, and timeouts.
9. For every attempted row, call `report.record_sheet_row_result(...)` with useful `actual` text and status exactly `✅ PASSED` or `❌ FAILED`. Add `http_status` only when a meaningful API response exists.
10. Catch failures per row, record them, continue with safe remaining rows, and raise a final `RuntimeError` if any row failed. Raise an error if no valid row was tested.
11. Update `framework/executor.py`: import the module and add the exact scenario step code to `MODULE_REGISTRY`.
12. For a newly created feature, create a separate workbook under `test-data` named `PythonTest_Input_Scenario<N>.xlsx`, using the next unused number. Copy prerequisite steps/sheets (`Login`, `Home Page`, `Menu`, `Logout`) and add only the new module sheet and Scenario row. Do not alter an existing scenario workbook for a new feature.
13. Never put passwords, tokens, production personal data, generated output workbooks, screenshots, or Playwright recordings into source code.

Required module structure (adapt names, fields, and feature-specific helpers):

```python
from playwright.sync_api import Page

from framework import report
from framework.excel import ExcelManager
from modules.common import do_global_search, sheet_name_from_input


MODULE_NAME = "<MODULE DISPLAY NAME>"


def perform_feature_action(page: Page, value: str) -> tuple[bool, str]:
    # Feature-specific work only. Reuse common helpers for shared UI flows.
    # Verify the real success signal before returning True.
    ...


def run(*, page: Page, excel: ExcelManager, output_excel: ExcelManager, input_sheet: str) -> None:
    sheet_name = sheet_name_from_input(input_sheet)
    rows = excel.read_sheet_as_dicts(sheet_name)
    if not rows:
        raise RuntimeError(f"No data found in '{sheet_name}' sheet")

    do_global_search(page, search_term=MODULE_NAME)
    any_failed = False
    any_tested = False

    for idx, row in enumerate(rows, start=2):
        value = str(row.get("<EXACT HEADER>") or "").strip()
        if not value:
            continue

        any_tested = True
        try:
            passed, actual = perform_feature_action(page, value)
        except Exception as exc:
            passed, actual = False, str(exc)

        report.record_sheet_row_result(
            output_excel, sheet_name, idx,
            actual=actual,
            status="✅ PASSED" if passed else "❌ FAILED",
        )
        any_failed = any_failed or not passed

    if not any_tested:
        raise RuntimeError(f"No valid test rows found in '{sheet_name}'")
    if any_failed:
        raise RuntimeError(f"One or more rows failed in '{sheet_name}'")
```

Validation and delivery
1. Run `python -m compileall modules` and `git diff --check`.
2. Run `python runner.py --scenario Scenario<N>` when the application, credentials, and workbook are available. Do not claim an end-to-end pass if they are unavailable.
3. Return production-ready changed code, not suggestions only. State: changed files; common helpers reused/added; workbook name and worksheet/Scenario additions; executed validation commands and results; and any assumptions or blockers.
```

## Excel naming contract

Names are explicit and are not inferred from the Python filename.

| Location | Required value | Example |
| --- | --- | --- |
| Module file | Python import name | `modules/payment_entry_page.py` |
| StepCode / registry key | Exact shared value in Scenario column A and `MODULE_REGISTRY` | `Payment Entry` |
| Scenario column B | `/` followed by Excel sheet name | `/payment_entry` |
| Excel worksheet | Value resolved from `input_sheet` | `payment_entry` |

The new workbook's Scenario steps should be: `Login`, `Home Page`, `Menu`, `<Module Display Name>`, `Logout`. Add the module name to `MenuPage` when Global Search navigation is required.
