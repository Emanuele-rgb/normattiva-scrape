#!/usr/bin/env python3
"""
Multi-Year Database Population Script
Populates the database with normattiva data from the last 5 years (2020-2024)
"""
import os
import sys
import subprocess
from datetime import datetime

def run_scraper_for_year(year, num_docs=-1):
    """Run the scraper for a specific year"""
    print(f"\n{'='*60}")
    if num_docs == -1:
        print(f"PROCESSING YEAR {year} (FULL YEAR)")
    else:
        print(f"PROCESSING YEAR {year} ({num_docs} documents)")
    print(f"{'='*60}")
    
    try:
        # Run the scraper with PowerShell
        if num_docs == -1:
            # For full year processing, use a large number
            cmd = f'python scraper_optimized.py {year} 50000'
        else:
            cmd = f'python scraper_optimized.py {year} {num_docs}'
            
        print(f"Running command: {cmd}")
        print(f"Starting at {datetime.now().strftime('%H:%M:%S')}")
        
        # Start the process
        result = subprocess.run([
            'powershell.exe', '-Command', cmd
        ], 
        cwd=os.getcwd(),
        text=True, 
        encoding='utf-8',
        errors='replace'
        )
        
        print(f"Completed at {datetime.now().strftime('%H:%M:%S')}")
        
        if result.returncode == 0:
            print(f"SUCCESS: Year {year} completed successfully")
            return True
        else:
            print(f"ERROR: Year {year} failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception processing year {year}: {e}")
        return False

def populate_multiple_years():
    """Populate the database with documents from multiple years"""
    print("Starting multi-year population process...")
    print(f"Current directory: {os.getcwd()}")
    
    # Years to process (last 5 years)
    years = [
        #2020, 2021, 2022, 2023, 2024,
            2025]
    
    print(f"Years to process: {years}")
    print(f"Starting at {datetime.now().strftime('%H:%M:%S')}")
    
    successful_years = []
    failed_years = []
    
    for year in years:
        print(f"\nProcessing year {year}...")
        success = run_scraper_for_year(year)
        
        if success:
            successful_years.append(year)
        else:
            failed_years.append(year)
    
    # Print summary
    print(f"\n{'='*60}")
    print("MULTI-YEAR POPULATION COMPLETE")
    print(f"{'='*60}")
    print(f"Completed at {datetime.now().strftime('%H:%M:%S')}")
    print(f"Successfully processed years: {successful_years}")
    
    if failed_years:
        print(f"Failed years: {failed_years}")
    else:
        print("All years processed successfully!")

def main():
    """Main function"""
    print("Multi-Year Database Population Script")
    print("====================================")
    print("Features:")
    print("  ✓ Multi-year legal document scraping")
    print("  ✓ Allegati length filtering (max 500K chars)")
    print("  ✓ Automatic database optimization")
    print()
    
    # Check if scraper exists
    if not os.path.exists('scraper_optimized.py'):
        print("ERROR: scraper_optimized.py not found in current directory")
        sys.exit(1)
    
    # Start the population process
    populate_multiple_years()

if __name__ == "__main__":
    main()
