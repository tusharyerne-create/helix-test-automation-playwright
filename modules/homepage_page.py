from playwright.sync_api import Page
from framework.excel import ExcelManager
from framework.network import NetworkCapture
from framework import report
from modules.common import sheet_name_from_input


def run(*, page: Page, excel: ExcelManager, network: NetworkCapture, input_sheet: str) -> None:
    sheet_name = sheet_name_from_input(input_sheet)  # "homepage"
    page.wait_for_load_state("networkidle")

    loaded = page.locator("body").is_visible()
    actual = "Homepage loaded" if loaded else "Homepage did not load"

    excel.write_cell_by_header(sheet_name, 2, "Actual", actual)
    report.record_sheet_row_result(excel, sheet_name, 2, status="✅ PASSED" if loaded else "❌ FAILED")

    if not loaded:
        raise RuntimeError("Homepage failed to load")
