# Amazon Ads Analyzer

Upload an Amazon Sponsored Products Targeting Report and get an interactive dashboard: spend/sales breakdown by keyword, ACOS vs. your target, and plain-language insights.

## Quick start

1. Install dependencies (only needed once):
   ```
   poetry install
   ```
2. Run the dashboard — either double-click **`run_dashboard.bat`** in File Explorer, or run this command yourself:
   ```
   poetry run streamlit run streamlit_app.py
   ```
3. Your browser opens automatically at `http://localhost:8501`. Upload a Targeting Report CSV in the sidebar and you're in.

To stop it, close the terminal/console window it opened (or press `Ctrl+C` inside it).

No test data on hand? Use `src/data/Targeting_Report_Demo_Sample.csv` to see the dashboard fully populated.

## Other commands

Run the API (separate from the dashboard, not required to use it):
```
poetry run uvicorn main:app --reload
```

Run the test suite:
```
poetry run pytest
```

## Project structure

See [CLAUDE.md](CLAUDE.md) for the codebase layout and conventions.
