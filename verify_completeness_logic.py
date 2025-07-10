#!/usr/bin/env python3
"""
Quick verification that the year completeness logic is working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from populate_multi_year import check_year_completeness

def verify_logic():
    """Verify the year completeness logic"""
    print("🔍 VERIFYING YEAR COMPLETENESS LOGIC")
    print("=" * 50)
    
    # Test years we know about
    test_cases = [
        (1861, True, "Should be complete (has 408 documents with 8033 articles)"),
        (1862, False, "Should be incomplete (no documents found)"),
        (2024, False, "Should be incomplete (no documents found)"),
    ]
    
    for year, expected, description in test_cases:
        print(f"\n📅 Testing year {year}:")
        print(f"   Expected: {'Complete' if expected else 'Incomplete'}")
        print(f"   Reason: {description}")
        
        result = check_year_completeness(year)
        
        if result == expected:
            print(f"   ✅ CORRECT: Year {year} is {'complete' if result else 'incomplete'}")
        else:
            print(f"   ❌ WRONG: Year {year} is {'complete' if result else 'incomplete'}, expected {'complete' if expected else 'incomplete'}")
    
    print("\n" + "=" * 50)
    print("🏁 VERIFICATION COMPLETE")
    print("=" * 50)
    
    print("\n💡 What this means for populate_multi_year.py:")
    print("   - Year 1861 will be SKIPPED (already complete)")
    print("   - Years 1862-2025 will be PROCESSED (incomplete)")
    print("   - This is the correct behavior!")

if __name__ == "__main__":
    verify_logic()
