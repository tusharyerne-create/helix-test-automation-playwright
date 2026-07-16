# Steps: Add a New Module Page

Follow these steps whenever creating a new Playwright page module.

## 1. Record the Playwright flow

Activate the project environment if needed, then record the page flow from the repository root:

```powershell
.\venv\Scripts\Activate.ps1
python -m playwright codegen --browser firefox "<application-url>"
URL- python -m playwright codegen --browser firefox http://10.165.100.49:9010/drs/
```

Use the URL from `config/settings.py` or navigate from the login page. Record one business flow at a time: login, navigation, data entry, save/submit, and the expected confirmation/result.

Copy the generated script. It is reference material only; do not paste it directly into the project without refactoring.

## 2. Decide the module and Excel names

Current workbooks contain mixed legacy worksheet names such as `MenuPage`, `ptpfollowup`, `rcfollowup`, and `deliquent_reason`. Do not rename those existing sheets. For a **new** feature, use a clear lowercase snake-case base name, for example `payment_entry`.

| Item | Example |
| --- | --- |
| Module file | `modules/payment_entry_page.py` |
| Excel data sheet | `payment_entry` |
| Scenario sheet input | `/payment_entry` |
| StepCode (Excel `Scenario` column A and executor registry key) | `Payment Entry` |

These values do not connect automatically. `StepCode` is one shared value: add `"Payment Entry": payment_entry_page.run` to `MODULE_REGISTRY` in `framework/executor.py`, then put `Payment Entry` in Excel `Scenario` column A. The registry key and `StepCode` must match character-for-character. The part after `/` in Scenario column B must exactly match the Excel worksheet name.

One module may use more than one Excel sheet when it handles variations of the same feature. For example, the existing `FollowUp` module runs for both `/ptpfollowup` and `/rcfollowup`.

## 3. Give the recorded flow to an AI agent

Open `CODEX.MD`, copy the complete prompt, and paste it into ChatGPT, Claude, or Codex. Fill in:

- module display name and filename;
- data-sheet name and exact Excel headers;
- navigation and expected results;
- success/negative scenarios;
- Playwright Codegen recording.

The prompt instructs the agent to analyse the current module implementations and create code compatible with this framework.

## 4. Add Excel input data

This project does **not** use an `/input` folder. For each new feature module, create a separate workbook under `test-data/` named `PythonTest_Input_Scenario<N>.xlsx`, using the next unused scenario number. Do not add a new feature to an existing Scenario workbook.

1. Copy the common prerequisite steps and their sheets into the new workbook: `Login`, `Home Page`, `Menu`, and `Logout`.
2. Create a worksheet named `<sheet_name>`. For new features prefer lowercase snake case; retain existing legacy sheet names as they are.
3. Add exact field headers in row 1, based on what the module reads.
4. Include `Actual` and `Status` headers so the runner can write row results.
5. Add one input row per test case.
6. In the `Scenario` sheet, add the new row between `Menu` and `Logout`:

| Column A: step code | Column B: input sheet |
| --- | --- |
| `<Module Display Name>` | `/<sheet_name>` |

If the module uses Global Search, add its display name to the new workbook's `MenuPage` sheet.

Do not put real credentials, tokens, or production-sensitive data in the workbook.

## 5. Check the generated code

Confirm that the AI created/updated all required pieces:

- `modules/<module_name>_page.py` with the required `run(page, excel, output_excel, input_sheet)` function;
- `framework/executor.py` import and `MODULE_REGISTRY` mapping;
- Excel worksheet and `Scenario` row;
- shared navigation/actions in `modules/common.py` only when genuinely reusable.

Each processed Excel row must call `report.record_sheet_row_result`. The module must raise an error after processing if one or more rows fail; otherwise the Scenario step could be marked passed incorrectly.

## 6. Run the test

From the repository root:

```powershell
python runner.py
```

To run one workbook explicitly or all scenario workbooks one by one:

```powershell
python runner.py --scenario Scenario1
python runner.py --all
```

Alternatively set `RUN_MODE = "all"` in `config/settings.py` and run `python runner.py`.

Results are written to the output workbook configured by `framework/output_manager.py`. Scenario-level status is written to the output `Scenario` sheet; row-level `Actual` and `Status` results are written to the module worksheet. Failure screenshots are saved under `screenshots/`.

## 7. Review before committing

- Confirm every new Excel row has `✅ PASSED` or `❌ FAILED`.
- Check the output workbook and screenshots for failed cases.
- Verify the new scenario step runs and is registered under the intended name.
- Remove temporary Playwright recordings and generated test artifacts from the change list.
- Confirm no secrets or production data were added.
