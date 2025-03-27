@echo off
echo Starting servers...

:: Start backend server
start cmd /k "cd backend && uvicorn main:app --reload --port 8000"

:: Start frontend server
start cmd /k "cd frontend && streamlit run app.py --server.port 8501"

echo Servers started. Press Ctrl+C to stop all servers.
pause 