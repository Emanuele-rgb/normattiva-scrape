#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data.sqlite')
cursor = conn.cursor()

# Check document title
cursor.execute('SELECT titoloAtto, url_normattiva FROM documenti_normativi LIMIT 1')
doc_result = cursor.fetchone()
print('Document title:', doc_result)

# Check article titles and URLs
cursor.execute('SELECT numero_articolo, titoloAtto, url_documento FROM articoli LIMIT 3')
articles = cursor.fetchall()
print('\nArticles:')
for row in articles:
    print(f'  Article {row[0]}: {row[1][:50]}... | URL: {row[2]}')

conn.close()
