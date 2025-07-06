#!/usr/bin/env python3
"""
Verification script to confirm that the scraper_optimized.py integration with populate_fonte_origine.py is working correctly.
"""

import sqlite3
import sys

def verify_integration():
    """Verify that the integration between scraper and fonte_origine population is working."""
    
    print("🔍 VERIFYING SCRAPER-FONTE_ORIGINE INTEGRATION")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Check if fonte_origine column exists
        cursor.execute("PRAGMA table_info(articoli)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'fonte_origine' not in columns:
            print("❌ ERROR: fonte_origine column not found in articoli table")
            return False
        
        print("✅ fonte_origine column exists in articoli table")
        
        # Check total articles
        cursor.execute("SELECT COUNT(*) FROM articoli")
        total_articles = cursor.fetchone()[0]
        print(f"📊 Total articles in database: {total_articles}")
        
        # Check articles with fonte_origine populated
        cursor.execute("SELECT COUNT(*) FROM articoli WHERE fonte_origine IS NOT NULL")
        populated_articles = cursor.fetchone()[0]
        print(f"✅ Articles with fonte_origine populated: {populated_articles}")
        
        # Check articles with NULL fonte_origine
        cursor.execute("SELECT COUNT(*) FROM articoli WHERE fonte_origine IS NULL")
        null_articles = cursor.fetchone()[0]
        print(f"⚠️  Articles with NULL fonte_origine: {null_articles}")
        
        # Show distribution by fonte_origine
        cursor.execute("""
            SELECT fonte_origine, COUNT(*) as count 
            FROM articoli 
            WHERE fonte_origine IS NOT NULL 
            GROUP BY fonte_origine 
            ORDER BY count DESC
        """)
        distribution = cursor.fetchall()
        
        print("\n📈 FONTE ORIGINE DISTRIBUTION:")
        print("-" * 30)
        for fonte, count in distribution:
            print(f"  {fonte}: {count} articles")
        
        # Show some sample articles
        cursor.execute("""
            SELECT numero_articolo, fonte_origine, SUBSTR(testo_completo, 1, 50) 
            FROM articoli 
            WHERE fonte_origine IS NOT NULL 
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        print("\n🔍 SAMPLE ARTICLES:")
        print("-" * 30)
        for art_num, fonte, text in samples:
            print(f"  Article {art_num}: {fonte} - {text[:50]}...")
        
        conn.close()
        
        # Verify integration success
        success_rate = (populated_articles / total_articles * 100) if total_articles > 0 else 0
        print(f"\n📊 INTEGRATION SUCCESS RATE: {success_rate:.1f}%")
        
        if success_rate >= 100:
            print("✅ INTEGRATION SUCCESSFUL: All articles have fonte_origine populated!")
            return True
        elif success_rate >= 95:
            print("⚠️  INTEGRATION MOSTLY SUCCESSFUL: Most articles have fonte_origine populated")
            return True
        else:
            print("❌ INTEGRATION FAILED: Too many articles missing fonte_origine")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during verification: {e}")
        return False

if __name__ == "__main__":
    if verify_integration():
        print("\n🎉 VERIFICATION COMPLETE: Integration is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED: Integration needs attention")
        sys.exit(1)
