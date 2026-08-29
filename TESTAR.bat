@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -3.12 -m venv .venv 2>nul || py -3.13 -m venv .venv 2>nul || py -3.11 -m venv .venv 2>nul || python -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade -r requirements-dev.txt
if errorlevel 1 goto :erro
set QT_QPA_PLATFORM=offscreen
python -m pytest -q
if errorlevel 1 goto :erro

echo.
echo Todos os testes passaram.
pause
exit /b 0

:erro
echo.
echo Algum teste falhou.
pause
exit /b 1
