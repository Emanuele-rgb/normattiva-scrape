#!/usr/bin/env python3
"""
Test script to verify duplicate checking functionality
"""

import subprocess
import sys
import os

def test_duplicate_detection():
    """Test that duplicate documents and articles are properly skipped"""
    print("🧪 TESTING DUPLICATE DETECTION FUNCTIONALITY")
    print("=" * 50)
    
    # Test with a small sample - run the same command twice
    print("📋 Test Plan:")
    print("   1. Run scraper with 2 documents from 2024")
    print("   2. Run the same command again")
    print("   3. Verify that duplicates are detected and skipped")
    print()
    
    # First run
    print("🚀 FIRST RUN - Should process documents normally")
    print("-" * 50)
    
    try:
        result1 = subprocess.run([
            'powershell.exe', '-Command',
            'python scraper_optimized.py 2024 2'
        ], 
        cwd=os.getcwd(),
        capture_output=True, 
        text=True, 
        encoding='utf-8',
        errors='replace',
        timeout=300
        )
        
        print("Return code:", result1.returncode)
        print("Output:")
        print(result1.stdout)
        if result1.stderr:
            print("Errors:")
            print(result1.stderr)
        
        if result1.returncode != 0:
            print("❌ First run failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ First run timed out")
        return False
    except Exception as e:
        print(f"❌ Error in first run: {e}")
        return False
    
    print("\n" + "=" * 50)
    
    # Second run - should detect duplicates
    print("🔍 SECOND RUN - Should detect and skip duplicates")
    print("-" * 50)
    
    try:
        result2 = subprocess.run([
            'powershell.exe', '-Command',
            'python scraper_optimized.py 2024 2'
        ], 
        cwd=os.getcwd(),
        capture_output=True, 
        text=True, 
        encoding='utf-8',
        errors='replace',
        timeout=300
        )
        
        print("Return code:", result2.returncode)
        print("Output:")
        print(result2.stdout)
        if result2.stderr:
            print("Errors:")
            print(result2.stderr)
        
        # Check if duplicates were detected in the output
        output_text = result2.stdout.lower()
        
        duplicate_indicators = [
            'already exists',
            'document already exists',
            'article already exists',
            'already processed',
            'duplicate',
            'skipping'
        ]
        
        duplicates_detected = any(indicator in output_text for indicator in duplicate_indicators)
        
        print("\n" + "=" * 50)
        print("🔍 DUPLICATE DETECTION ANALYSIS")
        print("=" * 50)
        
        if duplicates_detected:
            print("✅ SUCCESS: Duplicate detection is working!")
            print("   The scraper correctly identified and skipped existing documents/articles")
            
            # Show specific messages found
            for indicator in duplicate_indicators:
                if indicator in output_text:
                    print(f"   Found indicator: '{indicator}'")
                    
        else:
            print("❌ WARNING: No clear duplicate detection messages found")
            print("   This could mean:")
            print("   - The duplicate detection is not working properly")
            print("   - The output messages need to be checked")
            print("   - The test documents weren't actually duplicates")
        
        return duplicates_detected
        
    except subprocess.TimeoutExpired:
        print("⏰ Second run timed out")
        return False
    except Exception as e:
        print(f"❌ Error in second run: {e}")
        return False

def main():
    """Main function"""
    print("🧪 DUPLICATE DETECTION TEST")
    print("This script tests whether the scraper correctly detects and skips duplicate documents/articles")
    print()
    
    # Ask for confirmation
    response = input("🔍 Run duplicate detection test? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Test cancelled")
        return
    
    # Run the test
    success = test_duplicate_detection()
    
    print("\n" + "=" * 50)
    print("🏁 FINAL RESULT")
    print("=" * 50)
    
    if success:
        print("✅ DUPLICATE DETECTION TEST PASSED!")
        print("   The scraper correctly handles duplicate documents and articles")
        print("   You can safely run populate_multi_year.py multiple times")
        print("   without worrying about duplicate data")
    else:
        print("❌ DUPLICATE DETECTION TEST FAILED!")
        print("   Please check the scraper implementation")
        print("   You may need to clear the database between runs")
    
    print("\n💡 Next steps:")
    print("   - If test passed: You can run populate_multi_year.py with confidence")
    print("   - If test failed: Check the duplicate detection logic in scraper_optimized.py")

if __name__ == "__main__":
    main()
