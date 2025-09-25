#!/bin/bash
# Happy Buttons Service Installation Script
# Installs the Happy Buttons systemd service for autostart

set -e

# Configuration
SERVICE_NAME="happy-buttons"
SERVICE_FILE="/home/pi/happy_button/scripts/happy-buttons.service"
SYSTEMD_SERVICE="/etc/systemd/system/$SERVICE_NAME.service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Installing Happy Buttons System Service${NC}"
echo "========================================"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root or with sudo${NC}"
    echo "Usage: sudo $0"
    exit 1
fi

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}Error: Service file not found at $SERVICE_FILE${NC}"
    exit 1
fi

# Stop existing service if running
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo -e "${YELLOW}Stopping existing service...${NC}"
    systemctl stop "$SERVICE_NAME"
fi

# Disable existing service if enabled
if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo -e "${YELLOW}Disabling existing service...${NC}"
    systemctl disable "$SERVICE_NAME"
fi

# Copy service file
echo -e "${YELLOW}Installing service file...${NC}"
cp "$SERVICE_FILE" "$SYSTEMD_SERVICE"
chmod 644 "$SYSTEMD_SERVICE"

# Reload systemd
echo -e "${YELLOW}Reloading systemd daemon...${NC}"
systemctl daemon-reload

# Enable service for autostart
echo -e "${YELLOW}Enabling service for autostart...${NC}"
systemctl enable "$SERVICE_NAME"

# Start service
echo -e "${YELLOW}Starting service...${NC}"
if systemctl start "$SERVICE_NAME"; then
    echo -e "${GREEN}✓ Service started successfully${NC}"
else
    echo -e "${RED}✗ Failed to start service${NC}"
    echo "Check logs with: journalctl -u $SERVICE_NAME -f"
    exit 1
fi

# Verify service status
sleep 3
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✓ Service is running${NC}"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    systemctl status "$SERVICE_NAME" --no-pager
    exit 1
fi

echo ""
echo "========================================"
echo -e "${GREEN}Happy Buttons Service Installation Complete!${NC}"
echo ""
echo "Service Status:"
systemctl status "$SERVICE_NAME" --no-pager -l
echo ""
echo "Available Commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo -e "${BLUE}The service will automatically start on system boot.${NC}"