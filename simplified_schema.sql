-- ========================================
-- SIMPLIFIED SCHEMA WITHOUT VERSIONING TABLE
-- ========================================

-- Drop versioning-related tables and views
DROP TABLE IF EXISTS articoli_versioni;
DROP TABLE IF EXISTS modifiche_normative;
DROP VIEW IF EXISTS articoli_correnti;
DROP VIEW IF EXISTS articoli_storico;

-- Remove versioning columns from articoli table
ALTER TABLE articoli DROP COLUMN versione_corrente_id;
ALTER TABLE articoli DROP COLUMN numero_versioni;
ALTER TABLE articoli DROP COLUMN data_prima_versione;
ALTER TABLE articoli DROP COLUMN data_ultima_modifica_versione;

-- Add new column to track which article each update references
ALTER TABLE articoli ADD COLUMN articolo_base_id INTEGER REFERENCES articoli(id);
-- This will be NULL for original articles and contain the ID of the base article for updates

-- Add column to identify version type (orig, agg.1, agg.2, etc.)
ALTER TABLE articoli ADD COLUMN tipo_versione VARCHAR(20) DEFAULT 'orig';

-- Add column to track update number
ALTER TABLE articoli ADD COLUMN numero_aggiornamento INTEGER;

-- Add column to track the source/origin of the article
ALTER TABLE articoli ADD COLUMN fonte_origine VARCHAR(100);
-- This will contain values like 'Articoli', 'Allegati > Agreement', 'Allegati > Protocol', etc.

-- Create index for efficient queries
CREATE INDEX idx_articoli_base ON articoli(articolo_base_id);
CREATE INDEX idx_articoli_versione ON articoli(tipo_versione);
CREATE INDEX idx_articoli_aggiornamento ON articoli(numero_aggiornamento);
CREATE INDEX idx_articoli_fonte ON articoli(fonte_origine);

-- View to easily get all versions of an article
CREATE VIEW articoli_con_versioni AS
SELECT 
    a.id,
    a.documento_id,
    a.numero_articolo,
    a.titoloAtto,
    a.fonte_origine,
    a.testo_completo,
    a.testo_pulito,
    a.tipo_versione,
    a.numero_aggiornamento,
    a.articolo_base_id,
    a.data_attivazione,
    a.data_cessazione,
    a.status,
    CASE 
        WHEN a.articolo_base_id IS NULL THEN a.id 
        ELSE a.articolo_base_id 
    END as gruppo_articolo,
    base.numero_articolo as numero_articolo_base
FROM articoli a
LEFT JOIN articoli base ON a.articolo_base_id = base.id;
