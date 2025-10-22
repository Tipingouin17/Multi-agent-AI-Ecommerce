@echo off
REM Kafka Connectivity Verification Script for Windows

echo.
echo ================================================================================
echo   Kafka Connectivity Verification
echo ================================================================================
echo.

REM Change to project root directory
cd /d "%~dp0\.."

REM Run the verification script
python scripts\verify_kafka_connectivity.py

echo.
echo ================================================================================
echo   Verification Complete
echo ================================================================================
echo.
pause

