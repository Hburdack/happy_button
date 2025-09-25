#!/bin/bash
# Happy Buttons System - Status Script
# Shows status of all Happy Buttons services

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

echo -e "${BLUE}Happy Buttons System Status${NC}"
echo "========================================="

# Function to check service status
check_service() {
    local name="$1"
    local port="$2"

    printf "%-20s" "$name:"

    if [ ! -f "$PID_DIR/$name.pid" ]; then
        echo -e "${RED}STOPPED${NC} (no PID file)"
        return 1
    fi

    local pid=$(cat "$PID_DIR/$name.pid")

    if ! kill -0 "$pid" 2>/dev/null; then
        echo -e "${RED}STOPPED${NC} (PID $pid not running)"
        rm -f "$PID_DIR/$name.pid"
        return 1
    fi

    # Check if port is responding (for web services)
    if [ "$port" != "N/A" ] && command -v curl >/dev/null 2>&1; then
        local http_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port 2>/dev/null || echo "000")
        if [ "$http_status" = "200" ] || [ "$http_status" = "302" ] || [ "$http_status" = "404" ]; then
            echo -e "${GREEN}RUNNING${NC} (PID $pid, HTTP $http_status on port $port)"
        else
            echo -e "${YELLOW}RUNNING${NC} (PID $pid, port $port not responding)"
        fi
    else
        echo -e "${GREEN}RUNNING${NC} (PID $pid)"
    fi
    return 0
}

# Check all services
running_count=0
total_count=0

services=(
    "main-app:80"
    "dashboard-8085:8085"
    "dashboard-8090:8090"
    "email-processor:N/A"
    "background-services:N/A"
)

for service_info in "${services[@]}"; do
    IFS=':' read -r service port <<< "$service_info"
    total_count=$((total_count + 1))
    if check_service "$service" "$port"; then
        running_count=$((running_count + 1))
    fi
done

echo ""
echo "========================================="
echo -e "System Status: ${running_count}/${total_count} services running"

if [ $running_count -eq $total_count ]; then
    echo -e "${GREEN}✓ All services are running${NC}"
elif [ $running_count -gt 0 ]; then
    echo -e "${YELLOW}⚠ Some services are not running${NC}"
else
    echo -e "${RED}✗ No services are running${NC}"
fi

# Show system resources
echo ""
echo "System Resources:"
if command -v free >/dev/null 2>&1; then
    echo "Memory usage: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
fi

if [ -d "$LOG_DIR" ]; then
    echo "Recent log activity:"
    find "$LOG_DIR" -name "*.log" -type f -exec ls -lh {} \; 2>/dev/null | tail -5 | while read -r line; do
        echo "  $line"
    done
fi

echo ""
echo "Commands:"
echo "  Start:  happy-buttons-start.sh"
echo "  Stop:   happy-buttons-stop.sh"
echo "  Logs:   tail -f $LOG_DIR/*.log"