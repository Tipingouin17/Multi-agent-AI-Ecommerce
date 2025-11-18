# Launch Platform with Ngrok for Remote Testing
# PowerShell script for better process management

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LAUNCH PLATFORM WITH NGROK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if ngrok is installed
$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokPath) {
    Write-Host "ERROR: ngrok not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install ngrok:"
    Write-Host "1. Download from: https://ngrok.com/download"
    Write-Host "2. Extract and add to PATH"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Step 1: Starting Backend Agents..." -ForegroundColor Yellow
Write-Host ""

# Start backend agents
Start-Process -FilePath "cmd.exe" -ArgumentList "/c StartAllAgents.bat" -NoNewWindow

Write-Host "Waiting for agents to start..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Step 2: Starting Frontend..." -ForegroundColor Yellow
Write-Host ""

# Start frontend
Set-Location multi-agent-dashboard
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run dev" -PassThru -NoNewWindow
Set-Location ..

Write-Host "Waiting for frontend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "Step 3: Starting Ngrok..." -ForegroundColor Yellow
Write-Host ""

# Start ngrok
$ngrokProcess = Start-Process -FilePath "ngrok" -ArgumentList "http 5173" -PassThru

Write-Host "Waiting for ngrok tunnel..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "PUBLIC URL" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Get ngrok URL
try {
    $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
    $publicUrl = $response.tunnels[0].public_url
    
    Write-Host "Your platform is now accessible at:" -ForegroundColor White
    Write-Host ""
    Write-Host "  $publicUrl" -ForegroundColor Green
    Write-Host ""
    Write-Host "Copy this URL and share it for testing!" -ForegroundColor Yellow
    Write-Host ""
    
    # Also save to file for easy copying
    $publicUrl | Out-File -FilePath "ngrok_url.txt" -Encoding UTF8
    Write-Host "URL also saved to: ngrok_url.txt" -ForegroundColor Gray
    
} catch {
    Write-Host "Could not retrieve ngrok URL automatically." -ForegroundColor Red
    Write-Host "Please check: http://localhost:4040" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SERVICES RUNNING" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "- Backend Agents: 37 agents on ports 8000-8036"
Write-Host "- Frontend: http://localhost:5173"
Write-Host "- Ngrok Dashboard: http://localhost:4040"
Write-Host "- Public URL: Check above or ngrok_url.txt"
Write-Host ""
Write-Host "To stop all services:" -ForegroundColor Yellow
Write-Host "1. Close this window (or press Ctrl+C)"
Write-Host "2. Run: StopAllAgents.bat"
Write-Host "3. Kill ngrok from Task Manager if needed"
Write-Host ""

# Keep window open
Write-Host "Press any key to stop all services..." -ForegroundColor Red
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Cleanup
Write-Host ""
Write-Host "Stopping services..." -ForegroundColor Yellow

if ($ngrokProcess -and !$ngrokProcess.HasExited) {
    Stop-Process -Id $ngrokProcess.Id -Force
    Write-Host "- Ngrok stopped" -ForegroundColor Gray
}

if ($frontendProcess -and !$frontendProcess.HasExited) {
    Stop-Process -Id $frontendProcess.Id -Force
    Write-Host "- Frontend stopped" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Don't forget to run: StopAllAgents.bat" -ForegroundColor Yellow
Write-Host ""
