"""
settings.py
Owns: tunable constants only (timeouts, headless flag, dirs). No logic here.
"""
import os
from config.environment import BASE_DIR

HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
DEFAULT_TIMEOUT_MS = 30_000
NETWORK_IDLE_TIMEOUT_MS = 15_000
SHORT_WAIT_MS = 1_000

TEST_DATA_DIR = os.path.join(BASE_DIR, "test-data")
INPUT_EXCEL_PATH = os.path.join(TEST_DATA_DIR, "PythonTest.xlsx")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

BROWSER_LAUNCH_ARGS = [
    "--disable-features=AutofillServerCommunication",
    "--disable-save-password-bubble",
    "--disable-password-generation",
    "--disable-notifications",
]
