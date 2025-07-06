#!/usr/bin/env python3
"""
Script per pulire/resettare il database di NORMATTIVA-SCRAPE
"""

import sqlite3
import os
import sys
from datetime import datetime

def clear_database(confirm=True):
    """
    Pulisce completamente il database rimuovendo tutti i dati dalle tabelle
    """
    database_path = 'data.sqlite'
    
    if not os.path.exists(database_path):
        print(f"❌ Database non trovato: {database_path}")
        return False
    
    if confirm:
        print("⚠️  ATTENZIONE: Questa operazione cancellerà TUTTI i dati dal database!")
        print(f"Database: {database_path}")
        
        response = input("Sei sicuro di voler continuare? (digita 'CONFERMA' per procedere): ")
        if response != 'CONFERMA':
            print("❌ Operazione annullata dall'utente")
            return False
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Ottieni statistiche prima della pulizia
        print("\n📊 STATISTICHE PRIMA DELLA PULIZIA:")
        
        tables_to_check = [
            ('documenti_normativi', 'Documenti normativi'),
            ('articoli', 'Articoli'),
            ('articoli_versioni', 'Versioni articoli'),
            ('modifiche_normative', 'Modifiche normative'),
            ('citazioni_normative', 'Citazioni normative')
        ]
        
        total_records = 0
        for table_name, display_name in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  {display_name}: {count:,} record")
                total_records += count
            except sqlite3.OperationalError:
                print(f"  {display_name}: Tabella non esistente")
        
        print(f"  TOTALE: {total_records:,} record")
        
        if total_records == 0:
            print("✅ Il database è già vuoto")
            conn.close()
            return True
        
        # Disabilita foreign key constraints temporaneamente
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Pulisci le tabelle nell'ordine corretto (rispettando le foreign key)
        tables_to_clear = [
            'citazioni_normative',  # Dipende da articoli
            'modifiche_normative',  # Dipende da articoli_versioni
            'articoli_versioni',    # Dipende da articoli
            'articoli',             # Dipende da documenti_normativi  
            'documenti_normativi'   # Tabella principale
        ]
        
        print("\n🧹 PULIZIA IN CORSO:")
        
        for table_name in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table_name}")
                deleted_count = cursor.rowcount
                print(f"  ✅ {table_name}: {deleted_count:,} record eliminati")
            except sqlite3.OperationalError as e:
                print(f"  ⚠️ {table_name}: Errore durante la pulizia - {e}")
        
        # Reset degli auto-increment counters
        print("\n🔄 RESET CONTATORI AUTO-INCREMENT:")
        for table_name in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
                print(f"  ✅ {table_name}: Contatore resettato")
            except sqlite3.OperationalError:
                print(f"  ⚠️ {table_name}: Nessun contatore da resettare")
        
        # Riabilita foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Commit delle modifiche
        conn.commit()
        
        # Verifica finale
        print("\n📊 VERIFICA FINALE:")
        final_total = 0
        for table_name, display_name in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  {display_name}: {count:,} record")
                final_total += count
            except sqlite3.OperationalError:
                print(f"  {display_name}: Tabella non esistente")
        
        print(f"  TOTALE: {final_total:,} record")
        
        conn.close()
        
        if final_total == 0:
            print("✅ Database pulito con successo!")
            return True
        else:
            print("❌ Alcuni record potrebbero non essere stati eliminati")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante la pulizia del database: {e}")
        return False

def backup_database():
    """
    Crea un backup del database prima della pulizia
    """
    database_path = 'data.sqlite'
    
    if not os.path.exists(database_path):
        print(f"❌ Database non trovato: {database_path}")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data_backup_{timestamp}.sqlite"
    
    try:
        import shutil
        shutil.copy2(database_path, backup_path)
        print(f"✅ Backup creato: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Errore durante la creazione del backup: {e}")
        return None

def show_database_info():
    """
    Mostra informazioni sul database senza cancellare nulla
    """
    database_path = 'data.sqlite'
    
    if not os.path.exists(database_path):
        print(f"❌ Database non trovato: {database_path}")
        return
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        print("📊 INFORMAZIONI DATABASE:")
        print(f"📁 Path: {os.path.abspath(database_path)}")
        
        # Dimensione file
        file_size = os.path.getsize(database_path)
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024*1024:
            size_str = f"{file_size/1024:.1f} KB"
        else:
            size_str = f"{file_size/(1024*1024):.1f} MB"
        print(f"📦 Dimensione: {size_str}")
        
        # Tabelle esistenti
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"📋 Tabelle: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  • {table_name}: {count:,} record")
            except sqlite3.OperationalError:
                print(f"  • {table_name}: Errore nel conteggio")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore durante la lettura del database: {e}")

def main():
    """
    Funzione principale con menu interattivo
    """
    print("🗃️  NORMATTIVA-SCRAPE Database Manager")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'clear':
            # Modalità non interattiva per automation
            confirm = '--force' not in sys.argv
            clear_database(confirm=confirm)
        elif command == 'info':
            show_database_info()
        elif command == 'backup':
            backup_database()
        else:
            print("❌ Comando non riconosciuto")
            print("Comandi disponibili: clear, info, backup")
            print("Opzioni: --force (per clear senza conferma)")
    else:
        # Modalità interattiva
        while True:
            print("\nScegli un'opzione:")
            print("1. 📊 Mostra informazioni database")
            print("2. 💾 Crea backup database")
            print("3. 🧹 Pulisci database")
            print("4. ❌ Esci")
            
            choice = input("\nInserisci la tua scelta (1-4): ").strip()
            
            if choice == '1':
                show_database_info()
            elif choice == '2':
                backup_database()
            elif choice == '3':
                # Offri opzione di backup prima della pulizia
                print("\n⚠️  Prima di pulire, vuoi creare un backup?")
                backup_choice = input("Crea backup? (s/N): ").strip().lower()
                if backup_choice in ['s', 'si', 'y', 'yes']:
                    backup_database()
                    print()
                
                clear_database()
            elif choice == '4':
                print("👋 Uscita dal programma")
                break
            else:
                print("❌ Scelta non valida, riprova")

if __name__ == '__main__':
    main()
