"""
VIP Customer Mishandling Scenario Implementation
Release 3.0 - Weakness Injection System
Simulates inadequate handling of VIP customer requests causing reputation damage
"""

import asyncio
import logging
import time
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .email_generator import scenario_email_generator

logger = logging.getLogger(__name__)

class VIPTier(Enum):
    """VIP customer tiers"""
    ROYAL_BLUE = "royal_blue"
    STRATEGIC = "strategic"
    HIGH_VALUE = "high_value"
    MEDIA_VISIBLE = "media_visible"

class MishandlingType(Enum):
    """Types of VIP mishandling"""
    DELAYED_RESPONSE = "delayed_response"
    WRONG_DEPARTMENT = "wrong_department"
    AUTOMATED_REPLY = "automated_reply"
    NO_ESCALATION = "no_escalation"
    JUNIOR_STAFF = "junior_staff"
    GENERIC_TREATMENT = "generic_treatment"

@dataclass
class VIPIncident:
    """Represents a VIP customer mishandling incident"""
    incident_id: str
    customer_id: str
    customer_name: str
    vip_tier: VIPTier
    email_content: str
    annual_revenue_euro: float
    mishandling_types: List[MishandlingType]
    response_delay_hours: float
    reputation_impact_score: int
    social_media_risk: bool
    media_coverage_risk: bool
    relationship_damage: str
    recovery_difficulty: str
    timestamp: datetime
    generated_email_path: Optional[str] = None

