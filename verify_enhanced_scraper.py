#!/usr/bin/env python3
"""
Verification script to test the enhanced scraper with sample HTML content
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from scraper_optimized import (
    extract_article_activation_date,
    extract_article_links_from_navigation,
    extract_article_number_from_text,
    sort_article_number
)
import lxml.html

def test_html_activation_date():
    """Test activation date extraction from HTML"""
    print("🧪 Testing HTML activation date extraction...")
    
    # Sample HTML content as provided by user
    sample_html = '''
    <div>
        <span id="artInizio" class="rosso">&nbsp;26-5-2021</span>
        <div class="bodyTesto">
            <p>This is the article content...</p>
        </div>
    </div>
    '''
    
    html_element = lxml.html.fromstring(sample_html)
    activation_date = extract_article_activation_date(html_element)
    
    if activation_date:
        print(f"  ✓ Extracted activation date: {activation_date}")
    else:
        print("  ❌ Failed to extract activation date")

def test_navigation_extraction():
    """Test article navigation extraction"""
    print("\n🧪 Testing navigation extraction...")
    
    # Sample navigation HTML
    sample_nav_html = '''
    <div class="navigation">
        <a onclick="showArticle('/art1')">art. 1</a>
        <a onclick="showArticle('/art1bis')">art. 1-bis</a>
        <a onclick="showArticle('/art1ter')">art. 1-ter</a>
        <a onclick="showArticle('/art2')">art. 2</a>
        <a onclick="showArticle('/allegato-a')">Allegato A</a>
        <a onclick="showArticle('/allegato-b')">Allegato B</a>
    </div>
    '''
    
    html_element = lxml.html.fromstring(sample_nav_html)
    
    # Mock the _get_absolute_url function for testing
    def mock_get_absolute_url(url):
        return f"https://www.normattiva.it{url}"
    
    # Temporarily replace the function
    import scraper_optimized
    original_func = scraper_optimized._get_absolute_url
    scraper_optimized._get_absolute_url = mock_get_absolute_url
    
    try:
        article_links = extract_article_links_from_navigation(html_element)
        
        print(f"  Found {len(article_links)} items:")
        for link in article_links:
            print(f"    - {link['content_type']}: {link['number']} ({link['text']})")
        
        expected_order = ['1', '1-bis', '1-ter', '2', 'Allegato A', 'Allegato B']
        actual_order = [link['number'] for link in article_links]
        
        if actual_order == expected_order:
            print("  ✓ Navigation extraction and sorting works correctly")
        else:
            print(f"  ❌ Expected order: {expected_order}")
            print(f"  ❌ Actual order: {actual_order}")
            
    finally:
        # Restore original function
        scraper_optimized._get_absolute_url = original_func

def test_complex_article_numbers():
    """Test complex article number patterns"""
    print("\n🧪 Testing complex article number patterns...")
    
    test_cases = [
        ("Art. 1", "1"),
        ("Art. 1-bis", "1-bis"),
        ("Art. 1-ter", "1-ter"),
        ("Art. 5-quater", "5-quater"),
        ("Art. 10-quinquies", "10-quinquies"),
        ("Art. 15-sexies", "15-sexies"),
        ("Articolo 20-septies", "20-septies"),
        ("Articolo 25-octies", "25-octies"),
        ("Articolo 30-novies", "30-novies"),
        ("Articolo 35-decies", "35-decies"),
        ("123 bis", "123-bis"),
        ("456 ter", "456-ter"),
        ("Allegato A", None),
        ("Allegato 1", None),
        ("Allegato I", None),
    ]
    
    for input_text, expected in test_cases:
        result = extract_article_number_from_text(input_text)
        status = "✓" if result == expected else "❌"
        print(f"  {status} '{input_text}' -> '{result}' (expected: '{expected}')")

def test_comprehensive_sorting():
    """Test comprehensive sorting with various article types"""
    print("\n🧪 Testing comprehensive sorting...")
    
    articles = [
        "10-bis",
        "1-ter",
        "Allegato III",
        "1",
        "2-bis",
        "Allegato A",
        "15",
        "1-bis",
        "Allegato B",
        "2",
        "10",
        "3-quater",
        "Allegato 1",
        "1-quater",
        "2-ter",
        "3-bis",
        "3"
    ]
    
    sorted_articles = sorted(articles, key=sort_article_number)
    
    print(f"  Original: {articles}")
    print(f"  Sorted:   {sorted_articles}")
    
    # Check if basic ordering is maintained
    # Articles should come before allegati
    article_indices = []
    allegato_indices = []
    
    for i, article in enumerate(sorted_articles):
        if 'allegato' in article.lower():
            allegato_indices.append(i)
        else:
            article_indices.append(i)
    
    # All articles should come before all allegati
    if article_indices and allegato_indices:
        if max(article_indices) < min(allegato_indices):
            print("  ✓ Articles correctly sorted before allegati")
        else:
            print("  ❌ Articles and allegati not properly separated")
    else:
        print("  ✓ Sorting completed (no mixed content)")

def main():
    """Run all verification tests"""
    print("🚀 Running enhanced scraper verification tests...\n")
    
    test_html_activation_date()
    test_navigation_extraction()
    test_complex_article_numbers()
    test_comprehensive_sorting()
    
    print("\n✅ All verification tests completed!")

if __name__ == "__main__":
    main()
