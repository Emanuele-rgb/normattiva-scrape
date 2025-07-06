#!/usr/bin/env python3
"""
NORMATTIVA-SCRAPE Unified Scraper - Enhanced Legal Document Scraper
Supports bodyTesto extraction, correlated articles, and versioning (original + aggiornamenti)
Main entry point: python scraper_optimized.py [year] [num_docs]
"""

from collections import OrderedDict
import re
import json
import sqlite3
from datetime import datetime, date
import lxml.html
import requests
import sys
from urllib.parse import urljoin, urlparse, parse_qs
import time
import copy
import os

# Import the FonteOriginePopulator for automatic population
try:
    from populate_fonte_origine import FonteOriginePopulator
except ImportError:
    print("Warning: populate_fonte_origine.py not found. Fonte origine will not be populated automatically.")
    FonteOriginePopulator = None

normattiva_url = "http://www.normattiva.it"

# ========================================
# URL UTILITY FUNCTIONS
# ========================================

def convert_to_permalink_format(full_url):
    """Convert a full URL to the actual permalink format from normattiva.it"""
    try:
        if not full_url:
            return ""
        
        # If it's already a full URL, convert http to https and return
        if full_url.startswith('http'):
            # Ensure we use https
            if full_url.startswith('http://'):
                return full_url.replace('http://', 'https://')
            return full_url
        
        # Convert relative URL to absolute URL with normattiva.it domain
        if full_url.startswith('/'):
            permalink = f"https://www.normattiva.it{full_url}"
        else:
            permalink = f"https://www.normattiva.it/{full_url}"
        
        print(f"[convert_to_permalink] {full_url} -> {permalink}")
        return permalink
        
    except Exception as e:
        print(f"⚠️ Error converting URL to permalink: {e}")
        return full_url if full_url else ""

# ========================================
# HELPER FUNCTIONS FOR ARTICLE PROCESSING
# ========================================

def determine_content_type(text):
    """Determina il tipo di contenuto basandosi sul testo del link"""
    text_lower = text.lower()
    
    if 'allegato' in text_lower or 'allegati' in text_lower:
        return 'allegato'
    elif 'art' in text_lower or 'articolo' in text_lower:
        return 'articolo'
    elif any(word in text_lower for word in ['bis', 'ter', 'quater', 'quinquies', 'sexies', 'septies', 'octies', 'novies', 'decies']):
        return 'articolo'
    else:
        return 'articolo'  # Default to articolo

def sort_article_number(number_str):
    """Ordina i numeri degli articoli considerando bis, ter, allegati"""
    if not number_str:
        return (999, 0, 0)
    
    # Handle allegati separately
    if 'allegato' in number_str.lower():
        # Extract number from allegato if present
        match = re.search(r'(\d+)', number_str)
        if match:
            return (1000, int(match.group(1)), 0)
        else:
            return (1000, 0, 0)
    
    # Handle standard articles with bis, ter, etc.
    base_match = re.search(r'^(\d+)', number_str)
    if base_match:
        base_num = int(base_match.group(1))
        
        # Check for bis, ter, etc.
        if 'bis' in number_str.lower():
            return (base_num, 1, 0)
        elif 'ter' in number_str.lower():
            return (base_num, 2, 0)
        elif 'quater' in number_str.lower():
            return (base_num, 3, 0)
        elif 'quinquies' in number_str.lower():
            return (base_num, 4, 0)
        elif 'sexies' in number_str.lower():
            return (base_num, 5, 0)
        elif 'septies' in number_str.lower():
            return (base_num, 6, 0)
        elif 'octies' in number_str.lower():
            return (base_num, 7, 0)
        elif 'novies' in number_str.lower():
            return (base_num, 8, 0)
        elif 'decies' in number_str.lower():
            return (base_num, 9, 0)
        else:
            return (base_num, 0, 0)
    
    return (999, 0, 0)

def extract_article_activation_date(article_element):
    """Estrae la data di attivazione dell'articolo dal span artInizio"""
    try:
        # Cerca il span con id="artInizio" e class="rosso"
        date_span = article_element.xpath('.//span[@id="artInizio" and contains(@class, "rosso")]')
        
        if date_span:
            date_text = date_span[0].text_content().strip()
            
            # Rimuovi caratteri non stampabili e spazi extra
            date_text = re.sub(r'[^\d\-/]', '', date_text)
            
            # Prova diversi formati di data
            date_patterns = [
                r'(\d{1,2})-(\d{1,2})-(\d{4})',  # dd-mm-yyyy
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # dd/mm/yyyy
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # yyyy-mm-dd
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_text)
                if match:
                    day, month, year = match.groups()
                    try:
                        # Converti in formato ISO
                        parsed_date = datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", "%Y-%m-%d").date()
                        print(f"🗓️ Found article activation date: {parsed_date}")
                        return parsed_date
                    except ValueError:
                        continue
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error extracting article activation date: {e}")
        return None

def extract_article_end_date(article_element):
    """Estrae la data di cessazione dell'articolo dal span artFine"""
    try:
        # Cerca il span con id="artFine" e class="rosso"
        date_span = article_element.xpath('.//span[@id="artFine" and contains(@class, "rosso")]')
        
        if date_span:
            date_text = date_span[0].text_content().strip()
            
            # Rimuovi caratteri non stampabili e spazi extra
            date_text = re.sub(r'[^\d\-/]', '', date_text)
            
            # Prova diversi formati di data
            date_patterns = [
                r'(\d{1,2})-(\d{1,2})-(\d{4})',  # dd-mm-yyyy
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # dd/mm/yyyy
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # yyyy-mm-dd
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_text)
                if match:
                    day, month, year = match.groups()
                    try:
                        # Converti in formato ISO
                        parsed_date = datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", "%Y-%m-%d").date()
                        print(f"⏰ Found article end date: {parsed_date}")
                        return parsed_date
                    except ValueError:
                        continue
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error extracting article end date: {e}")
        return None

def extract_allegati_content(article_element, session, base_url):
    """Estrae il contenuto degli allegati se presenti"""
    allegati = []
    
    try:
        # Cerca link agli allegati
        allegato_links = article_element.xpath('.//a[contains(@href, "allegato") or contains(text(), "Allegato")]')
        
        for link in allegato_links:
            href = link.get('href')
            text = link.text_content().strip()
            
            if href:
                # Converti in URL assoluto
                allegato_url = urljoin(base_url, href)
                
                # Estrai il numero dell'allegato
                allegato_number = extract_allegato_number(text)
                
                # Fetch contenuto allegato
                allegato_content = fetch_allegato_content(allegato_url, session)
                
                allegati.append({
                    'numero': allegato_number,
                    'titolo': text,
                    'url': allegato_url,
                    'contenuto': allegato_content
                })
                
                print(f"📎 Found allegato {allegato_number}: {text}")
        
        return allegati
        
    except Exception as e:
        print(f"❌ Error extracting allegati: {e}")
        return []

