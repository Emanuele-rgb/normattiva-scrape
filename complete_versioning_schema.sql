-- ========================================
-- COMPLETE SCHEMA FOR NORME-NET WITH VERSIONING
-- ========================================

-- Create all tables from scratch including versioning

-- Documents table
CREATE TABLE IF NOT EXISTS documenti_normativi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titoloAtto TEXT NOT NULL,
    tipo_atto VARCHAR(100),
    numero VARCHAR(50),
    anno INTEGER,
    data_pubblicazione DATE,
    data_entrata_vigore DATE,
    urn TEXT UNIQUE,
    url_normattiva TEXT,
    materia_principale VARCHAR(200),
    status VARCHAR(20) DEFAULT 'vigente',
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Articles table (enhanced with versioning support)
CREATE TABLE IF NOT EXISTS articoli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id INTEGER REFERENCES documenti_normativi(id) ON DELETE CASCADE,
    numero_articolo VARCHAR(20) NOT NULL,
    titoloAtto TEXT,
    rubrica TEXT,
    
    -- Versioning fields
    versione_corrente_id INTEGER, -- Will reference articoli_versioni(id)
    numero_versioni INTEGER DEFAULT 1,
    data_prima_versione DATE,
    data_ultima_modifica_versione DATE,
    
    -- Status and metadata
    status VARCHAR(20) DEFAULT 'vigente',
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Article versions table (stores all versions: orig, agg.1, agg.2, etc.)
CREATE TABLE IF NOT EXISTS articoli_versioni (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articolo_id INTEGER REFERENCES articoli(id) ON DELETE CASCADE,
    
    -- Version identification
    tipo_versione VARCHAR(20) NOT NULL, -- 'orig', 'agg.1', 'agg.2', etc.
    numero_aggiornamento INTEGER, -- NULL for 'orig', 1 for 'agg.1', 2 for 'agg.2', etc.
    
    -- Content
    testo_versione TEXT NOT NULL,
    testo_pulito TEXT, -- Cleaned version without references, notes, etc.
    
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
);

-- Enhanced modifiche_normative table with better version tracking
CREATE TABLE IF NOT EXISTS modifiche_normative (
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

-- Citations table
CREATE TABLE IF NOT EXISTS citazioni_normative (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articolo_citante_id INTEGER REFERENCES articoli(id) ON DELETE CASCADE,
    documento_citato_id INTEGER REFERENCES documenti_normativi(id),
    articolo_citato_id INTEGER REFERENCES articoli(id),
    testo_citazione TEXT,
    tipo_citazione VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_articoli_documento ON articoli(documento_id);
CREATE INDEX IF NOT EXISTS idx_articoli_numero ON articoli(numero_articolo);

CREATE INDEX IF NOT EXISTS idx_versioni_articolo ON articoli_versioni(articolo_id);
CREATE INDEX IF NOT EXISTS idx_versioni_tipo ON articoli_versioni(tipo_versione);
CREATE INDEX IF NOT EXISTS idx_versioni_current ON articoli_versioni(is_current);
CREATE INDEX IF NOT EXISTS idx_versioni_vigore ON articoli_versioni(data_inizio_vigore);
CREATE INDEX IF NOT EXISTS idx_versioni_documento ON articoli_versioni(documento_modificante_id);

CREATE INDEX IF NOT EXISTS idx_citazioni_citante ON citazioni_normative(articolo_citante_id);
CREATE INDEX IF NOT EXISTS idx_citazioni_citato ON citazioni_normative(articolo_citato_id);

CREATE INDEX IF NOT EXISTS idx_modifiche_articolo ON modifiche_normative(articolo_modificato_id);
CREATE INDEX IF NOT EXISTS idx_modifiche_documento ON modifiche_normative(documento_modificante_id);

-- Views for easier querying

-- View for easily getting current version of articles
CREATE VIEW IF NOT EXISTS articoli_correnti AS
SELECT 
    a.id as articolo_id,
    a.numero_articolo,
    a.documento_id,
    a.titoloAtto,
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
WHERE av.is_current = 1 AND a.status = 'vigente';

-- View for getting all versions of an article
CREATE VIEW IF NOT EXISTS articoli_storico AS
SELECT 
    a.id as articolo_id,
    a.numero_articolo,
    a.documento_id,
    a.titoloAtto,
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
