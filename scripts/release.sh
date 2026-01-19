#!/bin/bash
set -e

echo "Starting build and release process for php-parser-py..."

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running in correct directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Detect if uv is available
USE_UV=false
if command -v uv &> /dev/null; then
    USE_UV=true
    echo -e "${GREEN}Detected uv project${NC}"
fi

# Function to check and install build tools
check_build_tools() {
    if [ "$USE_UV" = true ]; then
        # For uv projects, use uv to install tools
        if ! uv pip list | grep -q "^build "; then
            echo -e "${YELLOW}Installing build via uv...${NC}"
            uv pip install build || {
                echo -e "${RED}Error: Failed to install build module${NC}"
                exit 1
            }
        fi
        
        if ! uv pip list | grep -q "^twine "; then
            echo -e "${YELLOW}Installing twine via uv...${NC}"
            uv pip install twine || {
                echo -e "${RED}Error: Failed to install twine${NC}"
                exit 1
            }
        fi
        echo "uv"
        return
    fi
    
    # Fallback to standard Python/pip
    local python_cmd=""
    if command -v python &> /dev/null; then
        python_cmd="python"
    elif command -v python3 &> /dev/null; then
        python_cmd="python3"
    else
        echo -e "${RED}Error: Python not found${NC}"
        exit 1
    fi

    # Check if pip is available
    if ! $python_cmd -m pip --version &> /dev/null 2>&1; then
        echo -e "${YELLOW}Warning: pip module not found, trying to install...${NC}"
        $python_cmd -m ensurepip --upgrade 2>/dev/null || {
            echo -e "${RED}Error: Cannot install pip. Please install pip manually.${NC}"
            exit 1
        }
    fi

    # Check if build module is installed
    if ! $python_cmd -m build --version &> /dev/null 2>&1; then
        echo -e "${YELLOW}Warning: build module not found, installing...${NC}"
        $python_cmd -m pip install --upgrade build || {
            echo -e "${RED}Error: Failed to install build module${NC}"
            exit 1
        }
    fi

    # Check if twine is installed
    if ! $python_cmd -m twine --version &> /dev/null 2>&1; then
        echo -e "${YELLOW}Warning: twine not found, installing...${NC}"
        $python_cmd -m pip install --upgrade twine || {
            echo -e "${RED}Error: Failed to install twine${NC}"
            exit 1
        }
    fi

    echo "$python_cmd"
}

# Get command prefix
CMD_PREFIX=$(check_build_tools)

# 1. Clean previous build files
echo -e "${YELLOW}Cleaning previous build files...${NC}"
rm -rf build/ dist/ *.egg-info src/*.egg-info
echo -e "${GREEN}Cleanup complete${NC}"

# 2. Run tests (optional)
read -p "Run tests? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Running tests...${NC}"
    if [ "$USE_UV" = true ]; then
        uv run pytest tests/ -v || {
            echo -e "${RED}Tests failed!${NC}"
            read -p "Continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        }
    elif command -v pytest &> /dev/null; then
        pytest tests/ -v || {
            echo -e "${RED}Tests failed!${NC}"
            read -p "Continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        }
    else
        echo -e "${YELLOW}Warning: pytest not found, skipping tests${NC}"
    fi
    echo -e "${GREEN}Tests complete${NC}"
fi

# 3. Build distribution packages
echo -e "${YELLOW}Building distribution packages...${NC}"
if [ "$USE_UV" = true ]; then
    uv build
else
    $CMD_PREFIX -m build
fi
echo -e "${GREEN}Build complete${NC}"

# 4. Check build artifacts
echo -e "${YELLOW}Checking build artifacts...${NC}"
if [ "$USE_UV" = true ]; then
    if uv run twine check dist/* 2>/dev/null; then
        echo -e "${GREEN}Check passed${NC}"
    else
        echo -e "${YELLOW}Warning: twine check failed or not available${NC}"
    fi
else
    if $CMD_PREFIX -m twine check dist/* 2>/dev/null; then
        echo -e "${GREEN}Check passed${NC}"
    else
        echo -e "${YELLOW}Warning: twine check failed or not available${NC}"
    fi
fi

# 5. Show build artifacts
echo -e "${YELLOW}Build artifacts:${NC}"
ls -lh dist/

# 6. Choose release target
echo ""
echo -e "${YELLOW}Choose release target:${NC}"
echo "1) TestPyPI (test)"
echo "2) PyPI (production)"
echo "3) Build only, do not publish"
read -p "Please choose (1/2/3): " -n 1 -r choice
echo

# Trim whitespace
choice=$(echo "$choice" | tr -d '[:space:]')

case "$choice" in
    1)
        echo -e "${YELLOW}Uploading to TestPyPI...${NC}"
        if [ "$USE_UV" = true ]; then
            uv run twine upload --repository testpypi dist/*
        else
            $CMD_PREFIX -m twine upload --repository testpypi dist/*
        fi
        echo -e "${GREEN}Uploaded to TestPyPI${NC}"
        echo -e "${GREEN}Test install: pip install --index-url https://test.pypi.org/simple/ php-parser-py${NC}"
        ;;
    2)
        read -p "Confirm publish to PyPI? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Uploading to PyPI...${NC}"
            if [ "$USE_UV" = true ]; then
                uv run twine upload dist/*
            else
                $CMD_PREFIX -m twine upload dist/*
            fi
            echo -e "${GREEN}Published to PyPI${NC}"
            echo -e "${GREEN}Install: pip install --upgrade php-parser-py${NC}"
        else
            echo -e "${YELLOW}Publish cancelled${NC}"
        fi
        ;;
    3)
        echo -e "${GREEN}Build complete, not published${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"
