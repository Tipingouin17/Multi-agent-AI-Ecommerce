@echo off
REM Dependency Checker and Installer (Batch version)

echo ============================================================
echo Python Dependency Checker
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

echo ============================================================
echo Checking Critical Packages
echo ============================================================
echo.

REM Test critical packages
set MISSING=0

echo Checking fastapi...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo   [X] Missing: fastapi
    set MISSING=1
) else (
    echo   [OK] Installed: fastapi
)

echo Checking uvicorn...
python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo   [X] Missing: uvicorn
    set MISSING=1
) else (
    echo   [OK] Installed: uvicorn
)

echo Checking pydantic...
python -c "import pydantic" >nul 2>&1
if errorlevel 1 (
    echo   [X] Missing: pydantic
    set MISSING=1
) else (
    echo   [OK] Installed: pydantic
)

echo Checking sqlalchemy...
python -c "import sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo   [X] Missing: sqlalchemy
    set MISSING=1
) else (
    echo   [OK] Installed: sqlalchemy
)

echo Checking openai...
python -c "import openai" >nul 2>&1
if errorlevel 1 (
    echo   [X] Missing: openai
    set MISSING=1
) else (
    echo   [OK] Installed: openai
)

echo Checking numpy...
python -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo   [X] Missing: numpy
    set MISSING=1
) else (
    echo   [OK] Installed: numpy
)

echo.

if %MISSING%==1 (
    echo ============================================================
    echo Installing Dependencies
    echo ============================================================
    echo.
    echo Installing from requirements.txt...
    echo.
    
    pip install -r requirements.txt
    
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies
        echo.
        echo Try running manually:
        echo   venv\Scripts\activate.bat
        echo   pip install -r requirements.txt
        pause
        exit /b 1
    )
    
    echo.
    echo [OK] All dependencies installed
) else (
    echo [OK] All required packages are installed
)

echo.
echo ============================================================
echo Dependency Check Complete
echo ============================================================
echo.
echo You can now start the system:
echo   start-system.bat
echo.
pause

