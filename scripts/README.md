# Happy Buttons System Scripts

This directory contains scripts for managing the Happy Buttons business automation system.

## Quick Start

### Manual Control
```bash
# Start all services
./scripts/happy-buttons-start.sh

# Check status
./scripts/happy-buttons-status.sh

# Stop all services
./scripts/happy-buttons-stop.sh
```

### Automatic Startup (Systemd Service)
```bash
# Install service for autostart on boot
sudo ./scripts/install-service.sh

# Remove autostart service
sudo ./scripts/uninstall-service.sh
```

## Scripts Overview

### Core Management Scripts
- **`happy-buttons-start.sh`** - Starts all Happy Buttons services
- **`happy-buttons-stop.sh`** - Stops all Happy Buttons services gracefully
- **`happy-buttons-status.sh`** - Shows status of all services

### Service Installation
- **`install-service.sh`** - Installs systemd service for autostart *(requires sudo)*
- **`uninstall-service.sh`** - Removes systemd service *(requires sudo)*
- **`happy-buttons.service`** - Systemd service configuration file

## Services Managed

The scripts manage these Happy Buttons components:

1. **Main Application** (Port 80)
   - Primary web interface
   - Company landing page
   - Core business logic

2. **Dashboard 8085** (Port 8085)
   - Alternative dashboard interface
   - System monitoring

3. **Dashboard 8090** (Port 8090)
   - Demo Flow visualization
   - Real-time email processing display

4. **Email Processor** (Background)
   - Email ingestion and routing
   - Order processing pipeline

5. **Background Services** (Background)
   - Additional system services

## Service Features

### Automatic Management
- **PID tracking** - Each service tracked with PID files in `/pids/`
- **Log management** - Service logs in `/logs/`
- **Health checks** - HTTP status checks for web services
- **Graceful shutdown** - SIGTERM followed by SIGKILL if needed
- **Duplicate prevention** - Prevents starting already running services

### Systemd Integration
- **Auto-start on boot** - Services start automatically after system reboot
- **Restart on failure** - Failed services automatically restart
- **Resource limits** - Memory and process limits configured
- **Security hardening** - Restricted permissions and access
- **Journal logging** - Integration with systemd logging

## Usage Examples

### Check if services are running
```bash
./scripts/happy-buttons-status.sh
```

### Start services manually
```bash
./scripts/happy-buttons-start.sh
```

### Install for automatic startup
```bash
sudo ./scripts/install-service.sh
```

### View service logs (after installing systemd service)
```bash
# Real-time logs
sudo journalctl -u happy-buttons -f

# Recent logs
sudo journalctl -u happy-buttons -n 50
```

### Control via systemd (after installation)
```bash
# Start
sudo systemctl start happy-buttons

# Stop
sudo systemctl stop happy-buttons

# Restart
sudo systemctl restart happy-buttons

# Status
sudo systemctl status happy-buttons
```

## File Locations

- **Scripts**: `/home/pi/happy_button/scripts/`
- **Logs**: `/home/pi/happy_button/logs/`
- **PID files**: `/home/pi/happy_button/pids/`
- **Service file**: `/etc/systemd/system/happy-buttons.service` (after installation)

## Troubleshooting

### Services won't start
1. Check logs: `tail -f /home/pi/happy_button/logs/*.log`
2. Verify permissions: Scripts should be executable (`chmod +x`)
3. Check virtual environment: Ensure `venv` directory exists
4. Port conflicts: Ensure ports 80, 8085, 8090 are available

### Service installation fails
1. Run with sudo: `sudo ./scripts/install-service.sh`
2. Check systemd status: `sudo systemctl status happy-buttons`
3. View detailed logs: `sudo journalctl -u happy-buttons -n 50`

### Services running but not responding
1. Check port availability: `netstat -tlnp | grep :80`
2. Check firewall settings
3. Verify application logs for errors
4. Test with curl: `curl http://localhost:80`

## Notes

- The system runs as user `pi` for security
- Virtual environment is automatically activated if present
- Services are started in dependency order
- Failed services are automatically restarted (when using systemd)
- All scripts include colored output for better visibility