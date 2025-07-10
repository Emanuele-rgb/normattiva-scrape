#!/usr/bin/env python3
"""
Test script to verify older document retrieval for specific historical years
"""

import requests
import sys
import os

# Add the current directory to the path to import scraper functions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_optimized import construct_norma_url, _get_permalinks, find_last_document_for_year

def test_historical_years():
    """Test a few historical years to verify document retrieval"""
    print("🏛️ Testing historical years for older document format...")
    
    # Test some key historical years
    test_years = [1862, 1870, 1880, 1890, 1898]
    
    # Create session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    results = {}
    
    for year in test_years:
        print(f"\n📅 Testing year {year}...")
        
        # Try to find the last document for this year (limit search to reasonable number)
        try:
            last_doc = find_last_document_for_year(year, session, max_search=1000)
            if last_doc > 0:
                print(f"✅ Year {year}: Found {last_doc} documents")
                results[year] = last_doc
            else:
                print(f"❌ Year {year}: No documents found")
                results[year] = 0
                
        except Exception as e:
            print(f"❌ Year {year}: Error - {e}")
            results[year] = -1
    
    # Summary
    print(f"\n📊 HISTORICAL YEAR TEST RESULTS")
    print("=" * 40)
    
    successful_years = [year for year, count in results.items() if count > 0]
    failed_years = [year for year, count in results.items() if count <= 0]
    
    for year, count in results.items():
        if count > 0:
            print(f"✅ {year}: {count} documents")
        elif count == 0:
            print(f"❌ {year}: No documents found")
        else:
            print(f"❌ {year}: Error during search")
    
    print(f"\n📈 Summary:")
    print(f"   Successful years: {len(successful_years)}/{len(test_years)}")
    print(f"   Failed years: {len(failed_years)}/{len(test_years)}")
    
    if successful_years:
        print(f"   ✅ Years with documents: {successful_years}")
    
    if failed_years:
        print(f"   ❌ Years without documents: {failed_years}")

def main():
    """Run the historical years test"""
    print("🔍 Testing historical document retrieval for pre-1900 years")
    print("=" * 60)
    
    test_historical_years()

if __name__ == "__main__":
    main()
