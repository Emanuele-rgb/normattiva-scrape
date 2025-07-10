#!/usr/bin/env python3
"""
Monitor progress of the comprehensive historical database population
Run this script periodically to check progress during the overnight run
"""

import os
import glob
import sqlite3
from datetime import datetime
import time

def get_latest_log_file():
    """Find the most recent historical population log file"""
    log_files = glob.glob("historical_population_*.log")
    if not log_files:
        return None
    return max(log_files, key=os.path.getctime)

def parse_log_progress(log_file):
    """Parse the log file to extract progress information"""
    if not os.path.exists(log_file):
        return None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find start time
    start_time = None
    for line in lines:
        if "Started:" in line:
            start_time = line.split("Started: ")[1].strip()
            break
    
    # Count completed years
    completed_years = []
    failed_years = []
    
    for line in lines:
        if "✅ Year" in line and "completed successfully" in line:
            year = line.split("Year ")[1].split(" ")[0]
            completed_years.append(int(year))
        elif "❌ Year" in line and "failed" in line:
            year = line.split("Year ")[1].split(" ")[0]
            failed_years.append(int(year))
    
    return {
        'start_time': start_time,
        'completed_years': sorted(completed_years),
        'failed_years': sorted(failed_years),
        'total_years': 165  # 1861-2025
    }

def get_database_stats():
    """Get current database statistics"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Count documents
        cursor.execute("SELECT COUNT(*) FROM documenti_normativi")
        doc_count = cursor.fetchone()[0]
        
        # Count articles
        cursor.execute("SELECT COUNT(*) FROM articoli")
        art_count = cursor.fetchone()[0]
        
        # Get year distribution
        cursor.execute("""
            SELECT 
                SUBSTR(data_pubblicazione, 1, 4) as year,
                COUNT(*) as count
            FROM documenti_normativi 
            WHERE year IS NOT NULL AND year != ''
            GROUP BY year 
            ORDER BY year
        """)
        year_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            'documents': doc_count,
            'articles': art_count,
            'year_distribution': year_stats
        }
    except Exception as e:
        return {'error': str(e)}

def display_progress():
    """Display current progress information"""
    print("🏛️ COMPREHENSIVE HISTORICAL DATABASE - PROGRESS MONITOR")
    print("=" * 70)
    print(f"📅 Current time: {datetime.now()}")
    print()
    
    # Check log file
    log_file = get_latest_log_file()
    if not log_file:
        print("❌ No historical population log file found")
        print("💡 Make sure you've started the populate_multi_year.py script")
        return
    
    print(f"📝 Log file: {log_file}")
    
    # Parse progress
    progress = parse_log_progress(log_file)
    if not progress:
        print("❌ Could not parse log file")
        return
    
    print(f"🚀 Started: {progress['start_time']}")
    print()
    
    # Progress statistics
    completed = len(progress['completed_years'])
    failed = len(progress['failed_years'])
    total = progress['total_years']
    remaining = total - completed - failed
    
    print(f"📊 PROGRESS STATISTICS")
    print(f"   ✅ Completed: {completed}/{total} years ({completed/total*100:.1f}%)")
    print(f"   ❌ Failed: {failed}/{total} years ({failed/total*100:.1f}%)")
    print(f"   ⏳ Remaining: {remaining}/{total} years ({remaining/total*100:.1f}%)")
    print()
    
    # Show progress bar
    progress_bar_width = 50
    progress_filled = int((completed + failed) / total * progress_bar_width)
    completed_filled = int(completed / total * progress_bar_width)
    failed_filled = int(failed / total * progress_bar_width)
    
    bar = ""
    for i in range(progress_bar_width):
        if i < completed_filled:
            bar += "█"
        elif i < completed_filled + failed_filled:
            bar += "▓"
        else:
            bar += "░"
    
    print(f"📈 Progress: [{bar}] {(completed + failed)/total*100:.1f}%")
    print()
    
    # Show year ranges
    if progress['completed_years']:
        print(f"📅 Successfully completed years: {min(progress['completed_years'])} - {max(progress['completed_years'])}")
    if progress['failed_years']:
        print(f"⚠️ Failed years: {progress['failed_years'][:10]}{'...' if len(progress['failed_years']) > 10 else ''}")
    print()
    
    # Database statistics
    print(f"💾 DATABASE STATISTICS")
    db_stats = get_database_stats()
    if 'error' in db_stats:
        print(f"   ❌ Error: {db_stats['error']}")
    else:
        print(f"   📄 Documents: {db_stats['documents']:,}")
        print(f"   📋 Articles: {db_stats['articles']:,}")
        
        if db_stats['year_distribution']:
            earliest_year = min(int(year) for year, count in db_stats['year_distribution'] if year.isdigit())
            latest_year = max(int(year) for year, count in db_stats['year_distribution'] if year.isdigit())
            print(f"   📅 Document year range: {earliest_year} - {latest_year}")
    
    print()
    print("💡 Run this script again to check updated progress")
    print("🔄 Tip: Use 'python monitor_progress.py' every 30-60 minutes")

def main():
    """Main monitoring function"""
    try:
        display_progress()
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error monitoring progress: {e}")

if __name__ == "__main__":
    main()
