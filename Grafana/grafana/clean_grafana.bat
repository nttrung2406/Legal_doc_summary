@echo off
echo Cleaning Grafana plugins and cache...

:: Remove plugins directory contents
if exist "plugins" (
    echo Removing plugins directory contents...
    rmdir /s /q "plugins"
    mkdir "plugins"
)

:: Remove cache
if exist "data\cache" (
    echo Removing cache...
    rmdir /s /q "data\cache"
)

:: Remove plugin cache
if exist "data\plugin-cache" (
    echo Removing plugin cache...
    rmdir /s /q "data\plugin-cache"
)

echo Cleanup complete! 