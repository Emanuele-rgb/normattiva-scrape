#!/usr/bin/env python3
"""
Utility to demonstrate and query the simplified versioning system
"""

import sqlite3

def simple_table(data, headers):
    """Simple table formatting without external dependencies"""
    if not data:
        return "No data"
    
    # Calculate column widths
    col_widths = [len(str(h)) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Format header
    header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    separator = "-" * len(header_line)
    
    # Format rows
    rows = []
    for row in data:
        formatted_row = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        rows.append(formatted_row)
    
    return f"{header_line}\n{separator}\n" + "\n".join(rows)

def show_article_versions(numero_articolo=None):
    """Show all versions of a specific article or all articles"""
    
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    if numero_articolo:
        print(f"\n📋 All versions of Article {numero_articolo}:")
        query = """
            SELECT 
                a.id,
                a.numero_articolo,
                a.tipo_versione,
                a.numero_aggiornamento,
                a.articolo_base_id,
                LEFT(a.testo_completo, 100) as testo_preview,
                a.data_attivazione,
                a.status
            FROM articoli a
            WHERE a.numero_articolo = ? 
               OR a.articolo_base_id IN (
                   SELECT id FROM articoli WHERE numero_articolo = ? AND articolo_base_id IS NULL
               )
            ORDER BY COALESCE(a.numero_aggiornamento, 0)
        """
        cursor.execute(query, [numero_articolo, numero_articolo])
    else:
        print("\n📋 Sample of articles with versions:")
        query = """
            SELECT 
                a.id,
                a.numero_articolo,
                a.tipo_versione,
                a.numero_aggiornamento,
                a.articolo_base_id,
                LEFT(a.testo_completo, 50) as testo_preview,
                a.data_attivazione,
                a.status
            FROM articoli a
            WHERE a.numero_articolo IN ('1', '2', '3', '4', '5')
            ORDER BY a.numero_articolo, COALESCE(a.numero_aggiornamento, 0)
            LIMIT 20
        """
        cursor.execute(query)
    
    results = cursor.fetchall()
    
    if results:
        headers = ['ID', 'Art.', 'Version', 'Update#', 'Base ID', 'Text Preview', 'Date', 'Status']
        table_data = []
        
        for row in results:
            table_data.append([
                row[0],  # ID
                row[1],  # numero_articolo
                row[2],  # tipo_versione
                row[3] if row[3] is not None else '-',  # numero_aggiornamento
                row[4] if row[4] is not None else '-',  # articolo_base_id
                f"{row[5]}..." if row[5] else '',  # testo_preview
                row[6],  # data_attivazione
                row[7]   # status
            ])
        
        print(simple_table(table_data, headers))
    else:
        print("No articles found")
    
    conn.close()

def show_versioning_stats():
    """Show statistics about the versioning system"""
    
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print("\n📊 Versioning Statistics:")
    
    # Count by version type
    cursor.execute("""
        SELECT tipo_versione, COUNT(*) as count
        FROM articoli
        GROUP BY tipo_versione
        ORDER BY 
            CASE tipo_versione 
                WHEN 'orig' THEN 0
                ELSE CAST(REPLACE(tipo_versione, 'agg.', '') AS INTEGER)
            END
    """)
    
    version_stats = cursor.fetchall()
    print("\n🔢 Articles by version type:")
    for version_type, count in version_stats:
        print(f"   {version_type}: {count} articles")
    
    # Articles with updates
    cursor.execute("""
        SELECT COUNT(DISTINCT articolo_base_id) as articles_with_updates
        FROM articoli
        WHERE articolo_base_id IS NOT NULL
    """)
    
    updated_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM articoli WHERE articolo_base_id IS NULL")
    base_count = cursor.fetchone()[0]
    
    print(f"\n📈 Update summary:")
    print(f"   Base articles: {base_count}")
    print(f"   Articles with updates: {updated_count}")
    print(f"   Percentage with updates: {(updated_count/base_count*100):.1f}%")
    
    # Most updated articles
    cursor.execute("""
        SELECT 
            base.numero_articolo,
            COUNT(*) as update_count,
            GROUP_CONCAT(upd.tipo_versione, ', ') as versions
        FROM articoli base
        JOIN articoli upd ON base.id = upd.articolo_base_id
        GROUP BY base.id, base.numero_articolo
        ORDER BY update_count DESC
        LIMIT 5
    """)
    
    most_updated = cursor.fetchall()
    if most_updated:
        print(f"\n🏆 Most updated articles:")
        for art_num, count, versions in most_updated:
            print(f"   Art. {art_num}: {count} updates ({versions})")
    
    conn.close()

def search_article_updates(search_term):
    """Search for articles or updates containing specific text"""
    
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    print(f"\n🔍 Searching for '{search_term}' in articles:")
    
    cursor.execute("""
        SELECT 
            a.numero_articolo,
            a.tipo_versione,
            a.numero_aggiornamento,
            LEFT(a.testo_completo, 150) as preview,
            CASE WHEN a.articolo_base_id IS NULL THEN 'Base' ELSE 'Update' END as tipo
        FROM articoli a
        WHERE a.testo_completo LIKE ?
        ORDER BY a.numero_articolo, COALESCE(a.numero_aggiornamento, 0)
        LIMIT 10
    """, [f'%{search_term}%'])
    
    results = cursor.fetchall()
    
    if results:
        headers = ['Article', 'Version', 'Update#', 'Text Preview', 'Type']
        table_data = []
        
        for row in results:
            table_data.append([
                row[0],  # numero_articolo
                row[1],  # tipo_versione
                row[2] if row[2] is not None else '-',  # numero_aggiornamento
                f"{row[3]}...",  # preview
                row[4]   # tipo
            ])
        
        print(simple_table(table_data, headers))
    else:
        print("No articles found containing that term")
    
    conn.close()

def main():
    """Main function with menu"""
    
    print("🗂️  Simplified Versioning System Utility")
    print("=" * 50)
    
    while True:
        print("\nChoose an option:")
        print("1. Show versions of a specific article")
        print("2. Show sample articles with versions")
        print("3. Show versioning statistics")
        print("4. Search articles")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            article_num = input("Enter article number: ").strip()
            show_article_versions(article_num)
        
        elif choice == '2':
            show_article_versions()
        
        elif choice == '3':
            show_versioning_stats()
        
        elif choice == '4':
            search_term = input("Enter search term: ").strip()
            if search_term:
                search_article_updates(search_term)
        
        elif choice == '5':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
