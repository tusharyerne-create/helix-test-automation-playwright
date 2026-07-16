# Playwright + Excel Test Automation Framework

A Python/Playwright UI test runner for the DRS web app.

## Requirements

- Python 3.9+
- Google Chrome / Chromium (installed via Playwright)

## Project Structure

```
config/
      #enviroment config
framework/
      #other config(screenshot, excel,etc)
modules/
       #page script
test-data/
  PythonTest.xlsx      # the one workbook: scenario + all input/output sheets
screenshots/            # failure screenshots, cleared/populated per run
```

## Setup

```bash
(
- python -m venv venv
- .\venv\Scripts\Activate. ) -> Optional but best practice to make separate profile for testing virtually

-- Mandatory
pip install -r requirements.txt
playwright install firefox
```

## Configuration

Create a `.env` file in the project root:

```dotenv
URL=http://10.165.100.49:9010
HEADLESS=true (false if you want to see running test visible)
```

Login credentials come from the **`login`** sheet in `test-data/PythonTest.xlsx`:

| Tenant | UserName | Password |
| ------ | -------- | -------- |
| KBANK  | ADMIN    | 12345    |

## Run in terminal with project directory

```bash
python runner.py
```

### Run a selected scenario or every scenario

`config/settings.py` contains the default selection:

```python
RUN_MODE = "single"       # "single" or "all"
SCENARIO_NAME = "Scenario2"  # used when RUN_MODE is "single"
```

You can also select the run from the command line:

```powershell
# Run only one workbook
python runner.py --scenario Scenario1

# Run Scenario1, Scenario2, and every matching input workbook in test-data
python runner.py --all
```

Each scenario creates its own output workbook. The runner starts a fresh browser session for each scenario.
