#!/bin/bash

#
# Complete Setup and Testing Script
#
# This script performs a complete system setup and validation:
# 1. Initializes the database
# 2. Starts all 16 agents
# 3. Runs comprehensive validation tests
# 4. Generates production readiness report
#

set -e  # Exit on error

echo "================================================================================"
echo "Multi-Agent E-commerce System - Complete Setup and Testing"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Step 1: Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL is not running on localhost:5432${NC}"
    echo "Please start PostgreSQL and try again."
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL is running${NC}"

# Check if Kafka is running (optional)
if ! nc -z localhost 9092 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Kafka is not running on localhost:9092${NC}"
    echo "Some features may not work without Kafka."
else
    echo -e "${GREEN}✅ Kafka is running${NC}"
fi

echo ""

# Step 2: Initialize database
echo -e "${YELLOW}Step 2: Initializing database...${NC}"
echo ""

python3 init_database.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Database initialization failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Database initialized${NC}"
echo ""

# Step 3: Stop any running agents
echo -e "${YELLOW}Step 3: Stopping any running agents...${NC}"
echo ""

if [ -f "./stop_all_agents.sh" ]; then
    ./stop_all_agents.sh > /dev/null 2>&1 || true
fi

echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# Step 4: Start all agents
echo -e "${YELLOW}Step 4: Starting all 16 agents...${NC}"
echo ""

python3 start_production_system.py &
STARTUP_PID=$!

# Wait for agents to start
echo "Waiting 15 seconds for agents to initialize..."
sleep 15

# Check if startup process is still running
if ! ps -p $STARTUP_PID > /dev/null 2>&1; then
    echo -e "${RED}❌ Agent startup failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Agents started${NC}"
echo ""

# Step 5: Check agent health
echo -e "${YELLOW}Step 5: Checking agent health...${NC}"
echo ""

if [ -f "./check_agents_status.sh" ]; then
    ./check_agents_status.sh
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Some agents are not healthy${NC}"
    else
        echo -e "${GREEN}✅ All agents healthy${NC}"
    fi
fi

echo ""

# Step 6: Run tests
echo -e "${YELLOW}Step 6: Running comprehensive validation tests...${NC}"
echo ""

# Run workflow tests
echo "Running workflow tests..."
python3 testing/comprehensive_workflow_tests.py

# Run UI tests (if dashboard is running)
if nc -z localhost 5173 > /dev/null 2>&1; then
    echo "Running UI tests..."
    python3 testing/ui_automation_tests.py
else
    echo -e "${YELLOW}⚠️  Dashboard not running on port 5173, skipping UI tests${NC}"
fi

# Run production validation suite
echo "Running production validation suite..."
python3 testing/production_validation_suite.py

echo ""
echo "================================================================================"
echo -e "${GREEN}Setup and Testing Complete!${NC}"
echo "================================================================================"
echo ""
echo "Test results are available in the test_logs/ directory"
echo ""
echo "To stop all agents:"
echo "  ./stop_all_agents.sh"
echo ""
echo "To check agent status:"
echo "  ./check_agents_status.sh"
echo ""
echo "================================================================================"

