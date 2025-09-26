"""
Test Suite for Happy Buttons Email System
Tests email parsing, routing, agents, and templates
"""

import pytest
import asyncio
import email
from datetime import datetime
from pathlib import Path

# Import our modules
import sys
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from email_processing.parser import EmailParser, ParsedEmail, create_test_email
from email_processing.router import EmailRouter, RoutingDecision
from agents.base_agent import BaseAgent, AgentResponse, AgentTask
from agents.business_agents import (
    InfoAgent, OrdersAgent, OEMAgent, SupplierAgent,
    QualityAgent, ManagementAgent, create_business_agents
)
from utils.templates import RoyalCourtesyTemplates, create_template_context


class TestEmailParser:
    """Test the email parsing functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.parser = EmailParser()

    def test_parser_initialization(self):
        """Test parser initializes correctly"""
        assert self.parser is not None
        assert len(self.parser.keywords) > 0
        assert 'order' in self.parser.keywords
        assert len(self.parser.oem_domains) > 0

    def test_create_test_email(self):
        """Test creating test emails"""
        email = create_test_email(
            sender='John Smith <john@oem1.com>',
            subject='Urgent Order Request',
            body='We need 10,000 red buttons urgently. Order value $5,000.'
        )

        assert email.sender.email == 'john@oem1.com'
        assert email.sender.name == 'John Smith'
        assert email.sender.domain == 'oem1.com'
        assert 'urgent' in email.subject.lower()
        assert email.metadata.is_oem == True

    def test_oem_detection(self):
        """Test OEM customer detection"""
        # OEM customer
        oem_email = create_test_email(
            sender='buyer@oem1.com',
            subject='Order Request',
            body='Please quote for buttons.'
        )
        assert oem_email.metadata.is_oem == True

        # Regular customer
        regular_email = create_test_email(
            sender='customer@gmail.com',
            subject='Order Request',
            body='Please quote for buttons.'
        )
        assert regular_email.metadata.is_oem == False

    def test_urgent_detection(self):
        """Test urgent email detection"""
        urgent_email = create_test_email(
            sender='customer@test.com',
            subject='URGENT: Need buttons ASAP',
            body='This is an emergency order.'
        )
        assert urgent_email.metadata.is_urgent == True

        normal_email = create_test_email(
            sender='customer@test.com',
            subject='Regular order',
            body='Standard order request.'
        )
        assert normal_email.metadata.is_urgent == False

    def test_category_detection(self):
        """Test email categorization"""
        # Order category
        order_email = create_test_email(
            sender='customer@test.com',
            subject='Purchase Order',
            body='We want to order 1000 buttons.'
        )
        assert order_email.metadata.category == 'order'

        # Complaint category
        complaint_email = create_test_email(
            sender='customer@test.com',
            subject='Complaint about quality',
            body='The buttons we received are defective.'
        )
        assert complaint_email.metadata.category == 'complaint'

        # Supplier category
        supplier_email = create_test_email(
            sender='supplier@materials.com',
            subject='Delivery confirmation',
            body='Your shipment has been delivered.'
        )
        assert supplier_email.metadata.category == 'supplier'

    def test_priority_determination(self):
        """Test priority level determination"""
        # High priority: OEM + urgent
        high_priority_email = create_test_email(
            sender='urgent@oem1.com',
            subject='URGENT ORDER',
            body='Emergency order for $15,000'
        )
        assert high_priority_email.metadata.priority in ['high', 'critical']

        # Low priority: regular customer, no urgency
        low_priority_email = create_test_email(
            sender='customer@email.com',
            subject='Question',
            body='Just wondering about your products.'
        )
        assert low_priority_email.metadata.priority in ['low', 'medium']


class TestEmailRouter:
    """Test the email routing functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.router = EmailRouter()

    @pytest.mark.asyncio
    async def test_router_initialization(self):
        """Test router initializes correctly"""
        assert self.router is not None
        assert len(self.router.routing_rules) > 0
        assert 'order_pdf' in self.router.routing_rules
        assert 'default_support' in self.router.routing_rules

    @pytest.mark.asyncio
    async def test_order_routing(self):
        """Test order email routing"""
        order_email = create_test_email(
            sender='customer@test.com',
            subject='Order Request',
            body='I want to order buttons.',
            attachments=[{
                'filename': 'order.pdf',
                'content': b'PDF order content'
            }]
        )

        decision = await self.router.route_email(order_email)

        assert decision.destination == 'orders@h-bu.de'
        assert decision.auto_reply_template is not None
        assert 'order' in decision.reasoning[0].lower()

    @pytest.mark.asyncio
    async def test_oem_priority_routing(self):
        """Test OEM customer priority routing"""
        oem_email = create_test_email(
            sender='buyer@oem1.com',
            subject='Partnership inquiry',
            body='We are interested in a large volume order.'
        )

        decision = await self.router.route_email(oem_email)

        assert decision.destination == 'oem1@h-bu.de'
        assert decision.sla_hours <= 4  # OEM priority SLA
        assert any('oem' in reason.lower() for reason in decision.reasoning)

    @pytest.mark.asyncio
    async def test_complaint_routing(self):
        """Test complaint routing"""
        complaint_email = create_test_email(
            sender='unhappy@customer.com',
            subject='Complaint about product quality',
            body='The buttons are defective and wrong color.'
        )

        decision = await self.router.route_email(complaint_email)

        assert decision.destination == 'quality@h-bu.de'
        assert decision.requires_human_review == True
        assert 'complaint' in decision.auto_reply_template.lower()

    @pytest.mark.asyncio
    async def test_escalation_routing(self):
        """Test escalation scenarios"""
        legal_email = create_test_email(
            sender='lawyer@lawfirm.com',
            subject='Legal notice',
            body='This is a legal notice regarding your products.'
        )

        decision = await self.router.route_email(legal_email)

        assert decision.destination == 'management@h-bu.de'
        assert decision.requires_human_review == True
        assert decision.escalation_level > 0

    @pytest.mark.asyncio
    async def test_default_routing(self):
        """Test default routing for unclear emails"""
        general_email = create_test_email(
            sender='someone@somewhere.com',
            subject='Hello',
            body='Just saying hello.'
        )

        decision = await self.router.route_email(general_email)

        assert decision.destination == 'support@h-bu.de'
        assert decision.auto_reply_template == 'generic_ack'


