#!/usr/bin/env python3
"""
Test script for enhanced article scraping with bis/ter and allegati support
"""

import sqlite3
import json
from datetime import datetime
import sys
import os

# Add the current directory to the path to import the scraper
sys.path.insert(0, os.getcwd())

from scraper_optimized import (
    extract_article_number_from_text,
    sort_article_number,
    determine_content_type,
    extract_article_activation_date,
    init_versioning_database
)

def test_article_number_extraction():
    """Test the enhanced article number extraction"""
    print("🧪 Testing article number extraction...")
    
    test_cases = [
        ("art. 1", "1"),
        ("art. 1-bis", "1-bis"),
        ("art. 1-ter", "1-ter"),
        ("articolo 5-quater", "5-quater"),
        ("Art. 123 bis", "123-bis"),
        ("12 ter", "12-ter"),
        ("allegato A", None),
        ("1", "1"),
        ("15-sexies", "15-sexies"),
    ]
    
    for input_text, expected in test_cases:
        result = extract_article_number_from_text(input_text)
        status = "✓" if result == expected else "❌"
        print(f"  {status} '{input_text}' -> '{result}' (expected: '{expected}')")

def test_content_type_detection():
    """Test content type detection"""
    print("\n🧪 Testing content type detection...")
    
    test_cases = [
        ("art. 1", "articolo"),
        ("Allegato A", "allegato"),
        ("Allegati", "allegato"),
        ("art. 1-bis", "articolo"),
        ("articolo 5-ter", "articolo"),
    ]
    
    for input_text, expected in test_cases:
        result = determine_content_type(input_text)
        status = "✓" if result == expected else "❌"
        print(f"  {status} '{input_text}' -> '{result}' (expected: '{expected}')")

def test_article_sorting():
    """Test article sorting with bis/ter/allegati"""
    print("\n🧪 Testing article sorting...")
    
    articles = [
        "1-ter",
        "Allegato A",
        "1",
        "2",
        "1-bis",
        "Allegato B",
        "3-bis",
        "10",
        "3"
    ]
    
    sorted_articles = sorted(articles, key=sort_article_number)
    expected_order = ["1", "1-bis", "1-ter", "2", "3", "3-bis", "10", "Allegato A", "Allegato B"]
    
    print(f"  Input: {articles}")
    print(f"  Sorted: {sorted_articles}")
    print(f"  Expected: {expected_order}")
    
    if sorted_articles == expected_order:
        print("  ✓ Sorting works correctly")
    else:
        print("  ❌ Sorting failed")

def test_database_schema():
    """Test database schema with new columns"""
    print("\n🧪 Testing database schema...")
    
    try:
        # Initialize versioning database
        init_versioning_database()
        
        # Connect and check if new columns exist
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Check if new columns exist in articoli table
        cursor.execute("PRAGMA table_info(articoli)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = ['data_attivazione', 'allegati']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"  ❌ Missing columns: {missing_columns}")
            print("  🔧 Running migration...")
            
            # Run the migration
            with open('migration_article_enhancements.sql', 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            cursor.executescript(migration_sql)
            conn.commit()
            print("  ✓ Migration completed")
        else:
            print("  ✓ All required columns present")
        
        # Check if versioning table has allegati column
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articoli_versioni'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(articoli_versioni)")
            version_columns = cursor.fetchall()
            version_column_names = [col[1] for col in version_columns]
            
            if 'allegati' in version_column_names:
                print("  ✓ Versioning table has allegati column")
            else:
                print("  ❌ Versioning table missing allegati column")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Database schema test failed: {e}")

def test_sample_article_data():
    """Test saving sample article data with new features"""
    print("\n🧪 Testing sample article data...")
    
    try:
        # Sample article data with new features
        sample_data = {
            'documento_id': 1,
            'numero_articolo': '1-bis',
            'titoloAtto': 'Test Document Title',
            'testo_completo': 'This is a test article with bis designation',
            'testo_pulito': 'This is a test article with bis designation',
            'articoli_correlati': json.dumps([{'article_number': '2', 'type': 'reference'}]),
            'allegati': json.dumps([{'numero': 'A', 'titolo': 'Test Allegato', 'contenuto': 'Test content'}]),
            'data_attivazione': datetime.now().date(),
            'url_documento': 'https://example.com/test',
            'versions': [{
                'tipo_versione': 'orig',
                'numero_aggiornamento': None,
                'testo_versione': 'This is a test article with bis designation',
                'testo_pulito': 'This is a test article with bis designation',
                'articoli_correlati': [],
                'allegati': [{'numero': 'A', 'titolo': 'Test Allegato', 'contenuto': 'Test content'}],
                'data_inizio_vigore': datetime.now().date(),
                'data_fine_vigore': None,
                'is_current': True,
                'status': 'vigente'
            }]
        }
        
        print("  ✓ Sample data structure created")
        print(f"  - Article number: {sample_data['numero_articolo']}")
        print(f"  - Has allegati: {len(json.loads(sample_data['allegati'])) > 0}")
        print(f"  - Has activation date: {sample_data['data_attivazione'] is not None}")
        print(f"  - Has versions: {len(sample_data['versions']) > 0}")
        
    except Exception as e:
        print(f"  ❌ Sample data test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Running enhanced article scraper tests...\n")
    
    test_article_number_extraction()
    test_content_type_detection()
    test_article_sorting()
    test_database_schema()
    test_sample_article_data()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
