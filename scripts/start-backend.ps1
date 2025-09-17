# Start Django Backend
Write-Host "Starting Django Backend..." -ForegroundColor Green

# Navigate to project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1

# Start Django server
Write-Host "Starting Django server on 127.0.0.1:8000..." -ForegroundColor Yellow
python manage.py runserver 127.0.0.1:8000
