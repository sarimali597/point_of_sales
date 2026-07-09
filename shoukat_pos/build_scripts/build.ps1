# Build script for Shoukat POS on Windows (PowerShell)
# Usage: .\build.ps1 [-Clean] [-Debug]

param(
    [switch]$Clean,
    [switch]$Debug
)

$ErrorActionPreference = "Stop"

# Configuration
$AppName = "ShoukatPOS"
$SpecFile = "ShoukatPOS.spec"
$MainScript = "shoukat_pos\main.py"
$DistDir = "dist"
$BuildDir = "build"

# ANSI color codes (Windows 10+)
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Reset = "`e[0m"

Write-Host "==================================" -ForegroundColor Green
Write-Host "  Shoukat POS Build Script" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""

# Check Python version
try {
    $PythonVersion = python --version 2>&1
    Write-Host "$PythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Error: Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check if running in virtual environment
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Warning: Not running in a virtual environment" -ForegroundColor Yellow
    Write-Host "Consider creating one with: python -m venv venv"
}

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
    Write-Host "✓ Clean complete" -ForegroundColor Green
}

# Install/upgrade build dependencies
Write-Host "Checking build dependencies..." -ForegroundColor Yellow
pip install --quiet pyinstaller>=5.0

# Verify main script exists
if (-not (Test-Path $MainScript)) {
    Write-Host "Error: Main script not found at $MainScript" -ForegroundColor Red
    exit 1
}

# Verify spec file exists
if (-not (Test-Path $SpecFile)) {
    Write-Host "Error: Spec file not found at $SpecFile" -ForegroundColor Red
    exit 1
}

# Build command
$BuildCmd = "pyinstaller"

if ($Debug) {
    $BuildCmd += " --debug=all"
    Write-Host "Building in DEBUG mode" -ForegroundColor Yellow
} else {
    Write-Host "Building in RELEASE mode" -ForegroundColor Yellow
}

# Run PyInstaller
Write-Host "Running PyInstaller..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..."
Write-Host ""

& pyinstaller --noconfirm $SpecFile

# Check build success
if (Test-Path "$DistDir\$AppName") {
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Green
    Write-Host "  ✓ Build Successful!" -ForegroundColor Green
    Write-Host "==================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable location:" -ForegroundColor White
    Write-Host "  $DistDir\$AppName\$AppName.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To run the application:" -ForegroundColor White
    Write-Host "  cd $DistDir\$AppName" -ForegroundColor Cyan
    Write-Host "  .\$AppName.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Note: The first launch may be slow as libraries are extracted." -ForegroundColor Yellow
    
    # Open dist folder
    explorer.exe "$DistDir\$AppName"
    
    exit 0
} else {
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Red
    Write-Host "  ✗ Build Failed" -ForegroundColor Red
    Write-Host "==================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the error messages above."
    Write-Host "Common issues:"
    Write-Host "  - Missing dependencies (run: pip install -r requirements.txt)"
    Write-Host "  - Import errors in source files"
    Write-Host "  - Missing asset files"
    Write-Host ""
    Write-Host "Try building with -Debug flag for more details:"
    Write-Host "  .\build.ps1 -Debug"
    
    exit 1
}
