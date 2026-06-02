#!/bin/bash
# Development Installation Script for pywave

set -e

echo "🚀 Installing pywave in development mode..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install in editable mode with optional dependencies
echo ""
echo "📦 Installing viscowave in editable mode..."
pip install -e .

echo ""
echo "📦 Installing optional dependencies..."
pip install -e ".[units]"  # pint for unit handling

echo ""
echo "📦 Installing development dependencies..."
pip install -e ".[dev]"  # pytest, mypy, etc.

echo ""
echo "✅ Installation complete!"
echo ""
echo "To use viscowave:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run Python scripts:"
echo "     python examples/modern_api_demo.py"
echo ""
echo "  3. Deactivate when done:"
echo "     deactivate"
