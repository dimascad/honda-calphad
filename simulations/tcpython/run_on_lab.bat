@echo off
REM TC-Python runner for OSU lab machines
REM Usage: run_on_lab.bat [script_name]

set TC_PYTHON="C:\Program Files\Thermo-Calc\2025b\python\python.exe"

echo ============================================================
echo Honda CALPHAD - TC-Python Runner
echo ============================================================

REM Check for script argument
if "%1"=="" (
    echo.
    echo Available scripts:
    echo   1. check_databases.py       - Diagnostic: list databases/phases
    echo   2. extract_oxide_gibbs.py   - Extract oxide Gibbs energies
    echo   3. cu_al_o_phase_stability.py - Cu-Al-O phase diagram
    echo.
    echo Usage: run_on_lab.bat script_name.py
    echo Example: run_on_lab.bat check_databases.py
    echo.
    pause
    exit /b 0
)

echo Running: %1
echo.
%TC_PYTHON% %1

echo.
echo ============================================================
echo Script complete!
echo Output should be in: data\tcpython\raw\
echo.
echo To get results back to your Mac:
echo   Option A: Copy CSV files to USB/cloud drive
echo   Option B: If git works: git add . ^&^& git commit -m "TC output" ^&^& git push
echo ============================================================
pause
