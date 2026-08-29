@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Epicuro 2.0.1 - Build otimizado

if not exist ".venv\Scripts\python.exe" (
    echo [1/6] Criando ambiente de build...
    py -3.12 -m venv .venv 2>nul || py -3.11 -m venv .venv 2>nul || py -3.13 -m venv .venv 2>nul || python -m venv .venv
    if errorlevel 1 goto :erro
) else (
    echo [1/6] Ambiente de build encontrado.
)

call ".venv\Scripts\activate.bat"
echo [2/6] Instalando dependencias necessarias...
python -m pip install --disable-pip-version-check --upgrade pip >nul
python -m pip install --disable-pip-version-check --upgrade -r requirements-build.txt
if errorlevel 1 goto :erro

echo [3/6] Limpando build anterior...
if exist build rmdir /s /q build
if exist dist\Epicuro rmdir /s /q dist\Epicuro

echo [4/6] Gerando Epicuro.exe sem console...
python -m PyInstaller --noconfirm --clean Epicuro.spec
if errorlevel 1 goto :erro

if not exist "dist\Epicuro\Epicuro.exe" goto :erro

echo [5/6] Testando o executavel congelado...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Start-Process -FilePath '%CD%\dist\Epicuro\Epicuro.exe' -ArgumentList '--self-test' -PassThru -Wait -WindowStyle Hidden; exit $p.ExitCode"
if errorlevel 1 (
    echo O auto-teste do executavel falhou.
    goto :erro
)

echo [6/6] Calculando tamanho final...
powershell -NoProfile -Command "$s=(Get-ChildItem -LiteralPath '%CD%\dist\Epicuro' -Recurse -File | Measure-Object Length -Sum).Sum; $mb=[math]::Round($s/1MB,1); Write-Host ('Tamanho instalado: ' + $mb + ' MB')"

echo.
echo Build concluido: dist\Epicuro\Epicuro.exe
echo O executavel nao abre terminal.
if /I not "%~1"=="--no-open" explorer "dist\Epicuro"
exit /b 0

:erro
echo.
echo Falha ao gerar o Epicuro 2.0.1.
pause
exit /b 1
