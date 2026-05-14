@echo off
title Betting Simulator - Disabilita sospensione
echo.
echo ============================================
echo  DISATTIVAZIONE SOSPENSIONE E IBERNAZIONE
echo ============================================
echo.
echo Serve eseguire come amministratore
echo.
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Richiedo privilegi di amministratore...
    powershell start-process "%~f0" -verb runas
    exit /b
)
echo.
echo Disattivo sospensione...
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
echo Disattivo ibernazione...
powercfg /h off
echo.
echo ✅ SOSPENSIONE E IBERNAZIONE DISATTIVATI!
echo Il PC restera' sempre acceso.
echo Premi un tasto per uscire.
pause >nul