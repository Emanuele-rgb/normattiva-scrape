# 📚 NORME-NET - Article Versioning System

## Overview

This enhanced version of NORME-NET supports complete article versioning with historical tracking of all changes. The system captures both the **original content** (`orig.`) and all **updates** (`agg.1`, `agg.2`, etc.) with their respective **validity dates**.

## Features

### ✅ Complete Article Versioning

- **Original Version (`orig.`)**: The initial text of the article
- **Updates (`agg.1`, `agg.2`, etc.)**: All subsequent modifications
- **Validity Dates**: When each version became effective and when it was superseded
- **Current Version Tracking**: Automatic identification of the currently active version

### ✅ Historical Preservation

- All previous versions are preserved in the database
- Complete audit trail of article changes
- Timeline visualization of article evolution

### ✅ Enhanced Database Schema

- `articoli_versioni`: Stores all versions of each article
- Enhanced `modifiche_normative`: Tracks version-to-version changes
- Views for easy querying of current and historical data

## Database Schema

### Main Tables

#### `articoli_versioni`

```sql
CREATE TABLE articoli_versioni (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articolo_id INTEGER REFERENCES articoli(id),

    -- Version identification
    tipo_versione VARCHAR(20) NOT NULL,     -- 'orig', 'agg.1', 'agg.2', etc.
    numero_aggiornamento INTEGER,           -- NULL for 'orig', 1 for 'agg.1', etc.

    -- Content
    testo_versione TEXT NOT NULL,
    testo_pulito TEXT,

    -- Validity dates
    data_inizio_vigore DATE NOT NULL,       -- When this version became effective
    data_fine_vigore DATE,                  -- When superseded (NULL if current)

    -- Status
    is_current BOOLEAN DEFAULT FALSE,       -- TRUE only for currently active version
    status VARCHAR(20) DEFAULT 'vigente',   -- 'vigente', 'abrogato', 'sostituito'

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Convenient Views

#### `articoli_correnti` - Current Versions Only

Shows only the currently active version of each article.

#### `articoli_storico` - Complete History

Shows all versions of all articles with timeline information.

## Usage

### 1. Initialize Versioning Database

```powershell
# First, ensure you have the versioning schema
python -c "from scraper_with_versioning import init_versioning_database; init_versioning_database()"
```

### 2. Scrape Documents with Versioning

```powershell
# Scrape a document and extract all article versions
python scraper_with_versioning.py "urn:nir:stato:legge:2020-03-17;18"
```

### 3. Test the Versioning System

```powershell
# Run comprehensive tests
python test_versioning.py
```

### 4. Analyze Article Versions

```powershell
# Analyze all articles
python analyze_versions.py analyze

# Analyze specific article
python analyze_versions.py analyze 1

# Compare two versions
python analyze_versions.py compare 1 orig agg.2

# Show validity timeline
python analyze_versions.py timeline 1

# List articles by update count
python analyze_versions.py list-by-updates

# Export to JSON
python analyze_versions.py export article_versions.json
```

### 5. Database Management

```powershell
# Show database info
python clear_database.py info

# Create backup
python clear_database.py backup

# Clear database (with confirmation)
python clear_database.py clear

# Clear database without confirmation
python clear_database.py clear --force
```

## Example Data Structure

When scraping an article with updates, the system will create:

### Article: "Art. 4"

```
📄 Articolo 4 - "Misure urgenti per la salute pubblica"

📝 orig: Original text from March 17, 2020
   Vigore: 2020-03-17 → 2020-04-29
   Status: SOSTITUITO

📝 agg.1: First update
   Vigore: 2020-04-30 → 2020-12-31
   Status: SOSTITUITO

📝 agg.2: Second update ⭐ CORRENTE
   Vigore: 2021-01-01 → attuale
   Status: VIGENTE
```

## Key Features for Legal Research

### 🔍 Historical Analysis

- See exactly what an article said at any point in time
- Track how legal provisions evolved over time
- Identify when specific changes were introduced

### 📅 Validity Periods

- Know exactly when each version was in effect
- Avoid confusion about which text applies to specific dates
- Proper citation with temporal context

### 🔄 Change Tracking

- Compare any two versions of an article
- Identify what was added, removed, or modified
- Understand the evolution of legal concepts

## API Examples

### Query Current Version

```sql
SELECT * FROM articoli_correnti WHERE articolo_id = 1;
```

### Query All Versions

```sql
SELECT * FROM articoli_storico WHERE articolo_id = 1 ORDER BY data_inizio_vigore;
```

### Find Articles Active on Specific Date

```sql
SELECT * FROM articoli_versioni
WHERE data_inizio_vigore <= '2020-06-01'
AND (data_fine_vigore IS NULL OR data_fine_vigore > '2020-06-01');
```

## File Structure

```
norme-net/
├── enhanced_schema_versioning.sql     # Database schema with versioning
├── scraper_with_versioning.py        # Enhanced scraper with version support
├── test_versioning.py                # Comprehensive test suite
├── analyze_versions.py               # Analysis and comparison tools
├── clear_database.py                 # Database management utilities
└── VERSIONING_README.md              # This file
```

## Technical Notes

### Version Identification

- `orig`: Original version of the article
- `agg.1`: First aggiornamento (update)
- `agg.2`: Second aggiornamento, etc.
- `numero_aggiornamento`: Numeric identifier for sorting

### Validity Dates

- `data_inizio_vigore`: When the version became effective
- `data_fine_vigore`: When superseded (NULL for current version)
- Extracted from page content using multiple date patterns

### Current Version Logic

- Only one version per article can have `is_current = TRUE`
- Previous versions automatically marked as `sostituito`
- Original version preserved even if superseded

## Benefits

1. **Complete Historical Record**: Never lose track of how articles evolved
2. **Legal Compliance**: Proper citation with temporal context
3. **Research Efficiency**: Quick access to any version of any article
4. **Data Integrity**: Versioning prevents data loss during updates
5. **Temporal Analysis**: Understand legal changes over time

## Testing

The system includes comprehensive tests for:

- Database schema validation
- Version insertion and retrieval
- Current version tracking
- Historical queries
- Data integrity constraints

Run tests with:

```powershell
python test_versioning.py
```

This versioning system ensures that NORME-NET preserves the complete evolution of Italian legal documents, making it a powerful tool for legal research and historical analysis.
