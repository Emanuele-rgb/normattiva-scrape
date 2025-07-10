#!/usr/bin/env python3
"""
Test script to verify specific URN-NIR formats mentioned by the user
"""

import requests
import sys
import os

# Add the current directory to the path to import scraper functions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_optimized import _get_permalinks

def test_specific_formats():
    """Test the specific URN-NIR formats mentioned by the user"""
    print("🧪 Testing specific URN-NIR formats...")
    
    # Test cases from user's examples
    test_urls = [
        {
            'url': '/uri-res/N2Ls?urn:nir:stato:legge:1870-12-31;6177',
            'description': 'State law format (1870)'
        },
        {
            'url': '/uri-res/N2Ls?urn:nir:ministero.pubblica.istruzione:decreto.ministeriale:1870-10-31;6066',
            'description': 'Ministry decree format (1870)'
        },
        {
            'url': '/uri-res/N2Ls?urn:nir:stato:regio.decreto:1862;606',
            'description': 'Royal decree format (1862)'
        }
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    successful_tests = 0
    
    for test_case in test_urls:
        url = test_case['url']
        description = test_case['description']
        
        print(f"\n📄 Testing {description}")
        print(f"🔗 URL: {url}")
        
        try:
            result = _get_permalinks(url, session=session)
            
            if result is not None:
                print(f"✅ Success! Document found")
                print(f"📄 Result type: {type(result)}")
                if hasattr(result, '__len__'):
                    print(f"📄 Result length: {len(result)}")
                successful_tests += 1
            else:
                print(f"❌ Document not found")
                
        except Exception as e:
            print(f"❌ Error testing format: {e}")
    
    return successful_tests, len(test_urls)

def test_multivigente_versions():
    """Test the same formats with multivigente parameter"""
    print("\n🧪 Testing multivigente versions...")
    
    # Test cases with multivigente
    test_urls = [
        {
            'url': '/uri-res/N2Ls?urn:nir:stato:legge:1870-12-31;6177!multivigente~',
            'description': 'State law format (1870) with multivigente'
        },
        {
            'url': '/uri-res/N2Ls?urn:nir:ministero.pubblica.istruzione:decreto.ministeriale:1870-10-31;6066!multivigente~',
            'description': 'Ministry decree format (1870) with multivigente'
        },
        {
            'url': '/uri-res/N2Ls?urn:nir:stato:regio.decreto:1862;606!multivigente~',
            'description': 'Royal decree format (1862) with multivigente'
        }
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    successful_tests = 0
    
    for test_case in test_urls:
        url = test_case['url']
        description = test_case['description']
        
        print(f"\n📄 Testing {description}")
        print(f"🔗 URL: {url}")
        
        try:
            result = _get_permalinks(url, session=session)
            
            if result is not None:
                print(f"✅ Success! Document found")
                successful_tests += 1
            else:
                print(f"❌ Document not found")
                
        except Exception as e:
            print(f"❌ Error testing format: {e}")
    
    return successful_tests, len(test_urls)

def main():
    """Run the specific format tests"""
    print("🔍 Testing specific URN-NIR formats mentioned by user")
    print("=" * 60)
    
    # Test basic formats
    basic_success, basic_total = test_specific_formats()
    
    # Test multivigente versions
    multi_success, multi_total = test_multivigente_versions()
    
    print("\n📊 TEST RESULTS")
    print("=" * 40)
    print(f"📄 Basic formats: {basic_success}/{basic_total} PASSED")
    print(f"🔄 Multivigente formats: {multi_success}/{multi_total} PASSED")
    
    total_success = basic_success + multi_success
    total_tests = basic_total + multi_total
    
    print(f"\n🎯 Overall success rate: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
    
    if total_success == total_tests:
        print("🎉 All formats work perfectly!")
    elif total_success > 0:
        print(f"⚠️ {total_success} out of {total_tests} formats work")
    else:
        print("❌ No formats work - check connection and URLs")

if __name__ == "__main__":
    main()
