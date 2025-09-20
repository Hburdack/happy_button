#!/usr/bin/env python3
"""
Happy Buttons System Dashboard
Real-time monitoring and control interface
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import psutil
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import requests

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import our modules
try:
    from utils.templates import RoyalCourtesyTemplates
    from email.router import EmailRouter
    from email.parser import EmailParser
    from agents.business_agents import create_business_agents
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")

app = Flask(__name__)
app.secret_key = 'happy_buttons_dashboard_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitors system health and performance"""

    def __init__(self):
        self.metrics_history = []
        self.max_history = 100

        # Initialize system components
        try:
            self.templates = RoyalCourtesyTemplates()
            self.router = EmailRouter()
            self.parser = EmailParser()
            self.agents = create_business_agents()
        except Exception as e:
            logger.warning(f"Could not initialize all components: {e}")
            self.templates = None
            self.router = None
            self.parser = None
            self.agents = {}

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # System resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Network info
            network_stats = psutil.net_io_counters()

            # Process count
            process_count = len(psutil.pids())

            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'memory_total_gb': memory.total / (1024**3),
                    'disk_percent': (disk.used / disk.total) * 100,
                    'disk_free_gb': disk.free / (1024**3),
                    'disk_total_gb': disk.total / (1024**3),
                    'process_count': process_count,
                    'boot_time': psutil.boot_time()
                },
                'network': {
                    'bytes_sent': network_stats.bytes_sent,
                    'bytes_recv': network_stats.bytes_recv,
                    'packets_sent': network_stats.packets_sent,
                    'packets_recv': network_stats.packets_recv
                }
            }

            # Add to history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)

            return metrics

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        services = {
            'dashboard': {
                'name': 'Dashboard Server',
                'port': 8080,
                'status': 'running',
                'health': 'healthy'
            },
            'email_processor': {
                'name': 'Email Processing Service',
                'port': 8081,
                'status': 'checking',
                'health': 'unknown'
            },
            'swarm_coordinator': {
                'name': 'Claude Flow Swarm',
                'port': 8082,
                'status': 'checking',
                'health': 'unknown'
            }
        }

        # Check each service
        for service_name, service_info in services.items():
            if service_name != 'dashboard':  # Skip self
                try:
                    if service_info.get('port'):
                        response = requests.get(
                            f"http://localhost:{service_info['port']}/health",
                            timeout=2
                        )
                        if response.status_code == 200:
                            services[service_name]['status'] = 'running'
                            services[service_name]['health'] = 'healthy'
                        else:
                            services[service_name]['status'] = 'error'
                            services[service_name]['health'] = 'unhealthy'
                except requests.RequestException:
                    services[service_name]['status'] = 'stopped'
                    services[service_name]['health'] = 'offline'

        return services

    def get_email_stats(self) -> Dict[str, Any]:
        """Get email processing statistics"""
        stats = {
            'total_processed': 0,
            'auto_replies_sent': 0,
            'escalations': 0,
            'categories': {
                'order': 0,
                'complaint': 0,
                'supplier': 0,
                'general': 0
            },
            'routing_destinations': {
                'orders@h-bu.de': 0,
                'support@h-bu.de': 0,
                'quality@h-bu.de': 0,
                'oem1@h-bu.de': 0
            }
        }

        # In a real implementation, this would come from a database
        # For demo purposes, we'll simulate some data
        import random
        stats['total_processed'] = random.randint(50, 200)
        stats['auto_replies_sent'] = int(stats['total_processed'] * 0.75)
        stats['escalations'] = int(stats['total_processed'] * 0.1)

        return stats

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        agent_status = {}

        for agent_name, agent in self.agents.items():
            try:
                status = agent.get_status() if hasattr(agent, 'get_status') else {}
                agent_status[agent_name] = {
                    'name': agent.agent_type if hasattr(agent, 'agent_type') else agent_name,
                    'active': status.get('is_active', False),
                    'processed_tasks': status.get('processed_tasks', 0),
                    'error_count': status.get('error_count', 0),
                    'queue_size': status.get('queue_size', 0),
                    'capabilities': agent.get_agent_capabilities() if hasattr(agent, 'get_agent_capabilities') else {}
                }
            except Exception as e:
                agent_status[agent_name] = {
                    'name': agent_name,
                    'active': False,
                    'error': str(e)
                }

        return agent_status

    def get_swarm_status(self) -> Dict[str, Any]:
        """Get Claude Flow swarm status"""
        try:
            # This would integrate with the ruv-swarm MCP tools
            # For now, return mock data
            return {
                'active_swarms': 1,
                'total_agents': len(self.agents),
                'memory_usage_mb': 48,
                'features': {
                    'neural_networks': True,
                    'cognitive_diversity': True,
                    'forecasting': True,
                    'simd_support': True
                }
            }
        except Exception as e:
            logger.error(f"Error getting swarm status: {e}")
            return {}


