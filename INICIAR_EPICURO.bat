@echo off
setlocal
cd /d "%~dp0"
title Epicuro - Preparacao

if not exist ".venv\Scripts\python.exe" goto :create

rem Verifica dependencias sem importar pacotes pesados nem rodar pip em todo inicio.
".venv\Scripts\python.exe" -c "import importlib.util as u,sys; mods=('PySide6','yt_dlp','imageio_ffmpeg','spotdl','pkg_resources'); sys.exit(0 if all(u.find_spec(m) for m in mods) else 1)" >nul 2>&1
if errorlevel 1 goto :install
goto :start

:create
echo [Epicuro] Primeira execucao: preparando o ambiente...
py -3.12 -m venv .venv 2>nul || py -3.13 -m venv .venv 2>nul || py -3.11 -m venv .venv 2>nul || python -m venv .venv
if errorlevel 1 goto :erro

:install
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul
python -m pip install --upgrade -r requirements.txt
if errorlevel 1 goto :erro

:start
rem pythonw deixa somente a janela do aplicativo. O CMD termina imediatamente.
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0

:erro
echo.
echo Nao foi possivel preparar o Epicuro.
pause
exit /b 1
