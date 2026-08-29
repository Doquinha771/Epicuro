@echo off
setlocal
cd /d "%~dp0"
title Epicuro - Build do aplicativo

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Criando ambiente virtual...
    py -3.12 -m venv .venv 2>nul || py -3.13 -m venv .venv 2>nul || py -3.11 -m venv .venv 2>nul || python -m venv .venv
)

call ".venv\Scripts\activate.bat"
echo [2/4] Instalando dependencias do app...
python -m pip install --upgrade pip >nul
python -m pip install --upgrade -r requirements.txt pyinstaller
if errorlevel 1 goto :erro

echo [3/4] Limpando build anterior...
if exist build rmdir /s /q build
if exist dist\Epicuro rmdir /s /q dist\Epicuro

echo [4/4] Gerando Epicuro.exe sem console...
python -m PyInstaller --noconfirm --clean Epicuro.spec
if errorlevel 1 goto :erro

echo.
echo Build concluido.
echo O aplicativo esta em: dist\Epicuro\Epicuro.exe
echo Esse EXE usa subsistema de janela: nenhum terminal abre junto com o app.
explorer "dist\Epicuro"
exit /b 0

:erro
echo.
echo Falha ao gerar o aplicativo. Veja o erro acima.
pause
exit /b 1
