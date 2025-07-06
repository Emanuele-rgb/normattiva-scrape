#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data.sqlite')
cursor = conn.cursor()

# Check document title
cursor.execute('SELECT titoloAtto FROM documenti_normativi LIMIT 1')
doc_title = cursor.fetchone()[0]
print('Document title from documenti_normativi:')
print(repr(doc_title))

# Check article titles
cursor.execute('SELECT numero_articolo, titoloAtto FROM articoli LIMIT 5')
articles = cursor.fetchall()
print('\nArticle titles from articoli:')
for row in articles:
    print(f'  Article {row[0]}: {repr(row[1][:100])}...')

conn.close()
