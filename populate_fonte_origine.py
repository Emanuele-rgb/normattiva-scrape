#!/usr/bin/env python3
"""
Script to populate the fonte_origine column in the articoli table.
This script analyzes the existing articles and assigns appropriate source origins.
"""

import sqlite3
import re
from typing import Dict, List, Optional

class FonteOriginePopulator:
    def __init__(self, db_path: str = 'data.sqlite'):
        """Initialize the populator with database connection."""
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def disconnect(self):
        """Disconnect from the database."""
        if self.conn:
            self.conn.close()
            
    def add_fonte_origine_column(self):
        """Add the fonte_origine column if it doesn't exist."""
        cursor = self.conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(articoli)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'fonte_origine' not in columns:
            print("Adding fonte_origine column...")
            cursor.execute("ALTER TABLE articoli ADD COLUMN fonte_origine VARCHAR(100)")
            self.conn.commit()
            print("✅ Column added successfully")
        else:
            print("Column fonte_origine already exists")
            
    def analyze_article_structure(self, article_text: str, article_number: str) -> str:
        """
        Analyze article text and number to determine the source origin.
        
        Args:
            article_text: The full text of the article
            article_number: The article number (e.g., "1", "Agreement", "Protocol")
            
        Returns:
            The appropriate fonte_origine value
        """
        # Convert to lowercase for analysis
        text_lower = article_text.lower() if article_text else ""
        number_lower = article_number.lower() if article_number else ""
        
        # Check for Allegato in the article number (like "Allegato-Allegato 1")
        if "allegato" in number_lower:
            return "Allegati"
            
        # Check for Allegato in the article text content
        if text_lower.startswith("allegato"):
            # Check if it's part of an update (agg.1, orig., etc.)
            if any(prefix in number_lower for prefix in ["agg.", "orig."]):
                return "Allegati"
            else:
                return "Allegati"
        
        # Check for specific patterns in the text content
        if "agreement" in text_lower or "accordo" in text_lower:
            if "promozione" in text_lower or "investimento" in text_lower:
                return "Allegati > Agreement"
            elif "protocol" in text_lower or "protocollo" in text_lower:
                return "Allegati > Protocol"
            else:
                return "Allegati > Accordo"
                
        # Check if it's from Protocol section
        if "protocol" in text_lower or "protocollo" in text_lower:
            return "Allegati > Protocol"
            
        # Check if it's a standard article number (1, 2, 3, etc.)
        if re.match(r'^\d+$', number_lower):
            return "Articoli"
            
        # Check if it's versioned articles (agg.1, agg.2, etc.)
        if re.match(r'^agg\.\d+$', number_lower):
            return "Articoli"
            
        # Check if it's original versions (orig.)
        if number_lower == "orig.":
            return "Articoli"
            
        # Default fallback
        return "Articoli"
        
    def populate_fonte_origine(self):
        """Populate the fonte_origine column for all articles."""
        cursor = self.conn.cursor()
        
        # Get all articles
        cursor.execute("""
            SELECT id, numero_articolo, testo_completo, titoloAtto, url_documento
            FROM articoli
        """)
        
        articles = cursor.fetchall()
        
        if not articles:
            print("No articles found in the database.")
            return
            
        print(f"Processing {len(articles)} articles...")
        
        updated_count = 0
        for article in articles:
            article_id = article['id']
            numero_articolo = article['numero_articolo']
            testo_completo = article['testo_completo']
            titolo_atto = article['titoloAtto']
            url_documento = article['url_documento']
            
            # Determine fonte_origine
            fonte_origine = self.analyze_article_structure(
                testo_completo, numero_articolo
            )
            
            # Additional analysis based on titoloAtto and URL
            if titolo_atto and url_documento:
                if "investimenti" in titolo_atto.lower() or "agreement" in url_documento.lower():
                    if numero_articolo and re.match(r'^\d+$', numero_articolo):
                        fonte_origine = "Allegati > Accordo"
                        
            # Update the article
            cursor.execute("""
                UPDATE articoli 
                SET fonte_origine = ?
                WHERE id = ?
            """, (fonte_origine, article_id))
            
            updated_count += 1
            
            print(f"Article {numero_articolo} -> {fonte_origine}")
            
        self.conn.commit()
        print(f"✅ Updated {updated_count} articles")
        
    def populate_based_on_url_patterns(self):
        """
        Populate fonte_origine based on URL patterns and document structure.
        This method is useful when we have specific URL patterns to identify sections.
        """
        cursor = self.conn.cursor()
        
        # Update based on URL patterns
        patterns = [
            ("allegati", "Agreement", "Allegati > Agreement"),
            ("allegati", "Protocol", "Allegati > Protocol"),
            ("allegati", "Accordo", "Allegati > Accordo"),
            ("allegati", "Protocollo", "Allegati > Protocollo"),
        ]
        
        for url_pattern, section_pattern, fonte_value in patterns:
            cursor.execute("""
                UPDATE articoli 
                SET fonte_origine = ?
                WHERE (url_documento LIKE ? OR 
                       testo_completo LIKE ? OR 
                       titoloAtto LIKE ?)
                  AND fonte_origine IS NULL
            """, (fonte_value, f"%{url_pattern}%", f"%{section_pattern}%", f"%{section_pattern}%"))
            
            updated = cursor.rowcount
            if updated > 0:
                print(f"Updated {updated} articles for {fonte_value}")
                
        self.conn.commit()
        
    def set_default_values(self):
        """Set default values for articles without fonte_origine."""
        cursor = self.conn.cursor()
        
        # Set default to "Articoli" for articles without fonte_origine
        cursor.execute("""
            UPDATE articoli 
            SET fonte_origine = 'Articoli'
            WHERE fonte_origine IS NULL
        """)
        
        updated = cursor.rowcount
        if updated > 0:
            print(f"Set default 'Articoli' for {updated} articles")
            
        self.conn.commit()
        
    def show_statistics(self):
        """Show statistics about the fonte_origine distribution."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT fonte_origine, COUNT(*) as count
            FROM articoli
            GROUP BY fonte_origine
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        
        print("\n📊 FONTE ORIGINE DISTRIBUTION:")
        print("=" * 50)
        total = 0
        for row in results:
            fonte = row['fonte_origine'] or 'NULL'
            count = row['count']
            total += count
            print(f"  {fonte}: {count} articles")
            
        print(f"  TOTAL: {total} articles")
        
    def run_full_population(self):
        """Run the complete population process."""
        try:
            self.connect()
            
            print("🚀 Starting fonte_origine population process...")
            print("=" * 50)
            
            # Add column if needed
            self.add_fonte_origine_column()
            
            # Populate based on analysis
            self.populate_fonte_origine()
            
            # Populate based on URL patterns
            self.populate_based_on_url_patterns()
            
            # Set default values
            self.set_default_values()
            
            # Show statistics
            self.show_statistics()
            
            print("\n✅ Fonte origine population completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during population: {e}")
            if self.conn:
                self.conn.rollback()
                
        finally:
            self.disconnect()


def main():
    """Main execution function."""
    populator = FonteOriginePopulator()
    populator.run_full_population()


if __name__ == "__main__":
    main()
