@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Epicuro 2.0.1 - Preparacao

if not exist ".venv\Scripts\python.exe" goto :create

".venv\Scripts\python.exe" -c "import importlib.util as u,sys; mods=('PySide6','yt_dlp','imageio_ffmpeg','spotdl','pkg_resources'); sys.exit(0 if all(u.find_spec(m) for m in mods) else 1)" >nul 2>&1
if errorlevel 1 goto :install
goto :start

:create
echo [Epicuro] Preparando a primeira execucao...
py -3.12 -m venv .venv 2>nul || py -3.11 -m venv .venv 2>nul || py -3.13 -m venv .venv 2>nul || python -m venv .venv
if errorlevel 1 goto :erro

:install
call ".venv\Scripts\activate.bat"
python -m pip install --disable-pip-version-check --upgrade pip >nul
python -m pip install --disable-pip-version-check --upgrade -r requirements.txt
if errorlevel 1 goto :erro

:start
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0

:erro
echo.
echo Nao foi possivel preparar o Epicuro.
pause
exit /b 1
