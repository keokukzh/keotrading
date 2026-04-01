#!/bin/bash
# KEOTrading Start Script

set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "=========================================="
echo "  KEOTrading"
echo "=========================================="

# Parse arguments
MODE=${1:-dashboard}

case "$MODE" in
    dashboard)
        echo "Starting Dashboard..."
        streamlit run src/dashboard/app.py --server.port 3000
        ;;
    api)
        echo "Starting API Server..."
        uvicorn src.dashboard.api:app --host 0.0.0.0 --port 8080 --reload
        ;;
    orchestrator)
        echo "Starting Orchestrator..."
        python -m src.orchestrator.main
        ;;
    docker)
        echo "Starting Docker Compose..."
        docker compose -f docker/docker-compose.yml up -d
        ;;
    test)
        echo "Running tests..."
        pytest src/ -v
        ;;
    *)
        echo "Usage: ./start.sh [dashboard|api|orchestrator|docker|test]"
        echo ""
        echo "Modes:"
        echo "  dashboard    - Start Streamlit dashboard (default)"
        echo "  api          - Start FastAPI backend"
        echo "  orchestrator - Start the trading orchestrator"
        echo "  docker       - Start Docker containers"
        echo "  test         - Run tests"
        ;;
esac
