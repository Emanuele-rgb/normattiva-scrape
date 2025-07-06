#!/usr/bin/env python3
"""
Article Updates Manager
Provides utilities to manage and view article updates
"""

import sqlite3
import sys
from datetime import datetime, timedelta

def show_article_modifications():
    """Show all article modifications in the database"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        query = """
        SELECT 
            m.id,
            a.numero_articolo,
            d.titoloAtto,
            m.tipo_modifica,
            m.data_modifica,
            m.descrizione_modifica,
            LENGTH(m.testo_precedente) as len_old,
            LENGTH(m.testo_nuovo) as len_new
        FROM modifiche_normative m
        JOIN articoli a ON m.articolo_modificato_id = a.id
        JOIN documenti_normativi d ON a.documento_id = d.id
        ORDER BY m.data_modifica DESC
        """
        
        cursor.execute(query)
        modifications = cursor.fetchall()
        
        if not modifications:
            print("📋 No article modifications found in database")
            return
        
        print(f"📋 Found {len(modifications)} article modifications:")
        print("-" * 100)
        print(f"{'ID':<5} {'Article':<10} {'Document':<30} {'Type':<15} {'Date':<12} {'Old':<6} {'New':<6} {'Description':<20}")
        print("-" * 100)
        
        for mod in modifications:
            mod_id, art_num, doc_title, tipo, data, desc, len_old, len_new = mod
            doc_title_short = (doc_title[:27] + "...") if len(doc_title) > 30 else doc_title
            desc_short = (desc[:17] + "...") if len(desc) > 20 else desc
            
            print(f"{mod_id:<5} {art_num:<10} {doc_title_short:<30} {tipo:<15} {data:<12} {len_old:<6} {len_new:<6} {desc_short:<20}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing modifications: {e}")

def show_modified_articles():
    """Show articles that have been modified"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        query = """
        SELECT DISTINCT
            a.id,
            a.numero_articolo,
            a.titoloAtto,
            a.status,
            a.data_ultima_modifica,
            d.titoloAtto as documento_titolo,
            COUNT(m.id) as num_modifications
        FROM articoli a
        JOIN documenti_normativi d ON a.documento_id = d.id
        LEFT JOIN modifiche_normative m ON a.id = m.articolo_modificato_id
        WHERE a.status IN ('modificato', 'sostituito') OR m.id IS NOT NULL
        GROUP BY a.id
        ORDER BY a.data_ultima_modifica DESC
        """
        
        cursor.execute(query)
        articles = cursor.fetchall()
        
        if not articles:
            print("📋 No modified articles found in database")
            return
        
        print(f"📋 Found {len(articles)} modified articles:")
        print("-" * 120)
        print(f"{'ID':<5} {'Art#':<8} {'Status':<12} {'Modifications':<13} {'Last Modified':<15} {'Document':<30} {'Article Title':<30}")
        print("-" * 120)
        
        for article in articles:
            art_id, art_num, art_title, status, last_mod, doc_title, num_mods = article
            
            art_title_short = (art_title[:27] + "...") if art_title and len(art_title) > 30 else (art_title or "")
            doc_title_short = (doc_title[:27] + "...") if len(doc_title) > 30 else doc_title
            
            print(f"{art_id:<5} {art_num:<8} {status:<12} {num_mods:<13} {last_mod or 'N/A':<15} {doc_title_short:<30} {art_title_short:<30}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing modified articles: {e}")

def show_modification_details(modification_id):
    """Show detailed information about a specific modification"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        query = """
        SELECT 
            m.id,
            m.tipo_modifica,
            m.data_modifica,
            m.descrizione_modifica,
            m.testo_precedente,
            m.testo_nuovo,
            a.numero_articolo,
            a.titoloAtto as articolo_titolo,
            d.titoloAtto as documento_titolo,
            d.numero,
            d.anno
        FROM modifiche_normative m
        JOIN articoli a ON m.articolo_modificato_id = a.id
        JOIN documenti_normativi d ON a.documento_id = d.id
        WHERE m.id = ?
        """
        
        cursor.execute(query, [modification_id])
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ Modification with ID {modification_id} not found")
            return
        
        (mod_id, tipo, data, desc, testo_old, testo_new, art_num, art_title, 
         doc_title, doc_num, doc_anno) = result
        
        print(f"📋 Modification Details (ID: {mod_id})")
        print("=" * 60)
        print(f"Document: {doc_title}")
        print(f"Document Number: {doc_num}/{doc_anno}")
        print(f"Article: {art_num} - {art_title}")
        print(f"Modification Type: {tipo}")
        print(f"Date: {data}")
        print(f"Description: {desc}")
        print()
        
        if testo_old:
            print("📄 PREVIOUS TEXT:")
            print("-" * 40)
            print(testo_old[:500] + ("..." if len(testo_old) > 500 else ""))
            print()
        
        if testo_new:
            print("📄 NEW TEXT:")
            print("-" * 40)
            print(testo_new[:500] + ("..." if len(testo_new) > 500 else ""))
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing modification details: {e}")

def clean_old_modifications(days=365):
    """Clean modifications older than specified days"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        # Count modifications to be deleted
        cursor.execute("SELECT COUNT(*) FROM modifiche_normative WHERE data_modifica < ?", [cutoff_str])
        count_to_delete = cursor.fetchone()[0]
        
        if count_to_delete == 0:
            print(f"📋 No modifications older than {days} days found")
            return
        
        print(f"⚠️ Found {count_to_delete} modifications older than {days} days")
        response = input("Do you want to delete them? (type 'yes' to confirm): ")
        
        if response.lower() == 'yes':
            cursor.execute("DELETE FROM modifiche_normative WHERE data_modifica < ?", [cutoff_str])
            deleted = cursor.rowcount
            conn.commit()
            print(f"✅ Deleted {deleted} old modifications")
        else:
            print("❌ Operation cancelled")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error cleaning old modifications: {e}")

