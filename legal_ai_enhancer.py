#!/usr/bin/env python3
"""
Legal AI Enhancement Script
Implements the critical missing features for legal AI system
"""

import sqlite3
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests

# Optional imports for embeddings (fallback if not available)
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    import numpy as np
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not available. Install with: pip install transformers torch numpy")
    print("   Embeddings will be skipped, but other enhancements will run.")

class LegalAIEnhancer:
    def __init__(self, db_path: str = "data.sqlite"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Initialize Italian legal language model
        if TRANSFORMERS_AVAILABLE:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-italian-cased")
                self.model = AutoModel.from_pretrained("dbmdz/bert-base-italian-cased")
                self.embedding_model_available = True
            except Exception as e:
                print(f"⚠️ Embedding model not available: {e}")
                self.embedding_model_available = False
        else:
            self.embedding_model_available = False
    
    def generate_embeddings(self, text: str) -> Optional[List[float]]:
        """Generate embeddings for legal text using Italian BERT"""
        if not self.embedding_model_available:
            return None
        
        try:
            # Truncate text if too long
            max_length = 512
            if len(text) > max_length:
                text = text[:max_length]
            
            # Tokenize and encode
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use CLS token embedding
                embeddings = outputs.last_hidden_state[:, 0, :].squeeze()
                return embeddings.tolist()
        
        except Exception as e:
            print(f"⚠️ Error generating embedding: {e}")
            return None
    
    def classify_article_type(self, text: str) -> Dict[str, Any]:
        """Classify article type based on content analysis"""
        text_lower = text.lower()
        
        # Determine tipo_norma
        if any(keyword in text_lower for keyword in ['è punito', 'sanzione', 'multa', 'arresto', 'reclusione']):
            tipo_norma = 'sanzionatoria'
        elif any(keyword in text_lower for keyword in ['si intende', 'definisce', 'significa', 'comprende']):
            tipo_norma = 'definitoria'
        elif any(keyword in text_lower for keyword in ['procedura', 'processo', 'termine', 'istanza', 'ricorso']):
            tipo_norma = 'procedurale'
        else:
            tipo_norma = 'sostanziale'
        
        # Determine soggetti_applicabili
        soggetti = []
        if any(keyword in text_lower for keyword in ['persona fisica', 'cittadino', 'individuo']):
            soggetti.append('persone_fisiche')
        if any(keyword in text_lower for keyword in ['società', 'impresa', 'azienda', 'ditta']):
            soggetti.append('societa')
        if any(keyword in text_lower for keyword in ['pubblica amministrazione', 'stato', 'ministero', 'comune']):
            soggetti.append('pa')
        if not soggetti:
            soggetti = ['generale']
        
        # Determine ambito_applicazione
        ambito = []
        if any(keyword in text_lower for keyword in ['contratto', 'accordo', 'convenzione']):
            ambito.append('contratti')
        if any(keyword in text_lower for keyword in ['famiglia', 'coniuge', 'matrimonio', 'figli']):
            ambito.append('famiglia')
        if any(keyword in text_lower for keyword in ['responsabilità', 'danno', 'risarcimento']):
            ambito.append('responsabilita')
        if any(keyword in text_lower for keyword in ['proprietà', 'possesso', 'beni']):
            ambito.append('proprieta')
        if any(keyword in text_lower for keyword in ['lavoro', 'dipendente', 'datore']):
            ambito.append('lavoro')
        if not ambito:
            ambito = ['generale']
        
        return {
            'tipo_norma': tipo_norma,
            'soggetti_applicabili': soggetti,
            'ambito_applicazione': ambito
        }
    
    def extract_commi(self, article_text: str) -> List[Dict[str, Any]]:
        """Extract individual commi from article text"""
        commi = []
        
        # Common comma patterns in Italian legal texts
        patterns = [
            r'(?:^|\n)\s*(\d+)\.\s*([^0-9\n]+(?:\n(?!\s*\d+\.)[^\n]*)*)',
            r'(?:^|\n)\s*(\d+)\)\s*([^0-9\n]+(?:\n(?!\s*\d+\))[^\n]*)*)',
            r'(?:^|\n)\s*([a-z])\)\s*([^a-z\n]+(?:\n(?!\s*[a-z]\))[^\n]*)*)',
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, article_text, re.MULTILINE | re.DOTALL)
            if matches:
                for match in matches:
                    numero_comma = match[0]
                    testo_comma = match[1].strip()
                    
                    if len(testo_comma) > 20:  # Minimum length for meaningful content
                        commi.append({
                            'numero_comma': numero_comma,
                            'testo': testo_comma,
                            'ha_sottopunti': bool(re.search(r'[a-z]\)|[0-9]\)', testo_comma))
                        })
                
                break  # Use first matching pattern
        
        # If no structured commi found, treat entire text as single comma
        if not commi:
            commi.append({
                'numero_comma': 1,
                'testo': article_text.strip(),
                'ha_sottopunti': False
            })
        
        return commi
    
    def extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract legal citations from text"""
        citations = []
        
        # Citation patterns
        patterns = [
            r'art(?:icolo)?\s*(\d+)(?:\s*(?:del|della)\s*([^,\n]+))?',
            r'(?:legge|decreto|d\.lgs\.?|d\.p\.r\.?)\s*(\d+)\s*(?:del\s*)?(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
            r'comma\s*(\d+)',
            r'lettera\s*([a-z])',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    citations.append({
                        'tipo_citazione': 'rinvio',
                        'riferimento': ' '.join(str(m) for m in match if m),
                        'contesto': text[max(0, text.find(match[0])-50):text.find(match[0])+100]
                    })
                else:
                    citations.append({
                        'tipo_citazione': 'rinvio',
                        'riferimento': str(match),
                        'contesto': text[max(0, text.find(match)-50):text.find(match)+100]
                    })
        
        return citations
    
    def categorize_document(self, document_text: str, title: str) -> List[int]:
        """Categorize document based on content analysis"""
        text_lower = document_text.lower()
        title_lower = title.lower()
        
        category_keywords = {
            1: ['contratto', 'obbligazione', 'privato', 'civile'],  # Diritto Civile
            2: ['reato', 'penale', 'sanzione', 'punizione'],      # Diritto Penale
            3: ['amministrazione', 'pubblica', 'procedimento'],   # Diritto Amministrativo
            4: ['costituzione', 'costituzionale', 'stato'],       # Diritto Costituzionale
            5: ['tributo', 'imposta', 'fiscale', 'tassa'],        # Diritto Tributario
            6: ['lavoro', 'dipendente', 'datore', 'sindacale'],   # Diritto del Lavoro
            7: ['impresa', 'società', 'commercio', 'commerciale'] # Diritto Commerciale
        }
        
        matched_categories = []
        for category_id, keywords in category_keywords.items():
            if any(keyword in text_lower or keyword in title_lower for keyword in keywords):
                matched_categories.append(category_id)
        
        # Default to Diritto Civile if no matches
        if not matched_categories:
            matched_categories = [1]
        
        return matched_categories
    
    def enhance_database(self):
        """Main method to enhance the database with AI-ready features"""
        print("🚀 Starting Legal AI Enhancement Process...")
        
        # 1. Generate embeddings for all articles
        print("\n1. Generating embeddings for articles...")
        self.cursor.execute("SELECT id, testo_completo FROM articoli WHERE testo_completo IS NOT NULL")
        articles = self.cursor.fetchall()
        
        embeddings_generated = 0
        for article_id, text in articles:
            if self.embedding_model_available:
                embedding = self.generate_embeddings(text)
                if embedding:
                    embedding_json = json.dumps(embedding)
                    self.cursor.execute(
                        "UPDATE articoli SET embedding_articolo = ? WHERE id = ?",
                        (embedding_json, article_id)
                    )
                    embeddings_generated += 1
            
            # Add semantic classification
            classification = self.classify_article_type(text)
            self.cursor.execute("""
                UPDATE articoli SET 
                    tipo_norma = ?,
                    soggetti_applicabili = ?,
                    ambito_applicazione = ?
                WHERE id = ?
            """, (
                classification['tipo_norma'],
                json.dumps(classification['soggetti_applicabili']),
                json.dumps(classification['ambito_applicazione']),
                article_id
            ))
        
        print(f"   Generated {embeddings_generated} embeddings")
        print(f"   Classified {len(articles)} articles")
        
        # 2. Extract and populate commi
        print("\n2. Extracting individual commi...")
        commi_extracted = 0
        for article_id, text in articles:
            commi = self.extract_commi(text)
            for comma in commi:
                embedding = None
                if self.embedding_model_available:
                    embedding = self.generate_embeddings(comma['testo'])
                
                self.cursor.execute("""
                    INSERT INTO commi (articolo_id, numero_comma, testo, embedding_comma, ha_sottopunti)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    article_id,
                    comma['numero_comma'],
                    comma['testo'],
                    json.dumps(embedding) if embedding else None,
                    comma['ha_sottopunti']
                ))
                commi_extracted += 1
        
        print(f"   Extracted {commi_extracted} commi")
        
        # 3. Categorize documents
        print("\n3. Categorizing documents...")
        self.cursor.execute("SELECT id, testo_completo, titoloAtto FROM documenti_normativi")
        documents = self.cursor.fetchall()
        
        categorized_docs = 0
        for doc_id, text, title in documents:
            categories = self.categorize_document(text, title)
            for category_id in categories:
                # Calculate relevance based on keyword frequency
                relevance = min(1.0, len(categories) / 3.0)  # Simple relevance calculation
                
                self.cursor.execute("""
                    INSERT OR REPLACE INTO documento_categorie (documento_id, categoria_id, rilevanza)
                    VALUES (?, ?, ?)
                """, (doc_id, category_id, relevance))
            categorized_docs += 1
        
        print(f"   Categorized {categorized_docs} documents")
        
        # 4. Extract citations
        print("\n4. Extracting legal citations...")
        citations_extracted = 0
        for article_id, text in articles:
            citations = self.extract_citations(text)
            for citation in citations:
                self.cursor.execute("""
                    INSERT INTO citazioni_normative (articolo_citante_id, tipo_citazione, contesto_citazione)
                    VALUES (?, ?, ?)
                """, (article_id, citation['tipo_citazione'], citation['contesto']))
                citations_extracted += 1
        
        print(f"   Extracted {citations_extracted} citations")
        
        # 5. Generate document embeddings
        print("\n5. Generating document embeddings...")
        doc_embeddings_generated = 0
        for doc_id, text, title in documents:
            if self.embedding_model_available and text:
                # Use title + first 1000 chars for document embedding
                doc_text = f"{title}\n{text[:1000]}"
                embedding = self.generate_embeddings(doc_text)
                if embedding:
                    embedding_json = json.dumps(embedding)
                    self.cursor.execute(
                        "UPDATE documenti_normativi SET embedding_documento = ? WHERE id = ?",
                        (embedding_json, doc_id)
                    )
                    doc_embeddings_generated += 1
        
        print(f"   Generated {doc_embeddings_generated} document embeddings")
        
        # Commit all changes
        self.conn.commit()
        
        print("\n✅ Legal AI Enhancement Complete!")
        print(f"   - {embeddings_generated} article embeddings")
        print(f"   - {len(articles)} articles classified")
        print(f"   - {commi_extracted} commi extracted")
        print(f"   - {categorized_docs} documents categorized")
        print(f"   - {citations_extracted} citations extracted")
        print(f"   - {doc_embeddings_generated} document embeddings")
        
        return {
            'embeddings_generated': embeddings_generated,
            'articles_classified': len(articles),
            'commi_extracted': commi_extracted,
            'documents_categorized': categorized_docs,
            'citations_extracted': citations_extracted,
            'doc_embeddings_generated': doc_embeddings_generated
        }
    
    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    """Main enhancement script"""
    enhancer = LegalAIEnhancer()
    
    try:
        results = enhancer.enhance_database()
        print("\n📊 Enhancement Results:")
        for key, value in results.items():
            print(f"   {key}: {value}")
    
    except Exception as e:
        print(f"❌ Error during enhancement: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        enhancer.close()

if __name__ == "__main__":
    main()
