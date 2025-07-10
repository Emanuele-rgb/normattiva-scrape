# Duplicate Checking Feature Guide

## Overview

The normattiva scraper now includes intelligent duplicate checking to prevent re-processing of documents and articles that already exist in the database. This makes it safe to run the scraper multiple times without worrying about duplicate data.

## How It Works

### Document Level Checking

- **Primary Check**: URN (Uniform Resource Name) matching
- **Secondary Check**: Combination of `numero`, `anno`, and `tipo_atto`
- **Action**: If duplicate found, skips processing and returns existing document ID
- **Message**: `✅ Document already exists with id: XXX`

### Article Level Checking

- **Check**: Combination of `documento_id` and `numero_articolo`
- **Action**: If duplicate found, skips processing and returns existing article ID
- **Message**: `✅ Article X already exists with id: XXX`

## Benefits

### 🔄 Safe Re-runs

- Run `populate_multi_year.py` multiple times safely
- No need to clear database between runs
- Resume interrupted scraping sessions

### ⚡ Performance

- Saves time by skipping already processed content
- Reduces server load by avoiding unnecessary requests
- Faster completion of large scraping jobs

### 🛡️ Data Integrity

- Prevents duplicate documents in database
- Maintains referential integrity
- Avoids wasted storage space

## Usage Examples

### Comprehensive Historical Population

```bash
python populate_multi_year.py
```

- Safe to run multiple times
- Will only process new/missing content
- Automatically skips existing years/documents

### Specific Year Processing

```bash
python scraper_optimized.py 2024 100
```

- Safe to run again with same parameters
- Will skip any documents already processed
- Useful for testing and incremental updates

### Testing

```bash
python test_duplicate_check.py
```

- Verifies duplicate detection is working
- Runs same command twice to test behavior
- Shows duplicate detection messages

## Configuration Changes

### Database Clearing

The `populate_multi_year.py` script now:

- **Discourages** database clearing by default
- Shows warning when user wants to clear database
- Recommends using duplicate checking instead

### User Interface

- Added informative messages about duplicate checking
- Shows details when duplicates are found
- Provides clear indication of what was skipped

## Technical Implementation

### Database Queries

```sql
-- Document duplicate check
SELECT id, titoloAtto FROM documenti_normativi
WHERE urn = ? OR (numero = ? AND anno = ? AND tipo_atto = ?)

-- Article duplicate check
SELECT id, titoloAtto FROM articoli
WHERE documento_id = ? AND numero_articolo = ?
```

### Error Handling

- Graceful handling of database connection issues
- Fallback behavior when checks fail
- Detailed error messages for debugging

## Best Practices

### 1. Don't Clear Database Unnecessarily

- Use duplicate checking instead of clearing
- Only clear when starting completely fresh
- Backup before clearing if needed

### 2. Monitor Output Messages

- Watch for "already exists" messages
- Verify duplicate detection is working
- Check logs for processing statistics

### 3. Use Test Scripts

- Run `test_duplicate_check.py` to verify functionality
- Test with small samples before large runs
- Verify duplicate detection with `duplicate_check_info.py`

### 4. Incremental Processing

- Process new years without re-processing old ones
- Add missing documents without full re-scrape
- Resume interrupted sessions safely

## Troubleshooting

### If Duplicates Aren't Detected

1. Check database schema compatibility
2. Verify URN format consistency
3. Review document metadata extraction
4. Run test scripts to diagnose issues

### If False Positives Occur

1. Review duplicate detection logic
2. Check URN parsing accuracy
3. Verify document metadata accuracy
4. Consider adjusting matching criteria

## Migration from Previous Versions

### For Existing Databases

- Duplicate checking works with existing data
- No migration required for basic functionality
- Enhanced features require schema updates

### For New Installations

- Duplicate checking enabled by default
- No additional configuration needed
- Full functionality available immediately

## Monitoring and Logging

### Progress Tracking

- Log files show duplicate detection statistics
- Console output indicates skipped items
- Database queries show processing efficiency

### Performance Metrics

- Track duplicate detection rate
- Monitor processing speed improvements
- Measure database growth over time

## Future Enhancements

### Potential Improvements

- Hash-based content comparison
- More sophisticated duplicate detection
- Configurable duplicate checking sensitivity
- Advanced conflict resolution strategies

This feature significantly improves the robustness and usability of the normattiva scraper, making it suitable for production environments and large-scale legal document processing.
