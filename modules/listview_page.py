from playwright.sync_api import Page
from framework.excel import ExcelManager
from framework.network import NetworkCapture
from framework import report
from modules.common import do_global_search, sheet_name_from_input


def search_account(page: Page, account_id: str) -> None:
    do_global_search(page, search_term="List View")
    search_box = page.get_by_role("textbox", name="Search accounts...")
    search_box.click()
    search_box.fill(account_id)
    page.get_by_role("button", name="Search", exact=True).click()
    page.wait_for_load_state("networkidle")


def run(*, page: Page, excel: ExcelManager, network: NetworkCapture, input_sheet: str) -> None:
    sheet_name = sheet_name_from_input(input_sheet)  # "listview"
    rows = excel.read_sheet_as_dicts(sheet_name)
    if not rows:
        raise RuntimeError(f"No data found in '{sheet_name}' sheet")

    any_failed = False
    for idx, row in enumerate(rows, start=2):
        account_id = str(row.get("AccountNo") or "").strip()
        if not account_id:
            continue
        search_account(page, account_id)
        found = page.get_by_role("button", name=account_id).is_visible()
        report.record_sheet_row_result(
            excel, sheet_name, idx,
            status="✅ PASSED" if found else "❌ FAILED",
        )
        any_failed = any_failed or not found

    if any_failed:
        raise RuntimeError("One or more accounts were not found in List View")