#!/usr/bin/env python3
"""
Test script for scenario email integration
Verifies that scenario emails are generated and saved properly
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scenarios.late_triage import LateTriage
from scenarios.missed_expedite import MissedExpedite
from scenarios.vip_handling import VIPHandling
from scenarios.global_disruption import GlobalDisruption
from scenarios.email_generator import scenario_email_generator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_late_triage_emails():
    """Test email generation in Late Triage scenario"""
    print("\n🧪 Testing Late Triage email generation...")

    config = {
        'configuration': {
            'delay_range': {'min_minutes': 60, 'max_minutes': 300},
            'sla_targets': {'customer_inquiry': 60, 'complaint': 30},
            'escalation': {'escalation_threshold': 120}
        }
    }

    scenario = LateTriage(config)

    # Run scenario for a short duration to generate some emails
    try:
        metrics = await scenario.execute_scenario(duration_seconds=10)
        print(f"✅ Late Triage: Generated {metrics.get('total_emails_delayed', 0)} delayed emails")
        return True
    except Exception as e:
        print(f"❌ Late Triage failed: {e}")
        return False

async def test_missed_expedite_emails():
    """Test email generation in Missed Expedite scenario"""
    print("\n🧪 Testing Missed Expedite email generation...")

    config = {
        'configuration': {
            'expedite_keywords': ['urgent', 'expedite', 'rush'],
            'opportunity_values': {'min_euro': 5000, 'max_euro': 50000, 'profit_multiplier': 10},
            'customer_response': {'competitor_switch_rate': 0.4, 'negative_reviews': 0.6},
            'miss_rate': 0.75,
            'detection_delay': 180
        }
    }

    scenario = MissedExpedite(config)

    try:
        metrics = await scenario.execute_scenario(duration_seconds=10)
        print(f"✅ Missed Expedite: Generated {metrics.get('total_opportunities', 0)} opportunity emails")
        return True
    except Exception as e:
        print(f"❌ Missed Expedite failed: {e}")
        return False

async def test_vip_handling_emails():
    """Test email generation in VIP Handling scenario"""
    print("\n🧪 Testing VIP Handling email generation...")

    config = {
        'configuration': {
            'vip_criteria': {'min_annual_value': 100000},
            'vip_indicators': ['royal', 'premium', 'strategic'],
            'mishandling_types': {},
            'reputation_damage': {}
        }
    }

    scenario = VIPHandling(config)

    try:
        metrics = await scenario.execute_scenario(duration_seconds=10)
        print(f"✅ VIP Handling: Generated {metrics.get('total_vip_incidents', 0)} VIP incident emails")
        return True
    except Exception as e:
        print(f"❌ VIP Handling failed: {e}")
        return False

async def test_global_disruption_emails():
    """Test email generation in Global Disruption scenario"""
    print("\n🧪 Testing Global Disruption email generation...")

    config = {
        'configuration': {
            'disruption_types': {
                'suez_canal_blockage': {'enabled': True, 'delay_multiplier': 3.5}
            },
            'supply_routes': {},
            'impact_calculation': {}
        }
    }

    scenario = GlobalDisruption(config)

    try:
        metrics = await scenario.execute_scenario(duration_seconds=10)
        print(f"✅ Global Disruption: Generated {metrics.get('total_orders_affected', 0)} affected order emails")
        return True
    except Exception as e:
        print(f"❌ Global Disruption failed: {e}")
        return False

def verify_generated_emails():
    """Verify that emails were actually generated and saved"""
    print("\n📧 Verifying generated emails...")

    emails_dir = Path("data/scenario_emails")
    if not emails_dir.exists():
        print("❌ Scenario emails directory does not exist")
        return False

    email_files = list(emails_dir.glob("*.json"))
    print(f"📄 Found {len(email_files)} scenario email files")

    if len(email_files) == 0:
        print("⚠️  No scenario emails were generated")
        return False

    # Display some sample emails
    for i, email_file in enumerate(email_files[:3]):  # Show first 3 emails
        try:
            import json
            with open(email_file, 'r', encoding='utf-8') as f:
                email = json.load(f)

            print(f"\n📩 Sample Email {i+1}:")
            print(f"  Type: {email.get('scenario_type', 'unknown')}/{email.get('email_type', 'unknown')}")
            print(f"  Subject: {email.get('subject', 'No subject')[:60]}...")
            print(f"  From: {email.get('from', 'unknown')}")
            print(f"  Urgency: {email.get('urgency', 'unknown')}")
            print(f"  File: {email_file.name}")

        except Exception as e:
            print(f"❌ Error reading email file {email_file}: {e}")

    return True

async def run_integration_test():
    """Run the complete integration test"""
    print("🚀 Starting Scenario Email Integration Test")
    print("=" * 60)

    # Test each scenario
    results = []
    results.append(await test_late_triage_emails())
    results.append(await test_missed_expedite_emails())
    results.append(await test_vip_handling_emails())
    results.append(await test_global_disruption_emails())

    # Verify generated emails
    email_verification = verify_generated_emails()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"  Late Triage: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"  Missed Expedite: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"  VIP Handling: {'✅ PASS' if results[2] else '❌ FAIL'}")
    print(f"  Global Disruption: {'✅ PASS' if results[3] else '❌ FAIL'}")
    print(f"  Email Verification: {'✅ PASS' if email_verification else '❌ FAIL'}")

    total_passed = sum(results) + (1 if email_verification else 0)
    total_tests = len(results) + 1

    print(f"\n🏆 Overall Result: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("🎉 All tests passed! Scenario email integration is working correctly.")
        print("\n💡 Next steps:")
        print("  1. Scenario emails are being saved to data/scenario_emails/")
        print("  2. These emails should be visible in your email system interfaces")
        print("  3. Run actual scenarios to see emails generated in real-time")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")

    return total_passed == total_tests

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs("data/scenario_emails", exist_ok=True)

    # Run the test
    success = asyncio.run(run_integration_test())

    # Exit with appropriate code
    sys.exit(0 if success else 1)