#!/usr/bin/env python3
"""
Database Status Checker
Monitors the progress of database population and provides statistics
"""

import sqlite3
import json
from datetime import datetime
from collections import defaultdict

def check_database_status():
    """Check the current status of the database"""
    print("📊 NORMATTIVA DATABASE STATUS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Basic statistics
        cursor.execute("SELECT COUNT(*) FROM documenti_normativi")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articoli")
        art_count = cursor.fetchone()[0]
        
        print(f"📋 Total Documents: {doc_count}")
        print(f"📜 Total Articles: {art_count}")
        
        if doc_count == 0:
            print("⚠️ Database is empty. Run population script first.")
            return
        
        # Documents by year
        print(f"\n📅 Documents by Year:")
        cursor.execute("""
            SELECT anno, COUNT(*) as count 
            FROM documenti_normativi 
            GROUP BY anno 
            ORDER BY anno DESC
        """)
        year_stats = cursor.fetchall()
        
        for year, count in year_stats:
            print(f"   {year}: {count} documents")
        
        # Documents by type
        print(f"\n📋 Documents by Type:")
        cursor.execute("""
            SELECT tipo_atto, COUNT(*) as count 
            FROM documenti_normativi 
            GROUP BY tipo_atto 
            ORDER BY count DESC
            LIMIT 10
        """)
        type_stats = cursor.fetchall()
        
        for tipo, count in type_stats:
            print(f"   {tipo}: {count}")
        
        # Articles with content
        cursor.execute("SELECT COUNT(*) FROM articoli WHERE testo_completo IS NOT NULL AND LENGTH(testo_completo) > 0")
        articles_with_content = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articoli WHERE testo_pulito IS NOT NULL AND LENGTH(testo_pulito) > 0")
        articles_with_clean_text = cursor.fetchone()[0]
        
        print(f"\n📝 Content Quality:")
        print(f"   Articles with content: {articles_with_content}")
        print(f"   Articles with clean text: {articles_with_clean_text}")
        
        # Check AI enhancements
        print(f"\n🤖 AI Enhancement Status:")
        
        # Check for embeddings
        cursor.execute("SELECT COUNT(*) FROM articoli WHERE embedding_articolo IS NOT NULL")
        articles_with_embeddings = cursor.fetchone()[0]
        print(f"   Articles with embeddings: {articles_with_embeddings}")
        
        # Check for classifications
        cursor.execute("SELECT COUNT(*) FROM articoli WHERE tipo_norma IS NOT NULL")
        articles_classified = cursor.fetchone()[0]
        print(f"   Articles classified: {articles_classified}")
        
        # Check for commi
        try:
            cursor.execute("SELECT COUNT(*) FROM commi")
            commi_count = cursor.fetchone()[0]
            print(f"   Commi extracted: {commi_count}")
        except:
            print(f"   Commi extracted: 0 (table not found)")
        
        # Check for citations
        try:
            cursor.execute("SELECT COUNT(*) FROM citazioni_normative")
            citations_count = cursor.fetchone()[0]
            print(f"   Citations extracted: {citations_count}")
        except:
            print(f"   Citations extracted: 0 (table not found)")
        
        # Check for document categorization
        try:
            cursor.execute("SELECT COUNT(*) FROM documento_categorie")
            doc_categories = cursor.fetchone()[0]
            print(f"   Document categorizations: {doc_categories}")
        except:
            print(f"   Document categorizations: 0 (table not found)")
        
        # Recent activity
        print(f"\n⏰ Recent Activity:")
        cursor.execute("""
            SELECT created_at, COUNT(*) as count 
            FROM documenti_normativi 
            WHERE created_at IS NOT NULL 
            GROUP BY DATE(created_at) 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_activity = cursor.fetchall()
        
        for date, count in recent_activity:
            print(f"   {date}: {count} documents added")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if doc_count < 50:
            print("   📈 Consider running more years to build a comprehensive dataset")
            print("   🧪 Run: python test_multi_year.py (for testing)")
            print("   🚀 Run: python populate_multi_year.py (for full population)")
        
        if articles_with_embeddings == 0:
            print("   🤖 Run Legal AI Enhancer to add AI features:")
            print("   🎯 Run: python legal_ai_enhancer.py")
        
        if articles_classified == 0:
            print("   🏷️ Articles need classification - run AI enhancer")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        print("💡 Try running: python clear_database.py to reset")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    check_database_status()
    
    print(f"\n🔄 Status checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💡 Run this script anytime to check progress: python check_status.py")

if __name__ == "__main__":
    main()
