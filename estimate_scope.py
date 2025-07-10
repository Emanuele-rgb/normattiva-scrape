#!/usr/bin/env python3
"""
Estimate the scope of the comprehensive historical database population
"""

from datetime import datetime
import requests
import time

def estimate_documents_for_sample_years():
    """Estimate documents for a sample of years to project total scope"""
    print("🔍 ESTIMATING COMPREHENSIVE DATABASE SCOPE")
    print("=" * 60)
    
    # Sample years across different historical periods
    sample_years = [
        1861,  # Unification of Italy
        1900,  # Early 20th century
        1946,  # Post-war reconstruction
        1970,  # Economic boom
        1990,  # Modern era
        2000,  # New millennium
        2010,  # Recent decade
        2020,  # Very recent
        2024,  # Current
    ]
    
    print("📊 Sampling key historical periods...")
    print(f"   Sample years: {sample_years}")
    print()
    
    session = requests.Session()
    session.headers.update({
        'User-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    estimates = {}
    
    for year in sample_years:
        print(f"🔍 Estimating documents for year {year}...")
        
        # Quick binary search to find approximate document count
        low, high = 1, 10000
        last_valid = 0
        
        for _ in range(10):  # Limited iterations for estimation
            mid = (low + high) // 2
            url = f"https://www.normattiva.it/uri-res/N2Ls?urn:nir:{year};{mid}!multivigente~"
            
            try:
                response = session.get(url, timeout=10)
                
                if b'Errore nel caricamento delle informazioni' in response.content:
                    high = mid - 1
                else:
                    last_valid = mid
                    low = mid + 1
                    
            except:
                high = mid - 1
                
            time.sleep(0.2)  # Be nice to the server
        
        estimates[year] = last_valid
        print(f"   📄 Estimated documents for {year}: {last_valid}")
    
    print()
    print("📊 SCOPE ESTIMATION RESULTS")
    print("=" * 60)
    
    # Calculate totals
    total_estimated = sum(estimates.values())
    avg_per_year = total_estimated / len(estimates)
    total_years = 165  # 1861-2025
    projected_total = int(avg_per_year * total_years)
    
    print(f"📈 Sample statistics:")
    print(f"   📄 Total documents in sample: {total_estimated:,}")
    print(f"   📊 Average per year: {avg_per_year:.0f}")
    print(f"   📅 Total years to process: {total_years}")
    print(f"   🎯 Projected total documents: {projected_total:,}")
    print()
    
    # Time estimates
    print(f"⏱️ TIME ESTIMATES:")
    print(f"   🚀 At 5 minutes per year: {total_years * 5 / 60:.1f} hours")
    print(f"   🐌 At 15 minutes per year: {total_years * 15 / 60:.1f} hours")
    print(f"   📊 Expected range: 14-41 hours")
    print()
    
    # Show year breakdown
    print(f"📅 HISTORICAL BREAKDOWN:")
    for year, count in estimates.items():
        period = get_historical_period(year)
        print(f"   {year} ({period}): {count:,} documents")
    
    print()
    print("🏛️ SIGNIFICANCE:")
    print("   This will be the most comprehensive Italian legal database")
    print("   covering 164 years of legal history from the unification")
    print("   of Italy to the present day!")
    print()
    print("💡 Run 'python populate_multi_year.py' to start the process")

def get_historical_period(year):
    """Get historical period name for a year"""
    if year < 1900:
        return "Unification Era"
    elif year < 1946:
        return "Early Kingdom/Fascism"
    elif year < 1970:
        return "Post-war Republic"
    elif year < 1990:
        return "Economic Boom"
    elif year < 2000:
        return "Modern Era"
    elif year < 2010:
        return "New Millennium"
    elif year < 2020:
        return "Recent Decade"
    else:
        return "Current Era"

if __name__ == "__main__":
    estimate_documents_for_sample_years()
