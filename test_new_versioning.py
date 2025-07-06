#!/usr/bin/env python3
"""
Test script for the new versioning functionality
"""

import json
from datetime import datetime, date
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper_optimized import save_articolo_with_versions

def test_new_versioning_functionality():
    """Test the new versioning functionality with mock data"""
    
    print("🧪 Testing new versioning functionality...")
    
    # Create mock article data with versions
    mock_article_data = {
        'documento_id': 999,  # Use a test document ID
        'numero_articolo': '42',
        'titoloAtto': 'Test Article Title',
        'testo_completo': 'This is the complete text of the test article.',
        'testo_pulito': 'This is the clean text of the test article.',
        'articoli_correlati': json.dumps([], ensure_ascii=False),
        'allegati': json.dumps([], ensure_ascii=False),
        'data_attivazione': date(2023, 1, 1),
        'data_cessazione': None,  # Vigente article
        'url_documento': 'https://example.com/test-article',
        'versions': [
            {
                'tipo_versione': 'orig',
                'numero_aggiornamento': None,
                'testo_versione': 'Original version text',
                'testo_pulito': 'Original version clean text',
                'articoli_correlati': json.dumps([], ensure_ascii=False),
                'allegati': json.dumps([], ensure_ascii=False),
                'data_inizio_vigore': date(2023, 1, 1),
                'data_fine_vigore': date(2023, 6, 1),
                'is_current': False,
                'status': 'vigente'
            },
            {
                'tipo_versione': 'agg.1',
                'numero_aggiornamento': 1,
                'testo_versione': 'First update version text',
                'testo_pulito': 'First update clean text',
                'articoli_correlati': json.dumps([], ensure_ascii=False),
                'allegati': json.dumps([], ensure_ascii=False),
                'data_inizio_vigore': date(2023, 6, 1),
                'data_fine_vigore': date(2023, 12, 1),
                'is_current': False,
                'status': 'vigente'
            },
            {
                'tipo_versione': 'agg.2',
                'numero_aggiornamento': 2,
                'testo_versione': 'Second update version text',
                'testo_pulito': 'Second update clean text',
                'articoli_correlati': json.dumps([], ensure_ascii=False),
                'allegati': json.dumps([], ensure_ascii=False),
                'data_inizio_vigore': date(2023, 12, 1),
                'data_fine_vigore': None,
                'is_current': True,
                'status': 'vigente'
            }
        ]
    }
    
    # Test vigente article
    print("  Testing vigente article with multiple versions...")
    article_id_vigente = save_articolo_with_versions(mock_article_data)
    print(f"    ✓ Saved vigente article with ID: {article_id_vigente}")
    
    # Test abrogato article
    print("  Testing abrogato article...")
    mock_article_data_abrogato = mock_article_data.copy()
    mock_article_data_abrogato['numero_articolo'] = '43'
    mock_article_data_abrogato['data_cessazione'] = date(2024, 1, 1)
    mock_article_data_abrogato['versions'] = [
        {
            'tipo_versione': 'orig',
            'numero_aggiornamento': None,
            'testo_versione': 'Abrogated article text',
            'testo_pulito': 'Abrogated article clean text',
            'articoli_correlati': json.dumps([], ensure_ascii=False),
            'allegati': json.dumps([], ensure_ascii=False),
            'data_inizio_vigore': date(2023, 1, 1),
            'data_fine_vigore': None,
            'is_current': True,
            'status': 'abrogato'
        }
    ]
    
    article_id_abrogato = save_articolo_with_versions(mock_article_data_abrogato)
    print(f"    ✓ Saved abrogato article with ID: {article_id_abrogato}")
    
    return article_id_vigente, article_id_abrogato

def verify_test_articles(article_id_vigente, article_id_abrogato):
    """Verify the test articles were saved correctly"""
    
    import sqlite3
    
    print("\n🔍 Verifying test articles...")
    
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    # Check vigente article
    cursor.execute("""
        SELECT numero_articolo, status, data_cessazione, numero_versioni
        FROM articoli 
        WHERE id = ?
    """, [article_id_vigente])
    
    vigente_data = cursor.fetchone()
    if vigente_data:
        numero, status, cessazione, num_versions = vigente_data
        print(f"  Article {numero}: status={status}, cessazione={cessazione}, versions={num_versions}")
        
        # Check versions
        cursor.execute("""
            SELECT tipo_versione, is_current, status
            FROM articoli_versioni 
            WHERE articolo_id = ?
            ORDER BY numero_aggiornamento ASC
        """, [article_id_vigente])
        
        versions = cursor.fetchall()
        print(f"    Versions:")
        for tipo, is_current, v_status in versions:
            current_mark = " (CURRENT)" if is_current else ""
            print(f"      {tipo}: {v_status}{current_mark}")
    
    # Check abrogato article
    cursor.execute("""
        SELECT numero_articolo, status, data_cessazione, numero_versioni
        FROM articoli 
        WHERE id = ?
    """, [article_id_abrogato])
    
    abrogato_data = cursor.fetchone()
    if abrogato_data:
        numero, status, cessazione, num_versions = abrogato_data
        print(f"  Article {numero}: status={status}, cessazione={cessazione}, versions={num_versions}")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Testing enhanced versioning and status functionality...\n")
    
    article_id_vigente, article_id_abrogato = test_new_versioning_functionality()
    verify_test_articles(article_id_vigente, article_id_abrogato)
    
    print("\n✅ Testing completed!")