class TestBusinessAgents:
    """Test business unit agents"""

    def setup_method(self):
        """Setup for each test"""
        self.agents = create_business_agents()

    def test_agents_creation(self):
        """Test all agents are created correctly"""
        expected_agents = ['info', 'orders', 'oem', 'supplier', 'quality', 'management']

        for agent_name in expected_agents:
            assert agent_name in self.agents
            agent = self.agents[agent_name]
            assert isinstance(agent, BaseAgent)
            assert agent.agent_id is not None
            assert agent.agent_type is not None

    def test_agent_capabilities(self):
        """Test agent capabilities are properly defined"""
        for agent_name, agent in self.agents.items():
            capabilities = agent.get_agent_capabilities()
            assert isinstance(capabilities, dict)
            assert len(capabilities) > 0

    def test_info_agent(self):
        """Test Info Agent specifically"""
        info_agent = self.agents['info']
        assert info_agent.agent_type == 'info_agent'

        # Test validation - info agent should handle all emails
        test_email = create_test_email(
            sender='anyone@anywhere.com',
            subject='Any subject',
            body='Any content'
        )
        assert info_agent.validate_email_for_agent(test_email) == True

    def test_orders_agent(self):
        """Test Orders Agent specifically"""
        orders_agent = self.agents['orders']
        assert orders_agent.agent_type == 'orders_agent'

        # Test validation - should handle order emails
        order_email = create_test_email(
            sender='customer@test.com',
            subject='Order request',
            body='I want to order buttons'
        )
        assert orders_agent.validate_email_for_agent(order_email) == True

        # Should not handle non-order emails
        random_email = create_test_email(
            sender='someone@test.com',
            subject='Random question',
            body='Just a random question'
        )
        assert orders_agent.validate_email_for_agent(random_email) == False

    def test_oem_agent(self):
        """Test OEM Agent specifically"""
        oem_agent = self.agents['oem']
        assert oem_agent.agent_type == 'oem_agent'

        # Test validation - should handle OEM emails
        oem_email = create_test_email(
            sender='buyer@oem1.com',
            subject='Partnership inquiry',
            body='Volume order request'
        )
        assert oem_agent.validate_email_for_agent(oem_email) == True

        # Should not handle non-OEM emails
        regular_email = create_test_email(
            sender='customer@gmail.com',
            subject='Regular order',
            body='Small order'
        )
        assert oem_agent.validate_email_for_agent(regular_email) == False

    @pytest.mark.asyncio
    async def test_agent_processing_flow(self):
        """Test complete agent processing flow"""
        # Create test email and routing decision
        test_email = create_test_email(
            sender='customer@test.com',
            subject='Order request',
            body='We need 1000 buttons for $2000'
        )

        from datetime import datetime

        routing_decision = RoutingDecision(
            email_id=test_email.id,
            timestamp=datetime.now(),
            destination='orders@h-bu.de',
            priority='medium',
            auto_reply_template='order_received'
        )

        # Test info agent processing
        info_agent = self.agents['info']
        await info_agent.start()

        response = await info_agent.process_email(test_email, routing_decision)

        assert isinstance(response, AgentResponse)
        assert response.status == 'success'
        assert response.agent_id == info_agent.agent_id
        assert response.auto_reply is not None

        await info_agent.stop()


