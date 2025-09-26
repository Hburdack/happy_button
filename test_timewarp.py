#!/usr/bin/env python3
"""
TimeWarp System Test Suite - Happy Buttons Release 2.1
Comprehensive testing of all 5 TimeWarp acceleration levels

Tests:
1. Time acceleration accuracy
2. Email generation scaling
3. Agent processing scaling
4. Weekly cycle functionality
5. Configuration management
6. API endpoint functionality
7. Performance at different speeds
"""

import sys
import time
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeWarpTester:
    """Comprehensive TimeWarp system tester"""

    def __init__(self, base_url="http://localhost:8099"):
        self.base_url = base_url
        self.test_results = {
            'start_time': datetime.now(),
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': {}
        }

    def run_comprehensive_tests(self):
        """Run all TimeWarp tests across 5 acceleration levels"""
        print("🚀 Starting TimeWarp System Comprehensive Test Suite")
        print("=" * 60)

        try:
            # Test 1: System availability and basic functionality
            self.test_system_availability()

            # Test 2: Configuration management
            self.test_configuration_management()

            # Test 3: All 5 speed levels
            for level in range(1, 6):
                self.test_speed_level(level)

            # Test 4: Weekly cycle functionality
            self.test_weekly_cycles()

            # Test 5: Agent processing
            self.test_agent_processing()

            # Test 6: Email generation patterns
            self.test_email_generation()

            # Test 7: Performance benchmarks
            self.test_performance_benchmarks()

        except Exception as e:
            logger.error(f"Test suite error: {e}")
            self.record_test_result("test_suite_error", False, str(e))

        finally:
            self.print_test_summary()

    def test_system_availability(self):
        """Test basic system availability and API endpoints"""
        print("\n📡 Testing System Availability...")

        tests = [
            ("TimeWarp Status", "/api/timewarp/status"),
            ("Agent Status", "/api/timewarp/agents/status"),
            ("Mailbox Config", "/api/timewarp/mailboxes"),
            ("Configuration", "/api/timewarp/config"),
            ("Statistics", "/api/timewarp/statistics")
        ]

        for test_name, endpoint in tests:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                success = response.status_code == 200

                if success:
                    data = response.json()
                    success = data.get('success', False)

                self.record_test_result(f"availability_{test_name.lower().replace(' ', '_')}",
                                      success, f"Status: {response.status_code}")
                print(f"  ✅ {test_name}: {'PASS' if success else 'FAIL'}")

            except Exception as e:
                self.record_test_result(f"availability_{test_name.lower().replace(' ', '_')}",
                                      False, str(e))
                print(f"  ❌ {test_name}: FAIL - {e}")

    def test_configuration_management(self):
        """Test configuration loading and updating"""
        print("\n⚙️ Testing Configuration Management...")

        try:
            # Get current configuration
            response = requests.get(f"{self.base_url}/api/timewarp/config")
            if response.status_code == 200:
                config_data = response.json()
                success = 'configuration' in config_data
                self.record_test_result("config_retrieval", success,
                                      f"Config sections: {list(config_data.get('configuration', {}).keys())}")
                print(f"  ✅ Configuration Retrieval: {'PASS' if success else 'FAIL'}")
            else:
                self.record_test_result("config_retrieval", False, f"HTTP {response.status_code}")
                print(f"  ❌ Configuration Retrieval: FAIL")

            # Test configuration sections
            if 'configuration' in config_data:
                config = config_data['configuration']
                required_sections = ['timewarp', 'agents', 'mailboxes', 'email_patterns']

                for section in required_sections:
                    has_section = section in config
                    self.record_test_result(f"config_section_{section}", has_section,
                                          f"Section present: {has_section}")
                    print(f"  {'✅' if has_section else '❌'} {section.title()} Section: {'PASS' if has_section else 'FAIL'}")

        except Exception as e:
            self.record_test_result("config_management", False, str(e))
            print(f"  ❌ Configuration Management: FAIL - {e}")

    def test_speed_level(self, level: int):
        """Test specific TimeWarp speed level"""
        print(f"\n⚡ Testing TimeWarp Level {level}...")

        try:
            # Set speed level
            response = requests.post(f"{self.base_url}/api/timewarp/set-speed",
                                   json={'level': level}, timeout=10)

            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False) and data.get('level') == level

                self.record_test_result(f"speed_level_{level}_set", success,
                                      f"Multiplier: {data.get('multiplier', 'unknown')}")
                print(f"  {'✅' if success else '❌'} Set Level {level}: {'PASS' if success else 'FAIL'}")

                if success:
                    # Test time acceleration accuracy
                    self.test_time_acceleration_accuracy(level, data.get('multiplier', 1))

            else:
                self.record_test_result(f"speed_level_{level}_set", False, f"HTTP {response.status_code}")
                print(f"  ❌ Set Level {level}: FAIL - HTTP {response.status_code}")

        except Exception as e:
            self.record_test_result(f"speed_level_{level}", False, str(e))
            print(f"  ❌ Speed Level {level}: FAIL - {e}")

    def test_time_acceleration_accuracy(self, level: int, expected_multiplier: int):
        """Test time acceleration accuracy for a specific level"""
        print(f"    🕐 Testing time acceleration accuracy (Level {level})...")

        try:
            # Start TimeWarp
            requests.post(f"{self.base_url}/api/timewarp/start")

            # Record start time and get initial status
            real_start = time.time()
            response = requests.get(f"{self.base_url}/api/timewarp/status")
            initial_status = response.json()
            initial_sim_time = datetime.fromisoformat(initial_status['status']['simulation_time'])

            # Wait for 5 seconds real time
            time.sleep(5)

            # Get final status
            response = requests.get(f"{self.base_url}/api/timewarp/status")
            final_status = response.json()
            final_sim_time = datetime.fromisoformat(final_status['status']['simulation_time'])

            # Calculate actual vs expected acceleration
            real_elapsed = time.time() - real_start
            sim_elapsed = (final_sim_time - initial_sim_time).total_seconds()
            actual_multiplier = sim_elapsed / real_elapsed if real_elapsed > 0 else 0

            # Check accuracy (allow 10% tolerance)
            accuracy_threshold = 0.1
            multiplier_diff = abs(actual_multiplier - expected_multiplier) / expected_multiplier
            success = multiplier_diff <= accuracy_threshold

            self.record_test_result(f"speed_level_{level}_accuracy", success,
                                  f"Expected: {expected_multiplier}x, Actual: {actual_multiplier:.1f}x, Diff: {multiplier_diff:.1%}")
            print(f"    {'✅' if success else '❌'} Acceleration Accuracy: {'PASS' if success else 'FAIL'} "
                  f"({actual_multiplier:.1f}x vs {expected_multiplier}x)")

            # Pause TimeWarp after test
            requests.post(f"{self.base_url}/api/timewarp/pause")

        except Exception as e:
            self.record_test_result(f"speed_level_{level}_accuracy", False, str(e))
            print(f"    ❌ Acceleration Accuracy: FAIL - {e}")

    def test_weekly_cycles(self):
        """Test weekly cycle functionality"""
        print("\n📅 Testing Weekly Cycle Functionality...")

        try:
            # Set to maximum speed for faster testing
            requests.post(f"{self.base_url}/api/timewarp/set-speed", json={'level': 5})

            # Reset and start TimeWarp
            requests.post(f"{self.base_url}/api/timewarp/reset")
            requests.post(f"{self.base_url}/api/timewarp/start")

            # Get initial week info
            response = requests.get(f"{self.base_url}/api/timewarp/status")
            initial_status = response.json()
            initial_week_progress = initial_status['status'].get('week_progress', 0)

            print(f"    Initial week progress: {initial_week_progress:.1f}%")

            # Wait for some time to see progress
            time.sleep(10)

            # Get final week info
            response = requests.get(f"{self.base_url}/api/timewarp/status")
            final_status = response.json()
            final_week_progress = final_status['status'].get('week_progress', 0)

            print(f"    Final week progress: {final_week_progress:.1f}%")

            # Check if progress advanced
            progress_advanced = final_week_progress > initial_week_progress
            self.record_test_result("weekly_cycle_progress", progress_advanced,
                                  f"Progress: {initial_week_progress:.1f}% -> {final_week_progress:.1f}%")
            print(f"  {'✅' if progress_advanced else '❌'} Week Progress: {'PASS' if progress_advanced else 'FAIL'}")

            # Test day of week tracking
            day_of_week = final_status['status'].get('day_of_week', 'Unknown')
            has_day_info = day_of_week != 'Unknown'
            self.record_test_result("weekly_cycle_day_tracking", has_day_info, f"Day: {day_of_week}")
            print(f"  {'✅' if has_day_info else '❌'} Day Tracking: {'PASS' if has_day_info else 'FAIL'} ({day_of_week})")

            # Pause TimeWarp
            requests.post(f"{self.base_url}/api/timewarp/pause")

        except Exception as e:
            self.record_test_result("weekly_cycles", False, str(e))
            print(f"  ❌ Weekly Cycles: FAIL - {e}")

    def test_agent_processing(self):
        """Test agent processing functionality"""
        print("\n🤖 Testing Agent Processing...")

        try:
            # Get agent status
            response = requests.get(f"{self.base_url}/api/timewarp/agents/status")
            if response.status_code == 200:
                data = response.json()
                success = 'agents' in data and len(data['agents']) > 0

                self.record_test_result("agent_status_retrieval", success,
                                      f"Agents found: {len(data.get('agents', {}))}")
                print(f"  {'✅' if success else '❌'} Agent Status Retrieval: {'PASS' if success else 'FAIL'}")

                if success:
                    # Check individual agent configurations
                    agents = data['agents']
                    for agent_id, agent_info in agents.items():
                        has_config = agent_info.get('configuration') is not None
                        is_active = agent_info.get('is_active', False)

                        self.record_test_result(f"agent_{agent_id}_config", has_config,
                                              f"Active: {is_active}, Config: {has_config}")
                        print(f"    {'✅' if has_config else '❌'} Agent {agent_id}: "
                              f"{'PASS' if has_config else 'FAIL'} (Active: {is_active})")

            else:
                self.record_test_result("agent_processing", False, f"HTTP {response.status_code}")
                print(f"  ❌ Agent Processing: FAIL - HTTP {response.status_code}")

        except Exception as e:
            self.record_test_result("agent_processing", False, str(e))
            print(f"  ❌ Agent Processing: FAIL - {e}")

    def test_email_generation(self):
        """Test email generation patterns"""
        print("\n📧 Testing Email Generation...")

        try:
            # Set to fast speed for email generation
            requests.post(f"{self.base_url}/api/timewarp/set-speed", json={'level': 3})
            requests.post(f"{self.base_url}/api/timewarp/start")

            # Get initial statistics
            response = requests.get(f"{self.base_url}/api/timewarp/statistics")
            initial_stats = response.json()
            initial_emails = initial_stats['statistics']['email_generation'].get('total_generated', 0)

            print(f"    Initial emails generated: {initial_emails}")

            # Wait for email generation
            time.sleep(15)

            # Get final statistics
            response = requests.get(f"{self.base_url}/api/timewarp/statistics")
            final_stats = response.json()
            final_emails = final_stats['statistics']['email_generation'].get('total_generated', 0)

            print(f"    Final emails generated: {final_emails}")

            # Check if emails were generated
            emails_generated = final_emails > initial_emails
            self.record_test_result("email_generation", emails_generated,
                                  f"Emails: {initial_emails} -> {final_emails}")
            print(f"  {'✅' if emails_generated else '❌'} Email Generation: {'PASS' if emails_generated else 'FAIL'}")

            # Test email patterns
            if 'email_generation' in final_stats['statistics']:
                email_stats = final_stats['statistics']['email_generation']
                has_patterns = email_stats.get('current_speed_level', 0) > 0
                self.record_test_result("email_patterns", has_patterns,
                                      f"Speed level: {email_stats.get('current_speed_level', 0)}")
                print(f"  {'✅' if has_patterns else '❌'} Email Patterns: {'PASS' if has_patterns else 'FAIL'}")

            requests.post(f"{self.base_url}/api/timewarp/pause")

        except Exception as e:
            self.record_test_result("email_generation", False, str(e))
            print(f"  ❌ Email Generation: FAIL - {e}")

    def test_performance_benchmarks(self):
        """Test performance at different speed levels"""
        print("\n⚡ Testing Performance Benchmarks...")

        performance_results = {}

        for level in [1, 3, 5]:  # Test key speed levels
            try:
                print(f"    Testing performance at Level {level}...")

                # Set speed level
                requests.post(f"{self.base_url}/api/timewarp/set-speed", json={'level': level})

                # Start timing
                start_time = time.time()

                # Start TimeWarp
                requests.post(f"{self.base_url}/api/timewarp/start")

                # Wait and measure
                time.sleep(5)

                # Get statistics
                response = requests.get(f"{self.base_url}/api/timewarp/statistics")
                end_time = time.time()

                if response.status_code == 200:
                    response_time = end_time - start_time
                    stats = response.json()

                    performance_results[level] = {
                        'response_time': response_time,
                        'success': True,
                        'stats_available': 'statistics' in stats
                    }

                    print(f"      Level {level}: {response_time:.2f}s response time")
                else:
                    performance_results[level] = {
                        'response_time': 999,
                        'success': False,
                        'stats_available': False
                    }

                requests.post(f"{self.base_url}/api/timewarp/pause")

            except Exception as e:
                performance_results[level] = {
                    'response_time': 999,
                    'success': False,
                    'error': str(e)
                }

        # Analyze performance results
        successful_tests = sum(1 for result in performance_results.values() if result['success'])
        performance_acceptable = successful_tests >= 2

        self.record_test_result("performance_benchmarks", performance_acceptable,
                              f"Successful tests: {successful_tests}/3")
        print(f"  {'✅' if performance_acceptable else '❌'} Performance Benchmarks: "
              f"{'PASS' if performance_acceptable else 'FAIL'} ({successful_tests}/3 successful)")

    def record_test_result(self, test_name: str, success: bool, details: str = ""):
        """Record test result"""
        if success:
            self.test_results['tests_passed'] += 1
        else:
            self.test_results['tests_failed'] += 1

        self.test_results['test_details'][test_name] = {
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

    def print_test_summary(self):
        """Print comprehensive test summary"""
        end_time = datetime.now()
        duration = end_time - self.test_results['start_time']

        print("\n" + "=" * 60)
        print("🏁 TIMEWARP SYSTEM TEST SUMMARY")
        print("=" * 60)

        total_tests = self.test_results['tests_passed'] + self.test_results['tests_failed']
        pass_rate = (self.test_results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0

        print(f"📊 Total Tests Run: {total_tests}")
        print(f"✅ Tests Passed: {self.test_results['tests_passed']}")
        print(f"❌ Tests Failed: {self.test_results['tests_failed']}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        print(f"⏱️ Duration: {duration.total_seconds():.1f} seconds")

        # Overall system status
        if pass_rate >= 90:
            status = "🟢 EXCELLENT"
        elif pass_rate >= 75:
            status = "🟡 GOOD"
        elif pass_rate >= 50:
            status = "🟠 NEEDS ATTENTION"
        else:
            status = "🔴 CRITICAL ISSUES"

        print(f"🎯 Overall Status: {status}")

        # Save detailed results
        results_file = f"timewarp_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            print(f"📄 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️ Could not save results file: {e}")

        print("=" * 60)

        # Print failed tests for debugging
        failed_tests = [name for name, result in self.test_results['test_details'].items()
                       if not result['success']]
        if failed_tests:
            print("\n❌ Failed Tests Details:")
            for test_name in failed_tests:
                details = self.test_results['test_details'][test_name]
                print(f"  • {test_name}: {details.get('details', 'No details')}")

def main():
    """Run TimeWarp test suite"""
    print("Happy Buttons Release 2.1 - TimeWarp System Test Suite")
    print("Testing all 5 acceleration levels and system functionality")
    print()

    # Check if application is running
    try:
        response = requests.get("http://localhost:8099", timeout=5)
        if response.status_code != 200:
            print("❌ Application not accessible at http://localhost:8099")
            print("Please start the application with: python app.py")
            return 1
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to application at http://localhost:8099")
        print("Please start the application with: python app.py")
        return 1

    # Run tests
    tester = TimeWarpTester()
    tester.run_comprehensive_tests()

    # Return exit code based on results
    if tester.test_results['tests_failed'] == 0:
        return 0  # All tests passed
    elif tester.test_results['tests_passed'] > tester.test_results['tests_failed']:
        return 1  # More tests passed than failed
    else:
        return 2  # More tests failed than passed

if __name__ == "__main__":
    exit(main())