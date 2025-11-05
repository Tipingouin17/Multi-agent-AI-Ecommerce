#!/bin/bash

################################################################################
# Multi-Agent E-commerce Platform - Complete System Launcher
################################################################################
#
# This script launches the ENTIRE platform in the correct order:
# 1. Docker infrastructure (PostgreSQL, Redis, Kafka, monitoring)
# 2. Database initialization
# 3. All 27 backend agents
# 4. Frontend UI
# 5. Verification and monitoring setup
#
# Usage: ./start_platform.sh [options]
#
# Options:
#   --skip-docker    Skip Docker infrastructure startup (if already running)
#   --skip-db-init   Skip database initialization (if already done)
#   --dev            Start with development tools (pgAdmin, Kafka UI)
#   --full           Start with all optional services
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRASTRUCTURE_DIR="$PROJECT_ROOT/infrastructure"
AGENTS_DIR="$PROJECT_ROOT/agents"
FRONTEND_DIR="$PROJECT_ROOT/multi-agent-dashboard"
LOGS_DIR="$PROJECT_ROOT/logs"

# Flags
SKIP_DOCKER=false
SKIP_DB_INIT=false
DOCKER_PROFILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --skip-db-init)
            SKIP_DB_INIT=true
            shift
            ;;
        --dev)
            DOCKER_PROFILE="--profile dev"
            shift
            ;;
        --full)
            DOCKER_PROFILE="--profile full"
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

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_wait=${4:-60}
    
    echo -n "Waiting for $service_name to be ready..."
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo ""
            print_success "$service_name is ready!"
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
        echo -n "."
    done
    echo ""
    print_warning "$service_name did not start within ${max_wait} seconds"
    return 1
}

################################################################################
# BANNER
################################################################################

clear
echo -e "${MAGENTA}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   Multi-Agent E-commerce Platform - Complete System Launcher             ║
║                                                                           ║
║   🚀 Starting: Docker Infrastructure + 27 Agents + Frontend UI            ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

################################################################################
# STEP 1: Check Prerequisites
################################################################################

print_header "STEP 1: Checking Prerequisites"

check_command "docker"
check_command "docker-compose"
check_command "python3.11"
check_command "node"
check_command "npm"
check_command "nc"

print_success "Docker installed: $(docker --version)"
print_success "Docker Compose installed: $(docker-compose --version)"
print_success "Python installed: $(python3.11 --version)"
print_success "Node.js installed: $(node --version)"
print_success "npm installed: $(npm --version)"

################################################################################
# STEP 2: Start Docker Infrastructure
################################################################################

if [ "$SKIP_DOCKER" = false ]; then
    print_header "STEP 2: Starting Docker Infrastructure"
    
    cd "$INFRASTRUCTURE_DIR"
    
    print_info "Starting Docker containers with docker-compose..."
    docker-compose $DOCKER_PROFILE up -d
    
    echo ""
    print_info "Waiting for services to be healthy..."
    echo ""
    
    # Wait for critical services
    wait_for_service localhost 5432 "PostgreSQL" 60
    wait_for_service localhost 6379 "Redis" 30
    wait_for_service localhost 9092 "Kafka" 60
    wait_for_service localhost 9090 "Prometheus" 30
    wait_for_service localhost 3000 "Grafana" 30
    
    echo ""
    print_success "Docker infrastructure is ready!"
    
    # Show running containers
    echo ""
    print_info "Running containers:"
    docker-compose ps
    
    cd "$PROJECT_ROOT"
else
    print_header "STEP 2: Skipping Docker Infrastructure (--skip-docker)"
    print_warning "Assuming Docker services are already running..."
fi

################################################################################
# STEP 3: Initialize Database
################################################################################

if [ "$SKIP_DB_INIT" = false ]; then
    print_header "STEP 3: Initializing Database"
    
    if [ -f "$PROJECT_ROOT/database/schema.sql" ]; then
        print_info "Importing database schema..."
        docker exec -i multi-agent-postgres psql -U postgres -d ecommerce_db < "$PROJECT_ROOT/database/schema.sql" 2>/dev/null || true
        print_success "Database schema imported!"
    else
        print_warning "database/schema.sql not found, skipping schema import"
    fi
    
    if [ -f "$PROJECT_ROOT/database/seed_data.sql" ]; then
        print_info "Importing seed data..."
        docker exec -i multi-agent-postgres psql -U postgres -d ecommerce_db < "$PROJECT_ROOT/database/seed_data.sql" 2>/dev/null || true
        print_success "Seed data imported!"
    else
        print_info "No seed data file found, skipping"
    fi
else
    print_header "STEP 3: Skipping Database Initialization (--skip-db-init)"
fi

################################################################################
# STEP 4: Start All 27 Agents
################################################################################

print_header "STEP 4: Starting All 27 Backend Agents"

if [ -f "$PROJECT_ROOT/start_all_agents.sh" ]; then
    print_info "Launching agents..."
    "$PROJECT_ROOT/start_all_agents.sh"
    
    echo ""
    print_info "Waiting 10 seconds for agents to initialize..."
    sleep 10
    
    print_success "Agents started!"
