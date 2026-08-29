@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Epicuro 2.0.1 - Release portatil

call GERAR_EXE.bat --no-open
if errorlevel 1 exit /b 1
if not exist release mkdir release
if exist "release\Epicuro-2.0.1-Portable.zip" del /q "release\Epicuro-2.0.1-Portable.zip"

echo Compactando release portatil...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%CD%\dist\Epicuro\*' -DestinationPath '%CD%\release\Epicuro-2.0.1-Portable.zip' -CompressionLevel Optimal -Force"
if errorlevel 1 goto :erro
powershell -NoProfile -Command "$f=Get-Item '%CD%\release\Epicuro-2.0.1-Portable.zip'; Write-Host ('Release: ' + [math]::Round($f.Length/1MB,1) + ' MB')"
explorer "release"
exit /b 0

:erro
echo Falha ao compactar a release portatil.
pause
exit /b 1
