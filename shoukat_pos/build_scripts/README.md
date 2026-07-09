# Build Scripts for Shoukat POS

This directory contains build and deployment scripts for creating distributable packages.

## Quick Start

### Windows (PowerShell)
```powershell
.\build.ps1
```

### Linux/macOS (Bash)
```bash
./build.sh
```

## Build Scripts

- `build.ps1` - Windows PowerShell build script
- `build.sh` - Linux/macOS Bash build script
- `ShoukatPOS.spec` - PyInstaller specification file

## Requirements

Before building, ensure you have:
1. Python 3.9+ installed
2. All dependencies: `pip install -r requirements.txt`
3. PyInstaller: `pip install pyinstaller`

## Output

The build process creates:
- `dist/ShoukatPOS/` - Application directory with executable
- `dist/ShoukatPOS.exe` - Single executable (Windows)
- `build/` - Temporary build files (can be deleted after successful build)

## Troubleshooting

### Missing DLLs
If the built executable fails with missing DLL errors, try:
```bash
pyinstaller --clean ShoukatPOS.spec
```

### Antivirus False Positives
Some antivirus software may flag PyInstaller executables. Add an exception or sign the executable with a code signing certificate.

### Large Executable Size
To reduce size:
1. Remove unused hidden imports from `.spec` file
2. Use UPX compression (enabled by default)
3. Exclude test modules in `excludes` list