class VIPHandling:
    """
    Simulates VIP customer mishandling causing reputation damage
    Models realistic failures in premium customer service
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_active = False
        self.incidents_created = []
        self.total_incidents = 0
        self.reputation_damage_score = 0
        self.social_media_incidents = 0
        self.media_coverage_incidents = 0
        self.relationship_terminations = 0

        # Extract configuration
        self.vip_config = config.get('configuration', {})
        self.vip_criteria = self.vip_config.get('vip_criteria', {})
        self.vip_indicators = self.vip_config.get('vip_indicators', [])
        self.mishandling_types_config = self.vip_config.get('mishandling_types', {})
        self.reputation_damage_config = self.vip_config.get('reputation_damage', {})

        logger.info("VIP Handling scenario initialized")

    async def execute_scenario(self, duration_seconds: int, metrics_callback=None) -> Dict[str, Any]:
        """Execute the VIP handling mismanagement scenario"""
        logger.info(f"Starting VIP Handling scenario for {duration_seconds} seconds")

        self.is_active = True
        start_time = time.time()

        # Scenario execution metrics
        execution_metrics = {
            'total_vip_incidents': 0,
            'reputation_damage_score': 0,
            'social_media_incidents': 0,
            'media_coverage_incidents': 0,
            'relationship_terminations': 0,
            'average_response_delay': 0.0,
            'high_value_incidents': 0,
            'recovery_difficulty_high': 0
        }

        try:
            while time.time() - start_time < duration_seconds and self.is_active:
                # Simulate VIP customer incidents
                await self._process_vip_incident_batch(execution_metrics)

                # Update metrics if callback provided
                if metrics_callback:
                    await metrics_callback(execution_metrics)

                # Wait before next batch (VIP incidents are less frequent but more impactful)
                await asyncio.sleep(random.uniform(60, 180))  # 1-3 minute intervals

        except Exception as e:
            logger.error(f"Error in VIP handling execution: {e}")
        finally:
            self.is_active = False
            logger.info("VIP Handling scenario completed")

        return execution_metrics

    async def _process_vip_incident_batch(self, metrics: Dict[str, Any]):
        """Process a batch of VIP incidents"""
        # VIP incidents are rare but critical - typically 1 per batch
        batch_size = random.choices([1, 2], weights=[80, 20])[0]

        for _ in range(batch_size):
            await self._create_vip_incident(metrics)

    async def _create_vip_incident(self, metrics: Dict[str, Any]):
        """Create a single VIP mishandling incident"""
        # Generate VIP customer profile
        incident_id = f"vip_{int(time.time())}_{random.randint(1000, 9999)}"
        vip_profile = self._generate_vip_customer_profile()

        # Generate VIP request content
        email_content = self._generate_vip_email_content(vip_profile)

        # Determine mishandling types
        mishandling_types = self._determine_mishandling_types()

        # Calculate response delay based on mishandling
        response_delay = self._calculate_response_delay(mishandling_types, vip_profile['tier'])

        # Calculate reputation impact
        reputation_impact = self._calculate_reputation_impact(vip_profile, mishandling_types, response_delay)

        # Determine risks and damages
        social_media_risk = self._assess_social_media_risk(vip_profile, reputation_impact)
        media_coverage_risk = self._assess_media_coverage_risk(vip_profile, reputation_impact)
        relationship_damage = self._assess_relationship_damage(vip_profile, mishandling_types)
        recovery_difficulty = self._assess_recovery_difficulty(vip_profile, reputation_impact)

        # Create incident record
        incident = VIPIncident(
            incident_id=incident_id,
            customer_id=vip_profile['customer_id'],
            customer_name=vip_profile['customer_name'],
            vip_tier=vip_profile['tier'],
            email_content=email_content,
            annual_revenue_euro=vip_profile['annual_revenue'],
            mishandling_types=mishandling_types,
            response_delay_hours=response_delay,
            reputation_impact_score=reputation_impact,
            social_media_risk=social_media_risk,
            media_coverage_risk=media_coverage_risk,
            relationship_damage=relationship_damage,
            recovery_difficulty=recovery_difficulty,
            timestamp=datetime.now()
        )

        self.incidents_created.append(incident)

        # Update metrics
        metrics['total_vip_incidents'] += 1
        self.total_incidents += 1

        metrics['reputation_damage_score'] += reputation_impact
        self.reputation_damage_score += reputation_impact

        if social_media_risk:
            metrics['social_media_incidents'] += 1
            self.social_media_incidents += 1

        if media_coverage_risk:
            metrics['media_coverage_incidents'] += 1
            self.media_coverage_incidents += 1

        if relationship_damage == "severe":
            metrics['relationship_terminations'] += 1
            self.relationship_terminations += 1

        if vip_profile['annual_revenue'] > 500000:  # High-value customers
            metrics['high_value_incidents'] += 1

        if recovery_difficulty == "high":
            metrics['recovery_difficulty_high'] += 1

        # Update average response delay
        all_delays = [i.response_delay_hours for i in self.incidents_created]
        metrics['average_response_delay'] = sum(all_delays) / len(all_delays)

        logger.warning(f"VIP incident created: {vip_profile['tier'].value} customer, {len(mishandling_types)} mishandling types, {response_delay:.1f}h delay")

        # Generate scenario email for this VIP incident
        await self._generate_scenario_email(incident)

        # Simulate cascading effects for severe incidents
        if reputation_impact > 80 or media_coverage_risk:
            await self._trigger_cascading_effects(incident, metrics)

    async def _generate_scenario_email(self, incident: VIPIncident):
        """Generate a visible scenario email for this VIP incident"""
        try:
            # Create delay information for email generation
            delay_info = {
                'delay_minutes': incident.response_delay_hours * 60,
                'sla_minutes': 15,  # VIPs should get very fast responses
                'vip_tier': incident.vip_tier.value,
                'annual_revenue': incident.annual_revenue_euro,
                'mishandling_types': [mt.value for mt in incident.mishandling_types],
                'reputation_impact': incident.reputation_impact_score,
                'social_media_risk': incident.social_media_risk,
                'media_coverage_risk': incident.media_coverage_risk,
                'relationship_damage': incident.relationship_damage,
                'recovery_difficulty': incident.recovery_difficulty,
                'scenario_id': incident.incident_id
            }

            # Generate the scenario email
            scenario_email = scenario_email_generator.generate_scenario_email(
                scenario_type='vip_handling',
                email_type='vip_request',
                delay_info=delay_info
            )

            if scenario_email:
                # Save the email to filesystem for integration with email interfaces
                filepath = scenario_email_generator.save_scenario_email(scenario_email)

                if filepath:
                    logger.info(f"📧 Generated VIP scenario email for incident {incident.incident_id}: {scenario_email['subject'][:50]}...")

                    # Store reference in incident record for tracking
                    incident.generated_email_path = filepath
                else:
                    logger.warning(f"Failed to save VIP scenario email for incident {incident.incident_id}")
            else:
                logger.warning(f"Failed to generate VIP scenario email for incident {incident.incident_id}")

        except Exception as e:
            logger.error(f"Error generating VIP scenario email for incident {incident.incident_id}: {e}")

    def _generate_vip_customer_profile(self) -> Dict[str, Any]:
        """Generate a realistic VIP customer profile"""
        # Determine VIP tier
        tier_weights = [30, 25, 35, 10]  # royal_blue, strategic, high_value, media_visible
        tier = random.choices(list(VIPTier), weights=tier_weights)[0]

        # Generate customer details based on tier
        if tier == VIPTier.ROYAL_BLUE:
            customer_names = ["Royal Palace Procurement", "Duke of Wellington Estate", "Crown Property Services", "Royal Household Management"]
            annual_revenue_range = (500000, 2000000)
        elif tier == VIPTier.STRATEGIC:
            customer_names = ["Global Manufacturing Corp", "Strategic Partners Inc", "Enterprise Solutions Ltd", "International Holdings"]
            annual_revenue_range = (250000, 1000000)
        elif tier == VIPTier.HIGH_VALUE:
            customer_names = ["Premium Client Services", "Elite Business Group", "Executive Solutions", "Corporate Excellence"]
            annual_revenue_range = (100000, 500000)
        else:  # MEDIA_VISIBLE
            customer_names = ["Celebrity Event Planning", "Media Production House", "Public Relations Agency", "Entertainment Group"]
            annual_revenue_range = (150000, 800000)

        customer_id = f"{tier.value}_{random.randint(1000, 9999)}"
        customer_name = random.choice(customer_names)
        annual_revenue = random.uniform(*annual_revenue_range)

        return {
            'customer_id': customer_id,
            'customer_name': customer_name,
            'tier': tier,
            'annual_revenue': annual_revenue
        }

    def _generate_vip_email_content(self, vip_profile: Dict[str, Any]) -> str:
        """Generate realistic VIP email content"""
        tier = vip_profile['tier']
        customer_name = vip_profile['customer_name']

        if tier == VIPTier.ROYAL_BLUE:
            templates = [
                f"Subject: Urgent Royal Household Request\n\nWe require immediate assistance with a confidential royal engagement. As our trusted premium supplier, we need your personal attention to this matter. Time is of the essence.",
                f"Subject: Crown Property Requirements\n\nThe Royal Household has specific requirements that need immediate attention. We expect the highest level of service as per our long-standing relationship.",
                f"Subject: Confidential Royal Commission\n\nWe have an exclusive requirement for the Royal Family. Please ensure this receives your personal oversight and absolute discretion."
            ]
        elif tier == VIPTier.STRATEGIC:
            templates = [
                f"Subject: Strategic Partnership - Urgent Board Request\n\nOur board has requested immediate action on this strategic initiative. As our key partner, we need executive-level attention to resolve this matter.",
                f"Subject: C-Level Escalation Required\n\nThis requires immediate escalation to your senior management. Our strategic partnership depends on your swift resolution of this issue.",
                f"Subject: Board-Level Priority\n\nOur CEO has personally asked me to contact you regarding this critical matter. We need your most senior people involved immediately."
            ]
        elif tier == VIPTier.HIGH_VALUE:
            templates = [
                f"Subject: Premium Client - Immediate Attention Required\n\nAs one of your largest clients, we expect immediate premium service. This matter requires your personal oversight and fastest resolution.",
                f"Subject: High-Value Account - Executive Escalation\n\nGiven our significant business relationship, we need this escalated to your senior team immediately. Standard procedures are not sufficient.",
                f"Subject: VIP Client Request - Urgent Response Needed\n\nWe pay premium rates and expect premium service. Please ensure your best people handle this personally."
            ]
        else:  # MEDIA_VISIBLE
            templates = [
                f"Subject: Media Event - Public Relations Critical\n\nThis is for a high-profile media event with significant public exposure. Any delays could result in negative publicity for both our organizations.",
                f"Subject: Celebrity Client - Reputation Risk\n\nWe're handling this for a major celebrity client. Public reputation is at stake, so we need flawless execution and complete discretion.",
                f"Subject: Public Event - Media Coverage Expected\n\nThis will have extensive media coverage and public attention. Your performance will reflect on both our companies' reputations."
            ]

        return random.choice(templates)

    def _determine_mishandling_types(self) -> List[MishandlingType]:
        """Determine what types of mishandling occur"""
        mishandling_types = []

        # Check each mishandling type based on configuration probabilities
        if random.random() < self.mishandling_types_config.get('delayed_response', 0.6):
            mishandling_types.append(MishandlingType.DELAYED_RESPONSE)

        if random.random() < self.mishandling_types_config.get('wrong_department', 0.3):
            mishandling_types.append(MishandlingType.WRONG_DEPARTMENT)

        if random.random() < self.mishandling_types_config.get('automated_reply', 0.4):
            mishandling_types.append(MishandlingType.AUTOMATED_REPLY)

        if random.random() < self.mishandling_types_config.get('no_escalation', 0.8):
            mishandling_types.append(MishandlingType.NO_ESCALATION)

        # Additional mishandling types
        if random.random() < 0.5:  # 50% chance of junior staff handling VIP
            mishandling_types.append(MishandlingType.JUNIOR_STAFF)

        if random.random() < 0.6:  # 60% chance of generic treatment
            mishandling_types.append(MishandlingType.GENERIC_TREATMENT)

        # Ensure at least one mishandling type occurs
        if not mishandling_types:
            mishandling_types.append(random.choice(list(MishandlingType)))

        return mishandling_types

    def _calculate_response_delay(self, mishandling_types: List[MishandlingType], vip_tier: VIPTier) -> float:
        """Calculate response delay based on mishandling types"""
        base_delay = 0.5  # 30 minutes base delay

        # Add delay for each mishandling type
        delay_multipliers = {
            MishandlingType.DELAYED_RESPONSE: 2.0,
            MishandlingType.WRONG_DEPARTMENT: 4.0,
            MishandlingType.AUTOMATED_REPLY: 1.5,
            MishandlingType.NO_ESCALATION: 6.0,
            MishandlingType.JUNIOR_STAFF: 3.0,
            MishandlingType.GENERIC_TREATMENT: 1.8
        }

        total_delay = base_delay
        for mishandling_type in mishandling_types:
            total_delay *= delay_multipliers.get(mishandling_type, 1.0)

        # VIP tier adjustment (higher tier = worse when delayed)
        tier_multipliers = {
            VIPTier.ROYAL_BLUE: 2.5,
            VIPTier.STRATEGIC: 2.0,
            VIPTier.HIGH_VALUE: 1.5,
            VIPTier.MEDIA_VISIBLE: 3.0  # Media visible customers have highest impact
        }

        total_delay *= tier_multipliers.get(vip_tier, 1.0)

        return min(total_delay, 72.0)  # Cap at 72 hours

    def _calculate_reputation_impact(self, vip_profile: Dict[str, Any], mishandling_types: List[MishandlingType], response_delay: float) -> int:
        """Calculate reputation impact score (0-100)"""
        base_impact = 10

        # Impact from each mishandling type
        impact_scores = {
            MishandlingType.DELAYED_RESPONSE: 15,
            MishandlingType.WRONG_DEPARTMENT: 20,
            MishandlingType.AUTOMATED_REPLY: 25,
            MishandlingType.NO_ESCALATION: 30,
            MishandlingType.JUNIOR_STAFF: 20,
            MishandlingType.GENERIC_TREATMENT: 18
        }

        total_impact = base_impact
        for mishandling_type in mishandling_types:
            total_impact += impact_scores.get(mishandling_type, 10)

        # Response delay impact
        if response_delay > 24:
            total_impact += 20
        elif response_delay > 12:
            total_impact += 15
        elif response_delay > 6:
            total_impact += 10

        # VIP tier impact multiplier
        tier_multipliers = {
            VIPTier.ROYAL_BLUE: 1.8,
            VIPTier.STRATEGIC: 1.5,
            VIPTier.HIGH_VALUE: 1.3,
            VIPTier.MEDIA_VISIBLE: 2.0
        }

        total_impact *= tier_multipliers.get(vip_profile['tier'], 1.0)

        # Annual revenue impact
        if vip_profile['annual_revenue'] > 1000000:
            total_impact *= 1.5

        return min(int(total_impact), 100)

    def _assess_social_media_risk(self, vip_profile: Dict[str, Any], reputation_impact: int) -> bool:
        """Assess risk of social media backlash"""
        base_risk = self.reputation_damage_config.get('social_media_risk', 0.7)

        # Higher risk for media visible and royal customers
        if vip_profile['tier'] == VIPTier.MEDIA_VISIBLE:
            base_risk += 0.2
        elif vip_profile['tier'] == VIPTier.ROYAL_BLUE:
            base_risk += 0.15

        # Higher risk for higher reputation impact
        if reputation_impact > 80:
            base_risk += 0.2
        elif reputation_impact > 60:
            base_risk += 0.1

        return random.random() < base_risk

    def _assess_media_coverage_risk(self, vip_profile: Dict[str, Any], reputation_impact: int) -> bool:
        """Assess risk of media coverage"""
        base_risk = self.reputation_damage_config.get('media_coverage_risk', 0.3)

        # Much higher risk for royal and media visible customers
        if vip_profile['tier'] == VIPTier.ROYAL_BLUE:
            base_risk += 0.4
        elif vip_profile['tier'] == VIPTier.MEDIA_VISIBLE:
            base_risk += 0.3
        elif vip_profile['tier'] == VIPTier.STRATEGIC:
            base_risk += 0.1

        # Higher risk for severe reputation impact
        if reputation_impact > 90:
            base_risk += 0.3
        elif reputation_impact > 75:
            base_risk += 0.2

        return random.random() < base_risk

    def _assess_relationship_damage(self, vip_profile: Dict[str, Any], mishandling_types: List[MishandlingType]) -> str:
        """Assess level of relationship damage"""
        damage_score = len(mishandling_types)

        # Severe mishandling types
        severe_types = {MishandlingType.NO_ESCALATION, MishandlingType.AUTOMATED_REPLY}
        if any(mt in severe_types for mt in mishandling_types):
            damage_score += 2

        # VIP tier sensitivity
        if vip_profile['tier'] == VIPTier.ROYAL_BLUE:
            damage_score += 2
        elif vip_profile['tier'] == VIPTier.MEDIA_VISIBLE:
            damage_score += 1

        if damage_score >= 6:
            return "severe"
        elif damage_score >= 4:
            return "moderate"
        else:
            return "minor"

    def _assess_recovery_difficulty(self, vip_profile: Dict[str, Any], reputation_impact: int) -> str:
        """Assess difficulty of recovering from this incident"""
        difficulty_score = 0

        if reputation_impact > 80:
            difficulty_score += 3
        elif reputation_impact > 60:
            difficulty_score += 2
        elif reputation_impact > 40:
            difficulty_score += 1

        # VIP tier recovery difficulty
        if vip_profile['tier'] == VIPTier.ROYAL_BLUE:
            difficulty_score += 3
        elif vip_profile['tier'] == VIPTier.MEDIA_VISIBLE:
            difficulty_score += 2

        if difficulty_score >= 5:
            return "high"
        elif difficulty_score >= 3:
            return "medium"
        else:
            return "low"

    async def _trigger_cascading_effects(self, incident: VIPIncident, metrics: Dict[str, Any]):
        """Handle cascading effects from severe VIP incidents"""
        logger.critical(f"CASCADING EFFECTS: Severe VIP incident {incident.incident_id}")

        # Severe incidents can trigger:
        # 1. Industry gossip and reputation spread
        if incident.reputation_impact_score > 80:
            await self._trigger_industry_gossip(incident)

        # 2. Media investigation
        if incident.media_coverage_risk:
            await self._trigger_media_investigation(incident)

        # 3. Customer network effects
        if incident.vip_tier in [VIPTier.ROYAL_BLUE, VIPTier.STRATEGIC]:
            await self._trigger_customer_network_effects(incident)

    async def _trigger_industry_gossip(self, incident: VIPIncident):
        """Simulate industry reputation spread"""
        logger.warning(f"INDUSTRY GOSSIP: VIP incident spreading through industry networks")
        # Industry gossip can affect future business opportunities

    async def _trigger_media_investigation(self, incident: VIPIncident):
        """Simulate media investigation"""
        logger.critical(f"MEDIA INVESTIGATION: {incident.customer_name} incident may receive media coverage")
        # Media coverage can amplify reputation damage significantly

    async def _trigger_customer_network_effects(self, incident: VIPIncident):
        """Simulate customer network effects"""
        logger.warning(f"NETWORK EFFECTS: {incident.vip_tier.value} customers may share negative experience")
        # High-tier customers often share experiences with peer networks

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current scenario metrics"""
        if not self.incidents_created:
            return {
                'total_incidents': 0,
                'reputation_damage': 0,
                'social_media_risk': 0,
                'media_coverage_risk': 0,
                'active': self.is_active
            }

        return {
            'total_incidents': len(self.incidents_created),
            'reputation_damage_score': self.reputation_damage_score,
            'social_media_incidents': self.social_media_incidents,
            'media_coverage_incidents': self.media_coverage_incidents,
            'relationship_terminations': self.relationship_terminations,
            'average_response_delay_hours': sum(i.response_delay_hours for i in self.incidents_created) / len(self.incidents_created),
            'active': self.is_active
        }

    def get_kpi_impact(self) -> Dict[str, float]:
        """Calculate KPI degradation caused by VIP mishandling"""
        if not self.incidents_created:
            return {}

        # Reputation score calculation
        baseline_reputation = 95
        reputation_drop = min(60, self.reputation_damage_score / 10)  # Scale down
        current_reputation = max(30, baseline_reputation - reputation_drop)

        # Customer satisfaction for VIP segment
        baseline_vip_satisfaction = 98
        satisfaction_drop = (self.total_incidents * 25) + (self.relationship_terminations * 40)
        vip_satisfaction = max(20, baseline_vip_satisfaction - satisfaction_drop)

        # Market position (VIP customers influence market perception)
        baseline_market_position = 85
        market_position_loss = (self.social_media_incidents * 15) + (self.media_coverage_incidents * 25)
        market_position = max(30, baseline_market_position - market_position_loss)

        # Brand value impact
        baseline_brand_value = 90
        brand_damage = (self.reputation_damage_score / 5) + (self.media_coverage_incidents * 20)
        brand_value = max(25, baseline_brand_value - brand_damage)

        return {
            'reputation_score': current_reputation,
            'vip_customer_satisfaction': vip_satisfaction,
            'market_position_score': market_position,
            'brand_value_score': brand_value,
            'social_media_sentiment': max(20, 80 - (self.social_media_incidents * 30)),
            'industry_standing': max(25, 85 - (self.total_incidents * 15))
        }

    def stop_scenario(self):
        """Stop the running scenario"""
        logger.info("Stopping VIP Handling scenario")
        self.is_active = False

    def reset_scenario(self):
        """Reset scenario to initial state"""
        logger.info("Resetting VIP Handling scenario")
        self.is_active = False
        self.incidents_created = []
        self.total_incidents = 0
        self.reputation_damage_score = 0
        self.social_media_incidents = 0
        self.media_coverage_incidents = 0
        self.relationship_terminations = 0

    def get_detailed_report(self) -> Dict[str, Any]:
        """Generate detailed scenario report"""
        if not self.incidents_created:
            return {'message': 'No VIP incidents recorded yet'}

        # Categorize incidents by tier
        incidents_by_tier = {}
        for incident in self.incidents_created:
            tier = incident.vip_tier.value
            if tier not in incidents_by_tier:
                incidents_by_tier[tier] = []
            incidents_by_tier[tier].append(incident)

        # Calculate financial impact
        annual_revenues = [i.annual_revenue_euro for i in self.incidents_created]
        total_at_risk_revenue = sum(annual_revenues)

        return {
            'scenario_summary': {
                'total_incidents': len(self.incidents_created),
                'reputation_damage_score': self.reputation_damage_score,
                'social_media_incidents': self.social_media_incidents,
                'media_coverage_incidents': self.media_coverage_incidents,
                'relationship_terminations': self.relationship_terminations
            },
            'tier_breakdown': {
                tier: len(incidents) for tier, incidents in incidents_by_tier.items()
            },
            'financial_impact': {
                'at_risk_annual_revenue_euro': total_at_risk_revenue,
                'average_customer_value_euro': sum(annual_revenues) / len(annual_revenues),
                'max_customer_value_euro': max(annual_revenues),
                'estimated_revenue_loss_percent': min(50, self.relationship_terminations * 15)
            },
            'kpi_impact': self.get_kpi_impact(),
            'recovery_analysis': {
                'incidents_requiring_executive_intervention': sum(1 for i in self.incidents_created if i.recovery_difficulty == "high"),
                'estimated_recovery_time_months': max(3, self.total_incidents * 2),
                'reputation_recovery_difficulty': "high" if self.media_coverage_incidents > 0 else "medium"
            }
        }