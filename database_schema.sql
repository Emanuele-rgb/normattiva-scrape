-- ========================================
-- SCHEMA DATABASE OTTIMIZZATO PER RAG
-- ========================================

-- Documenti normativi (leggi, decreti, regolamenti)
CREATE TABLE documenti_normativi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Identificatori ufficiali
    numero VARCHAR(50) NOT NULL,
    anno INTEGER NOT NULL,
    tipo_atto VARCHAR(100) NOT NULL, -- 'Legge', 'Decreto Legislativo', 'DPR', etc.
    
    -- Metadata essenziali
    titoloAtto TEXT NOT NULL,
    data_pubblicazione DATE NOT NULL,
    data_entrata_vigore DATE,
    data_abrogazione DATE, -- NULL se vigente
    
    -- Categorizzazione
    materia_principale VARCHAR(100), -- 'Civile', 'Penale', 'Amministrativo', etc.
    materie_secondarie TEXT, -- JSON array per materie multiple
    organo_emanante VARCHAR(200),
    
    -- Status e gerarchia
    status VARCHAR(20) DEFAULT 'vigente', -- 'vigente', 'abrogato', 'modificato'
    livello_gerarchia INTEGER, -- 1=Costituzione, 2=Leggi, 3=Decreti, etc.
    
    -- URL e riferimenti
    url_normattiva TEXT,
    url_gazzetta_ufficiale TEXT,
    urn TEXT UNIQUE,
    
    -- Testo completo per backup
    testo_completo TEXT,
    
    -- Metadata per RAG (stored as JSON for SQLite compatibility)
    embedding_documento TEXT, -- JSON serialized embedding
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indici
    UNIQUE(numero, anno, tipo_atto)
);

-- Articoli individuali (unità atomiche per RAG)
CREATE TABLE articoli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id INTEGER REFERENCES documenti_normativi(id) ON DELETE CASCADE,
    
    -- Struttura gerarchica
    numero_articolo VARCHAR(20) NOT NULL, -- '1', '1-bis', '1-ter'
    titoloAtto VARCHAR(500),
    rubrica TEXT, -- Intestazione dell'articolo
    
    -- Contenuto
    testo_completo TEXT NOT NULL,
    testo_pulito TEXT, -- Senza riferimenti, note, etc.
    
    -- Struttura interna
    numero_commi INTEGER DEFAULT 1,
    ha_lettere BOOLEAN DEFAULT FALSE,
    ha_numeri BOOLEAN DEFAULT FALSE,
    
    -- Categorizzazione semantica
    tipo_norma VARCHAR(50), -- 'sostanziale', 'procedurale', 'definitoria', 'sanzionatoria'
    soggetti_applicabili TEXT, -- JSON array: ['persone_fisiche', 'societa', 'pa']
    ambito_applicazione TEXT, -- JSON array: ['contratti', 'responsabilita', 'famiglia']
    
    -- Relazioni
    articoli_correlati TEXT, -- JSON array di ID articoli correlati
    
    -- Allegati
    allegati TEXT, -- JSON array di allegati associati all'articolo
    
    -- URL di riferimento per debugging
    url_documento TEXT, -- URL del documento originale per debug/reference
    
    -- Embedding per similarity search
    embedding_articolo TEXT, -- JSON serialized embedding
    
    -- Status e date
    status VARCHAR(20) DEFAULT 'vigente',
    data_attivazione DATE, -- Data di attivazione dell'articolo
    data_cessazione DATE, -- Data di cessazione dell'articolo (se non più vigente)
    data_ultima_modifica DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Commi (sotto-unità degli articoli)
CREATE TABLE commi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articolo_id INTEGER REFERENCES articoli(id) ON DELETE CASCADE,
    
    numero_comma INTEGER NOT NULL,
    testo TEXT NOT NULL,
    
    -- Embedding per ricerche granulari
    embedding_comma TEXT, -- JSON serialized embedding
    
    -- Lettere e numeri del comma
    ha_sottopunti BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TABELLE DI SUPPORTO
-- ========================================

