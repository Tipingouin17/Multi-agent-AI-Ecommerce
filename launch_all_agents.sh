#!/bin/bash

# launch_all_agents.sh
# Script to launch all Python agents concurrently in the background for local development.
# NOTE: This is for convenience and is NOT a production-grade process manager.
# Use start_local_dev.sh first to ensure infrastructure is running.

# --- Configuration ---
# List of all agent files to launch.
# NOTE: Ensure these paths are correct relative to the project root.
AGENTS=(
    "agents/order_agent_production_v2.py"
    "agents/inventory_agent.py"
    "agents/backoffice_agent_production.py"
    "agents/customer_agent_enhanced.py"
    "agents/transport_management_agent_enhanced.py"
    "agents/warehouse_agent_production.py"
    "agents/after_sales_agent_production.py"
    "agents/promotion_agent.py"
    "agents/dynamic_pricing_agent.py"
    "agents/compliance_agent.py"
    "agents/fraud_detection_agent.py"
    "agents/monitoring_agent.py"
    "agents/recommendation_agent.py"
    "agents/quality_control_agent_production.py"
    "agents/risk_anomaly_detection_agent.py"
    "agents/demand_forecasting_agent.py"
    "agents/marketplace_connector_agent.py"
)

# --- Main Script ---

# 1. Load Environment Variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env"
    source ./.env
else
    echo "WARNING: .env file not found. Using default environment settings. This may cause database connection failures."
fi

echo "--- Launching All Agents Concurrently ---"

# 2. Check for virtual environment activation
if [ -z "$VIRTUAL_ENV" ]; then
    echo "WARNING: Virtual environment is not active. Attempting to activate..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "Virtual environment activated."
    elif [ -f "venv/Scripts/activate" ]; then
        # For Windows Git Bash/WSL compatibility
        source venv/Scripts/activate
        echo "Virtual environment activated."
    else
        echo "ERROR: Virtual environment not found. Please run 'source venv/bin/activate' manually."
        exit 1
    fi
fi

# 2. Launch API in background (optional, uncomment if desired)
# echo "Launching API in background..."
# nohup uvicorn api.main_secured:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
# API_PID=$!
# echo "API started with PID: $API_PID (logging to api.log)"

# 3. Launch all agents
for AGENT_FILE in "${AGENTS[@]}"; do
    AGENT_NAME=$(basename "${AGENT_FILE}" .py)
    LOG_FILE="logs/${AGENT_NAME}.log"
    
    echo "Starting ${AGENT_NAME}..."
    
    # Use nohup to run in background, redirecting output to a specific log file
    # and appending the PID to a file for easy cleanup.
    nohup python "${AGENT_FILE}" > "${LOG_FILE}" 2>&1 &
    AGENT_PID=$!
    
    echo "${AGENT_PID}" >> agent_pids.txt
    echo "  -> PID: ${AGENT_PID} (logging to ${LOG_FILE})"
done

echo "--- All agents launched in the background. ---"
echo "To stop all agents, run: kill \$(cat agent_pids.txt) && rm agent_pids.txt"
echo "To view logs, check the 'logs/' directory."
