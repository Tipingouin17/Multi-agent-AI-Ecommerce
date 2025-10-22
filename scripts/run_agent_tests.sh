#!/bin/bash
# Linux/Mac Shell Script to Run Agent Production Readiness Tests
# This script will test all agents and generate comprehensive logs

set -e  # Exit on error

echo "================================================================================"
echo "MULTI-AGENT E-COMMERCE SYSTEM - PRODUCTION READINESS TEST"
echo "================================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and ensure it's in your PATH"
    exit 1
fi

echo "Python found:"
python3 --version
echo ""

# Check if we're in the right directory
if [ ! -f "scripts/test_all_agents_with_logging.py" ]; then
    echo "ERROR: Please run this script from the project root directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "Running agent tests..."
echo "This may take several minutes..."
echo ""

# Run the test script
python3 scripts/test_all_agents_with_logging.py

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo "================================================================================"
echo "TEST COMPLETED"
echo "================================================================================"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "Result: ALL TESTS PASSED"
    echo "Exit Code: 0"
elif [ $TEST_EXIT_CODE -eq 1 ]; then
    echo "Result: SOME TESTS FAILED"
    echo "Exit Code: 1"
    echo "Please check the logs directory for details"
elif [ $TEST_EXIT_CODE -eq 2 ]; then
    echo "Result: PARTIAL SUCCESS - Some agents have warnings"
    echo "Exit Code: 2"
    echo "Please check the logs directory for details"
else
    echo "Result: UNEXPECTED ERROR"
    echo "Exit Code: $TEST_EXIT_CODE"
fi

echo ""
echo "Log files are available in the 'logs' directory"
echo ""
echo "To view the summary:"
echo "  cat logs/summary_*.json | jq ."
echo ""
echo "To view individual agent logs:"
echo "  ls -la logs/agents/"
echo ""
echo "================================================================================"

exit $TEST_EXIT_CODE

