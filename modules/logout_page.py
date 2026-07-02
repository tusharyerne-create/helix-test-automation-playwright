from playwright.sync_api import Page
from framework.excel import ExcelManager
from framework.network import NetworkCapture
from modules.common import dismiss_error_toast

MODULE_NAME = "Logout"


def run(*, page: Page, excel: ExcelManager, network: NetworkCapture, input_sheet: str) -> None:
    dismiss_error_toast(page)

    icon = page.get_by_test_id("KeyboardArrowDownIcon")
    icon.wait_for(state="visible", timeout=5000)
    try:
        icon.click(timeout=5000)
    except Exception:
        icon.click(timeout=5000, force=True)

    page.get_by_role("menuitem", name="Logout").click()
    page.wait_for_load_state("networkidle")