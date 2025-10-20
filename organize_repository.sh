#!/bin/bash

################################################################################
# Repository Organization Script
# 
# This script moves historical/development documentation files into an 'old'
# folder to keep the repository root clean and organized.
#
# Files to keep in root:
#   - README.md (main documentation)
#   - COMPLETE_STARTUP_GUIDE.md (essential for users)
#   - DEPLOYMENT_GUIDE.md (essential for deployment)
#   - TESTING_GUIDE.md (essential for testing)
#   - CHANGELOG.md (version history)
#
# All other progress reports, fix guides, and implementation summaries
# will be moved to the 'old' folder.
################################################################################

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OLD_DIR="$PROJECT_ROOT/old"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Repository Organization Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create old directory if it doesn't exist
if [ ! -d "$OLD_DIR" ]; then
    echo -e "${YELLOW}Creating 'old' directory...${NC}"
    mkdir -p "$OLD_DIR"
    echo -e "${GREEN}✓ Directory created${NC}"
else
    echo -e "${YELLOW}'old' directory already exists${NC}"
fi

echo ""
echo -e "${BLUE}Moving historical documentation files...${NC}"
echo ""

# Array of files to move (historical/development documentation)
FILES_TO_MOVE=(
    "AGENT_IMPLEMENTATION_MASTER_PLAN.md"
    "AGENT_VERIFICATION_REPORT.md"
    "ALL_26_AGENTS_COMPLETE_FINAL_SUMMARY.md"
    "ALL_26_AGENTS_FINAL_STATUS.md"
    "BACKGROUND_WORK_PROGRESS.md"
    "COMPLETE_IMPROVEMENTS_SUMMARY.md"
    "COMPLETE_SYSTEM_FINAL_REPORT.md"
    "COMPLETE_SYSTEM_VERIFICATION.md"
    "COMPREHENSIVE_DELIVERY_SUMMARY.md"
    "CRITICAL_ISSUES_FIX.md"
    "DASHBOARD_FIX_GUIDE.md"
    "DESIGN_SYSTEM_REQUIREMENTS.md"
    "DOCKER_FIX_GUIDE.md"
    "FASTAPI_DEPRECATION_GUIDE.md"
    "FINAL_ALL_AGENTS_STATUS.md"
    "FINAL_BACKGROUND_WORK_COMPLETE.md"
    "FINAL_PROGRESS_SUMMARY.md"
    "FINAL_STATUS.md"
    "FIX_DEPENDENCIES.md"
    "FIX_VERIFICATION_REPORT.md"
    "IMPLEMENTATION_COMPLETE_SUMMARY.md"
    "IMPLEMENTATION_STATUS.md"
    "IMPORT_FIX_SUMMARY.md"
    "IMPROVEMENTS.md"
    "INFRASTRUCTURE_SETUP_GUIDE.md"
    "KAFKA_FIX_GUIDE.md"
    "KAFKA_LISTENER_FIX.md"
    "LESSONS_LEARNED_ORDER_AGENT.md"
    "MULTI_AGENT_FEATURE_INTEGRATION_ANALYSIS.md"
    "MULTI_AGENT_SYSTEM_PLAN.md"
    "POSTGRESQL_SETUP_WINDOWS.md"
    "POSTGRES_PERMISSION_FIX.md"
    "PRODUCT_AGENT_PHASE2_COMPLETE.md"
    "PRODUCT_AGENT_PHASE2_DESIGN.md"
    "PRODUCT_AGENT_PHASE2_FINAL_COMPLETE.md"
    "PRODUCT_AGENT_PHASE2_PROGRESS.md"
    "PROGRESS_PHASE1_12_AGENTS_COMPLETE.md"
    "PROGRESS_PHASE2_16_AGENTS_COMPLETE.md"
    "PROGRESS_UPDATE_PHASE_1_COMPLETE.md"
    "REMAINING_AGENTS_BATCH_IMPLEMENTATION.md"
    "STARTUP_GUIDE.md"
    "SYSTEM_ARCHITECTURE.md"
    "TESTING_NEW_AGENTS_GUIDE.md"
    "TEST_FIXTURE_FIX_SUMMARY.md"
    "UI_INTEGRATION_GUIDE.md"
    "UI_UX_RESEARCH_FINDINGS.md"
    "VERIFICATION_GUIDE.md"
    "WINDOWS_LAUNCH_GUIDE.md"
    "WINDOWS_SETUP_GUIDE.md"
)

