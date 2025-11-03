#!/bin/bash

#
# Complete System Startup Script
#
# This script launches the entire multi-agent e-commerce system:
# 1. Checks prerequisites (PostgreSQL, Kafka)
# 2. Starts all 26 agents
# 3. Waits for agents to be healthy
# 4. Launches the dashboard UI
# 5. Provides status monitoring
#

set -e  # Exit on error

echo "================================================================================"
echo "Multi-Agent E-commerce Platform - Complete System Startup"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Configuration
AGENT_STARTUP_WAIT=30
DASHBOARD_PORT=5173

# Functions
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        error_exit "$1 is not installed. Please install it first."
    fi
}

check_port() {
    local port=$1
    if nc -z localhost "$port" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# STEP 1: Check Prerequisites
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}STEP 1: Checking Prerequisites${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check Python
check_command "python3.11"
PYTHON_VERSION=$(python3.11 --version)
echo -e "${GREEN}✅ Python installed: $PYTHON_VERSION${NC}"

# Check PostgreSQL
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL is not running on localhost:5432${NC}"
    echo -e "${YELLOW}   Please start PostgreSQL and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL is running${NC}"

# Check Kafka (optional)
if check_port 9092; then
    echo -e "${GREEN}✅ Kafka is running (optional)${NC}"
else
    echo -e "${YELLOW}⚠️  Kafka is not running (agents will run in degraded mode)${NC}"
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js installed: $NODE_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  Node.js not found (dashboard will not start)${NC}"
    echo -e "${YELLOW}   Install Node.js 18+ from https://nodejs.org/${NC}"
fi

echo ""

# ============================================================================
# STEP 2: Start All Agents
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}STEP 2: Starting All 26 Agents${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

if [ ! -f "./start_all_26_agents.sh" ]; then
    error_exit "start_all_26_agents.sh not found"
fi

echo -e "${BLUE}Launching agents in background...${NC}"
./start_all_26_agents.sh

echo ""
echo -e "${YELLOW}Waiting ${AGENT_STARTUP_WAIT} seconds for agents to initialize...${NC}"
sleep "$AGENT_STARTUP_WAIT"
echo ""

# ============================================================================
# STEP 3: Check Agent Health
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}STEP 3: Checking Agent Health${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

if [ -f "./check_all_26_agents_health.py" ]; then
    python3.11 check_all_26_agents_health.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Agent health check completed${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠️  Some agents may not be fully healthy${NC}"
        echo -e "${YELLOW}   The system will continue, but some features may not work.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Health check script not found, skipping...${NC}"
fi

echo ""

# ============================================================================
# STEP 4: Launch Dashboard
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}STEP 4: Launching Dashboard UI${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

if [ ! -f "./start_dashboard.sh" ]; then
    echo -e "${YELLOW}⚠️  start_dashboard.sh not found${NC}"
    echo -e "${YELLOW}   You can manually start the dashboard:${NC}"
    echo -e "${BLUE}   cd multi-agent-dashboard && npm run dev${NC}"
    echo ""
else
    echo -e "${BLUE}Starting dashboard...${NC}"
    echo ""
    
    # Start dashboard in background
    ./start_dashboard.sh > dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    
    echo -e "${GREEN}✅ Dashboard started (PID: $DASHBOARD_PID)${NC}"
    echo -e "${BLUE}   Logs: dashboard.log${NC}"
    
    # Wait for dashboard to be ready
    echo ""
    echo -e "${YELLOW}Waiting for dashboard to be ready...${NC}"
    
    MAX_WAIT=60
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        if check_port $DASHBOARD_PORT; then
            echo -e "${GREEN}✅ Dashboard is ready!${NC}"
            break
        fi
        sleep 2
        WAITED=$((WAITED + 2))
        echo -n "."
    done
    
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Dashboard did not start within ${MAX_WAIT} seconds${NC}"
        echo -e "${YELLOW}   Check dashboard.log for errors${NC}"
    fi
fi

echo ""

# ============================================================================
# STEP 5: System Status Summary
# ============================================================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}SYSTEM STARTUP COMPLETE!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BLUE}📊 System Status:${NC}"
echo ""

# Check key agent ports
AGENT_PORTS=(8000 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 8011 8012 8013 8014 8015 8016 8017 8018 8019 8020 8021 8022 8023 8024 8025)
HEALTHY_COUNT=0
TOTAL_AGENTS=${#AGENT_PORTS[@]}

for port in "${AGENT_PORTS[@]}"; do
    if check_port "$port"; then
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
    fi
done

echo -e "   Agents Running: ${GREEN}${HEALTHY_COUNT}/${TOTAL_AGENTS}${NC}"

# Check dashboard
if check_port $DASHBOARD_PORT; then
    echo -e "   Dashboard: ${GREEN}✅ Running${NC}"
    echo -e "   Dashboard URL: ${CYAN}http://localhost:${DASHBOARD_PORT}${NC}"
else
    echo -e "   Dashboard: ${YELLOW}⚠️  Not running${NC}"
fi

echo ""
echo -e "${BLUE}📋 Access Points:${NC}"
echo ""
echo -e "   🌐 Dashboard: ${CYAN}http://localhost:5173${NC}"
echo -e "   🔧 Admin Interface: ${CYAN}http://localhost:5173${NC} → Select 'System Administrator'"
echo -e "   🛍️  Merchant Portal: ${CYAN}http://localhost:5173${NC} → Select 'Merchant Portal'"
echo -e "   🛒 Customer Interface: ${CYAN}http://localhost:5173${NC} → Select 'Customer Experience'"
echo -e "   🧪 Database Test: ${CYAN}http://localhost:5173${NC} → Select 'Database Integration Test'"
echo ""
echo -e "   📡 Primary API: ${CYAN}http://localhost:8000${NC}"
echo -e "   📊 API Docs: ${CYAN}http://localhost:8000/docs${NC}"
echo ""

echo -e "${BLUE}📁 Log Files:${NC}"
echo ""
echo -e "   Agent Logs: ${CYAN}logs/agents/${NC}"
echo -e "   Dashboard Log: ${CYAN}dashboard.log${NC}"
echo ""

echo -e "${BLUE}🛑 To Stop the System:${NC}"
echo ""
echo -e "   1. Stop dashboard: ${CYAN}pkill -f 'vite'${NC} or ${CYAN}kill \$DASHBOARD_PID${NC}"
echo -e "   2. Stop agents: ${CYAN}./stop_all_agents.sh${NC}"
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Happy Testing! 🚀${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

