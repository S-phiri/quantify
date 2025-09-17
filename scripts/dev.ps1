# Start both Backend and Frontend
Write-Host "Starting Development Environment..." -ForegroundColor Cyan

# Navigate to project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Start backend in background
Write-Host "Starting Django Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-backend.ps1"

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend in background
Write-Host "Starting Next.js Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-frontend.ps1"

Write-Host "Both servers are starting..." -ForegroundColor Cyan
Write-Host "Django: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Next.js: http://localhost:3000" -ForegroundColor Yellow
