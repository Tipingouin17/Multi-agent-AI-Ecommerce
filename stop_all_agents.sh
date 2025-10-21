#!/bin/bash
# Stop All Agents Script

echo "Stopping all agents..."

if [ -f logs/agent_pids.txt ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping agent PID: $pid"
            kill $pid
        fi
    done < logs/agent_pids.txt
    rm logs/agent_pids.txt
else
    echo "No PID file found, killing all python agent processes..."
    pkill -f "python3 agents/"
fi

echo "✅ All agents stopped!"

