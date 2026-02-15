@echo off
echo Starting MCSManager Production...

start "MCSManager Daemon" cmd /k "cd production-code\daemon && node app.js"
timeout /t 5 /nobreak
start "MCSManager Web" cmd /k "cd production-code\web && node app.js"

echo.
echo Services started!
echo Daemon: http://localhost:24444
echo Web Panel: http://localhost:23333
echo.
echo Press any key to exit (services will keep running)...
pause
