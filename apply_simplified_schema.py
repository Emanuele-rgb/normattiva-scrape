#!/usr/bin/env python3
"""
Apply simplified versioning schema - removes articoli_versioni table and adds simple columns to articoli
"""

import sqlite3
import os

def apply_simplified_schema():
    """Apply simplified schema by removing versioning table and adding simple columns"""
    try:
        if not os.path.exists('data.sqlite'):
            print("❌ Database file 'data.sqlite' not found")
            return False
        
        conn = sqlite3.connect('data.sqlite')
        cursor = conn.cursor()
        
        print("🔄 Applying simplified versioning schema...")
        
        # Check if versioning table exists and drop it
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articoli_versioni'")
        if cursor.fetchone():
            print("📋 Removing articoli_versioni table...")
            cursor.execute("DROP TABLE IF EXISTS articoli_versioni")
            print("✓ articoli_versioni table removed")
        
        # Drop versioning-related tables
        cursor.execute("DROP TABLE IF EXISTS modifiche_normative")
        cursor.execute("DROP VIEW IF EXISTS articoli_correnti")
        cursor.execute("DROP VIEW IF EXISTS articoli_storico")
        print("✓ Removed versioning tables and views")
        
        # Remove versioning columns from articoli table if they exist
        cursor.execute("PRAGMA table_info(articoli)")
        columns = [column[1] for column in cursor.fetchall()]
        
        versioning_columns_to_remove = [
            'versione_corrente_id', 
            'numero_versioni', 
            'data_prima_versione', 
            'data_ultima_modifica_versione'
        ]
        
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        # First, let's check if any of these columns exist
        columns_to_drop = [col for col in versioning_columns_to_remove if col in columns]
        
        if columns_to_drop:
            print(f"📋 Removing columns: {', '.join(columns_to_drop)}")
            
            # Get current table schema without the versioning columns
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='articoli'")
            original_schema = cursor.fetchone()[0]
            
            # Create a backup of the data
            cursor.execute("ALTER TABLE articoli RENAME TO articoli_backup")
            
            # Recreate table without versioning columns but with new simplified columns
            create_table_sql = """
                CREATE TABLE articoli (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento_id INTEGER REFERENCES documenti_normativi(id) ON DELETE CASCADE,
                    numero_articolo VARCHAR(20) NOT NULL,
                    titoloAtto VARCHAR(500),
                    rubrica TEXT,
                    testo_completo TEXT NOT NULL,
                    testo_pulito TEXT,
                    numero_commi INTEGER DEFAULT 1,
                    ha_lettere BOOLEAN DEFAULT FALSE,
                    ha_numeri BOOLEAN DEFAULT FALSE,
                    tipo_norma VARCHAR(50),
                    soggetti_applicabili TEXT,
                    ambito_applicazione TEXT,
                    articoli_correlati TEXT,
                    allegati TEXT,
                    url_documento TEXT,
                    embedding_articolo TEXT,
                    status VARCHAR(20) DEFAULT 'vigente',
                    data_attivazione DATE,
                    data_cessazione DATE,
                    data_ultima_modifica DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    articolo_base_id INTEGER REFERENCES articoli(id),
                    tipo_versione VARCHAR(20) DEFAULT 'orig',
                    numero_aggiornamento INTEGER
                )
            """
            
            cursor.execute(create_table_sql)
            
            # Copy data back (excluding the versioning columns)
            safe_columns = [col for col in columns if col not in columns_to_drop and col in [
                'id', 'documento_id', 'numero_articolo', 'titoloAtto', 'rubrica',
                'testo_completo', 'testo_pulito', 'numero_commi', 'ha_lettere', 'ha_numeri',
                'tipo_norma', 'soggetti_applicabili', 'ambito_applicazione', 'articoli_correlati',
                'allegati', 'url_documento', 'embedding_articolo', 'status',
                'data_attivazione', 'data_cessazione', 'data_ultima_modifica',
                'created_at', 'updated_at'
            ]]
            
            columns_str = ', '.join(safe_columns)
            cursor.execute(f"""
                INSERT INTO articoli ({columns_str}, articolo_base_id, tipo_versione, numero_aggiornamento)
                SELECT {columns_str}, NULL, 'orig', NULL FROM articoli_backup
            """)
            
            # Drop backup table
            cursor.execute("DROP TABLE articoli_backup")
            print("✓ Table recreated with simplified schema")
        
        else:
            # Just add the new columns if they don't exist
            if 'articolo_base_id' not in columns:
                print("📋 Adding simplified versioning columns...")
                cursor.execute("ALTER TABLE articoli ADD COLUMN articolo_base_id INTEGER REFERENCES articoli(id)")
                cursor.execute("ALTER TABLE articoli ADD COLUMN tipo_versione VARCHAR(20) DEFAULT 'orig'")
                cursor.execute("ALTER TABLE articoli ADD COLUMN numero_aggiornamento INTEGER")
                print("✓ Added new versioning columns")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articoli_base ON articoli(articolo_base_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articoli_versione ON articoli(tipo_versione)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articoli_aggiornamento ON articoli(numero_aggiornamento)")
        
        # Create view for easy querying
        cursor.execute("DROP VIEW IF EXISTS articoli_con_versioni")
        cursor.execute("""
            CREATE VIEW articoli_con_versioni AS
            SELECT 
                a.id,
                a.documento_id,
                a.numero_articolo,
                a.titoloAtto,
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
            LEFT JOIN articoli base ON a.articolo_base_id = base.id
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Simplified versioning schema applied successfully!")
        print()
        print("📊 New schema features:")
        print("  • articolo_base_id: References the base article for updates (NULL for originals)")
        print("  • tipo_versione: 'orig', 'agg.1', 'agg.2', etc.")
        print("  • numero_aggiornamento: 1, 2, 3, etc. for updates (NULL for originals)")
        print("  • View 'articoli_con_versioni' for easy querying")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying simplified schema: {e}")
        return False

if __name__ == "__main__":
    apply_simplified_schema()
