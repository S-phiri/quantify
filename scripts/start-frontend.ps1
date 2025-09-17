# Start Next.js Frontend
Write-Host "Starting Next.js Frontend..." -ForegroundColor Green

# Navigate to project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Navigate to frontend directory
Set-Location frontend

# Start Next.js development server
Write-Host "Starting Next.js server on localhost:3000..." -ForegroundColor Yellow
npm run dev