-- Modifiche e aggiornamenti
CREATE TABLE modifiche_normative (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Documento modificato
    documento_modificato_id INTEGER REFERENCES documenti_normativi(id),
    articolo_modificato_id INTEGER REFERENCES articoli(id),
    
    -- Documento modificante
    documento_modificante_id INTEGER REFERENCES documenti_normativi(id),
    
    tipo_modifica VARCHAR(50), -- 'sostituzione', 'aggiunta', 'abrogazione', 'modifica'
    descrizione_modifica TEXT,
    
    data_modifica DATE NOT NULL,
    testo_precedente TEXT,
    testo_nuovo TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tassonomia legale
CREATE TABLE categorie_legali (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) UNIQUE NOT NULL,
    descrizione TEXT,
    categoria_padre_id INTEGER REFERENCES categorie_legali(id),
    livello INTEGER DEFAULT 1,
    
    -- Per albero delle categorie: Diritto Civile > Contratti > Vendita
    path_completo TEXT -- 'diritto_civile.contratti.vendita'
);

-- Relazione documenti-categorie (many-to-many)
CREATE TABLE documento_categorie (
    documento_id INTEGER REFERENCES documenti_normativi(id),
    categoria_id INTEGER REFERENCES categorie_legali(id),
    rilevanza DECIMAL(3,2) DEFAULT 1.0, -- Peso della categorizzazione
    
    PRIMARY KEY (documento_id, categoria_id)
);

-- Citazioni e riferimenti normativi
CREATE TABLE citazioni_normative (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Articolo che cita
    articolo_citante_id INTEGER REFERENCES articoli(id),
    
    -- Articolo citato
    articolo_citato_id INTEGER REFERENCES articoli(id),
    
    tipo_citazione VARCHAR(50), -- 'rinvio', 'deroga', 'integrazione', 'abrogazione'
    contesto_citazione TEXT, -- Frase in cui appare la citazione
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- INDICI PER PERFORMANCE
-- ========================================

CREATE INDEX idx_documenti_anno ON documenti_normativi(anno);
CREATE INDEX idx_documenti_tipo ON documenti_normativi(tipo_atto);
CREATE INDEX idx_documenti_status ON documenti_normativi(status);
CREATE INDEX idx_documenti_materia ON documenti_normativi(materia_principale);
CREATE INDEX idx_documenti_urn ON documenti_normativi(urn);

CREATE INDEX idx_articoli_documento ON articoli(documento_id);
CREATE INDEX idx_articoli_numero ON articoli(numero_articolo);
CREATE INDEX idx_articoli_status ON articoli(status);

CREATE INDEX idx_commi_articolo ON commi(articolo_id);

CREATE INDEX idx_citazioni_citante ON citazioni_normative(articolo_citante_id);
CREATE INDEX idx_citazioni_citato ON citazioni_normative(articolo_citato_id);

-- ========================================
-- POPOLAMENTO INIZIALE CATEGORIE
-- ========================================

INSERT INTO categorie_legali (nome, descrizione, livello, path_completo) VALUES 
('Diritto Civile', 'Norme che regolano i rapporti tra privati', 1, 'diritto_civile'),
('Diritto Penale', 'Norme che definiscono reati e sanzioni', 1, 'diritto_penale'),
('Diritto Amministrativo', 'Norme sulla Pubblica Amministrazione', 1, 'diritto_amministrativo'),
('Diritto Costituzionale', 'Norme fondamentali dello Stato', 1, 'diritto_costituzionale'),
('Diritto Tributario', 'Norme fiscali e tributarie', 1, 'diritto_tributario'),
('Diritto del Lavoro', 'Norme sui rapporti di lavoro', 1, 'diritto_lavoro'),
('Diritto Commerciale', 'Norme su imprese e società', 1, 'diritto_commerciale');

-- Sottocategorie Diritto Civile
INSERT INTO categorie_legali (nome, descrizione, categoria_padre_id, livello, path_completo) VALUES 
('Contratti', 'Norme sui contratti', (SELECT id FROM categorie_legali WHERE nome = 'Diritto Civile'), 2, 'diritto_civile.contratti'),
('Famiglia', 'Diritto di famiglia', (SELECT id FROM categorie_legali WHERE nome = 'Diritto Civile'), 2, 'diritto_civile.famiglia'),
('Successioni', 'Diritto successorio', (SELECT id FROM categorie_legali WHERE nome = 'Diritto Civile'), 2, 'diritto_civile.successioni'),
('Responsabilità', 'Responsabilità civile', (SELECT id FROM categorie_legali WHERE nome = 'Diritto Civile'), 2, 'diritto_civile.responsabilita');
