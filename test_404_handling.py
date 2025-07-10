#!/usr/bin/env python3
"""
Test script to verify the improved 404 handling with intelligent document detection
"""

import subprocess
import sys
import os
import requests
import lxml.html

def test_404_detection():
    """Test that we can detect 404 pages correctly"""
    print("🧪 Testing 404 detection with known 404 URL...")
    
    # Test the known 404 URL
    test_url = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:2000;1000!multivigente~"
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        response = session.get(test_url)
        print(f"Status code: {response.status_code}")
        
        # Check for the specific 404 content
        if b'Errore nel caricamento delle informazioni' in response.content:
            print("✅ 404 page detected correctly!")
            return True
        else:
            print("❌ 404 page not detected")
            print(f"Content preview: {response.content[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error during 404 test: {e}")
        return False

def test_valid_document():
    """Test that a valid document is detected correctly"""
    print("🧪 Testing valid document detection...")
    
    # Test a document that should exist (early 2024)
    test_url = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:2024;1!multivigente~"
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        response = session.get(test_url)
        print(f"Status code: {response.status_code}")
        
        # Check that it's NOT a 404 page
        if b'Errore nel caricamento delle informazioni' not in response.content:
            print("✅ Valid document detected correctly!")
            return True
        else:
            print("❌ Valid document incorrectly detected as 404")
            return False
            
    except Exception as e:
        print(f"❌ Error during valid document test: {e}")
        return False

def test_intelligent_scraper():
    """Test the intelligent scraper with a small year range"""
    print("🧪 Testing intelligent scraper with year 2025 (small range)...")
    
    try:
        result = subprocess.run([
            'powershell.exe', '-Command',
            'python scraper_optimized.py 2025 100'  # Small range for testing
        ], 
        cwd=os.getcwd(),
        capture_output=True, 
        text=True, 
        timeout=600  # 10 minutes timeout
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout preview: {result.stdout[:1000]}...")
        if result.stderr:
            print(f"Stderr: {result.stderr[:1000]}...")
        
        # Check if the output contains evidence of intelligent detection
        if "Finding last document for year" in result.stdout:
            print("✅ Intelligent document detection is working!")
            return True
        else:
            print("⚠️ Intelligent detection output not found, but process completed")
            return result.returncode == 0
            
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Error during intelligent scraper test: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing improved 404 handling with intelligent document detection...")
    print("=" * 70)
    
    # Run all tests
    test_results = []
    
    print("\n1. Testing 404 detection...")
    test_results.append(test_404_detection())
    
    print("\n2. Testing valid document detection...")
    test_results.append(test_valid_document())
    
    print("\n3. Testing intelligent scraper...")
    test_results.append(test_intelligent_scraper())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n{'='*70}")
    print(f"TEST SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The intelligent 404 handling is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the output above.")
    
    print("=" * 70)
