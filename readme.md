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
