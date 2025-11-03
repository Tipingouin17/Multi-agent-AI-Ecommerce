#!/bin/bash

#
# MASTER LAUNCH SCRIPT - Multi-Agent E-Commerce Platform
#
# This is the ultimate one-command launcher that:
# - Tracks all infrastructure components
# - Creates comprehensive logs for every agent
# - Monitors startup sequence
# - Provides real-time status updates
# - Ensures 100% visibility into system state
#

# Parse command-line arguments
VERBOSE=0
for arg in "$@"; do
    case $arg in
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [-v|--verbose] [-h|--help]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose    Enable verbose output with detailed command tracing"
            echo "  -h, --help       Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                # Normal mode"
            echo "  $0 --verbose      # Verbose mode with detailed output"
            echo "  $0 -v             # Verbose mode (short form)"
            exit 0
            ;;
    esac
done

# Enable error handling
# Note: VERBOSE mode shows detailed results/logs, not command traces
set -e  # Exit on error
set -o pipefail  # Catch errors in pipes

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Logging configuration
MASTER_LOG_DIR="logs/master"
AGENT_LOG_DIR="logs/agents"
INFRASTRUCTURE_LOG_DIR="logs/infrastructure"
STARTUP_LOG="$MASTER_LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"
PROCESS_TRACKING_FILE="$MASTER_LOG_DIR/process_tracking.json"

# Timing configuration
AGENT_STARTUP_DELAY=2
HEALTH_CHECK_WAIT=30
DASHBOARD_STARTUP_WAIT=60

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$STARTUP_LOG"
}

log_info() {
    log "INFO" "$@"
    echo -e "${BLUE}[INFO]${NC} $@"
}

log_success() {
    log "SUCCESS" "$@"
    echo -e "${GREEN}[SUCCESS]${NC} $@"
}

log_warning() {
    log "WARNING" "$@"
    echo -e "${YELLOW}[WARNING]${NC} $@"
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}[ERROR]${NC} $@"
}

log_section() {
    local title="$@"
    echo "" | tee -a "$STARTUP_LOG"
    echo "═══════════════════════════════════════════════════════════════════════════" | tee -a "$STARTUP_LOG"
    echo "$title" | tee -a "$STARTUP_LOG"
    echo "═══════════════════════════════════════════════════════════════════════════" | tee -a "$STARTUP_LOG"
    echo "" | tee -a "$STARTUP_LOG"
}

# ============================================================================
# INITIALIZATION
# ============================================================================

initialize_logging() {
    log_section "INITIALIZING MASTER LAUNCH SCRIPT"
    
    # Create all log directories
    mkdir -p "$MASTER_LOG_DIR"
    mkdir -p "$AGENT_LOG_DIR"
    mkdir -p "$INFRASTRUCTURE_LOG_DIR"
    
    log_success "Created log directories:"
    log_success "  - Master logs: $MASTER_LOG_DIR"
    log_success "  - Agent logs: $AGENT_LOG_DIR"
    log_success "  - Infrastructure logs: $INFRASTRUCTURE_LOG_DIR"
    
    # Initialize process tracking file
    echo "{\"agents\": {}, \"infrastructure\": {}, \"dashboard\": {}}" > "$PROCESS_TRACKING_FILE"
    log_success "Initialized process tracking: $PROCESS_TRACKING_FILE"
    
    log_info "Master log file: $STARTUP_LOG"
}

# ============================================================================
# INFRASTRUCTURE CHECKS
# ============================================================================

