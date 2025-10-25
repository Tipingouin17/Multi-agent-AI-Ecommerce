#!/bin/bash
# Script to start all multi-agent system components for local development

# Exit immediately if a command exits with a non-zero status.
set -e

echo "================================================================================"
echo "STARTING MULTI-AGENT E-COMMERCE LOCAL ENVIRONMENT"
echo "================================================================================"

# --- Infrastructure Startup (Simulated/Placeholder) ---
echo "Starting Infrastructure (PostgreSQL, Kafka, Redis)..."
echo "INFO: Assuming PostgreSQL, Kafka, and Redis are running on default ports (5432, 9092, 6379)."
echo "INFO: If tests fail, please ensure these services are running."

# --- Agent Startup (Running in background using Uvicorn) ---
echo "Starting Agents in the background..."

# Function to start an agent
start_agent() {
    local agent_name=$1
    local port=$2
    local module_path="multi_agent_ecommerce.agents.${agent_name}:app"
    local log_file="logs/${agent_name}.log"
    
    echo "Starting $agent_name Agent on port $port..."
    
    # Use nohup to run the process in the background and detach it
    # We assume a standard FastAPI/Uvicorn setup where the agent module exposes an 'app' instance.
    nohup uvicorn "${module_path}" --host 0.0.0.0 --port "${port}" > "${log_file}" 2>&1 &
    
    echo "PID: $!"
}

# List of Agents and their ports (from production_validation_suite.py)
AGENTS=(
    "monitoring 8000"
    "order 8001"
    "product 8002"
    "marketplace 8003"
    "customer 8004"
    "inventory 8005"
    "transport 8006"
    "payment 8007"
    "warehouse 8008"
    "document 8009"
    "fraud 8010"
    "risk 8011"
    "knowledge 8012"
    "aftersales 8020"
    "backoffice 8021"
    "quality 8022"
)

# Create logs directory if it doesn't exist
mkdir -p logs

# Start all agents
for agent_info in "${AGENTS[@]}"; do
    start_agent $agent_info
done

# --- UI (Vite) Startup (Running in background) ---
echo "Starting UI (Vite) on port 5173..."
# We assume the UI is a Node.js/Vite project and is run via 'npm run dev' or 'pnpm run dev'
# Since we don't have the package.json, we will assume the command is 'npm run dev'
# NOTE: This will only work if the UI project is properly set up.

# Check if npm is available and run the dev script
if command -v npm &> /dev/null; then
    echo "Running 'npm install' and 'npm run dev' for UI..."
    (
        cd ui # Assuming the UI project is in a 'ui' subdirectory
        npm install > ../logs/ui_npm_install.log 2>&1
        nohup npm run dev > ../logs/ui.log 2>&1 &
        echo "UI PID: $!"
    )
else
    echo "WARNING: npm not found. UI will not be started."
fi


echo "All components started (or attempted to start) in the background."
echo "The Python validation script will now wait for them to become healthy."

# Final message before exiting the script
echo "Startup script finished."

