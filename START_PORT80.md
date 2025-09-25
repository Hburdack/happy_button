# Starting Happy Buttons on Port 80

You've successfully installed the systemd service! Now you need to start it with root privileges.

## Start the Systemd Service

Run these commands as root (or with sudo if available):

```bash
# Start the service
sudo systemctl start happy-buttons

# Check if it's running
sudo systemctl status happy-buttons

# Test port 80
curl http://localhost:80
```

## If you don't have sudo access

Contact your system administrator to run:

```bash
systemctl start happy-buttons
```

## Alternative: Manual Start with Capabilities

If you can run commands as root, set the capability and start manually:

```bash
# As root: Grant port 80 binding capability
setcap 'cap_net_bind_service=+ep' /usr/bin/python3

# Then as regular user:
cd /home/pi/happy_button
./scripts/happy-buttons-start.sh
```

## Current Status

The systemd service is:
- ✅ **Installed**: Service file is in place
- ✅ **Enabled**: Will start automatically on boot
- ❌ **Stopped**: Needs to be started with root privileges

Once started, Happy Buttons will be available on:
- **Main Application**: http://localhost:80
- **Dashboard 8085**: http://localhost:8085
- **Dashboard 8090**: http://localhost:8090

## Troubleshooting

If the service fails to start, check logs:

```bash
sudo journalctl -u happy-buttons -n 50
```