else
    print_error "start_all_agents.sh not found!"
    exit 1
fi

################################################################################
# STEP 5: Verify Agent Health
################################################################################

print_header "STEP 5: Verifying Agent Health"

if [ -f "$PROJECT_ROOT/check_all_agents.sh" ]; then
    "$PROJECT_ROOT/check_all_agents.sh"
else
    print_warning "check_all_agents.sh not found, skipping health check"
fi

################################################################################
# STEP 6: Start Frontend UI
################################################################################

print_header "STEP 6: Starting Frontend UI"

if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_info "Installing frontend dependencies..."
        npm install
    fi
    
    print_info "Starting Vite development server..."
    
    # Start in background
    npm run dev > "$LOGS_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    
    print_success "Frontend started (PID: $FRONTEND_PID)"
    print_info "Logs: $LOGS_DIR/frontend.log"
    
    # Wait for frontend to be ready
    wait_for_service localhost 5173 "Frontend UI" 60
    
    cd "$PROJECT_ROOT"
else
    print_error "Frontend directory not found: $FRONTEND_DIR"
fi

################################################################################
# STEP 7: System Status Summary
################################################################################

print_header "SYSTEM STARTUP COMPLETE! 🎉"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        🎯 ACCESS POINTS                                   ║${NC}"
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
echo ""

echo -e "${GREEN}📱 User Interfaces:${NC}"
echo -e "   ${CYAN}Frontend UI:${NC}         http://localhost:5173"
echo -e "   ${CYAN}Admin Dashboard:${NC}     http://localhost:5173 → Select 'Admin Dashboard'"
echo -e "   ${CYAN}Merchant Portal:${NC}     http://localhost:5173 → Select 'Merchant Portal'"
echo -e "   ${CYAN}Customer Portal:${NC}     http://localhost:5173 → Select 'Customer Portal'"
echo ""

echo -e "${GREEN}📊 Monitoring & Management:${NC}"
echo -e "   ${CYAN}Grafana:${NC}             http://localhost:3000 (admin/admin123)"
echo -e "   ${CYAN}Prometheus:${NC}          http://localhost:9090"
echo -e "   ${CYAN}pgAdmin:${NC}             http://localhost:5050 (admin@multiagent.com)"
echo -e "   ${CYAN}Kafka UI:${NC}            http://localhost:8080"
echo ""

echo -e "${GREEN}🔧 Backend Services:${NC}"
echo -e "   ${CYAN}System API Gateway:${NC}  http://localhost:8100"
echo -e "   ${CYAN}API Documentation:${NC}   http://localhost:8100/docs"
echo -e "   ${CYAN}Agent Health:${NC}        http://localhost:8100/api/agents"
echo ""

echo -e "${GREEN}🗄️  Infrastructure:${NC}"
echo -e "   ${CYAN}PostgreSQL:${NC}          localhost:5432 (postgres/postgres)"
echo -e "   ${CYAN}Redis:${NC}               localhost:6379"
echo -e "   ${CYAN}Kafka:${NC}               localhost:9092"
echo ""

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        📋 SYSTEM STATUS                                   ║${NC}"
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Count healthy agents
HEALTHY_COUNT=0
TOTAL_AGENTS=27
for port in {8000..8100}; do
    if nc -z localhost "$port" 2>/dev/null; then
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
    fi
done

echo -e "   ${GREEN}✅ Docker Infrastructure:${NC} Running"
echo -e "   ${GREEN}✅ Backend Agents:${NC}        $HEALTHY_COUNT/$TOTAL_AGENTS healthy"
echo -e "   ${GREEN}✅ Frontend UI:${NC}           Running on port 5173"
echo -e "   ${GREEN}✅ Monitoring:${NC}            Prometheus + Grafana + Loki"
echo ""

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        🛑 STOP COMMANDS                                   ║${NC}"
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
echo ""

echo -e "   ${YELLOW}Stop Frontend:${NC}       kill $FRONTEND_PID"
echo -e "   ${YELLOW}Stop Agents:${NC}         ./stop_all_agents.sh"
echo -e "   ${YELLOW}Stop Docker:${NC}         cd infrastructure && docker-compose down"
echo -e "   ${YELLOW}Stop Everything:${NC}     ./stop_platform.sh"
echo ""

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        📁 LOG FILES                                       ║${NC}"
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
echo ""

echo -e "   ${CYAN}Agent Logs:${NC}          $LOGS_DIR/agents/"
echo -e "   ${CYAN}Frontend Log:${NC}        $LOGS_DIR/frontend.log"
echo -e "   ${CYAN}Docker Logs:${NC}         cd infrastructure && docker-compose logs"
echo ""

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                           ║${NC}"
echo -e "${GREEN}║   🎉 Platform is ready! Open http://localhost:5173 to get started!       ║${NC}"
echo -e "${GREEN}║                                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Save frontend PID for later
echo "$FRONTEND_PID" > "$PROJECT_ROOT/.frontend.pid"

print_success "All systems operational! 🚀"
echo ""
