from collections import OrderedDict
import re
import json
import sqlite3
from datetime import datetime
import lxml.html
import requests
import scraperwiki

# Import the new article updates functionality
try:
    from article_updates_scraper import (
        enhanced_article_scraping,
        process_article_with_updates,
        save_article_with_updates,
        get_article_updates_stats
    )
    ARTICLE_UPDATES_AVAILABLE = True
except ImportError as e:
    print(f"Article updates functionality not available: {e}")
    ARTICLE_UPDATES_AVAILABLE = False

normattiva_url = "http://www.normattiva.it"

# ========================================
# UTILITY FUNCTIONS FOR NEW DATABASE
# ========================================

def init_optimized_database():
    """Inizializza il database con la nuova struttura ottimizzata"""
    try:
        import sqlite3
        
        # Connessione diretta al database
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
        # Fallback usando scraperwiki se disponibile
        try:
            cursor = scraperwiki.sql.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documenti_normativi'")
            if not cursor:
                print("Initializing new optimized database schema via scraperwiki...")
                with open("database_schema.sql", "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                scraperwiki.sql.executescript(schema_sql)
                print("New database schema initialized successfully")
        except Exception as e2:
            print(f"Both database initialization methods failed: {e}, {e2}")
            raise

def parse_urn_components(urn: str) -> dict:
    """Estrae componenti da URN: urn:nir:stato:legge:2023-12-01;123"""
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
        import sqlite3
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
    """Salva un articolo nel database"""
    try:
        import sqlite3
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        insert_query = """
            INSERT INTO articoli (
                documento_id, numero_articolo, titoloAtto, testo_completo, testo_pulito
            ) VALUES (?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, [
            articolo_data.get('documento_id'),
            articolo_data.get('numero_articolo', '1'),
            articolo_data.get('titoloAtto', ''),
            articolo_data.get('testo_completo', ''),
            articolo_data.get('testo_pulito', '')
        ])
        
        art_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"Saved article with id: {art_id}")
        return art_id
        
    except Exception as e:
        print(f"Error saving article: {e}")
        return None

def save_citazione_normativa(citazione_data: dict):
    """Salva una citazione normativa"""
    try:
        import sqlite3
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
        import sqlite3
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
        import sqlite3
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM articoli WHERE documento_id = ? LIMIT 1", [documento_id])
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting articles by document: {e}")
        return None


def _get_relative_url(absolute_url, base_url=normattiva_url):
    """elimina la base_url da una url assoluta

    :param absolute_url:
    :param base_url:
    :return: string
    """
    return absolute_url.replace(base_url, '')


def _get_absolute_url(relative_url, base_url=normattiva_url):
    """torna una url assoluta, partendo da una relativa

    :param relative_url:
    :param base_url:
    :return: string
    """
    return f"{base_url}{relative_url}"


def _get_permalinks(tmp_url, session=None):
    print(f"[_get_permalinks] tmp_url: {tmp_url}")
    norma_url_tmp = _get_absolute_url(tmp_url)
    print(f"[_get_permalinks] norma_url_tmp: {norma_url_tmp}")
    norma_res_tmp = session.get(norma_url_tmp)
    print(f"[_get_permalinks] status_code: {norma_res_tmp.status_code}")
    # Save HTML for inspection
    with open("debug_norma_res_tmp.html", "wb") as f:
        f.write(norma_res_tmp.content)
    print("[_get_permalinks] Saved HTML to debug_norma_res_tmp.html")
    if norma_res_tmp.status_code == 404:
        print("[_get_permalinks] 404 Not Found")
        return None, None
    
    # Check if content contains "Provvedimento non trovato"
    if b'Provvedimento non trovato in banca dati' in norma_res_tmp.content:
        print("[_get_permalinks] Provvedimento non trovato in banca dati")
        return None, None
    
    # Extract URN from tmp_url
    urn_match = re.search(r"urn:nir:[^!]+", tmp_url)
    law_urn = urn_match.group(0) if urn_match else None
    
    # For this type of page, return the current URL as the only permalink
    # since it appears to be the final document page
    return [tmp_url], law_urn


def _get_permalink(tmp_url, session=None):
    print(f"[_get_permalink] tmp_url: {tmp_url}")
    if session is None:
        print("La sessione deve essere specificata")
        return None
    norma_res_tmp = session.get(tmp_url)
    print(f"[_get_permalink] status_code: {norma_res_tmp.status_code}")
    norma_el_tmp = lxml.html.fromstring(norma_res_tmp.content)
    if b'Provvedimento non trovato in banca dati' in norma_res_tmp.content or 'Provvedimento non trovato in banca dati' in norma_res_tmp.text:
        print("[_get_permalink] Provvedimento non trovato in banca dati")
        return None
    permalink_imgs = norma_el_tmp.cssselect(
        "img[alt='Collegamento permanente']"
    )
    print(f"[_get_permalink] permalink_imgs: {permalink_imgs}")
    if not permalink_imgs:
        print("[_get_permalink] No permalink_imgs found")
        return None
    permalink_href = permalink_imgs[0].getparent().attrib['href']
    print(f"[_get_permalink] permalink_href: {permalink_href}")
    permalink_url = _get_absolute_url(permalink_href)
    print(f"[_get_permalink] permalink_url: {permalink_url}")
    permalink_res = session.get(permalink_url)
    print(f"[_get_permalink] permalink_res status_code: {permalink_res.status_code}")
    permalink_el = lxml.html.fromstring(permalink_res.content)
    norma_urn_links = permalink_el.cssselect(
        '#corpo_errore a'
    )
    print(f"[_get_permalink] norma_urn_links: {norma_urn_links}")
    if not norma_urn_links:
        print("[_get_permalink] No norma_urn_links found")
        return None
    norma_urn_href = norma_urn_links[0].attrib['href']
    print(f"[_get_permalink] norma_urn_href: {norma_urn_href}")
    return norma_urn_href


def _get_name_type_year(norma_urn):
    """Extract name, type and year from a urn.
    Return None in case of parser error

    :param norma_urn: the urn, containing the number
    :return: tuple with name and type or None
    """
    try:
        norma_inner_urn, norma_number = norma_urn.split(';')
    except ValueError:
        # Not enough parts
        return (None, None, None)
    norma_inner_urn_parts = norma_inner_urn.split(':')
    if len(norma_inner_urn_parts) < 5:
        # Not enough fields in URN
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
                original_date, '%Y'
            ).strftime('%Y')
            norma_year = norma_date
        except ValueError as e:
            if 'unconverted data remains' in e.args[0]:
                unconverted_data = e.args[0].split(':')[1].strip()
                norma_date = original_date.replace(unconverted_data, '')
                try:
                    norma_date = datetime.strptime(norma_date, '%Y').strftime('%Y')
                    norma_year = norma_date
                except ValueError:
                    return (None, None, None)

    norma_name = f"{norma_type_initials} {norma_number} del {norma_date}"

    return (norma_name, norma_type, norma_year)


def process_permalinks(permalinks_and_urn, session=None):
    """Processa i permalink utilizzando la nuova struttura del database ottimizzata"""
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
        
        # Extract law metadata from meta tags
        meta_title = norma_el.xpath('//meta[@property="eli:title"]/@content')
        meta_type = norma_el.xpath('//meta[@property="eli:type_document"]/@resource')
        meta_year = norma_el.xpath('//meta[@property="eli:date_document"]/@content')
        
        name = meta_title[0].strip() if meta_title else None
        type_ = meta_type[0].split('#')[-1] if meta_type else None
        year = meta_year[0][:4] if meta_year else None
        
        # Extract URN from the current law
        current_urn = law_urn if law_urn else None
        if not current_urn and permalink_url:
            urn_match = re.search(r"urn:nir:[^!]+", permalink_url)
            current_urn = urn_match.group(0) if urn_match else None
        
        # Extract content - try different selectors
        content_el = (norma_el.cssselect('#testoNormalizzato .bodyTesto') or 
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
            page_title = norma_el.xpath('//title/text()')
            if page_title:
                name = page_title[0].strip()
            else:
                h_elements = norma_el.cssselect('h2, h3')
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
        
        # Parse URN per ottenere numero
        urn_components = parse_urn_components(current_urn or "")
        numero = urn_components.get("numero", "")
        if not numero and name:
            numero_match = re.search(r'\b(\d+)\b', name)
            if numero_match:
                numero = numero_match.group(1)
        
        # Determina metadati
        tipo_atto = extract_tipo_atto(name, type_)
        anno = int(year) if year and year.isdigit() else extract_year_from_name(name)
        materia_principale = determine_materia_principale(name, content)
        livello_gerarchia = get_livello_gerarchia(tipo_atto)
        
        # Prepara dati documento
        documento_data = {
            'numero': numero or "N/A",
            'anno': anno,
            'tipo_atto': tipo_atto,
            'titolo': name,
            'data_pubblicazione': f"{anno}-01-01",
            'materia_principale': materia_principale,
            'status': 'vigente',
            'livello_gerarchia': livello_gerarchia,
            'url_normattiva': norma_url,
            'urn': current_urn or "",
            'testo_completo': content[:10000] if content else ""  # Limite per performance
        }
        
        # Salva documento
        documento_id = save_documento_normativo(documento_data)
        if not documento_id:
            print(f"[process_permalinks] Failed to save document")
            continue
        
        # ==================================================
        # ENHANCED ARTICLE SCRAPING WITH UPDATES
        # ==================================================
        
        articolo_principale_id = None
        
        if ARTICLE_UPDATES_AVAILABLE:
            # Use enhanced article scraping that handles updates
            try:
                article_ids = enhanced_article_scraping(norma_url, session, documento_id)
                if article_ids:
                    articolo_principale_id = article_ids[0]  # Use first article as main
                    print(f"Enhanced scraping processed {len(article_ids)} articles")
                else:
                    print("Enhanced scraping found no articles, falling back to basic method")
            except Exception as e:
                print(f"Enhanced article scraping failed: {e}, falling back to basic method")
        
        # Fallback to basic article creation if enhanced scraping didn't work
        if not articolo_principale_id:
            articolo_data = {
                'documento_id': documento_id,
                'numero_articolo': '1',
                'titolo': 'Articolo principale',
                'testo_completo': content[:5000] if content else "",
                'testo_pulito': content[:5000] if content else ""
            }
            
            articolo_principale_id = save_articolo(articolo_data)
        
        # ==================================================
        # GESTIONE RIFERIMENTI E CITAZIONI
        # ==================================================
        
        links = set()
        
        # Cerca iframe con TOC
        toc_frames = norma_el.cssselect("iframe[id*='Frame'], iframe[src*='albero']")
        if toc_frames:
            try:
                toc_src = toc_frames[0].attrib['src']
                print(f"[process_permalinks] toc_src: {toc_src}")
                toc_url = _get_absolute_url(toc_src)
                toc_res = session.get(toc_url)
                
                if toc_res.status_code == 200:
                    toc_el = lxml.html.fromstring(toc_res.content)
                    for a in toc_el.cssselect("a[href*='articolo'], a[href*='urn']"):
                        href = a.attrib.get('href', '')
                        if 'urn' in href and ';' in href:
                            links.add(href)
            except Exception as e:
                print(f"[process_permalinks] Error processing TOC: {e}")
        
        # Cerca riferimenti URN diretti
        urn_links = norma_el.cssselect("a[href*='urn:nir']")
        for link in urn_links:
            href = link.attrib.get('href', '')
            if 'urn:nir' in href and ';' in href:
                urn_match = re.search(r'urn:nir:[^;]+;\d+', href)
                if urn_match:
                    links.add(href)
        
        print(f"[process_permalinks] Found {len(links)} reference links")
        
        # Processa i link trovati
        for l in links:
            try:
                # Estrai URN dal link
                if '?' in l:
                    l_urn = l.split('?')[1].split('!')[0] if '!' in l.split('?')[1] else l.split('?')[1]
                else:
                    urn_match = re.search(r'urn:nir:[^;]+;\d+', l)
                    l_urn = urn_match.group(0) if urn_match else None
                
                if not l_urn:
                    continue
                
                # Ottieni metadati del documento riferito
                ref_name, ref_type, ref_year = _get_name_type_year(l_urn)
                if not ref_name:
                    continue
                
                # Verifica se il documento riferito esiste già
                ref_documento_id = get_documento_by_urn(l_urn)
                ref_articolo_id = None
                
                if ref_documento_id:
                    # Trova o crea articolo principale
                    ref_articolo_id = get_articoli_by_documento(ref_documento_id)
                else:
                    # Crea documento riferito con dati minimali
                    ref_urn_components = parse_urn_components(l_urn)
                    ref_numero = ref_urn_components.get("numero", "")
                    ref_tipo_atto = extract_tipo_atto(ref_name, ref_type)
                    ref_anno = int(ref_year) if ref_year and ref_year.isdigit() else 2000
                    
                    ref_documento_data = {
                        'numero': ref_numero or "N/A",
                        'anno': ref_anno,
                        'tipo_atto': ref_tipo_atto,
                        'titolo': ref_name,
                        'data_pubblicazione': f"{ref_anno}-01-01",
                        'materia_principale': 'Altro',
                        'status': 'vigente',
                        'livello_gerarchia': get_livello_gerarchia(ref_tipo_atto),
                        'urn': l_urn,
                        'testo_completo': ''
                    }
                    
                    ref_documento_id = save_documento_normativo(ref_documento_data)
                    
                    if ref_documento_id:
                        # Crea articolo principale per il documento riferito
                        ref_articolo_data = {
                            'documento_id': ref_documento_id,
                            'numero_articolo': '1',
                            'titolo': 'Articolo principale',
                            'testo_completo': '',
                            'testo_pulito': ''
                        }
                        ref_articolo_id = save_articolo(ref_articolo_data)
                
                # Salva citazione se abbiamo entrambi gli articoli
                if articolo_principale_id and ref_articolo_id:
                    citazione_data = {
                        'articolo_citante_id': articolo_principale_id,
                        'articolo_citato_id': ref_articolo_id,
                        'tipo_citazione': 'rinvio',
                        'contesto_citazione': f"Riferimento da {name} a {ref_name}"
                    }
                    save_citazione_normativa(citazione_data)
                
            except Exception as e:
                print(f"[process_permalinks] Error processing reference {l}: {e}")
                continue



if __name__ == '__main__':

    # Inizializza il database ottimizzato
    init_optimized_database()

    norme_anno = OrderedDict([
        (2025, 15),
        # (2015, 222),
        # (2014, 203),
        # (2013, 159),
        # (2012, 263),
        # (2011, 237),
        # (2010, 277),
        # (2009, 220),
        # (2008, 222),
        # (2007, 278),
    ])

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

        for anno, n_norme in norme_anno.items():
            for k in range(1, n_norme+1):
                norma_url = f"/uri-res/N2Ls?urn:nir:{anno};{k}!vig="
                print(norma_url)

                # urn e url parziali della norma
                process_permalinks(
                    _get_permalinks(
                        norma_url,
                        session=session
                    ),
                    session=session
                )
                scraperwiki.status('ok')

        # Statistiche finali
        try:
            import sqlite3
            conn = sqlite3.connect('data.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM documenti_normativi")
            doc_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articoli")
            art_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM citazioni_normative")
            cit_count = cursor.fetchone()[0]
            
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
            
            # Statistiche aggiornamenti articoli se disponibili
            if ARTICLE_UPDATES_AVAILABLE:
                try:
                    updates_stats = get_article_updates_stats()
                    print(f"\n=== STATISTICHE AGGIORNAMENTI ARTICOLI ===")
                    print(f"Modifiche totali: {updates_stats.get('total_modifications', 0)}")
                    print(f"Articoli con modifiche: {updates_stats.get('articles_with_modifications', 0)}")
                    print(f"Modifiche recenti (30gg): {updates_stats.get('recent_modifications', 0)}")
                    
                    by_type = updates_stats.get('by_type', {})
                    if by_type:
                        print(f"Per tipo di modifica:")
                        for tipo, count in by_type.items():
                            print(f"  {tipo}: {count}")
                except Exception as e:
                    print(f"Error getting article updates stats: {e}")
            
            conn.close()
                
        except Exception as e:
            print(f"Error generating statistics: {e}")
        
        # Compatibilità con scraperwiki per status
        try:
            scraperwiki.status('ok')
        except:
            print("ScraperWiki status not available")

