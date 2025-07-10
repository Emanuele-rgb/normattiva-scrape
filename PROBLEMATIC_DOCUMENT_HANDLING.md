# NORMATTIVA SCRAPER - PROBLEMATIC DOCUMENT HANDLING IMPROVEMENTS

PROBLEM IDENTIFIED:
The scraper was hanging on specific documents, particularly:

- URI: https://www.normattiva.it/uri-res/N2Ls?urn:nir:2022;14!multivigente~
- Article date: 2022-02-25

IMPROVEMENTS IMPLEMENTED:

1. ENHANCED HANG DETECTION:

   - Reduced timeout from 5 minutes to 3 minutes without output
   - Added specific detection for repeated article activation dates
   - Added detection for URLs that appear multiple times in output
   - Better progress tracking and diagnostic information

2. PROBLEMATIC DOCUMENT DETECTION:

   - Added detect_problematic_document() function
   - Specifically looks for known problematic patterns
   - Creates skip instruction files for future runs
   - Tracks problematic documents per year

3. RECOVERY MECHANISM:

   - Added run_scraper_with_recovery() function
   - Attempts up to 3 retries for failed years
   - Tracks progress between attempts
   - Handles partial success cases

4. IMPROVED YEAR PROCESSING:

   - Better verification of year completeness
   - Considers partial success as success if documents were processed
   - Creates blacklist files for problematic documents
   - Enhanced logging for troubleshooting

5. MONITORING IMPROVEMENTS:
   - Real-time progress tracking
   - Better identification of stuck processes
   - Detailed diagnostic output during hanging
   - Process monitoring with PID tracking

FILES MODIFIED:

- populate_multi_year.py: Enhanced with all improvements above

BLACKLIST FILES CREATED:

- problematic*documents*[year].txt: Contains known problematic documents
- skip*documents*[year].txt: Instructions for future runs

RECOMMENDATION:
The scraper now has better handling for problematic documents, but the underlying
issue (specific documents causing infinite loops) may still exist in scraper_optimized.py.
Consider adding timeout mechanisms or skip logic directly in the scraper for production use.

NEXT STEPS FOR FULL SOLUTION:

1. Modify scraper_optimized.py to read skip instruction files
2. Add timeout mechanisms for individual document processing
3. Implement graceful error handling for malformed documents
4. Add document-level retry logic with exponential backoff