class TestRoyalCourtesyTemplates:
    """Test the Royal Courtesy Templates system"""

    def setup_method(self):
        """Setup for each test"""
        self.templates = RoyalCourtesyTemplates()

    def test_templates_initialization(self):
        """Test templates system initializes correctly"""
        assert self.templates is not None
        available_templates = self.templates.get_available_templates()
        assert len(available_templates) > 0
        assert 'order_received' in available_templates
        assert 'generic_ack' in available_templates

    def test_template_generation(self):
        """Test template generation"""
        context = create_template_context(
            customer_name='Mr. Smith',
            order_number='ORD-123'
        )

        response = self.templates.generate_response('order_received', context)

        assert response['subject'] is not None
        assert response['body'] is not None
        assert 'Mr. Smith' in response['body']
        assert 'ORD-123' in response['subject']
        assert response['template_used'] == 'order_received'
        assert response['style'] == 'royal_courtesy'

    def test_royal_courtesy_validation(self):
        """Test royal courtesy validation"""
        # Good royal courtesy content
        good_content = """Dear Esteemed Customer,

We are most delighted to receive your gracious order and shall endeavour to process it with the utmost care.

With the greatest pleasure,
Happy Buttons Team"""

        validation = self.templates.validate_royal_courtesy(good_content)
        assert validation['is_valid'] == True
        assert validation['score'] > 60

        # Poor courtesy content
        poor_content = """Hi there!

Thanks for your order! We'll get right on it!!!

Cheers,
Team"""

        validation = self.templates.validate_royal_courtesy(poor_content)
        assert validation['is_valid'] == False
        assert len(validation['issues']) > 0

    def test_template_context_handling(self):
        """Test template context variable handling"""
        context = {
            'customer_name': 'Ms. Johnson',
            'urgent_hours': '6',
            'order_number': 'ORD-456'
        }

        response = self.templates.generate_response('expedite_ack', context)

        assert 'Ms. Johnson' in response['body']
        assert '6 hours' in response['body'] or '6' in response['body']
        assert response['validation']['is_valid'] == True

    def test_error_handling(self):
        """Test error handling in template system"""
        # Test with non-existent template
        response = self.templates.generate_response('non_existent_template')

        assert 'error' in response
        assert response['template_used'] == 'error_fallback'
        assert response['validation']['is_valid'] == True

    def test_bulk_validation(self):
        """Test bulk template validation"""
        results = self.templates.bulk_validate_templates()

        assert isinstance(results, dict)
        assert len(results) > 0

        for template_name, validation in results.items():
            assert 'is_valid' in validation
            assert 'score' in validation
            assert isinstance(validation['score'], (int, float))

    def test_template_stats(self):
        """Test template statistics"""
        stats = self.templates.get_template_stats()

        assert 'total_templates' in stats
        assert 'template_names' in stats
        assert 'average_length' in stats
        assert stats['total_templates'] > 0


