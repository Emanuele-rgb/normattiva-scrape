import requests
import lxml.html

URLS = [
    "https://www.normattiva.it/uri-res/N2Ls?urn:nir:2022;14!multivigente~",
    "https://www.normattiva.it/uri-res/N2Ls?urn:nir:2022;15!multivigente~"
]

def test_scrape_url(url):
    print(f"Testing URL: {url}")
    resp = requests.get(url)
    print(f"Status code: {resp.status_code}")
    if resp.status_code != 200:
        print("Failed to fetch page.")
        return
    doc = lxml.html.fromstring(resp.content)
    title = doc.xpath('//title/text()')
    print(f"Page title: {title[0] if title else 'N/A'}")
    # Try to extract main law title
    meta_title = doc.xpath('//meta[@property="eli:title"]/@content')
    if meta_title:
        print(f"eli:title: {meta_title[0]}")
    else:
        print("eli:title not found")
    # Print first 300 chars of bodyTesto if present
    body_testo = doc.xpath('//div[@class="bodyTesto"]')
    if body_testo:
        text = body_testo[0].text_content().strip()
        print(f"bodyTesto (first 300 chars): {text[:300]}")
    else:
        print("bodyTesto not found")
    print("-"*60)

if __name__ == "__main__":
    for url in URLS:
        test_scrape_url(url)
