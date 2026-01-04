# Run this script to set up and start the frontend server

Write-Host "=== Plum OPD Claim Adjudication - Frontend Setup ===" -ForegroundColor Cyan

# Check Node.js
Write-Host "`nChecking Node.js..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}
Write-Host "Found: Node.js $nodeVersion" -ForegroundColor Green

# Navigate to frontend
Set-Location -Path $PSScriptRoot\frontend

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
npm install

# Start development server
Write-Host "`n=== Starting Frontend Server ===" -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

npm run dev