check_infrastructure() {
    log_section "CHECKING INFRASTRUCTURE COMPONENTS"
    
    local all_ok=true
    
    # Check Python
    log_info "Checking Python installation..."
    if [ "$VERBOSE" = "1" ]; then
        echo -e "${CYAN}  → Running: which python3.11${NC}"
    fi
    if command -v python3.11 &> /dev/null; then
        PYTHON_VERSION=$(python3.11 --version)
        log_success "Python: $PYTHON_VERSION"
        echo "$PYTHON_VERSION" > "$INFRASTRUCTURE_LOG_DIR/python.log"
        if [ "$VERBOSE" = "1" ]; then
            echo -e "${GREEN}  → Python path: $(which python3.11)${NC}"
        fi
    else
        log_error "Python 3.11 not found"
        echo -e "${RED}  → Please install Python 3.11${NC}"
        all_ok=false
    fi
    
    # Check PostgreSQL
    log_info "Checking PostgreSQL..."
    if [ "$VERBOSE" = "1" ]; then
        echo -e "${CYAN}  → Running: pg_isready -h localhost -p 5432${NC}"
    fi
    if pg_isready -h localhost -p 5432 > "$INFRASTRUCTURE_LOG_DIR/postgresql.log" 2>&1; then
        log_success "PostgreSQL: Running on port 5432"
        if [ "$VERBOSE" = "1" ]; then
            pg_isready -h localhost -p 5432 | head -1
        fi
    else
        log_error "PostgreSQL: Not running on port 5432"
        echo -e "${RED}  → Error output:${NC}"
        cat "$INFRASTRUCTURE_LOG_DIR/postgresql.log"
        echo -e "${YELLOW}  → Please start PostgreSQL: sudo systemctl start postgresql${NC}"
        all_ok=false
    fi
    
    # Check Kafka (optional)
    log_info "Checking Kafka..."
    if nc -z localhost 9092 2>/dev/null; then
        log_success "Kafka: Running on port 9092"
        echo "Kafka running" > "$INFRASTRUCTURE_LOG_DIR/kafka.log"
    else
        log_warning "Kafka: Not running (optional - agents will run in degraded mode)"
        echo "Kafka not running" > "$INFRASTRUCTURE_LOG_DIR/kafka.log"
    fi
    
    # Check Node.js
    log_info "Checking Node.js..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_success "Node.js: $NODE_VERSION"
        echo "$NODE_VERSION" > "$INFRASTRUCTURE_LOG_DIR/nodejs.log"
    else
        log_warning "Node.js: Not found (dashboard will not start)"
        echo "Node.js not found" > "$INFRASTRUCTURE_LOG_DIR/nodejs.log"
    fi
    
    # Check disk space
    log_info "Checking disk space..."
    df -h . | tail -1 | tee "$INFRASTRUCTURE_LOG_DIR/disk_space.log"
    
    # Check memory
    log_info "Checking memory..."
    free -h | tee "$INFRASTRUCTURE_LOG_DIR/memory.log"
    
    if [ "$all_ok" = false ]; then
        log_error "Infrastructure check failed. Please fix the issues above."
        echo -e "${RED}═══════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}CRITICAL ERROR: Infrastructure prerequisites not met${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════════════════════${NC}"
        exit 1
    fi
    
    log_success "All infrastructure components are ready!"
}

# ============================================================================
# AGENT MANAGEMENT
# ============================================================================

declare -A AGENT_PIDS
declare -A AGENT_PORTS
declare -A AGENT_NAMES

# Agent configuration
AGENTS=(
    "order_agent_production_v2:8000"
    "product_agent_production:8001"
    "inventory_agent:8002"
    "marketplace_connector_agent:8003"
    "payment_agent_enhanced:8004"
    "dynamic_pricing_agent:8005"
    "carrier_selection_agent:8006"
    "customer_agent_enhanced:8007"
    "customer_communication_agent:8008"
    "returns_agent:8009"
    "fraud_detection_agent:8010"
    "recommendation_agent:8011"
    "promotion_agent:8012"
    "risk_anomaly_detection_agent:8013"
    "knowledge_management_agent:8014"
    "transport_management_agent_enhanced:8015"
    "warehouse_agent:8016"
    "document_generation_agent:8017"
    "support_agent:8018"
    "d2c_ecommerce_agent:8019"
    "after_sales_agent_production:8020"
    "backoffice_agent_production:8021"
    "infrastructure_agents:8022"
    "ai_monitoring_agent_self_healing:8023"
    "monitoring_agent:8024"
    "quality_control_agent_production:8025"
)

