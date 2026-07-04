from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from config.settings import (
    HEADLESS,
    BROWSER,
    BROWSER_LAUNCH_ARGS,
    DEFAULT_TIMEOUT_MS,
)


class BrowserManager:
    def __init__(self):
        self._playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def launch(self) -> Page:
        self._playwright = sync_playwright().start()

        browser_map = {
            "chromium": self._playwright.chromium,
            "firefox": self._playwright.firefox,
            "webkit": self._playwright.webkit,
        }

        browser_type = browser_map.get(BROWSER)

        if browser_type is None:
            raise ValueError(
                f"Unsupported browser '{BROWSER}'. "
                "Supported: chromium, firefox, webkit"
            )

        # Firefox/WebKit don't support Chromium launch args
        launch_args = (
            BROWSER_LAUNCH_ARGS if BROWSER == "chromium" else []
        )

        self.browser = browser_type.launch(
            headless=HEADLESS,
            args=launch_args,
        )

        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.set_default_timeout(DEFAULT_TIMEOUT_MS)

        return self.page

    def close(self) -> None:
        if self.context:
            self.context.close()

        if self.browser:
            self.browser.close()

        if self._playwright:
            self._playwright.stop()