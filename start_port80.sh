#!/bin/bash
# Start Happy Buttons on port 80
# This script helps with port 80 binding

echo "Starting Happy Buttons System on Port 80..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Running as root - starting directly on port 80"
    cd /home/pi/happy_button
    source venv/bin/activate
    PORT=80 python app.py
else
    echo "Not running as root - attempting to use capabilities"

    # Check if capabilities are set
    if command -v setcap >/dev/null 2>&1; then
        echo "Setting capabilities for Python..."
        sudo /sbin/setcap 'cap_net_bind_service=+ep' /usr/bin/python3.11
        sudo /sbin/setcap 'cap_net_bind_service=+ep' /home/pi/happy_button/.venv/bin/python3

        if [ $? -eq 0 ]; then
            echo "Capabilities set successfully"
        else
            echo "Failed to set capabilities - you may need to run with sudo"
        fi
    fi

    cd /home/pi/happy_button
    source venv/bin/activate
    PORT=80 python app.py
fi