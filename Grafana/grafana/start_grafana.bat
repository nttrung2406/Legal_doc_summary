@echo off
setlocal


set "SCRIPT_DIR=%~dp0"


if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"


set "GF_PATHS_PROVISIONING=%SCRIPT_DIR%\conf\provisioning"
set "GF_PATHS_DATA=%SCRIPT_DIR%\data"
set "GF_PATHS_LOGS=%SCRIPT_DIR%\logs"
set "GF_PATHS_PLUGINS=%SCRIPT_DIR%\plugins"


cd /d "%SCRIPT_DIR%"
bin\grafana-server.exe --homepath="%SCRIPT_DIR%"

endlocal
