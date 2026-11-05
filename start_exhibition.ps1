# Autonomous DevOps Swarm - PowerShell Live Presentation Launcher
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "      AUTONOMOUS DEVOPS SWARM - LIVE EXHIBITION PRESENTATION" -ForegroundColor Green
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Starting Autonomous DevOps Backend (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; .\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "[2/3] Starting Interactive DevOps Frontend (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; npm --prefix frontend run dev"

Write-Host "[3/3] Waiting for servers to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Opening Cockpit at http://localhost:5173 ..." -ForegroundColor Green
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "              SWARM COCKPIT READY FOR EVALUATORS!" -ForegroundColor Green
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presentation Steps:" -ForegroundColor White
Write-Host "1. Click 'Demo Access' to enter the cockpit." -ForegroundColor Gray
Write-Host "2. Enter mission: 'Build a e commerce website' -> Click 'Launch Mission ->'" -ForegroundColor Gray
Write-Host "3. Watch all 8 agents complete across Dev & Ops teams." -ForegroundColor Gray
Write-Host "4. Click 'Preview Website' to show live storefront, cart, and checkout." -ForegroundColor Gray
Write-Host ""
