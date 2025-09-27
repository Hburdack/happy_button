"""
Late Triage Scenario Implementation
Release 3.0 - Weakness Injection System
Simulates delayed email processing causing SLA violations and customer escalation
"""

import asyncio
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .email_generator import scenario_email_generator

logger = logging.getLogger(__name__)

@dataclass
class TriageDelay:
    """Represents a delayed email processing event"""
    email_id: str
    email_type: str
    original_sla_minutes: int
    actual_delay_minutes: int
    customer_impact: str
    escalation_triggered: bool
    timestamp: datetime
    generated_email_path: Optional[str] = None

class LateTriage:
    """
    Simulates late email triage causing organizational failures
    Models realistic email processing delays and their cascading effects
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_active = False
        self.delays_created = []
        self.escalations_triggered = 0
        self.sla_violations = 0
        self.customer_complaints = 0

        # Extract configuration
        self.delay_config = config.get('configuration', {}).get('delay_range', {})
        self.sla_targets = config.get('configuration', {}).get('sla_targets', {})
        self.escalation_config = config.get('configuration', {}).get('escalation', {})

        logger.info("Late Triage scenario initialized")

    async def execute_scenario(self, duration_seconds: int, metrics_callback=None) -> Dict[str, Any]:
        """Execute the late triage scenario"""
        logger.info(f"Starting Late Triage scenario for {duration_seconds} seconds")

        self.is_active = True
        start_time = time.time()

        # Scenario execution metrics
        execution_metrics = {
            'total_emails_delayed': 0,
            'sla_violations': 0,
            'escalations_triggered': 0,
            'customer_complaints': 0,
            'average_delay_minutes': 0,
            'max_delay_minutes': 0,
            'reputation_impact': 0
        }

        try:
            while time.time() - start_time < duration_seconds and self.is_active:
                # Simulate incoming emails that get delayed
                await self._process_delayed_email_batch(execution_metrics)

                # Update metrics if callback provided
                if metrics_callback:
                    await metrics_callback(execution_metrics)

                # Wait before next batch (simulate natural email flow)
                await asyncio.sleep(random.uniform(15, 45))  # 15-45 second intervals

        except Exception as e:
            logger.error(f"Error in late triage execution: {e}")
        finally:
            self.is_active = False
            logger.info("Late Triage scenario completed")

        return execution_metrics

    async def _process_delayed_email_batch(self, metrics: Dict[str, Any]):
        """Process a batch of emails with deliberate delays"""
        # Determine number of emails in this batch (1-5 emails)
        batch_size = random.randint(1, 5)

        for _ in range(batch_size):
            await self._create_delayed_email(metrics)

    async def _create_delayed_email(self, metrics: Dict[str, Any]):
        """Create a single delayed email scenario"""
        # Select email type to delay
        email_types = list(self.sla_targets.keys())
        if not email_types:
            email_types = ['customer_inquiry', 'support_request', 'complaint', 'general_info']

        email_type = random.choice(email_types)
        email_id = f"email_{int(time.time())}_{random.randint(1000, 9999)}"

        # Get normal SLA for this email type
        normal_sla_minutes = self.sla_targets.get(email_type, 60)

        # Calculate delay to inject
        min_delay = self.delay_config.get('min_minutes', 15)
        max_delay = self.delay_config.get('max_minutes', 240)
        actual_delay = random.randint(min_delay, max_delay)

        # Determine customer impact based on delay severity
        customer_impact = self._calculate_customer_impact(actual_delay, normal_sla_minutes)

        # Check if escalation is triggered
        escalation_threshold = self.escalation_config.get('escalation_threshold', 120)
        escalation_triggered = actual_delay > escalation_threshold

        # Create delay record
        delay_record = TriageDelay(
            email_id=email_id,
            email_type=email_type,
            original_sla_minutes=normal_sla_minutes,
            actual_delay_minutes=actual_delay,
            customer_impact=customer_impact,
            escalation_triggered=escalation_triggered,
            timestamp=datetime.now()
        )

        self.delays_created.append(delay_record)

        # Update metrics
        metrics['total_emails_delayed'] += 1

        if actual_delay > normal_sla_minutes:
            metrics['sla_violations'] += 1
            self.sla_violations += 1

        if escalation_triggered:
            metrics['escalations_triggered'] += 1
            self.escalations_triggered += 1

        if customer_impact in ['high', 'severe']:
            metrics['customer_complaints'] += 1
            self.customer_complaints += 1

        # Update delay statistics
        all_delays = [d.actual_delay_minutes for d in self.delays_created]
        metrics['average_delay_minutes'] = sum(all_delays) / len(all_delays)
        metrics['max_delay_minutes'] = max(all_delays)

        # Calculate reputation impact (0-100 scale)
        metrics['reputation_impact'] = min(100, self.escalations_triggered * 15 + self.customer_complaints * 10)

        logger.info(f"Created delayed email: {email_type} delayed {actual_delay}min (SLA: {normal_sla_minutes}min)")

        # Generate scenario email for this delay
        await self._generate_scenario_email(delay_record)

        # Simulate additional effects for severe delays
        if actual_delay > 180:  # 3+ hour delays
            await self._trigger_severe_delay_effects(delay_record, metrics)

    async def _generate_scenario_email(self, delay_record: TriageDelay):
        """Generate a visible scenario email for this delay"""
        try:
            # Map email types to scenario email types
            email_type_mapping = {
                'customer_inquiry': 'customer_inquiry',
                'support_request': 'customer_inquiry',
                'general_info': 'customer_inquiry',
                'complaint': 'complaint'
            }

            # Determine scenario email type based on delay severity and original type
            if delay_record.actual_delay_minutes > 120 or delay_record.customer_impact in ['high', 'severe']:
                scenario_email_type = 'complaint'
            else:
                scenario_email_type = email_type_mapping.get(delay_record.email_type, 'customer_inquiry')

            # Create delay information for email generation
            delay_info = {
                'delay_minutes': delay_record.actual_delay_minutes,
                'sla_minutes': delay_record.original_sla_minutes,
                'customer_impact': delay_record.customer_impact,
                'escalation_triggered': delay_record.escalation_triggered,
                'scenario_id': delay_record.email_id
            }

            # Generate the scenario email
            scenario_email = scenario_email_generator.generate_scenario_email(
                scenario_type='late_triage',
                email_type=scenario_email_type,
                delay_info=delay_info
            )

            if scenario_email:
                # Save the email to filesystem for integration with email interfaces
                filepath = scenario_email_generator.save_scenario_email(scenario_email)

                if filepath:
                    logger.info(f"📧 Generated scenario email for delay {delay_record.email_id}: {scenario_email['subject'][:50]}...")

                    # Store reference in delay record for tracking
                    delay_record.generated_email_path = filepath
                else:
                    logger.warning(f"Failed to save scenario email for delay {delay_record.email_id}")
            else:
                logger.warning(f"Failed to generate scenario email for delay {delay_record.email_id}")

        except Exception as e:
            logger.error(f"Error generating scenario email for delay {delay_record.email_id}: {e}")

    def _calculate_customer_impact(self, delay_minutes: int, sla_minutes: int) -> str:
        """Calculate customer impact based on delay severity"""
        if delay_minutes <= sla_minutes:
            return 'none'
        elif delay_minutes <= sla_minutes * 2:
            return 'low'
        elif delay_minutes <= sla_minutes * 4:
            return 'moderate'
        elif delay_minutes <= sla_minutes * 6:
            return 'high'
        else:
            return 'severe'

    async def _trigger_severe_delay_effects(self, delay_record: TriageDelay, metrics: Dict[str, Any]):
        """Handle severe delays with additional cascading effects"""
        logger.warning(f"Severe delay detected: {delay_record.actual_delay_minutes} minutes for {delay_record.email_type}")

        # Severe delays can trigger:
        # 1. Customer frustration escalation
        if delay_record.actual_delay_minutes > 240:  # 4+ hours
            await self._trigger_customer_frustration_escalation(delay_record)

        # 2. Media attention risk
        if delay_record.actual_delay_minutes > 360 and delay_record.email_type == 'complaint':  # 6+ hours for complaints
            await self._trigger_media_attention_risk(delay_record)

        # 3. Internal escalation
        if delay_record.escalation_triggered:
            await self._trigger_internal_escalation(delay_record)

    async def _trigger_customer_frustration_escalation(self, delay_record: TriageDelay):
        """Simulate customer frustration escalation"""
        frustration_rate = self.escalation_config.get('customer_frustration_rate', 1.5)

        # Customer may send additional angry emails
        additional_emails = int(delay_record.actual_delay_minutes / 120)  # One per 2 hours

        logger.warning(f"Customer frustration escalation: {additional_emails} additional angry emails generated")

        # These additional emails also get delayed, creating a feedback loop
        for i in range(additional_emails):
            follow_up_delay = TriageDelay(
                email_id=f"{delay_record.email_id}_followup_{i}",
                email_type='complaint',
                original_sla_minutes=15,  # Complaints should be fast
                actual_delay_minutes=random.randint(60, 180),  # But they're also delayed
                customer_impact='high',
                escalation_triggered=True,
                timestamp=datetime.now()
            )
            self.delays_created.append(follow_up_delay)

            # Generate additional angry emails for the escalation
            await self._generate_scenario_email(follow_up_delay)

    async def _trigger_media_attention_risk(self, delay_record: TriageDelay):
        """Simulate media attention risk for severe service failures"""
        logger.critical(f"MEDIA ATTENTION RISK: Severe delay ({delay_record.actual_delay_minutes}min) may attract negative publicity")

        # This could trigger social media complaints, review site negative reviews, etc.
        # For simulation purposes, we just log the risk

    async def _trigger_internal_escalation(self, delay_record: TriageDelay):
        """Simulate internal management escalation"""
        logger.warning(f"Internal escalation triggered for {delay_record.email_id}")

        # Management now gets involved, adding overhead
        # In reality, this might involve:
        # - Manager emails asking for status
        # - Emergency meetings
        # - Process reviews
        # - Additional delays due to management overhead

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current scenario metrics"""
        if not self.delays_created:
            return {
                'total_delays': 0,
                'sla_violations': 0,
                'escalations': 0,
                'average_delay': 0,
                'max_delay': 0,
                'active': self.is_active
            }

        delays = [d.actual_delay_minutes for d in self.delays_created]

        return {
            'total_delays': len(self.delays_created),
            'sla_violations': self.sla_violations,
            'escalations': self.escalations_triggered,
            'customer_complaints': self.customer_complaints,
            'average_delay': sum(delays) / len(delays),
            'max_delay': max(delays),
            'active': self.is_active,
            'reputation_impact': min(100, self.escalations_triggered * 15 + self.customer_complaints * 10)
        }

    def get_kpi_impact(self) -> Dict[str, float]:
        """Calculate KPI degradation caused by late triage"""
        if not self.delays_created:
            return {}

        # Calculate various KPI impacts
        baseline_response_time = 60  # 1 hour baseline
        delays = [d.actual_delay_minutes for d in self.delays_created]
        avg_delay = sum(delays) / len(delays)

        # Response time degradation (percentage increase)
        response_time_degradation = ((avg_delay - baseline_response_time) / baseline_response_time) * 100
        response_time_degradation = max(0, min(400, response_time_degradation))  # Cap at 400%

        # Customer satisfaction impact (0-100, where 100 is perfect)
        baseline_satisfaction = 95
        satisfaction_drop = (self.escalations_triggered * 15) + (self.customer_complaints * 8)
        customer_satisfaction = max(30, baseline_satisfaction - satisfaction_drop)

        # SLA compliance (percentage of emails meeting SLA)
        total_emails = len(self.delays_created)
        sla_compliant = total_emails - self.sla_violations
        sla_compliance = (sla_compliant / total_emails) * 100 if total_emails > 0 else 100

        return {
            'response_time_increase_percent': response_time_degradation,
            'customer_satisfaction_score': customer_satisfaction,
            'sla_compliance_percent': sla_compliance,
            'escalation_rate_percent': (self.escalations_triggered / total_emails) * 100 if total_emails > 0 else 0,
            'reputation_score': max(0, 100 - (self.escalations_triggered * 15 + self.customer_complaints * 10))
        }

    def stop_scenario(self):
        """Stop the running scenario"""
        logger.info("Stopping Late Triage scenario")
        self.is_active = False

    def reset_scenario(self):
        """Reset scenario to initial state"""
        logger.info("Resetting Late Triage scenario")
        self.is_active = False
        self.delays_created = []
        self.escalations_triggered = 0
        self.sla_violations = 0
        self.customer_complaints = 0

    def get_detailed_report(self) -> Dict[str, Any]:
        """Generate detailed scenario report"""
        if not self.delays_created:
            return {'message': 'No delays recorded yet'}

        # Categorize delays by severity
        delays_by_impact = {}
        for delay in self.delays_created:
            impact = delay.customer_impact
            if impact not in delays_by_impact:
                delays_by_impact[impact] = []
            delays_by_impact[impact].append(delay)

        # Calculate statistics
        delays = [d.actual_delay_minutes for d in self.delays_created]

        return {
            'scenario_summary': {
                'total_emails_delayed': len(self.delays_created),
                'sla_violations': self.sla_violations,
                'escalations_triggered': self.escalations_triggered,
                'customer_complaints': self.customer_complaints
            },
            'delay_statistics': {
                'average_delay_minutes': sum(delays) / len(delays),
                'max_delay_minutes': max(delays),
                'min_delay_minutes': min(delays),
                'total_delay_hours': sum(delays) / 60
            },
            'impact_breakdown': {
                impact: len(delays) for impact, delays in delays_by_impact.items()
            },
            'kpi_impact': self.get_kpi_impact(),
            'business_impact': {
                'estimated_customer_loss': self.escalations_triggered * 0.15,  # 15% customer loss per escalation
                'reputation_damage_score': min(100, self.escalations_triggered * 15),
                'recovery_time_estimate_hours': max(24, self.escalations_triggered * 8)
            }
        }