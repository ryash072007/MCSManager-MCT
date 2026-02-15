@echo off
echo ========================================
echo MCSManager-MCT Production
echo ========================================
echo.

echo Starting MCSManager Daemon...
start "MCSManager Daemon" cmd /k "cd daemon && node app.js"

echo Waiting for daemon to start...
timeout /t 5 /nobreak >nul

echo Starting MCSManager Web Panel...
start "MCSManager Web" cmd /k "cd web && node app.js"

echo Waiting for web panel to start...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Services Started!
echo ========================================
echo Daemon: http://localhost:24444
echo Web Panel: http://localhost:23333
echo.
echo Now start mmar tunnel with:
echo   mmar client --local-port 23333
echo.
pause
