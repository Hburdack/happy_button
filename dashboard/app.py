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
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, make_response
from flask_socketio import SocketIO, emit
import requests

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import our modules
try:
    from utils.templates import RoyalCourtesyTemplates
    from email_processing.router import EmailRouter
    from email_processing.parser import EmailParser
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

@app.route('/agents')
def agents():
    """Agent management page"""
    return render_template('agents.html')


@app.route('/external')
def external():
    """External partners and email processing page"""
    return render_template('external.html')

@app.route('/api/agents/<agent_name>/restart', methods=['POST'])
def restart_agent(agent_name):
    """Restart a specific agent"""
    try:
        # Simulate agent restart
        logger.info(f"Restarting {agent_name} agent")
        return jsonify({
            'status': 'success',
            'message': f'{agent_name} agent restarted successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/agents/<agent_name>/details')
def agent_details(agent_name):
    """Get detailed information about a specific agent"""
    try:
        # Mock agent details
        agent_details = {
            'info': {
                'status': 'active',
                'processed_emails': 127,
                'queue_size': 2,
                'uptime': '2h 15m',
                'capabilities': ['E-Mail Triage', 'Routing', 'Auto-Reply'],
                'last_error': None
            },
            'orders': {
                'status': 'active',
                'processed_emails': 89,
                'queue_size': 1,
                'uptime': '2h 15m',
                'capabilities': ['Bestellungsverarbeitung', 'ERP-Integration', 'Bestätigungen'],
                'last_error': None
            },
            'oem': {
                'status': 'active',
                'processed_emails': 45,
                'queue_size': 0,
                'uptime': '2h 15m',
                'capabilities': ['VIP-Behandlung', 'Priority Routing', 'Escalation'],
                'last_error': None
            },
            'quality': {
                'status': 'busy',
                'processed_emails': 23,
                'queue_size': 3,
                'uptime': '2h 15m',
                'capabilities': ['Qualitätskontrolle', 'Beschwerdemanagement', 'Eskalation'],
                'last_error': 'Warning: High queue size detected'
            },
            'supplier': {
                'status': 'active',
                'processed_emails': 67,
                'queue_size': 0,
                'uptime': '2h 15m',
                'capabilities': ['Lieferantenkoordination', 'Tracking', 'Benachrichtigungen'],
                'last_error': None
            },
            'management': {
                'status': 'active',
                'processed_emails': 12,
                'queue_size': 1,
                'uptime': '2h 15m',
                'capabilities': ['Eskalation', 'Management Reports', 'Kritische Fälle'],
                'last_error': None
            }
        }

        return jsonify(agent_details.get(agent_name, {
            'status': 'unknown',
            'processed_emails': 0,
            'queue_size': 0,
            'uptime': 'N/A',
            'capabilities': [],
            'last_error': 'Agent not found'
        }))
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/emails/recent')
def recent_emails():
    """Get the last 100 processed emails with full details"""
    try:
        # Generate realistic email data for the last 100 emails
        import random
        from datetime import datetime, timedelta

        # More detailed email configurations with human-like content
        email_scenarios = [
            {
                'type': 'order', 'route': 'orders@h-bu.de', 'priority': 'high',
                'senders': ['john.smith@oem1.com', 'sarah.jones@manufacturing-corp.com', 'orders@premium-buttons.com'],
                'subjects': [
                    'URGENT: Need 15,000 Navy Blue Buttons for Q4 Production',
                    'Re: Bulk Order Quote - Custom Logo Buttons Required',
                    'Follow-up: December Delivery Timeline for Holiday Orders',
                    'Special Request: Eco-Friendly Button Materials'
                ],
                'content_templates': [
                    "Hi Happy Buttons team,\n\nWe're facing an unexpected demand surge and urgently need 15,000 navy blue buttons (part #HB-NB-2024) for our Q4 production line. Can you please confirm availability and expedited shipping options?\n\nOur production deadline is November 15th, so timing is critical.\n\nBest regards,\n{sender_name}",
                    "Dear procurement team,\n\nFollowing up on our previous discussion about custom logo buttons. We've finalized our design and need 8,500 units with our company logo embossed.\n\nAttached you'll find:\n- Final logo specifications\n- Preferred button dimensions\n- Color matching requirements\n\nLooking forward to your quote.\n\nKind regards,\n{sender_name}"
                ],
                'attachment_types': ['order_form.pdf', 'specifications.docx', 'logo_design.ai', 'purchase_order.xlsx']
            },
            {
                'type': 'oem', 'route': 'oem1@h-bu.de', 'priority': 'critical',
                'senders': ['premium.orders@bmw-supplier.com', 'procurement@audi-parts.de', 'vip@luxury-brands.com'],
                'subjects': [
                    'BMW Project X7: Critical Timeline Update Required',
                    'Audi Q8 Interior - Button Quality Specifications',
                    'CONFIDENTIAL: New Luxury Brand Partnership Opportunity'
                ],
                'content_templates': [
                    "Dear Happy Buttons VIP Team,\n\nRegarding the BMW Project X7 initiative, we need to discuss potential timeline adjustments. Our engineering team has identified some specification refinements that may impact delivery.\n\nCould we schedule a priority call this week? This project is mission-critical for our Q1 2025 launch.\n\nConfidential regards,\n{sender_name}\nSenior Procurement Manager",
                    "Happy Buttons Premium Division,\n\nOur quality assurance team requires additional documentation for the Audi Q8 interior button specifications. The automotive grade requirements are more stringent than initially outlined.\n\nPlease prioritize this request as it affects our production certification timeline.\n\nBest,\n{sender_name}"
                ],
                'attachment_types': ['nda_agreement.pdf', 'technical_specs.dwg', 'quality_standards.pdf', 'project_timeline.mpp']
            },
            {
                'type': 'supplier', 'route': 'supplier@h-bu.de', 'priority': 'medium',
                'senders': ['logistics@china-materials.com', 'dispatch@mexico-production.mx', 'shipping@poland-factory.pl'],
                'subjects': [
                    'Shipment Delay: Raw Materials from Guangzhou Factory',
                    'Weekly Production Report - Mexico Facility',
                    'Quality Control Update: Poland Manufacturing Line'
                ],
                'content_templates': [
                    "Dear Happy Buttons Supply Chain,\n\nWe regret to inform you of a 3-day delay in shipment HB-GM-240920 from our Guangzhou facility. This is due to unexpected customs inspections and port congestion.\n\nNew estimated arrival: September 27th\nOriginal ETA: September 24th\n\nWe're working with our logistics partners to minimize further delays.\n\nApologies for any inconvenience,\n{sender_name}\nSupply Chain Coordinator",
                    "Hello Happy Buttons Team,\n\nPlease find attached our weekly production report from the Mexico facility. We've exceeded targets by 12% this week and quality metrics remain at 99.2%.\n\nNotable achievements:\n- Zero safety incidents\n- Improved efficiency in button finishing\n- Successful implementation of new quality protocols\n\nBest regards,\n{sender_name}"
                ],
                'attachment_types': ['shipping_manifest.pdf', 'production_report.xlsx', 'quality_certificate.pdf', 'customs_docs.pdf']
            },
            {
                'type': 'quality', 'route': 'quality@h-bu.de', 'priority': 'high',
                'senders': ['inspector@quality-control.com', 'compliance@certification-body.org', 'lab@materials-testing.de'],
                'subjects': [
                    'Quality Alert: Batch HB-2024-0920 Color Variance Detected',
                    'ISO 9001 Compliance Audit - Action Items',
                    'Material Testing Results: New Polymer Samples'
                ],
                'content_templates': [
                    "QUALITY ALERT - IMMEDIATE ATTENTION REQUIRED\n\nBatch ID: HB-2024-0920\nIssue: Color variance exceeding tolerance (±2.3 Delta E)\nAffected Units: 2,847 buttons\n\nOur quality team detected color inconsistencies during routine inspection. Batch is currently quarantined pending investigation.\n\nRoot cause analysis initiated.\nCustomer notification: Pending your approval\n\nPlease advise on next steps.\n\n{sender_name}\nQuality Assurance Manager",
                    "Dear Happy Buttons Quality Team,\n\nFollowing our ISO 9001 compliance audit, please find attached the detailed findings report. Overall performance is excellent with minor improvement opportunities identified.\n\nKey action items:\n1. Update calibration records for measurement equipment\n2. Enhance traceability documentation\n3. Review supplier qualification process\n\nCompliance deadline: October 15th, 2024\n\nRegards,\n{sender_name}"
                ],
                'attachment_types': ['quality_report.pdf', 'test_results.xlsx', 'audit_findings.docx', 'calibration_cert.pdf']
            }
        ]

        def get_file_icon(filename):
            """Return appropriate icon for file type"""
            extension = filename.split('.')[-1].lower()
            icon_map = {
                'pdf': 'fas fa-file-pdf',
                'docx': 'fas fa-file-word',
                'doc': 'fas fa-file-word',
                'xlsx': 'fas fa-file-excel',
                'xls': 'fas fa-file-excel',
                'ai': 'fas fa-file-image',
                'dwg': 'fas fa-drafting-compass',
                'mpp': 'fas fa-project-diagram',
                'zip': 'fas fa-file-archive',
                'jpg': 'fas fa-file-image',
                'png': 'fas fa-file-image'
            }
            return icon_map.get(extension, 'fas fa-file')

        recent_emails = []
        now = datetime.now()

        for i in range(100):
            # Choose a scenario and generate human-like email
            scenario = random.choice(email_scenarios)
            sender = random.choice(scenario['senders'])
            subject = random.choice(scenario['subjects'])

            # Extract sender name for content personalization
            sender_name = sender.split('@')[0].replace('.', ' ').title()
            if '.' in sender_name:
                sender_name = sender_name.replace('.', ' ')

            # Generate email content
            content_template = random.choice(scenario['content_templates'])
            email_content = content_template.format(sender_name=sender_name)

            # Create realistic attachments with clickable details
            num_attachments = random.randint(0, 3)
            attachments_list = []
            if num_attachments > 0:
                available_attachments = scenario['attachment_types']
                selected_attachments = random.sample(available_attachments, min(num_attachments, len(available_attachments)))

                for attachment_name in selected_attachments:
                    attachments_list.append({
                        'name': attachment_name,
                        'size': f'{random.randint(50, 2500)}KB',
                        'type': attachment_name.split('.')[-1].upper(),
                        'url': f'/api/emails/attachment/{i+1}/{attachment_name}',
                        'icon': get_file_icon(attachment_name)
                    })

            # Create timestamp going backwards
            minutes_ago = i * random.randint(2, 15)
            timestamp = now - timedelta(minutes=minutes_ago)

            email = {
                'id': f'email_{i+1}',
                'from': sender,
                'from_name': sender_name,
                'to': 'info@h-bu.de',
                'subject': subject,
                'content': email_content,
                'timestamp': timestamp.isoformat(),
                'time_ago': f'vor {minutes_ago} Min' if minutes_ago < 60 else f'vor {minutes_ago//60}h {minutes_ago%60}m',
                'routed_to': scenario['route'],
                'priority': scenario['priority'],
                'status': random.choice(['processed', 'routed', 'escalated', 'auto_replied']),
                'category': scenario['type'],
                'size': f'{random.randint(15, 250)}KB',
                'attachments': num_attachments,
                'attachments_list': attachments_list,
                'processing_time': f'{random.randint(50, 500)}ms',
                'auto_reply_sent': random.choice([True, False]),
                'escalation_level': random.choice([None, 'management', 'urgent']) if scenario['priority'] == 'critical' else None,
                'importance': random.choice(['normal', 'high', 'urgent']) if scenario['priority'] in ['high', 'critical'] else 'normal',
                'read_receipt_requested': random.choice([True, False]) if scenario['priority'] == 'critical' else False
            }

            recent_emails.append(email)

        return jsonify({
            'status': 'success',
            'total_count': 20,
            'emails': recent_emails,
            'last_updated': now.isoformat()
        })

    except Exception as e:
        logger.error(f"Error retrieving recent emails: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/emails/attachment/<email_id>/<filename>')
def download_attachment(email_id, filename):
    """Mock attachment download endpoint"""
    try:
        # In a real system, this would serve actual files
        # For simulation, we generate a mock response

        file_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'dwg': 'application/acad',
            'mpp': 'application/vnd.ms-project',
            'ai': 'application/postscript'
        }

        extension = filename.split('.')[-1].lower()
        content_type = file_types.get(extension, 'application/octet-stream')

        # Generate mock file content based on file type
        if extension == 'pdf':
            mock_content = b'%PDF-1.4\n%Mock PDF content for Happy Buttons simulation\n%%EOF'
        elif extension == 'docx':
            mock_content = b'Mock Microsoft Word document content for ' + filename.encode()
        elif extension == 'xlsx':
            mock_content = b'Mock Excel spreadsheet content for ' + filename.encode()
        else:
            mock_content = f'Mock file content for {filename} - Happy Buttons simulation'.encode()

        response = make_response(mock_content)
        response.headers['Content-Type'] = content_type
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Length'] = len(mock_content)

        logger.info(f"Attachment download: {filename} for email {email_id}")
        return response

    except Exception as e:
        logger.error(f"Error downloading attachment {filename}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to download {filename}'
        }), 500

