# from framework.excel import ExcelManager
# from framework.scenario import SCENARIO_SHEET, ScenarioStep


# class StepResult:
#     def __init__(self, status: str, http_status: str = "", screenshot: str = "", remarks: str = ""):
#         self.status = status            # "PASSED" | "FAILED"
#         self.http_status = http_status
#         self.screenshot = screenshot
#         self.remarks = remarks


# def record_step_result(excel: ExcelManager, step: ScenarioStep, result: StepResult) -> None:
#     excel.write_cell_by_header(SCENARIO_SHEET, step.row_number, "Status",
#                                 "✅ PASSED" if result.status == "PASSED" else "❌ FAILED")
#     if excel.find_column(SCENARIO_SHEET, "Screenshot") is not None:
#         excel.write_cell_by_header(SCENARIO_SHEET, step.row_number, "Screenshot",
#                                     result.screenshot or None)


# def record_sheet_row_result(excel: ExcelManager, sheet_name: str, row_number: int,
#                              *, actual: str = None, status: str = None,
#                              http_status: str = None, screenshot: str = None) -> None:
    
#     if actual is not None and excel.find_column(sheet_name, "Actual") is not None:
#         excel.write_cell_by_header(sheet_name, row_number, "Actual", actual)
#     if status is not None and excel.find_column(sheet_name, "Status") is not None:
#         excel.write_cell_by_header(sheet_name, row_number, "Status", status)
#     if http_status is not None and excel.find_column(sheet_name, "Http Status") is not None:
#         excel.write_cell_by_header(sheet_name, row_number, "Http Status", http_status)
#     if screenshot is not None and excel.find_column(sheet_name, "Screenshot") is not None:
#         excel.write_cell_by_header(sheet_name, row_number, "Screenshot", screenshot)


# def finalize(excel: ExcelManager, results: list[tuple[ScenarioStep, StepResult]]) -> dict:
  
#     excel.save()
#     total = len(results)
#     passed = sum(1 for _, r in results if r.status == "PASSED")
#     return {"total": total, "passed": passed, "failed": total - passed}

from framework.excel import ExcelManager
from framework.scenario import SCENARIO_SHEET, ScenarioStep
from framework import network as network_module


class StepResult:
    def __init__(self, status: str, http_status: str = "", screenshot: str = "", remarks: str = ""):
        self.status = status            # "PASSED" | "FAILED"
        self.http_status = http_status
        self.screenshot = screenshot
        self.remarks = remarks


def record_step_result(excel: ExcelManager, step: ScenarioStep, result: StepResult) -> None:
    excel.write_cell_by_header(SCENARIO_SHEET, step.row_number, "Status",
                                "✅ PASSED" if result.status == "PASSED" else "❌ FAILED")
    if excel.find_column(SCENARIO_SHEET, "Screenshot") is not None:
        excel.write_cell_by_header(SCENARIO_SHEET, step.row_number, "Screenshot",
                                    result.screenshot or None)


def _auto_http_status() -> str:
    """Pulls the status code of whatever network request most recently
    fired, straight from the shared NetworkCapture. This is what makes
    Http Status 'just work' for any sheet that has the column, without any
    page module (listview_page.py, menu_page.py, etc.) having to call into
    network capture itself."""
    capture = network_module.get_active_capture()
    if capture is None:
        return ""
    latest = capture.get_latest()
    return str(latest["status"]) if latest else ""


def record_sheet_row_result(excel: ExcelManager, sheet_name: str, row_number: int,
                             *, actual: str = None, status: str = None,
                             http_status: str = None, screenshot: str = None) -> None:

    if actual is not None and excel.find_column(sheet_name, "Actual") is not None:
        excel.write_cell_by_header(sheet_name, row_number, "Actual", actual)
    if status is not None and excel.find_column(sheet_name, "Status") is not None:
        excel.write_cell_by_header(sheet_name, row_number, "Status", status)

    if excel.find_column(sheet_name, "Http Status") is not None:
        # A page module (e.g. followup_page.py via execute_result) may
        # already know its own precise status and pass it in explicitly —
        # that always wins. Otherwise, auto-fill from the network capture.
        resolved_http_status = http_status if http_status is not None else _auto_http_status()
        excel.write_cell_by_header(sheet_name, row_number, "Http Status", resolved_http_status)

    if screenshot is not None and excel.find_column(sheet_name, "Screenshot") is not None:
        excel.write_cell_by_header(sheet_name, row_number, "Screenshot", screenshot)


def finalize(excel: ExcelManager, results: list[tuple[ScenarioStep, StepResult]]) -> dict:
    excel.save()
    total = len(results)
    passed = sum(1 for _, r in results if r.status == "PASSED")
    return {"total": total, "passed": passed, "failed": total - passed}