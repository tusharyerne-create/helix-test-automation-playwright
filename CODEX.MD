# Prompt for Creating a New QA Module

Copy the prompt below into Codex, ChatGPT, or Claude **after** recording the Playwright flow. Replace all text inside `<...>`.

```text
You are editing an existing Python Playwright + Excel QA automation framework.
Create a new page module for <MODULE DISPLAY NAME>.

Important: do not redesign the framework or change unrelated files. Analyse the existing implementation first and make the new module follow the same style as `modules/followup_page.py`, `modules/listview_page.py`, and `modules/reason_master_page.py`.

Read these files before writing code:
1. `modules/followup_page.py` — required module and per-row result pattern.
2. `modules/common.py` — shared navigation/action helpers; reuse or extend this file rather than duplicating common flows.
3. `framework/executor.py` — module imports and `MODULE_REGISTRY`.
4. `framework/excel.py` and `framework/report.py` — Excel reading and result-writing contract.
5. `framework/scenario.py` — `Scenario` worksheet format.
6. `config/settings.py` and `config/urls.py` — URL, browser, workbook, and route conventions.

Feature to automate:
- Display name / scenario step code: <EXACT STEP CODE, e.g. Payment Entry>
- Python filename: `modules/<module_name>_page.py` (use lowercase `snake_case` for new files)
- Excel data-sheet name: `<sheet_name>`
- Navigation path: <HOW TO OPEN THE PAGE>
- Test-data headers: <HEADER 1>, <HEADER 2>, <HEADER 3>
- One-row business action: <WHAT THE MODULE DOES FOR ONE EXCEL ROW>
- Success condition: <VISIBLE UI OR RESPONSE EXPECTED>
- Failure/validation conditions: <EXPECTED NEGATIVE CASES>
- Playwright Codegen recording (reference only):
  <PASTE THE RECORDED SCRIPT HERE>

Required implementation rules:
1. Create `modules/<module_name>_page.py` with Playwright sync API imports:
   `from playwright.sync_api import Page`
   `from framework.excel import ExcelManager`
   `from framework import report`
2. Export this exact entry-point signature:
   `def run(*, page: Page, excel: ExcelManager, output_excel: ExcelManager, input_sheet: str) -> None:`
3. Resolve the worksheet with `sheet_name_from_input(input_sheet)` from `modules.common`.
4. Read rows using `excel.read_sheet_as_dicts(sheet_name)` and raise a useful `RuntimeError` when the sheet has no data.
5. Process input rows one by one using `enumerate(rows, start=2)`. Read each value by its exact Excel header, trim string values, and skip only rows that have no required test data.
6. Put reusable page actions in small helpers. Use stable semantic locators (`get_by_role`, `get_by_label`, and stable accessible names) and explicit UI/network waits. Do not use raw Codegen output unchanged and do not use `time.sleep()`.
7. For every attempted row, call `report.record_sheet_row_result(output_excel, sheet_name, idx, ...)`. Write `actual` when a useful result/message is available and write `status` as exactly `✅ PASSED` or `❌ FAILED`. Include `http_status` only when the module has a meaningful HTTP/API status.
8. Track failures across all rows. After processing, raise `RuntimeError` if any row failed, so the scenario step is marked failed by the executor. Do not stop at the first row unless proceeding would be unsafe.
9. Update `framework/executor.py`:
   - import the new module in the `from modules import (...)` block;
   - add the exact scenario step code to `MODULE_REGISTRY`, pointing to `<module_name>_page.run`.
10. Do not create an `/input` directory. This project reads one input workbook from `test-data`, configured by `INPUT_EXCEL_PATH` in `config/settings.py`. Add a worksheet and a `Scenario` row to that workbook as described below; preserve current formatting and output columns.
11. Do not write passwords, tokens, production personal data, generated output workbooks, screenshots, or Playwright recordings into source files.

Expected module shape (adapt the helper names and Excel columns to the actual feature):

```python
from playwright.sync_api import Page
from framework.excel import ExcelManager
from framework import report
from modules.common import sheet_name_from_input


def perform_action(page: Page, value: str) -> tuple[bool, str]:
    # Navigate, perform the recorded flow, and verify the real result.
    # Return (passed, actual_message).
    ...


def run(*, page: Page, excel: ExcelManager, output_excel: ExcelManager, input_sheet: str) -> None:
    sheet_name = sheet_name_from_input(input_sheet)
    rows = excel.read_sheet_as_dicts(sheet_name)
    if not rows:
        raise RuntimeError(f"No data found in '{sheet_name}' sheet")

    any_failed = False
    any_tested = False

    for idx, row in enumerate(rows, start=2):
        value = str(row.get("<EXACT HEADER>") or "").strip()
        if not value:
            continue

        any_tested = True
        try:
            passed, actual = perform_action(page, value)
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

Before finishing, run `python runner.py` from the repository root. Report the files changed, the required worksheet/Scenario additions, the command result, and any assumptions. Do not claim the test passed if the application, workbook, or credentials were unavailable.
```

## Excel contract for the new module

The input workbook path is defined by `INPUT_EXCEL_PATH` in `config/settings.py`, currently under `test-data/`. It contains both the `Scenario` worksheet and data worksheets.

For a new module:

1. Add a worksheet named `<sheet_name>`. Existing sheets use mixed naming (`login2`, `MenuPage`, `ptpfollowup`, and `deliquent_reason`), so do not rename existing sheets. For a new module, prefer a clear lowercase `snake_case` sheet name.
2. Put headers in row 1. Include the fields needed by the module and, when expected by reporting, `Actual` and `Status` (plus `Screenshot` if required).
3. Add one test-data row per independent action/scenario.
4. In `Scenario`, add a row where column A is the **exact** `MODULE_REGISTRY` key and column B is `/<sheet_name>`.

Example:

| Scenario column A | Scenario column B |
| --- | --- |
| `Payment Entry` | `/payment_entry` |

This makes the executor call `payment_entry_page.run(..., input_sheet="/payment_entry")`; `sheet_name_from_input` converts it to `payment_entry`.

## How names connect in this project

Names are connected explicitly; they are not inferred from the Python filename.

| Location | Required value | Example |
| --- | --- | --- |
| Module file | Python import name | `modules/payment_entry_page.py` |
| StepCode / `MODULE_REGISTRY` key | Exact shared value: Excel `Scenario` column A and executor registry key | `"Payment Entry"` |
| `Scenario` column B | `/` followed by the exact Excel worksheet name | `/payment_entry` |
| Excel worksheet | Name resolved from `input_sheet` | `payment_entry` |

The current project already has mixed legacy names. For example, `modules/followup_page.py` handles the `FollowUp` registry key with both `/ptpfollowup` and `/rcfollowup`; `modules/menu_page.py` uses `/MenuPage`; and `modules/reason_master_page.py` uses `/deliquent_reason`.

A new feature should normally use the consistent example above, but one module may intentionally support multiple sheets when those sheets represent variations of the same feature.

## Required output

The AI must return production-ready changed code, not only suggestions. It must state every changed file, including the module, `framework/executor.py`, and required Excel workbook worksheets/rows.
