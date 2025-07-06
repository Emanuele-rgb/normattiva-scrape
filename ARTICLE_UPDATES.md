# Article Updates Feature

This document describes the new article updates feature that has been added to the NORME-NET scraper. This feature automatically detects and handles the "aggiornamenti all'articolo" (article updates) functionality found on Italian legislation websites.

## 🚀 Features

### Automatic Update Detection

- Automatically detects "aggiornamenti all'articolo" buttons on article pages
- Handles various button types (links, buttons, data attributes)
- Extracts updated content and modification dates

### Database Integration

- Stores both original and updated article content
- Tracks modification history using the `modifiche_normative` table
- Maintains relationships between original and modified articles
- Supports multiple versions of the same article

### Enhanced Scraping

- Seamless integration with existing scraper functionality
- Fallback to basic scraping if enhanced features fail
- Preserves compatibility with existing database structure

## 📁 New Files

### `article_updates_scraper.py`

Core module containing the article updates functionality:

- `detect_article_updates_button()` - Detects update buttons on pages
- `extract_article_updates()` - Extracts update information from update pages
- `process_article_with_updates()` - Processes individual articles with updates
- `save_article_with_updates()` - Saves articles and their modifications to database
- `enhanced_article_scraping()` - Enhanced scraping that handles updates

### `test_article_updates.py`

Test script for the article updates functionality:

- Tests database schema compatibility
- Tests article processing with updates
- Provides example usage

### `article_updates_manager.py`

Management utility for viewing and managing article modifications:

- View all modifications
- Show modified articles
- Export modifications to CSV
- Clean old modifications
- Statistics and reporting

## 🗃️ Database Changes

The feature uses the existing `modifiche_normative` table from the database schema:

```sql
CREATE TABLE modifiche_normative (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Modified document/article
    documento_modificato_id INTEGER REFERENCES documenti_normativi(id),
    articolo_modificato_id INTEGER REFERENCES articoli(id),

    -- Modifying document
    documento_modificante_id INTEGER REFERENCES documenti_normativi(id),

    tipo_modifica VARCHAR(50), -- 'sostituzione', 'aggiunta', 'abrogazione', 'modifica'
    descrizione_modifica TEXT,

    data_modifica DATE NOT NULL,
    testo_precedente TEXT,
    testo_nuovo TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Enhanced Articles Table

The `articoli` table now uses additional fields:

- `status` - Can be 'vigente', 'modificato', 'sostituito'
- `data_ultima_modifica` - Date of last modification

## 🔧 Usage

### Basic Usage

The feature is automatically integrated into the main scraper. When you run the normal scraping process:

```powershell
python scraper.py
```

The scraper will automatically:

1. Detect articles with "aggiornamenti all'articolo" buttons
2. Extract the original content
3. Click the updates button and extract updated content
4. Store both versions in the database with modification tracking

### Manual Testing

Test the functionality with specific URLs:

```powershell
# Run full functionality test
python test_article_updates.py test

# Test only database schema
python test_article_updates.py schema

# Show current statistics
python test_article_updates.py stats
```

### Managing Article Updates

Use the management utility to view and manage modifications:

```powershell
# View all modifications
python article_updates_manager.py list

# View modified articles
python article_updates_manager.py articles

# Show details of specific modification
python article_updates_manager.py details 5

# Show statistics
python article_updates_manager.py stats

# Export to CSV
python article_updates_manager.py export modifications.csv

