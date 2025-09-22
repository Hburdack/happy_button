# Happy Buttons GmbH - Deployment Guide

## 🚀 Production Deployment

This guide covers deploying the Happy Buttons Agentic Email Simulation System in production environments.

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 20GB available space
- **Network**: Port 80 (HTTP) access required

### Dependencies
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install system dependencies
sudo apt install nginx supervisor postgresql redis-server -y
```

## 🔧 Installation

### 1. Clone Repository
```bash
# Create application directory
sudo mkdir -p /opt/happy-buttons
cd /opt/happy-buttons

# Clone repository
git clone <repository-url> .
chown -R www-data:www-data /opt/happy-buttons
```

### 2. Python Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install production WSGI server
pip install gunicorn gevent
```

### 3. Environment Configuration
```bash
# Create environment file
sudo nano /opt/happy-buttons/.env
```

Add the following configuration:
```bash
# Server Configuration
PORT=80
HOST=0.0.0.0
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost/happy_buttons

# Email Configuration
IMAP_HOST=mail.h-bu.de
SMTP_HOST=mail.h-bu.de
COMPANY_DOMAIN=h-bu.de

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/happy-buttons/app.log

# Security
CSRF_SECRET_KEY=your-csrf-key-here
```

## 🗄️ Database Setup

### PostgreSQL Configuration
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE happy_buttons;
CREATE USER happy_buttons_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE happy_buttons TO happy_buttons_user;
\q
```

### Database Migration
```bash
# Initialize database schema
cd /opt/happy-buttons
source venv/bin/activate
python -c "from dashboard.app import init_db; init_db()"
```

## 🌐 Web Server Configuration

### Nginx Setup
Create Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/happy-buttons
```

Add configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Static files
    location /static/ {
        alias /opt/happy-buttons/dashboard/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/api/system/health;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/happy-buttons /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔄 Process Management

### Gunicorn Configuration
Create Gunicorn config:
```bash
sudo nano /opt/happy-buttons/gunicorn.conf.py
```

Add configuration:
```python
# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = 4
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout settings
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/happy-buttons/access.log"
errorlog = "/var/log/happy-buttons/error.log"
loglevel = "info"

# Process naming
proc_name = "happy-buttons"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
```

### Supervisor Configuration
Create supervisor config:
```bash
sudo nano /etc/supervisor/conf.d/happy-buttons.conf
```

Add configuration:
```ini
[program:happy-buttons]
command=/opt/happy-buttons/venv/bin/gunicorn -c gunicorn.conf.py dashboard.app:app
directory=/opt/happy-buttons
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/happy-buttons/supervisor.log
environment=PATH="/opt/happy-buttons/venv/bin"

[program:happy-buttons-worker]
command=/opt/happy-buttons/venv/bin/python -m dashboard.worker
directory=/opt/happy-buttons
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/happy-buttons/worker.log
environment=PATH="/opt/happy-buttons/venv/bin"
```

### Start Services
```bash
# Create log directory
sudo mkdir -p /var/log/happy-buttons
sudo chown www-data:www-data /var/log/happy-buttons

# Start supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start happy-buttons:*
```

## 🔒 Security Configuration

### SSL/TLS Setup with Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Firewall Configuration
```bash
# Configure UFW
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### Security Headers
Update Nginx configuration for enhanced security:
```nginx
# Add to server block
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; img-src 'self' data:; font-src 'self' cdnjs.cloudflare.com;" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

## 📊 Monitoring & Logging

### Application Monitoring
```bash
# Install monitoring tools
pip install prometheus-client psutil

# Create monitoring config
sudo nano /opt/happy-buttons/monitoring.py
```

### Log Rotation
```bash
sudo nano /etc/logrotate.d/happy-buttons
```

Add configuration:
```
/var/log/happy-buttons/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload nginx
        supervisorctl restart happy-buttons:*
    endscript
}
```

### Health Checks
Create health check script:
```bash
sudo nano /opt/happy-buttons/health_check.sh
```

```bash
#!/bin/bash
# Health check script

# Check if application is responding
if curl -f http://localhost/api/system/health > /dev/null 2>&1; then
    echo "Application: HEALTHY"
    exit 0
else
    echo "Application: UNHEALTHY"
    exit 1
fi
```

## 🔄 Backup Strategy

### Database Backup
```bash
# Create backup script
sudo nano /opt/happy-buttons/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/happy-buttons"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
pg_dump happy_buttons > $BACKUP_DIR/db_backup_$DATE.sql

# Application backup
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz /opt/happy-buttons

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Automated Backups
```bash
# Add to crontab
sudo crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/happy-buttons/backup.sh
```

## 🚀 Performance Optimization

### Redis Caching
```bash
# Configure Redis
sudo nano /etc/redis/redis.conf

# Add configurations
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_emails_timestamp ON emails(timestamp);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_kpis_metric_name ON kpis(metric_name);
```

### Static File Optimization
```bash
# Compress static files
cd /opt/happy-buttons/dashboard/static
find . -type f \( -name "*.css" -o -name "*.js" \) -exec gzip -k {} \;
```

## 🔄 Deployment Automation

### CI/CD Pipeline (GitHub Actions)
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/happy-buttons
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            supervisorctl restart happy-buttons:*
```

### Rolling Updates
```bash
# Create deployment script
sudo nano /opt/happy-buttons/deploy.sh
```

```bash
#!/bin/bash
set -e

echo "Starting deployment..."

# Pull latest code
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run migrations if needed
python -c "from dashboard.app import migrate_db; migrate_db()"

# Restart services
supervisorctl restart happy-buttons:*

echo "Deployment complete!"
```

## 🐛 Troubleshooting

### Common Issues

**Service Won't Start:**
```bash
# Check supervisor logs
sudo tail -f /var/log/happy-buttons/supervisor.log

# Check application logs
sudo tail -f /var/log/happy-buttons/error.log

# Restart services
sudo supervisorctl restart happy-buttons:*
```

**Database Connection Issues:**
```bash
# Test database connection
sudo -u postgres psql -h localhost -U happy_buttons_user -d happy_buttons

# Check PostgreSQL status
sudo systemctl status postgresql
```

**High Memory Usage:**
```bash
# Monitor memory usage
htop

# Check for memory leaks
sudo supervisorctl restart happy-buttons:*
```

### Performance Monitoring
```bash
# Monitor application performance
curl http://localhost/api/system/metrics

# Check database performance
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Monitor Nginx access
sudo tail -f /var/log/nginx/access.log
```

## 📞 Support

### Emergency Procedures
1. **Service Down**: Restart all services via supervisor
2. **High Load**: Scale worker processes
3. **Database Issues**: Check PostgreSQL logs and restart if needed
4. **SSL Certificate Expiry**: Renew with certbot

### Contact Information
- **System Administrator**: sysadmin@h-bu.de
- **Development Team**: dev@h-bu.de
- **Emergency Contact**: +49-xxx-xxx-xxxx

---

**Last Updated**: September 2025
**Deployment Version**: 1.0.0