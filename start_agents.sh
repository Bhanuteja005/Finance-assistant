#!/bin/bash

# Start all agents in the background
echo "Starting Finance Assistant Multi-Agent System..."

# Create logs directory
mkdir -p logs

# Start API Agent
echo "Starting API Agent..."
python agents/api_agent.py &
API_PID=$!

# Start Retriever Agent
echo "Starting Retriever Agent..."
python agents/retriever_agent.py &
RETRIEVER_PID=$!

# Start Language Agent
echo "Starting Language Agent..."
python agents/language_agent.py &
LANGUAGE_PID=$!

# Start Voice Agent
echo "Starting Voice Agent..."
python agents/voice_agent.py &
VOICE_PID=$!

# Wait a bit for agents to start
sleep 5

# Start Orchestrator
echo "Starting Orchestrator..."
python orchestrator/main.py &
ORCHESTRATOR_PID=$!

# Wait a bit more
sleep 3

# Start Streamlit App
echo "Starting Streamlit App..."
streamlit run streamlit_app/main.py --server.port=8501 --server.address=0.0.0.0 &
STREAMLIT_PID=$!

echo "All services started!"
echo "API Agent PID: $API_PID"
echo "Retriever Agent PID: $RETRIEVER_PID"
echo "Language Agent PID: $LANGUAGE_PID"
echo "Voice Agent PID: $VOICE_PID"
echo "Orchestrator PID: $ORCHESTRATOR_PID"
echo "Streamlit App PID: $STREAMLIT_PID"

echo ""
echo "Access the application at: http://localhost:8501"
echo ""
echo "To stop all services, run: ./stop_agents.sh"

# Save PIDs to file for cleanup
echo "$API_PID $RETRIEVER_PID $LANGUAGE_PID $VOICE_PID $ORCHESTRATOR_PID $STREAMLIT_PID" > .agent_pids

# Wait for user input to keep script running
read -p "Press Enter to stop all services..."

# Kill all processes
kill $API_PID $RETRIEVER_PID $LANGUAGE_PID $VOICE_PID $ORCHESTRATOR_PID $STREAMLIT_PID
echo "All services stopped."
