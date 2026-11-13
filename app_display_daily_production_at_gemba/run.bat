@echo off
cd /d "%~dp0"

start "Dashboard" cmd /k "..\.venv\Scripts\python.exe main.py"
start "PLC Data Collector" cmd /k "..\.venv\Scripts\python.exe insert_prod_data_from_plc.py"
