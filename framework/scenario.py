from dataclasses import dataclass
from framework.excel import ExcelManager

SCENARIO_SHEET = "Scenario"


@dataclass
class ScenarioStep:
    row_number: int        # 1-based row in the Scenario sheet (for writing Status back)
    step_code: str         # e.g. "Login", "FollowUp", "Settlement"
    input_sheet: str       # e.g. "/login", "/followup1", "List View"


def load_scenario(excel: ExcelManager) -> list[ScenarioStep]:
    ws = excel.get_sheet(SCENARIO_SHEET)
    steps = []
    for row_idx in range(2, ws.max_row + 1):
        step_code = ws.cell(row_idx, 1).value
        input_sheet = ws.cell(row_idx, 2).value
        if not step_code or not str(step_code).strip():
            continue
        steps.append(ScenarioStep(
            row_number=row_idx,
            step_code=str(step_code).strip(),
            input_sheet=str(input_sheet).strip() if input_sheet else None,
        ))
    return steps
