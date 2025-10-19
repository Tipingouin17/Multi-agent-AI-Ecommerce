#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test all critical fixes for the Multi-Agent E-commerce System
.DESCRIPTION
    This script verifies that all fixes are working correctly:
    1. Kafka version compatibility fix
    2. OpenAI API syntax updates
    3. Dashboard import resolution
.NOTES
    Run this after applying all fixes
#>

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
    Write-ColorOutput "ℹ $Message" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✓ $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "✗ $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠ $Message" "Yellow"
}

function Write-TestHeader {
    param([string]$Message)
    Write-Host ""
    Write-ColorOutput "═══════════════════════════════════════════════════════════" "Cyan"
    Write-ColorOutput " $Message" "Cyan"
    Write-ColorOutput "═══════════════════════════════════════════════════════════" "Cyan"
    Write-Host ""
}

# Banner
Write-Host ""
Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" "Cyan"
Write-ColorOutput "║   Multi-Agent System - Fix Verification Tests             ║" "Cyan"
Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" "Cyan"
Write-Host ""

$testResults = @{
    Passed = 0
    Failed = 0
    Warnings = 0
}

# Test 1: Verify Kafka API version fix in base_agent.py
Write-TestHeader "TEST 1: Kafka Version Compatibility Fix"

$baseAgentPath = "shared/base_agent.py"
if (Test-Path $baseAgentPath) {
    $content = Get-Content $baseAgentPath -Raw
    
    # Check for api_version in producer
    if ($content -match "AIOKafkaProducer\([^)]*api_version='auto'") {
        Write-Success "Kafka Producer has api_version='auto' parameter"
        $testResults.Passed++
    } else {
        Write-Error "Kafka Producer missing api_version parameter"
        $testResults.Failed++
    }
    
    # Check for api_version in consumer
    if ($content -match "AIOKafkaConsumer\([^)]*api_version='auto'") {
        Write-Success "Kafka Consumer has api_version='auto' parameter"
        $testResults.Passed++
    } else {
        Write-Error "Kafka Consumer missing api_version parameter"
        $testResults.Failed++
    }
} else {
    Write-Error "File not found: $baseAgentPath"
    $testResults.Failed += 2
}

# Test 2: Verify OpenAI helper exists
Write-TestHeader "TEST 2: OpenAI Helper Module"

$openaiHelperPath = "shared/openai_helper.py"
if (Test-Path $openaiHelperPath) {
    Write-Success "OpenAI helper module exists"
    $testResults.Passed++
    
    $helperContent = Get-Content $openaiHelperPath -Raw
    
    # Check for AsyncOpenAI import
    if ($helperContent -match "from openai import AsyncOpenAI") {
        Write-Success "Uses new AsyncOpenAI client"
        $testResults.Passed++
    } else {
        Write-Error "Missing AsyncOpenAI import"
        $testResults.Failed++
    }
    
    # Check for chat_completion function
    if ($helperContent -match "async def chat_completion") {
        Write-Success "chat_completion function defined"
        $testResults.Passed++
    } else {
        Write-Error "Missing chat_completion function"
        $testResults.Failed++
    }
} else {
    Write-Error "File not found: $openaiHelperPath"
    $testResults.Failed += 3
}

# Test 3: Verify all AI agents use new OpenAI syntax
Write-TestHeader "TEST 3: AI Agents OpenAI Integration"

$aiAgents = @(
    "agents/ai_monitoring_agent.py",
    "agents/carrier_selection_agent.py",
    "agents/customer_communication_agent.py",
    "agents/dynamic_pricing_agent.py",
    "agents/reverse_logistics_agent.py",
    "agents/risk_anomaly_detection_agent.py"
)

foreach ($agent in $aiAgents) {
    $agentName = Split-Path $agent -Leaf
    
    if (Test-Path $agent) {
        $agentContent = Get-Content $agent -Raw
        
        # Check for openai_helper import
        if ($agentContent -match "from shared\.openai_helper import") {
            Write-Success "$agentName: Uses openai_helper"
            $testResults.Passed++
        } else {
            Write-Error "$agentName: Missing openai_helper import"
            $testResults.Failed++
        }
        
        # Check for old syntax (should not exist)
        if ($agentContent -match "openai\.ChatCompletion\.acreate") {
            Write-Error "$agentName: Still uses old OpenAI syntax"
            $testResults.Failed++
        } else {
            Write-Success "$agentName: No old OpenAI syntax found"
            $testResults.Passed++
        }
    } else {
        Write-Error "File not found: $agent"
        $testResults.Failed += 2
    }
}

