-- Migration script to add support for article activation dates and allegati
-- Run this to add the new columns to existing databases

-- Add data_attivazione column to articoli table
ALTER TABLE articoli ADD COLUMN data_attivazione DATE;

-- Add allegati column to articoli table to store JSON array of allegati
ALTER TABLE articoli ADD COLUMN allegati TEXT;

-- Add index for data_attivazione for better query performance
CREATE INDEX IF NOT EXISTS idx_articoli_data_attivazione ON articoli(data_attivazione);

-- Add index for numero_articolo to support bis, ter, etc. queries
CREATE INDEX IF NOT EXISTS idx_articoli_numero_articolo ON articoli(numero_articolo);

-- Update the enhanced versioning schema to support allegati
ALTER TABLE articoli_versioni ADD COLUMN allegati TEXT;

-- Add a view for getting active articles with activation dates
CREATE VIEW IF NOT EXISTS articoli_attivi AS
SELECT 
    a.id,
    a.documento_id,
    a.numero_articolo,
    a.titoloAtto,
    a.testo_completo,
    a.testo_pulito,
    a.data_attivazione,
    a.allegati,
    a.status,
    a.created_at,
    a.updated_at,
    d.titoloAtto as documento_titolo,
    d.tipo_atto,
    d.numero as documento_numero,
    d.anno as documento_anno
FROM articoli a
JOIN documenti_normativi d ON a.documento_id = d.id
WHERE a.status = 'vigente'
ORDER BY a.data_attivazione DESC;

PRAGMA user_version = 3;
