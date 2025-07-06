-- ========================================
-- ENHANCED SCHEMA FOR ARTICLE VERSIONING
-- ========================================

-- New table for article versions (original + aggiornamenti)
CREATE TABLE articoli_versioni (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articolo_id INTEGER REFERENCES articoli(id) ON DELETE CASCADE,
    
    -- Version identification
    tipo_versione VARCHAR(20) NOT NULL, -- 'orig', 'agg.1', 'agg.2', etc.
    numero_aggiornamento INTEGER, -- NULL for 'orig', 1 for 'agg.1', 2 for 'agg.2', etc.
    
    -- Content
    testo_versione TEXT NOT NULL,
    testo_pulito TEXT, -- Cleaned version without references, notes, etc.
    
    -- Allegati for this version
    allegati TEXT, -- JSON array of allegati for this version
    
    -- Validity dates
    data_inizio_vigore DATE NOT NULL, -- When this version became effective
    data_fine_vigore DATE, -- When this version was superseded (NULL if current)
    
    -- Source information
    documento_modificante_id INTEGER REFERENCES documenti_normativi(id), -- Document that introduced this version
    riferimento_modifica TEXT, -- e.g., "D.L. 17 marzo 2020, n. 18"
    
    -- Status
    is_current BOOLEAN DEFAULT FALSE, -- TRUE only for the currently active version
    status VARCHAR(20) DEFAULT 'vigente', -- 'vigente', 'abrogato', 'sostituito'
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
    -- Note: Only one current version per article should exist
    -- This is enforced by application logic rather than database constraint
);

-- Enhanced modifiche_normative table with better version tracking
DROP TABLE IF EXISTS modifiche_normative;
CREATE TABLE modifiche_normative (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Version tracking
    versione_precedente_id INTEGER REFERENCES articoli_versioni(id),
    versione_nuova_id INTEGER REFERENCES articoli_versioni(id),
    
    -- Documento modificato
    documento_modificato_id INTEGER REFERENCES documenti_normativi(id),
    articolo_modificato_id INTEGER REFERENCES articoli(id),
    
    -- Documento modificante
    documento_modificante_id INTEGER REFERENCES documenti_normativi(id),
    
    tipo_modifica VARCHAR(50), -- 'sostituzione', 'aggiunta', 'abrogazione', 'modifica'
    descrizione_modifica TEXT,
    
    data_modifica DATE NOT NULL,
    data_entrata_vigore DATE NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add new columns to existing articoli table for better version management
ALTER TABLE articoli ADD COLUMN versione_corrente_id INTEGER REFERENCES articoli_versioni(id);
ALTER TABLE articoli ADD COLUMN numero_versioni INTEGER DEFAULT 1;
ALTER TABLE articoli ADD COLUMN data_prima_versione DATE;
ALTER TABLE articoli ADD COLUMN data_ultima_modifica_versione DATE;
ALTER TABLE articoli ADD COLUMN data_cessazione DATE; -- Data di cessazione dell'articolo

-- Indexes for performance
CREATE INDEX idx_versioni_articolo ON articoli_versioni(articolo_id);
CREATE INDEX idx_versioni_tipo ON articoli_versioni(tipo_versione);
CREATE INDEX idx_versioni_current ON articoli_versioni(is_current);
CREATE INDEX idx_versioni_vigore ON articoli_versioni(data_inizio_vigore);
CREATE INDEX idx_versioni_documento ON articoli_versioni(documento_modificante_id);

-- View for easily getting current version of articles
CREATE VIEW articoli_correnti AS
SELECT 
    a.id as articolo_id,
    a.numero_articolo,
    a.documento_id,
    a.titolo,
    a.rubrica,
    av.id as versione_id,
    av.tipo_versione,
    av.numero_aggiornamento,
    av.testo_versione as testo_completo,
    av.testo_pulito,
    av.data_inizio_vigore,
    av.data_fine_vigore,
    av.riferimento_modifica,
    a.status,
    a.created_at,
    a.updated_at
FROM articoli a
JOIN articoli_versioni av ON a.versione_corrente_id = av.id
WHERE av.is_current = TRUE AND a.status = 'vigente';

-- View for getting all versions of an article
CREATE VIEW articoli_storico AS
SELECT 
    a.id as articolo_id,
    a.numero_articolo,
    a.documento_id,
    a.titolo,
    a.rubrica,
    av.id as versione_id,
    av.tipo_versione,
    av.numero_aggiornamento,
    av.testo_versione as testo_completo,
    av.testo_pulito,
    av.data_inizio_vigore,
    av.data_fine_vigore,
    av.riferimento_modifica,
    av.is_current,
    av.status as status_versione,
    a.status as status_articolo,
    av.created_at as versione_created_at,
    a.created_at as articolo_created_at
FROM articoli a
JOIN articoli_versioni av ON a.id = av.articolo_id
ORDER BY a.id, av.data_inizio_vigore;
