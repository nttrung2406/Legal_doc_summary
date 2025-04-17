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

:: Set paths for RabbitMQ and Grafana
set RABBITMQ_PATH="E:\RabbitMQ_Server\rabbitmq_server-4.0.5\sbin\rabbitmq-server.bat"
set RABBITMQ_CTL="E:\RabbitMQ_Server\rabbitmq_server-4.0.5\sbin\rabbitmqctl.bat"
set GRAFANA_PATH="E:\Grafa\grafana\bin\grafana-server.exe"
set PROMETHEUS_PATH="E:\Prometheus\prometheus.exe"


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

:: Start Prometheus
echo Starting Prometheus...
if exist %PROMETHEUS_PATH% (
    start cmd /k %PROMETHEUS_PATH% --config.file=backend/prometheus.yml
) else (
    echo Warning: Prometheus not found at %PROMETHEUS_PATH%
    echo Please install Prometheus or update the path in start.bat
)

:: Start Grafana
echo Starting Grafana...
if exist %GRAFANA_PATH% (
    start cmd /k %GRAFANA_PATH%
) else (
    echo Warning: Grafana not found at %GRAFANA_PATH%
    echo Please install Grafana or update the path in start.bat
)

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
echo Prometheus will be available at: http://localhost:9090
echo Grafana will be available at: http://localhost:3000
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:5173
echo.
echo Press Ctrl+C in each window to stop the servers.
echo.
pause 