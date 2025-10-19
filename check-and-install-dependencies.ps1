# Dependency Checker and Installer
# Checks if all required Python packages are installed and installs them if missing

param(
    [switch]$Force
)

$ErrorActionPreference = "Continue"

function Write-Step {
    param([string]$Text)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $Text
}

function Write-Failure {
    param([string]$Text)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Text
}

function Write-Warn {
    param([string]$Text)
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host $Text
}

Write-Step "Python Dependency Checker"

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Failure "Virtual environment not found!"
    Write-Host ""
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Failure "Failed to create virtual environment"
        exit 1
    }
    
    Write-Success "Virtual environment created"
}

# Use venv python directly instead of activating
$venvPython = ".\venv\Scripts\python.exe"
$venvPip = ".\venv\Scripts\pip.exe"

Write-Success "Using virtual environment Python"

# Check Python version
Write-Host ""
Write-Host "Checking Python version..." -ForegroundColor Gray
$pythonVersion = & $venvPython --version 2>&1
Write-Host "  $pythonVersion" -ForegroundColor Gray

Write-Step "Installing/Updating Dependencies"

Write-Host "Installing from requirements.txt..." -ForegroundColor Yellow
Write-Host ""

if ($Force) {
    Write-Host "Force reinstall mode" -ForegroundColor Yellow
    & $venvPip install -r requirements.txt --force-reinstall
} else {
    & $venvPip install -r requirements.txt
}

if ($LASTEXITCODE -ne 0) {
    Write-Failure "Failed to install dependencies"
    Write-Host ""
    Write-Host "Try running manually:" -ForegroundColor Yellow
    Write-Host '  .\venv\Scripts\Activate.ps1'
    Write-Host '  pip install -r requirements.txt'
    exit 1
}

Write-Success "Dependencies installed"

# Verify critical packages
Write-Step "Verifying Critical Packages"

$criticalPackages = @(
    "fastapi",
    "uvicorn",
    "pydantic",
    "sqlalchemy",
    "openai",
    "numpy"
)

$allOk = $true
foreach ($package in $criticalPackages) {
    Write-Host "Checking $package... " -NoNewline -ForegroundColor Gray
    
    $testResult = & $venvPython -c "import $package" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK]" -ForegroundColor Green
    } else {
        Write-Host "[MISSING]" -ForegroundColor Red
        $allOk = $false
    }
}

Write-Host ""

if (-not $allOk) {
    Write-Failure "Some packages are still missing"
    Write-Host ""
    Write-Host "Try installing manually:" -ForegroundColor Yellow
    Write-Host '  .\venv\Scripts\Activate.ps1'
    Write-Host '  pip install -r requirements.txt --force-reinstall'
    exit 1
}

Write-Host "============================================================" -ForegroundColor Green
Write-Host "[OK] All Dependencies Ready" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "You can now start the system:" -ForegroundColor Cyan
Write-Host '  .\start-system.ps1' -ForegroundColor White
Write-Host ""

