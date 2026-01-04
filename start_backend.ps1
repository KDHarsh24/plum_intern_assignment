# Run this script to set up and start the backend server

Write-Host "=== Plum OPD Claim Adjudication - Backend Setup ===" -ForegroundColor Cyan

# Check Python
Write-Host "`nChecking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Navigate to backend
Set-Location -Path $PSScriptRoot\backend

# Create virtual environment if not exists
if (-not (Test-Path "venv")) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check Tesseract
Write-Host "`nChecking Tesseract OCR..." -ForegroundColor Yellow
$tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
if (Test-Path $tesseractPath) {
    Write-Host "Tesseract found at: $tesseractPath" -ForegroundColor Green
} else {
    Write-Host "WARNING: Tesseract not found at default path." -ForegroundColor Yellow
    Write-Host "Please install from: https://github.com/UB-Mannheim/tesseract/releases" -ForegroundColor Yellow
    Write-Host "Or update TESSERACT_CMD in backend/app/config.py" -ForegroundColor Yellow
}

# Check Ollama
Write-Host "`nChecking Ollama..." -ForegroundColor Yellow
try {
    $ollamaResponse = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET -ErrorAction Stop
    Write-Host "Ollama is running!" -ForegroundColor Green
    Write-Host "Available models: $($ollamaResponse.models.name -join ', ')" -ForegroundColor Cyan
} catch {
    Write-Host "WARNING: Ollama not running. System will use regex fallback." -ForegroundColor Yellow
    Write-Host "To enable AI extraction:" -ForegroundColor Yellow
    Write-Host "  1. Install Ollama from https://ollama.ai" -ForegroundColor Yellow
    Write-Host "  2. Run: ollama pull mistral" -ForegroundColor Yellow
    Write-Host "  3. Run: ollama serve" -ForegroundColor Yellow
}

# Start server
Write-Host "`n=== Starting Backend Server ===" -ForegroundColor Green
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
