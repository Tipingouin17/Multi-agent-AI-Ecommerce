#!/bin/bash

# start_local_dev.sh
# Local Development Startup Script for Multi-Agent E-commerce
# Designed to work on Linux, macOS, and Windows (via WSL or Git Bash).

# --- Configuration ---
COMPOSE_FILE="infrastructure/docker-compose.yml"
PROJECT_NAME="multi-agent-ecommerce"

# --- Functions ---

# Function to display error and exit
error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null
    then
        error_exit "$1 could not be found. Please ensure Docker Desktop is running."
    fi
}

# --- Main Script ---

# 1. Load Environment Variables from .env file
if [ -f "../.env" ]; then
    echo "Loading environment variables from ../.env"
    source ../.env
else
    echo "WARNING: .env file not found. Using default environment settings."
fi

echo "--- Starting Local Development Environment Setup ---"

# 1. Check Prerequisites
check_command "docker"
check_command "docker-compose"

# 2. Start Infrastructure Services (Postgres, Kafka, Redis, Monitoring Stack)
echo "Starting infrastructure services via Docker Compose..."
docker-compose -f "${COMPOSE_FILE}" up -d || error_exit "Failed to start Docker Compose services."

# 3. Wait for Infrastructure to be ready (Simple wait)
echo "Waiting 30 seconds for services (Postgres, Kafka) to initialize..."
sleep 30

# 4. Initialize Database and Kafka Topics
echo "Initializing database and Kafka topics..."
# NOTE: This assumes you have a local Python environment set up to run these commands
# If you prefer to run this inside a temporary container, modify the command below.
# Assuming Python environment is active:
python init_database.py || error_exit "Database initialization failed."
python init_kafka_topics.py || error_exit "Kafka topics initialization failed."

# 5. Instructions for Running Agents Locally
echo "--- Infrastructure is READY ---"
echo " "
echo "To run the application, you must now start the Python agents and API in your local development environment."
echo " "
echo "1. **Activate Virtual Environment** (If you haven't already):"
echo "   source venv/bin/activate"
echo " "
echo "2. **Start the API (with hot-reloading):**"
echo "   uvicorn api.main_secured:app --reload --host 0.0.0.0 --port 8000"
echo " "
echo "3. **Start the Agents (in separate terminals):**"
echo "   python agents/order_agent_production_v2.py"
echo "   python agents/inventory_agent.py"
echo "   python agents/backoffice_agent_production.py"
echo "   # ... and so on for all other agents."
echo " "
echo "4. **Stop the environment when done:**"
echo "   docker-compose -f ${COMPOSE_FILE} down"
echo " "
echo "Happy Coding!"
