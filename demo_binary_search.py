#!/usr/bin/env python3
"""
Demonstration of the binary search approach for finding last document
"""

import requests
import time

def demo_binary_search_for_year(year, max_search=1000):
    """
    Demonstrate how binary search finds the last document for a year
    """
    print(f"🔍 Demonstrating binary search for year {year}...")
    print(f"📊 Search range: 1 to {max_search}")
    print("-" * 50)
    
    session = requests.Session()
    session.headers.update({
        'User-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    low = 1
    high = max_search
    last_valid = 0
    step = 1
    
    while low <= high:
        mid = (low + high) // 2
        url = f"https://www.normattiva.it/uri-res/N2Ls?urn:nir:{year};{mid}!multivigente~"
        
        print(f"Step {step}: Testing document {mid} (range: {low}-{high})")
        
        try:
            response = session.get(url, timeout=10)
            
            # Check if it's a 404 page
            if b'Errore nel caricamento delle informazioni' in response.content:
                print(f"   ❌ Document {mid} doesn't exist")
                high = mid - 1
            else:
                print(f"   ✅ Document {mid} exists")
                last_valid = mid
                low = mid + 1
                
        except Exception as e:
            print(f"   ⚠️ Error checking document {mid}: {e}")
            high = mid - 1
        
        step += 1
        time.sleep(0.5)  # Be nice to the server
        
        if step > 20:  # Safety limit for demo
            print("   ⏰ Demo limit reached")
            break
    
    print("-" * 50)
    print(f"🎯 Result: Last valid document for year {year} is {last_valid}")
    print(f"📊 Binary search completed in {step-1} steps")
    print(f"💡 Linear search would have taken up to {last_valid} steps")
    
    return last_valid

if __name__ == "__main__":
    print("🚀 BINARY SEARCH DEMONSTRATION")
    print("=" * 60)
    print("This demo shows how binary search efficiently finds")
    print("the last available document for a given year.")
    print("=" * 60)
    
    # Demo with year 2025 (current year, likely to have fewer documents)
    demo_binary_search_for_year(2025, 500)
    
    print("\n" + "=" * 60)
    print("🎉 Demo completed!")
    print("💡 The actual scraper uses this same approach but with")
    print("   a much larger search range (up to 50,000 documents)")
    print("=" * 60)