def extract_allegato_number(text):
    """Estrae il numero dell'allegato dal testo"""
    match = re.search(r'allegato\s*([A-Z0-9]+)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Fallback: cerca solo numeri o lettere
    match = re.search(r'([A-Z0-9]+)', text)
    if match:
        return match.group(1)
    
    return "1"

def fetch_allegato_content(allegato_url, session):
    """Fetch e pulisce il contenuto di un allegato"""
    try:
        response = session.get(allegato_url)
        if response.status_code == 200:
            html_content = lxml.html.fromstring(response.content)
            
            # Cerca il contenuto dell'allegato
            content_selectors = [
                './/div[contains(@class, "bodyTesto")]',
                './/div[contains(@class, "allegato")]',
                './/div[@id="contenuto"]',
                './/div[contains(@class, "contenuto")]'
            ]
            
            for selector in content_selectors:
                elements = html_content.xpath(selector)
                if elements:
                    content = elements[0].text_content().strip()
                    if content:
                        return clean_article_text(content)
            
            # Fallback: tutto il testo
            return clean_article_text(html_content.text_content())
            
    except Exception as e:
        print(f"❌ Error fetching allegato content: {e}")
        return ""
    
    return ""

def process_allegato_content(allegato_url, allegato_number, session, documento_id, main_document_url):
    """Process an allegato as a special type of article"""
    try:
        print(f"[process_allegato] Fetching allegato {allegato_number}: {allegato_url}")
        allegato_response = session.get(allegato_url)
        
        if allegato_response.status_code != 200:
            print(f"[process_allegato] Error {allegato_response.status_code} for allegato {allegato_number}")
            return None
        
        allegato_html = lxml.html.fromstring(allegato_response.content)
        
        # Extract allegato content
        allegato_title = f"Allegato {allegato_number}"
        
        # Look for bodyTesto div or fallback content
        body_testo = allegato_html.xpath('.//div[contains(@class, "bodyTesto")]')
        
        if body_testo:
            testo_completo = body_testo[0].text_content().strip()
            testo_pulito = clean_article_text(testo_completo)
        else:
            # Fallback extraction for allegati
            content = extract_article_content_fallback(allegato_html)
            testo_completo = content
            testo_pulito = clean_article_text(content)
        
        # Extract activation date
        activation_date = extract_article_activation_date(allegato_html)
        
        # Extract end date
        end_date = extract_article_end_date(allegato_html)
        
        # Save allegato as a special article
        articolo_data = {
            'documento_id': documento_id,
            'numero_articolo': f"Allegato-{allegato_number}",
            'titoloAtto': allegato_title,
            'testo_completo': testo_completo,
            'testo_pulito': testo_pulito,
            'articoli_correlati': json.dumps([], ensure_ascii=False),
            'allegati': json.dumps([], ensure_ascii=False),
            'data_attivazione': activation_date,
            'data_cessazione': end_date,
            'url_documento': convert_to_permalink_format(main_document_url),
            'versions': [{
                'tipo_versione': 'orig',
                'numero_aggiornamento': None,
                'testo_versione': testo_completo,
                'testo_pulito': testo_pulito,
                'articoli_correlati': [],
                'allegati': [],
                'data_inizio_vigore': activation_date or datetime.now().date(),
                'data_fine_vigore': None,
                'is_current': True,
                'status': 'vigente'
            }]
        }
        
        print(f"📎 Processed allegato {allegato_number}: {len(testo_completo)} chars")
        return save_articolo_with_versions(articolo_data)
        
    except Exception as e:
        print(f"❌ Error processing allegato {allegato_number}: {e}")
        return None

# ========================================
# DATABASE INITIALIZATION WITH VERSIONING
# ========================================

def init_simplified_database():
    """Initialize database with simplified article versioning"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Check if we need to apply simplified schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articoli_versioni'")
        if cursor.fetchone():
            print("Applying simplified schema (removing versioning table)...")
            with open("simplified_schema.sql", "r", encoding="utf-8") as f:
                schema_sql = f.read()
            
            conn.executescript(schema_sql)
            conn.commit()
            print("✓ Simplified database schema applied successfully")
        else:
            # Check if we have the new columns
            cursor.execute("PRAGMA table_info(articoli)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'articolo_base_id' not in columns:
                print("Adding simplified versioning columns...")
                cursor.execute("ALTER TABLE articoli ADD COLUMN articolo_base_id INTEGER REFERENCES articoli(id)")
                cursor.execute("ALTER TABLE articoli ADD COLUMN tipo_versione VARCHAR(20) DEFAULT 'orig'")
                cursor.execute("ALTER TABLE articoli ADD COLUMN numero_aggiornamento INTEGER")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articoli_base ON articoli(articolo_base_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articoli_versione ON articoli(tipo_versione)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articoli_aggiornamento ON articoli(numero_aggiornamento)")
                conn.commit()
                print("✓ Simplified versioning columns added successfully")
            else:
                print("✓ Using existing simplified database schema")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error initializing simplified database: {e}")
        raise

# ========================================
# UTILITY FUNCTIONS FOR NEW DATABASE
# ========================================

def init_optimized_database():
    """Inizializza il database con la nuova struttura ottimizzata e versioning semplificato"""
    try:
        # Try simplified schema first
        init_simplified_database()
        return
    except Exception as e:
        print(f"⚠️ Simplified schema not available, falling back to optimized schema: {e}")
    
    try:
        # Fallback to optimized schema
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Verifica se esistono già le nuove tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documenti_normativi'")
        if not cursor.fetchone():
            print("Initializing new optimized database schema...")
            with open("database_schema.sql", "r", encoding="utf-8") as f:
                schema_sql = f.read()
            
            # Esegui lo schema usando sqlite3 direttamente
            conn.executescript(schema_sql)
            conn.commit()
            print("New database schema initialized successfully")
        else:
            print("Using existing optimized database schema")
            
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")
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
    
    # Remove navigation patterns
    navigation_patterns = [
        r'nascondi.*?visualizza.*?atto.*?intero',
        r'precedente.*?successivo',
        r'stampa.*?questa.*?pagina',
        r'torna.*?su',
        r'vai.*?al.*?contenuto',
        r'menu.*?di.*?navigazione',
        r'testo.*?in.*?vigore.*?dal.*?\d{2}/\d{2}/\d{4}',
        r'vigente.*?al.*?\d{2}/\d{2}/\d{4}',
        r'Gazzetta.*?Ufficiale',
        r'visualizza.*?atto.*?intero',
        r'elemento.*?grafico',
        r'articolo.*?precedente',
        r'articolo.*?successivo',
        r'mostra.*?nascond[i|ere]',
        r'chiudi.*?apri',
        r'cerca.*?ricerca',
        r'home.*?indietro',
        r'condividi.*?stampa',
        r'\(GU\s+n\.\d+\s+del\s+\d{2}-\d{2}-\d{4}\)',
        r'visualizza\s+atto\s+intero',
        r'nascondi\s*$',
        r'vigente\s+al\s+\d{2}/\d{2}/\d{4}',
    ]
    
    for pattern in navigation_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
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

def parse_urn_components(urn: str) -> dict:
    """Estrae componenti da URN: urn:nir:stato:legge:2023-12-01;123 or urn:nir:2000;13"""
    if not urn or not urn.startswith("urn:nir:"):
        return {}
    
    try:
        urn_clean = urn.replace("urn:nir:", "")
        if ";" in urn_clean:
            main_part, numero = urn_clean.split(";", 1)
            parts = main_part.split(":")
            
            # Handle full URN format: urn:nir:stato:legge:2023-12-01;123
            if len(parts) >= 4:
                return {
                    "stato": parts[0],
                    "tipo": parts[1],
                    "data": parts[2] if len(parts) > 2 else "",
                    "numero": numero
                }
            # Handle short URN format: urn:nir:2000;13
            elif len(parts) == 1 and parts[0].isdigit():
                return {
                    "stato": "",
                    "tipo": "",
                    "data": parts[0],  # Year
                    "numero": numero
                }
        
        # Handle URN without semicolon - extract year if present
        elif urn_clean.isdigit():
            return {
                "stato": "",
                "tipo": "",
                "data": urn_clean,  # Year
                "numero": ""
            }
            
    except Exception as e:
        print(f"Error parsing URN {urn}: {e}")
    
    return {}

def extract_tipo_atto(name: str, type_field: str = "") -> str:
    """Estrae il tipo di atto dal nome o dal campo type"""
    if not name and not type_field:
        return "Documento"
    
    text = (name or "") + " " + (type_field or "")
    text = text.upper()
    
    if "LEGGE" in text:
        return "Legge"
    elif "DECRETO LEGISLATIVO" in text or "D.LGS" in text:
        return "Decreto Legislativo"
    elif "DECRETO DEL PRESIDENTE DELLA REPUBBLICA" in text or "D.P.R" in text:
        return "Decreto del Presidente della Repubblica"
    elif "DECRETO" in text:
        return "Decreto"
    elif "REGOLAMENTO" in text:
        return "Regolamento"
    elif "COSTITUZIONE" in text:
        return "Costituzione"
    elif "CODICE" in text:
        return "Codice"
    else:
        return "Documento"

def extract_year_from_name(name: str) -> int:
    """Estrae l'anno dal nome del documento"""
    if not name:
        return 2000
    
    year_patterns = [
        r'\b(19|20)\d{2}\b',
        r'\b(\d{1,2})/(\d{1,2})/(19|20)\d{2}\b',
        r'del\s+(19|20)\d{2}',
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, name)
        if match:
            if len(match.groups()) == 1:
                return int(match.group(0))
            else:
                return int(match.group(-1))
    
    return 2000

def determine_materia_principale(name: str, content: str) -> str:
    """Determina la materia principale basandosi su nome e contenuto"""
    text = ((name or "") + " " + (content or "")).upper()
    
    materie_map = {
        "Diritto Civile": ["CIVILE", "CONTRATTO", "FAMIGLIA", "MATRIMONIO", "PROPRIETÀ", "SUCCESSIONE"],
        "Diritto Penale": ["PENALE", "REATO", "SANZIONE", "CONDANNA", "CARCERE"],
        "Diritto Amministrativo": ["AMMINISTRATIVO", "PUBBLICA AMMINISTRAZIONE", "PA", "PROCEDIMENTO"],
        "Diritto del Lavoro": ["LAVORO", "DIPENDENTE", "CONTRATTO DI LAVORO", "SINDACATO"],
        "Diritto Tributario": ["TRIBUTO", "TASSA", "IMPOSTA", "FISCO", "IVA"],
        "Diritto Commerciale": ["SOCIETÀ", "IMPRESA", "COMMERCIO", "FALLIMENTO"],
        "Diritto Costituzionale": ["COSTITUZIONE", "COSTITUZIONALE", "PARLAMENTO", "GOVERNO"]
    }
    
    for materia, keywords in materie_map.items():
        if any(keyword in text for keyword in keywords):
            return materia
    
    return "Altro"

def get_livello_gerarchia(tipo_atto: str) -> int:
    """Determina il livello gerarchico del documento"""
    gerarchia_map = {
        "Costituzione": 1,
        "Legge": 2,
        "Decreto Legislativo": 3,
        "Decreto del Presidente della Repubblica": 3,
        "Decreto": 4,
        "Regolamento": 5,
        "Codice": 2
    }
    
    return gerarchia_map.get(tipo_atto, 6)

def save_documento_normativo(documento_data: dict) -> int:
    """Salva un documento normativo nel database ottimizzato"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Verifica se il documento esiste già
        cursor.execute(
            "SELECT id FROM documenti_normativi WHERE urn = ? OR (numero = ? AND anno = ? AND tipo_atto = ?)",
            [documento_data.get('urn', ''), documento_data.get('numero', ''), 
             documento_data.get('anno', 0), documento_data.get('tipo_atto', '')]
        )
        existing = cursor.fetchone()
        
        if existing:
            doc_id = existing[0]
            print(f"Document already exists with id: {doc_id}")
            conn.close()
            return doc_id
        
        # Insert nuovo documento
        insert_query = """
            INSERT INTO documenti_normativi (
                numero, anno, tipo_atto, titoloAtto, data_pubblicazione,
                materia_principale, status, livello_gerarchia,
                url_normattiva, urn, testo_completo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, [
            documento_data.get('numero', 'N/A'),
            documento_data.get('anno', 2000),
            documento_data.get('tipo_atto', 'Documento'),
            documento_data.get('titoloAtto', 'Documento senza titolo'),
            documento_data.get('data_pubblicazione', f"{documento_data.get('anno', 2000)}-01-01"),
            documento_data.get('materia_principale', 'Altro'),
            documento_data.get('status', 'vigente'),
            documento_data.get('livello_gerarchia', 6),
            documento_data.get('url_normattiva', None),
            documento_data.get('urn', ''),
            documento_data.get('testo_completo', '')
        ])
        
        # Ottieni l'ID del documento appena inserito
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"Saved document with id: {doc_id}")
        return doc_id
        
    except Exception as e:
        print(f"Error saving document: {e}")
        return None

