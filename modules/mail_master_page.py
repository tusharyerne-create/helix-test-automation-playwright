from playwright.sync_api import Page, expect

from framework import report
from framework.excel import ExcelManager
from modules.common import click_save, do_global_search, sheet_name_from_input


MODULE_NAME = "Mail Master"


def _mail_combobox(page: Page):
    comboboxes = page.get_by_role("combobox")
    for index in range(comboboxes.count()):
        candidate = comboboxes.nth(index)
        if candidate.is_visible():
            return candidate
    raise RuntimeError("Mail Master selector was not visible")


def verify_selected_mail(page: Page, expected_mail_name: str) -> None:
    actual_mail_name = _mail_combobox(page).input_value().strip()
    if actual_mail_name.casefold() != expected_mail_name.casefold():
        raise RuntimeError(
            "Mail Code verification failed: "
            f"expected '{expected_mail_name}' from Excel, got '{actual_mail_name}' in the UI"
        )


def select_mail(page: Page, mail_name: str) -> None:
    combobox = _mail_combobox(page)
    combobox.click()
    combobox.fill(mail_name)

    option = page.get_by_role("option", name=mail_name, exact=True)
    if option.count() == 0:
        option = page.get_by_text(mail_name, exact=True)
    expect(option.first).to_be_visible(timeout=10_000)
    option.first.click()

    verify_selected_mail(page, mail_name)


def save_mail_selection(page: Page) -> str:
    # Use the exact shared save flow used by Follow Up and other modules.
    click_save(page)

    # The application's toast is the actual persistence acknowledgement.
    toast = page.get_by_role("alert").last
    expect(toast).to_be_visible(timeout=10_000)
    message = toast.inner_text().strip()
    if any(word in message.casefold() for word in ("error", "failed", "invalid", "unable")):
        raise RuntimeError(f"Mail Master save failed: {message}")
    return message or "Mail selection saved"


def execute_one(page: Page, mail_name: str) -> tuple[bool, str]:
    try:
        select_mail(page, mail_name)
        save_message = save_mail_selection(page)
        verify_selected_mail(page, mail_name)
        return True, f"{save_message}; verified Mail Code '{mail_name}' in the UI"
    except Exception as exc:
        return False, str(exc)


def run(*, page: Page, excel: ExcelManager, output_excel: ExcelManager, input_sheet: str) -> None:
    sheet_name = sheet_name_from_input(input_sheet)
    rows = excel.read_sheet_as_dicts(sheet_name)
    if not rows:
        raise RuntimeError(f"No data found in '{sheet_name}' sheet")

    do_global_search(page, search_term=MODULE_NAME)

    any_failed = False
    any_tested = False
    for idx, row in enumerate(rows, start=2):
        mail_name = str(row.get("MailName") or "").strip()
        if not mail_name:
            continue

        any_tested = True
        passed, actual = execute_one(page, mail_name)
        report.record_sheet_row_result(
            output_excel,
            sheet_name,
            idx,
            actual=actual,
            status="âœ… PASSED" if passed else "âŒ FAILED",
        )
        any_failed = any_failed or not passed

    if not any_tested:
        raise RuntimeError(f"No valid MailName rows found in '{sheet_name}'")
    if any_failed:
        raise RuntimeError(f"One or more mail selections failed in '{sheet_name}'")
