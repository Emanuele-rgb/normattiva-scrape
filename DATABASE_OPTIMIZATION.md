# Database Optimization per NORME-NET

## Panoramica

Questa ottimizzazione trasforma il database da una struttura semplice nodi-archi a una struttura relazionale avanzata ottimizzata per sistemi RAG (Retrieval-Augmented Generation) e analisi legali.

## Struttura Precedente vs Nuova

### Struttura Precedente

```sql
-- Tabelle semplici
Nodes (Type, Name, Year, Content, URN)
Edges (From Type, From Name, Edge, To Type, To Name)
```

### Nuova Struttura Ottimizzata

#### Tabelle Principali

1. **`documenti_normativi`** - Documenti legali completi
2. **`articoli`** - Singoli articoli (unità atomiche per RAG)
3. **`commi`** - Sotto-unità degli articoli
4. **`citazioni_normative`** - Riferimenti tra documenti
5. **`categorie_legali`** - Tassonomia legale gerarchica
6. **`modifiche_normative`** - Tracking delle modifiche

## Vantaggi della Nuova Struttura

### 1. Ottimizzazione per RAG

- **Granularità**: Articoli e commi come unità atomiche
- **Embedding**: Supporto per vector embeddings a livello di documento, articolo e comma
- **Similarity Search**: Ricerca semantica ottimizzata

### 2. Metadati Ricchi

- **Categorizzazione**: Materie legali gerarchiche
- **Status**: Vigente/abrogato/modificato
- **Gerarchia**: Livelli normativi (Costituzione → Leggi → Decreti)
- **Temporalità**: Date di pubblicazione, entrata in vigore, abrogazione

### 3. Relazioni Complesse

- **Citazioni tipizzate**: rinvio, deroga, integrazione, abrogazione
- **Modifiche tracciate**: Storia delle modifiche normative
- **Correlazioni**: Articoli correlati per tema

### 4. Performance

- **Indici ottimizzati**: Per ricerche frequenti
- **Normalizzazione**: Eliminazione ridondanze
- **Partizionamento logico**: Per tipi di documento e materie

## File di Migrazione

### `database_schema.sql`

Schema completo del nuovo database con:

- Definizioni tabelle
- Indici per performance
- Popolamento iniziale categorie legali

### `migrate_db_to_new_schema.py`

Script di migrazione che:

- Backup dati esistenti
- Creazione nuova struttura
- Mappatura Nodes → documenti_normativi
- Mappatura Edges → citazioni_normative
- Parsing intelligente di metadati

### `scraper.py` (modificato)

Scraper aggiornato con:

- Funzioni di utilità per nuovo DB
- Estrazione metadati avanzata
- Salvataggio strutturato
- Gestione citazioni e riferimenti

## Utilizzo

### 1. Migrazione Database Esistente

```bash
python migrate_db_to_new_schema.py
```

### 2. Test della Nuova Struttura

```bash
python test_optimization.py
```

### 3. Scraping con Nuova Struttura

```bash
python scraper.py
```

## Esempi di Query Avanzate

### Ricerca per Materia

```sql
SELECT d.titolo, d.anno, d.tipo_atto
FROM documenti_normativi d
WHERE d.materia_principale = 'Diritto Civile'
ORDER BY d.anno DESC;
```

### Analisi Citazioni

```sql
SELECT
    d1.titolo as documento_citante,
    d2.titolo as documento_citato,
    c.tipo_citazione,
    COUNT(*) as num_citazioni
FROM citazioni_normative c
JOIN articoli a1 ON c.articolo_citante_id = a1.id
JOIN articoli a2 ON c.articolo_citato_id = a2.id
JOIN documenti_normativi d1 ON a1.documento_id = d1.id
JOIN documenti_normativi d2 ON a2.documento_id = d2.id
GROUP BY d1.id, d2.id, c.tipo_citazione
ORDER BY num_citazioni DESC;
```

### Documenti per Gerarchia

