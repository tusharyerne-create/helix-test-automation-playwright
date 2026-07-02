from framework.session import Session
from framework.excel import ExcelManager
from framework.network import NetworkCapture
from framework.executor import run_scenario


def main() -> None:
    excel = ExcelManager()
    session = Session()
    page = session.start()
    network = NetworkCapture(page)

    try:
        summary = run_scenario(page, excel, network)
        print(f"Run complete: {summary['passed']}/{summary['total']} steps passed.")
        if summary["failed"]:
            raise SystemExit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()