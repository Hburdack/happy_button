# Port 80 Setup Instructions

Currently, the Happy Buttons system runs on port 8080 due to permission restrictions. To enable port 80 access, choose one of the following methods:

## Method 1: Run as System Service (Recommended)

Install the systemd service which has the necessary capabilities:

```bash
# Install the systemd service (requires root)
sudo ./scripts/install-service.sh

# The service will automatically use port 80
sudo systemctl status happy-buttons
```

## Method 2: Grant Capabilities to Python (One-time setup)

Run this command as root to allow Python to bind to port 80:

```bash
# Run as root
sudo /sbin/setcap 'cap_net_bind_service=+ep' /usr/bin/python3

# Verify capabilities
getcap /usr/bin/python3

# Now you can start services normally
./scripts/happy-buttons-start.sh
```

## Method 3: Use Port Forwarding

Set up iptables to forward port 80 to 8080:

```bash
# Forward port 80 to 8080 (requires root)
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080

# Make permanent (varies by system)
sudo iptables-save > /etc/iptables/rules.v4
```

## Method 4: Root Execution Script

Use the provided root script:

```bash
# Run as root
sudo ./scripts/enable-port80.sh
```

## Current Status

- **Main Application**: http://localhost:8080 (fallback from port 80)
- **Dashboard 8085**: http://localhost:8085
- **Dashboard 8090**: http://localhost:8090

The system automatically falls back to port 8080 when port 80 is not accessible, ensuring reliable operation.

## Verification

After enabling port 80 access, restart the services:

```bash
./scripts/happy-buttons-stop.sh
./scripts/happy-buttons-start.sh
```

The startup script will attempt port 80 first, then fall back to 8080 if needed.