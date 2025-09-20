#!/usr/bin/env python3
"""
Happy Buttons Agentic Simulation System - Main Application
Python implementation with Claude Flow integration
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime

from email.parser import EmailParser, create_test_email
from email.router import EmailRouter
from agents.business_agents import create_business_agents
from agents.base_agent import AgentCoordinator
from utils.templates import RoyalCourtesyTemplates

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HappyButtonsEmailSystem:
    """
    Main Happy Buttons Email Processing System
    Coordinates parsing, routing, agents, and templates
    """

    def __init__(self):
        self.parser = EmailParser()
        self.router = EmailRouter()
        self.templates = RoyalCourtesyTemplates()
        self.coordinator = AgentCoordinator()
        self.agents = {}

        # System metrics
        self.metrics = {
            'emails_processed': 0,
            'auto_replies_sent': 0,
            'escalations': 0,
            'system_start_time': datetime.now()
        }

    async def initialize(self):
        """Initialize the email system"""
        logger.info("🚀 Initializing Happy Buttons Email System...")

        # Create and register business agents
        self.agents = create_business_agents()

        for agent_name, agent in self.agents.items():
            await self.coordinator.register_agent(agent)

        logger.info(f"✅ Initialized {len(self.agents)} business agents")
        logger.info("🔄 System ready for email processing")

    async def process_email(self, raw_email_data):
        """
        Process a single email through the complete pipeline

        Args:
            raw_email_data: Raw email data or test email

        Returns:
            Dict: Processing results
        """
        try:
            start_time = datetime.now()

            # Step 1: Parse email
            if isinstance(raw_email_data, str):
                # For demo, create test email
                parsed_email = create_test_email(
                    sender=raw_email_data,
                    subject="Demo Email",
                    body="This is a demonstration email."
                )
            else:
                parsed_email = await self.parser.parse_email(raw_email_data)

            logger.info(f"📧 Processing email {parsed_email.id} from {parsed_email.sender.email}")

            # Step 2: Route email
            routing_decision = await self.router.route_email(parsed_email)

            logger.info(f"📍 Routed to {routing_decision.destination} (Priority: {routing_decision.priority})")

            # Step 3: Process with appropriate agent
            agent_response = await self.coordinator.route_to_agent(parsed_email, routing_decision)

            # Step 4: Generate auto-reply if needed
            auto_reply = None
            if routing_decision.auto_reply_template and not routing_decision.requires_human_review:
                context = {
                    'customer_name': parsed_email.sender.name or 'Valued Customer',
                    'order_number': None,  # Could extract from content
                    'urgent_hours': '4' if parsed_email.metadata.is_urgent else '12'
                }

                reply_response = self.templates.generate_response(
                    routing_decision.auto_reply_template,
                    context
                )

                auto_reply = reply_response
                self.metrics['auto_replies_sent'] += 1

            # Update metrics
            self.metrics['emails_processed'] += 1
            if routing_decision.escalation_level > 0:
                self.metrics['escalations'] += 1

            processing_time = (datetime.now() - start_time).total_seconds()

            return {
                'email_id': parsed_email.id,
                'processing_time_seconds': processing_time,
                'routing': {
                    'destination': routing_decision.destination,
                    'priority': routing_decision.priority,
                    'sla_hours': routing_decision.sla_hours,
                    'requires_human_review': routing_decision.requires_human_review,
                    'reasoning': routing_decision.reasoning
                },
                'metadata': {
                    'category': parsed_email.metadata.category,
                    'is_oem': parsed_email.metadata.is_oem,
                    'is_urgent': parsed_email.metadata.is_urgent,
                    'confidence': parsed_email.metadata.confidence_score
                },
                'agent_response': agent_response.__dict__ if agent_response else None,
                'auto_reply': auto_reply,
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"❌ Email processing failed: {str(e)}")
            return {
                'email_id': getattr(parsed_email, 'id', 'unknown'),
                'status': 'error',
                'error': str(e)
            }

    async def demo_simulation(self):
        """Run a demonstration of the email system"""
        logger.info("🎭 Running Happy Buttons Email System Demo...")

        # Demo email scenarios
        demo_emails = [
            {
                'sender': 'John Smith <john@oem1.com>',
                'subject': 'Urgent Order Request - High Priority',
                'body': 'We need 5000 red buttons urgently. Budget is $10,000. Please expedite.',
                'scenario': 'OEM Priority Customer'
            },
            {
                'sender': 'customer@email.com',
                'subject': 'Button Order',
                'body': 'I would like to order 100 blue buttons for my project.',
                'scenario': 'Regular Order'
            },
            {
                'sender': 'unhappy@customer.com',
                'subject': 'Complaint about product quality',
                'body': 'The buttons I received are defective and wrong color.',
                'scenario': 'Quality Complaint'
            },
            {
                'sender': 'supplier@materials.com',
                'subject': 'Delivery confirmation',
                'body': 'Your raw materials shipment has been delivered.',
                'scenario': 'Supplier Communication'
            }
        ]

        results = []

        for demo in demo_emails:
            logger.info(f"\n🔄 Processing: {demo['scenario']}")

            test_email = create_test_email(
                sender=demo['sender'],
                subject=demo['subject'],
                body=demo['body']
            )

            result = await self.process_email(test_email)
            result['scenario'] = demo['scenario']
            results.append(result)

            # Print summary
            if result['status'] == 'success':
                logger.info(f"✅ {demo['scenario']} → {result['routing']['destination']}")
                logger.info(f"   Priority: {result['routing']['priority']}, SLA: {result['routing']['sla_hours']}h")
                if result['auto_reply']:
                    logger.info(f"   Auto-reply: {result['auto_reply']['template_used']}")
            else:
                logger.error(f"❌ {demo['scenario']} failed: {result['error']}")

        return results

    def get_system_status(self):
        """Get current system status"""
        agent_status = self.coordinator.get_system_status()
        uptime = (datetime.now() - self.metrics['system_start_time']).total_seconds()

        return {
            'system_metrics': self.metrics,
            'uptime_seconds': uptime,
            'agents': agent_status,
            'parser_stats': self.parser.get_parsing_stats(),
            'router_stats': self.router.get_routing_stats(),
            'template_stats': self.templates.get_template_stats()
        }

    async def shutdown(self):
        """Shutdown the email system"""
        logger.info("🛑 Shutting down Happy Buttons Email System...")

        for agent_id in list(self.coordinator.agents.keys()):
            await self.coordinator.unregister_agent(agent_id)

        logger.info("✅ System shutdown complete")


async def main():
    """Main application entry point"""
    system = HappyButtonsEmailSystem()

    try:
        # Initialize system
        await system.initialize()

        # Run demonstration
        demo_results = await system.demo_simulation()

        # Print final statistics
        logger.info(f"\n📊 DEMO RESULTS SUMMARY")
        logger.info(f"=" * 50)

        for result in demo_results:
            if result['status'] == 'success':
                logger.info(f"✅ {result['scenario']}")
                logger.info(f"   Destination: {result['routing']['destination']}")
                logger.info(f"   Processing Time: {result['processing_time_seconds']:.3f}s")
            else:
                logger.info(f"❌ {result['scenario']}: {result['error']}")

        # System metrics
        status = system.get_system_status()
        logger.info(f"\n📈 SYSTEM METRICS")
        logger.info(f"   Emails Processed: {status['system_metrics']['emails_processed']}")
        logger.info(f"   Auto-replies Sent: {status['system_metrics']['auto_replies_sent']}")
        logger.info(f"   Escalations: {status['system_metrics']['escalations']}")
        logger.info(f"   Active Agents: {status['agents']['active_agents']}")
        logger.info(f"   Uptime: {status['uptime_seconds']:.1f}s")

        # Show KPI achievement
        auto_handle_rate = (status['system_metrics']['auto_replies_sent'] /
                           max(status['system_metrics']['emails_processed'], 1)) * 100

        logger.info(f"\n🎯 KPI ACHIEVEMENT")
        logger.info(f"   Auto-handled Rate: {auto_handle_rate:.1f}% (Target: ≥70%)")
        logger.info(f"   Status: {'✅ ACHIEVED' if auto_handle_rate >= 70 else '⚠️ BELOW TARGET'}")

    except Exception as e:
        logger.error(f"❌ System error: {str(e)}")
    finally:
        await system.shutdown()


if __name__ == "__main__":
    print("""
🎉 Happy Buttons Agentic Simulation System
📧 Python Implementation with Claude Flow Integration
🤖 Royal Courtesy Email Processing

Starting demonstration...
    """)

    asyncio.run(main())