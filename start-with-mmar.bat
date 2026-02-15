@echo off
echo ========================================
echo MCSManager-MCT with mmar Tunnel
echo ========================================
echo.

REM Start MCSManager services
echo Starting MCSManager Daemon...
start "MCSManager Daemon" cmd /k "cd production-code\daemon && node app.js"

echo Waiting for daemon to start...
timeout /t 5 /nobreak >nul

echo Starting MCSManager Web Panel...
start "MCSManager Web" cmd /k "cd production-code\web && node app.js"

echo Waiting for web panel to start...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Services Started!
echo ========================================
echo Daemon: http://localhost:24444
echo Web Panel: http://localhost:23333
echo.

REM Check if mmar is installed
where mmar >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] mmar is not installed!
    echo.
    echo Please install mmar from: https://mmar.dev
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)

echo Starting mmar tunnel on port 23333...
echo.
echo ========================================
echo IMPORTANT: Copy the tunnel URL below
echo and share it with your users!
echo ========================================
echo.

REM Start mmar tunnel (this will block and show the URL)
mmar client --local-port 23333

REM This line only runs if mmar exits
echo.
echo mmar tunnel stopped.
pause
