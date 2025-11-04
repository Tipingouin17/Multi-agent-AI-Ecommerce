@echo off
setlocal enabledelayedexpansion
REM ============================================================================
REM Start Dashboard - Windows Version
REM ============================================================================

echo ================================================================================
echo Multi-Agent E-commerce Dashboard - Startup Script (Windows)
echo ================================================================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Node.js is not installed
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

set NODE_VERSION=
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js installed: %NODE_VERSION%
echo.

REM Check for package manager
set PACKAGE_MANAGER=
set PM_VERSION=

where pnpm >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    set PACKAGE_MANAGER=pnpm
    for /f "tokens=*" %%i in ('pnpm --version') do set PM_VERSION=%%i
    echo [OK] pnpm installed: !PM_VERSION!
    goto pm_found
)

where npm >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    set PACKAGE_MANAGER=npm
    for /f "tokens=*" %%i in ('npm --version') do set PM_VERSION=%%i
    echo [OK] npm installed: !PM_VERSION!
    goto pm_found
)

echo [ERROR] No package manager found (npm or pnpm)
pause
exit /b 1

:pm_found
echo Using package manager: !PACKAGE_MANAGER!
echo.

REM Show current directory
echo Current directory: %CD%
echo.

REM Navigate to dashboard directory
echo [INFO] Navigating to dashboard directory...
if not exist multi-agent-dashboard (
    echo [ERROR] Dashboard directory 'multi-agent-dashboard' not found
    echo [ERROR] Current directory: %CD%
    echo [ERROR] Please ensure you're running this script from the project root
    pause
    exit /b 1
)

cd multi-agent-dashboard
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Failed to navigate to dashboard directory
    pause
    exit /b 1
)

echo [OK] In dashboard directory: %CD%
echo.

REM Install dependencies if needed
if not exist node_modules (
    echo [WARNING] node_modules not found, installing dependencies...
    echo.
    goto install_deps
)

REM Verify vite is installed
if not exist node_modules\.bin\vite.cmd (
    echo [WARNING] Vite not found in node_modules, reinstalling dependencies...
    echo.
    goto install_deps
)

echo [OK] Dependencies already installed
goto deps_done

:install_deps
if "!PACKAGE_MANAGER!"=="pnpm" (
    pnpm install
) else (
    npm install --legacy-peer-deps
)

if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Dependency installation failed
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies installed successfully

:deps_done

echo.

REM Create .env file if it doesn't exist
if not exist .env (
    echo [WARNING] .env file not found, creating default configuration...
    
    (
        echo # Multi-Agent Dashboard Configuration
        echo.
        echo # API Configuration
        echo VITE_API_URL=http://localhost:8000
        echo VITE_WS_URL=ws://localhost:8015/ws
        echo.
        echo # Development Tools
        echo VITE_ENABLE_DEVTOOLS=true
    ) > .env
    
    echo [OK] Created .env file with default configuration
) else (
    echo [OK] .env file already exists
)

echo.

REM Check if agents are running
echo Checking agent connectivity...
echo.

curl -s -f http://localhost:8000/health >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    echo [OK] Primary API ^(order_agent^) is running on port 8000
) else (
    echo [WARNING] Primary API ^(order_agent^) is not responding on port 8000
    echo [WARNING] The dashboard will start but may not function correctly.
    echo [WARNING] Please start agents first: start_all_26_agents.bat
)

curl -s -f http://localhost:8015/health >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    echo [OK] WebSocket API ^(transport_agent^) is running on port 8015
) else (
    echo [WARNING] WebSocket API ^(transport_agent^) is not responding on port 8015
    echo [WARNING] Real-time features may not work.
)

echo.

REM Start the dashboard
echo Starting dashboard...
echo.
echo Dashboard will be available at: http://localhost:5173
echo Press Ctrl+C to stop the dashboard
echo.
echo ================================================================================
echo.

if "!PACKAGE_MANAGER!"=="pnpm" (
    pnpm run dev
) else (
    npm run dev
)

