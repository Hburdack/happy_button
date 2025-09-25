#!/bin/bash
# Happy Buttons Service Uninstallation Script
# Removes the Happy Buttons systemd service

set -e

# Configuration
SERVICE_NAME="happy-buttons"
SYSTEMD_SERVICE="/etc/systemd/system/$SERVICE_NAME.service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Uninstalling Happy Buttons System Service${NC}"
echo "=========================================="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root or with sudo${NC}"
    echo "Usage: sudo $0"
    exit 1
fi

# Stop service if running
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo -e "${YELLOW}Stopping service...${NC}"
    systemctl stop "$SERVICE_NAME"
    echo -e "${GREEN}✓ Service stopped${NC}"
fi

# Disable service if enabled
if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo -e "${YELLOW}Disabling service...${NC}"
    systemctl disable "$SERVICE_NAME"
    echo -e "${GREEN}✓ Service disabled${NC}"
fi

# Remove service file
if [ -f "$SYSTEMD_SERVICE" ]; then
    echo -e "${YELLOW}Removing service file...${NC}"
    rm -f "$SYSTEMD_SERVICE"
    echo -e "${GREEN}✓ Service file removed${NC}"
fi

# Reload systemd
echo -e "${YELLOW}Reloading systemd daemon...${NC}"
systemctl daemon-reload
systemctl reset-failed 2>/dev/null || true

echo ""
echo "=========================================="
echo -e "${GREEN}Happy Buttons Service Uninstalled Successfully!${NC}"
echo ""
echo -e "${BLUE}The service will no longer start automatically on boot.${NC}"
echo -e "${BLUE}You can still use the manual scripts in /home/pi/happy_button/scripts/${NC}"