"""
InfoAgent - Email Triage and General Inquiries
The first point of contact for info@ mailbox processing
"""

import asyncio
import re
from typing import Dict, List, Any, Optional
from ..business.base_agent_v2 import BaseAgent, AgentTask, TaskPriority
from ...services.order.state_machine import OrderItem, OrderStateMachine
from ...parsers.pdf.pdf_parser import PDFParser

class InfoAgent(BaseAgent):
    """
    InfoAgent handles general inquiries and email triage
    Primary responsibilities:
    - Email classification and initial processing
    - Routing decisions to specialized agents
    - Auto-reply generation with royal courtesy
    - Order extraction from emails and PDFs
    """

    def __init__(self):
        super().__init__("InfoAgent")
        self.pdf_parser = PDFParser()
        self.order_machine = OrderStateMachine()

        # Classification keywords from config
        self.classification_rules = self._load_classification_rules()

        # Setup event handlers
        self.register_event_handler('email_received', self._handle_email_received)
        self.register_event_handler('pdf_attachment', self._handle_pdf_attachment)

    def _load_classification_rules(self) -> Dict[str, List[str]]:
        """Load email classification rules from config"""
        rules = self.config.get('rules', {}).get('priority', [])

        classification = {
            'order': ['order', 'purchase', 'buy', 'quote', 'price', 'catalog'],
            'complaint': ['complaint', 'problem', 'issue', 'defect', 'broken', 'faulty'],
            'support': ['help', 'support', 'assistance', 'question', 'how to'],
            'billing': ['invoice', 'payment', 'billing', 'receipt', 'account'],
            'urgent': ['urgent', 'asap', 'emergency', 'critical', 'immediately'],
            'vip': ['royal', 'majesty', 'highness', 'excellency', 'vip'],
            'oem': []  # Will be populated from config OEM domains
        }

        # Add OEM domains from config
        oem_customers = self.config.get('oem_customers', [])
        classification['oem'] = [domain.split('@')[-1] if '@' in domain else domain
                               for domain in oem_customers]

        return classification

    def get_capabilities(self) -> List[str]:
        """Return InfoAgent capabilities"""
        return [
            'email_triage',
            'general_inquiries',
            'order_extraction',
            'customer_classification',
            'routing_decisions',
            'auto_reply_generation',
            'pdf_processing',
            'priority_assessment',
            'escalation_detection'
        ]

    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process InfoAgent tasks"""
        task_type = task.type

        if task_type == 'process_email':
            return await self._process_email(task.data)
        elif task_type == 'classify_email':
            return await self._classify_email(task.data)
        elif task_type == 'extract_order':
            return await self._extract_order_from_email(task.data)
        elif task_type == 'generate_reply':
            return await self._generate_auto_reply(task.data)
        elif task_type == 'route_email':
            return await self._route_email(task.data)
        else:
            return {'error': f'Unknown task type: {task_type}'}

    async def _process_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main email processing workflow"""
        try:
            email_id = email_data.get('id')
            self.logger.info(f"Processing email {email_id}")

            # Step 1: Classify the email
            classification = await self._classify_email(email_data)

            # Step 2: Check for attachments and extract orders
            order_data = None
            if email_data.get('attachments'):
                order_data = await self._process_attachments(email_data)

            # Step 3: Determine routing
            routing_decision = await self._determine_routing(email_data, classification)

            # Step 4: Generate auto-reply
            reply_data = await self._generate_auto_reply(email_data, classification)

            # Step 5: Create order if applicable
            order_id = None
            if order_data and classification.get('category') == 'order':
                order_id = await self._create_order_from_data(email_data, order_data)

            # Step 6: Emit events for other systems
            await self._emit_processing_events(email_data, classification, routing_decision, order_id)

            return {
                'status': 'processed',
                'email_id': email_id,
                'classification': classification,
                'routing': routing_decision,
                'auto_reply': reply_data,
                'order_created': order_id,
                'processing_time': self._get_processing_time()
            }

        except Exception as e:
            self.logger.error(f"Error processing email: {e}")
            return {'error': str(e)}

    async def _classify_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify email content and determine priority"""
        from_addr = email_data.get('from', '').lower()
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()

        content = f"{subject} {body}"

        # Initialize classification
        classification = {
            'category': 'general',
            'priority': 3,
            'confidence': 0.5,
            'keywords_found': [],
            'is_oem': False,
            'is_urgent': False,
            'is_vip': False
        }

        # Check OEM customer
        domain = from_addr.split('@')[-1] if '@' in from_addr else ''
        if domain in self.classification_rules.get('oem', []):
            classification['is_oem'] = True
            classification['priority'] = 2

        # Check for VIP keywords
        vip_keywords = self.classification_rules.get('vip', [])
        for keyword in vip_keywords:
            if keyword in content:
                classification['is_vip'] = True
                classification['priority'] = 1
                classification['keywords_found'].append(keyword)
                break

        # Check for urgent keywords
        urgent_keywords = self.classification_rules.get('urgent', [])
        for keyword in urgent_keywords:
            if keyword in content:
                classification['is_urgent'] = True
                classification['priority'] = min(classification['priority'], 1)
                classification['keywords_found'].append(keyword)

        # Determine category
        max_score = 0
        detected_category = 'general'

        for category, keywords in self.classification_rules.items():
            if category in ['oem', 'urgent', 'vip']:
                continue

            score = sum(1 for keyword in keywords if keyword in content)
            if score > max_score:
                max_score = score
                detected_category = category
                classification['keywords_found'].extend([k for k in keywords if k in content])

        if max_score > 0:
            classification['category'] = detected_category
            classification['confidence'] = min(0.9, 0.3 + (max_score * 0.2))

        self.logger.info(f"Email classified as {classification['category']} "
                        f"(priority {classification['priority']}, confidence {classification['confidence']:.2f})")

        return classification

    async def _process_attachments(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process PDF attachments for order extraction"""
        attachments = email_data.get('attachments', [])

        for attachment in attachments:
            if attachment.get('content_type', '').startswith('application/pdf'):
                try:
                    # In real implementation, would parse actual PDF file
                    # For now, simulate PDF parsing
                    self.logger.info(f"Processing PDF attachment: {attachment.get('filename')}")

                    # Simulate order data extraction
                    order_data = {
                        'order_number': f"ORD_{int(asyncio.get_event_loop().time())}",
                        'customer_name': email_data.get('from', '').split('@')[0],
                        'customer_email': email_data.get('from', ''),
                        'items': [
                            {
                                'sku': 'BTN-001',
                                'name': 'Standard Button',
                                'quantity': 100,
                                'unit_price': 2.50,
                                'total_price': 250.00
                            }
                        ],
                        'total': 250.00,
                        'source': 'pdf_attachment'
                    }

                    return order_data

                except Exception as e:
                    self.logger.error(f"Error processing PDF attachment: {e}")

        return None

    async def _determine_routing(self, email_data: Dict[str, Any],
                                classification: Dict[str, Any]) -> Dict[str, Any]:
        """Determine where to route the email"""
        category = classification.get('category')
        priority = classification.get('priority')
        is_oem = classification.get('is_oem')

        # Default routing rules
        routing = {
            'primary_agent': 'InfoAgent',
            'escalate_to': None,
            'cc_agents': [],
            'sla_hours': 24,
            'reason': 'Default routing'
        }

        # Category-based routing
        if category == 'order':
            routing['primary_agent'] = 'SalesAgent'
            routing['sla_hours'] = 12
            routing['reason'] = 'Order processing'

        elif category == 'complaint':
            routing['primary_agent'] = 'QualityAgent'
            routing['escalate_to'] = 'MgmtAgent' if priority == 1 else None
            routing['sla_hours'] = 4
            routing['reason'] = 'Quality issue'

        elif category == 'support':
            routing['primary_agent'] = 'SupportAgent'
            routing['sla_hours'] = 8
            routing['reason'] = 'Customer support'

        elif category == 'billing':
            routing['primary_agent'] = 'FinanceAgent'
            routing['sla_hours'] = 12
            routing['reason'] = 'Billing inquiry'

        # Priority overrides
        if is_oem:
            routing['sla_hours'] = min(routing['sla_hours'], 4)
            routing['cc_agents'].append('OEMAgent')

        if priority == 1:  # Critical
            routing['sla_hours'] = min(routing['sla_hours'], 2)
            routing['escalate_to'] = 'MgmtAgent'

        return routing

    async def _generate_auto_reply(self, email_data: Dict[str, Any],
                                  classification: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate royal courtesy auto-reply"""
        customer_name = email_data.get('from', '').split('@')[0].title()
        subject = email_data.get('subject', '')
        category = classification.get('category', 'general') if classification else 'general'

        # Royal courtesy templates based on category
        templates = {
            'order': f"""Dear {customer_name},

Thank you for your esteemed order inquiry. We have received your request and are delighted to assist you with your button requirements.

Your inquiry has been forwarded to our Sales department for immediate attention. You may expect a detailed quotation within 12 hours.

Should you require any immediate assistance, please do not hesitate to contact us.

With our sincerest regards,
Happy Buttons GmbH Customer Service""",

            'complaint': f"""Dear {customer_name},

We sincerely apologize for any inconvenience you may have experienced. Your satisfaction is of utmost importance to us.

Your concern has been escalated to our Quality department for immediate investigation. A dedicated specialist will contact you within 4 hours to resolve this matter.

We deeply value your business and trust.

Most respectfully,
Happy Buttons GmbH Quality Assurance""",

            'general': f"""Dear {customer_name},

Thank you for contacting Happy Buttons GmbH. We are honored by your inquiry and will ensure it receives our prompt attention.

Your message has been received and will be processed according to our service standards. We shall respond within 24 hours.

We remain at your distinguished service.

Yours faithfully,
Happy Buttons GmbH Customer Relations"""
        }

        reply_template = templates.get(category, templates['general'])

        return {
            'template_used': f'{category}_auto_reply',
            'subject': f"Re: {subject}" if subject else "Your Inquiry - Happy Buttons GmbH",
            'body': reply_template,
            'courtesy_score': 85,  # Royal courtesy scoring
            'send_immediately': classification.get('is_urgent', False) if classification else False
        }

    async def _create_order_from_data(self, email_data: Dict[str, Any],
                                     order_data: Dict[str, Any]) -> str:
        """Create order in the system"""
        try:
            items = []
            for item_data in order_data.get('items', []):
                item = OrderItem(
                    sku=item_data.get('sku'),
                    name=item_data.get('name'),
                    quantity=item_data.get('quantity'),
                    unit_price=item_data.get('unit_price'),
                    total_price=item_data.get('total_price')
                )
                items.append(item)

            # Determine priority based on classification
            priority = 3  # Default
            if order_data.get('total', 0) > 10000:
                priority = 2  # High value

            order = self.order_machine.create_order(
                customer_email=order_data.get('customer_email'),
                customer_name=order_data.get('customer_name'),
                items=items,
                priority=priority,
                metadata={
                    'source_email_id': email_data.get('id'),
                    'extracted_by': 'InfoAgent',
                    'source_type': order_data.get('source', 'email')
                }
            )

            self.logger.info(f"Created order {order.id} from email {email_data.get('id')}")
            return order.id

        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            return None

    async def _emit_processing_events(self, email_data: Dict[str, Any],
                                    classification: Dict[str, Any],
                                    routing: Dict[str, Any],
                                    order_id: Optional[str]):
        """Emit events for dashboard and other systems"""
        # Email processed event
        await self.emit_event('email_processed', {
            'email_id': email_data.get('id'),
            'classification': classification,
            'routing': routing,
            'order_created': order_id,
            'processing_agent': self.agent_id
        })

        # If order created, emit order event
        if order_id:
            await self.emit_event('order_created', {
                'order_id': order_id,
                'customer_email': email_data.get('from'),
                'source': 'email_processing',
                'agent': self.agent_id
            })

        # If requires escalation, emit escalation event
        if routing.get('escalate_to'):
            await self.emit_event('escalation_required', {
                'email_id': email_data.get('id'),
                'escalate_to': routing['escalate_to'],
                'reason': classification.get('category'),
                'priority': classification.get('priority')
            })

    def _get_processing_time(self) -> float:
        """Get current task processing time"""
        if self.current_task and self.current_task.assigned_at:
            import time
            return time.time() - self.current_task.assigned_at
        return 0.0

    # Event handlers
    async def _handle_email_received(self, event):
        """Handle incoming email events"""
        email_data = event.data

        # Create task to process the email
        task = AgentTask(
            id=f"email_{email_data.get('id')}",
            type='process_email',
            priority=TaskPriority.NORMAL,
            data=email_data
        )

        await self.assign_task(task)

    async def _handle_pdf_attachment(self, event):
        """Handle PDF attachment processing events"""
        attachment_data = event.data

        # Create task to process the PDF
        task = AgentTask(
            id=f"pdf_{attachment_data.get('email_id')}_{attachment_data.get('filename')}",
            type='extract_order',
            priority=TaskPriority.HIGH,
            data=attachment_data
        )

        await self.assign_task(task)

# Demo usage
if __name__ == "__main__":
    import asyncio
    import logging

    logging.basicConfig(level=logging.INFO)

    async def demo_info_agent():
        agent = InfoAgent()

        # Demo email processing
        demo_email = {
            'id': 'demo_001',
            'from': 'customer@oem1.com',
            'to': 'info@h-bu.de',
            'subject': 'Urgent Order Request - 10000 Premium Buttons',
            'body': 'Dear Happy Buttons, we need an urgent order for 10000 premium buttons. Please quote ASAP.',
            'attachments': [
                {'filename': 'order.pdf', 'content_type': 'application/pdf'}
            ]
        }

        task = AgentTask(
            id="demo_task",
            type="process_email",
            priority=TaskPriority.NORMAL,
            data=demo_email
        )

        await agent.assign_task(task)
        result = await agent.process_next_task()

        print("InfoAgent Demo Result:")
        print(f"Status: {agent.get_status()}")
        print(f"Processing Result: {result}")

        await agent.shutdown()

    asyncio.run(demo_info_agent())