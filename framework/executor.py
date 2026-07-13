from playwright.sync_api import Page
from framework.excel import ExcelManager
from framework import screenshot
from framework import report
from framework.scenario import ScenarioStep, load_scenario
from modules.common import _force_close_search_modal, dismiss_error_toast

from modules import (
    login_page,
    homepage_page,
    listview_page,
    followup_page,
    menu_page,
    reason_master_page,
    logout_page,
)

MODULE_REGISTRY = {
    "Login": login_page.run,
    "Home Page": homepage_page.run,
    "Menu": menu_page.run,
    "List view": listview_page.run,
    "FollowUp": followup_page.run,
    "Reason Master": reason_master_page.run,
    "Logout": logout_page.run,
}

NON_EXECUTABLE_STEPS = {"Function"}


def _reset_ui_state(page: Page) -> None:
    dismiss_error_toast(page)
    _force_close_search_modal(page)


def run_scenario(page: Page, input_excel: ExcelManager, output_excel: ExcelManager) -> dict:
    screenshot.clear_screenshot_dir()

    steps = load_scenario(input_excel)  # scenario + step data always read from input
    results: list[tuple[ScenarioStep, report.StepResult]] = []

    for i, step in enumerate(steps, start=1):
        print(f"Step {i} - {step.step_code} check")

        if step.step_code in NON_EXECUTABLE_STEPS:
            continue

        module_fn = MODULE_REGISTRY.get(step.step_code)
        if module_fn is None:
            result = report.StepResult(status="FAILED", remarks=f"No module registered for '{step.step_code}'")
            results.append((step, result))
            report.record_step_result(output_excel, step, result)
            continue

        _reset_ui_state(page)
        try:
            # excel = read input data, output_excel = write per-row Actual/Status results
            module_fn(page=page, excel=input_excel, output_excel=output_excel, input_sheet=step.input_sheet)
            shot_path = screenshot.capture(page, step.step_code, step.input_sheet or "")
            result = report.StepResult(status="PASSED", screenshot=shot_path)
        except Exception as exc:
            shot_path = screenshot.capture(page, step.step_code, step.input_sheet or "")
            result = report.StepResult(status="FAILED", screenshot=shot_path, remarks=str(exc))
            _reset_ui_state(page)

        results.append((step, result))
        report.record_step_result(output_excel, step, result)

    return report.finalize(output_excel, results)