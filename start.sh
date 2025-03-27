#!/bin/bash

cleanup() {
    echo "Stopping all servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Set up trap for cleanup on script termination
trap cleanup SIGINT SIGTERM

# Start backend server
echo "Starting backend server..."
cd backend
uvicorn main:app --reload --port 8000 &

# Start frontend server
echo "Starting frontend server..."
cd ../frontend
streamlit run app.py --server.port 8501 &

# Wait for all background processes
wait 