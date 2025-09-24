# Happy Buttons GmbH - API Documentation

## 🚀 REST API Reference

The Happy Buttons Dashboard provides a comprehensive REST API for programmatic access to email processing, e-commerce, and business intelligence features.

**Base URL**: `http://localhost` (port 80)

## 📧 Email Processing API

### Get Recent Emails
Retrieve the latest processed emails with metadata and attachments.

```http
GET /api/emails
```

**Query Parameters:**
- `limit` (optional): Number of emails to return (default: 20, max: 100)
- `status` (optional): Filter by status (`processed`, `routed`, `pending`)
- `type` (optional): Filter by email type (`order`, `invoice`, `complaint`, `supplier`, `internal`)

**Response:**
```json
{
  "status": "success",
  "count": 20,
  "emails": [
    {
      "id": "email_1",
      "from": "john@oem1.com",
      "subject": "Urgent Button Order - Premium Collection",
      "timestamp": "2025-09-22 08:30",
      "type": "order",
      "status": "processed",
      "route": "oem1@h-bu.de",
      "content": "Email content...",
      "priority": "urgent",
      "attachments": 1,
      "attachments_list": [
        {
          "name": "order_12345.pdf",
          "size": "245KB",
          "type": "application/pdf"
        }
      ]
    }
  ]
}
```

### Get Email Details
Retrieve detailed information about a specific email.

```http
GET /api/emails/{email_id}
```

**Response:**
```json
{
  "status": "success",
  "email": {
    "id": "email_1",
    "from": "customer@company.com",
    "to": "info@h-bu.de",
    "subject": "Button Order Request",
    "content": "Full email content...",
    "metadata": {
      "processed_at": "2025-09-22T08:30:00Z",
      "processing_time_ms": 150,
      "confidence_score": 0.95,
      "routing_decision": "orders@h-bu.de"
    },
    "attachments": [...],
    "royal_response": "We are most delighted to confirm..."
  }
}
```

### Download Email Attachment
Download a specific email attachment.

```http
GET /api/emails/{email_id}/attachments/{filename}
```

**Response**: Binary file download with appropriate MIME type headers.

## 🛒 E-commerce API

### Get Products
Retrieve the product catalog.

```http
GET /api/shop/products
```

**Response:**
```json
{
  "status": "success",
  "categories": [
    {
      "name": "Premium Collection",
      "products": [
        {
          "id": "premium_gold",
          "name": "Premium Gold Buttons",
          "price": 45.99,
          "description": "Luxurious gold-plated buttons...",
          "image": "/static/images/premium_gold.jpg",
          "stock": 150,
          "features": ["24k gold plating", "Hand-crafted", "Royal quality"]
        }
      ]
    }
  ]
}
```

### Create Order
Place a new order through the API.

```http
POST /api/shop/orders
```

**Request Body:**
```json
{
  "customer_name": "John Smith",
  "customer_email": "john@company.com",
  "customer_phone": "+1-555-0123",
  "customer_company": "ABC Corp",
  "shipping_address": "123 Business St, City, Country",
  "notes": "Urgent delivery required",
  "items": [
    {
      "product_id": "premium_gold",
      "quantity": 50
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "order_id": 12345,
  "total_amount": 2299.50,
  "estimated_delivery": "5-7 business days",
  "confirmation_email_sent": true
}
```

### Get Order Details
Retrieve information about a specific order.

```http
GET /api/shop/orders/{order_id}
```

**Response:**
```json
{
  "status": "success",
  "order": {
    "id": 12345,
    "status": "confirmed",
    "created_at": "2025-09-22T08:30:00Z",
    "customer": {...},
    "items": [...],
    "totals": {
      "subtotal": 2299.50,
      "tax": 367.92,
      "total": 2667.42
    },
    "shipping": {
      "address": "...",
      "method": "standard",
      "estimated_delivery": "5-7 business days"
    }
  }
}
```

## 📊 Business Intelligence API

### Get KPI Summary
Retrieve overall business performance metrics.

```http
GET /api/kpi/summary
```

**Response:**
```json
{
  "status": "success",
  "performance_summary": {
    "overall_score": 87,
    "auto_handled_share": 68,
    "customer_satisfaction": 91,
    "revenue_growth": 15.2
  },
  "targets": {
    "auto_handled_target": 70,
    "satisfaction_target": 85,
    "response_time_target": 3600
  }
}
```

### Get Department KPIs
Retrieve KPIs for specific business departments.

```http
GET /api/kpi/departments
```

**Response:**
```json
{
  "status": "success",
  "departments": {
    "Customer Service": [
      {
        "name": "Response Time",
        "current_value": 45,
        "target_value": 60,
        "unit": "min",
        "status": "good",
        "trend": "down",
        "description": "Average response time to customer inquiries"
      }
    ],
    "Operations": [...],
    "Sales": [...]
  }
}
```

### Get Optimization Recommendations
Retrieve AI-generated business optimization suggestions.

```http
GET /api/kpi/recommendations
```

