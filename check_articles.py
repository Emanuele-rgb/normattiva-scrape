import sqlite3

conn = sqlite3.connect('data.sqlite')
cursor = conn.cursor()

# Check all articles to see their structure
cursor.execute('SELECT numero_articolo, titoloAtto, testo_completo FROM articoli ORDER BY numero_articolo')
results = cursor.fetchall()

print("All articles:")
for i, (numero, titolo, testo) in enumerate(results, 1):
    text_preview = testo[:100] if testo else "No text"
    print(f"{i}. Article: {numero}, Title: {titolo}, Text: {text_preview}...")

# Check specifically for Allegato patterns
cursor.execute('SELECT numero_articolo, titoloAtto FROM articoli WHERE numero_articolo LIKE "%Allegato%"')
allegato_results = cursor.fetchall()

print(f"\nFound {len(allegato_results)} Allegato articles:")
for numero, titolo in allegato_results:
    print(f"- {numero}: {titolo}")

conn.close()
