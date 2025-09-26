# 📡 API Reference - Release 2.2

**Complete REST API Documentation for Happy Buttons Business Automation Platform**

---

## 🎯 **Overview**

The Release 2.2 API provides comprehensive access to all system components including agent management, email processing, TimeWarp simulation, business intelligence, and real-time monitoring. All endpoints return JSON responses and support standard HTTP status codes.

### **Base URL**
```
http://localhost:8080
```

### **Authentication**
Currently no authentication required for local deployment. Production deployments should implement appropriate security measures.

---

## 🤖 **Agent System API**

### **GET /api/agents**
Get status of all business agents

```bash
curl http://localhost:8080/api/agents
```

**Response:**
```json
{
  "success": true,
  "agents": {
    "InfoAgent": {
      "name": "InfoAgent",
      "is_active": true,
      "description": "Email triage, classification, and routing coordination",
      "last_activity": "2025-09-26T10:30:45",
      "error_count": 0,
      "uptime_seconds": 3600
    },
    "SalesAgent": {
      "name": "SalesAgent",
      "is_active": true,
      "description": "Sales inquiries, quotations, and order management",
      "last_activity": "2025-09-26T10:30:42",
      "error_count": 0,
      "uptime_seconds": 3598
    },
    "SupportAgent": {
      "name": "SupportAgent",
      "is_active": true,
      "description": "Technical support, issue resolution, troubleshooting",
      "last_activity": "2025-09-26T10:30:40",
      "error_count": 0,
      "uptime_seconds": 3596
    },
    "FinanceAgent": {
      "name": "FinanceAgent",
      "is_active": true,
      "description": "Billing, invoicing, payment processing",
      "last_activity": "2025-09-26T10:30:38",
      "error_count": 0,
      "uptime_seconds": 3594
    }
  },
  "summary": {
    "total_agents": 4,
    "active_agents": 4,
    "health_score": 100
  }
}
```

### **GET /api/agents/{agent_name}**
Get detailed status of specific agent

```bash
curl http://localhost:8080/api/agents/InfoAgent
```

**Response:**
```json
{
  "success": true,
  "agent": {
    "name": "InfoAgent",
    "is_active": true,
    "description": "Email triage, classification, and routing coordination",
    "last_activity": "2025-09-26T10:30:45",
    "error_count": 0,
    "uptime_seconds": 3600,
    "performance_metrics": {
      "emails_processed": 142,
      "average_response_time": 0.41,
      "success_rate": 98.6
    }
  }
}
```

### **POST /api/agents/{agent_name}/restart**
Restart specific agent

```bash
curl -X POST http://localhost:8080/api/agents/InfoAgent/restart
```

**Response:**
```json
{
  "success": true,
  "message": "Agent InfoAgent restarted successfully",
  "agent_status": {
    "name": "InfoAgent",
    "is_active": true,
    "uptime_seconds": 0
  }
}
```

---

## ⚡ **TimeWarp API**

### **GET /api/timewarp/status**
Get current TimeWarp status

```bash
curl http://localhost:8080/api/timewarp/status
```

**Response:**
```json
{
  "success": true,
  "status": {
    "speed_level": 5,
    "speed_name": "Time Warp",
    "multiplier": 1008,
    "is_running": true,
    "week_progress": 23.5,
    "day_of_week": "Tuesday",
    "simulation_time": "2025-09-26T14:30:00",
    "real_time": "2025-09-26T10:15:30",
    "elapsed_real_seconds": 900,
    "elapsed_simulation_hours": 252
  }
}
```

### **POST /api/timewarp/set-speed**
Set TimeWarp speed level

```bash
curl -X POST http://localhost:8080/api/timewarp/set-speed \
  -H "Content-Type: application/json" \
  -d '{"level": 5}'
```

**Request Body:**
```json
{
  "level": 5  // Integer 1-5
}
```

**Response:**
```json
{
  "success": true,
  "message": "TimeWarp speed set to Level 5: Time Warp",
  "new_status": {
    "speed_level": 5,
    "speed_name": "Time Warp",
    "multiplier": 1008
  }
}
```

### **POST /api/timewarp/start**
Start TimeWarp simulation

```bash
curl -X POST http://localhost:8080/api/timewarp/start
```

