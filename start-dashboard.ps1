#!/usr/bin/env pwsh
# Start the Multi-Agent E-commerce Dashboard
# Requires Node.js v18+ or v22+

param(
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"

# Color functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "INFO: $Message" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "SUCCESS: $Message" "Green"
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-ColorOutput "ERROR: $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "WARNING: $Message" "Yellow"
}

# Banner
Write-Host ""
Write-ColorOutput "============================================================" "Cyan"
Write-ColorOutput "   Multi-Agent E-commerce Dashboard Launcher" "Cyan"
Write-ColorOutput "============================================================" "Cyan"
Write-Host ""

# Check Node.js version
Write-Info "Checking Node.js version..."
try {
    $nodeVersion = node --version
    if ($nodeVersion) {
        Write-Success "Node.js version: $nodeVersion"
        
        # Extract major version number
        if ($nodeVersion -match 'v(\d+)\.') {
            $majorVersion = [int]$Matches[1]
            if ($majorVersion -lt 18) {
                Write-ErrorMsg "Node.js version $nodeVersion is not supported"
                Write-Warning "Please install Node.js v18, v20, or v22+"
                Write-Info "Download from: https://nodejs.org/"
                exit 1
            }
        }
    }
} catch {
    Write-ErrorMsg "Node.js is not installed"
    Write-Info "Download from: https://nodejs.org/"
    exit 1
}

# Change to dashboard directory
$dashboardDir = Join-Path $PSScriptRoot "multi-agent-dashboard"
if (-not (Test-Path $dashboardDir)) {
    Write-ErrorMsg "Dashboard directory not found: $dashboardDir"
    exit 1
}

Set-Location $dashboardDir
Write-Success "Changed to dashboard directory"

# Clean installation if requested
if ($Clean) {
    Write-Info "Performing clean installation..."
    
    if (Test-Path "node_modules") {
        Write-Info "Removing node_modules..."
        Remove-Item -Recurse -Force "node_modules"
    }
    
    if (Test-Path "package-lock.json") {
        Write-Info "Removing package-lock.json..."
        Remove-Item -Force "package-lock.json"
    }
    
    if (Test-Path ".vite") {
        Write-Info "Removing Vite cache..."
        Remove-Item -Recurse -Force ".vite"
    }
    
    Write-Info "Clearing npm cache..."
    npm cache clean --force
    
    Write-Success "Clean completed"
}

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Info "Installing dependencies..."
    npm install
    
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to install dependencies"
        exit 1
    }
    Write-Success "Dependencies installed"
} else {
    Write-Info "Dependencies already installed"
}

# Verify dashboard structure
Write-Info "Verifying dashboard structure..."
$requiredFiles = @(
    "src/lib/api.js",
    "src/App.jsx",
    "vite.config.js",
    "package.json"
)

$allFilesExist = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Success "Found: $file"
    } else {
        Write-ErrorMsg "Missing: $file"
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-ErrorMsg "Critical files are missing. Please check the dashboard structure."
    exit 1
}

# Check if backend agents are running
Write-Info "Checking if backend agents are running..."
$agentPorts = @(8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010, 8011, 8012, 8013, 8014)
$runningAgents = 0

foreach ($port in $agentPorts) {
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($connection.TcpTestSucceeded) {
            $runningAgents++
        }
    } catch {
        # Port not accessible
    }
}

if ($runningAgents -eq 0) {
    Write-Warning "No backend agents detected running"
    Write-Info "Dashboard will start but may not display data"
    Write-Info "Start agents first: .\start-system.ps1"
} else {
    Write-Success "Detected $runningAgents/$($agentPorts.Count) agents running"
}

# Start dashboard
Write-Host ""
Write-ColorOutput "============================================================" "Green"
Write-Success "Starting dashboard on http://localhost:5173"
Write-ColorOutput "============================================================" "Green"
Write-Host ""
Write-Info "Press Ctrl+C to stop the dashboard"
Write-Host ""

# Start Vite dev server
npm run dev