**Response:**
```json
{
  "status": "success",
  "recommendations": [
    {
      "id": "email_automation",
      "title": "Enhance Email Automation",
      "description": "Implement advanced AI routing...",
      "priority": "high",
      "expected_impact": "+15% efficiency",
      "implementation_time": "2-3 weeks",
      "icon": "robot"
    }
  ]
}
```

### Refresh KPI Data
Trigger a refresh of all KPI metrics.

```http
POST /api/kpi/refresh
```

**Response:**
```json
{
  "status": "success",
  "refreshed_at": "2025-09-22T08:30:00Z",
  "metrics_updated": 45,
  "processing_time_ms": 1250
}
```

## 🤖 Agent Management API

### Get Agent Status
Retrieve status of all AI agents.

```http
GET /api/agents
```

**Response:**
```json
{
  "status": "success",
  "agents": [
    {
      "id": "info_agent",
      "name": "Info Center Agent",
      "type": "email_processor",
      "status": "active",
      "performance": {
        "emails_processed": 245,
        "success_rate": 94.2,
        "avg_processing_time": 150
      },
      "last_activity": "2025-09-22T08:29:45Z"
    }
  ],
  "coordination": {
    "active_workflows": 3,
    "pending_tasks": 7,
    "system_load": 0.65
  }
}
```

### Get Agent Performance
Retrieve detailed performance metrics for agents.

```http
GET /api/agents/performance
```

**Response:**
```json
{
  "status": "success",
  "timeframe": "24h",
  "metrics": {
    "total_tasks": 1247,
    "completed_tasks": 1189,
    "failed_tasks": 12,
    "average_completion_time": 180,
    "efficiency_score": 95.3
  },
  "by_agent": {...}
}
```

## 👥 Team Management API

### Get Team Overview
Retrieve business unit team information.

```http
GET /api/teams
```

**Response:**
```json
{
  "status": "success",
  "business_units": [
    {
      "name": "Customer Service",
      "email": "support@h-bu.de",
      "team_size": 8,
      "current_workload": 67,
      "performance_score": 89,
      "active_agents": 2,
      "recent_activity": "Processing customer inquiries"
    }
  ]
}
```

## 🔧 System API

### System Health Check
Check overall system health and status.

```http
GET /api/system/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-22T08:30:00Z",
  "services": {
    "dashboard": {
      "status": "running",
      "port": 80,
      "uptime": "2h 15m",
      "health": "healthy"
    },
    "email_processor": {
      "status": "running",
      "port": 8081,
      "processed_today": 245,
      "health": "healthy"
    },
    "database": {
      "status": "connected",
      "query_time": 15,
      "health": "healthy"
    }
  }
}
```

### Get System Metrics
Retrieve detailed system performance metrics.

```http
GET /api/system/metrics
```

**Response:**
```json
{
  "status": "success",
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 34.1,
    "network_io": {
      "requests_per_minute": 127,
      "response_time_avg": 95
    },
    "active_connections": 23
  }
}
```

## 🔐 Authentication & Security

### API Key Authentication
All API endpoints support optional API key authentication:

```http
Authorization: Bearer YOUR_API_KEY
```

### Rate Limiting
- **Rate Limit**: 1000 requests per hour per IP
- **Burst Limit**: 100 requests per minute
- **Headers**: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### CORS Policy
- **Allowed Origins**: `*` (development), specific domains (production)
- **Allowed Methods**: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`
- **Allowed Headers**: `Content-Type`, `Authorization`

## 📝 Error Handling

### Standard Error Response
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format provided",
    "details": {
      "field": "customer_email",
      "value": "invalid-email"
    }
  },
  "timestamp": "2025-09-22T08:30:00Z"
}
```

### HTTP Status Codes
- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## 🔄 WebSocket API

### Real-time Updates
Connect to WebSocket for real-time dashboard updates:

```javascript
const socket = io('http://localhost');

// Listen for email updates
socket.on('new_email', (data) => {
  console.log('New email:', data);
});

// Listen for KPI updates
socket.on('kpi_update', (data) => {
  console.log('KPI updated:', data);
});

// Listen for system alerts
socket.on('system_alert', (data) => {
  console.log('System alert:', data);
});
```

## 📚 SDK Examples

### Python SDK Example
```python
import requests

# Get recent emails
response = requests.get('http://localhost/api/emails')
emails = response.json()['emails']

# Place an order
order_data = {
    'customer_name': 'John Smith',
    'customer_email': 'john@company.com',
    'items': [{'product_id': 'premium_gold', 'quantity': 50}]
}
response = requests.post('http://localhost/api/shop/orders', json=order_data)
order = response.json()
```

### JavaScript SDK Example
```javascript
// Fetch KPI summary
const kpiResponse = await fetch('/api/kpi/summary');
const kpiData = await kpiResponse.json();

// Download attachment
const downloadAttachment = async (emailId, filename) => {
  const response = await fetch(`/api/emails/${emailId}/attachments/${filename}`);
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
};
```

---

**Last Updated**: September 2025
**API Version**: Release 1.0
**Base URL**: `http://localhost` (port 80)