# Move old batch/PowerShell scripts
OLD_SCRIPTS=(
    "check-and-install-dependencies.bat"
    "check-and-install-dependencies.ps1"
    "diagnose-kafka.ps1"
    "fix-kafka-connection.ps1"
    "install.bat"
    "launch-all.ps1"
    "quick-fix.bat"
    "setup-database.bat"
    "start-system.bat"
    "check-status.bat"
    "check-health.bat"
    "init-database.bat"
    "view-config.bat"
)

# Counter for moved files
MOVED_COUNT=0

# Move markdown documentation files
for file in "${FILES_TO_MOVE[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        mv "$PROJECT_ROOT/$file" "$OLD_DIR/"
        echo -e "${GREEN}✓ Moved: $file${NC}"
        ((MOVED_COUNT++))
    fi
done

# Move old scripts
for file in "${OLD_SCRIPTS[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        mv "$PROJECT_ROOT/$file" "$OLD_DIR/"
        echo -e "${GREEN}✓ Moved: $file${NC}"
        ((MOVED_COUNT++))
    fi
done

# Move docs folder if it exists and contains old documentation
if [ -d "$PROJECT_ROOT/docs" ]; then
    mv "$PROJECT_ROOT/docs" "$OLD_DIR/"
    echo -e "${GREEN}✓ Moved: docs/ folder${NC}"
    ((MOVED_COUNT++))
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Organization complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Total files moved: ${GREEN}$MOVED_COUNT${NC}"
echo ""
echo -e "${BLUE}Files remaining in root:${NC}"
echo "  - README.md (main documentation)"
echo "  - COMPLETE_STARTUP_GUIDE.md (startup instructions)"
echo "  - DEPLOYMENT_GUIDE.md (deployment instructions)"
echo "  - TESTING_GUIDE.md (testing instructions)"
echo "  - CHANGELOG.md (version history)"
echo "  - launch.sh (Linux/Mac launch script)"
echo "  - launch.ps1 (Windows launch script)"
echo ""
echo -e "${YELLOW}Historical documentation moved to: $OLD_DIR${NC}"
echo ""

# Create a README in the old directory
cat > "$OLD_DIR/README.md" << 'EOF'
# Historical Documentation

This folder contains historical documentation from the development process of the Multi-Agent AI E-commerce Platform.

## Contents

This directory includes:

- **Progress Reports**: Documentation tracking the development phases and milestones
- **Fix Guides**: Troubleshooting guides for issues encountered during development
- **Implementation Summaries**: Detailed summaries of agent implementations
- **Verification Reports**: Testing and verification documentation
- **Old Scripts**: Legacy batch and PowerShell scripts replaced by the unified launch scripts

## Current Documentation

For current, up-to-date documentation, please refer to the files in the project root:

- `README.md` - Main project documentation
- `COMPLETE_STARTUP_GUIDE.md` - Comprehensive startup instructions
- `DEPLOYMENT_GUIDE.md` - Deployment instructions
- `TESTING_GUIDE.md` - Testing guidelines
- `CHANGELOG.md` - Version history

## Purpose

These files have been archived to keep the repository root clean and organized while preserving the development history for reference purposes.
EOF

echo -e "${GREEN}✓ Created README in old/ directory${NC}"
echo ""
echo -e "${GREEN}Repository organization complete!${NC}"

