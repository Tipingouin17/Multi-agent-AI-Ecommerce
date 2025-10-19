# Dependency Checker and Installer
# Checks if all required Python packages are installed and installs them if missing

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

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

function Test-PythonPackage {
    param([string]$Package)
    
    $result = python -c "import $Package" 2>&1
    return $LASTEXITCODE -eq 0
}

Write-Step "Python Dependency Checker"

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
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

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Gray
& ".\venv\Scripts\Activate.ps1"
Write-Success "Virtual environment activated"

# Check Python version
Write-Host ""
Write-Host "Checking Python version..." -ForegroundColor Gray
$pythonVersion = python --version 2>&1
Write-Host "  $pythonVersion" -ForegroundColor Gray

# Critical packages to check
$criticalPackages = @(
    "fastapi",
    "uvicorn",
    "pydantic",
    "sqlalchemy",
    "psycopg2",
    "aiokafka",
    "redis",
    "structlog",
    "openai",
    "numpy",
    "pandas"
)

Write-Step "Checking Critical Packages"

$missingPackages = @()
$installedPackages = @()

foreach ($package in $criticalPackages) {
    Write-Host "Checking $package... " -NoNewline -ForegroundColor Gray
    
    if (Test-PythonPackage $package) {
        Write-Host "[OK] Installed" -ForegroundColor Green
        $installedPackages += $package
    } else {
        Write-Host "[X] Missing" -ForegroundColor Red
        $missingPackages += $package
    }
}

Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Installed: $($installedPackages.Count)/$($criticalPackages.Count)" -ForegroundColor Green
Write-Host "  Missing: $($missingPackages.Count)/$($criticalPackages.Count)" -ForegroundColor $(if ($missingPackages.Count -gt 0) { "Red" } else { "Green" })

if ($missingPackages.Count -gt 0 -or $Force) {
    Write-Step "Installing Dependencies"
    
    if ($Force) {
        Write-Host "Force flag set - reinstalling all dependencies" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Running: pip install -r requirements.txt --force-reinstall" -ForegroundColor Gray
        pip install -r requirements.txt --force-reinstall
    } else {
        Write-Host "Installing missing packages from requirements.txt" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Running: pip install -r requirements.txt" -ForegroundColor Gray
        pip install -r requirements.txt
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Failure "Failed to install dependencies"
        Write-Host ""
        Write-Host "Try running manually:" -ForegroundColor Yellow
        Write-Host '  .\venv\Scripts\Activate.ps1'
        Write-Host '  pip install -r requirements.txt'
        exit 1
    }
    
    Write-Success "All dependencies installed"
    
    # Verify again
    Write-Step "Verifying Installation"
    
    $stillMissing = @()
    foreach ($package in $missingPackages) {
        Write-Host "Verifying $package... " -NoNewline -ForegroundColor Gray
        
        if (Test-PythonPackage $package) {
            Write-Host "[OK] OK" -ForegroundColor Green
        } else {
            Write-Host "[X] Still missing" -ForegroundColor Red
            $stillMissing += $package
        }
    }
    
    if ($stillMissing.Count -gt 0) {
        Write-Failure "Some packages still missing after installation"
        Write-Host ""
        Write-Host "Missing packages:" -ForegroundColor Red
        foreach ($pkg in $stillMissing) {
            Write-Host "  - $pkg" -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "Try installing manually:" -ForegroundColor Yellow
        foreach ($pkg in $stillMissing) {
            Write-Host "  pip install $pkg" -ForegroundColor Gray
        }
        exit 1
    }
    
    Write-Success "All packages verified successfully"
} else {
    Write-Success "All required packages are installed"
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "[OK] Dependency Check Complete" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "You can now start the system:" -ForegroundColor Cyan
Write-Host '  .\start-system.ps1' -ForegroundColor White
Write-Host ""

