from playwright.sync_api import Page
from framework.excel import ExcelManager
from framework.session import Session
from framework import report
from modules.common import sheet_name_from_input


def run(*, page: Page, excel: ExcelManager, output_excel: ExcelManager, input_sheet: str) -> None:
    sheet_name = sheet_name_from_input(input_sheet)
    rows = excel.read_sheet_as_dicts(sheet_name)
    if not rows:
        raise RuntimeError(f"No data found in '{sheet_name}' sheet")

    row = rows[0]
    organization = str(row.get("Tenant") or row.get("Tenat") or "").strip()
    username = str(row.get("UserName") or "").strip()
    password = str(row.get("Password") or "").strip()

    if not organization or not username or not password:
        raise RuntimeError(
            f"'{sheet_name}' sheet is missing required values — "
            f"Tenant='{organization}', UserName='{username}', "
            f"Password={'set' if password else 'MISSING'}"
        )

    logged_in, detail = Session.login(page, organization=organization, username=username, password=password)

    for idx, _ in enumerate(rows, start=2):
        report.record_sheet_row_result(
            output_excel, sheet_name, idx,
            actual=detail,
            status="✅ PASSED" if logged_in else "❌ FAILED",
        )

    if not logged_in:
        raise RuntimeError(f"Login failed for tenant '{organization}', user '{username}': {detail}")