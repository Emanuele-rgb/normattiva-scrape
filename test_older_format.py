#!/usr/bin/env python3
"""
Test script to verify the older URN-NIR format works for pre-1900 documents
"""

import requests
import sys
import os

# Add the current directory to the path to import scraper functions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_optimized import construct_norma_url, _get_permalinks, try_multiple_formats_for_old_documents

def test_older_document_formats():
    """Test fetching older documents using different URN-NIR formats"""
    print("🧪 Testing older document formats (pre-1900)...")
    
    # Test cases for different formats
    test_cases = [
        {
            'year': 1862,
            'doc_number': 606,
            'expected_format': 'regio.decreto',
            'description': 'Royal decree format'
        },
        {
            'year': 1870,
            'doc_number': 6177,
            'expected_format': 'legge',
            'description': 'State law format'
        },
        {
            'year': 1870,
            'doc_number': 6066,
            'expected_format': 'ministero',
            'description': 'Ministry decree format'
        }
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    successful_tests = 0
    
    for test_case in test_cases:
        year = test_case['year']
        doc_number = test_case['doc_number']
        description = test_case['description']
        
        print(f"\n📄 Testing {description}: {year};{doc_number}")
        
        try:
            # Use the new multi-format approach
            result_url = try_multiple_formats_for_old_documents(year, doc_number, session, multivigente=True)
            
            if result_url:
                result = _get_permalinks(result_url, session=session)
                if result is not None:
                    print(f"✅ Success! Found document {doc_number} from year {year} ({description})")
                    print(f"📄 URL: {result_url}")
                    successful_tests += 1
                else:
                    print(f"❌ URL found but no content for {doc_number} from year {year}")
            else:
                print(f"❌ No working format found for document {doc_number} from year {year}")
                
        except Exception as e:
            print(f"❌ Error testing {description}: {e}")
    
    return successful_tests, len(test_cases)

def test_modern_document_format():
    """Test fetching a modern document using the standard format"""
    print("\n🧪 Testing modern document format (post-1900)...")
    
    # Test year 2024 (after 1900)
    test_year = 2024
    test_doc_number = 1
    
    # Create URL using the new format
    norma_url = construct_norma_url(test_year, test_doc_number, multivigente=True)
    print(f"📄 Testing URL: {norma_url}")
    
    # Test with a session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        result = _get_permalinks(norma_url, session=session)
        if result is not None:
            print(f"✅ Success! Found document {test_doc_number} from year {test_year}")
            print(f"📄 Result type: {type(result)}")
            if hasattr(result, '__len__'):
                print(f"📄 Result length: {len(result)}")
            return True
        else:
            print(f"❌ No result for document {test_doc_number} from year {test_year}")
            return False
    except Exception as e:
        print(f"❌ Error testing document: {e}")
        return False

def main():
    """Run the tests"""
    print("🔍 Testing URN-NIR format handling for older and modern documents")
    print("=" * 60)
    
    # Test older document formats
    older_success, older_total = test_older_document_formats()
    
    # Test modern document format  
    modern_success = test_modern_document_format()
    
    print("\n📊 TEST RESULTS")
    print("=" * 30)
    print(f"🏛️ Older document formats: {older_success}/{older_total} PASSED")
    print(f"🆕 Modern document format: {'✅ PASS' if modern_success else '❌ FAIL'}")
    
    if older_success > 0 and modern_success:
        print(f"\n🎉 Tests passed! The scraper can handle multiple old and modern document formats.")
        print(f"✅ Successfully tested {older_success} older document formats")
    elif older_success > 0:
        print(f"\n⚠️ Some older formats work ({older_success}/{older_total}). Modern format may need adjustment.")
    elif modern_success:
        print(f"\n⚠️ Only modern format works. Older formats may need adjustment.")
    else:
        print(f"\n❌ All formats failed. Check internet connection and formats.")

if __name__ == "__main__":
    main()
