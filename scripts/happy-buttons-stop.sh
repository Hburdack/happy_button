#!/bin/bash
# Happy Buttons System - Stop Script
# Stops all Happy Buttons services gracefully

set -e

# Configuration
HAPPY_BUTTONS_DIR="/home/pi/happy_button"
LOG_DIR="$HAPPY_BUTTONS_DIR/logs"
PID_DIR="$HAPPY_BUTTONS_DIR/pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping Happy Buttons System...${NC}"
echo "========================================="

# Function to stop a service
stop_service() {
    local name="$1"
    local signal="${2:-TERM}"

    echo -e "${YELLOW}Stopping $name...${NC}"

    if [ ! -f "$PID_DIR/$name.pid" ]; then
        echo -e "${YELLOW}$name PID file not found${NC}"
        return 0
    fi

    local pid=$(cat "$PID_DIR/$name.pid")

    if ! kill -0 "$pid" 2>/dev/null; then
        echo -e "${YELLOW}$name is not running${NC}"
        rm -f "$PID_DIR/$name.pid"
        return 0
    fi

    # Send termination signal
    kill -$signal "$pid" 2>/dev/null || true

    # Wait for graceful shutdown
    local timeout=10
    local count=0
    while kill -0 "$pid" 2>/dev/null && [ $count -lt $timeout ]; do
        sleep 1
        count=$((count + 1))
        echo -ne "\rWaiting for $name to stop... ${count}s"
    done
    echo ""

    # Force kill if still running
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${YELLOW}Force stopping $name...${NC}"
        kill -KILL "$pid" 2>/dev/null || true
        sleep 1
    fi

    # Check if stopped
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${RED}✗ Failed to stop $name (PID: $pid)${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $name stopped successfully${NC}"
        rm -f "$PID_DIR/$name.pid"
        return 0
    fi
}

# Stop all known services
services=("main-app" "dashboard-8085" "dashboard-8090" "email-processor" "background-services")

for service in "${services[@]}"; do
    stop_service "$service"
done

# Kill any remaining python processes running Happy Buttons components
echo -e "${YELLOW}Checking for remaining Happy Buttons processes...${NC}"
pids=$(pgrep -f "python.*app\.py\|python.*dashboard\|python.*email_processor\|python.*background_services" 2>/dev/null || true)
if [ -n "$pids" ]; then
    echo -e "${YELLOW}Found additional processes, stopping them...${NC}"
    echo $pids | xargs kill -TERM 2>/dev/null || true
    sleep 2
    # Force kill if still running
    remaining=$(pgrep -f "python.*app\.py\|python.*dashboard\|python.*email_processor\|python.*background_services" 2>/dev/null || true)
    if [ -n "$remaining" ]; then
        echo -e "${YELLOW}Force killing remaining processes...${NC}"
        echo $remaining | xargs kill -KILL 2>/dev/null || true
    fi
fi

# Clean up any stale PID files
echo -e "${YELLOW}Cleaning up PID files...${NC}"
for pidfile in "$PID_DIR"/*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile" 2>/dev/null || echo "")
        if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
            rm -f "$pidfile"
            echo -e "${GREEN}Removed stale PID file: $(basename "$pidfile")${NC}"
        fi
    fi
done

echo "========================================="
echo -e "${GREEN}Happy Buttons System stopped successfully!${NC}"
echo ""
echo -e "${BLUE}Use 'happy-buttons-start.sh' to start all services${NC}"