start_agent() {
    local agent_config=$1
    local agent_file=$(echo "$agent_config" | cut -d':' -f1)
    local agent_port=$(echo "$agent_config" | cut -d':' -f2)
    local agent_name=$(echo "$agent_file" | sed 's/_agent.*//' | sed 's/_production.*//' | sed 's/_enhanced.*//')
    
    local log_file="$AGENT_LOG_DIR/${agent_name}.log"
    local pid_file="$AGENT_LOG_DIR/${agent_name}.pid"
    
    log_info "Starting $agent_name on port $agent_port..."
    if [ "$VERBOSE" = "1" ]; then
        echo -e "${CYAN}  → Command: python3.11 agents/${agent_file}.py${NC}"
        echo -e "${CYAN}  → Port: $agent_port${NC}"
        echo -e "${CYAN}  → Log: $log_file${NC}"
    fi
    
    # Set environment variables
    export API_PORT=$agent_port
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/multi_agent_ecommerce"
    
    # Check if agent file exists
    if [ ! -f "agents/${agent_file}.py" ]; then
        log_error "Agent file not found: agents/${agent_file}.py"
        return 1
    fi
    
    # Start agent in background
    if [ "$VERBOSE" = "1" ]; then
        echo -e "${YELLOW}  → Executing: nohup python3.11 agents/${agent_file}.py > $log_file 2>&1 &${NC}"
    fi
    nohup python3.11 "agents/${agent_file}.py" > "$log_file" 2>&1 &
    local pid=$!
    local start_result=$?
    
    if [ $start_result -ne 0 ]; then
        log_error "Failed to start $agent_name (exit code: $start_result)"
        log_error "Check log file: $log_file"
        tail -20 "$log_file" 2>/dev/null || echo "No log output yet"
        return 1
    fi
    
    # Verify process is running
    sleep 0.5
    if ! ps -p $pid > /dev/null 2>&1; then
        log_error "Agent $agent_name died immediately after start!"
        log_error "Last 20 lines of log:"
        tail -20 "$log_file" 2>/dev/null || echo "No log output"
        return 1
    fi
    
    # In verbose mode, show initial log output
    if [ "$VERBOSE" = "1" ]; then
        echo -e "${CYAN}  → Initial log output (first 5 lines):${NC}"
        head -5 "$log_file" 2>/dev/null | sed 's/^/    /' || echo "    (no output yet)"
    fi
    
    # Save PID
    echo $pid > "$pid_file"
    AGENT_PIDS[$agent_name]=$pid
    AGENT_PORTS[$agent_name]=$agent_port
    AGENT_NAMES[$agent_port]=$agent_name
    
    # Log startup
    log_success "  ✓ $agent_name started (PID: $pid, Port: $agent_port)"
    log_success "    Log: $log_file"
    
    # Update process tracking
    python3.11 -c "
import json
with open('$PROCESS_TRACKING_FILE', 'r') as f:
    data = json.load(f)
data['agents']['$agent_name'] = {
    'pid': $pid,
    'port': $agent_port,
    'log_file': '$log_file',
    'pid_file': '$pid_file',
    'started_at': '$(date -Iseconds)'
}
with open('$PROCESS_TRACKING_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"
    
    # Wait before starting next agent
    sleep $AGENT_STARTUP_DELAY
}

start_all_agents() {
    log_section "STARTING ALL 26 AGENTS"
    
    log_info "Agent startup sequence initiated..."
    log_info "Startup delay between agents: ${AGENT_STARTUP_DELAY}s"
    echo ""
    
    local count=0
    for agent_config in "${AGENTS[@]}"; do
        count=$((count + 1))
        log_info "[$count/26] Starting agent..."
        start_agent "$agent_config"
    done
    
    echo ""
    log_success "All 26 agents started successfully!"
    log_info "Total agents: ${#AGENT_PIDS[@]}"
    
    # Wait for agents to initialize
    log_info "Waiting ${HEALTH_CHECK_WAIT}s for agents to initialize..."
    sleep $HEALTH_CHECK_WAIT
}

# ============================================================================
# HEALTH MONITORING
# ============================================================================

check_agent_health() {
    log_section "CHECKING AGENT HEALTH"
    
    local healthy=0
    local unhealthy=0
    local not_running=0
    
    log_info "Performing health checks on all 26 agents..."
    echo ""
    
    for port in {8000..8025}; do
        local agent_name=${AGENT_NAMES[$port]:-"unknown"}
        local health_log="$AGENT_LOG_DIR/${agent_name}_health.log"
        
        if [ "$VERBOSE" = "1" ]; then
            echo -e "${CYAN}Checking port $port ($agent_name)...${NC}"
            echo -e "${CYAN}  → Running: curl -s -f -m 5 http://localhost:$port/health${NC}"
        fi
        
        if curl -s -f -m 5 "http://localhost:$port/health" > "$health_log" 2>&1; then
            log_success "✓ Port $port ($agent_name) - HEALTHY"
            if [ "$VERBOSE" = "1" ]; then
                echo -e "${GREEN}  → Health response:${NC}"
                head -3 "$health_log" | sed 's/^/    /'
            fi
            healthy=$((healthy + 1))
        else
            if nc -z localhost $port 2>/dev/null; then
                log_warning "⚠ Port $port ($agent_name) - UNHEALTHY (port open but /health failed)"
                echo -e "${YELLOW}  → Port is open but health check failed${NC}"
                if [ "$VERBOSE" = "1" ]; then
                    echo -e "${YELLOW}  → Error output:${NC}"
                    cat "$health_log" 2>/dev/null | head -10 | sed 's/^/    /'
                fi
                unhealthy=$((unhealthy + 1))
            else
                log_error "✗ Port $port ($agent_name) - NOT RUNNING"
                echo -e "${RED}  → Port is not listening${NC}"
                echo -e "${RED}  → Check agent log: $AGENT_LOG_DIR/${agent_name}.log${NC}"
                if [ -f "$AGENT_LOG_DIR/${agent_name}.log" ]; then
                    echo -e "${RED}  → Last 10 lines of log:${NC}"
                    tail -10 "$AGENT_LOG_DIR/${agent_name}.log" 2>/dev/null | sed 's/^/    /'
                fi
                not_running=$((not_running + 1))
            fi
        fi
        if [ "$VERBOSE" = "1" ]; then
            echo ""
        fi
    done
    
    echo ""
    log_section "HEALTH CHECK SUMMARY"
    log_success "Healthy:     $healthy/26"
    log_warning "Unhealthy:   $unhealthy/26"
    log_error "Not Running: $not_running/26"
    
    local total_ok=$((healthy + unhealthy))
    local percentage=$((total_ok * 100 / 26))
    
    log_info "Overall Status: $percentage% operational"
    
    if [ $healthy -eq 26 ]; then
        log_success "🎉 ALL AGENTS ARE HEALTHY! 🎉"
        return 0
    elif [ $total_ok -ge 20 ]; then
        log_warning "System is operational but some agents need attention"
        return 1
    else
        log_error "System is in degraded state"
        return 2
    fi
}

# ============================================================================
# DASHBOARD MANAGEMENT
# ============================================================================

start_dashboard() {
    log_section "STARTING DASHBOARD UI"
    
    if [ ! -f "start_dashboard.sh" ]; then
        log_warning "start_dashboard.sh not found, skipping dashboard startup"
        return 1
    fi
    
    log_info "Launching dashboard in background..."
    
    local dashboard_log="$MASTER_LOG_DIR/dashboard.log"
    nohup ./start_dashboard.sh > "$dashboard_log" 2>&1 &
    local dashboard_pid=$!
    
    log_success "Dashboard started (PID: $dashboard_pid)"
    log_success "Dashboard log: $dashboard_log"
    
    # Update process tracking
    python3.11 -c "
import json
with open('$PROCESS_TRACKING_FILE', 'r') as f:
    data = json.load(f)
data['dashboard'] = {
    'pid': $dashboard_pid,
    'log_file': '$dashboard_log',
    'started_at': '$(date -Iseconds)'
}
with open('$PROCESS_TRACKING_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"
    
    # Wait for dashboard
    log_info "Waiting for dashboard to be ready (max ${DASHBOARD_STARTUP_WAIT}s)..."
    
    local waited=0
    while [ $waited -lt $DASHBOARD_STARTUP_WAIT ]; do
        if nc -z localhost 5173 2>/dev/null; then
            log_success "Dashboard is ready on http://localhost:5173"
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
        echo -n "."
    done
    
    echo ""
    log_warning "Dashboard did not start within ${DASHBOARD_STARTUP_WAIT}s"
    log_info "Check dashboard log: $dashboard_log"
    return 1
}

# ============================================================================
# FINAL STATUS REPORT
# ============================================================================

generate_status_report() {
    log_section "SYSTEM STATUS REPORT"
    
    local report_file="$MASTER_LOG_DIR/status_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "═══════════════════════════════════════════════════════════════════════════"
        echo "MULTI-AGENT E-COMMERCE PLATFORM - STATUS REPORT"
        echo "═══════════════════════════════════════════════════════════════════════════"
        echo ""
        echo "Generated: $(date)"
        echo "Project Root: $PROJECT_ROOT"
        echo ""
        
        echo "INFRASTRUCTURE:"
        echo "  - PostgreSQL: $(pg_isready -h localhost -p 5432 && echo 'Running' || echo 'Not Running')"
        echo "  - Kafka: $(nc -z localhost 9092 2>/dev/null && echo 'Running' || echo 'Not Running')"
        echo "  - Node.js: $(node --version 2>/dev/null || echo 'Not Installed')"
        echo ""
        
        echo "AGENTS (26 total):"
        for port in {8000..8025}; do
            local agent_name=${AGENT_NAMES[$port]:-"unknown"}
            local status="NOT RUNNING"
            if nc -z localhost $port 2>/dev/null; then
                if curl -s -f -m 5 "http://localhost:$port/health" >/dev/null 2>&1; then
                    status="HEALTHY"
                else
                    status="UNHEALTHY"
                fi
            fi
            printf "  [%-10s] Port %d - %s\n" "$status" "$port" "$agent_name"
        done
        echo ""
        
        echo "DASHBOARD:"
        if nc -z localhost 5173 2>/dev/null; then
            echo "  Status: Running"
            echo "  URL: http://localhost:5173"
        else
            echo "  Status: Not Running"
        fi
        echo ""
        
        echo "LOG FILES:"
        echo "  - Master Log: $STARTUP_LOG"
        echo "  - Agent Logs: $AGENT_LOG_DIR/"
        echo "  - Infrastructure Logs: $INFRASTRUCTURE_LOG_DIR/"
        echo "  - Process Tracking: $PROCESS_TRACKING_FILE"
        echo ""
        
        echo "PROCESS TRACKING:"
        cat "$PROCESS_TRACKING_FILE" | python3.11 -m json.tool
        echo ""
        
        echo "═══════════════════════════════════════════════════════════════════════════"
        
    } | tee "$report_file"
    
    log_success "Status report saved: $report_file"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    # Initialize
    initialize_logging
    
    # Check infrastructure
    check_infrastructure
    
    # Start all agents
    start_all_agents
    
    # Check health
    check_agent_health
    
    # Start dashboard
    start_dashboard
    
    # Generate final report
    generate_status_report
    
    # Final message
    log_section "MASTER LAUNCH COMPLETE!"
    
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    SYSTEM SUCCESSFULLY LAUNCHED!                          ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Access Points:${NC}"
    echo -e "  🌐 Dashboard:    ${GREEN}http://localhost:5173${NC}"
    echo -e "  🔧 Primary API:  ${GREEN}http://localhost:8000${NC}"
    echo -e "  📚 API Docs:     ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${CYAN}Logs:${NC}"
    echo -e "  📋 Master Log:   ${BLUE}$STARTUP_LOG${NC}"
    echo -e "  📁 Agent Logs:   ${BLUE}$AGENT_LOG_DIR/${NC}"
    echo -e "  🔍 Tracking:     ${BLUE}$PROCESS_TRACKING_FILE${NC}"
    echo ""
    echo -e "${CYAN}Management:${NC}"
    echo -e "  Stop agents:     ${YELLOW}./stop_all_agents.sh${NC}"
    echo -e "  Check health:    ${YELLOW}python3.11 check_all_26_agents_health.py${NC}"
    echo ""
}

# Run main function
main

