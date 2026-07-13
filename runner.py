from framework.session import Session
from framework.excel import ExcelManager
from framework.executor import run_scenario
from framework.screenshot import clear_screenshot_dir
from framework.output_manager import get_output_path
from config.settings import INPUT_EXCEL_PATH


def main() -> None:
    clear_screenshot_dir()

    input_excel = ExcelManager(INPUT_EXCEL_PATH)     # read-only: scenario + module data
    output_excel = ExcelManager(get_output_path())   # results get written/saved here

    session = Session()
    page = session.start()

    try:
        summary = run_scenario(page, input_excel, output_excel)
        print(f"Run complete: {summary['passed']}/{summary['total']} steps passed.")
        if summary["failed"]:
            raise SystemExit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()