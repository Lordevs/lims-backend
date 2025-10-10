#!/usr/bin/env python3
"""
Log viewer with filtering and search capabilities
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

def read_log_file(log_file, lines=None, filter_level=None, search_term=None):
    """
    Read and filter log file
    Args:
        log_file: Path to log file
        lines: Number of lines to read (from end)
        filter_level: Log level to filter (INFO, ERROR, WARNING, DEBUG)
        search_term: Search term to filter by
    """
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        # Filter by log level
        if filter_level:
            all_lines = [line for line in all_lines if filter_level.upper() in line.upper()]
        
        # Filter by search term
        if search_term:
            all_lines = [line for line in all_lines if search_term.lower() in line.lower()]
        
        # Get last N lines
        if lines:
            all_lines = all_lines[-lines:]
        
        return all_lines
    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        return []

def format_log_line(line, show_timestamp=True, show_level=True):
    """
    Format a log line for display
    """
    line = line.strip()
    if not line:
        return ""
    
    # Color coding
    if "ERROR" in line:
        color = "🔴"
    elif "WARNING" in line or "WARN" in line:
        color = "🟡"
    elif "DEBUG" in line:
        color = "🔵"
    elif "INFO" in line:
        color = "🟢"
    else:
        color = "⚪"
    
    return f"{color} {line}"

def show_log_stats(log_file):
    """Show log file statistics"""
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        return
    
    try:
        file_size = os.path.getsize(log_file)
        mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Count log levels
        error_count = sum(1 for line in lines if "ERROR" in line)
        warning_count = sum(1 for line in lines if "WARNING" in line or "WARN" in line)
        info_count = sum(1 for line in lines if "INFO" in line)
        debug_count = sum(1 for line in lines if "DEBUG" in line)
        
        print(f"\n📊 LOG STATISTICS: {log_file}")
        print("=" * 50)
        print(f"📁 File size: {file_size:,} bytes")
        print(f"📅 Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📄 Total lines: {len(lines):,}")
        print(f"🔴 Errors: {error_count}")
        print(f"🟡 Warnings: {warning_count}")
        print(f"🟢 Info: {info_count}")
        print(f"🔵 Debug: {debug_count}")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error getting log stats: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Django Log Viewer')
    parser.add_argument('--file', '-f', default='server.log', help='Log file to view (default: server.log)')
    parser.add_argument('--lines', '-n', type=int, help='Number of lines to show (from end)')
    parser.add_argument('--level', '-l', choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'], help='Filter by log level')
    parser.add_argument('--search', '-s', help='Search term to filter by')
    parser.add_argument('--stats', action='store_true', help='Show log statistics')
    parser.add_argument('--tail', '-t', type=int, help='Show last N lines and follow (like tail -f)')
    
    args = parser.parse_args()
    
    if args.stats:
        show_log_stats(args.file)
        return
    
    if args.tail:
        print(f"📖 Following last {args.tail} lines of {args.file}")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        try:
            import time
            last_position = 0
            if os.path.exists(args.file):
                last_position = os.path.getsize(args.file)
                # Read last N lines
                with open(args.file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-args.tail:]:
                        print(format_log_line(line))
            
            while True:
                with open(args.file, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    last_position = f.tell()
                    
                    for line in new_lines:
                        if line.strip():
                            print(format_log_line(line))
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopped following logs")
        except Exception as e:
            print(f"❌ Error following logs: {e}")
        return
    
    # Read and display logs
    lines = read_log_file(args.file, args.lines, args.level, args.search)
    
    if not lines:
        print("📭 No log entries found")
        return
    
    print(f"📖 Showing {len(lines)} log entries from {args.file}")
    if args.level:
        print(f"🔍 Filtered by level: {args.level}")
    if args.search:
        print(f"🔍 Filtered by search: {args.search}")
    print("=" * 50)
    
    for line in lines:
        print(format_log_line(line))

if __name__ == "__main__":
    main()