**Response:**
```json
{
  "success": true,
  "message": "TimeWarp simulation started",
  "status": {
    "is_running": true,
    "speed_level": 5,
    "started_at": "2025-09-26T10:15:30"
  }
}
```

### **POST /api/timewarp/pause**
Pause TimeWarp simulation

```bash
curl -X POST http://localhost:8080/api/timewarp/pause
```

**Response:**
```json
{
  "success": true,
  "message": "TimeWarp simulation paused",
  "status": {
    "is_running": false,
    "paused_at": "2025-09-26T10:20:30"
  }
}
```

### **POST /api/timewarp/reset**
Reset TimeWarp simulation

```bash
curl -X POST http://localhost:8080/api/timewarp/reset
```

**Response:**
```json
{
  "success": true,
  "message": "TimeWarp simulation reset",
  "status": {
    "is_running": false,
    "speed_level": 1,
    "simulation_time": "2025-09-26T10:25:30"
  }
}
```

---

## 📧 **Email System API**

### **GET /api/email-status**
Get email system status

```bash
curl http://localhost:8080/api/email-status
```

**Response:**
```json
{
  "success": true,
  "status": {
    "is_running": true,
    "queue_size": 3,
    "emails_sent": 342,
    "errors_count": 4,
    "success_rate": 98.9,
    "rate_limit_minute": 5,
    "rate_limit_hour": 30,
    "recent_send_rate_minute": 2,
    "recent_send_rate_hour": 28,
    "server_config": {
      "host": "192.168.2.13",
      "port": 587,
      "use_tls": true
    }
  }
}
```

### **POST /api/email/send**
Send email via real SMTP

```bash
curl -X POST http://localhost:8080/api/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "from": "test@customer.com",
    "subject": "Test Order Inquiry",
    "body": "Testing email system integration",
    "priority": "normal"
  }'
```

**Request Body:**
```json
{
  "from": "test@customer.com",
  "subject": "Test Order Inquiry",
  "body": "Testing email system integration",
  "priority": "normal"  // normal, high, critical
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email queued for delivery",
  "email_id": "email_1727340900_1234",
  "estimated_delivery": "2025-09-26T10:30:45"
}
```

### **GET /api/email/queue**
Get email queue status

```bash
curl http://localhost:8080/api/email/queue
```

**Response:**
```json
{
  "success": true,
  "queue": {
    "size": 3,
    "pending_emails": [
      {
        "id": "email_1727340900_1234",
        "subject": "Test Order Inquiry",
        "priority": "normal",
        "queued_at": "2025-09-26T10:25:30"
      }
    ],
    "processing_status": "active"
  }
}
```

---

## 🔄 **Simulation API**

### **GET /api/simulation/status**
Get business simulation status

```bash
curl http://localhost:8080/api/simulation/status
```

**Response:**
```json
{
  "success": true,
  "simulation": {
    "enhanced_business": {
      "running": true,
      "day_number": 3,
      "day_name": "Wednesday",
      "hour": 14,
      "theme": "Supply Chain Disruption",
      "current_issues": 2,
      "total_emails_today": 23,
      "optimization_opportunities": 5
    },
    "company_manager": {
      "running": true,
      "simulation_cycles": 12,
      "total_emails_sent": 342,
      "runtime_hours": 6.5,
      "current_cycle_progress": 68.3
    }
  }
}
```

### **POST /api/simulation/start**
Start business simulation

```bash
curl -X POST http://localhost:8080/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "enhanced", "speed_multiplier": 3}'
```

**Request Body:**
```json
{
  "mode": "enhanced",        // enhanced, company, timewarp
  "speed_multiplier": 3,     // 1-10 for enhanced mode
  "enable_real_emails": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Business simulation started",
  "simulation_id": "sim_1727340900",
  "mode": "enhanced",
  "estimated_duration": "5 minutes"
}
```

### **POST /api/simulation/stop**
Stop business simulation

```bash
curl -X POST http://localhost:8080/api/simulation/stop
```

**Response:**
```json
{
  "success": true,
  "message": "Business simulation stopped",
  "final_stats": {
    "emails_generated": 156,
    "issues_resolved": 8,
    "optimization_opportunities": 12,
    "runtime_minutes": 15.3
  }
}
```

---

## 📊 **Business Intelligence API**

