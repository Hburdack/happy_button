#!/bin/bash
# Enable port 80 binding for Python applications
# This script must be run as root

echo "Enabling port 80 binding for Happy Buttons..."

# Set capabilities for python3
/sbin/setcap 'cap_net_bind_service=+ep' /usr/bin/python3

if [ $? -eq 0 ]; then
    echo "✓ Port 80 binding enabled for Python applications"
    echo "You can now run Happy Buttons services on port 80"
else
    echo "✗ Failed to set capabilities. Make sure you run this script as root."
    exit 1
fi

echo "Starting Happy Buttons services..."
cd /home/pi/happy_button
su pi -c './scripts/happy-buttons-start.sh'