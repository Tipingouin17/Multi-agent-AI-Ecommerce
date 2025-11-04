#!/bin/bash
# ============================================================================
# Dashboard UI Testing Script - Linux/macOS
# ============================================================================
# This script runs comprehensive UI tests for all dashboard interfaces
# ============================================================================

set -e

echo ""
echo "============================================================================"
echo "                     DASHBOARD UI TESTING SUITE"
echo "============================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "[INFO] Python found"
python3 --version

# Check if dashboard is running
echo ""
echo "[INFO] Checking if dashboard is running on http://localhost:5173..."
if ! curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "[WARNING] Dashboard is not running on http://localhost:5173"
    echo ""
    echo "Please start the dashboard first using:"
    echo "  ./start_dashboard.sh"
    echo ""
    exit 1
fi

echo "[SUCCESS] Dashboard is running"

# Install Selenium if not already installed
echo ""
echo "[INFO] Checking Selenium installation..."
if ! python3 -c "import selenium" 2>/dev/null; then
    echo "[INFO] Installing Selenium WebDriver..."
    pip3 install selenium
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install Selenium"
        exit 1
    fi
fi

echo "[SUCCESS] Selenium is installed"

# Check for ChromeDriver
echo ""
echo "[INFO] Checking ChromeDriver..."
if ! command -v chromedriver &> /dev/null; then
    echo "[WARNING] ChromeDriver not found in PATH"
    echo ""
    echo "Please install ChromeDriver:"
    echo "  - Ubuntu/Debian: sudo apt-get install chromium-chromedriver"
    echo "  - macOS: brew install chromedriver"
    echo "  - Or download from: https://chromedriver.chromium.org/"
    echo ""
    echo "Alternatively, install via pip:"
    echo "  pip3 install webdriver-manager"
    echo ""
    exit 1
fi

echo "[SUCCESS] ChromeDriver found"

# Run the tests
echo ""
echo "============================================================================"
echo "                        RUNNING UI TESTS"
echo "============================================================================"
echo ""

cd "$(dirname "$0")"

# Run with headless mode by default (add --headless flag)
python3 testing/ui_dashboard_comprehensive_tests.py --url http://localhost:5173 --headless

TEST_EXIT_CODE=$?

echo ""
echo "============================================================================"
echo "                        TEST EXECUTION COMPLETE"
echo "============================================================================"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "[SUCCESS] All tests passed!"
    echo "Exit code: $TEST_EXIT_CODE"
else
    echo "[WARNING] Some tests failed or encountered errors"
    echo "Exit code: $TEST_EXIT_CODE"
fi

echo ""
echo "Check the log files and screenshots in the testing directory for details."
echo ""

exit $TEST_EXIT_CODE

