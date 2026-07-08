from framework.session import Session
from framework.excel import ExcelManager
from framework.executor import run_scenario
from framework.screenshot import clear_screenshot_dir


def main() -> None:
    clear_screenshot_dir()
    excel = ExcelManager()
    session = Session()
    page = session.start()


    try:
        summary = run_scenario(page, excel)
        print(f"Run complete: {summary['passed']}/{summary['total']} steps passed.")
        if summary["failed"]:
            raise SystemExit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()