# Clean old modifications (older than 180 days)
python article_updates_manager.py clean 180
```

## 🔍 How It Works

### 1. Article Detection

When processing a document, the scraper:

- Looks for individual article links
- If found, processes each article separately
- If not found, processes the entire document as one article

### 2. Update Button Detection

For each article page, the scraper searches for:

- Buttons with text "aggiornamenti all'articolo"
- Links with similar text
- Elements with specific data attributes
- Alternative patterns for update functionality

### 3. Content Extraction

When an update button is found:

- Clicks/navigates to the updates page
- Extracts the table of modifications
- Follows links to detailed change descriptions
- Parses dates and modification types

### 4. Database Storage

The system stores:

- Original article content in the `articoli` table
- Modified versions as new articles with status 'modificato'
- Modification records in `modifiche_normative` table
- Relationships between original and modified versions

## 🎯 Example Workflow

1. **Scraper encounters an article**:

   ```
   Article: "Art. 1 - Disposizioni generali"
   URL: http://www.normattiva.it/...
   ```

2. **Detects update button**:

   ```
   Found: "aggiornamenti all'articolo" button
   Update URL: http://www.normattiva.it/.../aggiornamenti
   ```

3. **Extracts updates**:

   ```
   Found 2 updates:
   - 29/04/2020: L. 27/2020 - Modified text content
   - 15/06/2021: D.L. 52/2021 - Further modifications
   ```

4. **Stores in database**:
   ```
   - Original article (ID: 123, status: 'sostituito')
   - Modified version 1 (ID: 124, status: 'sostituito')
   - Modified version 2 (ID: 125, status: 'vigente')
   - 2 modification records in modifiche_normative
   ```

## ⚙️ Configuration

### Customization Options

You can customize the behavior by modifying parameters in `article_updates_scraper.py`:

- **Update detection patterns**: Modify the XPath expressions in `detect_article_updates_button()`
- **Content extraction**: Adjust selectors in `extract_article_updates()`
- **Processing limits**: Change the article limit in `enhanced_article_scraping()`
- **Delay settings**: Modify `time.sleep()` values for server-friendly scraping

### Error Handling

The system includes comprehensive error handling:

- Network timeouts and connection errors
- Missing or malformed content
- Database connection issues
- Fallback to basic scraping when enhanced features fail

## 📊 Monitoring and Statistics

### Built-in Statistics

The scraper provides detailed statistics about article modifications:

```powershell
python article_updates_manager.py stats
```

Output includes:

- Total number of modifications
- Unique articles modified
- Modifications by type
- Recent activity trends
- Monthly breakdown

### Example Output

```
📊 Article Modifications Statistics
========================================
Total Modifications: 156
Unique Articles Modified: 89
Unique Modifying Documents: 45

By Modification Type:
  sostituzione: 98
  modifica: 45
  aggiunta: 13

Recent Activity:
  Last 7 days: 3
  Last 30 days: 12
```

## 🔒 Data Integrity

### Version Control

- Each modification creates a new article version
- Original articles are marked as 'sostituito' (replaced)
- Full audit trail maintained in `modifiche_normative`
- No data loss - all versions preserved

### Consistency Checks

- Foreign key constraints ensure data integrity
- Automatic rollback on errors
- Validation of required fields
- Duplicate prevention

## 🚨 Troubleshooting

### Common Issues

1. **"Import could not be resolved" errors**

   - Install required packages: `pip install requests lxml`
   - Ensure Python environment is properly configured

2. **No updates detected**

   - Website structure may have changed
   - Check XPath selectors in `detect_article_updates_button()`
   - Verify article URL is accessible

3. **Database errors**

   - Ensure database schema is up to date
   - Run `python test_article_updates.py schema` to check
   - Verify write permissions on database file

4. **Network timeouts**
   - Increase timeout values in requests
   - Add longer delays between requests
   - Check internet connectivity

### Debug Mode

Enable verbose logging by adding debug prints:

```python
# In article_updates_scraper.py
DEBUG = True

if DEBUG:
    print(f"[DEBUG] Processing: {url}")
```

## 🔄 Future Enhancements

Potential improvements for future versions:

1. **Machine Learning Integration**

   - Automatic classification of modification types
   - Content similarity analysis
   - Anomaly detection for unusual changes

2. **Real-time Monitoring**

   - Scheduled checks for new modifications
   - Email notifications for important changes
   - RSS feeds for updates

3. **Advanced Analytics**

   - Trend analysis of legislative changes
   - Impact assessment of modifications
   - Visualization of change patterns

4. **API Integration**
   - RESTful API for accessing modifications
   - Webhook support for real-time updates
   - Integration with external legal databases

## 📝 Contributing

When contributing to the article updates feature:

1. **Test thoroughly** - Use the test scripts before submitting changes
2. **Maintain compatibility** - Ensure fallback to basic functionality works
3. **Document changes** - Update this README for significant modifications
4. **Follow patterns** - Use existing code patterns and error handling
5. **Performance** - Consider impact on scraping speed and database size

## 📞 Support

For issues with the article updates feature:

1. Check this documentation first
2. Run the test script to identify the problem
3. Check database schema compatibility
4. Review error messages in console output
5. Examine the modification records in the database