### **GET /api/kpis**
Get key performance indicators

```bash
curl http://localhost:8080/api/kpis
```

**Response:**
```json
{
  "success": true,
  "kpis": {
    "overall_performance_score": 94.8,
    "email_processing_efficiency": 97.3,
    "agent_operational_status": 100.0,
    "order_fulfillment_rate": 96.1,
    "customer_satisfaction": 95.8,
    "real_email_delivery": 98.9,
    "sla_compliance": 97.8,
    "system_automation_rate": 92.7
  },
  "trends": {
    "performance_change_24h": +2.5,
    "email_volume_change": +12.3,
    "agent_efficiency_change": +1.2
  }
}
```

### **GET /api/metrics**
Get detailed system metrics

```bash
curl http://localhost:8080/api/metrics
```

**Response:**
```json
{
  "success": true,
  "metrics": {
    "system": {
      "cpu_usage_percent": 15.2,
      "memory_usage_mb": 245.7,
      "disk_usage_percent": 42.1,
      "uptime_seconds": 86400
    },
    "agents": {
      "total_requests_processed": 1250,
      "average_response_time": 0.41,
      "error_rate_percent": 1.4,
      "active_agents": 4
    },
    "email": {
      "emails_sent_24h": 342,
      "delivery_success_rate": 98.9,
      "average_queue_time": 1.2,
      "rate_limit_utilization": 56.7
    },
    "simulation": {
      "cycles_completed": 12,
      "average_cycle_duration": 300,
      "issues_generated": 45,
      "optimization_opportunities": 18
    }
  }
}
```

### **GET /api/analytics**
Get business analytics data

```bash
curl http://localhost:8080/api/analytics
```

**Response:**
```json
{
  "success": true,
  "analytics": {
    "business_intelligence": {
      "revenue_processing_capability": 346100,
      "order_throughput_daily": 89,
      "customer_satisfaction_score": 95.8,
      "operational_efficiency": 94.8
    },
    "optimization_opportunities": [
      {
        "area": "Email Processing",
        "potential_improvement": "15% faster response times",
        "implementation_effort": "Low",
        "business_impact": "High"
      },
      {
        "area": "Agent Coordination",
        "potential_improvement": "12% better load balancing",
        "implementation_effort": "Medium",
        "business_impact": "Medium"
      }
    ],
    "performance_trends": {
      "7_day_avg_performance": 93.2,
      "30_day_avg_performance": 91.8,
      "performance_trajectory": "improving"
    }
  }
}
```

---

## 🔍 **System Health API**

### **GET /health**
Basic health check

```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2025-09-26T10:30:45",
  "version": "2.2.0"
}
```

### **GET /api/system-status**
Comprehensive system status

```bash
curl http://localhost:8080/api/system-status
```

**Response:**
```json
{
  "success": true,
  "system": {
    "overall_health": "excellent",
    "health_score": 94.8,
    "components": {
      "agents": "operational",
      "email_system": "operational",
      "timewarp": "operational",
      "simulation": "operational",
      "database": "operational",
      "web_interface": "operational"
    },
    "performance": {
      "response_time_ms": 150,
      "throughput_requests_per_second": 45.2,
      "error_rate_percent": 1.1
    },
    "resources": {
      "cpu_usage_percent": 15.2,
      "memory_usage_percent": 24.1,
      "disk_usage_percent": 42.1
    }
  }
}
```

### **GET /api/system-metrics**
Detailed system metrics

```bash
curl http://localhost:8080/api/system-metrics
```

**Response:**
```json
{
  "success": true,
  "metrics": {
    "uptime": {
      "seconds": 86400,
      "human_readable": "1d 0h 0m 0s"
    },
    "requests": {
      "total": 12500,
      "successful": 12362,
      "failed": 138,
      "success_rate": 98.9
    },
    "performance": {
      "avg_response_time": 0.15,
      "p95_response_time": 0.45,
      "p99_response_time": 0.82
    },
    "resources": {
      "memory": {
        "used_mb": 245.7,
        "available_mb": 768.3,
        "usage_percent": 24.1
      },
      "cpu": {
        "usage_percent": 15.2,
        "load_average": [0.45, 0.38, 0.42]
      },
      "disk": {
        "used_gb": 4.2,
        "available_gb": 5.8,
        "usage_percent": 42.1
      }
    }
  }
}
```

