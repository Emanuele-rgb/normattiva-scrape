#!/usr/bin/env python3
"""
Quick test of the enhanced scraper functionality
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from scraper_optimized import (
    extract_article_number_from_text,
    determine_content_type,
    sort_article_number,
    init_versioning_database
)

def test_quick_functionality():
    """Quick test of the enhanced functionality"""
    print("🧪 Testing enhanced scraper functionality...")
    
    # Test article number extraction
    print("\n1. Article number extraction:")
    test_cases = [
        "art. 1",
        "art. 1-bis", 
        "Art. 123 bis",
        "articolo 5-ter",
        "Allegato A"
    ]
    
    for case in test_cases:
        result = extract_article_number_from_text(case)
        content_type = determine_content_type(case)
        print(f"  '{case}' -> number: '{result}', type: '{content_type}'")
    
    # Test sorting
    print("\n2. Article sorting:")
    articles = ["1-ter", "1", "1-bis", "2", "Allegato A", "10"]
    sorted_articles = sorted(articles, key=sort_article_number)
    print(f"  Original: {articles}")
    print(f"  Sorted:   {sorted_articles}")
    
    # Test database initialization
    print("\n3. Database initialization:")
    try:
        init_versioning_database()
        print("  ✓ Database initialization successful")
    except Exception as e:
        print(f"  ❌ Database initialization failed: {e}")
    
    print("\n✅ Enhanced scraper functionality test completed!")

if __name__ == "__main__":
    test_quick_functionality()
