@echo off
REM Run TC-Python scripts on OSU lab machine
REM Usage: run_on_lab.bat script_name.py

SET TC_PYTHON="C:\Program Files\Thermo-Calc\2025b\python\python.exe"
SET SCRIPT=%1

IF "%SCRIPT%"=="" (
    echo Usage: run_on_lab.bat script_name.py
    echo.
    echo Available scripts:
    dir /B *.py
    exit /b 1
)

echo Running %SCRIPT% with TC-Python...
echo.
%TC_PYTHON% %SCRIPT%
echo.
echo Done. Don't forget to: git add ../data/tcpython ^&^& git commit -m "TC output" ^&^& git push
