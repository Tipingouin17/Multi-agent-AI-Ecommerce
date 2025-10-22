#!/bin/bash
# Kafka Connectivity Verification Script for Linux/Mac

echo ""
echo "================================================================================"
echo "  Kafka Connectivity Verification"
echo "================================================================================"
echo ""

# Change to project root directory
cd "$(dirname "$0")/.."

# Run the verification script
python3 scripts/verify_kafka_connectivity.py

echo ""
echo "================================================================================"
echo "  Verification Complete"
echo "================================================================================"
echo ""

