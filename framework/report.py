from framework.excel import ExcelManager
from framework.scenario import SCENARIO_SHEET, ScenarioStep



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



def record_sheet_row_result(excel: ExcelManager, sheet_name: str, row_number: int,
                             *, actual: str = None, status: str = None,
                             http_status: str = None, screenshot: str = None) -> None:

    if actual is not None and excel.find_column(sheet_name, "Actual") is not None:
        excel.write_cell_by_header(sheet_name, row_number, "Actual", actual)
    if status is not None and excel.find_column(sheet_name, "Status") is not None:
        excel.write_cell_by_header(sheet_name, row_number, "Status", status)

    if screenshot is not None and excel.find_column(sheet_name, "Screenshot") is not None:
        excel.write_cell_by_header(sheet_name, row_number, "Screenshot", screenshot)


def finalize(excel: ExcelManager, results: list[tuple[ScenarioStep, StepResult]]) -> dict:
    excel.save()
    total = len(results)
    passed = sum(1 for _, r in results if r.status == "PASSED")
    return {"total": total, "passed": passed, "failed": total - passed}