#!/usr/bin/env python3
"""
Script to scrape and populate fonte_origine based on actual document structure.
This script analyzes the specific URL structure from normattiva.it
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Tuple
import time

class NormattivaScraper:
    def __init__(self, db_path: str = 'data.sqlite'):
        """Initialize the scraper with database connection."""
        self.db_path = db_path
        self.conn = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def connect(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def disconnect(self):
        """Disconnect from the database."""
        if self.conn:
            self.conn.close()
            
    def scrape_document_structure(self, url: str) -> Dict[str, List[str]]:
        """
        Scrape the document structure to understand article organization.
        
        Args:
            url: The normattiva.it URL
            
        Returns:
            Dictionary mapping sections to article numbers
        """
        try:
            print(f"Scraping document structure from: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            structure = {
                'Articoli': [],
                'Allegati > Agreement': [],
                'Allegati > Protocol': [],
                'Allegati > Accordo': [],
                'Allegati > Protocollo': []
            }
            
            # Find the document structure
            current_section = None
            
            # Look for text patterns that indicate sections
            text_content = soup.get_text()
            lines = text_content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Identify section headers
                if line == 'Articoli':
                    current_section = 'Articoli'
                    continue
                elif line == 'Allegati':
                    current_section = 'Allegati'
                    continue
                elif line == 'Agreement' and current_section == 'Allegati':
                    current_section = 'Allegati > Agreement'
                    continue
                elif line == 'Protocol' and current_section == 'Allegati':
                    current_section = 'Allegati > Protocol'
                    continue
                elif line == 'Accordo' and current_section == 'Allegati':
                    current_section = 'Allegati > Accordo'
                    continue
                elif line == 'Protocollo' and current_section == 'Allegati':
                    current_section = 'Allegati > Protocollo'
                    continue
                    
                # Look for article numbers
                if current_section and current_section in structure:
                    # Match article patterns
                    if re.match(r'^\d+$', line):  # Simple number
                        structure[current_section].append(line)
                    elif re.match(r'^art\.\s*\d+$', line.lower()):  # art. X
                        art_num = re.search(r'\d+', line).group()
                        structure[current_section].append(art_num)
                        
            print("Document structure found:")
            for section, articles in structure.items():
                if articles:
                    print(f"  {section}: {len(articles)} articles")
                    
            return structure
            
        except Exception as e:
            print(f"Error scraping document structure: {e}")
            return {}
            
    def update_fonte_origine_from_structure(self, structure: Dict[str, List[str]]):
        """
        Update the fonte_origine column based on scraped structure.
        
        Args:
            structure: Dictionary mapping sections to article numbers
        """
        cursor = self.conn.cursor()
        
        # Get all articles in the database
        cursor.execute("""
            SELECT id, numero_articolo, testo_completo, titoloAtto
            FROM articoli
        """)
        
        articles = cursor.fetchall()
        
        if not articles:
            print("No articles found in database.")
            return
            
        print(f"Updating {len(articles)} articles based on structure...")
        
        updated_count = 0
        
        for article in articles:
            article_id = article['id']
            numero_articolo = article['numero_articolo']
            
            # Clean the article number for comparison
            clean_number = re.sub(r'[^\d]', '', numero_articolo) if numero_articolo else ""
            
            # Find which section this article belongs to
            fonte_origine = "Articoli"  # Default
            
            for section, article_numbers in structure.items():
                if clean_number in article_numbers or numero_articolo in article_numbers:
                    fonte_origine = section
                    break
                    
            # Special handling for specific patterns
            if numero_articolo:
                if numero_articolo.lower() == "agreement":
                    fonte_origine = "Allegati > Agreement"
                elif numero_articolo.lower() == "protocol":
                    fonte_origine = "Allegati > Protocol"
                elif numero_articolo.lower() == "protocollo":
                    fonte_origine = "Allegati > Protocollo"
                    
            # Update the article
            cursor.execute("""
                UPDATE articoli 
                SET fonte_origine = ?
                WHERE id = ?
            """, (fonte_origine, article_id))
            
            updated_count += 1
            print(f"  Article {numero_articolo} -> {fonte_origine}")
            
        self.conn.commit()
        print(f"✅ Updated {updated_count} articles")
        
    def populate_based_on_content_analysis(self):
        """
        Populate fonte_origine based on content analysis for investment agreements.
        """
        cursor = self.conn.cursor()
        
        # Investment-related keywords for Accordo section
        investment_keywords = [
            "investimento", "investimenti", "protezione", "promozione",
            "trattamento", "nazionale", "clausola", "nazione", "capitale",
            "rendimento", "trasferimento", "espropriazione", "compenso"
        ]
        
        # Get articles that might be from investment agreements
        cursor.execute("""
            SELECT id, numero_articolo, testo_completo, titoloAtto
            FROM articoli
            WHERE fonte_origine IS NULL OR fonte_origine = 'Articoli'
        """)
        
        articles = cursor.fetchall()
        updated_count = 0
        
        for article in articles:
            article_id = article['id']
            numero_articolo = article['numero_articolo']
            testo_completo = article['testo_completo'] or ""
            titolo_atto = article['titoloAtto'] or ""
            
            # Combine text for analysis
            full_text = (testo_completo + " " + titolo_atto).lower()
            
            # Check for investment-related content
            investment_score = sum(1 for keyword in investment_keywords if keyword in full_text)
            
            # If it's a numbered article with investment content, it's likely from Accordo
            if (re.match(r'^\d+$', numero_articolo or "") and 
                investment_score >= 2):
                
                cursor.execute("""
                    UPDATE articoli 
                    SET fonte_origine = 'Allegati > Accordo'
                    WHERE id = ?
                """, (article_id,))
                
                updated_count += 1
                print(f"  Article {numero_articolo} -> Allegati > Accordo (content analysis)")
                
        if updated_count > 0:
            self.conn.commit()
            print(f"✅ Updated {updated_count} articles based on content analysis")
            
    def run_population_with_url(self, url: str):
        """
        Run the complete population process using the provided URL.
        
        Args:
            url: The normattiva.it URL to analyze
        """
        try:
            self.connect()
            
            print("🚀 Starting fonte_origine population with URL analysis...")
            print("=" * 60)
            
            # Add column if needed
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA table_info(articoli)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'fonte_origine' not in columns:
                print("Adding fonte_origine column...")
                cursor.execute("ALTER TABLE articoli ADD COLUMN fonte_origine VARCHAR(100)")
                self.conn.commit()
                print("✅ Column added successfully")
            
            # Scrape document structure
            structure = self.scrape_document_structure(url)
            
            if structure:
                # Update based on structure
                self.update_fonte_origine_from_structure(structure)
                
                # Additional content analysis
                self.populate_based_on_content_analysis()
                
                # Set default values for remaining articles
                cursor.execute("""
                    UPDATE articoli 
                    SET fonte_origine = 'Articoli'
                    WHERE fonte_origine IS NULL
                """)
                
                updated = cursor.rowcount
                if updated > 0:
                    print(f"Set default 'Articoli' for {updated} remaining articles")
                    self.conn.commit()
                
                # Show statistics
                self.show_statistics()
                
            print("\n✅ Population completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during population: {e}")
            if self.conn:
                self.conn.rollback()
                
        finally:
            self.disconnect()
            
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


def main():
    """Main execution function."""
    url = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:2000;13!multivigente~"
    
    scraper = NormattivaScraper()
    scraper.run_population_with_url(url)


if __name__ == "__main__":
    main()
