#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data.sqlite')
cursor = conn.cursor()

# Check document columns
cursor.execute('PRAGMA table_info(documenti_normativi)')
print('documenti_normativi columns:')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')

print()

# Check article columns
cursor.execute('PRAGMA table_info(articoli)')
print('articoli columns:')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')

conn.close()