# Test 4: Verify dashboard structure
Write-TestHeader "TEST 4: Dashboard Configuration"

$dashboardFiles = @{
    "multi-agent-dashboard/vite.config.js" = "Vite configuration"
    "multi-agent-dashboard/src/lib/api.js" = "API service"
    "multi-agent-dashboard/package.json" = "Package configuration"
}

foreach ($file in $dashboardFiles.Keys) {
    if (Test-Path $file) {
        Write-Success "$($dashboardFiles[$file]): ✓"
        $testResults.Passed++
    } else {
        Write-Error "$($dashboardFiles[$file]): Missing"
        $testResults.Failed++
    }
}

# Check vite.config.js for path alias
$viteConfigPath = "multi-agent-dashboard/vite.config.js"
if (Test-Path $viteConfigPath) {
    $viteConfig = Get-Content $viteConfigPath -Raw
    
    if ($viteConfig -match '@":\s*path\.resolve') {
        Write-Success "Vite config has @ path alias"
        $testResults.Passed++
    } else {
        Write-Error "Vite config missing @ path alias"
        $testResults.Failed++
    }
}

# Test 5: Check Docker configuration
Write-TestHeader "TEST 5: Docker Configuration"

$dockerComposePath = "infrastructure/docker-compose.yml"
if (Test-Path $dockerComposePath) {
    Write-Success "Docker Compose file exists"
    $testResults.Passed++
    
    $dockerContent = Get-Content $dockerComposePath -Raw
    
    # Check for Kafka service
    if ($dockerContent -match "kafka:") {
        Write-Success "Kafka service configured"
        $testResults.Passed++
    } else {
        Write-Error "Kafka service not found"
        $testResults.Failed++
    }
    
    # Check for PostgreSQL service
    if ($dockerContent -match "postgres:") {
        Write-Success "PostgreSQL service configured"
        $testResults.Passed++
    } else {
        Write-Error "PostgreSQL service not found"
        $testResults.Failed++
    }
} else {
    Write-Error "File not found: $dockerComposePath"
    $testResults.Failed += 3
}

# Test 6: Check startup scripts
Write-TestHeader "TEST 6: Startup Scripts"

$startupScripts = @(
    "start-system.ps1",
    "start-dashboard.ps1",
    "verify-system.ps1"
)

foreach ($script in $startupScripts) {
    if (Test-Path $script) {
        Write-Success "$script exists"
        $testResults.Passed++
    } else {
        Write-Error "$script not found"
        $testResults.Failed++
    }
}

# Test 7: Check documentation
Write-TestHeader "TEST 7: Documentation"

$docs = @(
    "README.md",
    "CRITICAL_ISSUES_FIX.md",
    "DASHBOARD_FIX_GUIDE.md",
    "WINDOWS_LAUNCH_GUIDE.md"
)

foreach ($doc in $docs) {
    if (Test-Path $doc) {
        Write-Success "$doc exists"
        $testResults.Passed++
    } else {
        Write-Warning "$doc not found"
        $testResults.Warnings++
    }
}

# Summary
Write-Host ""
Write-ColorOutput "═══════════════════════════════════════════════════════════" "Cyan"
Write-ColorOutput " TEST SUMMARY" "Cyan"
Write-ColorOutput "═══════════════════════════════════════════════════════════" "Cyan"
Write-Host ""

$total = $testResults.Passed + $testResults.Failed
$successRate = if ($total -gt 0) { [math]::Round(($testResults.Passed / $total) * 100, 2) } else { 0 }

Write-ColorOutput "Total Tests: $total" "White"
Write-Success "Passed: $($testResults.Passed)"
Write-Error "Failed: $($testResults.Failed)"
Write-Warning "Warnings: $($testResults.Warnings)"
Write-Host ""
Write-ColorOutput "Success Rate: $successRate%" $(if ($successRate -ge 90) { "Green" } elseif ($successRate -ge 70) { "Yellow" } else { "Red" })
Write-Host ""

if ($testResults.Failed -eq 0) {
    Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" "Green"
    Write-ColorOutput "║   ✓ ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT        ║" "Green"
    Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" "Green"
    Write-Host ""
    Write-Info "Next steps:"
    Write-Host "  1. Start Docker services: docker-compose -f infrastructure/docker-compose.yml up -d"
    Write-Host "  2. Start agents: .\start-system.ps1"
    Write-Host "  3. Start dashboard: .\start-dashboard.ps1"
    exit 0
} else {
    Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" "Red"
    Write-ColorOutput "║   ✗ SOME TESTS FAILED - PLEASE REVIEW ERRORS ABOVE        ║" "Red"
    Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" "Red"
    exit 1
}

