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
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import our modules
try:
    from utils.templates import RoyalCourtesyTemplates
    from email_processing.router import EmailRouter
    from email_processing.parser import EmailParser
    from models.database import db, product_model, order_model, team_model, kpi_model
    from utils.order_email import order_email_generator
    models_available = True
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    models_available = False
    # Set fallback models
    product_model = None
    order_model = None
    team_model = None
    kpi_model = None

# Import TimeWarp system
try:
    from src.timewarp_engine import get_timewarp
    from src.timewarp_ui import get_timewarp_ui, init_timewarp_ui
    from src.timewarp_email_generator import get_email_generator
    from src.timewarp_config import get_timewarp_config, reload_timewarp_config
    from src.timewarp_agent_processor import get_agent_processor, init_agent_processor
    timewarp_available = True
    print("TimeWarp system imported successfully")
except ImportError as e:
    print(f"TimeWarp system not available: {e}")
    timewarp_available = False
    get_timewarp = lambda: None
    get_timewarp_ui = lambda: None
    get_email_generator = lambda: None

# Try to import create_business_agents separately since it might not exist
try:
    from agents.business_agents import create_business_agents
except ImportError:
    def create_business_agents():
        return {}

# Import Release 3.0 scenario system
try:
    from scenarios import get_scenario_manager
    scenario_system_available = True
    print("Release 3.0 Scenario system imported successfully")
except ImportError as e:
    print(f"Scenario system not available: {e}")
    scenario_system_available = False
    get_scenario_manager = lambda: None

app = Flask(__name__, template_folder='dashboard/templates')
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

            # Initialize Release 3.0 scenario system
            if scenario_system_available:
                self.scenario_manager = get_scenario_manager()
                logger.info("Scenario system initialized successfully")
            else:
                self.scenario_manager = None

            # Start agents asynchronously
            self._start_agents()
        except Exception as e:
            logger.warning(f"Could not initialize all components: {e}")
            self.templates = None
            self.router = None
            self.parser = None
            self.agents = {}
            self.scenario_manager = None

    def _start_agents(self):
        """Start all agents asynchronously"""
        async def start_all_agents():
            for agent_name, agent in self.agents.items():
                try:
                    if hasattr(agent, 'start'):
                        await agent.start()
                        logger.info(f"Started agent: {agent_name}")
                except Exception as e:
                    logger.error(f"Failed to start agent {agent_name}: {e}")

        # Run the async startup in a new event loop
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_all_agents())
            loop.close()
        except Exception as e:
            logger.error(f"Error starting agents: {e}")

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
                'port': 80,
                'status': 'running',
                'health': 'healthy'
            },
            'email_processor': {
                'name': 'Email Processing Service',
                'port': 80,
                'status': 'checking',
                'health': 'unknown'
            },
            'swarm_coordinator': {
                'name': 'Claude Flow Swarm',
                'port': 80,
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

        # Get real email statistics from email server
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
            from real_email_connector import RealEmailConnector

            connector = RealEmailConnector()
            mailbox_counts = connector.get_mailbox_counts()

            # Update stats with real data
            stats['mailbox_counts'] = mailbox_counts
            total_emails = sum(mailbox_counts.values())
            stats['total_processed'] = total_emails
            stats['auto_replies_sent'] = int(total_emails * 0.75)  # Estimated
            stats['escalations'] = int(total_emails * 0.1)  # Estimated

            print(f"📊 Real email stats: {total_emails} total emails across {len(mailbox_counts)} mailboxes")

        except Exception as e:
            print(f"⚠️ Error getting real email stats: {e}")
            # Fallback to basic counts
            stats['total_processed'] = 24  # Based on real connector test
            stats['auto_replies_sent'] = 18
            stats['escalations'] = 3

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

def get_recent_emails(limit=20):
    """Get recent emails for display on landing page - PRODUCTION MODE: REAL EMAIL SERVER"""
    try:
        # Check email settings mode
        import yaml
        try:
            with open('config/email_settings.yaml', 'r') as f:
                email_config = yaml.safe_load(f)
            production_mode = email_config.get('mode') == 'production'
        except:
            production_mode = True  # Default to production if config not found

        if not production_mode:
            print("📧 Email system in simulation mode - using mock data")
            return get_recent_emails_old_simulation(limit)

        # Import real email connector
        sys.path.insert(0, str(Path(__file__).parent / 'src'))
        from real_email_connector import RealEmailConnector

        # Get real emails from the email server (including read emails for display)
        connector = RealEmailConnector()
        real_emails = connector.get_real_emails(limit=limit, include_read=True)

        # Convert to dashboard format
        emails = []
        for email_data in real_emails:
            emails.append({
                'id': email_data.get('id', f"real_{len(emails)}"),
                'from': email_data.get('from', 'Unknown'),
                'to': email_data.get('to_address', email_data.get('to', '')),
                'subject': email_data.get('subject', 'No Subject'),
                'content': email_data.get('content', ''),
                'full_content': email_data.get('full_content', email_data.get('content', '')),
                'type': email_data.get('type', 'inquiry'),
                'priority': email_data.get('priority', 'medium'),
                'timestamp': email_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'mailbox': email_data.get('mailbox', 'info'),
                'attachments': email_data.get('attachments', []),
                'attachments_list': email_data.get('attachments', []),
                'source': 'real_server_production',
                'status': 'processed',
                'route': f"{email_data.get('mailbox', 'info')}_agent",
                'agent_assigned': email_data.get('mailbox', 'info') + '_agent'
            })

        print(f"🎯 PRODUCTION MODE: Retrieved {len(emails)} real emails from mail.h-bu.de")
        return emails

    except Exception as e:
        print(f"⚠️ Error getting real emails in production mode: {e}")
        print("📧 Falling back to simulation data")
        return get_recent_emails_old_simulation(limit)

def get_recent_emails_old_simulation(limit=20):
    """BACKUP: Get simulated emails (old method) - kept for reference"""
    import random
    from datetime import datetime, timedelta

    # Sample email data from info@h-bu.de with detailed content
    email_templates = [
        {
            'from': 'john.smith@oem1.com',
            'subject': 'URGENT: Need 15,000 Navy Blue Buttons for Q4',
            'type': 'order',
            'content': 'Dear Happy Buttons Team,\n\nWe are in urgent need of 15,000 navy blue premium buttons for our Q4 production schedule. Specifications:\n\n- Material: Premium plastic with matte finish\n- Size: 15mm diameter\n- Color: Navy Blue (Pantone 2768C)\n- Delivery: Required by October 15th\n\nPlease confirm availability and pricing at your earliest convenience.\n\nBest regards,\nJohn Smith\nOEM Procurement Manager',
            'priority': 'high'
        },
        {
            'from': 'sarah.jones@manufacturing.com',
            'subject': 'Re: Custom Logo Buttons - Quote Request',
            'type': 'inquiry',
            'content': 'Hello,\n\nThank you for your initial quote. We would like to proceed with custom logo buttons for our new product line.\n\nQuantity: 5,000 pieces\nLogo: Company branding (files attached)\nDelivery: End of month\n\nCould you please provide:\n1. Final pricing\n2. Sample delivery timeline\n3. Quality certifications\n\nLooking forward to your response.\n\nBest,\nSarah Jones',
            'priority': 'medium',
            'attachments': [
                {'name': 'Company_Logo_Vector.ai', 'size': '2.1 MB', 'type': 'image'},
                {'name': 'Brand_Guidelines.pdf', 'size': '856 KB', 'type': 'document'},
                {'name': 'Button_Specifications.docx', 'size': '124 KB', 'type': 'document'}
            ]
        },
        {
            'from': 'orders@automotive-parts.de',
            'subject': 'BMW Button Order #78451 - Delivery Update',
            'type': 'order',
            'content': 'Happy Buttons GmbH,\n\nThis is a delivery update for Order #78451 (BMW Premium Button Set):\n\n- Order Status: In Production\n- Expected Completion: September 25th\n- Shipping Method: Express Courier\n- Tracking will be provided once shipped\n\nPlease confirm the delivery address is still:\nBMW AG, Munich Plant\nPetuelring 130, 80788 München\n\nBest regards,\nAutomotive Parts Team',
            'priority': 'medium'
        },
        {
            'from': 'quality@supplier-network.com',
            'subject': 'Quality Control Report - Batch #QC-2025-001',
            'type': 'quality',
            'content': 'Quality Assurance Team,\n\nAttached is the quality control report for Batch #QC-2025-001.\n\nSummary:\n- Total pieces tested: 500\n- Pass rate: 99.2%\n- Minor defects: 4 pieces (surface scratches)\n- Major defects: 0\n\nAll pieces meet ISO 9001 standards. The batch is approved for shipment.\n\nDetailed analysis attached.\n\nQuality Team',
            'priority': 'low',
            'attachments': [
                {'name': 'QC_Report_QC-2025-001.pdf', 'size': '1.4 MB', 'type': 'document'},
                {'name': 'Defect_Analysis.xlsx', 'size': '387 KB', 'type': 'spreadsheet'},
                {'name': 'ISO_Compliance_Certificate.pdf', 'size': '245 KB', 'type': 'document'}
            ]
        },
        {
            'from': 'logistics@royal-shipping.co.uk',
            'subject': 'Shipment Notification: UK Delivery Schedule',
            'type': 'logistics',
            'content': 'Dear Happy Buttons,\n\nYour shipment to UK customers is scheduled as follows:\n\nShipment #: RS-2025-0892\nDeparture: September 24th, 08:00\nArrival: September 25th, 14:00\nDestination: London Distribution Center\n\nContents:\n- 12,000 assorted premium buttons\n- 3,500 eco-friendly button sets\n- Custom BMW order (5,000 pieces)\n\nTracking: Available on our portal\n\nRoyal Shipping Team',
            'priority': 'medium'
        },
        {
            'from': 'support@eco-buttons.org',
            'subject': 'Sustainable Material Certification Request',
            'type': 'inquiry',
            'content': 'Dear Happy Buttons Team,\n\nWe are reviewing suppliers for our sustainable fashion initiative. Could you please provide:\n\n1. Environmental certifications\n2. Sustainable material sourcing documentation\n3. Carbon footprint analysis\n4. Recycling programs information\n\nWe are particularly interested in your eco-friendly button line and would appreciate a sample pack.\n\nThank you for your commitment to sustainability.\n\nEco Buttons Organization',
            'priority': 'low'
        },
        {
            'from': 'finance@premium-manufacturing.com',
            'subject': 'Invoice Payment Confirmation - INV-2025-0234',
            'type': 'finance',
            'content': 'Happy Buttons Finance Department,\n\nThis confirms payment of Invoice INV-2025-0234:\n\nAmount: €15,750.00\nPayment Date: September 22nd, 2025\nMethod: Bank Transfer\nReference: PRM-HB-092225\n\nThe payment has been processed and should appear in your account within 2-3 business days.\n\nThank you for your continued partnership.\n\nPremium Manufacturing Finance',
            'priority': 'low',
            'attachments': [
                {'name': 'Payment_Confirmation_INV-2025-0234.pdf', 'size': '128 KB', 'type': 'document'},
                {'name': 'Bank_Transfer_Receipt.pdf', 'size': '89 KB', 'type': 'document'}
            ]
        },
        {
            'from': 'hr@h-bu.de',
            'subject': 'Internal: New Team Member Welcome',
            'type': 'internal',
            'content': 'Team,\n\nPlease join me in welcoming our new Quality Assurance Specialist, Dr. Sophie Chen, who joins us from the automotive industry.\n\nDr. Chen brings 10+ years of experience in quality control and will be leading our new ISO certification initiative.\n\nPlease make her feel welcome when she starts on Monday.\n\nBest regards,\nHR Team\nHappy Buttons GmbH',
            'priority': 'low'
        },
        {
            'from': 'management@h-bu.de',
            'subject': 'Monthly KPI Review Meeting Scheduled',
            'type': 'internal',
            'content': 'Dear Department Heads,\n\nOur monthly KPI review meeting is scheduled for:\n\nDate: September 30th, 2025\nTime: 10:00 - 12:00\nLocation: Conference Room A\nVideo: Teams link will be provided\n\nAgenda:\n1. Q3 Performance Review\n2. Customer Satisfaction Metrics\n3. Production Efficiency Analysis\n4. Q4 Targets Setting\n\nPlease prepare your departmental reports.\n\nBest regards,\nManagement Team',
            'priority': 'medium'
        },
        {
            'from': 'supplier@chinese-manufacturing.cn',
            'subject': 'Production Capacity Update - Q1 2025',
            'type': 'supplier',
            'content': 'Happy Buttons Procurement,\n\nWe are pleased to inform you of our expanded production capacity for Q1 2025:\n\nNew capacity: +40% increase\nDaily output: 50,000 buttons\nNew machinery: 3 additional production lines\nQuality improvements: Enhanced surface finishing\n\nThis will allow us to better serve your increasing demand and reduce lead times to 7-10 days.\n\nWe look forward to continued partnership.\n\nChinese Manufacturing Partner',
            'priority': 'medium'
        }
    ]

    emails = []
    now = datetime.now()

    for i in range(limit):
        template = random.choice(email_templates)
        email_time = now - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))

        attachments = template.get('attachments', [])
        emails.append({
            'id': f'email_{i+1}',
            'from': template['from'],
            'subject': template['subject'],
            'timestamp': email_time.strftime('%Y-%m-%d %H:%M'),
            'type': template['type'],
            'status': random.choice(['processed', 'routed', 'pending']),
            'route': f"{template['type']}@h-bu.de" if template['type'] != 'internal' else 'info@h-bu.de',
            'content': template['content'],
            'priority': template['priority'],
            'attachments': len(attachments),  # Count for display
            'attachments_list': attachments  # Full list for popup
        })

    return sorted(emails, key=lambda x: x['timestamp'], reverse=True)


