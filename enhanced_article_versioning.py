#!/usr/bin/env python3
"""
Enhanced article versioning functionality for NORMATTIVA-SCRAPE
Handles original content (orig.) and updates (agg.1, agg.2, etc.) with validity dates
"""

import re
import json
import sqlite3
from datetime import datetime, date
import lxml.html
import requests
from urllib.parse import urljoin
from typing import List, Dict, Optional, Tuple

def parse_validity_dates(date_text: str) -> Tuple[Optional[date], Optional[date]]:
    """
    Parse validity dates from Italian legal text
    
    Args:
        date_text: Text containing date information like "Testo in vigore dal: 17-3-2020 al: 29-4-2020"
        
    Returns:
        Tuple of (start_date, end_date) or (None, None) if parsing fails
    """
    try:
        # Pattern for "Testo in vigore dal: DD-MM-YYYY al: DD-MM-YYYY"
        full_range_pattern = r'Testo in vigore dal:\s*(\d{1,2}-\d{1,2}-\d{4})\s*al:\s*(\d{1,2}-\d{1,2}-\d{4})'
        
        # Pattern for "Testo in vigore dal: DD-MM-YYYY"
        start_only_pattern = r'Testo in vigore dal:\s*(\d{1,2}-\d{1,2}-\d{4})'
        
        # Try full range first
        full_match = re.search(full_range_pattern, date_text)
        if full_match:
            start_str, end_str = full_match.groups()
            start_date = datetime.strptime(start_str, '%d-%m-%Y').date()
            end_date = datetime.strptime(end_str, '%d-%m-%Y').date()
            return start_date, end_date
        
        # Try start only
        start_match = re.search(start_only_pattern, date_text)
        if start_match:
            start_str = start_match.group(1)
            start_date = datetime.strptime(start_str, '%d-%m-%Y').date()
            return start_date, None
        
        # Alternative patterns
        # Pattern: "dal DD-MM-YYYY" or "dal DD/MM/YYYY"
        alt_pattern = r'dal\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
        alt_match = re.search(alt_pattern, date_text)
        if alt_match:
            date_str = alt_match.group(1).replace('/', '-')
            start_date = datetime.strptime(date_str, '%d-%m-%Y').date()
            return start_date, None
            
    except ValueError as e:
        print(f"Warning: Could not parse date from '{date_text}': {e}")
    
    return None, None

def extract_article_version_type(element) -> str:
    """
    Extract version type from article element (orig., agg.1, agg.2, etc.)
    
    Args:
        element: lxml element containing the article version
        
    Returns:
        str: Version type like 'orig', 'agg.1', 'agg.2', etc.
    """
    # Look for version indicators in the element
    version_indicators = element.xpath('.//text()[contains(., "agg.") or contains(., "orig.")]')
    
    for indicator in version_indicators:
        text = indicator.strip()
        # Match patterns like "agg.1", "agg.2", "orig."
        match = re.search(r'(orig\.|agg\.\d+)', text)
        if match:
            return match.group(1)
    
    # Check in parent elements or siblings
    parent = element.getparent()
    if parent is not None:
        parent_text = parent.text_content()
        match = re.search(r'(orig\.|agg\.\d+)', parent_text)
        if match:
            return match.group(1)
    
    # Default to 'orig' if no indicator found
    return 'orig'

