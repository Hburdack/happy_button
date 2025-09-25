#!/bin/bash
"""
Setup Cron Jobs for Happy Buttons Daily Order Generation
Automates the wiederholbares Tagesskript (repeatable daily script)
"""

echo "🕐 Setting up Happy Buttons Cron Jobs"
echo "====================================="

# Create cron directory if it doesn't exist
mkdir -p /home/pi/happy_button/cron

# Create the cron job script
cat > /home/pi/happy_button/cron/daily_orders.sh << 'EOF'
#!/bin/bash
# Daily Order Generation Cron Job
# Runs every day at 6 AM to generate new orders

cd /home/pi/happy_button

# Set Python path
export PYTHONPATH=/home/pi/happy_button/src:$PYTHONPATH

# Run daily order generation
python3 daily_order_script.py >> logs/cron_daily_$(date +%Y%m%d).log 2>&1

# Optional: Clean up old logs (keep last 30 days)
find logs/ -name "cron_daily_*.log" -mtime +30 -delete 2>/dev/null || true

# Optional: Clean up old event files
python3 daily_order_script.py --cleanup >> logs/cron_cleanup_$(date +%Y%m%d).log 2>&1

echo "$(date): Daily order generation completed" >> logs/cron_status.log
EOF

# Make the script executable
chmod +x /home/pi/happy_button/cron/daily_orders.sh

# Create the cron entry
CRON_JOB="0 6 * * * /home/pi/happy_button/cron/daily_orders.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "daily_orders.sh"; then
    echo "⚠️  Cron job already exists"
    echo "Current crontab:"
    crontab -l | grep daily_orders.sh
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Added cron job: $CRON_JOB"
fi

# Create alternative: weekly historical seeding (Sundays at 2 AM)
WEEKLY_CRON_JOB="0 2 * * 0 cd /home/pi/happy_button && python3 daily_order_script.py --seed-history >> logs/weekly_seed_\$(date +\%Y\%m\%d).log 2>&1"

echo ""
echo "📋 CRON SETUP COMPLETE"
echo "====================="
echo "Daily Orders: Every day at 6:00 AM"
echo "   Command: /home/pi/happy_button/cron/daily_orders.sh"
echo "   Logs: logs/cron_daily_YYYYMMDD.log"
echo ""
echo "Optional Weekly Seeding:"
echo "   To add weekly re-seeding, run:"
echo "   (crontab -l; echo \"$WEEKLY_CRON_JOB\") | crontab -"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To edit cron jobs: crontab -e"
echo "To remove cron jobs: crontab -r"
echo ""
echo "✅ Automation setup complete!"