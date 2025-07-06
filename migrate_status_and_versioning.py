#!/usr/bin/env python3
"""
Migration script to update existing articles with proper status and versioning info
"""

import sqlite3
from datetime import datetime

def update_article_status():
    """Update article status based on data_cessazione"""
    
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print("🔄 Updating article status based on data_cessazione...")
    
    # Update articles with data_cessazione to 'abrogato'
    cursor.execute("""
        UPDATE articoli 
        SET status = 'abrogato', updated_at = ?
        WHERE data_cessazione IS NOT NULL AND status != 'abrogato'
    """, [datetime.now()])
    
    abrogato_count = cursor.rowcount
    
    # Update articles without data_cessazione to 'vigente' 
    cursor.execute("""
        UPDATE articoli 
        SET status = 'vigente', updated_at = ?
        WHERE data_cessazione IS NULL AND status != 'vigente'
    """, [datetime.now()])
    
    vigente_count = cursor.rowcount
    
    print(f"✓ Updated {abrogato_count} articles to 'abrogato' status")
    print(f"✓ Updated {vigente_count} articles to 'vigente' status")
    
    conn.commit()
    conn.close()

def update_version_labels():
    """Update version labels to include article references"""
    
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print("🔄 Updating version labels to include article references...")
    
    # Get all versions that need updating
    cursor.execute("""
        SELECT av.id, a.numero_articolo, av.tipo_versione, av.numero_aggiornamento
        FROM articoli_versioni av
        JOIN articoli a ON av.articolo_id = a.id
        WHERE av.tipo_versione NOT LIKE '%dell''art.%'
    """)
    
    versions_to_update = cursor.fetchall()
    
    updated_count = 0
    for version_id, numero_articolo, tipo_versione, numero_aggiornamento in versions_to_update:
        
        # Create proper version label
        if numero_aggiornamento is not None:
            new_label = f"agg.{numero_aggiornamento} dell'art. {numero_articolo}"
        elif tipo_versione == 'orig':
            new_label = f"orig. dell'art. {numero_articolo}"
        else:
            continue  # Skip unknown types
        
        # Update the version
        cursor.execute("""
            UPDATE articoli_versioni 
            SET tipo_versione = ?, updated_at = ?
            WHERE id = ?
        """, [new_label, datetime.now(), version_id])
        
        updated_count += 1
        print(f"  Updated version {tipo_versione} -> {new_label}")
    
    print(f"✓ Updated {updated_count} version labels")
    
    conn.commit()
    conn.close()

def update_version_status():
    """Update version status based on main article status"""
    
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print("🔄 Updating version status based on main article...")
    
    # Update version status to match main article status
    cursor.execute("""
        UPDATE articoli_versioni 
        SET status = (
            SELECT a.status 
            FROM articoli a 
            WHERE a.id = articoli_versioni.articolo_id
        ),
        updated_at = ?
        WHERE status != (
            SELECT a.status 
            FROM articoli a 
            WHERE a.id = articoli_versioni.articolo_id
        )
    """, [datetime.now()])
    
    updated_count = cursor.rowcount
    print(f"✓ Updated {updated_count} version statuses")
    
    conn.commit()
    conn.close()

def verify_updates():
    """Verify the migration results"""
    
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print("\n🔍 Verifying migration results...")
    
    # Check article status consistency
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN data_cessazione IS NOT NULL THEN 1 ELSE 0 END) as with_cessazione,
            SUM(CASE WHEN status = 'abrogato' THEN 1 ELSE 0 END) as status_abrogato,
            SUM(CASE WHEN data_cessazione IS NOT NULL AND status = 'abrogato' THEN 1 ELSE 0 END) as correct_abrogato,
            SUM(CASE WHEN data_cessazione IS NULL AND status = 'vigente' THEN 1 ELSE 0 END) as correct_vigente
        FROM articoli
    """)
    
    stats = cursor.fetchone()
    total, with_cessazione, status_abrogato, correct_abrogato, correct_vigente = stats
    
    print(f"📊 Article status verification:")
    print(f"  Total articles: {total}")
    print(f"  With data_cessazione: {with_cessazione}")
    print(f"  Status 'abrogato': {status_abrogato}")
    print(f"  Correctly abrogato: {correct_abrogato}")
    print(f"  Correctly vigente: {correct_vigente}")
    print(f"  Status consistency: {((correct_abrogato + correct_vigente) / total * 100):.1f}%")
    
    # Check version labeling
    cursor.execute("""
        SELECT COUNT(*) FROM articoli_versioni 
        WHERE tipo_versione LIKE '%dell''art.%'
    """)
    
    proper_labels = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM articoli_versioni")
    total_versions = cursor.fetchone()[0]
    
    print(f"📊 Version labeling verification:")
    print(f"  Total versions: {total_versions}")
    print(f"  Properly labeled: {proper_labels}")
    print(f"  Labeling accuracy: {(proper_labels / total_versions * 100):.1f}%")
    
    # Show sample of updated versions
    cursor.execute("""
        SELECT a.numero_articolo, av.tipo_versione, av.status
        FROM articoli_versioni av
        JOIN articoli a ON av.articolo_id = a.id
        WHERE av.tipo_versione LIKE '%dell''art.%'
        ORDER BY a.id DESC
        LIMIT 5
    """)
    
    samples = cursor.fetchall()
    print(f"\n📋 Sample updated versions:")
    for numero_articolo, tipo_versione, status in samples:
        print(f"  {tipo_versione} - status: {status}")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Running migration to fix article status and versioning...\n")
    
    update_article_status()
    update_version_labels() 
    update_version_status()
    verify_updates()
    
    print("\n✅ Migration completed!")
