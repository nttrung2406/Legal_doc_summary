@echo off
echo Starting ReadLaw servers...

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if backend dependencies are installed
if not exist "backend\__pycache__" (
    echo Installing backend dependencies...
    cd backend
    pip install -r requirements.txt
    cd ..
)

:: Check if node_modules exists
if not exist "frontend-react\node_modules" (
    echo Installing frontend dependencies...
    cd frontend-react
    npm install
    cd ..
)

:: Start RabbitMQ server (if not running)
echo Starting RabbitMQ server...
start cmd /k "rabbitmq-server"

:: Wait for RabbitMQ to start
timeout /t 5 /nobreak >nul

:: Start Celery worker
echo Starting Celery worker...
start cmd /k "cd backend && celery -A tasks worker --loglevel=info"

:: Start Celery beat for scheduled tasks
echo Starting Celery beat...
start cmd /k "cd backend && celery -A tasks beat --loglevel=info"

:: Start backend server
echo Starting backend server...
start cmd /k "cd backend && uvicorn main:app --reload"

:: Wait a moment to ensure backend starts
timeout /t 2 /nobreak >nul

:: Start frontend server
echo Starting frontend server...
start cmd /k "cd frontend-react && npm run dev"

echo.
echo Servers are starting...
echo RabbitMQ will be available at: http://localhost:15672
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:5173
echo.
echo Press Ctrl+C in each window to stop the servers.
echo.
pause 