#!/usr/bin/env python3
"""
Script to demonstrate the fonte_origine column functionality.
Shows how articles are now categorized by their source/origin.
"""

import sqlite3

def show_fonte_origine_examples():
    """Show examples of each fonte_origine category"""
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print("📋 FONTE ORIGINE EXAMPLES")
    print("=" * 50)
    
    # Get examples from each category
    cursor.execute("""
        SELECT DISTINCT fonte_origine
        FROM articoli
        WHERE fonte_origine IS NOT NULL
        ORDER BY fonte_origine
    """)
    
    categories = cursor.fetchall()
    
    for (category,) in categories:
        print(f"\n🏷️  {category}")
        print("-" * 30)
        
        # Get a few examples from this category
        cursor.execute("""
            SELECT numero_articolo, titoloAtto, testo_completo
            FROM articoli
            WHERE fonte_origine = ?
            LIMIT 3
        """, (category,))
        
        examples = cursor.fetchall()
        
        for i, (numero, titolo, testo) in enumerate(examples, 1):
            text_preview = testo[:100] if testo else "No text"
            print(f"  {i}. Article {numero}")
            print(f"     Title: {titolo}")
            print(f"     Text: {text_preview}...")
            print()
    
    conn.close()

def show_fonte_origine_statistics():
    """Show detailed statistics about fonte_origine distribution"""
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print("\n📊 DETAILED STATISTICS")
    print("=" * 50)
    
    # Total count
    cursor.execute("SELECT COUNT(*) FROM articoli")
    total = cursor.fetchone()[0]
    print(f"Total articles: {total}")
    
    # Distribution by fonte_origine
    cursor.execute("""
        SELECT 
            fonte_origine,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / ?, 1) as percentage
        FROM articoli
        WHERE fonte_origine IS NOT NULL
        GROUP BY fonte_origine
        ORDER BY count DESC
    """, (total,))
    
    print("\nDistribution by source:")
    for fonte, count, percentage in cursor.fetchall():
        print(f"  • {fonte}: {count} articles ({percentage}%)")
    
    # Show which document types have which sources
    print("\nBy document type:")
    cursor.execute("""
        SELECT 
            d.tipo_atto,
            a.fonte_origine,
            COUNT(*) as count
        FROM articoli a
        JOIN documenti_normativi d ON a.documento_id = d.id
        WHERE a.fonte_origine IS NOT NULL
        GROUP BY d.tipo_atto, a.fonte_origine
        ORDER BY d.tipo_atto, count DESC
    """)
    
    current_tipo = None
    for tipo_atto, fonte, count in cursor.fetchall():
        if tipo_atto != current_tipo:
            print(f"\n  {tipo_atto}:")
            current_tipo = tipo_atto
        print(f"    - {fonte}: {count} articles")
    
    conn.close()

def show_usage_examples():
    """Show examples of how to use the fonte_origine column in queries"""
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print("\n💡 USAGE EXAMPLES")
    print("=" * 50)
    
    print("1. Get all articles from Allegati:")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articoli 
        WHERE fonte_origine LIKE 'Allegati%'
    """)
    count = cursor.fetchone()[0]
    print(f"   Found {count} articles from Allegati sections")
    
    print("\n2. Get only main articles (not from Allegati):")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articoli 
        WHERE fonte_origine = 'Articoli'
    """)
    count = cursor.fetchone()[0]
    print(f"   Found {count} main articles")
    
    print("\n3. Get articles from specific Agreement sections:")
    cursor.execute("""
        SELECT numero_articolo, titoloAtto
        FROM articoli 
        WHERE fonte_origine IN ('Allegati > Agreement', 'Allegati > Accordo')
        LIMIT 3
    """)
    results = cursor.fetchall()
    for numero, titolo in results:
        print(f"   - Article {numero}: {titolo}")
    
    print("\n4. Group articles by document and source:")
    cursor.execute("""
        SELECT 
            d.titoloAtto,
            a.fonte_origine,
            COUNT(*) as count
        FROM articoli a
        JOIN documenti_normativi d ON a.documento_id = d.id
        WHERE a.fonte_origine IS NOT NULL
        GROUP BY d.id, a.fonte_origine
        HAVING count > 2
        ORDER BY d.titoloAtto, count DESC
        LIMIT 5
    """)
    
    print("   Documents with multiple sources:")
    for titolo, fonte, count in cursor.fetchall():
        doc_title = titolo[:50] + "..." if len(titolo) > 50 else titolo
        print(f"   - {doc_title}")
        print(f"     {fonte}: {count} articles")
    
    conn.close()

if __name__ == "__main__":
    print("🎯 FONTE ORIGINE DEMONSTRATION")
    print("=" * 60)
    print("This demonstrates the new fonte_origine column that tracks")
    print("where each article comes from (Articoli vs Allegati sections)")
    print()
    
    show_fonte_origine_examples()
    show_fonte_origine_statistics()
    show_usage_examples()
    
    print("\n✅ SUMMARY")
    print("=" * 50)
    print("The fonte_origine column successfully categorizes articles by their source:")
    print("• 'Articoli' - Main document articles")
    print("• 'Allegati' - General attachments")
    print("• 'Allegati > Agreement' - Agreement-specific sections")
    print("• 'Allegati > Accordo' - Accordo-specific sections")
    print("• 'Allegati > Protocol' - Protocol-specific sections")
    print("\nThis enables precise filtering and organization of legal content!")
