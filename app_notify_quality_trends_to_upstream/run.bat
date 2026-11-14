@echo off
cd /d "%~dp0"

start "Real Time Rreport" cmd /k "..\.venv\Scripts\python.exe create_realtime_report.py"
start "PLC Data Collector" cmd /k "..\.venv\Scripts\python.exe insert_csv_to_db.py"