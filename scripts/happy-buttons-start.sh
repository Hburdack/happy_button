#!/bin/bash
# Happy Buttons System - Start Script
# Creates and manages all Happy Buttons services

set -e

# Configuration
HAPPY_BUTTONS_DIR="/home/pi/happy_button"
LOG_DIR="$HAPPY_BUTTONS_DIR/logs"
PID_DIR="$HAPPY_BUTTONS_DIR/pids"
USER="pi"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

echo -e "${BLUE}Starting Happy Buttons System...${NC}"
echo "========================================="

# Function to start a service
start_service() {
    local name="$1"
    local command="$2"
    local port="$3"
    local working_dir="${4:-$HAPPY_BUTTONS_DIR}"

    echo -e "${YELLOW}Starting $name on port $port...${NC}"

    # Check if already running
    if [ -f "$PID_DIR/$name.pid" ]; then
        local pid=$(cat "$PID_DIR/$name.pid")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}$name is already running (PID: $pid)${NC}"
            return 0
        else
            rm -f "$PID_DIR/$name.pid"
        fi
    fi

    # Start the service
    cd "$working_dir"
    nohup bash -c "$command" > "$LOG_DIR/$name.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_DIR/$name.pid"

    # Wait a moment and check if it started successfully
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}✓ $name started successfully (PID: $pid)${NC}"

        # Check if port is responding
        if command -v curl >/dev/null 2>&1; then
            sleep 3
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:$port | grep -q "200\|302\|404"; then
                echo -e "${GREEN}✓ $name responding on port $port${NC}"
            else
                echo -e "${YELLOW}⚠ $name may still be starting up on port $port${NC}"
            fi
        fi
    else
        echo -e "${RED}✗ Failed to start $name${NC}"
        rm -f "$PID_DIR/$name.pid"
        return 1
    fi
}

# Change to Happy Buttons directory
cd "$HAPPY_BUTTONS_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Start main application on port 80 only
echo -e "${YELLOW}Starting main application on port 80...${NC}"
if start_service "main-app" "PORT=80 python app.py" "80" "$HAPPY_BUTTONS_DIR"; then
    MAIN_PORT=80
else
    echo -e "${RED}Failed to start main application on port 80${NC}"
    echo -e "${YELLOW}Make sure port 80 capabilities are set: sudo ./scripts/enable-port80.sh${NC}"
    exit 1
fi

# Start email processor if it exists
if [ -f "email_processor.py" ]; then
    start_service "email-processor" "python email_processor.py" "N/A" "$HAPPY_BUTTONS_DIR"
fi

# Start any additional services
if [ -f "background_services.py" ]; then
    start_service "background-services" "python background_services.py" "N/A" "$HAPPY_BUTTONS_DIR"
fi

echo "========================================="
echo -e "${GREEN}Happy Buttons System startup complete!${NC}"
echo ""
echo "Services running:"
echo "- Main Application: http://localhost:${MAIN_PORT:-80}"
echo ""
echo "Log files: $LOG_DIR/"
echo "PID files: $PID_DIR/"
echo ""
echo -e "${BLUE}Use 'happy-buttons-stop.sh' to stop all services${NC}"