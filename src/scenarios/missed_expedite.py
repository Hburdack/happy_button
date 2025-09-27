"""
Missed Expedite Scenario Implementation
Release 3.0 - Weakness Injection System
Simulates missed high-profit expedite requests due to poor email routing
"""

import asyncio
import logging
import time
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .email_generator import scenario_email_generator

logger = logging.getLogger(__name__)

@dataclass
class ExpediteOpportunity:
    """Represents a missed expedite opportunity"""
    opportunity_id: str
    customer_email: str
    email_content: str
    expedite_value_euro: float
    profit_multiplier: float
    keywords_detected: List[str]
    missed: bool
    detection_delay_minutes: int
    customer_response: str
    competitor_switch: bool
    timestamp: datetime
    generated_email_path: Optional[str] = None

class MissedExpedite:
    """
    Simulates missed high-profit expedite opportunities
    Models realistic email detection failures and revenue impact
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_active = False
        self.opportunities_created = []
        self.opportunities_missed = 0
        self.total_revenue_lost = 0.0
        self.competitor_switches = 0
        self.negative_reviews = 0

        # Extract configuration
        self.expedite_config = config.get('configuration', {})
        self.keywords = self.expedite_config.get('expedite_keywords', [])
        self.opportunity_values = self.expedite_config.get('opportunity_values', {})
        self.customer_response_config = self.expedite_config.get('customer_response', {})
        self.miss_rate = self.expedite_config.get('miss_rate', 0.75)
        self.detection_delay = self.expedite_config.get('detection_delay', 180)

        logger.info("Missed Expedite scenario initialized")

    async def execute_scenario(self, duration_seconds: int, metrics_callback=None) -> Dict[str, Any]:
        """Execute the missed expedite scenario"""
        logger.info(f"Starting Missed Expedite scenario for {duration_seconds} seconds")

        self.is_active = True
        start_time = time.time()

        # Scenario execution metrics
        execution_metrics = {
            'total_opportunities': 0,
            'opportunities_missed': 0,
            'revenue_lost_euro': 0.0,
            'competitor_switches': 0,
            'negative_reviews': 0,
            'average_opportunity_value': 0.0,
            'max_opportunity_value': 0.0,
            'detection_efficiency': 0.0
        }

        try:
            while time.time() - start_time < duration_seconds and self.is_active:
                # Simulate incoming expedite opportunities
                await self._process_expedite_opportunity_batch(execution_metrics)

                # Update metrics if callback provided
                if metrics_callback:
                    await metrics_callback(execution_metrics)

                # Wait before next batch (expedites are less frequent than regular emails)
                await asyncio.sleep(random.uniform(45, 120))  # 45-120 second intervals

        except Exception as e:
            logger.error(f"Error in missed expedite execution: {e}")
        finally:
            self.is_active = False
            logger.info("Missed Expedite scenario completed")

        return execution_metrics

    async def _process_expedite_opportunity_batch(self, metrics: Dict[str, Any]):
        """Process a batch of potential expedite opportunities"""
        # Expedites are rarer - typically 1-2 per batch
        batch_size = random.choices([1, 2, 3], weights=[60, 30, 10])[0]

        for _ in range(batch_size):
            await self._create_expedite_opportunity(metrics)

    async def _create_expedite_opportunity(self, metrics: Dict[str, Any]):
        """Create a single expedite opportunity scenario"""
        # Generate realistic expedite email content
        opportunity_id = f"expedite_{int(time.time())}_{random.randint(1000, 9999)}"
        customer_email = f"customer_{random.randint(1000, 9999)}@company.com"

        # Generate expedite request content
        email_content, detected_keywords = self._generate_expedite_email()

        # Calculate opportunity value
        min_value = self.opportunity_values.get('min_euro', 5000)
        max_value = self.opportunity_values.get('max_euro', 50000)
        opportunity_value = random.uniform(min_value, max_value)
        profit_multiplier = self.opportunity_values.get('profit_multiplier', 10)

        # Determine if this opportunity is missed
        is_missed = random.random() < self.miss_rate

        # Calculate detection delay (if detected at all)
        if is_missed:
            detection_delay = self.detection_delay + random.randint(60, 300)  # Much longer delay
        else:
            detection_delay = random.randint(5, 30)  # Quick detection

        # Determine customer response based on miss
        customer_response = self._determine_customer_response(is_missed, detection_delay)

        # Check if customer switches to competitor
        switch_rate = self.customer_response_config.get('competitor_switch_rate', 0.4)
        competitor_switch = is_missed and random.random() < switch_rate

        # Create opportunity record
        opportunity = ExpediteOpportunity(
            opportunity_id=opportunity_id,
            customer_email=customer_email,
            email_content=email_content,
            expedite_value_euro=opportunity_value,
            profit_multiplier=profit_multiplier,
            keywords_detected=detected_keywords,
            missed=is_missed,
            detection_delay_minutes=detection_delay,
            customer_response=customer_response,
            competitor_switch=competitor_switch,
            timestamp=datetime.now()
        )

        self.opportunities_created.append(opportunity)

        # Update metrics
        metrics['total_opportunities'] += 1

        if is_missed:
            metrics['opportunities_missed'] += 1
            self.opportunities_missed += 1

            # Calculate revenue loss
            revenue_loss = opportunity_value * profit_multiplier
            metrics['revenue_lost_euro'] += revenue_loss
            self.total_revenue_lost += revenue_loss

        if competitor_switch:
            metrics['competitor_switches'] += 1
            self.competitor_switches += 1

        # Check for negative reviews
        review_rate = self.customer_response_config.get('negative_reviews', 0.6)
        if is_missed and random.random() < review_rate:
            metrics['negative_reviews'] += 1
            self.negative_reviews += 1

        # Update opportunity statistics
        all_values = [o.expedite_value_euro for o in self.opportunities_created]
        metrics['average_opportunity_value'] = sum(all_values) / len(all_values)
        metrics['max_opportunity_value'] = max(all_values)

        # Calculate detection efficiency
        total_opportunities = len(self.opportunities_created)
        detected_opportunities = total_opportunities - self.opportunities_missed
        metrics['detection_efficiency'] = (detected_opportunities / total_opportunities) * 100 if total_opportunities > 0 else 100

        logger.info(f"Created expedite opportunity: €{opportunity_value:,.0f} {'MISSED' if is_missed else 'DETECTED'}")

        # Generate scenario email for this expedite opportunity
        await self._generate_scenario_email(opportunity)

        # Simulate additional effects for high-value missed opportunities
        if is_missed and opportunity_value > 25000:  # High-value opportunities
            await self._trigger_high_value_miss_effects(opportunity, metrics)

    async def _generate_scenario_email(self, opportunity: ExpediteOpportunity):
        """Generate a visible scenario email for this expedite opportunity"""
        try:
            # Create delay information for email generation
            delay_info = {
                'delay_minutes': opportunity.detection_delay_minutes,
                'sla_minutes': 30,  # Expedites should be responded to quickly
                'opportunity_value': opportunity.expedite_value_euro,
                'profit_multiplier': opportunity.profit_multiplier,
                'keywords_detected': opportunity.keywords_detected,
                'missed': opportunity.missed,
                'competitor_switch': opportunity.competitor_switch,
                'scenario_id': opportunity.opportunity_id
            }

            # Generate the scenario email
            scenario_email = scenario_email_generator.generate_scenario_email(
                scenario_type='missed_expedite',
                email_type='expedite_request',
                delay_info=delay_info
            )

            if scenario_email:
                # Save the email to filesystem for integration with email interfaces
                filepath = scenario_email_generator.save_scenario_email(scenario_email)

                if filepath:
                    logger.info(f"📧 Generated expedite scenario email for opportunity {opportunity.opportunity_id}: {scenario_email['subject'][:50]}...")

                    # Store reference in opportunity record for tracking
                    opportunity.generated_email_path = filepath
                else:
                    logger.warning(f"Failed to save expedite scenario email for opportunity {opportunity.opportunity_id}")
            else:
                logger.warning(f"Failed to generate expedite scenario email for opportunity {opportunity.opportunity_id}")

        except Exception as e:
            logger.error(f"Error generating expedite scenario email for opportunity {opportunity.opportunity_id}: {e}")

    def _generate_expedite_email(self) -> tuple[str, List[str]]:
        """Generate realistic expedite email content with keyword detection"""
        # Email templates with varying urgency levels
        templates = [
            "Subject: URGENT - Need expedite delivery for €{value} order\n\nWe have a critical project deadline and need rush delivery. Can you expedite our order for 24h delivery? This is worth 10x our normal profit margin. Please confirm immediately.",

            "Subject: Emergency Rush Order - Premium Delivery Required\n\nHi, we have an immediate need for emergency delivery. Our client is willing to pay premium rates for expedite service. Time is critical - can you help with urgent processing?",

            "Subject: High Priority - Expedite Request for Strategic Project\n\nWe need to expedite delivery for a major client project. Standard delivery won't work - we need rush processing. This is a high-value opportunity with excellent profit margins.",

            "Subject: Time-Sensitive - 24h Delivery Required\n\nOur client has an immediate deadline and we need emergency expedite service. They're offering premium pricing for 24h delivery. Can you confirm expedite availability?",

            "Subject: Critical Deadline - Rush Order with 10x Profit\n\nWe have a critical situation requiring immediate expedite processing. The client is offering exceptional rates for emergency delivery. This is a high-profit opportunity that requires urgent attention."
        ]

        # Select random template and value
        template = random.choice(templates)
        value = random.randint(5000, 50000)
        email_content = template.format(value=value)

        # Detect keywords in the generated content
        detected_keywords = []
        for keyword in self.keywords:
            if keyword.lower() in email_content.lower():
                detected_keywords.append(keyword)

        return email_content, detected_keywords

    def _determine_customer_response(self, is_missed: bool, detection_delay: int) -> str:
        """Determine customer response based on detection performance"""
        if not is_missed and detection_delay < 15:
            return "delighted"  # Quick detection, customer very happy
        elif not is_missed and detection_delay < 60:
            return "satisfied"  # Reasonable detection time
        elif not is_missed:
            return "concerned"  # Detected but slow
        elif detection_delay < 240:
            return "frustrated"  # Missed but detected within 4 hours
        elif detection_delay < 480:
            return "angry"  # Missed, detected after 4-8 hours
        else:
            return "furious"  # Missed, detected after 8+ hours or not at all

    async def _trigger_high_value_miss_effects(self, opportunity: ExpediteOpportunity, metrics: Dict[str, Any]):
        """Handle high-value missed opportunities with additional cascading effects"""
        logger.critical(f"HIGH-VALUE MISS: €{opportunity.expedite_value_euro:,.0f} opportunity missed")

        # High-value misses can trigger:
        # 1. Immediate competitor engagement
        if opportunity.expedite_value_euro > 30000:
            await self._trigger_competitor_engagement(opportunity)

        # 2. Industry reputation damage
        if opportunity.expedite_value_euro > 40000:
            await self._trigger_industry_reputation_damage(opportunity)

        # 3. Customer relationship termination
        if opportunity.competitor_switch:
            await self._trigger_relationship_termination(opportunity)

    async def _trigger_competitor_engagement(self, opportunity: ExpediteOpportunity):
        """Simulate customer immediately engaging competitors"""
        logger.warning(f"Customer {opportunity.customer_email} immediately contacted competitors for €{opportunity.expedite_value_euro:,.0f} opportunity")

        # Customer likely gets better service from competitor
        # This could lead to:
        # - Lost current sale
        # - Lost future business
        # - Competitor gaining market intelligence
        # - Customer sharing negative experience

    async def _trigger_industry_reputation_damage(self, opportunity: ExpediteOpportunity):
        """Simulate industry reputation damage from high-value misses"""
        logger.critical(f"INDUSTRY REPUTATION DAMAGE: High-value miss may damage industry standing")

        # High-value misses in small industries get noticed
        # This could trigger:
        # - Word-of-mouth damage
        # - Industry conference discussions
        # - Reduced referrals
        # - Competitive disadvantage

    async def _trigger_relationship_termination(self, opportunity: ExpediteOpportunity):
        """Simulate customer relationship termination"""
        logger.critical(f"RELATIONSHIP TERMINATION: Customer {opportunity.customer_email} switching to competitor")

        # Calculate future business impact
        annual_value = opportunity.expedite_value_euro * random.uniform(5, 15)  # 5-15x annual relationship value
        logger.warning(f"Estimated annual relationship value lost: €{annual_value:,.0f}")

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current scenario metrics"""
        if not self.opportunities_created:
            return {
                'total_opportunities': 0,
                'opportunities_missed': 0,
                'revenue_lost': 0.0,
                'competitor_switches': 0,
                'detection_rate': 100.0,
                'active': self.is_active
            }

        total_opportunities = len(self.opportunities_created)
        opportunities_detected = total_opportunities - self.opportunities_missed
        detection_rate = (opportunities_detected / total_opportunities) * 100

        return {
            'total_opportunities': total_opportunities,
            'opportunities_missed': self.opportunities_missed,
            'revenue_lost_euro': self.total_revenue_lost,
            'competitor_switches': self.competitor_switches,
            'negative_reviews': self.negative_reviews,
            'detection_rate_percent': detection_rate,
            'average_opportunity_value': sum(o.expedite_value_euro for o in self.opportunities_created) / total_opportunities,
            'active': self.is_active
        }

    def get_kpi_impact(self) -> Dict[str, float]:
        """Calculate KPI degradation caused by missed expedites"""
        if not self.opportunities_created:
            return {}

        total_opportunities = len(self.opportunities_created)

        # Revenue impact calculation
        potential_revenue = sum(o.expedite_value_euro * o.profit_multiplier for o in self.opportunities_created)
        actual_revenue = sum(o.expedite_value_euro * o.profit_multiplier for o in self.opportunities_created if not o.missed)
        revenue_loss_percent = ((potential_revenue - actual_revenue) / potential_revenue) * 100 if potential_revenue > 0 else 0

        # Market position impact
        baseline_market_share = 25  # 25% baseline market share
        market_share_loss = self.competitor_switches * 2  # 2% loss per competitor switch
        current_market_share = max(10, baseline_market_share - market_share_loss)

        # Customer satisfaction (expedite customers are typically high-value)
        baseline_satisfaction = 90
        satisfaction_drop = (self.opportunities_missed * 20) + (self.negative_reviews * 15)
        customer_satisfaction = max(30, baseline_satisfaction - satisfaction_drop)

        # Competitive advantage (expedites are often unique opportunities)
        baseline_advantage = 80
        advantage_loss = (self.opportunities_missed * 15) + (self.competitor_switches * 25)
        competitive_advantage = max(20, baseline_advantage - advantage_loss)

        return {
            'revenue_loss_percent': revenue_loss_percent,
            'market_share_percent': current_market_share,
            'customer_satisfaction_score': customer_satisfaction,
            'competitive_advantage_score': competitive_advantage,
            'detection_efficiency_percent': (total_opportunities - self.opportunities_missed) / total_opportunities * 100 if total_opportunities > 0 else 100,
            'reputation_score': max(0, 100 - (self.competitor_switches * 30 + self.negative_reviews * 20))
        }

    def stop_scenario(self):
        """Stop the running scenario"""
        logger.info("Stopping Missed Expedite scenario")
        self.is_active = False

    def reset_scenario(self):
        """Reset scenario to initial state"""
        logger.info("Resetting Missed Expedite scenario")
        self.is_active = False
        self.opportunities_created = []
        self.opportunities_missed = 0
        self.total_revenue_lost = 0.0
        self.competitor_switches = 0
        self.negative_reviews = 0

    def get_detailed_report(self) -> Dict[str, Any]:
        """Generate detailed scenario report"""
        if not self.opportunities_created:
            return {'message': 'No expedite opportunities recorded yet'}

        # Categorize opportunities by value
        opportunities_by_value = {
            'low_value': [],      # < €10K
            'medium_value': [],   # €10K - €25K
            'high_value': [],     # €25K - €40K
            'critical_value': []  # > €40K
        }

        for opp in self.opportunities_created:
            if opp.expedite_value_euro < 10000:
                opportunities_by_value['low_value'].append(opp)
            elif opp.expedite_value_euro < 25000:
                opportunities_by_value['medium_value'].append(opp)
            elif opp.expedite_value_euro < 40000:
                opportunities_by_value['high_value'].append(opp)
            else:
                opportunities_by_value['critical_value'].append(opp)

        # Calculate statistics
        values = [o.expedite_value_euro for o in self.opportunities_created]
        total_potential_revenue = sum(o.expedite_value_euro * o.profit_multiplier for o in self.opportunities_created)
        actual_revenue = sum(o.expedite_value_euro * o.profit_multiplier for o in self.opportunities_created if not o.missed)

        return {
            'scenario_summary': {
                'total_opportunities': len(self.opportunities_created),
                'opportunities_missed': self.opportunities_missed,
                'competitor_switches': self.competitor_switches,
                'negative_reviews': self.negative_reviews
            },
            'financial_impact': {
                'total_potential_revenue_euro': total_potential_revenue,
                'actual_revenue_euro': actual_revenue,
                'revenue_lost_euro': self.total_revenue_lost,
                'average_opportunity_value_euro': sum(values) / len(values),
                'max_opportunity_value_euro': max(values),
                'profit_multiplier_average': self.opportunity_values.get('profit_multiplier', 10)
            },
            'opportunity_breakdown': {
                category: len(opportunities) for category, opportunities in opportunities_by_value.items()
            },
            'kpi_impact': self.get_kpi_impact(),
            'business_impact': {
                'market_share_loss_percent': self.competitor_switches * 2,
                'customer_relationship_damage': self.competitor_switches,
                'industry_reputation_impact': 'high' if self.opportunities_missed > 5 else 'medium',
                'recovery_time_estimate_months': max(6, self.competitor_switches * 3)
            },
            'keyword_analysis': {
                'most_common_keywords': self._analyze_keyword_frequency(),
                'detection_patterns': self._analyze_detection_patterns()
            }
        }

    def _analyze_keyword_frequency(self) -> Dict[str, int]:
        """Analyze frequency of expedite keywords"""
        keyword_count = {}
        for opp in self.opportunities_created:
            for keyword in opp.keywords_detected:
                keyword_count[keyword] = keyword_count.get(keyword, 0) + 1

        # Sort by frequency
        return dict(sorted(keyword_count.items(), key=lambda x: x[1], reverse=True))

    def _analyze_detection_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in detection success/failure"""
        patterns = {
            'keywords_per_detection': {},
            'value_threshold_analysis': {},
            'timing_patterns': {}
        }

        # Analyze keyword count vs detection success
        for opp in self.opportunities_created:
            keyword_count = len(opp.keywords_detected)
            if keyword_count not in patterns['keywords_per_detection']:
                patterns['keywords_per_detection'][keyword_count] = {'total': 0, 'detected': 0}

            patterns['keywords_per_detection'][keyword_count]['total'] += 1
            if not opp.missed:
                patterns['keywords_per_detection'][keyword_count]['detected'] += 1

        return patterns