class TestIntegration:
    """Integration tests for the complete system"""

    def setup_method(self):
        """Setup for integration tests"""
        self.parser = EmailParser()
        self.router = EmailRouter()
        self.templates = RoyalCourtesyTemplates()
        self.agents = create_business_agents()

    @pytest.mark.asyncio
    async def test_complete_email_flow(self):
        """Test complete email processing flow"""
        # Create test email
        test_email = create_test_email(
            sender='John Doe <john@oem1.com>',
            subject='Urgent Order - High Priority',
            body='We need 5000 red buttons urgently. Budget is $10,000. Please expedite.',
            attachments=[{
                'filename': 'specifications.pdf',
                'content': b'PDF specifications content'
            }]
        )

        # Step 1: Parse email
        assert test_email.metadata.is_oem == True
        assert test_email.metadata.is_urgent == True
        assert test_email.metadata.priority in ['high', 'critical']

        # Step 2: Route email
        routing_decision = await self.router.route_email(test_email)

        assert routing_decision.destination in ['orders@h-bu.de', 'oem1@h-bu.de']
        assert routing_decision.sla_hours <= 4  # OEM priority
        assert routing_decision.auto_reply_template is not None

        # Step 3: Generate template response
        template_context = create_template_context(
            customer_name='John Doe',
            urgent_hours='4'
        )

        template_response = self.templates.generate_response(
            routing_decision.auto_reply_template,
            template_context
        )

        assert template_response['validation']['is_valid'] == True
        assert 'John Doe' in template_response['body']

        # Step 4: Agent processing
        appropriate_agent = None
        if routing_decision.destination == 'oem1@h-bu.de':
            appropriate_agent = self.agents['oem']
        elif routing_decision.destination == 'orders@h-bu.de':
            appropriate_agent = self.agents['orders']

        if appropriate_agent:
            await appropriate_agent.start()
            agent_response = await appropriate_agent.process_email(test_email, routing_decision)

            assert agent_response.status == 'success'
            assert agent_response.auto_reply is not None

            await appropriate_agent.stop()

        print(f"✅ Complete flow test passed:")
        print(f"   Email ID: {test_email.id}")
        print(f"   Category: {test_email.metadata.category}")
        print(f"   Priority: {test_email.metadata.priority}")
        print(f"   Routed to: {routing_decision.destination}")
        print(f"   SLA Hours: {routing_decision.sla_hours}")
        print(f"   Template: {routing_decision.auto_reply_template}")

    @pytest.mark.asyncio
    async def test_multiple_email_scenarios(self):
        """Test multiple email scenarios"""
        scenarios = [
            {
                'name': 'Regular Order',
                'sender': 'customer@email.com',
                'subject': 'Button Order',
                'body': 'I need 100 blue buttons.',
                'expected_destination': 'orders@h-bu.de'
            },
            {
                'name': 'OEM Priority',
                'sender': 'buyer@oem1.com',
                'subject': 'Large Volume Order',
                'body': 'Need quote for 50,000 buttons.',
                'expected_destination': 'oem1@h-bu.de'
            },
            {
                'name': 'Quality Complaint',
                'sender': 'unhappy@customer.com',
                'subject': 'Defective Products',
                'body': 'The buttons are broken and wrong color.',
                'expected_destination': 'quality@h-bu.de'
            },
            {
                'name': 'Supplier Communication',
                'sender': 'supplier@materials.com',
                'subject': 'Delivery Update',
                'body': 'Your raw materials have been shipped.',
                'expected_destination': 'supplier@h-bu.de'
            }
        ]

        for scenario in scenarios:
            test_email = create_test_email(
                sender=scenario['sender'],
                subject=scenario['subject'],
                body=scenario['body']
            )

            routing_decision = await self.router.route_email(test_email)

            assert routing_decision.destination == scenario['expected_destination'], \
                f"Scenario '{scenario['name']}' failed: expected {scenario['expected_destination']}, got {routing_decision.destination}"

            print(f"✅ Scenario '{scenario['name']}' passed")


# Performance and stats tests
class TestSystemStats:
    """Test system statistics and performance"""

    def setup_method(self):
        """Setup for stats tests"""
        self.parser = EmailParser()
        self.router = EmailRouter()
        self.templates = RoyalCourtesyTemplates()

    def test_parser_stats(self):
        """Test parser statistics"""
        stats = self.parser.get_parsing_stats()

        assert 'supported_types' in stats
        assert 'keyword_categories' in stats
        assert 'total_keywords' in stats
        assert isinstance(stats['total_keywords'], int)
        assert stats['total_keywords'] > 0

    def test_router_stats(self):
        """Test router statistics"""
        stats = self.router.get_routing_stats()

        assert 'available_destinations' in stats
        assert isinstance(stats['available_destinations'], list)
        assert len(stats['available_destinations']) > 0

    def test_template_stats(self):
        """Test template statistics"""
        stats = self.templates.get_template_stats()

        assert 'total_templates' in stats
        assert 'average_length' in stats
        assert stats['total_templates'] > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
