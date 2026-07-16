import re as _re
from playwright.sync_api import Page
from framework.excel import ExcelManager
from framework import report
from modules.common import click_save, do_global_search, sheet_name_from_input

MODULE_NAME = "Reason Master"


def select_reason_type(page: Page, reason_type: str) -> None:
    combo = page.get_by_role("combobox", name="Select reason type")
    combo.click()
    page.wait_for_timeout(200)
    combo.fill(reason_type)
    page.get_by_role("option", name=reason_type).wait_for(state="visible", timeout=5000)
    page.get_by_role("option", name=reason_type).click()
    page.wait_for_timeout(300)
    page.get_by_role("button", name="FETCH").click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)


def navigate_to_new_row(page: Page) -> None:
    page.locator(".h-ag-grid-pagination-left > button").click()
    page.wait_for_timeout(500)
    page.locator(".ag-row-last .ag-cell").first.click()
    page.wait_for_timeout(400)


def fill_reason_code(page: Page, reason_code: str) -> None:
    editor = page.get_by_role("textbox", name="Input Editor")
    editor.wait_for(state="visible", timeout=5000)
    editor.clear()
    editor.fill(reason_code)
    page.wait_for_timeout(300)


def _is_editor_open(page: Page, timeout: int = 1200) -> bool:
    try:
        editor = page.get_by_role("textbox", name="Input Editor").first
        editor.wait_for(state="visible", timeout=timeout)
        return True
    except Exception:
        return False


def _description_cell_candidates(page: Page):
    primary = page.get_by_role("gridcell").filter(has_text=_re.compile(r"^$"))
    for idx in (4, 3, 5, 2, 1, 0):
        candidate = primary.nth(idx)
        if candidate.count() > 0:
            yield candidate

    for parity in ("odd", "even"):
        loc = page.locator(
            f".ag-row-{parity}.ag-row.ag-row-level-0.ag-row-position-absolute.ag-row-last > div:nth-child(2)"
        )
        if loc.count() > 0:
            yield loc.first

    loc = page.locator(".ag-row-last > div:nth-child(2)")
    if loc.count() > 0:
        yield loc.first


def fill_reason_description(page: Page, reason_description: str) -> None:
    opened = False

    for candidate in _description_cell_candidates(page):
        try:
            candidate.scroll_into_view_if_needed(timeout=2000)
        except Exception:
            pass

        try:
            candidate.dblclick(timeout=2000)
            page.wait_for_timeout(300)
            if _is_editor_open(page):
                opened = True
                break
        except Exception:
            pass
        try:
            candidate.click(timeout=2000)
            page.wait_for_timeout(200)
            focused = page.locator(".ag-cell-focus")
            if focused.count() > 0:
                focused.first.dblclick(timeout=2000)
                page.wait_for_timeout(300)
                if _is_editor_open(page):
                    opened = True
                    break
        except Exception:
            pass

        try:
            candidate.click(timeout=2000)
            page.wait_for_timeout(200)
            page.keyboard.press("F2")
            page.wait_for_timeout(300)
            if _is_editor_open(page):
                opened = True
                break
            page.keyboard.press("Enter")
            page.wait_for_timeout(300)
            if _is_editor_open(page):
                opened = True
                break
        except Exception:
            pass

    if not opened:
        raise RuntimeError(
            "fill_reason_description: Description cell editor did not open "
            "after all fallback attempts (dblclick / click+dblclick / F2 / Enter)"
        )

    editor = page.get_by_role("textbox", name="Input Editor").first
    editor.wait_for(state="visible", timeout=5000)
    editor.clear()
    editor.fill(reason_description)
    page.wait_for_timeout(300)


def select_row_checkbox(page: Page, reason_code: str, reason_description: str) -> None:
    row = page.get_by_role("row", name=f"{reason_code} {reason_description} Delete")
    row.get_by_label("", exact=True).first.check()
    page.wait_for_timeout(300)


def open_action_menu_and_save(page: Page) -> None:
    click_save(page)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)


def verify_row_present(page: Page, reason_code: str) -> bool:
    page.get_by_role("button", name="FETCH").click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    return page.locator(".ag-cell", has_text=reason_code).count() > 0


def delete_row(page: Page, reason_code: str, reason_description: str) -> None:
    row = page.get_by_role("row", name=f"{reason_code} {reason_description} Delete")
    count = row.count()
    if count == 0:
        raise RuntimeError(f"delete_row: '{reason_code}' not found in grid after save")
    elif count == 1:
        row.get_by_label("Delete").click()
    else:
        row.first.get_by_label("Delete").click()
    page.wait_for_timeout(400)


def verify_row_absent(page: Page, reason_code: str) -> bool:
    page.get_by_role("button", name="FETCH").click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    return page.locator(".ag-cell", has_text=reason_code).count() == 0


def execute_one(page: Page, reason_type: str, reason_code: str, reason_desc: str) -> tuple[bool, str]:
    select_reason_type(page, reason_type)
    navigate_to_new_row(page)
    fill_reason_code(page, reason_code)
    fill_reason_description(page, reason_desc)
    select_row_checkbox(page, reason_code, reason_desc)
    open_action_menu_and_save(page)

    if not verify_row_present(page, reason_code):
        return False, "ADD FAILED: row not found after save"

    delete_row(page, reason_code, reason_desc)
    open_action_menu_and_save(page)
    if not verify_row_absent(page, reason_code):
        return False, "DELETE FAILED: row still present"

    return True, "ADD + DELETE verified"


def run(*, page: Page, excel: ExcelManager, output_excel: ExcelManager, input_sheet: str) -> None:
    sheet_name = sheet_name_from_input(input_sheet) or "reason_master"
    rows = excel.read_sheet_as_dicts(sheet_name)
    if not rows:
        raise RuntimeError(f"No data found in '{sheet_name}' sheet")

    do_global_search(page, search_term=MODULE_NAME)

    any_failed = False
    for idx, row in enumerate(rows, start=2):
        reason_type = str(row.get("ReasonType") or "").strip()
        reason_code = str(row.get("ReasonCode") or "").strip()
        reason_desc = str(row.get("ReasonDescription") or "").strip()
        if not reason_code:
            continue

        passed, remarks = execute_one(page, reason_type, reason_code, reason_desc)
        report.record_sheet_row_result(
            output_excel, sheet_name, idx,
            actual=remarks,
            status="✅ PASSED" if passed else "❌ FAILED",
        )
        any_failed = any_failed or not passed

    if any_failed:
        raise RuntimeError(f"One or more reason codes failed in '{sheet_name}'")
