@echo off
cd /d "%~dp0"
poetry run streamlit run streamlit_app.py
pause
