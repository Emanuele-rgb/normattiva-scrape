#!/usr/bin/env python3
"""
Test script to verify the titoloAtto fix is working
"""
import sqlite3

def check_database():
    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    
    # Check for documents with "n. 13"
    cursor.execute('SELECT id, titoloAtto FROM documenti_normativi WHERE titoloAtto LIKE "%n. 13%"')
    docs_13 = cursor.fetchall()
    
    print("📊 Documents with 'n. 13' in title:")
    for doc in docs_13:
        print(f"  ID: {doc[0]}, Title: {doc[1]}")
    
    # Check for documents with "n. 10" (the wrong one)
    cursor.execute('SELECT id, titoloAtto FROM documenti_normativi WHERE titoloAtto LIKE "%n. 10%"')
    docs_10 = cursor.fetchall()
    
    print("\n📊 Documents with 'n. 10' in title:")
    for doc in docs_10:
        print(f"  ID: {doc[0]}, Title: {doc[1]}")
    
    # Check all documents from year 2000
    cursor.execute('SELECT id, numero, titoloAtto FROM documenti_normativi WHERE anno = 2000')
    docs_2000 = cursor.fetchall()
    
    print("\n📊 All documents from year 2000:")
    for doc in docs_2000:
        print(f"  ID: {doc[0]}, Numero: {doc[1]}, Title: {doc[2]}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
