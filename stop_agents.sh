#!/bin/bash

echo "Stopping Finance Assistant Multi-Agent System..."

# Read PIDs from file if it exists
if [ -f .agent_pids ]; then
    PIDS=$(cat .agent_pids)
    for PID in $PIDS; do
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping process $PID..."
            kill $PID
        fi
    done
    rm .agent_pids
fi

# Also kill any remaining processes by name
pkill -f "api_agent.py"
pkill -f "retriever_agent.py"
pkill -f "language_agent.py"
pkill -f "voice_agent.py"
pkill -f "orchestrator/main.py"
pkill -f "streamlit_app/main.py"

echo "All services stopped."
