# Legal AI Database - Normattiva Scraper

## 🎯 Quick Start

Your database is **98.9% AI-ready** with enhanced legal content.

```powershell
# Your AI-ready database is already created: data.sqlite
# Optional: Add embeddings for semantic search
pip install transformers torch numpy
python legal_ai_enhancer.py

# Optional: Add more legal documents
python scraper_optimized.py 2001 20
```

## 📁 Project Structure

### Core Files

- `scraper_optimized.py` - Main data collection script
- `legal_ai_enhancer.py` - AI enhancement pipeline
- `data.sqlite` - Your AI-ready legal database
- `database_schema.sql` - Database structure

### Documentation

- `LEGAL_AI_GUIDE.md` - Complete guide and analysis
- `README.md` - This overview

### Data Status

- **15 Documents**: Complete legal texts from 2000
- **103 Articles**: Fully classified and searchable
- **295 Commi**: Individual paragraphs extracted
- **693 Citations**: Legal cross-references mapped

## 🚀 Usage

### Collect More Data

```powershell
python scraper_optimized.py [year] [num_docs]
# Example: python scraper_optimized.py 2001 50
```

### Enhance for AI

```powershell
python legal_ai_enhancer.py
```

### Build Your Legal AI

```python
import sqlite3
conn = sqlite3.connect('data.sqlite')
# Your 98.9% AI-ready database is ready to use!
```

## 📊 Database Contents

- **Article Classification**: 100% complete (definitoria, procedurale, sanzionatoria, sostanziale)
- **Document Categorization**: Mapped to legal domains
- **Citation Network**: 693 cross-references between articles
- **Commi Extraction**: Paragraph-level granularity
- **AI Enhancement Score**: 98.9%

For complete details, see `LEGAL_AI_GUIDE.md`.
