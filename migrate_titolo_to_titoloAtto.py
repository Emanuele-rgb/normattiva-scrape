#!/usr/bin/env python3
"""
Database migration script to rename 'titolo' column to 'titoloAtto' in the normattiva-scrape database.
This ensures compatibility with the new schema that uses 'titoloAtto' as the field name.
"""

import sqlite3
import os

def migrate_database():
    """Migrate the database from 'titolo' to 'titoloAtto'"""
    
    db_path = 'data.sqlite'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. Creating new database with current schema.")
        return
        
    print("Starting database migration: titolo -> titoloAtto")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(documenti_normativi)")
        columns = cursor.fetchall()
        
        has_titolo = False
        has_titoloAtto = False
        
        for column in columns:
            if column[1] == 'titolo':
                has_titolo = True
            elif column[1] == 'titoloAtto':
                has_titoloAtto = True
        
        if has_titoloAtto and not has_titolo:
            print("✓ Database already migrated to use 'titoloAtto'")
            return
        
        if has_titolo and not has_titoloAtto:
            print("📋 Migrating documenti_normativi table...")
            
            # For documenti_normativi table
            cursor.execute("""
                ALTER TABLE documenti_normativi 
                RENAME COLUMN titolo TO titoloAtto
            """)
            
            print("✓ Renamed 'titolo' to 'titoloAtto' in documenti_normativi table")
        
        # Check articoli table
        cursor.execute("PRAGMA table_info(articoli)")
        columns = cursor.fetchall()
        
        has_titolo_articoli = False
        has_titoloAtto_articoli = False
        
        for column in columns:
            if column[1] == 'titolo':
                has_titolo_articoli = True
            elif column[1] == 'titoloAtto':
                has_titoloAtto_articoli = True
        
        if has_titolo_articoli and not has_titoloAtto_articoli:
            print("📋 Migrating articoli table...")
            
            # For articoli table
            cursor.execute("""
                ALTER TABLE articoli 
                RENAME COLUMN titolo TO titoloAtto
            """)
            
            print("✓ Renamed 'titolo' to 'titoloAtto' in articoli table")
        
        conn.commit()
        conn.close()
        
        print("✅ Database migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"❌ Database migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")

def verify_migration():
    """Verify that the migration was successful"""
    db_path = 'data.sqlite'
    
    if not os.path.exists(db_path):
        print("Database does not exist - nothing to verify")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check documenti_normativi table
        cursor.execute("PRAGMA table_info(documenti_normativi)")
        columns = cursor.fetchall()
        
        has_titoloAtto = any(column[1] == 'titoloAtto' for column in columns)
        has_titolo = any(column[1] == 'titolo' for column in columns)
        
        print(f"📋 documenti_normativi table:")
        print(f"  - Has 'titoloAtto': {has_titoloAtto}")
        print(f"  - Has 'titolo': {has_titolo}")
        
        # Check articoli table
        cursor.execute("PRAGMA table_info(articoli)")
        columns = cursor.fetchall()
        
        has_titoloAtto_articoli = any(column[1] == 'titoloAtto' for column in columns)
        has_titolo_articoli = any(column[1] == 'titolo' for column in columns)
        
        print(f"📋 articoli table:")
        print(f"  - Has 'titoloAtto': {has_titoloAtto_articoli}")
        print(f"  - Has 'titolo': {has_titolo_articoli}")
        
        if has_titoloAtto and has_titoloAtto_articoli and not has_titolo and not has_titolo_articoli:
            print("✅ Migration verification successful!")
        else:
            print("⚠️  Migration verification indicates potential issues")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    print("🔄 Database Migration: titolo -> titoloAtto")
    print("=" * 50)
    
    migrate_database()
    verify_migration()
    
    print("\n🎯 Migration process completed!")
    print("The database now uses 'titoloAtto' as the title field name.")
