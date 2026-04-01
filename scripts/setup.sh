#!/bin/bash
# KEOTrading Setup Script

set -e

echo "=========================================="
echo "  KEOTrading Setup"
echo "=========================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create data directories
mkdir -p data logs

# Copy config template if not exists
if [ ! -f "configs/exchanges.yaml" ]; then
    cp configs/exchanges.yaml.example configs/exchanges.yaml
    echo "Created configs/exchanges.yaml from template"
    echo "Please edit configs/exchanges.yaml with your API keys"
fi

echo ""
echo "=========================================="
echo "  ✅ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit configs/exchanges.yaml with your API keys"
echo "2. Run: ./scripts/start.sh"
echo ""
