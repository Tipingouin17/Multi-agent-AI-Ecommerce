#!/bin/bash
# Corrected script to start all multi-agent system components for local development

# --- Configuration ---
AGENT_MODULES=(
    "monitoring_agent"
    "order_agent_production_v2"
    "product_agent_production"
    "inventory_agent"
    "warehouse_agent_production"
    "payment_agent_enhanced"
    "transport_management_agent_enhanced"
    "marketplace_connector_agent"
    "customer_agent_enhanced"
    "fraud_detection_agent"
    "risk_anomaly_detection_agent"
    "backoffice_agent_production"
    "knowledge_management_agent"
    "quality_control_agent_production"
    "promotion_agent"
    "recommendation_agent"
)
START_PORT=8000
END_PORT=$((START_PORT + ${#AGENT_MODULES[@]} - 1))
LOG_DIR="./logs/agents"

# --- Functions ---

# Function to kill all running agents
cleanup() {
    echo ""
    echo "--- Cleaning up running agents (Ports $START_PORT-$END_PORT) ---"
    for port in $(seq $START_PORT $END_PORT); do
        fuser -k $port/tcp 2>/dev/null
    done
    echo "Cleanup complete."
}

# Trap signals to ensure cleanup runs on exit
trap cleanup EXIT

# --- Main Execution ---

echo "================================================================================"
echo "STARTING MULTI-AGENT E-COMMERCE LOCAL ENVIRONMENT"
echo "================================================================================"

# 1. Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
echo "PYTHONPATH set to include project root."

# 2. Infrastructure Startup (Placeholder - requires Docker/Manual setup)
echo ""
echo "--- Infrastructure Startup (Requires Docker Compose or Manual Setup) ---"
echo "INFO: Please ensure PostgreSQL (5432), Kafka (9092), and Redis (6379) are running."
echo "INFO: Skipping infrastructure startup as it is external to this script."

# 3. Agent Startup
echo ""
echo "--- Starting Agents (Ports $START_PORT to $END_PORT) ---"
mkdir -p $LOG_DIR

CURRENT_PORT=$START_PORT
for module in "${AGENT_MODULES[@]}"; do
    AGENT_NAME=$(echo $module | sed 's/_agent.*//')
    MODULE_PATH="agents.$module:app"
    
    echo "Starting $AGENT_NAME Agent on port $CURRENT_PORT..."
    
    # Run uvicorn in the background, redirecting output to a log file
    # We use nohup to ensure the process continues even if the terminal is closed
    nohup uvicorn $MODULE_PATH --host 0.0.0.0 --port $CURRENT_PORT --workers 1 > $LOG_DIR/$AGENT_NAME.log 2>&1 &
    
    PID=$!
    echo "  -> PID: $PID"
    
    CURRENT_PORT=$((CURRENT_PORT + 1))
done

echo ""
echo "--- Agent Startup Complete ---"
echo "All agents are running in the background. Check logs in $LOG_DIR"
echo "To stop all agents, press Ctrl+C or run: ./scripts/start_local_dev.sh cleanup"
echo "Waiting 10 seconds for agents to initialize..."
sleep 10

# 4. UI Startup (Placeholder)
echo ""
echo "--- UI Startup (Placeholder) ---"
echo "INFO: Assuming UI is started via 'npm run dev' or similar on port 5173."
echo "INFO: Skipping UI startup as it is external to this script."

echo ""
echo "================================================================================"
echo "PLATFORM STARTUP FINISHED. Agents are running in the background."
echo "================================================================================"

# Prevent the script from exiting immediately so the trap can be triggered
# This is mainly for interactive use.
# If the script is run in a non-interactive shell, it will exit and the trap will run.
if [[ $- == *i* ]]; then
    echo "Press Ctrl+C to stop all agents and exit."
    wait
fi

