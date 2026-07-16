import argparse
from pathlib import Path

from config.settings import RUN_MODE, SCENARIO_NAME, TEST_DATA_DIR
from framework.excel import ExcelManager
from framework.executor import run_scenario
from framework.output_manager import get_output_path
from framework.screenshot import clear_screenshot_dir
from framework.session import Session


INPUT_PREFIX = "PythonTest_Input_"


def _scenario_name_from_path(path: Path) -> str:
    return path.stem.removeprefix(INPUT_PREFIX)


def _available_input_files() -> list[Path]:
    return sorted(Path(TEST_DATA_DIR).glob(f"{INPUT_PREFIX}Scenario*.xlsx"))


def _find_input_file(scenario_name: str) -> Path:
    requested = scenario_name.strip().lower()
    for path in _available_input_files():
        if _scenario_name_from_path(path).lower() == requested:
            return path

    available = ", ".join(_scenario_name_from_path(path) for path in _available_input_files()) or "none"
    raise FileNotFoundError(
        f"No input workbook found for '{scenario_name}'. Available scenarios: {available}"
    )


def _run_workbook(input_path: Path) -> bool:
    scenario_name = _scenario_name_from_path(input_path)
    print(f"\n=== Running {scenario_name}: {input_path.name} ===")

    input_excel = ExcelManager(str(input_path))
    output_path = get_output_path(scenario_name, str(input_path))
    output_excel = ExcelManager(output_path)

    session = Session()
    page = session.start()
    try:
        summary = run_scenario(page, input_excel, output_excel, scenario_name=scenario_name)
    finally:
        session.close()

    print(
        f"{scenario_name} complete: {summary['passed']}/{summary['total']} steps passed. "
        f"Output: {output_path}"
    )
    return summary["failed"] == 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one or all PythonTest input workbooks."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all",
        action="store_true",
        help="Run every PythonTest_Input_Scenario*.xlsx workbook in test-data.",
    )
    group.add_argument(
        "--scenario",
        metavar="NAME",
        help="Run one scenario, for example: --scenario Scenario1",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.all or (not args.scenario and RUN_MODE.lower() == "all"):
        input_files = _available_input_files()
        if not input_files:
            raise FileNotFoundError(
                f"No PythonTest_Input_Scenario*.xlsx files found in {TEST_DATA_DIR}"
            )
    else:
        input_files = [_find_input_file(args.scenario or SCENARIO_NAME)]

    clear_screenshot_dir()
    failed_scenarios = [path for path in input_files if not _run_workbook(path)]


if __name__ == "__main__":
    main()
