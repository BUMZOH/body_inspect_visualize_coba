@echo off

REM run.batのフォルダへ移動
cd /d %~dp0

REM 親フォルダの .venv を使用
set PYTHON=..\.venv\Scripts\python.exe

if not exist "%PYTHON%" (
    echo ERROR: Python not found.
    echo Please create .venv in the project folder.
    pause
    exit /b 1
)

"%PYTHON%" main.py

pause