#!/usr/bin/env python3
"""
Test simplified versioning system
"""

import sqlite3
import json
from datetime import datetime, date

def test_simplified_versioning():
    """Test the simplified versioning system"""
    
    print("🧪 Testing simplified versioning system...")
    
    # Sample article data with versions
    test_article_data = {
        'documento_id': 1,
        'numero_articolo': '5',
        'titoloAtto': 'Test Article with Updates',
        'testo_completo': 'Original text of the article',
        'testo_pulito': 'Original text of the article',
        'articoli_correlati': '[]',
        'allegati': '[]',
        'data_attivazione': date(2020, 1, 1),
        'url_documento': 'http://example.com/doc',
        'versions': [
            {
                'tipo_versione': 'orig',
                'numero_aggiornamento': None,
                'testo_versione': 'Original text of the article',
                'testo_pulito': 'Original text of the article',
                'data_inizio_vigore': date(2020, 1, 1),
                'is_current': False,
                'status': 'vigente'
            },
            {
                'tipo_versione': 'agg.1',
                'numero_aggiornamento': 1,
                'testo_versione': 'Updated text of the article - first update',
                'testo_pulito': 'Updated text of the article - first update',
                'data_inizio_vigore': date(2021, 6, 15),
                'is_current': False,
                'status': 'vigente'
            },
            {
                'tipo_versione': 'agg.2',
                'numero_aggiornamento': 2,
                'testo_versione': 'Updated text of the article - second update',
                'testo_pulito': 'Updated text of the article - second update',
                'data_inizio_vigore': date(2022, 12, 1),
                'is_current': True,
                'status': 'vigente'
            }
        ]
    }
    
    # Import the save function
    try:
        import sys
        sys.path.append('.')
        from scraper_optimized import save_articolo_with_versions
        
        # Save the test article
        print("💾 Saving test article with versions...")
        article_id = save_articolo_with_versions(test_article_data)
        
        if article_id:
            print(f"✅ Successfully saved article with base ID: {article_id}")
            
            # Query the results
            conn = sqlite3.connect('data.sqlite')
            cursor = conn.cursor()
            
            # Get all versions of this article
            cursor.execute("""
                SELECT id, numero_articolo, tipo_versione, numero_aggiornamento, 
                       articolo_base_id, testo_completo, data_attivazione, status
                FROM articoli 
                WHERE numero_articolo = ? OR articolo_base_id = ?
                ORDER BY COALESCE(numero_aggiornamento, 0)
            """, [test_article_data['numero_articolo'], article_id])
            
            results = cursor.fetchall()
            
            print(f"\n📋 Found {len(results)} article versions:")
            for row in results:
                id_val, num_art, tipo_ver, num_agg, base_id, testo, data_att, status = row
                base_ref = f" (references article {base_id})" if base_id else " (base article)"
                print(f"  • ID {id_val}: Art. {num_art} - {tipo_ver}{base_ref}")
                print(f"    Text: {testo[:50]}...")
                print(f"    Status: {status}")
                print()
            
            # Test the view
            cursor.execute("""
                SELECT numero_articolo, tipo_versione, numero_aggiornamento, 
                       gruppo_articolo, numero_articolo_base
                FROM articoli_con_versioni 
                WHERE numero_articolo = ? OR articolo_base_id = ?
                ORDER BY COALESCE(numero_aggiornamento, 0)
            """, [test_article_data['numero_articolo'], article_id])
            
            view_results = cursor.fetchall()
            print("📊 View results (articoli_con_versioni):")
            for row in view_results:
                num_art, tipo_ver, num_agg, gruppo, base_art = row
                print(f"  • Art. {num_art} - {tipo_ver} (Group: {gruppo}, Base: {base_art})")
            
            conn.close()
            
        else:
            print("❌ Failed to save article")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

def test_query_examples():
    """Show examples of how to query the simplified versioning system"""
    
    print("\n🔍 Query examples for simplified versioning:")
    
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print("\n1️⃣ Get all versions of articles:")
    cursor.execute("""
        SELECT numero_articolo, tipo_versione, numero_aggiornamento, 
               CASE WHEN articolo_base_id IS NULL THEN 'Base' ELSE 'Update' END as tipo
        FROM articoli
        ORDER BY numero_articolo, COALESCE(numero_aggiornamento, 0)
    """)
    
    results = cursor.fetchall()
    for row in results[:10]:  # Show first 10
        print(f"   Art. {row[0]} - {row[1]} ({row[3]})")
    
    print("\n2️⃣ Get only base articles (originals):")
    cursor.execute("""
        SELECT numero_articolo, titoloAtto, status
        FROM articoli
        WHERE articolo_base_id IS NULL
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    for row in results:
        print(f"   Art. {row[0]}: {row[1][:50]}... (Status: {row[2]})")
    
    print("\n3️⃣ Get all updates for a specific article:")
    cursor.execute("""
        SELECT a.numero_articolo, a.tipo_versione, a.numero_aggiornamento, 
               base.numero_articolo as base_article
        FROM articoli a
        JOIN articoli base ON a.articolo_base_id = base.id
        WHERE base.numero_articolo = '1'
        ORDER BY a.numero_aggiornamento
    """)
    
    results = cursor.fetchall()
    if results:
        print(f"   Updates for article 1:")
        for row in results:
            print(f"     {row[1]} (Update #{row[2]})")
    else:
        print("   No updates found for article 1")
    
    print("\n4️⃣ Count articles by type:")
    cursor.execute("""
        SELECT tipo_versione, COUNT(*) as count
        FROM articoli
        GROUP BY tipo_versione
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    for row in results:
        print(f"   {row[0]}: {row[1]} articles")
    
    conn.close()

if __name__ == "__main__":
    test_simplified_versioning()
    test_query_examples()