# Initialize monitor
monitor = SystemMonitor()


@app.route('/')
def index():
    """Dashboard home page"""
    return render_template('dashboard.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/metrics')
def api_metrics():
    """API endpoint for system metrics"""
    return jsonify(monitor.get_system_metrics())


@app.route('/api/services')
def api_services():
    """API endpoint for service status"""
    return jsonify(monitor.get_service_status())


@app.route('/api/email/stats')
def api_email_stats():
    """API endpoint for email statistics"""
    return jsonify(monitor.get_email_stats())


@app.route('/api/agents')
def api_agents():
    """API endpoint for agent status"""
    return jsonify(monitor.get_agent_status())


@app.route('/api/swarm')
def api_swarm():
    """API endpoint for swarm status"""
    return jsonify(monitor.get_swarm_status())


@app.route('/api/templates')
def api_templates():
    """API endpoint for template information"""
    if monitor.templates:
        return jsonify({
            'available_templates': monitor.templates.get_available_templates(),
            'stats': monitor.templates.get_template_stats(),
            'validation_results': monitor.templates.bulk_validate_templates()
        })
    return jsonify({'error': 'Templates not available'})


@app.route('/api/test_email', methods=['POST'])
def api_test_email():
    """API endpoint to test email processing"""
    try:
        data = request.get_json()
        sender = data.get('sender', 'test@example.com')
        subject = data.get('subject', 'Test Email')
        body = data.get('body', 'This is a test email.')

        if monitor.parser and monitor.router:
            # Create test email
            from email.parser import create_test_email
            test_email = create_test_email(sender, subject, body)

            # Route email
            routing_decision = asyncio.run(monitor.router.route_email(test_email))

            # Generate template response if applicable
            response_data = {
                'email_id': test_email.id,
                'metadata': {
                    'category': test_email.metadata.category,
                    'priority': test_email.metadata.priority,
                    'is_oem': test_email.metadata.is_oem,
                    'is_urgent': test_email.metadata.is_urgent,
                    'confidence': test_email.metadata.confidence_score
                },
                'routing': {
                    'destination': routing_decision.destination,
                    'sla_hours': routing_decision.sla_hours,
                    'priority': routing_decision.priority,
                    'reasoning': routing_decision.reasoning
                },
                'template': routing_decision.auto_reply_template
            }

            return jsonify({'success': True, 'result': response_data})
        else:
            return jsonify({'success': False, 'error': 'Email system not available'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/config')
def config():
    """Configuration management page"""
    return render_template('config.html')


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected to dashboard')
    emit('status', {'message': 'Connected to Happy Buttons Dashboard'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected from dashboard')


@socketio.on('request_update')
def handle_request_update():
    """Handle real-time update requests"""
    try:
        data = {
            'metrics': monitor.get_system_metrics(),
            'services': monitor.get_service_status(),
            'email_stats': monitor.get_email_stats(),
            'agents': monitor.get_agent_status(),
            'swarm': monitor.get_swarm_status()
        }
        emit('update', data)
    except Exception as e:
        emit('error', {'message': str(e)})


def background_updates():
    """Send periodic updates to connected clients"""
    while True:
        try:
            socketio.sleep(5)  # Update every 5 seconds
            data = {
                'metrics': monitor.get_system_metrics(),
                'services': monitor.get_service_status(),
                'timestamp': datetime.now().isoformat()
            }
            socketio.emit('auto_update', data)
        except Exception as e:
            logger.error(f"Error in background updates: {e}")


if __name__ == '__main__':
    # Start background update thread
    socketio.start_background_task(background_updates)

    # Run the dashboard
    logger.info("🌐 Starting Happy Buttons Dashboard on http://localhost:8080")
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)