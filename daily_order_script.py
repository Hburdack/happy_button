#!/usr/bin/env python3
"""
Wiederholbares Tagesskript (Repeatable Daily Script)
Happy Buttons Release 2 - Daily Order Generation

This script can be run daily to generate realistic new orders
and maintain continuous business simulation data.

Usage:
  python daily_order_script.py                    # Generate orders for today
  python daily_order_script.py --date 2025-01-15  # Generate for specific date
  python daily_order_script.py --seed-history     # Generate 30-day historical data
  python daily_order_script.py --stats            # Show current system statistics
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, '/home/pi/happy_button/src')

from services.history.history_seeder import HistorySeeder, DailyOrderGenerator
from services.order.state_machine import OrderStateMachine

def setup_logging():
    """Setup logging for daily script"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = f"{log_dir}/daily_orders_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def generate_daily_orders(target_date: datetime = None):
    """Generate orders for a specific day"""
    logger = logging.getLogger(__name__)

    if target_date is None:
        target_date = datetime.now()

    logger.info(f"🏭 DAILY ORDER GENERATION - {target_date.strftime('%Y-%m-%d')}")
    logger.info("=" * 60)

    try:
        daily_gen = DailyOrderGenerator()
        result = daily_gen.generate_daily_orders(target_date)

        logger.info(f"✅ Successfully generated {result['orders_generated']} orders")
        logger.info(f"💰 Total value: €{result['total_value']:,.2f}")
        logger.info("📋 Orders created:")

        for order in result['orders']:
            logger.info(f"  • {order['order_id']}: {order['customer']} - €{order['value']:,.2f} (P{order['priority']})")

        return result

    except Exception as e:
        logger.error(f"❌ Error generating daily orders: {e}")
        return None

def seed_historical_data():
    """Generate 30-day historical simulation data"""
    logger = logging.getLogger(__name__)

    logger.info("🌱 HISTORICAL DATA SEEDING")
    logger.info("=" * 60)

    try:
        seeder = HistorySeeder()
        stats = seeder.seed_historical_data()

        logger.info("🎯 SEEDING COMPLETE!")
        logger.info(f"📈 Total Orders: {stats['total_orders']}")
        logger.info(f"💰 Total Revenue: €{stats['total_value']:,.2f}")
        logger.info(f"🏭 Completion Rate: {(stats['completed_orders']/stats['total_orders']*100):.1f}%")
        logger.info(f"📊 Orders by State: {stats['orders_by_state']}")

        return stats

    except Exception as e:
        logger.error(f"❌ Error seeding historical data: {e}")
        return None

def show_system_statistics():
    """Show current system statistics"""
    logger = logging.getLogger(__name__)

    logger.info("📊 SYSTEM STATISTICS")
    logger.info("=" * 40)

    try:
        state_machine = OrderStateMachine("src/sim/config/company_release2.yaml")
        state_machine.load_orders()

        stats = state_machine.get_order_statistics()
        overdue_orders = state_machine.get_overdue_orders()

        logger.info(f"📈 Total Orders: {stats['total_orders']}")
        logger.info(f"💰 Total Value: €{stats['total_value']:,.2f}")
        logger.info(f"⏰ Avg Processing Time: {stats['avg_processing_time']:.2f} hours")
        logger.info(f"🚨 Overdue Orders: {len(overdue_orders)}")

        logger.info("\n📋 Orders by State:")
        for state, count in stats['by_state'].items():
            if count > 0:
                logger.info(f"  • {state}: {count}")

        logger.info("\n🏷️ Orders by Priority:")
        for priority, count in stats['by_priority'].items():
            if count > 0:
                logger.info(f"  • Priority {priority}: {count}")

        if overdue_orders:
            logger.info("\n⚠️ OVERDUE ORDERS:")
            for order in overdue_orders[:5]:  # Show first 5
                hours_overdue = (datetime.now().timestamp() - order.created_at) / 3600
                logger.info(f"  • {order.id}: {order.customer_name} - {hours_overdue:.1f}h overdue")

        return stats

    except Exception as e:
        logger.error(f"❌ Error getting statistics: {e}")
        return None

def cleanup_old_events():
    """Clean up old event files (older than 30 days)"""
    logger = logging.getLogger(__name__)

    try:
        events_dir = "data/events"
        if not os.path.exists(events_dir):
            return

        cutoff_time = datetime.now() - timedelta(days=30)
        cutoff_timestamp = cutoff_time.timestamp()

        cleaned_count = 0
        for filename in os.listdir(events_dir):
            if filename.startswith("order_event_") and filename.endswith(".json"):
                try:
                    timestamp_str = filename.replace("order_event_", "").replace(".json", "")
                    file_timestamp = float(timestamp_str)

                    if file_timestamp < cutoff_timestamp:
                        os.remove(os.path.join(events_dir, filename))
                        cleaned_count += 1

                except (ValueError, OSError):
                    continue  # Skip files with invalid timestamps

        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} old event files")

    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")

def main():
    """Main script entry point"""
    parser = argparse.ArgumentParser(description="Happy Buttons Daily Order Script")
    parser.add_argument('--date', type=str, help='Generate orders for specific date (YYYY-MM-DD)')
    parser.add_argument('--seed-history', action='store_true', help='Generate 30-day historical data')
    parser.add_argument('--stats', action='store_true', help='Show current system statistics')
    parser.add_argument('--cleanup', action='store_true', help='Clean up old event files')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("🚀 HAPPY BUTTONS DAILY SCRIPT STARTED")
    logger.info(f"⏰ Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Handle different script modes
        if args.seed_history:
            result = seed_historical_data()
            if result:
                logger.info("✅ Historical data seeding completed successfully")
            else:
                logger.error("❌ Historical data seeding failed")
                sys.exit(1)

        elif args.stats:
            result = show_system_statistics()
            if result is None:
                logger.error("❌ Failed to retrieve statistics")
                sys.exit(1)

        else:
            # Generate daily orders
            target_date = None
            if args.date:
                try:
                    target_date = datetime.strptime(args.date, '%Y-%m-%d')
                except ValueError:
                    logger.error("❌ Invalid date format. Use YYYY-MM-DD")
                    sys.exit(1)

            result = generate_daily_orders(target_date)
            if result:
                logger.info("✅ Daily order generation completed successfully")
            else:
                logger.error("❌ Daily order generation failed")
                sys.exit(1)

        # Optional cleanup
        if args.cleanup:
            cleanup_old_events()

        logger.info("🎯 SCRIPT EXECUTION COMPLETED")

    except KeyboardInterrupt:
        logger.info("⚠️ Script interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()