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
@REM echo Installing backend dependencies...
@REM cd backend
@REM pip install -r requirements.txt
@REM cd ..

:: Check if node_modules exists
if not exist "frontend-react\node_modules" (
    echo Installing frontend dependencies...
    cd frontend-react
    npm install
    cd ..
)

set "SCRIPT_DIR=%~dp0"
set "RABBITMQ_PATH=%SCRIPT_DIR%RabbitMQ_Server\rabbitmq_server-4.0.5\sbin\rabbitmq-server.bat"
set "RABBITMQ_CTL=%SCRIPT_DIR%RabbitMQ_Server\rabbitmq_server-4.0.5\sbin\rabbitmqctl.bat"
set "PROMETHEUS_PATH=%SCRIPT_DIR%Prometheus\prometheus.exe"
set "GRAFANA_HOME=%SCRIPT_DIR%Grafana\grafana"
set "GRAFANA_PATH=%GRAFANA_HOME%\bin\grafana.exe"
set "GRAFANA_SV_PATH=%GRAFANA_HOME%\bin\grafana-server.exe"

echo Using RabbitMQ: %RABBITMQ_PATH%
echo Using Prometheus: %PROMETHEUS_PATH%
echo Using Grafana: %GRAFANA_SV_PATH%

:: Start RabbitMQ server
echo Starting RabbitMQ server...
if exist %RABBITMQ_PATH% (
    start cmd /k %RABBITMQ_PATH%
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

echo Starting monitoring services...

:: Start Prometheus
echo Starting Prometheus...
start cmd /k "%PROMETHEUS_PATH% --config.file=%SCRIPT_DIR%Prometheus\prometheus.yml"

:: Start Grafana
echo Starting Grafana...
start cmd /k "cd %GRAFANA_HOME% && call start_grafana.bat"

:: Wait for services to start
timeout /t 5 /nobreak >nul

echo.
echo Servers are starting...
echo RabbitMQ will be available at: http://localhost:15672
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:5173
echo Prometheus will be available at: http://localhost:9090
echo Grafana will be available at: http://localhost:3000
echo.
echo Press Ctrl+C in each window to stop the servers.
echo.
pause