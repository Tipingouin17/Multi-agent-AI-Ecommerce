#!/bin/bash

################################################################################
# Multi-Agent E-commerce Platform - Complete System Shutdown
################################################################################
#
# This script stops the ENTIRE platform in the correct order:
# 1. Frontend UI
# 2. All 27 backend agents
# 3. Docker infrastructure (optional)
#
# Usage: ./stop_platform.sh [options]
#
# Options:
#   --keep-docker    Keep Docker infrastructure running
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRASTRUCTURE_DIR="$PROJECT_ROOT/infrastructure"

# Flags
KEEP_DOCKER=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep-docker)
            KEEP_DOCKER=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Functions
print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

################################################################################
# BANNER
################################################################################

clear
echo -e "${YELLOW}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   Multi-Agent E-commerce Platform - System Shutdown                      ║
║                                                                           ║
║   🛑 Stopping: Frontend UI + 27 Agents + Docker Infrastructure            ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

################################################################################
# STEP 1: Stop Frontend
################################################################################

print_header "STEP 1: Stopping Frontend UI"

# Check for saved PID
if [ -f "$PROJECT_ROOT/.frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/.frontend.pid")
    if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
        print_info "Stopping frontend (PID: $FRONTEND_PID)..."
        kill "$FRONTEND_PID" 2>/dev/null || true
        print_success "Frontend stopped"
    fi
    rm -f "$PROJECT_ROOT/.frontend.pid"
fi

# Kill any remaining Vite processes
pkill -f "vite" 2>/dev/null || true
print_success "All frontend processes stopped"

################################################################################
# STEP 2: Stop All Agents
################################################################################

print_header "STEP 2: Stopping All 27 Backend Agents"

if [ -f "$PROJECT_ROOT/stop_all_agents.sh" ]; then
    "$PROJECT_ROOT/stop_all_agents.sh"
    print_success "All agents stopped"
else
    print_info "stop_all_agents.sh not found, killing Python processes..."
    pkill -f "agents/.*_v3.py" 2>/dev/null || true
    print_success "Python agent processes stopped"
fi

################################################################################
# STEP 3: Stop Docker Infrastructure
################################################################################

if [ "$KEEP_DOCKER" = false ]; then
    print_header "STEP 3: Stopping Docker Infrastructure"
    
    cd "$INFRASTRUCTURE_DIR"
    
    print_info "Stopping Docker containers..."
    docker-compose down
    
    print_success "Docker infrastructure stopped"
    
    cd "$PROJECT_ROOT"
else
    print_header "STEP 3: Keeping Docker Infrastructure Running (--keep-docker)"
    print_info "Docker containers are still running"
fi

################################################################################
# SUMMARY
################################################################################

print_header "SHUTDOWN COMPLETE! ✅"

echo -e "${GREEN}All systems stopped successfully!${NC}"
echo ""

if [ "$KEEP_DOCKER" = true ]; then
    echo -e "${YELLOW}Note: Docker infrastructure is still running${NC}"
    echo -e "${BLUE}To stop Docker: cd infrastructure && docker-compose down${NC}"
    echo ""
fi

echo -e "${BLUE}To start the platform again:${NC}"
echo -e "   ./start_platform.sh"
echo ""
