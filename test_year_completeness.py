#!/usr/bin/env python3
"""
Test script to verify year completeness checking
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from populate_multi_year import check_year_completeness, get_database_statistics

def test_year_completeness():
    """Test the year completeness checking function"""
    print("🧪 TESTING YEAR COMPLETENESS CHECKING")
    print("=" * 50)
    
    # Get database statistics first
    stats = get_database_statistics()
    if stats:
        print("📊 DATABASE OVERVIEW:")
        print(f"   Total documents: {stats['total_docs']:,}")
        print(f"   Total articles: {stats['total_articles']:,}")
        if stats['year_range'][0] and stats['year_range'][1]:
            print(f"   Year range: {stats['year_range'][0]} - {stats['year_range'][1]}")
        if stats['docs_without_articles'] > 0:
            print(f"   Documents without articles: {stats['docs_without_articles']:,}")
        print()
    
    # Test a few specific years
    test_years = [1861, 1900, 1950, 2000, 2020, 2024]
    
    print("🔍 TESTING SPECIFIC YEARS:")
    print("-" * 30)
    
    for year in test_years:
        print(f"\n📅 Testing year {year}:")
        is_complete = check_year_completeness(year)
        if is_complete:
            print(f"   ✅ Year {year} is complete")
        else:
            print(f"   ⚠️ Year {year} needs processing")
    
    print("\n" + "=" * 50)
    print("🏁 YEAR COMPLETENESS TEST COMPLETED")
    print("=" * 50)

def show_incomplete_years():
    """Show years that need processing"""
    print("\n🔍 FINDING INCOMPLETE YEARS")
    print("=" * 40)
    
    # Check a range of years
    start_year = 1861
    end_year = 2025
    
    incomplete_years = []
    complete_years = []
    
    print(f"Checking years {start_year} to {end_year}...")
    
    for year in range(start_year, end_year + 1):
        if year % 20 == 0:  # Progress indicator
            print(f"   Checking year {year}...")
        
        if check_year_completeness(year):
            complete_years.append(year)
        else:
            incomplete_years.append(year)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Complete years: {len(complete_years)}")
    print(f"   Incomplete years: {len(incomplete_years)}")
    print(f"   Total years checked: {len(complete_years) + len(incomplete_years)}")
    
    if incomplete_years:
        print(f"\n⚠️ INCOMPLETE YEARS (need processing):")
        if len(incomplete_years) <= 20:
            print(f"   {incomplete_years}")
        else:
            print(f"   First 20: {incomplete_years[:20]}")
            print(f"   ... and {len(incomplete_years) - 20} more")
    
    if complete_years:
        print(f"\n✅ COMPLETE YEARS:")
        if len(complete_years) <= 20:
            print(f"   {complete_years}")
        else:
            print(f"   Range: {min(complete_years)} - {max(complete_years)}")
            print(f"   Count: {len(complete_years)} years")

def main():
    """Main function"""
    print("🧪 YEAR COMPLETENESS CHECKER")
    print("This script tests the year completeness checking functionality")
    print()
    
    # Test the completeness checking
    test_year_completeness()
    
    # Ask if user wants to see incomplete years
    response = input("\n🔍 Find all incomplete years? (y/N): ")
    if response.lower() in ['y', 'yes']:
        show_incomplete_years()
    
    print("\n💡 Usage:")
    print("   The populate_multi_year.py script will now automatically skip")
    print("   complete years and only process incomplete ones.")
    print("   This saves time and ensures no duplicate processing.")

if __name__ == "__main__":
    main()