def get_combined_emails_for_landing(limit=20):
    """Get combined emails from all sources for landing page display"""
    try:
        all_emails = []

        # 1. Get real mailbox emails
        try:
            real_emails = get_recent_emails(limit=limit//3)
            for email in real_emails:
                email['source'] = 'real_mailbox'
                email['email_type'] = email.get('type', 'order')
                all_emails.append(email)
        except Exception as e:
            logger.warning(f"Error loading real emails: {e}")

        # 2. Get enhanced business simulation emails (if running)
        if enhanced_simulation_available:
            try:
                enhanced_emails = enhanced_sim.get_generated_emails(limit//3)
                for email in enhanced_emails:
                    # Convert enhanced simulation format to display format
                    converted_email = {
                        'id': f'enhanced_{hash(str(email))}',
                        'from': email.get('from', 'business@simulation.com'),
                        'subject': email.get('subject', 'Business Simulation Email'),
                        'content': email.get('body', 'Enhanced business simulation email'),
                        'timestamp': email.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S+02:00'),
                        'time_ago': 'gerade eben',
                        'priority': email.get('priority', 'medium'),
                        'type': email.get('needs_escalation', False) and 'urgent' or 'simulation',
                        'email_type': 'business',
                        'source': 'enhanced_simulation',
                        'routing': {
                            'category': 'business',
                            'confidence': 0.95,
                            'destination': 'business_agent'
                        },
                        'attachments': []
                    }
                    all_emails.append(converted_email)
            except Exception as e:
                logger.warning(f"Error loading enhanced simulation emails: {e}")

        # Sort all emails by timestamp (most recent first)
        # Convert timestamps to string format for consistent sorting
        for email in all_emails:
            if 'timestamp' in email and hasattr(email['timestamp'], 'strftime'):
                email['timestamp'] = email['timestamp'].strftime('%Y-%m-%d %H:%M:%S+02:00')

        all_emails.sort(key=lambda x: str(x.get('timestamp', '')), reverse=True)

        # Limit final result
        return all_emails[:limit]

    except Exception as e:
        logger.error(f"Error combining emails for landing: {e}")
        # Fallback to just real emails if combination fails
        try:
            return get_recent_emails(limit=limit)
        except:
            return []


@app.route('/')
def index():
    """Company landing page"""
    # Get combined recent emails from all sources for display
    recent_emails = get_combined_emails_for_landing(limit=20)

    # Get company metrics
    try:
        total_products = len(product_model.get_all_products())
    except (NameError, AttributeError):
        total_products = 8  # Default value

    company_stats = {
        'total_products': total_products,
        'active_departments': 10,
        'global_locations': 6,
        'annual_production': '2.5M',
        'customer_satisfaction': '98.7%'
    }

    return render_template('landing.html',
                         recent_emails=recent_emails,
                         company_stats=company_stats)

@app.route('/dashboard')
def dashboard():
    """System dashboard"""
    return render_template('dashboard.html')

@app.route('/scenarios')
def scenarios():
    """Release 3.0 - Weakness Injection Scenarios Dashboard"""
    return render_template('scenarios.html')

@app.route('/mailbox/<mailbox_name>')
def mailbox_view(mailbox_name):
    """Mailbox view for specific department"""
    # Validate mailbox name
    valid_mailboxes = ['info', 'orders', 'quality', 'supplier', 'oem', 'management', 'logistics', 'finance', 'support']
    if mailbox_name not in valid_mailboxes:
        return redirect('/')

    return render_template('mailbox.html', mailbox_name=mailbox_name)

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

        if True:  # Simplified test for now
            # Create test email object manually
            import uuid
            from datetime import datetime

            # Create a simple email object with the expected structure
            class TestEmail:
                def __init__(self, sender, subject, body):
                    self.id = str(uuid.uuid4())
                    self.sender = sender
                    self.subject = subject
                    self.body = body
                    self.timestamp = datetime.now()
                    self.metadata = self._create_metadata()

                def _create_metadata(self):
                    # Simple classification logic
                    category = 'general'
                    priority = 'medium'
                    is_oem = '@oem' in self.sender.lower()
                    is_urgent = 'urgent' in self.subject.lower() or 'expedite' in self.body.lower()

                    if 'order' in self.subject.lower() or 'need' in self.body.lower():
                        category = 'order'
                    elif 'complaint' in self.subject.lower() or 'problem' in self.body.lower():
                        category = 'complaint'
                    elif 'supplier' in self.sender.lower():
                        category = 'supplier'

                    if is_urgent or is_oem:
                        priority = 'high'

                    return type('Metadata', (), {
                        'category': category,
                        'priority': priority,
                        'is_oem': is_oem,
                        'is_urgent': is_urgent,
                        'confidence_score': 0.85
                    })()

            test_email = TestEmail(sender, subject, body)

            # Create mock routing decision
            class RoutingDecision:
                def __init__(self, email):
                    # Basic routing logic
                    if email.metadata.category == 'order':
                        self.destination = 'orders@h-bu.de'
                        self.sla_hours = 2
                    elif email.metadata.category == 'complaint':
                        self.destination = 'quality@h-bu.de'
                        self.sla_hours = 4
                    elif email.metadata.category == 'supplier':
                        self.destination = 'supplier@h-bu.de'
                        self.sla_hours = 8
                    elif email.metadata.is_oem:
                        self.destination = 'oem1@h-bu.de'
                        self.sla_hours = 1
                    else:
                        self.destination = 'support@h-bu.de'
                        self.sla_hours = 12

                    self.priority = email.metadata.priority
                    self.reasoning = [
                        f"Category: {email.metadata.category}",
                        f"Priority: {email.metadata.priority}",
                        f"OEM Customer: {email.metadata.is_oem}",
                        f"Urgent: {email.metadata.is_urgent}"
                    ]

                    # Select appropriate auto-reply template
                    if email.metadata.category == 'order':
                        self.auto_reply_template = "order_received"
                    elif email.metadata.category == 'complaint':
                        self.auto_reply_template = "complaint_ack"
                    elif email.metadata.is_oem:
                        self.auto_reply_template = "oem_priority_ack"
                    elif email.metadata.is_urgent:
                        self.auto_reply_template = "expedite_ack"
                    else:
                        self.auto_reply_template = "generic_ack"

            routing_decision = RoutingDecision(test_email)

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


@app.route('/api/recent_emails')
def api_recent_emails():
    """API endpoint to get last 100 emails for agents page"""
    try:
        limit = request.args.get('limit', 100, type=int)
        limit = min(limit, 100)  # Cap at 100 emails

        recent_emails = get_recent_emails(limit=limit)

        # Add more details for each email including ID, routing info, and attachments
        enhanced_emails = []
        for i, email in enumerate(recent_emails):
            # Calculate time ago from timestamp
            from datetime import datetime
            try:
                email_time = datetime.strptime(email['timestamp'], '%Y-%m-%d %H:%M')
                time_diff = datetime.now() - email_time
                if time_diff.days > 0:
                    time_ago = f"vor {time_diff.days} Tag{'en' if time_diff.days > 1 else ''}"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    time_ago = f"vor {hours} Stunde{'n' if hours > 1 else ''}"
                else:
                    minutes = max(1, time_diff.seconds // 60)
                    time_ago = f"vor {minutes} Minute{'n' if minutes > 1 else ''}"
            except:
                time_ago = "gerade eben"

            enhanced_email = {
                'id': email.get('id', f'email_{i + 1}'),
                'from': email['from'],
                'subject': email['subject'],
                'type': email['type'],
                'content': email['content'],
                'priority': email['priority'],
                'timestamp': email['timestamp'],
                'time_ago': time_ago,
                'attachments': email.get('attachments_list', []),
                'routing': {
                    'destination': email.get('route', f"{email['type']}@h-bu.de"),
                    'category': email['type'],
                    'confidence': 0.85
                }
            }
            enhanced_emails.append(enhanced_email)

        return jsonify({
            'success': True,
            'emails': enhanced_emails,
            'total': len(enhanced_emails)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/config')
def config():
    """Configuration management page"""
    return render_template('config.html')


@app.route('/teams')
def teams():
    """Team members page (people not agents)"""
    try:
        if not models_available or not team_model:
            # Fallback team data when models aren't available
            teams_by_department = {
                'Management': [
                    {'name': 'Sir Charles Windsor', 'role': 'Chief Executive Officer', 'email': 'charles@h-bu.de', 'phone': '+49-89-123-4567', 'department': 'Management', 'status': 'active'},
                    {'name': 'Lady Margaret Thorne', 'role': 'Chief Operating Officer', 'email': 'margaret@h-bu.de', 'phone': '+49-89-123-4568', 'department': 'Management', 'status': 'active'},
                    {'name': 'Dr. James Harrison', 'role': 'Head of Innovation', 'email': 'james@h-bu.de', 'phone': '+49-89-123-4569', 'department': 'Management', 'status': 'active'}
                ],
                'Orders': [
                    {'name': 'Emma Richardson', 'role': 'Senior Order Specialist', 'email': 'emma@h-bu.de', 'phone': '+49-89-234-5678', 'department': 'Orders', 'status': 'active'},
                    {'name': 'Thomas Mueller', 'role': 'Order Processing Manager', 'email': 'thomas@h-bu.de', 'phone': '+49-89-234-5679', 'department': 'Orders', 'status': 'active'}
                ],
                'OEM': [
                    {'name': 'Victoria Sterling', 'role': 'OEM Relations Director', 'email': 'victoria@h-bu.de', 'phone': '+49-89-345-6789', 'department': 'OEM', 'status': 'active'},
                    {'name': 'Alexander Richter', 'role': 'Premium Account Manager', 'email': 'alexander@h-bu.de', 'phone': '+49-89-345-6780', 'department': 'OEM', 'status': 'active'}
                ],
                'Quality': [
                    {'name': 'Dr. Sophie Chen', 'role': 'Quality Assurance Director', 'email': 'sophie@h-bu.de', 'phone': '+49-89-456-7890', 'department': 'Quality', 'status': 'active'},
                    {'name': 'Michael Thompson', 'role': 'Quality Control Manager', 'email': 'michael@h-bu.de', 'phone': '+49-89-456-7891', 'department': 'Quality', 'status': 'active'}
                ],
                'Support': [
                    {'name': 'Isabella Martinez', 'role': 'Customer Success Manager', 'email': 'isabella@h-bu.de', 'phone': '+49-89-567-8901', 'department': 'Support', 'status': 'active'},
                    {'name': 'William Davies', 'role': 'Technical Support Lead', 'email': 'william@h-bu.de', 'phone': '+49-89-567-8902', 'department': 'Support', 'status': 'active'}
                ],
                'Logistics': [
                    {'name': 'Oliver Schmidt', 'role': 'Logistics Coordinator', 'email': 'oliver@h-bu.de', 'phone': '+49-89-678-9012', 'department': 'Logistics', 'status': 'active'},
                    {'name': 'Sophia Hoffman', 'role': 'Supply Chain Manager', 'email': 'sophia@h-bu.de', 'phone': '+49-89-678-9013', 'department': 'Logistics', 'status': 'active'}
                ]
            }

            department_stats = {
                '_total': {
                    'total_members': 15,
                    'total_departments': 6
                },
                'Management': {'member_count': 3},
                'Orders': {'member_count': 2},
                'OEM': {'member_count': 2},
                'Quality': {'member_count': 2},
                'Support': {'member_count': 2},
                'Logistics': {'member_count': 2}
            }

            return render_template('teams.html',
                                 teams_by_department=teams_by_department,
                                 department_stats=department_stats)

        teams_by_department = team_model.get_teams_by_department()
        department_stats = team_model.get_department_stats()

        return render_template('teams.html',
                             teams_by_department=teams_by_department,
                             department_stats=department_stats)
    except Exception as e:
        logger.error(f"Error loading teams: {e}")
        # Return empty teams structure if there's any error
        teams_by_department = {}
        department_stats = {'_total': {'total_members': 0, 'total_departments': 0}}
        return render_template('teams.html',
                             teams_by_department=teams_by_department,
                             department_stats=department_stats)

@app.route('/agents')
def agents():
    """AI Agent management and activity page"""
    # Get agent status from the monitor
    agent_status = monitor.get_agent_status()
    swarm_status = monitor.get_swarm_status()

    return render_template('agents.html',
                         agent_status=agent_status,
                         swarm_status=swarm_status)


@app.route('/external')
def external():
    """External partners and email processing page"""
    return render_template('external.html')

@app.route('/kpi')
def kpi_dashboard():
    """Business KPI Dashboard"""
    try:
        if not models_available or not kpi_model:
            # Fallback KPI data
            kpis_by_department = {
                'Email Processing': [
                    {'name': 'Auto-handled Share', 'current_value': 67, 'target_value': 70, 'status': 'warning', 'unit': '%'},
                    {'name': 'Average Response Time', 'current_value': 1.2, 'target_value': 1.0, 'status': 'warning', 'unit': 'h'}
                ],
                'Finance': [
                    {'name': 'Invoice Processing Time', 'current_value': 24, 'target_value': 12, 'status': 'warning', 'unit': 'h'}
                ],
                'HR': [
                    {'name': 'Employee Satisfaction', 'current_value': 85, 'target_value': 90, 'status': 'warning', 'unit': '%'},
                    {'name': 'Response Time to Queries', 'current_value': 4, 'target_value': 2, 'status': 'warning', 'unit': 'h'},
                    {'name': 'Policy Compliance Rate', 'current_value': 95, 'target_value': 98, 'status': 'good', 'unit': '%'}
                ],
                'IT': [
                    {'name': 'System Uptime', 'current_value': 99.2, 'target_value': 99.9, 'status': 'good', 'unit': '%'},
                    {'name': 'Ticket Resolution Time', 'current_value': 8, 'target_value': 6, 'status': 'warning', 'unit': 'h'},
                    {'name': 'Security Incident Response', 'current_value': 2, 'target_value': 1, 'status': 'warning', 'unit': 'h'}
                ],
                'Info Center': [
                    {'name': 'Email Triage Accuracy', 'current_value': 92, 'target_value': 95, 'status': 'warning', 'unit': '%'},
                    {'name': 'Royal Courtesy Compliance', 'current_value': 98, 'target_value': 100, 'status': 'good', 'unit': '%'},
                    {'name': 'Customer Satisfaction Score', 'current_value': 87, 'target_value': 90, 'status': 'warning', 'unit': '%'},
                    {'name': 'Response Time SLA', 'current_value': 1.5, 'target_value': 1.0, 'status': 'warning', 'unit': 'h'},
                    {'name': 'Escalation Rate', 'current_value': 5, 'target_value': 3, 'status': 'warning', 'unit': '%'}
                ],
                'Logistics': [
                    {'name': 'On-Time Delivery Rate', 'current_value': 88, 'target_value': 95, 'status': 'warning', 'unit': '%'},
                    {'name': 'Shipping Cost Efficiency', 'current_value': 92, 'target_value': 95, 'status': 'warning', 'unit': '%'}
                ],
                'Manufacturing': [
                    {'name': 'Production Quality Score', 'current_value': 96, 'target_value': 99, 'status': 'good', 'unit': '%'}
                ],
                'OEM': [
                    {'name': 'OEM Customer Retention', 'current_value': 94, 'target_value': 98, 'status': 'good', 'unit': '%'},
                    {'name': 'Premium Service Response', 'current_value': 0.5, 'target_value': 0.25, 'status': 'warning', 'unit': 'h'}
                ],
                'Orders': [
                    {'name': 'Order Processing Speed', 'current_value': 6, 'target_value': 4, 'status': 'warning', 'unit': 'h'},
                    {'name': 'Order Accuracy Rate', 'current_value': 97, 'target_value': 99, 'status': 'good', 'unit': '%'}
                ],
                'Quality': [
                    {'name': 'Defect Detection Rate', 'current_value': 98, 'target_value': 99.5, 'status': 'good', 'unit': '%'},
                    {'name': 'Customer Complaint Resolution', 'current_value': 48, 'target_value': 24, 'status': 'warning', 'unit': 'h'}
                ],
                'Support': [
                    {'name': 'Customer Satisfaction', 'current_value': 91, 'target_value': 95, 'status': 'good', 'unit': '%'}
                ]
            }
            info_center_kpis = [
                {'name': 'Email Triage Accuracy', 'current_value': 92, 'target_value': 95, 'status': 'warning', 'unit': '%'},
                {'name': 'Royal Courtesy Compliance', 'current_value': 98, 'target_value': 100, 'status': 'good', 'unit': '%'}
            ]
            performance_summary = {'overall_score': 85, 'auto_handled_share': 67, 'customer_satisfaction': 92, 'revenue_growth': 15}
            optimization_recommendations = [
                {
                    'title': 'Improve Email Automation',
                    'description': 'Implement advanced AI-powered email classification to increase auto-handled share above target threshold.',
                    'priority': 'High',
                    'expected_impact': '+8% efficiency',
                    'implementation_time': '2-3 weeks',
                    'icon': 'robot'
                },
                {
                    'title': 'Optimize Response Time Workflow',
                    'description': 'Streamline royal courtesy template selection and automate standard responses to reduce average response time.',
                    'priority': 'Medium',
                    'expected_impact': '+15% faster responses',
                    'implementation_time': '1-2 weeks',
                    'icon': 'clock'
                }
            ]
        else:
            # Get all KPI data
            kpis_by_department = kpi_model.get_kpis_by_department()
            info_center_kpis = kpi_model.get_info_center_kpis()
            performance_summary = kpi_model.get_performance_summary()
            optimization_recommendations = kpi_model.get_business_optimization_recommendations()

        # Convert performance_summary to template-expected format
        if isinstance(performance_summary, dict) and 'avg_performance' in performance_summary:
            # Transform dynamic performance summary to template format
            performance_summary = {
                'overall_score': int(performance_summary.get('avg_performance', 85)),
                'auto_handled_share': 67,  # Static value for now
                'customer_satisfaction': 92,  # Static value for now
                'revenue_growth': 15  # Static value for now
            }

        # Validate and fix KPI data structure
        logger.info(f"KPI Dashboard - raw info_center_kpis: {info_center_kpis}")
        logger.info(f"KPI Dashboard - raw kpis_by_department sample: {list(kpis_by_department.keys())}")

        # Check if info_center_kpis has proper structure
        if not info_center_kpis or not isinstance(info_center_kpis, list) or (len(info_center_kpis) > 0 and not info_center_kpis[0].get('name')):
            info_center_kpis = [
                {'name': 'Email Triage Accuracy', 'current_value': 92, 'target_value': 95, 'status': 'warning', 'unit': '%', 'trend': 'stable', 'description': 'Accuracy of email classification and routing'},
                {'name': 'Royal Courtesy Compliance', 'current_value': 98, 'target_value': 100, 'status': 'good', 'unit': '%', 'trend': 'up', 'description': 'Adherence to royal courtesy standards'},
                {'name': 'Response Time SLA', 'current_value': 1.2, 'target_value': 1.0, 'status': 'warning', 'unit': 'h', 'trend': 'stable', 'description': 'Average response time for info@ emails'}
            ]
            logger.info("Using fallback info_center_kpis due to incomplete model data")

        # Check if kpis_by_department has proper structure
        kpi_sample = None
        for dept, kpis in kpis_by_department.items():
            if kpis and len(kpis) > 0:
                kpi_sample = kpis[0]
                break

        if not kpi_sample or not kpi_sample.get('name'):
            # Use fallback data with proper structure
            kpis_by_department = {
                'Email Processing': [
                    {'name': 'Auto-handled Share', 'current_value': 67, 'target_value': 70, 'status': 'warning', 'unit': '%', 'trend': 'stable', 'description': 'Percentage of emails handled automatically'},
                    {'name': 'Average Response Time', 'current_value': 1.2, 'target_value': 1.0, 'status': 'warning', 'unit': 'h', 'trend': 'down', 'description': 'Average time to respond to emails'}
                ],
                'Finance': [
                    {'name': 'Invoice Processing Time', 'current_value': 24, 'target_value': 12, 'status': 'warning', 'unit': 'h', 'trend': 'stable', 'description': 'Time to process incoming invoices'}
                ],
                'Quality': [
                    {'name': 'Defect Detection Rate', 'current_value': 98, 'target_value': 99.5, 'status': 'good', 'unit': '%', 'trend': 'up', 'description': 'Rate of quality issues detected'},
                    {'name': 'Customer Complaint Resolution', 'current_value': 48, 'target_value': 24, 'status': 'warning', 'unit': 'h', 'trend': 'down', 'description': 'Time to resolve customer complaints'}
                ],
                'Support': [
                    {'name': 'Customer Satisfaction', 'current_value': 91, 'target_value': 95, 'status': 'good', 'unit': '%', 'trend': 'up', 'description': 'Customer satisfaction score'}
                ]
            }
            logger.info("Using fallback kpis_by_department due to incomplete model data")

        logger.info(f"KPI Dashboard - transformed performance_summary: {performance_summary}")
        logger.info(f"KPI Dashboard - validated info_center_kpis count: {len(info_center_kpis)}")
        logger.info(f"KPI Dashboard - validated kpis_by_department departments: {list(kpis_by_department.keys())}")

        return render_template('kpi_dashboard.html',
                             kpis_by_department=kpis_by_department,
                             info_center_kpis=info_center_kpis,
                             performance_summary=performance_summary,
                             optimization_recommendations=optimization_recommendations)
    except Exception as e:
        logger.error(f"Error loading KPI dashboard: {e}")
        flash('Error loading KPI dashboard. Please try again.', 'error')
        return redirect(url_for('index'))

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
    """Get detailed mailbox information with real emails"""
    try:
        # Get all emails from combined endpoint
        all_emails = []
        limit = 100  # Get more emails for filtering

        # 1. Get real mailbox emails
        try:
            real_emails = get_recent_emails(limit=limit//3)
            for email in real_emails:
                email['source'] = 'real_mailbox'
                email['email_type'] = email.get('type', 'order')
                all_emails.append(email)
        except Exception as e:
            logger.warning(f"Error loading real emails: {e}")

        # 2. Get TimeWarp simulation emails
        try:
            import requests
            response = requests.get(f'http://localhost:{request.environ.get("SERVER_PORT", "80")}/api/emails/recent?limit={limit//3}')
            if response.status_code == 200:
                sim_data = response.json()
                if sim_data.get('emails'):
                    for email in sim_data['emails'][:limit//3]:
                        email['source'] = 'timewarp_simulation'
                        email['email_type'] = email.get('category', 'order')
                        if 'timestamp' in email:
                            email['timestamp'] = email['timestamp'].replace('T', ' ')
                        all_emails.append(email)
        except Exception as e:
            logger.warning(f"Error loading TimeWarp emails: {e}")

        # 3. Get enhanced business simulation emails
        if enhanced_simulation_available:
            try:
                enhanced_emails = enhanced_sim.get_generated_emails(limit//3)
                for email in enhanced_emails:
                    converted_email = {
                        'id': f'enhanced_{hash(str(email))}',
                        'from': email.get('from', 'business@simulation.com'),
                        'subject': email.get('subject', 'Business Simulation Email'),
                        'content': email.get('body', 'Enhanced business simulation email'),
                        'timestamp': email.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
                        'time_ago': 'simulation',
                        'priority': email.get('priority', 'medium'),
                        'type': 'simulation',
                        'email_type': 'business',
                        'source': 'enhanced_simulation'
                    }
                    all_emails.append(converted_email)
            except Exception as e:
                logger.warning(f"Error loading enhanced simulation emails: {e}")

        # 4. Get scenario emails
        try:
            from src.scenarios.email_generator import scenario_email_generator
            scenario_emails = scenario_email_generator.get_scenario_emails(limit=limit//4)
            for email in scenario_emails:
                converted_email = {
                    'id': email.get('id', f'scenario_{hash(str(email))}'),
                    'from': email.get('from', 'scenario@simulation.com'),
                    'subject': email.get('subject', 'Scenario Email'),
                    'content': email.get('body', 'Scenario simulation email'),
                    'timestamp': email.get('timestamp', datetime.now().isoformat()).replace('T', ' '),
                    'time_ago': 'scenario',
                    'priority': email.get('urgency', 'medium'),
                    'type': email.get('email_type', 'scenario'),
                    'email_type': email.get('scenario_type', 'business'),
                    'source': 'scenario_emails',
                    'scenario_info': email.get('scenario_info', {})
                }
                all_emails.append(converted_email)
        except Exception as e:
            logger.warning(f"Error loading scenario emails: {e}")

        # Filter emails by mailbox type
        filtered_emails = []
        for email in all_emails:
            email_type = email.get('email_type', '').lower()
            routing_category = email.get('routing', {}).get('category', '').lower() if isinstance(email.get('routing'), dict) else ''

            # Route emails to appropriate mailboxes
            if mailbox_name == 'orders' and (
                email_type in ['order', 'expedite_request'] or
                'order' in email.get('subject', '').lower() or
                'expedite' in email.get('subject', '').lower() or
                routing_category in ['order', 'expedite']
            ):
                filtered_emails.append(email)
            elif mailbox_name == 'quality' and (
                email_type in ['quality', 'complaint'] or
                'quality' in email.get('subject', '').lower() or
                routing_category == 'quality'
            ):
                filtered_emails.append(email)
            elif mailbox_name == 'supplier' and (
                email_type == 'supplier' or
                'supplier' in email.get('subject', '').lower() or
                routing_category == 'supplier'
            ):
                filtered_emails.append(email)
            elif mailbox_name == 'oem' and (
                email_type == 'oem' or
                'oem' in email.get('subject', '').lower() or
                routing_category == 'oem'
            ):
                filtered_emails.append(email)
            elif mailbox_name == 'management' and (
                email_type == 'management' or
                email.get('priority') == 'critical' or
                routing_category == 'management'
            ):
                filtered_emails.append(email)
            elif mailbox_name == 'info':
                # Info gets all emails for now
                filtered_emails.append(email)

        # Sort by timestamp
        filtered_emails.sort(key=lambda x: str(x.get('timestamp', '')), reverse=True)

        # Format recent emails for display
        recent_emails = []
        for email in filtered_emails[:10]:  # Show last 10 emails
            recent_emails.append({
                'id': email.get('id'),
                'from': email.get('from', 'Unknown'),
                'subject': email.get('subject', 'No Subject'),
                'time': email.get('time_ago', 'Unknown'),
                'timestamp': email.get('timestamp'),
                'routed_to': f'{mailbox_name}@h-bu.de',
                'status': email.get('status', 'processed'),
                'priority': email.get('priority', 'medium'),
                'source': email.get('source', 'unknown'),
                'content': email.get('content', '')[:200] + '...' if len(email.get('content', '')) > 200 else email.get('content', '')
            })

        return jsonify({
            'address': f'{mailbox_name}@h-bu.de',
            'total_emails': len(filtered_emails),
            'today_emails': len([e for e in filtered_emails if 'today' in str(e.get('timestamp', '')) or 'vor' in str(e.get('time_ago', ''))]),
            'recent_emails': recent_emails
        })
    except Exception as e:
        logger.error(f"Error in mailbox endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'address': f'{mailbox_name}@h-bu.de',
            'total_emails': 0,
            'today_emails': 0,
            'recent_emails': []
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


# ===== WEBSHOP ROUTES =====

@app.route('/shop')
def shop():
    """Main webshop page"""
    try:
        if not models_available or not product_model:
            # Fallback shop data
            products_by_category = {
                'Premium': [
                    {'id': 1, 'name': 'Royal Blue Premium Button', 'price': 12.50, 'category': 'Premium', 'stock_quantity': 150},
                    {'id': 2, 'name': 'BMW M-Series Button Set', 'price': 45.99, 'category': 'Premium', 'stock_quantity': 75}
                ],
                'OEM': [
                    {'id': 3, 'name': 'Audi Q-Series Interior Buttons', 'price': 89.99, 'category': 'OEM', 'stock_quantity': 50}
                ]
            }
            total_products = 3
        else:
            products = product_model.get_all_products()

            # Group products by category for better display
            products_by_category = {}
            for product in products:
                category = product['category']
                if category not in products_by_category:
                    products_by_category[category] = []
                products_by_category[category].append(product)
            total_products = len(products)

        return render_template('shop.html',
                             products_by_category=products_by_category,
                             total_products=total_products)
    except Exception as e:
        logger.error(f"Error loading shop: {e}")
        flash('Error loading shop. Please try again.', 'error')
        return redirect(url_for('index'))


@app.route('/shop/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    try:
        product = product_model.get_product_by_id(product_id)
        if not product:
            flash('Product not found.', 'error')
            return redirect(url_for('shop'))

        # Parse specifications if available
        if product['specifications']:
            import json
            try:
                product['specs'] = json.loads(product['specifications'])
            except:
                product['specs'] = {}
        else:
            product['specs'] = {}

        # Get related products from same category
        related_products = product_model.get_products_by_category(product['category'])
        related_products = [p for p in related_products if p['id'] != product_id][:4]

        return render_template('product_detail.html',
                             product=product,
                             related_products=related_products)
    except Exception as e:
        logger.error(f"Error loading product {product_id}: {e}")
        flash('Error loading product details.', 'error')
        return redirect(url_for('shop'))


@app.route('/shop/cart')
def cart():
    """Shopping cart page"""
    return render_template('cart.html')


@app.route('/shop/checkout')
def checkout():
    """Checkout page"""
    return render_template('checkout.html')


# ===== WEBSHOP API ROUTES =====

@app.route('/api/shop/products')
def api_products():
    """API: Get all products"""
    try:
        products = product_model.get_all_products()
        return jsonify({
            'status': 'success',
            'products': products,
            'total_count': len(products)
        })
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/shop/products/<int:product_id>')
def api_product_detail(product_id):
    """API: Get product by ID"""
    try:
        product = product_model.get_product_by_id(product_id)
        if not product:
            return jsonify({'status': 'error', 'message': 'Product not found'}), 404

        return jsonify({
            'status': 'success',
            'product': product
        })
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/shop/cart/add', methods=['POST'])
def api_add_to_cart():
    """API: Add item to cart (session-based)"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        # Validate product exists and has stock
        product = product_model.get_product_by_id(product_id)
        if not product:
            return jsonify({'status': 'error', 'message': 'Product not found'}), 404

        if product['stock_quantity'] < quantity:
            return jsonify({'status': 'error', 'message': 'Insufficient stock'}), 400

        return jsonify({
            'status': 'success',
            'message': 'Product added to cart',
            'product': product,
            'quantity': quantity
        })
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/shop/orders', methods=['POST'])
def api_create_order():
    """API: Create new order"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['customer_name', 'customer_email', 'shipping_address', 'items']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400

        # Check if models are available
        if not models_available or not product_model or not order_model:
            # Fallback mode - simulate order creation with mock data
            import random
            order_id = random.randint(100000, 999999)

            # Calculate total from items using fallback product data
            fallback_products = {
                1: {'name': 'Royal Blue Premium Button', 'price': 12.50, 'stock_quantity': 150},
                2: {'name': 'BMW M-Series Button Set', 'price': 45.99, 'stock_quantity': 75},
                3: {'name': 'OEM Quality Standard Button', 'price': 8.99, 'stock_quantity': 500},
                4: {'name': 'Eco-Friendly Green Button', 'price': 11.25, 'stock_quantity': 200},
                5: {'name': 'Premium Black Leather Button', 'price': 18.50, 'stock_quantity': 100}
            }

            total_amount = 0
            for item in data['items']:
                product_id = item['product_id']
                if product_id in fallback_products:
                    product = fallback_products[product_id]
                    item_total = float(product['price']) * item['quantity']
                    total_amount += item_total
                else:
                    # Default price for unknown products
                    item_total = 10.00 * item['quantity']
                    total_amount += item_total

            logger.info(f"Simulated order creation for {data['customer_name']} - Order #{order_id}")

            return jsonify({
                'status': 'success',
                'message': 'Order created successfully',
                'order_id': order_id,
                'total_amount': total_amount
            })

        # Normal mode with database models
        # Calculate total and validate items
        total_amount = 0
        order_items = []

        for item in data['items']:
            product = product_model.get_product_by_id(item['product_id'])
            if not product:
                return jsonify({'status': 'error', 'message': f'Product {item["product_id"]} not found'}), 404

            if product['stock_quantity'] < item['quantity']:
                return jsonify({'status': 'error', 'message': f'Insufficient stock for {product["name"]}'}), 400

            item_total = float(product['price']) * item['quantity']
            total_amount += item_total

            order_items.append({
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'unit_price': product['price'],
                'total_price': item_total
            })

        # Create order data
        order_data = {
            'customer_name': data['customer_name'],
            'customer_email': data['customer_email'],
            'customer_phone': data.get('customer_phone'),
            'customer_company': data.get('customer_company'),
            'shipping_address': data['shipping_address'],
            'billing_address': data.get('billing_address'),
            'total_amount': total_amount,
            'notes': data.get('notes')
        }

        # Create order
        order_id = order_model.create_order(order_data, order_items)

        # Update stock quantities
        for item in order_items:
            product_model.update_stock(item['product_id'], item['quantity'])

        # Get complete order details for email generation
        complete_order = order_model.get_order_by_id(order_id)

        # Generate order confirmation email
        try:
            email_data = order_email_generator.generate_order_email(complete_order)
            order_email_generator.integrate_with_email_system(email_data)
            logger.info(f"Generated order confirmation email for order {order_id}")
        except Exception as e:
            logger.error(f"Failed to generate order email: {e}")
            # Continue with order creation even if email fails

        return jsonify({
            'status': 'success',
            'message': 'Order created successfully',
            'order_id': order_id,
            'total_amount': total_amount
        })
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/shop/orders/<int:order_id>')
def api_get_order(order_id):
    """API: Get order details"""
    try:
        order = order_model.get_order_by_id(order_id)
        if not order:
            return jsonify({'status': 'error', 'message': 'Order not found'}), 404

        return jsonify({
            'status': 'success',
            'order': order
        })
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/kpi/refresh')
def api_kpi_refresh():
    """API: Refresh KPI data"""
    try:
        # Check if KPI model is available
        if kpi_model is None:
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'message': 'KPI model not available, using fallback data',
                'kpis_by_department': {},
                'info_center_kpis': [],
                'performance_summary': {'overall_score': 85, 'auto_handled_share': 67, 'customer_satisfaction': 92, 'revenue_growth': 15}
            })

        # Get updated KPI data
        kpis_by_department = kpi_model.get_kpis_by_department()
        info_center_kpis = kpi_model.get_info_center_kpis()
        performance_summary = kpi_model.get_performance_summary()

        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'kpis_by_department': kpis_by_department,
            'info_center_kpis': info_center_kpis,
            'performance_summary': performance_summary
        })
    except Exception as e:
        logger.error(f"Error refreshing KPI data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/kpi/summary')
def api_kpi_summary():
    """API: Get KPI summary for dashboard"""
    try:
        performance_summary = kpi_model.get_performance_summary()
        info_center_kpis = kpi_model.get_info_center_kpis()

        # Calculate key metrics
        critical_kpis = [kpi for kpi in info_center_kpis if kpi['status'] == 'critical']
        warning_kpis = [kpi for kpi in info_center_kpis if kpi['status'] == 'warning']

        summary = {
            'overall_health': 'excellent' if len(critical_kpis) == 0 and len(warning_kpis) <= 2 else 'good' if len(critical_kpis) == 0 else 'needs_attention',
            'critical_issues': len(critical_kpis),
            'warning_issues': len(warning_kpis),
            'total_kpis': len(info_center_kpis),
            'performance_score': performance_summary.get('overall_score', 85),
            'auto_handled_share': performance_summary.get('auto_handled_share', 67),
            'customer_satisfaction': performance_summary.get('customer_satisfaction', 92)
        }

        return jsonify({
            'status': 'success',
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting KPI summary: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Demo Flow Integration
@app.route('/demo-flow')
def demo_flow():
    """Demo email flow visualization"""
    try:
        # Import demo enhancer
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        from demo_email_enhancer import DemoEmailEnhancer

        # Load demo data
        enhancer = DemoEmailEnhancer()
        enhanced_emails = enhancer.get_enhanced_emails_for_demo(limit=10)
        demo_stats = enhancer.get_live_demo_stats()

        # Prepare stats for template
        stats = {
            'total_emails': demo_stats['total_real_emails'],
            'processed_today': demo_stats['demo_metrics']['emails_processed_today'],
            'auto_rate': int(demo_stats['demo_metrics']['auto_response_rate']),
            'sla_compliance': int(demo_stats['demo_metrics']['sla_compliance'])
        }

        return render_template('demo_flow.html', emails=enhanced_emails, stats=stats, current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    except Exception as e:
        logger.error(f"Error in demo flow: {e}")
        return render_template('demo_flow.html', emails=[], stats={
            'total_emails': 0,
            'processed_today': 0,
            'auto_rate': 0,
            'sla_compliance': 0
        }, current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/demo/flow-stats')
def api_demo_flow_stats():
    """API endpoint for demo flow statistics"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        from demo_email_enhancer import DemoEmailEnhancer

        enhancer = DemoEmailEnhancer()
        demo_stats = enhancer.get_live_demo_stats()

        return jsonify({
            'success': True,
            'stats': {
                'total_emails': demo_stats['total_real_emails'],
                'processed_today': demo_stats['demo_metrics']['emails_processed_today'],
                'auto_rate': int(demo_stats['demo_metrics']['auto_response_rate']),
                'sla_compliance': int(demo_stats['demo_metrics']['sla_compliance'])
            },
            'stage_counts': {
                'received': 5,
                'parsed': 4,
                'classified': 6,
                'routed': 8,
                'processing': 2,
                'completed': demo_stats['total_real_emails']
            }
        })

    except Exception as e:
        logger.error(f"Error getting demo flow stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Initialize TimeWarp system integration
if timewarp_available:
    try:
        # Load TimeWarp configuration
        timewarp_config = get_timewarp_config()

        # Initialize TimeWarp UI with Flask app and SocketIO
        timewarp_ui = init_timewarp_ui(app, socketio)

        # Initialize TimeWarp email generator with configuration
        timewarp_email_gen = get_email_generator()

        # Initialize TimeWarp agent processor
        timewarp_agent_processor = init_agent_processor()

        # Add email callback to integrate with existing system
        def timewarp_email_callback(email):
            try:
                # Process generated emails through existing system
                logger.info(f"TimeWarp generated: {email['type']} from {email['from']}")

                # Route to appropriate agents based on configuration
                mailbox_id = timewarp_config.get_mailbox_for_email(email.get('to', 'info@h-bu.de'))
                if mailbox_id:
                    agents = timewarp_config.get_agents_for_mailbox(mailbox_id)
                    logger.debug(f"Email routed to agents: {agents}")

                # Process through TimeWarp agent system
                success = timewarp_agent_processor.process_email(email)
                if success:
                    logger.debug(f"Email {email.get('id')} processed by agent system")
                else:
                    logger.warning(f"Failed to process email {email.get('id')} through agent system")

            except Exception as e:
                logger.error(f"Error processing TimeWarp email: {e}")

        timewarp_email_gen.add_generation_callback(timewarp_email_callback)

        # Initialize TimeWarp engine with configuration
        timewarp_engine = get_timewarp()
        timewarp_engine.register_email_generator(timewarp_email_gen)

        # Set email patterns from configuration
        email_patterns = timewarp_config.get_email_patterns()
        if email_patterns:
            timewarp_engine.configure_email_patterns(email_patterns)

        # Start TimeWarp systems based on configuration
        settings = timewarp_config.get_timewarp_settings()
        if settings.get('auto_start', False):
            timewarp_engine.start()
            timewarp_email_gen.start_generation()
            logger.info("🚀 TimeWarp auto-started")
        else:
            logger.info("⏸️ TimeWarp ready (manual start required)")

        # Add TimeWarp management API endpoints
        @app.route('/api/timewarp/status', methods=['GET'])
        def get_timewarp_status():
            """Get TimeWarp system status"""
            try:
                if not timewarp_available:
                    return jsonify({'success': False, 'error': 'TimeWarp not available', 'status': 'disabled'}), 503

                engine = get_timewarp()
                status = engine.get_time_status() if engine else {}

                return jsonify({
                    'success': True,
                    'status': 'ready',
                    'current_level': status.get('current_level', 1),
                    'max_level': 5,
                    'active': status.get('active', False),
                    'simulation_time': status.get('simulation_time'),
                    'real_time': status.get('real_time'),
                    'acceleration_factor': status.get('acceleration_factor', 1),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting TimeWarp status: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @app.route('/api/timewarp/agents/status', methods=['GET'])
        def get_agent_status():
            """Get status of all TimeWarp agents"""
            try:
                if not timewarp_available:
                    return jsonify({'success': False, 'error': 'TimeWarp not available'}), 503

                processor = get_agent_processor()
                agent_stats = processor.get_processing_statistics()

                # Get detailed status for each agent
                agent_details = {}
                for agent_id in timewarp_config.get_all_agents().keys():
                    agent_details[agent_id] = processor.get_agent_status(agent_id)

                return jsonify({
                    'success': True,
                    'statistics': agent_stats,
                    'agents': agent_details,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error getting agent status: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @app.route('/api/timewarp/mailboxes', methods=['GET'])
        def get_mailbox_configuration():
            """Get mailbox configuration and statistics"""
            try:
                if not timewarp_available:
                    return jsonify({'success': False, 'error': 'TimeWarp not available'}), 503

                mailboxes = {}
                for mailbox_id, config in timewarp_config.get_all_mailboxes().items():
                    mailboxes[mailbox_id] = {
                        'address': config.address,
                        'display_name': config.display_name,
                        'assigned_agents': config.assigned_agents,
                        'auto_routing': config.auto_routing,
                        'response_templates': config.response_templates,
                        'timewarp_priority': config.timewarp_priority,
                        'max_emails_per_hour': config.max_emails_per_hour,
                        'current_queue_size': sum(
                            get_agent_processor().agent_queues[agent].qsize()
                            for agent in config.assigned_agents
                            if agent in get_agent_processor().agent_queues
                        )
                    }

                return jsonify({
                    'success': True,
                    'mailboxes': mailboxes,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error getting mailbox configuration: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @app.route('/api/timewarp/config', methods=['GET'])
        def get_timewarp_configuration():
            """Get complete TimeWarp configuration"""
            try:
                if not timewarp_available:
                    return jsonify({'success': False, 'error': 'TimeWarp not available'}), 503

                config_data = timewarp_config.export_config_for_ui()
                summary = timewarp_config.get_configuration_summary()

                return jsonify({
                    'success': True,
                    'configuration': config_data,
                    'summary': summary,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error getting TimeWarp configuration: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @app.route('/api/timewarp/config', methods=['POST'])
        def update_timewarp_configuration():
            """Update TimeWarp configuration"""
            try:
                if not timewarp_available:
                    return jsonify({'success': False, 'error': 'TimeWarp not available'}), 503

                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'No configuration data provided'}), 400

                success = True
                errors = []

                # Update different configuration sections
                if 'timewarp' in data:
                    if not timewarp_config.update_timewarp_settings(data['timewarp']):
                        success = False
                        errors.append('Failed to update TimeWarp settings')

                if 'email_patterns' in data:
                    if not timewarp_config.update_email_patterns(data['email_patterns']):
                        success = False
                        errors.append('Failed to update email patterns')

                if 'agents' in data:
                    for agent_id, agent_updates in data['agents'].items():
                        if not timewarp_config.update_agent_config(agent_id, agent_updates):
                            success = False
                            errors.append(f'Failed to update agent {agent_id}')

                # Save configuration
                if success:
                    timewarp_config.save_configuration()

                return jsonify({
                    'success': success,
                    'errors': errors if not success else [],
                    'message': 'Configuration updated successfully' if success else 'Configuration update failed'
                })

            except Exception as e:
                logger.error(f"Error updating TimeWarp configuration: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @app.route('/api/timewarp/statistics', methods=['GET'])
        def get_timewarp_statistics():
            """Get comprehensive TimeWarp system statistics"""
            try:
                if not timewarp_available:
                    return jsonify({'success': False, 'error': 'TimeWarp not available'}), 503

                # Get statistics from various components
                timewarp_status = get_timewarp().get_time_status()
                email_gen_stats = get_email_generator().get_generation_stats()
                agent_stats = get_agent_processor().get_processing_statistics()
                config_summary = timewarp_config.get_configuration_summary()

                # Add business simulator stats if available
                business_stats = {}
                try:
                    from timewarp_business_simulation import get_business_simulator
                    business_stats = get_business_simulator().get_generation_statistics()
                except ImportError:
                    pass

                return jsonify({
                    'success': True,
                    'statistics': {
                        'timewarp': timewarp_status,
                        'email_generation': email_gen_stats,
                        'agent_processing': agent_stats,
                        'business_simulation': business_stats,
                        'configuration': config_summary
                    },
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error getting TimeWarp statistics: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # TimeWarp Control Endpoints are handled by TimeWarp UI class

        logger.info("✅ TimeWarp system initialized with configuration and API endpoints")

    except Exception as e:
        logger.error(f"Error initializing TimeWarp system: {e}")
        timewarp_available = False
else:
    logger.info("⚠️ TimeWarp system not available - running without time acceleration")

# Enhanced Business Simulation Integration
try:
    from src.enhanced_business_simulation import get_enhanced_simulation
    enhanced_sim = get_enhanced_simulation()
    enhanced_simulation_available = True

    @app.route('/api/simulation/start', methods=['POST'])
    def start_enhanced_simulation():
        """Start enhanced business week simulation"""
        try:
            data = request.get_json() or {}
            speed_multiplier = data.get('speed', 1)

            enhanced_sim.start_simulation(speed_multiplier)

            return jsonify({
                'success': True,
                'message': f'Enhanced business simulation started (Speed: {speed_multiplier}x)',
                'status': enhanced_sim.get_simulation_status()
            })
        except Exception as e:
            logger.error(f"Error starting enhanced simulation: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/simulation/stop', methods=['POST'])
    def stop_enhanced_simulation():
        """Stop enhanced business simulation"""
        try:
            enhanced_sim.stop_simulation()
            return jsonify({
                'success': True,
                'message': 'Enhanced simulation stopped'
            })
        except Exception as e:
            logger.error(f"Error stopping enhanced simulation: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/simulation/status', methods=['GET'])
    def get_enhanced_simulation_status():
        """Get enhanced simulation status"""
        try:
            return jsonify({
                'success': True,
                'status': enhanced_sim.get_simulation_status(),
                'available': True
            })
        except Exception as e:
            logger.error(f"Error getting simulation status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/simulation/emails', methods=['GET'])
    def get_simulation_emails():
        """Get emails generated by enhanced simulation"""
        try:
            limit = request.args.get('limit', 50, type=int)
            emails = enhanced_sim.get_generated_emails(limit)

            return jsonify({
                'success': True,
                'emails': emails,
                'total': len(emails)
            })
        except Exception as e:
            logger.error(f"Error getting simulation emails: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    logger.info("✅ Enhanced Business Simulation integrated successfully")

except Exception as e:
    logger.error(f"Error integrating enhanced simulation: {e}")
    enhanced_simulation_available = False

# Combined Email Feed Endpoint for Landing Page
# Release 3.0 Scenario API Endpoints
if scenario_system_available:
    @app.route('/api/v3/scenarios', methods=['GET'])
    def get_scenarios():
        """Get all available scenarios"""
        try:
            scenario_manager = monitor.scenario_manager
            if not scenario_manager:
                return jsonify({'success': False, 'error': 'Scenario system not available'}), 503

            scenarios = scenario_manager.get_available_scenarios()
            return jsonify({
                'success': True,
                'scenarios': scenarios,
                'total': len(scenarios)
            })
        except Exception as e:
            logger.error(f"Error getting scenarios: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v3/scenarios/emails', methods=['GET'])
    def get_scenario_emails():
        """Get scenario-generated emails"""
        try:
            # Import the scenario email generator
            from src.scenarios.email_generator import scenario_email_generator

            scenario_type = request.args.get('scenario_type')
            limit = int(request.args.get('limit', 50))

            emails = scenario_email_generator.get_scenario_emails(scenario_type, limit)

            return jsonify({
                'success': True,
                'emails': emails,
                'count': len(emails)
            })
        except Exception as e:
            logger.error(f"Error getting scenario emails: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v3/scenarios/<scenario_id>', methods=['GET'])
    def get_scenario_details(scenario_id):
        """Get detailed information about a specific scenario"""
        try:
            scenario_manager = monitor.scenario_manager
            if not scenario_manager:
                return jsonify({'success': False, 'error': 'Scenario system not available'}), 503

            details = scenario_manager.get_scenario_details(scenario_id)
            if not details:
                return jsonify({'success': False, 'error': f'Scenario not found: {scenario_id}'}), 404

            return jsonify({
                'success': True,
                'scenario': details
            })
        except Exception as e:
            logger.error(f"Error getting scenario details: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v3/scenarios/<scenario_id>/start', methods=['POST'])
    def start_scenario(scenario_id):
        """Start a specific scenario"""
        try:
            scenario_manager = monitor.scenario_manager
            if not scenario_manager:
                return jsonify({'success': False, 'error': 'Scenario system not available'}), 503

            data = request.get_json() or {}
            duration_seconds = data.get('duration_seconds')

            result = asyncio.run(scenario_manager.start_scenario(scenario_id, duration_seconds))
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error starting scenario: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v3/scenarios/<scenario_id>/stop', methods=['POST'])
    def stop_scenario(scenario_id):
        """Stop a running scenario"""
        try:
            scenario_manager = monitor.scenario_manager
            if not scenario_manager:
                return jsonify({'success': False, 'error': 'Scenario system not available'}), 503

            result = asyncio.run(scenario_manager.stop_scenario(scenario_id))
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error stopping scenario: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v3/scenarios/<scenario_id>/enable', methods=['POST'])
    def enable_scenario(scenario_id):
        """Enable a scenario"""
        try:
            scenario_manager = monitor.scenario_manager
            if not scenario_manager:
                return jsonify({'success': False, 'error': 'Scenario system not available'}), 503

            result = scenario_manager.enable_scenario(scenario_id)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error enabling scenario: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v3/scenarios/<scenario_id>/disable', methods=['POST'])
    def disable_scenario(scenario_id):
        """Disable a scenario"""
        try:
            scenario_manager = monitor.scenario_manager
            if not scenario_manager:
                return jsonify({'success': False, 'error': 'Scenario system not available'}), 503

            result = scenario_manager.disable_scenario(scenario_id)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error disabling scenario: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v3/scenarios/status', methods=['GET'])
    def get_scenarios_status():
        """Get status of all scenarios"""
        try:
            scenario_manager = monitor.scenario_manager
            if not scenario_manager:
                return jsonify({'success': False, 'error': 'Scenario system not available'}), 503

            system_status = scenario_manager.get_system_status()
            return jsonify({
                'success': True,
                'status': system_status
            })
        except Exception as e:
            logger.error(f"Error getting scenario status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v3/scenarios/metrics', methods=['GET'])
    def get_scenarios_metrics():
        """Get metrics for all scenarios"""
        try:
            scenario_manager = monitor.scenario_manager
            if not scenario_manager:
                return jsonify({'success': False, 'error': 'Scenario system not available'}), 503

            scenario_id = request.args.get('scenario_id')
            metrics = scenario_manager.get_scenario_metrics(scenario_id)

            return jsonify({
                'success': True,
                'metrics': metrics
            })
        except Exception as e:
            logger.error(f"Error getting scenario metrics: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # KPI Tracking API Endpoints
    @app.route('/api/v3/kpi/current', methods=['GET'])
    def get_current_kpi_metrics():
        """Get current real-time KPI metrics"""
        try:
            scenario_manager = monitor.scenario_manager
            if not scenario_manager:
                return jsonify({'success': False, 'error': 'Scenario system not available'}), 503

            kpi_metrics = scenario_manager.get_real_time_kpi_metrics()
            return jsonify({
                'success': True,
                'kpi_metrics': kpi_metrics
            })
        except Exception as e:
            logger.error(f"Error getting current KPI metrics: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v3/kpi/history/<kpi_type>', methods=['GET'])
    def get_kpi_history(kpi_type):
        """Get KPI history for visualization"""
        try:
            scenario_manager = monitor.scenario_manager
            if not scenario_manager:
                return jsonify({'success': False, 'error': 'Scenario system not available'}), 503

            hours = request.args.get('hours', 1, type=int)
            history = scenario_manager.get_kpi_history(kpi_type, hours)

            return jsonify({
                'success': True,
                'kpi_type': kpi_type,
                'hours': hours,
                'history': history
            })
        except Exception as e:
            logger.error(f"Error getting KPI history for {kpi_type}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v3/kpi/alerts', methods=['GET'])
    def get_kpi_alerts():
        """Get KPI alert summary"""
        try:
            scenario_manager = monitor.scenario_manager
            if not scenario_manager:
                return jsonify({'success': False, 'error': 'Scenario system not available'}), 503

            hours = request.args.get('hours', 1, type=int)
            kpi_metrics = scenario_manager.get_real_time_kpi_metrics()
            alert_summary = kpi_metrics.get('alert_summary', {})

            return jsonify({
                'success': True,
                'hours': hours,
                'alert_summary': alert_summary
            })
        except Exception as e:
            logger.error(f"Error getting KPI alerts: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    logger.info("✅ Release 3.0 Scenario API endpoints registered successfully")

else:
    logger.warning("⚠️ Scenario system not available - API endpoints not registered")

@app.route('/api/emails/combined')
def get_combined_emails():
    """Get combined emails from all sources for landing page display"""
    try:
        limit = request.args.get('limit', 20, type=int)
        all_emails = []

        # 1. Get real mailbox emails
        try:
            real_emails = get_recent_emails(limit=limit//3)
            for email in real_emails:
                # Normalize real email format
                email['source'] = 'real_mailbox'
                email['email_type'] = email.get('type', 'order')
                all_emails.append(email)
        except Exception as e:
            logger.warning(f"Error loading real emails: {e}")

        # 2. Get TimeWarp simulation emails
        try:
            import requests
            response = requests.get(f'http://localhost:{request.environ.get("SERVER_PORT", "8080")}/api/emails/recent?limit={limit//3}')
            if response.status_code == 200:
                sim_data = response.json()
                if sim_data.get('emails'):
                    for email in sim_data['emails'][:limit//3]:
                        email['source'] = 'timewarp_simulation'
                        email['email_type'] = email.get('category', 'order')
                        # Convert timestamp format if needed
                        if 'timestamp' in email:
                            email['timestamp'] = email['timestamp'].replace('T', ' ')
                        all_emails.append(email)
        except Exception as e:
            logger.warning(f"Error loading TimeWarp emails: {e}")

        # 3. Get enhanced business simulation emails
        if enhanced_simulation_available:
            try:
                enhanced_emails = enhanced_sim.get_generated_emails(limit//3)
                for email in enhanced_emails:
                    # Convert enhanced simulation format to display format
                    converted_email = {
                        'id': f'enhanced_{hash(str(email))}',
                        'from': email.get('from', 'business@simulation.com'),
                        'subject': email.get('subject', 'Business Simulation Email'),
                        'content': email.get('body', 'Enhanced business simulation email'),
                        'timestamp': email.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
                        'time_ago': 'simulation',
                        'priority': email.get('priority', 'medium'),
                        'type': 'simulation',
                        'email_type': 'business',
                        'source': 'enhanced_simulation',
                        'routing': {
                            'category': 'business',
                            'confidence': 0.95,
                            'destination': 'business_agent'
                        },
                        'attachments': []
                    }
                    all_emails.append(converted_email)
            except Exception as e:
                logger.warning(f"Error loading enhanced simulation emails: {e}")

        # 4. Get scenario emails from weakness injection scenarios
        try:
            from src.scenarios.email_generator import scenario_email_generator
            scenario_emails = scenario_email_generator.get_scenario_emails(limit=limit//4)
            for email in scenario_emails:
                # Convert scenario email format to display format
                converted_email = {
                    'id': email.get('id', f'scenario_{hash(str(email))}'),
                    'from': email.get('from', 'scenario@simulation.com'),
                    'subject': email.get('subject', 'Scenario Email'),
                    'content': email.get('body', 'Scenario simulation email'),
                    'timestamp': email.get('timestamp', datetime.now().isoformat()).replace('T', ' '),
                    'time_ago': 'scenario',
                    'priority': email.get('urgency', 'medium'),
                    'type': email.get('email_type', 'scenario'),
                    'email_type': email.get('scenario_type', 'business'),
                    'source': 'scenario_emails',
                    'routing': {
                        'category': email.get('scenario_type', 'business'),
                        'confidence': 0.98,
                        'destination': 'business_agent'
                    },
                    'attachments': [],
                    'scenario_info': {
                        'scenario_type': email.get('scenario_type'),
                        'business_impact': email.get('business_impact', {}),
                        'sla_violation': email.get('sla_violation', False),
                        'customer_info': email.get('customer_info', {})
                    }
                }
                all_emails.append(converted_email)
        except Exception as e:
            logger.warning(f"Error loading scenario emails: {e}")

        # Sort all emails by timestamp (most recent first)
        # Convert timestamps to string format for consistent sorting
        for email in all_emails:
            if 'timestamp' in email and hasattr(email['timestamp'], 'strftime'):
                email['timestamp'] = email['timestamp'].strftime('%Y-%m-%d %H:%M:%S+02:00')

        all_emails.sort(key=lambda x: str(x.get('timestamp', '')), reverse=True)

        # Limit final result
        final_emails = all_emails[:limit]

        return jsonify({
            'success': True,
            'emails': final_emails,
            'total': len(final_emails),
            'sources': {
                'real_mailbox': len([e for e in final_emails if e.get('source') == 'real_mailbox']),
                'timewarp_simulation': len([e for e in final_emails if e.get('source') == 'timewarp_simulation']),
                'enhanced_simulation': len([e for e in final_emails if e.get('source') == 'enhanced_simulation']),
                'scenario_emails': len([e for e in final_emails if e.get('source') == 'scenario_emails'])
            }
        })

    except Exception as e:
        logger.error(f"Error in combined email endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'emails': []
        }), 500

if __name__ == '__main__':
    # Start background update thread
    socketio.start_background_task(background_updates)

    # Run the dashboard
    port = int(os.environ.get('FLASK_PORT', os.environ.get('PORT', 80)))
    logger.info(f"🌐 Starting Happy Buttons Dashboard on http://localhost:{port}")
    logger.info(f"🚀 Happy Buttons Release 2.2 - Enhanced Business Simulation")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)