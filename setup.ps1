# Quick Setup Script for VENOM Dashboard
# Run this script to set up everything automatically

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VENOM Dashboard - Quick Setup" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found! Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "`n[2/5] Installing Python dependencies..." -ForegroundColor Green
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check templates folder
Write-Host "`n[3/5] Checking templates folder..." -ForegroundColor Green
if (Test-Path "templates") {
    $templateCount = (Get-ChildItem "templates\*.html").Count
    Write-Host "✓ Found $templateCount HTML templates" -ForegroundColor Green
} else {
    Write-Host "✗ Templates folder not found!" -ForegroundColor Red
    exit 1
}

# Check static folder
Write-Host "`n[4/5] Checking static folder..." -ForegroundColor Green
if (Test-Path "static") {
    Write-Host "✓ Static folder exists" -ForegroundColor Green
} else {
    Write-Host "! Creating static folder..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "static" | Out-Null
}

# Start Flask server
Write-Host "`n[5/5] Starting Flask server..." -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Server will start now!" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 URL: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "🔐 Login credentials in SETUP_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Run Flask app
python app.py
