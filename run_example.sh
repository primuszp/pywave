#!/bin/bash
# Quick script to run examples without installing

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ -z "$1" ]; then
    echo "Usage: ./run_example.sh <example_name>"
    echo ""
    echo "Available examples:"
    echo "  quick_start              - Quick start example (recommended)"
    echo "  modern_api_demo          - Complete modern API demonstration"
    echo "  viscowave_basic          - Basic ViscoWave usage"
    echo "  relaxation_basic         - Basic Relaxation_Sig_to_Prony usage"
    echo "  viscowave_si_units       - SI units example"
    echo ""
    echo "Example:"
    echo "  ./run_example.sh quick_start"
    exit 1
fi

EXAMPLE_FILE="examples/${1}.py"

if [ ! -f "$EXAMPLE_FILE" ]; then
    echo "Error: Example '$EXAMPLE_FILE' not found!"
    exit 1
fi

echo "Running $EXAMPLE_FILE..."
echo ""
PYTHONPATH=. python3 "$EXAMPLE_FILE"
