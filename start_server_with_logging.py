#!/usr/bin/env python3
"""
Start Django server with enhanced logging
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def clear_logs():
    """Clear existing log files"""
    log_files = ['server.log', 'error.log']
    for log_file in log_files:
        if os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write(f"# Log file cleared at {datetime.now().isoformat()}\n")
            print(f"✅ Cleared {log_file}")

def start_server():
    """Start the Django development server"""
    print("🚀 Starting Django Server with Enhanced Logging")
    print("=" * 50)
    
    # Clear existing logs
    clear_logs()
    
    # Start the server
    try:
        print(f"📅 Server started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🌐 Server URL: http://0.0.0.0:8000")
        print("📁 Log file: server.log")
        print("📁 Error log: error.log")
        print("=" * 50)
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Start Django server
        subprocess.run([
            sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        print(f"⏰ Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    start_server()
