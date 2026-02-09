#!/bin/bash

# Maia Project One-Click Start Script

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Project Maia ===${NC}"

# Get the absolute path of the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check Prerequisites
echo -e "${BLUE}>>> Checking prerequisites...${NC}"
if ! command_exists python3; then
    echo "Error: Python 3 is not installed."
    exit 1
fi
if ! command_exists npm; then
    echo "Error: npm is not installed."
    exit 1
fi

# 2. Setup Backend
echo -e "${BLUE}>>> Setting up Backend...${NC}"
cd "$PROJECT_ROOT"
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Checking backend dependencies..."
pip install -q fastapi uvicorn websockets python-dotenv

# Start Backend in background
echo -e "${GREEN}>>> Starting Backend Server...${NC}"
python backend/server.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend running (PID: $BACKEND_PID), logs in backend.log"

# 3. Setup Frontend
echo -e "${BLUE}>>> Setting up Frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

# Install dependencies if node_modules missing
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (first time only)..."
    npm install
else
    echo "Frontend dependencies found, skipping installation."
fi

# Start Frontend
echo -e "${GREEN}>>> Starting Frontend Server...${NC}"
echo "The application will be available at http://localhost:5173"
npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
