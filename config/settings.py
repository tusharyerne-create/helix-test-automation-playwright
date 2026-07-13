import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

URL = "http://10.165.100.49:9010"
HEADLESS = True
BROWSER = "firefox"

DEFAULT_TIMEOUT_MS = 30_000
NETWORK_IDLE_TIMEOUT_MS = 15_000
SHORT_WAIT_MS = 1_000

TEST_DATA_DIR = os.path.join(BASE_DIR, "test-data")
SCENARIO_NAME = "Scenario2"
INPUT_EXCEL_PATH = os.path.join(TEST_DATA_DIR, f"PythonTest_Input_{SCENARIO_NAME.lower()}.xlsx")

OUTPUT_DIR = os.path.join(TEST_DATA_DIR, "output")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

BROWSER_LAUNCH_ARGS = [
    "--disable-features=AutofillServerCommunication",
    "--disable-save-password-bubble",
    "--disable-password-generation",
    "--disable-notifications",
]