#!/bin/bash
# Quick release script - skips tests and confirmation
set -e

echo "Quick release to TestPyPI..."

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running in correct directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Clean
echo -e "${YELLOW}Cleaning...${NC}"
rm -rf build/ dist/ *.egg-info src/*.egg-info

# Build
echo -e "${YELLOW}Building...${NC}"
if command -v uv &> /dev/null; then
    uv build
else
    python -m build
fi

# Upload to TestPyPI
echo -e "${YELLOW}Uploading to TestPyPI...${NC}"
if command -v uv &> /dev/null; then
    uv run twine upload --repository testpypi dist/*
else
    python -m twine upload --repository testpypi dist/*
fi

echo -e "${GREEN}Done! Test install with:${NC}"
echo -e "${GREEN}pip install --index-url https://test.pypi.org/simple/ php-parser-py${NC}"
