#!/usr/bin/env python3
"""
Simple test to verify dashboard can start without email conflicts
"""

from flask import Flask, jsonify, render_template
import psutil
import time
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/metrics')
def api_metrics():
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'system': {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
    })

@app.route('/api/services')
def api_services():
    return jsonify({
        'dashboard': {
            'name': 'Dashboard Server',
            'port': 8080,
            'status': 'running',
            'health': 'healthy'
        }
    })

@app.route('/api/email/stats')
def api_email_stats():
    return jsonify({
        'total_processed': 42,
        'auto_replies_sent': 35,
        'escalations': 3,
        'categories': {
            'order': 15,
            'complaint': 5,
            'supplier': 12,
            'general': 10
        }
    })

@app.route('/api/agents')
def api_agents():
    return jsonify({
        'info': {'name': 'Info Agent', 'active': True, 'processed_tasks': 25, 'error_count': 0, 'queue_size': 0, 'capabilities': {'triage': True}},
        'orders': {'name': 'Orders Agent', 'active': True, 'processed_tasks': 15, 'error_count': 0, 'queue_size': 1, 'capabilities': {'order_processing': True}},
        'oem': {'name': 'OEM Agent', 'active': True, 'processed_tasks': 8, 'error_count': 0, 'queue_size': 0, 'capabilities': {'oem_priority': True}},
        'quality': {'name': 'Quality Agent', 'active': False, 'processed_tasks': 2, 'error_count': 1, 'queue_size': 0, 'capabilities': {'quality_management': True}}
    })

@app.route('/api/swarm')
def api_swarm():
    return jsonify({
        'active_swarms': 1,
        'total_agents': 4,
        'memory_usage_mb': 48,
        'features': {
            'neural_networks': True,
            'cognitive_diversity': True
        }
    })

@app.route('/api/templates')
def api_templates():
    return jsonify({
        'available_templates': ['order_received', 'generic_ack', 'oem_priority_ack', 'complaint_ack'],
        'stats': {'total_templates': 4, 'average_length': 250},
        'validation_results': {
            'order_received': {'score': 95, 'is_valid': True},
            'generic_ack': {'score': 88, 'is_valid': True},
            'oem_priority_ack': {'score': 92, 'is_valid': True},
            'complaint_ack': {'score': 85, 'is_valid': True}
        }
    })

if __name__ == '__main__':
    print("🌐 Starting Simple Dashboard Test on http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)