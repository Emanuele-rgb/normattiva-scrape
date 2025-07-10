#!/usr/bin/env python3
"""
Overnight Progress Monitor
Monitors the progress of the overnight complete scraping process
"""

import sqlite3
import time
import os
from datetime import datetime
import sys

def get_database_stats():
    """Get current database statistics"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Get document counts
        cursor.execute("SELECT COUNT(*) FROM documenti_normativi")
        total_docs = cursor.fetchone()[0]
        
        # Get article counts
        cursor.execute("SELECT COUNT(*) FROM articoli")
        total_articles = cursor.fetchone()[0]
        
        # Get documents per year
        cursor.execute("""
            SELECT SUBSTR(data_pubblicazione, 1, 4) as year, COUNT(*) as count
            FROM documenti_normativi 
            WHERE data_pubblicazione IS NOT NULL
            GROUP BY year
            ORDER BY year DESC
        """)
        year_stats = cursor.fetchall()
        
        # Get recent activity (last 10 documents)
        cursor.execute("""
            SELECT titoloAtto, data_pubblicazione, tipo_atto
            FROM documenti_normativi 
            ORDER BY id DESC 
            LIMIT 10
        """)
        recent_docs = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_docs': total_docs,
            'total_articles': total_articles,
            'year_stats': year_stats,
            'recent_docs': recent_docs
        }
    except Exception as e:
        return {'error': str(e)}

def monitor_progress():
    """Monitor the overnight scraping progress"""
    print("🌙 OVERNIGHT SCRAPING PROGRESS MONITOR")
    print("=" * 50)
    print("This monitor will show real-time progress of the overnight scraping")
    print("Press Ctrl+C to stop monitoring (scraping will continue)")
    print()
    
    start_time = datetime.now()
    previous_total = 0
    
    try:
        while True:
            stats = get_database_stats()
            
            if 'error' in stats:
                print(f"❌ Error accessing database: {stats['error']}")
                print("The scraping process might not be running yet.")
            else:
                current_time = datetime.now()
                elapsed = current_time - start_time
                
                print(f"\n📊 STATUS UPDATE - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏱️ Monitoring for: {elapsed}")
                print(f"📄 Total documents: {stats['total_docs']}")
                print(f"📝 Total articles: {stats['total_articles']}")
                
                # Show progress rate
                if previous_total > 0:
                    new_docs = stats['total_docs'] - previous_total
                    print(f"📈 New documents since last check: {new_docs}")
                
                previous_total = stats['total_docs']
                
                # Show documents per year
                if stats['year_stats']:
                    print(f"\n📅 Documents by year:")
                    for year, count in stats['year_stats']:
                        print(f"   {year}: {count}")
                
                # Show recent activity
                if stats['recent_docs']:
                    print(f"\n🔄 Recent documents:")
                    for doc in stats['recent_docs'][:5]:  # Show last 5
                        title = doc[0][:60] + "..." if len(doc[0]) > 60 else doc[0]
                        print(f"   {doc[1]} - {title}")
                
                # Check log files for additional info
                log_files = [f for f in os.listdir('.') if f.startswith('multi_year_population_') and f.endswith('.log')]
                if log_files:
                    latest_log = max(log_files, key=os.path.getctime)
                    print(f"\n📝 Latest log file: {latest_log}")
                    
                    try:
                        with open(latest_log, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            if lines:
                                print(f"📋 Last log entry: {lines[-1].strip()}")
                    except:
                        pass
            
            print(f"\n{'='*50}")
            print("Next update in 60 seconds... (Ctrl+C to stop)")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Monitoring stopped by user")
        print(f"⚠️ The overnight scraping process continues in the background")
        print(f"💡 You can restart monitoring anytime with: python monitor_overnight.py")

def show_final_summary():
    """Show final summary after completion"""
    stats = get_database_stats()
    
    if 'error' in stats:
        print(f"❌ Error accessing database: {stats['error']}")
        return
    
    print("🎉 OVERNIGHT SCRAPING COMPLETED!")
    print("=" * 50)
    print(f"📄 Total documents collected: {stats['total_docs']}")
    print(f"📝 Total articles extracted: {stats['total_articles']}")
    
    if stats['year_stats']:
        print(f"\n📅 Final distribution by year:")
        for year, count in stats['year_stats']:
            print(f"   {year}: {count} documents")
    
    print(f"\n💡 Next steps:")
    print(f"1. Run Legal AI Enhancement: python legal_ai_enhancer.py")
    print(f"2. Check database status: python check_status.py")
    print(f"3. Query your data using SQL or custom scripts")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'summary':
        show_final_summary()
    else:
        monitor_progress()
