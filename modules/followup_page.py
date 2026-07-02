from playwright.sync_api import Page
from framework.excel import ExcelManager
from framework.network import NetworkCapture
from framework import report
from modules.common import open_followup, execute_result, sheet_name_from_input


def _resolve_account_id(excel: ExcelManager, row: dict) -> str:
    account_id = str(row.get("AccountNo") or "").strip()
    if account_id:
        return account_id

    try:
        listview_rows = excel.read_sheet_as_dicts("listview")
    except Exception:
        return ""

    for lv_row in listview_rows:
        candidate = str(lv_row.get("AccountNo") or "").strip()
        if candidate:
            return candidate
    return ""


def run(*, page: Page, excel: ExcelManager, network: NetworkCapture, input_sheet: str) -> None:
    sheet_name = sheet_name_from_input(input_sheet)
    rows = excel.read_sheet_as_dicts(sheet_name)
    if not rows:
        raise RuntimeError(f"No data found in '{sheet_name}' sheet")

    any_failed = False
    any_tested = False
    current_account = None

    for idx, row in enumerate(rows, start=2):
        result_code = str(row.get("Result Code") or "").strip()

        if not result_code:
            continue

        http_status, output, passed = None, None, False

        try:
            account_id = _resolve_account_id(excel, row)
            if not account_id:
                raise RuntimeError(
                    f"No AccountNo found on '{sheet_name}' row {idx} or on 'listview' sheet"
                )

            if account_id != current_account:
                current_account = account_id
                open_followup(page, current_account)

            any_tested = True
            http_status, output = execute_result(page, network, result_code)
            try:
                passed = 200 <= int(http_status) < 300
            except ValueError:
                passed = False

        except Exception as row_err:
            any_tested = True
            http_status, output, passed = "ERROR", str(row_err), False

        report.record_sheet_row_result(
            excel, sheet_name, idx,
            actual=output,
            status="✅ PASSED" if passed else "❌ FAILED",
            http_status=http_status,
        )
        any_failed = any_failed or not passed

    if not any_tested:
        raise RuntimeError(
            f"No Result Code rows were actually tested in '{sheet_name}' "
            f"(no valid AccountNo could be resolved)"
        )

    if any_failed:
        raise RuntimeError(f"One or more result codes failed in '{sheet_name}'")