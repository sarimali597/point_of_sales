#!/bin/bash
# Build script for Shoukat POS on Linux/macOS
# Usage: ./build.sh [--clean] [--debug]

set -e  # Exit on error

# Configuration
APP_NAME="ShoukatPOS"
SPEC_FILE="ShoukatPOS.spec"
MAIN_SCRIPT="shoukat_pos/main.py"
DIST_DIR="dist"
BUILD_DIR="build"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
CLEAN_BUILD=false
DEBUG_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--clean] [--debug]"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}  Shoukat POS Build Script${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${YELLOW}Python version: ${PYTHON_VERSION}${NC}"

# Check if running in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Not running in a virtual environment${NC}"
    echo "Consider creating one with: python3 -m venv venv"
fi

# Clean previous builds if requested
if [ "$CLEAN_BUILD" = true ]; then
    echo -e "${YELLOW}Cleaning previous builds...${NC}"
    rm -rf "$DIST_DIR" "$BUILD_DIR"
    echo "✓ Clean complete"
fi

# Install/upgrade build dependencies
echo -e "${YELLOW}Checking build dependencies...${NC}"
pip install --quiet pyinstaller>=5.0

# Verify main script exists
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo -e "${RED}Error: Main script not found at $MAIN_SCRIPT${NC}"
    exit 1
fi

# Verify spec file exists
if [ ! -f "$SPEC_FILE" ]; then
    echo -e "${RED}Error: Spec file not found at $SPEC_FILE${NC}"
    exit 1
fi

# Build command
BUILD_CMD="pyinstaller"

if [ "$DEBUG_MODE" = true ]; then
    BUILD_CMD="$BUILD_CMD --debug=all"
    echo -e "${YELLOW}Building in DEBUG mode${NC}"
else
    echo -e "${YELLOW}Building in RELEASE mode${NC}"
fi

# Run PyInstaller
echo -e "${YELLOW}Running PyInstaller...${NC}"
echo "This may take a few minutes..."
echo ""

$BUILD_CMD --noconfirm "$SPEC_FILE"

# Check build success
if [ -d "$DIST_DIR/$APP_NAME" ]; then
    echo ""
    echo -e "${GREEN}==================================${NC}"
    echo -e "${GREEN}  ✓ Build Successful!${NC}"
    echo -e "${GREEN}==================================${NC}"
    echo ""
    echo "Executable location:"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "  $DIST_DIR/$APP_NAME/$APP_NAME.app"
    else
        # Linux
        echo "  $DIST_DIR/$APP_NAME/$APP_NAME"
    fi
    
    echo ""
    echo "To run the application:"
    echo "  cd $DIST_DIR/$APP_NAME"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  open $APP_NAME.app"
    else
        echo "  ./\$APP_NAME"
    fi
    
    echo ""
    echo -e "${YELLOW}Note: The first launch may be slow as libraries are extracted.${NC}"
    
    exit 0
else
    echo ""
    echo -e "${RED}==================================${NC}"
    echo -e "${RED}  ✗ Build Failed${NC}"
    echo -e "${RED}==================================${NC}"
    echo ""
    echo "Check the error messages above."
    echo "Common issues:"
    echo "  - Missing dependencies (run: pip install -r requirements.txt)"
    echo "  - Import errors in source files"
    echo "  - Missing asset files"
    echo ""
    echo "Try building with --debug flag for more details:"
    echo "  $0 --debug"
    
    exit 1
fi
