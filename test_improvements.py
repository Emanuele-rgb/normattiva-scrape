#!/usr/bin/env python3
"""
Test script for the improved populate_multi_year.py
Tests the problematic document detection and recovery mechanisms
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from populate_multi_year import (
    detect_problematic_document,
    create_skip_document_instruction,
    get_document_count_for_year,
    check_year_completeness
)

def test_problematic_document_detection():
    """Test the problematic document detection function"""
    print("Testing problematic document detection...")
    
    # Test with problematic output
    problematic_output = [
        "Processing document...",
        "DATE: Found article activation date: 2022-02-25",
        "Processing article...",
        "DATE: Found article activation date: 2022-02-25",
        "Processing article...",
        "DATE: Found article activation date: 2022-02-25",
        "Processing article...",
        "DATE: Found article activation date: 2022-02-25",
    ]
    
    is_problematic, pattern = detect_problematic_document(problematic_output, 2022)
    
    if is_problematic:
        print(f"✓ SUCCESS: Detected problematic document pattern: {pattern}")
        
        # Test creating skip instruction
        skip_file = create_skip_document_instruction(2022, pattern)
        if skip_file:
            print(f"✓ SUCCESS: Created skip instruction file: {skip_file}")
        else:
            print("✗ FAILED: Could not create skip instruction file")
    else:
        print("✗ FAILED: Did not detect problematic document")
    
    # Test with normal output
    normal_output = [
        "Processing document 1...",
        "SUCCESS: Document 1 processed",
        "Processing document 2...",
        "SUCCESS: Document 2 processed",
        "Processing document 3...",
        "SUCCESS: Document 3 processed",
    ]
    
    is_problematic, pattern = detect_problematic_document(normal_output, 2022)
    
    if not is_problematic:
        print("✓ SUCCESS: Normal output correctly identified as non-problematic")
    else:
        print(f"✗ FAILED: Normal output incorrectly identified as problematic: {pattern}")

def test_year_completeness():
    """Test the year completeness check"""
    print("\nTesting year completeness check...")
    
    # Test with years that might exist in the database
    test_years = [2022, 2023, 2024, 2025]
    
    for year in test_years:
        is_complete = check_year_completeness(year)
        doc_count = get_document_count_for_year(year)
        
        print(f"Year {year}: {'Complete' if is_complete else 'Incomplete'} - {doc_count} documents")

def main():
    """Run all tests"""
    print("TESTING IMPROVED POPULATE_MULTI_YEAR.PY")
    print("=" * 50)
    
    test_problematic_document_detection()
    test_year_completeness()
    
    print("\n" + "=" * 50)
    print("TEST COMPLETED")
    print("If you see ✓ SUCCESS messages, the improvements are working correctly.")
    print("If you see ✗ FAILED messages, there may be issues to fix.")

if __name__ == "__main__":
    main()
