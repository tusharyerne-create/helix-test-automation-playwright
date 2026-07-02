import json
from playwright.sync_api import Page
from framework.network import NetworkCapture


def _force_close_search_modal(page: Page) -> None:
    search_box = page.get_by_role("textbox", name="Search modules...")

    def is_closed() -> bool:
        try:
            return search_box.count() == 0 or not search_box.first.is_visible()
        except Exception:
            return True

    if is_closed():
        return
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
    except Exception:
        pass
    if is_closed():
        return

    try:
        page.mouse.click(5, 5)
        page.wait_for_timeout(400)
    except Exception:
        pass
    if is_closed():
        return

    try:
        page.get_by_role("button", name="Global Search (ctrl+k)").click()
        page.wait_for_timeout(400)
    except Exception:
        pass
    if is_closed():
        return

    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
    except Exception:
        pass
    
    
def dismiss_error_toast(page: Page, timeout: int = 1500) -> bool:
    alert = page.get_by_role("alert")
    if alert.count() == 0:
        return False
    try:
        alert.locator("button").first.click(timeout=timeout)
    except Exception:
        page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    return True

def do_global_search(page: Page, *, search_term: str) -> None:
    page.get_by_role("button", name="Global Search (ctrl+k)").click()
    search_box = page.get_by_role("textbox", name="Search modules...")
    try:
        search_box.wait_for(state="visible", timeout=5000)
        search_box.fill(search_term)
        search_box.press("Enter")
        page.get_by_role("button", name=search_term).wait_for(state="visible", timeout=5000)
        page.get_by_role("button", name=search_term).click()
        page.wait_for_load_state("networkidle")
    except Exception:
        _force_close_search_modal(page)
        raise


def sheet_name_from_input(input_sheet: str) -> str:
    if input_sheet and input_sheet.startswith("/"):
        return input_sheet[1:]
    return input_sheet


def open_followup(page: Page, account_id: str) -> None:
    do_global_search(page, search_term="List View")
    search_box = page.get_by_role("textbox", name="Search accounts...")
    search_box.click()
    search_box.fill(account_id)
    page.get_by_role("button", name="Search", exact=True).click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name=account_id).click()
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name="Collection").click()
    page.get_by_role("menuitem", name="Follow Up").click()
    page.wait_for_timeout(1000)


def select_result_code(page: Page, result_code: str) -> None:
    dropdown = page.get_by_role("combobox", name="Result")
    dropdown.click()
    page.wait_for_timeout(300)
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    page.wait_for_timeout(500)
    dropdown.fill(result_code)
    page.wait_for_timeout(2000)

    for strategy in [
        lambda: page.get_by_role("option", name=result_code, exact=True).first,
        lambda: page.locator('[role="listbox"]').get_by_text(result_code, exact=True).first,
        lambda: page.get_by_role("option", name=result_code).first,
    ]:
        try:
            el = strategy()
            el.wait_for(state="visible", timeout=2000)
            el.click()
            break
        except Exception:
            continue
    else:
        raise RuntimeError(f"Result Code '{result_code}' not found in dropdown")

    page.wait_for_timeout(1000)
    actual = dropdown.input_value()
    if actual.strip().upper() != result_code.upper():
        raise RuntimeError(f"Dropdown mismatch — Expected: {result_code}, Got: {actual}")


def click_save(page: Page) -> None:
    action_menu = page.get_by_role("button", name="Action Menu")
    action_menu.click()
    page.wait_for_timeout(1000)
    save_btn = page.get_by_role("menuitem", name="Save")
    try:
        save_btn.wait_for(state="visible", timeout=3000)
    except Exception:
        action_menu.click()
        page.wait_for_timeout(1000)
        save_btn.wait_for(state="visible", timeout=5000)
    save_btn.click(force=True)


def execute_result(page: Page, network: NetworkCapture, result_code: str) -> tuple[str, str]:
    network.clear()

    try:
        select_result_code(page, result_code)
    except Exception as dropdown_err:
        return "DROPDOWN_ERROR", str(dropdown_err)

    try:
        with page.expect_response(lambda r: "updateFollowup" in r.url, timeout=30000) as info:
            click_save(page)
        response = info.value
        try:
            rj = response.json()
            output = rj.get("message") or rj.get("error") or str(rj)
        except Exception:
            output = response.text() or "(empty body)"
        return str(response.status), output
    except Exception as wait_err:
        page.wait_for_timeout(3000)
        fallback = (network.get_api_response("updateFollowup") or network.get_api_response("followup")
                    or network.get_api_response("earlyCollections") or network.get_last_error_response())
        if fallback:
            try:
                rj = json.loads(fallback["body"])
                output = rj.get("message") or rj.get("error") or fallback["body"]
            except Exception:
                output = fallback["body"] or str(wait_err)
            return str(fallback["status"]), output
        return "5xx", str(wait_err)