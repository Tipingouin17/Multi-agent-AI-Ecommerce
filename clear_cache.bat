@echo off
echo Clearing Python cache...
del /s /q agents\__pycache__\*.pyc 2>nul
del /s /q shared\__pycache__\*.pyc 2>nul
del /s /q __pycache__\*.pyc 2>nul
rmdir /s /q agents\__pycache__ 2>nul
rmdir /s /q shared\__pycache__ 2>nul
rmdir /s /q __pycache__ 2>nul
echo Cache cleared successfully!
echo.
echo Now run: .\scripts\run_agent_tests.bat
pause
