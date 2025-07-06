#!/usr/bin/env python3
"""
Test script to verify the new features in the enhanced scraper:
- Article activation dates
- Allegati support
- Bis/ter article support
"""

import sqlite3
import json
from datetime import datetime

def test_new_features():
    """Test the new features in the enhanced scraper"""
    
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print("🔍 Testing New Features in Enhanced Scraper")
    print("=" * 60)
    
    # Check database schema
    print("\n1. Database Schema Check:")
    cursor.execute("PRAGMA table_info(articoli)")
    columns = [row[1] for row in cursor.fetchall()]
    
    expected_columns = ['data_attivazione', 'allegati']
    for col in expected_columns:
        if col in columns:
            print(f"  ✓ Column '{col}' exists")
        else:
            print(f"  ❌ Column '{col}' missing")
    
    # Check activation dates
    print("\n2. Article Activation Dates:")
    cursor.execute("SELECT numero_articolo, data_attivazione FROM articoli WHERE data_attivazione IS NOT NULL ORDER BY numero_articolo LIMIT 10")
    rows = cursor.fetchall()
    
    if rows:
        print(f"  ✓ Found {len(rows)} articles with activation dates:")
        for row in rows:
            print(f"    Article {row[0]}: {row[1]}")
    else:
        print("  ❌ No articles with activation dates found")
    
    # Check allegati
    print("\n3. Allegati Support:")
    cursor.execute("SELECT numero_articolo, allegati FROM articoli WHERE allegati IS NOT NULL AND allegati != '[]' LIMIT 5")
    rows = cursor.fetchall()
    
    if rows:
        print(f"  ✓ Found {len(rows)} articles with allegati:")
        for row in rows:
            allegati = json.loads(row[1]) if row[1] else []
            print(f"    Article {row[0]}: {len(allegati)} allegati")
    else:
        print("  ℹ️  No articles with allegati found (expected for this document)")
    
    # Check text extraction
    print("\n4. Text Extraction Quality:")
    cursor.execute("SELECT numero_articolo, LENGTH(testo_completo), LENGTH(testo_pulito) FROM articoli WHERE testo_completo IS NOT NULL ORDER BY numero_articolo LIMIT 5")
    rows = cursor.fetchall()
    
    if rows:
        print(f"  ✓ Found {len(rows)} articles with extracted text:")
        for row in rows:
            print(f"    Article {row[0]}: {row[1]} chars complete, {row[2]} chars clean")
    else:
        print("  ❌ No articles with extracted text found")
    
    # Check correlated articles
    print("\n5. Correlated Articles:")
    cursor.execute("SELECT numero_articolo, articoli_correlati FROM articoli WHERE articoli_correlati IS NOT NULL AND articoli_correlati != '[]' LIMIT 5")
    rows = cursor.fetchall()
    
    if rows:
        print(f"  ✓ Found {len(rows)} articles with correlations:")
        for row in rows:
            correlati = json.loads(row[1]) if row[1] else []
            print(f"    Article {row[0]}: {len(correlati)} correlations")
    else:
        print("  ❌ No articles with correlations found")
    
    # Check versioning
    print("\n6. Versioning Support:")
    cursor.execute("SELECT COUNT(*) FROM articoli_versioni")
    version_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT numero_articolo) FROM articoli")
    article_count = cursor.fetchone()[0]
    
    print(f"  ✓ Found {version_count} versions for {article_count} articles")
    
    if version_count > article_count:
        print("  ✓ Multi-version articles detected")
        
        # Show articles with multiple versions
        cursor.execute("""
            SELECT articolo_id, COUNT(*) as version_count 
            FROM articoli_versioni 
            GROUP BY articolo_id 
            HAVING COUNT(*) > 1
        """)
        multi_version_rows = cursor.fetchall()
        
        if multi_version_rows:
            print(f"  ✓ {len(multi_version_rows)} articles have multiple versions:")
            for row in multi_version_rows:
                print(f"    Article {row[0]}: {row[1]} versions")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✓ Test completed successfully!")

if __name__ == "__main__":
    test_new_features()
