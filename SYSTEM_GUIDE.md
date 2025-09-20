# Happy Buttons System Control & Dashboard Guide

## 🚀 **SYSTEM OVERVIEW**

The Happy Buttons System includes:
- **Start/Stop Script**: `happy_buttons.py` - Complete system management
- **Web Dashboard**: Real-time monitoring and control interface
- **Service Management**: Health checks and process monitoring
- **Configuration UI**: System settings and agent management

## 🛠️ **SYSTEM CONTROL SCRIPT**

### Quick Commands

```bash
# Start the complete system
python happy_buttons.py start

# Stop the system
python happy_buttons.py stop

# Restart all services
python happy_buttons.py restart

# Check system status
python happy_buttons.py status

# Run with monitoring
python happy_buttons.py monitor
```

### Service-Specific Control

```bash
# Start specific service
python happy_buttons.py start --service dashboard
python happy_buttons.py start --service email_processor
python happy_buttons.py start --service swarm_coordinator

# Stop specific service
python happy_buttons.py stop --service dashboard

# Restart specific service
python happy_buttons.py restart --service email_processor
```

### System Services

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| `dashboard` | 8080 | Web monitoring interface | `http://localhost:8080/health` |
| `email_processor` | 8081 | Email processing service | `http://localhost:8081/health` |
| `swarm_coordinator` | 8082 | Claude Flow swarm | Internal monitoring |

## 🌐 **WEB DASHBOARD**

### Access Points

- **Main Dashboard**: http://localhost:8080
- **Configuration**: http://localhost:8080/config
- **Health Check**: http://localhost:8080/health

### Dashboard Features

#### 📊 **Real-Time Monitoring**
- **System Metrics**: CPU, Memory, Disk usage
- **Service Status**: All services with health indicators
- **Performance Charts**: Real-time system performance
- **Email Statistics**: Processing rates and categories

#### 🤖 **Agent Management**
- **Agent Status**: All 6 business unit agents
- **Task Monitoring**: Queue sizes and processing rates
- **Capabilities Overview**: Agent specializations
- **Performance Metrics**: Success rates and response times

#### 📧 **Email Testing**
- **Live Email Tester**: Test routing logic
- **Scenario Simulation**: OEM, regular, complaint, supplier
- **Routing Visualization**: See decision process
- **Template Generation**: Preview auto-replies

#### ⚙️ **Configuration Management**
- **Business Rules**: SLA settings, thresholds
- **Template Validation**: Royal courtesy scoring
- **Agent Configuration**: Capabilities and settings
- **System Commands**: Start/stop/restart controls

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/metrics` | GET | System performance metrics |
| `/api/services` | GET | Service status overview |
| `/api/email/stats` | GET | Email processing statistics |
| `/api/agents` | GET | Agent status and performance |
| `/api/swarm` | GET | Claude Flow swarm status |
| `/api/templates` | GET | Template information |
| `/api/test_email` | POST | Test email processing |

## 🔧 **SYSTEM ARCHITECTURE**

### Process Management

```
happy_buttons.py (Controller)
├── dashboard/app.py (Port 8080)
│   ├── Real-time monitoring
│   ├── WebSocket updates
│   └── Configuration UI
├── src/service.py (Port 8081)
│   ├── Email processing
│   ├── Agent coordination
│   └── Health monitoring
└── Claude Flow Swarm (Port 8082)
    ├── Swarm coordination
    ├── Neural networks
    └── Memory management
```

### Health Check System

Each service provides health endpoints:
- **HTTP Status**: 200 (healthy), 503 (unhealthy)
- **Metrics**: Uptime, processing counts, error rates
- **Auto-Recovery**: Failed services automatically restart

### Monitoring & Alerting

- **Real-time Updates**: 5-second intervals via WebSocket
- **Performance Tracking**: CPU, memory, disk, network
- **Service Health**: Automatic failure detection
- **Process Monitoring**: PID tracking, resource usage

## 📋 **USAGE SCENARIOS**

### 1. **System Startup**

```bash
# Initialize and start everything
python happy_buttons.py start

# Verify all services are running
python happy_buttons.py status

