#!/bin/bash

################################################################################
# Multi-Agent AI E-commerce Platform - Launch Script
# 
# This script automates the complete startup process for the multi-agent system.
# It handles infrastructure services, database initialization, and agent launch.
#
# Usage: ./launch.sh [options]
# Options:
#   --skip-deps     Skip dependency installation
#   --skip-db       Skip database initialization
#   --dev           Start with development tools (pgAdmin, Kafka UI)
#   --stop          Stop all services
#   --status        Check system status
#   --help          Show this help message
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/infrastructure/docker-compose.yml"

# Parse command line arguments
SKIP_DEPS=false
SKIP_DB=false
DEV_MODE=false
STOP_SERVICES=false
CHECK_STATUS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --skip-db)
            SKIP_DB=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --stop)
            STOP_SERVICES=true
            shift
            ;;
        --status)
            CHECK_STATUS=true
            shift
            ;;
        --help)
            head -n 20 "$0" | grep "^#" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

################################################################################
# Stop Services Function
################################################################################

stop_services() {
    print_header "Stopping Multi-Agent E-commerce System"
    
    cd "$PROJECT_ROOT/infrastructure"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        docker compose down
    else
        print_error "Docker Compose not found"
        exit 1
    fi
    
    print_success "All services stopped"
    exit 0
}

################################################################################
# Status Check Function
################################################################################

check_status() {
    print_header "Multi-Agent E-commerce System Status"
    
    cd "$PROJECT_ROOT/infrastructure"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        docker compose ps
    else
        print_error "Docker Compose not found"
        exit 1
    fi
    
    echo ""
    print_info "Access Points:"
    echo "  - Grafana Dashboard: http://localhost:3000 (admin/admin123)"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - API Documentation: http://localhost:8000/docs"
    
    if [ "$DEV_MODE" = true ]; then
        echo "  - Kafka UI: http://localhost:8080"
        echo "  - pgAdmin: http://localhost:5050"
    fi
    
    exit 0
}

################################################################################
# Main Launch Process
################################################################################

if [ "$STOP_SERVICES" = true ]; then
    stop_services
fi

if [ "$CHECK_STATUS" = true ]; then
    check_status
fi

print_header "Multi-Agent AI E-commerce Platform Launcher"

# Step 1: Check Prerequisites
print_info "Checking prerequisites..."

MISSING_DEPS=false
check_command "python3" || MISSING_DEPS=true
check_command "docker" || MISSING_DEPS=true
check_command "git" || MISSING_DEPS=true

if [ "$MISSING_DEPS" = true ]; then
    print_error "Missing required dependencies. Please install them first."
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
    print_success "docker-compose is installed"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
    print_success "docker compose (v2) is installed"
else
    print_error "Docker Compose not found"
    exit 1
fi

# Step 2: Setup Python Virtual Environment
if [ "$SKIP_DEPS" = false ]; then
    print_header "Setting up Python Environment"
    
    if [ ! -d "$VENV_PATH" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv "$VENV_PATH"
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    print_info "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    
    print_info "Installing Python dependencies..."
    pip install --upgrade pip -q
    pip install -r "$PROJECT_ROOT/requirements.txt" -q
    pip install -e "$PROJECT_ROOT" -q
    print_success "Python dependencies installed"
else
    print_warning "Skipping dependency installation"
    if [ -d "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
    fi
fi

# Step 3: Check Environment Variables
print_header "Checking Configuration"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    print_warning ".env file not found. Creating from template..."
    
    cat > "$PROJECT_ROOT/.env" << 'EOF'
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=multi_agent_ecommerce
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres123

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis123

# OpenAI API Key (optional - required for AI features)
OPENAI_API_KEY=

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
EOF
    
    print_success ".env file created"
    print_warning "Please edit .env and add your OPENAI_API_KEY if needed"
else
    print_success ".env file exists"
fi

# Step 4: Start Infrastructure Services
print_header "Starting Infrastructure Services"

cd "$PROJECT_ROOT/infrastructure"

if [ "$DEV_MODE" = true ]; then
    print_info "Starting services in development mode (with dev tools)..."
    $DOCKER_COMPOSE_CMD --profile dev up -d
else
    print_info "Starting services..."
    $DOCKER_COMPOSE_CMD up -d
fi

print_info "Waiting for services to be ready..."
sleep 10

# Check service health
print_info "Checking service health..."
RETRIES=30
HEALTHY=false

for i in $(seq 1 $RETRIES); do
    if docker ps --filter "health=healthy" | grep -q "multi-agent"; then
        HEALTHY=true
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

if [ "$HEALTHY" = true ]; then
    print_success "Infrastructure services are healthy"
else
    print_warning "Some services may still be starting up"
fi

# Step 5: Initialize Database
if [ "$SKIP_DB" = false ]; then
    print_header "Initializing Database"
    
    cd "$PROJECT_ROOT"
    
    print_info "Creating database schema..."
    python3 init_database.py
    
    print_info "Creating Kafka topics..."
    python3 init_kafka_topics.py
    
    print_success "Database and Kafka initialization complete"
else
    print_warning "Skipping database initialization"
fi

# Step 6: Display Access Information
print_header "Launch Complete!"

print_success "Multi-Agent E-commerce System is running"
echo ""
print_info "Access Points:"
echo "  - Grafana Dashboard: http://localhost:3000 (admin/admin123)"
echo "  - Prometheus: http://localhost:9090"
echo "  - PostgreSQL: localhost:5432 (postgres/postgres123)"
echo "  - Redis: localhost:6379 (password: redis123)"
echo "  - Kafka: localhost:9092"
echo ""

if [ "$DEV_MODE" = true ]; then
    print_info "Development Tools:"
    echo "  - Kafka UI: http://localhost:8080"
    echo "  - pgAdmin: http://localhost:5050 (admin@multiagent.com/admin123)"
    echo ""
fi

print_info "Next Steps:"
echo "  1. Start agents: python3 agents/start_agents.py"
echo "  2. View logs: cd infrastructure && $DOCKER_COMPOSE_CMD logs -f"
echo "  3. Check status: ./launch.sh --status"
echo "  4. Stop system: ./launch.sh --stop"
echo ""

print_info "For more information, see README.md and COMPLETE_STARTUP_GUIDE.md"

