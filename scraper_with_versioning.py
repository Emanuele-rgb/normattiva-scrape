#!/usr/bin/env python3
"""
Enhanced scraper for NORME-NET with full article versioning support
Handles original content (orig.) and all updates (agg.1, agg.2, etc.) with validity dates
"""

import re
import json
import sqlite3
from datetime import datetime, date
import lxml.html
import requests
import sys
from urllib.parse import urljoin, urlparse, parse_qs
import time
from collections import OrderedDict

normattiva_url = "http://www.normattiva.it"

# ========================================
# DATABASE INITIALIZATION WITH VERSIONING
# ========================================

def init_versioning_database():
    """Initialize database with versioning support"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Check if versioning tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articoli_versioni'")
        if not cursor.fetchone():
            print("Initializing versioning database schema...")
            with open("enhanced_schema_versioning.sql", "r", encoding="utf-8") as f:
                schema_sql = f.read()
            
            conn.executescript(schema_sql)
            conn.commit()
            print("✓ Versioning database schema initialized successfully")
        else:
            print("✓ Using existing versioning database schema")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error initializing versioning database: {e}")
        raise

# ========================================
# TEXT PROCESSING AND CORRELATION EXTRACTION
# ========================================

def clean_article_text(text):
    """Clean article text by removing extra whitespace and normalizing"""
    if not text:
        return ""
    
    # Remove multiple whitespaces and normalize line breaks
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # Remove common artifacts
    text = re.sub(r'\s*\.\s*\n', '.\n', text)
    text = re.sub(r'\s*;\s*\n', ';\n', text)
    
    # Clean up common legal document artifacts
    text = re.sub(r'\s*\(\s*\)', '', text)  # Empty parentheses
    text = re.sub(r'\s*\[\s*\]', '', text)  # Empty brackets
    
    return text.strip()

def extract_correlated_articles(body_element):
    """Extract correlated articles from links within the bodyTesto div"""
    try:
        correlated_articles = []
        
        # Find all links within the bodyTesto
        links = body_element.xpath('.//a[@href]')
        
        for link in links:
            href = link.get('href')
            link_text = link.text_content().strip()
            
            if not href or not link_text:
                continue
            
            # Check if link refers to an article (common patterns)
            article_patterns = [
                r'art\.\s*(\d+)',  # art. 123
                r'articolo\s+(\d+)',  # articolo 123
                r'art\s+(\d+)',  # art 123
                r'comma\s+(\d+)',  # comma 123
                r'lettera\s+([a-z])',  # lettera a
            ]
            
            # Extract article references from link text
            for pattern in article_patterns:
                matches = re.findall(pattern, link_text, re.IGNORECASE)
                for match in matches:
                    article_ref = {
                        'text': link_text,
                        'href': href,
                        'article_number': match,
                        'type': 'article_reference'
                    }
                    
                    # Avoid duplicates
                    if not any(ref['href'] == href and ref['article_number'] == match 
                             for ref in correlated_articles):
                        correlated_articles.append(article_ref)
            
            # Also check if the href contains article references
            if 'art' in href.lower() or 'articolo' in href.lower():
                # Extract from URL
                url_match = re.search(r'art[^0-9]*(\d+)', href, re.IGNORECASE)
                if url_match:
                    article_ref = {
                        'text': link_text,
                        'href': href,
                        'article_number': url_match.group(1),
                        'type': 'url_reference'
                    }
                    
                    # Avoid duplicates
                    if not any(ref['href'] == href for ref in correlated_articles):
                        correlated_articles.append(article_ref)
        
        print(f"🔗 Found {len(correlated_articles)} correlated articles")
        return correlated_articles
        
    except Exception as e:
        print(f"❌ Error extracting correlated articles: {e}")
        return []

# ========================================
# ENHANCED ARTICLE PROCESSING WITH VERSIONS
# ========================================

def extract_article_with_versions(article_element, document_id, session):
    """
    Extract article with all its versions (original + aggiornamenti)
    
    Args:
        article_element: lxml element containing the article
        document_id: ID of the document in database
        session: requests session for fetching updates
        
    Returns:
        dict: Complete article data with all versions
    """
    try:
        # Extract basic article information
        article_data = extract_basic_article_info(article_element)
        if not article_data:
            return None
        
        # Look for "aggiornamenti all'articolo" button
        updates_url = detect_article_updates_button(article_element)
        
        versions = []
        
        # Extract original version (orig.)
        original_version = extract_original_version(article_element, document_id)
        if original_version:
            versions.append(original_version)
        
        # Extract all aggiornamenti versions if updates button exists
        if updates_url:
            print(f"🔍 Found updates button for article {article_data.get('numero_articolo', 'N/A')}")
            aggiornamenti_versions = extract_aggiornamenti_versions(updates_url, session, document_id)
            versions.extend(aggiornamenti_versions)
        
        # Combine article data with versions
        article_data['versions'] = versions
        article_data['document_id'] = document_id
        
        return article_data
        
    except Exception as e:
        print(f"❌ Error extracting article with versions: {e}")
        return None

def extract_basic_article_info(article_element):
    """Extract basic article information (number, title, etc.)"""
    try:
        # Extract article number
        numero_articolo = None
        
        # Try various selectors for article number
        number_patterns = [
            './/strong[contains(text(), "Art.")]',
            './/h1[contains(text(), "Art.")]',
            './/h2[contains(text(), "Art.")]',
            './/span[contains(@class, "articolo")]'
        ]
        
        for pattern in number_patterns:
            elements = article_element.xpath(pattern)
            if elements:
                text = elements[0].text_content().strip()
                match = re.search(r'Art\.\s*(\d+)', text, re.IGNORECASE)
                if match:
                    numero_articolo = match.group(1)
                    break
        
        if not numero_articolo:
            # Fallback: try to find any number
            text = article_element.text_content()
            match = re.search(r'(?:Art\.|Articolo)\s*(\d+)', text, re.IGNORECASE)
            if match:
                numero_articolo = match.group(1)
        
        # Extract title/rubrica
        title_elements = article_element.xpath('.//h1 | .//h2 | .//h3 | .//strong')
        titolo = ""
        rubrica = ""
        
        for elem in title_elements:
            text = elem.text_content().strip()
            if text and not text.startswith("Art.") and len(text) > 5:
                if not titolo:
                    titolo = text
                elif not rubrica and text != titolo:
                    rubrica = text
                    break
        
        return {
            'numero_articolo': numero_articolo or "1",
            'titolo': titolo[:500] if titolo else "",
            'rubrica': rubrica[:500] if rubrica else ""
        }
        
    except Exception as e:
        print(f"❌ Error extracting basic article info: {e}")
        return None

def extract_original_version(article_element, document_id):
    """Extract the original version (orig.) of the article from bodyTesto div"""
    try:
        # Look for bodyTesto div - this contains the actual article text
        body_testo = article_element.xpath('.//div[contains(@class, "bodyTesto")]')
        
        if not body_testo:
            # Fallback: look for original content section with "orig." text
            original_sections = article_element.xpath('.//*[contains(text(), "orig.")]')
            
            if original_sections:
                original_section = original_sections[0]
                # Try to find bodyTesto in the vicinity
                parent_container = original_section.getparent()
                while parent_container is not None:
                    body_testo = parent_container.xpath('.//div[contains(@class, "bodyTesto")]')
                    if body_testo:
                        break
                    parent_container = parent_container.getparent()
            
            if not body_testo:
                print("⚠️ No bodyTesto div found for original version")
                return None
        
        # Extract content from bodyTesto div
        body_div = body_testo[0]
        
        # Get the complete text content
        testo_completo = body_div.text_content().strip()
        
        # Clean the text (remove extra whitespace, normalize)
        testo_pulito = clean_article_text(testo_completo)
        
        # Extract correlated articles from links within bodyTesto
        articoli_correlati = extract_correlated_articles(body_div)
        
        # Remove any "orig." prefix if present
        testo_completo = re.sub(r'^orig\.\s*', '', testo_completo, flags=re.IGNORECASE)
        testo_pulito = re.sub(r'^orig\.\s*', '', testo_pulito, flags=re.IGNORECASE)
        
        return {
            'tipo_versione': 'orig',
            'numero_aggiornamento': None,
            'testo_versione': testo_completo,
            'testo_pulito': testo_pulito,
            'articoli_correlati': articoli_correlati,
            'data_inizio_vigore': datetime.now().date(),  # Will be updated with actual date
            'data_fine_vigore': None,
            'is_current': True,
            'status': 'vigente'
        }
        
    except Exception as e:
        print(f"❌ Error extracting original version: {e}")
        return None

def detect_article_updates_button(article_element):
    """Detect if the article has an updates button and return its URL"""
    try:
        # Look for the "aggiornamenti all'articolo" button
        update_buttons = article_element.xpath('.//button[contains(text(), "aggiornamenti all\'articolo")] | .//a[contains(text(), "aggiornamenti all\'articolo")]')
        
        if not update_buttons:
            # Try alternative patterns
            update_buttons = article_element.xpath('.//button[contains(text(), "aggiornamenti")] | .//a[contains(text(), "aggiornamenti")]')
        
        if not update_buttons:
            # Try data attributes
            update_buttons = article_element.xpath('.//*[@data-action="show-updates"] | .//*[contains(@class, "aggiornamenti")]')
        
        if update_buttons:
            button = update_buttons[0]
            
            # Check for href
            href = button.get('href')
            if href:
                return href
            
            # Check onclick for URL
            onclick = button.get('onclick', '')
            if onclick:
                url_match = re.search(r'["\']([^"\']*aggiornamenti[^"\']*)["\']', onclick)
                if url_match:
                    return url_match.group(1)
            
            # Check data attributes
            data_url = button.get('data-url') or button.get('data-href')
            if data_url:
                return data_url
            
            # Look for parent link
            parent_link = button.xpath('./ancestor::a[@href]')
            if parent_link:
                return parent_link[0].get('href')
        
        return None
        
    except Exception as e:
        print(f"❌ Error detecting updates button: {e}")
        return None

def extract_aggiornamenti_versions(updates_url, session, document_id):
    """Extract all aggiornamenti versions from the updates page"""
    try:
        if not updates_url.startswith('http'):
            updates_url = urljoin(normattiva_url, updates_url)
        
        print(f"🔍 Fetching aggiornamenti from: {updates_url}")
        
        response = session.get(updates_url)
        response.raise_for_status()
        
        updates_page = lxml.html.fromstring(response.content)
        versions = []
        
        # Look for aggiornamento sections (agg.1, agg.2, etc.)
        agg_sections = updates_page.xpath('.//*[contains(text(), "agg.")]')
        
        for i, agg_section in enumerate(agg_sections, 1):
            try:
                # Extract version identifier (agg.1, agg.2, etc.)
                agg_text = agg_section.text_content().strip()
                agg_match = re.search(r'agg\.(\d+)', agg_text, re.IGNORECASE)
                
                if agg_match:
                    agg_number = int(agg_match.group(1))
                    tipo_versione = f"agg.{agg_number}"
                else:
                    agg_number = i
                    tipo_versione = f"agg.{i}"
                
                # Look for bodyTesto div in the aggiornamento section
                parent_container = agg_section.getparent()
                body_testo = None
                
                # Search for bodyTesto in the vicinity of the aggiornamento
                search_element = parent_container
                while search_element is not None and body_testo is None:
                    body_testo_divs = search_element.xpath('.//div[contains(@class, "bodyTesto")]')
                    if body_testo_divs:
                        body_testo = body_testo_divs[0]
                        break
                    search_element = search_element.getparent()
                
                if body_testo is not None:
                    # Extract from bodyTesto
                    testo_completo = body_testo.text_content().strip()
                    testo_pulito = clean_article_text(testo_completo)
                    articoli_correlati = extract_correlated_articles(body_testo)
                else:
                    # Fallback to parent container text
                    testo_completo = parent_container.text_content().strip() if parent_container else ""
                    testo_pulito = clean_article_text(testo_completo)
                    articoli_correlati = []
                
                # Clean up the content (remove agg.X prefix)
                testo_completo = re.sub(r'^agg\.\d+\s*', '', testo_completo, flags=re.IGNORECASE)
                testo_pulito = re.sub(r'^agg\.\d+\s*', '', testo_pulito, flags=re.IGNORECASE)
                
                # Extract validity dates from the content or surrounding elements
                validity_dates = extract_validity_dates_from_content(parent_container or agg_section)
                
                version_data = {
                    'tipo_versione': tipo_versione,
                    'numero_aggiornamento': agg_number,
                    'testo_versione': testo_completo,
                    'testo_pulito': testo_pulito,
                    'articoli_correlati': articoli_correlati,
                    'data_inizio_vigore': validity_dates.get('inizio') or datetime.now().date(),
                    'data_fine_vigore': validity_dates.get('fine'),
                    'is_current': False,  # Will be updated later
                    'status': 'vigente'
                }
                
                versions.append(version_data)
                print(f"✓ Extracted {tipo_versione} with {len(articoli_correlati)} correlated articles")
                
            except Exception as e:
                print(f"❌ Error extracting aggiornamento {i}: {e}")
                continue
        
        # Mark the latest version as current
        if versions:
            versions[-1]['is_current'] = True
            # Mark previous versions as superseded
            for version in versions[:-1]:
                version['is_current'] = False
                version['status'] = 'sostituito'
        
        print(f"✓ Extracted {len(versions)} aggiornamenti versions")
        return versions
        
    except Exception as e:
        print(f"❌ Error extracting aggiornamenti versions: {e}")
        return []

def extract_validity_dates_from_content(element):
    """Extract validity dates from element content"""
    try:
        text = element.text_content()
        dates = {}
        
        # Look for "Testo in vigore dal: DD-MM-YYYY"
        vigor_match = re.search(r'Testo in vigore dal:\s*(\d{1,2}-\d{1,2}-\d{4})', text)
        if vigor_match:
            try:
                dates['inizio'] = datetime.strptime(vigor_match.group(1), '%d-%m-%Y').date()
            except ValueError:
                pass
        
        # Look for "al: DD-MM-YYYY"
        end_match = re.search(r'al:\s*(\d{1,2}-\d{1,2}-\d{4})', text)
        if end_match:
            try:
                dates['fine'] = datetime.strptime(end_match.group(1), '%d-%m-%Y').date()
            except ValueError:
                pass
        
        # Alternative patterns
        if not dates.get('inizio'):
            # Look for other date patterns
            date_patterns = [
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}-\d{1,2}-\d{4})',
                r'(\d{4}-\d{1,2}-\d{1,2})'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    for match in matches:
                        try:
                            if '/' in match:
                                date_obj = datetime.strptime(match, '%d/%m/%Y').date()
                            elif '-' in match and match.count('-') == 2:
                                if match.startswith('20') or match.startswith('19'):
                                    date_obj = datetime.strptime(match, '%Y-%m-%d').date()
                                else:
                                    date_obj = datetime.strptime(match, '%d-%m-%Y').date()
                            else:
                                continue
                            
                            if not dates.get('inizio'):
                                dates['inizio'] = date_obj
                            elif not dates.get('fine') and date_obj > dates['inizio']:
                                dates['fine'] = date_obj
                                
                        except ValueError:
                            continue
        
        return dates
        
    except Exception as e:
        print(f"❌ Error extracting validity dates: {e}")
        return {}

# ========================================
# DATABASE OPERATIONS FOR VERSIONING
# ========================================

def save_article_with_versions(article_data):
    """Save article with all its versions to the database"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Get current version data for main article record
        current_version = None
        for version in article_data['versions']:
            if version.get('is_current', False):
                current_version = version
                break
        
        # If no current version found, use the last one
        if not current_version and article_data['versions']:
            current_version = article_data['versions'][-1]
        
        # Prepare article data
        testo_completo = current_version.get('testo_versione', '') if current_version else ''
        articoli_correlati_json = json.dumps(current_version.get('articoli_correlati', [])) if current_version else '[]'
        
        # Insert the main article record with complete data
        article_insert = """
            INSERT INTO articoli (
                documento_id, numero_articolo, titoloAtto, rubrica,
                testo_completo, articoli_correlati,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'vigente', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        
        cursor.execute(article_insert, [
            article_data['document_id'],
            article_data['numero_articolo'],
            article_data['titoloAtto'],
            article_data['rubrica'],
            testo_completo,
            articoli_correlati_json
        ])
        
        article_id = cursor.lastrowid
        
        # Insert all versions
        version_ids = []
        current_version_id = None
        
        for version in article_data['versions']:
            version_insert = """
                INSERT INTO articoli_versioni (
                    articolo_id, tipo_versione, numero_aggiornamento,
                    testo_versione, testo_pulito, data_inizio_vigore, data_fine_vigore,
                    is_current, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            cursor.execute(version_insert, [
                article_id,
                version['tipo_versione'],
                version['numero_aggiornamento'],
                version['testo_versione'],
                version.get('testo_pulito', ''),
                version['data_inizio_vigore'],
                version['data_fine_vigore'],
                version['is_current'],
                version['status']
            ])
            
            version_id = cursor.lastrowid
            version_ids.append(version_id)
            
            if version['is_current']:
                current_version_id = version_id
        
        # Update article with current version reference
        if current_version_id:
            cursor.execute("""
                UPDATE articoli 
                SET versione_corrente_id = ?, numero_versioni = ?
                WHERE id = ?
            """, [current_version_id, len(version_ids), article_id])
        
        conn.commit()
        conn.close()
        
        print(f"✓ Saved article {article_data['numero_articolo']} with {len(version_ids)} versions")
        if current_version and current_version.get('articoli_correlati'):
            print(f"  📎 Including {len(current_version['articoli_correlati'])} correlated articles")
        
        return article_id
        
    except Exception as e:
        print(f"❌ Error saving article with versions: {e}")
        return None

# ========================================
# MAIN SCRAPING FUNCTIONS
# ========================================

def scrape_document_with_versioning(urn):
    """Scrape a document and extract all articles with their versions"""
    try:
        # Initialize database
        init_versioning_database()
        
        # Create session
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Build document URL
        document_url = f"{normattiva_url}/uri-res/N2Ls?{urn}"
        print(f"🔍 Scraping document: {document_url}")
        
        # Fetch document
        response = session.get(document_url)
        response.raise_for_status()
        
        # Parse document
        page = lxml.html.fromstring(response.content)
        
        # Save document info first
        document_id = save_document_info(page, urn)
        if not document_id:
            print("❌ Failed to save document info")
            return False
        
        # Extract all articles
        articles = page.xpath('//div[contains(@class, "articolo")] | //article | //*[contains(text(), "Art.")]')
        
        if not articles:
            print("⚠️ No articles found on page")
            return False
        
        total_articles = len(articles)
        saved_articles = 0
        
        print(f"🔍 Found {total_articles} potential articles")
        
        for i, article_element in enumerate(articles, 1):
            try:
                print(f"\n📄 Processing article {i}/{total_articles}")
                
                # Extract article with all versions
                article_data = extract_article_with_versions(article_element, document_id, session)
                
                if article_data and article_data.get('versions'):
                    # Save to database
                    article_id = save_article_with_versions(article_data)
                    if article_id:
                        saved_articles += 1
                        print(f"✓ Saved article {article_data['numero_articolo']} (ID: {article_id})")
                    else:
                        print(f"❌ Failed to save article {article_data.get('numero_articolo', 'N/A')}")
                else:
                    print(f"⚠️ No valid data extracted for article {i}")
                
                # Small delay to be respectful
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing article {i}: {e}")
                continue
        
        print(f"\n✅ COMPLETED: Saved {saved_articles}/{total_articles} articles with versioning")
        return True
        
    except Exception as e:
        print(f"❌ Error scraping document with versioning: {e}")
        return False

def save_document_info(page, urn):
    """Save document information to database"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Extract document info from page
        title_elem = page.xpath('//title | //h1')[0] if page.xpath('//title | //h1') else None
        title = title_elem.text_content().strip() if title_elem is not None else "Documento"
        
        # Parse URN components
        urn_parts = parse_urn_components(urn)
        
        document_insert = """
            INSERT INTO documenti_normativi (
                titolo, tipo_atto, numero, anno, urn,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'vigente', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        
        cursor.execute(document_insert, [
            title,
            urn_parts.get('tipo', 'Documento'),
            urn_parts.get('numero', '1'),
            extract_year_from_urn(urn),
            urn
        ])
        
        document_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✓ Saved document: {title} (ID: {document_id})")
        return document_id
        
    except Exception as e:
        print(f"❌ Error saving document info: {e}")
        return None

def parse_urn_components(urn):
    """Parse URN components"""
    if not urn or not urn.startswith("urn:nir:"):
        return {}
    
    try:
        urn_clean = urn.replace("urn:nir:", "")
        if ";" in urn_clean:
            main_part, numero = urn_clean.split(";", 1)
            parts = main_part.split(":")
            
            if len(parts) >= 4:
                return {
                    "stato": parts[0],
                    "tipo": parts[1],
                    "data": parts[2] if len(parts) > 2 else "",
                    "numero": numero
                }
    except Exception:
        pass
    
    return {}

def extract_year_from_urn(urn):
    """Extract year from URN"""
    year_match = re.search(r'(19|20)\d{2}', urn)
    return int(year_match.group(0)) if year_match else 2000

# ========================================
# MAIN EXECUTION
# ========================================

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scraper_with_versioning.py <URN>")
        print("Example: python scraper_with_versioning.py 'urn:nir:stato:legge:2020-03-17;18'")
        sys.exit(1)
    
    urn = sys.argv[1]
    print(f"🚀 Starting enhanced scraping with versioning for: {urn}")
    
    success = scrape_document_with_versioning(urn)
    
    if success:
        print(f"\n🎉 Successfully completed scraping with versioning support!")
        print(f"📊 Check the database for articles with orig. and agg. versions")
    else:
        print(f"\n❌ Scraping failed!")
        sys.exit(1)