```sql
SELECT
    tipo_atto,
    livello_gerarchia,
    COUNT(*) as count,
    AVG(LENGTH(testo_completo)) as avg_length
FROM documenti_normativi
GROUP BY tipo_atto, livello_gerarchia
ORDER BY livello_gerarchia, count DESC;
```

### Tassonomia Completa

```sql
WITH RECURSIVE categoria_tree AS (
    SELECT id, nome, categoria_padre_id, path_completo, 0 as level
    FROM categorie_legali
    WHERE categoria_padre_id IS NULL

    UNION ALL

    SELECT c.id, c.nome, c.categoria_padre_id, c.path_completo, ct.level + 1
    FROM categorie_legali c
    JOIN categoria_tree ct ON c.categoria_padre_id = ct.id
)
SELECT * FROM categoria_tree ORDER BY level, nome;
```

## Preparazione per RAG

### Embedding Integration

La struttura supporta embedding a più livelli:

- **Documento**: Overview generale
- **Articolo**: Unità semantica principale
- **Comma**: Granularità massima

### Chunking Strategy

```python
# Esempio di strategia di chunking
def get_chunks_for_rag():
    return {
        'document_level': "SELECT titolo, testo_completo FROM documenti_normativi",
        'article_level': "SELECT numero_articolo, testo_completo FROM articoli",
        'comma_level': "SELECT numero_comma, testo FROM commi"
    }
```

### Metadata Enrichment

Ogni chunk include metadati ricchi:

- Tipo documento e gerarchia
- Materia legale
- Anno e status
- Contesto relazionale

## Monitoraggio e Statistiche

### Dashboard Query

```sql
-- Statistiche generali
SELECT
    'Documenti' as tipo, COUNT(*) as count FROM documenti_normativi
UNION ALL
SELECT
    'Articoli' as tipo, COUNT(*) as count FROM articoli
UNION ALL
SELECT
    'Citazioni' as tipo, COUNT(*) as count FROM citazioni_normative;

-- Distribuzione per anno
SELECT anno, COUNT(*) as count
FROM documenti_normativi
GROUP BY anno
ORDER BY anno DESC;

-- Top materie
SELECT materia_principale, COUNT(*) as count
FROM documenti_normativi
GROUP BY materia_principale
ORDER BY count DESC;
```

## Prossimi Sviluppi

1. **Vector Database Integration**: Collegamento a Pinecone/Weaviate
2. **Full-Text Search**: Integrazione con Elasticsearch
3. **API Layer**: REST API per accesso ai dati
4. **ML Pipeline**: Pipeline automatica per categorizzazione
5. **Graph Analytics**: Analisi delle reti di citazioni

## Backup e Recovery

### Backup Automatico

```bash
# Backup completo
sqlite3 data.sqlite ".backup backup_$(date +%Y%m%d).sqlite"

# Export specifico
sqlite3 data.sqlite ".output documenti_backup.sql" ".dump documenti_normativi"
```

### Recovery

```bash
# Restore da backup
sqlite3 data_restored.sqlite ".restore backup_20231201.sqlite"
```

## Note Tecniche

- **SQLite Compatibility**: Adattato per SQLite (no arrays nativi, JSON come TEXT)
- **Performance**: Indici ottimizzati per query comuni
- **Scalability**: Struttura preparata per migrazione a PostgreSQL
- **Encoding**: UTF-8 per caratteri speciali italiani
- **ACID**: Transazioni atomiche per consistenza dati

## Troubleshooting

### Problemi Comuni

1. **Memory Issues**: Per dataset grandi, considerare batch processing
2. **Encoding Errors**: Verificare UTF-8 encoding dei file
3. **Foreign Key Violations**: Controllare integrità referenziale
4. **Performance**: Monitorare utilizzo indici con EXPLAIN QUERY PLAN

### Debug Queries

```sql
-- Verifica integrità
PRAGMA foreign_key_check;

-- Statistiche tabelle
.tables
.schema documenti_normativi

-- Performance analysis
EXPLAIN QUERY PLAN
SELECT * FROM documenti_normativi
WHERE materia_principale = 'Diritto Civile';
```
