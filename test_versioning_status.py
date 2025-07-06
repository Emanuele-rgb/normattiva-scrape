#!/usr/bin/env python3
"""
Test script to verify the new versioning and status functionality
"""

import sqlite3
from datetime import datetime, date

def test_database_status_logic():
    """Test the status logic in the database"""
    
    # Connect to database
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print("🔍 Testing database status logic...")
    
    # Check if status column exists
    cursor.execute("PRAGMA table_info(articoli)")
    columns = [column[1] for column in cursor.fetchall()]
    has_status = 'status' in columns
    
    print(f"✓ Status column exists: {has_status}")
    
    if has_status:
        # Query articles with and without data_cessazione
        cursor.execute("""
            SELECT numero_articolo, data_cessazione, status 
            FROM articoli 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        articles = cursor.fetchall()
        print(f"\n📋 Recent articles status check:")
        for numero, data_cessazione, status in articles:
            expected_status = 'abrogato' if data_cessazione else 'vigente'
            status_ok = status == expected_status if status else 'N/A'
            print(f"  Article {numero}: cessazione={data_cessazione}, status={status}, expected={expected_status}, ok={status_ok}")
    
    # Check versioning table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articoli_versioni'")
    has_versioning = cursor.fetchone() is not None
    print(f"✓ Versioning table exists: {has_versioning}")
    
    if has_versioning:
        # Check recent versioned articles
        cursor.execute("""
            SELECT a.numero_articolo, av.tipo_versione, av.numero_aggiornamento, av.is_current, av.status
            FROM articoli a
            JOIN articoli_versioni av ON a.id = av.articolo_id
            ORDER BY a.id DESC, av.numero_aggiornamento ASC
            LIMIT 15
        """)
        
        versions = cursor.fetchall()
        print(f"\n📋 Recent article versions:")
        for numero, tipo_versione, numero_aggiornamento, is_current, status in versions:
            print(f"  Art. {numero}: {tipo_versione} (agg.{numero_aggiornamento if numero_aggiornamento else 'N/A'}) - current: {is_current}, status: {status}")
    
    conn.close()

def test_version_extraction_logic():
    """Test the version extraction and naming logic"""
    
    print("\n🧪 Testing version extraction logic...")
    
    # Mock version info examples
    test_cases = [
        {'tipo_versione': 'orig', 'numero_aggiornamento': None},
        {'tipo_versione': 'agg.1', 'numero_aggiornamento': 1},
        {'tipo_versione': 'agg.2', 'numero_aggiornamento': 2},
        {'tipo_versione': 'current', 'numero_aggiornamento': None, 'is_current': True}
    ]
    
    article_number = "42"
    
    for version_info in test_cases:
        # Simulate the version labeling logic from save_articolo_with_full_versioning
        version_label = version_info['tipo_versione']
        if version_info.get('numero_aggiornamento') is not None:
            version_label = f"agg.{version_info['numero_aggiornamento']} dell'art. {article_number}"
        elif version_info['tipo_versione'] == 'orig':
            version_label = f"orig. dell'art. {article_number}"
        
        print(f"  {version_info['tipo_versione']} -> '{version_label}'")

if __name__ == "__main__":
    print("🚀 Running enhanced versioning and status tests...\n")
    
    test_database_status_logic()
    test_version_extraction_logic()
    
    print("\n✅ Tests completed!")
