from playwright.sync_api import Page, expect
from framework.excel import ExcelManager
from framework import report
from framework import screenshot
from framework.errors import StepFailure
from modules.common import do_global_search, sheet_name_from_input, _force_close_search_modal, dismiss_error_toast


def run(*, page: Page, excel: ExcelManager, output_excel: ExcelManager, input_sheet: str) -> None:
    sheet_name = sheet_name_from_input(input_sheet)

    rows = excel.read_sheet_as_dicts(sheet_name)
    if not rows:
        raise RuntimeError(f"No data found in '{sheet_name}' sheet")

    failed_items = []
    failed_screenshots = []

    for idx, row in enumerate(rows, start=2):

        menu_name = str(row.get("MenuName") or row.get("Menu") or "").strip()
        if not menu_name:
            continue

        # start each row from a clean UI state — a previous row's failure must
        # not leave the search modal open/stale for this row's attempt
        dismiss_error_toast(page)
        _force_close_search_modal(page)

        opened = False
        error_detail = ""

        try:
            do_global_search(page, search_term=menu_name)

        except Exception as exc:
            shot_path = screenshot.capture(page, sheet_name, menu_name, "FAIL")

            report.record_sheet_row_result(
                output_excel,
                sheet_name,
                idx,
                status="❌ FAILED",
                screenshot=shot_path,
            )

            failed_items.append(
                f"{menu_name} (Global Search failed: {exc})"
            )
            failed_screenshots.append(shot_path)
            continue

        try:

            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Global Search popup should disappear
            expect(
                page.get_by_role(
                    "textbox",
                    name="Search modules..."
                )
            ).to_be_hidden(timeout=8000)

            page.wait_for_timeout(1000)

            opened = True

        except Exception as exc:
            opened = False
            error_detail = str(exc)

        if opened:

            report.record_sheet_row_result(
                output_excel,
                sheet_name,
                idx,
                status="✅ PASSED",
                screenshot="",
            )

        else:

            shot_path = screenshot.capture(page, sheet_name, menu_name, "FAIL")

            report.record_sheet_row_result(
                output_excel,
                sheet_name,
                idx,
                status="❌ FAILED",
                screenshot=shot_path,
            )

            failed_items.append(
                f"{menu_name} ({error_detail})"
            )
            failed_screenshots.append(shot_path)

    if failed_items:
        raise StepFailure(
            f"One or more menu items failed to open in '{sheet_name}': "
            + "; ".join(failed_items),
            screenshots=failed_screenshots,
        )