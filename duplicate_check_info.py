#!/usr/bin/env python3
"""
Demonstration of the duplicate checking feature
Shows how the scraper handles duplicate documents and articles
"""

import subprocess
import sys
import os

def show_duplicate_check_demo():
    """Show how duplicate checking works"""
    print("✅ DUPLICATE CHECKING FEATURE DEMONSTRATION")
    print("=" * 60)
    print()
    
    print("🔍 How the duplicate checking works:")
    print("=" * 40)
    print()
    
    print("📄 DOCUMENT LEVEL DUPLICATE CHECK:")
    print("   • Checks for existing documents by URN (Uniform Resource Name)")
    print("   • Also checks by combination of: numero + anno + tipo_atto")
    print("   • If found, skips processing and returns existing document ID")
    print("   • Message: '✅ Document already exists with id: XXX'")
    print()
    
    print("📝 ARTICLE LEVEL DUPLICATE CHECK:")
    print("   • Checks for existing articles by: documento_id + numero_articolo")
    print("   • If found, skips processing and returns existing article ID")
    print("   • Message: '✅ Article X already exists with id: XXX'")
    print()
    
    print("🎯 BENEFITS:")
    print("   • Safe to run the scraper multiple times")
    print("   • No need to clear database between runs")
    print("   • Saves time by skipping already processed content")
    print("   • Prevents duplicate data in the database")
    print()
    
    print("💡 USAGE EXAMPLES:")
    print("   • Run populate_multi_year.py multiple times safely")
    print("   • Resume interrupted scraping sessions")
    print("   • Add new years without re-processing existing ones")
    print("   • Test with small samples without data duplication")
    print()

def show_database_info():
    """Show current database status"""
    print("📊 DATABASE STATUS CHECK")
    print("=" * 30)
    
    try:
        result = subprocess.run([
            'powershell.exe', '-Command',
            'python check_status.py'
        ], 
        cwd=os.getcwd(),
        capture_output=True, 
        text=True, 
        encoding='utf-8',
        errors='replace',
        timeout=60
        )
        
        print("Current database status:")
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
            
    except Exception as e:
        print(f"Error checking database status: {e}")

def main():
    """Main function"""
    print("🎯 DUPLICATE CHECKING INFORMATION")
    print("This shows how the enhanced scraper handles duplicate documents/articles")
    print()
    
    # Show the demonstration
    show_duplicate_check_demo()
    
    # Ask if user wants to see database status
    response = input("📊 Show current database status? (y/N): ")
    if response.lower() in ['y', 'yes']:
        show_database_info()
    
    print("\n" + "=" * 60)
    print("🚀 READY TO USE!")
    print("=" * 60)
    print()
    print("You can now safely run:")
    print("   • python populate_multi_year.py  (for comprehensive historical data)")
    print("   • python scraper_optimized.py YEAR NUM  (for specific year/number)")
    print("   • python test_duplicate_check.py  (to test duplicate detection)")
    print()
    print("The scraper will automatically skip any documents or articles")
    print("that already exist in the database!")

if __name__ == "__main__":
    main()
