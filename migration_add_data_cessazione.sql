-- ========================================
-- MIGRATION: Add data_cessazione column to articoli table
-- ========================================
-- This migration adds the data_cessazione column to track when articles end their validity
-- Date: 2024-12-19

-- Add the data_cessazione column
ALTER TABLE articoli ADD COLUMN data_cessazione DATE;

-- Add comment to explain the column
-- data_cessazione: Date when the article ceases to be valid (extracted from <span id="artFine" class="rosso">)

-- Create index for performance on date queries
CREATE INDEX IF NOT EXISTS idx_articoli_data_cessazione ON articoli(data_cessazione);

-- Create index for date range queries (activation to cessation)
CREATE INDEX IF NOT EXISTS idx_articoli_date_range ON articoli(data_attivazione, data_cessazione);

-- Update any existing records to have NULL data_cessazione (default behavior)
-- This is the default behavior for ALTER TABLE ADD COLUMN, but we make it explicit
UPDATE articoli SET data_cessazione = NULL WHERE data_cessazione IS NULL;

-- Verification query to check the new column was added
SELECT 
    COUNT(*) as total_articoli,
    COUNT(data_cessazione) as articoli_with_end_date,
    COUNT(data_attivazione) as articoli_with_start_date
FROM articoli;

-- Show schema to verify the column was added
PRAGMA table_info(articoli);
