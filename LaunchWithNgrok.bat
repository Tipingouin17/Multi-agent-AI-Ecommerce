@echo off
REM Launch Platform with Ngrok for Remote Testing
REM This script starts the platform and exposes it via ngrok

echo ========================================
echo LAUNCH PLATFORM WITH NGROK
echo ========================================
echo.
echo This will:
echo 1. Start all backend agents
echo 2. Start the frontend dev server
echo 3. Expose the platform via ngrok
echo 4. Display the public URL
echo.

REM Check if ngrok is installed
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ========================================
    echo ERROR: ngrok not found!
    echo ========================================
    echo.
    echo Please install ngrok:
    echo 1. Download from: https://ngrok.com/download
    echo 2. Extract ngrok.exe to a folder
    echo 3. Add that folder to your PATH
    echo.
    echo OR place ngrok.exe in this directory
    echo.
    pause
    exit /b 1
)

echo ========================================
echo STEP 1: Starting Backend Agents
echo ========================================
echo.

REM Start all agents
call StartAllAgents.bat

echo.
echo ========================================
echo STEP 2: Starting Frontend
echo ========================================
echo.

REM Navigate to dashboard directory
cd multi-agent-dashboard

REM Start frontend in background
start /B cmd /c "npm run dev > ..\logs\frontend.log 2>&1"

echo Frontend starting... (check logs\frontend.log for details)
echo Waiting 10 seconds for frontend to initialize...
timeout /t 10 /nobreak >nul

cd ..

echo.
echo ========================================
echo STEP 3: Starting Ngrok
echo ========================================
echo.

REM Start ngrok in background and capture output
start /B cmd /c "ngrok http 5173 --log=stdout > logs\ngrok.log 2>&1"

echo Ngrok starting... waiting for tunnel to establish...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo PUBLIC URL
echo ========================================
echo.

REM Try to get the ngrok URL from the API
curl -s http://localhost:4040/api/tunnels > logs\ngrok_tunnels.json 2>nul

REM Use PowerShell to parse JSON and extract URL
powershell -Command "$json = Get-Content logs\ngrok_tunnels.json | ConvertFrom-Json; $url = $json.tunnels[0].public_url; Write-Host ''; Write-Host 'Your platform is now accessible at:'; Write-Host ''; Write-Host $url -ForegroundColor Green; Write-Host ''; Write-Host 'Copy this URL and share it for testing!'; Write-Host ''; Write-Host 'Press Ctrl+C to stop all services'; Write-Host ''"

echo.
echo ========================================
echo SERVICES RUNNING
echo ========================================
echo.
echo - Backend Agents: 37 agents on ports 8000-8036
echo - Frontend: http://localhost:5173
echo - Ngrok Dashboard: http://localhost:4040
echo.
echo To stop all services:
echo 1. Press Ctrl+C
echo 2. Run: StopAllAgents.bat
echo 3. Kill ngrok process
echo.

REM Keep window open
pause
