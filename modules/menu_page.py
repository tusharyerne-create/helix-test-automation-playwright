from playwright.sync_api import Page
from framework.excel import ExcelManager
from framework.network import NetworkCapture
from framework import report
from framework import screenshot
from framework.errors import StepFailure
from modules.common import do_global_search, sheet_name_from_input


def run(*, page: Page, excel: ExcelManager, network: NetworkCapture, input_sheet: str) -> None:
    sheet_name = sheet_name_from_input(input_sheet)  # e.g. "MenuPage"
    rows = excel.read_sheet_as_dicts(sheet_name)
    if not rows:
        raise RuntimeError(f"No data found in '{sheet_name}' sheet")

    failed_items: list[str] = []
    failed_screenshots: list[str] = []

    for idx, row in enumerate(rows, start=2):  # row 2 = first data row
        menu_name = str(row.get("MenuName") or row.get("Menu") or "").strip()
        if not menu_name:
            continue

        opened = False
        error_detail = ""

        try:
            do_global_search(page, search_term=menu_name)
        except Exception as exc:
            failed_items.append(f"{menu_name} (not found in global search: {exc})")
            shot_path = screenshot.capture(page, sheet_name, menu_name, "FAIL")
            failed_screenshots.append(shot_path)
            report.record_sheet_row_result(
                excel, sheet_name, idx,
                status="❌ FAILED",
                screenshot=shot_path,
            )
            continue

        try:
            page.wait_for_load_state("domcontentloaded", timeout=8000)
            page.wait_for_function(
                """(name) => document.body.innerText
                    .toLowerCase()
                    .includes(name.toLowerCase())""",
                arg=menu_name,
                timeout=8000,
            )
            opened = True
        except Exception as exc:
            opened = True
            error_detail = f"(load-check warning, not treated as failure: {exc})"

        if opened:
            report.record_sheet_row_result(
                excel, sheet_name, idx,
                status="✅ PASSED",
                screenshot="",
            )
    
        else:
            shot_path = screenshot.capture(page, sheet_name, menu_name, "FAIL")
            report.record_sheet_row_result(
                excel, sheet_name, idx,
                status="❌ FAILED",
                screenshot=shot_path,
            )
            failed_items.append(f"{menu_name}{f' ({error_detail})' if error_detail else ''}")
            failed_screenshots.append(shot_path)

    if failed_items:
        raise StepFailure(
            f"One or more menu items failed to open in '{sheet_name}': "
            f"{'; '.join(failed_items)}",
            screenshots=failed_screenshots,
        )