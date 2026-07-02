import os
from playwright.sync_api import Page
from config.settings import SCREENSHOT_DIR


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in str(name))


def clear_screenshot_dir() -> None:
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    for filename in os.listdir(SCREENSHOT_DIR):
        file_path = os.path.join(SCREENSHOT_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
        except Exception as cleanup_err:
            print(f"[screenshot] could not remove '{file_path}': {cleanup_err}")


def capture(page: Page, *labels: str) -> str:
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    key = "_".join(_safe(label) for label in labels if label)
    path = os.path.join(SCREENSHOT_DIR, f"{key}.png")

    if os.path.exists(path):
        os.remove(path)

    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        try:
            page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass

    page.screenshot(path=path, full_page=True)
    return path