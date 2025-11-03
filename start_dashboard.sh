#!/bin/bash

#
# Start Dashboard Script
#
# This script installs dependencies and launches the multi-agent dashboard UI.
# The dashboard connects to all 26 agents and provides admin, merchant, and customer interfaces.
#

set -e  # Exit on error

echo "================================================================================"
echo "Multi-Agent E-commerce Dashboard - Startup Script"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$PROJECT_ROOT/multi-agent-dashboard"

# Check if dashboard directory exists
if [ ! -d "$DASHBOARD_DIR" ]; then
    echo -e "${RED}❌ Dashboard directory not found: $DASHBOARD_DIR${NC}"
    exit 1
fi

cd "$DASHBOARD_DIR"

echo -e "${BLUE}Dashboard Directory: $DASHBOARD_DIR${NC}"
echo ""

# Step 1: Check if Node.js is installed
echo -e "${YELLOW}Step 1: Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✅ Node.js installed: $NODE_VERSION${NC}"
echo ""

# Step 2: Check for package manager (pnpm or npm)
echo -e "${YELLOW}Step 2: Checking package manager...${NC}"
PACKAGE_MANAGER=""

if command -v pnpm &> /dev/null; then
    PACKAGE_MANAGER="pnpm"
    PNPM_VERSION=$(pnpm --version)
    echo -e "${GREEN}✅ pnpm installed: $PNPM_VERSION${NC}"
elif command -v npm &> /dev/null; then
    PACKAGE_MANAGER="npm"
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm installed: $NPM_VERSION${NC}"
else
    echo -e "${RED}❌ No package manager found (npm or pnpm)${NC}"
    exit 1
fi

echo -e "${BLUE}Using package manager: $PACKAGE_MANAGER${NC}"
echo ""

# Step 3: Install dependencies if node_modules doesn't exist
echo -e "${YELLOW}Step 3: Checking dependencies...${NC}"
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found, installing dependencies...${NC}"
    echo ""
    
    if [ "$PACKAGE_MANAGER" = "pnpm" ]; then
        pnpm install
    else
        npm install --legacy-peer-deps
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Dependency installation failed${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

echo ""

# Step 4: Create .env file if it doesn't exist
echo -e "${YELLOW}Step 4: Configuring environment...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found, creating default configuration...${NC}"
    
    cat > .env << 'EOF'
# Multi-Agent Dashboard Configuration

# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8015/ws

# Development Tools
VITE_ENABLE_DEVTOOLS=true
EOF
    
    echo -e "${GREEN}✅ Created .env file with default configuration${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

echo ""

# Step 5: Check if agents are running
echo -e "${YELLOW}Step 5: Checking agent connectivity...${NC}"
echo ""

# Test primary API endpoint (order_agent on port 8000)
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Primary API (order_agent) is running on port 8000${NC}"
else
    echo -e "${YELLOW}⚠️  Primary API (order_agent) is not responding on port 8000${NC}"
    echo -e "${YELLOW}   The dashboard will start but may not function correctly.${NC}"
    echo -e "${YELLOW}   Please start agents first: ./start_all_26_agents.sh${NC}"
fi

# Test WebSocket endpoint (transport_agent on port 8015)
if curl -s -f http://localhost:8015/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ WebSocket API (transport_agent) is running on port 8015${NC}"
else
    echo -e "${YELLOW}⚠️  WebSocket API (transport_agent) is not responding on port 8015${NC}"
    echo -e "${YELLOW}   Real-time features may not work.${NC}"
fi

echo ""

# Step 6: Start the dashboard
echo -e "${YELLOW}Step 6: Starting dashboard...${NC}"
echo ""
echo -e "${BLUE}Dashboard will be available at: ${GREEN}http://localhost:5173${NC}"
echo -e "${BLUE}Press ${YELLOW}Ctrl+C${BLUE} to stop the dashboard${NC}"
echo ""
echo "================================================================================"
echo ""

# Start the dev server
if [ "$PACKAGE_MANAGER" = "pnpm" ]; then
    pnpm run dev
else
    npm run dev
fi

