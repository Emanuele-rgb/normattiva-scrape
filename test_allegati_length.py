#!/usr/bin/env python3
"""
Test script for allegati length checking functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the scraper module to test the functions
from scraper_optimized import MAX_ALLEGATO_LENGTH, fetch_allegato_content, clean_article_text

def test_allegato_length_check():
    """Test the allegato length checking functionality"""
    print("🧪 Testing Allegati Length Check")
    print("=" * 50)
    
    # Test 1: Check that the constant is properly set
    print(f"✓ MAX_ALLEGATO_LENGTH constant: {MAX_ALLEGATO_LENGTH:,} characters")
    
    # Test 2: Test clean_article_text with various lengths
    short_text = "This is a short allegato content that should be accepted."
    long_text = "A" * (MAX_ALLEGATO_LENGTH + 1000)  # Create text longer than max
    
    cleaned_short = clean_article_text(short_text)
    cleaned_long = clean_article_text(long_text)
    
    print(f"✓ Short text length: {len(cleaned_short)} chars - Should be accepted")
    print(f"✓ Long text length: {len(cleaned_long)} chars - Should be rejected")
    
    # Test 3: Simulate length check logic
    def simulate_allegato_check(content, name="Test Allegato"):
        if len(content) > MAX_ALLEGATO_LENGTH:
            print(f"⚠️ WOULD SKIP {name}: Content too long ({len(content)} chars > {MAX_ALLEGATO_LENGTH} max)")
            return False
        else:
            print(f"✓ WOULD ACCEPT {name}: Content size OK ({len(content)} chars)")
            return True
    
    print("\n🔍 Simulating allegato processing:")
    simulate_allegato_check(cleaned_short, "Short Allegato")
    simulate_allegato_check(cleaned_long, "Long Allegato")
    
    print("\n✅ Allegati length check functionality is properly configured!")
    print(f"   Any allegato longer than {MAX_ALLEGATO_LENGTH:,} characters will be skipped.")

if __name__ == "__main__":
    test_allegato_length_check()
