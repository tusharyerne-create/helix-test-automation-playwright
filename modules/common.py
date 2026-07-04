import json
from playwright.sync_api import Page
from framework.network import NetworkCapture
from playwright.sync_api import expect


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
    # Open Global Search
    page.get_by_role("button", name="Global Search (ctrl+k)").click()

    search_box = page.get_by_role("textbox", name="Search modules...")
    expect(search_box).to_be_visible(timeout=10000)

    # Clear existing text
    search_box.click()
    search_box.press("Control+A")
    search_box.press("Backspace")

    # Search
    search_box.fill(search_term)

    # Wait for results
    page.wait_for_timeout(1500)

    matches = page.get_by_role("button", name=search_term)

    if matches.count() == 0:
        raise RuntimeError(f"No search results found for '{search_term}'")

    for i in range(matches.count()):
        btn = matches.nth(i)

        if not btn.is_visible():
            continue

        try:
            btn.scroll_into_view_if_needed()
            btn.click(timeout=5000)

            # Wait for navigation/UI update
            page.wait_for_timeout(2500)

            # Search popup should disappear if module opened
            if search_box.count() == 0 or not search_box.first.is_visible():
                return

            # OR List View page loaded
            if page.get_by_role("textbox", name="Search accounts...").count() > 0:
                return

        except Exception as e:
            pass

    raise RuntimeError(
        f"Could not open '{search_term}'. "
        "Global Search results were found but none opened the page."
    )


def sheet_name_from_input(input_sheet: str) -> str:
    if input_sheet and input_sheet.startswith("/"):
        return input_sheet[1:]
    return input_sheet



def open_followup(page: Page, account_id: str) -> None:
    # Open List View
    do_global_search(page, search_term="List View")

    # Search Account
    search_box = page.get_by_role("textbox", name="Search accounts...")
    search_box.wait_for(state="visible", timeout=10000)
    search_box.click()
    search_box.fill(account_id)
    search_box.press("Enter")

    page.wait_for_timeout(1000)

    # Click Search
    search_btn = page.get_by_role("button", name="Search", exact=True)
    search_btn.wait_for(state="visible", timeout=5000)
    search_btn.click(force=True)

    page.wait_for_load_state("networkidle")

    ## Wait until search results are loaded
    page.wait_for_timeout(2000)

    account = page.get_by_text(account_id, exact=True).first

    account.wait_for(state="visible", timeout=10000)

    account.scroll_into_view_if_needed()
    account.click(force=True)

    page.wait_for_load_state("networkidle")

    collection = page.get_by_role("button", name="Collection")

    collection.wait_for(state="visible", timeout=10000)

    collection.click()

    followup = page.get_by_role("menuitem", name="Follow Up")

    followup.wait_for(state="visible", timeout=5000)

    followup.click()

    page.wait_for_timeout(2000)

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