def extract_modification_reference(element) -> Optional[str]:
    """
    Extract the legal reference for the modification (e.g., "D.L. 17 marzo 2020, n. 18")
    
    Args:
        element: lxml element containing the modification reference
        
    Returns:
        str or None: Reference text if found
    """
    # Look for patterns like "D.L.", "D.Lgs.", "L.", followed by date and number
    text = element.text_content()
    
    patterns = [
        r'(D\.L\.\s+\d{1,2}\s+\w+\s+\d{4},?\s*n\.\s*\d+)',
        r'(D\.Lgs\.\s+\d{1,2}\s+\w+\s+\d{4},?\s*n\.\s*\d+)',
        r'(L\.\s+\d{1,2}\s+\w+\s+\d{4},?\s*n\.\s*\d+)',
        r'(Legge\s+\d{1,2}\s+\w+\s+\d{4},?\s*n\.\s*\d+)',
        # More generic pattern
        r'([A-Z]\.[A-Z]*\.?\s*\d{1,2}\s+\w+\s+\d{4}.*?n\.\s*\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None

def save_article_version(cursor, articolo_id: int, version_data: Dict) -> int:
    """
    Save a single version of an article to the database
    
    Args:
        cursor: SQLite cursor
        articolo_id: ID of the main article
        version_data: Dictionary containing version information
        
    Returns:
        int: ID of the created version record
    """
    
    # Parse version number from tipo_versione
    numero_aggiornamento = None
    if version_data['tipo_versione'].startswith('agg.'):
        try:
            numero_aggiornamento = int(version_data['tipo_versione'].split('.')[1])
        except (IndexError, ValueError):
            numero_aggiornamento = 1
    
    insert_sql = """
        INSERT INTO articoli_versioni (
            articolo_id, tipo_versione, numero_aggiornamento,
            testo_versione, testo_pulito,
            data_inizio_vigore, data_fine_vigore,
            riferimento_modifica, is_current, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.execute(insert_sql, (
        articolo_id,
        version_data['tipo_versione'],
        numero_aggiornamento,
        version_data['testo_versione'],
        version_data.get('testo_pulito'),
        version_data.get('data_inizio_vigore'),
        version_data.get('data_fine_vigore'),
        version_data.get('riferimento_modifica'),
        version_data.get('is_current', False),
        version_data.get('status', 'vigente')
    ))
    
    return cursor.lastrowid

def update_article_current_version(cursor, articolo_id: int, current_version_id: int):
    """
    Update the main article record to point to the current version
    
    Args:
        cursor: SQLite cursor
        articolo_id: ID of the main article
        current_version_id: ID of the current version
    """
    
    # First, set all versions of this article to not current
    cursor.execute("""
        UPDATE articoli_versioni 
        SET is_current = FALSE 
        WHERE articolo_id = ?
    """, (articolo_id,))
    
    # Set the specified version as current
    cursor.execute("""
        UPDATE articoli_versioni 
        SET is_current = TRUE 
        WHERE id = ?
    """, (current_version_id,))
    
    # Update the main article record
    cursor.execute("""
        UPDATE articoli 
        SET versione_corrente_id = ?,
            data_ultima_modifica_versione = CURRENT_TIMESTAMP,
            numero_versioni = (
                SELECT COUNT(*) FROM articoli_versioni 
                WHERE articolo_id = ?
            )
        WHERE id = ?
    """, (current_version_id, articolo_id, articolo_id))

def process_article_with_all_versions(article_element, documento_id: int, numero_articolo: str) -> Dict:
    """
    Process an article element that may contain multiple versions (orig + aggiornamenti)
    
    Args:
        article_element: lxml element containing the article
        documento_id: ID of the parent document
        numero_articolo: Article number (e.g., "4")
        
    Returns:
        Dict containing article data and all versions
    """
    
    result = {
        'documento_id': documento_id,
        'numero_articolo': numero_articolo,
        'titoloAtto': None,
        'rubrica': None,
        'versions': []
    }
    
    # Extract article title/rubrica if present
    title_element = article_element.xpath('.//h2 | .//h3 | .//*[contains(@class, "titoloAtto")]')
    if title_element:
        result['titoloAtto'] = title_element[0].text_content().strip()
    
    # Look for different version containers
    version_containers = article_element.xpath('.//*[contains(text(), "orig.") or contains(text(), "agg.")]')
    
    if not version_containers:
        # If no explicit version containers, treat the whole element as original
        version_data = {
            'tipo_versione': 'orig',
            'testo_versione': article_element.text_content().strip(),
            'data_inizio_vigore': None,
            'data_fine_vigore': None,
            'riferimento_modifica': None,
            'is_current': True,
            'status': 'vigente'
        }
        result['versions'].append(version_data)
    else:
        # Process each version
        for container in version_containers:
            # Find the version type
            version_type = extract_article_version_type(container)
            
            # Extract the text content for this version
            version_text = ""
            next_sibling = container.getnext()
            if next_sibling is not None:
                version_text = next_sibling.text_content().strip()
            else:
                # Try to get content from parent or nearby elements
                parent = container.getparent()
                if parent is not None:
                    version_text = parent.text_content().strip()
            
            # Extract validity dates
            date_text = container.text_content() + (next_sibling.text_content() if next_sibling is not None else "")
            start_date, end_date = parse_validity_dates(date_text)
            
            # Extract modification reference
            ref = extract_modification_reference(container)
            
            # Determine if this is the current version (usually the last agg. or orig if no agg.)
            is_current = version_type == 'orig' and len(version_containers) == 1
            if version_type.startswith('agg.'):
                # Find the highest agg number to determine current
                all_agg_numbers = []
                for vc in version_containers:
                    vt = extract_article_version_type(vc)
                    if vt.startswith('agg.'):
                        try:
                            num = int(vt.split('.')[1])
                            all_agg_numbers.append(num)
                        except:
                            pass
                
                if all_agg_numbers:
                    current_agg_num = max(all_agg_numbers)
                    try:
                        this_agg_num = int(version_type.split('.')[1])
                        is_current = this_agg_num == current_agg_num
                    except:
                        is_current = False
            
            version_data = {
                'tipo_versione': version_type,
                'testo_versione': version_text,
                'data_inizio_vigore': start_date,
                'data_fine_vigore': end_date,
                'riferimento_modifica': ref,
                'is_current': is_current,
                'status': 'vigente' if end_date is None else 'sostituito'
            }
            
            result['versions'].append(version_data)
    
    return result

def save_complete_article_with_versions(cursor, article_data: Dict) -> int:
    """
    Save a complete article with all its versions to the database
    
    Args:
        cursor: SQLite cursor
        article_data: Dictionary containing article and versions data
        
    Returns:
        int: ID of the created article record
    """
    
    # First create the main article record
    article_sql = """
        INSERT INTO articoli (
            documento_id, numero_articolo, titoloAtto, rubrica,
            testo_completo, status, numero_versioni, 
            data_prima_versione, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """
    
    # Use the current version's text as testo_completo
    current_version = next((v for v in article_data['versions'] if v.get('is_current')), article_data['versions'][0])
    testo_completo = current_version['testo_versione']
    
    # Get the earliest date as first version date
    dates = [v['data_inizio_vigore'] for v in article_data['versions'] if v['data_inizio_vigore']]
    data_prima_versione = min(dates) if dates else None
    
    cursor.execute(article_sql, (
        article_data['documento_id'],
        article_data['numero_articolo'],
        article_data.get('titoloAtto'),
        article_data.get('rubrica'),
        testo_completo,
        'vigente',
        len(article_data['versions']),
        data_prima_versione
    ))
    
    articolo_id = cursor.lastrowid
    
    # Now save all versions
    current_version_id = None
    for version_data in article_data['versions']:
        version_id = save_article_version(cursor, articolo_id, version_data)
        if version_data.get('is_current'):
            current_version_id = version_id
    
    # Update the article to point to current version
    if current_version_id:
        cursor.execute("""
            UPDATE articoli 
            SET versione_corrente_id = ? 
            WHERE id = ?
        """, (current_version_id, articolo_id))
    
    return articolo_id

def get_article_version_history(cursor, articolo_id: int) -> List[Dict]:
    """
    Get the complete version history of an article
    
    Args:
        cursor: SQLite cursor
        articolo_id: ID of the article
        
    Returns:
        List of version dictionaries ordered by date
    """
    
    sql = """
        SELECT 
            av.id, av.tipo_versione, av.numero_aggiornamento,
            av.testo_versione, av.data_inizio_vigore, av.data_fine_vigore,
            av.riferimento_modifica, av.is_current, av.status,
            av.created_at
        FROM articoli_versioni av
        WHERE av.articolo_id = ?
        ORDER BY 
            CASE WHEN av.tipo_versione = 'orig' THEN 0 ELSE av.numero_aggiornamento END,
            av.data_inizio_vigore
    """
    
    cursor.execute(sql, (articolo_id,))
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

def apply_enhanced_versioning_schema(database_path: str = 'data.sqlite'):
    """
    Apply the enhanced versioning schema to an existing database
    
    Args:
        database_path: Path to the SQLite database
    """
    
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    try:
        # Read and execute the enhanced schema
        with open('enhanced_schema_versioning.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute each statement separately
        statements = schema_sql.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                except sqlite3.Error as e:
                    print(f"Warning: Could not execute statement (may already exist): {e}")
                    print(f"Statement: {statement[:100]}...")
        
        conn.commit()
        print("✅ Enhanced versioning schema applied successfully")
        
    except Exception as e:
        print(f"❌ Error applying enhanced schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    # Test the enhanced versioning functionality
    apply_enhanced_versioning_schema()
