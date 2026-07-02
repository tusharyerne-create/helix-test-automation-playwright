import re
from playwright.sync_api import Page
from framework.browser import BrowserManager
from config.environment import URL
from config.settings import SHORT_WAIT_MS


class Session:
    def __init__(self):
        self._browser_manager = BrowserManager()
        self._active_page: Page | None = None

    def start(self) -> Page:
        outer_page = self._browser_manager.launch()
        target_url = f"{URL}/drs/"
        popup = self._navigate_and_wait_for_popup(outer_page, target_url)
        self._active_page = popup
        return popup

    def _navigate_and_wait_for_popup(self, outer_page: Page, target_url: str, *, attempts: int = 2) -> Page:
        last_err = None

        for attempt in range(1, attempts + 1):
            print(f"[session] navigating outer page to: {target_url} (attempt {attempt}/{attempts})")
            try:
                with outer_page.expect_popup(timeout=30000) as popup_info:
                    response = outer_page.goto(target_url, wait_until="domcontentloaded")
                    print(f"[session] outer page goto status: "
                          f"{response.status if response else 'no response object'}")
            except Exception as popup_err:
                last_err = popup_err
                closed = outer_page.is_closed()
                print(f"[session] attempt {attempt} failed. outer_page.is_closed()={closed}. "
                      f"error: {popup_err}")

                if not closed:
                    try:
                        outer_page.screenshot(
                            path=f"debug_no_popup_outer_page_attempt{attempt}.png",
                            full_page=True,
                        )
                    except Exception:
                        pass

                if attempt < attempts:
                    try:
                        if outer_page.is_closed():
                            outer_page = self._browser_manager.context.new_page()
                    except Exception:
                        pass
                    continue

                raise RuntimeError(
                    f"No popup opened after navigating to '{target_url}' "
                    f"(tried {attempts} time(s)). "
                    f"outer_page.is_closed()={closed}. "
                    f"This often means a stale server-side session from a "
                    f"previous run that wasn't cleanly closed (check that "
                    f"session.close() runs in a finally block), or an "
                    f"orphaned browser process still holding a session. "
                    f"See debug_no_popup_outer_page_attempt*.png if available. "
                    f"Original error: {last_err}"
                )
            else:
                popup = popup_info.value
                outer_page.close()
                popup.goto(target_url, wait_until="domcontentloaded")
                return popup

        raise RuntimeError(f"Failed to obtain login popup: {last_err}")

    def get_active_page(self) -> Page:
        if self._active_page is None:
            raise RuntimeError("Session not started. Call session.start() first.")
        return self._active_page

    def close(self) -> None:
        self._browser_manager.close()

    @staticmethod
    def login(popup: Page, *, organization: str, username: str, password: str) -> tuple[bool, str]:
        popup.wait_for_load_state("domcontentloaded")

        already_on_credentials_screen = False
        try:
            existing_username_box = popup.get_by_role("textbox", name="Enter username").first
            already_on_credentials_screen = (
                existing_username_box.count() > 0 and existing_username_box.is_visible()
            )
        except Exception:
            already_on_credentials_screen = False

        if not already_on_credentials_screen:
            Session._select_organization(popup, organization)
            popup.get_by_role("button", name="Continue to Login").click()
            popup.wait_for_load_state("networkidle")

        username_box = popup.get_by_role("textbox", name="Enter username")
        password_box = popup.get_by_role("textbox", name="Enter password")

        Session._fill_verified(username_box, username, field_label="username")
        Session._fill_verified(password_box, password, field_label="password")

        final_user = username_box.input_value()
        final_pass = password_box.input_value()
        if final_user != username or final_pass != password:
            try:
                popup.screenshot(path="debug_pre_submit_mismatch.png", full_page=True)
            except Exception:
                pass
            return False, (
                f"Field values changed before submit — expected username "
                f"'{username}' but found '{final_user}'; password mismatch: "
                f"{final_pass != password}."
            )

        popup.get_by_role("button", name="Sign In").click()

        try:
            popup.wait_for_url(re.compile(r"^(?!.*login).*$", re.IGNORECASE), timeout=15000)
        except Exception:
            pass

        try:
            popup.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        popup.wait_for_timeout(SHORT_WAIT_MS * 5)

        succeeded, detail = Session._verify_login_success(popup)
        if not succeeded:
            try:
                popup.screenshot(path="./screenshots/debug_login_failure.png", full_page=True)
            except Exception:
                pass
        return succeeded, detail

    @staticmethod
    def _select_organization(popup: Page, organization: str) -> None:
        Session._open_org_dropdown(popup)
        Session._click_org_option(popup, organization)

    @staticmethod
    def _open_org_dropdown(popup: Page) -> None:
        trigger_strategies = [
            lambda: popup.get_by_role("combobox", name=re.compile("organization", re.IGNORECASE)).first,
            lambda: popup.get_by_role("button", name=re.compile("select an organization", re.IGNORECASE)).first,
            lambda: popup.get_by_text("Select an organization", exact=False).first,
        ]

        opened = False
        for strategy in trigger_strategies:
            try:
                trigger = strategy()
                trigger.wait_for(state="visible", timeout=5000)
                trigger.scroll_into_view_if_needed()
                trigger.click()
            except Exception:
                continue

            try:
                popup.locator('[role="listbox"], [role="option"]').first.wait_for(
                    state="visible", timeout=3000
                )
                opened = True
                break
            except Exception:
                continue

        if not opened:
            try:
                popup.screenshot(path="debug_org_dropdown_did_not_open.png", full_page=True)
            except Exception:
                pass
            raise RuntimeError(
                "Organization dropdown did not open after clicking the trigger "
                "(tried combobox role, button role, and plain text locators). "
                "See debug_org_dropdown_did_not_open.png for the on-screen state."
            )

    @staticmethod
    def _click_org_option(popup: Page, organization: str) -> None:
        strategies = [
            lambda: popup.get_by_role("option", name=organization).first,
            lambda: popup.locator('[role="listbox"]').get_by_text(organization, exact=False).first,
            lambda: popup.get_by_text(organization, exact=False).first,
            lambda: popup.get_by_role("option", name=organization, exact=True).first,
            lambda: popup.get_by_text(organization, exact=True).first,
        ]

        for strategy in strategies:
            try:
                option = strategy()
                option.wait_for(state="visible", timeout=10000)
                option.click()
                return
            except Exception:
                continue

        try:
            popup.screenshot(path="debug_org_selector_failure.png", full_page=True)
        except Exception:
            pass
        raise RuntimeError(
            f"Could not find organization '{organization}' in the dropdown. "
            f"Check the sheet's Tenant column for typos/whitespace — "
            f"note the on-screen label may be longer (e.g. 'KBANK - Kasikornbank' "
            f"vs a configured 'KBANK'), which is handled, but a genuine mismatch "
            f"or a closed/empty dropdown will still fail. "
            f"See debug_org_selector_failure.png for the on-screen state."
        )

    @staticmethod
    def _verify_login_success(popup: Page) -> tuple[bool, str]:
        try:
            error_locator = popup.locator(
                "text=/invalid|incorrect|failed to log|unable to log|login error|authentication failed/i"
            ).first
            if error_locator.count() > 0 and error_locator.is_visible():
                return False, f"Server error message shown: '{error_locator.inner_text().strip()}'"
        except Exception:
            pass

        try:
            username_box = popup.get_by_role("textbox", name="Enter username").first
            if username_box.count() > 0 and username_box.is_visible():
                return False, "Still on the login form (username field still visible) after Sign In."
        except Exception:
            pass

        try:
            popup.get_by_role("button", name="Global Search (ctrl+k)").first.wait_for(
                state="visible", timeout=8000
            )
            return True, "Global Search control is visible — logged in."
        except Exception:
            pass

        if not re.search(r".*login.*", popup.url, re.IGNORECASE):
            return True, "URL no longer contains 'login'."

        return False, f"Could not confirm a logged-in state. Current URL: {popup.url}"

    @staticmethod
    def _fill_verified(locator, value: str, *, field_label: str) -> None:
        locator.click()
        locator.press("Control+A")
        locator.press("Backspace")
        locator.press_sequentially(value, delay=50)
        locator.blur()

        actual = locator.input_value()
        if actual != value:
            locator.click()
            locator.press("Control+A")
            locator.press("Backspace")
            locator.press_sequentially(value, delay=50)
            locator.blur()
            actual = locator.input_value()

        if actual != value:
            raise RuntimeError(
                f"Could not reliably set the {field_label} field — "
                f"expected '{value}', got '{actual}'. Likely browser "
                f"autofill or framework state overwriting the value after fill()."
            )