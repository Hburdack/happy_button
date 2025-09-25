#!/usr/bin/env python3
import os
import signal
import subprocess
import time

# Find and kill the main Flask app
try:
    result = subprocess.run(['pgrep', '-f', 'python app.py'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        pids = result.stdout.strip().split('\n')
        for pid in pids:
            if pid.strip():
                print(f"Killing process {pid}")
                os.kill(int(pid), signal.SIGTERM)

        # Wait for processes to stop
        time.sleep(3)

        # Start new process
        print("Starting new Flask app...")
        subprocess.Popen(['python', 'app.py'], cwd='/home/pi/happy_button')
        print("App restarted!")
    else:
        print("No Flask app process found")

except Exception as e:
    print(f"Error restarting app: {e}")