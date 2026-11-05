@echo off
title Autonomous DevOps Swarm - Exhibition Launcher
color 0A
cls
echo =========================================================================
echo       AUTONOMOUS DEVOPS SWARM - LIVE EXHIBITION PRESENTATION
echo =========================================================================
echo.
echo [1/3] Starting Autonomous DevOps Backend (Port 8000)...
start "DevOps Swarm - Backend (Port 8000)" cmd /c "cd /d %~dp0 && .\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/3] Starting Interactive DevOps Frontend (Port 5173)...
start "DevOps Swarm - Frontend (Port 5173)" cmd /c "cd /d %~dp0 && npm --prefix frontend run dev"

echo [3/3] Waiting for servers to initialize...
timeout /t 3 /nobreak >nul

echo.
echo Launching Google Chrome / Default Browser at http://localhost:5173 ...
start http://localhost:5173

echo.
echo =========================================================================
echo               SWARM COCKPIT READY FOR EVALUATORS!
echo =========================================================================
echo.
echo PRESENTATION CHEAT SHEET:
echo 1. Sign In / Click "Demo Access" to enter the Cockpit.
echo 2. Recommended Live Missions to Demonstrate:
echo    - "Build a e commerce website" (Produces Live Store, Cart, Checkout)
echo    - "Build a student management portal" (Produces Academic Portal & Grades)
echo    - "Build a FreshSip juice center website" (Produces Juice Bar Catalog)
echo 3. Point out the 8 Collaborating Agents:
echo    - Dev Team: Planning, Coding, Build, Testing
echo    - Ops Team: Security, Release, Deploy, Monitor
echo 4. Click any Agent stage to inspect its skills.sh instructions and logs.
echo 5. Click "Preview Website" to show the live interactive generated app!
echo.
echo Both servers are running in separate background windows.
echo Keep this window open during your presentation.
pause
