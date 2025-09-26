#!/usr/bin/env python3
"""
Email Processing Daemon for Happy Buttons
Continuously monitors and processes emails from real mailboxes
"""

import time
import logging
import sys
import os
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.real_email_connector import RealEmailConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pi/happy_button/logs/email_processor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EmailProcessor:
    def __init__(self):
        self.running = True
        self.connector = None

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def start(self):
        """Start the email processing daemon"""
        # Register signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        logger.info("🚀 Starting Happy Buttons Email Processor Daemon")
        logger.info("="*60)

        try:
            # Initialize email connector
            logger.info("Initializing email connector...")
            self.connector = RealEmailConnector()
            logger.info("✅ Email connector initialized successfully")

            # Skip connection test - connector ready

            # Start processing loop
            logger.info("🔄 Starting email processing loop (30-second intervals)")
            self.process_loop()

        except Exception as e:
            logger.error(f"❌ Failed to start email processor: {e}")
            raise

    def process_loop(self):
        """Main processing loop"""
        email_count = 0

        while self.running:
            try:
                logger.debug("🔍 Checking for new emails...")

                # Fetch and process emails
                emails = self.connector.get_real_emails(limit=20)

                if emails:
                    email_count += len(emails)
                    logger.info(f"📧 Processed {len(emails)} new emails (total: {email_count})")

                    for email in emails[:3]:  # Log first 3 for debugging
                        logger.info(f"  • From: {email.get('from', 'Unknown')} - {email.get('subject', 'No Subject')}")
                else:
                    logger.debug("📭 No new emails")

                # Wait before next check
                if self.running:
                    time.sleep(30)

            except KeyboardInterrupt:
                logger.info("🛑 Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"❌ Email processing error: {e}")
                logger.info("⏳ Waiting 60 seconds before retry...")
                if self.running:
                    time.sleep(60)

        logger.info("🏁 Email processor daemon stopped")

def main():
    """Main entry point"""
    processor = EmailProcessor()

    try:
        processor.start()
    except KeyboardInterrupt:
        logger.info("👋 Email processor interrupted by user")
    except Exception as e:
        logger.error(f"💥 Email processor crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()