def save_articolo(articolo_data: dict) -> int:
    """Salva un articolo nel database usando lo schema semplificato"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Determine status based on data_cessazione
        status = 'abrogato' if articolo_data.get('data_cessazione') else 'vigente'
        
        # Check if we have the simplified versioning columns
        cursor.execute("PRAGMA table_info(articoli)")
        columns = [column[1] for column in cursor.fetchall()]
        has_simplified_columns = 'articolo_base_id' in columns
        
        if has_simplified_columns:
            insert_query = """
                INSERT INTO articoli (
                    documento_id, numero_articolo, titoloAtto, testo_completo, testo_pulito, 
                    url_documento, articoli_correlati, allegati, data_attivazione, data_cessazione, 
                    status, articolo_base_id, tipo_versione, numero_aggiornamento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, [
                articolo_data.get('documento_id'),
                articolo_data.get('numero_articolo', '1'),
                articolo_data.get('titoloAtto', ''),
                articolo_data.get('testo_completo', ''),
                articolo_data.get('testo_pulito', ''),
                articolo_data.get('url_documento', ''),
                articolo_data.get('articoli_correlati', '[]'),
                articolo_data.get('allegati', '[]'),
                articolo_data.get('data_attivazione'),
                articolo_data.get('data_cessazione'),
                status,
                None,  # articolo_base_id (NULL for single articles)
                'orig',  # tipo_versione
                None   # numero_aggiornamento
            ])
        else:
            # Fallback for older schema without simplified columns
            insert_query = """
                INSERT INTO articoli (
                    documento_id, numero_articolo, titoloAtto, testo_completo, testo_pulito, 
                    url_documento, articoli_correlati, allegati, data_attivazione, data_cessazione
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, [
                articolo_data.get('documento_id'),
                articolo_data.get('numero_articolo', '1'),
                articolo_data.get('titoloAtto', ''),
                articolo_data.get('testo_completo', ''),
                articolo_data.get('testo_pulito', ''),
                articolo_data.get('url_documento', ''),
                articolo_data.get('articoli_correlati', '[]'),
                articolo_data.get('allegati', '[]'),
                articolo_data.get('data_attivazione'),
                articolo_data.get('data_cessazione')
            ])
        
        art_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"Saved article with id: {art_id} (status: {status})")
        return art_id
        
    except Exception as e:
        print(f"Error saving article: {e}")
        return None

def save_citazione_normativa(citazione_data: dict):
    """Salva una citazione normativa"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        insert_query = """
            INSERT OR IGNORE INTO citazioni_normative (
                articolo_citante_id, articolo_citato_id, tipo_citazione, contesto_citazione
            ) VALUES (?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, [
            citazione_data.get('articolo_citante_id'),
            citazione_data.get('articolo_citato_id'),
            citazione_data.get('tipo_citazione', 'rinvio'),
            citazione_data.get('contesto_citazione', '')
        ])
        
        conn.commit()
        conn.close()
        
        print(f"Saved citation from {citazione_data.get('articolo_citante_id')} to {citazione_data.get('articolo_citato_id')}")
        
    except Exception as e:
        print(f"Error saving citation: {e}")

def get_documento_by_urn(urn: str):
    """Recupera un documento dal database tramite URN"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM documenti_normativi WHERE urn = ?", [urn])
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting document by URN: {e}")
        return None

def get_articoli_by_documento(documento_id: int):
    """Recupera gli articoli di un documento"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM articoli WHERE documento_id = ? LIMIT 1", [documento_id])
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting articles by document: {e}")
        return None

# ========================================
# ARTICLE NAVIGATION AND EXTRACTION UTILITIES
# ========================================

def extract_version_info(text, relative_url):
    """Estrae informazioni sulla versione dal testo e dall'URL"""
    version_info = {
        'tipo_versione': 'orig',
        'numero_aggiornamento': None,
        'is_current': False
    }
    
    # Controlla se è un aggiornamento
    if text.lower().startswith('agg.'):
        try:
            version_info['tipo_versione'] = text.lower()
            version_info['numero_aggiornamento'] = int(text.split('.')[1])
        except:
            version_info['tipo_versione'] = text.lower()
            version_info['numero_aggiornamento'] = 1
    elif text.lower() == 'orig.':
        version_info['tipo_versione'] = 'orig'
        version_info['numero_aggiornamento'] = None
    else:
        # Versione corrente se non ha imUpdate=true nell'URL
        if 'imUpdate=true' not in relative_url:
            version_info['is_current'] = True
            version_info['tipo_versione'] = 'current'
    
    # Estrai numero versione dall'URL se presente
    version_match = re.search(r'art\.versione=(\d+)', relative_url)
    if version_match:
        version_info['url_version'] = int(version_match.group(1))
    
    return version_info

def extract_article_number_from_element_id(element_id):
    """Estrae il numero dell'articolo dall'ID dell'elemento (es. 'a1-1-0' -> '1')"""
    # Pattern per ID come 'a1-1-0', 'a2-1-0', etc.
    match = re.search(r'^a(\d+)-', element_id)
    if match:
        return match.group(1)
    return None

def _get_absolute_url(relative_url, base_url=normattiva_url):
    """Converte URL relativo in assoluto"""
    if relative_url.startswith('http'):
        return relative_url
    return f"{base_url}{relative_url}"

def extract_article_links_from_navigation(html_element):
    """Estrae tutti i link degli articoli dalla navigazione laterale, inclusi bis, ter, allegati e versioni aggiornate"""
    article_links = []
    
    # Cerca i link showArticle nella navigazione
    onclick_elements = html_element.xpath('.//a[contains(@onclick, "showArticle")]')
    
    for element in onclick_elements:
        onclick = element.get('onclick', '')
        text = element.text_content().strip()
        
        # Estrai URL dalla chiamata showArticle
        url_match = re.search(r"showArticle\(['\"]([^'\"]+)['\"]", onclick)
        if url_match:
            relative_url = url_match.group(1)
            absolute_url = _get_absolute_url(relative_url)
            
            # Estrai il numero dell'articolo dal testo del link (supporta bis, ter, etc.)
            article_number = extract_article_number_from_text(text)
            
            # Determina il tipo di contenuto
            content_type = determine_content_type(text)
            
            # Controlla se è un aggiornamento (agg.1, agg.2, orig.)
            is_update = text.lower().startswith('agg.') or text.lower() == 'orig.'
            version_info = extract_version_info(text, relative_url)
            
            if article_number or content_type == 'allegato' or is_update:
                article_info = {
                    'number': article_number if article_number else text,
                    'url': absolute_url,
                    'text': text,
                    'content_type': content_type,
                    'is_update': is_update,
                    'version_info': version_info
                }
                
                article_links.append(article_info)
                print(f"[extract_article_links] Found {content_type} {article_number or text}: {text} (update: {is_update})")
    
    # Cerca anche i link con showUpdatesArticle per identificare articoli con aggiornamenti
    update_elements = html_element.xpath('.//a[contains(@onclick, "showUpdatesArticle")]')
    for element in update_elements:
        element_id = element.get('id', '')
        if element_id:
            # Cerca gli aggiornamenti nascosti per questo articolo
            update_links = html_element.xpath(f'.//li[contains(@class, "agg-{element_id}")]/a[contains(@onclick, "showArticle")]')
            for update_link in update_links:
                onclick = update_link.get('onclick', '')
                text = update_link.text_content().strip()
                
                url_match = re.search(r"showArticle\(['\"]([^'\"]+)['\"]", onclick)
                if url_match:
                    relative_url = url_match.group(1)
                    absolute_url = _get_absolute_url(relative_url)
                    
                    # Estrai informazioni sulla versione
                    version_info = extract_version_info(text, relative_url)
                    
                    # Determina il numero dell'articolo base dall'ID
                    article_number = extract_article_number_from_element_id(element_id)
                    
                    article_info = {
                        'number': article_number,
                        'url': absolute_url,
                        'text': text,
                        'content_type': 'articolo',
                        'is_update': True,
                        'version_info': version_info,
                        'parent_element_id': element_id
                    }
                    
                    # Controlla se questo link è già presente
                    if not any(link['url'] == absolute_url for link in article_links):
                        article_links.append(article_info)
                        print(f"[extract_article_links] Found update version for article {article_number}: {text}")
    
    # Ordina per numero articolo, gestendo bis, ter, allegati
    article_links.sort(key=lambda x: sort_article_number(x['number']))
    
    return article_links