# Open dashboard
open http://localhost:8080
```

### 2. **Development Monitoring**

```bash
# Start with continuous monitoring
python happy_buttons.py monitor

# Or check individual service logs
tail -f logs/dashboard_stdout.log
tail -f logs/email_processor_stdout.log
```

### 3. **Email Testing**

1. **Via Dashboard**: http://localhost:8080
   - Use the Email Processing Tester
   - Select scenario (OEM, Regular, Complaint, Supplier)
   - View routing decision and template

2. **Via API**:
```bash
curl -X POST http://localhost:8080/api/test_email \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "john@oem1.com",
    "subject": "Urgent Order",
    "body": "Need 5000 buttons urgently"
  }'
```

### 4. **Performance Monitoring**

1. **Dashboard View**: Real-time charts and metrics
2. **API Access**: GET `/api/metrics` for JSON data
3. **Health Checks**: Automated service monitoring
4. **Alerts**: Visual indicators for service failures

### 5. **Configuration Management**

1. **Business Rules**: Update SLA times, thresholds
2. **Agent Settings**: Configure capabilities and limits
3. **Template Management**: Validate royal courtesy templates
4. **Routing Logic**: Modify email routing rules

## 🚨 **TROUBLESHOOTING**

### Common Issues

#### Services Won't Start
```bash
# Check dependencies
pip install -r requirements.txt

# Verify ports are available
netstat -tulpn | grep :808

# Check logs
tail -f logs/happy_buttons.log
```

#### Dashboard Not Loading
```bash
# Verify dashboard service
python happy_buttons.py status

# Restart dashboard only
python happy_buttons.py restart --service dashboard

# Check browser console for errors
```

#### Email Processing Errors
```bash
# Check email service health
curl http://localhost:8081/health

# View processing logs
tail -f logs/email_processor_stdout.log

# Test with simple email
curl -X POST http://localhost:8080/api/test_email \
  -H "Content-Type: application/json" \
  -d '{"sender":"test@test.com","subject":"Test","body":"Test"}'
```

### Log Files

| File | Content |
|------|---------|
| `logs/happy_buttons.log` | Main system controller |
| `logs/dashboard_stdout.log` | Dashboard service output |
| `logs/email_processor_stdout.log` | Email processing logs |
| `logs/swarm_coordinator_stdout.log` | Swarm coordination logs |

### Performance Optimization

#### High CPU Usage
- Reduce monitoring frequency in dashboard
- Limit number of concurrent email processes
- Optimize agent task queues

#### Memory Issues
- Clear agent memory periodically
- Reduce metrics history retention
- Monitor swarm memory usage

#### Network Issues
- Check port availability
- Verify firewall settings
- Test health check endpoints

## 🔐 **SECURITY CONSIDERATIONS**

### Access Control
- Dashboard runs on localhost by default
- No authentication required (development mode)
- Health endpoints are publicly accessible

### Data Protection
- No sensitive data logged
- Memory cleared on shutdown
- Email content not persisted

### Network Security
- Services bind to localhost only
- Standard HTTP (not HTTPS) for development
- No external dependencies required

## 📊 **PERFORMANCE METRICS**

### System Targets
- **CPU Usage**: < 50% average
- **Memory Usage**: < 70% of available
- **Response Time**: < 2 seconds for email processing
- **Uptime**: > 99% service availability

### Monitoring Thresholds
- **Warning**: CPU > 70%, Memory > 80%
- **Critical**: CPU > 90%, Memory > 95%
- **Auto-restart**: Service down > 30 seconds

### Scaling Recommendations
- **Horizontal**: Multiple email processor instances
- **Vertical**: Increase memory for large agent swarms
- **Load Balancing**: Distribute across multiple ports

---

## 🎯 **QUICK START CHECKLIST**

1. ✅ **Dependencies**: `pip install -r requirements.txt`
2. ✅ **Permissions**: `chmod +x happy_buttons.py`
3. ✅ **Start System**: `python happy_buttons.py start`
4. ✅ **Verify Status**: `python happy_buttons.py status`
5. ✅ **Open Dashboard**: http://localhost:8080
6. ✅ **Test Email**: Use dashboard email tester
7. ✅ **Monitor**: Watch real-time metrics

**System Status**: 🟢 Ready for Production Use