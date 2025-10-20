#!/usr/bin/env python3
"""
Real-time log monitoring script for Django server
"""

import os
import time
import subprocess
import sys
from datetime import datetime

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the monitoring header"""
    print("=" * 80)
    print("🖥️  DJANGO SERVER LOG MONITOR - REAL-TIME")
    print("=" * 80)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Log file: server.log")
    print(f"📁 Error log: error.log")
    print("=" * 80)
    print("Press Ctrl+C to stop monitoring")
    print("=" * 80)

def monitor_log_file(log_file, last_position=0):
    """
    Monitor a log file for new entries
    Args:
        log_file: Path to the log file
        last_position: Last read position in the file
    Returns:
        tuple: (new_position, new_lines)
    """
    try:
        if not os.path.exists(log_file):
            return last_position, []
        
        with open(log_file, 'r', encoding='utf-8') as f:
            f.seek(last_position)
            new_lines = f.readlines()
            new_position = f.tell()
        
        return new_position, new_lines
    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        return last_position, []

def format_log_line(line, log_type="INFO"):
    """
    Format a log line for display
    Args:
        line: Raw log line
        log_type: Type of log (INFO, ERROR, etc.)
    Returns:
        str: Formatted log line
    """
    line = line.strip()
    if not line:
        return ""
    
    # Color coding based on log level
    if "ERROR" in line:
        return f"🔴 {line}"
    elif "WARNING" in line or "WARN" in line:
        return f"🟡 {line}"
    elif "DEBUG" in line:
        return f"🔵 {line}"
    elif "INFO" in line:
        return f"🟢 {line}"
    else:
        return f"⚪ {line}"

def show_log_stats():
    """Show log file statistics"""
    try:
        server_log_size = os.path.getsize('server.log') if os.path.exists('server.log') else 0
        error_log_size = os.path.getsize('error.log') if os.path.exists('error.log') else 0
        
        print(f"\n📊 LOG STATISTICS:")
        print(f"   Server log size: {server_log_size:,} bytes")
        print(f"   Error log size: {error_log_size:,} bytes")
        print(f"   Last updated: {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"❌ Error getting log stats: {e}")

def main():
    """Main monitoring function"""
    clear_screen()
    print_header()
    
    # Initialize file positions
    server_log_position = 0
    error_log_position = 0
    
    # Get initial file sizes
    if os.path.exists('server.log'):
        server_log_position = os.path.getsize('server.log')
    if os.path.exists('error.log'):
        error_log_position = os.path.getsize('error.log')
    
    line_count = 0
    last_stats_time = time.time()
    
    try:
        while True:
            # Monitor server.log
            server_log_position, server_lines = monitor_log_file('server.log', server_log_position)
            for line in server_lines:
                if line.strip():
                    formatted_line = format_log_line(line, "INFO")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {formatted_line}")
                    line_count += 1
            
            # Monitor error.log
            error_log_position, error_lines = monitor_log_file('error.log', error_log_position)
            for line in error_lines:
                if line.strip():
                    formatted_line = format_log_line(line, "ERROR")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {formatted_line}")
                    line_count += 1
            
            # Show stats every 30 seconds
            current_time = time.time()
            if current_time - last_stats_time >= 30:
                show_log_stats()
                last_stats_time = current_time
            
            # Sleep for a short interval
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Monitoring stopped by user")
        print(f"📊 Total lines processed: {line_count}")
        print(f"⏰ Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error in monitoring: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