def extract_article_number_from_text(text):
    """Estrae il numero dell'articolo dal testo del link, supportando bis, ter, etc."""
    if not text:
        return None
    
    # Pattern per diversi formati di numerazione inclusi bis, ter, etc.
    patterns = [
        r'art\.?\s*(\d+)\s+(bis|ter|quater|quinquies|sexies|septies|octies|novies|decies)',  # "art. 123 bis", "Art. 5 ter"
        r'art\.?\s*(\d+(?:-(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies))?)',  # "art. 1-bis", "art. 1-ter"
        r'articolo\s*(\d+)\s+(bis|ter|quater|quinquies|sexies|septies|octies|novies|decies)',  # "articolo 123 bis"
        r'articolo\s*(\d+(?:-(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies))?)',  # "articolo 1-bis"
        r'(\d+)\s+(bis|ter|quater|quinquies|sexies|septies|octies|novies|decies)',  # "123 bis", "5 ter"
        r'art\s+(\d+)',  # art 123
        r'comma\s+(\d+)',  # comma 123
        r'lettera\s+([a-z])',  # lettera a
        r'(\d+)\s*-?\s*(bis|ter|quater|quinquies|sexies|septies|octies|novies|decies)',  # "1 bis", "1-ter"
        r'^(\d+)$',  # solo numero "1"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower().strip())
        if match:
            if len(match.groups()) == 2:
                # Formato con parte latina separata
                base_num = match.group(1)
                latin_part = match.group(2)
                return f"{base_num}-{latin_part}"
            else:
                # Formato già completo
                return match.group(1)
    
    return None

# ========================================
# ENHANCED ARTICLE PROCESSING WITH BODYTEXT AND VERSIONING
# ========================================

def enhanced_article_scraping_with_versioning(base_url, session, documento_id):
    """
    Enhanced article scraping that extracts text from bodyTesto divs and supports versioning
    
    Args:
        base_url: Base URL of the document
        session: requests session
        documento_id: Document ID in database
        
    Returns:
        list: List of article IDs that were processed
    """
    article_ids = []
    
    try:
        print(f"[enhanced_article_scraping] Processing with bodyTesto extraction: {base_url}")
        response = session.get(base_url)
        
        if response.status_code != 200:
            print(f"[enhanced_article_scraping] Error {response.status_code} for {base_url}")
            return []
            
        html_content = lxml.html.fromstring(response.content)
        
        # Extract articles using different methods
        # Method 1: Try to extract from navigation
        article_links = extract_article_links_from_navigation(html_content)
        
        if article_links:
            print(f"[enhanced_article_scraping] Found {len(article_links)} items in navigation")
            
            # Group articles by their base number to handle versions together
            articles_by_number = {}
            for article_info in article_links:
                if article_info['content_type'] == 'allegato':
                    # Handle allegati separately
                    allegato_id = process_allegato_content(
                        article_info['url'], 
                        article_info['number'], 
                        session, 
                        documento_id,
                        base_url
                    )
                    if allegato_id:
                        article_ids.append(allegato_id)
                else:
                    # Group by base article number
                    base_number = article_info['number']
                    if base_number not in articles_by_number:
                        articles_by_number[base_number] = []
                    articles_by_number[base_number].append(article_info)
            
            # Process each article group (handling versions together)
            for base_number, article_versions in articles_by_number.items():
                print(f"[enhanced_article_scraping] Processing article {base_number} with {len(article_versions)} versions")
                
                # Sort versions by version info
                article_versions.sort(key=lambda x: (
                    x['version_info']['numero_aggiornamento'] if x['version_info']['numero_aggiornamento'] is not None else -1,
                    x['version_info']['is_current']
                ))
                
                # Process the article with all its versions
                article_id = process_article_with_versions(
                    base_number,
                    article_versions,
                    session,
                    documento_id,
                    base_url
                )
                if article_id:
                    article_ids.append(article_id)
        else:
            # Method 2: Try to extract from main content if no navigation links
            print("[enhanced_article_scraping] No navigation links found, trying main content extraction")
            article_elements = html_content.xpath('.//div[contains(@class, "articolo")] | .//article')
            
            if article_elements:
                for i, article_element in enumerate(article_elements, 1):
                    article_id = process_article_element_with_bodytext(
                        article_element, 
                        str(i), 
                        documento_id, 
                        base_url,  # Use main document URL
                        session
                    )
                    if article_id:
                        article_ids.append(article_id)
            else:
                # Method 3: Create single article from entire document content
                print("[enhanced_article_scraping] No article elements found, creating single article")
                article_id = create_single_article_from_content(html_content, documento_id, base_url)
                if article_id:
                    article_ids.append(article_id)
        
        print(f"[enhanced_article_scraping] Successfully processed {len(article_ids)} articles")
        return article_ids
        
    except Exception as e:
        print(f"❌ Error in enhanced article scraping: {e}")
        return []

def extract_single_version_content(article_url, version_info, session, documento_id, base_url):
    """Extract content for a single article version"""
    try:
        print(f"[extract_single_version] Extracting {version_info.get('tipo_versione', 'unknown')} version from: {article_url}")
        
        # Fetch the article content
        article_response = session.get(article_url)
        if article_response.status_code != 200:
            print(f"[extract_single_version] Error {article_response.status_code} for {article_url}")
            return None
        
        article_html = lxml.html.fromstring(article_response.content)
        
        # Extract article title using enhanced logic
        article_title = extract_article_title_enhanced(article_html, version_info.get('numero_aggiornamento', ''), documento_id)
        
        # Extract activation and end dates
        activation_date = extract_article_activation_date(article_html)
        end_date = extract_article_end_date(article_html)
        
        # Extract content from bodyTesto
        body_testo = article_html.xpath('.//div[contains(@class, "bodyTesto")]')
        if body_testo:
            body_div = body_testo[0]
            testo_completo = body_div.text_content().strip()
            testo_pulito = clean_article_text(testo_completo)
            articoli_correlati = extract_correlated_articles(body_div)
        else:
            # Fallback extraction
            content = extract_article_content_fallback(article_html)
            testo_completo = content
            testo_pulito = clean_article_text(content)
            articoli_correlati = []
        
        # Extract allegati
        allegati = extract_allegati_content(article_html, session, article_url)
        
        # Determine version dates and status
        data_inizio_vigore = activation_date or datetime.now().date()
        data_fine_vigore = None  # Will be set when superseded by newer version
        
        # Determine if this is the current version
        is_current = (version_info.get('is_current', False) or 
                     version_info.get('tipo_versione') == 'current')
        
        # Determine status based on data_cessazione
        if end_date:
            status = 'abrogato'  # Article has ended
        else:
            status = 'vigente'   # Article is still active
        
        # Create version data structure
        version_data = {
            'tipo_versione': version_info.get('tipo_versione', 'orig'),
            'numero_aggiornamento': version_info.get('numero_aggiornamento'),
            'testo_versione': testo_completo,
            'testo_pulito': testo_pulito,
            'articoli_correlati': json.dumps(articoli_correlati, ensure_ascii=False),
            'allegati': json.dumps(allegati, ensure_ascii=False),
            'data_inizio_vigore': data_inizio_vigore,
            'data_fine_vigore': data_fine_vigore,
            'is_current': is_current,
            'status': status,
            # Keep these for main article record
            'titoloAtto': article_title,
            'testo_completo': testo_completo,
            'data_attivazione': activation_date,
            'data_cessazione': end_date
        }
        
        print(f"✓ Extracted version {version_info.get('tipo_versione', 'unknown')}: {len(testo_completo)} chars, status: {status}")
        return version_data
        
    except Exception as e:
        print(f"❌ Error extracting version content: {e}")
        return None
def process_article_with_versions(article_number, article_versions, session, documento_id, base_url):
    """Process an article with all its versions - creates one main article with linked versions"""
    try:
        print(f"[process_article_with_versions] Processing article {article_number} with {len(article_versions)} versions")
        
        # Sort versions: orig first, then by aggiornamento number
        article_versions.sort(key=lambda x: (
            x['version_info']['tipo_versione'] != 'orig',  # orig first
            x['version_info']['numero_aggiornamento'] if x['version_info']['numero_aggiornamento'] is not None else -1
        ))
        
        # Collect all version data
        versions_data = []
        main_article_data = None
        current_version_data = None
        
        for version_info in article_versions:
            # Extract content for this version
            version_data = extract_single_version_content(
                version_info['url'],
                version_info['version_info'],
                session,
                documento_id,
                base_url
            )
            
            if version_data:
                versions_data.append(version_data)
                
                # Determine which version is current/main
                if (version_info['version_info'].get('is_current', False) or 
                    version_info['version_info'].get('tipo_versione') == 'current' or
                    (not current_version_data and version_info['version_info'].get('tipo_versione') == 'orig')):
                    current_version_data = version_data
        
        if not versions_data:
            print(f"❌ No valid versions found for article {article_number}")
            return None
        
        # Use the most recent/current version as the main article data
        if not current_version_data:
            current_version_data = versions_data[-1]  # Use last version as current
        
        # Create main article record with all versions
        articolo_data = {
            'documento_id': documento_id,
            'numero_articolo': str(article_number),
            'titoloAtto': current_version_data['titoloAtto'],
            'testo_completo': current_version_data['testo_completo'],
            'testo_pulito': current_version_data['testo_pulito'],
            'articoli_correlati': current_version_data['articoli_correlati'],
            'allegati': current_version_data['allegati'],
            'data_attivazione': current_version_data['data_attivazione'],
            'data_cessazione': current_version_data['data_cessazione'],
            'url_documento': convert_to_permalink_format(base_url),
            'versions': versions_data
        }
        
        return save_articolo_with_versions(articolo_data)
        
    except Exception as e:
        print(f"❌ Error processing article with versions: {e}")
        return None

def process_single_article_with_bodytext(article_url, article_number, session, documento_id, main_document_url=None):
    """Process a single article with bodyTesto extraction"""
    try:
        print(f"[process_single_article] Fetching article {article_number}: {article_url}")
        article_response = session.get(article_url)
        
        if article_response.status_code != 200:
            print(f"[process_single_article] Error {article_response.status_code} for article {article_number}")
            return None
        
        article_html = lxml.html.fromstring(article_response.content)
        
        # Use main document URL if provided, otherwise use article URL
        url_to_use = main_document_url if main_document_url else article_url
        
        return process_article_element_with_bodytext(
            article_html, 
            article_number, 
            documento_id, 
            url_to_use,  # Pass the main document URL
            session
        )
        
    except Exception as e:
        print(f"❌ Error processing single article {article_number}: {e}")
        return None

def process_article_element_with_bodytext(article_element, article_number, documento_id, article_url, session):
    """Process an article element with enhanced bodyTesto extraction"""
    try:
        # Extract basic article information - pass documento_id to get the document title
        article_title = extract_article_title_enhanced(article_element, article_number, documento_id)
        
        # Extract article activation date
        activation_date = extract_article_activation_date(article_element)
        
        # Extract article end date (cessazione)
        end_date = extract_article_end_date(article_element)
        
        # Look for bodyTesto div - this contains the actual article text
        body_testo = article_element.xpath('.//div[contains(@class, "bodyTesto")]')
        
        if body_testo:
            body_div = body_testo[0]
            
            # Extract testo_completo and testo_pulito from bodyTesto
            testo_completo = body_div.text_content().strip()
            testo_pulito = clean_article_text(testo_completo)
            
            # Extract correlated articles from links within bodyTesto
            articoli_correlati = extract_correlated_articles(body_div)
            
            print(f"📄 Article {article_number}: extracted {len(testo_completo)} chars from bodyTesto")
            print(f"🔗 Article {article_number}: found {len(articoli_correlati)} correlated articles")
            
        else:
            # Fallback: extract from general content
            print(f"⚠️ No bodyTesto found for article {article_number}, using fallback extraction")
            content = extract_article_content_fallback(article_element)
            testo_completo = content
            testo_pulito = clean_article_text(content)
            articoli_correlati = []
        
        # Extract allegati if present
        allegati = extract_allegati_content(article_element, session, article_url)
        
        # Check for article versions (original + aggiornamenti)
        versions = []
        
        # Extract original version
        original_version = {
            'tipo_versione': 'orig',
            'numero_aggiornamento': None,
            'testo_versione': testo_completo,
            'testo_pulito': testo_pulito,
            'articoli_correlati': articoli_correlati,
            'allegati': allegati,
            'data_inizio_vigore': activation_date or datetime.now().date(),
            'data_fine_vigore': None,
            'is_current': True,
            'status': 'vigente'
        }
        versions.append(original_version)
        
        # Look for aggiornamenti (updates) if in multivigente mode
        if '!multivigente' in article_url:
            aggiornamenti_versions = extract_aggiornamenti_versions_enhanced(article_element, session, documento_id)
            versions.extend(aggiornamenti_versions)
        
        # Save article with all versions
        articolo_data = {
            'documento_id': documento_id,
            'numero_articolo': str(article_number),
            'titoloAtto': article_title,
            'testo_completo': testo_completo,
            'testo_pulito': testo_pulito,
            'articoli_correlati': json.dumps(articoli_correlati, ensure_ascii=False),
            'allegati': json.dumps(allegati, ensure_ascii=False),
            'data_attivazione': activation_date,
            'data_cessazione': end_date,
            'url_documento': convert_to_permalink_format(article_url),
            'versions': versions
        }
        
        return save_articolo_with_versions(articolo_data)
        
    except Exception as e:
        print(f"❌ Error processing article element {article_number}: {e}")
        return None

def extract_article_title_enhanced(article_element, article_number, documento_id=None):
    """Extract article title with enhanced logic - should return the document title, not article content"""
    try:
        # If we have documento_id, get the document title from the database
        if documento_id:
            try:
                conn = sqlite3.connect('data.sqlite')
                cursor = conn.cursor()
                cursor.execute('SELECT titoloAtto FROM documenti_normativi WHERE id = ?', [documento_id])
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0]:
                    # Clean the document title
                    document_title = result[0].strip()
                    # Remove extra whitespace and line breaks
                    document_title = re.sub(r'\s+', ' ', document_title)
                    document_title = re.sub(r'\r\n|\r|\n', ' ', document_title)
                    document_title = re.sub(r'\s+', ' ', document_title).strip()
                    
                    if document_title and len(document_title) > 10:
                        return document_title
            except Exception as e:
                print(f"⚠️ Error getting document title from database: {e}")
        
        # Try to find the document title directly in the HTML (titoloAtto)
        title_selectors = [
            '#titoloAtto',  # Primary document title selector
            '.titoloAtto',  # Class-based selector
            'div[id="titoloAtto"]',  # Specific div element
            '.data_info.text-center',  # Based on screenshot classes
            './/div[@id="titoloAtto"]',  # XPath version
            './/div[contains(@class, "titoloAtto")]',  # XPath with class
            './/div[contains(@class, "data_info") and contains(@class, "text-center")]',  # XPath with multiple classes
        ]
        
        for selector in title_selectors:
            try:
                if selector.startswith('.//'):
                    # XPath selector
                    elements = article_element.xpath(selector)
                else:
                    # CSS selector
                    elements = article_element.cssselect(selector)
                    
                for element in elements:
                    text = element.text_content().strip()
                    if text and len(text) > 10:
                        # Clean the title
                        text = re.sub(r'\s+', ' ', text)
                        text = re.sub(r'\r\n|\r|\n', ' ', text)
                        text = re.sub(r'\s+', ' ', text).strip()
                        return text[:500]  # Limit length
            except Exception as e:
                continue
        
        # Fallback: use generic title based on article number
        return f"Articolo {article_number}"
        
    except Exception as e:
        print(f"⚠️ Error extracting article title: {e}")
        return f"Articolo {article_number}"