def export_modifications_csv(filename=None):
    """Export modifications to CSV file"""
    try:
        import csv
        from datetime import datetime
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"article_modifications_{timestamp}.csv"
        
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        query = """
        SELECT 
            m.id,
            d.numero || '/' || d.anno as documento,
            d.titoloAtto as documento_titolo,
            a.numero_articolo,
            a.titoloAtto as articolo_titolo,
            m.tipo_modifica,
            m.data_modifica,
            m.descrizione_modifica,
            m.testo_precedente,
            m.testo_nuovo
        FROM modifiche_normative m
        JOIN articoli a ON m.articolo_modificato_id = a.id
        JOIN documenti_normativi d ON a.documento_id = d.id
        ORDER BY m.data_modifica DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        if not results:
            print("📋 No modifications to export")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'ID', 'Document', 'Document Title', 'Article Number', 'Article Title',
                'Modification Type', 'Date', 'Description', 'Previous Text', 'New Text'
            ])
            
            # Write data
            for row in results:
                writer.writerow(row)
        
        print(f"✅ Exported {len(results)} modifications to {filename}")
        conn.close()
        
    except Exception as e:
        print(f"❌ Error exporting modifications: {e}")

def show_statistics():
    """Show detailed statistics about article modifications"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        print("📊 Article Modifications Statistics")
        print("=" * 40)
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM modifiche_normative")
        total_mods = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT articolo_modificato_id) FROM modifiche_normative")
        unique_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT documento_modificante_id) FROM modifiche_normative")
        unique_docs = cursor.fetchone()[0]
        
        print(f"Total Modifications: {total_mods}")
        print(f"Unique Articles Modified: {unique_articles}")
        print(f"Unique Modifying Documents: {unique_docs}")
        print()
        
        # By type
        cursor.execute("""
            SELECT tipo_modifica, COUNT(*) 
            FROM modifiche_normative 
            GROUP BY tipo_modifica 
            ORDER BY COUNT(*) DESC
        """)
        by_type = cursor.fetchall()
        
        if by_type:
            print("By Modification Type:")
            for tipo, count in by_type:
                print(f"  {tipo}: {count}")
            print()
        
        # By month
        cursor.execute("""
            SELECT strftime('%Y-%m', data_modifica) as month, COUNT(*) 
            FROM modifiche_normative 
            WHERE data_modifica IS NOT NULL
            GROUP BY month 
            ORDER BY month DESC 
            LIMIT 12
        """)
        by_month = cursor.fetchall()
        
        if by_month:
            print("Recent Activity (by month):")
            for month, count in by_month:
                print(f"  {month}: {count}")
            print()
        
        # Recent activity
        cursor.execute("""
            SELECT COUNT(*) 
            FROM modifiche_normative 
            WHERE data_modifica >= date('now', '-7 days')
        """)
        recent_week = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM modifiche_normative 
            WHERE data_modifica >= date('now', '-30 days')
        """)
        recent_month = cursor.fetchone()[0]
        
        print(f"Recent Activity:")
        print(f"  Last 7 days: {recent_week}")
        print(f"  Last 30 days: {recent_month}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing statistics: {e}")

def show_help():
    """Show help information"""
    print("""
🔧 Article Updates Manager

Usage:
  python article_updates_manager.py [command] [options]

Commands:
  list        - Show all article modifications
  articles    - Show modified articles
  details <id> - Show details of specific modification
  stats       - Show detailed statistics  
  export [file] - Export modifications to CSV
  clean [days] - Clean old modifications (default: 365 days)
  help        - Show this help

Examples:
  python article_updates_manager.py list
  python article_updates_manager.py details 5
  python article_updates_manager.py export my_export.csv
  python article_updates_manager.py clean 180
""")

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        command = "list"
    else:
        command = sys.argv[1].lower()
    
    if command == "list":
        show_article_modifications()
    elif command == "articles":
        show_modified_articles()
    elif command == "details":
        if len(sys.argv) >= 3:
            try:
                mod_id = int(sys.argv[2])
                show_modification_details(mod_id)
            except ValueError:
                print("❌ Invalid modification ID. Must be a number.")
        else:
            print("❌ Please provide a modification ID")
    elif command == "stats":
        show_statistics()
    elif command == "export":
        filename = sys.argv[2] if len(sys.argv) >= 3 else None
        export_modifications_csv(filename)
    elif command == "clean":
        days = int(sys.argv[2]) if len(sys.argv) >= 3 else 365
        clean_old_modifications(days)
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()