---

## 🔄 **WebSocket API**

### **Real-time Updates**
Connect to WebSocket for real-time updates

```javascript
const socket = io('http://localhost:8080');

// Listen for agent status updates
socket.on('agent_status_update', (data) => {
    console.log('Agent status changed:', data);
});

// Listen for email events
socket.on('email_sent', (data) => {
    console.log('Email sent:', data);
});

// Listen for simulation updates
socket.on('simulation_update', (data) => {
    console.log('Simulation status:', data);
});

// Listen for performance metrics
socket.on('metrics_update', (data) => {
    console.log('Performance metrics:', data);
});
```

### **WebSocket Events**
- `agent_status_update` - Agent status changes
- `email_sent` - Email delivery notifications
- `email_queued` - Email queuing events
- `simulation_update` - Simulation status changes
- `timewarp_update` - TimeWarp status changes
- `metrics_update` - Performance metric updates
- `system_alert` - System alerts and warnings

---

## 🛠️ **Configuration API**

### **GET /api/config**
Get system configuration

```bash
curl http://localhost:8080/api/config
```

**Response:**
```json
{
  "success": true,
  "config": {
    "email": {
      "server": "192.168.2.13",
      "port": 587,
      "rate_limit_minute": 5,
      "rate_limit_hour": 30
    },
    "timewarp": {
      "max_level": 5,
      "default_level": 1,
      "auto_start": false
    },
    "simulation": {
      "business_week_duration": 300,
      "inter_cycle_pause": 30,
      "enable_real_emails": true
    },
    "agents": {
      "auto_restart": true,
      "health_check_interval": 60
    }
  }
}
```

### **POST /api/config/update**
Update system configuration

```bash
curl -X POST http://localhost:8080/api/config/update \
  -H "Content-Type: application/json" \
  -d '{
    "email": {
      "rate_limit_minute": 3
    },
    "timewarp": {
      "default_level": 2
    }
  }'
```

---

## 📋 **Error Responses**

### **Standard Error Format**
```json
{
  "success": false,
  "error": {
    "code": "AGENT_NOT_FOUND",
    "message": "Agent 'InvalidAgent' not found",
    "details": {
      "available_agents": ["InfoAgent", "SalesAgent", "SupportAgent", "FinanceAgent"]
    }
  }
}
```

### **HTTP Status Codes**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (agent/resource not found)
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error
- `503` - Service Unavailable (system overloaded)

---

## 🧪 **API Testing**

### **Health Check Script**
```bash
#!/bin/bash
# test_api_health.sh

echo "Testing Happy Buttons API..."

# Basic health check
echo "1. Health Check:"
curl -s http://localhost:8080/health | jq .

# Agent status
echo "2. Agent Status:"
curl -s http://localhost:8080/api/agents | jq '.summary'

# System metrics
echo "3. System Metrics:"
curl -s http://localhost:8080/api/system-status | jq '.system.overall_health'

# Email status
echo "4. Email Status:"
curl -s http://localhost:8080/api/email-status | jq '.status.success_rate'

echo "API health check complete!"
```

### **Performance Test Script**
```bash
#!/bin/bash
# performance_test.sh

echo "Performance testing API endpoints..."

# Test response times
for endpoint in "/health" "/api/agents" "/api/kpis" "/api/system-status"; do
    echo "Testing $endpoint:"
    time curl -s http://localhost:8080$endpoint > /dev/null
done

echo "Performance test complete!"
```

---

## 🔮 **Future API Enhancements**

### **Planned for Release 2.3**
- **Authentication**: JWT token-based authentication
- **Rate Limiting**: Per-user API rate limiting
- **Webhooks**: Configurable webhook notifications
- **GraphQL**: GraphQL endpoint for complex queries
- **Batch Operations**: Bulk agent and email operations

### **Advanced Features**
- **API Versioning**: Version-specific endpoints
- **OpenAPI Spec**: Complete OpenAPI 3.0 specification
- **SDK Generation**: Auto-generated client SDKs
- **Real-time Analytics**: Streaming analytics API

---

**🏢 Happy Buttons Release 2.2 - Complete API Reference**
*Enterprise-Grade REST API Documentation - September 26, 2025*