# Happy Buttons System - Installation Guide

## Quick Setup for Autostart

### 1. Install the Systemd Service
```bash
cd /home/pi/happy_button
sudo ./scripts/install-service.sh
```

This will:
- Install the Happy Buttons systemd service
- Enable automatic startup on boot
- Start all services immediately
- Configure proper permissions and security

### 2. Verify Installation
```bash
# Check service status
sudo systemctl status happy-buttons

# Check if services are responding
curl http://localhost:80
curl http://localhost:8090
```

### 3. Service Management Commands
```bash
# Start all services
sudo systemctl start happy-buttons

# Stop all services
sudo systemctl stop happy-buttons

# Restart all services
sudo systemctl restart happy-buttons

# View real-time logs
sudo journalctl -u happy-buttons -f
```

## Manual Control (Alternative)

If you prefer manual control without systemd:

```bash
# Start all services
./scripts/happy-buttons-start.sh

# Check status
./scripts/happy-buttons-status.sh

# Stop all services
./scripts/happy-buttons-stop.sh
```

## Services Included

The system manages these components:

1. **Main Web Application** (Port 80)
   - Company landing page
   - Main dashboard interface

2. **Demo Flow Dashboard** (Port 8090)
   - Real-time email processing visualization
   - Demo flow interface

3. **Alternative Dashboard** (Port 8085)
   - Additional dashboard interface

4. **Email Processor** (Background)
   - Email ingestion and routing
   - Order processing

5. **Background Services** (Background)
   - Additional system services

## Features

### Automatic Management
- ✅ **Auto-start on boot** - Services start automatically after reboot
- ✅ **Health monitoring** - Failed services automatically restart
- ✅ **PID tracking** - Process management with PID files
- ✅ **Log management** - Organized logging in `/logs/` directory
- ✅ **Graceful shutdown** - Proper service termination
- ✅ **Port validation** - HTTP health checks for web services

### Security
- ✅ **User isolation** - Runs as `pi` user (non-root)
- ✅ **File permissions** - Restricted system access
- ✅ **Resource limits** - Memory and process limits
- ✅ **Secure paths** - Protected system directories

## Troubleshooting

### Service Won't Start
```bash
# Check detailed status
sudo systemctl status happy-buttons -l

# Check logs
sudo journalctl -u happy-buttons -n 50

# Check if ports are available
netstat -tlnp | grep -E ':80|:8085|:8090'
```

### Remove Autostart
```bash
# Uninstall the systemd service
sudo ./scripts/uninstall-service.sh
```

### Emergency Stop
```bash
# Force stop all Happy Buttons processes
pkill -f "python.*app\.py"
```

## File Locations

- **Scripts**: `/home/pi/happy_button/scripts/`
- **Logs**: `/home/pi/happy_button/logs/`
- **PID Files**: `/home/pi/happy_button/pids/`
- **Service Config**: `/etc/systemd/system/happy-buttons.service`

## Post-Installation

After installation, your Happy Buttons system will:
- ✅ Start automatically on server boot
- ✅ Restart failed services automatically
- ✅ Log all activity to systemd journal
- ✅ Be manageable via standard systemd commands
- ✅ Run securely as non-root user

**Access your system at:**
- Main Interface: http://localhost:80
- Demo Flow: http://localhost:8090
- Status Dashboard: http://localhost:8085

The system is now production-ready with full service management!