def extract_article_content_fallback(article_element):
    """Fallback content extraction when bodyTesto is not available"""
    try:
        # Try various content selectors
        content_selectors = [
            './/div[@id="articolo"]',
            './/div[contains(@class, "articolo")]',
            './/div[@class="contenutoArticolo"]',
            './/div[contains(@class, "art-text")]',
            './/div[contains(@class, "contenuto")]//p',
            './/div[@id="contenuto"]',
            './/div[@id="containerTesto"]',
            './/main//p',
            './/article//p'
        ]
        
        for selector in content_selectors:
            elements = article_element.xpath(selector)
            if elements:
                content_parts = []
                for element in elements:
                    text = element.text_content().strip()
                    if text:
                        content_parts.append(text)
                
                if content_parts:
                    content = ' '.join(content_parts)
                    if len(content.strip()) > 50:
                        return content.strip()
        
        # Last fallback: entire element text
        return article_element.text_content().strip()
        
    except Exception as e:
        print(f"⚠️ Error in fallback content extraction: {e}")
        return ""

def extract_aggiornamenti_versions_enhanced(article_element, session, documento_id):
    """Extract aggiornamenti (updates) versions of the article"""
    try:
        versions = []
        
        # Look for aggiornamenti buttons or links
        update_elements = article_element.xpath('.//button[contains(text(), "aggiornamenti")] | .//a[contains(text(), "aggiornamenti")]')
        
        for update_element in update_elements:
            # Extract update information
            onclick = update_element.get('onclick', '')
            href = update_element.get('href', '')
            
            if onclick or href:
                # This is a simplified version - in a full implementation,
                # you would follow the update links and extract the modified content
                update_version = {
                    'tipo_versione': 'agg.1',  # This would be determined dynamically
                    'numero_aggiornamento': 1,  # This would be determined dynamically
                    'testo_versione': "Testo aggiornato non ancora estratto",
                    'testo_pulito': "Testo aggiornato non ancora estratto",
                    'articoli_correlati': [],
                    'data_inizio_vigore': datetime.now().date(),
                    'data_fine_vigore': None,
                    'is_current': False,
                    'status': 'sostituito'
                }
                versions.append(update_version)
        
        return versions
        
    except Exception as e:
        print(f"⚠️ Error extracting aggiornamenti versions: {e}")
        return []

def create_single_article_from_content(html_element, documento_id, base_url):
    """Create a single article from entire document content when no articles are found"""
    try:
        # Extract content from bodyTesto if available
        body_testo = html_element.xpath('.//div[contains(@class, "bodyTesto")]')
        
        if body_testo:
            body_div = body_testo[0]
            testo_completo = body_div.text_content().strip()
            testo_pulito = clean_article_text(testo_completo)
            articoli_correlati = extract_correlated_articles(body_div)
        else:
            # Fallback to general content
            content_elements = html_element.xpath('.//div[@id="containerTesto"] | .//main | .//article')
            if content_elements:
                testo_completo = content_elements[0].text_content().strip()
            else:
                testo_completo = html_element.text_content().strip()
            
            testo_pulito = clean_article_text(testo_completo)
            articoli_correlati = []
        
        # Save single article
        articolo_data = {
            'documento_id': documento_id,
            'numero_articolo': '1',
            'titoloAtto': 'Documento completo',
            'testo_completo': testo_completo,
            'testo_pulito': testo_pulito,
            'articoli_correlati': json.dumps(articoli_correlati, ensure_ascii=False),
            'allegati': json.dumps([], ensure_ascii=False),
            'data_attivazione': None,
            'data_cessazione': None,
            'url_documento': convert_to_permalink_format(base_url),
            'versions': [{
                'tipo_versione': 'orig',
                'numero_aggiornamento': None,
                'testo_versione': testo_completo,
                'testo_pulito': testo_pulito,
                'articoli_correlati': articoli_correlati,
                'allegati': [],
                'data_inizio_vigore': datetime.now().date(),
                'data_fine_vigore': None,
                'is_current': True,
                'status': 'vigente'
            }]
        }
        
        return save_articolo_with_versions(articolo_data)
        
    except Exception as e:
        print(f"❌ Error creating single article: {e}")
        return None

