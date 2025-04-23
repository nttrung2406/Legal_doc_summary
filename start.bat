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
echo Installing backend dependencies...
@REM cd backend
@REM pip install -r requirements.txt
cd ..

:: Check if node_modules exists
if not exist "frontend-react\node_modules" (
    echo Installing frontend dependencies...
    cd frontend-react
    npm install
    cd ..
)

set RABBITMQ_PATH="E:\RabbitMQ_Server\rabbitmq_server-4.0.5\sbin\rabbitmq-server.bat"
set RABBITMQ_CTL="E:\RabbitMQ_Server\rabbitmq_server-4.0.5\sbin\rabbitmqctl.bat"
echo Using RabbitMQ: %RABBITMQ_PATH%

:: Start RabbitMQ server
echo Starting RabbitMQ server...
if exist %RABBITMQ_PATH% (
    start cmd /k %RABBITMQ_PATH%
) else (
    echo Warning: RabbitMQ not found at %RABBITMQ_PATH%
    echo Please install RabbitMQ or update the path in start.bat
)

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