@app.route('/api/agents/mailbox/<mailbox_name>')
def mailbox_details(mailbox_name):
    """Get detailed mailbox information"""
    try:
        # Mock mailbox data
        mailbox_data = {
            'info': {
                'address': 'info@h-bu.de',
                'total_emails': 245,
                'today_emails': 38,
                'recent_emails': [
                    {
                        'from': 'john@oem1.com',
                        'subject': 'Urgent Order Request - 5000 Blue Buttons',
                        'time': 'vor 2 Minuten',
                        'routed_to': 'orders@h-bu.de',
                        'status': 'routed'
                    },
                    {
                        'from': 'customer@example.com',
                        'subject': 'Product Quality Issue',
                        'time': 'vor 5 Minuten',
                        'routed_to': 'quality@h-bu.de',
                        'status': 'escalated'
                    },
                    {
                        'from': 'supplier@materials.com',
                        'subject': 'Delivery Confirmation',
                        'time': 'vor 8 Minuten',
                        'routed_to': 'supplier@h-bu.de',
                        'status': 'processed'
                    }
                ]
            }
        }

        return jsonify(mailbox_data.get(mailbox_name, {
            'address': f'{mailbox_name}@h-bu.de',
            'total_emails': 0,
            'today_emails': 0,
            'recent_emails': []
        }))
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


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
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)