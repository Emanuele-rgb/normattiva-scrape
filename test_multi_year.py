#!/usr/bin/env python3
"""
Conservative Multi-Year Test Script
Tests the scraper with a small number of documents from each year
before running the full population
"""

import subprocess
import sys
import os
from datetime import datetime
import time

def run_scraper_for_year(year, num_docs=5):
    """Run the scraper for a specific year with limited documents"""
    print(f"\n{'='*50}")
    print(f"🧪 TESTING YEAR {year} ({num_docs} documents)")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    try:
        # Run the scraper with PowerShell
        result = subprocess.run([
            'powershell.exe', '-Command',
            f'python scraper_optimized.py {year} {num_docs}'
        ], 
        cwd=os.getcwd(),
        capture_output=True, 
        text=True, 
        timeout=600  # 10 minutes timeout for testing
        )
        
        if result.returncode == 0:
            elapsed_time = time.time() - start_time
            print(f"✅ Year {year} test completed in {elapsed_time:.2f} seconds")
            return True
        else:
            print(f"❌ Error testing year {year}")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout testing year {year}")
        return False
    except Exception as e:
        print(f"❌ Exception testing year {year}: {e}")
        return False

def main():
    """Test the scraper with a few documents from each year"""
    print("🧪 NORMATTIVA MULTI-YEAR TEST")
    print("=" * 50)
    print("This script will test the scraper with a few documents")
    print("from each of the last 5 years to ensure everything works")
    print()
    
    # Test configuration - much smaller numbers
    years_config = {
        2024: 5,   # Test with 5 documents each
        2023: 5,   
        2022: 5,   
        2021: 5,   
        2020: 5,   
    }
    
    total_docs = sum(years_config.values())
    print(f"📋 Test Configuration:")
    for year, num_docs in years_config.items():
        print(f"   {year}: {num_docs} documents")
    print(f"   Total: {total_docs} documents")
    print()
    
    # Clear database for clean test
    print("🧹 Clearing database for clean test...")
    try:
        result = subprocess.run([
            'powershell.exe', '-Command',
            'python clear_database.py'
        ], 
        cwd=os.getcwd(),
        capture_output=True, 
        text=True
        )
        if result.returncode == 0:
            print("✅ Database cleared successfully")
        else:
            print(f"⚠️ Error clearing database: {result.stderr}")
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
    
    # Test each year
    successful_years = []
    failed_years = []
    
    start_total = time.time()
    
    for year, num_docs in years_config.items():
        print(f"\n⏳ Testing year {year}...")
        
        if run_scraper_for_year(year, num_docs):
            successful_years.append(year)
        else:
            failed_years.append(year)
        
        # Small delay between tests
        time.sleep(2)
    
    # Final summary
    total_time = time.time() - start_total
    print(f"\n{'='*50}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*50}")
    print(f"⏱️ Total time: {total_time:.2f} seconds")
    print(f"✅ Successful years: {successful_years}")
    print(f"❌ Failed years: {failed_years}")
    
    if len(successful_years) == len(years_config):
        print(f"\n🎉 All years tested successfully!")
        print(f"💡 You can now run the full population:")
        print(f"   python populate_multi_year.py")
        print(f"💡 Or run the Legal AI Enhancer on the test data:")
        print(f"   python legal_ai_enhancer.py")
    else:
        print(f"\n⚠️ Some years failed. Please check the configuration.")
        print(f"💡 You can retry individual years:")
        for year in failed_years:
            print(f"   python scraper_optimized.py {year} 5")

if __name__ == "__main__":
    main()