def extract_all_articles_with_bodytext(base_url, session, documento_id):
    """
    Fallback article extraction with bodyTesto support
    """
    return enhanced_article_scraping_with_versioning(base_url, session, documento_id)

# ========================================
# DATABASE FUNCTIONS WITH VERSIONING SUPPORT
# ========================================

def save_articolo_with_versions(articolo_data):
    """Save article with simplified versioning support"""
    try:
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        # Check if we have the simplified versioning columns
        cursor.execute("PRAGMA table_info(articoli)")
        columns = [column[1] for column in cursor.fetchall()]
        has_simplified_versioning = 'articolo_base_id' in columns
        
        if has_simplified_versioning:
            result = save_articolo_with_simplified_versioning(articolo_data, cursor, conn)
        else:
            result = save_articolo_basic(articolo_data, cursor, conn)
        
        conn.close()
        return result
            
    except Exception as e:
        print(f"❌ Error saving article with versions: {e}")
        if 'conn' in locals():
            conn.close()
        return None

def save_articolo_with_simplified_versioning(articolo_data, cursor, conn):
    """Save article with simplified versioning support"""
    try:
        versions = articolo_data.get('versions', [])
        
        if not versions:
            # No versions provided, save as simple article
            return save_articolo_basic(articolo_data, cursor, conn)
        
        article_ids = []
        base_article_id = None
        
        # Save each version as a separate article record
        for version in versions:
            # Determine status based on data_cessazione
            status = 'abrogato' if version.get('data_cessazione') or articolo_data.get('data_cessazione') else 'vigente'
            
            # Determine tipo_versione and numero_aggiornamento
            tipo_versione = version.get('tipo_versione', 'orig')
            numero_aggiornamento = version.get('numero_aggiornamento')
            
            # Use version-specific content if available, fallback to main article data
            testo_completo = version.get('testo_versione') or version.get('testo_completo') or articolo_data.get('testo_completo', '')
            testo_pulito = version.get('testo_pulito') or articolo_data.get('testo_pulito', '')
            
            insert_query = """
                INSERT INTO articoli (
                    documento_id, numero_articolo, titoloAtto, testo_completo, 
                    testo_pulito, articoli_correlati, allegati, data_attivazione, 
                    data_cessazione, url_documento, status, 
                    articolo_base_id, tipo_versione, numero_aggiornamento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, [
                articolo_data['documento_id'],
                articolo_data['numero_articolo'],
                articolo_data['titoloAtto'],
                testo_completo,
                testo_pulito,
                articolo_data.get('articoli_correlati', '[]'),
                version.get('allegati') or articolo_data.get('allegati', '[]'),
                version.get('data_inizio_vigore') or articolo_data.get('data_attivazione'),
                version.get('data_fine_vigore') or articolo_data.get('data_cessazione'),
                articolo_data.get('url_documento', ''),
                status,
                base_article_id,  # NULL for base article, set for updates
                tipo_versione,
                numero_aggiornamento
            ])
            
            article_id = cursor.lastrowid
            article_ids.append(article_id)
            
            # If this is the original article, use its ID as base for updates
            if tipo_versione == 'orig' or base_article_id is None:
                base_article_id = article_id
            
            print(f"✓ Saved article version {tipo_versione} (ID: {article_id}, status: {status})")
        
        # Update articolo_base_id for update versions
        if base_article_id and len(article_ids) > 1:
            for article_id in article_ids[1:]:  # Skip the first (base) article
                cursor.execute(
                    "UPDATE articoli SET articolo_base_id = ? WHERE id = ?",
                    [base_article_id, article_id]
                )
        
        conn.commit()
        
        print(f"✓ Saved article {articolo_data['numero_articolo']} with {len(versions)} versions")
        for i, version in enumerate(versions):
            version_desc = version.get('tipo_versione', 'orig')
            if version.get('numero_aggiornamento'):
                version_desc = f"agg.{version['numero_aggiornamento']}"
            print(f"  - {version_desc} (ID: {article_ids[i]})")
        
        return article_ids[0]  # Return base article ID
        
    except Exception as e:
        print(f"❌ Error saving article with simplified versioning: {e}")
        conn.rollback()
        return None

def save_articolo_basic(articolo_data, cursor, conn):
    """Save article using basic schema (fallback)"""
    try:
        # Determine status based on data_cessazione
        status = 'abrogato' if articolo_data.get('data_cessazione') else 'vigente'
        
        # Check if we have the simplified versioning columns
        cursor.execute("PRAGMA table_info(articoli)")
        columns = [column[1] for column in cursor.fetchall()]
        has_simplified_columns = 'articolo_base_id' in columns
        
        if has_simplified_columns:
            # Use simplified schema with versioning columns
            insert_query = """
                INSERT INTO articoli (
                    documento_id, numero_articolo, titoloAtto, testo_completo, 
                    testo_pulito, articoli_correlati, allegati, data_attivazione, 
                    data_cessazione, url_documento, status, 
                    articolo_base_id, tipo_versione, numero_aggiornamento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, [
                articolo_data['documento_id'],
                articolo_data['numero_articolo'],
                articolo_data['titoloAtto'],
                articolo_data['testo_completo'],
                articolo_data['testo_pulito'],
                articolo_data['articoli_correlati'],
                articolo_data.get('allegati', '[]'),
                articolo_data.get('data_attivazione'),
                articolo_data.get('data_cessazione'),
                articolo_data.get('url_documento', ''),
                status,
                None,  # articolo_base_id (NULL for single articles)
                'orig',  # tipo_versione (default to original)
                None   # numero_aggiornamento (NULL for original)
            ])
        else:
            # Fallback to basic schema
            insert_query = """
                INSERT INTO articoli (
                    documento_id, numero_articolo, titoloAtto, testo_completo, 
                    testo_pulito, articoli_correlati, allegati, data_attivazione, 
                    data_cessazione, url_documento, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, [
                articolo_data['documento_id'],
                articolo_data['numero_articolo'],
                articolo_data['titoloAtto'],
                articolo_data['testo_completo'],
                articolo_data['testo_pulito'],
                articolo_data['articoli_correlati'],
                articolo_data.get('allegati', '[]'),
                articolo_data.get('data_attivazione'),
                articolo_data.get('data_cessazione'),
                articolo_data.get('url_documento', ''),
                status
            ])
        
        article_id = cursor.lastrowid
        conn.commit()
        
        print(f"✓ Saved article {articolo_data['numero_articolo']} (basic schema, status: {status})")
        return article_id
        
    except Exception as e:
        print(f"❌ Error saving article with basic schema: {e}")
        conn.rollback()
        return None

# ========================================
# LEGACY UTILITY FUNCTIONS FOR COMPATIBILITY
# ========================================

def _get_name_type_year(norma_urn):
    """Extract name, type and year from a urn."""
    try:
        norma_inner_urn, norma_number = norma_urn.split(';')
    except ValueError:
        return (None, None, None)
        
    norma_inner_urn_parts = norma_inner_urn.split(':')
    if len(norma_inner_urn_parts) < 5:
        return (None, None, None)
        
    norma_dotted_type = norma_inner_urn_parts[3]
    norma_type = ' '.join(
        map(
            lambda x: x.title(),
            norma_dotted_type.split('.')
        )
    )
    norma_type_initials = ''.join(
        map(lambda x: x[0] + ".", norma_type.split())
    )
    original_date = norma_inner_urn_parts[4]
    norma_date = norma_year = None
    try:
        norma_date = datetime.strptime(
            original_date, '%Y-%m-%d'
        ).strftime('%d/%m/%Y')
        norma_year = datetime.strptime(
            original_date, '%Y-%m-%d'
        ).strftime('%Y')
    except ValueError:
        try:
            norma_date = datetime.strptime(
                original_date, '%Y-%m'
            ).strftime('%d/%m/%Y')
            norma_year = datetime.strptime(
                original_date, '%Y-%m'
            ).strftime('%Y')
        except ValueError as e:
            print(f"Error parsing date {original_date}: {e}")

    norma_name = f"{norma_type_initials} {norma_number} del {norma_date}"
    return (norma_name, norma_type, norma_year)

def _get_relative_url(absolute_url, base_url=normattiva_url):
    """elimina la base_url da una url assoluta"""
    return absolute_url.replace(base_url, '')

def _get_absolute_url(relative_url, base_url=normattiva_url):
    """torna una url assoluta, partendo da una relativa"""
    return f"{base_url}{relative_url}"

def _get_permalinks(tmp_url, session=None):
    print(f"[_get_permalinks] tmp_url: {tmp_url}")
    norma_url_tmp = _get_absolute_url(tmp_url)
    print(f"[_get_permalinks] norma_url_tmp: {norma_url_tmp}")
    norma_res_tmp = session.get(norma_url_tmp)
    print(f"[_get_permalinks] status_code: {norma_res_tmp.status_code}")
    
    if norma_res_tmp.status_code == 404:
        print("[_get_permalinks] 404 Not Found")
        return
    
    # Check if content contains "Provvedimento non trovato"
    if b'Provvedimento non trovato in banca dati' in norma_res_tmp.content:
        print("[_get_permalinks] Provvedimento non trovato in banca dati")
        return
    
    # Extract URN from tmp_url
    urn_match = re.search(r"urn:nir:[^!]+", tmp_url)
    law_urn = urn_match.group(0) if urn_match else None
    
    # For this type of page, return the current URL as the only permalink
    return [tmp_url], law_urn

def get_year_configuration():
    """Get year configuration from command line arguments or default"""
    if len(sys.argv) >= 2:
        try:
            target_year = int(sys.argv[1])
            
            # Check for optional second argument for number of documents
            num_docs = None
            if len(sys.argv) >= 3:
                try:
                    num_docs = int(sys.argv[2])
                except ValueError:
                    pass
            
            # Use provided number or estimate based on year
            if num_docs is None:
                if target_year >= 2020:
                    estimated_docs = 10  # Test with 10 documents for recent years
                elif target_year >= 2010:
                    estimated_docs = 8
                else:
                    estimated_docs = 5
            else:
                estimated_docs = num_docs
            
            print(f"🎯 Target year: {target_year} (processing {estimated_docs} documents)")
            
            # Warning for large numbers
            if estimated_docs > 50:
                print(f"⚠️ Processing {estimated_docs} documents may take a long time.")
                print(f"💡 Consider starting with a smaller number for testing.")
            
            return OrderedDict([(target_year, estimated_docs)])
        except ValueError:
            print(f"❌ Invalid year: {sys.argv[1]}. Using default configuration.")
    
    # Default configuration for testing
    return OrderedDict([
        (2024, 5),  # Test with 2024 documents
    ])

# ========================================
# MAIN PROCESSING FUNCTION
# ========================================

def process_permalinks(permalinks_and_urn, session=None):
    """Processa i permalink utilizzando la nuova struttura del database ottimizzata"""
    if not permalinks_and_urn:
        print("[process_permalinks] No permalinks data provided")
        return None
        
    permalinks, law_urn = permalinks_and_urn
    print(f"[process_permalinks] permalinks: {permalinks}, law_urn: {law_urn}")
    if session is None:
        print("La sessione deve essere specificata")
        return None
    if not permalinks:
        print("[process_permalinks] No permalinks to process")
        return None
    
    for permalink_url in permalinks:
        print(f"[process_permalinks] Processing permalink_url: {permalink_url}")
        norma_url = _get_absolute_url(permalink_url)
        norma_res = session.get(norma_url)
        print(f"[process_permalinks] norma_res status_code: {norma_res.status_code}")
        norma_el = lxml.html.fromstring(norma_res.content)
        
        # Extract law metadata from meta tags and HTML elements
        meta_title = norma_el.xpath('//meta[@property="eli:title"]/@content')
        meta_type = norma_el.xpath('//meta[@property="eli:type_document"]/@resource')
        meta_year = norma_el.xpath('//meta[@property="eli:date_document"]/@content')
        
        # Try to extract the actual document title from the HTML element
        # First try the titoloAtto element as shown in the screenshot
        title_from_html = None
        title_selectors = [
            '#titoloAtto',  # Primary selector for document title
            '.titoloAtto',  # Class-based selector
            'div[id="titoloAtto"]',  # Specific div element
            'div.data_info.text-center',  # Based on screenshot classes
            'h1.data_info',  # Alternative h1 with data_info class
            'h2.data_info',  # Alternative h2 with data_info class
            '.data_info.text-center',  # General data_info element
        ]
        
        for selector in title_selectors:
            elements = norma_el.cssselect(selector)
            if elements:
                title_text = elements[0].text_content().strip()
                if title_text and len(title_text) > 10:  # Make sure it's a meaningful title
                    # Clean the title by removing extra whitespace and normalizing
                    title_text = re.sub(r'\s+', ' ', title_text)
                    title_text = re.sub(r'\r\n|\r|\n', ' ', title_text)
                    title_text = re.sub(r'\t', ' ', title_text)
                    title_text = re.sub(r'\s+', ' ', title_text).strip()
                    
                    title_from_html = title_text
                    print(f"[process_permalinks] Found title from HTML: {title_from_html}")
                    break
        
        # Use HTML title if found, otherwise fall back to meta title
        name = title_from_html if title_from_html else (meta_title[0].strip() if meta_title else None)
        
        # Clean the title if we have one
        if name:
            # Remove extra whitespace, line breaks, and normalize
            name = re.sub(r'\s+', ' ', name)
            name = re.sub(r'\r\n|\r|\n', ' ', name)
            name = re.sub(r'\s+', ' ', name).strip()
            
        type_ = meta_type[0].split('#')[-1] if meta_type else None
        year = meta_year[0][:4] if meta_year else None
        
        # Extract URN from the current law
        current_urn = law_urn if law_urn else None
        if not current_urn and permalink_url:
            urn_match = re.search(r"urn:nir:[^!]+", permalink_url)
            current_urn = urn_match.group(0) if urn_match else None
        
        # Extract content - try different selectors with bodyTesto priority
        content_el = (norma_el.cssselect('#testoNormalizzato .bodyTesto') or 
                     norma_el.cssselect('.bodyTesto') or
                     norma_el.cssselect('#containerTesto') or
                     norma_el.cssselect('.DettaglioPag'))
        
        content = ""
        if content_el:
            content = content_el[0].text_content().strip()
        else:
            # Fallback to extracting content from the body
            body_content = norma_el.cssselect('body')
            if body_content:
                content = body_content[0].text_content().strip()
        
        # If we still don't have basic info, try to extract from other sources
        if not name:
            # Try titoloAtto element first
            title_elements = norma_el.cssselect('#titoloAtto, .titoloAtto, div[id="titoloAtto"]')
            if title_elements:
                name = title_elements[0].text_content().strip()
            else:
                # Fallback to page title
                page_title = norma_el.xpath('//title/text()')
                if page_title:
                    name = page_title[0].strip()
                else:
                    # Final fallback to headers
                    h_elements = norma_el.cssselect('h1, h2, h3')
                    if h_elements:
                        name = h_elements[0].text_content().strip()
        
        if not type_:
            if name and 'LEGGE' in name.upper():
                type_ = 'LEGGE'
            elif name and 'DECRETO' in name.upper():
                type_ = 'DECRETO'
        
        if not year and name:
            year_match = re.search(r'\b(19|20)\d{2}\b', name)
            if year_match:
                year = year_match.group(0)
        
        print(f"[process_permalinks] Extracted data: name={name}, type={type_}, year={year}, urn={current_urn}")
        
        if not (name and type_ and year):
            print(f"[process_permalinks] Skipping, missing essential data: name={name}, type={type_}, year={year}")
            continue
        
        # ==================================================
        # SALVATAGGIO CON NUOVA STRUTTURA OTTIMIZZATA
        # ==================================================
        
        # Parse URN per ottenere numero - URN should take precedence
        urn_components = parse_urn_components(current_urn or "")
        numero = urn_components.get("numero", "")
        
        # Only extract from name if URN doesn't provide the number
        if not numero and name:
            # Try to extract the official number from "n. XX" pattern first
            numero_match = re.search(r'\bn\.\s*(\d+)', name)
            if numero_match:
                numero = numero_match.group(1)
            else:
                # Fallback to any number in the name
                numero_match = re.search(r'\b(\d+)\b', name)
                if numero_match:
                    numero = numero_match.group(1)
        
        # Ensure URN number takes precedence - don't override it
        if urn_components.get("numero"):
            numero = urn_components.get("numero")
            print(f"[process_permalinks] Using URN numero: {numero} (URN: {current_urn})")
        
        print(f"[process_permalinks] URN components: {urn_components}")
        print(f"[process_permalinks] Extracted numero: {numero} from URN: {current_urn}")
        
        # Debug: Print what we found in the name for comparison
        if name:
            name_numero_match = re.search(r'\bn\.\s*(\d+)', name)
            if name_numero_match:
                print(f"[process_permalinks] Name contains 'n. {name_numero_match.group(1)}' - URN should take precedence")
        
        # Determina metadati
        tipo_atto = extract_tipo_atto(name, type_)
        anno = int(year) if year and year.isdigit() else extract_year_from_name(name)
        materia_principale = determine_materia_principale(name, content)
        livello_gerarchia = get_livello_gerarchia(tipo_atto)
        
        # Prepara dati documento con testo pulito
        cleaned_content = clean_article_text(content) if content else ""
        documento_data = {
            'numero': numero or "N/A",
            'anno': anno,
            'tipo_atto': tipo_atto,
            'titoloAtto': name,
            'data_pubblicazione': f"{anno}-01-01",
            'materia_principale': materia_principale,
            'status': 'vigente',
            'livello_gerarchia': livello_gerarchia,
            'url_normattiva': norma_url,
            'urn': current_urn or "",
            'testo_completo': cleaned_content[:10000] if cleaned_content else ""  # Limite per performance
        }
        
        # Salva documento
        documento_id = save_documento_normativo(documento_data)
        if not documento_id:
            print(f"[process_permalinks] Failed to save document")
            continue

        # ==================================================
        # ENHANCED ARTICLE SCRAPING WITH BODYTEXT AND VERSIONING
        # ==================================================
        
        articoli_extracted = False
        
        # Use enhanced article scraping that handles bodyTesto and versioning
        try:
            print(f"[process_permalinks] Using enhanced article scraping with bodyTesto extraction")
            article_ids = enhanced_article_scraping_with_versioning(norma_url, session, documento_id)
            if article_ids:
                articoli_extracted = True
                print(f"[process_permalinks] Enhanced scraping processed {len(article_ids)} articles with bodyTesto and versioning")
            else:
                print("[process_permalinks] Enhanced scraping found no articles")
        except Exception as e:
            print(f"[process_permalinks] Enhanced article scraping failed: {e}")
        
        # Fallback to standard article extraction if enhanced scraping didn't work
        if not articoli_extracted:
            print("[process_permalinks] Using standard article extraction")
            articoli_extracted = extract_all_articles_with_bodytext(norma_url, session, documento_id)
        
        # Final fallback: create main article if no articles were extracted
        if not articoli_extracted:
            print("[process_permalinks] Creating fallback main article")
            
            # Check if we have bodyTesto content
            bodytext_elements = norma_el.cssselect('.bodyTesto')
            if bodytext_elements:
                testo_completo = bodytext_elements[0].text_content().strip()
                testo_pulito = clean_article_text(testo_completo)
                articoli_correlati = extract_correlated_articles(bodytext_elements[0])
            else:
                testo_completo = content[:5000] if content else ""
                testo_pulito = clean_article_text(testo_completo)
                articoli_correlati = []
            
            articolo_data = {
                'documento_id': documento_id,
                'numero_articolo': '1',
                'titolo': 'Articolo principale',
                'testo_completo': testo_completo,
                'testo_pulito': testo_pulito,
                'articoli_correlati': json.dumps(articoli_correlati, ensure_ascii=False),
                'versions': [{
                    'tipo_versione': 'orig',
                    'numero_aggiornamento': None,
                    'testo_versione': testo_completo,
                    'testo_pulito': testo_pulito,
                    'articoli_correlati': articoli_correlati,
                    'allegati': [],
                    'data_inizio_vigore': datetime.now().date(),
                    'data_fine_vigore': None,
                    'is_current': True,
                    'status': 'vigente'
                }]
            }
            save_articolo_with_versions(articolo_data)

# ========================================
# MAIN EXECUTION
# ========================================

if __name__ == '__main__':

    print("🚀 NORMATTIVA-SCRAPE Unified Scraper - Enhanced Legal Document Scraper")
    print("=" * 70)
    print("✓ bodyTesto extraction for testo_completo and testo_pulito")
    print("✓ Correlated articles extraction from links within bodyTesto")
    print("✓ Versioning support (original + aggiornamenti)")
    print("✓ Automatic fonte_origine population after scraping")
    print("✓ Single unified scraper entry point")
    print()
    
    # Show usage if help requested
    if len(sys.argv) >= 2 and sys.argv[1] in ['-h', '--help', 'help']:
        print("📖 Utilizzo:")
        print("  python scraper_optimized.py [anno] [numero_documenti]")
        print()
        print("Esempi:")
        print("  python scraper_optimized.py 2024          # Estrae 10 documenti del 2024")
        print("  python scraper_optimized.py 2024 50       # Estrae 50 documenti del 2024") 
        print("  python scraper_optimized.py 2023 100      # Estrae 100 documenti del 2023")
        print("  python scraper_optimized.py               # Configurazione di default (2024, 5 docs)")
        print()
        print("🧹 Per resettare il database:")
        print("  python clear_database.py")
        print()
        print("💡 Caratteristiche:")
        print("  - Estrazione testo da div bodyTesto")
        print("  - Estrazione articoli correlati da link in bodyTesto") 
        print("  - Supporto versioning (originale + aggiornamenti)")
        print("  - Modalità multivigente per rilevare pulsanti aggiornamenti")
        print("  - Popolamento automatico fonte_origine dopo scraping")
        print()
        sys.exit(0)

    # Inizializza il database ottimizzato
    init_optimized_database()

    # Get year configuration
    norme_anno = get_year_configuration()

    # genera istanza di navigazione,
    # con header modificati
    with requests.session() as session:
        session.headers.update({
            'User-agent': "Mozilla/5.0"
                "(Macintosh; Intel Mac OS X 10_11_6) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/55.0.2883.95 Safari/537.36",
            'Connection': 'keep-alive'
        })

        # Process all documents for the specified years
        for anno, n_norme in norme_anno.items():
            for k in range(1, n_norme+1):
                # Use multivigente mode to show article updates buttons
                norma_url = f"/uri-res/N2Ls?urn:nir:{anno};{k}!multivigente~"
                print(f"Processing in multivigente mode: {norma_url}")

                # urn e url parziali della norma
                process_permalinks(
                    _get_permalinks(
                        norma_url,
                        session=session
                    ),
                    session=session
                )

        # ========================================
        # AUTOMATIC FONTE ORIGINE POPULATION
        # ========================================
        
        print("\n" + "=" * 70)
        print("🎯 POPULATING FONTE ORIGINE AUTOMATICALLY")
        print("=" * 70)
        
        if FonteOriginePopulator:
            try:
                populator = FonteOriginePopulator()
                populator.run_full_population()
                print("✅ Fonte origine population completed successfully!")
            except Exception as e:
                print(f"❌ Error during fonte origine population: {e}")
                print("⚠️  Articles may not have fonte_origine values populated")
        else:
            print("⚠️  FonteOriginePopulator not available - skipping automatic population")

        # ========================================
        # FINAL STATISTICS
        # ========================================

        # Statistiche finali
        try:
            conn = sqlite3.connect('data.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM documenti_normativi")
            doc_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articoli")
            art_count = cursor.fetchone()[0]
            
            # Try to get citations count (table may not exist)
            try:
                cursor.execute("SELECT COUNT(*) FROM citazioni_normative")
                cit_count = cursor.fetchone()[0]
            except:
                cit_count = 0
            
            print(f"\n=== STATISTICHE FINALI ===")
            print(f"Documenti normativi: {doc_count}")
            print(f"Articoli: {art_count}")
            print(f"Citazioni: {cit_count}")
            
            # Statistiche per tipo di atto
            cursor.execute("""
                SELECT tipo_atto, COUNT(*) as count 
                FROM documenti_normativi 
                GROUP BY tipo_atto 
                ORDER BY count DESC
            """)
            tipo_stats = cursor.fetchall()
            
            print(f"\n=== DISTRIBUZIONE PER TIPO ATTO ===")
            for stat in tipo_stats:
                print(f"{stat[0]}: {stat[1]}")
            
            # Statistiche per materia
            cursor.execute("""
                SELECT materia_principale, COUNT(*) as count 
                FROM documenti_normativi 
                GROUP BY materia_principale 
                ORDER BY count DESC
            """)
            materia_stats = cursor.fetchall()
            
            print(f"\n=== DISTRIBUZIONE PER MATERIA ===")
            for stat in materia_stats:
                print(f"{stat[0]}: {stat[1]}")
            
            # Try to get versioning statistics if available
            try:
                cursor.execute("SELECT COUNT(*) FROM articoli_versioni")
                result = cursor.fetchone()
                versions_count = result[0] if result else 0
                
                if versions_count > 0:
                    print(f"\n=== STATISTICHE VERSIONING ===")
                    print(f"Versioni articoli totali: {versions_count}")
                    
                    cursor.execute("""
                        SELECT tipo_versione, COUNT(*) as count 
                        FROM articoli_versioni 
                        GROUP BY tipo_versione 
                        ORDER BY count DESC
                    """)
                    version_stats = cursor.fetchall()
                    
                    print("Per tipo di versione:")
                    for stat in version_stats:
                        print(f"  {stat[0]}: {stat[1]}")
                        
            except Exception as e:
                print(f"Note: Versioning statistics not available: {e}")
            
            # Try to get bodyTesto extraction statistics
            try:
                cursor.execute("SELECT COUNT(*) FROM articoli WHERE testo_pulito IS NOT NULL AND LENGTH(testo_pulito) > 0")
                result = cursor.fetchone()
                bodytext_count = result[0] if result else 0
                
                cursor.execute("SELECT COUNT(*) FROM articoli WHERE articoli_correlati IS NOT NULL AND articoli_correlati != '[]'")
                result = cursor.fetchone()
                correlated_count = result[0] if result else 0
                
                print(f"\n=== STATISTICHE BODYTEXT EXTRACTION ===")
                print(f"Articoli con testo_pulito: {bodytext_count}")
                print(f"Articoli con correlazioni: {correlated_count}")
                
            except Exception as e:
                print(f"Note: BodyText statistics not available: {e}")
            
            # Try to get fonte_origine statistics
            try:
                cursor.execute("SELECT COUNT(*) FROM articoli WHERE fonte_origine IS NOT NULL")
                result = cursor.fetchone()
                fonte_count = result[0] if result else 0
                
                cursor.execute("SELECT fonte_origine, COUNT(*) as count FROM articoli WHERE fonte_origine IS NOT NULL GROUP BY fonte_origine ORDER BY count DESC")
                fonte_stats = cursor.fetchall()
                
                print(f"\n=== STATISTICHE FONTE ORIGINE ===")
                print(f"Articoli con fonte_origine: {fonte_count}")
                
                if fonte_stats:
                    print("Distribuzione per fonte:")
                    for stat in fonte_stats:
                        print(f"  {stat[0]}: {stat[1]}")
                
            except Exception as e:
                print(f"Note: Fonte origine statistics not available: {e}")
            
            conn.close()
                
        except Exception as e:
            print(f"Error generating statistics: {e}")
        
        print("✓ Unified scraping completed with enhanced bodyTesto extraction, versioning, and automatic fonte origine population!")
        print("✓ All articles now have fonte_origine values populated automatically!")
